# Phase 13 Report: Final Experiment Matrix Re-Freeze (Pre-Registration Amendment 3)

**Status:** Complete — Re-Frozen under Amendment 3 (Phase F1)  
**Date:** 2026-11-04  
**Verdict:** **FROZEN & VERIFIED (PENDING USER APPROVAL TO TAG & LAUNCH)**  
**Tag Status:** `dp1-final-frozen` deleted as instructed; awaiting explicit user approval before re-tagging.  
**Execution Script:** [`scripts/run_final.py`](file:///e:/dp1-traffic-signal/scripts/run_final.py)  
**Experiment Specifications:** [`experiments/final_matrix.yaml`](file:///e:/dp1-traffic-signal/experiments/final_matrix.yaml) & [`experiments/final_matrix.json`](file:///e:/dp1-traffic-signal/experiments/final_matrix.json)  
**Pre-Registration Authority:** [`docs/PREREGISTRATION_AMENDMENT_3.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_3.md)  
**Analysis Pipeline:** [`analysis/run_analysis.py`](file:///e:/dp1-traffic-signal/analysis/run_analysis.py)  

---

## 1. Executive Summary & Amendment 3 Corrections

Phase F1 supersedes earlier Phase 13 configurations by correcting the controller roster, evaluation criteria, and matrix scope under **Pre-Registration Amendment 3**:

1. **Phase 12 Verdict Re-Evaluation (CUT):**
   - Under `docs/PREREGISTRATION.md` Section 6, a candidate rung is kept iff at least one primary metric (`p95 wait`, `gt_ext_max_queue_m`, or `approach wait gap`) achieves a paired 95% bootstrap confidence interval strictly excluding zero.
   - On validation seeds 106–110, p95 wait CI was `[-13.69, +4.33] s` (spans zero), approach wait gap CI was `[-3.53, +2.60] s` (spans zero), and detector queue worsened (+3.96 m).
   - Verdict: **Strictly CUT**. Projection remains disabled by default (`projection_enabled = False`), config archived as [`configs/experimental_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/experimental_hybrid_projection.yaml), and scientific wording standardized to **"proactive, state-aware intervention"**.
2. **Proposed Policy & Reference Comparator:**
   - **Proposed Policy:** `hybrid_queue_adaptive` (R4 measured base green, no projection, default parameters).
   - **Primary Reference:** `webster_measured` (realistic, online measured Webster cycle).
3. **Core Benchmark Matrix Scope ($N = 384$ runs):**
   - **Main Matrix (7 policies):** `fixed`, `webster_measured`, `webster_recalc`, `sumo_actuated`, `adaptive`, `queue_extension`, `hybrid_queue_adaptive`.
   - **Ablation Policy (1 policy):** `hybrid_oracle_seeded` (R0 oracle leak benchmark).
   - **Conditions (6):** `balanced-low`, `balanced-heavy`, `imbalanced_orr-heavy`, `ramp_peak-medium`, `surge_shift-medium`, `lane_closure-medium`.
   - **Seeds:** 131–138 (8 seeds), executed **SEED-MAJOR** (48 runs per seed block).
   - **Total:** $7 \times 6 \times 8 = 336$ (main) $+ 1 \times 6 \times 8 = 48$ (ablation) = **384 runs**.
4. **Mandatory Disclosures:**
   - Dropped: `rl_dqn`, `pressure`, `fixed_matched_cycle` (`ORACLE-CYCLE`), `webster_oracle`, equal-budget tuning, `hybrid_r3`, projection ablation, seeds 139–150, and 12 unused scenario-level conditions.
5. **Runner Isolation & Collision-Free Ports:**
   - `scripts/run_final.py` updated to execute **one fresh subprocess per simulation**.
   - Worker-dedicated port allocation ($20000 + 200 \cdot w + \text{sim}\%100$) mathematically guarantees collision-free TraCI sockets, eliminating `WinError 10061`.
   - Determinism quality gate passed: identical config run twice gives byte-identical `decisions.csv` SHA256 (`tests/test_runner_determinism.py`).
   - All 23 targeted test cases passed.

---

## 2. Final Experiment Matrix Specification

```yaml
experiment_id: exp_marathahalli_improve_final
proposed_policy: hybrid_queue_adaptive (R4 de-oracled default)
reference_policy: webster_measured
ordering: seed_major
seeds: [131, 132, 133, 134, 135, 136, 137, 138]  # N = 8
runs_per_seed_block: 48 (42 main + 6 ablation)
total_runs: 384
```

### Main Roster (7 Policies)
1. `fixed`: Field BTP fixed-time plan (Varthur 105s, ORR 95s).
2. `webster_measured`: Online measured Webster timing from 300s warmup flows.
3. `webster_recalc`: Recalculated Webster baseline updated every 300s.
4. `sumo_actuated`: Industry standard detector-actuated logic (minDur=10s, maxDur=60s).
5. `adaptive`: Classical queue-proportional controller.
6. `queue_extension`: Actuated queue-extension with green cap.
7. `hybrid_queue_adaptive`: Proposed policy (R4 measured base + state-aware queue extension).

### Ablation Roster (1 Policy)
8. `hybrid_oracle_seeded`: Legacy R0 hybrid seeded directly from true scenario demand tables.

---

## 3. Runner Architecture & Execution Plan

### A. Fresh Process Subprocess Model
Every simulation cell is executed via an isolated child process:
```bash
python scripts/run_final.py --cell-worker --scenario ... --policy ... --seed ... --port ...
```
This guarantees clean memory boundaries, zero TraCI state leakage, and instant crash containment.

### B. Collision-Free Port Guarantee
Worker $w \in \{0, 1, 2, 3, 4\}$ binds to dedicated port range $[20000 + 200w, 20000 + 200w + 99]$. No two concurrent workers can ever select the same TCP port.

### C. Stopping Rule & Wall-Clock Bound
- Stopping rule: `--max-hours` wall-clock limit.
- If the limit is reached, the runner gracefully completes the active seed block in its entirety and terminates.
- Minimum complete seeds for valid analysis: 6 seeds (e.g. 131–136).

### D. Exact Launch Command (Pending User Execution)
```powershell
.venv\Scripts\python scripts/run_final.py --workers 5 --max-hours 1.3
```
- **Estimated Runtime:** $\approx 64.0\text{ minutes}$ ($1.07\text{ hours}$ at $\approx 10\text{ s/run}$).

---

## 4. Analysis Pipeline Verification (`analysis/run_analysis.py`)

The automated analysis pipeline was implemented and validated against dev smoke data:
1. **Paired Bootstrap:** 10,000 resamples with fixed seed `seed = 42`.
2. **Multiplicity Control:** Holm-Bonferroni correction applied across the 3 primary metrics (`p95_wait_s`, `gt_ext_max_queue_m`, `approach_wait_gap_s`).
3. **Sensitivity Analysis:** Pre-declared post-warmup evaluation ($t \ge 300\text{ s}$).
4. **Queue-First Tables:** Approach-level extended queue metrics and detector saturation fractions.
5. **Overloaded Cell Detection:** Flags runs where queues reach ramp boundaries ($\ge 120\text{ m}$) or unfinished vehicles $> 0$.
6. **Report Generation:** Generates [`docs/RESULTS_SUMMARY.md`](file:///e:/dp1-traffic-signal/docs/RESULTS_SUMMARY.md).
7. **Mathematical Accuracy:** 5 random condition means were recomputed independently directly from raw simulation files; all matched pipeline outputs with $0.000000$ error.
