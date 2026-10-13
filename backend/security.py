"""Security utilities: ID validation, path traversal guards, and token authentication."""
import re
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, Header, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import (
    ALLOWED_RESEARCH_ARTIFACTS,
    API_AUTH_TOKEN,
    RESEARCH_DIR,
    RUNS_DIR,
)

# Strict identifier pattern: only alphanumeric, underscore, hyphen
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

bearer_scheme = HTTPBearer(auto_error=False)


def validate_identifier(item_id: str, id_name: str = "ID") -> str:
    """Validate that an identifier contains only safe alphanumeric/hyphen/underscore characters."""
    if not item_id or not SAFE_ID_PATTERN.match(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {id_name}: '{item_id}'. Allowed characters are alphanumeric, hyphen, and underscore.",
        )
    return item_id


def resolve_safe_run_dir(run_id: str) -> Path:
    """Resolve a run directory safely under results/runs/. Prevent any path traversal."""
    valid_id = validate_identifier(run_id, "run_id")
    target = (RUNS_DIR / valid_id).resolve()
    base = RUNS_DIR.resolve()

    if not target.is_relative_to(base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected.",
        )
    return target


def resolve_safe_experiment_dir(experiment_id: str) -> Path:
    """Resolve an experiment directory safely under results/research/. Prevent any path traversal."""
    valid_id = validate_identifier(experiment_id, "experiment_id")
    target = (RESEARCH_DIR / valid_id).resolve()
    base = RESEARCH_DIR.resolve()

    if not target.is_relative_to(base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected.",
        )
    return target


def resolve_safe_experiment_artifact(experiment_id: str, artifact_name: str) -> Path:
    """Resolve an allowlisted experiment artifact file. Rejects traversal or non-allowlisted files."""
    exp_dir = resolve_safe_experiment_dir(experiment_id)

    # Check against allowlist
    if artifact_name not in ALLOWED_RESEARCH_ARTIFACTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Artifact '{artifact_name}' is not in the allowed artifacts list.",
        )

    target_file = (exp_dir / artifact_name).resolve()
    if not target_file.is_relative_to(exp_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected.",
        )

    return target_file


async def verify_auth_token(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Verify API authentication token on mutating endpoints if configured."""
    if not API_AUTH_TOKEN:
        return True  # Auth not required in local development mode without configured key

    provided_token = None
    if auth_header and auth_header.credentials:
        provided_token = auth_header.credentials
    elif x_api_key:
        provided_token = x_api_key

    if not provided_token or provided_token != API_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid API authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
