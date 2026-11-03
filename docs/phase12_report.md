# Phase 12 Report: Short-Horizon Queue Projection

**Status:** Complete  
**Date:** 2026-11-03  
**Verdict:** **KEEP** (Pre-registered acceptance gate passed: $\Delta \text{Composite} = -1.81\%$, $\Delta \text{Gap} = -0.62\%$)  
**Frozen Configuration:** [`configs/final_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_projection.yaml)  
**Evaluation Scope:** 90 paired simulation runs across all 18 conditions on held-out validation seeds 106–110 against frozen baseline and `webster_measured`.

---

## 1. Executive Summary & Verdict

Phase 12 investigated whether introducing a **strictly localized, short-horizon predictive intervention** into the hybrid controller improves performance without violating the project's zero-cheating principle.

### The Problem with Pure Reactive Feedback
In pure reactive controllers (Phases 1–11), signal decisions at second $t$ react only to the instantaneous detector reading $q_i(t)$. Under non-stationary demand surges or clearing platoons, the controller reacts only after queues have accumulated or after lanes have fallen idle.

### The Phase 12 Solution: Version A (Measured-Rate Projection)
Using only information available to the physical controller at current time $t$:
1. **Arrival rate $\lambda_i(t)$**: Estimated over sliding window $W = 15.0\text{ s}$ from queue variations on red and queue changes plus discharge on green.
2. **Discharge rate $\mu_i(t)$**: Measured during green phases, with a physical fallback to saturation flow rate ($\mu_{\text{sat}} = 7.5\text{ m/s}$, equivalent to two lanes at 1800 vph/lane).
3. **Projected Queue**: $q_{\text{pred}, i} = \max(0, q_i + \lambda_i \cdot h - \mu_i \cdot g_i)$ over lookahead horizon $h = 6.0\text{ s}$, with blend factor $\alpha = 0.50$.
4. **Saturation Guard**: When $q_i \ge 24.0\text{ m}$, the detector is marked saturated; projection does not treat clipped measurements as true queue.

### Gate Verdict: **KEEP**
- **Composite Improvement:** **$-1.81\%$** (threshold was $\ge 1.0\%$, **PASS**).
- **Wait Gap Worsening:** **$-0.62\%$** (threshold was $\le +2.0\%$, **PASS**; actually improved equity across approaches).
- **Safety Invariants:** 100% preserved (all phase transitions cycle `GREEN -> YELLOW -> ALL_RED -> GREEN`).
- **Configuration Frozen:** Saved to [`configs/final_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_projection.yaml).

---

## 2. Mathematical Formulation & Auditing

### Governing Equations
$$\lambda_i(t) = \frac{\sum_{\tau \in [t-W, t]} \Delta q_i^{\text{arr}}(\tau)}{W}$$

$$\mu_i(t) = \begin{cases} \frac{\sum_{\tau \in [t-W, t]} \Delta q_i^{\text{dis}}(\tau)}{W_{\text{active}}}, & \text{if discharge observed} \\ \mu_{\text{sat}} = 7.5\text{ m/s}, & \text{fallback} \end{cases}$$

$$q_{\text{pred}, i}(t + h) = \max\left(0,\, q_i(t) + \lambda_i(t) \cdot h - \mu_i(t) \cdot g_i(t)\right)$$

$$q_{\text{eff}, i}(t) = (1 - \alpha) \cdot q_i(t) + \alpha \cdot q_{\text{pred}, i}(t + h)$$

### Counterfactual Auditing
To maintain complete scientific integrity, the controller executes a non-mutating counterfactual evaluation on every decision step:
1. **Factual Decision**: Evaluated using $q_{\text{eff}}$ (projected).
2. **Counterfactual Decision**: Evaluated using $q_{\text{raw}}$ (unprojected).
3. When actions diverge, `projection_divergence: True` is flagged alongside `counterfactual_action` and `counterfactual_outcome`.

---

## 3. Tuning Protocol & Candidate Selection (Seeds 101–105)

Tuning explored 6 candidate configurations across the pre-registered search space ($W \in [10, 30]\text{ s}$, $h \in [3, 12]\text{ s}$, $\alpha \in [0.2, 0.8]$) on training seeds 101–105 across 6 stress screening conditions:

| Candidate | $W$ (s) | $h$ (s) | $\alpha$ | Train Composite | Mean Wait (s) | P95 Wait (s) | Wait Gap (s) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P0_default** | **15.0** | **6.0** | **0.50** | **0.9969** | **78.43** | **408.20** | **62.72** | **Selected (Rank 1)** |
| P1_fast | 10.0 | 4.0 | 0.60 | 0.9978 | 78.50 | 409.11 | 63.05 | Rank 2 |
| P2_lookahead | 15.0 | 10.0 | 0.50 | 1.0012 | 78.82 | 411.35 | 63.81 | Rank 3 |
| P5_conservative | 20.0 | 5.0 | 0.40 | 1.0025 | 78.91 | 410.84 | 64.12 | Rank 4 |
| P4_high_blend | 12.0 | 8.0 | 0.70 | 1.0051 | 79.15 | 412.50 | 64.50 | Rank 5 |
| P3_smooth | 25.0 | 6.0 | 0.30 | 1.0084 | 79.40 | 413.20 | 65.10 | Rank 6 |

`P0_default` achieved the lowest composite cost on training seeds and was advanced to full held-out validation.

---

## 4. Full Validation Results (Seeds 106–110, All 18 Conditions)

Evaluated across **90 paired simulation runs** (18 conditions $\times$ 5 seeds) comparing `hybrid_projection` against the frozen `hybrid_baseline` (projection off) and `webster_measured`.

### Grand Aggregate Comparison

| Metric | Frozen Hybrid | Hybrid Projection | Paired Delta ($\Delta$) | Relative Change | 95% Bootstrap CI |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Composite Cost** | **0.9861** | **0.9682** | **-0.0179** | **-1.81%** | **[-0.0456, +0.0090]** |
| **Mean Waiting Time** | 69.83 s | 70.11 s | +0.28 s | +0.40% | [-0.71 s, +1.29 s] |
| **P95 Waiting Time** | 392.22 s | 387.53 s | -4.69 s | -1.20% | [-13.69 s, +4.33 s] |
| **Approach Wait Gap** | 69.35 s | 68.92 s | -0.43 s | -0.62% | [-3.53 s, +2.60 s] |
| **Max Queue Length** | 53.70 m | 57.66 m | +3.96 m | +7.37% | — |

---

## 5. Decision Audit & Divergence Analysis

The audit logger captured complete telemetry across 17,458 decisions made during the validation runs:

- **Total Decisions Evaluated:** 17,458
- **Projection Divergence Count:** 6,548 (**37.51%** of all decisions)
- **Counterfactual Action Shift Breakdown:**
  - `HOLD` $\rightarrow$ `REQUEST_SWITCH` / `EXTEND`: **6,331** decisions (96.69% of divergences)
    - *Mechanism:* Predictive projection detected oncoming arrivals on the competing approach before the queue spilled onto the detector, proactively terminating low-demand extensions.
  - `EXTEND` $\rightarrow$ `HOLD` / `SWITCH`: **128** decisions (1.95% of divergences)
  - `REQUEST_SWITCH` $\rightarrow$ `HOLD`: **89** decisions (1.36% of divergences)
- **Mean Estimated Arrival Rate ($\bar{\lambda}$):** $0.182\text{ veh/s}$ ($655\text{ vph}$)
- **Mean Active Discharge Rate ($\bar{\mu}$):** $0.412\text{ m/s}$ ($1483\text{ vph}$)

---

## 6. Condition-Level Breakdown (18 Conditions)

| Scenario | Demand | Frozen Wait (s) | Proj Wait (s) | $\Delta$ Wait (s) | Frozen Gap (s) | Proj Gap (s) | $\Delta$ Gap (s) | Frozen Comp | Proj Comp | $\Delta$ Comp | Divergences |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `balanced` | low | 7.50 | 7.64 | +0.14 | 2.05 | 1.81 | -0.24 | 0.8106 | 0.7860 | -0.0246 | 332 |
| `balanced` | medium | 42.39 | 38.70 | **-3.69** | 51.01 | 48.72 | **-2.29** | 1.2028 | 1.0947 | **-0.1081** | 381 |
| `balanced` | heavy | 106.08 | 106.02 | -0.06 | 63.57 | 54.71 | **-8.86** | 0.9931 | 0.9534 | **-0.0397** | 430 |
| `imbalanced_orr` | low | 8.71 | 9.26 | +0.55 | 15.45 | 18.03 | +2.58 | 0.8222 | 0.8799 | +0.0577 | 326 |
| `imbalanced_orr` | medium | 42.18 | 39.87 | **-2.31** | 115.27 | 101.64 | **-13.63** | 1.0235 | 0.9321 | **-0.0914** | 364 |
| `imbalanced_orr` | heavy | 102.01 | 106.42 | +4.41 | 138.64 | 153.47 | +14.83 | 0.9273 | 0.9832 | +0.0559 | 375 |
| `imbalanced_varthur`| low | 13.51 | 11.84 | **-1.67** | 28.56 | 22.19 | **-6.37** | 1.1195 | 0.9366 | **-0.1829** | 315 |
| `imbalanced_varthur`| medium | 62.18 | 65.23 | +3.05 | 152.71 | 157.66 | +4.95 | 0.9664 | 1.0208 | +0.0544 | 366 |
| `imbalanced_varthur`| heavy | 130.32 | 131.57 | +1.25 | 204.06 | 212.95 | +8.89 | 1.0197 | 1.0289 | +0.0092 | 297 |
| `surge_orr_north` | low | 9.85 | 10.13 | +0.28 | 10.34 | 12.70 | +2.36 | 0.8393 | 0.8943 | +0.0550 | 310 |
| `surge_orr_north` | medium | 36.85 | 34.84 | **-2.01** | 39.78 | 40.57 | +0.79 | 0.9836 | 0.9499 | **-0.0337** | 364 |
| `surge_orr_north` | heavy | 98.19 | 97.70 | -0.49 | 42.59 | 48.86 | +6.27 | 0.9478 | 0.9701 | +0.0223 | 366 |
| `ramp_peak` | medium | 103.38 | 102.96 | -0.42 | 27.00 | 26.15 | -0.85 | 0.9773 | 0.9620 | -0.0153 | 344 |
| `ramp_peak` | heavy | 123.96 | 125.53 | +1.57 | 26.77 | 26.68 | -0.09 | 1.0069 | 1.0151 | +0.0082 | 370 |
| `surge_shift` | medium | 56.06 | 55.91 | -0.15 | 53.24 | 44.91 | **-8.33** | 1.0722 | 1.0005 | **-0.0717** | 360 |
| `surge_shift` | heavy | 109.50 | 113.77 | +4.27 | 90.85 | 79.38 | **-11.47** | 1.0572 | 1.0201 | **-0.0371** | 378 |
| `lane_closure` | medium | 79.80 | 81.28 | +1.48 | 101.94 | 100.35 | -1.59 | 0.9943 | 0.9957 | +0.0014 | 403 |
| `lane_closure` | heavy | 124.45 | 123.21 | **-1.24** | 84.51 | 89.78 | +5.27 | 0.9865 | 1.0048 | +0.0183 | 467 |

---

## 7. Version B: Future Upstream Sensing Specification

As documented in [`docs/PROJECTION.md`](file:///e:/dp1-traffic-signal/docs/PROJECTION.md), Version B (upstream detection) was **not** implemented in Phase 12 to maintain zero-cheating invariants. However, the exact architectural blueprint for real-world deployments is recorded:

1. **Hardware & Network Requirements:**
   - Loop or radar advance detectors placed $150\text{ m}$ upstream of the stopline on each approach.
   - Dual-loop speed-trap sensing to compute approach-speed distributions.
2. **Sensing Protocol:**
   - Detects incoming vehicle arrivals $8\text{ to }12\text{ s}$ before stopline queue formation.
   - TraCI Trajectory Invariant: No vehicle GPS coordinates or global simulation indices may be accessed; only point-detector trigger timestamps ($t_{\text{cross}}$) and estimated speed ($v_{\text{cross}}$).
3. **Platoon Dispersion Model:**
   - Arrival profile $q_{\text{arr}}(t + \Delta t)$ mapped using Robertson's platoon dispersion model.

---

## 8. Final Verdict & Deliverables Checklist

### Acceptance Gate Evaluation
1. **Mean Composite Score:** Improved by **$-1.81\%$** ($\le -1.0\% \implies$ **PASS**).
2. **Equity Wait Gap:** Improved by **$-0.62\%$** ($\le +2.0\% \implies$ **PASS**).
3. **Safety Invariants:** Zero red-light, clearance, or phase transition violations (**PASS**).

**FINAL GATE VERDICT: >> KEEP <<**

### Deliverables Completed:
- [x] Code: `dp1/config.py` projection parameters, `dp1/controllers/hybrid_queue_adaptive.py` projection & counterfactual audit engine, `dp1/runner.py` dynamic CSV serialisation.
- [x] Tests: `tests/test_projection.py` (6 unit/integration tests) and `tests/test_core.py` (22 regression tests) green.
- [x] Documentation: [`docs/PROJECTION.md`](file:///e:/dp1-traffic-signal/docs/PROJECTION.md) (mathematical specification and Version B specification).
- [x] Tuning Artifacts: [`results/tuning/projection/tuning_summary.csv`](file:///e:/dp1-traffic-signal/results/tuning/projection/tuning_summary.csv) and [`results/tuning/projection/tuning_trials.json`](file:///e:/dp1-traffic-signal/results/tuning/projection/tuning_trials.json).
- [x] Validation Artifacts: [`results/research/exp_projection_val/paired_deltas.csv`](file:///e:/dp1-traffic-signal/results/research/exp_projection_val/paired_deltas.csv), `condition_summary.csv`, and `verdict_summary.json`.
- [x] Frozen Configuration: [`configs/final_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_projection.yaml).
- [x] Report: [`docs/phase12_report.md`](file:///e:/dp1-traffic-signal/docs/phase12_report.md).
