# DP1 Specification - Sensor-Based Adaptive Traffic-Signal Optimisation

## 1. Problem
Fixed-time signals give each approach a preset green regardless of demand. One approach can have a long
queue while another has a few vehicles, yet both get predetermined times, increasing waiting time and
congestion. DP1 measures queue length in real time (simulated sensors) and re-allocates green time, while
always holding an all-red clearance during transitions.

## 2. Scope
In scope (DP1): simulated queue sensors, queue comparison between approaches, dynamic green extension,
adjusted red for the other axis, all-red clearance, SUMO + TraCI, comparison against fixed-time.
Out of scope (DP2, later): congestion prediction 20-30 min ahead, adaptive rerouting, multi-junction corridor,
live sensors, signal hardware.

## 3. System loop
Sense (queue in metres per approach) -> Compare approaches -> Allocate green -> Yellow -> All-red -> Switch -> Measure.

## 4. Network (current: synthetic 4-way junction)
- Node `C` (traffic light), 4 approaches N/S/E/W, two lanes per approach (`C.NET.lanes = 2`), 300 m long, 50 km/h.
- Detector per approach: SUMO lane-area detector covering the last 150 m before the stop line.
  Queue length = `traci.lanearea.getJamLengthMeters(det_<A>)` (jam = vehicles below ~1.4 m/s). Capped at 150 m.
- Two signal axes: NS (N+S together) and EW (E+W together). Left turns are permissive (yield).
- Controllers use `SignalStates`, not hard-coded phase indices.

## 5. Controllers (all use the same yellow = 3 s and all-red = 2 s)
Fixed-time baseline: NS green 105 s, EW green 95 s based on an explicitly documented BTP timing-structure adaptation (Marathahalli Bridge junction, Airport Police Station schedule; see docs/SOURCES.md and docs/btp_marathalli_yamlur.pdf). Note: BTP's 15 s exclusive pedestrian phase is not modelled in the two-phase vehicle simulation, resulting in an effective 210 s vehicle cycle (105s + 3s + 2s + 95s + 3s + 2s). The original synthetic 30/30 plan is preserved in config as `FIXED_PLACEHOLDER`.

Adaptive (rule-based, interpretable):
- Axis queue = max queue of its two approaches.
- Green for the axis about to be served: `green = clamp(min_green + k * queue_m, min_green, max_green)`
  defaults: min 10 s, max 60 s, k = 0.30 s per metre (100 m queue -> 40 s).
- During green: keep extending (1 s at a time) while own queue > 15 m, up to max_green.
  End early (gap-out) if own queue has been 0 for 3 s and the other axis queue >= 1 m, after min_green.
- Consequence: heavy axis gets more green, the other axis waits longer on red; light axis gets near-minimum green.
- Safety: GREEN -> YELLOW -> ALL_RED -> GREEN(other axis). Enforced by `controllers/base.py` and tests.

"AI" element: the rule has tunable parameters; BUILD_PLAN phase 4 tunes them with a train/held-out seed split and
tests a pressure-based variant. Do not call the default rule "deep learning".

Safe Action Seam (Phase P1, for future RL/emergency controllers):
- Seam actions: `ControllerAction.HOLD (0)` and `ControllerAction.REQUEST_SWITCH (1)`.
- Actions are evaluated on simulation steps during GREEN; ignored outside GREEN (during YELLOW or ALL_RED).
- Invariant bounds: minimum green cannot be violated (switch requests before `min_green` are ignored); maximum green forces a switch even if HOLD is requested.
- State-machine invariant: switching always passes through the configured yellow (3 s) and all-red (2 s) clearance intervals before the competing axis is served.
- Decisions tracking: records both `green_s` (planned nominal target) and `actual_green_s` (elapsed green seconds upon phase termination).
- Legacy controllers remain unchanged with external actions off by default (`action=None`).

Reinforcement Learning Interface & DQN Controller (Phase P2, integration & safety verified):
- Isolated optional RL dependencies: specified in `requirements-rl.txt` (`gymnasium>=0.29.0`, `stable-baselines3>=2.0.0`), keeping base `requirements.txt` lightweight.
- Gymnasium Environment: `SumoIntersectionEnv` in `dp1/rl/env.py`. Action space is `Discrete(2)` (`0=HOLD`, `1=REQUEST_SWITCH`). Observation space is `Box(11,)` with strictly normalized features: 4 approach queues, 2 axis one-hot, 3 phase one-hot, elapsed green fraction, and demand timeline fraction.
- Reward: Transparent per-second normalized reward based on total queue across all four approaches plus a switch penalty (`reward = - (total_queue_m / 600.0) - switch_penalty`).
- Phase Machine Reuse: Safety transitions are strictly owned by `PhaseMachineController`. The agent only issues switch requests; it can never set an arbitrary signal state.
- Inference Controller: `RLDQNController` in `dp1/controllers/rl_dqn.py` registered as `rl_dqn`. Loads trained `.zip` model and validates companion `.metadata.json` schema. Enforces min/max green bounds.
- Status: Integration, environment lifecycle, and signal safety are verified. No performance claims are made in this phase; the smoke model is a test artifact only.

## 6. Scenarios (vehicles/hour per approach, 1800 s demand)
balanced (400 each) | imbalanced_ns (N,S 700; E,W 200) | imbalanced_ew (mirror) |
surge_north (all 400, N rises to 1100 between 600-1200 s). Turn split 70% straight / 15% left / 15% right.
Same scenario + seed produces identical vehicles for both policies (paired comparison).

## 7. Metrics & Research Evaluation Pipeline (Phase P3)
- Legacy metrics (preserved): `avg_wait_s`, `avg_time_loss_s`, `avg_trip_s`, `p95_wait_s`, `avg_queue_m`, `max_queue_m`, `throughput_veh_per_h`, `completion_rate`, `cycles`.
- Research metrics: `completed_in_demand_window`, per-approach sample counts and wait means (`avg_wait_N_s`, `p95_wait_N_s`, etc.), directional wait disparity (`|Wait_NS - Wait_EW|`), and approach wait gap (`max(Wait_approach) - min(Wait_approach)`).
- Demand levels: config-driven arrival multipliers `low` (0.70), `medium` (1.00), and `heavy` (1.30). `FixedWebsterController` dynamically adapts cycle and green splits to the scaled profile.
- Primary Matrix: 4 scenario patterns (`balanced`, `imbalanced_ns`, `imbalanced_ew`, `surge_north`) x 3 demand levels x 5 policies (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`) x 10 seeds (`21..30`) = 600 runs.
- Statistical Rigor: Paired differences against `fixed` under byte-identical route arrivals, paired-bootstrap 95% percentile confidence intervals (10,000 resamples), seed separation (`TRAIN_SEEDS=1..5`, `RL_VALIDATION_SEEDS=6..10`, `HELD_OUT_SEEDS=11..15`, `RESEARCH_EVAL_SEEDS=21..30`).
- Orchestrator: `python -m dp1.cli evaluate-research` supporting `--dry-run`, `--preset smoke`, `--resume`, `--limit`, and `--jobs`. Output written to unique `results/research/<experiment_id>/` with `manifest.json`, `config.json`, `raw_runs.csv`, `aggregate.csv`, `paired_deltas.csv`, `fairness_by_approach.csv`, `fairness_by_direction.csv`, `matrix_status.csv`, `failures.jsonl`, `plots/`, and `report.md`.

## 7.1 Emergency Vehicle Priority (Phase P4)
- **Deterministic Event Generation**: Configured via `EmergencyConfig` in `dp1/config.py`. Controlled by explicit `--emergency-event` CLI flag. When enabled, background vehicles, IDs, routes, and departures are 100% identical to non-emergency runs. One ambulance is inserted in sorted chronological order with companion manifest record (`emergency: True`).
- **Geometry-based Detection**: `detect_approaching_emergency()` in `dp1/emergency.py` detects ambulance only when approaching on an incoming edge (`_in`) within `detection_dist_m=100.0m`. Internal intersection lanes (`:`) and outgoing edges (`_out`) are strictly excluded.
- **Safety Preemption Rules**: Controlled by independent `--emergency-priority` CLI flag:
  1. Minimum green on competing axis (`min_green_s=10.0s`) cannot be cut short.
  2. Maximum emergency green extension (`max_extension_s=30.0s`) strictly bounds the active axis to prevent starving the other axis.
  3. Every preemption switch passes strictly through `GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN`. No direct green-to-green transitions or simultaneous green states can ever occur.
- **Metrics & Transparency**: Extracted from SUMO `tripinfo.xml`: `emergency_completed`, `emergency_wait_s`, `emergency_time_loss_s`, `emergency_trip_s`, `emergency_arrival_s`, `emergency_depart_s`. Incomplete emergency vehicles are recorded as `emergency_completed=False` rather than silently dropped. Background traffic metrics are reported separately from the ambulance.


## 7.2 API Service & Live Telemetry Architecture (Phase P5A)
- **FastAPI Backend**: Thin, non-duplicative adapter layer located in `backend/` exposing atomic telemetry and simulation management.
- **Isolated Requirements**: Uses `requirements-api.txt` (`fastapi`, `uvicorn`, `pydantic`, `httpx`). Core simulation remains standalone.
- **Atomic Telemetry**: Per-second execution snapshots written via `.tmp` file swap to prevent read collisions. Fields: `sim_time_s`, `phase`, `axis`, `queues_m`, `traffic_light_state`, `emergency_approaching`, `emergency_dist_m`.
- **Security & Safety**: Identifier validation regex `^[a-zA-Z0-9_-]+$`, path traversal protection via `Path.is_relative_to()`, allowlisted parameter inputs, and optional bearer token authentication (`DP1_AUTH_TOKEN`).
- **Endpoints**: `GET /api/health` (checks SUMO), `GET /api/summary`, `POST /api/runs`, `GET /api/runs/{id}/telemetry` (with 5-second staleness flag), `GET /api/experiments`, and `GET /api/experiments/{id}/artifacts/{name}`.

## 7.3 React Operations & Research Dashboard (Phase P5B & P5C)
- **Modern Web Architecture**: Single Page Application in `frontend/` built with Vite, React 18, Tailwind CSS, Lucide icons, and Recharts.
- **Design System Tokens**: High-contrast, dark-mode design system with deep obsidian slate palettes, tabular numeric fonts, and reduced-motion support adhering to `Taste` and `emil-design-eng` guidelines.
- **5 Integrated Workspaces**:
  1. *Overview Workspace*: Health status, system statistics, quick metric comparison cards, and architecture summary.
  2. *Controller Lab*: Interactive comparative matrix for all 5 controllers (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`).
  3. *Run Explorer*: Detailed inspection of individual runs, timeseries charts, phase decisions, and tripinfo summaries.
  4. *Research & Evaluation*: Matrix progress tracker, paired-delta forest plot with bootstrap 95% CIs, directional fairness disparity table, and raw artifact downloads.
  5. *Live Monitor*: Real-time SVG junction schematic (`IntersectionSchematic.jsx`) with dynamic queue levels, active phase colors, ambulance indicator, and live telemetry feed.
- **Dual Operating Modes**:
  - *Live Mode*: Direct WebSocket/HTTP connection to FastAPI backend when `VITE_API_BASE_URL` is set.
  - *Snapshot Mode*: Self-contained, zero-backend demo mode consuming verified JSON/CSV artifacts in `public/demo-data/` with clear generation timestamp banner.
- **Vercel Deployment**: Static SPA rewrite configuration via `vercel.json` for cloud distribution.

## 7.4 Final Reproducibility & Research Protocol (Phase P6)
- **Seed Grouping Policy**:
  - `TRAIN_SEEDS` (1–5): Used for legacy grid search and Webster timing parameter calibration.
  - `RL_VALIDATION_SEEDS` (6–10): Used exclusively for RL training checkpoint validation.
  - `HELD_OUT_SEEDS` (11–15): Held-out evaluation seeds for baseline comparison.
  - `RESEARCH_EVAL_SEEDS` (21–30): Strictly isolated research test seeds; never used during training or parameter tuning.
- **Fairness & Statistical Invariants**:
  - Identical demand and arrival seeds for candidate and baseline runs.
  - Bootstrap resampling (10,000 resamples) for paired confidence intervals.
  - Disparities and null subgroup statistics explicitly surfaced (`null` rather than `0.0`).
- **Safety Invariant**: Strict transition rule `GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN` strictly preserved across all 5 controllers and emergency preemption.

## 8. Acceptance criteria for DP1
1. `pytest -q` passes (66 tests: safety invariant, clearance intervals, controller limits, Webster bounds, physical queue readings, action seams, RL environment, emergency preemption, API security, and research matrix stats).
2. Frontend unit tests (`npm test` in `frontend/`, 7 tests) and production build (`npm run build`) pass cleanly.
3. All 5 controllers (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`) run deterministically without runtime crashes.
4. Paired comparisons prove adaptive and pressure controllers reduce average wait and directional disparity in imbalanced traffic; trade-offs in surge scenarios are reported truthfully.
5. Deterministic emergency preemption reduces ambulance travel time while respecting minimum greens and clear transition intervals.
6. Every cited metric originates from verified SUMO run logs; no results are hand-edited or fabricated.
7. Limitations clearly stated: simulated SUMO detectors, synthetic junction geometry, adapted BTP timing baseline (pedestrian phase omitted).

## 9. Known limitations (say them before the mentor does)
Two lanes per approach on synthetic geometry; detector capped at 150 m; no pedestrians (BTP 15 s exclusive pedestrian phase is omitted); simple two-phase plan; surge scenario currently favours the fixed plan; results come from a simulator, not field data.

