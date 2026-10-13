"""Fixed observation schema and feature vector builder for RL environment and inference."""
import numpy as np
from .. import config as C

OBS_DIM = 11
OBS_SCHEMA_VERSION = "1.0.0"

OBS_FEATURE_NAMES = [
    "q_N_normalized",          # 0: approach N queue / 150m [0, 1]
    "q_S_normalized",          # 1: approach S queue / 150m [0, 1]
    "q_E_normalized",          # 2: approach E queue / 150m [0, 1]
    "q_W_normalized",          # 3: approach W queue / 150m [0, 1]
    "axis_NS",                 # 4: active axis is NS (one-hot: 1.0 or 0.0)
    "axis_EW",                 # 5: active axis is EW (one-hot: 1.0 or 0.0)
    "phase_GREEN",             # 6: active phase is GREEN (one-hot: 1.0 or 0.0)
    "phase_YELLOW",            # 7: active phase is YELLOW (one-hot: 1.0 or 0.0)
    "phase_ALL_RED",           # 8: active phase is ALL_RED (one-hot: 1.0 or 0.0)
    "elapsed_green_fraction",  # 9: elapsed green / max_green_s in [0, 1]
    "demand_timeline_fraction" # 10: simulation time t / demand_duration_s in [0, 1]
]


def build_observation(
    queues: dict,
    axis: str,
    phase: str,
    elapsed_green_s: float,
    t_s: float,
    max_detector_m: float = C.RL.max_detector_m,
    max_green_s: float = C.RL.max_green_s,
    demand_duration_s: float = float(C.SIM.demand_duration_s),
) -> np.ndarray:
    """Construct the documented normalized 11-dimensional observation vector.

    All feature values are strictly in [0.0, 1.0]. Future information is never leaked.

    Args:
        queues: dictionary of approach queues in metres {"N": ..., "S": ..., "E": ..., "W": ...}.
        axis: currently serving axis ("NS" or "EW").
        phase: currently active phase ("GREEN", "YELLOW", or "ALL_RED").
        elapsed_green_s: elapsed seconds since the start of the current GREEN phase (0 if not GREEN).
        t_s: current simulation time in seconds.
        max_detector_m: normalization denominator for approach queues.
        max_green_s: normalization denominator for elapsed green time.
        demand_duration_s: normalization denominator for demand timeline progress.

    Returns:
        np.ndarray: shape (11,), dtype np.float32.
    """
    obs = np.zeros(OBS_DIM, dtype=np.float32)

    # 0..3: Normalized approach queues
    obs[0] = min(max(0.0, float(queues.get("N", 0.0))), max_detector_m) / max_detector_m
    obs[1] = min(max(0.0, float(queues.get("S", 0.0))), max_detector_m) / max_detector_m
    obs[2] = min(max(0.0, float(queues.get("E", 0.0))), max_detector_m) / max_detector_m
    obs[3] = min(max(0.0, float(queues.get("W", 0.0))), max_detector_m) / max_detector_m

    # 4..5: Axis one-hot
    obs[4] = 1.0 if axis == "NS" else 0.0
    obs[5] = 1.0 if axis == "EW" else 0.0

    # 6..8: Phase one-hot
    obs[6] = 1.0 if phase == "GREEN" else 0.0
    obs[7] = 1.0 if phase == "YELLOW" else 0.0
    obs[8] = 1.0 if phase == "ALL_RED" else 0.0

    # 9: Elapsed green fraction
    if phase == "GREEN":
        obs[9] = min(max(0.0, float(elapsed_green_s)), max_green_s) / max_green_s
    else:
        obs[9] = 0.0

    # 10: Demand timeline fraction
    obs[10] = min(max(0.0, float(t_s)), demand_duration_s) / demand_duration_s

    return obs
