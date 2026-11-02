from .base import PhaseMachineController, ControllerAction
from .fixed_time import FixedTimeController
from .fixed_webster import FixedWebsterController, WebsterOracleController
from .adaptive_queue import AdaptiveQueueController
from .adaptive_pressure import AdaptivePressureController
from .queue_extension import QueueExtensionController
from .rl_dqn import RLDQNController
from .hybrid_queue_adaptive import HybridQueueAdaptiveController
from .webster_measured import WebsterMeasuredController
from .webster_recalc import WebsterRecalcController
from .fixed_matched_cycle import FixedMatchedCycleController
from .sumo_actuated import SumoActuatedController

POLICIES = {
    "fixed": FixedTimeController,
    "fixed_webster": FixedWebsterController,
    "adaptive": AdaptiveQueueController,
    "pressure": AdaptivePressureController,
    "queue_extension": QueueExtensionController,
    "rl_dqn": RLDQNController,
    "hybrid_queue_adaptive": HybridQueueAdaptiveController,
    "webster_measured": WebsterMeasuredController,
    "webster_recalc": WebsterRecalcController,
    "fixed_matched_cycle": FixedMatchedCycleController,
    "sumo_actuated": SumoActuatedController,
    "webster_oracle": WebsterOracleController,
}
