"""Fixed-time controller matching Webster's cycle length with BTP 105:95 split ratio.

Purpose:
Separates the performance benefit of "cycle length optimization" from
"directional green split adaptation". Webster adapts both cycle and split;
fixed_matched_cycle uses Webster's cycle length with the fixed BTP split ratio.
"""
from typing import Optional, Dict, List
from .base import PhaseMachineController
from .webster_utils import format_plan_record
from .. import config as C


class FixedMatchedCycleController(PhaseMachineController):
    """Fixed-time plan using Webster-matched cycle length and fixed BTP split ratio."""
    name = "fixed_matched_cycle"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "synthetic",
        cfg: Optional[C.FixedMatchedCycleConfig] = None,
        timing: Optional[C.SignalTiming] = None,
        **kw,
    ):
        super().__init__(states, timing=timing or C.TIMING, **kw)
        self.scenario = scenario
        self.demand_level = demand_level
        self.network = network.lower().strip()
        self.cfg = cfg or C.FIXED_MATCHED_CYCLE

        # 1. Obtain Webster plan for the specific scenario and demand level
        if self.network == "marathahalli" or self.scenario in (
            "imbalanced_orr", "imbalanced_varthur", "surge_orr_north",
            "ramp_peak", "surge_shift", "lane_closure",
        ):
            from ..site_scenarios import site_webster_plan
            w_plan = site_webster_plan(self.scenario, demand_level=self.demand_level)
        else:
            w_plan = C.webster_plan(self.scenario, demand_level=self.demand_level)

        # 2. Extract Webster cycle and total effective green
        L = 2.0 * (self.timing.yellow_s + self.timing.all_red_s)  # 10.0 s
        c_webster = w_plan.green_ns_s + w_plan.green_ew_s + L
        g_total = max(20.0, c_webster - L)

        # 3. Apply BTP split ratio (105s : 95s -> 52.5% : 47.5%)
        # In Marathahalli: Varthur (EW) is 105s, ORR (NS) is 95s
        # In Synthetic: NS is 105s, EW is 95s (historical mapping)
        min_g = float(self.cfg.min_green_s)
        if self.network == "marathahalli":
            g_ew = max(min_g, round(self.cfg.btp_split_ratio_ew * g_total, 1))
            g_ns = max(min_g, round(g_total - g_ew, 1))
        else:
            g_ns = max(min_g, round(self.cfg.btp_split_ratio_ew * g_total, 1))
            g_ew = max(min_g, round(g_total - g_ns, 1))

        self.plan = C.FixedTimeConfig(green_ns_s=g_ns, green_ew_s=g_ew)
        self.webster_cycle_s = c_webster

        # 4. Plan audit trail
        self.plan_log: List[Dict] = []
        extra = {
            "matched_webster_cycle_s": round(c_webster, 1),
            "webster_original_green_ns_s": round(w_plan.green_ns_s, 1),
            "webster_original_green_ew_s": round(w_plan.green_ew_s, 1),
            "split_ratio_description": "BTP 105:95 (52.5% : 47.5%)",
        }
        self._log_plan(0.0, self.plan, "fixed_matched_cycle", extra=extra)

    def _log_plan(self, t: float, plan: C.FixedTimeConfig, source: str, extra: Optional[Dict] = None):
        rec = format_plan_record(
            t_applied_s=t,
            plan=plan,
            timing=self.timing,
            source=source,
            cycle_index=self.cycle,
            extra=extra,
        )
        self.plan_log.append(rec)

    def decide_green(self, axis: str, queues, t: float) -> float:
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s
