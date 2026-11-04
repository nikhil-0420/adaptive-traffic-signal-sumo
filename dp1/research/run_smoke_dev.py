"""Phase 13: Dev Smoke Run & Automated Verification Engine.

Executes all final-matrix policies (10 main + 3 ablation) across all 18 conditions
on dev seeds 101 and 102 in results/research/exp_final_smoke_dev.
Verifies:
- All cells complete with no NaN/Inf
- Route hash equality across policies per (scenario, level, seed)
- Zero safety invariant violations (phase sequences and clearance durations)
- Unfinished vehicles count
- Saturated detector fraction
- Runtime statistics (median and p95 per policy)
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.runner import run_simulation
from dp1.controllers import POLICIES

NETWORK = "marathahalli"
NUM_WORKERS = 8
DEV_SEEDS = (101, 102)

CONDITIONS = [
    # 12 stationary conditions
    ("balanced", "low"),
    ("balanced", "medium"),
    ("balanced", "heavy"),
    ("imbalanced_orr", "low"),
    ("imbalanced_orr", "medium"),
    ("imbalanced_orr", "heavy"),
    ("imbalanced_varthur", "low"),
    ("imbalanced_varthur", "medium"),
    ("imbalanced_varthur", "heavy"),
    ("surge_orr_north", "low"),
    ("surge_orr_north", "medium"),
    ("surge_orr_north", "heavy"),
    # 6 non-stationary conditions
    ("ramp_peak", "medium"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("surge_shift", "heavy"),
    ("lane_closure", "medium"),
    ("lane_closure", "heavy"),
]

MAIN_POLICIES = [
    "fixed",
    "fixed_matched_cycle",
    "webster_measured",
    "webster_recalc",
    "sumo_actuated",
    "adaptive",
    "pressure",
    "queue_extension",
    "rl_dqn",
    "hybrid_queue_adaptive_proj",
]

ABLATION_POLICIES = [
    "hybrid_queue_adaptive",
    "hybrid_r3",
    "hybrid_oracle_seeded",
]

ALL_SMOKE_POLICIES = MAIN_POLICIES + ABLATION_POLICIES

SMOKE_OUT_DIR = Path("results/research/exp_final_smoke_dev")


def run_single_smoke_cell(task: Tuple) -> Dict[str, Any]:
    scenario, demand_level, seed, policy, out_dir_str = task
    out_dir = Path(out_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_file = out_dir / "metrics.json"
    ts_file = out_dir / "timeseries.csv"

    t0 = time.time()
    try:
        # Check if already completed
        if metrics_file.exists() and ts_file.exists():
            with open(metrics_file, "r", encoding="utf-8") as f:
                res = json.load(f)
            elapsed = res.get("wall_clock_s") or (time.time() - t0)
        else:
            res = run_simulation(
                scenario=scenario,
                policy=policy,
                seed=seed,
                network=NETWORK,
                demand_level=demand_level,
                out_dir=out_dir,
            )
            elapsed = time.time() - t0
            res["wall_clock_s"] = elapsed
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)

        res["scenario"] = scenario
        res["demand_level"] = demand_level
        res["seed"] = seed
        res["policy"] = policy
        res["run_dir"] = str(out_dir)
        res["wall_clock_s"] = elapsed
        res["status"] = "SUCCESS"
        return res
    except Exception as exc:
        elapsed = time.time() - t0
        return {
            "status": "FAILED",
            "scenario": scenario,
            "demand_level": demand_level,
            "seed": seed,
            "policy": policy,
            "run_dir": str(out_dir),
            "wall_clock_s": elapsed,
            "error": str(exc),
        }


def verify_signal_safety(ts_path: Path) -> Tuple[bool, List[str]]:
    """Verify safety invariants on timeseries: GREEN -> YELLOW -> ALL_RED -> GREEN."""
    errors = []
    if not ts_path.exists():
        return False, ["timeseries.csv missing"]

    try:
        df = pd.read_csv(ts_path)
    except Exception as e:
        return False, [f"Failed to read timeseries: {e}"]

    if "phase" not in df.columns:
        return False, ["'phase' column missing from timeseries"]

    # Deduplicate consecutive identical phases to get transition sequence
    transitions = df.loc[df["phase"].ne(df["phase"].shift()), "phase"].tolist()
    valid_transitions = {
        ("GREEN", "YELLOW"),
        ("YELLOW", "ALL_RED"),
        ("ALL_RED", "GREEN"),
    }
    for p_prev, p_next in zip(transitions, transitions[1:]):
        if (p_prev, p_next) not in valid_transitions:
            errors.append(f"Invalid phase switch: {p_prev} -> {p_next}")

    # Check yellow and all-red durations
    run_id = df["phase"].ne(df["phase"].shift()).cumsum()
    durations = df.groupby(run_id).agg(phase=("phase", "first"), n=("t", "size"))
    inner = durations.iloc[1:-1]

    yellow_lengths = inner[inner["phase"] == "YELLOW"]["n"]
    if not (yellow_lengths == C.TIMING.yellow_s).all():
        bad = yellow_lengths[yellow_lengths != C.TIMING.yellow_s].tolist()
        errors.append(f"Non-standard yellow duration found: {bad} (expected {C.TIMING.yellow_s}s)")

    all_red_lengths = inner[inner["phase"] == "ALL_RED"]["n"]
    if not (all_red_lengths == C.TIMING.all_red_s).all():
        bad = all_red_lengths[all_red_lengths != C.TIMING.all_red_s].tolist()
        errors.append(f"Non-standard all-red duration found: {bad} (expected {C.TIMING.all_red_s}s)")

    return len(errors) == 0, errors


def main():
    t_pipeline_start = time.time()
    SMOKE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=====================================================================")
    print("PHASE 13: FINAL MATRIX SMOKE RUN (DEV SEEDS 101, 102)")
    print(f"Policies ({len(ALL_SMOKE_POLICIES)}): {ALL_SMOKE_POLICIES}")
    print(f"Conditions ({len(CONDITIONS)}): 12 stationary + 6 non-stationary")
    print(f"Seeds: {DEV_SEEDS} | Parallel Workers: {NUM_WORKERS}")
    print("=====================================================================")

    tasks = []
    for sc, dl in CONDITIONS:
        for s in DEV_SEEDS:
            for pol in ALL_SMOKE_POLICIES:
                cell_id = f"{NETWORK}_{sc}_{dl}_{pol}_s{s}"
                run_dir = SMOKE_OUT_DIR / cell_id
                tasks.append((sc, dl, s, pol, str(run_dir)))

    total_tasks = len(tasks)
    print(f"Total smoke cells to execute: {total_tasks}")

    results = []
    completed = 0
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_map = {executor.submit(run_single_smoke_cell, t): t for t in tasks}
        for future in as_completed(future_map):
            completed += 1
            res = future.result()
            results.append(res)
            if completed % 25 == 0 or completed == total_tasks:
                print(f"  [Progress] {completed}/{total_tasks} cells completed ({(completed/total_tasks)*100:.1f}%)...")

    # -------------------------------------------------------------------------
    # Automated Verification Suite
    # -------------------------------------------------------------------------
    print("\n=== Executing Automated Verification Suite ===")
    verification_errors = []

    # 1. Completion & NaN/Inf Check
    failed_cells = [r for r in results if r.get("status") != "SUCCESS"]
    if failed_cells:
        verification_errors.append(f"{len(failed_cells)} cells failed simulation execution.")

    nan_inf_cells = []
    for r in results:
        if r.get("status") == "SUCCESS":
            for k in ["avg_wait_s", "p95_wait_s", "avg_queue_m", "completion_rate", "approach_wait_gap_s"]:
                val = r.get(k)
                if val is None or math.isnan(val) or math.isinf(val):
                    nan_inf_cells.append((r["policy"], r["scenario"], r["demand_level"], r["seed"], k, val))
    if nan_inf_cells:
        verification_errors.append(f"{len(nan_inf_cells)} NaN/Inf metric instances detected.")

    # 2. Route Hash Consistency Check
    route_hash_map: Dict[Tuple[str, str, int], Dict[str, str]] = {}
    for r in results:
        if r.get("status") == "SUCCESS":
            key = (r["scenario"], r["demand_level"], r["seed"])
            route_hash_map.setdefault(key, {})[r["policy"]] = r.get("route_hash")

    route_mismatches = []
    for key, pol_hashes in route_hash_map.items():
        unique_hashes = set(pol_hashes.values())
        if len(unique_hashes) > 1:
            route_mismatches.append((key, pol_hashes))
    if route_mismatches:
        verification_errors.append(f"Route hash mismatches detected across policies in {len(route_mismatches)} conditions.")

    # 3. Safety Invariant Trace Verification
    safety_violations = []
    for r in results:
        if r.get("status") == "SUCCESS":
            ts_path = Path(r["run_dir"]) / "timeseries.csv"
            safe, errs = verify_signal_safety(ts_path)
            if not safe:
                safety_violations.append((r["policy"], r["scenario"], r["demand_level"], r["seed"], errs))
    if safety_violations:
        verification_errors.append(f"Safety violations found in {len(safety_violations)} signal traces.")

    # 4. Runtime Statistics per Policy
    policy_runtimes = {}
    for r in results:
        pol = r["policy"]
        if "wall_clock_s" in r:
            policy_runtimes.setdefault(pol, []).append(r["wall_clock_s"])

    perf_summary = []
    for pol in ALL_SMOKE_POLICIES:
        times = policy_runtimes.get(pol, [])
        if times:
            perf_summary.append({
                "policy": pol,
                "n_runs": len(times),
                "median_s": round(float(np.median(times)), 2),
                "p95_s": round(float(np.percentile(times, 95)), 2),
                "mean_s": round(float(np.mean(times)), 2),
                "min_s": round(float(np.min(times)), 2),
                "max_s": round(float(np.max(times)), 2),
            })

    # 5. Saturated & Unfinished Summary
    summary_rows = []
    for r in results:
        if r.get("status") == "SUCCESS":
            summary_rows.append({
                "scenario": r["scenario"],
                "demand_level": r["demand_level"],
                "seed": r["seed"],
                "policy": r["policy"],
                "completion_rate": r.get("completion_rate", 1.0),
                "unfinished_vehicles": r.get("vehicles_unfinished", 0),
                "detector_full_frac": round(r.get("detector_full_frac", 0.0), 4),
                "avg_wait_s": round(r.get("avg_wait_s", 0.0), 2),
                "p95_wait_s": round(r.get("p95_wait_s", 0.0), 2),
                "approach_wait_gap_s": round(r.get("approach_wait_gap_s", 0.0), 2),
                "wall_clock_s": round(r.get("wall_clock_s", 0.0), 2),
                "route_hash": r.get("route_hash", "")[:8],
            })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(SMOKE_OUT_DIR / "smoke_cells.csv", index=False)
    pd.DataFrame(perf_summary).to_csv(SMOKE_OUT_DIR / "policy_performance.csv", index=False)

    grand_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_cells": total_tasks,
        "completed_cells": len([r for r in results if r.get("status") == "SUCCESS"]),
        "failed_cells": len(failed_cells),
        "nan_inf_count": len(nan_inf_cells),
        "route_hash_match": len(route_mismatches) == 0,
        "zero_safety_violations": len(safety_violations) == 0,
        "verification_passed": len(verification_errors) == 0,
        "verification_errors": verification_errors,
        "performance_by_policy": perf_summary,
    }

    with open(SMOKE_OUT_DIR / "smoke_verification_report.json", "w", encoding="utf-8") as f:
        json.dump(grand_report, f, indent=2)

    total_time_min = (time.time() - t_pipeline_start) / 60.0

    print("\n=================== SMOKE VERIFICATION REPORT ===================")
    print(f"Total cells executed: {total_tasks} across {len(ALL_SMOKE_POLICIES)} policies")
    print(f"Completed cells:      {grand_report['completed_cells']} / {total_tasks} ({(grand_report['completed_cells']/total_tasks)*100:.1f}%)")
    print(f"Failed cells:         {len(failed_cells)}")
    print(f"NaN / Inf instances:  {len(nan_inf_cells)}")
    print(f"Route Hash Match:     {'PASS (100% Identical demand across policies)' if len(route_mismatches)==0 else 'FAIL'}")
    print(f"Safety Invariants:    {'PASS (Zero transition / clearance violations)' if len(safety_violations)==0 else 'FAIL'}")
    print("-----------------------------------------------------------------")
    print("Policy Runtimes (Wall Clock Seconds per Simulation):")
    for ps in perf_summary:
        print(f"  {ps['policy']:<26}: Median={ps['median_s']}s, P95={ps['p95_s']}s, Mean={ps['mean_s']}s")
    print("-----------------------------------------------------------------")
    print(f"Overall Smoke Status: {'>> PASS <<' if grand_report['verification_passed'] else '>> FAIL <<'}")
    print(f"Total Execution Time: {total_time_min:.2f} minutes")
    print("=================================================================\n")


if __name__ == "__main__":
    main()
