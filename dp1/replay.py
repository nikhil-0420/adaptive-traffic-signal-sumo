"""Generate deterministic microscopic vehicle replays from real SUMO/TraCI runs.

Produces replay.json containing step-by-step positions, headings, speeds,
signal states, detector queues, and emergency preemption status.
All data is 100% sourced from SUMO TraCI telemetry — zero fabricated coordinates.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import traci
from . import config as C
from .controllers import POLICIES
from .network import NET_FILE, DET_FILE, build_network
from .scenarios import build_routes, load_route_manifest
from .signal_states import SignalStates
from .sumo_utils import binary
from .runner import read_queues


def generate_run_replay(
    scenario: str = "imbalanced_ns",
    policy: str = "adaptive",
    seed: int = 1,
    demand_level: str = C.DEFAULT_DEMAND_LEVEL,
    emergency_event: bool = False,
    emergency_priority: bool = False,
    max_duration_s: float = 400.0,
    out_dir: Optional[Path] = None,
    save_to_frontend: bool = True,
) -> Path:
    """Run simulation through TraCI and record microscopic vehicle positions into replay.json."""
    if not NET_FILE.exists():
        build_network()

    em_cfg = C.EMERGENCY
    em_tag = ""
    if emergency_event:
        em_tag = "_em_pri" if emergency_priority else "_em"

    if out_dir is None:
        if demand_level == C.DEFAULT_DEMAND_LEVEL:
            out_dir = C.RESULTS_DIR / "runs" / f"{scenario}_{policy}_s{seed}{em_tag}"
        else:
            out_dir = C.RESULTS_DIR / "runs" / f"{scenario}_{demand_level}_{policy}_s{seed}{em_tag}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = out_dir.name

    routes, n_vehicles = build_routes(
        scenario,
        seed,
        out_dir=out_dir,
        demand_level=demand_level,
        emergency_event=emergency_event,
        emergency_cfg=em_cfg,
    )
    manifest = load_route_manifest(routes)

    tripinfo = out_dir / "tripinfo.xml"
    cmd = [
        binary("sumo"),
        "-n", str(NET_FILE),
        "-r", str(routes),
        "-a", str(DET_FILE),
        "--tripinfo-output", str(tripinfo),
        "--seed", str(seed),
        "--step-length", str(C.SIM.step_s),
        "--time-to-teleport", "-1",
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--waiting-time-memory", "3600",
    ]

    label = f"replay_{run_id}_{int(time.time()*1000)}"
    traci.start(cmd, label=label)

    states = SignalStates(NET_FILE)
    kwargs: Dict[str, Any] = {}
    if policy == "fixed_webster":
        kwargs["scenario"] = scenario
        kwargs["demand_level"] = demand_level
    if emergency_priority:
        kwargs["emergency_priority"] = True
        kwargs["emergency_cfg"] = em_cfg

    ctl = POLICIES[policy](states, **kwargs)

    frames = []
    try:
        t = 0.0
        q = read_queues()
        ctl.start(t, q)
        ctl.apply()

        limit_s = min(C.SIM.max_sim_time_s, max_duration_s if max_duration_s else C.SIM.max_sim_time_s)

        while t < limit_s:
            traci.simulationStep()
            t = traci.simulation.getTime()
            q = read_queues()
            ctl.step(t, q)

            em_detected = False
            em_dist = None
            if emergency_event:
                from .emergency import detect_approaching_emergency
                det = detect_approaching_emergency(C.TLS_ID, em_cfg=em_cfg)
                if det is not None:
                    em_detected = True
                    em_dist = round(det[2], 1)

            # Microscopic vehicle extraction
            v_ids = traci.vehicle.getIDList()
            vehs = []
            for vid in v_ids:
                pos = traci.vehicle.getPosition(vid)
                angle = traci.vehicle.getAngle(vid)
                speed = traci.vehicle.getSpeed(vid)
                wait = traci.vehicle.getWaitingTime(vid)
                is_em = bool(vid == em_cfg.vehicle_id or "ambulance" in vid)

                vehs.append({
                    "id": vid,
                    "x": round(pos[0], 1),
                    "y": round(pos[1], 1),
                    "a": round(angle, 1),
                    "s": round(speed, 1),
                    "w": round(wait, 1),
                    "em": is_em,
                })

            frames.append({
                "t": round(t, 1),
                "phase": ctl.phase,
                "axis": ctl.axis,
                "tl_state": traci.trafficlight.getRedYellowGreenState(C.TLS_ID),
                "queues_m": {a: round(q[a], 1) for a in C.APPROACHES},
                "emergency_approaching": em_detected,
                "emergency_dist_m": em_dist,
                "vehicles": vehs,
            })

            if t >= C.SIM.demand_duration_s and traci.simulation.getMinExpectedNumber() == 0:
                break
    finally:
        try:
            traci.close()
        except Exception:
            pass

    replay_data = {
        "run_id": run_id,
        "scenario": scenario,
        "policy": policy,
        "seed": seed,
        "demand_level": demand_level,
        "emergency_event": emergency_event,
        "emergency_priority": emergency_priority,
        "total_vehicles": n_vehicles,
        "duration_s": frames[-1]["t"] if frames else 0,
        "frame_count": len(frames),
        "step_s": C.SIM.step_s,
        "frames": frames,
    }

    replay_path = out_dir / "replay.json"
    with open(replay_path, "w", encoding="utf-8") as f:
        json.dump(replay_data, f)

    if save_to_frontend:
        fe_dir = Path("frontend/public/demo-data/runs") / run_id
        fe_dir.mkdir(parents=True, exist_ok=True)
        with open(fe_dir / "replay.json", "w", encoding="utf-8") as f:
            json.dump(replay_data, f)

    return replay_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate SUMO replay JSON for a run")
    parser.add_argument("--scenario", default="imbalanced_ns")
    parser.add_argument("--policy", default="adaptive")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--duration", type=float, default=400.0)
    parser.add_argument("--emergency-event", action="store_true")
    parser.add_argument("--emergency-priority", action="store_true")
    args = parser.parse_args()

    path = generate_run_replay(
        scenario=args.scenario,
        policy=args.policy,
        seed=args.seed,
        max_duration_s=args.duration,
        emergency_event=args.emergency_event,
        emergency_priority=args.emergency_priority,
    )
    print(f"Generated replay saved to: {path}")
