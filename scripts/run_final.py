"""Final Evaluation Matrix Runner (Phase 13 Quality-Gated).

Enforces:
1. Working tree must be clean (no uncommitted edits).
2. HEAD commit must match the frozen tag 'dp1-final-frozen'.
3. Records environment manifest (commit, SUMO version, packages).
4. Resumes crashed/incomplete cells only; skips completed cells.
5. Logs real-time cell statuses to matrix_status.csv.
6. Provides --dry-run to display matrix counts without execution.
7. Supports --cut for faster review execution.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.runner import run_simulation

MATRIX_YAML = PROJECT_ROOT / "experiments" / "final_matrix.yaml"
MATRIX_JSON = PROJECT_ROOT / "experiments" / "final_matrix.json"
RESULTS_BASE_DIR = PROJECT_ROOT / "results" / "research" / "exp_marathahalli_improve_final"
FROZEN_TAG = "dp1-final-frozen"



def check_git_status(allow_dirty: bool = False, skip_tag_check: bool = False):
    """Enforce clean working tree and frozen tag alignment."""
    if allow_dirty:
        print("[WARNING] --allow-dirty specified: skipping git cleanliness verification.")
        return

    # Check for uncommitted modifications
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Git command failed: {proc.stderr}")
    uncommitted = [line for line in proc.stdout.strip().splitlines() if line and not line.startswith("?? results/")]
    if uncommitted:
        raise RuntimeError(
            f"REFUSING TO START: Working tree has uncommitted modifications:\n" +
            "\n".join(uncommitted) +
            "\nCommit or stash changes before running the frozen final matrix."
        )

    # Check HEAD matches frozen tag
    if not skip_tag_check:
        tag_proc = subprocess.run(["git", "rev-parse", FROZEN_TAG], cwd=PROJECT_ROOT, capture_output=True, text=True)
        head_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        if tag_proc.returncode != 0:
            raise RuntimeError(f"REFUSING TO START: Frozen tag '{FROZEN_TAG}' not found. Create the tag first.")
        tag_commit = tag_proc.stdout.strip()
        head_commit = head_proc.stdout.strip()
        if tag_commit != head_commit:
            raise RuntimeError(
                f"REFUSING TO START: HEAD ({head_commit[:8]}) does not equal frozen tag '{FROZEN_TAG}' ({tag_commit[:8]}).\n"
                f"Ensure you are checked out at the frozen commit."
            )
    print(f"[OK] Git cleanliness verified. HEAD matches frozen tag '{FROZEN_TAG}'.")


def get_environment_manifest(total_planned: int, is_cut: bool) -> Dict[str, Any]:
    """Capture precise reproducible manifest."""
    # Commit hash
    proc_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    commit_hash = proc_hash.stdout.strip() if proc_hash.returncode == 0 else "UNKNOWN"

    # SUMO version
    proc_sumo = subprocess.run(["sumo", "--version"], capture_output=True, text=True)
    sumo_ver = proc_sumo.stdout.splitlines()[0] if proc_sumo.returncode == 0 else "UNKNOWN"

    # Python packages
    packages = {}
    for pkg in ["gymnasium", "stable_baselines3", "torch", "pandas", "numpy", "traci"]:
        try:
            mod = __import__(pkg)
            packages[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            packages[pkg] = "not installed"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_hash": commit_hash,
        "frozen_tag": FROZEN_TAG,
        "sumo_version": sumo_ver,
        "python_version": sys.version,
        "packages": packages,
        "total_planned_cells": total_planned,
        "is_cut_matrix": is_cut,
    }


def load_matrix_cells(is_cut: bool = False) -> List[Tuple[str, str, str, int, str]]:
    """Parse experiments/final_matrix.yaml (or json) into list of (cell_id, scenario, demand_level, seed, policy)."""
    if yaml is not None and MATRIX_YAML.exists():
        with open(MATRIX_YAML, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    else:
        with open(MATRIX_JSON, "r", encoding="utf-8") as f:
            spec = json.load(f)


    main_pols = [p["name"] for p in spec["main_matrix"]["policies"]]
    main_conds = [(c["scenario"], c["demand_level"]) for c in spec["main_matrix"]["conditions"]]
    main_seeds = spec["main_matrix"]["seeds"]

    abl_pols = [p["name"] for p in spec["ablation_submatrix"]["variants"]]
    abl_conds = [(c["scenario"], c["demand_level"]) for c in spec["ablation_submatrix"]["conditions"]]
    abl_seeds = spec["ablation_submatrix"]["seeds"]

    if is_cut:
        # Apply cut rule: ablation seeds 20 -> 10 (seeds 131..140)
        abl_seeds = abl_seeds[:10]
        # Omit stationary-low conditions across all main policies
        main_conds = [c for c in main_conds if c[1] != "low"]

    cells = []
    # Main matrix
    for sc, dl in main_conds:
        for s in main_seeds:
            for pol in main_pols:
                cell_id = f"marathahalli_{sc}_{dl}_{pol}_s{s}"
                cells.append((cell_id, sc, dl, s, pol))

    # Ablation matrix
    for sc, dl in abl_conds:
        for s in abl_seeds:
            for pol in abl_pols:
                cell_id = f"ablation_{sc}_{dl}_{pol}_s{s}"
                cells.append((cell_id, sc, dl, s, pol))

    return cells


def execute_cell_worker(task: Tuple) -> Dict[str, Any]:
    cell_id, sc, dl, s, pol, out_dir_str = task
    out_dir = Path(out_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_file = out_dir / "metrics.json"
    ts_file = out_dir / "timeseries.csv"

    # Resume check: skip already completed cells
    if metrics_file.exists() and ts_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("completion_rate", 0.0) >= 0.99:
                return {
                    "cell_id": cell_id,
                    "policy": pol,
                    "scenario": sc,
                    "demand_level": dl,
                    "seed": s,
                    "status": "ALREADY_COMPLETED",
                    "elapsed_s": d.get("wall_clock_s", 0.0),
                    "error": "",
                }
        except Exception:
            pass

    t0 = time.time()
    try:
        res = run_simulation(
            scenario=sc,
            policy=pol,
            seed=s,
            network="marathahalli",
            demand_level=dl,
            out_dir=out_dir,
        )
        elapsed = time.time() - t0
        res["wall_clock_s"] = elapsed
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

        return {
            "cell_id": cell_id,
            "policy": pol,
            "scenario": sc,
            "demand_level": dl,
            "seed": s,
            "status": "SUCCESS",
            "elapsed_s": elapsed,
            "error": "",
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "cell_id": cell_id,
            "policy": pol,
            "scenario": sc,
            "demand_level": dl,
            "seed": s,
            "status": "FAILED",
            "elapsed_s": elapsed,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="Execute final experiment matrix for DP1.")
    parser.add_argument("--dry-run", action="store_true", help="Print cell list and counts without running simulations.")
    parser.add_argument("--cut", action="store_true", help="Execute the reduced cut matrix (ablation seeds 10, stationary-low omitted).")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel worker processes (default: 8).")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running with uncommitted git modifications.")
    parser.add_argument("--skip-tag-check", action="store_true", help="Skip verifying HEAD equals frozen tag.")
    args = parser.parse_args()

    cells = load_matrix_cells(is_cut=args.cut)
    total = len(cells)

    if args.dry_run:
        print(f"=== FINAL MATRIX DRY RUN (is_cut={args.cut}) ===")
        print(f"Total planned simulation cells: {total}")
        main_c = [c for c in cells if not c[0].startswith("ablation_")]
        abl_c = [c for c in cells if c[0].startswith("ablation_")]
        print(f"  - Main Matrix Cells:     {len(main_c)}")
        print(f"  - Ablation Matrix Cells: {len(abl_c)}")
        print("\nSample Cells:")
        for c in cells[:10]:
            print(f"    {c[0]} (Policy={c[4]}, Scen={c[1]}, Level={c[2]}, Seed={c[3]})")
        print(f"    ... ({total - 10} more cells)")
        return

    # Enforce Git Quality Gate
    check_git_status(allow_dirty=args.allow_dirty, skip_tag_check=args.skip_tag_check)

    RESULTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = get_environment_manifest(total, is_cut=args.cut)
    with open(RESULTS_BASE_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    status_csv_path = RESULTS_BASE_DIR / "matrix_status.csv"
    csv_file = open(status_csv_path, "a", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_file, fieldnames=["cell_id", "policy", "scenario", "demand_level", "seed", "status", "elapsed_s", "error"])
    if status_csv_path.stat().st_size == 0:
        csv_writer.writeheader()

    print(f"Starting execution of {total} cells with {args.workers} workers...")
    tasks = []
    for c in cells:
        cell_id, sc, dl, s, pol = c
        out_dir = RESULTS_BASE_DIR / cell_id
        tasks.append((cell_id, sc, dl, s, pol, str(out_dir)))

    completed = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(execute_cell_worker, t): t for t in tasks}
        for fut in as_completed(future_map):
            completed += 1
            res = fut.result()
            csv_writer.writerow(res)
            csv_file.flush()
            if completed % 50 == 0 or completed == total:
                elapsed_min = (time.time() - t0) / 60.0
                print(f"  [{completed}/{total}] cells processed in {elapsed_min:.1f}m ({(completed/total)*100:.1f}%)...")

    csv_file.close()
    print(f"Final matrix execution complete. Status logged to {status_csv_path}")


if __name__ == "__main__":
    main()
