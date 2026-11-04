from .base import PhaseMachineController, ControllerAction
from .fixed_time import FixedTimeController
from .fixed_webster import FixedWebsterController, WebsterOracleController
from .adaptive_queue import AdaptiveQueueController
from .adaptive_pressure import AdaptivePressureController
from .queue_extension import QueueExtensionController
from .rl_dqn import RLDQNController
from .hybrid_queue_adaptive import HybridQueueAdaptiveController
from .hybrid_oracle_seeded import HybridOracleSeededController
from .webster_measured import WebsterMeasuredController
from .webster_recalc import WebsterRecalcController
from .fixed_matched_cycle import FixedMatchedCycleController
from .sumo_actuated import SumoActuatedController
from .. import config as C


class HybridR2Controller(HybridQueueAdaptiveController):
    """Hybrid controller with R2: Comparative extension."""
    name = "hybrid_r2"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_R2, **kw)


class HybridR2R3Controller(HybridQueueAdaptiveController):
    """Hybrid controller with R2 (Comparative extension) + R3 (Queue-aware fairness)."""
    name = "hybrid_r2_r3"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_R2_R3, **kw)


class HybridR2R3R4Controller(HybridQueueAdaptiveController):
    """Hybrid controller with R2 + R3 + R4 (Measured Webster base green)."""
    name = "hybrid_r2_r3_r4"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_R2_R3_R4, **kw)


class HybridR3Controller(HybridQueueAdaptiveController):
    """Hybrid controller with R3: New default (R4) + R3 Queue-aware fairness."""
    name = "hybrid_r3"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_R3, **kw)


class HybridR4Controller(HybridQueueAdaptiveController):
    """Hybrid controller with R4 only (Measured Webster base green, identical to new default)."""
    name = "hybrid_r4"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_R4, **kw)


class HybridQueueAdaptiveProjController(HybridQueueAdaptiveController):
    """Hybrid controller with R4 + Short-Horizon Queue Projection (winning Phase 12 policy)."""
    name = "hybrid_queue_adaptive_proj"
    def __init__(self, states, cfg=None, **kw):
        super().__init__(states, cfg=cfg or C.HYBRID_QUEUE_ADAPTIVE_PROJ, **kw)


POLICIES = {
    "fixed": FixedTimeController,
    "fixed_webster": FixedWebsterController,
    "adaptive": AdaptiveQueueController,
    "pressure": AdaptivePressureController,
    "queue_extension": QueueExtensionController,
    "rl_dqn": RLDQNController,
    "hybrid_queue_adaptive": HybridQueueAdaptiveController,
    "hybrid_queue_adaptive_proj": HybridQueueAdaptiveProjController,
    "hybrid_oracle_seeded": HybridOracleSeededController,
    "hybrid_r2": HybridR2Controller,
    "hybrid_r3": HybridR3Controller,
    "hybrid_r4": HybridR4Controller,
    "hybrid_r2_r3": HybridR2R3Controller,
    "hybrid_r2_r3_r4": HybridR2R3R4Controller,
    "webster_measured": WebsterMeasuredController,
    "webster_recalc": WebsterRecalcController,
    "fixed_matched_cycle": FixedMatchedCycleController,
    "sumo_actuated": SumoActuatedController,
    "webster_oracle": WebsterOracleController,
}

