"""Comprehensive unit and integration tests for DP1 FastAPI backend (Phase P5A)."""
import csv
import json
import time
from pathlib import Path
import pytest
pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")
from fastapi.testclient import TestClient

from backend.app import app
from backend import config as api_config
from backend.process_manager import process_manager, ProcessInfo
from backend.security import validate_identifier, resolve_safe_run_dir, resolve_safe_experiment_dir


client = TestClient(app)


# ------------------------------------------------------------------
# Health & Diagnostics
# ------------------------------------------------------------------

def test_health_endpoint_ok():
    """Verify /api/health reports 200 and valid SUMO environment when SUMO is present."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["sumo_available"] is True
    assert data["sumo_binary"] is not None
    assert "SUMO" in data["sumo_version"]
    assert data["results_writable"] is True


def test_health_endpoint_sumo_missing(monkeypatch):
    """Verify /api/health truthfully returns 503 when SUMO binary is absent."""
    import dp1.sumo_utils
    monkeypatch.setattr(dp1.sumo_utils, "binary", lambda name: "C:\\nonexistent_sumo_path.exe")

    resp = client.get("/api/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "unavailable"
    assert data["sumo_available"] is False
    assert "action_required" in data["details"]


def test_summary_endpoint():
    """Verify /api/summary returns counts and available parameters."""
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_runs"] >= 0
    assert "imbalanced_ns" in data["scenarios"]
    assert "adaptive" in data["policies"]
    assert "medium" in data["demand_levels"]
    assert isinstance(data["latest_runs"], list)


# ------------------------------------------------------------------
# Security: Validation & Path Traversal Guards
# ------------------------------------------------------------------

def test_identifier_validation():
    """Verify safe identifier validator rejects slashes, dots, and shell characters."""
    assert validate_identifier("safe_id-123") == "safe_id-123"

    for bad in ["../evil", "evil/path", "..\\evil", "run;rm -rf", "run*", "run|sh"]:
        with pytest.raises(Exception):
            validate_identifier(bad)


def test_runs_path_traversal_rejection():
    """Verify path traversal attempts in run routes return 400 Bad Request."""
    resp = client.get("/api/runs/..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in (400, 404)

    resp = client.get("/api/runs/test..subdir")
    assert resp.status_code == 400


def test_experiment_path_traversal_and_allowlist_rejection():
    """Verify artifact downloads reject path traversal and non-allowlisted filenames."""
    from backend.security import resolve_safe_experiment_artifact

    # Disallowed filename
    resp = client.get("/api/experiments/exp_smoke_test/artifacts/secret_code.py")
    assert resp.status_code == 400
    assert "not in the allowed artifacts list" in resp.json()["detail"]

    # Traversal in artifact name via resolver
    with pytest.raises(Exception):
        resolve_safe_experiment_artifact("exp_smoke_test", "../secret.txt")

    # Traversal in artifact route
    resp = client.get("/api/experiments/exp_smoke_test/artifacts/..%2Fsecret.txt")
    assert resp.status_code in (400, 404)


# ------------------------------------------------------------------
# Simulation Run Launch Validation
# ------------------------------------------------------------------

def test_run_launch_validation():
    """Verify POST /api/runs enforces strict parameter allowlists."""
    # Unknown scenario
    resp = client.post("/api/runs", json={
        "scenario": "unknown_scenario_xyz",
        "policy": "adaptive",
        "seed": 1,
    })
    assert resp.status_code == 400
    assert "Invalid scenario" in resp.json()["detail"]

    # Unknown policy
    resp = client.post("/api/runs", json={
        "scenario": "imbalanced_ns",
        "policy": "unknown_policy_abc",
        "seed": 1,
    })
    assert resp.status_code == 400
    assert "Invalid policy" in resp.json()["detail"]

    # Invalid seed range
    resp = client.post("/api/runs", json={
        "scenario": "imbalanced_ns",
        "policy": "adaptive",
        "seed": -5,
    })
    assert resp.status_code == 400

    # Invalid demand level
    resp = client.post("/api/runs", json={
        "scenario": "imbalanced_ns",
        "policy": "adaptive",
        "seed": 1,
        "demand_level": "extreme",
    })
    assert resp.status_code == 400


def test_duplicate_run_conflict(monkeypatch):
    """Verify that launching an already running simulation returns 409 Conflict."""
    monkeypatch.setattr(process_manager, "is_running", lambda run_id: True)

    resp = client.post("/api/runs", json={
        "scenario": "imbalanced_ns",
        "policy": "adaptive",
        "seed": 1,
    })
    assert resp.status_code == 409
    assert "already running" in resp.json()["detail"]


# ------------------------------------------------------------------
# Runs: Detail, Timeseries, Decisions, Telemetry
# ------------------------------------------------------------------

def test_run_not_found():
    """Verify querying a non-existent run ID returns 404."""
    resp = client.get("/api/runs/nonexistent_run_s99999")
    assert resp.status_code == 404


def test_run_detail_and_legacy_schema(tmp_path, monkeypatch):
    """Verify run details properly report null for missing metrics rather than zero."""
    test_run_dir = api_config.RUNS_DIR / "test_api_legacy_s99"
    test_run_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Write dummy timeseries
        ts_file = test_run_dir / "timeseries.csv"
        with open(ts_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "phase", "axis", "q_N", "q_S", "q_E", "q_W"])
            w.writerow([1.0, "GREEN", "NS", 10.5, 8.0, 2.0, 1.5])
            w.writerow([2.0, "GREEN", "NS", 12.0, 9.0, 2.5, 1.0])

        # Write dummy metrics with intentional None / missing columns
        metrics_file = test_run_dir / "metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump({
                "avg_wait_s": 25.4,
                "p95_wait_s": 60.1,
                "directional_wait_disparity_s": None,  # explicitly missing in legacy
            }, f)

        # GET detail
        resp = client.get("/api/runs/test_api_legacy_s99")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == "test_api_legacy_s99"
        assert data["status"] == "completed"
        assert data["metrics"]["avg_wait_s"] == 25.4
        assert data["metrics"]["directional_wait_disparity_s"] is None

        # GET timeseries with pagination/step
        resp_ts = client.get("/api/runs/test_api_legacy_s99/timeseries?limit=1&step=1")
        assert resp_ts.status_code == 200
        ts_data = resp_ts.json()
        assert ts_data["total_points"] == 1
        assert ts_data["points"][0]["q_N"] == 10.5

    finally:
        # Cleanup
        for p in test_run_dir.glob("*"):
            p.unlink(missing_ok=True)
        test_run_dir.rmdir()


def test_telemetry_atomic_and_staleness(tmp_path):
    """Verify atomic telemetry parsing and staleness detection."""
    test_run_dir = api_config.RUNS_DIR / "test_api_telem_s88"
    test_run_dir.mkdir(parents=True, exist_ok=True)

    try:
        telem_file = test_run_dir / "telemetry.json"
        # 1. Fresh telemetry
        now = time.time()
        telem_data = {
            "run_id": "test_api_telem_s88",
            "status": "running",
            "sim_time_s": 150.0,
            "phase": "GREEN",
            "axis": "NS",
            "queues_m": {"N": 20.5, "S": 15.0, "E": 5.0, "W": 2.0},
            "traffic_light_state": "GGggrrrrGGggrrrr",
            "updated_at": now,
            "emergency_approaching": True,
            "emergency_dist_m": 85.0,
        }
        with open(telem_file, "w", encoding="utf-8") as f:
            json.dump(telem_data, f)

        resp = client.get("/api/runs/test_api_telem_s88/telemetry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sim_time_s"] == 150.0
        assert data["is_stale"] is False
        assert data["emergency_approaching"] is True
        assert data["emergency_dist_m"] == 85.0

        # 2. Stale telemetry (updated 10 seconds ago)
        telem_data["updated_at"] = now - 10.0
        with open(telem_file, "w", encoding="utf-8") as f:
            json.dump(telem_data, f)

        resp_stale = client.get("/api/runs/test_api_telem_s88/telemetry")
        assert resp_stale.status_code == 200
        assert resp_stale.json()["is_stale"] is True

    finally:
        for p in test_run_dir.glob("*"):
            p.unlink(missing_ok=True)
        test_run_dir.rmdir()


# ------------------------------------------------------------------
# Token Authentication Protection
# ------------------------------------------------------------------

def test_token_auth_protection(monkeypatch):
    """Verify mutating endpoints require valid token when API_AUTH_TOKEN is configured."""
    monkeypatch.setattr(api_config, "API_AUTH_TOKEN", "secret-test-token-123")
    import backend.security
    monkeypatch.setattr(backend.security, "API_AUTH_TOKEN", "secret-test-token-123")

    # Missing token -> 401
    resp = client.post("/api/runs", json={
        "scenario": "imbalanced_ns",
        "policy": "adaptive",
        "seed": 1,
    })
    assert resp.status_code == 401

    # Invalid token -> 401
    resp = client.post(
        "/api/runs",
        json={"scenario": "imbalanced_ns", "policy": "adaptive", "seed": 1},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401

    # Valid token via Bearer header
    monkeypatch.setattr(process_manager, "launch_run", lambda **kwargs: (True, "mock started"))
    resp_valid = client.post(
        "/api/runs",
        json={"scenario": "imbalanced_ns", "policy": "adaptive", "seed": 1},
        headers={"Authorization": "Bearer secret-test-token-123"},
    )
    assert resp_valid.status_code == 201

    # Valid token via X-API-Key header
    resp_key = client.post(
        "/api/runs",
        json={"scenario": "imbalanced_ns", "policy": "adaptive", "seed": 1},
        headers={"X-API-Key": "secret-test-token-123"},
    )
    assert resp_key.status_code == 201


# ------------------------------------------------------------------
# Research Experiments Endpoints
# ------------------------------------------------------------------

def test_research_endpoints():
    """Verify research experiments listing, details, status, results, and artifacts."""
    # List experiments
    resp = client.get("/api/experiments")
    assert resp.status_code == 200
    exps = resp.json()
    assert any(e["experiment_id"] == "exp_smoke_test" for e in exps)

    # Experiment detail
    resp_det = client.get("/api/experiments/exp_smoke_test")
    assert resp_det.status_code == 200
    det = resp_det.json()
    assert det["experiment_id"] == "exp_smoke_test"
    assert det["manifest"]["preset"] == "smoke"

    # Status
    resp_st = client.get("/api/experiments/exp_smoke_test/status")
    assert resp_st.status_code == 200
    st = resp_st.json()
    assert st["experiment_id"] == "exp_smoke_test"
    assert st["complete"] == 3

    # Results
    resp_res = client.get("/api/experiments/exp_smoke_test/results")
    assert resp_res.status_code == 200
    res = resp_res.json()
    assert len(res["aggregate"]) > 0
    assert len(res["raw_runs"]) > 0

    # Artifacts list
    resp_art = client.get("/api/experiments/exp_smoke_test/artifacts")
    assert resp_art.status_code == 200
    arts = resp_art.json()["artifacts"]
    assert any(a["name"] == "report.md" for a in arts)

    # Artifact download
    resp_dl = client.get("/api/experiments/exp_smoke_test/artifacts/report.md")
    assert resp_dl.status_code == 200
    assert resp_dl.headers["content-type"].startswith("text/markdown")


def test_experiment_launch_validation():
    """Verify POST /api/experiments validates presets and bounds."""
    # Invalid preset
    resp = client.post("/api/experiments", json={"preset": "invalid_preset"})
    assert resp.status_code == 400

    # Invalid jobs (> 8)
    resp = client.post("/api/experiments", json={"preset": "smoke", "jobs": 16})
    assert resp.status_code == 400

    # Invalid pattern
    resp = client.post("/api/experiments", json={"preset": "smoke", "patterns": ["nonexistent_pattern"]})
    assert resp.status_code == 400
