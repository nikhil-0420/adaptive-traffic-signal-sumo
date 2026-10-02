"""Turn raw SUMO output into the comparison metrics used in the report."""
import xml.etree.ElementTree as ET
import numpy as np
from . import config as C


def summarise_run(tripinfo_path, series, n_vehicles, unfinished):
    wait, loss, dur, arr = [], [], [], []
    for ti in ET.parse(tripinfo_path).getroot().iter("tripinfo"):
        wait.append(float(ti.get("waitingTime")))
        loss.append(float(ti.get("timeLoss")))
        dur.append(float(ti.get("duration")))
        arr.append(float(ti.get("arrival")))
    # throughput = vehicles that FINISHED inside the demand window, scaled to veh/h
    in_window = sum(1 for a in arr if a <= C.SIM.demand_duration_s)
    queues = np.array([[r[f"q_{a}"] for a in C.APPROACHES] for r in series]) if series else np.zeros((1, 4))
    arrived = len(dur)
    return {
        "vehicles_total": n_vehicles,
        "vehicles_arrived": arrived,
        "vehicles_unfinished": int(unfinished),
        "completion_rate": arrived / n_vehicles if n_vehicles else 1.0,
        "avg_wait_s": float(np.mean(wait)) if wait else float("nan"),
        "avg_time_loss_s": float(np.mean(loss)) if loss else float("nan"),
        "avg_trip_s": float(np.mean(dur)) if dur else float("nan"),
        "p95_wait_s": float(np.percentile(wait, 95)) if wait else float("nan"),
        "avg_queue_m": float(queues.mean()),          # mean over all approaches and seconds
        "max_queue_m": float(queues.max()),
        "throughput_veh_per_h": in_window / (C.SIM.demand_duration_s / 3600.0),
        "sim_end_s": series[-1]["t"] if series else 0.0,
    }
