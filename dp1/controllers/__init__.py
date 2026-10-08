from .fixed_time import FixedTimeController
from .fixed_webster import FixedWebsterController
from .adaptive_queue import AdaptiveQueueController
from .adaptive_pressure import AdaptivePressureController

POLICIES = {
    "fixed": FixedTimeController,
    "fixed_webster": FixedWebsterController,
    "adaptive": AdaptiveQueueController,
    "pressure": AdaptivePressureController,
}

