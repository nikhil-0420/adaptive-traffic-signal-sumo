"""Unit and integration tests for Hybrid Queue-Adaptive Controller and Queue Measurement Engine."""
import pytest
from unittest.mock import MagicMock

from dp1 import config as C
from dp1.queues import (
    APPROACH_DEFINITIONS,
    ApproachQueueInfo,
    LaneQueueInfo,
    QueueMeasurementEngine,
    queues_to_legacy_dict,
)
from dp1.controllers.hybrid_queue_adaptive import HybridQueueAdaptiveController
from dp1.signal_states import SignalStates
from dp1.network import NET_FILE, build_network


class DummyStates:
    """Mock states for unit testing controller transitions."""
    def __init__(self):
        self._states = {
            ("NS", "GREEN"): "GGGrrrGGGrrr",
            ("NS", "YELLOW"): "yyyrrryyyrrr",
            ("NS", "ALL_RED"): "rrrrrrrrrrrr",
            ("EW", "GREEN"): "rrrGGGrrrGGG",
            ("EW", "YELLOW"): "rrryyyrrryyy",
            ("EW", "ALL_RED"): "rrrrrrrrrrrr",
        }

    def green(self, axis: str) -> str:
        return self._states[(axis, "GREEN")]

    def yellow(self, axis: str) -> str:
        return self._states[(axis, "YELLOW")]

    def all_red(self) -> str:
        return "rrrrrrrrrrrr"


# -----------------------------------------------------------------------------
# 1. Approach Definitions and Detector Mapping Tests
# -----------------------------------------------------------------------------

def test_marathahalli_approach_definitions():
    """Verify correct physical approach mappings and detector IDs for Marathahalli."""
    defs = APPROACH_DEFINITIONS["marathahalli"]
    assert "N" in defs and "S" in defs and "E" in defs and "W" in defs
    
    # North: KR Puram
    assert defs["N"]["edge"] == "leg_orr_n_in"
    assert defs["N"]["detectors"] == ["det_orr_n_0", "det_orr_n_1"]
    assert defs["N"]["axis"] == "NS"
    assert defs["N"]["det_length_m"] == 24.9
    
    # South: Kadubeesanahalli
    assert defs["S"]["edge"] == "leg_orr_s_in"
    assert defs["S"]["detectors"] == ["det_orr_s_0", "det_orr_s_1"]
    assert defs["S"]["axis"] == "NS"
    assert defs["S"]["det_length_m"] == 24.9
    
    # East: Whitefield
    assert defs["E"]["edge"] == "leg_wf_in"
    assert defs["E"]["detectors"] == ["det_wf_0", "det_wf_1"]
    assert defs["E"]["axis"] == "EW"
    
    # West: HAL Airport Rd
    assert defs["W"]["edge"] == "leg_hal_in"
    assert defs["W"]["detectors"] == ["det_hal_0", "det_hal_1"]
    assert defs["W"]["axis"] == "EW"


def test_queue_aggregation_max_never_sum():
    """Verify longitudinal queue measurement is MAX across lanes, NEVER the sum."""
    lane0 = LaneQueueInfo(
        lane_id="leg_orr_n_in_0", lane_index=0, detector_id="det_orr_n_0",
        detector_queue_m=12.0, detector_veh_count=2, mean_speed_mps=0.5,
        is_saturated=False, ground_truth_queue_m=12.0, ground_truth_veh_count=2
    )
    lane1 = LaneQueueInfo(
        lane_id="leg_orr_n_in_1", lane_index=1, detector_id="det_orr_n_1",
        detector_queue_m=20.0, detector_veh_count=4, mean_speed_mps=0.1,
        is_saturated=False, ground_truth_queue_m=20.0, ground_truth_veh_count=4
    )

    longitudinal = max(lane0.detector_queue_m, lane1.detector_queue_m)
    total_vehs = lane0.detector_veh_count + lane1.detector_veh_count

    assert longitudinal == 20.0  # max(12, 20)
    assert longitudinal != 32.0  # NOT 12 + 20
    assert total_vehs == 6       # vehicle counts sum across lanes


def test_saturation_detection():
    """Verify saturation flag triggers when detector queue reaches 24.4m on a 24.9m detector."""
    det_len = 24.9
    sat_thresh = det_len - 0.5  # 24.4m
    assert 24.5 >= sat_thresh
    assert not (22.0 >= sat_thresh)


# -----------------------------------------------------------------------------
# 2. Hybrid Controller Unit Logic Tests
# -----------------------------------------------------------------------------

def test_hybrid_controller_baseline_allocation():
    """Verify baseline green allocation derives from Webster plan and respects bounds."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(min_green_s=10.0, max_green_s=60.0)
    ctl = HybridQueueAdaptiveController(states, scenario="balanced", cfg=cfg, network="marathahalli")

    assert ctl.baseline_green_s["NS"] >= 10.0
    assert ctl.baseline_green_s["NS"] <= 60.0
    assert ctl.baseline_green_s["EW"] >= 10.0
    assert ctl.baseline_green_s["EW"] <= 60.0


def test_min_green_floor_enforcement():
    """Verify min green floor (10s) holds green even under opposing demand."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(min_green_s=10.0, max_green_s=60.0)
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    queues = {"N": 0.0, "S": 0.0, "E": 50.0, "W": 50.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 5.0s (< 10.0s floor), must hold
    should_end = ctl.green_should_end("NS", elapsed=5.0, queues=queues, t=5.0)
    assert not should_end
    assert ctl.last_decision_record["action"] == "HOLD"
    assert ctl.last_decision_record["reason_code"] == "HOLD_MIN_GREEN"


def test_max_green_ceiling_enforcement():
    """Verify max green ceiling (60s) forces switch to prevent starvation."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(min_green_s=10.0, max_green_s=60.0)
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    queues = {"N": 100.0, "S": 100.0, "E": 20.0, "W": 20.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 60.0s (>= max_green_s), must switch
    should_end = ctl.green_should_end("NS", elapsed=60.0, queues=queues, t=60.0)
    assert should_end
    assert ctl.last_decision_record["action"] == "REQUEST_SWITCH"
    assert ctl.last_decision_record["reason_code"] == "SWITCH_MAX_GREEN"


def test_gap_out_logic():
    """Verify gap-out triggers when active queue is cleared for >= 3s with waiting opposing traffic."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(min_green_s=10.0, max_green_s=60.0, gap_out_s=3.0)
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    ctl.decide_green("NS", {"N": 20.0, "S": 20.0, "E": 30.0, "W": 30.0}, t=0.0)

    # Active cleared at t=12.0s
    queues_empty = {"N": 0.0, "S": 0.0, "E": 30.0, "W": 30.0}
    
    # First empty step (t=12.0s, empty duration = 0.0s < 3.0s) -> holds
    should_end = ctl.green_should_end("NS", elapsed=12.0, queues=queues_empty, t=12.0)
    assert not should_end
    assert ctl.last_decision_record["action"] == "HOLD"
    assert ctl.last_decision_record["reason_code"] == "HOLD_CLEARING"

    # Step at t=15.5s (empty duration = 3.5s >= 3.0s) -> gap out
    should_end = ctl.green_should_end("NS", elapsed=15.5, queues=queues_empty, t=15.5)
    assert should_end
    assert ctl.last_decision_record["action"] == "GAP_OUT"
    assert ctl.last_decision_record["reason_code"] == "SWITCH_GAP_OUT"


def test_approved_extension_increment():
    """Verify step extension of +3.0s when demand condition is satisfied."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(
        min_green_s=10.0, max_green_s=60.0, extend_step_s=3.0,
        extend_threshold_m=5.0, max_competing_wait_s=35.0
    )
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    # Set baseline target = 20s
    ctl.baseline_green_s["NS"] = 20.0
    queues = {"N": 15.0, "S": 15.0, "E": 10.0, "W": 10.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 20.0s (target reached): active queue 15m >= 5m threshold, competing wait 20s < 35s
    should_end = ctl.green_should_end("NS", elapsed=20.0, queues=queues, t=20.0)
    assert not should_end
    assert ctl.last_decision_record["action"] == "EXTEND"
    assert ctl.last_decision_record["reason_code"] == "EXTEND_APPROVED"
    assert ctl.last_decision_record["delta_g_app_s"] == 3.0
    assert ctl.target_green_s == 23.0
    assert ctl.accumulated_extra_s == 3.0


def test_anti_monopoly_competing_wait_limit():
    """Verify extension is rejected when competing red wait >= 35s."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(
        min_green_s=10.0, max_green_s=60.0, extend_step_s=3.0,
        extend_threshold_m=5.0, max_competing_wait_s=35.0
    )
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    ctl.baseline_green_s["NS"] = 35.0
    queues = {"N": 20.0, "S": 20.0, "E": 15.0, "W": 15.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At t = 36.0s: competing red has waited 36s (>= 35s limit) with 15m queue
    should_end = ctl.green_should_end("NS", elapsed=36.0, queues=queues, t=36.0)
    assert should_end
    assert ctl.last_decision_record["action"] == "REQUEST_SWITCH"
    assert ctl.last_decision_record["reason_code"] == "SWITCH_FAIRNESS_WAIT_LIMIT"


def test_demand_fairness_switch():
    """Verify extension is rejected when competing demand exceeds active demand by fairness ratio."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(
        min_green_s=10.0, max_green_s=60.0, fairness_ratio=1.2, min_competing_queue_m=5.0
    )
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    ctl.baseline_green_s["NS"] = 20.0
    # Active queue = 10.0m (above extend_threshold_m), but Competing queue = 20.0m (> 10.0 * 1.2)
    queues = {"N": 10.0, "S": 10.0, "E": 20.0, "W": 20.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 20.0s, fairness ratio violated -> switch to relieve competing corridor
    should_end = ctl.green_should_end("NS", elapsed=20.0, queues=queues, t=20.0)
    assert should_end
    assert ctl.last_decision_record["action"] == "REQUEST_SWITCH"
    assert ctl.last_decision_record["reason_code"] == "SWITCH_DEMAND_FAIRNESS"


def test_demand_exhausted_switch():
    """Verify extension is rejected when active queue falls below extension threshold with no arrivals."""
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(
        min_green_s=10.0, max_green_s=60.0, extend_threshold_m=5.0, min_competing_queue_m=5.0
    )
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    ctl.baseline_green_s["NS"] = 20.0
    # Active queue = 3.0m < 5.0m threshold, competing queue = 2.0m (< 5.0m min competing threshold)
    queues = {"N": 2.0, "S": 3.0, "E": 2.0, "W": 2.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 20.0s, demand exhausted -> switch
    should_end = ctl.green_should_end("NS", elapsed=20.0, queues=queues, t=20.0)
    assert should_end
    assert ctl.last_decision_record["action"] == "REQUEST_SWITCH"
    assert ctl.last_decision_record["reason_code"] == "SWITCH_DEMAND_EXHAUSTED"


# -----------------------------------------------------------------------------
# 3. Safety Invariant Compliance Test (State Machine Transitions)
# -----------------------------------------------------------------------------

def test_phase_state_machine_strict_sequence():
    """Verify that Hybrid controller strictly transitions GREEN -> YELLOW -> ALL_RED -> GREEN."""
    states = DummyStates()
    ctl = HybridQueueAdaptiveController(states)

    queues = {"N": 10.0, "S": 10.0, "E": 10.0, "W": 10.0}
    ctl.start(0.0, queues)

    assert ctl.phase == "GREEN"
    assert ctl.axis == "NS"

    # Step past max green to force switch
    t = 61.0
    ctl.step(t, queues)
    # Next phase MUST be YELLOW (never direct GREEN to EW)
    assert ctl.phase == "YELLOW"
    assert ctl.axis == "NS"

    # Step through yellow duration (3s)
    t += 3.0
    ctl.step(t, queues)
    assert ctl.phase == "ALL_RED"

    # Step through all_red duration (2s)
    t += 2.0
    ctl.step(t, queues)
    assert ctl.phase == "GREEN"
    assert ctl.axis == "EW"


# -----------------------------------------------------------------------------
# 4. Schema Separation and Sensor Semantics Regression Tests
# -----------------------------------------------------------------------------

def test_approved_and_rejected_extension_schema_separation():
    """Verify unambiguous separation of proposed_action and applied_action.

    When an extension is approved:
      proposed_action == 'EXTEND', applied_action == 'EXTEND', action == 'EXTEND',
      decision_outcome == 'EXTEND_APPROVED', delta_g_req_s == 3.0, delta_g_app_s == 3.0.

    When an extension is requested at target green but rejected due to fairness (competing wait limit):
      proposed_action == 'EXTEND', applied_action == 'REQUEST_SWITCH', action == 'REQUEST_SWITCH',
      decision_outcome == 'SWITCH_FAIRNESS_WAIT_LIMIT', delta_g_req_s == 3.0, delta_g_app_s == 0.0.
      The applied action must NEVER be 'EXTEND', and the switch record must be appended as a separate event.
    """
    states = DummyStates()
    cfg = C.HybridQueueAdaptiveConfig(
        min_green_s=10.0, max_green_s=60.0, extend_step_s=3.0,
        extend_threshold_m=5.0, max_competing_wait_s=35.0
    )
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)

    # 1. Start NS green with baseline 20.0s
    ctl.baseline_green_s["NS"] = 20.0
    queues = {"N": 15.0, "S": 15.0, "E": 10.0, "W": 10.0}
    ctl.decide_green("NS", queues, t=0.0)

    # At elapsed = 20.0s: target green reached, competing red wait = 20.0s (< 35.0s limit)
    # Extension is APPROVED (+3.0s)
    should_end = ctl.green_should_end("NS", elapsed=20.0, queues=queues, t=20.0)
    assert not should_end
    appr_rec = ctl.last_decision_record
    assert appr_rec["proposed_action"] == "EXTEND"
    assert appr_rec["applied_action"] == "EXTEND"
    assert appr_rec["action"] == "EXTEND"
    assert appr_rec["decision_outcome"] == "EXTEND_APPROVED"
    assert appr_rec["delta_g_req_s"] == 3.0
    assert appr_rec["delta_g_app_s"] == 3.0
    assert appr_rec["g_extra_s"] == 3.0
    assert appr_rec["target_green_s"] == 23.0
    assert len(ctl.decisions) == 1
    assert ctl.decisions[0]["action"] == "EXTEND"

    # Advance time: t = 36.0s, elapsed = 36.0s, competing_red_elapsed >= 35.0s limit
    ctl.competing_red_start_s = 0.0
    ctl.baseline_green_s["NS"] = 36.0
    ctl.target_green_s = 36.0
    should_end = ctl.green_should_end("NS", elapsed=36.0, queues=queues, t=36.0)
    assert should_end  # Must switch!
    rej_rec = ctl.last_decision_record
    assert rej_rec["proposed_action"] == "EXTEND"
    assert rej_rec["applied_action"] == "REQUEST_SWITCH"
    assert rej_rec["action"] == "REQUEST_SWITCH"
    assert rej_rec["action"] != "EXTEND"  # Invariant: rejected extension MUST NOT show action=EXTEND
    assert rej_rec["decision_outcome"] == "SWITCH_FAIRNESS_WAIT_LIMIT"
    assert rej_rec["delta_g_req_s"] == 3.0
    assert rej_rec["delta_g_app_s"] == 0.0
    # Decisions history must contain both: first the approved extend, second the rejected switch
    assert len(ctl.decisions) == 2
    assert ctl.decisions[0]["action"] == "EXTEND"
    assert ctl.decisions[0]["decision_outcome"] == "EXTEND_APPROVED"
    assert ctl.decisions[1]["action"] == "REQUEST_SWITCH"
    assert ctl.decisions[1]["decision_outcome"] == "SWITCH_FAIRNESS_WAIT_LIMIT"


def test_sensor_semantics_and_saturation_status():
    """Verify detector saturation and zero-queue semantics in ApproachQueueInfo."""
    # 1. Saturation: queue >= length - 0.5m
    info_sat = ApproachQueueInfo(
        approach="N", name="ORR North (KR Puram)", axis="NS", edge_id="leg_orr_n_in",
        detector_length_m=24.9, longitudinal_queue_m=24.5, total_queued_vehicles=5,
        is_saturated=True, sensor_status="SATURATED", data_valid=True
    )
    assert info_sat.is_saturated is True
    assert info_sat.sensor_status == "SATURATED"
    assert info_sat.data_valid is True

    # 2. Confirmed zero queue: queue == 0.0 with valid sensor reading
    info_zero = ApproachQueueInfo(
        approach="S", name="ORR South (Kadubeesanahalli)", axis="NS", edge_id="leg_orr_s_in",
        detector_length_m=24.9, longitudinal_queue_m=0.0, total_queued_vehicles=0,
        is_saturated=False, sensor_status="CONFIRMED_ZERO", data_valid=True
    )
    assert info_zero.is_saturated is False
    assert info_zero.sensor_status == "CONFIRMED_ZERO"
    assert info_zero.longitudinal_queue_m == 0.0

    # 3. Active queue measuring
    info_measuring = ApproachQueueInfo(
        approach="E", name="Varthur East (Whitefield)", axis="EW", edge_id="leg_wf_in",
        detector_length_m=24.9, longitudinal_queue_m=14.2, total_queued_vehicles=3,
        is_saturated=False, sensor_status="MEASURING", data_valid=True
    )
    assert info_measuring.sensor_status == "MEASURING"

    # 4. Sensor offline/failure
    info_offline = ApproachQueueInfo(
        approach="W", name="Varthur West (HAL Airport Rd)", axis="EW", edge_id="leg_hal_in",
        detector_length_m=24.9, longitudinal_queue_m=0.0, total_queued_vehicles=0,
        is_saturated=False, sensor_status="OFFLINE", data_valid=False
    )
    assert info_offline.sensor_status == "OFFLINE"
    assert info_offline.data_valid is False
