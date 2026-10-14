# DP1 Upgrade Decisions and Scope Guardrails

This file makes a few architectural choices explicit so the Antigravity agent does not invent a different project design mid-implementation.

## Chosen architecture

- **Implementation order:** first complete the entire advanced upgrade on the existing synthetic SUMO network. The Marathahalli Bridge / Varthur Road / ORR network is a deferred final addition after P6 passes; it must not delay or replace DQN, emergency priority, research evaluation, API, React dashboard, visual QA or report freeze.
- **Source accuracy:** OpenCity road centerlines/road widths do not by themselves prove lane count, signal placements, phase timing or grade separation. A source/confidence audit is required. Unknown values stay unknown until corroborated.
- **Deferred site scope:** in P7A/P7B, build a realistic site-area road topology with one owner-approved signal-controlled node or documented signal group. No city-wide/multi-junction coordination.
- **Research order:** P0 baseline audit → P1 safe synthetic control seam → P2 DQN environment/inference → P3 synthetic research matrix → P4 synthetic emergency tests → P5A API → P5B JSX dashboard → P5C skill-led UI QA/Vercel → P6 synthetic validation/report freeze → P7A OpenCity mapping + owner review → P7B site integration/model/evaluation/dashboard extension.

- **RL algorithm:** DQN with a two-action discrete interface: HOLD or REQUEST_SWITCH.
- **Decision cadence:** one simulation second, so reward and state have a stable per-second interpretation; during P0–P6 action means hold or request the next legal stage in the existing synthetic two-phase plan. Deferred P7B may generalize this only to the owner-approved site phase plan.
- **Safety:** shared phase machine alone executes phase transitions; controller/RL only requests a switch.
- **Reward:** primary signal is normalized sum of all approach queues. Optional waiting-time term must be explicitly configured and logged. No privileged knowledge of future demand.
- **Optional packages:** RL and dashboard libraries are installed through separate requirements files, never core requirements.
- **Emergency priority:** a separate flag applied to the same ambulance event, making priority-off/on a paired experiment.
- **Dashboard frontend:** React + Vite + JavaScript/JSX deployed on Vercel. P0–P6 dashboard contains synthetic simulation, controller, emergency and Research & Evaluation views only. Add the Network/Site Model view in P7B after P6 freeze and P7A owner approval. Never Streamlit, Dash, or Python-rendered UI.
- **API:** optional FastAPI service wrapping existing CLI/artifact outputs and telemetry; full live SUMO execution must run on a separate SUMO-capable Python host/container. Vercel frontend supports labelled read-only snapshot mode when no API is configured.
- **Evaluation seeds:** preserve existing `HELD_OUT_SEEDS` (11–15) for legacy synthetic commands; add `RL_VALIDATION_SEEDS` (6–10) and `RESEARCH_EVAL_SEEDS` (21–30) for Phase A synthetic research. For deferred Phase B, use separate site seed groups: train 101–105, validation 106–110, research test 121–130. Never tune against the relevant research-test seeds.
- **Research protocol:** Phase A crosses 4 existing synthetic patterns × low/medium/heavy × 5 policies × 10 test seeds (target 600 base runs), plus an emergency-priority paired study on synthetic. Phase B is later: after site approval, cross 4 site-appropriate patterns × 3 levels × 5 compatible policies × 10 site test seeds, with a separately trained model. Use resumable/chunked execution and never combine the two geometries in one aggregate.
- **Research UI:** include a dedicated React Research & Evaluation view. Evaluation is an implemented project capability, not only a write-up: launch/status/provenance/results/artifact downloads must be exposed through CLI and API and surfaced in JSX.
- **Demand-level compatibility:** medium multiplier is exactly 1.00 and retains the current demand rates; low/high multipliers are configurable (initially 0.70/1.30), with all values centralized in config.

## Why the agent should not begin with coordinated multi-intersection control

Marathahalli Bridge is not to be assumed to be a generic four-way at-grade intersection. Model the supported road topology and grade-separated connectors, but begin adaptive-control experiments at one verified signal-controlled node or signal group. Do not make every junction signalised, and do not make a 2D overpass crossing into a conflict. Coordinated multi-node control remains out of scope until this site's geometry, signal phases and single-node controller are validated.

## What counts as evidence

- The training reward shows learning dynamics; it does not by itself prove better traffic operations.
- Performance claims come from paired research test runs with identical background routes for the same scenario-pattern/load-level/seed, mean ± standard deviation, and paired-difference 95% confidence intervals.
- Directional fairness comes from per-vehicle origin attribution: publish per-approach and NS-versus-EW wait summaries plus sample counts. Interpret disparity alongside demand; it is not a standalone optimization objective.
- Emergency response claims come from actual emergency-vehicle records in SUMO `tripinfo.xml`, alongside impacts on normal traffic.
- Dashboard charts must load generated outputs and display sample count/seed context. During P0–P6, every view/run labels the network as synthetic. Only after P7B, where both network options exist, must views also distinguish `synthetic` from `marathahalli`, identify model version and show geometry/signal assumption status. Site-demand profiles remain synthetic unless real counts are sourced. The Research & Evaluation view exposes matrix progress/coverage, uncertainty, fairness and artifact exports. Empty data is an empty state, not a zero; partial experiments are never labelled complete.
- Historical `results/` files are not proof of current reproducibility. P0 regenerates and freezes a clean baseline.

## Mandatory UI/UX skill contract

Before implementing frontend UI, read `docs/UI_SKILL_CONTRACT.md`. The Antigravity agent must locate and actively use the installed `ui-ux-pro-max`, `Taste`, and `emil-design-eng` skills and the relevant `emilkowalski/skills` subskills. Persist a project-specific design system; make considered choices about typography, layout proportions, hierarchy, surface treatment, shadows and motion; then perform explicit visual/animation/edge-case review. If a named skill cannot be located, report that exact blocker and search the installed skill catalog paths before proceeding; do not claim the skill was used if it was not.
