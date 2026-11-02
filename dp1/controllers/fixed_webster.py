"""Fixed-time signal controller using Webster's optimal cycle and split per scenario."""
from typing import Optional, List, Dict
from .base import PhaseMachineController
from .webster_utils import format_plan_record
from .. import config as C


class FixedWebsterController(PhaseMachineController):
    """Fixed-time baseline using Webster's formula derived from average scenario demand."""
    name = "fixed_webster"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        plan: Optional[C.FixedTimeConfig] = None,
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "synthetic",
        timing: Optional[C.SignalTiming] = None,
        **kw,
    ):
        super().__init__(states, timing=timing or C.TIMING, **kw)
        self.scenario = scenario
        self.demand_level = demand_level
        self.network = network.lower().strip()
        if plan is not None:
            self.plan = plan
        elif self.network == "marathahalli" or scenario in (
            "imbalanced_orr", "imbalanced_varthur", "surge_orr_north",
            "ramp_peak", "surge_shift", "lane_closure",
        ):
            from ..site_scenarios import site_webster_plan
            self.plan = site_webster_plan(scenario, demand_level=demand_level)
        else:
            self.plan = C.webster_plan(scenario, demand_level=demand_level)

        self.plan_log: List[Dict] = []
        rec = format_plan_record(
            t_applied_s=0.0,
            plan=self.plan,
            timing=self.timing,
            source=self.name,
            cycle_index=0,
            extra={"scenario": self.scenario, "demand_level": self.demand_level},
        )
        self.plan_log.append(rec)

    def decide_green(self, axis: str, queues, t: float) -> float:
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s


class WebsterOracleController(FixedWebsterController):
    """[ORACLE] Webster baseline using true offline mathematical scenario demand curves.

    Diagnostic only; not included in the main competitive evaluation matrix.
    Uses true scenario arrival curves rather than live or warm-up sensor measurements.
    """
    name = "webster_oracle"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.plan_log:
            self.plan_log[0]["source"] = "webster_oracle"
            self.plan_log[0]["is_oracle"] = True
