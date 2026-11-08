"""Improved Hybrid Queue-Adaptive traffic signal controller v2 for DP1.

Maintains all v1 safety invariants:
- Minimum green floor: 10.0 s
- Maximum green ceiling: 60.0 s
- Yellow transition: 3.0 s
- All-red clearance: 2.0 s
- Clearance order: GREEN -> YELLOW -> ALL_RED -> GREEN(other axis)

Extends v1 with modular candidate improvements:
- (a) rest_in_green: Prevents switching away from active phase when competing approach has zero detected demand; switches as soon as competing demand appears.
- (b) unconditional_wait_cap: Strictly forces switch at 35 s red wait whether or not competing queue is detected.
- (c) pressure_extension: Extends only when active queue minus competing queue exceeds threshold.
- (d) rest_in_green + unconditional_wait_cap combined.
"""
from typing import Dict, Any, Optional, Tuple
from .hybrid_queue_adaptive import HybridQueueAdaptiveController
from .. import config as C


class HybridQueueAdaptiveV2Controller(HybridQueueAdaptiveController):
    """Hybrid Queue-Adaptive Signal Controller v2."""

    name = "hybrid_queue_adaptive_v2"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "marathahalli",
        cfg: Optional[C.HybridQueueAdaptiveV2Config] = None,
        plan: Optional[C.FixedTimeConfig] = None,
        **kw,
    ):
        v2_cfg = cfg or C.HYBRID_QUEUE_ADAPTIVE_V2
        super().__init__(
            states,
            scenario=scenario,
            demand_level=demand_level,
            network=network,
            cfg=v2_cfg,
            plan=plan,
            **kw,
        )
        self.cfg: C.HybridQueueAdaptiveV2Config = v2_cfg

    def _evaluate_rules(
        self,
        axis: str,
        elapsed: float,
        cleaned_q: Dict[str, float],
        t: float,
        record_decisions: bool = True,
        raw_queues: Optional[Dict[str, float]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate v2 signal state machine decision rules."""
        c = self.cfg
        other_axis = C.OTHER_AXIS[axis]
        logged_q = raw_queues or cleaned_q

        own_q = self.axis_queue(axis, cleaned_q)
        comp_q = self.axis_queue(other_axis, cleaned_q)
        competing_red_elapsed = max(0.0, t - self.red_start_times.get(other_axis, 0.0))

        # Dynamic arrival detection
        prev_own = self._prev_queues.get(axis, own_q)
        delta_q = max(0.0, own_q - prev_own)
        prev_comp = self._prev_queues.get(other_axis, comp_q)
        comp_delta_q = max(0.0, comp_q - prev_comp)

        if record_decisions:
            self._prev_queues[axis] = own_q
            self._prev_queues[other_axis] = comp_q

        # Demand scores
        score_active = own_q + 0.5 * delta_q
        wait_factor = 1.0 + (competing_red_elapsed / max(1.0, c.max_competing_wait_s))
        score_competing = comp_q * wait_factor

        axis_label = "North–South" if axis == "NS" else "East–West"
        comp_label = "East–West" if axis == "NS" else "North–South"

        # 1. Hard Minimum Green Floor Enforcement (Safety Invariant)
        if elapsed < c.min_green_s:
            rec = self._make_record(
                t, axis, "HOLD",
                f"{axis_label} elapsed green ({elapsed:.1f}s) < minimum green floor ({c.min_green_s:.1f}s); switch prohibited by safety invariant.",
                "HOLD_MIN_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="HOLD", applied_action="HOLD", decision_outcome="HOLD_MIN_GREEN"
            )
            if record_decisions:
                self.last_decision_record = rec
            return False, rec

        # 2. Hard Maximum Green Ceiling Enforcement (Safety Invariant)
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

        # 2b. Unconditional Red-Wait Cap (Candidate b and d)
        if getattr(c, "unconditional_wait_cap", False) and competing_red_elapsed >= c.max_competing_wait_s:
            rec = self._make_record(
                t, axis, "REQUEST_SWITCH",
                f"Extension rejected: Competing {comp_label} red wait ({competing_red_elapsed:.1f}s) >= unconditional anti-starvation cap ({c.max_competing_wait_s:.1f}s). Forcing fair switch.",
                "SWITCH_FAIRNESS_HARD_CAP", c.extend_step_s, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                proposed_action="REQUEST_SWITCH", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_FAIRNESS_HARD_CAP"
            )
            if record_decisions:
                self.last_decision_record = rec
                self.decisions.append(rec)
            return True, rec

        # 3. Gap-Out Evaluation: Active approach fully cleared
        comp_has_demand = (comp_q >= c.min_competing_queue_m or comp_delta_q >= c.arrival_detection_threshold)

        if own_q <= 0.0 and comp_q >= c.min_competing_queue_m:
            if getattr(c, "rest_in_green", False) and elapsed >= self.target_green_s:
                # Active approach already completed target green; switch immediately upon competing demand appearance
                rec = self._make_record(
                    t, axis, "GAP_OUT",
                    f"{axis_label} queue cleared while competing {comp_label} has demand ({comp_q:.1f}m); switching phase immediately.",
                    "SWITCH_GAP_OUT", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="GAP_OUT", applied_action="GAP_OUT", decision_outcome="SWITCH_GAP_OUT"
                )
                if record_decisions:
                    self.last_decision_record = rec
                    self.decisions.append(rec)
                return True, rec

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

        # 5. Target Reached: Evaluate Bounded Extension Increment
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

        # 5b. Anti-Monopoly / Fairness Wait Check
        if getattr(c, "unconditional_wait_cap", False):
            if competing_red_elapsed >= c.max_competing_wait_s:
                rec = self._make_record(
                    t, axis, "REQUEST_SWITCH",
                    f"Extension rejected: Competing {comp_label} red wait ({competing_red_elapsed:.1f}s) >= unconditional anti-starvation cap ({c.max_competing_wait_s:.1f}s). Forcing fair switch.",
                    "SWITCH_FAIRNESS_HARD_CAP", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_FAIRNESS_HARD_CAP"
                )
                if record_decisions:
                    self.last_decision_record = rec
                    self.decisions.append(rec)
                return True, rec
        elif comp_q >= c.min_competing_queue_m and competing_red_elapsed >= c.max_competing_wait_s:
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

        # 5d. Extension Justification / Rest-in-Green / Pressure Check
        if own_q < c.extend_threshold_m and delta_q < c.arrival_detection_threshold:
            # Active demand exhausted
            if getattr(c, "rest_in_green", False) and not comp_has_demand:
                # Rest-in-green: no switch if opposing approach has zero demand
                rec = self._make_record(
                    t, axis, "HOLD",
                    f"{axis_label} demand exhausted but competing {comp_label} has no detected demand (queue {comp_q:.1f}m < {c.min_competing_queue_m:.1f}m); resting in green.",
                    "HOLD_REST_IN_GREEN", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="HOLD", applied_action="HOLD", decision_outcome="HOLD_REST_IN_GREEN"
                )
                if record_decisions:
                    self.last_decision_record = rec
                return False, rec

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

        # Active demand present: evaluate extension
        if getattr(c, "pressure_extension", False):
            pressure = own_q - comp_q
            thresh = getattr(c, "pressure_threshold_m", 0.0)
            if pressure <= thresh:
                rec = self._make_record(
                    t, axis, "REQUEST_SWITCH",
                    f"Pressure extension rejected: Active {axis_label} queue ({own_q:.1f}m) minus competing {comp_label} queue ({comp_q:.1f}m) = {pressure:.1f}m <= threshold ({thresh:.1f}m). Switching phase.",
                    "SWITCH_PRESSURE_DEFICIT", req_increment, 0.0, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
                    proposed_action="EXTEND", applied_action="REQUEST_SWITCH", decision_outcome="SWITCH_PRESSURE_DEFICIT"
                )
                if record_decisions:
                    self.last_decision_record = rec
                    self.decisions.append(rec)
                return True, rec

        # Approved extension
        app_increment = min(req_increment, headroom)
        if record_decisions:
            self.accumulated_extra_s += app_increment
            self.target_green_s += app_increment
            self.extensions_granted += 1

        explanation = (
            f"{axis_label} green extended by {app_increment:.0f} seconds: "
            f"its queue/demand condition ({own_q:.1f}m >= {c.extend_threshold_m:.1f}m) satisfied the configured extension rule, "
            f"the competing-direction wait ({competing_red_elapsed:.1f}s) remained within its permitted limit ({c.max_competing_wait_s:.0f}s), "
            f"and maximum green was not reached."
        )

        outcome = "EXTEND_PRESSURE" if getattr(c, "pressure_extension", False) else "EXTEND_APPROVED"
        rec = self._make_record(
            t, axis, "EXTEND",
            explanation,
            outcome, req_increment, app_increment, elapsed, own_q, comp_q, score_active, score_competing, logged_q, False,
            proposed_action="EXTEND", applied_action="EXTEND", decision_outcome=outcome
        )
        if record_decisions:
            self.last_decision_record = rec
            self.decisions.append(rec)
        return False, rec


class HybridV2CandAController(HybridQueueAdaptiveV2Controller):
    """Candidate (a): Rest-in-green."""
    name = "hybrid_v2_cand_a"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_V2_CAND_A, **kw)


class HybridV2CandBController(HybridQueueAdaptiveV2Controller):
    """Candidate (b): Unconditional red-wait cap."""
    name = "hybrid_v2_cand_b"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_V2_CAND_B, **kw)


class HybridV2CandCController(HybridQueueAdaptiveV2Controller):
    """Candidate (c): Pressure-based extension."""
    name = "hybrid_v2_cand_c"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_V2_CAND_C, **kw)


class HybridV2CandDController(HybridQueueAdaptiveV2Controller):
    """Candidate (d): Rest-in-green + Unconditional red-wait cap."""
    name = "hybrid_v2_cand_d"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_V2_CAND_D, **kw)
