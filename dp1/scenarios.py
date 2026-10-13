"""Generate reproducible demand (route files) for a scenario + demand_level + seed."""
import hashlib
import json
from pathlib import Path
import random
from typing import Dict, Optional, Tuple

from . import config as C

# movement -> (from approach, to approach). Right-hand traffic.
MOVES = {
    "N": {"straight": "S", "left": "E", "right": "W"},
    "S": {"straight": "N", "left": "W", "right": "E"},
    "E": {"straight": "W", "left": "S", "right": "N"},
    "W": {"straight": "E", "left": "N", "right": "S"},
}


def _departures(profile, rng):
    """Poisson arrivals for a piecewise-constant rate profile [(t0, t1, vph), ...]."""
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


def hash_file_content(path: Path) -> str:
    """Compute deterministic SHA-256 digest of file content."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_routes(
    scenario: str,
    seed: int,
    out_dir: Path = C.SUMO_DIR,
    demand_level: str = C.DEFAULT_DEMAND_LEVEL,
    emergency_event: bool = False,
    emergency_cfg: Optional[C.EmergencyConfig] = None,
) -> Tuple[Path, int]:
    """Generate deterministic route XML and companion manifest JSON.

    Args:
        scenario: Demand pattern name.
        seed: Random seed for departure generation.
        out_dir: Output directory for route file.
        demand_level: Flow scale ('low', 'medium', 'heavy').
        emergency_event: If True, inserts deterministic ambulance vehicle.
        emergency_cfg: Configuration for emergency vehicle event.

    Returns:
        Tuple[Path, int]: (route_file_path, total_number_of_vehicles)
    """
    prof = C.scenarios(demand_level=demand_level)[scenario]
    rng = random.Random(seed)
    events = []
    vehicle_origins: Dict[str, str] = {}
    vehicle_records = []

    # 1. Deterministic generation of background ordinary vehicles
    for a in C.APPROACHES:
        for t in _departures(prof[a], rng):
            r = rng.random()
            turn = "straight" if r < C.TURN_SPLIT["straight"] else (
                "left" if r < C.TURN_SPLIT["straight"] + C.TURN_SPLIT["left"] else "right")
            events.append((t, a, MOVES[a][turn]))
    events.sort()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Naming convention: preserve legacy filename for non-emergency, add _em for emergency
    em_tag = "_em" if emergency_event else ""
    if demand_level == C.DEFAULT_DEMAND_LEVEL:
        path = out_dir / f"routes_{scenario}{em_tag}_s{seed}.rou.xml"
    else:
        path = out_dir / f"routes_{scenario}_{demand_level}{em_tag}_s{seed}.rou.xml"

    lines = [
        '<routes>',
        '  <vType id="car" length="5" minGap="2.5" accel="2.6" decel="4.5" sigma="0.5" maxSpeed="13.89"/>'
    ]

    em_cfg = emergency_cfg or C.EMERGENCY
    if emergency_event:
        lines.append(
            f'  <vType id="emergency" vClass="{em_cfg.vclass}" guiShape="emergency" length="6.5" minGap="2.5" '
            f'accel="{em_cfg.accel}" decel="{em_cfg.decel}" sigma="0.2" maxSpeed="{em_cfg.speed_m_s}" color="{em_cfg.color}"/>'
        )

    for a in C.APPROACHES:
        for turn, b in MOVES[a].items():
            lines.append(f'  <route id="{a}_{b}" edges="{a}_in {b}_out"/>')

    # Add ordinary vehicles
    for i, (t, a, b) in enumerate(events):
        v_id = f"v{i}"
        vehicle_origins[v_id] = a
        vehicle_records.append({
            "id": v_id,
            "origin": a,
            "destination": b,
            "depart": round(t, 2),
            "emergency": False,
        })

    # Add deterministic emergency vehicle if enabled
    if emergency_event:
        app = em_cfg.approach
        dest = MOVES[app][em_cfg.turn]
        vehicle_origins[em_cfg.vehicle_id] = app
        vehicle_records.append({
            "id": em_cfg.vehicle_id,
            "origin": app,
            "destination": dest,
            "depart": round(em_cfg.depart_time_s, 2),
            "emergency": True,
        })

    # Ensure all vehicles are strictly sorted by departure time for SUMO
    vehicle_records.sort(key=lambda r: (r["depart"], r["id"]))

    for vr in vehicle_records:
        v_type = "emergency" if vr["emergency"] else "car"
        route_name = f"{vr['origin']}_{vr['destination']}"
        lines.append(
            f'  <vehicle id="{vr["id"]}" type="{v_type}" route="{route_name}" '
            f'depart="{vr["depart"]:.2f}" departLane="best" departSpeed="max"/>'
        )

    lines.append('</routes>')

    xml_text = "\n".join(lines) + "\n"
    path.write_text(xml_text, encoding="utf-8")

    # Compute SHA-256 hash of the generated route XML
    route_hash = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()

    # Write companion manifest for audit and origin attribution
    manifest_path = path.with_name(f"{path.name}.manifest.json")
    manifest_data = {
        "route_hash": route_hash,
        "scenario": scenario,
        "demand_level": demand_level,
        "demand_multiplier": C.DEMAND_LEVELS[demand_level],
        "seed": seed,
        "n_vehicles": len(vehicle_records),
        "emergency_event": emergency_event,
        "emergency_vehicle_id": em_cfg.vehicle_id if emergency_event else None,
        "vehicle_origins": vehicle_origins,
        "vehicles": vehicle_records,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return path, len(vehicle_records)


def load_route_manifest(route_file: Path) -> dict:
    """Load the companion manifest for a route file."""
    manifest_path = route_file.with_name(f"{route_file.name}.manifest.json")
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
