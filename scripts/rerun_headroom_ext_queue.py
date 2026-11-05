"""Re-run cells needed for extended ground-truth queue and re-analyse exp_headroom_recheck_dev.

Policies evaluated:
- hybrid_queue_adaptive (proposed non-oracle policy)
- webster_measured
- webster_recalc
- sumo_actuated
- hybrid_oracle_seeded

Deltas: hybrid_queue_adaptive minus {comparator}
Metrics:
- mean wait (avg_wait_s)
- p95 wait (p95_wait_s)
- extended max queue (gt_ext_max_queue_m)
- approach wait gap (approach_wait_gap_s)
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

EXP_DIR = Path("results/research/exp_headroom_recheck_dev")
NUM_WORKERS = 4
DEV_SEEDS = tuple(range(101, 106))
NETWORK = "marathahalli"

CONDITIONS = [
    ("ramp_peak", "medium"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("surge_shift", "heavy"),
    ("lane_closure", "medium"),
    ("lane_closure", "heavy"),
    ("balanced", "heavy"),
    ("imbalanced_orr", "heavy"),
    ("surge_orr_north", "heavy"),
]

TARGET_POLICIES = [
    "hybrid_queue_adaptive",
    "webster_measured",
    "webster_recalc",
    "sumo_actuated",
    "hybrid_oracle_seeded",
]

COMPARATORS = [
    "webster_measured",
    "webster_recalc",
    "sumo_actuated",
    "hybrid_oracle_seeded",
]

METRICS = [
    ("avg_wait_s", "mean_wait"),
    ("p95_wait_s", "p95_wait"),
    ("gt_ext_max_queue_m", "ext_max_queue"),
    ("approach_wait_gap_s", "approach_wait_gap"),
]


def run_single_cell(task):
    scenario, demand_level, seed, policy, out_dir = task
    out_dir = Path(out_dir)
    # Check if existing metrics already has gt_ext_max_queue_m
    if (out_dir / "metrics.json").exists():
        try:
            with open(out_dir / "metrics.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("gt_ext_max_queue_m") is not None:
                return d
        except Exception:
            pass

    # Run simulation with new queue engine instrumentation
    res = run_simulation(
        scenario=scenario,
        policy=policy,
        seed=seed,
        network=NETWORK,
        demand_level=demand_level,
        out_dir=out_dir,
    )
    return res


def bootstrap_ci(diffs: np.ndarray, n_boot: int = 2000, ci: float = 0.95) -> Tuple[float, float]:
    """Compute bootstrap percentile confidence interval for mean of paired differences."""
    if len(diffs) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(42)
    boot_means = np.empty(n_boot)
    n = len(diffs)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    lower_pct = (1.0 - ci) / 2.0 * 100.0
    upper_pct = (1.0 + ci) / 2.0 * 100.0
    return float(np.percentile(boot_means, lower_pct)), float(np.percentile(boot_means, upper_pct))


def main():
    print("=== Step 1: Executing / Updating Cells for Extended Queue ===")
    tasks = []
    for pol in TARGET_POLICIES:
        for sc, dl in CONDITIONS:
            for s in DEV_SEEDS:
                run_id = f"{NETWORK}_{sc}_{dl}_{pol}_s{s}"
                run_dir = EXP_DIR / run_id
                tasks.append((sc, dl, s, pol, str(run_dir)))

    total_tasks = len(tasks)
    print(f"Total target tasks: {total_tasks} across {len(TARGET_POLICIES)} policies and 9 conditions.")
    t0 = time.time()
    completed = 0
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_map = {executor.submit(run_single_cell, task): task for task in tasks}
        for future in as_completed(future_map):
            completed += 1
            if completed % 25 == 0 or completed == total_tasks:
                elapsed = time.time() - t0
                print(f"[{completed}/{total_tasks}] completed in {elapsed:.1f}s...")

    print("\n=== Step 2: Collecting Raw Runs & Overload Classification ===")
    records = []
    for pol in TARGET_POLICIES:
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
                records.append(d)

    df = pd.DataFrame(records)

    # Classify overload per condition
    overload_info = {}
    print("\n--- Overload Assessment per Condition ---")
    for sc, dl in CONDITIONS:
        cond_df = df[(df["scenario"] == sc) & (df["demand_level"] == dl)]
        mean_unf = cond_df["vehicles_unfinished"].mean()
        max_ext_q = cond_df["gt_ext_max_queue_m"].max()
        max_p95 = cond_df["p95_wait_s"].max()
        
        reasons = []
        if mean_unf > 0.05:
            reasons.append(f"unfinished vehicles ({mean_unf:.1f})")
        # Extended queue boundary check: ramp length extent is 127m-164m
        # Also leg extent was 34.2m
        if max_ext_q >= 60.0:
            reasons.append(f"large queue spillover ({max_ext_q:.1f} m)")
        if max_p95 >= 720.0:
            reasons.append(f"severe delay p95 >= 720s ({max_p95:.1f} s)")

        is_ov = len(reasons) > 0
        overload_info[(sc, dl)] = {
            "is_overloaded": is_ov,
            "reasons": reasons,
            "max_ext_q": max_ext_q,
            "max_p95": max_p95,
        }
        status_str = f"[OVERLOADED: {', '.join(reasons)}]" if is_ov else "[NORMAL]"
        print(f"  {sc} ({dl}): {status_str} (max_ext_q={max_ext_q:.1f}m, max_p95={max_p95:.1f}s)")

    print("\n=== Step 3: Seed-Matched Paired Delta Analysis ===")
    print("Formula: Delta = hybrid_queue_adaptive - Comparator (Negative is Better for all 4 metrics)\n")

    summary_rows = []

    for comp in COMPARATORS:
        print(f"================================================================================")
        print(f"COMPARATOR: {comp}")
        print(f"================================================================================")
        
        # Track pooled deltas across conditions
        pooled_diffs = {m_key: [] for m_key, _ in METRICS}

        for sc, dl in CONDITIONS:
            ov = overload_info[(sc, dl)]
            ov_flag = " [OVLD]" if ov["is_overloaded"] else ""
            
            # Match by seed
            sub_prop = df[(df["scenario"] == sc) & (df["demand_level"] == dl) & (df["policy"] == "hybrid_queue_adaptive")].set_index("seed")
            sub_comp = df[(df["scenario"] == sc) & (df["demand_level"] == dl) & (df["policy"] == comp)].set_index("seed")
            common_seeds = sorted(list(set(sub_prop.index).intersection(sub_comp.index)))
            n = len(common_seeds)

            row_entry = {
                "comparator": comp,
                "scenario": sc,
                "demand_level": dl,
                "is_overloaded": ov["is_overloaded"],
                "n": n,
            }

            print(f"\nCondition: {sc} ({dl}){ov_flag} (n={n})")
            for m_key, m_name in METRICS:
                vals_prop = np.array([sub_prop.loc[s, m_key] for s in common_seeds])
                vals_comp = np.array([sub_comp.loc[s, m_key] for s in common_seeds])
                diffs = vals_prop - vals_comp
                pooled_diffs[m_key].extend(diffs)

                mean_d = float(np.mean(diffs))
                sd_d = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
                ci_low, ci_high = bootstrap_ci(diffs)

                row_entry[f"{m_name}_mean_delta"] = round(mean_d, 2)
                row_entry[f"{m_name}_sd_delta"] = round(sd_d, 2)
                row_entry[f"{m_name}_ci95"] = f"[{ci_low:.2f}, {ci_high:.2f}]"

                print(f"  {m_name:18s}: mean_delta={mean_d:+7.2f} +/- {sd_d:6.2f} | 95% CI: [{ci_low:+7.2f}, {ci_high:+7.2f}]")

            summary_rows.append(row_entry)

        # Print pooled across all 9 conditions
        print(f"\n--- POOLED ACROSS ALL 9 CONDITIONS (n={len(pooled_diffs[METRICS[0][0]])}) for {comp} ---")
        pooled_entry = {
            "comparator": comp,
            "scenario": "POOLED_ALL",
            "demand_level": "ALL",
            "is_overloaded": "MIXED",
            "n": len(pooled_diffs[METRICS[0][0]]),
        }
        for m_key, m_name in METRICS:
            p_diffs = np.array(pooled_diffs[m_key])
            p_mean = float(np.mean(p_diffs))
            p_sd = float(np.std(p_diffs, ddof=1))
            p_ci_low, p_ci_high = bootstrap_ci(p_diffs)
            pooled_entry[f"{m_name}_mean_delta"] = round(p_mean, 2)
            pooled_entry[f"{m_name}_sd_delta"] = round(p_sd, 2)
            pooled_entry[f"{m_name}_ci95"] = f"[{p_ci_low:.2f}, {p_ci_high:.2f}]"
            print(f"  {m_name:18s}: mean_delta={p_mean:+7.2f} +/- {p_sd:6.2f} | 95% CI: [{p_ci_low:+7.2f}, {p_ci_high:+7.2f}]")
        summary_rows.append(pooled_entry)

    summary_df = pd.DataFrame(summary_rows)
    out_csv = EXP_DIR / "paired_deltas_headroom_analysis.csv"
    summary_df.to_csv(out_csv, index=False)
    print(f"\nSaved paired delta summary table to: {out_csv}")


if __name__ == "__main__":
    main()
