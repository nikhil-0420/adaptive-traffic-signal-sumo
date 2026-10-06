from .fixed_time import FixedTimeController
from .fixed_webster import FixedWebsterController
from .adaptive_queue import AdaptiveQueueController

POLICIES = {
    "fixed": FixedTimeController,
    "fixed_webster": FixedWebsterController,
    "adaptive": AdaptiveQueueController,
}

