# Research & Evaluation Workspace — Design Guidelines

## Purpose
Dedicated research workbench for executing, tracking, and analyzing large-scale simulation matrices ($N=600$ full matrix, smoke tests, and custom evaluations). Fully adheres to `docs/RESEARCH_EVALUATION_SPEC.md`.

## Key Sections & Features
1. **Experiment Launcher (API Mode Only):**
   - Preset selector: `Smoke (3 cells)`, `Full 600-cell Matrix`, or `Custom Filter`.
   - Pattern filters: multi-select across scenarios.
   - Demand level filters: `low`, `medium`, `heavy`.
   - Policy filters: `fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`.
   - Seed selection (with strict separation between train seeds 1-5 and evaluation seeds 21-30).
   - Parallel jobs slider (1 to 8 workers).
   - "Launch Experiment" button (disabled with explanation in Read-Only Snapshot Mode).
2. **Live Matrix Execution Progress:**
   - Granular progress bar and status badges: Total Cells, Complete, Running, Pending, Failed, Blocked.
   - Real-time cell progress table with status indicator and elapsed execution time.
   - "Cancel Experiment" button for running jobs.
3. **Primary Evaluation Results View:**
   - **Aggregate Table:** Mean $\pm$ SD waiting time, 95% bootstrap confidence intervals, throughput, and completion rate per policy/scenario combination.
   - **Paired Deltas vs Fixed Baseline:** Clear table showing $\Delta \text{Wait (s)} = \text{Candidate} - \text{Fixed}$, 95% paired percentile bootstrap CIs, and whether difference is statistically significant.
   - **Directional Fairness Matrix:** Directional disparity ($|\overline{W}_{NS} - \overline{W}_{EW}|$) and Approach wait gap ($\max - \min$).
4. **Artifact Downloads Inventory:**
   - Download links for allowlisted experiment outputs:
     - `report.md` (Scientific markdown report)
     - `aggregate.csv`
     - `raw_runs.csv`
     - `paired_deltas.csv`
     - `fairness_by_approach.csv`
     - `fairness_by_direction.csv`
     - `manifest.json`
     - `matrix_status.csv`
