from .base import PhaseMachineController
from .. import config as C


class FixedTimeController(PhaseMachineController):
    """Baseline: preset green per axis, ignores traffic. Uses SAME yellow/all-red as adaptive."""
    name = "fixed"

    def __init__(self, states, plan=None, network="synthetic", **kw):
        super().__init__(states, **kw)
        if plan is not None:
            self.plan = plan
        elif network == "marathahalli":
            self.plan = C.FIXED_MARATHAHALLI
        else:
            self.plan = C.FIXED

    def decide_green(self, axis, queues, t):
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s
