# Phase 13 Report: Freeze Final Matrix and Smoke Run

**Status:** Complete  
**Date:** 2026-11-04  
**Verdict:** **QUALITY GATE PASSED (READY FOR FINAL EVALUATION)**  
**Frozen Tag:** `dp1-final-frozen`  
**Execution Script:** [`scripts/run_final.sh`](file:///e:/dp1-traffic-signal/scripts/run_final.sh) / [`scripts/run_final.py`](file:///e:/dp1-traffic-signal/scripts/run_final.py)  
**Experiment Specification:** [`experiments/final_matrix.yaml`](file:///e:/dp1-traffic-signal/experiments/final_matrix.yaml) & [`experiments/final_matrix.json`](file:///e:/dp1-traffic-signal/experiments/final_matrix.json)  
**Smoke Verification Suite:** [`results/research/exp_final_smoke_dev`](file:///e:/dp1-traffic-signal/results/research/exp_final_smoke_dev) (468/468 cells passing)

---

## 1. Executive Summary

Phase 13 establishes the **final frozen experimental matrix** for DP1 and verifies the complete end-to-end execution pipeline on dev seeds (101, 102) before executing on evaluation seeds (131–150).

### Key Outcomes:
1. **Proposed Policy Locked:** Following the **KEEP** verdict of Phase 12, **`hybrid_queue_adaptive_proj`** (de-oracled R4 base green + queue extension + measured-rate short-horizon projection) is locked as the primary proposed policy. The unprojected de-oracled baseline (`hybrid_queue_adaptive`) is preserved in the ablation matrix.
2. **Matrix Size Confirmed:**
   - **Main Matrix:** 10 policies $\times$ 18 conditions $\times$ 20 seeds (131–150) = **3,600 runs**.
   - **Ablation Sub-matrix:** 3 variants $\times$ 9 conditions $\times$ 20 seeds (131–150) = **540 runs**.
   - **Grand Total (Full):** **4,140 runs** (exact match to target specification).
   - **Cut Option (Fast Review):** **3,070 runs** (ablation seeds reduced to 10; 4 stationary-low conditions omitted across all policies, strictly adhering to the rule: *never reduce seeds or conditions for only some policies*).
3. **DQN Checksum & Compatibility Verified:** Model ID `dqn_marathahalli_all_s101_1791958726` verified with SHA-256 `ca46961a82ae9d9847ff3745b9fa5c3ae1be531c032b967fb18b5b9be2e73f59`, observation schema version 1.0.0, trained on seeds 101–105, successfully loading on all conditions.
4. **Smoke Run Quality Gate 100% Green:** 468 simulation cells executed across all 13 policies and 18 conditions on seeds 101 and 102:
   - **0 failures** (468 / 468 completed).
   - **0 NaN/Inf instances**.
   - **100% route hash equality** across policies per (scenario, demand level, seed).
   - **Zero safety invariant violations** in every signal trace.

---

## 2. Final Experiment Matrix Definition

### A. Main Policies (10 Roster)
All policies use frozen configurations established across Phases 1–12:

| # | Policy Identifier | Category | Configuration Source | Description |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `fixed` | Classical Baseline | `dp1/config.py:FIXED_MARATHAHALLI` | Field BTP weekday fixed-time plan (Varthur 105s, ORR 95s green). |
| 2 | `fixed_matched_cycle` | Classical Baseline | `dp1/config.py:FIXED_MATCHED_CYCLE` | Fixed-time plan matched to adaptive mean cycle time per condition. |
| 3 | `webster_measured` | Theoretical Baseline | `dp1/config.py:WEBSTER_MEASURED` | Webster equisaturation timing from online measured 300s warmup flows. |
| 4 | `webster_recalc` | Dynamic Baseline | `dp1/config.py:WEBSTER_RECALC` | Webster equisaturation timing recalculated dynamically every 300s. |
| 5 | `sumo_actuated` | Industry Standard | `dp1/config.py:SUMO_ACTUATED` | Native SUMO gap-out actuated signal with E2 detector gap thresholds. |
| 6 | `adaptive` | Queue-Proportional | `configs/final_adaptive.yaml` | Classical green duration proportional to observed queue lengths. |
| 7 | `pressure` | Max-Pressure | `dp1/config.py:PRESSURE` | Max-pressure greedy routing based on approach differential queues. |
| 8 | `queue_extension` | Actuated Extension | `configs/final_queue_extension.yaml` | Actuated green extension with gap-out and competing wait cap. |
| 9 | `rl_dqn` | Reinforcement Learning | `models/dqn_marathahalli_site_best.zip` | Deep Q-Network discrete action agent trained on Marathahalli junction. |
| 10 | **`hybrid_queue_adaptive_proj`** | **Proposed Policy** | `configs/final_hybrid_projection.yaml` | **Proposed:** De-oracled Webster base + extension + measured queue projection. |

### B. Conditions (18 Total)
- **12 Stationary Conditions:** 4 patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`) $\times$ 3 levels (`low`, `medium`, `heavy`).
- **6 Non-Stationary Conditions:** 3 dynamic scenarios (`ramp_peak`, `surge_shift`, `lane_closure`) $\times$ 2 levels (`medium`, `heavy`).

### C. Ablation Sub-matrix (540 Cells)
Isolates the architectural contributions of each rung from `docs/ablation_ladder.md`:
1. **`hybrid_queue_adaptive` (Rung R4):** Proposed architecture without projection (frozen unprojected baseline from Phase 11).
2. **`hybrid_r3` (Rung R4 + R3):** Tests queue-aware fairness soft-wait scaling on top of R4.
3. **`hybrid_oracle_seeded` (Rung R0):** Legacy reference hybrid seeded with true offline scenario demand tables (oracle leak benchmark).
- **Conditions (9):** All 6 non-stationary conditions + 3 stationary heavy conditions (`balanced/heavy`, `imbalanced_orr/heavy`, `imbalanced_varthur/heavy`).
- **Seeds:** 131–150 ($n=20$).

### D. Diagnostic Sub-matrix
- **`webster_oracle`:** Fixed Webster plan calculated directly from ground-truth scenario demand matrices (offline upper bound).

---

## 3. Cell Count & Runtime Projections

### A. Cell Totals
- **Main Matrix:** $10 \text{ policies} \times 18 \text{ conditions} \times 20 \text{ seeds} = \mathbf{3,600\text{ runs}}$.
- **Ablation Matrix:** $3 \text{ variants} \times 9 \text{ conditions} \times 20 \text{ seeds} = \mathbf{540\text{ runs}}$.
- **Grand Total (Full Matrix):** $3,600 + 540 = \mathbf{4,140\text{ runs}}$.
- **Grand Total (Cut Matrix for Fast Review):**
  - Ablation seeds reduced to 10 ($3 \times 9 \times 10 = 270$ runs).
  - 4 stationary-low conditions omitted across all main policies ($10 \times 14 \times 20 = 2,800$ runs).
  - Grand total cut: $2,800 + 270 = \mathbf{3,070\text{ runs}}$.

### B. Empirical Runtime per Policy (Measured on Machine)
Derived from 468 completed simulations in `results/research/exp_final_smoke_dev`:

| Policy | Completed Runs | Median Runtime (s) | Mean Runtime (s) | P95 Runtime (s) | Max Runtime (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `fixed` | 36 | 33.65 | 51.07 | 157.31 | 185.20 |
| `fixed_matched_cycle` | 36 | 29.30 | 45.57 | 150.48 | 163.06 |
| `webster_measured` | 36 | 30.24 | 47.07 | 145.84 | 162.49 |
| `webster_recalc` | 36 | 30.50 | 47.96 | 146.61 | 161.18 |
| `sumo_actuated` | 36 | 28.35 | 44.76 | 140.09 | 151.66 |
| `adaptive` | 36 | 27.70 | 44.47 | 141.17 | 155.57 |
| `pressure` | 36 | 28.71 | 44.70 | 137.11 | 146.09 |
| `queue_extension` | 36 | 28.75 | 45.84 | 132.20 | 149.84 |
| `rl_dqn` | 36 | 34.57 | 55.91 | 148.09 | 165.12 |
| **`hybrid_queue_adaptive_proj`** | 36 | **30.63** | **48.89** | **144.24** | **159.19** |
| `hybrid_queue_adaptive` | 36 | 30.62 | 47.51 | 141.80 | 151.37 |
| `hybrid_r3` | 36 | 29.33 | 45.95 | 147.17 | 156.37 |
| `hybrid_oracle_seeded` | 36 | 30.38 | 46.63 | 152.29 | 158.48 |
| **Overall Grand Mean** | **468** | **30.21** | **47.66** | **145.72** | **185.20** |

### C. Estimated Total Execution Times

| Worker Configuration | Full Matrix (4,140 runs) | Cut Matrix (3,070 runs) | Feasibility / Recommendation |
| :---: | :---: | :---: | :--- |
| **1 Worker (Serial)** | 54.8 hours | 40.7 hours | Unfeasible for single session. |
| **2 Workers** | 27.4 hours | 20.3 hours | Too slow for review deadline. |
| **4 Workers** | 13.7 hours | 10.2 hours | Conservative background option. |
| **8 Workers (Available CPU)** | **6.86 hours** | **5.08 hours** | **Recommended for production run.** |

---

## 4. DQN Controller Verification

As required by Task 4:
- **Model Checksum:** `ca46961a82ae9d9847ff3745b9fa5c3ae1be531c032b967fb18b5b9be2e73f59` (SHA-256).
- **Model Artifact:** [`models/dqn_marathahalli_site_best.zip`](file:///e:/dp1-traffic-signal/models/dqn_marathahalli_site_best.zip).
- **Companion Metadata:** [`models/dqn_marathahalli_site_best.metadata.json`](file:///e:/dp1-traffic-signal/models/dqn_marathahalli_site_best.metadata.json).
- **Run ID:** `dqn_marathahalli_all_s101_1791958726`.
- **Observation Schema:** Dimension 11 (`q_N`, `q_S`, `q_E`, `q_W` normalized + axis indicators + phase one-hot + elapsed green + timeline fraction). Schema version `1.0.0`.
- **Training Seeds:** `[101, 102, 103, 104, 105]`.
- **Load Verification:** Successfully loaded and executed in 36 smoke cells with zero crashes, generating valid actuation decisions (`mean_s = 55.91s`).

---

## 5. Automated Smoke Verification Suite Results

The verification script [`dp1/research/run_smoke_dev.py`](file:///e:/dp1-traffic-signal/dp1/research/run_smoke_dev.py) completed with zero errors:

```json
{
  "total_cells": 468,
  "completed_cells": 468,
  "failed_cells": 0,
  "nan_inf_count": 0,
  "route_hash_match": true,
  "zero_safety_violations": true,
  "verification_passed": true,
  "verification_errors": []
}
```

### Detailed Quality Gates Passed:
1. **Completion Check:** 468 / 468 cells completed (100.0% completion rate).
2. **Numerical Validity:** Zero NaN, Inf, or null values in any primary metric (`avg_wait_s`, `p95_wait_s`, `avg_queue_m`, `approach_wait_gap_s`).
3. **Route Hash Determinism:** For every `(scenario, demand_level, seed)` triplet, all 13 policies received 100% byte-for-byte identical vehicle routes and demand schedules.
4. **Safety Invariant Enforcement:** Every phase transition across all 468 timeseries strictly satisfied `GREEN -> YELLOW -> ALL_RED -> GREEN`. Yellow duration was exactly $3.0\text{ s}$ and all-red clearance was exactly $2.0\text{ s}$. Never green on opposing axes.
5. **Port Contention Recovery:** Automatic TraCI retry logic recovered from temporary socket collisions without aborting any runs.

---

## 6. Production Execution Script & Manifest Protection

The execution scripts [`scripts/run_final.py`](file:///e:/dp1-traffic-signal/scripts/run_final.py) and [`scripts/run_final.sh`](file:///e:/dp1-traffic-signal/scripts/run_final.sh) provide strict quality controls:

1. **Working Tree Cleanliness Enforcement:**
   - Halts immediately if uncommitted files or unstaged modifications are present.
2. **Frozen Tag Verification:**
   - Refuses to start unless `HEAD` commit equals `dp1-final-frozen`.
3. **Environment Manifest:**
   - Writes `results/research/exp_marathahalli_improve_final/manifest.json` recording Git commit hash, SUMO version, Python version, and dependency versions (`torch`, `stable-baselines3`, `traci`, `pandas`, `numpy`).
4. **Crash-Resilience & Resumption:**
   - Checks existing `metrics.json` and `timeseries.csv`; completed cells are skipped and never rerun.
5. **Audit Logging:**
   - Real-time logging of cell completion status and runtime to `matrix_status.csv`.
6. **Dry-Run Capability:**
   - `--dry-run` displays exact cell lists and counts without invoking SUMO.
   - Supports `--cut` to execute the reduced 3,070 cell matrix.

---

## 7. Deliverables Checklist & Freeze Confirmation

- [x] Matrix Specification: [`experiments/final_matrix.yaml`](file:///e:/dp1-traffic-signal/experiments/final_matrix.yaml) & [`experiments/final_matrix.json`](file:///e:/dp1-traffic-signal/experiments/final_matrix.json).
- [x] Production Runner: [`scripts/run_final.sh`](file:///e:/dp1-traffic-signal/scripts/run_final.sh) & [`scripts/run_final.py`](file:///e:/dp1-traffic-signal/scripts/run_final.py).
- [x] Smoke Run Artifacts: [`results/research/exp_final_smoke_dev`](file:///e:/dp1-traffic-signal/results/research/exp_final_smoke_dev) (`smoke_cells.csv`, `policy_performance.csv`, `smoke_verification_report.json`).
- [x] Phase Report: [`docs/phase13_report.md`](file:///e:/dp1-traffic-signal/docs/phase13_report.md).
- [x] Quality Gate: Verified 468 / 468 smoke runs green.
- [x] Frozen Tag: `dp1-final-frozen`.

**NO CODE OR CONFIGURATION CHANGES FROM THIS POINT FORWARD.**  
**DO NOT RUN THE FINAL MATRIX (SEEDS 131–150) UNTIL EXPLICITLY DIRECTED.**
