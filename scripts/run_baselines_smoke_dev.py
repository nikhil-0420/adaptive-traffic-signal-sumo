"""Smoke test execution script for Phase 9 reference baselines.

Matrix:
- Scenarios (3): ramp_peak, surge_shift, lane_closure
- Demand levels (2): medium, heavy
- Dev seeds (2): 101, 102
- Policies (7):
    1. webster_measured
    2. webster_recalc
    3. fixed_matched_cycle
    4. sumo_actuated
    5. fixed
    6. fixed_webster
    7. hybrid_queue_adaptive
Total: 3 * 2 * 2 * 7 = 84 runs.
Output directory: results/research/exp_baselines_smoke_dev
"""
import concurrent.futures
import json
import math
import os
import sys
import time
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dp1.runner import run_simulation
from dp1 import config as C

SCENARIOS = ["ramp_peak", "surge_shift", "lane_closure"]
DEMAND_LEVELS = ["medium", "heavy"]
SEEDS = [101, 102]
POLICIES = [
    "webster_measured",
    "webster_recalc",
    "fixed_matched_cycle",
    "sumo_actuated",
    "fixed",
    "fixed_webster",
    "hybrid_queue_adaptive",
]
EXP_DIR = C.RESULTS_DIR / "research" / "exp_baselines_smoke_dev"


def run_single_cell(args):
    scenario, demand_level, seed, policy = args
    run_id = f"marathahalli_{scenario}_{demand_level}_{policy}_s{seed}"
    out_dir = EXP_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        metrics = run_simulation(
            scenario=scenario,
            policy=policy,
            seed=seed,
            network="marathahalli",
            demand_level=demand_level,
            out_dir=out_dir,
        )
        elapsed = round(time.time() - t0, 1)
        return {
            "run_id": run_id,
            "scenario": scenario,
            "demand_level": demand_level,
            "seed": seed,
            "policy": policy,
            "status": "completed",
            "elapsed_s": elapsed,
            "route_hash": metrics.get("route_hash"),
            "n_vehicles": metrics.get("vehicles_total"),
            "finished_vehicles": metrics.get("vehicles_arrived"),
            "unfinished_vehicles": metrics.get("vehicles_unfinished", 0),
            "mean_waiting_s": metrics.get("avg_wait_s"),
            "max_queue_m": metrics.get("max_queue_m"),
            "error": None,
        }
    except Exception as exc:
        elapsed = round(time.time() - t0, 1)
        return {
            "run_id": run_id,
            "scenario": scenario,
            "demand_level": demand_level,
            "seed": seed,
            "policy": policy,
            "status": "failed",
            "elapsed_s": elapsed,
            "route_hash": None,
            "n_vehicles": None,
            "finished_vehicles": None,
            "unfinished_vehicles": None,
            "mean_waiting_s": None,
            "max_queue_m": None,
            "error": str(exc),
        }


def main():
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for sc in SCENARIOS:
        for dl in DEMAND_LEVELS:
            for s in SEEDS:
                for p in POLICIES:
                    tasks.append((sc, dl, s, p))

    print(f"[Phase 9 Smoke Test] Running {len(tasks)} runs across 7 policies with 4 parallel processes...")
    t_start = time.time()
    results = []

    # Using 4 parallel worker processes for clean TraCI isolation
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_single_cell, arg): arg for arg in tasks}
        completed_count = 0
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            results.append(res)
            completed_count += 1
            if completed_count % 7 == 0 or completed_count == len(tasks):
                print(f"[{completed_count:2d}/{len(tasks)}] {res['policy']} | {res['scenario']} | {res['demand_level']} | s{res['seed']} -> {res['status']} ({res['elapsed_s']}s)")

    total_time = round(time.time() - t_start, 1)
    df = pd.DataFrame(results)
    csv_path = EXP_DIR / "smoke_summary.csv"
    df.to_csv(csv_path, index=False)

    # Verification checks
    completed_runs = (df.status == "completed").sum()
    failed_runs = (df.status == "failed").sum()

    # Route hash consistency: for each (scenario, demand_level, seed), route_hash must be identical across policies
    hash_groups = df.groupby(["scenario", "demand_level", "seed"])["route_hash"].nunique()
    hash_mismatches = (hash_groups != 1).sum()

    # NaN checks on completed runs
    nan_waiting = df[df.status == "completed"]["mean_waiting_s"].isna().sum()
    nan_queues = df[df.status == "completed"]["max_queue_m"].isna().sum()

    total_unfinished = int(df[df.status == "completed"]["unfinished_vehicles"].sum())

    summary = {
        "total_runs": len(tasks),
        "completed_runs": int(completed_runs),
        "failed_runs": int(failed_runs),
        "total_wallclock_s": total_time,
        "route_hash_conditions_checked": len(hash_groups),
        "route_hash_mismatches": int(hash_mismatches),
        "nan_mean_waiting_count": int(nan_waiting),
        "nan_max_queue_count": int(nan_queues),
        "total_unfinished_vehicles": total_unfinished,
    }

    with open(EXP_DIR / "smoke_audit.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("PHASE 9 SMOKE TEST AUDIT SUMMARY:")
    print(json.dumps(summary, indent=2))
    print(f"Results saved to: {EXP_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
