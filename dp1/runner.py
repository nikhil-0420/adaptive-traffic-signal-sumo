"""Run ONE simulation (scenario x policy x seed) through TraCI and write its outputs."""
import csv
import random
import time
from pathlib import Path
import traci

from . import config as C
from .controllers import POLICIES
from .metrics import summarise_run
from .network import NET_FILE, DET_FILE, build_network
from .scenarios import build_routes
from .signal_states import SignalStates
from .sumo_utils import binary


def read_queues():
    return {a: max(traci.lanearea.getJamLengthMeters(f"det_{a}_{i}") for i in range(C.NET.lanes)) for a in C.APPROACHES}


def run_simulation(scenario, policy, seed, gui=False, out_dir=None, policy_kwargs=None, attempts=5):
    """Run one simulation. Retries on TraCI connection failures (parallel runs can race for ports).

    policy_kwargs: e.g. {'cfg': AdaptiveConfig(k_s_per_m=0.2)} to override controller settings (used by tuning).
    """
    last = None
    for _ in range(attempts):
        try:
            return _run_once(scenario, policy, seed, gui, out_dir, policy_kwargs)
        except Exception as e:
            last = e
            try:
                traci.close()
            except Exception:
                pass
            time.sleep(random.uniform(0.3, 1.5))
    raise RuntimeError(f"SUMO failed {attempts} times for {scenario}/{policy}/seed{seed}") from last


def _run_once(scenario, policy, seed, gui, out_dir, policy_kwargs):
    if not NET_FILE.exists():
        build_network()
    out_dir = Path(out_dir or C.RESULTS_DIR / "runs" / f"{scenario}_{policy}_s{seed}")
    out_dir.mkdir(parents=True, exist_ok=True)
    routes, n_vehicles = build_routes(scenario, seed, out_dir=out_dir)  # per-run file: safe for parallel jobs
    tripinfo = out_dir / "tripinfo.xml"

    cmd = [binary("sumo-gui" if gui else "sumo"),
           "-n", str(NET_FILE), "-r", str(routes), "-a", str(DET_FILE),
           "--tripinfo-output", str(tripinfo),
           "--seed", str(seed), "--step-length", str(C.SIM.step_s),
           "--time-to-teleport", "-1",          # no teleporting: jams must show up in the metrics
           "--no-step-log", "true", "--no-warnings", "true",
           "--waiting-time-memory", "3600"]
    if gui:
        cmd += ["--start", "true", "--delay", "100"]
    traci.start(cmd, label=f"{scenario}_{policy}_{seed}")

    states = SignalStates(NET_FILE)
    kwargs = dict(policy_kwargs or {})
    if policy == "fixed_webster" and "scenario" not in kwargs:
        kwargs["scenario"] = scenario
    ctl = POLICIES[policy](states, **kwargs)
    series = []
    try:
        t = 0.0
        ctl.start(t, read_queues())
        ctl.apply()
        while t < C.SIM.max_sim_time_s:
            traci.simulationStep()
            t = traci.simulation.getTime()
            q = read_queues()
            ctl.step(t, q)
            series.append({"t": t, "phase": ctl.phase, "axis": ctl.axis,
                           **{f"q_{a}": round(q[a], 2) for a in C.APPROACHES},
                           "state": traci.trafficlight.getRedYellowGreenState(C.TLS_ID)})
            if t >= C.SIM.demand_duration_s and traci.simulation.getMinExpectedNumber() == 0:
                break
        unfinished = traci.simulation.getMinExpectedNumber()
    finally:
        try:
            traci.close()
        except Exception:
            pass

    _write_csv(out_dir / "timeseries.csv", series)
    _write_csv(out_dir / "decisions.csv", ctl.decisions)
    metrics = summarise_run(tripinfo, series, n_vehicles, unfinished)
    metrics.update(scenario=scenario, policy=policy, seed=seed, cycles=ctl.cycle)
    return metrics


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
