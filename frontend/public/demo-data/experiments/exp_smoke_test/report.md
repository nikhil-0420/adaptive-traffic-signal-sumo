# DP1 Research Evaluation Report — Experiment `exp_smoke_test`

> **Simulation Integrity Notice**
> All metrics are derived from real execution of Eclipse SUMO with TraCI on simulated lane-area detectors.
> Results reflect the synthetic four-way junction model and do not constitute field evidence from live roads.

## 1. Executive Summary & Matrix Status

- **Experiment Status:** `COMPLETE` (3/3 cells completed)
- **Failed Cells:** 0
- **Blocked Cells:** 0
- **Execution Timestamp:** 2026-10-12T06:49:49Z
- **Bootstrap Configuration:** 10,000 resamples (seed: 42)

| Factor | Evaluated Levels |
|---|---|
| **Patterns** | imbalanced_ns |
| **Demand Levels** | medium (x1.00) |
| **Policies** | fixed, adaptive, pressure |
| **Evaluation Seeds** | [21] (n=1) |

## 2. Experimental Setup & Seed Separation

In compliance with fair evaluation protocols, controller hyperparameters and RL models were frozen prior to running on research evaluation seeds:
- **Training Seeds:** `1..5` (used for Webster profile baseline and legacy grid search).
- **RL Validation Seeds:** `6..10` (used for checkpoint validation).
- **Legacy Held-Out Seeds:** `11..15` (used for baseline comparison).
- **Research Test Seeds:** `21..30` (strictly held out for final reporting; never used to tune or select policies).

## 3. Aggregate Performance Across Demand Levels

Values represent mean ± sample standard deviation over evaluation seeds for each condition.

| Pattern | Level | Policy | Seeds | Mean Wait (s) | Time Loss (s) | Mean Queue (m) | Throughput (veh/h) | Completion |
|---|---|---|---:|---:|---:|---:|---:|---:|
| imbalanced_ns | medium | `adaptive` | 1 | 45.1 ± nan | 70.5 ± nan | 49.6 ± nan | 2798 | 100.0% |
| imbalanced_ns | medium | `fixed` | 1 | 122.4 ± nan | 152.0 ± nan | 60.9 ± nan | 2426 | 100.0% |
| imbalanced_ns | medium | `pressure` | 1 | 45.9 ± nan | 69.3 ± nan | 52.5 ± nan | 2806 | 100.0% |

## 4. Paired Delta Analysis vs Fixed Baseline (95% Bootstrap CI)

Paired differences are calculated per-seed against `fixed` under identical arrival traffic:
$$\Delta = \text{Metric}_{\text{candidate}} - \text{Metric}_{\text{fixed}}$$
A **negative delta** indicates a reduction (improvement) in delay or queuing relative to the fixed plan.

| Pattern | Level | Policy | Valid Pairs | Delta Wait (s) [95% CI] | Delta Time Loss (s) [95% CI] | Delta Queue (m) |
|---|---|---|---:|---|---|---:|
| imbalanced_ns | medium | `adaptive` | 1 | **-77.30** [-77.30, -77.30] | -81.56 [-81.56, -81.56] | -11.29 |
| imbalanced_ns | medium | `pressure` | 1 | **-76.54** [-76.54, -76.54] | -82.74 [-82.74, -82.74] | -8.44 |

## 5. Directional Service Disparity & Approach Wait Gaps

Service disparity measures the imbalance in waiting times between competing directions:
$$\text{Disparity} = |\text{Wait}_{\text{NS}} - \text{Wait}_{\text{EW}}|$$
$$\text{Wait Gap} = \max(\text{Wait}_{\text{approach}}) - \min(\text{Wait}_{\text{approach}})$$

| Pattern | Level | Policy | Wait NS (s) | Wait EW (s) | Direction Disparity (s) | Approach Gap (s) |
|---|---|---|---:|---:|---:|---:|
| imbalanced_ns | medium | `adaptive` | 49.1 | 32.5 | 16.6 | 29.8 |
| imbalanced_ns | medium | `fixed` | 150.6 | 32.8 | 117.8 | 124.8 |
| imbalanced_ns | medium | `pressure` | 41.4 | 60.1 | 18.7 | 26.8 |

## 6. Known Trade-Offs & Honest Limitations

1. **Imbalance vs Surge Behavior:** Adaptive and pressure policies offer substantial reductions in vehicle delay under sustained demand imbalance (`imbalanced_ns`, `imbalanced_ew`). However, during temporary surges (`surge_north`), rapid queue clearance may incur switching lost time.
2. **Simulation Boundaries:** Experiments were executed on synthetic 300 m approach links with 150 m detector coverage. Unobserved queues beyond 150 m are not measured by sensors.
3. **Fixed-Time Baseline Adaptation:** The fixed-time plan is adapted from BTP Marathahalli Bridge junction schedule with clearance intervals (3s yellow, 2s all-red), omitting the pedestrian-only phase.

## 7. Artifact Manifest

- `manifest.json`: Complete execution metadata and environment configuration.
- `raw_runs.csv`: Unaggregated per-run metrics for every completed cell.
- `aggregate.csv`: Grouped means and standard deviations.
- `paired_deltas.csv`: Paired per-seed differences with bootstrap confidence intervals.
- `fairness_by_approach.csv`: Approach-level vehicle counts, delays, and detector queues.
- `fairness_by_direction.csv`: NS vs EW directional disparity summaries.
- `matrix_status.csv`: Cell-by-cell lifecycle tracking.
- `plots/`: Rendered figures.
