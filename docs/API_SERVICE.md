# DP1 API Service & Live Telemetry Architecture (Phase P5A)

The DP1 API Service is a thin, decoupled adapter over the SUMO traffic simulation engine and research experiment pipeline. It does **not** reimplement the simulation physics or traffic controllers.

---

## 1. Local Run & Development

### 1.1 Prerequisites
- Python 3.10+
- Eclipse SUMO 1.20+ (with `SUMO_HOME` set in environment and `sumo` binary on `PATH`)
- Install API dependencies:
  ```powershell
  pip install -r requirements-api.txt
  ```

### 1.2 Running the API Service
You can start the server via Python module or directly using `uvicorn`:
```powershell
# Using the backend runner:
python -m backend

# Or via uvicorn directly:
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation is automatically available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 2. API Contract & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | System health check (truthfully returns `503` if SUMO is missing) | No |
| `GET` | `/api/summary` | Summary counts of runs, experiments, and parameter allowlists | No |
| `POST` | `/api/runs` | Launch a validated simulation run in a managed subprocess | Yes (if configured) |
| `GET` | `/api/runs/{run_id}` | Retrieve run metrics, status, and artifact inventory | No |
| `GET` | `/api/runs/{run_id}/status` | Execution status and exit code | No |
| `GET` | `/api/runs/{run_id}/telemetry` | Live atomic telemetry with automatic staleness detection | No |
| `GET` | `/api/runs/{run_id}/timeseries` | Second-by-second queues and signal states (supports pagination) | No |
| `GET` | `/api/runs/{run_id}/decisions` | Cycle decisions (queue per approach -> green duration) | No |
| `GET` | `/api/experiments` | List all research experiments in `results/research/` | No |
| `POST` | `/api/experiments` | Launch research evaluation matrix (`full`, `smoke`, `custom`) | Yes (if configured) |
| `GET` | `/api/experiments/{experiment_id}` | Experiment details and manifest | No |
| `GET` | `/api/experiments/{experiment_id}/status` | Cell progress counts (`pending`, `running`, `complete`, etc.) | No |
| `GET` | `/api/experiments/{experiment_id}/results` | Aggregate and raw run records | No |
| `GET` | `/api/experiments/{experiment_id}/artifacts` | Allowlisted downloadable artifact metadata | No |
| `GET` | `/api/experiments/{experiment_id}/artifacts/{artifact_name}` | Download allowlisted report or CSV artifact | No |
| `POST` | `/api/experiments/{experiment_id}/cancel` | Safely terminate active research matrix process | Yes (if configured) |

---

## 3. Security Measures

1. **Strict Path Traversal Guards:**
   - All `run_id` and `experiment_id` parameters are validated against `^[a-zA-Z0-9_-]+$`.
   - Filepaths are resolved strictly relative to `results/runs/` and `results/research/` using `pathlib.Path.is_relative_to()`. Any dot-dot (`..`) or traversal attempts return `400 Bad Request`.
2. **Artifact Allowlist:**
   - Artifact downloads only serve pre-approved filenames: `report.md`, `manifest.json`, `aggregate.csv`, `raw_runs.csv`, `paired_deltas.csv`, `fairness_by_approach.csv`, `fairness_by_direction.csv`, `matrix_status.csv`. Arbitrary file paths or script files cannot be accessed.
3. **No Shell Execution:**
   - Subprocesses are spawned exclusively via `sys.executable` with argument lists. `shell=True` is forbidden across all invocations.
4. **Token Authentication on Mutating Endpoints:**
   - Configure `DP1_AUTH_TOKEN` or `DP1_API_KEY` in environment.
   - If set, `POST /api/runs`, `POST /api/experiments`, and `POST /api/experiments/{id}/cancel` require `Authorization: Bearer <token>` or header `X-API-Key: <token>`. Returns `401 Unauthorized` if omitted or invalid.
5. **Exact CORS Configuration:**
   - Configured via `DP1_CORS_ORIGINS` (comma-separated). Defaults strictly to local frontend dev servers (`http://localhost:5173`, `http://localhost:3000`).

---

## 4. Live Atomic Telemetry

During active simulations, `dp1/runner.py` writes simulation telemetry at step 0, on each simulation second, and at completion or failure:
- **Atomicity:** Written to `telemetry.json.tmp` and swapped via `os.replace` to eliminate race conditions and partial file reads.
- **Staleness Detection:** Includes `updated_at` unix timestamp. The API compares `time.time() - updated_at > 5.0s`. If stale, `is_stale: true` is returned and process status is verified.

---

## 5. Deployment Requirements

> [!IMPORTANT]
> **Vercel Frontend vs Simulation Host:**
> Vercel hosts only the static React/Vite dashboard. Vercel serverless functions **cannot** run Eclipse SUMO. The API service must run on a dedicated host/container with SUMO installed.

### Docker / VM Container Requirements:
1. **Operating System:** Linux (Ubuntu 22.04 LTS recommended) or Windows Server.
2. **Dependencies:**
   - Python 3.10+
   - Eclipse SUMO: `apt-get install sumo sumo-tools`
   - `SUMO_HOME` environment variable pointing to SUMO installation (e.g., `/usr/share/sumo`).
3. **Storage & Persistence:**
   - Persistent volume mounted at `/app/results` so simulation runs, checkpoints, and research evaluations survive container restarts.
4. **Network:**
   - Expose port `8000` (or reverse proxy behind NGINX / Caddy with HTTPS).
   - Configure `DP1_CORS_ORIGINS` with the production Vercel frontend domain.
