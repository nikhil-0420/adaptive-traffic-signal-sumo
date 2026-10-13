"""Health and system summary routes."""
import os
import platform
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Response, status

from dp1 import sumo_utils
from ..config import (
    ALLOWED_DEMAND_LEVELS,
    ALLOWED_POLICIES,
    ALLOWED_SCENARIOS,
    RESEARCH_DIR,
    RESULTS_DIR,
    RUNS_DIR,
)
from ..schemas import HealthResponse, SummaryResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def get_health(response: Response):
    """Check system health, SUMO installation, and environment readiness.

    Returns HTTP 503 if SUMO is unavailable, ensuring truthful reporting.
    """
    sumo_bin = None
    sumo_ver = None
    sumo_available = False
    details = {}

    try:
        sumo_bin = sumo_utils.binary("sumo")
        # Run sumo --version to verify executable works
        res = subprocess.run(
            [sumo_bin, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            sumo_available = True
            first_line = res.stdout.strip().split("\n")[0] if res.stdout else "SUMO found"
            sumo_ver = first_line
        else:
            details["sumo_error"] = res.stderr.strip()
    except Exception as e:
        details["sumo_exception"] = str(e)

    # Check results directory writability
    writable = False
    try:
        test_file = RESULTS_DIR / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        writable = True
    except Exception as e:
        details["write_error"] = str(e)

    if not sumo_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        status_str = "unavailable"
        details["action_required"] = (
            "SUMO binary not found in PATH or SUMO_HOME. Please install Eclipse SUMO to run simulations."
        )
    elif not writable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        status_str = "degraded"
        details["action_required"] = "Results directory is not writable."
    else:
        status_str = "ok"

    return HealthResponse(
        status=status_str,
        sumo_available=sumo_available,
        sumo_binary=str(sumo_bin) if sumo_bin else None,
        sumo_version=sumo_ver,
        python_version=platform.python_version(),
        results_writable=writable,
        details=details,
    )


@router.get("/summary", response_model=SummaryResponse)
def get_summary():
    """Return overview counts of completed runs, experiments, and supported parameters."""
    runs = [d for d in RUNS_DIR.iterdir() if d.is_dir()] if RUNS_DIR.exists() else []
    experiments = [d for d in RESEARCH_DIR.iterdir() if d.is_dir()] if RESEARCH_DIR.exists() else []

    # Sort runs by modification time descending
    recent = []
    for d in sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        has_timeseries = (d / "timeseries.csv").exists()
        has_telemetry = (d / "telemetry.json").exists()
        status_val = "completed" if has_timeseries else "unknown"
        recent.append({
            "run_id": d.name,
            "status": status_val,
            "has_telemetry": has_telemetry,
            "mtime": d.stat().st_mtime,
        })

    return SummaryResponse(
        total_runs=len(runs),
        total_experiments=len(experiments),
        scenarios=ALLOWED_SCENARIOS,
        policies=ALLOWED_POLICIES,
        demand_levels=ALLOWED_DEMAND_LEVELS,
        latest_runs=recent,
    )
