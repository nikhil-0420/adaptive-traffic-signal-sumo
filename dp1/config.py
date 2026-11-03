"""All tunable numbers live here. Change values here, never hard-code them elsewhere."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
class QueueExtensionConfig:
    """Settings for bounded queue-extension traffic signal controller."""
    min_green_s: float = 10.0           # Minimum green duration before any switch can be considered
    max_green_s: float = 60.0           # Hard upper bound on green phase duration
    initial_green_s: float = 15.0       # Initial green granted upon phase entry
    extend_step_s: float = 3.0          # Green increment granted per extension evaluation
    extend_threshold_m: float = 4.0     # Minimum active approach queue required to justify extension
    min_competing_queue_m: float = 2.0  # Competing queue threshold triggering anti-monopoly fairness
    max_competing_wait_s: float = 35.0  # Maximum red wait time for competing axis before switch is forced
    fairness_ratio: float = 1.2         # Competing queue accumulation factor vs active queue
    gap_out_s: float = 3.0              # Gap-out persistence duration when active queue clears


@dataclass(frozen=True)
class HybridQueueAdaptiveConfig:
    """Settings for Hybrid Queue-Adaptive traffic signal controller.

    Combines:
    1. Baseline Webster-derived green allocation (G_base) appropriate to Marathahalli/scenario demand.
    2. Dynamic queue-aware green extensions (delta_G = 3s increments) evaluated each step.
    3. Safety and fairness supervisor enforcing min_green, max_green, anti-monopoly waiting limits,
       and gap-out clearance.
    """
    min_green_s: float = 10.0           # Minimum green duration before any switch can be considered
    max_green_s: float = 60.0           # Hard upper bound on green phase duration
    extend_step_s: float = 3.0          # Green increment granted per approved extension evaluation
    extend_threshold_m: float = 4.0     # Minimum active approach queue required to justify extension
    min_competing_queue_m: float = 2.0  # Competing queue threshold triggering anti-monopoly fairness
    max_competing_wait_s: float = 35.0  # Maximum red wait time for competing axis before switch is forced
    fairness_ratio: float = 1.2         # Competing queue accumulation factor vs active queue
    gap_out_s: float = 3.0              # Gap-out persistence duration when active queue clears
    k_s_per_m: float = 0.30             # Green scaling factor per metre of queue
    demand_weight_active: float = 1.0   # Weight for active approach queue in demand score
    demand_weight_competing: float = 1.0 # Weight for competing approach queue in demand score
    arrival_detection_threshold: float = 0.5 # Min queue delta to detect active arrivals

    # Ablation Ladder Rung Configuration
    rungs: tuple = ()                   # Active rungs: e.g. ("R2",), ("R2", "R3"), ("R2", "R3", "R4")
    # R2: Comparative extension parameters
    r2_margin: float = 1.0              # Multiplier on competing score (1.0 = parity)
    r2_switch_cost_m: float = 5.0       # 5.0s lost clearance time in score units (5.0m effective queue)
    # R3: Queue-aware fairness parameters
    r3_soft_min_wait_s: float = 20.0    # Min competing wait before soft queue-aware fairness triggers
    r3_queue_ref_m: float = 20.0        # Reference competing queue scaling soft wait limit
    r3_hard_wait_cap_s: float = 35.0    # Hard anti-starvation cap regardless of competing queue
    # R4: Measured Webster baseline green
    r4_warmup_s: float = 300.0          # Measured arrival estimation window for Webster baseline green

    # Phase 12: Short-Horizon Queue Projection
    projection_enabled: bool = False    # Predictive short-horizon queue projection intervention
    projection_window_s: float = 15.0   # Sliding window W [seconds] for arrival rate smoothing
    projection_horizon_s: float = 6.0   # Short-horizon lookahead h [seconds]
    projection_blend_alpha: float = 0.5 # Convex blend weight alpha: q_eff = (1 - alpha)*q + alpha*q_pred
    projection_sat_flow_fallback_mps: float = 7.5 # Saturation discharge capacity fallback [m/s]


@dataclass(frozen=True)
class WebsterMeasuredConfig:
    """Settings for measured Webster baseline (flows measured in warm-up, then fixed)."""
    warmup_s: float = 300.0              # Approved 5-minute warm-up window
    sat_flow_per_lane_vph: float = 1800.0
    min_cycle_s: float = 40.0
    max_cycle_s: float = 120.0
    min_green_s: float = 10.0


@dataclass(frozen=True)
class WebsterRecalcConfig:
    """Settings for periodically recalculated Webster baseline (sliding window)."""
    recalc_interval_s: float = 300.0     # Approved 5-minute recalculation interval (N)
    window_s: float = 300.0              # Approved 5-minute sliding measurement window (W)
    sat_flow_per_lane_vph: float = 1800.0
    min_cycle_s: float = 40.0
    max_cycle_s: float = 120.0
    min_green_s: float = 10.0


@dataclass(frozen=True)
class FixedMatchedCycleConfig:
    """Settings for fixed plan matching Webster's cycle length with BTP split ratio."""
    btp_split_ratio_ew: float = 0.525    # 105 / 200 = 52.5% Varthur (EW)
    btp_split_ratio_ns: float = 0.475    # 95 / 200 = 47.5% ORR (NS)
    min_green_s: float = 10.0


@dataclass(frozen=True)
class SumoActuatedConfig:
    """Settings for SUMO built-in actuated traffic signal logic with detectors."""
    min_green_s: float = 10.0            # SUMO minDur: minimum green duration
    max_green_s: float = 60.0            # SUMO maxDur: maximum green duration
    max_gap_s: float = 3.0               # SUMO max-gap: vehicle time headway before gap-out
    detector_gap_s: float = 3.0          # SUMO detector-gap



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

# BTP Baseline Signal Timings (weekday 08:00-11:30):
# Phase 1 = 110s, Phase 2 = 100s, Pedestrian = 15s (effective vehicle cycle = 210s)
# Net green computed from TIMING by subtracting yellow (3s) and all-red (2s) clearance intervals (5s lost time per phase).
# Synthetic network: historical mapping Phase 1 -> NS (105s), Phase 2 -> EW (95s) (preserved for baseline backward compatibility).
FIXED = FixedTimeConfig(
    green_ns_s=110 - (TIMING.yellow_s + TIMING.all_red_s),  # 105.0s
    green_ew_s=100 - (TIMING.yellow_s + TIMING.all_red_s),  # 95.0s
)

# Marathahalli real-road site network:
# Varthur Road (HAL Airport Rd <-> Whitefield) is the East-West axis (EW), corresponding to BTP Phase 1 (110s field -> 105s green).
# Outer Ring Road (Kadubeesanahalli <-> KR Puram) is the North-South axis (NS), corresponding to BTP Phase 2 (100s field -> 95s green).
FIXED_MARATHAHALLI = FixedTimeConfig(
    green_ns_s=100 - (TIMING.yellow_s + TIMING.all_red_s),  # 95.0s
    green_ew_s=110 - (TIMING.yellow_s + TIMING.all_red_s),  # 105.0s
)
ADAPTIVE = AdaptiveConfig()
PRESSURE = PressureConfig()
QUEUE_EXTENSION = QueueExtensionConfig()
HYBRID_QUEUE_ADAPTIVE = HybridQueueAdaptiveConfig(rungs=("R4",))
HYBRID_ORACLE_SEEDED = HybridQueueAdaptiveConfig(rungs=())
HYBRID_R2 = HybridQueueAdaptiveConfig(rungs=("R2",))
HYBRID_R3 = HybridQueueAdaptiveConfig(rungs=("R4", "R3"))
HYBRID_R4 = HybridQueueAdaptiveConfig(rungs=("R4",))
HYBRID_R2_R3 = HybridQueueAdaptiveConfig(rungs=("R2", "R3"))
HYBRID_R2_R3_R4 = HybridQueueAdaptiveConfig(rungs=("R2", "R3", "R4"))
WEBSTER_MEASURED = WebsterMeasuredConfig()
WEBSTER_RECALC = WebsterRecalcConfig()
FIXED_MATCHED_CYCLE = FixedMatchedCycleConfig()
SUMO_ACTUATED = SumoActuatedConfig()
ACTION = ActionConfig()
RL = RLConfig()
SIM = SimConfig()

# Evaluation policy rosters
STANDARD_POLICIES = ("fixed", "fixed_webster", "adaptive", "pressure", "queue_extension", "rl_dqn")
HYBRID_SITE_POLICIES = ("fixed", "fixed_webster", "adaptive", "pressure", "queue_extension", "rl_dqn", "hybrid_queue_adaptive")
BASELINE_POLICIES = ("fixed", "fixed_webster", "webster_measured", "webster_recalc", "fixed_matched_cycle", "sumo_actuated")
ALL_POLICIES = (
    "fixed", "fixed_webster", "adaptive", "pressure", "queue_extension",
    "rl_dqn", "hybrid_queue_adaptive", "hybrid_oracle_seeded", "webster_measured", "webster_recalc",
    "fixed_matched_cycle", "sumo_actuated", "webster_oracle",
    "hybrid_r2", "hybrid_r3", "hybrid_r4", "hybrid_r2_r3", "hybrid_r2_r3_r4",
)

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
    """Settings for the 720-run research-grade evaluation matrix and statistical analysis."""
    patterns: tuple = ("balanced", "imbalanced_ns", "imbalanced_ew", "surge_north")
    levels: tuple = ("low", "medium", "heavy")
    policies: tuple = ("fixed", "fixed_webster", "adaptive", "pressure", "queue_extension", "rl_dqn")
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


# ==============================================================================
# Site Demand Patterns & Non-Stationary Scenarios (Phase 8 Frozen Configuration)
# ==============================================================================

# 1. Existing Stationary Site Demand Patterns (Unmodified)
SITE_DEMAND_PATTERNS_STATIONARY: Dict[str, Dict[str, List[Tuple[int, int, int]]]] = {
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

# 2. Non-Stationary Scenarios
@dataclass(frozen=True)
class RampPeakConfig:
    """Parameters for ramp_peak non-stationary scenario.
    
    Morning peak shape with piecewise-linear ramp:
    - Base rate per approach: 700 vph
    - Start multiplier: 0.40x (280 vph) from 0 to 300s
    - Ramp-up: 300s to 700s, linearly increasing from 0.40x to 1.80x (discretized in 50s buckets)
    - Peak plateau: 700s to 1100s, held at 1.80x (1260 vph)
    - Ramp-down: 1100s to 1500s, linearly decreasing from 1.80x to 0.40x (discretized in 50s buckets)
    - Post-peak base: 1500s to 1800s, held at 0.40x (280 vph)
    """
    base_vph: int = 700
    start_mult: float = 0.40
    peak_mult: float = 1.80
    ramp_up_start_s: float = 300.0
    plateau_start_s: float = 700.0
    plateau_end_s: float = 1100.0
    ramp_down_end_s: float = 1500.0
    horizon_s: float = 1800.0
    step_s: float = 50.0


@dataclass(frozen=True)
class SurgeShiftConfig:
    """Parameters for surge_shift non-stationary scenario.
    
    Mid-run directional shift from ORR North-South dominant to Varthur East-West dominant:
    - Phase 1 (0 to 700s): ORR dominant (N: 1200, S: 1050, W: 350, E: 350 vph)
    - Transition window (700s to 1100s): Handover across 4x100s intervals
    - Phase 2 (1100s to 1800s): Varthur dominant (W: 1200, E: 1200, N: 350, S: 350 vph)
    """
    orr_high_vph: int = 1200
    orr_low_vph: int = 350
    varthur_high_vph: int = 1200
    varthur_low_vph: int = 350
    phase1_end_s: float = 700.0
    transition_end_s: float = 1100.0
    horizon_s: float = 1800.0
    step_s: float = 100.0


@dataclass(frozen=True)
class LaneClosureConfig:
    """Parameters for lane_closure non-stationary scenario.
    
    Inbound lane closed mid-run on ORR North inbound approach ramp (ramp_orr_n_in_0):
    - Closure lane: ramp_orr_n_in_0 (right lane of 2-lane approach ramp from ORR North)
    - Closure window: 600.0s to 1200.0s (10 min duration)
    - Reopened: 1200.0s to 1800.0s
    - Demand: High commuter corridor traffic (N: 1050, S: 1050, W: 600, E: 600 vph)
    """
    lane_id: str = "ramp_orr_n_in_0"
    start_s: float = 600.0
    end_s: float = 1200.0
    horizon_s: float = 1800.0
    north_vph: int = 1050
    south_vph: int = 1050
    west_vph: int = 600
    east_vph: int = 600


RAMP_PEAK = RampPeakConfig()
SURGE_SHIFT = SurgeShiftConfig()
LANE_CLOSURE = LaneClosureConfig()


def build_ramp_peak_intervals(cfg: RampPeakConfig = RAMP_PEAK) -> List[Tuple[int, int, int]]:
    intervals: List[Tuple[int, int, int]] = []
    # Pre-ramp base
    intervals.append((0, int(cfg.ramp_up_start_s), int(round(cfg.base_vph * cfg.start_mult))))
    # Ramp-up
    ramp_dur = cfg.plateau_start_s - cfg.ramp_up_start_s
    t = cfg.ramp_up_start_s
    while t < cfg.plateau_start_s:
        t_next = min(cfg.plateau_start_s, t + cfg.step_s)
        mid_t = (t + t_next) / 2.0
        frac = (mid_t - cfg.ramp_up_start_s) / ramp_dur
        mult = cfg.start_mult + frac * (cfg.peak_mult - cfg.start_mult)
        intervals.append((int(t), int(t_next), int(round(cfg.base_vph * mult))))
        t = t_next
    # Plateau
    intervals.append((int(cfg.plateau_start_s), int(cfg.plateau_end_s), int(round(cfg.base_vph * cfg.peak_mult))))
    # Ramp-down
    down_dur = cfg.ramp_down_end_s - cfg.plateau_end_s
    t = cfg.plateau_end_s
    while t < cfg.ramp_down_end_s:
        t_next = min(cfg.ramp_down_end_s, t + cfg.step_s)
        mid_t = (t + t_next) / 2.0
        frac = (mid_t - cfg.plateau_end_s) / down_dur
        mult = cfg.peak_mult - frac * (cfg.peak_mult - cfg.start_mult)
        intervals.append((int(t), int(t_next), int(round(cfg.base_vph * mult))))
        t = t_next
    # Post-ramp base
    intervals.append((int(cfg.ramp_down_end_s), int(cfg.horizon_s), int(round(cfg.base_vph * cfg.start_mult))))
    return intervals


def build_surge_shift_intervals(cfg: SurgeShiftConfig = SURGE_SHIFT) -> Dict[str, List[Tuple[int, int, int]]]:
    # Phase 1: ORR dominant
    orr_ints: List[Tuple[int, int, int]] = [(0, int(cfg.phase1_end_s), cfg.orr_high_vph)]
    varthur_ints: List[Tuple[int, int, int]] = [(0, int(cfg.phase1_end_s), cfg.varthur_low_vph)]
    # Transition
    t = cfg.phase1_end_s
    trans_dur = cfg.transition_end_s - cfg.phase1_end_s
    while t < cfg.transition_end_s:
        t_next = min(cfg.transition_end_s, t + cfg.step_s)
        mid_t = (t + t_next) / 2.0
        frac = (mid_t - cfg.phase1_end_s) / trans_dur
        orr_vph = int(round(cfg.orr_high_vph - frac * (cfg.orr_high_vph - cfg.orr_low_vph)))
        varthur_vph = int(round(cfg.varthur_low_vph + frac * (cfg.varthur_high_vph - cfg.varthur_low_vph)))
        orr_ints.append((int(t), int(t_next), orr_vph))
        varthur_ints.append((int(t), int(t_next), varthur_vph))
        t = t_next
    # Phase 2: Varthur dominant
    orr_ints.append((int(cfg.transition_end_s), int(cfg.horizon_s), cfg.orr_low_vph))
    varthur_ints.append((int(cfg.transition_end_s), int(cfg.horizon_s), cfg.varthur_high_vph))
    return {
        "N": list(orr_ints),
        "S": [(t0, t1, int(round(v * 1050.0 / 1200.0)) if t0 < 700 else v) for t0, t1, v in orr_ints],
        "W": list(varthur_ints),
        "E": list(varthur_ints),
    }


_ramp_intervals = build_ramp_peak_intervals()
_shift_intervals = build_surge_shift_intervals()

SITE_DEMAND_PATTERNS: Dict[str, Dict[str, List[Tuple[int, int, int]]]] = {
    **SITE_DEMAND_PATTERNS_STATIONARY,
    "ramp_peak": {
        "W": list(_ramp_intervals),
        "E": list(_ramp_intervals),
        "N": list(_ramp_intervals),
        "S": list(_ramp_intervals),
    },
    "surge_shift": _shift_intervals,
    "lane_closure": {
        "N": [(0, 1800, LANE_CLOSURE.north_vph)],
        "S": [(0, 1800, LANE_CLOSURE.south_vph)],
        "W": [(0, 1800, LANE_CLOSURE.west_vph)],
        "E": [(0, 1800, LANE_CLOSURE.east_vph)],
    },
}

SITE_PATTERNS_STATIONARY = ("balanced", "imbalanced_orr", "imbalanced_varthur", "surge_orr_north")
SITE_PATTERNS_NON_STATIONARY = ("ramp_peak", "surge_shift", "lane_closure")
SITE_PATTERNS_ALL = SITE_PATTERNS_STATIONARY + SITE_PATTERNS_NON_STATIONARY
