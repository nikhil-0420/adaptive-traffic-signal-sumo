from .fixed_time import FixedTimeController
from .adaptive_queue import AdaptiveQueueController

POLICIES = {
    "fixed": FixedTimeController,
    "adaptive": AdaptiveQueueController,
}
