"""Unit and regression tests for PhaseMachineController action seam (Phase P1).

Verifies:
1. Default legacy controller behavior remains intact (action=None).
2. Action seam semantics: ControllerAction.HOLD vs ControllerAction.REQUEST_SWITCH.
3. Minimum green cannot be violated: requests before min_green are ignored.
4. Maximum green forces switch even when HOLD is requested.
5. External actions are ignored outside GREEN (during YELLOW and ALL_RED).
6. Clearance safety invariant is strictly maintained (GREEN -> YELLOW -> ALL_RED -> GREEN(other axis)).
7. Both integer (0/1) and enum action representations are accepted.
8. Subclass decide_action() hook integration.
9. Decisions record tracks both green_s (planned target) and actual_green_s (elapsed duration).
"""
import random
import pytest

from dp1 import config as C
from dp1.controllers.base import PhaseMachineController, ControllerAction
from dp1.controllers.fixed_time import FixedTimeController
from dp1.controllers.adaptive_queue import AdaptiveQueueController


class DummyStates:
    def green(self, axis):
        return "GGGG" if axis == "NS" else "gggg"

    def yellow(self, axis):
        return "yyyy"

    def all_red(self):
        return "rrrr"


class ActionTestController(PhaseMachineController):
    name = "action_test"

    def __init__(self, states=None, min_green_s=10.0, max_green_s=60.0, **kw):
        super().__init__(states or DummyStates(), min_green_s=min_green_s, max_green_s=max_green_s, **kw)

    def decide_green(self, axis, queues, t):
        return float(self.max_green_s)


class HookTestController(PhaseMachineController):
    name = "hook_test"

    def __init__(self, action_sequence, states=None, min_green_s=10.0, max_green_s=60.0, **kw):
        super().__init__(states or DummyStates(), min_green_s=min_green_s, max_green_s=max_green_s, **kw)
        self.action_sequence = dict(action_sequence)

    def decide_green(self, axis, queues, t):
        return float(self.max_green_s)

    def decide_action(self, axis, elapsed, queues, t):
        return self.action_sequence.get(int(elapsed), ControllerAction.HOLD)


@pytest.fixture
def empty_queues():
    return {a: 0.0 for a in C.APPROACHES}


def test_default_legacy_fixed_controller_timing_unchanged(empty_queues):
    """Legacy FixedTimeController runs 105s NS, 3s Y, 2s AR, 95s EW with action=None."""
    ctl = FixedTimeController(DummyStates())
    ctl.start(0.0, empty_queues)

    assert ctl.phase == "GREEN"
    assert ctl.axis == "NS"
    assert ctl.target_green == C.FIXED.green_ns_s

    # Step through NS green
    for t in range(1, int(C.FIXED.green_ns_s)):
        ctl.step(float(t), empty_queues)
        assert ctl.phase == "GREEN"

    # At exact target green, switch to YELLOW
    ctl.step(float(C.FIXED.green_ns_s), empty_queues)
    assert ctl.phase == "YELLOW"
    assert ctl.decisions[-1]["actual_green_s"] == C.FIXED.green_ns_s
    assert ctl.decisions[-1]["green_s"] == C.FIXED.green_ns_s

    # Yellow clearance (3s)
    y_start = float(C.FIXED.green_ns_s)
    ctl.step(y_start + 1.0, empty_queues)
    assert ctl.phase == "YELLOW"
    ctl.step(y_start + 2.0, empty_queues)
    assert ctl.phase == "YELLOW"
    ctl.step(y_start + 3.0, empty_queues)
    assert ctl.phase == "ALL_RED"

    # All-red clearance (2s)
    ar_start = y_start + 3.0
    ctl.step(ar_start + 1.0, empty_queues)
    assert ctl.phase == "ALL_RED"
    ctl.step(ar_start + 2.0, empty_queues)
    assert ctl.phase == "GREEN"
    assert ctl.axis == "EW"
    assert ctl.target_green == C.FIXED.green_ew_s


def test_action_seam_request_switch_rejected_before_min_green(empty_queues):
    """REQUEST_SWITCH is ignored while elapsed < min_green_s."""
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    for t in range(1, 10):
        ctl.step(float(t), empty_queues, action=ControllerAction.REQUEST_SWITCH)
        assert ctl.phase == "GREEN", f"Premature switch at t={t} before min_green=10"
        assert ctl.axis == "NS"


def test_action_seam_request_switch_accepted_at_min_green(empty_queues):
    """REQUEST_SWITCH is accepted at elapsed >= min_green_s."""
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    for t in range(1, 10):
        ctl.step(float(t), empty_queues, action=ControllerAction.HOLD)
        assert ctl.phase == "GREEN"

    # At t=10 (elapsed=10 >= min_green=10), switch is accepted
    ctl.step(10.0, empty_queues, action=ControllerAction.REQUEST_SWITCH)
    assert ctl.phase == "YELLOW"
    assert ctl.decisions[-1]["actual_green_s"] == 10.0


def test_action_seam_max_green_forces_switch_on_hold(empty_queues):
    """HOLD cannot prevent transition once elapsed >= max_green_s."""
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    for t in range(1, 60):
        ctl.step(float(t), empty_queues, action=ControllerAction.HOLD)
        assert ctl.phase == "GREEN"

    # At t=60 (elapsed=60 >= max_green=60), switch is forced
    ctl.step(60.0, empty_queues, action=ControllerAction.HOLD)
    assert ctl.phase == "YELLOW"
    assert ctl.decisions[-1]["actual_green_s"] == 60.0


def test_action_seam_actions_ignored_during_yellow_and_all_red(empty_queues):
    """Action is completely ignored during clearance phases (YELLOW / ALL_RED)."""
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    # Trigger switch at t=15
    ctl.step(15.0, empty_queues, action=ControllerAction.REQUEST_SWITCH)
    assert ctl.phase == "YELLOW"

    # During YELLOW: spam REQUEST_SWITCH
    ctl.step(16.0, empty_queues, action=ControllerAction.REQUEST_SWITCH)
    assert ctl.phase == "YELLOW"
    ctl.step(17.0, empty_queues, action=ControllerAction.REQUEST_SWITCH)
    assert ctl.phase == "YELLOW"
    ctl.step(18.0, empty_queues, action=ControllerAction.HOLD)
    assert ctl.phase == "ALL_RED"

    # During ALL_RED: spam REQUEST_SWITCH
    ctl.step(19.0, empty_queues, action=ControllerAction.REQUEST_SWITCH)
    assert ctl.phase == "ALL_RED"
    ctl.step(20.0, empty_queues, action=ControllerAction.HOLD)
    assert ctl.phase == "GREEN"
    assert ctl.axis == "EW"


def test_action_seam_supports_integer_actions(empty_queues):
    """Integer actions 0 (HOLD) and 1 (REQUEST_SWITCH) work identically to enum."""
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    # 1 before min_green ignored
    ctl.step(5.0, empty_queues, action=1)
    assert ctl.phase == "GREEN"

    # 0 holds
    ctl.step(10.0, empty_queues, action=0)
    assert ctl.phase == "GREEN"

    # 1 after min_green switches
    ctl.step(12.0, empty_queues, action=1)
    assert ctl.phase == "YELLOW"


def test_action_seam_invalid_action_raises_value_error(empty_queues):
    """Invalid action raises ValueError."""
    ctl = ActionTestController()
    ctl.start(0.0, empty_queues)

    with pytest.raises(ValueError, match="Invalid action"):
        ctl.step(5.0, empty_queues, action=99)

    with pytest.raises(ValueError, match="Invalid action"):
        ctl.step(5.0, empty_queues, action="INVALID_ACTION")


def test_action_seam_decide_action_subclass_hook(empty_queues):
    """Subclass implementing decide_action() has actions applied when action=None."""
    # Switch at elapsed = 20s
    ctl = HookTestController(action_sequence={20: ControllerAction.REQUEST_SWITCH})
    ctl.start(0.0, empty_queues)

    for t in range(1, 20):
        ctl.step(float(t), empty_queues)
        assert ctl.phase == "GREEN"

    ctl.step(20.0, empty_queues)
    assert ctl.phase == "YELLOW"
    assert ctl.decisions[-1]["actual_green_s"] == 20.0


def test_action_seam_never_switches_green_to_green_under_random_actions(empty_queues):
    """Invariant: under arbitrary random actions, every switch is GREEN -> YELLOW -> ALL_RED -> GREEN(other)."""
    rng = random.Random(42)
    ctl = ActionTestController(min_green_s=10.0, max_green_s=60.0)
    ctl.start(0.0, empty_queues)

    history = [(0.0, ctl.phase, ctl.axis)]
    for t in range(1, 600):
        act = rng.choice([0, 1])
        ctl.step(float(t), empty_queues, action=act)
        history.append((float(t), ctl.phase, ctl.axis))

    # Analyze phase changes
    phase_changes = []
    for (t0, p0, a0), (t1, p1, a1) in zip(history, history[1:]):
        if (p0, a0) != (p1, a1):
            phase_changes.append((t1, p0, a0, p1, a1))

    for t, p0, a0, p1, a1 in phase_changes:
        assert (p0, p1) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, (
            f"Illegal transition at t={t}: {p0} -> {p1}"
        )
        if p0 == "ALL_RED" and p1 == "GREEN":
            assert a0 != a1, f"Axis did not switch after ALL_RED at t={t}: {a0} -> {a1}"
