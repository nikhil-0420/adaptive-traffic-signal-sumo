"""Backend configuration, path resolution, and allowlists for DP1 API."""
import os
from pathlib import Path
from typing import List, Optional

from dp1 import config as C

# Host and Port
API_HOST: str = os.getenv("DP1_API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("DP1_API_PORT", "8000"))

# Allowed CORS origins
DEFAULT_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_cors = os.getenv("DP1_CORS_ORIGINS")
if env_cors:
    CORS_ORIGINS: List[str] = [orig.strip() for orig in env_cors.split(",") if orig.strip()]
else:
    CORS_ORIGINS: List[str] = DEFAULT_CORS

# Optional token authentication (if set, mutating endpoints require Bearer or X-API-Key)
API_AUTH_TOKEN: Optional[str] = os.getenv("DP1_AUTH_TOKEN") or os.getenv("DP1_API_KEY") or None

# Directory paths (resolved strictly relative to REPO_ROOT)
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
RESULTS_DIR: Path = REPO_ROOT / "results"
RUNS_DIR: Path = RESULTS_DIR / "runs"
RESEARCH_DIR: Path = RESULTS_DIR / "research"
MODELS_DIR: Path = RESULTS_DIR / "models"

# Ensure essential directories exist
RUNS_DIR.mkdir(parents=True, exist_ok=True)
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

# Allowlist definitions
ALLOWED_SCENARIOS = list(C.scenarios())
ALLOWED_POLICIES = ["fixed", "fixed_webster", "adaptive", "pressure", "queue_extension", "rl_dqn"]
ALLOWED_DEMAND_LEVELS = ["low", "medium", "heavy"]
ALLOWED_PRESETS = ["full", "smoke", "custom"]
ALLOWED_EMERGENCY_APPROACHES = ["N", "S", "E", "W"]

# Allowed research artifacts that can be downloaded / viewed
ALLOWED_RESEARCH_ARTIFACTS = {
    "report.md",
    "manifest.json",
    "aggregate.csv",
    "raw_runs.csv",
    "paired_deltas.csv",
    "fairness_by_approach.csv",
    "fairness_by_direction.csv",
    "matrix_status.csv",
}

# Telemetry staleness threshold (seconds)
TELEMETRY_STALE_THRESHOLD_S: float = 5.0
