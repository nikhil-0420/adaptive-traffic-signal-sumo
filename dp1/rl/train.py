"""Training routine for DQN agent on SumoIntersectionEnv with companion metadata saving."""
import json
from pathlib import Path
import sys
import time
from typing import Optional, Tuple

from .. import config as C
from .env import SumoIntersectionEnv
from .obs import OBS_DIM, OBS_SCHEMA_VERSION, OBS_FEATURE_NAMES


def train_dqn(
    scenario: str = "imbalanced_ns",
    seed: int = 1,
    timesteps: int = 1000,
    out_path: Optional[Path] = None,
    learning_rate: Optional[float] = None,
    cfg: Optional[C.RLConfig] = None,
    verbose: int = 0,
) -> Tuple[Path, Path]:
    """Train a DQN agent on SumoIntersectionEnv and save model checkpoint + metadata.

    Args:
        scenario: traffic demand scenario pattern.
        seed: random seed for reproducibility.
        timesteps: total training steps (seconds of simulation).
        out_path: target path for model .zip file.
        learning_rate: optimizer learning rate.
        cfg: RLConfig instance.
        verbose: Stable-Baselines3 verbosity level (0 = silent).

    Returns:
        Tuple[Path, Path]: (model_path, metadata_path)
    """
    try:
        import gymnasium
        import stable_baselines3
        from stable_baselines3 import DQN
        import torch
    except ImportError as exc:
        raise ImportError(
            "Reinforcement learning dependencies (gymnasium, stable-baselines3, torch) are missing. "
            "Install requirements-rl.txt: pip install -r requirements-rl.txt"
        ) from exc

    cfg = cfg or C.RL
    lr = learning_rate or cfg.learning_rate

    # Resolve output path
    if out_path is None:
        target_path = cfg.models_dir / f"{cfg.default_model_name}.zip"
    else:
        target_path = Path(out_path)
        if target_path.suffix != ".zip":
            target_path = target_path.with_suffix(".zip")

    target_path.parent.mkdir(parents=True, exist_ok=True)

    env = SumoIntersectionEnv(scenario=scenario, seed=seed, cfg=cfg)

    # Use hyperparameter bounds appropriate for small/smoke training runs
    buffer_sz = min(cfg.buffer_size, max(timesteps * 2, 500))
    learn_starts = min(cfg.learning_starts, max(10, timesteps // 10))
    batch_sz = min(cfg.batch_size, 32)
    target_update = min(cfg.target_update_interval, max(20, timesteps // 5))

    model = DQN(
        "MlpPolicy",
        env,
        learning_rate=lr,
        buffer_size=buffer_sz,
        learning_starts=learn_starts,
        batch_size=batch_sz,
        gamma=cfg.gamma,
        train_freq=cfg.train_freq,
        gradient_steps=cfg.gradient_steps,
        target_update_interval=target_update,
        exploration_initial_eps=cfg.exploration_initial_eps,
        exploration_final_eps=cfg.exploration_final_eps,
        exploration_fraction=cfg.exploration_fraction,
        seed=seed,
        verbose=verbose,
    )

    try:
        model.learn(total_timesteps=timesteps)
    finally:
        env.close()

    # Save model checkpoint
    model.save(str(target_path))

    # Save comprehensive metadata alongside checkpoint
    run_id = f"dqn_{scenario}_s{seed}_{int(time.time())}"
    meta_path = target_path.with_name(f"{target_path.stem}.metadata.json")
    metadata = {
        "run_id": run_id,
        "algorithm": "DQN",
        "framework": "stable-baselines3",
        "scenario": scenario,
        "seed": seed,
        "timesteps": timesteps,
        "obs_dim": OBS_DIM,
        "obs_schema_version": OBS_SCHEMA_VERSION,
        "obs_features": OBS_FEATURE_NAMES,
        "action_mapping": {
            "0": "HOLD",
            "1": "REQUEST_SWITCH",
        },
        "bounds": {
            "min_green_s": cfg.min_green_s,
            "max_green_s": cfg.max_green_s,
            "max_detector_m": cfg.max_detector_m,
        },
        "hyperparameters": {
            "learning_rate": lr,
            "buffer_size": buffer_sz,
            "learning_starts": learn_starts,
            "batch_size": batch_sz,
            "gamma": cfg.gamma,
            "train_freq": cfg.train_freq,
            "gradient_steps": cfg.gradient_steps,
            "target_update_interval": target_update,
            "exploration_fraction": cfg.exploration_fraction,
        },
        "seed_splits": {
            "train_seeds": list(cfg.train_seeds),
            "validation_seeds": list(cfg.validation_seeds),
            "eval_seeds": list(cfg.eval_seeds),
            "research_seeds": list(cfg.research_seeds),
        },
        "package_versions": {
            "python": sys.version,
            "gymnasium": getattr(gymnasium, "__version__", "unknown"),
            "stable_baselines3": getattr(stable_baselines3, "__version__", "unknown"),
            "torch": getattr(torch, "__version__", "unknown"),
        },
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return target_path, meta_path
