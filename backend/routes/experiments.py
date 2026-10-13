"""Research experiments management and artifacts routes."""
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..config import (
    ALLOWED_DEMAND_LEVELS,
    ALLOWED_POLICIES,
    ALLOWED_PRESETS,
    ALLOWED_RESEARCH_ARTIFACTS,
    ALLOWED_SCENARIOS,
    RESEARCH_DIR,
)
from ..process_manager import process_manager
from ..schemas import (
    ArtifactItem,
    ArtifactsListResponse,
    ExperimentDetailResponse,
    ExperimentLaunchRequest,
    ExperimentResultsResponse,
    ExperimentStatusResponse,
)
from ..security import (
    resolve_safe_experiment_artifact,
    resolve_safe_experiment_dir,
    validate_identifier,
    verify_auth_token,
)

router = APIRouter(prefix="/experiments", tags=["Research Experiments"])


def _parse_csv_records(file_path: Path) -> List[Dict[str, Any]]:
    """Helper to parse CSV records converting numeric types and empty strings to None."""
    records = []
    if not file_path.exists():
        return records

    try:
        with open(file_path, "r", encoding="utf-8") as f:
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
                            if v.lower() == "true":
                                rec[k] = True
                            elif v.lower() == "false":
                                rec[k] = False
                            else:
                                rec[k] = v
                records.append(rec)
    except Exception:
        pass
    return records


@router.get("", response_model=List[Dict[str, Any]])
def list_experiments():
    """List all available research experiments and their summary metadata."""
    if not RESEARCH_DIR.exists():
        return []

    experiments = []
    for d in sorted(RESEARCH_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        exp_id = d.name
        manifest_file = d / "manifest.json"
        manifest_data = {}
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception:
                pass

        status_str = manifest_data.get("status", "unknown")
        info = process_manager.get_info(exp_id)
        if info and info.poll_status() == "running":
            status_str = "running"
        elif (d / "report.md").exists() or (d / "aggregate.csv").exists():
            status_str = "complete"

        experiments.append({
            "experiment_id": exp_id,
            "status": status_str,
            "preset": manifest_data.get("preset"),
            "total_cells": manifest_data.get("total_cells"),
            "created_at": manifest_data.get("created_at"),
            "modified_at": d.stat().st_mtime,
        })
    return experiments


@router.post("", response_model=ExperimentStatusResponse, status_code=status.HTTP_201_CREATED)
def launch_experiment(
    req: ExperimentLaunchRequest,
    _auth: bool = Depends(verify_auth_token),
):
    """Validate research matrix request and launch evaluation in managed subprocess."""
    # 1. Validation
    if req.preset not in ALLOWED_PRESETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid preset '{req.preset}'. Allowed: {ALLOWED_PRESETS}",
        )
    if req.patterns:
        for p in req.patterns:
            if p not in ALLOWED_SCENARIOS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid pattern '{p}'. Allowed: {ALLOWED_SCENARIOS}",
                )
    if req.levels:
        for l in req.levels:
            if l not in ALLOWED_DEMAND_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid demand level '{l}'. Allowed: {ALLOWED_DEMAND_LEVELS}",
                )
    if req.policies:
        for pol in req.policies:
            if pol not in ALLOWED_POLICIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid policy '{pol}'. Allowed: {ALLOWED_POLICIES}",
                )
    if req.jobs < 1 or req.jobs > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker jobs must be between 1 and 8.",
        )

    # 2. Concurrency limit (max 1 research experiment simultaneously)
    if process_manager.count_active("experiment") >= 1:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Another research experiment is currently executing. Concurrency is limited to 1.",
        )

    # 3. Derive or validate experiment ID
    if req.experiment_id:
        exp_id = validate_identifier(req.experiment_id, "experiment_id")
    else:
        exp_id = f"exp_{time.strftime('%Y%m%d_%H%M%S')}"

    if process_manager.is_running(exp_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Experiment '{exp_id}' is already running.",
        )

    # 4. Launch subprocess
    success, msg = process_manager.launch_experiment(
        experiment_id=exp_id,
        preset=req.preset,
        patterns=req.patterns,
        levels=req.levels,
        policies=req.policies,
        seeds=req.seeds,
        limit=req.limit,
        jobs=req.jobs,
        emergency_matrix=req.emergency_matrix,
        model_path=req.model_path,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )

    return ExperimentStatusResponse(
        experiment_id=exp_id,
        status="running",
        total_cells=0,
        pending=0,
        running=0,
        complete=0,
        started_at=time.time(),
    )


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
def get_experiment(experiment_id: str):
    """Retrieve details and manifest for an experiment."""
    exp_dir = resolve_safe_experiment_dir(experiment_id)
    if not exp_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )

    manifest = None
    manifest_file = exp_dir / "manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    info = process_manager.get_info(experiment_id)
    if info and info.poll_status() == "running":
        exp_status = "running"
    elif manifest and "status" in manifest:
        exp_status = manifest["status"]
    elif (exp_dir / "aggregate.csv").exists():
        exp_status = "complete"
    else:
        exp_status = "unknown"

    artifacts = [f.name for f in exp_dir.iterdir() if f.is_file() and f.name in ALLOWED_RESEARCH_ARTIFACTS]

    return ExperimentDetailResponse(
        experiment_id=experiment_id,
        status=exp_status,
        manifest=manifest,
        available_artifacts=artifacts,
    )


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
def get_experiment_status(experiment_id: str):
    """Retrieve real-time execution status and cell progress counts."""
    exp_dir = resolve_safe_experiment_dir(experiment_id)
    info = process_manager.get_info(experiment_id)

    if not exp_dir.exists() and not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )

    status_str = "unknown"
    exit_code = None
    started_at = None
    finished_at = None

    if info:
        status_str = info.poll_status()
        exit_code = info.exit_code
        started_at = info.started_at
        finished_at = info.finished_at

    # Read matrix_status.csv for granular cell progress
    status_csv = exp_dir / "matrix_status.csv"
    counts = {"pending": 0, "running": 0, "complete": 0, "failed": 0, "blocked": 0, "skipped": 0}
    total_cells = 0

    if status_csv.exists():
        try:
            with open(status_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_cells += 1
                    c_status = row.get("status", "pending")
                    if c_status in counts:
                        counts[c_status] += 1
        except Exception:
            pass
    else:
        # Check manifest.json if matrix_status.csv not yet written
        manifest_file = exp_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    m = json.load(f)
                    total_cells = m.get("total_cells", 0)
                    m_counts = m.get("status_counts", {})
                    for k in counts:
                        counts[k] = m_counts.get(k, 0)
                    if not info:
                        status_str = m.get("status", status_str)
            except Exception:
                pass

    if not info and status_str == "unknown":
        if (exp_dir / "aggregate.csv").exists():
            status_str = "complete"
            counts["complete"] = total_cells
        else:
            status_str = "pending"

    return ExperimentStatusResponse(
        experiment_id=experiment_id,
        status=status_str,
        total_cells=total_cells,
        pending=counts["pending"],
        running=counts["running"],
        complete=counts["complete"],
        failed=counts["failed"],
        blocked=counts["blocked"],
        skipped=counts["skipped"],
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
    )


@router.get("/{experiment_id}/results", response_model=ExperimentResultsResponse)
def get_experiment_results(experiment_id: str):
    """Retrieve aggregate and raw run data from research matrix evaluation."""
    exp_dir = resolve_safe_experiment_dir(experiment_id)
    if not exp_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )

    aggregate = _parse_csv_records(exp_dir / "aggregate.csv")
    raw_runs = _parse_csv_records(exp_dir / "raw_runs.csv")

    if not aggregate and not raw_runs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results not available yet for experiment '{experiment_id}'.",
        )

    return ExperimentResultsResponse(
        experiment_id=experiment_id,
        aggregate=aggregate,
        raw_runs=raw_runs,
    )


@router.get("/{experiment_id}/artifacts", response_model=ArtifactsListResponse)
def list_experiment_artifacts(experiment_id: str):
    """List all allowed experiment output artifacts available for download."""
    exp_dir = resolve_safe_experiment_dir(experiment_id)
    if not exp_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )

    items = []
    for f in exp_dir.iterdir():
        if f.is_file() and f.name in ALLOWED_RESEARCH_ARTIFACTS:
            stat = f.stat()
            items.append(ArtifactItem(
                name=f.name,
                size_bytes=stat.st_size,
                modified_at=stat.st_mtime,
                download_url=f"/api/experiments/{experiment_id}/artifacts/{f.name}",
            ))

    return ArtifactsListResponse(
        experiment_id=experiment_id,
        artifacts=items,
    )


@router.get("/{experiment_id}/artifacts/{artifact_name}")
def download_experiment_artifact(experiment_id: str, artifact_name: str):
    """Download an allowlisted research artifact with path traversal prevention."""
    file_path = resolve_safe_experiment_artifact(experiment_id, artifact_name)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_name}' not found in experiment '{experiment_id}'.",
        )

    media_type = "text/plain"
    if artifact_name.endswith(".csv"):
        media_type = "text/csv"
    elif artifact_name.endswith(".json"):
        media_type = "application/json"
    elif artifact_name.endswith(".md"):
        media_type = "text/markdown"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=artifact_name,
    )


@router.post("/{experiment_id}/cancel")
def cancel_experiment(
    experiment_id: str,
    _auth: bool = Depends(verify_auth_token),
):
    """Safely cancel an active research experiment process."""
    validate_identifier(experiment_id, "experiment_id")
    success, msg = process_manager.cancel(experiment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )
    return {"experiment_id": experiment_id, "message": msg, "status": "cancelled"}
