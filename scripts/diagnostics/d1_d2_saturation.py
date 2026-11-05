"""Diagnostic D1 & D2: Detector Saturation Rate and Episode Durations.

D1: Detector saturation rate by approach x demand level x policy:
    SATURATED obs / valid obs * 100, excluding OFFLINE rows from denominator.
    Report counts too.
    Saturation rule confirmed in dp1/queues.py:
    det_len = 24.9m, margin = 0.5m -> saturation threshold = 24.4m.

D2: Longest continuous SATURATED stretch (s) per approach per condition,
    and number of separate episodes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

APPROACHES = ["N", "S", "E", "W"]
DET_SPAN_M = 24.9
DET_MARGIN_M = 0.5
SAT_THRESHOLD_M = DET_SPAN_M - DET_MARGIN_M  # 24.4m


def analyze_cell_timeseries(ts_path: Path) -> Dict[str, Dict]:
    df = pd.read_csv(ts_path)
    res = {}
    for app in APPROACHES:
        col = f"q_{app}"
        if col not in df.columns:
            continue
        vals = df[col].to_numpy()
        valid_mask = ~np.isnan(vals)
        total_valid = int(np.sum(valid_mask))
        sat_mask = vals >= SAT_THRESHOLD_M
        sat_count = int(np.sum(sat_mask))

        # Episodes of continuous saturation
        # An episode is a contiguous block of sat_mask == True
        longest_stretch_s = 0
        episodes_count = 0
        current_stretch = 0

        for is_sat in sat_mask:
            if is_sat:
                current_stretch += 1
            else:
                if current_stretch > 0:
                    episodes_count += 1
                    longest_stretch_s = max(longest_stretch_s, current_stretch)
                    current_stretch = 0
        if current_stretch > 0:
            episodes_count += 1
            longest_stretch_s = max(longest_stretch_s, current_stretch)

        res[app] = {
            "valid_obs": total_valid,
            "sat_obs": sat_count,
            "longest_stretch_s": longest_stretch_s,
            "episodes_count": episodes_count,
        }
    return res


def run_saturation_diagnostics(exp_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    raw_csv = exp_dir / "raw_runs.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw_runs.csv at {raw_csv}")
    raw_df = pd.read_csv(raw_csv)

    d1_records = []
    d2_records = []

    for _, row in raw_df.iterrows():
        cell_id = row["cell_id"]
        policy = row["policy"]
        pattern = row["pattern"]
        demand_level = row["demand_level"]
        seed = row["seed"]

        ts_path = exp_dir / "runs" / cell_id / "timeseries.csv"
        if not ts_path.exists():
            continue

        cell_data = analyze_cell_timeseries(ts_path)
        for app, stats in cell_data.items():
            d1_records.append({
                "cell_id": cell_id,
                "policy": policy,
                "pattern": pattern,
                "demand_level": demand_level,
                "seed": seed,
                "approach": app,
                "valid_obs": stats["valid_obs"],
                "sat_obs": stats["sat_obs"],
            })
            d2_records.append({
                "cell_id": cell_id,
                "policy": policy,
                "pattern": pattern,
                "demand_level": demand_level,
                "seed": seed,
                "approach": app,
                "longest_stretch_s": stats["longest_stretch_s"],
                "episodes_count": stats["episodes_count"],
            })

    df1_all = pd.DataFrame(d1_records)
    df2_all = pd.DataFrame(d2_records)

    # D1 Aggregate: by approach x demand level x policy
    d1_agg = df1_all.groupby(["approach", "demand_level", "policy"]).agg(
        total_valid=("valid_obs", "sum"),
        total_sat=("sat_obs", "sum"),
    ).reset_index()
    d1_agg["saturation_rate_pct"] = (d1_agg["total_sat"] / d1_agg["total_valid"]) * 100.0

    # D2 Aggregate: longest continuous stretch per approach per condition (pattern x demand x policy)
    d2_agg = df2_all.groupby(["pattern", "demand_level", "policy", "approach"]).agg(
        max_longest_stretch_s=("longest_stretch_s", "max"),
        mean_longest_stretch_s=("longest_stretch_s", "mean"),
        total_episodes=("episodes_count", "sum"),
        mean_episodes_per_run=("episodes_count", "mean"),
    ).reset_index()

    return d1_agg, d2_agg


def main():
    parser = argparse.ArgumentParser(description="Compute D1 and D2 saturation diagnostics.")
    parser.add_argument("--exp-dir", type=str, default="results/research/exp_diag_dev_101_110",
                        help="Path to experiment directory")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    print(f"Running D1 & D2 diagnostics on: {exp_dir}")
    d1_agg, d2_agg = run_saturation_diagnostics(exp_dir)

    print("\n" + "=" * 80)
    print("D1: DETECTOR SATURATION RATE BY APPROACH x DEMAND LEVEL x POLICY")
    print(f"Saturation Rule: span = {DET_SPAN_M}m, margin = {DET_MARGIN_M}m, threshold = {SAT_THRESHOLD_M}m")
    print("=" * 80)
    print(d1_agg.to_string(index=False))

    print("\n" + "=" * 80)
    print("D2: LONGEST SATURATED STRETCH & EPISODES PER CONDITION")
    print("=" * 80)
    print(d2_agg.to_string(index=False))


if __name__ == "__main__":
    main()
