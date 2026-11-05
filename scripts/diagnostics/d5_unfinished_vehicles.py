"""Diagnostic D5: Unfinished Vehicles Analysis and Average Wait Bias.

D5: Unfinished vehicles per policy and condition (generated vs completed) from raw_runs.csv;
    state whether avg_wait_s includes completed vehicles only (quote the parser lines).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def analyze_unfinished_vehicles(exp_dir: Path) -> pd.DataFrame:
    raw_csv = exp_dir / "raw_runs.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw_runs.csv at {raw_csv}")
    raw_df = pd.read_csv(raw_csv)

    # Columns: pattern, demand_level, policy, vehicles_total, vehicles_arrived, vehicles_unfinished, completion_rate, avg_wait_s
    agg = raw_df.groupby(["pattern", "demand_level", "policy"]).agg(
        n_runs=("seed", "count"),
        mean_total_generated=("vehicles_total", "mean"),
        mean_arrived=("vehicles_arrived", "mean"),
        mean_unfinished=("vehicles_unfinished", "mean"),
        max_unfinished=("vehicles_unfinished", "max"),
        mean_completion_rate=("completion_rate", "mean"),
        mean_avg_wait_s=("avg_wait_s", "mean"),
    ).reset_index()

    agg["completion_pct"] = agg["mean_completion_rate"] * 100.0
    agg["unfinished_pct"] = 100.0 - agg["completion_pct"]

    return agg


PARSER_CITATION = """
Code Citation from dp1/metrics.py (lines 53-85, 102):
--------------------------------------------------------------------------------
53:     tree = ET.parse(tripinfo_path)
54:     for ti in tree.getroot().iter("tripinfo"):
55:         w = float(ti.get("waitingTime"))
56:         l = float(ti.get("timeLoss"))
57:         d = float(ti.get("duration"))
...
75:         wait.append(w)
...
85:     arrived = len(dur)
...
102:         "avg_wait_s": float(np.mean(wait)) if wait else float("nan"),
--------------------------------------------------------------------------------
Interpretation:
SUMO's tripinfo.xml records ONLY vehicles that reached their destination (arrived).
Vehicles trapped in congestion or queues at simulation termination are NEVER emitted
to tripinfo.xml. Therefore, avg_wait_s strictly computes the mean wait of COMPLETED
vehicles only. If one policy has higher unfinished vehicles (severe congestion), its
avg_wait_s can artificially appear lower or truncated because the most severely delayed
vehicles never completed their trips.
"""


def main():
    parser = argparse.ArgumentParser(description="Compute D5 unfinished vehicle diagnostics.")
    parser.add_argument("--exp-dir", type=str, default="results/research/exp_diag_dev_101_110",
                        help="Path to experiment directory")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    print(f"Running D5 on: {exp_dir}")
    agg = analyze_unfinished_vehicles(exp_dir)

    print("\n" + "=" * 80)
    print("D5: UNFINISHED VEHICLES AND COMPLETION RATES PER CONDITION")
    print("=" * 80)
    print(agg.to_string(index=False))

    print("\n" + "=" * 80)
    print("D5: PARSER GROUND TRUTH AUDIT (DOES avg_wait_s INCLUDE COMPLETED VEHICLES ONLY?)")
    print("=" * 80)
    print(PARSER_CITATION)


if __name__ == "__main__":
    main()
