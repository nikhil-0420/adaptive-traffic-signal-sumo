"""Emergency vehicle detection and safe traffic signal priority (Phase P4).

Safety & fairness invariants:
- Base phase state machine in dp1/controllers/base.py remains the sole authority.
- Every preemption switch passes strictly through GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN.
- Preemption can only occur after minimum green (min_green_s) has elapsed on the active axis.
- When emergency axis is active, green can be extended up to max_extension_s to allow crossing.
- Maximum extension cap strictly prevents starving the competing axis indefinitely.
- The ambulance is detected strictly while approaching on an incoming edge (_in) within detection_dist_m.
  Once it enters junction (:J0) or outgoing edge (_out), it is no longer approaching.
"""
from typing import Dict, Optional, Tuple
import traci

from . import config as C
from .controllers.base import ControllerAction


MARATHAHALLI_APPROACH_EDGES = {
    "leg_orr_s_in": ("S", "NS", 0.0),
    "ramp_orr_s_in": ("S", "NS", 34.0),
    "leg_orr_n_in": ("N", "NS", 0.0),
    "ramp_orr_n_in": ("N", "NS", 34.0),
    "leg_wf_in": ("E", "EW", 0.0),
    "ramp_wf_in": ("E", "EW", 34.0),
    "leg_hal_in": ("W", "EW", 0.0),
    "ramp_hal_in": ("W", "EW", 34.0),
}


def detect_approaching_emergency(
    tls_id: str = C.TLS_ID,
    em_cfg: C.EmergencyConfig = C.EMERGENCY,
) -> Optional[Tuple[str, str, float]]:
    """Detect if the configured emergency vehicle is approaching the intersection.

    Returns:
        Optional[Tuple[str, str, float]]:
            (approach, axis, distance_to_junction_m) if approaching within detection_dist_m
            on an incoming edge (e.g. 'N_in' or 'leg_orr_s_in').
            Returns None if vehicle is not loaded, has passed the stop line, is inside the junction,
            is on an outgoing edge, or is beyond detection_dist_m.
    """
    try:
        active_ids = traci.vehicle.getIDList()
    except (traci.TraCIException, traci.FatalTraCIError):
        return None

    if em_cfg.vehicle_id not in active_ids:
        return None

    try:
        road_id = traci.vehicle.getRoadID(em_cfg.vehicle_id)
        if not road_id:
            return None

        offset = 0.0
        if road_id in MARATHAHALLI_APPROACH_EDGES:
            app, axis, offset = MARATHAHALLI_APPROACH_EDGES[road_id]
        elif road_id.endswith("_in"):
            app = road_id.split("_")[0]
            if app not in C.APPROACHES:
                return None
            axis = C.AXIS_OF[app]
        else:
            return None

        lane_id = traci.vehicle.getLaneID(em_cfg.vehicle_id)
        lane_pos = traci.vehicle.getLanePosition(em_cfg.vehicle_id)
        lane_len = traci.lane.getLength(lane_id)
        dist_m = max(0.0, lane_len - lane_pos) + offset

        if dist_m <= em_cfg.detection_dist_m:
            return (app, axis, dist_m)
    except (traci.TraCIException, traci.FatalTraCIError, KeyError):
        return None

    return None


class EmergencyPriorityCoordinator:
    """Coordinates priority decisions while maintaining state machine safety invariants."""

    def __init__(self, em_cfg: C.EmergencyConfig = C.EMERGENCY, tls_id: str = C.TLS_ID):
        self.em_cfg = em_cfg
        self.tls_id = tls_id
        self.extension_start_s: Optional[float] = None
        self.last_detected_dist: Optional[float] = None
        self.last_status: str = "idle"

    def reset(self):
        self.extension_start_s = None
        self.last_detected_dist = None
        self.last_status = "idle"

    def evaluate(
        self,
        current_axis: str,
        current_phase: str,
        elapsed_green: float,
        t: float,
        policy_wants_switch: bool,
    ) -> Tuple[Optional[ControllerAction], Dict]:
        """Evaluate whether emergency priority should override or constrain the controller action.

        Args:
            current_axis: Currently active signal axis ("NS" or "EW").
            current_phase: Current phase ("GREEN", "YELLOW", "ALL_RED").
            elapsed_green: Seconds elapsed in the current green phase.
            t: Current simulation time in seconds.
            policy_wants_switch: Whether the underlying controller policy wants to terminate green.

        Returns:
            Tuple[Optional[ControllerAction], Dict]:
                - action_override: ControllerAction.HOLD, ControllerAction.REQUEST_SWITCH, or None.
                - info: Diagnostic metadata about emergency status.
        """
        detection = detect_approaching_emergency(tls_id=self.tls_id, em_cfg=self.em_cfg)

        if detection is None:
            self.extension_start_s = None
            self.last_detected_dist = None
            self.last_status = "no_emergency_detected"
            return None, {"status": self.last_status, "detected": False}

        app, em_axis, dist_m = detection
        self.last_detected_dist = dist_m

        # Safety rule 1: Outside GREEN (YELLOW or ALL_RED), clearance cannot be interrupted
        if current_phase != "GREEN":
            self.last_status = "clearance_in_progress"
            return None, {
                "status": self.last_status,
                "detected": True,
                "approach": app,
                "axis": em_axis,
                "dist_m": dist_m,
            }

        # Case A: Emergency vehicle is on the COMPETING axis (needs preemption switch)
        if current_axis != em_axis:
            self.extension_start_s = None
            # Safety rule 2: Minimum green on current axis must be respected
            if elapsed_green < self.em_cfg.min_green_s:
                self.last_status = f"waiting_min_green_{elapsed_green:.1f}s"
                # Keep holding until minimum green elapses
                return ControllerAction.HOLD, {
                    "status": self.last_status,
                    "detected": True,
                    "approach": app,
                    "axis": em_axis,
                    "dist_m": dist_m,
                    "elapsed_green": elapsed_green,
                    "min_green_s": self.em_cfg.min_green_s,
                }
            else:
                self.last_status = "preemption_switch_requested"
                # Minimum green satisfied -> request transition to clearance sequence
                return ControllerAction.REQUEST_SWITCH, {
                    "status": self.last_status,
                    "detected": True,
                    "approach": app,
                    "axis": em_axis,
                    "dist_m": dist_m,
                }

        # Case B: Emergency vehicle is on the ACTIVE axis (needs green extension)
        if current_axis == em_axis:
            # If the underlying policy wants to switch, we extend green for the ambulance
            if policy_wants_switch:
                if self.extension_start_s is None:
                    self.extension_start_s = t
                ext_duration = t - self.extension_start_s

                # Safety rule 3: Maximum extension cap prevents indefinite starvation
                if ext_duration < self.em_cfg.max_extension_s:
                    self.last_status = f"extended_green_{ext_duration:.1f}s"
                    return ControllerAction.HOLD, {
                        "status": self.last_status,
                        "detected": True,
                        "approach": app,
                        "axis": em_axis,
                        "dist_m": dist_m,
                        "extension_s": ext_duration,
                        "max_extension_s": self.em_cfg.max_extension_s,
                    }
                else:
                    self.last_status = "max_extension_cap_reached"
                    return ControllerAction.REQUEST_SWITCH, {
                        "status": self.last_status,
                        "detected": True,
                        "approach": app,
                        "axis": em_axis,
                        "dist_m": dist_m,
                        "extension_s": ext_duration,
                        "max_extension_s": self.em_cfg.max_extension_s,
                    }
            else:
                # Controller policy naturally wants to hold green; allow it
                self.extension_start_s = None
                self.last_status = "natural_green_hold"
                return None, {
                    "status": self.last_status,
                    "detected": True,
                    "approach": app,
                    "axis": em_axis,
                    "dist_m": dist_m,
                }

        return None, {"status": "idle", "detected": False}
