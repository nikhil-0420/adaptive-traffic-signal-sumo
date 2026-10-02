from .base import PhaseMachineController
from .. import config as C


class FixedTimeController(PhaseMachineController):
    """Baseline: preset green per axis, ignores traffic. Uses SAME yellow/all-red as adaptive."""
    name = "fixed"

    def __init__(self, states, plan=C.FIXED, **kw):
        super().__init__(states, **kw)
        self.plan = plan

    def decide_green(self, axis, queues, t):
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s
