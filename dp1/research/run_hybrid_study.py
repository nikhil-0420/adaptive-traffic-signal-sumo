"""Runner script for the 840-cell Marathahalli Hybrid Controller Study (exp_marathahalli_hybrid_840).

Integrates the 720 verified baseline runs from exp_marathahalli_site_720 with the 120
real execution runs of hybrid_queue_adaptive on held-out seeds (121..130), and executes
the complete research statistics pipeline (bootstrap CIs, fairness, plots, reports).
"""
import concurrent.futures
import csv
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Dict, List, Tuple

import pandas as pd

from dp1 import config as C
from dp1.runner import run_simulation
from dp1.research.matrix import (
    CellStatus,
    MatrixCell,
    ResearchMatrix,
    SITE_PATTERNS,
    HYBRID_SITE_POLICIES,
    SITE_RESEARCH_SEEDS,
)
from dp1.research.stats import (
    compute_aggregates,
    compute_fairness_by_approach,
    compute_fairness_by_direction,
    compute_paired_best_policy_analysis,
    compute_paired_deltas,
)
from dp1.research.plots import generate_research_plots
from dp1.research.report_gen import generate_research_report


EXP_ID = "exp_marathahalli_hybrid_840"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXP_DIR = REPO_ROOT / "results" / "research" / EXP_ID
SITE_720_DIR = REPO_ROOT / "results" / "research" / "exp_marathahalli_site_720"


def _run_single_hybrid_cell(args: Tuple[str, str, int, Path]) -> Dict:
    pattern, demand_level, seed, run_dir = args
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = run_dir / "metrics.json"

    # Reuse if already completed
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("completion_rate", 0) > 0:
                return data
        except Exception:
            pass

    t0 = time.time()
    metrics = run_simulation(
        scenario=pattern,
        policy="hybrid_queue_adaptive",
        seed=seed,
        demand_level=demand_level,
        out_dir=run_dir,
        network="marathahalli",
        attempts=3,
    )
    elapsed = round(time.time() - t0, 2)
    metrics["runtime_s"] = elapsed
    metrics["pattern"] = pattern
    metrics["demand_level"] = demand_level
    metrics["policy"] = "hybrid_queue_adaptive"
    metrics["seed"] = seed
    metrics["network"] = "marathahalli"
    metrics["cell_id"] = f"cell_marathahalli_{pattern}_{demand_level}_hybrid_queue_adaptive_s{seed}"
    return metrics


def execute_study(jobs: int = 4):
    print(f"=== Starting {EXP_ID} Execution Pipeline ===")
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    runs_dir = EXP_DIR / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load baseline runs from exp_marathahalli_site_720
    assert SITE_720_DIR.exists(), f"Missing baseline dataset at {SITE_720_DIR}"
    site_720_raw = SITE_720_DIR / "raw_runs.csv"
    assert site_720_raw.exists(), f"Missing {site_720_raw}"

    df_base = pd.read_csv(site_720_raw)
    print(f"Loaded {len(df_base)} baseline runs from exp_marathahalli_site_720.")

    raw_csv = EXP_DIR / "raw_runs.csv"
    if raw_csv.exists():
        df_all = pd.read_csv(raw_csv)
        if len(df_all) == 840:
            print(f"Reusing existing complete 840-run dataset from {raw_csv}.")
        else:
            df_all = None
    else:
        df_all = None

    if df_all is None:
        # 2. Identify and execute the 120 hybrid_queue_adaptive runs
        tasks = []
        for pat in SITE_PATTERNS:
            for lvl in C.RESEARCH.levels:
                for sd in SITE_RESEARCH_SEEDS:
                    cell_id = f"cell_marathahalli_{pat}_{lvl}_hybrid_queue_adaptive_s{sd}"
                    cell_run_dir = runs_dir / cell_id
                    tasks.append((pat, lvl, sd, cell_run_dir))

        print(f"Prepared {len(tasks)} hybrid_queue_adaptive cells on held-out seeds 121..130.")

        hybrid_results = []
        completed_count = 0
        t_start = time.time()

        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = {executor.submit(_run_single_hybrid_cell, t): t for t in tasks}
            for future in concurrent.futures.as_completed(futures):
                t_info = futures[future]
                try:
                    res = future.result()
                    hybrid_results.append(res)
                    completed_count += 1
                    if completed_count % 10 == 0 or completed_count == len(tasks):
                        rate = completed_count / max(1.0, time.time() - t_start)
                        print(f"  [{completed_count}/{len(tasks)}] Completed {res.get('scenario')} ({res.get('demand_level')}) s{res.get('seed')} - avg_wait: {res.get('avg_wait_s'):.1f}s ({rate:.2f} runs/s)")
                except Exception as e:
                    print(f"ERROR running cell {t_info}: {e}", file=sys.stderr)
                    raise

        df_hybrid = pd.DataFrame(hybrid_results)
        # Ensure required columns align with df_base
        for col in df_base.columns:
            if col not in df_hybrid.columns:
                df_hybrid[col] = None

        # Harmonize pattern/scenario column names
        if "pattern" not in df_hybrid.columns and "scenario" in df_hybrid.columns:
            df_hybrid["pattern"] = df_hybrid["scenario"]
        if "pattern" not in df_base.columns and "scenario" in df_base.columns:
            df_base["pattern"] = df_base["scenario"]

        # 3. Combine into complete 840-cell matrix
        df_all = pd.concat([df_base, df_hybrid], ignore_index=True)
        df_all.to_csv(raw_csv, index=False)
        print(f"Saved complete 840-run dataset to {raw_csv} (shape: {df_all.shape}).")

    # 4. Statistical computations
    print("Computing statistical aggregates and paired bootstrap confidence intervals (10,000 resamples)...")
    agg_df = compute_aggregates(df_all)
    agg_df.to_csv(EXP_DIR / "aggregate.csv", index=False)

    deltas_webster = compute_paired_deltas(df_all, reference_policy="fixed_webster", n_bootstrap=10_000, seed=42)
    deltas_webster.to_csv(EXP_DIR / "paired_deltas.csv", index=False)

    fairness_app = compute_fairness_by_approach(df_all)
    fairness_app.to_csv(EXP_DIR / "fairness_by_approach.csv", index=False)

    fairness_dir = compute_fairness_by_direction(df_all)
    fairness_dir.to_csv(EXP_DIR / "fairness_by_direction.csv", index=False)

    paired_best = compute_paired_best_policy_analysis(df_all, n_bootstrap=10_000, seed=42)
    paired_best.to_csv(EXP_DIR / "paired_best_policy.csv", index=False)

    # 5. Build matrix status and manifest
    matrix_cells = []
    status_records = []
    for _, row in df_all.iterrows():
        cid = row.get("cell_id") or f"cell_marathahalli_{row['pattern']}_{row['demand_level']}_{row['policy']}_s{row['seed']}"
        matrix_cells.append(MatrixCell(
            cell_id=cid,
            pattern=row["pattern"],
            demand_level=row["demand_level"],
            policy=row["policy"],
            seed=int(row["seed"]),
            network="marathahalli",
            status=CellStatus.COMPLETE.value,
            runtime_s=float(row.get("runtime_s", 0.0) or 0.0),
            route_hash=str(row.get("route_hash", "")),
        ))
        status_records.append({
            "cell_id": cid,
            "pattern": row["pattern"],
            "demand_level": row["demand_level"],
            "policy": row["policy"],
            "seed": int(row["seed"]),
            "status": "complete",
            "runtime_s": float(row.get("runtime_s", 0.0) or 0.0),
            "route_hash": str(row.get("route_hash", "")),
            "error_message": "",
        })

    pd.DataFrame(status_records).to_csv(EXP_DIR / "matrix_status.csv", index=False)

    manifest = {
        "experiment_id": EXP_ID,
        "status": "complete",
        "total_cells": len(df_all),
        "status_counts": {
            "pending": 0,
            "running": 0,
            "complete": len(df_all),
            "failed": 0,
            "blocked": 0,
            "skipped": 0,
        },
        "preset": "full",
        "patterns": list(SITE_PATTERNS),
        "levels": list(C.RESEARCH.levels),
        "demand_multipliers": {"low": 0.7, "medium": 1.0, "heavy": 1.3},
        "policies": list(HYBRID_SITE_POLICIES),
        "seeds": list(SITE_RESEARCH_SEEDS),
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 42,
        "emergency_matrix": false if "false" in locals() else False,
        "network": "marathahalli",
        "python_version": sys.version,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(EXP_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 6. Generate Plots
    print("Generating publication-quality figures in plots/...")
    plots_dir = EXP_DIR / "plots"
    generate_research_plots(
        raw_df=df_all,
        agg_df=agg_df,
        deltas_df=deltas_webster,
        out_dir=plots_dir,
        paired_ties_df=paired_best,
    )

    # 7. Generate Markdown Report
    print("Generating comprehensive research report (report.md)...")
    generate_research_report(
        manifest=manifest,
        agg_df=agg_df,
        deltas_df=deltas_webster,
        fairness_df=fairness_app,
        direction_df=fairness_dir,
        status_df=pd.DataFrame(status_records),
        out_path=EXP_DIR / "report.md",
        raw_df=df_all,
        paired_best_df=paired_best,
    )

    # 8. Export to Frontend Demo Snapshot
    fe_exp_dir = REPO_ROOT / "frontend" / "public" / "demo-data" / "experiments" / EXP_ID
    fe_exp_dir.mkdir(parents=True, exist_ok=True)
    for fname in [
        "manifest.json", "report.md", "aggregate.csv", "raw_runs.csv",
        "paired_deltas.csv", "fairness_by_approach.csv", "fairness_by_direction.csv",
        "paired_best_policy.csv", "matrix_status.csv"
    ]:
        src = EXP_DIR / fname
        if src.exists():
            shutil.copy2(src, fe_exp_dir / fname)
            if fname.endswith(".csv"):
                # Also write json format for frontend client consumption
                df_temp = pd.read_csv(src)
                df_temp.to_json(fe_exp_dir / fname.replace(".csv", ".json"), orient="records", indent=2)

    print(f"=== Study {EXP_ID} Successfully Completed! Artifacts saved to {EXP_DIR} and {fe_exp_dir} ===")


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    execute_study(jobs=workers)
