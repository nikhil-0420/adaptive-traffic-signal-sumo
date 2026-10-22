"""Deterministic scenario and route generation for the Marathahalli Bridge site network.

Supports four site demand patterns:
1. 'balanced': Equal baseline load across all four approaches.
2. 'imbalanced_orr': Heavy traffic on the Outer Ring Road (ORR North + South IT corridor).
3. 'imbalanced_varthur': Heavy traffic on Varthur Road (HAL West + Whitefield East).
4. 'surge_orr_north': Peak morning burst from K.R. Puram heading south.

Features:
- Multipliers: low (0.70x), medium (1.00x), heavy (1.30x).
- Grade separation split: through traffic splits between elevated/mainline and surface paths.
- Deterministic emergency vehicle preemption event.
- Cryptographic SHA-256 route manifest verification.
"""

import hashlib
import json
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple, Any

from . import config as C

SITE_APPROACHES = ["W", "E", "N", "S"]

# Named route edge sequences on Marathahalli network
SITE_ROUTES = {
    # West (HAL) routes
    "W_E_flyover": "hal_in flyover_eb_1 flyover_eb_2 flyover_eb_3 flyover_eb_4 wf_out",
    "W_E_surface": "hal_in ramp_hal_in leg_hal_in leg_wf_out ramp_wf_out wf_out",
    "W_N_slip": "hal_in slip_hal_to_orr_n orr_n_out",
    "W_S_surface": "hal_in ramp_hal_in leg_hal_in leg_orr_s_out ramp_orr_s_out orr_s_out",

    # East (Whitefield) routes
    "E_W_flyover": "wf_in flyover_wb_1 flyover_wb_2 flyover_wb_3 flyover_wb_4 hal_out",
    "E_W_surface": "wf_in ramp_wf_in leg_wf_in leg_hal_out ramp_hal_out hal_out",
    "E_S_slip": "wf_in slip_wf_to_orr_s orr_s_out",
    "E_N_surface": "wf_in ramp_wf_in leg_wf_in leg_orr_n_out ramp_orr_n_out orr_n_out",

    # North (K.R. Puram) routes
    "N_S_mainline": "orr_n_in orr_mainline_sb orr_s_out",
    "N_S_surface": "orr_n_in ramp_orr_n_in leg_orr_n_in leg_orr_s_out ramp_orr_s_out orr_s_out",
    "N_E_slip": "orr_n_in slip_orr_n_to_wf wf_out",
    "N_W_surface": "orr_n_in ramp_orr_n_in leg_orr_n_in leg_hal_out ramp_hal_out hal_out",

    # South (Kadubeesanahalli) routes
    "S_N_mainline": "orr_s_in orr_mainline_nb orr_n_out",
    "S_N_surface": "orr_s_in ramp_orr_s_in leg_orr_s_in leg_orr_n_out ramp_orr_n_out orr_n_out",
    "S_W_slip": "orr_s_in slip_orr_s_to_hal hal_out",
    "S_E_surface": "orr_s_in ramp_orr_s_in leg_orr_s_in leg_wf_out ramp_wf_out wf_out",
}

# Base hourly rates for 1800s simulation window (vph)
SITE_DEMAND_PATTERNS = {
    "balanced": {
        "W": [(0, 1800, 650)],
        "E": [(0, 1800, 650)],
        "N": [(0, 1800, 650)],
        "S": [(0, 1800, 650)],
    },
    "imbalanced_orr": {
        "W": [(0, 1800, 400)],
        "E": [(0, 1800, 400)],
        "N": [(0, 1800, 1050)],
        "S": [(0, 1800, 1050)],
    },
    "imbalanced_varthur": {
        "W": [(0, 1800, 1050)],
        "E": [(0, 1800, 1050)],
        "N": [(0, 1800, 400)],
        "S": [(0, 1800, 400)],
    },
    "surge_orr_north": {
        "W": [(0, 1800, 500)],
        "E": [(0, 1800, 500)],
        "N": [(0, 400, 600), (400, 1000, 1500), (1000, 1800, 600)],
        "S": [(0, 1800, 650)],
    },
}

DEMAND_MULTIPLIERS = {
    "low": 0.70,
    "medium": 1.00,
    "heavy": 1.30,
}


def get_site_scenarios(demand_level: str = "medium") -> Dict[str, Dict[str, List[Tuple[int, int, int]]]]:
    """Return scaled rate profiles for the requested demand level."""
    mult = DEMAND_MULTIPLIERS.get(demand_level, 1.0)
    scaled = {}
    for pat_name, app_map in SITE_DEMAND_PATTERNS.items():
        scaled[pat_name] = {}
        for app, intervals in app_map.items():
            scaled[pat_name][app] = [
                (t0, t1, int(round(vph * mult)))
                for t0, t1, vph in intervals
            ]
    return scaled


def _departures(profile: List[Tuple[int, int, int]], rng: random.Random) -> List[float]:
    """Generate Poisson departures."""
    times = []
    for t0, t1, vph in profile:
        if vph <= 0:
            continue
        rate = vph / 3600.0
        t = t0 + rng.expovariate(rate)
        while t < t1:
            times.append(t)
            t += rng.expovariate(rate)
    return times


def build_site_routes(
    scenario: str = "balanced",
    seed: int = 101,
    out_dir: Optional[Path] = None,
    demand_level: str = "medium",
    emergency_event: bool = False,
    emergency_cfg: Optional[C.EmergencyConfig] = None,
) -> Tuple[Path, int]:
    """Generate deterministic route XML and companion manifest JSON for Marathahalli network."""
    scenarios_map = get_site_scenarios(demand_level=demand_level)
    if scenario not in scenarios_map:
        raise ValueError(f"Unknown site scenario '{scenario}'. Available: {list(scenarios_map.keys())}")

    prof = scenarios_map[scenario]
    rng = random.Random(seed)
    events: List[Tuple[float, str, str]] = []
    vehicle_records: List[Dict[str, Any]] = []

    # Movement turn probabilities for site:
    # Through traffic: 65% (of which 70% uses elevated/mainline, 30% uses surface)
    # Left turn: 20% (uses channelized slip road)
    # Right turn: 15% (uses surface signal-controlled junction)
    for app in SITE_APPROACHES:
        for t in _departures(prof[app], rng):
            r = rng.random()
            if r < 0.65:
                # Through movement
                if app == "W":
                    r_id = "W_E_flyover" if rng.random() < 0.70 else "W_E_surface"
                elif app == "E":
                    r_id = "E_W_flyover" if rng.random() < 0.70 else "E_W_surface"
                elif app == "N":
                    r_id = "N_S_mainline" if rng.random() < 0.70 else "N_S_surface"
                else:  # S
                    r_id = "S_N_mainline" if rng.random() < 0.70 else "S_N_surface"
            elif r < 0.85:
                # Left turn (slip road)
                if app == "W":
                    r_id = "W_N_slip"
                elif app == "E":
                    r_id = "E_S_slip"
                elif app == "N":
                    r_id = "N_E_slip"
                else:  # S
                    r_id = "S_W_slip"
            else:
                # Right turn (surface signal junction)
                if app == "W":
                    r_id = "W_S_surface"
                elif app == "E":
                    r_id = "E_N_surface"
                elif app == "N":
                    r_id = "N_W_surface"
                else:  # S
                    r_id = "S_E_surface"

            events.append((t, app, r_id))

    events.sort(key=lambda x: x[0])

    if out_dir is None:
        out_dir = C.ROOT / "network" / "marathahalli" / "dist" / "routes"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    em_tag = "_em" if emergency_event else ""
    route_filename = f"routes_marathahalli_{scenario}_{demand_level}{em_tag}_s{seed}.rou.xml"
    route_path = out_dir / route_filename

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '  <vType id="car" length="5.0" minGap="2.5" accel="2.6" decel="4.5" sigma="0.5" maxSpeed="16.67"/>'
    ]

    em_cfg = emergency_cfg or C.EMERGENCY
    if emergency_event:
        lines.append(
            f'  <vType id="emergency" vClass="{em_cfg.vclass}" guiShape="emergency" length="6.5" minGap="2.5" '
            f'accel="{em_cfg.accel}" decel="{em_cfg.decel}" sigma="0.2" maxSpeed="{em_cfg.speed_m_s}" color="{em_cfg.color}"/>'
        )

    # Route definitions
    for r_id, edges in SITE_ROUTES.items():
        lines.append(f'  <route id="{r_id}" edges="{edges}"/>')

    # Ordinary vehicles
    for i, (t, app, r_id) in enumerate(events):
        v_id = f"v{i}"
        vehicle_records.append({
            "id": v_id,
            "origin": app,
            "route_id": r_id,
            "depart": round(t, 2),
            "emergency": False,
        })

    # Emergency vehicle insertion
    if emergency_event:
        # Ambulance enters on South approach and takes surface route through marathahalli_tls
        em_route_id = "S_N_surface"
        vehicle_records.append({
            "id": em_cfg.vehicle_id,
            "origin": "S",
            "route_id": em_route_id,
            "depart": round(em_cfg.depart_time_s, 2),
            "emergency": True,
        })

    vehicle_records.sort(key=lambda r: (r["depart"], r["id"]))

    for vr in vehicle_records:
        v_type = "emergency" if vr["emergency"] else "car"
        lines.append(
            f'  <vehicle id="{vr["id"]}" type="{v_type}" route="{vr["route_id"]}" '
            f'depart="{vr["depart"]:.2f}" departLane="best" departSpeed="max"/>'
        )

    lines.append('</routes>')
    xml_text = "\n".join(lines) + "\n"
    route_path.write_text(xml_text, encoding="utf-8")

    route_hash = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()

    manifest_path = route_path.with_name(f"{route_path.name}.manifest.json")
    manifest = {
        "network_name": "marathahalli",
        "scenario": scenario,
        "demand_level": demand_level,
        "seed": seed,
        "emergency_event": emergency_event,
        "total_vehicles": len(vehicle_records),
        "route_file": str(route_path),
        "route_hash": route_hash,
        "vehicles": {vr["id"]: vr["origin"] for vr in vehicle_records}
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return route_path, len(vehicle_records)


def site_webster_plan(
    scenario: str,
    timing: Optional[C.SignalTiming] = None,
    cfg: Optional[C.WebsterConfig] = None,
    demand_level: str = C.DEFAULT_DEMAND_LEVEL,
) -> C.FixedTimeConfig:
    """Compute Webster's optimal fixed-time plan for Marathahalli site demand."""
    scens = get_site_scenarios(demand_level=demand_level)
    if scenario not in scens:
        raise KeyError(f"Unknown site scenario: {scenario}")
    prof = scens[scenario]
    timing = timing or C.TIMING
    cfg = cfg or C.WEBSTER
    duration = float(C.SIM.demand_duration_s)

    avg_flows = {}
    for a in SITE_APPROACHES:
        segments = prof[a]
        total_veh = sum((t1 - t0) * (vph / 3600.0) for t0, t1, vph in segments)
        avg_flows[a] = total_veh * (3600.0 / duration)

    # 2 lanes per surface approach leg
    sat_flow = cfg.sat_flow_per_lane_vph * 2
    # In site demand, through traffic uses 30% surface, right turns use 15% surface
    # Approach traffic arriving at surface signal is approx 35% of total approach flow
    surface_factor = 0.35
    y_ns = (max(avg_flows["N"], avg_flows["S"]) * surface_factor) / sat_flow
    y_ew = (max(avg_flows["W"], avg_flows["E"]) * surface_factor) / sat_flow

    Y = y_ns + y_ew
    L = 2.0 * (timing.yellow_s + timing.all_red_s)
    if Y >= 1.0:
        c_opt = cfg.max_cycle_s
    else:
        c_opt = (1.5 * L + 5.0) / (1.0 - Y)
    cycle = max(cfg.min_cycle_s, min(cfg.max_cycle_s, c_opt))

    total_green = max(0.0, cycle - L)
    if Y > 0:
        g_ns = total_green * (y_ns / Y)
        g_ew = total_green * (y_ew / Y)
    else:
        g_ns = total_green / 2.0
        g_ew = total_green / 2.0

    min_g = 10.0
    g_ns = max(min_g, g_ns)
    g_ew = max(min_g, g_ew)

    return C.FixedTimeConfig(green_ns_s=round(g_ns, 1), green_ew_s=round(g_ew, 1))

