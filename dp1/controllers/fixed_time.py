"""Fixed-time signal controller using preset BTP signal plans."""
from typing import Optional, List, Dict
from .base import PhaseMachineController
from .webster_utils import format_plan_record
from .. import config as C


class FixedTimeController(PhaseMachineController):
    """Baseline: preset green per axis, ignores traffic. Uses SAME yellow/all-red as adaptive."""
    name = "fixed"

    def __init__(self, states, plan=None, network="synthetic", timing=None, **kw):
        super().__init__(states, timing=timing or C.TIMING, **kw)
        self.network = network.lower().strip()
        if plan is not None:
            self.plan = plan
        elif self.network == "marathahalli":
            self.plan = C.FIXED_MARATHAHALLI
        else:
            self.plan = C.FIXED

        self.plan_log: List[Dict] = []
        rec = format_plan_record(
            t_applied_s=0.0,
            plan=self.plan,
            timing=self.timing,
            source="btp_fixed",
            cycle_index=0,
            extra={"network": self.network},
        )
        self.plan_log.append(rec)

    def decide_green(self, axis: str, queues, t: float) -> float:
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s
