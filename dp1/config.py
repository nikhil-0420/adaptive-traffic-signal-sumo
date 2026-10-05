"""All tunable numbers live here. Change values here, never hard-code them elsewhere."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMO_DIR = ROOT / "sumo"
RESULTS_DIR = ROOT / "results"

APPROACHES = ["N", "S", "E", "W"]
AXES = {"NS": ["N", "S"], "EW": ["E", "W"]}
AXIS_OF = {"N": "NS", "S": "NS", "E": "EW", "W": "EW"}
OTHER_AXIS = {"NS": "EW", "EW": "NS"}
TLS_ID = "C"


@dataclass(frozen=True)
class NetworkConfig:
    approach_length_m: float = 300.0
    speed_mps: float = 13.89          # 50 km/h
    detector_length_m: float = 150.0  # sensor zone measured back from the stop line
    lanes: int = 2


@dataclass(frozen=True)
class SignalTiming:
    """Shared by BOTH controllers so the comparison is fair."""
    yellow_s: int = 3
    all_red_s: int = 2


@dataclass(frozen=True)
class FixedTimeConfig:
    green_ns_s: float = 105.0
    green_ew_s: float = 95.0


@dataclass(frozen=True)
class AdaptiveConfig:
    min_green_s: int = 10
    max_green_s: int = 60
    k_s_per_m: float = 0.30       # extra green seconds per metre of queue
    gap_out_s: int = 3            # end green early if own queue is empty this long ...
    extend_threshold_m: float = 15.0  # ... and keep extending while queue is above this
    min_competing_queue_m: float = 1.0  # only gap-out if the other axis is actually waiting


@dataclass(frozen=True)
class SimConfig:
    step_s: float = 1.0
    demand_duration_s: int = 1800
    max_sim_time_s: int = 3600     # drain time cap after demand stops
    seeds: tuple = (1, 2, 3, 4, 5)


NET = NetworkConfig()
TIMING = SignalTiming()

# Old 30/30 plan kept for reference
FIXED_PLACEHOLDER = FixedTimeConfig(green_ns_s=30, green_ew_s=30)

# BTP Marathalli Bridge Junction (weekday 08:00-11:30): Phase 1 = 110s (NS), Phase 2 = 100s (EW)
# Net green computed from TIMING by subtracting yellow and all-red clearance intervals
FIXED = FixedTimeConfig(
    green_ns_s=110 - (TIMING.yellow_s + TIMING.all_red_s),
    green_ew_s=100 - (TIMING.yellow_s + TIMING.all_red_s),
)
ADAPTIVE = AdaptiveConfig()
SIM = SimConfig()

# Demand scenarios: vehicles/hour per approach, as piecewise segments (t_start, t_end, vph)
DEMAND_SCALE = 1.7


def _flat(vph, end):
    return [(0, end, vph * DEMAND_SCALE)]


def scenarios(duration=SIM.demand_duration_s):
    d = duration
    return {
        "balanced":      {a: _flat(400, d) for a in APPROACHES},
        "imbalanced_ns": {"N": _flat(700, d), "S": _flat(700, d), "E": _flat(200, d), "W": _flat(200, d)},
        "imbalanced_ew": {"N": _flat(200, d), "S": _flat(200, d), "E": _flat(700, d), "W": _flat(700, d)},
        "surge_north":   {"N": [(0, 600, 400 * DEMAND_SCALE), (600, 1200, 1100 * DEMAND_SCALE), (1200, d, 400 * DEMAND_SCALE)],
                          "S": _flat(400, d), "E": _flat(400, d), "W": _flat(400, d)},
    }


# Turning split for every approach
TURN_SPLIT = {"straight": 0.70, "left": 0.15, "right": 0.15}
