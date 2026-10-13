"""Pydantic schemas for DP1 API requests and responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Health & Summary
# ---------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok', 'degraded', or 'unavailable'")
    sumo_available: bool = Field(..., description="Whether SUMO binary was found and works")
    sumo_binary: Optional[str] = Field(None, description="Path to discovered SUMO binary")
    sumo_version: Optional[str] = Field(None, description="Discovered SUMO version string")
    python_version: str = Field(..., description="Python runtime version")
    results_writable: bool = Field(..., description="Whether results directory is writable")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic details")


class SummaryResponse(BaseModel):
    total_runs: int
    total_experiments: int
    scenarios: List[str]
    policies: List[str]
    demand_levels: List[str]
    latest_runs: List[Dict[str, Any]]


# ---------------------------------------------------------
# Simulation Runs
# ---------------------------------------------------------

class RunLaunchRequest(BaseModel):
    scenario: str = Field(..., description="Scenario name from allowlist")
    policy: str = Field(..., description="Policy name from allowlist")
    seed: int = Field(1, description="Simulation random seed")
    demand_level: str = Field("medium", description="Demand level: low, medium, heavy")
    emergency_event: bool = Field(False, description="Insert emergency vehicle")
    emergency_priority: bool = Field(False, description="Enable emergency signal priority")
    emergency_approach: str = Field("N", description="Approach for emergency: N, S, E, W")
    emergency_depart: float = Field(300.0, description="Emergency departure time (seconds)")
    model_path: Optional[str] = Field(None, description="Path to trained RL model for rl_dqn")
    gui: bool = Field(False, description="Launch in sumo-gui (local desktop only)")


class RunStatusResponse(BaseModel):
    run_id: str
    status: str = Field(..., description="'queued', 'running', 'completed', 'failed'")
    exit_code: Optional[int] = None
    sim_time_s: Optional[float] = None
    message: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class RunDetailResponse(BaseModel):
    run_id: str
    status: str
    scenario: Optional[str] = None
    policy: Optional[str] = None
    seed: Optional[int] = None
    demand_level: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    available_artifacts: List[str] = Field(default_factory=list)


class TimeseriesResponse(BaseModel):
    run_id: str
    total_points: int
    points: List[Dict[str, Any]]


class DecisionsResponse(BaseModel):
    run_id: str
    total_decisions: int
    decisions: List[Dict[str, Any]]


class TelemetryResponse(BaseModel):
    run_id: str
    status: str
    sim_time_s: float
    phase: str
    axis: str
    queues_m: Dict[str, float]
    traffic_light_state: str
    updated_at: float
    is_stale: bool
    emergency_approaching: bool = False
    emergency_dist_m: Optional[float] = None
    vehicles: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ReplayResponse(BaseModel):
    run_id: str
    scenario: str
    policy: str
    seed: int
    demand_level: str
    emergency_event: bool
    emergency_priority: bool
    total_vehicles: int
    duration_s: float
    frame_count: int
    step_s: float
    frames: List[Dict[str, Any]]


# ---------------------------------------------------------
# Research Experiments
# ---------------------------------------------------------

class ExperimentLaunchRequest(BaseModel):
    preset: str = Field("smoke", description="Preset: full, smoke, custom")
    patterns: Optional[List[str]] = Field(None, description="Scenario patterns")
    levels: Optional[List[str]] = Field(None, description="Demand levels (low, medium, heavy)")
    policies: Optional[List[str]] = Field(None, description="Policies to evaluate")
    seeds: Optional[List[int]] = Field(None, description="Seeds to evaluate")
    limit: Optional[int] = Field(None, description="Limit max matrix cells")
    jobs: int = Field(1, description="Parallel worker processes (max 8)")
    emergency_matrix: bool = Field(False, description="Emergency matrix sub-study")
    model_path: Optional[str] = Field(None, description="RL model path for rl_dqn")
    experiment_id: Optional[str] = Field(None, description="Custom experiment ID (alphanumeric)")


class ExperimentStatusResponse(BaseModel):
    experiment_id: str
    status: str = Field(..., description="'queued', 'running', 'complete', 'failed', 'cancelled'")
    total_cells: int
    pending: int = 0
    running: int = 0
    complete: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0
    exit_code: Optional[int] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class ExperimentDetailResponse(BaseModel):
    experiment_id: str
    status: str
    manifest: Optional[Dict[str, Any]] = None
    available_artifacts: List[str] = Field(default_factory=list)


class ExperimentResultsResponse(BaseModel):
    experiment_id: str
    aggregate: List[Dict[str, Any]] = Field(default_factory=list)
    raw_runs: List[Dict[str, Any]] = Field(default_factory=list)


class ArtifactItem(BaseModel):
    name: str
    size_bytes: int
    modified_at: float
    download_url: str


class ArtifactsListResponse(BaseModel):
    experiment_id: str
    artifacts: List[ArtifactItem]
