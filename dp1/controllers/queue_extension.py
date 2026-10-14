"""Bounded Queue-Extension traffic signal controller (Upgrade 1).

Dynamically extends green-light duration in response to active approach queues
and recent arrivals while enforcing anti-monopoly fairness bounds to prevent starving
competing traffic.
"""
from .base import PhaseMachineController
from .. import config as C


class QueueExtensionController(PhaseMachineController):
    """Queue-extension controller with anti-monopoly fairness bounding.

    Algorithm:
    1. Initial Phase Green: Upon entering GREEN, assigns an initial baseline green
       duration `initial_green_s` based on initial queue length.
    2. Inputs Observed:
       - Active queue length: maximum queue length across active approaches.
       - Competing queue length: maximum queue length across competing approaches.
       - Competing waiting time: seconds elapsed since the competing axis entered RED.
       - Recent arrivals: dynamic queue increment Delta_Q = Q(t) - Q(t-1) detecting
         newly arriving vehicles during green service.
    3. Extension Evaluation: When elapsed green reaches target green, inspects the
       active approach queue and recent arrivals. If active queue exceeds `extend_threshold_m`
       or incoming arrivals are detected, an extension increment of `extend_step_s` is
       granted, bounded by `max_green_s`.
    4. Anti-Monopoly & Fairness Termination:
       - Competing axis wait time: Tracks when competing axis was last served. If
         competing red wait exceeds `max_competing_wait_s` and competing traffic is
         present (`>= min_competing_queue_m`), green extension is denied and switch
         is triggered.
       - Dynamic Pressure Ratio: If competing queue accumulation
         (competing_queue * elapsed / min_green) exceeds active queue by `fairness_ratio`,
         switch is triggered to prevent monopolizing the intersection.
    5. Gap-Out: If active queue drops to zero while competing traffic is waiting,
       ends green early after `gap_out_s` seconds of persistent vacancy.
    6. Invariants: Strict transition sequence (GREEN -> YELLOW -> ALL_RED -> GREEN)
       and bounds [min_green_s, max_green_s] are strictly preserved.
    """
    name = "queue_extension"

    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, **kw)
        self.cfg = cfg or C.QUEUE_EXTENSION
        self._empty_since = None
        self._extensions_granted = 0
        self.red_start_times = {"NS": 0.0, "EW": 0.0}
        self._prev_queues = {"NS": 0.0, "EW": 0.0}

    @staticmethod
    def axis_queue(axis, queues):
        return max(queues[a] for a in C.AXES[axis])

    def decide_green(self, axis, queues, t):
        c = self.cfg
        self._empty_since = None
        self._extensions_granted = 0
        other_axis = C.OTHER_AXIS[axis]
        self.red_start_times[other_axis] = t

        # Initial baseline green
        own = self.axis_queue(axis, queues)
        self._prev_queues[axis] = own
        self._prev_queues[other_axis] = self.axis_queue(other_axis, queues)
        initial = max(c.min_green_s, min(c.initial_green_s, c.min_green_s + 0.15 * own))
        return initial

    def green_should_end(self, axis, elapsed, queues, t):
        c = self.cfg
        own = self.axis_queue(axis, queues)
        other_axis = C.OTHER_AXIS[axis]
        competing = self.axis_queue(other_axis, queues)
        competing_red_elapsed = t - self.red_start_times.get(other_axis, 0.0)

        # Dynamic arrival detection: check queue growth indicating incoming arrivals
        prev_own = self._prev_queues.get(axis, own)
        delta_q = own - prev_own
        recent_arrivals = max(0.0, delta_q)
        self._prev_queues[axis] = own
        self._prev_queues[other_axis] = competing

        # 1. Hard minimum green enforcement
        if elapsed < c.min_green_s:
            return False

        # 2. Hard maximum green enforcement
        if elapsed >= c.max_green_s:
            return True

        # 3. Gap-out termination: active approach cleared and competing axis waiting
        if own <= 0.0 and competing >= c.min_competing_queue_m:
            if self._empty_since is None:
                self._empty_since = t
            if t - self._empty_since >= c.gap_out_s:
                return True
        else:
            self._empty_since = None

        # 4. Anti-monopoly fairness checks (only apply if competing axis has waiting queue)
        if competing >= c.min_competing_queue_m:
            # Check maximum allowable red delay for competing axis
            if competing_red_elapsed >= c.max_competing_wait_s:
                return True

            # Dynamic fairness ratio: if competing queue accumulation exceeds active queue
            if elapsed >= self.target_green:
                competing_pressure = competing * (elapsed / c.min_green_s)
                if competing_pressure > (own * c.fairness_ratio):
                    return True

        # 5. Extension evaluation when reaching currently scheduled green
        if elapsed >= self.target_green:
            has_demand = (own > c.extend_threshold_m) or (recent_arrivals > 0.0 and own > 0.0)
            if has_demand and (self.target_green + c.extend_step_s <= c.max_green_s):
                # Grant green extension increment
                self.target_green += c.extend_step_s
                self._extensions_granted += 1
                return False
            else:
                return True

        return False
