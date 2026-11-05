# Phase 12 Report: Short-Horizon Queue Projection (Re-evaluated Negative Result)

**Status:** Complete — **RE-EVALUATED VERDICT: CUT**  
**Date:** 2026-11-04 (Re-evaluated under Pre-Registration Section 6)  
**Parent Documents:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md), [`docs/PREREGISTRATION_AMENDMENT_2.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_2.md), [`docs/PROJECTION.md`](file:///e:/dp1-traffic-signal/docs/PROJECTION.md)  
**Configuration:** [`configs/experimental_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/experimental_hybrid_projection.yaml) (projection disabled by default in production)  
**Evaluation Scope:** 90 paired simulation runs across all 18 conditions on held-out validation seeds 106–110 comparing `hybrid_projection` against frozen baseline `hybrid_queue_adaptive` (projection off).

---

## 1. Executive Summary & Authoritative Verdict

### Pre-Registered Acceptance Criteria (`docs/PREREGISTRATION.md` Section 6)
To be kept in the production controller ladder, a candidate rung must satisfy:
1. **Rule 1 (Primary Significance):** At least one PRIMARY metric (`p95 wait`, `gt_ext_max_queue_m`, or `approach wait gap`) improves with a paired 95% bootstrap confidence interval strictly excluding zero.
2. **Rule 2 (Mean Delay Degradation Bound):** Mean wait time does not degrade by more than $+1.0\%$ with 95% confidence.
3. **Rule 3 (Completion Invariant):** Completion rate does not degrade ($\Delta \ge -0.5\%$) and unfinished vehicles do not increase.

### Re-Evaluation Findings on Validation Seeds 106–110 ($N = 90$ pairs)

| Metric | Type | Frozen Hybrid | Hybrid Proj | Paired Delta ($\Delta$) | 95% Bootstrap CI | Statistically Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **P95 Waiting Time** | Primary | 392.22 s | 387.53 s | -4.69 s (-1.20%) | **[-13.69 s, +4.33 s]** | **NO** (spans zero) |
| **Approach Wait Gap** | Primary | 69.35 s | 68.92 s | -0.43 s (-0.62%) | **[-3.53 s, +2.60 s]** | **NO** (spans zero) |
| **Extended Max Queue** (`gt_ext_max_queue_m`) | Primary | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | **NO** (not logged) |
| *Detector Max Queue* (`max_queue_m`) | Secondary | 53.70 m | 57.66 m | +3.96 m (+7.37%) | — | Worsened |
| **Mean Waiting Time** | Secondary | 69.83 s | 70.11 s | +0.28 s (+0.40%) | [-0.71 s, +1.29 s] | Satisfies +1% bound |
| *Composite Cost Index* | Secondary | 0.9861 | 0.9682 | -0.0179 (-1.81%) | **[-0.0456, +0.0090]** | **NO** (spans zero) |

### Formal Verdict: **CUT**
- An earlier draft claimed "KEEP" based on point-estimate composite cost reduction ($\Delta = -1.81\%$). However, strict adherence to `docs/PREREGISTRATION.md` Section 6 dictates that **Rule 1 is violated**: no primary metric exhibits a paired 95% confidence interval strictly excluding zero.
- Even the composite metric confidence interval spans zero (`[-0.0456, +0.0090]`).
- Detector-level maximum queue worsened by $+3.96\text{ m}$.
- Consequently, short-horizon queue projection is **CUT** from the production controller ladder.
- Projection parameters remain disabled by default in `dp1/config.py` (`projection_enabled = False`).
- The configuration file is preserved for research reproducibility as [`configs/experimental_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/experimental_hybrid_projection.yaml).

---

## 2. Research Analysis & Why Projection Did Not Distinguish Itself

### 2.1 The Divergence-Noise Trade-off
Decision telemetry recorded 17,458 decisions across validation seeds:
- Projection changed actions in **37.51%** of evaluations (6,548 decisions).
- 96.69% of these divergences shifted `HOLD` to `REQUEST_SWITCH` / `EXTEND`, aiming to preempt queue accumulation on the opposing axis.
- However, stop-line E2 detectors span only $24.4\text{ m}$. Once queues reached detector capacity, arrival rates could only be approximated via historical holdover values.
- In transient surges, linear extrapolation of noisy arrival rates introduced premature phase terminations during platooning, offsetting its gains on queue clearance.

### 2.2 Recommended Scientific Terminology
In research publications, presentation slides, and thesis documentation:
- **Do NOT claim:** "Predictive signal optimization", "Machine learning forecasting", or "Queue forecasting superiority".
- **Recommended wording:** **"Proactive, state-aware intervention"** (or *"Short-horizon arrival-rate heuristic"*).
- The hybrid controller's verified performance stems from R4 de-oracled measured base green allocation and state-aware queue extension with strict safety boundaries, not from linear predictive projection.

---

## 3. Preservation of Invariants

- **Safety Invariants:** 100% verified. Every phase change strictly follows `GREEN -> YELLOW -> ALL_RED -> GREEN`.
- **Default Behavior:** Production hybrid controller (`hybrid_queue_adaptive`) runs with `projection_enabled: False`.
