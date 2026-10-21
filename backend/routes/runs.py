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
    REPO_ROOT,
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


def _candidate_run_ids(run_id: str) -> List[str]:
    """Generate potential alternate IDs (handling _medium_, _low_, _heavy_ insertion/removal)."""
    cands = [run_id]

    # 1. Toggling demand level tags
    if "_medium_" in run_id:
        for alt_lvl in ["_low_", "_heavy_", "_"]:
            cand = run_id.replace("_medium_", alt_lvl)
            if cand not in cands:
                cands.append(cand)
    elif "_low_" in run_id:
        for alt_lvl in ["_medium_", "_heavy_", "_"]:
            cand = run_id.replace("_low_", alt_lvl)
            if cand not in cands:
                cands.append(cand)
    elif "_heavy_" in run_id:
        for alt_lvl in ["_medium_", "_low_", "_"]:
            cand = run_id.replace("_heavy_", alt_lvl)
            if cand not in cands:
                cands.append(cand)
    else:
        # No explicit demand level tag: test inserting _medium_, _low_, _heavy_
        known_policies = [
            "hybrid_queue_adaptive",
            "queue_extension",
            "fixed_webster",
            "rl_dqn",
            "adaptive",
            "pressure",
            "fixed",
        ]
        for pol in known_policies:
            marker = f"_{pol}"
            if marker in run_id:
                for lvl in ["_medium_", "_low_", "_heavy_"]:
                    cand = run_id.replace(marker, f"{lvl}{pol}")
                    if cand not in cands:
                        cands.append(cand)
                break
    return cands



def _find_run_file(run_id: str, filename: str) -> Optional[Path]:
    """Find a specific file for a run across candidate IDs, results/runs, research, and demo-data."""
    cands = _candidate_run_ids(run_id)

    # 1. Check in results/runs/
    for cid in cands:
        cand_dir = RUNS_DIR / cid
        if cand_dir.is_dir() and (cand_dir / filename).is_file():
            return cand_dir / filename

    # 2. Check in research matrix directories
    if RESEARCH_DIR.is_dir():
        for exp_dir in RESEARCH_DIR.iterdir():
            if exp_dir.is_dir():
                runs_sub = exp_dir / "runs"
                if runs_sub.is_dir():
                    for cid in cands:
                        for prefix in ["cell_", ""]:
                            cand_dir = runs_sub / f"{prefix}{cid}"
                            if cand_dir.is_dir() and (cand_dir / filename).is_file():
                                return cand_dir / filename

    # 3. Check in frontend demo-data
    demo_runs = REPO_ROOT / "frontend" / "public" / "demo-data" / "runs"
    if demo_runs.is_dir():
        for cid in cands:
            cand_dir = demo_runs / cid
            if cand_dir.is_dir() and (cand_dir / filename).is_file():
                return cand_dir / filename

    return None


def _find_run_dir(run_id: str) -> Optional[Path]:
    """Find run directory matching run_id in results/runs/ or research matrix runs/."""
    cands = _candidate_run_ids(run_id)
    for cid in cands:
        cand_dir = RUNS_DIR / cid
        if cand_dir.is_dir():
            return cand_dir

    if RESEARCH_DIR.is_dir():
        for exp_dir in RESEARCH_DIR.iterdir():
            if exp_dir.is_dir():
                runs_sub = exp_dir / "runs"
                if runs_sub.is_dir():
                    for cid in cands:
                        for prefix in ["cell_", ""]:
                            cand_dir = runs_sub / f"{prefix}{cid}"
                            if cand_dir.is_dir():
                                return cand_dir

    demo_runs = REPO_ROOT / "frontend" / "public" / "demo-data" / "runs"
    if demo_runs.is_dir():
        for cid in cands:
            cand_dir = demo_runs / cid
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

    # 2. Check and clean stale processes, then check concurrency
    process_manager.clean_stale_processes()
    if process_manager.count_active("run") >= 2:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum concurrent runs limit reached (2). Please wait for active runs to finish.",
        )

    run_id = _derive_run_id(req)

    # 3. Prevent duplicate active runs with detailed actionable message
    if process_manager.is_running(run_id):
        if req.force:
            process_manager.cancel(run_id)
            time.sleep(0.5)
        else:
            info = process_manager.get_info(run_id)
            pid_str = f" (PID {info.proc.pid})" if info and info.proc else ""
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run '{run_id}' is already running{pid_str}. You can reconnect to monitor it in Live Twin Monitor or stop it to launch a new simulation.",
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


@router.get("/active")
def get_active_runs():
    """List all currently active simulation runs managed by the backend."""
    process_manager.clean_stale_processes()
    active = []
    with process_manager._lock:
        for run_id, info in process_manager._processes.items():
            if info.item_type == "run" and info.poll_status() == "running":
                active.append({
                    "run_id": run_id,
                    "pid": info.proc.pid if info.proc else None,
                    "started_at": info.started_at,
                    "status": "running",
                })
    return {"active_runs": active}


@router.post("/{run_id}/stop")
def stop_run(run_id: str):
    """Safely terminate an active simulation run."""
    success, msg = process_manager.cancel(run_id)
    run_dir = RUNS_DIR / run_id
    telem_file = run_dir / "telemetry.json"
    if telem_file.exists():
        try:
            with open(telem_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "stopped"
            data["updated_at"] = time.time()
            data["error"] = "Simulation stopped by user."
            with open(telem_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
    return {"run_id": run_id, "status": "stopped", "message": msg}


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
    has_timeseries = bool(_find_run_file(run_id, "timeseries.csv") or (run_dir / "timeseries.csv").exists())
    if info and info.poll_status() == "running":
        run_status = "running"
    elif has_timeseries:
        run_status = "completed"
    else:
        run_status = "failed"

    # Load metrics if available
    metrics = None
    metrics_file = _find_run_file(run_id, "metrics.json") or (run_dir / "metrics.json")
    if metrics_file and metrics_file.exists():
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
                        row_scenario = row.get("scenario")
                        row_policy = row.get("policy")
                        row_seed = row.get("seed")
                        if (
                            row.get("run_id") == run_id
                            or f"{row_scenario}_{row_policy}_s{row_seed}" == run_id
                            or f"{row_scenario}_medium_{row_policy}_s{row_seed}" == run_id
                        ):
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
    artifacts = [f.name for f in run_dir.iterdir() if f.is_file()] if run_dir.exists() else []
    for extra_file in ["timeseries.csv", "decisions.csv", "replay.json", "metrics.json"]:
        if extra_file not in artifacts and _find_run_file(run_id, extra_file):
            artifacts.append(extra_file)

    network_val = "marathahalli" if ("marathahalli" in run_id or "orr" in run_id or "varthur" in run_id) else "synthetic"
    return RunDetailResponse(
        run_id=run_id,
        status=run_status,
        network=network_val,
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
    else:
        has_ts = bool(_find_run_file(run_id, "timeseries.csv") or (run_dir / "timeseries.csv").exists())
        if has_ts:
            st = "completed"
            exit_code = 0
        elif run_dir.exists() or _find_run_dir(run_id):
            st = "failed"
            exit_code = 1
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )

    # Check telemetry for current sim_time_s
    telem_file = _find_run_file(run_id, "telemetry.json") or (run_dir / "telemetry.json")
    if telem_file and telem_file.exists():
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
    csv_path = _find_run_file(run_id, "timeseries.csv")
    if not csv_path:
        run_dir = resolve_safe_run_dir(run_id)
        if run_dir.exists() and (run_dir / "timeseries.csv").exists():
            csv_path = run_dir / "timeseries.csv"
        else:
            raise HTTPException(status_code=404, detail=f"timeseries.csv not found for run '{run_id}'.")

    points = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < offset:
                continue
            if (i - offset) % step != 0:
                continue
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
    csv_path = _find_run_file(run_id, "decisions.csv")
    if not csv_path:
        run_dir = resolve_safe_run_dir(run_id)
        if run_dir.exists() and (run_dir / "decisions.csv").exists():
            csv_path = run_dir / "decisions.csv"
        else:
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
    info = process_manager.get_info(run_id)
    telem_file = _find_run_file(run_id, "telemetry.json")
    if not telem_file:
        run_dir = resolve_safe_run_dir(run_id)
        if run_dir.exists() and (run_dir / "telemetry.json").exists():
            telem_file = run_dir / "telemetry.json"

    if not telem_file or not telem_file.exists():
        if info and info.poll_status() == "running":
            return TelemetryResponse(
                run_id=run_id,
                status="starting",
                sim_time_s=0.0,
                phase="GREEN",
                axis="NS",
                queues_m={},
                traffic_light_state="",
                updated_at=info.started_at,
                is_stale=False,
                emergency_approaching=False,
                emergency_dist_m=None,
                vehicles=[],
                approach_queues=None,
                adaptive_decision=None,
                error=None,
            )
        # Check if completed run exists (e.g. timeseries.csv or metrics.json)
        ts_file = _find_run_file(run_id, "timeseries.csv")
        metrics_file = _find_run_file(run_id, "metrics.json")
        if ts_file or metrics_file:
            sim_time_s = 2000.0
            if metrics_file:
                try:
                    with open(metrics_file, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        sim_time_s = float(m_data.get("sim_end_s", 2000.0))
                except Exception:
                    pass
            return TelemetryResponse(
                run_id=run_id,
                status="completed",
                sim_time_s=sim_time_s,
                phase="GREEN",
                axis="NS",
                queues_m={"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0},
                traffic_light_state="GGggrrrrGGggrrrr",
                updated_at=time.time(),
                is_stale=True,
                emergency_approaching=False,
                emergency_dist_m=None,
                vehicles=[],
                approach_queues=None,
                adaptive_decision=None,
                error=None,
            )
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    data = None
    for _ in range(4):
        try:
            with open(telem_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data and "status" in data:
                break
        except (PermissionError, json.JSONDecodeError, OSError):
            time.sleep(0.04)
        except Exception:
            time.sleep(0.04)

    if data is None:
        if info and info.poll_status() == "running":
            return TelemetryResponse(
                run_id=run_id,
                status="running",
                sim_time_s=0.0,
                phase="GREEN",
                axis="NS",
                queues_m={},
                traffic_light_state="GGggrrrrGGggrrrr",
                updated_at=time.time(),
                is_stale=False,
                emergency_approaching=False,
                emergency_dist_m=None,
                vehicles=[],
                approach_queues=None,
                adaptive_decision=None,
                error=None,
            )
        data = {"status": "completed", "sim_time_s": 2000.0, "phase": "GREEN", "axis": "NS", "queues_m": {}}

    updated_at = float(data.get("updated_at", 0))
    is_stale = (time.time() - updated_at) > TELEMETRY_STALE_THRESHOLD_S

    status_str = data.get("status", "unknown")
    if info and info.poll_status() != "running" and status_str == "running":
        status_str = info.poll_status()

    tl_state = data.get("traffic_light_state", "")
    if not tl_state:
        tl_state = "GGggrrrrGGggrrrr" if data.get("phase") == "GREEN" else "yyyyrrrryyyyrrrr"

    return TelemetryResponse(
        run_id=data.get("run_id", run_id),
        status=status_str,
        sim_time_s=float(data.get("sim_time_s", 0.0)),
        phase=data.get("phase", "GREEN"),
        axis=data.get("axis", "NS"),
        queues_m=data.get("queues_m", {}),
        traffic_light_state=tl_state,
        updated_at=updated_at,
        is_stale=is_stale,
        emergency_approaching=bool(data.get("emergency_approaching", False)),
        emergency_dist_m=data.get("emergency_dist_m"),
        vehicles=data.get("vehicles") or [],
        approach_queues=data.get("approach_queues"),
        adaptive_decision=data.get("adaptive_decision"),
        error=data.get("error"),
    )


@router.get("/{run_id}/replay", response_model=ReplayResponse)
def get_replay(run_id: str):
    """Retrieve full microscopic vehicle replay data for a run."""
    replay_file = _find_run_file(run_id, "replay.json")
    if replay_file and replay_file.exists():
        try:
            with open(replay_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("network"):
                if "marathahalli" in str(replay_file) or "orr" in data.get("scenario", ""):
                    data["network"] = "marathahalli"
                else:
                    data["network"] = "synthetic"
            return ReplayResponse(**data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read replay data: {e}")

    # Fallback: synthesize lightweight replay from timeseries.csv
    ts_file = _find_run_file(run_id, "timeseries.csv")
    if ts_file and ts_file.exists():
        try:
            frames = []
            with open(ts_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    em_app = str(row.get("emergency_approaching", "False")).lower() == "true"
                    em_dist = float(row["emergency_dist_m"]) if row.get("emergency_dist_m") else None
                    frames.append({
                        "t": float(row.get("t", len(frames))),
                        "phase": row.get("phase", "GREEN"),
                        "axis": row.get("axis", "NS"),
                        "tl_state": row.get("state", "GGggrrrrGGggrrrr"),
                        "queues_m": {
                            "N": float(row.get("q_N", 0.0)),
                            "S": float(row.get("q_S", 0.0)),
                            "E": float(row.get("q_E", 0.0)),
                            "W": float(row.get("q_W", 0.0)),
                        },
                        "emergency_approaching": em_app,
                        "emergency_dist_m": em_dist,
                        "vehicles": [],
                    })
            network_type = "marathahalli" if ("marathahalli" in run_id or "orr" in run_id or "varthur" in run_id) else "synthetic"
            return ReplayResponse(
                run_id=run_id,
                network=network_type,
                scenario="imbalanced_orr" if "orr" in run_id else "imbalanced_ns",
                policy="adaptive",
                seed=121,
                demand_level="medium",
                emergency_event=False,
                emergency_priority=False,
                total_vehicles=len(frames),
                duration_s=frames[-1]["t"] if frames else 0.0,
                frame_count=len(frames),
                step_s=1.0,
                frames=frames,
            )
        except Exception:
            pass

    raise HTTPException(
        status_code=404,
        detail=f"Replay not available for run '{run_id}'. Run may need replay generation.",
    )
