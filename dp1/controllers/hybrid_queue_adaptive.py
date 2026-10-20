"""Hybrid Queue-Adaptive traffic signal controller for DP1.

Integrates three complementary functions:
1. Baseline timing allocation (G_base): Derived from Webster's optimal cycle split
   based on scenario flow and saturation flow rates, bounded by [min_green, max_green].
2. Queue-aware dynamic control: Evaluates active queues, competing queues, dynamic arrivals
   and demand scores to approve bounded extensions (delta_G, default 3s steps).
3. Safety and fairness supervisor: Enforces min_green (10s), max_green (60s), gap-out,
   anti-monopoly competing wait limits (35s), and legal phase transitions.
"""

from typing import Dict, Any, Optional
from .base import PhaseMachineController
from .. import config as C


class HybridQueueAdaptiveController(PhaseMachineController):
    """Hybrid Queue-Adaptive Signal Controller with Explainable Increments."""

    name = "hybrid_queue_adaptive"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "marathahalli",
        cfg: Optional[C.HybridQueueAdaptiveConfig] = None,
        plan: Optional[C.FixedTimeConfig] = None,
        **kw,
    ):
        self.cfg = cfg or C.HYBRID_QUEUE_ADAPTIVE
        min_g = kw.pop("min_green_s", self.cfg.min_green_s)
        max_g = kw.pop("max_green_s", self.cfg.max_green_s)
        super().__init__(states, min_green_s=min_g, max_green_s=max_g, **kw)

        self.scenario = scenario
        self.demand_level = demand_level
        self.network = network

        # 1. Establish Webster-derived baseline green plan
        if plan is not None:
            self.baseline_plan = plan
        elif network == "marathahalli" or scenario in ("imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
            from ..site_scenarios import site_webster_plan
            self.baseline_plan = site_webster_plan(scenario, demand_level=demand_level)
        else:
            self.baseline_plan = C.webster_plan(scenario, demand_level=demand_level)

        # Baseline targets clamped to [min_green, max_green]
        self.baseline_green_s = {
            "NS": max(self.cfg.min_green_s, min(self.cfg.max_green_s, self.baseline_plan.green_ns_s)),
            "EW": max(self.cfg.min_green_s, min(self.cfg.max_green_s, self.baseline_plan.green_ew_s)),
        }

        # Dynamic state tracking
        self.accumulated_extra_s: float = 0.0  # G_extra
        self.target_green_s: float = 0.0       # G_target = G_base + G_extra
        self.red_start_times: Dict[str, float] = {"NS": 0.0, "EW": 0.0}
        self._prev_queues: Dict[str, float] = {"NS": 0.0, "EW": 0.0}
        self._empty_since: Optional[float] = None
        self.extensions_granted: int = 0
        self.last_decision_record: Dict[str, Any] = {}

    @staticmethod
    def axis_queue(axis: str, queues: Dict[str, float]) -> float:
        """Maximum longitudinal approach queue across approaches on this axis."""
        return max(queues.get(a, 0.0) for a in C.AXES[axis])

    def decide_green(self, axis: str, queues: Dict[str, float], t: float) -> float:
        """Establish baseline green duration upon entering GREEN."""
        c = self.cfg
        self._empty_since = None
        self.accumulated_extra_s = 0.0
        self.extensions_granted = 0
        other_axis = C.OTHER_AXIS[axis]
        self.red_start_times[other_axis] = t

        # Set baseline green G_base
        g_base = self.baseline_green_s.get(axis, c.min_green_s)
        self.target_green_s = g_base

        own_q = self.axis_queue(axis, queues)
        comp_q = self.axis_queue(other_axis, queues)
        self._prev_queues[axis] = own_q
        self._prev_queues[other_axis] = comp_q

        axis_label = "North–South (ORR)" if axis == "NS" else "East–West (Varthur Rd)"
        rec = {
            "t": round(t, 1),
            "cycle": self.cycle,
            "axis": axis,
            "action": "ENTER_GREEN",
            "reason": f"{axis_label} green initiated with Webster baseline allocation {g_base:.1f}s.",
            "reason_code": "BASELINE_ENTRY",
            "g_base_s": round(g_base, 1),
            "delta_g_req_s": 0.0,
            "delta_g_app_s": 0.0,
            "g_extra_s": 0.0,
            "target_green_s": round(self.target_green_s, 1),
            "elapsed_s": 0.0,
            "q_active_m": round(own_q, 1),
            "q_competing_m": round(comp_q, 1),
            "score_active": round(own_q, 1),
            "score_competing": round(comp_q, 1),
            "is_max_green": False,
            "green_s": round(self.target_green_s, 1),
            "actual_green_s": round(self.target_green_s, 1),
            **{f"q_{a}_m": round(queues.get(a, 0.0), 1) for a in C.APPROACHES},
        }
        self.last_decision_record = rec
        return g_base

    def green_should_end(self, axis: str, elapsed: float, queues: Dict[str, float], t: float) -> bool:
        """Evaluate hold, extension, gap-out, or switch at each step during GREEN."""
        c = self.cfg
        other_axis = C.OTHER_AXIS[axis]
        own_q = self.axis_queue(axis, queues)
        comp_q = self.axis_queue(other_axis, queues)
        competing_red_elapsed = max(0.0, t - self.red_start_times.get(other_axis, 0.0))

        # Dynamic arrival detection: check queue growth indicating incoming arrivals
        prev_own = self._prev_queues.get(axis, own_q)
        delta_q = max(0.0, own_q - prev_own)
        self._prev_queues[axis] = own_q
        self._prev_queues[other_axis] = comp_q

        # Demand scores
        score_active = own_q + 0.5 * delta_q
        wait_factor = 1.0 + (competing_red_elapsed / max(1.0, c.max_competing_wait_s))
        score_competing = comp_q * wait_factor

        axis_label = "North–South" if axis == "NS" else "East–West"
        comp_label = "East–West" if axis == "NS" else "North–South"

        # -------------------------------------------------------------
        # 1. Hard Minimum Green Floor Enforcement
        # -------------------------------------------------------------
        if elapsed < c.min_green_s:
            rec = self._make_record(
                t, axis, "HOLD",
                f"{axis_label} elapsed green ({elapsed:.1f}s) < minimum green floor ({c.min_green_s:.1f}s); switch prohibited by safety invariant.",
                "HOLD_MIN_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
            )
            self.last_decision_record = rec
            return False

        # -------------------------------------------------------------
        # 2. Hard Maximum Green Ceiling Enforcement
        # -------------------------------------------------------------
        if elapsed >= c.max_green_s:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"{axis_label} elapsed green ({elapsed:.1f}s) >= maximum green ceiling ({c.max_green_s:.1f}s); switch forced to prevent approach starvation.",
                "SWITCH_MAX_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, True
            )
            self.last_decision_record = rec
            return True

        # -------------------------------------------------------------
        # 3. Gap-Out Evaluation: Active approach fully cleared
        # -------------------------------------------------------------
        if own_q <= 0.0 and comp_q >= c.min_competing_queue_m:
            if self._empty_since is None:
                self._empty_since = t
            empty_duration = t - self._empty_since
            if empty_duration >= c.gap_out_s:
                rec = self._make_record(
                    t, axis, "GAP_OUT",
                    f"{axis_label} queue cleared (0.0m for {empty_duration:.1f}s >= gap-out threshold {c.gap_out_s:.1f}s) while {comp_label} is waiting ({comp_q:.1f}m); gapping out early.",
                    "SWITCH_GAP_OUT", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
                )
                self.last_decision_record = rec
                return True
            else:
                rec = self._make_record(
                    t, axis, "HOLD",
                    f"{axis_label} queue empty for {empty_duration:.1f}s (< gap-out persistence {c.gap_out_s:.1f}s); holding green for clearance.",
                    "HOLD_CLEARING", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
                )
                self.last_decision_record = rec
                return False
        else:
            self._empty_since = None

        # -------------------------------------------------------------
        # 4. Within Approved Target Green Duration
        # -------------------------------------------------------------
        if elapsed < self.target_green_s:
            rec = self._make_record(
                t, axis, "HOLD",
                f"{axis_label} green servicing within approved target ({self.target_green_s:.1f}s = baseline {self.baseline_green_s[axis]:.1f}s + extra {self.accumulated_extra_s:.1f}s); elapsed: {elapsed:.1f}s.",
                "HOLD_SERVICING", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
            )
            self.last_decision_record = rec
            return False

        # -------------------------------------------------------------
        # 5. Target Reached: Evaluate Bounded Extension Increment
        # -------------------------------------------------------------
        req_increment = c.extend_step_s
        headroom = max(0.0, c.max_green_s - self.target_green_s)

        # 5a. Check Headroom to Max Green
        if headroom <= 0.0:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: {axis_label} target green ({self.target_green_s:.1f}s) has reached maximum ceiling ({c.max_green_s:.1f}s). Enforcing mandatory switch.",
                "SWITCH_CEILING_REACHED", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, True
            )
            self.last_decision_record = rec
            return True

        # 5b. Anti-Monopoly Check: Competing red wait limit
        if comp_q >= c.min_competing_queue_m and competing_red_elapsed >= c.max_competing_wait_s:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Competing {comp_label} red wait ({competing_red_elapsed:.1f}s) >= maximum allowed wait ({c.max_competing_wait_s:.1f}s) with waiting queue ({comp_q:.1f}m). Triggering fair phase switch.",
                "SWITCH_FAIRNESS_WAIT_LIMIT", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
            )
            self.last_decision_record = rec
            return True

        # 5c. Demand Imbalance Check: Competing score exceeds fairness ratio
        if comp_q >= c.min_competing_queue_m and score_competing > (score_active * c.fairness_ratio):
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Competing {comp_label} demand score ({score_competing:.1f}) exceeds active {axis_label} score ({score_active:.1f}) by fairness ratio ({c.fairness_ratio}). Switching to relieve opposing corridor.",
                "SWITCH_DEMAND_FAIRNESS", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
            )
            self.last_decision_record = rec
            return True

        # 5d. Active Demand Justification: Queue must exceed threshold or have arrivals
        if own_q < c.extend_threshold_m and delta_q < c.arrival_detection_threshold:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Active {axis_label} queue ({own_q:.1f}m < threshold {c.extend_threshold_m:.1f}m) and no new arrivals detected (delta Q = {delta_q:.1f}m). Terminating green phase.",
                "SWITCH_DEMAND_EXHAUSTED", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False
            )
            self.last_decision_record = rec
            return True

        # -------------------------------------------------------------
        # 6. Approved Extension
        # -------------------------------------------------------------
        app_increment = min(req_increment, headroom)
        self.accumulated_extra_s += app_increment
        self.target_green_s += app_increment
        self.extensions_granted += 1

        explanation = (
            f"{axis_label} green extended by {app_increment:.0f} seconds: "
            f"its queue/demand condition ({own_q:.1f}m >= {c.extend_threshold_m:.1f}m) satisfied the configured extension rule, "
            f"the competing-direction wait ({competing_red_elapsed:.1f}s) remained within its permitted limit ({c.max_competing_wait_s:.0f}s), "
            f"and maximum green was not reached."
        )

        rec = self._make_record(
            t, axis, "EXTEND",
            explanation,
            "EXTEND_APPROVED", req_increment, app_increment, elapsed, own_q, comp_q, score_active, score_competing, queues, False
        )
        self.last_decision_record = rec
        self.decisions.append(rec)
        return False

    def _make_record(
        self,
        t: float,
        axis: str,
        action: str,
        reason: str,
        reason_code: str,
        req_increment: float,
        app_increment: float,
        elapsed: float,
        own_q: float,
        comp_q: float,
        score_active: float,
        score_competing: float,
        queues: Dict[str, float],
        is_max: bool,
    ) -> Dict[str, Any]:
        """Construct structured decision record."""
        return {
            "t": round(t, 1),
            "cycle": self.cycle,
            "axis": axis,
            "action": action,
            "reason": reason,
            "reason_code": reason_code,
            "g_base_s": round(self.baseline_green_s[axis], 1),
            "delta_g_req_s": round(req_increment, 1),
            "delta_g_app_s": round(app_increment, 1),
            "g_extra_s": round(self.accumulated_extra_s, 1),
            "target_green_s": round(self.target_green_s, 1),
            "elapsed_s": round(elapsed, 1),
            "q_active_m": round(own_q, 1),
            "q_competing_m": round(comp_q, 1),
            "score_active": round(score_active, 1),
            "score_competing": round(score_competing, 1),
            "is_max_green": is_max,
            "green_s": round(self.target_green_s, 1),
            "actual_green_s": round(elapsed, 1),
            **{f"q_{a}_m": round(queues.get(a, 0.0), 1) for a in C.APPROACHES},
        }
