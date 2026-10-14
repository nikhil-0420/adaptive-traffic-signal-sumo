"""Fixed-time signal controller using Webster's optimal cycle and split per scenario."""
from .base import PhaseMachineController
from .. import config as C


class FixedWebsterController(PhaseMachineController):
    """Fixed-time baseline using Webster's formula derived from average scenario demand."""
    name = "fixed_webster"

    def __init__(self, states, scenario="balanced", plan=None, demand_level=C.DEFAULT_DEMAND_LEVEL, network="synthetic", **kw):
        super().__init__(states, **kw)
        self.scenario = scenario
        self.demand_level = demand_level
        self.network = network
        if plan is not None:
            self.plan = plan
        elif network == "marathahalli" or scenario in ("imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
            from ..site_scenarios import site_webster_plan
            self.plan = site_webster_plan(scenario, demand_level=demand_level)
        else:
            self.plan = C.webster_plan(scenario, demand_level=demand_level)

    def decide_green(self, axis, queues, t):
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s

