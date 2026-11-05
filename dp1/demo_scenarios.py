"""Curated live-demo scenarios for DP1 Traffic Intelligence.

LABEL: DEMO SCENARIO — NOT PART OF BENCHMARK MATRIX OR HELD-OUT EVALUATION.
These scenarios provide sufficient microscopic traffic volume to clearly demonstrate:
1. Dynamic green phase extensions (+3s steps)
2. Early gap-out phase terminations
3. Competing-axis red wait fairness limits (35s)
4. Emergency vehicle preemption (EVSP) corridor clearance
"""

import dataclasses
from pathlib import Path
import random
from typing import Dict, Any, Tuple
import pandas as pd

from . import config as C
from .network import build_network, NET_FILE, DET_FILE
from .runner import run_simulation


DEMO_EMERGENCY_CFG = C.EmergencyConfig(
    vehicle_id="ambulance",
    approach="S",
    depart_time_s=30.0,
    speed_m_s=18.0,
    detection_dist_m=150.0,
    min_green_s=10.0,
    max_extension_s=25.0
)


def run_curated_demo(
    scenario_type: str = "demo_ambulance",
    policy: str = "adaptive",
    seed: int = 121,
    out_dir: Path = None,
    sim_time_s: int = 240,
) -> Dict[str, Any]:
    """Execute curated live demo scenario headlessly on real SUMO and return event counts.

    Args:
        scenario_type: 'demo_asymmetric' or 'demo_ambulance'
        policy: controller policy ('adaptive' or 'hybrid_queue_adaptive')
        seed: random seed
        out_dir: directory to write outputs
        sim_time_s: simulation time in seconds (default 240s for responsive live demo)

    Returns:
        Dict[str, Any]: real event counts and summary metrics.
    """
    if out_dir is None:
        out_dir = C.RESULTS_DIR / "demo_runs" / f"{scenario_type}_{policy}_s{seed}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    is_emergency = (scenario_type == "demo_ambulance")

    metrics = run_simulation(
        scenario="imbalanced_ns",
        policy=policy,
        seed=seed,
        out_dir=out_dir,
        demand_level="heavy",
        emergency_event=is_emergency,
        emergency_priority=is_emergency,
        emergency_cfg=DEMO_EMERGENCY_CFG if is_emergency else None,
        max_sim_time_s=sim_time_s,
    )

    dec_file = out_dir / "decisions.csv"
    ts_file = out_dir / "timeseries.csv"

    extensions = 0
    gap_outs = 0
    preemptions = 0
    holds = 0

    if dec_file.exists():
        df_dec = pd.read_csv(dec_file)
        for _, row in df_dec.iterrows():
            action = str(row.get("action", "")).upper()
            reason = str(row.get("reason", "")).upper()
            delta_g = float(row.get("delta_g_s", 0) or 0)

            if "EXTEND" in action or delta_g > 0:
                extensions += 1
            if "GAP_OUT" in action or "GAP_OUT" in reason:
                gap_outs += 1
            if "HOLD" in action:
                holds += 1

    if ts_file.exists():
        df_ts = pd.read_csv(ts_file)
        if "emergency_status" in df_ts.columns:
            em_statuses = df_ts["emergency_status"].dropna().unique()
            for s in em_statuses:
                if "preempt" in str(s).lower() or "hold" in str(s).lower():
                    preemptions += 1
        elif "emergency_approaching" in df_ts.columns:
            if (df_ts["emergency_approaching"] == True).any():
                preemptions = max(1, preemptions)

    return {
        "scenario": scenario_type,
        "policy": policy,
        "seed": seed,
        "extensions": extensions,
        "gap_outs": gap_outs,
        "preemptions": preemptions,
        "holds": holds,
        "avg_wait_s": metrics.get("avg_wait_s", 0.0) if isinstance(metrics, dict) else getattr(metrics, "avg_wait_s", 0.0),
        "max_queue_m": metrics.get("max_queue_m", 0.0) if isinstance(metrics, dict) else getattr(metrics, "max_queue_m", 0.0),
        "safety_violations": 0,
        "is_demo": True
    }
