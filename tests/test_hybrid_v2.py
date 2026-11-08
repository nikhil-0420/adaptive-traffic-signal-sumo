"""Unit tests for Hybrid Queue-Adaptive Controller v2 candidates."""
import pytest
from dp1.controllers.hybrid_queue_adaptive_v2 import (
    HybridQueueAdaptiveV2Controller,
    HybridV2CandAController,
    HybridV2CandBController,
    HybridV2CandCController,
    HybridV2CandDController,
)
from dp1 import config as C


class DummyStates:
    def __init__(self):
        self.yellow_time_s = 3.0
        self.all_red_time_s = 2.0
        self.current_state = "GGGgrrrrGGGgrrrr"


def test_v2_candidate_instantiation():
    states = DummyStates()
    ctl_a = HybridV2CandAController(states)
    assert ctl_a.cfg.rest_in_green is True
    assert ctl_a.cfg.unconditional_wait_cap is False

    ctl_b = HybridV2CandBController(states)
    assert ctl_b.cfg.rest_in_green is False
    assert ctl_b.cfg.unconditional_wait_cap is True

    ctl_c = HybridV2CandCController(states)
    assert ctl_c.cfg.pressure_extension is True

    ctl_d = HybridV2CandDController(states)
    assert ctl_d.cfg.rest_in_green is True
    assert ctl_d.cfg.unconditional_wait_cap is True


def test_v2_cand_a_rest_in_green():
    """Verify Candidate A rests in green when active cleared and competing has zero demand."""
    states = DummyStates()
    ctl = HybridV2CandAController(states)
    ctl.phase = "GREEN"
    ctl.axis = "NS"
    ctl.baseline_green_s = {"NS": 15.0, "EW": 15.0}
    ctl.target_green_s = 15.0
    ctl.red_start_times = {"EW": 0.0}

    # At t = 20.0 (elapsed = 20s > target 15s), own queue is 0, competing is 0
    queues = {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}
    should_end, rec = ctl._evaluate_rules("NS", 20.0, queues, 20.0, record_decisions=True)
    assert should_end is False
    assert rec["decision_outcome"] == "HOLD_REST_IN_GREEN"

    # Now competing demand appears (E = 5.0m)
    queues["E"] = 5.0
    should_end2, rec2 = ctl._evaluate_rules("NS", 21.0, queues, 21.0, record_decisions=True)
    assert should_end2 is True
    assert rec2["decision_outcome"] == "SWITCH_GAP_OUT"


def test_v2_cand_b_unconditional_wait_cap():
    """Verify Candidate B forces switch at 35s red wait even with 0 competing queue."""
    states = DummyStates()
    ctl = HybridV2CandBController(states)
    ctl.phase = "GREEN"
    ctl.axis = "NS"
    ctl.baseline_green_s = {"NS": 25.0, "EW": 25.0}
    ctl.target_green_s = 25.0
    ctl.red_start_times = {"EW": 0.0}

    # Active has queue, competing has 0 queue, competing red wait is 36s (> 35s)
    queues = {"N": 10.0, "S": 10.0, "E": 0.0, "W": 0.0}
    should_end, rec = ctl._evaluate_rules("NS", 12.0, queues, 36.0, record_decisions=True)
    assert should_end is True
    assert rec["decision_outcome"] == "SWITCH_FAIRNESS_HARD_CAP"


def test_v2_cand_c_pressure_extension():
    """Verify Candidate C grants extension only when active queue exceeds competing queue."""
    states = DummyStates()
    ctl = HybridV2CandCController(states)
    ctl.phase = "GREEN"
    ctl.axis = "NS"
    ctl.baseline_green_s = {"NS": 10.0, "EW": 10.0}
    ctl.target_green_s = 10.0
    ctl.red_start_times = {"EW": 0.0}

    # Active queue = 6.0m, Competing queue = 6.5m (fairness_ratio 1.2 would allow, but pressure deficit -0.5m rejects)
    queues = {"N": 6.0, "S": 6.0, "E": 6.5, "W": 6.5}
    should_end, rec = ctl._evaluate_rules("NS", 11.0, queues, 11.0, record_decisions=True)
    assert should_end is True
    assert rec["decision_outcome"] == "SWITCH_PRESSURE_DEFICIT"

    # Active queue = 15m, Competing queue = 5m -> pressure = 10m > 0 -> extend
    queues = {"N": 15.0, "S": 15.0, "E": 5.0, "W": 5.0}
    should_end2, rec2 = ctl._evaluate_rules("NS", 11.0, queues, 11.0, record_decisions=True)
    assert should_end2 is False
    assert rec2["decision_outcome"] == "EXTEND_PRESSURE"
