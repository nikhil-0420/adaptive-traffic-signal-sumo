from .base import PhaseMachineController, ControllerAction
from .fixed_time import FixedTimeController
from .fixed_webster import FixedWebsterController
from .adaptive_queue import AdaptiveQueueController
from .adaptive_pressure import AdaptivePressureController
from .rl_dqn import RLDQNController

POLICIES = {
    "fixed": FixedTimeController,
    "fixed_webster": FixedWebsterController,
    "adaptive": AdaptiveQueueController,
    "pressure": AdaptivePressureController,
    "rl_dqn": RLDQNController,
}

