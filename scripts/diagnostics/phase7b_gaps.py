"""Phase 7B Diagnostics: Reconciliations and Diagnostic Gaps.

Covers:
1. Base Green Oracle Audit: Call chain and inputs in Hybrid controller.
2. Extension & Fairness Audit: Score comparison and competing wait metrics.
3. D1 vs D7 Reconcilation: Saturation threshold sensitivity and lead car setback.
4. Max Queue Source: Detector vs Ground Truth.
5. Balanced-Low Comparison: Hybrid vs Adaptive green lengths and min greens.
"""

from __future__ import annotations

import glob
from pathlib import Path
import numpy as np
import pandas as pd


def audit_item2_extensions_and_fairness(exp_dir: Path) -> dict:
    runs = list(exp_dir.glob("runs/*hybrid_queue_adaptive*/decisions.csv"))
    total_approved = 0
    comp_gt_active = 0
    comp_waits_at_ext = []
    comp_waits_at_switch = []

    fairness_counts = {"SWITCH_DEMAND_FAIRNESS": 0, "SWITCH_FAIRNESS_WAIT_LIMIT": 0}
    fairness_lt_5m = {"SWITCH_DEMAND_FAIRNESS": 0, "SWITCH_FAIRNESS_WAIT_LIMIT": 0}
    fairness_lt_10m = {"SWITCH_DEMAND_FAIRNESS": 0, "SWITCH_FAIRNESS_WAIT_LIMIT": 0}

    for r in runs:
        df = pd.read_csv(r)
        n = len(df)
        for idx, row in df.iterrows():
            rc = str(row["reason_code"])
            if rc == "EXTEND_APPROVED":
                total_approved += 1
                if row["score_competing"] > row["score_active"]:
                    comp_gt_active += 1
                comp_waits_at_ext.append(row["elapsed_s"])
                for next_idx in range(idx + 1, n):
                    next_row = df.iloc[next_idx]
                    if str(next_row["reason_code"]).startswith("SWITCH_"):
                        comp_waits_at_switch.append(next_row["elapsed_s"])
                        break
            elif rc in fairness_counts:
                fairness_counts[rc] += 1
                q_comp = float(row["q_competing_m"])
                if q_comp < 5.0:
                    fairness_lt_5m[rc] += 1
                if q_comp < 10.0:
                    fairness_lt_10m[rc] += 1

    return {
        "total_approved_extensions": total_approved,
        "competing_score_gt_active_count": comp_gt_active,
        "competing_score_gt_active_pct": (comp_gt_active / total_approved * 100.0) if total_approved else 0.0,
        "mean_competing_wait_at_extension_s": float(np.mean(comp_waits_at_ext)) if comp_waits_at_ext else 0.0,
        "mean_competing_wait_at_next_switch_s": float(np.mean(comp_waits_at_switch)) if comp_waits_at_switch else 0.0,
        "mean_competing_wait_at_next_switch_plus_clearance_s": (float(np.mean(comp_waits_at_switch)) + 5.0) if comp_waits_at_switch else 0.0,
        "fairness_counts": fairness_counts,
        "fairness_lt_5m": fairness_lt_5m,
        "fairness_lt_10m": fairness_lt_10m,
    }


def audit_item3_reconciliation(exp_dir: Path) -> dict:
    results = {}
    for condition, app, col in [
        ("imbalanced_orr_heavy", "South", "q_S"),
        ("surge_orr_north_heavy", "North", "q_N"),
    ]:
        seed_files = list(exp_dir.glob(f"runs/cell_marathahalli_{condition}_hybrid_queue_adaptive_s*/timeseries.csv"))
        rates_24_4 = []
        rates_24_0 = []
        for sf in seed_files:
            ts = pd.read_csv(sf)
            rates_24_4.append(float((ts[col] >= 24.4).mean() * 100.0))
            rates_24_0.append(float((ts[col] >= 24.0).mean() * 100.0))
        
        # Seed 101 specifically
        s101_file = exp_dir / f"runs/cell_marathahalli_{condition}_hybrid_queue_adaptive_s101/timeseries.csv"
        ts101 = pd.read_csv(s101_file)
        
        results[condition] = {
            "approach": app,
            "s101_sat_rate_24_4_pct": round(float((ts101[col] >= 24.4).mean() * 100.0), 2),
            "s101_sat_rate_24_0_pct": round(float((ts101[col] >= 24.0).mean() * 100.0), 2),
            "mean_10seeds_sat_rate_24_4_pct": round(float(np.mean(rates_24_4)), 2),
            "mean_10seeds_sat_rate_24_0_pct": round(float(np.mean(rates_24_0)), 2),
            "max_reported_det_q_s101_m": round(float(ts101[col].max()), 2),
        }
    return results


def audit_item5_balanced_low(exp_dir: Path) -> dict:
    def extract_completed_greens(run_dirs):
        all_greens = []
        for d in run_dirs:
            ts = pd.read_csv(Path(d) / "timeseries.csv")
            curr_g = 0
            in_green = False
            for p in ts["phase"]:
                if p == "GREEN":
                    curr_g += 1
                    in_green = True
                else:
                    if in_green:
                        all_greens.append(curr_g)
                        curr_g = 0
                        in_green = False
        return {
            "mean_green_s": round(float(np.mean(all_greens)), 2),
            "median_green_s": round(float(np.median(all_greens)), 2),
            "min_green_s": round(float(np.min(all_greens)), 2),
            "max_green_s": round(float(np.max(all_greens)), 2),
            "p10_green_s": round(float(np.percentile(all_greens, 10)), 2),
            "p90_green_s": round(float(np.percentile(all_greens, 90)), 2),
            "pct_at_or_below_10s": round(float(np.mean(np.array(all_greens) <= 10.0)) * 100.0, 2),
            "total_completed_phases": len(all_greens),
        }

    hybrid_runs = list(exp_dir.glob("runs/*balanced_low_hybrid*"))
    adaptive_runs = list(Path("results/research/exp_marathahalli_site_720").glob("runs/*balanced_low_adaptive*"))
    webster_runs = list(exp_dir.glob("runs/*balanced_low_fixed*"))

    return {
        "hybrid": extract_completed_greens(hybrid_runs),
        "adaptive": extract_completed_greens(adaptive_runs),
        "webster": extract_completed_greens(webster_runs),
    }


def main():
    exp_dir = Path("results/research/exp_diag_dev_101_110")
    print("=" * 80)
    print("PHASE 7B: DIAGNOSTIC GAPS AUDIT")
    print("=" * 80)

    print("\n--- ITEM 2: APPROVED EXTENSIONS & FAIRNESS SWITCHES ---")
    res2 = audit_item2_extensions_and_fairness(exp_dir)
    print(f"Total Approved Extensions: {res2['total_approved_extensions']}")
    print(f"Competing Score > Active Score: {res2['competing_score_gt_active_count']} ({res2['competing_score_gt_active_pct']:.2f}%)")
    print(f"Mean Competing Red Wait at Extension: {res2['mean_competing_wait_at_extension_s']:.2f}s")
    print(f"Mean Competing Red Wait at Next Switch (controller internal): {res2['mean_competing_wait_at_next_switch_s']:.2f}s")
    print(f"Mean Competing Red Wait at Next Switch (+5s clearance): {res2['mean_competing_wait_at_next_switch_plus_clearance_s']:.2f}s")
    print(f"Fairness Switch Counts: {res2['fairness_counts']}")
    print(f"Fairness Switches with comp_q < 5m: {res2['fairness_lt_5m']}")
    print(f"Fairness Switches with comp_q < 10m: {res2['fairness_lt_10m']}")

    print("\n--- ITEM 3: D1 VS D7 RECONCILIATION ---")
    res3 = audit_item3_reconciliation(exp_dir)
    for k, v in res3.items():
        print(f"Condition: {k} ({v['approach']})")
        print(f"  Max Reported Detector Queue (s101): {v['max_reported_det_q_s101_m']}m")
        print(f"  Seed 101 SAT Rate (threshold 24.4m): {v['s101_sat_rate_24_4_pct']}%")
        print(f"  Seed 101 SAT Rate (threshold 24.0m): {v['s101_sat_rate_24_0_pct']}%")
        print(f"  10-Seed Mean SAT Rate (threshold 24.4m): {v['mean_10seeds_sat_rate_24_4_pct']}%")
        print(f"  10-Seed Mean SAT Rate (threshold 24.0m): {v['mean_10seeds_sat_rate_24_0_pct']}%")

    print("\n--- ITEM 5: BALANCED LOW GREEN LENGTH & MIN GREEN ---")
    res5 = audit_item5_balanced_low(exp_dir)
    print(f"Hybrid:   Mean={res5['hybrid']['mean_green_s']}s, Median={res5['hybrid']['median_green_s']}s, Min={res5['hybrid']['min_green_s']}s, <=10s={res5['hybrid']['pct_at_or_below_10s']}%")
    print(f"Adaptive: Mean={res5['adaptive']['mean_green_s']}s, Median={res5['adaptive']['median_green_s']}s, Min={res5['adaptive']['min_green_s']}s, <=10s={res5['adaptive']['pct_at_or_below_10s']}%")
    print(f"Webster:  Mean={res5['webster']['mean_green_s']}s, Median={res5['webster']['median_green_s']}s, Min={res5['webster']['min_green_s']}s, <=10s={res5['webster']['pct_at_or_below_10s']}%")


if __name__ == "__main__":
    main()
