You are working on my DP1 research project. Read this entire message carefully; it is your full context. I cannot attach files, so everything you need is here. You will work phase by phase. I will give you ONE phase at a time. Never start the next phase on your own.

==================== PROJECT ====================
Title: "Queue-Length-Aware Adaptive Signal Control and Predictive Intervention".
Institution: Alliance University, Dept. of AI & Data Science, Design Project 1 (DP1).
Stack: Eclipse SUMO + TraCI (Python) microscopic simulation; FastAPI adapter; React + Vite + JSX dashboard (product name shown in the UI: "Phasora"). Frontend deploys statically on Vercel; live SUMO needs a separate Python/SUMO backend.
Evidence type: SUMO simulation only. Not a field deployment. No real CCTV/loop/BTP feeds.

Site model: Marathahalli Bridge / Varthur Road / Outer Ring Road (ORR), Bengaluru. One controlled SURFACE signal node: marathahalli_tls. The model also contains an elevated Varthur Road flyover and ORR bypass/underpass paths that are NOT controlled by this signal. Geometry is geographically grounded (BBMP centreline, OpenCity road width, BTP signal timing doc) but lane counts, ramp radii and flyover elevation (about +6.5 to +7 m) are inferred/modelled, not surveyed. Traffic demand is synthetic. It is not a certified digital twin.

Approaches (reported mapping; verify against net XML before relying on it): North = leg_orr_n_in lanes _0,_1; South = leg_orr_s_in; East = leg_wf_in; West = leg_hal_in. Phase groups: NS (ORR) and EW (Varthur). 16 controlled links: 0-3 N, 4-7 E, 8-11 S, 12-15 W. Phase strings: NS green GGGgrrrrGGGgrrrr; EW green rrrrGGGgrrrrGGGg; all-red rrrrrrrrrrrrrrrr; yellows with y. Yellow 3 s, all-red 2 s. BTP fixed plan adaptation: 105 s EW green, 95 s NS green (pedestrian phase omitted).
Detectors: eight E2 lane-area detectors (two per approach), span about 24.9 m (pos -25.0, endPos -0.1; verify in files). Sensor status: MEASURING, SATURATED (queue within 0.5 m of the span), CONFIRMED_ZERO, OFFLINE (data_valid false; never treat as zero).
Queue definitions: approach queue length = MAX over lane queue extents (never sum lanes); queued vehicle count = SUM over lanes. Detector-visible queue and simulator ground-truth queue are separate things; never silently substitute one for the other.

==================== POLICIES ====================
Site policies: fixed (BTP-adapted fixed time), fixed_webster, adaptive (legacy queue-adaptive), pressure, queue_extension (bounded rule-based; initial score weights 0.5 queue / 0.3 wait / 0.2 arrivals, verify in code), rl_dqn (DQN via shared safety state machine), hybrid_queue_adaptive (the proposed policy).
Hybrid behaviour: reads approach queues and demand measures, decides HOLD / bounded EXTEND (+3.0 s steps seen in a trace) / REQUEST_SWITCH, with a competing-direction fairness guard (switch forced when competing red wait reaches 35 s; saved trace showed switch at 36.0 s). Decision log separates proposed_action, applied_action, decision_outcome, reason_code, reason, g_base_s, delta_g_req_s, delta_g_app_s, g_extra_s, target_green_s, elapsed_s, actual_green_s, per-approach queues. A requested extension is NOT an applied extension; use delta_g_app_s for applied. The hybrid's baseline green in the saved trace was g_base_s = 15.0 s. Read the exact formulas from dp1/controllers/hybrid_queue_adaptive.py and dp1/config.py; never assume the queue_extension weights apply to the hybrid.
ALL controllers send requests through the shared safety state machine (dp1/controllers/base.py): GREEN -> YELLOW -> ALL_RED -> next legal GREEN. No controller may write a signal string directly.

==================== EXISTING RESULTS (exp_marathahalli_hybrid_840) ====================
Matrix: 4 patterns (balanced, imbalanced_orr, imbalanced_varthur, surge_orr_north) x 3 levels (low 0.70x, medium 1.00x, heavy 1.30x) x 7 policies x 10 seeds (121-130) = 840 runs. Reported grand-mean waiting time (s): fixed 60.27; fixed_webster 55.77; adaptive 55.67; pressure 55.63; rl_dqn 55.70; queue_extension 55.51; hybrid 55.49. Paired bootstrap shows statistical parity among leading dynamic controllers.
KEY PROBLEM: about 94% of the hybrid's gain over fixed already comes from Webster (4.50 of 4.78 s). Hybrid vs Webster is only about 0.28 s (about 0.5%). In balanced-low the hybrid is worse than adaptive/pressure (8.00 s vs 7.38 s). Existing patterns are stationary, so adaptive control has little headroom. Paired deltas were against fixed, which flatters everything. Detector saturation may limit visibility in heavy demand (hypothesis, to be checked, not assumed). The separate emergency study (exp_marathahalli_emergency_360) does NOT include the hybrid. Other experiment IDs that must never be mixed: exp_marathahalli_site_720, exp_marathahalli_site (600), exp_primary_720 (synthetic network, not Marathahalli).
Telemetry/UI findings so far: Live Twin Monitor shows a dark isometric 2.5D map ("2.5D Iso / Top-Down" toggle, "Explode 3-Tier View", zoom up to 350%); vehicles are hard to see during simulation (small/low contrast, possibly drawn under the flyover deck); HUD said "3 active vehs"; banner says "REAL-TIME TRACI LIVE TWIN"; an event card says "Early Gap-Out Terminated: No vehicles detected on stop-line detector for 3s; initiating yellow clearance" and another "+3.0s Green Extended: Continuous arrivals on NS; opposing queues within fairness bounds" (unclear whether these strings come from the controller's logged reason or are built in the frontend; must be checked). Earlier runs also showed replay 404s, an HTML-parsed-as-JSON error and 409 run-launch conflicts.

==================== THE PLAN (you execute it phase by phase) ====================
Goal: the research question, pre-registered: "Does queue-aware adaptive control improve p95 waiting time, peak queue and directional fairness under non-stationary demand, without a mean-waiting-time penalty versus Webster-based fixed-time control?" A negative or mixed answer is acceptable. Do not force a win.
Phases: 0 setup/pre-registration; 1 UI audit; 2 vehicle visibility fix; 3 network export for 3D; 4 3D scene; 5 3D vehicles/signals/queues; 6 camera/labels/performance/QA/merge; 7 research baseline tag + diagnostics; 8 freeze non-stationary scenarios (ramp_peak, surge_shift, lane_closure); 9 add baselines (webster_measured, webster_recalc, fixed_matched_cycle, sumo_actuated); 10 ablation ladder (one controller change at a time); 11 equal-budget tuning; 12 short-horizon projection; 13 freeze final matrix + smoke run; 14 final run on seeds 131-150; 15 analysis; 16 paper update.

==================== HARD RULES (all phases) ====================
SEEDS
- 101-105 = development (build, debug, tune, UI testing).
- 106-110 = validation (accept/reject changes).
- 121-130 = already seen: EXPLORATORY ONLY. Never use them to tune, select or accept changes.
- 131-150 = FINAL evaluation. You must NOT run, open, plot or summarise anything on seeds 131-150 unless the phase prompt explicitly says "final run". If you accidentally touch them, stop and tell me.
INTEGRITY
- Never invent numbers, formulas, parameters, file paths, references or results. Every figure you report must come from a raw artifact, with the file and exact command named.
- If a path/name I give does not exist, search the repo for the closest match, report it, and continue only if unambiguous; otherwise ask.
- If a value is unknown, write "UNKNOWN" and say what is needed. Never use a textbook default.
- Never overwrite an existing experiment directory. Create new experiment IDs. Never hand-edit raw results. Never delete raw results.
- If a result looks bad, report it. Do not rerun cells because a result looked unfavourable. Only rerun cells that crashed.
SAFETY AND TERMINOLOGY
- Safety state machine rules above are inviolable. Sequence GREEN -> YELLOW(3 s) -> ALL_RED(2 s) -> next legal GREEN.
- "Predictive intervention" means proactive intervention from current and recent measurements. Do NOT add LSTM/GRU/long-horizon forecasting.
- OFFLINE is never zero. Missing subgroup data stays null, not zero.
- SUMO timeLoss is not renamed "signal delay".
UI RULES (phases 1-6)
- Frontend-only by default. Do not change simulation behaviour, controllers, queue measurement, metrics or recorded run artifacts. Never edit dp1/runner.py, controllers, queues or metrics for UI reasons. The ONLY backend change allowed is adding vehicle elevation (z) to the telemetry payload in the API/telemetry layer in Phase 5, and it requires a regression test proving byte-identical raw_runs.csv, decisions.csv and timeseries.csv (excluding timestamps) on a fixed dev seed with and without the change.
- Never fake data: no invented vehicles, queues, signal states or decision text. Reason text shown in the UI must come from the logged reason/reason_code.
- Live vs replay vs snapshot must be labelled correctly. "Live" only when a real run ID is advancing from an active SUMO/TraCI process.
- Light mode, dark mode and mobile must keep working. Provide before/after screenshots for visual changes.
PROCESS
- Work on branch dp1-improve. Commit often with clear messages. Tag at the end of each phase as the prompt says.
- Add/update tests for what you change. Run the full test suite before reporting.
- Log the environment (SUMO version, Python version, package versions, git commit) in every report.
- At the end of each phase write the report file named in the prompt, then STOP and wait.
REPORT FORMAT (every phase)
1. What you did (short bullets)  2. Files created/changed  3. Exact commands run  4. Results (tables from raw data, with source file for each)  5. Problems, surprises, anything contradicting this plan  6. DECISION NEEDED items (questions for me)  7. Checklist: seed rules respected? no experiment overwritten? tests passing?

Acknowledge these rules in four lines max, then wait for the phase prompt.
