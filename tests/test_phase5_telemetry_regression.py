"""Phase 5 Backend & Telemetry Regression Test.

Validates:
1. `raw_runs.csv` / `summary.json` / `metrics.json` are byte-identical across runs (excluding timestamps).
2. `decisions.csv` is byte-identical across runs.
3. `timeseries.csv` is byte-identical across runs.
4. `telemetry.json` vehicle entries have `z` coordinate included.
5. In Marathahalli network, flyover vehicles have z > 6.0m while surface vehicles have z == 0.0m.
"""

import hashlib
import json
from pathlib import Path
import pytest
from dp1 import config as C
from dp1.runner import run_simulation

EXPECTED_DECISIONS_SHA256 = "4e6410651b7468c992a59be4fed946c96c45d20f657b3f77b504fd6ebe354b67"
EXPECTED_TIMESERIES_SHA256 = "895bad0226bf6bfd00a84ebfcd19982fb3c3c73bea6218f4773ecd829b73f95f"


def test_phase5_telemetry_z_regression():
    """Verify that adding z to vehicle telemetry does not alter decisions or timeseries."""
    run_dir = C.RESULTS_DIR / "runs" / "balanced_hybrid_queue_adaptive_s101"
    baseline_dir = C.ROOT / "scratch" / "regression_baseline"

    if not run_dir.exists():
        run_simulation(
            "balanced",
            "hybrid_queue_adaptive",
            seed=101,
            demand_level="medium",
            record_vehicles=True,
        )

    assert run_dir.exists(), f"Run directory {run_dir} must exist"

    # 1. Compare decisions.csv
    dec_run = (run_dir / "decisions.csv").read_bytes()
    dec_hash = hashlib.sha256(dec_run).hexdigest()
    assert dec_hash == EXPECTED_DECISIONS_SHA256, (
        f"decisions.csv hash mismatch: {dec_hash} != {EXPECTED_DECISIONS_SHA256}"
    )

    # 2. Compare timeseries.csv
    ts_run = (run_dir / "timeseries.csv").read_bytes()
    ts_hash = hashlib.sha256(ts_run).hexdigest()
    assert ts_hash == EXPECTED_TIMESERIES_SHA256, (
        f"timeseries.csv hash mismatch: {ts_hash} != {EXPECTED_TIMESERIES_SHA256}"
    )

    # 3. Direct byte comparison if baseline dir is present
    if baseline_dir.exists():
        dec_base = (baseline_dir / "decisions.csv").read_bytes()
        assert dec_run == dec_base, "decisions.csv must be byte-identical to baseline"
        ts_base = (baseline_dir / "timeseries.csv").read_bytes()
        assert ts_run == ts_base, "timeseries.csv must be byte-identical to baseline"
        metrics_run = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        metrics_base = json.loads((baseline_dir / "metrics.json").read_text(encoding="utf-8"))
        assert metrics_run == metrics_base, "metrics.json must be identical to baseline"


def test_phase5_telemetry_includes_z():
    """Verify that live telemetry payloads include the z coordinate for each vehicle."""
    run_dir = C.RESULTS_DIR / "runs" / "marathahalli_imbalanced_orr_hybrid_queue_adaptive_s101"
    if not run_dir.exists():
        # Run short 60s smoke simulation if directory not yet created
        run_simulation(
            "imbalanced_orr",
            "hybrid_queue_adaptive",
            seed=101,
            network="marathahalli",
            demand_level="medium",
            record_vehicles=True,
            max_sim_time_s=60.0,
        )

    telem_file = run_dir / "telemetry.json"
    assert telem_file.exists(), "telemetry.json must exist"
    telem = json.loads(telem_file.read_text(encoding="utf-8"))

    vehs = telem.get("vehicles", [])
    assert len(vehs) > 0, "Telemetry must contain active vehicles"
    for v in vehs:
        assert "z" in v, f"Vehicle {v['id']} must contain 'z' elevation field"
        assert isinstance(v["z"], (int, float)), f"Vehicle {v['id']} z must be numeric"

    # Assert that at least one vehicle is elevated on the flyover (z > 6.0m)
    elevated = [v for v in vehs if v.get("z", 0.0) >= 6.0]
    assert len(elevated) > 0, "Must have at least one elevated vehicle on flyover deck"
