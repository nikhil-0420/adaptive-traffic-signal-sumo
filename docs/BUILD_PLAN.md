# DP1 Advanced AI Upgrade — Build Plan for Antigravity

**Project:** Sensor-Based Adaptive Traffic-Signal Optimisation (SUMO + TraCI)  
**Implementation environment:** Antigravity IDE, using the existing repository and its local Python environment  
**Target level:** Level 2 — an advanced AI project with reproducible controller comparisons, emergency-vehicle priority, and a React dashboard deployed on Vercel  
**Expected working cadence:** a few weeks, implementing one gated phase at a time

---

## 1. Mission and scope

Upgrade the existing DP1 codebase without replacing its working core. The final system should let a reviewer:

1. Preserve and verify the existing four non-RL controllers on the current synthetic network as the first-upgrade baseline and ongoing regression reference.
2. Complete all AI, emergency-priority, research-evaluation, API and React dashboard improvements on the existing synthetic network first.
3. Only after the synthetic-network upgrade passes its final P6 gate, reconstruct a geographically grounded Marathahalli Bridge / Varthur Road / ORR SUMO network from OpenCity road-view and downloadable geospatial sources. After owner approval, adapt the system and train/evaluate a separate DQN model for that site-network schema.
4. Simulate a deterministic ambulance event where the selected network and route support it, and compare priority disabled/enabled without bypassing safe signal transitions.
5. Inspect the synthetic simulation, controller decisions, live telemetry and research results in a polished React + Vite + JSX dashboard deployed on Vercel. Add the Marathahalli Network/Site Model view only in the final post-upgrade site-network phase.
6. Run and explore the required research-grade evaluation from the CLI and a dedicated **Research & Evaluation** dashboard view: controlled low/medium/heavy traffic demand, repeated paired seed runs, uncertainty summaries, directional fairness, provenance, and generated downloads.
7. Reproduce all reported numbers from generated artifacts and recorded experiment configuration.

**In scope, in this order:** (A) the full advanced upgrade on the existing synthetic network, including optional DQN, deterministic emergency event, reproducible research matrix, React + Vite + JSX frontend on Vercel, optional FastAPI adapter and tests; then (B), only after Phase A is frozen and approved, a Marathahalli network grounded in OpenCity/map evidence, a separate site-compatible model/controller configuration, separate site-specific experiments and a Network/Site Model dashboard view.

**Out of scope:** real-time road cameras/sensors, traffic-signal hardware, claims of field deployment, city-wide or coordinated multi-junction adaptive control, forecasting 20–30 minutes ahead, route rerouting, and claiming exact field fidelity without lane/traffic/signal data. A site-grounded road layout with synthetic demand is not real-world traffic calibration.

## 2. What already exists and must be preserved

The uploaded repository contains:

- `dp1/config.py`: shared timing, geometry, demand profiles, controller tuning and seed split.
- `dp1/network.py`, `dp1/scenarios.py`, `dp1/signal_states.py`: generated four-way SUMO network, seeded demand, and signal-state strings.
- `dp1/controllers/base.py`: the common GREEN → YELLOW → ALL_RED phase machine.
- `dp1/controllers/fixed_time.py`, `fixed_webster.py`, `adaptive_queue.py`, `adaptive_pressure.py`: four existing non-RL controllers.
- `dp1/runner.py`: individual TraCI simulation, queue collection, timeseries, decisions and tripinfo output.
- `dp1/metrics.py`, `compare.py`, `tune.py`, `report.py`, `cli.py`: scoring, experiments, tuning, reporting and CLI.
- `tests/test_core.py`: signal-safety, clearance, controller bounds, queue readings and reporting tests.

The current fixed plan is configured from the BTP Marathalli Bridge timing document as a **timing-structure adaptation on a synthetic junction**: configured vehicle green is 105 s NS and 95 s EW after assumed 3 s yellow and 2 s all-red clearance are subtracted. It must remain labelled as the legacy synthetic-network timing adaptation. Do **not** copy 105/95 to the Marathahalli site network unless the source documents the same phase plan for the exact selected control node. The current synthetic model does not include BTP's exclusive pedestrian phase.

## 3. Initial audit findings to resolve in P0

The uploaded package has several documentation or hand-off inconsistencies. They are not proof that the simulation code is broken, but they must be reconciled before adding features:

- `README.md` says the fixed 30/30 plan is a placeholder, while `dp1/config.py` currently defines the adapted 105/95 s greens.
- `docs/SPEC.md` describes one lane per approach and a 30/30 placeholder, while `dp1/config.py` uses two lanes per approach and the configured BTP-derived split.
- `README.md` says there are 11 tests, while the test file now contains more coverage.
- `README.md` directs the developer to `docs/PROMPTS.md`, but that file is missing from the uploaded ZIP.
- Existing `results/` and `docs/results_snapshot/` files are historical artifacts, not proof that the same output can be regenerated in the current environment.
- Generated SUMO XML files appear in the ZIP even though `.gitignore` excludes them. Treat them as generated files; do not hand-edit them.

P0 must write down actual local versions and test/run outcomes, then update only statements that can be checked from code or freshly generated artifacts.

## 4. Deferred Marathahalli network — only after the full synthetic upgrade

`docs/MARATHAHALLI_NETWORK_SPEC.md` is a **later-phase specification, not an instruction to begin mapping now**. During P0–P6, the implemented target remains the existing synthetic four-way SUMO network. Finish DQN, emergency priority, the research matrix, FastAPI, the React dashboard, skill-led UI QA, Vercel readiness and the final report on that network first.

Only after the P6 release/freeze gate passes may Phase P7A inspect OpenCity's road/data view and available geospatial datasets to reconstruct the Marathahalli Bridge / Varthur Road / Outer Ring Road area. The road-centreline and road-width datasets help establish geography but do not prove every lane, turn, signal or elevation detail. Require provenance, verified/inferred/unknown labels and owner review; do not invent unknowns.

P7A must create `docs/MARATHAHALLI_NETWORK_AUDIT.md`, source inventory, a SUMO-GUI/network screenshot, route-connectivity output and a control-node/phase inventory. It then stops for the owner's approval. Only P7B may adapt controllers, train a **separate site-compatible DQN model**, run site-specific experiments, and add site network selection plus the Network/Site Model view. Site metrics must be stored and reported separately from synthetic results. Demand remains synthetic unless measured counts are sourced.

Do not implement the real network, site selection, site-specific controller phases or site matrix during P0–P6. Preparing and retaining this written specification is allowed; implementation is explicitly deferred.

## 5. Target architecture

### 5.1 Existing non-RL controllers stay intact

Keep the existing controller names and behaviour unless a compatibility fix is required. For P0–P6, the existing phase machine remains the single source of truth for all safety transitions on `synthetic`. Do not introduce site-specific phase groups during the initial upgrade. The deferred P7B site phase may extend the abstraction after owner approval. Do not let DQN or emergency logic write signal states directly or bypass configured clearance.

### 5.2 DQN control contract

Implement DQN as an **optional controller**. Start with the small, interpretable action space:

- `0 = HOLD`: keep the current legal green stage, if allowed.
- `1 = REQUEST_SWITCH` (or `ADVANCE`): request the next legal stage in the owner-approved signal plan, if allowed. The legacy synthetic network must retain its existing two-axis semantics.

Requests must be ignored outside a legal green stage. A switch request before the stage's configured minimum green is ignored. Reaching maximum green forces advancement according to the legal plan. An accepted switch follows the configured clearance sequence (yellow/all-red where applicable); no controller may mutate SUMO signal strings directly. For P0–P6, the model uses the existing synthetic network schema. Do not add a site schema early. During P7B, derive site movements and phase stages only from the owner-approved `docs/MARATHAHALLI_NETWORK_AUDIT.md`.

At each simulation-second decision, use a normalized observation with a documented fixed shape per model/network schema. Recommended components are queue lengths for all relevant approaches/lanes of the selected signal group (capped and normalized by detector/approach scale), current legal phase/stage one-hot, elapsed-stage-green fraction, and simulation-time fraction. Include only measurements available at that simulation time; do not leak future arrivals or evaluation labels. The initial model is trained and evaluated on `synthetic` only. P7B must train/save a separate site-specific model; never load the synthetic model on the Marathahalli schema unless compatibility is separately proven and documented.

Use Gymnasium for the environment interface and Stable-Baselines3 DQN for the first learned policy. Keep these dependencies **optional** in `requirements-rl.txt` so users can still run the original project without installing PyTorch/RL packages. Verify versions against the Python interpreter actually used in the project; never silently replace the user's interpreter or base virtual environment. If the existing interpreter has no compatible wheel, propose a clearly separate RL virtual environment and document exact commands.

### 5.3 RL reward and evaluation contract

Start with a transparent per-simulation-second reward based on normalized total queue across all four approaches. A waiting-time term may be included only if it is consistently computed and its coefficient is defined in `dp1/config.py`. Put reward weights, training steps, learning rate, replay-buffer settings, exploration settings, and green bounds in configuration—not magic numbers scattered throughout modules. Log reward components so reward hacking or scaling errors are visible.

The agent must not be trained on the evaluation seeds. Preserve the existing rule-tuning split (`TRAIN_SEEDS` and `HELD_OUT_SEEDS`) and define a clearly disjoint RL training seed set if needed. Use paired demand: a given scenario/seed must generate identical background traffic for every policy being compared. Evaluate every controller on the same scenarios/seeds.

A trained model must be saved with a small metadata/config file containing algorithm, observation schema/version, action mapping, configuration, training seed range, training timesteps, package versions, and creation/run identifier. Loading a model with incompatible metadata must fail with an actionable message, not silently run with the wrong observation schema.

### 5.4 Emergency priority contract

Emergency priority is a separately switchable feature so its impact can be measured. Add an optional, deterministic emergency-vehicle event to the existing route generation; for the same scenario and seed, regular background vehicles and the ambulance event must be identical across compared policies. Do not make emergency traffic a hidden change to baseline demand.

The ambulance's approach/direction and arrival time should be deterministic from the experiment seed or explicit config, and recorded in run metadata. Detect it while approaching the stop line. When priority is enabled, request the appropriate axis using the shared phase machine, while respecting minimum green, yellow, all-red, and a configured upper bound on emergency green extension so the other axis cannot be starved indefinitely. When priority is disabled, the same ambulance is present but no priority override is applied.

Record emergency completion, waiting time and time loss separately from background-traffic metrics. Label `timeLoss` as SUMO time loss, not simply “signal delay”. If the emergency vehicle does not finish within the drain cap, record it as incomplete; do not omit that run.

### 5.5 Dashboard contract — React + Vite + JSX + Vercel

**Required frontend stack:** React, Vite, JavaScript/JSX (not TypeScript/TSX), CSS or a justified utility-CSS setup, and Vercel static deployment. Do not use Streamlit, Dash, Gradio, Flask templates, or a Python-rendered dashboard. The frontend lives in `frontend/` and owns all dashboard presentation and client-side interaction.

**Backend boundary:** the existing Python/SUMO project remains the simulation engine. Add a small FastAPI adapter under `backend/` that reads generated result artifacts and exposes run/telemetry endpoints. It must call the existing modules/CLI rather than reimplement traffic simulation. Keep API dependencies separate from base requirements in `requirements-api.txt`; keep DQN dependencies in `requirements-rl.txt`. Do not add dashboard Python requirements.

Vercel should host the built React static app only. A live SUMO process requires a separate Python runtime/container with SUMO and the project dependencies installed; it should not be run in a Vercel frontend/serverless function. Support these modes explicitly:

1. **Local full mode:** FastAPI runs on localhost with SUMO installed; React fetches its endpoints via `VITE_API_BASE_URL` or a Vite development proxy.
2. **Vercel read-only preview mode:** the frontend can load a labelled, versioned snapshot generated from real project CSV artifacts bundled under `frontend/public/demo-data/`. It must show when this snapshot was generated and must never present snapshot data as live. Simulation-launch controls are disabled when no API is configured.
3. **Vercel + remote API mode:** set `VITE_API_BASE_URL` in Vercel to a separately deployed backend whose container has SUMO available. Configure exact frontend origins in backend CORS. Do not claim live run support unless the health/telemetry endpoints are reachable. Protect mutation/launch endpoints with server-side authentication or a user-supplied session token; never bake secrets into `VITE_*` variables or the client bundle.

**Minimum views:**

- **Operations overview:** simulation/connection status, selected result dataset, number of valid runs, mean waiting time, average queue, throughput, completion rate, visible sample count and variation.
- **Controller laboratory:** scenario/policy/seed filters and paired comparisons of `fixed`, `fixed_webster`, `adaptive`, `pressure`, and `rl_dqn`; show mean ± standard deviation or error bars with units and improvement direction.
- **Run explorer:** per-approach queue time series, signal phase/axis timeline, decision log and actual green durations. Include emergency metrics only when they exist in the selected results.
- **Live simulation:** only when API is connected; show run ID, process status, simulation time, active axis/phase, recent telemetry timestamp, approach queues, progress and error/log details. Poll only while active and stop on complete/failure. Indicate stale telemetry rather than pretending it is live.
- **Experiment provenance:** policy, scenario pattern, demand level/multiplier, seed, simulation configuration, model ID/metadata and run/artifact timestamp.
- **Research & Evaluation (required first-class view):** launch or inspect a research matrix; show experiment progress, completed/failed/skipped cell counts, scenario-pattern × demand-level × policy × seed coverage, paired per-seed comparisons, mean ± standard deviation, 95% confidence intervals for paired differences, directional wait disparity, per-approach details, and links/downloads to raw and aggregated output artifacts. Partial matrices must be labelled PARTIAL and can never be presented as final.

**API shape (adapt only if the repository establishes a better existing convention):** `GET /api/health`, `GET /api/summary`, `GET /api/experiments`, `POST /api/experiments` (validated research matrix request), `GET /api/experiments/{experiment_id}`, `GET /api/experiments/{experiment_id}/status`, `GET /api/experiments/{experiment_id}/results`, `GET /api/experiments/{experiment_id}/artifacts`, `GET /api/experiments/{experiment_id}/artifacts/{artifact_name}`, `GET /api/runs/{run_id}`, `GET /api/runs/{run_id}/timeseries`, `GET /api/runs/{run_id}/decisions`, `POST /api/runs` (validated allowlisted run request), and `GET /api/runs/{run_id}/status`. A safe experiment cancel endpoint may be added if process cleanup is reliable. Define response schemas and useful 4xx/5xx messages. Paths must be scoped to approved results directories; do not accept arbitrary filesystem paths from the browser.

**Data integrity and reliability:** no fabricated metrics or hand-edited charts; missing data is not zero. Include intentional empty, loading, stale-data, disconnected API, failure, and successful states. Launch simulations with list-based subprocess arguments (never `shell=True`), capture logs, prevent conflicting concurrent SUMO runs, use unique run folders, write telemetry atomically, and clean up child processes on cancellation/shutdown. Do not start model training automatically from a dashboard page load.

**Design quality is a build requirement, not a finishing suggestion.** Before writing UI, the agent must follow `docs/UI_SKILL_CONTRACT.md`, use `ui-ux-pro-max`, `Taste`, and `emil-design-eng` plus relevant installed skills from `emilkowalski/skills`. Do not settle for generic admin-dashboard cards, a giant empty hero, stock imagery, emoji navigation or arbitrary gradients. Create a project-specific visual system and a traffic-specific visualization (for example, an animated/schematic intersection with clearly mapped signal states) only where it helps people understand the simulation. Keep decorative motion restrained, informative and accessible. Use actual metric labels, axes, units, seed counts and provenance.

**Verification:** use the actual dashboard in browser/dev server where available, test responsive widths and keyboard/empty/error states, run animation review, and run `break-ui` or equivalent on long labels, missing data, very large values and disconnected/failed APIs. The Python CLI and tests must continue to work with the frontend/backend packages absent.

## 6. Proposed file changes (agent must adjust only if the current code proves a better seam)

| Area | Intended files | Expected change |
|---|---|---|
| Deferred site-network provenance/model | `docs/MARATHAHALLI_NETWORK_SPEC.md`, later-generated `docs/MARATHAHALLI_NETWORK_AUDIT.md`, `data/reference/opencity/` and `network/marathahalli/` | **P7A/P7B only, after P6.** Keep map source data and generated SUMO data distinct; preserve metadata; add the network selector only after owner approval. |
| Config | `dp1/config.py` | Add typed `RLConfig` and `EmergencyConfig`, with all new tunables in one place; define RL-only seeds and reward/training parameters. |
| Controller safety | `dp1/controllers/base.py` | Add a clean action/switch-request seam and optional emergency-priority hook without changing existing default behaviour. Keep transition safety centralised. |
| RL controller | `dp1/controllers/rl_dqn.py` (or `dp1/rl/controller.py`) | Load/predict with a saved DQN model; enforce min/max green and action schema. |
| RL environment | `dp1/rl/env.py` | Gymnasium environment using the same SUMO/TraCI setup, selected network and approved phase-plan semantics; deterministic reset/close and versioned observation/action schemas. Train separate models per network/signal schema unless compatibility is explicitly proven. |
| RL training | `dp1/rl/train.py` | Deterministic training entry point, model metadata, reward logs, optional TensorBoard. |
| Emergency routing | `dp1/scenarios.py`, `dp1/runner.py`, `dp1/config.py` | Deterministic optional ambulance, detection of approach/axis, safe priority override, explicit feature flags. |
| Metrics + research evaluation | `dp1/metrics.py`, `dp1/compare.py`, `dp1/report.py`, new `dp1/research_eval.py` (or equivalent) | Preserve legacy metric meanings; add approach-origin manifest, per-approach/per-direction statistics, paired aggregation and confidence intervals, demand-level matrix, resumable orchestration and generated research report. |
| CLI | `dp1/cli.py` | Add train/evaluate args, model path and emergency flags, output-dir/live options as needed. Keep existing command signatures working. |
| Frontend | `frontend/` (`package.json`, Vite config, JSX components, styles, tests, `vercel.json`) | React + Vite + JSX dashboard and Vercel static deployment, including the dedicated Research & Evaluation workspace. |
| API service | `backend/` (FastAPI routes, schemas, artifact reader, run/experiment manager) | Thin API over the existing CLI/artifacts; live simulation and research batches only on a host with SUMO. Expose experiment lifecycle/progress/results and safe artifact downloads. |
| Tests | `tests/test_core.py` plus new focused test files | Preserve old tests; add action bounds, Gymnasium API, seeded routes, emergency safety and telemetry tests. |
| Dependencies | `requirements-rl.txt`, `requirements-api.txt`, `frontend/package.json` | Keep AI and API dependencies separate; frontend uses npm and must not require Python UI packages. |
| Docs | `README.md`, `docs/SPEC.md`, `docs/BUILD_PLAN.md`, `docs/PROMPTS.md`, `docs/MARATHAHALLI_NETWORK_SPEC.md`, `docs/MARATHAHALLI_NETWORK_AUDIT.md`, `docs/UI_SKILL_CONTRACT.md`, `docs/CHANGELOG.md` | During P0–P6, document and verify only the synthetic network. During P7A/P7B, record site provenance/assumptions and keep site results separate from synthetic results. |

## 7. Staged schedule and gates

### Phase 0 — Baseline audit and freeze (first session)

**Goal:** know exactly what currently works before code changes. Check the active Python and SUMO versions, install only existing core requirements if missing, run tests, run a small smoke matrix, and save a freshly regenerated pre-upgrade comparison snapshot. Reconcile README/SPEC/BUILD_PLAN statements against the actual source. Do not build new features in this phase.

**Gate:** actual test output, SUMO version, smoke-run commands, source-of-truth config and a `results/baseline_pre_upgrade/` snapshot. If the baseline fails, isolate/fix only the baseline issue before proceeding.

### Deferral guardrail — no Marathahalli implementation before P6

There is deliberately **no network-reconstruction phase between P0 and P6**. Do not use OpenCity to create or alter the simulation network while implementing the first upgrade. Complete the sequence in the order shown below. The Marathahalli source/network phases are Phase 7A and 7B, after the P6 synthetic release/freeze gate.

### Phase 1 — Safe extension seams and regression coverage

**Goal:** prepare a clean way for a controller to request a legal phase transition without owning the transition state machine on the **existing synthetic network only**. Add a switch-request/decision hook that preserves current behaviour for all legacy policies; clarify decision-log fields (requested target vs actual green duration); add tests for default legacy behaviour. Do not introduce site-specific phase plans, RL or emergency logic yet.

**Gate:** existing `pytest -q` passes; same scenario/seed baseline policies run; legacy fixed green durations and yellow/all-red timings remain unchanged; before/after fixed/adaptive/pressure metrics are within reproducibility expectations (small differences must be explained, not hidden).

### Phase 2 — RL environment and DQN inference controller

**Goal:** create a Gymnasium environment around the existing synthetic network with discrete HOLD/REQUEST_SWITCH actions, normalized observation, per-second reward, reset/close lifecycle and exact phase safety. Add a DQN-backed controller, but keep the feature optional and fail helpfully when its package/model is absent. Do not claim it is trained or performs well yet.

**Gate:** environment passes Gymnasium environment checks (or equivalent focused API tests); deterministic reset with the same seed; no illegal green transition; minimum/maximum green enforcement; inference works from a saved tiny/test model; all legacy controllers still run with RL extras uninstalled.

### Phase 3 — Train, persist, compare and run research-grade evaluation on synthetic

**Goal:** add CLI commands to train, save metadata, load and evaluate the controller, plus a dedicated resumable research-matrix runner. Keep training reward/config logs; compare DQN against `fixed`, `fixed_webster`, `adaptive` and `pressure` on the existing `synthetic` network under low/medium/heavy demand using identical scenario-pattern/level/seed traffic for every controller. Use train seeds 1–5, validation seeds 6–10, and a new research-only test range 21–30. Keep existing `HELD_OUT_SEEDS` (11–15) and legacy commands unchanged for backward compatibility.

**Gate:** a documented fresh training command creates a model and metadata; loading reproduces the same action for a fixed observation (deterministic inference); a smoke research matrix can be run/resumed; full evaluation writes raw rows, aggregates, paired-difference intervals, fairness summaries, manifest, plots and report. Default Phase A research test protocol uses 10 unseen seeds (21–30) for all 4 existing synthetic scenario patterns × 3 demand levels × 5 controllers; it must be resumable and configurable because this is a 600-run matrix. Do not include Marathahalli data in this phase. Never require DQN to win; accurately report regressions and uncertainty.

### Phase 4 — Emergency vehicle priority

**Goal:** add the deterministic ambulance event on the existing synthetic network and a switchable priority override. Compare priority off vs on using the same ambulance event and same background vehicles. Enforce green floor, yellow clearance, all-red clearance, and a maximum emergency extension/fairness bound.

**Gate:** tests prove no direct GREEN-to-GREEN transition, no simultaneous greens, minimum green is respected, configured emergency extension bound is respected, and the ambulance appears identically across paired runs. Experiment report includes ambulance waiting/time-loss/completion and the effect on ordinary traffic. If the priority feature worsens other traffic, report that trade-off.

### Phase 5A — API and telemetry contract

**Goal:** add the minimal FastAPI service and atomic telemetry/run lifecycle that exposes actual artifacts and safely launches an allowlisted simulation or research experiment. The service must remain a thin adapter to the current Python simulation and `dp1/research_eval.py`; no second simulation engine.

**Gate:** API unit tests cover missing/empty/legacy/new artifacts, path-safety validation, launch argument validation, atomic telemetry and running/complete/failed status. Original CLI/tests remain independent of FastAPI.

### Phase 5B — React + Vite + JSX dashboard

**Goal:** implement the frontend in `frontend/`; use the mandatory design-skill process in `docs/UI_SKILL_CONTRACT.md`; build overview, controller lab, run explorer, dedicated Research & Evaluation workspace, and connected live monitor for the synthetic network only. Do not add a Network/Site Model view or Marathahalli selector in this phase. The research workspace must consume the real experiment API/artifacts and must support filters, matrix progress/completion, paired policy results, uncertainty, directional fairness and downloads. Include static read-only mode using real generated demo snapshots when `VITE_API_BASE_URL` is unset; label the snapshot with its generation timestamp and disable live controls/research launch actions.

**Gate:** `npm run build` succeeds; actual endpoints and snapshot mode are tested; all chart numbers come from data; no fake placeholder values; legacy CLI still runs.

### Phase 5C — Design review, accessibility, responsive behaviour and Vercel deployment

**Goal:** conduct a proper visual pass using `Taste` and `emil-design-eng` skills, then run animation review, accessibility checks and edge-case UI testing. Verify Vercel SPA routes and document environment variables. Do not claim live deployed simulation until the separately hosted SUMO-capable API is connected.

**Gate:** reviewed at desktop and narrow mobile widths; reduced-motion preference works; keyboard/focus states are visible; empty/disconnected/stale/failed states are accurate; `npm run build` succeeds and Vercel configuration is present; dashboard deployment limitations are documented.

### Phase 6 — Final reproducibility, report and demo freeze

**Goal:** rerun the exact final experiment matrix; generate the report from raw generated CSV/XML; include setup/training/evaluation commands, limitations, model metadata and comparisons. Update README/SPEC/DEMO_SCRIPT and CHANGELOG after results exist. No metric is copied by hand.

**Gate:** clean test run, base-controller smoke tests, DQN train/load/evaluation smoke, emergency tests, FastAPI/API smoke, React build and dashboard smoke, final held-out report, and a successful demo script. Every result in slides/report points to generated files. No claim of field-readiness or guaranteed improvement.


### Phase 7A — OpenCity/Marathahalli network reconstruction (only after P6 passes)

**Precondition:** P0–P6 are completed, tests and frontend build pass, the synthetic research evaluation has an honest completion status, the report/README are updated, and the project owner approves the P6 freeze. Do not begin this phase just because `docs/MARATHAHALLI_NETWORK_SPEC.md` exists.

**Goal:** use OpenCity's road/data view and available geospatial sources to build a source-grounded road topology around Marathahalli Bridge / Varthur Road / ORR. Preserve the existing synthetic network as the default and untouched reference. Do not replace the synthetic research results.

**Gate:** produce `docs/MARATHAHALLI_NETWORK_AUDIT.md`, provenance/assumption tables, generated network screenshot, route connectivity tests, legal movement/signal inventory and model-version metadata. Show verified/inferred/unknown distinctions and stop for the owner to approve the topology and proposed controlled node/phase plan. If sources are unavailable, report the blocker; do not fake a detailed site layout.

### Phase 7B — Add the approved site network to the completed system (COMPLETED)

**Precondition:** P7A review is explicitly approved. Do not change the synthetic implementation as a shortcut.

**Goal:** integrate an explicit site-network loader/selector, extend the safety state machine only as required by the approved site phase plan, validate site routes/demand, train and save a separate DQN model for the site's observation/action schema, run a separate site-specific research matrix using the seed protocol in `docs/RESEARCH_EVALUATION_SPEC.md`, and add a Network/Site Model view plus site/synthetic comparison selection to the existing React dashboard. Keep every network's aggregates separate and label site demand as synthetic unless measured counts are sourced.

**Gate:** site network generation is repeatable; route and signal legality tests pass; owner-approved assumptions are visible in the UI; all compatible controllers are compared fairly; incompatible policy cells remain blocked; the site model metadata matches the network/signal schema; site-specific report and downloadable artifacts are generated; existing synthetic tests/reports/dashboard modes continue to pass.

**Status:** Completed. Full 600-run site research matrix (`exp_marathahalli_site`) and 360-run site emergency matrix (`exp_marathahalli_emergency_360`) executed on held-out seeds 121..130; dedicated `SiteModelView.jsx` workspace mounted with 3-tier grade separation and 16-link phase machine breakdown; network toggles integrated into `Navbar.jsx`, `ResearchView.jsx`, and `LiveMonitorView.jsx`; all unit tests pass green (`pytest -q` 82/82 passed, frontend `npm test` 7/7 passed, Vite build clean).

## 8. Required research-grade experiment protocol

The **Phase A primary study for the initial upgrade must use the existing `synthetic` network** and the full contract in `docs/RESEARCH_EVALUATION_SPEC.md`. It is not just a report script: the CLI, raw artifacts, API lifecycle and React dashboard must all support it. A separate Phase B site-network study is allowed only after P6 has passed and P7A/P7B are approved/completed. Never mix network geometries in the same aggregate.

1. **Preserve and use the synthetic network for P0–P6:** keep existing patterns (`balanced`, `imbalanced_ns`, `imbalanced_ew`, `surge_north`) and policies (`fixed`, `fixed_webster`, `adaptive`, `pressure`) working on the existing network. Do not overwrite the pre-upgrade baseline or legacy result files. The Phase A research study and initial dashboard use this network. Existing CLI behavior remains backward compatible.
2. **Phase A crossed traffic-demand matrix (synthetic network):** introduce configurable `low`, `medium`, and `heavy` demand levels (initial multipliers 0.70, 1.00, 1.30; all centralized in config). Reuse the four existing reproducible patterns (`balanced`, `imbalanced_ns`, `imbalanced_ew`, `surge_north`) so medium demand stays backward-compatible. The Phase A matrix is 4 patterns × 3 levels × 5 policies × 10 research-test seeds (21–30) = 600 runs. Same condition/seed creates identical background routes for every policy. Add smoke, dry-run, chunked and resumable modes.
3. **Phase B site-network matrix (deferred):** only after P6 and approved P7A, map four demand patterns to the verified site entry approaches/movements, use a separately trained site-specific model, and run 4 site patterns × 3 levels × 5 compatible policies × 10 site research-test seeds (121–130) = up to 600 site runs. Define site training seeds 101–105 and validation seeds 106–110; never use 121–130 for tuning. If any legacy policy is incompatible with the approved phase plan, mark its cells blocked and the site study partial rather than forcing controller semantics. Do not run this matrix during P0–P6.
3. **Seed roles:** existing train seeds 1–5; new validation seeds 6–10; keep existing legacy held-out seeds 11–15 for compatibility; use research-only final test seeds 21–30. RL checkpoint/hyperparameter selection uses train/validation only, never the research test seeds.
4. **Metrics per run:** current metrics plus vehicle count/completions, mean wait, mean SUMO time loss, mean trip duration, p95 wait, mean/max queue, throughput count and rate, completion rate, per-approach completed sample counts/mean wait/p95 wait, NS-vs-EW mean waiting-time disparity, and max-min disparity across approach mean waits. Clearly define the population and units for every metric; return null (not zero) when a subgroup has no valid observations.
5. **Uncertainty and paired analysis:** for every condition and policy report seed count, mean, standard deviation, and a 95% paired-bootstrap confidence interval for difference from `fixed` for primary wait/time-loss metrics. Store per-seed paired deltas; use a configurable deterministic bootstrap RNG seed and record the method/resample count. Treat small-sample intervals as descriptive; do not claim a universal/statistically conclusive win based only on overlapping/non-overlapping intervals.
6. **Fairness interpretation:** show per-approach and per-direction results; define directional wait disparity as `abs(mean_wait_NS_origins - mean_wait_EW_origins)` using completed vehicles with known origin, with subgroup sample counts. Report the per-approach max-min gap too. A smaller gap means more even observed waiting, not necessarily better overall service; always pair it with total wait and demand profile.
7. **Emergency study:** a separately paired matrix, minimum: `balanced` and `surge_north` patterns × low/medium/heavy levels × `fixed`, `pressure`, `rl_dqn` (if trained) × priority off/on × the same 10 test seeds. Same ambulance event and identical non-emergency traffic routes in each paired condition. Preserve partial/failure rows.
8. **Deliverables:** immutable experiment config/manifest (schema version, policies, patterns, levels/multipliers, seeds, model ID/checksum, SUMO/Python/package versions, git commit if available, command, started/completed timestamps); raw run rows; aggregate mean/std; paired-delta + interval table; per-approach/direction fairness table; missing/failed-cell table; plots; Markdown report (PDF if existing export pipeline supports it); frontend downloadable artifact links. Write under unique `results/research/<experiment_id>/` directories; never overwrite the frozen baseline or type in metrics manually.
9. **Research & Evaluation dashboard:** let a user choose smoke/full or a bounded matrix, selected scenario patterns/levels/policies/seeds, run it through the API, see completed/running/failed/skipped counts and live progress, inspect comparisons, uncertainty, fairness, sample sizes and provenance, and download raw/aggregate/report artifacts. Disable run controls in snapshot mode. Mark partial matrices conspicuously.
10. **Reproducibility and honesty:** paired runs use shared route files and controlled seeds; no evaluation data leaks into training or model selection. Store stdout/stderr and per-cell failures, allow resume without rerunning completed valid cells, and only label an experiment `complete` if all requested cells have terminal successful results or its manifest explicitly labels the matrix as partial. Simulated results are not road-deployment evidence.

## 9. Definition of done

The upgrade is complete when all of the following are true:

- Original four policies remain available by their existing names and are covered by tests.
- DQN can be installed optionally, trained, saved, loaded and run through the normal simulation/CLI.
- Controller transitions always satisfy the safety invariant and clearance timings.
- Emergency event can be reproduced and priority can be toggled independently from the event itself.
- The final report honestly compares DQN and non-RL policies on held-out seeds, including regressions and variance.
- The React + Vite + JSX dashboard visualizes generated data and accurately communicates API connection, snapshot freshness, live-running, complete, failed, partial-matrix and no-data states.
- A first-class Research & Evaluation page can launch/inspect the crossed low/medium/heavy demand study, show paired seed-level results and confidence intervals, report directional/per-approach fairness, expose failures/missing matrix cells, and download the exact generated artifacts.
- Research matrices have immutable manifests, reproducible configuration and seeds, a resumable run ledger, and raw + aggregate outputs; there are tests for pairing, completeness, partial failures, uncertainty and null subgroup metrics.
- Frontend can be deployed to Vercel; full live simulation is documented as requiring a separately hosted Python/SUMO API.
- The UI-skill workflow was actually run, design-system outputs are saved, and the final implementation received animation/accessibility/edge-case review.
- `pytest -q` passes in the documented environment, plus the documented CLI smoke commands complete.
- README, SPEC, CHANGELOG, prompt plan and demo script agree with the current implementation.
- No generated result was hand-edited; no feature is described as live/real-world when it is simulated.

## 10. Optional installation notes

Do not add RL or API packages to the base `requirements.txt`. Keep the Python additions optional:

```powershell
python -m pip install -r requirements-rl.txt
python -m pip install -r requirements-api.txt
```

The dashboard is a separate JavaScript application under `frontend/`; install its packages with `npm install` (or `npm ci` when a lockfile exists) inside that directory. Do not create `requirements-dashboard.txt` and do not use Python dashboard libraries. Antigravity must first check which Python interpreter the current project uses and whether compatible wheels exist. If RL dependencies are incompatible with that interpreter, use a documented, separate compatible virtual environment rather than destabilizing the existing one.

Stable-Baselines3 installation requirements should be checked against the selected pinned/current version: https://stable-baselines3.readthedocs.io/en/master/guide/install.html .
