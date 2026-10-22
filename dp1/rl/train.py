"""Training routine for DQN agent on SumoIntersectionEnv with companion metadata saving."""
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from .. import config as C
from .env import SumoIntersectionEnv
from .obs import OBS_DIM, OBS_SCHEMA_VERSION, OBS_FEATURE_NAMES


def train_dqn(
    scenario: Optional[str] = None,
    seed: Optional[int] = None,
    timesteps: int = 1000,
    out_path: Optional[Path] = None,
    learning_rate: Optional[float] = None,
    cfg: Optional[C.RLConfig] = None,
    verbose: int = 0,
    rotate_seeds: bool = True,
    eval_freq: Optional[int] = None,
    val_seeds: Optional[tuple] = None,
    network: str = "synthetic",
    train_seeds: Optional[tuple] = None,
) -> Tuple[Path, Path]:
    """Train a DQN agent on SumoIntersectionEnv and save model checkpoint + metadata.

    Args:
        scenario: traffic demand scenario pattern or "all".
        seed: initial random seed for reproducibility.
        timesteps: total training steps (seconds of simulation).
        out_path: target path for model .zip file.
        learning_rate: optimizer learning rate.
        cfg: RLConfig instance.
        verbose: Stable-Baselines3 verbosity level (0 = silent).
        rotate_seeds: whether to rotate through train_seeds on episode resets.
        eval_freq: step frequency for validation evaluation and checkpointing.
        val_seeds: validation seeds for model selection.
        network: 'synthetic' or 'marathahalli'.
        train_seeds: training seed list.

    Returns:
        Tuple[Path, Path]: (model_path, metadata_path)
    """
    try:
        import gymnasium
        import stable_baselines3
        from stable_baselines3 import DQN
        from stable_baselines3.common.callbacks import BaseCallback
        import torch
    except ImportError as exc:
        raise ImportError(
            "Reinforcement learning dependencies (gymnasium, stable-baselines3, torch) are missing. "
            "Install requirements-rl.txt: pip install -r requirements-rl.txt"
        ) from exc

    cfg = cfg or C.RL
    lr = learning_rate or cfg.learning_rate

    if network == "marathahalli":
        scenario = scenario or "all"
        seed = seed if seed is not None else 101
        training_seeds = train_seeds or (101, 102, 103, 104, 105)
        validation_seeds = val_seeds or (106, 107, 108, 109, 110)
        research_seeds = tuple(range(121, 131))
        eval_seeds = tuple(range(111, 121))
        scenarios = ("imbalanced_orr", "imbalanced_varthur", "balanced", "surge_orr_north") if scenario == "all" else None
        eval_scen = "imbalanced_orr" if scenario == "all" else scenario
        default_target = C.ROOT / "models" / "dqn_marathahalli_site_best.zip"
    else:
        scenario = scenario or "imbalanced_ns"
        seed = seed if seed is not None else 1
        training_seeds = train_seeds or cfg.train_seeds
        validation_seeds = val_seeds or cfg.validation_seeds
        research_seeds = cfg.research_seeds
        eval_seeds = cfg.eval_seeds
        scenarios = ("imbalanced_ns", "imbalanced_ew", "balanced", "surge_north") if scenario == "all" else None
        eval_scen = "imbalanced_ns" if scenario == "all" else scenario
        default_target = cfg.models_dir / f"{cfg.default_model_name}.zip"

    # Resolve output path
    if out_path is None:
        target_path = default_target
    else:
        target_path = Path(out_path)
        if target_path.suffix != ".zip":
            target_path = target_path.with_suffix(".zip")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = target_path.parent / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    env = SumoIntersectionEnv(
        scenario="imbalanced_orr" if (network == "marathahalli" and scenario == "all") else ("imbalanced_ns" if scenario == "all" else scenario),
        seed=seed,
        cfg=cfg,
        rotate_seeds=rotate_seeds,
        scenarios=scenarios,
        network=network,
    )

    # Hyperparameters scaled appropriately
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

    # Periodic checkpoint callback during training
    saved_checkpoints: List[Tuple[int, Path]] = []

    class CheckpointProgressCallback(BaseCallback):
        def __init__(self, frequency: int):
            super().__init__(verbose=verbose)
            self.frequency = frequency

        def _on_step(self) -> bool:
            if self.n_calls % self.frequency == 0:
                step_idx = self.n_calls
                ckpt_file = checkpoints_dir / f"dqn_{network}_step_{step_idx}.zip"
                self.model.save(str(ckpt_file))
                saved_checkpoints.append((step_idx, ckpt_file))
                if verbose:
                    print(f"[Step {step_idx}/{timesteps}] Intermediate checkpoint saved: {ckpt_file.name}")
            return True

    callback = None
    step_freq = eval_freq or (10000 if timesteps >= 10000 else None)
    if step_freq and step_freq > 0 and timesteps >= step_freq:
        callback = CheckpointProgressCallback(frequency=step_freq)

    start_time = time.time()
    try:
        model.learn(total_timesteps=timesteps, callback=callback)
    finally:
        env.close()
    duration_s = round(time.time() - start_time, 2)

    # Save final model checkpoint
    model.save(str(target_path))
    saved_checkpoints.append((timesteps, target_path))

    # Evaluate checkpoints on validation seeds to select the best production model
    training_history: List[Dict[str, Any]] = []
    best_val_wait = float("inf")
    best_model_file: Optional[Path] = None

    if timesteps >= 5000 and len(saved_checkpoints) > 1:
        from ..runner import run_simulation
        if verbose:
            print(f"\n--- Post-Training Validation across {len(saved_checkpoints)} Checkpoints ---")

        for step_idx, ckpt_file in saved_checkpoints:
            val_waits = []
            val_queues = []
            val_completions = []
            for vs in validation_seeds[:3]:  # evaluate on representative validation seeds
                try:
                    res = run_simulation(
                        eval_scen,
                        "rl_dqn",
                        seed=vs,
                        policy_kwargs={"model_path": str(ckpt_file), "network": network},
                        network=network,
                        record_vehicles=False,
                    )
                    val_waits.append(res["avg_wait_s"])
                    val_queues.append(res["avg_queue_m"])
                    val_completions.append(res["completion_rate"])
                except Exception as err:
                    if verbose:
                        print(f"[Validation Error] step {step_idx}, seed {vs}: {err}")

            mean_val_wait = float(sum(val_waits) / len(val_waits)) if val_waits else float("nan")
            mean_val_queue = float(sum(val_queues) / len(val_queues)) if val_queues else float("nan")
            mean_val_comp = float(sum(val_completions) / len(val_completions)) if val_completions else float("nan")

            eval_record = {
                "step": step_idx,
                "checkpoint": str(ckpt_file),
                "mean_val_wait_s": round(mean_val_wait, 2),
                "mean_val_queue_m": round(mean_val_queue, 2),
                "mean_val_completion": round(mean_val_comp, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            training_history.append(eval_record)
            if verbose:
                print(
                    f"  Step {step_idx:5d}: wait={mean_val_wait:5.1f}s | "
                    f"queue={mean_val_queue:5.1f}m | done={mean_val_comp:4.0%}"
                )

            if mean_val_wait < best_val_wait and mean_val_comp >= 0.85:
                best_val_wait = mean_val_wait
                best_model_file = ckpt_file

    # If best validation checkpoint found, preserve it
    if best_model_file and best_model_file.exists():
        best_target = target_path.with_name(f"{target_path.stem}_best_val.zip")
        shutil.copyfile(best_model_file, best_target)

    # Save comprehensive metadata alongside checkpoint
    run_id = f"dqn_{network}_{scenario}_s{seed}_{int(time.time())}"
    meta_path = target_path.with_name(f"{target_path.stem}.metadata.json")
    metadata = {
        "run_id": run_id,
        "algorithm": "DQN",
        "framework": "stable-baselines3",
        "network_name": network,
        "scenario": scenario,
        "scenarios_rotated": list(scenarios) if scenarios else [scenario],
        "seed": seed,
        "timesteps": timesteps,
        "training_duration_s": duration_s,
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
            "train_seeds": list(training_seeds),
            "validation_seeds": list(validation_seeds),
            "eval_seeds": list(eval_seeds),
            "research_seeds": list(research_seeds),
        },
        "validation_summary": {
            "best_validation_wait_s": round(best_val_wait, 2) if best_val_wait != float("inf") else None,
            "best_model_path": str(best_model_file) if best_model_file else None,
            "eval_checkpoints": training_history,
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

    # Save training history JSON
    history_path = target_path.with_name(f"{target_path.stem}.history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2)

    return target_path, meta_path
