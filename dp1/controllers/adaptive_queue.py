from .base import PhaseMachineController
from .. import config as C


class AdaptiveQueueController(PhaseMachineController):
    """Queue-driven green allocation (DP1 core).

    1. Sensors give queue length (m) per approach.
    2. The axis about to get green is sized from its own longest queue:
           green = clamp(min_green + k * queue_m, min_green, max_green)
       so a heavy approach gets extra green and, as a consequence, the other axis waits longer.
    3. During green: keep extending while the queue is still long (up to max_green);
       end early (gap-out) if the queue is empty and the other axis is waiting.
    4. Switching always goes yellow -> all-red (enforced by the base state machine).
    """
    name = "adaptive"

    def __init__(self, states, cfg=C.ADAPTIVE, **kw):
        super().__init__(states, **kw)
        self.cfg = cfg
        self._empty_since = None

    @staticmethod
    def axis_queue(axis, queues):
        return max(queues[a] for a in C.AXES[axis])

    def decide_green(self, axis, queues, t):
        q = self.axis_queue(axis, queues)
        c = self.cfg
        self._empty_since = None
        return max(c.min_green_s, min(c.max_green_s, c.min_green_s + c.k_s_per_m * q))

    def green_should_end(self, axis, elapsed, queues, t):
        c = self.cfg
        own = self.axis_queue(axis, queues)
        other = self.axis_queue(C.OTHER_AXIS[axis], queues)
        if elapsed >= c.max_green_s:
            return True
        # keep extending while the queue on the green axis is still long
        if elapsed >= self.target_green and own > c.extend_threshold_m:
            return False
        if elapsed < c.min_green_s:
            return False
        # gap-out: own queue cleared and the other axis is actually waiting
        if own <= 0.0 and other >= c.min_competing_queue_m:
            if self._empty_since is None:
                self._empty_since = t
            if t - self._empty_since >= c.gap_out_s:
                return True
        else:
            self._empty_since = None
        return elapsed >= self.target_green
