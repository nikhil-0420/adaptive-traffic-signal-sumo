# DP1 Upgrade Decisions and Scope Guardrails

This file makes a few architectural choices explicit so the Antigravity agent does not invent a different project design mid-implementation.

## Chosen architecture

- **RL algorithm:** DQN with a two-action discrete interface: HOLD or REQUEST_SWITCH.
- **Decision cadence:** one simulation second, so reward and state have a stable per-second interpretation.
- **Safety:** shared phase machine alone executes phase transitions; controller/RL only requests a switch.
- **Reward:** primary signal is normalized sum of all approach queues. Optional waiting-time term must be explicitly configured and logged. No privileged knowledge of future demand.
- **Optional packages:** RL and dashboard libraries are installed through separate requirements files, never core requirements.
- **Emergency priority:** a separate flag applied to the same ambulance event, making priority-off/on a paired experiment.
- **Dashboard frontend:** React + Vite + JavaScript/JSX deployed on Vercel. Never Streamlit, Dash, or Python-rendered UI.
- **API:** optional FastAPI service wrapping existing CLI/artifact outputs and telemetry; full live SUMO execution must run on a separate SUMO-capable Python host/container. Vercel frontend supports labelled read-only snapshot mode when no API is configured.
- **Evaluation:** preserve existing `HELD_OUT_SEEDS` (11–15) for legacy commands; add `RL_VALIDATION_SEEDS` (6–10) and `RESEARCH_EVAL_SEEDS` (21–30) for the new research protocol so the final study uses a fresh, explicit test seed range. Train/model selection must never use 21–30.
- **Research protocol:** cross 4 existing scenario patterns × low/medium/heavy load multipliers × 5 policies × 10 research test seeds (600 base runs), with resumable/chunked execution. The focused emergency study covers balanced + north-surge patterns × 3 load levels × fixed/pressure/DQN × priority off/on × the same 10 test seeds.
- **Research UI:** include a dedicated React Research & Evaluation view. Evaluation is an implemented project capability, not only a write-up: launch/status/provenance/results/artifact downloads must be exposed through CLI and API and surfaced in JSX.
- **Demand-level compatibility:** medium multiplier is exactly 1.00 and retains the current demand rates; low/high multipliers are configurable (initially 0.70/1.30), with all values centralized in config.

## Why the agent should not begin with multi-intersection support

The current `SignalStates`, generated junction, queue sensors, demand model, fixed plans and test suite all target one synthetic 4-way junction with two signal axes. A multi-intersection refactor would multiply the surface area and risk the core safety guarantee. It is explicitly postponed until this single-junction upgrade is trained, measured and documented.

## What counts as evidence

- The training reward shows learning dynamics; it does not by itself prove better traffic operations.
- Performance claims come from paired research test runs with identical background routes for the same scenario-pattern/load-level/seed, mean ± standard deviation, and paired-difference 95% confidence intervals.
- Directional fairness comes from per-vehicle origin attribution: publish per-approach and NS-versus-EW wait summaries plus sample counts. Interpret disparity alongside demand; it is not a standalone optimization objective.
- Emergency response claims come from actual emergency-vehicle records in SUMO `tripinfo.xml`, alongside impacts on normal traffic.
- Dashboard charts must load generated outputs and display sample count/seed context. The Research & Evaluation view exposes matrix progress/coverage, uncertainty, fairness and artifact exports. Empty data is an empty state, not a zero; partial experiments are never labelled complete.
- Historical `results/` files are not proof of current reproducibility. P0 regenerates and freezes a clean baseline.

## Mandatory UI/UX skill contract

Before implementing frontend UI, read `docs/UI_SKILL_CONTRACT.md`. The Antigravity agent must locate and actively use the installed `ui-ux-pro-max`, `Taste`, and `emil-design-eng` skills and the relevant `emilkowalski/skills` subskills. Persist a project-specific design system; make considered choices about typography, layout proportions, hierarchy, surface treatment, shadows and motion; then perform explicit visual/animation/edge-case review. If a named skill cannot be located, report that exact blocker and search the installed skill catalog paths before proceeding; do not claim the skill was used if it was not.
