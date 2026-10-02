"""Generate reproducible demand (route files) for a scenario + seed."""
import random
from pathlib import Path
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


def build_routes(scenario: str, seed: int, out_dir: Path = C.SUMO_DIR):
    """Returns (route_file_path, number_of_vehicles)."""
    prof = C.scenarios()[scenario]
    rng = random.Random(seed)
    events = []
    for a in C.APPROACHES:
        for t in _departures(prof[a], rng):
            r = rng.random()
            turn = "straight" if r < C.TURN_SPLIT["straight"] else (
                "left" if r < C.TURN_SPLIT["straight"] + C.TURN_SPLIT["left"] else "right")
            events.append((t, a, MOVES[a][turn]))
    events.sort()

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"routes_{scenario}_s{seed}.rou.xml"
    lines = ['<routes>',
             '  <vType id="car" length="5" minGap="2.5" accel="2.6" decel="4.5" sigma="0.5" maxSpeed="13.89"/>']
    for a in C.APPROACHES:
        for turn, b in MOVES[a].items():
            lines.append(f'  <route id="{a}_{b}" edges="{a}_in {b}_out"/>')
    for i, (t, a, b) in enumerate(events):
        lines.append(f'  <vehicle id="v{i}" type="car" route="{a}_{b}" depart="{t:.2f}" departLane="best" departSpeed="max"/>')
    lines.append('</routes>')
    path.write_text("\n".join(lines) + "\n")
    return path, len(events)
