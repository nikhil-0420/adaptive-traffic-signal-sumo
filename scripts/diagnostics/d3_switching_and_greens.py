"""Diagnostic D3: Switching Frequency and Green Duration Analysis.

D3: Balanced-low (and balanced-medium/heavy for comparison):
    - switches per hour
    - mean/min/max actual green duration
    - per policy where decisions.csv exists (and/or derived from phase transitions in timeseries.csv)
    - Question: Does the hybrid switch more or hold shorter greens than adaptive/pressure in balanced-low?
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np


def analyze_cell_switching(cell_dir: Path) -> Dict:
    """Analyze phase switches and green durations from decisions.csv and timeseries.csv."""
    dec_path = cell_dir / "decisions.csv"
    ts_path = cell_dir / "timeseries.csv"

    # From decisions.csv if present
    greens = []
    switches_count = 0
    sim_duration_s = 1800.0

    if ts_path.exists():
        df_ts = pd.read_csv(ts_path)
        if not df_ts.empty:
            sim_duration_s = float(df_ts["t"].max())
            # Detect phase switches: green phase changes
            # Look at transitions where phase == 'GREEN' starts
            phases = df_ts["phase"].tolist()
            axes = df_ts["axis"].tolist()
            current_phase = None
            current_axis = None
            green_start_t = None

            for _, r in df_ts.iterrows():
                p = r["phase"]
                ax = r["axis"]
                t = r["t"]

                if p == "GREEN":
                    if current_phase != "GREEN" or ax != current_axis:
                        # Starting new green
                        if green_start_t is not None and current_phase == "GREEN":
                            greens.append(t - green_start_t)
                        green_start_t = t
                        switches_count += 1
                else:
                    if current_phase == "GREEN" and green_start_t is not None:
                        greens.append(t - green_start_t)
                        green_start_t = None

                current_phase = p
                current_axis = ax

            if current_phase == "GREEN" and green_start_t is not None:
                greens.append(sim_duration_s - green_start_t)

    switches_per_hour = (switches_count / (sim_duration_s / 3600.0)) if sim_duration_s > 0 else 0.0

    # Also extract decision stats if decisions.csv exists
    dec_greens = []
    if dec_path.exists():
        df_dec = pd.read_csv(dec_path)
        if not df_dec.empty and "actual_green_s" in df_dec.columns:
            # Drop nulls
            valid_g = df_dec["actual_green_s"].dropna().tolist()
            if valid_g:
                dec_greens = valid_g

    reported_greens = dec_greens if dec_greens else greens

    return {
        "switches_count": switches_count,
        "switches_per_hour": switches_per_hour,
        "mean_green_s": float(np.mean(reported_greens)) if reported_greens else float("nan"),
        "min_green_s": float(np.min(reported_greens)) if reported_greens else float("nan"),
        "max_green_s": float(np.max(reported_greens)) if reported_greens else float("nan"),
        "n_greens": len(reported_greens),
    }


def run_d3(exp_dir: Path, pattern_filter: str = "balanced") -> pd.DataFrame:
    raw_csv = exp_dir / "raw_runs.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw_runs.csv at {raw_csv}")
    raw_df = pd.read_csv(raw_csv)
    if pattern_filter:
        raw_df = raw_df[raw_df["pattern"] == pattern_filter]

    records = []
    for _, row in raw_df.iterrows():
        cell_id = row["cell_id"]
        policy = row["policy"]
        pattern = row["pattern"]
        demand_level = row["demand_level"]
        seed = row["seed"]

        cell_dir = exp_dir / "runs" / cell_id
        if not cell_dir.exists():
            continue

        stats = analyze_cell_switching(cell_dir)
        records.append({
            "cell_id": cell_id,
            "policy": policy,
            "pattern": pattern,
            "demand_level": demand_level,
            "seed": seed,
            **stats,
        })

    df = pd.DataFrame(records)
    agg = df.groupby(["pattern", "demand_level", "policy"]).agg(
        mean_switches_per_hour=("switches_per_hour", "mean"),
        mean_green_s=("mean_green_s", "mean"),
        min_green_s=("min_green_s", "min"),
        max_green_s=("max_green_s", "max"),
        n_seeds=("seed", "count"),
    ).reset_index()

    return agg


def main():
    parser = argparse.ArgumentParser(description="Compute D3 switching and green duration diagnostics.")
    parser.add_argument("--exp-dir", type=str, default="results/research/exp_diag_dev_101_110",
                        help="Path to experiment directory")
    parser.add_argument("--pattern", type=str, default="balanced", help="Filter by pattern")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    print(f"Running D3 on: {exp_dir} (pattern: {args.pattern})")
    agg = run_d3(exp_dir, pattern_filter=args.pattern)
    print("\n" + "=" * 80)
    print(f"D3: SWITCHING FREQUENCY AND GREEN DURATION ({args.pattern})")
    print("=" * 80)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
