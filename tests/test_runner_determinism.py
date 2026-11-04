"""Test runner determinism across multiple runs."""
import hashlib
from pathlib import Path
import pytest
from dp1.runner import run_simulation


def test_runner_determinism_decisions_sha256(tmp_path):
    """Verify the same config run twice through the runner path yields identical decisions.csv SHA256."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    # Run on dev seed 101 (never final seeds)
    res1 = run_simulation(
        scenario="balanced",
        policy="hybrid_queue_adaptive",
        seed=101,
        demand_level="low",
        network="marathahalli",
        out_dir=dir1,
        port=25101,
    )
    res2 = run_simulation(
        scenario="balanced",
        policy="hybrid_queue_adaptive",
        seed=101,
        demand_level="low",
        network="marathahalli",
        out_dir=dir2,
        port=25102,
    )

    decisions1 = dir1 / "decisions.csv"
    decisions2 = dir2 / "decisions.csv"

    assert decisions1.exists(), "decisions.csv not produced in run1"
    assert decisions2.exists(), "decisions.csv not produced in run2"

    bytes1 = decisions1.read_bytes()
    bytes2 = decisions2.read_bytes()

    sha1 = hashlib.sha256(bytes1).hexdigest()
    sha2 = hashlib.sha256(bytes2).hexdigest()

    assert sha1 == sha2, f"decisions.csv non-deterministic! Hash 1: {sha1}, Hash 2: {sha2}"
    assert len(bytes1) > 0, "decisions.csv is empty"
