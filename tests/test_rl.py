"""Tests for Gymnasium environment, observation schema, and DQN controller in Phase P2.

Marked to skip gracefully if optional RL dependencies are missing,
ensuring legacy test suites and clean environments run without error.
"""
import json
from pathlib import Path
import pytest
import numpy as np

from dp1 import config as C
from dp1.network import NET_FILE, build_network
from dp1.signal_states import SignalStates
from dp1.rl.obs import build_observation, OBS_DIM, OBS_SCHEMA_VERSION, OBS_FEATURE_NAMES


def test_observation_builder_shape_and_bounds():
    """Verify build_observation produces exact 11-dim vector strictly in [0.0, 1.0]."""
    queues = {"N": 45.0, "S": 10.0, "E": 120.0, "W": 0.0}
    obs = build_observation(
        queues=queues,
        axis="NS",
        phase="GREEN",
        elapsed_green_s=15.0,
        t_s=300.0,
        max_detector_m=150.0,
        max_green_s=60.0,
        demand_duration_s=1800.0,
    )
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (11,)
    assert obs.dtype == np.float32
    assert np.all(obs >= 0.0)
    assert np.all(obs <= 1.0)

    # Queue checks: 45 / 150 = 0.3, 10 / 150 = 0.0667, 120 / 150 = 0.8, 0 / 150 = 0.0
    assert pytest.approx(obs[0], abs=1e-4) == 0.3
    assert pytest.approx(obs[1], abs=1e-4) == 10.0 / 150.0
    assert pytest.approx(obs[2], abs=1e-4) == 0.8
    assert pytest.approx(obs[3], abs=1e-4) == 0.0

    # One-hot axis & phase
    assert obs[4] == 1.0  # NS
    assert obs[5] == 0.0  # EW
    assert obs[6] == 1.0  # GREEN
    assert obs[7] == 0.0  # YELLOW
    assert obs[8] == 0.0  # ALL_RED

    # Elapsed green & timeline fraction
    assert pytest.approx(obs[9], abs=1e-4) == 15.0 / 60.0
    assert pytest.approx(obs[10], abs=1e-4) == 300.0 / 1800.0


def test_observation_schema_metadata():
    """Verify schema version and feature name count match OBS_DIM."""
    assert len(OBS_FEATURE_NAMES) == OBS_DIM
    assert OBS_SCHEMA_VERSION == "1.0.0"


def test_rl_dqn_missing_model_error():
    """Verify RLDQNController raises an actionable FileNotFoundError when model is missing."""
    gym = pytest.importorskip("gymnasium")
    sb3 = pytest.importorskip("stable_baselines3")
    from dp1.controllers.rl_dqn import RLDQNController

    if not NET_FILE.exists():
        build_network()
    states = SignalStates(NET_FILE)

    with pytest.raises(FileNotFoundError) as exc_info:
        RLDQNController(states, model_path="/path/that/does/not/exist/model.zip")
    assert "Trained RL model not found" in str(exc_info.value)
    assert "train-rl" in str(exc_info.value)


def test_rl_dqn_metadata_mismatch_error(tmp_path):
    """Verify RLDQNController rejects model when companion metadata schema mismatches."""
    gym = pytest.importorskip("gymnasium")
    sb3 = pytest.importorskip("stable_baselines3")
    from dp1.controllers.rl_dqn import RLDQNController

    if not NET_FILE.exists():
        build_network()
    states = SignalStates(NET_FILE)

    fake_model = tmp_path / "fake_model.zip"
    fake_model.write_bytes(b"PK\x03\x04fake_zip_bytes")
    fake_meta = tmp_path / "fake_model.metadata.json"
    fake_meta.write_text(json.dumps({
        "obs_dim": 999,
        "obs_schema_version": "0.1.0",
    }))

    with pytest.raises(ValueError) as exc_info:
        RLDQNController(states, model_path=fake_model)
    assert "Observation schema dimension mismatch" in str(exc_info.value)


def test_sumo_intersection_env_spaces_and_reset(tmp_path):
    """Verify Gymnasium environment spaces and seeded reset lifecycle."""
    gym = pytest.importorskip("gymnasium")
    from dp1.rl.env import SumoIntersectionEnv

    env = SumoIntersectionEnv(scenario="imbalanced_ns", seed=1, out_dir=tmp_path)
    assert env.action_space.n == 2
    assert env.observation_space.shape == (11,)

    try:
        obs, info = env.reset(seed=1)
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (11,)
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)
        assert info["phase"] == "GREEN"
        assert info["axis"] == "NS"
        assert "queues" in info
    finally:
        env.close()


def test_sumo_intersection_env_step_and_safety(tmp_path):
    """Verify stepping with external actions respects min-green, max-green, and clearance intervals."""
    gym = pytest.importorskip("gymnasium")
    from dp1.rl.env import SumoIntersectionEnv

    env = SumoIntersectionEnv(scenario="imbalanced_ns", seed=1, out_dir=tmp_path)
    try:
        obs, info = env.reset(seed=1)

        # 1. HOLD for 5 steps (elapsed = 5s < min_green=10s)
        for _ in range(5):
            obs, reward, term, trunc, info = env.step(action=0)
            assert info["phase"] == "GREEN"
            assert info["axis"] == "NS"
            assert reward <= 0.0

        # 2. REQUEST_SWITCH at t=5s (elapsed < min_green=10s -> must be REJECTED, stays GREEN)
        obs, reward, term, trunc, info = env.step(action=1)
        assert info["phase"] == "GREEN"
        assert info["axis"] == "NS"

        # 3. Step until elapsed >= min_green (t=10s), then REQUEST_SWITCH
        for _ in range(4):  # t=7, 8, 9, 10
            obs, reward, term, trunc, info = env.step(action=0)

        # At t=10s, elapsed green is 10s >= min_green, request switch
        obs, reward, term, trunc, info = env.step(action=1)
        assert info["phase"] == "YELLOW"  # accepted switch initiates clearance
        assert info["switched"] is True

        # Clearance interval: must spend yellow_s (3s) in YELLOW, then all_red_s (2s) in ALL_RED
        # Step 1 in yellow
        obs, reward, term, trunc, info = env.step(action=0)
        assert info["phase"] == "YELLOW"
        # Step 2 in yellow
        obs, reward, term, trunc, info = env.step(action=0)
        assert info["phase"] == "YELLOW"
        # Step 3 completes yellow -> transitions to ALL_RED
        obs, reward, term, trunc, info = env.step(action=0)
        assert info["phase"] == "ALL_RED"

        # Step 1 in all-red
        obs, reward, term, trunc, info = env.step(action=0)
        assert info["phase"] == "ALL_RED"
        # Step 2 completes all-red -> enters GREEN on other axis (EW)
        obs, reward, term, trunc, info = env.step(action=0)
        assert info["phase"] == "GREEN"
        assert info["axis"] == "EW"
    finally:
        env.close()


def test_tiny_smoke_training_and_inference(tmp_path):
    """Verify tiny smoke training creates valid model + metadata, and RLDQNController predicts cleanly."""
    gym = pytest.importorskip("gymnasium")
    sb3 = pytest.importorskip("stable_baselines3")
    from dp1.rl.train import train_dqn
    from dp1.controllers.rl_dqn import RLDQNController

    model_path = tmp_path / "smoke_dqn.zip"
    meta_path = tmp_path / "smoke_dqn.metadata.json"

    # Train for 20 timesteps as a pure smoke test
    saved_model, saved_meta = train_dqn(
        scenario="imbalanced_ns",
        seed=1,
        timesteps=20,
        out_path=model_path,
        verbose=0,
    )

    assert saved_model.exists()
    assert saved_meta.exists()

    with open(saved_meta, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["algorithm"] == "DQN"
    assert meta["obs_dim"] == 11
    assert meta["obs_schema_version"] == "1.0.0"
    assert "package_versions" in meta
    assert "hyperparameters" in meta

    # Test loading and inference
    if not NET_FILE.exists():
        build_network()
    states = SignalStates(NET_FILE)
    ctl = RLDQNController(states, model_path=saved_model)

    queues = {"N": 20.0, "S": 15.0, "E": 5.0, "W": 0.0}
    action = ctl.decide_action("NS", elapsed=12.0, queues=queues, t=12.0)
    assert action in (0, 1)
