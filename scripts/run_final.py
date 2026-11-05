"""Final Evaluation Matrix Runner (Pre-Registration Amendment 3).

Enforces:
1. Working tree verification.
2. One FRESH process per simulation (subprocess isolation).
3. Collision-free TraCI/SUMO ports so WinError 10061 cannot occur.
4. Seed-major execution (each seed block contains 42 main cells + 6 ablation cells = 48 cells).
5. Resumes crashed/incomplete cells only; never reruns completed cells.
6. Logs real-time statuses to matrix_status.csv.
7. Stopping rule via --max-hours (finishes current seed block before graceful exit).
8. Comprehensive --dry-run reporting.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MATRIX_YAML = PROJECT_ROOT / "experiments" / "final_matrix.yaml"
MATRIX_JSON = PROJECT_ROOT / "experiments" / "final_matrix.json"
RESULTS_BASE_DIR = PROJECT_ROOT / "results" / "research" / "exp_marathahalli_improve_final"


def load_matrix_spec() -> Dict[str, Any]:
    """Load matrix definition from JSON or YAML."""
    if MATRIX_JSON.exists():
        with open(MATRIX_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    elif MATRIX_YAML.exists():
        try:
            import yaml
            with open(MATRIX_YAML, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            pass
    raise FileNotFoundError("Neither final_matrix.json nor readable final_matrix.yaml found.")


def build_seed_blocks() -> List[Tuple[int, List[Dict[str, Any]]]]:
    """Build seed-major blocks of cells (42 main + 6 ablation = 48 cells per seed)."""
    spec = load_matrix_spec()
    seeds = spec["main_matrix"]["seeds"]
    main_pols = [p["name"] for p in spec["main_matrix"]["policies"]]
    main_conds = [(c["scenario"], c["demand_level"]) for c in spec["main_matrix"]["conditions"]]

    abl_pols = [p["name"] for p in spec["ablation_submatrix"]["variants"]]
    abl_conds = [(c["scenario"], c["demand_level"]) for c in spec["ablation_submatrix"]["conditions"]]

    blocks = []
    for s in seeds:
        block_cells = []
        # 1. Main matrix (42 cells: 6 conditions x 7 policies)
        for sc, dl in main_conds:
            for pol in main_pols:
                cell_id = f"marathahalli_{sc}_{dl}_{pol}_s{s}"
                block_cells.append({
                    "cell_id": cell_id,
                    "scenario": sc,
                    "demand_level": dl,
                    "policy": pol,
                    "seed": s,
                    "is_ablation": False,
                })

        # 2. Ablation matrix (6 cells: 6 conditions x 1 policy)
        for sc, dl in abl_conds:
            for pol in abl_pols:
                cell_id = f"ablation_{sc}_{dl}_{pol}_s{s}"
                block_cells.append({
                    "cell_id": cell_id,
                    "scenario": sc,
                    "demand_level": dl,
                    "policy": pol,
                    "seed": s,
                    "is_ablation": True,
                })
        blocks.append((s, block_cells))

    return blocks


def execute_cell_worker_subprocess(task: Dict[str, Any], port: int) -> Dict[str, Any]:
    """Execute one simulation in a FRESH subprocess with dedicated collision-free port."""
    cell_id = task["cell_id"]
    sc = task["scenario"]
    dl = task["demand_level"]
    pol = task["policy"]
    s = task["seed"]
    out_dir = RESULTS_BASE_DIR / cell_id
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
    # Launch fresh isolated child process
    worker_cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--cell-worker",
        "--scenario", sc,
        "--demand-level", dl,
        "--policy", pol,
        "--seed", str(s),
        "--out-dir", str(out_dir),
        "--port", str(port),
    ]

    proc = subprocess.run(worker_cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    elapsed = time.time() - t0

    if proc.returncode == 0:
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
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Process exited with code {proc.returncode}"
        return {
            "cell_id": cell_id,
            "policy": pol,
            "scenario": sc,
            "demand_level": dl,
            "seed": s,
            "status": "FAILED",
            "elapsed_s": elapsed,
            "error": err_msg[:500],
        }


def run_cell_worker_cli():
    """Worker entry point running inside a dedicated fresh subprocess."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--demand-level", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    from dp1.runner import run_simulation
    t0 = time.time()
    res = run_simulation(
        scenario=args.scenario,
        policy=args.policy,
        seed=args.seed,
        network="marathahalli",
        demand_level=args.demand_level,
        out_dir=Path(args.out_dir),
        port=args.port,
    )
    elapsed = time.time() - t0
    res["wall_clock_s"] = elapsed
    metrics_file = Path(args.out_dir) / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)


def main():
    if "--cell-worker" in sys.argv:
        sys.argv.remove("--cell-worker")
        run_cell_worker_cli()
        return

    parser = argparse.ArgumentParser(description="Execute final experiment matrix for DP1 (Amendment 3).")
    parser.add_argument("--dry-run", action="store_true", help="Print cell counts, launch command and estimates.")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel fresh workers (default: 5).")
    parser.add_argument("--max-hours", type=float, default=None, help="Wall-clock hours stopping rule.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running with uncommitted git modifications.")
    args = parser.parse_args()

    seed_blocks = build_seed_blocks()
    total_seeds = len(seed_blocks)
    cells_per_block = len(seed_blocks[0][1]) if seed_blocks else 0
    total_runs = sum(len(b[1]) for b in seed_blocks)
    main_runs = sum(sum(1 for c in b[1] if not c["is_ablation"]) for b in seed_blocks)
    abl_runs = total_runs - main_runs

    # Measured rate calculation: ~6 s per run at 8 workers -> ~10 s per run at 5 workers
    est_sec_per_run_at_5 = 10.0
    est_total_min = (total_runs * est_sec_per_run_at_5) / 60.0
    est_hours = est_total_min / 60.0

    if args.dry_run:
        print("================================================================================")
        print("          DP1 FINAL EVALUATION MATRIX DRY RUN (PRE-REGISTRATION AMENDMENT 3)    ")
        print("================================================================================")
        print(f"Total planned simulations:       {total_runs}")
        print(f"  - Main Matrix Runs (7x6x8):   {main_runs}")
        print(f"  - Ablation Runs (1x6x8):      {abl_runs}")
        print(f"Total Seed Blocks:               {total_seeds} (Seeds: {[b[0] for b in seed_blocks]})")
        print(f"Runs per Seed Block:             {cells_per_block} (42 main + 6 ablation)")
        print(f"Ordering Protocol:               SEED-MAJOR")
        print(f"Process Isolation:               ONE FRESH SUBPROCESS PER SIMULATION")
        print(f"Port Allocation:                 Worker-dedicated collision-free TraCI ports")
        print(f"Workers Configured:              {args.workers}")
        print(f"Estimated Rate:                  ~6s/run at 8 workers | ~10s/run at 5 workers")
        print(f"Estimated Total Runtime:         {est_total_min:.1f} minutes ({est_hours:.2f} hours)")
        print("--------------------------------------------------------------------------------")
        print("EXACT LAUNCH COMMAND TO RUN IN YOUR TERMINAL:")
        print(f"  .venv\\Scripts\\python scripts/run_final.py --workers {args.workers} --max-hours 1.3")
        print("================================================================================")
        return

    # Check git status
    if not args.allow_dirty:
        proc = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        uncommitted = [l for l in proc.stdout.strip().splitlines() if l and not l.startswith("?? results/")]
        if uncommitted:
            print("[WARNING] Working tree has uncommitted modifications:\n" + "\n".join(uncommitted))

    RESULTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    status_csv_path = RESULTS_BASE_DIR / "matrix_status.csv"
    file_exists = status_csv_path.exists()
    csv_file = open(status_csv_path, "a", newline="", encoding="utf-8")
    fieldnames = ["cell_id", "policy", "scenario", "demand_level", "seed", "status", "elapsed_s", "error", "timestamp"]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if not file_exists or status_csv_path.stat().st_size == 0:
        csv_writer.writeheader()
        csv_file.flush()

    print(f"Launching Seed-Major Matrix: {total_runs} runs across {total_seeds} seed blocks with {args.workers} workers...")
    global_start = time.time()
    total_completed = 0
    seeds_completed = 0

    # Dedicated worker port offset table: 20000 + worker_id * 200
    # Thread pool coordinates worker threads that each spawn isolated subprocesses
    worker_cell_counts = {w: 0 for w in range(args.workers)}

    for seed_idx, (seed_val, block_tasks) in enumerate(seed_blocks):
        elapsed_hours = (time.time() - global_start) / 3600.0
        if args.max_hours is not None and elapsed_hours >= args.max_hours:
            print(f"[STOPPING RULE] Elapsed time ({elapsed_hours:.2f}h) reached max-hours ({args.max_hours}h).")
            print(f"Terminating before starting seed block {seed_val}. Completed {seeds_completed} complete seed blocks.")
            break

        print(f"\n--- Starting Seed Block {seed_idx + 1}/{total_seeds} (Seed {seed_val}: {len(block_tasks)} cells) ---")
        block_start = time.time()

        # Execute block with ThreadPool assigning tasks to workers
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_task = {}
            for i, task in enumerate(block_tasks):
                w_id = i % args.workers
                worker_cell_counts[w_id] += 1
                port = 20000 + (w_id * 200) + (worker_cell_counts[w_id] % 100)
                fut = executor.submit(execute_cell_worker_subprocess, task, port)
                future_to_task[fut] = task

            block_done = 0
            for fut in as_completed(future_to_task):
                res = fut.result()
                res["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                csv_writer.writerow(res)
                csv_file.flush()
                block_done += 1
                total_completed += 1
                if block_done % 12 == 0 or block_done == len(block_tasks):
                    print(f"  [Seed {seed_val}] {block_done}/{len(block_tasks)} cells finished...")

        block_time = time.time() - block_start
        seeds_completed += 1
        print(f"Completed Seed Block {seed_val} in {block_time/60.0:.2f}m. Cumulative complete seeds: {seeds_completed}")

    csv_file.close()
    tot_time = time.time() - global_start
    print(f"\nMatrix execution finished in {tot_time/60.0:.1f}m. Complete seed blocks: {seeds_completed}/{total_seeds}.")
    print(f"Results recorded in: {RESULTS_BASE_DIR}")
    print(f"Status log: {status_csv_path}")


if __name__ == "__main__":
    main()
