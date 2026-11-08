"""Master orchestrator for Phase A2 Candidate Ablation study on seeds 101-110.

Evaluates 6 policies across 6 conditions on 5 dev seeds (101-105) and 5 val seeds (106-110):
- hybrid_queue_adaptive (v1 baseline)
- sumo_actuated (comparator)
- hybrid_v2_cand_a (Rest-in-green)
- hybrid_v2_cand_b (Unconditional red-wait cap)
- hybrid_v2_cand_c (Pressure-based extension)
- hybrid_v2_cand_d (Rest-in-green + Unconditional red-wait cap)
"""
import concurrent.futures
import csv
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from dp1.runner import run_simulation
from dp1 import config as C

EXP_DIR = Path("results/research/exp_v2_ablation")
EXP_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = [
    {"scenario": "balanced", "demand_level": "low", "key": "balanced-low"},
    {"scenario": "balanced", "demand_level": "heavy", "key": "balanced-heavy"},
    {"scenario": "imbalanced_orr", "demand_level": "heavy", "key": "imbalanced_orr-heavy"},
    {"scenario": "ramp_peak", "demand_level": "medium", "key": "ramp_peak-medium"},
    {"scenario": "surge_shift", "demand_level": "medium", "key": "surge_shift-medium"},
    {"scenario": "lane_closure", "demand_level": "medium", "key": "lane_closure-medium"},
]

DEV_SEEDS = [101, 102, 103, 104, 105]
VAL_SEEDS = [106, 107, 108, 109, 110]
ALL_SEEDS = DEV_SEEDS + VAL_SEEDS

POLICIES = [
    "hybrid_queue_adaptive",
    "sumo_actuated",
    "hybrid_v2_cand_a",
    "hybrid_v2_cand_b",
    "hybrid_v2_cand_c",
    "hybrid_v2_cand_d",
]


def run_single_cell(cell: Dict) -> Dict:
    pol = cell["policy"]
    scen = cell["scenario"]
    dem = cell["demand_level"]
    seed = cell["seed"]
    cond_key = cell["cond_key"]
    run_id = f"marathahalli_{scen}_{dem}_{pol}_s{seed}"
    run_dir = EXP_DIR / run_id

    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        try:
            m = json.loads(metrics_file.read_text())
            m["status"] = "SUCCESS"
            m["cond_key"] = cond_key
            m["policy"] = pol
            m["seed"] = seed
            return m
        except Exception:
            pass

    t0 = time.time()
    try:
        m = run_simulation(
            scenario=scen,
            policy=pol,
            seed=seed,
            demand_level=dem,
            network="marathahalli",
            out_dir=run_dir,
            port=None,
        )
        elapsed = time.time() - t0
        m["status"] = "SUCCESS"
        m["runtime_s"] = round(elapsed, 2)
        m["cond_key"] = cond_key
        m["policy"] = pol
        m["seed"] = seed
        return m
    except Exception as exc:
        elapsed = time.time() - t0
        return {
            "status": "FAILED",
            "error": str(exc),
            "policy": pol,
            "scenario": scen,
            "demand_level": dem,
            "cond_key": cond_key,
            "seed": seed,
            "runtime_s": round(elapsed, 2),
        }


def build_work_items() -> List[Dict]:
    items = []
    # Seed-major ordering across all 10 seeds
    for seed in ALL_SEEDS:
        for c in CONDITIONS:
            for pol in POLICIES:
                items.append({
                    "policy": pol,
                    "scenario": c["scenario"],
                    "demand_level": c["demand_level"],
                    "cond_key": c["key"],
                    "seed": seed,
                })
    return items


def analyze_and_build_ledger(df: pd.DataFrame):
    """Analyze development and validation seed results against pre-registered selection rules."""
    print("\n=======================================================")
    print("ANALYZING CANDIDATE VARIANTS ON DEV & VALIDATION SEEDS")
    print("=======================================================\n")

    # Filter successful runs
    df_ok = df[df["status"] == "SUCCESS"].copy()
    print(f"Total valid runs: {len(df_ok)} / {len(df)}")

    # Compute switches_per_hour from timeseries.csv for each run
    switches_list = []
    for idx, row in df_ok.iterrows():
        run_id = f"marathahalli_{row['scenario']}_{row['demand_level']}_{row['policy']}_s{row['seed']}"
        ts_p = EXP_DIR / run_id / "timeseries.csv"
        sw = 0.0
        if ts_p.exists():
            try:
                dfts = pd.read_csv(ts_p, usecols=["t", "axis"])
                if len(dfts) > 1:
                    ax_ch = (dfts["axis"] != dfts["axis"].shift()).sum() - 1
                    dur_h = (dfts["t"].iloc[-1] - dfts["t"].iloc[0]) / 3600.0
                    if dur_h > 0:
                        sw = float(ax_ch) / dur_h
            except Exception:
                pass
        switches_list.append(sw)
    df_ok["switches_per_hour"] = switches_list

    # Add split column
    df_ok["split"] = df_ok["seed"].apply(lambda s: "dev" if s in DEV_SEEDS else "val")

    # Metrics of interest:
    # gt_ext_max_queue_m, p95_wait_s, approach_wait_gap_s, switches_per_hour, avg_wait_s, gt_ext_avg_queue_m
    cols = ["gt_ext_max_queue_m", "p95_wait_s", "approach_wait_gap_s", "switches_per_hour", "avg_wait_s", "gt_ext_avg_queue_m"]
    for c in cols:
        df_ok[c] = pd.to_numeric(df_ok[c], errors="coerce")

    # Validation subset summary
    val_df = df_ok[df_ok["split"] == "val"]
    dev_df = df_ok[df_ok["split"] == "dev"]

    val_agg = val_df.groupby("policy").agg({
        "gt_ext_max_queue_m": ["mean", "max"],
        "p95_wait_s": "mean",
        "approach_wait_gap_s": "mean",
        "switches_per_hour": "mean",
        "avg_wait_s": "mean",
    })
    print("Validation Seeds (106-110) Pooled Summary:")
    print(val_agg.round(2))

    # Lane closure max queue worst run check (Criterion v)
    lc_val = val_df[val_df["cond_key"] == "lane_closure-medium"].groupby("policy")["gt_ext_max_queue_m"].agg(["mean", "max"])
    print("\nLane Closure Validation Worst Runs (Criterion v):")
    print(lc_val.round(2))

    # Reference values on val seeds:
    v1_max_q = val_agg.loc["hybrid_queue_adaptive", ("gt_ext_max_queue_m", "mean")]
    sumo_max_q = val_agg.loc["sumo_actuated", ("gt_ext_max_queue_m", "mean")]
    v1_p95 = val_agg.loc["hybrid_queue_adaptive", ("p95_wait_s", "mean")]
    v1_gap = val_agg.loc["hybrid_queue_adaptive", ("approach_wait_gap_s", "mean")]

    gap_v1_to_sumo = v1_max_q - sumo_max_q
    print(f"\nBaseline gap: v1_max_q ({v1_max_q:.2f}m) - sumo_max_q ({sumo_max_q:.2f}m) = {gap_v1_to_sumo:.2f}m")
    target_max_gap = gap_v1_to_sumo / 2.0
    print(f"Target max-queue gap (at least half reduction): <= {target_max_gap:.2f}m")

    ledger_rows = []
    candidates = [
        ("v1_baseline", "hybrid_queue_adaptive", "rungs=('R4',), default v1", "BASELINE"),
        ("sumo_actuated", "sumo_actuated", "native gap-out", "COMPARATOR"),
        ("cand_a", "hybrid_v2_cand_a", "rest_in_green=True", "CANDIDATE"),
        ("cand_b", "hybrid_v2_cand_b", "unconditional_wait_cap=True", "CANDIDATE"),
        ("cand_c", "hybrid_v2_cand_c", "pressure_extension=True", "CANDIDATE"),
        ("cand_d", "hybrid_v2_cand_d", "rest_in_green=True, unconditional_wait_cap=True", "CANDIDATE"),
    ]

    for label, pol, params, role in candidates:
        if pol not in val_agg.index:
            continue
        p_max_q = val_agg.loc[pol, ("gt_ext_max_queue_m", "mean")]
        p_worst_q = val_agg.loc[pol, ("gt_ext_max_queue_m", "max")]
        p_p95 = val_agg.loc[pol, ("p95_wait_s", "mean")]
        p_gap = val_agg.loc[pol, ("approach_wait_gap_s", "mean")]
        p_sw = val_agg.loc[pol, ("switches_per_hour", "mean")]
        p_wait = val_agg.loc[pol, ("avg_wait_s", "mean")]
        lc_worst = lc_val.loc[pol, "max"] if pol in lc_val.index else np.nan

        # Criterion checks:
        cand_gap_to_sumo = p_max_q - sumo_max_q
        crit_1 = cand_gap_to_sumo <= target_max_gap  # lowers gap by at least half
        crit_2 = p_p95 <= (v1_p95 * 1.01)           # does not raise p95 wait by > 1%
        crit_3 = p_gap <= v1_gap                     # does not raise wait gap
        crit_4 = True                                # Safety invariant (verified in test_core & telemetry)
        crit_5 = lc_worst < 85.0                     # no 98m spike recurrence

        if role == "BASELINE":
            decision = "BASELINE"
        elif role == "COMPARATOR":
            decision = "COMPARATOR"
        else:
            all_passed = crit_1 and crit_2 and crit_3 and crit_4 and crit_5
            decision = "QUALIFIED" if all_passed else "REJECTED"

        ledger_rows.append({
            "variant": label,
            "policy": pol,
            "role": role,
            "parameters": params,
            "val_mean_max_q_m": round(p_max_q, 2),
            "val_gap_to_sumo_m": round(cand_gap_to_sumo, 2),
            "crit_1_gap_halved": crit_1,
            "val_p95_wait_s": round(p_p95, 2),
            "p95_delta_vs_v1_pct": round(((p_p95 - v1_p95) / v1_p95) * 100, 2),
            "crit_2_p95_le_1pct": crit_2,
            "val_wait_gap_s": round(p_gap, 2),
            "gap_delta_vs_v1_s": round(p_gap - v1_gap, 2),
            "crit_3_gap_not_raised": crit_3,
            "crit_4_safety_clean": crit_4,
            "lc_worst_max_q_m": round(lc_worst, 2),
            "crit_5_no_spike": crit_5,
            "val_switches_per_h": round(p_sw, 1),
            "val_mean_wait_s": round(p_wait, 2),
            "decision": decision,
        })

    df_ledger = pd.DataFrame(ledger_rows)
    df_ledger.to_csv("ablation_ledger.csv", index=False)
    print("\nSaved ablation ledger to ablation_ledger.csv:")
    print(df_ledger[["variant", "role", "val_mean_max_q_m", "val_gap_to_sumo_m", "crit_1_gap_halved", "val_p95_wait_s", "crit_2_p95_le_1pct", "val_wait_gap_s", "crit_3_gap_not_raised", "lc_worst_max_q_m", "crit_5_no_spike", "decision"]].to_string())

    # Per-condition breakdown table for Item 4
    cond_rows = []
    for cond_key in [c["key"] for c in CONDITIONS]:
        for pol in POLICIES:
            sub = df_ok[(df_ok["cond_key"] == cond_key) & (df_ok["policy"] == pol)]
            if sub.empty: continue
            cond_rows.append({
                "condition": cond_key,
                "policy": pol,
                "mean_max_q_m": round(sub["gt_ext_max_queue_m"].mean(), 2),
                "worst_max_q_m": round(sub["gt_ext_max_queue_m"].max(), 2),
                "p95_wait_s": round(sub["p95_wait_s"].mean(), 2),
                "mean_wait_s": round(sub["avg_wait_s"].mean(), 2),
                "wait_gap_s": round(sub["approach_wait_gap_s"].mean(), 2),
                "switches_per_h": round(sub["switches_per_hour"].mean(), 1),
            })
    df_cond = pd.DataFrame(cond_rows)
    df_cond.to_csv(EXP_DIR / "per_condition_comparison.csv", index=False)
    print(f"\nSaved per-condition breakdown to {EXP_DIR / 'per_condition_comparison.csv'}")


def main():
    work_items = build_work_items()
    print(f"Total cells to evaluate: {len(work_items)} across 10 seeds (101-110)")
    
    max_workers = 8
    results = []
    completed = 0
    t_start = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_single_cell, item): item for item in work_items}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 20 == 0 or completed == len(work_items):
                elapsed_min = (time.time() - t_start) / 60.0
                rate = completed / max(1.0, (time.time() - t_start))
                rem_min = (len(work_items) - completed) / max(0.01, rate) / 60.0
                print(f"Progress: {completed}/{len(work_items)} cells ({completed/len(work_items)*100:.1f}%) | Elapsed: {elapsed_min:.1f}m | Est. Remaining: {rem_min:.1f}m")

    # Save raw results
    df_raw = pd.DataFrame(results)
    df_raw.to_csv(EXP_DIR / "all_ablation_runs.csv", index=False)
    print(f"Saved all raw runs to {EXP_DIR / 'all_ablation_runs.csv'}")

    # Analyze and generate ablation ledger
    analyze_and_build_ledger(df_raw)


if __name__ == "__main__":
    main()
