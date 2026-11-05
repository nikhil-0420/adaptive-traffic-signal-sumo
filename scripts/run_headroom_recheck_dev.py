"""Task 5: Headroom Recheck on Dev Seeds (101–105).

Conditions (9):
- 6 Non-stationary: ramp_peak (medium, heavy), surge_shift (medium, heavy), lane_closure (medium, heavy)
- 3 Stationary: balanced (heavy), imbalanced_orr (heavy), surge_orr_north (heavy)

Policies (7):
- webster_measured
- webster_recalc
- sumo_actuated
- fixed_matched_cycle
- hybrid_queue_adaptive (new default; or hybrid_r3 if Task 4 KEEP)
- hybrid_oracle_seeded (oracle-seeded legacy hybrid)
- fixed_webster (oracle fixed Webster)

Runs: 7 policies x 9 conditions x 5 seeds = 315 runs.
Directory: results/research/exp_headroom_recheck_dev
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.runner import run_simulation

DEV_SEEDS = tuple(range(101, 106))  # 101..105 (n=5)
NETWORK = "marathahalli"
EXP_DIR = Path("results/research/exp_headroom_recheck_dev")
TASK4_DIR = Path("results/research/exp_ladder_R3_amend_val2")
NUM_WORKERS = 4

CONDITIONS = [
    # 6 Non-stationary conditions
    ("ramp_peak", "medium"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("surge_shift", "heavy"),
    ("lane_closure", "medium"),
    ("lane_closure", "heavy"),
    # 3 Stationary heavy conditions
    ("balanced", "heavy"),
    ("imbalanced_orr", "heavy"),
    ("surge_orr_north", "heavy"),
]

METRICS_REPORT = [
    "avg_wait_s",
    "p95_wait_s",
    "gt_max_queue_m",
    "gt_avg_queue_m",
    "approach_wait_gap_s",
    "switches_per_h",
    "unfinished_vehicles",
    "detector_full_frac",
]


def determine_hybrid_policy() -> str:
    manifest_file = TASK4_DIR / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            m = json.load(f)
        verdict = m.get("verdict", "CUT")
        if verdict == "KEEP":
            print("Task 4 verdict was KEEP -> Using hybrid_r3 for headroom recheck hybrid policy.")
            return "hybrid_r3"
        else:
            print("Task 4 verdict was CUT -> Using hybrid_queue_adaptive for headroom recheck hybrid policy.")
            return "hybrid_queue_adaptive"
    print("Warning: Task 4 manifest not found yet, defaulting to hybrid_queue_adaptive.")
    return "hybrid_queue_adaptive"


def run_cell_worker(task):
    scenario, demand_level, seed, policy, out_dir = task
    out_dir = Path(out_dir)
    if (out_dir / "metrics.json").exists():
        with open(out_dir / "metrics.json", "r", encoding="utf-8") as f:
            return json.load(f)

    t0 = time.time()
    res = run_simulation(
        scenario=scenario,
        policy=policy,
        seed=seed,
        network=NETWORK,
        demand_level=demand_level,
        out_dir=out_dir,
    )
    res["elapsed_wallclock_s"] = round(time.time() - t0, 1)
    return res


def execute_matrix(policies: List[str], max_workers: int = NUM_WORKERS):
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for pol in policies:
        for sc, dl in CONDITIONS:
            for s in DEV_SEEDS:
                run_id = f"{NETWORK}_{sc}_{dl}_{pol}_s{s}"
                run_dir = EXP_DIR / run_id
                tasks.append((sc, dl, s, pol, str(run_dir)))

    total_tasks = len(tasks)
    print(f"Total simulations to execute: {total_tasks} across {len(policies)} policies, 9 conditions, 5 seeds.")
    completed = 0
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(run_cell_worker, task): task for task in tasks}
        for future in as_completed(future_map):
            completed += 1
            if completed % 25 == 0 or completed == total_tasks:
                elapsed = time.time() - t_start
                rate = completed / max(1.0, elapsed)
                remaining = (total_tasks - completed) / max(0.01, rate)
                print(f"[{completed}/{total_tasks}] runs finished ({rate:.1f} runs/s, ~{remaining:.0f}s remaining)...")


def analyze_headroom(policies: List[str]):
    print("\n--- Analyzing Headroom Recheck Results ---")
    records = []
    for pol in policies:
        for sc, dl in CONDITIONS:
            for s in DEV_SEEDS:
                run_id = f"{NETWORK}_{sc}_{dl}_{pol}_s{s}"
                p_metrics = EXP_DIR / run_id / "metrics.json"
                with open(p_metrics, "r", encoding="utf-8") as f:
                    d = json.load(f)
                d["policy"] = pol
                d["scenario"] = sc
                d["demand_level"] = dl
                d["seed"] = s
                cycles = d.get("cycles", 0)
                d["switches_per_h"] = round(cycles * 2.0 / (C.SIM.demand_duration_s / 3600.0), 1)
                d["unfinished_vehicles"] = d.get("vehicles_unfinished", 0)
                records.append(d)

    df = pd.DataFrame(records)
    df.to_csv(EXP_DIR / "raw_runs.csv", index=False)

    # Compute mean and SD per condition and policy
    grouped = df.groupby(["scenario", "demand_level", "policy"])[METRICS_REPORT]
    means = grouped.mean().rename(columns={c: f"{c}_mean" for c in METRICS_REPORT})
    sds = grouped.std().rename(columns={c: f"{c}_sd" for c in METRICS_REPORT})
    summary_df = pd.concat([means, sds], axis=1).reset_index()
    summary_df.to_csv(EXP_DIR / "condition_policy_summary.csv", index=False)

    # Measured policies: webster_measured, webster_recalc, sumo_actuated, and the hybrid policy
    measured_policies = [p for p in policies if p in ("webster_measured", "webster_recalc", "sumo_actuated", "hybrid_queue_adaptive", "hybrid_r3")]

    overloaded_conditions = []
    separation_findings = []

    print("\n=== PER CONDITION HEADROOM & SEPARATION ANALYSIS ===")
    for sc, dl in CONDITIONS:
        cond_df = df[(df["scenario"] == sc) & (df["demand_level"] == dl)]
        print(f"\nCondition: {sc} ({dl})")

        # Check overload criteria:
        # 1. unfinished vehicles > 0
        # 2. queue beyond GT covered extent (~34.2m)
        # 3. p95 wait > 40% of run horizon (40% of 1800s = 720s)
        mean_unf = cond_df["unfinished_vehicles"].mean()
        max_gt_q = cond_df["gt_max_queue_m"].max()
        max_p95 = cond_df["p95_wait_s"].max()

        overload_reasons = []
        if mean_unf > 0.05:
            overload_reasons.append(f"unfinished vehicles ({mean_unf:.1f})")
        if max_gt_q >= 34.0:
            overload_reasons.append(f"queue near/at covered extent limit ({max_gt_q:.1f} m)")
        if max_p95 >= 720.0:
            overload_reasons.append(f"p95 wait > 720s ({max_p95:.1f} s)")

        is_overloaded = len(overload_reasons) > 0
        if is_overloaded:
            overloaded_conditions.append((sc, dl, ", ".join(overload_reasons)))
            print(f"  [FLAGGED OVERLOADED]: {', '.join(overload_reasons)} (differences compressed)")

        # Measured-information policies separation check
        # Does any measured policy differ from others by more than the seed SD?
        meas_df = cond_df[cond_df["policy"].isin(measured_policies)]
        pol_means = meas_df.groupby("policy")["avg_wait_s"].mean()
        pol_sds = meas_df.groupby("policy")["avg_wait_s"].std()

        min_pol = pol_means.idxmin()
        max_pol = pol_means.idxmax()
        spread = pol_means.max() - pol_means.min()
        pooled_sd = float(pol_sds.mean())

        separates = spread > pooled_sd
        sep_note = f"Spread={spread:.2f}s vs avg seed SD={pooled_sd:.2f}s -> {'SEPARATES' if separates else 'TIES WITHIN SD'}"
        print(f"  Measured policies wait spread: {sep_note}")
        for pol in measured_policies:
            print(f"    - {pol:22s}: wait={pol_means[pol]:.2f} +/- {pol_sds[pol]:.2f} s | p95={meas_df[meas_df['policy']==pol]['p95_wait_s'].mean():.1f} s | gt_max_q={meas_df[meas_df['policy']==pol]['gt_max_queue_m'].mean():.1f} m | det_full={meas_df[meas_df['policy']==pol]['detector_full_frac'].mean()*100:.1f}%")

        separation_findings.append({
            "scenario": sc,
            "demand_level": dl,
            "is_overloaded": is_overloaded,
            "overload_reasons": overload_reasons,
            "spread_wait_s": round(spread, 2),
            "pooled_sd_wait_s": round(pooled_sd, 2),
            "separates": bool(separates),
            "best_measured": str(min_pol),
            "worst_measured": str(max_pol),
        })

    manifest = {
        "experiment_id": "exp_headroom_recheck_dev",
        "description": "Task 5 Headroom Recheck on Dev Seeds (101-105)",
        "policies": policies,
        "n_seeds": len(DEV_SEEDS),
        "seeds": list(DEV_SEEDS),
        "conditions": CONDITIONS,
        "overloaded_conditions": overloaded_conditions,
        "separation_findings": separation_findings,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(EXP_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== HEADROOM RECHECK COMPLETE ===")
    return manifest


def main():
    hybrid_pol = determine_hybrid_policy()
    policies = [
        "webster_measured",
        "webster_recalc",
        "sumo_actuated",
        "fixed_matched_cycle",
        hybrid_pol,
        "hybrid_oracle_seeded",
        "fixed_webster",
    ]
    execute_matrix(policies)
    analyze_headroom(policies)


if __name__ == "__main__":
    main()
