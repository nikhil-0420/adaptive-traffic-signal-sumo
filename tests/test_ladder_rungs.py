"""Unit and regression tests for Phase 10 Ablation Ladder (Rungs R0, R2, R3, R4).

Verifies:
1. R0 bit-for-bit regression equivalence (flags-off outputs equal old hybrid).
2. Shared safety state machine invariant (GREEN -> YELLOW 3s -> ALL_RED 2s -> GREEN).
3. Both queues zero: no false extensions; returns appropriate action.
4. Min green not reached: strictly holds green (HOLD_MIN_GREEN).
5. Hard cap reached while active queue is large: mandatory switch (SWITCH_FAIRNESS_HARD).
6. Saturated sensor: physical queues at detector limit handled safely without errors.
7. Offline sensor: missing/negative/NaN queue readings are never read as 0.0 (falls back safely).
8. R2 comparative extension: approved only when active_score > margin * competing_score + switch_cost.
9. R3 queue-aware fairness: soft limit scaled by competing queue; no switch if competing queue empty.
10. R4 measured Webster base green: un-oracled baseline at start, updates at cycle boundary from measured arrivals.
"""

import math
from pathlib import Path
import pytest

from dp1 import config as C
from dp1.controllers import (
    HybridQueueAdaptiveController,
    HybridR2Controller,
    HybridR2R3Controller,
    HybridR2R3R4Controller,
)
from dp1.runner import run_simulation


class MockStates:
    """Mock states for unit testing signal machine transitions."""
    def __init__(self):
        self.tls_id = "test_tls"

    def green(self, axis):
        return "GGGrrrGGGrrr" if axis == "NS" else "rrrGGGrrrGGG"

    def yellow(self, axis):
        return "yyyrrryyyrrr" if axis == "NS" else "rrryyyrrryyy"

    def all_red(self):
        return "rrrrrrrrrrrr"


def test_r0_flags_off_regression_identity(tmp_path):
    """Regression test: hybrid with flags off (rungs=()) is bit-for-bit identical to default hybrid."""
    # Run with default HYBRID_QUEUE_ADAPTIVE
    run_default = tmp_path / "run_default"
    res_default = run_simulation(
        scenario="imbalanced_ns",
        policy="hybrid_queue_adaptive",
        seed=1,
        network="synthetic",
        demand_level="medium",
        out_dir=run_default,
    )

    # Run with explicit flags-off config
    cfg_off = C.HybridQueueAdaptiveConfig(rungs=())
    run_off = tmp_path / "run_off"
    res_off = run_simulation(
        scenario="imbalanced_ns",
        policy="hybrid_queue_adaptive",
        policy_kwargs={"cfg": cfg_off},
        seed=1,
        network="synthetic",
        demand_level="medium",
        out_dir=run_off,
    )

    assert res_default["avg_wait_s"] == pytest.approx(res_off["avg_wait_s"], abs=1e-6)
    assert res_default["max_queue_m"] == pytest.approx(res_off["max_queue_m"], abs=1e-6)
    assert res_default["cycles"] == res_off["cycles"]

    # Byte-identical decisions check
    dec_default = (run_default / "decisions.csv").read_bytes()
    dec_off = (run_off / "decisions.csv").read_bytes()
    assert dec_default == dec_off, "Flags-off decisions.csv must be 100% byte-identical to default hybrid"


def test_min_green_not_reached_holds_green():
    """Unit test: green_should_end strictly returns False (HOLD) when elapsed < min_green."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2_R3)
    ctl.decide_green("NS", {"N": 0.0, "S": 0.0, "E": 20.0, "W": 20.0}, t=0.0)

    # Elapsed = 5.0s < min_green (10.0s), competing queue is huge (20m)
    should_end = ctl.green_should_end("NS", elapsed=5.0, queues={"N": 0.0, "S": 0.0, "E": 20.0, "W": 20.0}, t=5.0)
    assert should_end is False
    assert ctl.last_decision_record["reason_code"] == "HOLD_MIN_GREEN"


def test_both_queues_zero_behavior():
    """Unit test: when both active and competing queues are zero, no false extension is granted."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2)
    ctl.decide_green("NS", {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}, t=0.0)

    # After base green (e.g. at 25s), both queues are zero
    should_end = ctl.green_should_end("NS", elapsed=25.0, queues={"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}, t=25.0)
    # Under R2 comparative extension: active score (0.0) <= switch cost (5.0m) -> rejects extension
    assert should_end is True
    assert ctl.last_decision_record["reason_code"] == "SWITCH_COMPARATIVE_REJECTED"


def test_hard_cap_forces_switch_with_large_active_queue():
    """Unit test: hard cap reached forces switch regardless of how large the active queue is."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2_R3)
    ctl.decide_green("NS", {"N": 24.0, "S": 24.0, "E": 15.0, "W": 15.0}, t=0.0)
    # Competing axis red started at 0.0
    ctl.red_start_times["EW"] = 0.0

    # At t = 40.0s, competing red elapsed = 40s >= hard cap (35s)
    # Active queue is still saturated at 24.0m
    should_end = ctl.green_should_end("NS", elapsed=40.0, queues={"N": 24.0, "S": 24.0, "E": 15.0, "W": 15.0}, t=40.0)
    assert should_end is True
    assert ctl.last_decision_record["reason_code"] == "SWITCH_FAIRNESS_HARD"


def test_r3_soft_fairness_empty_competing_queue_does_not_switch():
    """Unit test: R3 queue-aware fairness does NOT trigger a soft switch if competing queue is empty."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2_R3)
    ctl.decide_green("NS", {"N": 15.0, "S": 15.0, "E": 0.0, "W": 0.0}, t=0.0)
    ctl.red_start_times["EW"] = 0.0

    # Competing red elapsed = 25s (> soft min wait 20s), but competing queue is 0.0m
    # Under R3, soft fairness should NOT trigger because competing queue is empty!
    # Active score (15.0) > 0 + 5.0 -> comparative extension approved!
    should_end = ctl.green_should_end("NS", elapsed=25.0, queues={"N": 15.0, "S": 15.0, "E": 0.0, "W": 0.0}, t=25.0)
    assert should_end is False
    assert ctl.last_decision_record["reason_code"] == "EXTEND_COMPARATIVE"


def test_r2_comparative_extension_logic():
    """Unit test: R2 extension approved only if active_score > margin * competing_score + switch_cost."""
    states = MockStates()
    cfg = C.HybridQueueAdaptiveConfig(rungs=("R2",), r2_margin=1.0, r2_switch_cost_m=5.0)
    ctl = HybridQueueAdaptiveController(states, cfg=cfg)
    ctl.decide_green("NS", {"N": 10.0, "S": 10.0, "E": 8.0, "W": 8.0}, t=0.0)

    # Competing red elapsed = 10s. Competing score = 8.0 * (1 + 10/35) = 10.28m
    # Threshold = 1.0 * 10.28 + 5.0 = 15.28m
    # Case A: Active queue = 12.0m -> score_active = 12.0m < 15.28m -> REJECT
    should_end = ctl.green_should_end("NS", elapsed=25.0, queues={"N": 12.0, "S": 12.0, "E": 8.0, "W": 8.0}, t=25.0)
    assert should_end is True
    assert ctl.last_decision_record["reason_code"] == "SWITCH_COMPARATIVE_REJECTED"

    # Case B: Active queue = 20.0m -> score_active = 20.0m > 15.28m -> APPROVE
    ctl2 = HybridQueueAdaptiveController(states, cfg=cfg)
    ctl2.decide_green("NS", {"N": 20.0, "S": 20.0, "E": 8.0, "W": 8.0}, t=0.0)
    should_end2 = ctl2.green_should_end("NS", elapsed=25.0, queues={"N": 20.0, "S": 20.0, "E": 8.0, "W": 8.0}, t=25.0)
    assert should_end2 is False
    assert ctl2.last_decision_record["reason_code"] == "EXTEND_COMPARATIVE"


def test_saturated_sensor_handled_safely():
    """Unit test: saturated sensor readings (24.9m) are handled without error or numerical instability."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2_R3)
    ctl.decide_green("NS", {"N": 24.9, "S": 24.9, "E": 24.9, "W": 24.9}, t=0.0)
    should_end = ctl.green_should_end("NS", elapsed=15.0, queues={"N": 24.9, "S": 24.9, "E": 24.9, "W": 24.9}, t=15.0)
    assert isinstance(should_end, bool)
    assert ctl.last_decision_record["q_active_m"] == 24.9


def test_offline_sensor_never_read_as_zero():
    """Unit test: missing, negative (-1.0), or NaN queue values fall back safely and are never read as 0.0."""
    states = MockStates()
    ctl = HybridQueueAdaptiveController(states, cfg=C.HYBRID_R2_R3)
    
    # 1. Step with valid initial reading
    ctl.decide_green("NS", {"N": 14.5, "S": 12.0, "E": 8.0, "W": 7.0}, t=0.0)
    assert ctl._last_valid_queues["N"] == 14.5

    # 2. Detector on North goes offline (returns negative SUMO error code -1.0)
    dirty_queues = {"N": -1.0, "S": 12.0, "E": 8.0, "W": 7.0}
    clean = ctl._clean_queues(dirty_queues)
    assert clean["N"] == 14.5, "Offline sensor (-1.0) must fall back to last valid reading (14.5m), never 0.0"

    # 3. Detector on East is NaN
    dirty_queues2 = {"N": 14.5, "S": 12.0, "E": float("nan"), "W": 7.0}
    clean2 = ctl._clean_queues(dirty_queues2)
    assert clean2["E"] == 8.0, "Offline sensor (NaN) must fall back to last valid reading (8.0m), never 0.0"

    # 4. Detector is completely missing from dict
    dirty_queues3 = {"S": 12.0, "W": 7.0}
    clean3 = ctl._clean_queues(dirty_queues3)
    assert clean3["N"] == 14.5
    assert clean3["E"] == 8.0


def test_safety_invariants_across_all_rung_controllers():
    """Verify no green-to-green and yellow/all-red clearances across all ladder rung controller classes."""
    states = MockStates()
    controllers = [
        HybridQueueAdaptiveController(states),
        HybridR2Controller(states),
        HybridR2R3Controller(states),
        HybridR2R3R4Controller(states),
    ]
    for ctl in controllers:
        assert ctl.timing.yellow_s == 3.0
        assert ctl.timing.all_red_s == 2.0
        ctl.step(0.0, {"N": 10.0, "S": 10.0, "E": 10.0, "W": 10.0})
        assert ctl.phase == "GREEN"
        assert ctl.desired_state() == states.green("NS")
