"""Simulation runs management routes."""
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import (
    ALLOWED_DEMAND_LEVELS,
    ALLOWED_EMERGENCY_APPROACHES,
    ALLOWED_POLICIES,
    ALLOWED_SCENARIOS,
    RESEARCH_DIR,
    RESULTS_DIR,
    RUNS_DIR,
    TELEMETRY_STALE_THRESHOLD_S,
)
from ..process_manager import process_manager
from ..schemas import (
    DecisionsResponse,
    ReplayResponse,
    RunDetailResponse,
    RunLaunchRequest,
    RunStatusResponse,
    TelemetryResponse,
    TimeseriesResponse,
)
from ..security import resolve_safe_run_dir, verify_auth_token

router = APIRouter(prefix="/runs", tags=["Runs"])


def _derive_run_id(req: RunLaunchRequest) -> str:
    """Derive standard run ID consistent with dp1.runner."""
    net_tag = "" if req.network == "synthetic" else f"{req.network}_"
    em_tag = ""
    if req.emergency_event:
        em_tag = "_em_pri" if req.emergency_priority else "_em"
    if req.demand_level == "medium":
        # Check if legacy pattern or standard pattern
        return f"{net_tag}{req.scenario}_{req.policy}_s{req.seed}{em_tag}"
    return f"{net_tag}{req.scenario}_{req.demand_level}_{req.policy}_s{req.seed}{em_tag}"


def _find_run_dir(run_id: str) -> Optional[Path]:
    """Find run directory matching run_id in results/runs/ or research matrix runs/."""
    # 1. Direct in results/runs/
    direct = RUNS_DIR / run_id
    if direct.is_dir():
        return direct

    # 2. Alternative naming with explicit medium in results/runs/
    if "_medium_" not in run_id:
        parts = run_id.split("_", 2)
        if len(parts) >= 3:
            alt_id = f"{parts[0]}_{parts[1]}_medium_{parts[2]}"
            alt_dir = RUNS_DIR / alt_id
            if alt_dir.is_dir():
                return alt_dir
    else:
        alt_id = run_id.replace("_medium_", "_")
        alt_dir = RUNS_DIR / alt_id
        if alt_dir.is_dir():
            return alt_dir

    # 3. Check in research matrix directories (e.g. exp_marathahalli_site_720/runs/)
    if RESEARCH_DIR.is_dir():
        candidates = [run_id, f"cell_{run_id}"]
        if run_id.startswith("cell_"):
            candidates.append(run_id[5:])
        for exp_dir in RESEARCH_DIR.iterdir():
            if exp_dir.is_dir():
                runs_sub = exp_dir / "runs"
                if runs_sub.is_dir():
                    for cand in candidates:
                        cand_dir = runs_sub / cand
                        if cand_dir.is_dir():
                            return cand_dir

    return None


@router.post("", response_model=RunStatusResponse, status_code=status.HTTP_201_CREATED)
def launch_run(
    req: RunLaunchRequest,
    _auth: bool = Depends(verify_auth_token),
):
    """Validate request and launch a single simulation run in a managed subprocess."""
    # 1. Validation against allowlists
    if req.scenario not in ALLOWED_SCENARIOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario '{req.scenario}'. Allowed: {ALLOWED_SCENARIOS}",
        )
    if req.policy not in ALLOWED_POLICIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy '{req.policy}'. Allowed: {ALLOWED_POLICIES}",
        )
    if req.demand_level not in ALLOWED_DEMAND_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demand_level '{req.demand_level}'. Allowed: {ALLOWED_DEMAND_LEVELS}",
        )
    if req.emergency_approach not in ALLOWED_EMERGENCY_APPROACHES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid emergency_approach '{req.emergency_approach}'. Allowed: {ALLOWED_EMERGENCY_APPROACHES}",
        )
    if req.seed < 0 or req.seed > 100000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seed {req.seed} out of acceptable range [0, 100000].",
        )

    # 2. Check concurrency
    if process_manager.count_active("run") >= 2:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum concurrent runs limit reached (2). Please wait for active runs to finish.",
        )

    run_id = _derive_run_id(req)

    # 3. Prevent duplicate active runs
    if process_manager.is_running(run_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run '{run_id}' is already running.",
        )

    # 4. Launch subprocess safely
    success, msg = process_manager.launch_run(
        run_id=run_id,
        scenario=req.scenario,
        policy=req.policy,
        seed=req.seed,
        demand_level=req.demand_level,
        emergency_event=req.emergency_event,
        emergency_priority=req.emergency_priority,
        emergency_approach=req.emergency_approach,
        emergency_depart=req.emergency_depart,
        model_path=req.model_path,
        gui=req.gui,
        network=req.network,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )

    return RunStatusResponse(
        run_id=run_id,
        status="running",
        message=msg,
        started_at=time.time(),
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str):
    """Retrieve run details and performance metrics."""
    run_dir = resolve_safe_run_dir(run_id)
    if not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run directory '{run_id}' not found.",
            )

    info = process_manager.get_info(run_id)
    if info and info.poll_status() == "running":
        run_status = "running"
    elif (run_dir / "timeseries.csv").exists():
        run_status = "completed"
    else:
        run_status = "failed"

    # Load metrics if available
    metrics = None
    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            pass

    # Fallback to all_runs.csv if metrics.json is not present
    if metrics is None:
        all_runs_csv = RESULTS_DIR / "all_runs.csv"
        if all_runs_csv.exists():
            try:
                with open(all_runs_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Match by run_id or (scenario, policy, seed)
                        row_scenario = row.get("scenario")
                        row_policy = row.get("policy")
                        row_seed = row.get("seed")
                        if (
                            row.get("run_id") == run_id
                            or f"{row_scenario}_{row_policy}_s{row_seed}" == run_id
                            or f"{row_scenario}_medium_{row_policy}_s{row_seed}" == run_id
                        ):
                            # Convert non-empty numeric fields to float/int, missing as None
                            metrics = {}
                            for k, v in row.items():
                                if v == "" or v is None:
                                    metrics[k] = None
                                else:
                                    try:
                                        metrics[k] = float(v) if "." in v else int(v)
                                    except ValueError:
                                        metrics[k] = v
                            break
            except Exception:
                pass

    # Collect available artifact names
    artifacts = [f.name for f in run_dir.iterdir() if f.is_file()]

    return RunDetailResponse(
        run_id=run_id,
        status=run_status,
        metrics=metrics,
        available_artifacts=artifacts,
    )


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: str):
    """Retrieve run execution status and exit code."""
    run_dir = resolve_safe_run_dir(run_id)
    info = process_manager.get_info(run_id)

    exit_code = None
    started_at = None
    finished_at = None
    sim_time_s = None

    if info:
        st = info.poll_status()
        exit_code = info.exit_code
        started_at = info.started_at
        finished_at = info.finished_at
    elif not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
            st = "completed" if (run_dir / "timeseries.csv").exists() else "failed"
            exit_code = 0 if st == "completed" else 1
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
    elif (run_dir / "timeseries.csv").exists():
        st = "completed"
        exit_code = 0
    else:
        st = "failed"

    # Check telemetry for current sim_time_s
    telem_file = run_dir / "telemetry.json"
    if telem_file.exists():
        try:
            with open(telem_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
                sim_time_s = tdata.get("sim_time_s")
        except Exception:
            pass

    return RunStatusResponse(
        run_id=run_id,
        status=st,
        exit_code=exit_code,
        sim_time_s=sim_time_s,
        started_at=started_at,
        finished_at=finished_at,
    )


@router.get("/{run_id}/timeseries", response_model=TimeseriesResponse)
def get_timeseries(
    run_id: str,
    limit: Optional[int] = Query(None, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    step: int = Query(1, ge=1, le=60, description="Downsample step"),
):
    """Retrieve timeseries queue and phase records for a run."""
    run_dir = resolve_safe_run_dir(run_id)
    if not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
        else:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    csv_path = run_dir / "timeseries.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"timeseries.csv not found for run '{run_id}'.")

    points = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < offset:
                continue
            if (i - offset) % step != 0:
                continue
            # Parse record
            rec: Dict[str, Any] = {}
            for k, v in row.items():
                if v == "" or v is None:
                    rec[k] = None
                else:
                    try:
                        rec[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        if v.lower() == "true":
                            rec[k] = True
                        elif v.lower() == "false":
                            rec[k] = False
                        else:
                            rec[k] = v
            points.append(rec)
            if limit and len(points) >= limit:
                break

    return TimeseriesResponse(
        run_id=run_id,
        total_points=len(points),
        points=points,
    )


@router.get("/{run_id}/decisions", response_model=DecisionsResponse)
def get_decisions(
    run_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000),
):
    """Retrieve cycle-by-cycle green time decisions for a run."""
    run_dir = resolve_safe_run_dir(run_id)
    if not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
        else:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    csv_path = run_dir / "decisions.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"decisions.csv not found for run '{run_id}'.")

    decisions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec: Dict[str, Any] = {}
            for k, v in row.items():
                if v == "" or v is None:
                    rec[k] = None
                else:
                    try:
                        rec[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        rec[k] = v
            decisions.append(rec)
            if limit and len(decisions) >= limit:
                break

    return DecisionsResponse(
        run_id=run_id,
        total_decisions=len(decisions),
        decisions=decisions,
    )


@router.get("/{run_id}/telemetry", response_model=TelemetryResponse)
def get_telemetry(run_id: str):
    """Retrieve live atomic telemetry for an active or completed simulation run."""
    run_dir = resolve_safe_run_dir(run_id)
    if not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
        else:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    telem_file = run_dir / "telemetry.json"
    if not telem_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Telemetry not available for run '{run_id}'. Run may have completed prior to telemetry support.",
        )

    try:
        with open(telem_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read telemetry: {e}")

    updated_at = float(data.get("updated_at", 0))
    is_stale = (time.time() - updated_at) > TELEMETRY_STALE_THRESHOLD_S

    status_str = data.get("status", "unknown")
    info = process_manager.get_info(run_id)
    if info and info.poll_status() != "running" and status_str == "running":
        # Process has terminated but telemetry still says running -> stale/failed
        status_str = info.poll_status()

    return TelemetryResponse(
        run_id=data.get("run_id", run_id),
        status=status_str,
        sim_time_s=float(data.get("sim_time_s", 0.0)),
        phase=data.get("phase", "GREEN"),
        axis=data.get("axis", "NS"),
        queues_m=data.get("queues_m", {}),
        traffic_light_state=data.get("traffic_light_state", ""),
        updated_at=updated_at,
        is_stale=is_stale,
        emergency_approaching=bool(data.get("emergency_approaching", False)),
        emergency_dist_m=data.get("emergency_dist_m"),
        vehicles=data.get("vehicles"),
        approach_queues=data.get("approach_queues"),
        adaptive_decision=data.get("adaptive_decision"),
        error=data.get("error"),
    )


@router.get("/{run_id}/replay", response_model=ReplayResponse)
def get_replay(run_id: str):
    """Retrieve full microscopic vehicle replay data for a run."""
    run_dir = resolve_safe_run_dir(run_id)
    if not run_dir.exists():
        alt = _find_run_dir(run_id)
        if alt:
            run_dir = alt
        else:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    replay_file = run_dir / "replay.json"
    if not replay_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Replay not available for run '{run_id}'. Run may need replay generation.",
        )

    try:
        with open(replay_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read replay data: {e}")

    if not data.get("network"):
        if "marathahalli" in run_dir.name or "orr" in data.get("scenario", ""):
            data["network"] = "marathahalli"
        else:
            data["network"] = "synthetic"

    return ReplayResponse(**data)
