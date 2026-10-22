# Changelog

## v1.2 - Phase 7B: Marathahalli Real-Road Site Network Integration, Site Matrix & Emergency Evaluation
- Integrated the approved Marathahalli Bridge reconstructed SUMO network (`--network marathahalli`) without altering the synthetic baseline (`--network synthetic`).
- Executed the full Phase B Site Research Matrix (`exp_marathahalli_site`, 600 runs, 100% complete):
  - Benchmarked 5 control policies (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`) across 4 site demand patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`) and 3 demand levels (`low`, `medium`, `heavy`) on held-out seeds 121..130.
  - Calculated 95% bootstrap percentile confidence intervals ($B=10,000$), paired deltas vs baseline fixed timing, and corridor direction disparity.
  - Key finding: In `imbalanced_varthur` heavy demand, `rl_dqn` delivered mean delay reduction of -7.32s (95% CI: [-13.16s, -1.90s]); `adaptive` delivered -5.49s (95% CI: [-10.15s, -0.94s]).
- Executed Marathahalli Site Emergency Matrix (`exp_marathahalli_emergency_360`, 360 runs) evaluating ambulance travel time and background traffic delay impacts.
- Extended FastAPI Backend:
  - Added `ALLOWED_NETWORKS = ["synthetic", "marathahalli"]` and Marathahalli demand scenarios to `backend/config.py`.
  - Added dedicated endpoint `GET /api/site-model` returning 3-tier grade separation details, 16-link phase machine schema, E2 detector telemetry, and provenance matrix.
  - Extended run launcher and experiment launcher to support `--network`.
- Extended React + Vite Frontend Dashboard:
  - Created `SiteModelView.jsx` featuring tabs for Topology Schematic & SUMO GUI renders, 3-Tier Grade Separation breakdown (Elevated Flyover, Grade Mainline, Surface Signal), Phasing Machine & Detectors, and Verification/Provenance Matrix.
  - Added `Site Model` navigation item to `Navbar.jsx` with active route handling in `App.jsx`.
  - Added Network Architecture toggles to `LiveMonitorView.jsx` and `ResearchView.jsx` allowing users to switch between Synthetic 4-Way and Marathahalli Bridge Site.
  - Exported site experiment artifacts (`aggregate.json`, `raw_runs.json`, `matrix_status.json`, `fairness_by_approach.json`, `paired_deltas.json`, `manifest.json`, `report.md`) to `frontend/public/demo-data/experiments/exp_marathahalli_site/` for offline/Vercel demonstration.
- Added comprehensive unit tests in `tests/test_marathahalli_network.py` verifying `/api/site-model`, site research matrix generator, and emergency configuration.
- Validated via `pytest -q` (all tests passing green) and frontend `npm test` (7/7 passed) + `npm run build` (production Vite build cleanly generated).

## v1.1 - Phase P6: Final reproducibility freeze, 5-controller matrix verification, and demo freeze
- Ran end-to-end verification gate across entire stack:
  - Complete Python test suite: 66/66 passed (`pytest -q`), covering safety invariants, clearance timing, controllers, RL environment, emergency preemption, FastAPI security, and research matrix statistics.
  - Frontend unit tests: 7/7 passed (`npm test` in `frontend/`), validating snapshot schema, manifest integrity, null metrics handling, and staleness detection.
  - Frontend production bundle: built cleanly via Vite (`npm run build`, 5.7s).
- Executed research evaluation matrix across research test seeds 21 and 22 (`exp_p6_validation`):
  - Benchmarked all 5 controllers (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`) under identical arrival traffic.
  - Produced real research artifacts in `results/research/exp_p6_validation/`: `manifest.json`, `matrix_status.csv`, `raw_runs.csv`, `aggregate.csv`, `paired_deltas.csv` with 95% bootstrap CIs, `fairness_by_approach.csv`, and `fairness_by_direction.csv`.
  - Documented real results: Fixed (127.29s wait), Webster (39.36s wait, -87.94s delta), Adaptive (50.14s wait, -77.15s delta), Pressure (49.67s wait, -77.62s delta, lowest disparity: 9.84s), RL DQN (57.04s wait, -70.25s delta).
- Hardened `.gitignore` to strictly exclude `node_modules/`, `dist/`, `.pytest_cache/`, `*.log`, `*.tmp`, and transient telemetry files.
- Synchronized demo snapshot dataset in `frontend/public/demo-data/` with verified experiments.
- Authored final deliverables: `docs/FINAL_VALIDATION.md`, updated `README.md`, `docs/SPEC.md`, and `docs/DEMO_SCRIPT.md`.

## v1.0 - Phase P5C: Design audit, motion review, responsive collapse QA, and Vercel deployment freeze
- Performed rigorous visual polish adhering to `Taste` and `emil-design-eng` guidelines:
  - Custom dark scrollbars (`scrollbar-thin`) to eliminate browser defaults.
  - 10-point motion and micro-interaction audit documented in `docs/UI_QA_REPORT.md` (smooth CSS transitions, cubic-bezier timing curves, reduced-motion media query support).
  - Responsive audit across 320px mobile, 768px tablet, and 1440px desktop breakpoints; mobile navigation bar with active highlights and horizontal scroll support.
- Configured Vercel deployment support via `frontend/vercel.json` with SPA route rewrites.
- Documented live deployment constraints: live simulation requires a self-hosted SUMO execution environment; static dashboard runs in self-contained Snapshot Mode.

## v0.9 - Phase P5B: React + Vite + JSX operations dashboard and live junction schematic
- Implemented full operations dashboard in `frontend/` using Vite, React 18, and Tailwind CSS.
- Built 5 dedicated workspaces:
  - `OverviewView.jsx`: System health, quick stats, controller summary, and architecture diagram.
  - `ControllerLabView.jsx`: Interactive side-by-side performance comparison across 5 controllers.
  - `RunExplorerView.jsx`: Detailed run browser with timeseries delay charts and phase decision tables.
  - `ResearchView.jsx`: Research matrix dashboard with forest plot of paired 95% bootstrap CIs, directional fairness disparity charts, and direct CSV/report downloaders.
  - `LiveMonitorView.jsx`: Real-time monitoring room featuring SVG intersection schematic (`IntersectionSchematic.jsx`) with dynamic lane queues, traffic light states, and emergency alerts.
- Built decoupled API client (`frontend/src/api/client.js`) with automatic graceful fallback to verified `public/demo-data/` snapshots when `VITE_API_BASE_URL` is unset.
- Created unit test suite `frontend/test/api-client.test.js` (7 tests).

## v0.8 - Phase P5A: FastAPI adapter, managed process lifecycle, and live atomic telemetry
- Added `requirements-api.txt` (`fastapi>=0.100.0`, `uvicorn>=0.22.0`, `pydantic>=2.0.0`, `httpx>=0.24.0`), isolating API dependencies from core `requirements.txt`.
- Core simulation engine, controllers, and CLI continue operating seamlessly without requiring FastAPI.
- Implemented live atomic telemetry in `dp1/runner.py`:
  - `_write_atomic_telemetry()` writes to `telemetry.json.tmp` and replaces atomically with `telemetry.json`.
  - Emits telemetry at step 0, on each simulation second, and on completion or failure.
  - Exposes `run_id`, `status`, `sim_time_s`, `phase`, `axis`, `queues_m`, `traffic_light_state`, `updated_at`, `emergency_approaching`, and `emergency_dist_m`.
  - Automatically records `metrics.json` in run directory upon completion.
- Built backend package `backend/`:
  - `config.py`: Host/port settings, allowlists, directory paths (`results/runs`, `results/research`), and exact CORS origins (`DP1_CORS_ORIGINS`).
  - `security.py`: Alphanumeric identifier validator (`^[a-zA-Z0-9_-]+$`), path traversal guards with `Path.is_relative_to()`, allowlisted research artifacts, and optional token authentication (`DP1_AUTH_TOKEN` / `DP1_API_KEY`).
  - `schemas.py`: Pydantic request/response schemas for health, summary, simulation runs, live telemetry, and research matrix evaluations. Missing metrics reported as `null` rather than zero.
  - `process_manager.py`: Thread-safe process manager executing subprocesses via `sys.executable` with `-u` and argument lists (never `shell=True`). Tracks PIDs, redirects logs to `process.log`, enforces concurrency limits, and supports safe cancellation (`SIGTERM` -> `SIGKILL`).
  - `routes/health.py`: `GET /api/health` inspects SUMO binary and returns truthful HTTP 503 if SUMO is absent/broken; `GET /api/summary` returns system summary and available parameters.
  - `routes/runs.py`: `POST /api/runs`, `GET /api/runs/{run_id}`, `GET /api/runs/{run_id}/status`, `GET /api/runs/{run_id}/timeseries`, `GET /api/runs/{run_id}/decisions`, and `GET /api/runs/{run_id}/telemetry` with 5-second staleness detection.
  - `routes/experiments.py`: `GET /api/experiments`, `POST /api/experiments`, `GET /api/experiments/{id}`, `GET /api/experiments/{id}/status`, `GET /api/experiments/{id}/results`, `GET /api/experiments/{id}/artifacts`, `GET /api/experiments/{id}/artifacts/{name}`, and `POST /api/experiments/{id}/cancel`.
  - `app.py`: FastAPI assembly with CORS middleware and mounted routers.
  - `__main__.py`: Entrypoint for running `python -m backend`.
- Added test suite `tests/test_api.py` (14 tests) covering health checks, missing SUMO graceful 503, parameter allowlist validation, path traversal rejection, legacy schema handling, atomic telemetry staleness, duplicate run conflicts, token authentication, research matrix endpoints, and artifact downloads.
- Documented API architecture, security model, and deployment constraints in `docs/API_SERVICE.md`.

## v0.7 - Phase P4: Deterministic emergency vehicle insertion and safe traffic signal priority
- Added `EmergencyConfig` in `dp1/config.py` with parameters: `detection_dist_m=100.0`, `min_green_s=10.0`, `max_extension_s=30.0`, `depart_time_s=300.0`, `approach='N'`, `turn='straight'`, `vehicle_id='ambulance'`, `speed_m_s=19.44`, `accel=3.5`, `decel=5.5`, `vclass='emergency'`, `color='1,0,0'`.
- Extended `dp1/scenarios.py` `build_routes()` to support `--emergency-event`:
  - When disabled (`emergency_event=False`), generated routes and SHA-256 hashes are 100% byte-identical to legacy routes.
  - When enabled (`emergency_event=True`), ordinary background vehicle IDs, routes, and departure times are preserved identically, and a visually distinct ambulance is inserted in strictly chronological order with companion manifest record (`emergency: True`).
- Implemented `dp1/emergency.py`:
  - `detect_approaching_emergency()`: verifies vehicle is approaching on an incoming edge (`_in`) within `detection_dist_m`; vehicles on internal junction lanes (`:`) or outgoing edges (`_out`) are strictly excluded.
  - `EmergencyPriorityCoordinator`: manages safe preemption and bounded green extension while preserving phase machine authority.
- Integrated priority seam in `dp1/controllers/base.py`:
  - Preemption requests on competing axis are allowed only after minimum green (`min_green_s=10.0s`) has elapsed.
  - When active axis is the emergency axis, green is extended up to `max_extension_s=30.0s` to prevent starving the other axis.
  - State machine invariants are 100% preserved: transitions strictly follow `GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN`.
- Extended `dp1/metrics.py` `summarise_run()`:
  - Extracts emergency-specific metrics from SUMO `tripinfo.xml`: `emergency_completed`, `emergency_wait_s`, `emergency_time_loss_s`, `emergency_trip_s`, `emergency_arrival_s`, `emergency_depart_s`.
  - Incomplete emergency vehicles are explicitly recorded as `emergency_completed=False` with `None` durations rather than silently dropped.
  - Background non-emergency traffic metrics (`non_emergency_avg_wait_s`, `non_emergency_avg_time_loss_s`) are isolated from the ambulance.
- Extended CLI `dp1 run` with `--emergency-event`, `--emergency-priority`, `--emergency-approach`, and `--emergency-depart`.
- Added test suite `tests/test_emergency.py` (7 tests). All 52 tests passing.
- Executed paired experiment across seeds 1..5 for `fixed`, `pressure`, and `rl_dqn`, demonstrating 64.6% reduction in emergency trip duration for `fixed` and honestly reporting trade-offs.

## v0.6 - Phase P3: DQN training and research evaluation pipeline
- Added configurable demand levels (`low=0.70`, `medium=1.00`, `heavy=1.30`) and `ResearchConfig` in `dp1/config.py`.
- Updated `dp1/scenarios.py` to support `demand_level`, deterministic route hashing (SHA-256), and vehicle manifest output (`.manifest.json`) attributing vehicle IDs to origin approaches.
- Scaled Webster plan: `FixedWebsterController` derives optimal cycle and green splits from the scaled scenario demand level.
- Extended `dp1/metrics.py` to calculate research-grade origin metrics (sample count, mean wait, p95 wait for N/S/E/W), directional NS vs EW wait disparity, and approach wait gap without modifying legacy column semantics. Missing subgroups are reported as `null`.
- Built complete research package `dp1/research/`:
  - `matrix.py`: Full 600-cell primary matrix definition ($4 \text{ patterns} \times 3 \text{ levels} \times 5 \text{ policies} \times 10 \text{ seeds}$), smoke preset, and dry-run preview.
  - `stats.py`: Aggregate statistics, paired candidate - fixed deltas, and deterministic 95% paired-bootstrap percentile confidence intervals ($B = 10,000$ resamples, logged RNG seed).
  - `plots.py`: Automatic generation of research figures (waiting time by level, paired wait delta with 95% CIs, queue length by level, and directional service disparity).
  - `report_gen.py`: Automatic scientific markdown report generator (`report.md`) derived directly from verified raw rows and manifest.
  - `orchestrator.py`: Execution engine supporting parallel execution, chunking (`--limit`), safe resume skipping validated successful cells, and graceful failure/blocked cell tracking (`failures.jsonl`, `matrix_status.csv`).
- Extended CLI `dp1` with `evaluate-research` subcommand supporting `--dry-run`, `--preset smoke|full|custom`, `--resume`, `--limit`, and `--jobs`.
- Added test suite `tests/test_research.py` (7 tests). All 45 tests passing.

## v0.5 - Phase P2: Gymnasium environment and DQN inference controller
- Added isolated `requirements-rl.txt` containing `gymnasium>=0.29.0` and `stable-baselines3>=2.0.0` (core `requirements.txt` preserved without heavy RL dependencies).
- Added `RLConfig` and seed groupings (`RL_VALIDATION_SEEDS=(6..10)`, `RESEARCH_EVAL_SEEDS=(21..30)`) in `dp1/config.py`.
- Implemented documented 11-dimensional observation vector builder `build_observation()` in `dp1/rl/obs.py` with feature metadata `OBS_FEATURE_NAMES` and schema version `OBS_SCHEMA_VERSION = "1.0.0"`.
- Implemented Gymnasium environment `SumoIntersectionEnv` in `dp1/rl/env.py` taking discrete actions `0=HOLD` and `1=REQUEST_SWITCH`, advancing 1 second per step, computing transparent normalized queue penalty and switch penalty, and strictly enforcing signal clearance invariants via `PhaseMachineController`.
- Implemented smoke training pipeline `train_dqn()` in `dp1/rl/train.py` which saves model `.zip` along with comprehensive companion `.metadata.json` (algorithm, schema version/dim, action mapping, bounds, seed splits, and package versions).
- Implemented `RLDQNController` in `dp1/controllers/rl_dqn.py` registered as `rl_dqn` in `POLICIES`, validating model existence and metadata schema before deterministic inference.
- Extended CLI `dp1` with `train-rl` subcommand, added `--model-path` argument, and added `rl_dqn` support across `run` and `compare`.
- Added test suite `tests/test_rl.py` covering observation shape/bounds, missing model error, metadata schema mismatch, environment step/reset lifecycle, signal safety bounds, and smoke training. All 38 tests passing.

## v0.4 - Phase P1: safe controller action seam and regression coverage
- Implemented `ControllerAction` (`HOLD=0`, `REQUEST_SWITCH=1`) in `dp1/controllers/base.py` for future RL/emergency controllers without altering legacy policy behavior.
- State-machine invariant: `base.py` strictly owns all phase transitions (`GREEN -> YELLOW (3 s) -> ALL_RED (2 s) -> GREEN(other axis)`). External action cannot bypass clearance or trigger direct green-to-green transitions.
- Enforced bounds at boundary: minimum green cannot be violated (switch requests before `min_green_s` are ignored); maximum green forces switch even if HOLD is requested.
- Decisions tracking: updated `decisions.csv` output to record both planned nominal green (`green_s`) and actual elapsed duration (`actual_green_s`).
- Tunable constants: added `ActionConfig` and `ACTION = ActionConfig()` in `dp1/config.py`.
- Added 9 unit/regression tests in `tests/test_action_seam.py`. All 31 tests green.

## v0.3 - real BTP fixed-time baseline (Marathalli Bridge Junction)
- Replaced placeholder 30/30 fixed-time plan with verified BTP timing: "Marathalli Bridge Junction, Airport Police Station – FIXED" (Varthur Rd × Outer Ring Rd Jn), weekday 08:00–11:30 (Phase 1 = 110 s, Phase 2 = 100 s, exclusive pedestrian = 15 s, cycle = 225 s) from OpenCity / BTP (`docs/btp_marathalli_yamlur.pdf`, page 10).
- Modelling decisions:
  1. Phase 1 mapped to NS axis and Phase 2 mapped to EW axis (adopting BTP's timing structure onto the junction).
  2. Clearance intervals: Subtracted yellow (3 s) and all-red (2 s) from phase durations dynamically via `config.TIMING`, yielding `FIXED.green_ns_s = 105 s` and `FIXED.green_ew_s = 95 s`.
  3. Pedestrian phase: 15 s exclusive pedestrian phase is not modelled; modelled cycle is 210 s vs 225 s real.
  4. Old 30/30 plan preserved in `config.py` as `FIXED_PLACEHOLDER`.
- Updated `test_fixed_green_is_constant` in `tests/test_core.py` to assert NS == 105 s and EW == 95 s.

## v0.2 - two lanes per approach (found by checking queue symmetry before the demo)
Problem found: with identical demand and identical green on all four approaches (balanced scenario, fixed plan), queues were
lopsided in v0.1 (single lane per approach): mean queue N 59 m, S 17 m, E 36 m, W 19 m (3 seeds).
Cause (tested): permissive left-turners blocking the single shared lane. With left turns removed, queues were symmetric
(N 9.9, S 9.0, E 8.1, W 8.8 m). It affected both policies equally (paired comparison stayed valid) but inflated absolute numbers.
Fix: 2 lanes per approach (lane 0 right+straight, lane 1 left+straight), one detector per lane, approach queue = max over lanes,
demand x1.7 (DEMAND_SCALE) so the junction is loaded comparably.
Check after fix (12 seeds, balanced, fixed): N 17.6, S 18.4, E 17.9, W 22.7 m; gaps scatter around zero.
New regression test: test_no_systematic_approach_bias_in_balanced_demand.
Effect on results: surge_north went from -9.8% (adaptive worse) to +1.0%; imbalanced gains rose from ~52% to ~63%.
Lesson for the report: validate the simulation model (symmetry, conservation) before trusting controller comparisons.

## v0.1 - first scaffold (single lane per approach), 11 tests.
