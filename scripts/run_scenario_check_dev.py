"""Run non-triviality check experiment on dev seeds 101-105.

Evaluates fixed_webster and hybrid_queue_adaptive on:
- Scenarios: ramp_peak, surge_shift, lane_closure
- Levels: medium, heavy
- Seeds: 101, 102, 103, 104, 105
- Network: marathahalli

Produces raw_runs.csv, per-cell outputs in results/research/exp_scenario_check_dev,
and computes:
- mean wait
- p95 wait
- max approach queue
- fraction of time any approach is SATURATED (q >= 24.0m)
- unfinished vehicles
"""

import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from dp1 import config as C
from dp1.research.matrix import MatrixCell, build_research_matrix
from dp1.research.orchestrator import run_research_experiment


EXP_ID = "exp_scenario_check_dev"
EXP_DIR = C.RESULTS_DIR / "research" / EXP_ID
SCENARIOS = ("ramp_peak", "surge_shift", "lane_closure")
LEVELS = ("medium", "heavy")
POLICIES = ("fixed_webster", "hybrid_queue_adaptive")
SEEDS = (101, 102, 103, 104, 105)


def run_experiment(jobs: int = 4):
    print(f"=== Running Non-Triviality Check: {EXP_ID} ===")
    print(f"Scenarios: {SCENARIOS}")
    print(f"Levels: {LEVELS}")
    print(f"Policies: {POLICIES}")
    print(f"Seeds: {SEEDS}")
    print(f"Total cells: {len(SCENARIOS) * len(LEVELS) * len(POLICIES) * len(SEEDS)}")

    res = run_research_experiment(
        experiment_id=EXP_ID,
        patterns=SCENARIOS,
        levels=LEVELS,
        policies=POLICIES,
        seeds=SEEDS,
        network="marathahalli",
        jobs=jobs,
    )
    matrix = res[0] if isinstance(res, tuple) else res
    if hasattr(matrix, "status_counts"):
        print("Experiment completed. Status:", matrix.status_counts())
    return res


def compute_metrics_and_saturation():
    runs_dir = EXP_DIR / "runs"
    records = []

    for sc in SCENARIOS:
        for lvl in LEVELS:
            for pol in POLICIES:
                for sd in SEEDS:
                    cell_id = f"cell_marathahalli_{sc}_{lvl}_{pol}_s{sd}"
                    run_dir = runs_dir / cell_id
                    metrics_file = run_dir / "metrics.json"
                    ts_file = run_dir / "timeseries.csv"

                    if not metrics_file.exists() or not ts_file.exists():
                        print(f"Warning: missing outputs for {cell_id}")
                        continue

                    with open(metrics_file, "r", encoding="utf-8") as f:
                        m = json.load(f)

                    # Compute saturation fraction from timeseries
                    ts = pd.read_csv(ts_file)
                    # Check any approach q >= 24.0m (detector physical saturation threshold)
                    is_sat = (
                        (ts["q_N"] >= 24.0) |
                        (ts["q_S"] >= 24.0) |
                        (ts["q_E"] >= 24.0) |
                        (ts["q_W"] >= 24.0)
                    )
                    sat_frac = float(is_sat.mean())

                    records.append({
                        "scenario": sc,
                        "level": lvl,
                        "policy": pol,
                        "seed": sd,
                        "avg_wait_s": m["avg_wait_s"],
                        "p95_wait_s": m["p95_wait_s"],
                        "max_queue_m": m["max_queue_m"],
                        "saturated_fraction": sat_frac,
                        "unfinished": m["vehicles_unfinished"],
                        "completion_rate": m["completion_rate"],
                        "total_vehicles": m["vehicles_total"],
                    })

    df = pd.DataFrame(records)
    summary_path = EXP_DIR / "scenario_check_summary.csv"
    df.to_csv(summary_path, index=False)
    print(f"Saved run-level metrics to {summary_path}")

    # Grouped aggregates per scenario x level x policy
    agg = df.groupby(["scenario", "level", "policy"]).agg(
        mean_wait=("avg_wait_s", "mean"),
        std_wait=("avg_wait_s", "std"),
        mean_p95=("p95_wait_s", "mean"),
        mean_max_q=("max_queue_m", "mean"),
        max_q_peak=("max_queue_m", "max"),
        mean_sat_frac=("saturated_fraction", "mean"),
        total_unfinished=("unfinished", "sum"),
    ).round(2).reset_index()

    agg_path = EXP_DIR / "scenario_check_aggregated.csv"
    agg.to_csv(agg_path, index=False)
    print(f"Saved aggregated metrics to {agg_path}")

    print("\n" + "="*80)
    print("PHASE 8 NON-TRIVIALITY CHECK RESULTS (Dev Seeds 101-105)")
    print("="*80)
    print(agg.to_string(index=False))
    print("="*80)

    return df, agg


if __name__ == "__main__":
    run_experiment(jobs=4)
    compute_metrics_and_saturation()
