"""[ORACLE-SEEDED] Hybrid Queue-Adaptive traffic signal controller.

LEGACY REFERENCE POLICY:
Seeds baseline green allocation (G_base) directly from the true offline mathematical
scenario demand table (SITE_DEMAND_PATTERNS / site_webster_plan) and demand level,
giving the controller oracle knowledge of future scenario demand.
This policy is preserved strictly for backward compatibility and ablation reference.
"""
from typing import Optional
from .hybrid_queue_adaptive import HybridQueueAdaptiveController
from ..site_scenarios import site_webster_plan
from .. import config as C


class HybridOracleSeededController(HybridQueueAdaptiveController):
    """[ORACLE-SEEDED] Legacy Hybrid controller with oracle-seeded baseline plan."""

    name = "hybrid_oracle_seeded"

    def __init__(
        self,
        states,
        scenario: str = "balanced",
        demand_level: str = C.DEFAULT_DEMAND_LEVEL,
        network: str = "marathahalli",
        cfg: Optional[C.HybridQueueAdaptiveConfig] = None,
        **kw,
    ):
        net = network.lower().strip()
        if net == "marathahalli" or scenario in ("imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
            oracle_plan = site_webster_plan(scenario, demand_level=demand_level)
        else:
            oracle_plan = C.webster_plan(scenario, demand_level=demand_level)

        oracle_cfg = cfg or C.HYBRID_ORACLE_SEEDED
        super().__init__(
            states,
            scenario=scenario,
            demand_level=demand_level,
            network=network,
            cfg=oracle_cfg,
            plan=oracle_plan,
            **kw,
        )
