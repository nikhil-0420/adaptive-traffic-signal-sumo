"""Reinforcement Learning DQN inference controller using action seam."""
import json
from pathlib import Path
from typing import Optional

from .. import config as C
from .base import PhaseMachineController
from ..rl.obs import build_observation, OBS_DIM, OBS_SCHEMA_VERSION


class RLDQNController(PhaseMachineController):
    """Inference controller for trained DQN policies.

    Observes current traffic queues and signal state, then selects a discrete action
    (HOLD = 0 or REQUEST_SWITCH = 1) on each simulation second during GREEN.
    Signal safety transitions (GREEN -> YELLOW -> ALL_RED -> GREEN) and bounds
    (min_green_s = 10s, max_green_s = 60s) are guaranteed by PhaseMachineController.
    """
    name = "rl_dqn"

    def __init__(
        self,
        states,
        model_path: Optional[str] = None,
        cfg: Optional[C.RLConfig] = None,
        **kwargs,
    ):
        self.rl_cfg = cfg or C.RL
        min_g = kwargs.pop("min_green_s", self.rl_cfg.min_green_s)
        max_g = kwargs.pop("max_green_s", self.rl_cfg.max_green_s)
        super().__init__(states, min_green_s=min_g, max_green_s=max_g, **kwargs)

        # 1. Actionable check for optional RL dependencies
        try:
            from stable_baselines3 import DQN
        except ImportError as exc:
            raise ImportError(
                "stable-baselines3 is required to use the 'rl_dqn' controller. "
                "Install requirements-rl.txt: pip install -r requirements-rl.txt"
            ) from exc

        # 2. Resolve model path
        if model_path is None:
            resolved_path = self.rl_cfg.models_dir / f"{self.rl_cfg.default_model_name}.zip"
        else:
            resolved_path = Path(model_path)
            if not resolved_path.exists() and resolved_path.with_suffix(".zip").exists():
                resolved_path = resolved_path.with_suffix(".zip")

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Trained RL model not found at '{resolved_path}'. "
                f"Please train a model using 'python -m dp1.cli train-rl' or pass a valid --model-path."
            )

        # 3. Validate metadata schema if companion file exists
        meta_path = resolved_path.with_name(f"{resolved_path.stem}.metadata.json")
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta_obs_dim = meta.get("obs_dim")
                if meta_obs_dim is not None and meta_obs_dim != OBS_DIM:
                    raise ValueError(
                        f"Observation schema dimension mismatch in '{meta_path}': "
                        f"model expects obs_dim={meta_obs_dim}, but current schema is {OBS_DIM}."
                    )
            except (json.JSONDecodeError, OSError) as e:
                # If metadata exists but is corrupted, raise error
                if isinstance(e, json.JSONDecodeError):
                    raise ValueError(f"Corrupt metadata file '{meta_path}': {e}") from e

        # 4. Load DQN model for inference
        self.model_path = resolved_path
        self.model = DQN.load(str(resolved_path))

    def decide_green(self, axis: str, queues: dict, t: float) -> float:
        """Nominal target green for RL controller (bounded by max_green)."""
        return self.get_max_green_s()

    def decide_action(self, axis: str, elapsed: float, queues: dict, t: float) -> Optional[int]:
        """Produce discrete action via DQN policy during GREEN.

        Returns ControllerAction.HOLD (0) or ControllerAction.REQUEST_SWITCH (1).
        Outside GREEN (handled by base machine), returns None.
        """
        if self.phase != "GREEN":
            return None

        obs = build_observation(
            queues=queues,
            axis=self.axis,
            phase=self.phase,
            elapsed_green_s=elapsed,
            t_s=t,
            max_detector_m=self.rl_cfg.max_detector_m,
            max_green_s=self.get_max_green_s(),
            demand_duration_s=float(C.SIM.demand_duration_s),
        )

        action, _ = self.model.predict(obs, deterministic=True)
        return int(action)
