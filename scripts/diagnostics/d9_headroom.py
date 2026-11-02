"""Diagnostic D9: Headroom Analysis (Hybrid vs Webster).

D9: Per condition (pattern x demand_level):
    - Hybrid-minus-Webster difference in:
      * Mean wait (s)
      * P95 wait (s)
      * Max queue (m)
      * Approach wait gap (max wait - min wait across approaches, in seconds)
    - Sample size n:
      * Seeds 121-130 for hypotheses (from exp_marathahalli_hybrid_840)
      * Dev seeds 101-110 for decisions (from exp_diag_dev_101_110)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


def compute_headroom_table(exp_dir: Path) -> pd.DataFrame:
    raw_csv = exp_dir / "raw_runs.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw_runs.csv at {raw_csv}")
    raw_df = pd.read_csv(raw_csv)

    # Filter to fixed_webster and hybrid_queue_adaptive
    sub_df = raw_df[raw_df["policy"].isin(["fixed_webster", "hybrid_queue_adaptive"])].copy()

    # Calculate approach wait gap per run: max(avg_wait_<app>) - min(avg_wait_<app>)
    wait_cols = [c for c in ["avg_wait_N_s", "avg_wait_S_s", "avg_wait_E_s", "avg_wait_W_s"] if c in sub_df.columns]
    if wait_cols:
        sub_df["approach_wait_gap_s"] = sub_df[wait_cols].max(axis=1) - sub_df[wait_cols].min(axis=1)
    else:
        sub_df["approach_wait_gap_s"] = np.nan

    # Pair by pattern x demand_level x seed
    piv = sub_df.pivot(
        index=["pattern", "demand_level", "seed"],
        columns="policy",
        values=["avg_wait_s", "p95_wait_s", "max_queue_m", "approach_wait_gap_s"]
    )

    if ("avg_wait_s", "hybrid_queue_adaptive") not in piv.columns or ("avg_wait_s", "fixed_webster") not in piv.columns:
        raise ValueError("Both hybrid_queue_adaptive and fixed_webster must be present in raw_runs.csv")

    diff = pd.DataFrame(index=piv.index)
    diff["delta_mean_wait_s"] = piv[("avg_wait_s", "hybrid_queue_adaptive")] - piv[("avg_wait_s", "fixed_webster")]
    diff["delta_p95_wait_s"] = piv[("p95_wait_s", "hybrid_queue_adaptive")] - piv[("p95_wait_s", "fixed_webster")]
    diff["delta_max_queue_m"] = piv[("max_queue_m", "hybrid_queue_adaptive")] - piv[("max_queue_m", "fixed_webster")]
    diff["delta_approach_gap_s"] = piv[("approach_wait_gap_s", "hybrid_queue_adaptive")] - piv[("approach_wait_gap_s", "fixed_webster")]
    diff = diff.reset_index()

    # Aggregate by pattern x demand_level
    agg = diff.groupby(["pattern", "demand_level"]).agg(
        n_seeds=("seed", "count"),
        delta_mean_wait_mean=("delta_mean_wait_s", "mean"),
        delta_p95_wait_mean=("delta_p95_wait_s", "mean"),
        delta_max_queue_mean=("delta_max_queue_m", "mean"),
        delta_approach_gap_mean=("delta_approach_gap_s", "mean"),
    ).reset_index()

    return agg


def main():
    parser = argparse.ArgumentParser(description="Compute D9 headroom diagnostics.")
    parser.add_argument("--exp-dir", type=str, default="results/research/exp_diag_dev_101_110",
                        help="Path to experiment directory")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    print(f"Running D9 Headroom Diagnostics on: {exp_dir}")
    agg = compute_headroom_table(exp_dir)

    print("\n" + "=" * 80)
    print("D9: HEADROOM TABLE (HYBRID - WEBSTER DELTAS; NEGATIVE VALUES = HYBRID WINS)")
    print("=" * 80)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
