"""Research evaluation matrix execution orchestrator."""
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .. import config as C
from ..runner import run_simulation
from .matrix import CellStatus, MatrixCell, ResearchMatrix, build_research_matrix, format_matrix_preview
from .plots import generate_research_plots
from .report_gen import generate_research_report
from .stats import (
    compute_aggregates,
    compute_fairness_by_approach,
    compute_fairness_by_direction,
    compute_paired_deltas,
)


def _get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def _worker_execute_cell(args: Tuple) -> Tuple[MatrixCell, Optional[Dict], Optional[str]]:
    """Worker function for executing a single matrix cell."""
    cell_dict, exp_dir_str, model_path_str = args
    cell = MatrixCell(**cell_dict)
    exp_dir = Path(exp_dir_str)
    cell_run_dir = exp_dir / "runs" / cell.cell_id

    # Check for RL model if policy is rl_dqn
    policy_kwargs = {}
    if cell.policy == "rl_dqn":
        resolved_model = Path(model_path_str) if model_path_str else (C.RL.models_dir / f"{C.RL.default_model_name}.zip")
        if not resolved_model.exists() and resolved_model.with_suffix(".zip").exists():
            resolved_model = resolved_model.with_suffix(".zip")
        if not resolved_model.exists():
            cell.status = CellStatus.BLOCKED.value
            cell.error_message = f"Model checkpoint not found at '{resolved_model}'"
            return cell, None, None
        policy_kwargs["model_path"] = str(resolved_model)

    start_t = time.time()
    try:
        metrics = run_simulation(
            scenario=cell.pattern,
            policy=cell.policy,
            seed=cell.seed,
            demand_level=cell.demand_level,
            out_dir=cell_run_dir,
            policy_kwargs=policy_kwargs if policy_kwargs else None,
        )
        elapsed = time.time() - start_t
        cell.runtime_s = round(elapsed, 2)
        cell.route_hash = metrics.get("route_hash")
        cell.status = CellStatus.COMPLETE.value

        # Standardize row columns for research schema
        row = dict(metrics)
        row["pattern"] = cell.pattern
        row["cell_id"] = cell.cell_id
        return cell, row, None
    except Exception as exc:
        elapsed = time.time() - start_t
        cell.runtime_s = round(elapsed, 2)
        cell.status = CellStatus.FAILED.value
        cell.error_message = str(exc)
        err_log = f"Error in cell {cell.cell_id}: {exc}"
        return cell, None, err_log


def run_research_experiment(
    experiment_id: Optional[str] = None,
    preset: str = "full",
    patterns: Optional[Tuple[str, ...]] = None,
    levels: Optional[Tuple[str, ...]] = None,
    policies: Optional[Tuple[str, ...]] = None,
    seeds: Optional[Tuple[int, ...]] = None,
    limit: Optional[int] = None,
    jobs: int = 1,
    resume: bool = True,
    dry_run: bool = False,
    out_dir: Optional[Path] = None,
    model_path: Optional[str] = None,
    emergency_matrix: bool = False,
) -> Tuple[ResearchMatrix, Path]:
    """Execute or preview a research evaluation matrix experiment."""
    exp_id = experiment_id or f"exp_{time.strftime('%Y%m%d_%H%M%S')}"
    exp_dir = Path(out_dir or C.RESEARCH.research_dir / exp_id)
    exp_dir.mkdir(parents=True, exist_ok=True)

    matrix = build_research_matrix(
        experiment_id=exp_id,
        patterns=patterns,
        levels=levels,
        policies=policies,
        seeds=seeds,
        preset=preset,
    )

    if dry_run:
        print(format_matrix_preview(matrix))
        return matrix, exp_dir

    status_file = exp_dir / "matrix_status.csv"
    raw_runs_file = exp_dir / "raw_runs.csv"
    failures_file = exp_dir / "failures.jsonl"

    existing_rows = []
    completed_cell_ids = set()

    # Resume handling: validate successful completed cells
    if resume and status_file.exists() and raw_runs_file.exists():
        try:
            prev_status = pd.read_csv(status_file)
            for _, r in prev_status.iterrows():
                cid = r["cell_id"]
                st = r["status"]
                if st == CellStatus.COMPLETE.value:
                    # Validate that tripinfo and timeseries exist
                    cell_dir = exp_dir / "runs" / cid
                    if (cell_dir / "tripinfo.xml").exists() and (cell_dir / "timeseries.csv").exists():
                        completed_cell_ids.add(cid)
            if completed_cell_ids:
                raw_df_prev = pd.read_csv(raw_runs_file)
                existing_rows = raw_df_prev[raw_df_prev["cell_id"].isin(completed_cell_ids)].to_dict("records")
        except Exception:
            pass

    # Update cells already complete
    for c in matrix.cells:
        if c.cell_id in completed_cell_ids:
            c.status = CellStatus.COMPLETE.value

    # Identify pending cells
    pending_cells = [c for c in matrix.cells if c.status != CellStatus.COMPLETE.value]
    if limit is not None and limit > 0:
        pending_cells = pending_cells[:limit]

    print(f"\n[RESEARCH] Experiment: {exp_id}")
    print(f"[RESEARCH] Target Directory: {exp_dir}")
    print(f"[RESEARCH] Total planned cells: {matrix.total_cells} | Complete: {len(completed_cell_ids)} | Executing now: {len(pending_cells)}")

    worker_args = [
        (c.to_dict(), str(exp_dir), model_path)
        for c in pending_cells
    ]

    new_rows = []
    if worker_args:
        if jobs > 1:
            with ProcessPoolExecutor(max_workers=jobs) as executor:
                for updated_cell, row, err in executor.map(_worker_execute_cell, worker_args):
                    # Update cell in matrix
                    for mc in matrix.cells:
                        if mc.cell_id == updated_cell.cell_id:
                            mc.status = updated_cell.status
                            mc.runtime_s = updated_cell.runtime_s
                            mc.route_hash = updated_cell.route_hash
                            mc.error_message = updated_cell.error_message
                            break
                    if row:
                        new_rows.append(row)
                        print(f"  [OK] {updated_cell.cell_id} ({updated_cell.runtime_s:.1f}s) wait={row.get('avg_wait_s', 0):.1f}s")
                        if len(new_rows) % 20 == 0:
                            pd.DataFrame([c.to_dict() for c in matrix.cells]).to_csv(status_file, index=False)
                            pd.DataFrame(existing_rows + new_rows).to_csv(raw_runs_file, index=False)
                    elif err:
                        print(f"  [ERR] {updated_cell.cell_id}: {updated_cell.error_message}")
                        with open(failures_file, "a", encoding="utf-8") as ff:
                            ff.write(json.dumps({"cell_id": updated_cell.cell_id, "error": err, "timestamp": time.time()}) + "\n")
        else:
            for warg in worker_args:
                updated_cell, row, err = _worker_execute_cell(warg)
                for mc in matrix.cells:
                    if mc.cell_id == updated_cell.cell_id:
                        mc.status = updated_cell.status
                        mc.runtime_s = updated_cell.runtime_s
                        mc.route_hash = updated_cell.route_hash
                        mc.error_message = updated_cell.error_message
                        break
                if row:
                    new_rows.append(row)
                    print(f"  [OK] {updated_cell.cell_id} ({updated_cell.runtime_s:.1f}s) wait={row.get('avg_wait_s', 0):.1f}s")
                elif err:
                    print(f"  [ERR] {updated_cell.cell_id}: {updated_cell.error_message}")
                    with open(failures_file, "a", encoding="utf-8") as ff:
                        ff.write(json.dumps({"cell_id": updated_cell.cell_id, "error": err, "timestamp": time.time()}) + "\n")

    # Save matrix_status.csv
    status_df = pd.DataFrame([c.to_dict() for c in matrix.cells])
    status_df.to_csv(status_file, index=False)

    # Save raw_runs.csv
    all_rows = existing_rows + new_rows
    raw_df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
    if not raw_df.empty:
        raw_df.to_csv(raw_runs_file, index=False)

    # Compute statistics and tables
    agg_df = compute_aggregates(raw_df)
    agg_df.to_csv(exp_dir / "aggregate.csv", index=False)

    deltas_df = compute_paired_deltas(
        raw_df,
        reference_policy="fixed",
        n_bootstrap=C.RESEARCH.bootstrap_resamples,
        seed=C.RESEARCH.bootstrap_seed,
    )
    deltas_df.to_csv(exp_dir / "paired_deltas.csv", index=False)

    fairness_app_df = compute_fairness_by_approach(raw_df)
    fairness_app_df.to_csv(exp_dir / "fairness_by_approach.csv", index=False)

    fairness_dir_df = compute_fairness_by_direction(raw_df)
    fairness_dir_df.to_csv(exp_dir / "fairness_by_direction.csv", index=False)

    # Generate figures
    plots_dir = exp_dir / "plots"
    generate_research_plots(raw_df, agg_df, deltas_df, plots_dir)

    # Write manifest.json
    status_counts = matrix.status_counts()
    overall_status = "complete" if status_counts.get("complete", 0) == matrix.total_cells else "partial"

    manifest_data = {
        "experiment_id": exp_id,
        "status": overall_status,
        "total_cells": matrix.total_cells,
        "status_counts": status_counts,
        "preset": matrix.preset,
        "patterns": list(matrix.patterns),
        "levels": list(matrix.levels),
        "demand_multipliers": {lvl: C.DEMAND_LEVELS[lvl] for lvl in matrix.levels},
        "policies": list(matrix.policies),
        "seeds": list(matrix.seeds),
        "bootstrap_resamples": C.RESEARCH.bootstrap_resamples,
        "bootstrap_seed": C.RESEARCH.bootstrap_seed,
        "emergency_matrix": emergency_matrix,
        "git_commit": _get_git_commit(),
        "python_version": sys.version,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(exp_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # Generate report.md
    generate_research_report(
        manifest=manifest_data,
        agg_df=agg_df,
        deltas_df=deltas_df,
        fairness_df=fairness_app_df,
        direction_df=fairness_dir_df,
        status_df=status_df,
        out_path=exp_dir / "report.md",
    )

    print(f"\n[RESEARCH] Experiment finished: status={overall_status} ({status_counts.get('complete', 0)}/{matrix.total_cells} complete)")
    print(f"[RESEARCH] Artifacts saved to: {exp_dir}")
    return matrix, exp_dir
