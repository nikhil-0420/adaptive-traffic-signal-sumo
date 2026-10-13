"""Turn raw SUMO output into research and comparison metrics."""
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import numpy as np
from . import config as C


def summarise_run(
    tripinfo_path: Path,
    series: List[Dict],
    n_vehicles: int,
    unfinished: int,
    vehicle_origins: Optional[Dict[str, str]] = None,
    route_hash: Optional[str] = None,
    emergency_event: bool = False,
    emergency_priority: bool = False,
    emergency_cfg: Optional[C.EmergencyConfig] = None,
) -> Dict:
    """Summarise a completed simulation run with legacy, research-grade, and emergency metrics.

    Args:
        tripinfo_path: Path to SUMO tripinfo.xml.
        series: List of timeseries records (each containing 't' and 'q_<approach>').
        n_vehicles: Total number of generated vehicles.
        unfinished: Number of unfinished vehicles remaining at simulation end.
        vehicle_origins: Optional mapping of vehicle_id -> origin approach ('N', 'S', 'E', 'W').
        route_hash: SHA-256 hash of the input route file.
        emergency_event: Whether an emergency vehicle was inserted in this run.
        emergency_priority: Whether signal priority was active for the emergency vehicle.
        emergency_cfg: Configuration for the emergency event.

    Returns:
        Dict: Complete metric dictionary preserving all legacy keys and adding research & emergency metrics.
    """
    wait: List[float] = []
    loss: List[float] = []
    dur: List[float] = []
    arr: List[float] = []

    # Non-emergency separate collections
    non_em_wait: List[float] = []
    non_em_loss: List[float] = []
    non_em_dur: List[float] = []

    em_cfg = emergency_cfg or C.EMERGENCY
    em_id = em_cfg.vehicle_id if emergency_event else None
    em_record = None

    # Approach-specific wait lists
    approach_waits: Dict[str, List[float]] = {a: [] for a in C.APPROACHES}

    tree = ET.parse(tripinfo_path)
    for ti in tree.getroot().iter("tripinfo"):
        w = float(ti.get("waitingTime"))
        l = float(ti.get("timeLoss"))
        d = float(ti.get("duration"))
        a_time = float(ti.get("arrival"))
        v_id = ti.get("id")

        if emergency_event and v_id == em_id:
            em_record = {
                "completed": True,
                "wait_s": w,
                "time_loss_s": l,
                "trip_s": d,
                "arrival_s": a_time,
                "depart_s": float(ti.get("depart", 0.0)),
            }
        else:
            non_em_wait.append(w)
            non_em_loss.append(l)
            non_em_dur.append(d)

        wait.append(w)
        loss.append(l)
        dur.append(d)
        arr.append(a_time)

        if vehicle_origins and v_id in vehicle_origins:
            orig = vehicle_origins[v_id]
            if orig in approach_waits:
                approach_waits[orig].append(w)

    arrived = len(dur)
    in_window = sum(1 for a in arr if a <= C.SIM.demand_duration_s)

    # Queue series matrix
    if series:
        q_matrix = np.array([[r[f"q_{a}"] for a in C.APPROACHES] for r in series])
        approach_queues = {a: np.array([r[f"q_{a}"] for r in series]) for a in C.APPROACHES}
    else:
        q_matrix = np.zeros((1, 4))
        approach_queues = {a: np.zeros(1) for a in C.APPROACHES}

    # Base legacy metrics
    metrics = {
        "vehicles_total": n_vehicles,
        "vehicles_arrived": arrived,
        "vehicles_unfinished": int(unfinished),
        "completion_rate": arrived / n_vehicles if n_vehicles else 1.0,
        "avg_wait_s": float(np.mean(wait)) if wait else float("nan"),
        "avg_time_loss_s": float(np.mean(loss)) if loss else float("nan"),
        "avg_trip_s": float(np.mean(dur)) if dur else float("nan"),
        "p95_wait_s": float(np.percentile(wait, 95)) if wait else float("nan"),
        "avg_queue_m": float(q_matrix.mean()),
        "max_queue_m": float(q_matrix.max()),
        "throughput_veh_per_h": in_window / (C.SIM.demand_duration_s / 3600.0),
        "sim_end_s": series[-1]["t"] if series else 0.0,
        # Research extensions
        "completed_in_demand_window": int(in_window),
        "route_hash": route_hash,
    }

    # Per-approach queue summaries
    for a in C.APPROACHES:
        aq = approach_queues[a]
        metrics[f"avg_queue_{a}_m"] = float(aq.mean())
        metrics[f"max_queue_{a}_m"] = float(aq.max())

    # Per-approach wait summaries (null/None if empty group)
    valid_approach_means: List[float] = []
    for a in C.APPROACHES:
        a_list = approach_waits[a]
        count = len(a_list)
        metrics[f"n_completed_{a}"] = count if vehicle_origins is not None else None
        if count > 0:
            m_wait = float(np.mean(a_list))
            p95 = float(np.percentile(a_list, 95))
            metrics[f"avg_wait_{a}_s"] = m_wait
            metrics[f"p95_wait_{a}_s"] = p95
            valid_approach_means.append(m_wait)
        else:
            metrics[f"avg_wait_{a}_s"] = None
            metrics[f"p95_wait_{a}_s"] = None

    # Directional NS vs EW aggregation
    ns_waits = approach_waits["N"] + approach_waits["S"]
    ew_waits = approach_waits["E"] + approach_waits["W"]
    metrics["n_completed_NS"] = len(ns_waits) if vehicle_origins is not None else None
    metrics["n_completed_EW"] = len(ew_waits) if vehicle_origins is not None else None

    avg_ns = float(np.mean(ns_waits)) if ns_waits else None
    avg_ew = float(np.mean(ew_waits)) if ew_waits else None
    metrics["avg_wait_NS_s"] = avg_ns
    metrics["avg_wait_EW_s"] = avg_ew

    # Disparity metrics
    if avg_ns is not None and avg_ew is not None:
        metrics["directional_wait_disparity_s"] = round(abs(avg_ns - avg_ew), 2)
    else:
        metrics["directional_wait_disparity_s"] = None

    if len(valid_approach_means) >= 2:
        metrics["approach_wait_gap_s"] = round(max(valid_approach_means) - min(valid_approach_means), 2)
    else:
        metrics["approach_wait_gap_s"] = None

    # Emergency and background separation metrics (Phase P4)
    if emergency_event:
        if em_record is not None:
            em_metrics = {
                "emergency_event": True,
                "emergency_priority": bool(emergency_priority),
                "emergency_vehicle_id": em_id,
                "emergency_approach": em_cfg.approach,
                "emergency_completed": True,
                "emergency_wait_s": em_record["wait_s"],
                "emergency_time_loss_s": em_record["time_loss_s"],
                "emergency_trip_s": em_record["trip_s"],
                "emergency_arrival_s": em_record["arrival_s"],
                "emergency_depart_s": em_record["depart_s"],
                "non_emergency_avg_wait_s": float(np.mean(non_em_wait)) if non_em_wait else float("nan"),
                "non_emergency_avg_time_loss_s": float(np.mean(non_em_loss)) if non_em_loss else float("nan"),
                "non_emergency_avg_trip_s": float(np.mean(non_em_dur)) if non_em_dur else float("nan"),
            }
        else:
            em_metrics = {
                "emergency_event": True,
                "emergency_priority": bool(emergency_priority),
                "emergency_vehicle_id": em_id,
                "emergency_approach": em_cfg.approach,
                "emergency_completed": False,
                "emergency_wait_s": None,
                "emergency_time_loss_s": None,
                "emergency_trip_s": None,
                "emergency_arrival_s": None,
                "emergency_depart_s": None,
                "non_emergency_avg_wait_s": float(np.mean(non_em_wait)) if non_em_wait else float("nan"),
                "non_emergency_avg_time_loss_s": float(np.mean(non_em_loss)) if non_em_loss else float("nan"),
                "non_emergency_avg_trip_s": float(np.mean(non_em_dur)) if non_em_dur else float("nan"),
            }
    else:
        em_metrics = {
            "emergency_event": False,
            "emergency_priority": False,
            "emergency_vehicle_id": None,
            "emergency_approach": None,
            "emergency_completed": None,
            "emergency_wait_s": None,
            "emergency_time_loss_s": None,
            "emergency_trip_s": None,
            "emergency_arrival_s": None,
            "emergency_depart_s": None,
            "non_emergency_avg_wait_s": float(np.mean(wait)) if wait else float("nan"),
            "non_emergency_avg_time_loss_s": float(np.mean(loss)) if loss else float("nan"),
            "non_emergency_avg_trip_s": float(np.mean(dur)) if dur else float("nan"),
        }
    metrics.update(em_metrics)

    return metrics
