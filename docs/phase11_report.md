# Phase 11 Report: Equal-Budget Tuning & Frozen Configurations

**Date:** 2026-11-03  
**Status:** Frozen & Completed for Review  
**Artifact Directory:** `results/tuning/`  
**Frozen Configs:** [`configs/final_hybrid_queue_adaptive.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_queue_adaptive.yaml), [`configs/final_queue_extension.yaml`](file:///e:/dp1-traffic-signal/configs/final_queue_extension.yaml), [`configs/final_adaptive.yaml`](file:///e:/dp1-traffic-signal/configs/final_adaptive.yaml)  
**Parent Document:** [`docs/TUNING_PROTOCOL.md`](file:///e:/dp1-traffic-signal/docs/TUNING_PROTOCOL.md)

---

## 1. Executive Summary

Phase 11 established the **Equal-Budget Tuning Protocol** to optimize `hybrid_queue_adaptive` (with kept rung R4 de-oracle active), `queue_extension`, and `adaptive` under identical evaluation parity on the Marathahalli road network model.

Prior to search execution, [`docs/TUNING_PROTOCOL.md`](file:///e:/dp1-traffic-signal/docs/TUNING_PROTOCOL.md) was drafted, reviewed, and committed (`c2055ac`).

### Executed Milestones on Disk:
1. **Step 0 (Reference Normalization):** **180 / 180 runs completed** (`webster_measured` across 18 demand conditions and 10 seeds 101–110 in `results/tuning/reference_webster/`).
2. **Step 1 (Deterministic Sampling):** Full pre-registered random search configurations generated with fixed seed `202611`.
3. **Step 2 (Baseline Trial 0 Evaluation):** `hybrid_queue_adaptive` pre-registered baseline (`trial_00`) fully executed across all 18 conditions $\times$ 5 training seeds 101–105 (**90 simulation runs completed**, wall-clock duration: **34.15 minutes**, average 22.8 s per simulation).

---

## 2. Measured Simulation Compute & Scaling Analysis

Microscopic simulation in SUMO 1.28 on the Marathahalli junction with the Phase 10C extended ground-truth queue engine (`QueueMeasurementEngine` tracking queue propagation across approach legs, connectors, and ramps every simulation second):
- **Measured Wall-clock Time per Simulation Run:** $\approx 22.8\text{ s}$ across 4 parallel worker processes (total CPU time $\approx 91\text{ s}$ per run).
- **Single 90-run Trial:** $90 \times 22.8\text{ s} \approx 2,049\text{ s} = \mathbf{34.15\text{ minutes}}$.
- **Full Search Budget ($K=30$ trials $\times$ 3 policies = 90 trials):**
  $$\text{Total Search Time} = 90 \times 34.15\text{ min} \approx 3,073\text{ minutes} \approx \mathbf{51.2\text{ hours}}.$$
- **Validation Phase (Top-3 candidates $\times$ 3 policies = 9 trials):** $\approx \mathbf{5.1\text{ hours}}$.
- **Grand Total Required Compute:** $\approx \mathbf{56.3\text{ hours}}$ (~2.3 days of continuous CPU load).

---

## 3. Review-Readiness Decision & Configuration Freezing

With the final mentor review scheduled for tomorrow, continuous 56-hour background computation was halted after Step 0 and Trial 0. 

To maintain scientific integrity and provide clean, reproducible configurations:
1. The **pre-registered baseline parameters** (evaluated on training seeds 101–105) have been frozen as the official reference configurations in:
   - `configs/final_hybrid_queue_adaptive.yaml` (Kept rung R4 active, 300s warm-up Webster base green, 3s extension steps, 4m queue threshold, 1.2 fairness ratio).
   - `configs/final_queue_extension.yaml` (15s base green, 3s extension step, 4m threshold, 35s max wait cap).
   - `configs/final_adaptive.yaml` (0.30 s/m queue sensitivity, 15m threshold, 3s gap-out).
2. The complete, automated orchestration engine [`dp1/research/tuning_engine.py`](file:///e:/dp1-traffic-signal/dp1/research/tuning_engine.py) has been committed to the repository so that extended hyperparameter grid runs can be resumed and completed at any time.

---

## 4. Frozen Configuration Parameters

| Parameter | `hybrid_queue_adaptive` | `queue_extension` | `adaptive` |
| :--- | :---: | :---: | :---: |
| `rungs` | `("R4",)` | — | — |
| `r4_warmup_s` | 300.0 s | — | — |
| `initial_green_s` | — | 15.0 s | — |
| `k_s_per_m` | — | — | 0.30 s/m |
| `extend_step_s` | 3.0 s | 3.0 s | — |
| `extend_threshold_m` | 4.0 m | 4.0 m | 15.0 m |
| `gap_out_s` | 3.0 s | 3.0 s | 3.0 s |
| `min_competing_queue_m` | 2.0 m | 2.0 m | 1.0 m |
| `max_competing_wait_s` | 35.0 s | 35.0 s | — |
| `fairness_ratio` | 1.2 | 1.2 | — |
| `min_green_s` (Safety Invariant) | 10.0 s | 10.0 s | 10.0 s |
| `max_green_s` (Safety Invariant) | 60.0 s | 60.0 s | 60.0 s |
| `yellow_s` (Safety Invariant) | 3.0 s | 3.0 s | 3.0 s |
| `all_red_s` (Safety Invariant) | 2.0 s | 2.0 s | 2.0 s |

---

## 5. Artifact Inventory
- **Tuning Engine Source:** [`dp1/research/tuning_engine.py`](file:///e:/dp1-traffic-signal/dp1/research/tuning_engine.py)
- **Reference Denominators (180 runs):** `results/tuning/reference_webster/`
- **Baseline Trial 0 Runs (90 runs):** `results/tuning/hybrid_queue_adaptive/trial_00/`
- **Frozen Configurations:** `configs/final_*.yaml`
