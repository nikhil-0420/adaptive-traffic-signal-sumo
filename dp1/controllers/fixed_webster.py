"""Fixed-time signal controller using Webster's optimal cycle and split per scenario."""
from .base import PhaseMachineController
from .. import config as C


class FixedWebsterController(PhaseMachineController):
    """Fixed-time baseline using Webster's formula derived from average scenario demand."""
    name = "fixed_webster"

    def __init__(self, states, scenario="balanced", plan=None, **kw):
        super().__init__(states, **kw)
        self.scenario = scenario
        self.plan = plan or C.webster_plan(scenario)

    def decide_green(self, axis, queues, t):
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s
