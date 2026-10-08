"""Max-pressure signal controller: sizes green from queue differential between axes."""
from .adaptive_queue import AdaptiveQueueController
from .. import config as C


class AdaptivePressureController(AdaptiveQueueController):
    """Pressure-based green allocation.

    1. Sensors measure queue length (m) per approach.
    2. Green duration for the axis about to turn green is sized from the
       queue DIFFERENCE between that axis and the competing axis:
           diff = max(0.0, own_queue - competing_queue)
           green = clamp(min_green + k * diff, min_green, max_green)
       If the competing axis has equal or longer queue (diff <= 0), this axis receives min_green.
    3. Switching enforces the invariant Green -> Yellow -> All-Red.
    4. Gap-out and green extension logic remain identical to adaptive.
    """
    name = "pressure"

    def __init__(self, states, cfg=C.PRESSURE, **kw):
        super().__init__(states, cfg=cfg, **kw)

    def decide_green(self, axis, queues, t):
        own = self.axis_queue(axis, queues)
        other = self.axis_queue(C.OTHER_AXIS[axis], queues)
        diff = max(0.0, own - other)
        c = self.cfg
        self._empty_since = None
        return max(c.min_green_s, min(c.max_green_s, c.min_green_s + c.k_s_per_m * diff))
