"""All tunable numbers live here. Change values here, never hard-code them elsewhere."""
from dataclasses import dataclass, field
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
class WebsterConfig:
    sat_flow_per_lane_vph: float = 1800.0
    min_cycle_s: float = 40.0
    max_cycle_s: float = 120.0


@dataclass(frozen=True)
class AdaptiveConfig:
    min_green_s: int = 10
    max_green_s: int = 60
    k_s_per_m: float = 0.30       # extra green seconds per metre of queue
    gap_out_s: int = 3            # end green early if own queue is empty this long ...
    extend_threshold_m: float = 15.0  # ... and keep extending while queue is above this
    min_competing_queue_m: float = 1.0  # only gap-out if the other axis is actually waiting


@dataclass(frozen=True)
class PressureConfig:
    min_green_s: int = 10
    max_green_s: int = 60
    k_s_per_m: float = 0.30       # extra green seconds per metre of queue difference
    gap_out_s: int = 3            # end green early if own queue is empty this long ...
    extend_threshold_m: float = 15.0  # ... and keep extending while queue is above this
    min_competing_queue_m: float = 1.0  # only gap-out if the other axis is actually waiting


@dataclass(frozen=True)
class ActionConfig:
    """Action seam configuration for external / RL controllers."""
    min_green_s: float = 10.0
    max_green_s: float = 60.0
    action_hold: int = 0
    action_switch: int = 1


@dataclass(frozen=True)
class SimConfig:
    step_s: float = 1.0
    demand_duration_s: int = 1800
    max_sim_time_s: int = 3600     # drain time cap after demand stops
    seeds: tuple = (1, 2, 3, 4, 5)


TUNE_SEARCH_SPACE = {
    "k_s_per_m": (0.15, 0.2, 0.3, 0.4, 0.5),
    "max_green_s": (30, 40, 45, 60),
    "min_green_s": (8, 10, 12),
    "gap_out_s": (2, 3, 5),
}
TRAIN_SEEDS = (1, 2, 3, 4, 5)
RL_VALIDATION_SEEDS = (6, 7, 8, 9, 10)
HELD_OUT_SEEDS = (11, 12, 13, 14, 15)
RESEARCH_EVAL_SEEDS = tuple(range(21, 31))


@dataclass(frozen=True)
class RLConfig:
    """Hyperparameters and configuration for RL environment and DQN controller."""
    # Action & green bounds
    min_green_s: float = 10.0
    max_green_s: float = 60.0
    action_hold: int = 0
    action_switch: int = 1

    # Observation space
    obs_dim: int = 11
    max_detector_m: float = 150.0  # normalization denominator for queues

    # Reward weights (per-second normalized reward)
    queue_weight: float = 1.0       # penalty weight for total normalized queue
    switch_penalty: float = 0.05    # penalty applied on accepted switch to discourage oscillation
    wait_weight: float = 0.0        # optional waiting-time component weight

    # Training hyperparameters
    learning_rate: float = 1e-3
    buffer_size: int = 10_000
    learning_starts: int = 100
    batch_size: int = 32
    tau: float = 1.0
    gamma: float = 0.99
    train_freq: int = 4
    gradient_steps: int = 1
    target_update_interval: int = 250
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.05
    exploration_fraction: float = 0.20
    total_timesteps: int = 10_000

    # Seed splits
    train_seeds: tuple = (1, 2, 3, 4, 5)
    validation_seeds: tuple = (6, 7, 8, 9, 10)
    eval_seeds: tuple = (11, 12, 13, 14, 15)
    research_seeds: tuple = tuple(range(21, 31))

    # Output paths
    models_dir: Path = RESULTS_DIR / "models"
    logs_dir: Path = RESULTS_DIR / "rl_logs"
    default_model_name: str = "dqn_dp1_latest"


NET = NetworkConfig()
TIMING = SignalTiming()
WEBSTER = WebsterConfig()

# Old 30/30 plan kept for reference
FIXED_PLACEHOLDER = FixedTimeConfig(green_ns_s=30, green_ew_s=30)

# BTP Marathalli Bridge Junction (weekday 08:00-11:30): Phase 1 = 110s (NS), Phase 2 = 100s (EW)
# Net green computed from TIMING by subtracting yellow and all-red clearance intervals
FIXED = FixedTimeConfig(
    green_ns_s=110 - (TIMING.yellow_s + TIMING.all_red_s),
    green_ew_s=100 - (TIMING.yellow_s + TIMING.all_red_s),
)
ADAPTIVE = AdaptiveConfig()
PRESSURE = PressureConfig()
ACTION = ActionConfig()
RL = RLConfig()
SIM = SimConfig()

# Demand levels and multipliers (P3)
DEMAND_LEVELS = {
    "low": 0.70,
    "medium": 1.00,
    "heavy": 1.30,
}
DEFAULT_DEMAND_LEVEL = "medium"

# Demand scenarios: vehicles/hour per approach, as piecewise segments (t_start, t_end, vph)
DEMAND_SCALE = 1.7


def scenarios(duration=SIM.demand_duration_s, demand_level: str = DEFAULT_DEMAND_LEVEL):
    if demand_level not in DEMAND_LEVELS:
        raise ValueError(f"Unknown demand_level: {demand_level}. Allowed: {list(DEMAND_LEVELS.keys())}")
    mult = DEMAND_LEVELS[demand_level]
    d = duration

    def _scaled_flat(vph):
        return [(0, d, vph * DEMAND_SCALE * mult)]

    return {
        "balanced":      {a: _scaled_flat(400) for a in APPROACHES},
        "imbalanced_ns": {"N": _scaled_flat(700), "S": _scaled_flat(700), "E": _scaled_flat(200), "W": _scaled_flat(200)},
        "imbalanced_ew": {"N": _scaled_flat(200), "S": _scaled_flat(200), "E": _scaled_flat(700), "W": _scaled_flat(700)},
        "surge_north":   {"N": [(0, 600, 400 * DEMAND_SCALE * mult), (600, 1200, 1100 * DEMAND_SCALE * mult), (1200, d, 400 * DEMAND_SCALE * mult)],
                          "S": _scaled_flat(400), "E": _scaled_flat(400), "W": _scaled_flat(400)},
    }


def webster_plan(scenario: str, net=NET, timing=TIMING, cfg=WEBSTER, demand_level: str = DEFAULT_DEMAND_LEVEL) -> FixedTimeConfig:
    """Compute Webster's optimal fixed-time plan from average scenario demand scaled by demand level."""
    scens = scenarios(demand_level=demand_level)
    if scenario not in scens:
        raise KeyError(f"Unknown scenario: {scenario}")
    prof = scens[scenario]
    duration = SIM.demand_duration_s

    # 1. Average flow (vph) per approach over demand duration
    avg_flows = {}
    for a in APPROACHES:
        segments = prof[a]
        total_veh = sum((t1 - t0) * (vph / 3600.0) for t0, t1, vph in segments)
        avg_flows[a] = total_veh * (3600.0 / duration)

    # 2. Critical flow ratio per axis: y = flow / saturation_flow
    sat_flow = cfg.sat_flow_per_lane_vph * net.lanes
    y_ns = max(avg_flows[a] for a in AXES["NS"]) / sat_flow
    y_ew = max(avg_flows[a] for a in AXES["EW"]) / sat_flow

    # 3. Y = y_NS + y_EW
    Y = y_ns + y_ew

    # 4. Lost time L = 2 * (yellow + all_red)
    L = 2.0 * (timing.yellow_s + timing.all_red_s)

    # 5. Cycle C = (1.5*L + 5)/(1 - Y) clamped to 40-120 s
    if Y >= 1.0:
        c_opt = cfg.max_cycle_s
    else:
        c_opt = (1.5 * L + 5.0) / (1.0 - Y)
    cycle = max(cfg.min_cycle_s, min(cfg.max_cycle_s, c_opt))

    # 6. Effective green split proportional to y: total green = C - L
    total_green = max(0.0, cycle - L)
    if Y > 0:
        g_ns = total_green * (y_ns / Y)
        g_ew = total_green * (y_ew / Y)
    else:
        g_ns = total_green / 2.0
        g_ew = total_green / 2.0

    return FixedTimeConfig(green_ns_s=round(g_ns, 1), green_ew_s=round(g_ew, 1))


# Turning split for every approach
TURN_SPLIT = {"straight": 0.70, "left": 0.15, "right": 0.15}


@dataclass(frozen=True)
class ResearchConfig:
    """Settings for the 600-run research-grade evaluation matrix and statistical analysis."""
    patterns: tuple = ("balanced", "imbalanced_ns", "imbalanced_ew", "surge_north")
    levels: tuple = ("low", "medium", "heavy")
    policies: tuple = ("fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn")
    seeds: tuple = tuple(range(21, 31))  # RESEARCH_EVAL_SEEDS (21..30)
    bootstrap_resamples: int = 10_000
    bootstrap_seed: int = 42
    confidence_level: float = 0.95
    research_dir: Path = RESULTS_DIR / "research"


@dataclass(frozen=True)
class EmergencyConfig:
    """Configuration for deterministic emergency vehicle event and priority (P4)."""
    detection_dist_m: float = 100.0
    min_green_s: float = 10.0
    max_extension_s: float = 30.0
    depart_time_s: float = 300.0
    approach: str = "N"
    turn: str = "straight"
    vehicle_id: str = "ambulance"
    speed_m_s: float = 19.44
    accel: float = 3.5
    decel: float = 5.5
    vclass: str = "emergency"
    color: str = "1,0,0"
    event_enabled: bool = False
    priority_enabled: bool = False


RESEARCH = ResearchConfig()
EMERGENCY = EmergencyConfig()
