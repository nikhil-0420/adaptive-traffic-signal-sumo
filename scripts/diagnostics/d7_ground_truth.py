"""Diagnostic D7: Detector vs Ground Truth Queue Comparison.

D7: For 3 cells (balanced-heavy, imbalanced_orr-heavy, surge_orr_north-heavy; seed 101):
    - Per-approach correlation (Pearson r)
    - Mean absolute error (MAE in metres)
    - Fraction of time ground truth exceeds the detector span (> 24.9m)
    - Explicitly state stop-speed threshold (< 1.4 m/s) and gap assumptions (<= 7.5m).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Dict, List
import pandas as pd
import numpy as np
import traci

from dp1 import config as C
from dp1.controllers.hybrid_queue_adaptive import HybridQueueAdaptiveController
from dp1.queues import QueueMeasurementEngine, queues_to_legacy_dict
from dp1.scenarios import load_route_manifest
from dp1.site_scenarios import build_site_routes
from dp1.signal_states import SignalStates
from dp1.sumo_utils import binary

DET_SPAN_M = 24.9
APPROACHES = ["N", "S", "E", "W"]


def run_ground_truth_sampling(pattern: str, demand_level: str, seed: int = 101) -> pd.DataFrame:
    """Run simulation with non-invasive ground truth queue logging."""
    route_file, _ = build_site_routes(
        scenario=pattern,
        seed=seed,
        demand_level=demand_level,
        emergency_event=False,
    )
    net_file = C.ROOT / "network" / "marathahalli" / "dist" / "marathahalli.net.xml"
    det_file = C.ROOT / "network" / "marathahalli" / "build" / "detectors.add.xml"

    sumo_cmd = [
        str(binary("sumo")),
        "-n", str(net_file),
        "-r", str(route_file),
        "-a", str(det_file),
        "--time-to-teleport", "-1",
        "--collision.action", "none",
        "--waiting-time-memory", "1000",
        "--step-length", "1.0",
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--duration-log.disable", "true",
        "--seed", str(seed),
    ]

    traci.start(sumo_cmd)
    try:
        q_engine = QueueMeasurementEngine(network="marathahalli")
        states = SignalStates(net_file, tls_id="marathahalli_tls")
        ctl = HybridQueueAdaptiveController(
            states,
            scenario=pattern,
            demand_level=demand_level,
            network="marathahalli",
            tls_id="marathahalli_tls",
        )

        records = []
        t = 0.0
        init_queues = q_engine.measure_all(t)
        q = queues_to_legacy_dict(init_queues)
        ctl.start(t, q)
        ctl.apply()

        sim_time_cap = C.SIM.max_sim_time_s
        while t < sim_time_cap:
            traci.simulationStep()
            t = traci.simulation.getTime()
            app_queues = q_engine.measure_all(t)
            q = queues_to_legacy_dict(app_queues)
            ctl.step(t, q)

            rec = {"t": t}
            for a in APPROACHES:
                info = app_queues[a]
                rec[f"det_{a}"] = info.longitudinal_queue_m
                rec[f"gt_{a}"] = info.ground_truth_queue_m
            records.append(rec)

        return pd.DataFrame(records)
    finally:
        try:
            traci.close(False)
        except Exception:
            pass


def compute_d7_metrics(df: pd.DataFrame, cell_name: str) -> pd.DataFrame:
    results = []
    for a in APPROACHES:
        det = df[f"det_{a}"].to_numpy()
        gt = df[f"gt_{a}"].to_numpy()

        # Correlation
        if np.std(det) > 1e-4 and np.std(gt) > 1e-4:
            corr = float(np.corrcoef(det, gt)[0, 1])
        else:
            corr = 1.0 if np.allclose(det, gt) else 0.0

        # MAE
        mae = float(np.mean(np.abs(det - gt)))

        # Fraction of time GT exceeds detector span (24.9m)
        gt_exceeds_pct = float(np.mean(gt > DET_SPAN_M)) * 100.0

        # Max GT extent observed
        max_gt = float(np.max(gt))
        max_det = float(np.max(det))

        results.append({
            "cell": cell_name,
            "approach": a,
            "pearson_r": round(corr, 3),
            "mae_m": round(mae, 2),
            "gt_exceeds_det_span_pct": round(gt_exceeds_pct, 1),
            "max_gt_m": round(max_gt, 1),
            "max_det_m": round(max_det, 1),
        })
    return pd.DataFrame(results)


def main():
    target_cells = [
        ("balanced", "heavy", "balanced_heavy_s101"),
        ("imbalanced_orr", "heavy", "imbalanced_orr_heavy_s101"),
        ("surge_orr_north", "heavy", "surge_orr_north_heavy_s101"),
    ]

    all_res = []
    print("=" * 80)
    print("D7: DETECTOR VS GROUND TRUTH QUEUE VALIDATION (3 CELLS, DEV SEED 101)")
    print("Rules: Stopped speed < 1.4 m/s, Contiguous gap threshold <= 7.5m, Stopline threshold <= 15.0m")
    print(f"Physical Detector Span: {DET_SPAN_M}m")
    print("=" * 80)

    for pat, lvl, name in target_cells:
        print(f"\nEvaluating Ground Truth for {name} ({pat}, {lvl})...")
        df_series = run_ground_truth_sampling(pat, lvl, seed=101)
        res_df = compute_d7_metrics(df_series, name)
        all_res.append(res_df)
        print(res_df.to_string(index=False))

    summary_df = pd.concat(all_res, ignore_index=True)
    summary_csv = Path("results/research/d7_ground_truth_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSaved D7 summary table to {summary_csv}")


if __name__ == "__main__":
    main()
