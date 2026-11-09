"""Hybrid Queue-Adaptive Ablation Controller for DP1 XAI Studies (Items 4 and 5).

Subclasses HybridQueueAdaptiveController while leaving v1 completely untouched.
Supports enabling/disabling the three core rules:
- R-base: Webster baseline allocation from rolling measured flows (when False, uses fixed 15s green).
- R-ext: Queue-responsive +3s extension when queue >= 4.0m (when False, switches at g_base).
- R-guard: Competing red-wait limit (35s) while competing queue >= 2.0m (when False, no wait cap).

Supports parameter overrides for sensitivity analysis (Item 5).
Guarantees bitwise exact reproduction of v1 when all rules are enabled with default parameters.
"""
from typing import Dict, Any, Optional
from copy import deepcopy

from .hybrid_queue_adaptive import HybridQueueAdaptiveController
from .. import config as C


class HybridQueueAdaptiveAblationController(HybridQueueAdaptiveController):
    """Ablation and sensitivity variant of the Hybrid Queue-Adaptive Controller."""

    name = "hybrid_queue_adaptive_ablation"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "marathahalli",
        cfg: Optional[C.HybridQueueAdaptiveConfig] = None,
        r_base: bool = True,
        r_ext: bool = True,
        r_guard: bool = True,
        extend_step_s: Optional[float] = None,
        extend_threshold_m: Optional[float] = None,
        max_competing_wait_s: Optional[float] = None,
        min_competing_queue_m: Optional[float] = None,
        **kw,
    ):
        base_cfg = cfg or C.HYBRID_QUEUE_ADAPTIVE
        # Clone configuration if any parameter override is specified
        has_overrides = any(
            x is not None for x in [extend_step_s, extend_threshold_m, max_competing_wait_s, min_competing_queue_m]
        )
        if has_overrides:
            self.custom_cfg = deepcopy(base_cfg)
            if extend_step_s is not None:
                self.custom_cfg.extend_step_s = float(extend_step_s)
            if extend_threshold_m is not None:
                self.custom_cfg.extend_threshold_m = float(extend_threshold_m)
            if max_competing_wait_s is not None:
                self.custom_cfg.max_competing_wait_s = float(max_competing_wait_s)
            if min_competing_queue_m is not None:
                self.custom_cfg.min_competing_queue_m = float(min_competing_queue_m)
            actual_cfg = self.custom_cfg
        else:
            actual_cfg = base_cfg

        super().__init__(
            states=states,
            scenario=scenario,
            demand_level=demand_level,
            network=network,
            cfg=actual_cfg,
            **kw,
        )

        self.r_base = bool(r_base)
        self.r_ext = bool(r_ext)
        self.r_guard = bool(r_guard)
        self.has_overrides = has_overrides

        # If R-base is disabled: fix baseline green to neutral 15.0s on both axes
        if not self.r_base:
            self.baseline_plan = C.FixedTimeConfig(green_ns_s=15.0, green_ew_s=15.0)
            self.baseline_green_s = {"NS": 15.0, "EW": 15.0}
            self.plan_solved = True
            self.plan_applied = True
            self.pending_plan = None

    def decide_green(self, axis: str, queues: Dict[str, float], t: float) -> float:
        """Decide green duration upon entering GREEN."""
        if self.r_base:
            return super().decide_green(axis, queues, t)

        # When R-base is disabled, fixed 15s base green without R4 Webster plan update
        self._empty_since = None
        self.accumulated_extra_s = 0.0
        self.extensions_granted = 0
        other_axis = C.OTHER_AXIS[axis]
        self.red_start_times[other_axis] = t

        cleaned_q = self._clean_queues(queues)
        g_base = 15.0
        self.target_green_s = g_base

        own_q = self.axis_queue(axis, cleaned_q)
        comp_q = self.axis_queue(other_axis, cleaned_q)
        self._prev_queues[axis] = own_q
        self._prev_queues[other_axis] = comp_q

        axis_label = "North–South (ORR)" if axis == "NS" else "East–West (Varthur Rd)"
        rec = {
            "t": round(t, 1),
            "cycle": self.cycle,
            "axis": axis,
            "proposed_action": "ENTER_GREEN",
            "applied_action": "ENTER_GREEN",
            "decision_outcome": "BASELINE_ENTRY",
            "action": "ENTER_GREEN",
            "reason": f"{axis_label} green initiated with fixed neutral baseline {g_base:.1f}s (R-base OFF).",
            "reason_code": "BASELINE_ENTRY",
            "g_base_s": round(g_base, 1),
            "delta_g_req_s": 0.0,
            "delta_g_app_s": 0.0,
            "g_extra_s": 0.0,
            "target_green_s": round(self.target_green_s, 1),
            "elapsed_s": 0.0,
            "actual_green_s": round(self.target_green_s, 1),
            "q_active_m": round(own_q, 1),
            "q_competing_m": round(comp_q, 1),
            "score_active": round(own_q, 1),
            "score_competing": round(comp_q, 1),
            "is_max_green": False,
            "green_s": round(self.target_green_s, 1),
            **{f"q_{a}_m": round(cleaned_q.get(a, 0.0), 1) for a in C.APPROACHES},
        }
        self.last_decision_record = rec
        return g_base

    def on_step_green(
        self, t: float, axis: str, queues: Dict[str, float], record_decisions: bool = True
    ) -> tuple[bool, Dict[str, Any]]:
        """Evaluate active green phase state and decide whether to extend or switch."""
        # Exact pass-through to v1 when all rules are on and no overrides exist
        if self.r_base and self.r_ext and self.r_guard and not self.has_overrides:
            return super().on_step_green(t, axis, queues, record_decisions)

        c = self.cfg
        elapsed = t - self.phase_start_time
        other_axis = C.OTHER_AXIS[axis]
        axis_label = "North–South" if axis == "NS" else "East–West"
        comp_label = "East–West" if axis == "NS" else "North–South"

        cleaned_q = self._clean_queues(queues)
        own_q = self.axis_queue(axis, cleaned_q)
        comp_q = self.axis_queue(other_axis, cleaned_q)
        delta_q = own_q - self._prev_queues.get(axis, own_q)
        self._prev_queues[axis] = own_q
        self._prev_queues[other_axis] = comp_q

        score_active = own_q
        score_competing = comp_q
        logged_q = cleaned_q
        competing_red_elapsed = t - self.red_start_times.get(other_axis, t)

        # 1. Enforce Minimum Green
        if elapsed < c.min_green_s:
            rec = self._make_record(
                t, axis, "HOLD",
                f"{axis_label} minimum green active ({elapsed:.1f}s < {c.min_green_s:.1f}s).",
                "HOLD_MIN_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="HOLD", applied_action="HOLD", decision_outcome="HOLD_MIN_GREEN"
            )
            if record_decisions:
                self.last_decision_record = rec
            return False, rec

        # 2. Hard Ceiling: Maximum Green Cap
        if elapsed >= c.max_green_s:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"{axis_label} elapsed green ({elapsed:.1f}s) >= maximum green ceiling ({c.max_green_s:.1f}s); switch forced to prevent approach starvation.",
                "SWITCH_MAX_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, True,
                proposed_action="REQUEST_SWITCH", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_MAX_GREEN"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        # 3. Gap-Out Evaluation: Active approach fully cleared
        if own_q <= 0.0 and comp_q >= c.min_competing_queue_m:
            if record_decisions:
                if self._empty_since is None:
                    self._empty_since = t
                empty_duration = t - self._empty_since
            else:
                empty_since = self._empty_since or t
                empty_duration = t - empty_since

            if empty_duration >= c.gap_out_s:
                rec = self._make_record(
                    t, axis, "GAP_OUT",
                    f"{axis_label} queue cleared (0.0m for {empty_duration:.1f}s >= gap-out threshold {c.gap_out_s:.1f}s) while {comp_label} is waiting ({comp_q:.1f}m); gapping out early.",
                    "SWITCH_GAP_OUT", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="GAP_OUT", applied_action="GAP_OUT", decision_outcome="SWITCH_GAP_OUT"
                )
                if record_decisions:
                    self.last_decision_record = rec
                    self.decisions.append(rec)
                return True, rec
            else:
                rec = self._make_record(
                    t, axis, "HOLD",
                    f"{axis_label} queue empty for {empty_duration:.1f}s (< gap-out persistence {c.gap_out_s:.1f}s); holding green for clearance.",
                    "HOLD_CLEARING", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="GAP_OUT", applied_action="HOLD", decision_outcome="HOLD_CLEARING"
                )
                if record_decisions:
                    self.last_decision_record = rec
                return False, rec
        else:
            if record_decisions:
                self._empty_since = None

        # 4. Within Approved Target Green Duration
        if elapsed < self.target_green_s:
            rec = self._make_record(
                t, axis, "HOLD",
                f"{axis_label} green servicing within approved target ({self.target_green_s:.1f}s = baseline {self.baseline_green_s[axis]:.1f}s + extra {self.accumulated_extra_s:.1f}s); elapsed: {elapsed:.1f}s.",
                "HOLD_SERVICING", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="HOLD", applied_action="HOLD", decision_outcome="HOLD_SERVICING"
            )
            if record_decisions:
                self.last_decision_record = rec
            return False, rec

        # 5. Target Reached: If R-ext is disabled, switch immediately at g_base
        if not self.r_ext:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"{axis_label} target green ({self.target_green_s:.1f}s) completed with queue extensions disabled (R-ext OFF); enforcing phase switch.",
                "SWITCH_DEMAND_EXHAUSTED", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="REQUEST_SWITCH", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_DEMAND_EXHAUSTED"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        # 5. Target Reached with Extensions Enabled: Evaluate Increment
        req_increment = c.extend_step_s
        headroom = max(0.0, c.max_green_s - self.target_green_s)

        # 5a. Check Headroom to Max Green
        if headroom <= 0.0:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: {axis_label} target green ({self.target_green_s:.1f}s) has reached maximum ceiling ({c.max_green_s:.1f}s). Enforcing mandatory switch.",
                "SWITCH_CEILING_REACHED", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, True,
                proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_CEILING_REACHED"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        # 5b. Anti-Monopoly / Fairness Wait Check (R-guard)
        if self.r_guard:
            if comp_q >= c.min_competing_queue_m and competing_red_elapsed >= c.max_competing_wait_s:
                rec = self._make_record(
                    t, axis, "REQUEST_SWITCH",
                    f"Extension rejected: Competing {comp_label} red wait ({competing_red_elapsed:.1f}s) >= maximum allowed wait ({c.max_competing_wait_s:.1f}s) with waiting queue ({comp_q:.1f}m). Triggering fair phase switch.",
                    "SWITCH_FAIRNESS_WAIT_LIMIT", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_FAIRNESS_WAIT_LIMIT"
                )
                if record_decisions:
                    self.last_decision_record = rec
                    self.decisions.append(rec)
                return True, rec

        # 5c. Demand Imbalance Check
        if comp_q >= c.min_competing_queue_m and score_competing > (score_active * c.fairness_ratio):
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Competing {comp_label} demand score ({score_competing:.1f}) exceeds active {axis_label} score ({score_active:.1f}) by fairness ratio ({c.fairness_ratio}). Switching to relieve opposing corridor.",
                "SWITCH_DEMAND_FAIRNESS", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_DEMAND_FAIRNESS"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        # 5d. Queue Extension Evaluation (R-ext threshold check)
        if own_q < c.extend_threshold_m and delta_q < c.arrival_detection_threshold:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Active {axis_label} queue ({own_q:.1f}m < threshold {c.extend_threshold_m:.1f}m) and no new arrivals detected (delta Q = {delta_q:.1f}m). Terminating green phase.",
                "SWITCH_DEMAND_EXHAUSTED", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_DEMAND_EXHAUSTED"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        app_increment = min(req_increment, headroom)
        if record_decisions:
            self.accumulated_extra_s += app_increment
            self.target_green_s += app_increment
            self.extensions_granted += 1

        explanation = (
            f"Queue extension approved: Active {axis_label} queue ({own_q:.1f}m >= {c.extend_threshold_m:.1f}m) "
            f"or arrival pulse ({delta_q:.1f}m); extending green by {app_increment:.0f}s "
            f"(target: {self.target_green_s:.1f}s, headroom: {headroom - app_increment:.1f}s)."
        )
        rec = self._make_record(
            t, axis, "EXTEND", explanation,
            "EXTEND_APPROVED", req_increment, app_increment, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
            proposed_action="EXTEND", applied_action="EXTEND", decision_outcome="EXTEND_APPROVED"
        )
        if record_decisions:
            self.last_decision_record = rec
            self.decisions.append(rec)
        return False, rec
