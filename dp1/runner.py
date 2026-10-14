"""Run ONE simulation (scenario x policy x seed) through TraCI and write its outputs."""
import csv
import json
import os
import random
import time
from pathlib import Path
import traci

from . import config as C
from .controllers import POLICIES
from .metrics import summarise_run
from .network import NET_FILE, DET_FILE, build_network
from .scenarios import build_routes, load_route_manifest
from .signal_states import SignalStates
from .sumo_utils import binary


def read_queues():
    return {a: max(traci.lanearea.getJamLengthMeters(f"det_{a}_{i}") for i in range(C.NET.lanes)) for a in C.APPROACHES}


def _write_atomic_telemetry(out_dir: Path, data: dict):
    """Write telemetry dict atomically via temp file replace to prevent partial reads."""
    tmp_path = out_dir / "telemetry.json.tmp"
    final_path = out_dir / "telemetry.json"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        tmp_path.replace(final_path)
    except Exception:
        pass


def run_simulation(
    scenario: str,
    policy: str,
    seed: int,
    gui: bool = False,
    out_dir: Path = None,
    policy_kwargs: dict = None,
    attempts: int = 5,
    demand_level: str = C.DEFAULT_DEMAND_LEVEL,
    emergency_event: bool = False,
    emergency_priority: bool = False,
    emergency_cfg: C.EmergencyConfig = None,
    record_vehicles: bool = False,
):
    """Run one simulation. Retries on TraCI connection failures (parallel runs can race for ports).

    policy_kwargs: e.g. {'cfg': AdaptiveConfig(k_s_per_m=0.2)} or {'model_path': '...'}
    """
    last = None
    for _ in range(attempts):
        try:
            return _run_once(
                scenario, policy, seed, gui, out_dir, policy_kwargs, demand_level,
                emergency_event=emergency_event,
                emergency_priority=emergency_priority,
                emergency_cfg=emergency_cfg,
                record_vehicles=record_vehicles,
            )
        except Exception as e:
            last = e
            try:
                traci.close()
            except Exception:
                pass
            time.sleep(random.uniform(0.3, 1.5))
    raise RuntimeError(f"SUMO failed {attempts} times for {scenario}/{demand_level}/{policy}/seed{seed}") from last


def _run_once(
    scenario, policy, seed, gui, out_dir, policy_kwargs, demand_level,
    emergency_event=False, emergency_priority=False, emergency_cfg=None,
    record_vehicles=False,
):
    if not NET_FILE.exists():
        build_network()

    if out_dir is None:
        em_tag = ""
        if emergency_event:
            em_tag = "_em_pri" if emergency_priority else "_em"
        if demand_level == C.DEFAULT_DEMAND_LEVEL:
            out_dir = C.RESULTS_DIR / "runs" / f"{scenario}_{policy}_s{seed}{em_tag}"
        else:
            out_dir = C.RESULTS_DIR / "runs" / f"{scenario}_{demand_level}_{policy}_s{seed}{em_tag}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build deterministic routes with companion manifest
    em_cfg = emergency_cfg or C.EMERGENCY
    routes, n_vehicles = build_routes(
        scenario, seed, out_dir=out_dir, demand_level=demand_level,
        emergency_event=emergency_event, emergency_cfg=em_cfg,
    )
    manifest = load_route_manifest(routes)
    route_hash = manifest.get("route_hash")
    vehicle_origins = manifest.get("vehicle_origins")

    tripinfo = out_dir / "tripinfo.xml"

    cmd = [
        binary("sumo-gui" if gui else "sumo"),
        "-n", str(NET_FILE), "-r", str(routes), "-a", str(DET_FILE),
        "--tripinfo-output", str(tripinfo),
        "--seed", str(seed), "--step-length", str(C.SIM.step_s),
        "--time-to-teleport", "-1",          # no teleporting: jams must show up in the metrics
        "--no-step-log", "true", "--no-warnings", "true",
        "--waiting-time-memory", "3600"
    ]
    if gui:
        cmd += ["--start", "true", "--delay", "100"]
    conn_label = f"{scenario}_{demand_level}_{policy}_{seed}_{os.getpid()}_{random.randint(1000, 9999)}"
    for attempt in range(4):
        try:
            traci.start(cmd, label=conn_label)
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(0.2 * (attempt + 1) + random.uniform(0.05, 0.2))

    states = SignalStates(NET_FILE)
    kwargs = dict(policy_kwargs or {})
    if policy == "fixed_webster":
        if "scenario" not in kwargs:
            kwargs["scenario"] = scenario
        if "demand_level" not in kwargs:
            kwargs["demand_level"] = demand_level
    if emergency_priority:
        kwargs["emergency_priority"] = True
        kwargs["emergency_cfg"] = em_cfg

    run_id = f"{scenario}_{demand_level}_{policy}_s{seed}"
    if emergency_event:
        run_id += "_em_pri" if emergency_priority else "_em"

    ctl = POLICIES[policy](states, **kwargs)
    series = []
    _write_atomic_telemetry(out_dir, {
        "run_id": run_id,
        "status": "running",
        "sim_time_s": 0.0,
        "phase": "GREEN",
        "axis": "NS",
        "queues_m": {a: 0.0 for a in C.APPROACHES},
        "traffic_light_state": "",
        "updated_at": time.time(),
        "emergency_approaching": False,
        "emergency_dist_m": None,
    })
    try:
        t = 0.0
        ctl.start(t, read_queues())
        ctl.apply()
        while t < C.SIM.max_sim_time_s:
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

            series_rec = {
                "t": t, "phase": ctl.phase, "axis": ctl.axis,
                **{f"q_{a}": round(q[a], 2) for a in C.APPROACHES},
                "state": traci.trafficlight.getRedYellowGreenState(C.TLS_ID),
            }
            if emergency_event:
                series_rec["emergency_approaching"] = em_detected
                series_rec["emergency_dist_m"] = em_dist
                if emergency_priority and hasattr(ctl, "emergency_coordinator") and ctl.emergency_coordinator:
                    series_rec["emergency_status"] = ctl.emergency_coordinator.last_status

            vehs = []
            if record_vehicles:
                v_ids = traci.vehicle.getIDList()
                for vid in v_ids:
                    pos = traci.vehicle.getPosition(vid)
                    angle = traci.vehicle.getAngle(vid)
                    speed = traci.vehicle.getSpeed(vid)
                    is_em = bool(emergency_event and (vid == em_cfg.vehicle_id or "ambulance" in vid))
                    vehs.append({
                        "id": vid,
                        "x": round(pos[0], 1),
                        "y": round(pos[1], 1),
                        "a": round(angle, 1),
                        "s": round(speed, 1),
                        "em": is_em,
                    })

            series.append(series_rec)
            _write_atomic_telemetry(out_dir, {
                "run_id": run_id,
                "status": "running",
                "sim_time_s": t,
                "phase": ctl.phase,
                "axis": ctl.axis,
                "queues_m": {a: round(q[a], 2) for a in C.APPROACHES},
                "traffic_light_state": traci.trafficlight.getRedYellowGreenState(C.TLS_ID),
                "updated_at": time.time(),
                "emergency_approaching": em_detected,
                "emergency_dist_m": em_dist,
                "vehicles": vehs,
            })
            if t >= C.SIM.demand_duration_s and traci.simulation.getMinExpectedNumber() == 0:
                break
        unfinished = traci.simulation.getMinExpectedNumber()
    except Exception as e:
        _write_atomic_telemetry(out_dir, {
            "run_id": run_id,
            "status": "failed",
            "sim_time_s": t if "t" in locals() else 0.0,
            "phase": getattr(ctl, "phase", "GREEN"),
            "axis": getattr(ctl, "axis", "NS"),
            "queues_m": {a: round(q[a], 2) for a in C.APPROACHES} if "q" in locals() else {},
            "traffic_light_state": "",
            "updated_at": time.time(),
            "emergency_approaching": False,
            "emergency_dist_m": None,
            "error": str(e),
        })
        raise
    finally:
        try:
            traci.close()
        except Exception:
            pass

    _write_atomic_telemetry(out_dir, {
        "run_id": run_id,
        "status": "completed",
        "sim_time_s": t if "t" in locals() else 0.0,
        "phase": getattr(ctl, "phase", "GREEN"),
        "axis": getattr(ctl, "axis", "NS"),
        "queues_m": {a: round(q[a], 2) for a in C.APPROACHES} if "q" in locals() else {},
        "traffic_light_state": "",
        "updated_at": time.time(),
        "emergency_approaching": False,
        "emergency_dist_m": None,
    })

    _write_csv(out_dir / "timeseries.csv", series)
    _write_csv(out_dir / "decisions.csv", ctl.decisions)

    metrics = summarise_run(
        tripinfo,
        series,
        n_vehicles,
        unfinished,
        vehicle_origins=vehicle_origins,
        route_hash=route_hash,
        emergency_event=emergency_event,
        emergency_priority=emergency_priority,
        emergency_cfg=em_cfg,
    )

    metrics.update(
        scenario=scenario,
        demand_level=demand_level,
        policy=policy,
        seed=seed,
        cycles=ctl.cycle,
        run_id=run_id,
        emergency_event=emergency_event,
        emergency_priority=emergency_priority,
    )
    try:
        with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass
    return metrics


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
