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
    network: str = Field("synthetic", description="Network topology: synthetic or marathahalli")
    emergency_event: bool = Field(False, description="Insert emergency vehicle")
    emergency_priority: bool = Field(False, description="Enable emergency signal priority")
    emergency_approach: str = Field("N", description="Approach for emergency: N, S, E, W")
    emergency_depart: float = Field(300.0, description="Emergency departure time (seconds)")
    model_path: Optional[str] = Field(None, description="Path to trained RL model for rl_dqn")
    gui: bool = Field(False, description="Launch in sumo-gui (local desktop only)")
    force: bool = Field(False, description="Force cancel and restart if run already active")


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
    network: Optional[str] = "synthetic"
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
    policy_provenance: Optional[str] = Field("MEASURED", description="Policy provenance: MEASURED, ORACLE, ORACLE-SEEDED, or LEARNED")
    decisions: List[Dict[str, Any]]


class AdaptiveDecisionSchema(BaseModel):
    t: float = Field(..., description="Simulation time in seconds")
    cycle: int = Field(..., description="Signal cycle number")
    axis: str = Field(..., description="Active axis: NS or EW")
    proposed_action: Optional[str] = Field(None, description="Proposed action: e.g. EXTEND, HOLD, GAP_OUT, ENTER_GREEN")
    applied_action: Optional[str] = Field(None, description="Actual applied action: e.g. EXTEND, REQUEST_SWITCH, HOLD, ENTER_GREEN")
    decision_outcome: Optional[str] = Field(None, description="Decision outcome: e.g. EXTEND_APPROVED, SWITCH_FAIRNESS_WAIT_LIMIT")
    action: str = Field(..., description="Backwards-compatible applied action (never EXTEND if rejected)")
    reason: str = Field(..., description="Human-readable decision explanation")
    reason_code: str = Field(..., description="Deterministic machine-readable reason code")
    g_base_s: float = Field(..., description="Webster baseline green duration in seconds")
    delta_g_req_s: float = Field(0.0, description="Requested green increment in seconds")
    delta_g_app_s: float = Field(0.0, description="Applied green increment in seconds")
    g_extra_s: float = Field(0.0, description="Accumulated extra green seconds granted so far")
    target_green_s: float = Field(..., description="Target green duration including accumulated extra")
    elapsed_s: float = Field(..., description="Green service duration elapsed at evaluation")
    actual_green_s: Optional[float] = Field(None, description="Total green duration served upon phase termination")
    q_active_m: float = Field(..., description="Active approach queue in metres")
    q_competing_m: float = Field(..., description="Competing approach queue in metres")
    score_active: float = Field(..., description="Calculated demand score for active axis")
    score_competing: float = Field(..., description="Calculated demand score for competing axis")
    is_max_green: bool = Field(False, description="Whether max green ceiling was reached")
    policy_provenance: Optional[str] = Field("MEASURED", description="Policy provenance: MEASURED, ORACLE, ORACLE-SEEDED, or LEARNED")


class VehicleTelemetryItem(BaseModel):
    id: str = Field(..., description="Vehicle unique identifier")
    x: float = Field(..., description="SUMO X coordinate (east-west metres)")
    y: float = Field(..., description="SUMO Y coordinate (north-south metres)")
    z: float = Field(0.0, description="SUMO Z coordinate (elevation metres)")
    a: float = Field(..., description="Vehicle heading angle in degrees")
    s: float = Field(..., description="Vehicle speed in m/s")
    w: Optional[float] = Field(None, description="Accumulated waiting time in seconds")
    em: bool = Field(False, description="Emergency vehicle flag")


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
    vehicles: Optional[List[VehicleTelemetryItem]] = None
    approach_queues: Optional[Dict[str, Any]] = None
    adaptive_decision: Optional[Dict[str, Any]] = None
    gt_ext_q_N: Optional[float] = Field(None, description="Extended ground-truth queue length (m) on North approach")
    gt_ext_q_S: Optional[float] = Field(None, description="Extended ground-truth queue length (m) on South approach")
    gt_ext_q_E: Optional[float] = Field(None, description="Extended ground-truth queue length (m) on East approach")
    gt_ext_q_W: Optional[float] = Field(None, description="Extended ground-truth queue length (m) on West approach")
    det_full_N: Optional[bool] = Field(None, description="Detector saturation flag on North approach")
    det_full_S: Optional[bool] = Field(None, description="Detector saturation flag on South approach")
    det_full_E: Optional[bool] = Field(None, description="Detector saturation flag on East approach")
    det_full_W: Optional[bool] = Field(None, description="Detector saturation flag on West approach")
    reason_code: Optional[str] = Field(None, description="Machine-readable decision reason code")
    delta_g_req_s: Optional[float] = Field(None, description="Requested green time increment (s)")
    delta_g_app_s: Optional[float] = Field(None, description="Applied green time increment (s)")
    policy_provenance: Optional[str] = Field("MEASURED", description="Policy provenance: MEASURED, ORACLE, ORACLE-SEEDED, or LEARNED")
    error: Optional[str] = None


class ReplayResponse(BaseModel):
    run_id: str
    network: Optional[str] = "synthetic"
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
    network: str = Field("synthetic", description="Network topology: synthetic or marathahalli")
    patterns: Optional[List[str]] = Field(None, description="Scenario patterns")
    levels: Optional[List[str]] = Field(None, description="Demand levels (low, medium, heavy)")
    policies: Optional[List[str]] = Field(None, description="Policies to evaluate")
    seeds: Optional[List[int]] = Field(None, description="Seeds to evaluate")
    limit: Optional[int] = Field(None, description="Limit max matrix cells")
    jobs: int = Field(1, description="Parallel worker processes (max 8)")
    emergency_matrix: bool = Field(False, description="Emergency matrix sub-study")
    model_path: Optional[str] = Field(None, description="RL model path for rl_dqn")
    experiment_id: Optional[str] = Field(None, description="Custom experiment ID (alphanumeric)")


class SiteModelResponse(BaseModel):
    network_id: str
    name: str
    location: str
    description: str
    grounding_sources: List[Dict[str, str]]
    grade_separation: Dict[str, Any]
    surface_junction: Dict[str, Any]
    provenance_table: List[Dict[str, str]]
    topology_image_url: str
    sumo_gui_image_url: str
    geometry_extents: Optional[Dict[str, Any]] = None


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
