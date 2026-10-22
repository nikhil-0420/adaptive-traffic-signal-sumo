# DP1 Research Evaluation Report — Experiment `exp_marathahalli_site`

> **Simulation Integrity Notice — Marathahalli Real-Road Site Model**
> All metrics are derived from real execution of Eclipse SUMO with TraCI on the Marathahalli Bridge junction model.
> Topology and grade-separation are grounded in OpenCity GIS and OSM centerlines; traffic demand is synthetic on real geometry.
> Controller models and timings reflect the physical site layout and do not constitute live traffic sensor telemetry.

## 1. Executive Summary & Matrix Status

- **Network:** `Marathahalli Bridge Real-Road Site`
- **Experiment Status:** `COMPLETE` (600/600 cells completed)
- **Failed Cells:** 0
- **Blocked Cells:** 0
- **Execution Timestamp:** 2026-10-14T06:54:21Z
- **Bootstrap Configuration:** 10,000 resamples (seed: 42)

| Factor | Evaluated Levels |
|---|---|
| **Patterns** | balanced, imbalanced_orr, imbalanced_varthur, surge_orr_north |
| **Demand Levels** | low (x0.70), medium (x1.00), heavy (x1.30) |
| **Policies** | fixed, fixed_webster, adaptive, pressure, rl_dqn |
| **Evaluation Seeds** | [121, 122, 123, 124, 125, 126, 127, 128, 129, 130] (n=10) |

## 2. Experimental Setup & Seed Separation

In compliance with fair evaluation protocols, controller hyperparameters and RL models were frozen prior to running on research evaluation seeds:
- **Site Training Seeds:** `101..105` (used for Webster profile baseline and site DQN replay training).
- **Site RL Validation Seeds:** `106..110` (used strictly for model checkpoint selection).
- **Site Research Test Seeds:** `121..130` (strictly held out for final reporting; never used to tune or select policies).

## 3. Aggregate Performance Across Demand Levels

Values represent mean ± sample standard deviation over evaluation seeds for each condition.

| Pattern | Level | Policy | Seeds | Mean Wait (s) | Time Loss (s) | Mean Queue (m) | Throughput (veh/h) | Completion |
|---|---|---|---:|---:|---:|---:|---:|---:|
| balanced | heavy | `adaptive` | 10 | 107.4 ± 7.0 | 137.7 ± 9.2 | 1.9 ± 0.1 | 2856 | 100.0% |
| balanced | heavy | `fixed` | 10 | 108.2 ± 8.3 | 137.6 ± 10.7 | 6.8 ± 0.4 | 2884 | 100.0% |
| balanced | heavy | `fixed_webster` | 10 | 105.6 ± 6.9 | 135.9 ± 9.6 | 2.2 ± 0.2 | 2866 | 100.0% |
| balanced | heavy | `pressure` | 10 | 107.4 ± 7.1 | 138.2 ± 9.7 | 2.0 ± 0.1 | 2857 | 100.0% |
| balanced | heavy | `rl_dqn` | 10 | 105.9 ± 7.9 | 135.7 ± 10.7 | 1.8 ± 0.1 | 2863 | 100.0% |
| balanced | low | `adaptive` | 10 | 7.4 ± 0.6 | 14.1 ± 0.7 | 1.1 ± 0.1 | 1781 | 100.0% |
| balanced | low | `fixed` | 10 | 15.2 ± 0.6 | 21.9 ± 0.7 | 4.7 ± 0.4 | 1768 | 100.0% |
| balanced | low | `fixed_webster` | 10 | 8.2 ± 0.8 | 15.0 ± 0.9 | 1.3 ± 0.1 | 1780 | 100.0% |
| balanced | low | `pressure` | 10 | 7.6 ± 0.6 | 14.3 ± 0.7 | 1.1 ± 0.1 | 1780 | 100.0% |
| balanced | low | `rl_dqn` | 10 | 8.2 ± 1.0 | 14.8 ± 1.2 | 1.3 ± 0.1 | 1777 | 100.0% |
| balanced | medium | `adaptive` | 10 | 40.3 ± 6.6 | 53.4 ± 8.4 | 1.6 ± 0.1 | 2456 | 100.0% |
| balanced | medium | `fixed` | 10 | 41.5 ± 5.7 | 53.6 ± 7.3 | 6.4 ± 0.3 | 2464 | 100.0% |
| balanced | medium | `fixed_webster` | 10 | 40.7 ± 8.4 | 53.8 ± 10.4 | 1.9 ± 0.1 | 2457 | 100.0% |
| balanced | medium | `pressure` | 10 | 37.1 ± 6.4 | 49.6 ± 8.3 | 1.6 ± 0.1 | 2464 | 100.0% |
| balanced | medium | `rl_dqn` | 10 | 39.0 ± 8.1 | 52.1 ± 10.1 | 1.7 ± 0.1 | 2464 | 100.0% |
| imbalanced_orr | heavy | `adaptive` | 10 | 104.2 ± 13.1 | 136.1 ± 15.6 | 2.8 ± 1.2 | 3268 | 100.0% |
| imbalanced_orr | heavy | `fixed` | 10 | 108.9 ± 15.1 | 138.7 ± 17.0 | 7.0 ± 0.8 | 3282 | 100.0% |
| imbalanced_orr | heavy | `fixed_webster` | 10 | 104.4 ± 13.8 | 136.5 ± 16.6 | 2.8 ± 1.0 | 3264 | 100.0% |
| imbalanced_orr | heavy | `pressure` | 10 | 106.6 ± 12.3 | 139.8 ± 14.5 | 3.1 ± 1.6 | 3255 | 100.0% |
| imbalanced_orr | heavy | `rl_dqn` | 10 | 103.7 ± 10.7 | 135.9 ± 13.5 | 2.4 ± 0.6 | 3268 | 100.0% |
| imbalanced_orr | low | `adaptive` | 10 | 9.3 ± 1.7 | 16.2 ± 1.9 | 1.2 ± 0.1 | 1966 | 100.0% |
| imbalanced_orr | low | `fixed` | 10 | 16.3 ± 1.2 | 23.1 ± 1.3 | 4.9 ± 0.4 | 1959 | 100.0% |
| imbalanced_orr | low | `fixed_webster` | 10 | 9.2 ± 2.0 | 16.0 ± 2.3 | 1.3 ± 0.1 | 1965 | 100.0% |
| imbalanced_orr | low | `pressure` | 10 | 9.2 ± 1.7 | 16.0 ± 1.9 | 1.2 ± 0.1 | 1966 | 100.0% |
| imbalanced_orr | low | `rl_dqn` | 10 | 9.3 ± 2.0 | 16.1 ± 2.2 | 1.3 ± 0.1 | 1963 | 100.0% |
| imbalanced_orr | medium | `adaptive` | 10 | 42.3 ± 10.8 | 55.2 ± 12.7 | 1.9 ± 0.2 | 2723 | 100.0% |
| imbalanced_orr | medium | `fixed` | 10 | 46.3 ± 9.2 | 58.7 ± 10.7 | 6.2 ± 0.4 | 2732 | 100.0% |
| imbalanced_orr | medium | `fixed_webster` | 10 | 42.2 ± 10.0 | 54.7 ± 11.2 | 1.8 ± 0.2 | 2731 | 100.0% |
| imbalanced_orr | medium | `pressure` | 10 | 41.8 ± 9.9 | 54.7 ± 11.3 | 1.8 ± 0.2 | 2725 | 100.0% |
| imbalanced_orr | medium | `rl_dqn` | 10 | 42.8 ± 9.1 | 55.8 ± 10.4 | 1.7 ± 0.2 | 2729 | 100.0% |
| imbalanced_varthur | heavy | `adaptive` | 10 | 129.3 ± 15.0 | 171.1 ± 17.5 | 6.2 ± 1.4 | 3036 | 100.0% |
| imbalanced_varthur | heavy | `fixed` | 10 | 134.8 ± 12.6 | 175.3 ± 16.0 | 9.2 ± 1.0 | 3055 | 100.0% |
| imbalanced_varthur | heavy | `fixed_webster` | 10 | 131.4 ± 14.7 | 174.0 ± 19.8 | 6.1 ± 1.5 | 3037 | 100.0% |
| imbalanced_varthur | heavy | `pressure` | 10 | 129.5 ± 11.8 | 172.2 ± 15.0 | 6.2 ± 1.1 | 3042 | 100.0% |
| imbalanced_varthur | heavy | `rl_dqn` | 10 | 127.5 ± 18.2 | 169.8 ± 22.6 | 5.0 ± 1.3 | 3028 | 100.0% |
| imbalanced_varthur | low | `adaptive` | 10 | 11.4 ± 1.9 | 19.0 ± 2.3 | 1.3 ± 0.1 | 1977 | 100.0% |
| imbalanced_varthur | low | `fixed` | 10 | 19.3 ± 1.7 | 27.1 ± 2.2 | 5.0 ± 0.4 | 1957 | 100.0% |
| imbalanced_varthur | low | `fixed_webster` | 10 | 11.6 ± 2.7 | 19.1 ± 3.2 | 1.3 ± 0.1 | 1976 | 100.0% |
| imbalanced_varthur | low | `pressure` | 10 | 11.2 ± 1.9 | 18.8 ± 2.3 | 1.2 ± 0.1 | 1977 | 100.0% |
| imbalanced_varthur | low | `rl_dqn` | 10 | 10.8 ± 1.2 | 18.2 ± 1.4 | 1.3 ± 0.1 | 1975 | 100.0% |
| imbalanced_varthur | medium | `adaptive` | 10 | 66.8 ± 10.4 | 84.3 ± 12.4 | 2.0 ± 0.4 | 2685 | 100.0% |
| imbalanced_varthur | medium | `fixed` | 10 | 73.0 ± 10.1 | 90.2 ± 11.9 | 6.5 ± 0.4 | 2666 | 100.0% |
| imbalanced_varthur | medium | `fixed_webster` | 10 | 70.1 ± 14.8 | 87.6 ± 16.8 | 2.3 ± 1.5 | 2674 | 100.0% |
| imbalanced_varthur | medium | `pressure` | 10 | 65.7 ± 11.5 | 82.8 ± 13.0 | 2.2 ± 1.2 | 2680 | 100.0% |
| imbalanced_varthur | medium | `rl_dqn` | 10 | 67.3 ± 12.2 | 84.2 ± 13.9 | 2.0 ± 0.9 | 2682 | 100.0% |
| surge_orr_north | heavy | `adaptive` | 10 | 95.5 ± 7.1 | 125.3 ± 9.0 | 2.6 ± 0.7 | 2947 | 100.0% |
| surge_orr_north | heavy | `fixed` | 10 | 99.9 ± 6.2 | 129.5 ± 8.4 | 7.0 ± 0.7 | 2957 | 100.0% |
| surge_orr_north | heavy | `fixed_webster` | 10 | 97.1 ± 8.7 | 127.2 ± 10.9 | 2.8 ± 0.6 | 2938 | 100.0% |
| surge_orr_north | heavy | `pressure` | 10 | 98.3 ± 5.1 | 128.7 ± 6.6 | 2.6 ± 0.7 | 2941 | 100.0% |
| surge_orr_north | heavy | `rl_dqn` | 10 | 95.1 ± 7.6 | 125.1 ± 10.0 | 2.4 ± 0.4 | 2947 | 100.0% |
| surge_orr_north | low | `adaptive` | 10 | 8.9 ± 1.5 | 15.8 ± 1.8 | 1.2 ± 0.1 | 1761 | 100.0% |
| surge_orr_north | low | `fixed` | 10 | 16.4 ± 2.1 | 23.4 ± 2.5 | 4.5 ± 0.4 | 1753 | 100.0% |
| surge_orr_north | low | `fixed_webster` | 10 | 8.6 ± 1.3 | 15.4 ± 1.5 | 1.3 ± 0.1 | 1762 | 100.0% |
| surge_orr_north | low | `pressure` | 10 | 8.5 ± 1.8 | 15.4 ± 2.1 | 1.1 ± 0.1 | 1761 | 100.0% |
| surge_orr_north | low | `rl_dqn` | 10 | 9.3 ± 1.5 | 16.2 ± 1.9 | 1.2 ± 0.1 | 1759 | 100.0% |
| surge_orr_north | medium | `adaptive` | 10 | 37.2 ± 8.4 | 51.0 ± 10.7 | 1.8 ± 0.3 | 2507 | 100.0% |
| surge_orr_north | medium | `fixed` | 10 | 42.1 ± 6.2 | 55.0 ± 7.8 | 5.9 ± 0.3 | 2501 | 100.0% |
| surge_orr_north | medium | `fixed_webster` | 10 | 37.3 ± 5.2 | 50.8 ± 6.5 | 1.9 ± 0.2 | 2508 | 100.0% |
| surge_orr_north | medium | `pressure` | 10 | 38.1 ± 8.8 | 51.9 ± 10.8 | 1.7 ± 0.3 | 2504 | 100.0% |
| surge_orr_north | medium | `rl_dqn` | 10 | 39.5 ± 8.5 | 53.7 ± 10.8 | 1.7 ± 0.2 | 2506 | 100.0% |

## 4. Paired Delta Analysis vs Fixed Baseline (95% Bootstrap CI)

Paired differences are calculated per-seed against `fixed` under identical arrival traffic:
$$\Delta = \text{Metric}_{\text{candidate}} - \text{Metric}_{\text{fixed}}$$
A **negative delta** indicates a reduction (improvement) in delay or queuing relative to the fixed plan.

| Pattern | Level | Policy | Valid Pairs | Delta Wait (s) [95% CI] | Delta Time Loss (s) [95% CI] | Delta Queue (m) |
|---|---|---|---:|---|---|---:|
| balanced | low | `fixed_webster` | 10 | **-6.94** [-7.24, -6.68] | -6.94 [-7.29, -6.64] | -3.44 |
| balanced | low | `adaptive` | 10 | **-7.73** [-7.99, -7.48] | -7.76 [-8.04, -7.49] | -3.59 |
| balanced | low | `pressure` | 10 | **-7.62** [-8.00, -7.27] | -7.63 [-8.11, -7.21] | -3.58 |
| balanced | low | `rl_dqn` | 10 | **-7.02** [-7.56, -6.45] | -7.08 [-7.64, -6.47] | -3.43 |
| balanced | medium | `fixed_webster` | 10 | **-0.87** [-3.49, +1.53] | +0.16 [-3.01, +3.02] | -4.51 |
| balanced | medium | `adaptive` | 10 | **-1.25** [-3.63, +1.02] | -0.25 [-3.20, +2.45] | -4.75 |
| balanced | medium | `pressure` | 10 | **-4.39** [-7.12, -1.67] | -4.06 [-7.45, -0.69] | -4.73 |
| balanced | medium | `rl_dqn` | 10 | **-2.47** [-5.40, +0.47] | -1.58 [-5.01, +1.87] | -4.68 |
| balanced | heavy | `fixed_webster` | 10 | **-2.62** [-4.24, -0.60] | -1.74 [-4.06, +0.94] | -4.59 |
| balanced | heavy | `adaptive` | 10 | **-0.76** [-2.90, +1.64] | +0.15 [-2.71, +3.12] | -4.91 |
| balanced | heavy | `pressure` | 10 | **-0.75** [-3.16, +1.45] | +0.56 [-2.31, +3.11] | -4.84 |
| balanced | heavy | `rl_dqn` | 10 | **-2.27** [-4.62, -0.06] | -1.87 [-4.81, +1.20] | -4.96 |
| imbalanced_orr | low | `fixed_webster` | 10 | **-7.02** [-7.68, -6.45] | -7.13 [-7.85, -6.47] | -3.60 |
| imbalanced_orr | low | `adaptive` | 10 | **-6.92** [-7.47, -6.07] | -6.88 [-7.50, -5.91] | -3.64 |
| imbalanced_orr | low | `pressure` | 10 | **-7.09** [-7.81, -6.19] | -7.09 [-7.93, -6.05] | -3.64 |
| imbalanced_orr | low | `rl_dqn` | 10 | **-6.98** [-7.61, -6.29] | -7.07 [-7.76, -6.30] | -3.61 |
| imbalanced_orr | medium | `fixed_webster` | 10 | **-4.09** [-5.93, -2.31] | -4.00 [-6.03, -2.12] | -4.39 |
| imbalanced_orr | medium | `adaptive` | 10 | **-3.97** [-7.03, -0.87] | -3.54 [-7.13, +0.29] | -4.36 |
| imbalanced_orr | medium | `pressure` | 10 | **-4.48** [-6.79, -2.22] | -4.03 [-6.72, -1.28] | -4.39 |
| imbalanced_orr | medium | `rl_dqn` | 10 | **-3.44** [-5.24, -2.00] | -2.87 [-5.00, -1.09] | -4.53 |
| imbalanced_orr | heavy | `fixed_webster` | 10 | **-4.45** [-7.90, -0.95] | -2.18 [-6.36, +2.31] | -4.28 |
| imbalanced_orr | heavy | `adaptive` | 10 | **-4.61** [-6.77, -2.35] | -2.64 [-5.04, +0.07] | -4.22 |
| imbalanced_orr | heavy | `pressure` | 10 | **-2.22** [-7.22, +2.86] | +1.07 [-4.08, +6.46] | -3.96 |
| imbalanced_orr | heavy | `rl_dqn` | 10 | **-5.12** [-9.00, -1.62] | -2.82 [-6.32, +1.18] | -4.61 |
| imbalanced_varthur | low | `fixed_webster` | 10 | **-7.77** [-8.88, -6.55] | -7.96 [-9.21, -6.59] | -3.70 |
| imbalanced_varthur | low | `adaptive` | 10 | **-7.95** [-8.77, -7.11] | -8.07 [-8.92, -7.16] | -3.73 |
| imbalanced_varthur | low | `pressure` | 10 | **-8.09** [-8.59, -7.60] | -8.28 [-8.81, -7.74] | -3.76 |
| imbalanced_varthur | low | `rl_dqn` | 10 | **-8.52** [-9.23, -7.82] | -8.92 [-9.74, -8.14] | -3.71 |
| imbalanced_varthur | medium | `fixed_webster` | 10 | **-2.94** [-6.27, +1.23] | -2.62 [-6.03, +1.67] | -4.21 |
| imbalanced_varthur | medium | `adaptive` | 10 | **-6.18** [-9.69, -2.92] | -5.90 [-9.99, -2.07] | -4.49 |
| imbalanced_varthur | medium | `pressure` | 10 | **-7.32** [-9.88, -4.43] | -7.34 [-10.32, -4.09] | -4.34 |
| imbalanced_varthur | medium | `rl_dqn` | 10 | **-5.72** [-8.23, -3.17] | -6.00 [-8.46, -3.64] | -4.46 |
| imbalanced_varthur | heavy | `fixed_webster` | 10 | **-3.39** [-9.31, +2.06] | -1.35 [-8.84, +6.11] | -3.08 |
| imbalanced_varthur | heavy | `adaptive` | 10 | **-5.49** [-10.15, -0.94] | -4.24 [-9.39, +0.73] | -3.04 |
| imbalanced_varthur | heavy | `pressure` | 10 | **-5.29** [-8.56, -2.10] | -3.13 [-8.03, +1.66] | -3.05 |
| imbalanced_varthur | heavy | `rl_dqn` | 10 | **-7.32** [-13.16, -1.90] | -5.51 [-12.56, +0.63] | -4.21 |
| surge_orr_north | low | `fixed_webster` | 10 | **-7.73** [-8.52, -6.95] | -7.92 [-8.82, -7.05] | -3.26 |
| surge_orr_north | low | `adaptive` | 10 | **-7.48** [-8.38, -6.56] | -7.52 [-8.48, -6.51] | -3.36 |
| surge_orr_north | low | `pressure` | 10 | **-7.91** [-8.59, -7.34] | -7.98 [-8.75, -7.33] | -3.45 |
| surge_orr_north | low | `rl_dqn` | 10 | **-7.07** [-7.75, -6.45] | -7.18 [-7.96, -6.47] | -3.29 |
| surge_orr_north | medium | `fixed_webster` | 10 | **-4.80** [-6.58, -3.26] | -4.22 [-6.52, -2.29] | -4.08 |
| surge_orr_north | medium | `adaptive` | 10 | **-4.93** [-7.37, -2.15] | -3.97 [-7.08, -0.11] | -4.16 |
| surge_orr_north | medium | `pressure` | 10 | **-4.00** [-6.01, -1.95] | -3.06 [-5.48, -0.51] | -4.21 |
| surge_orr_north | medium | `rl_dqn` | 10 | **-2.58** [-5.26, +0.43] | -1.28 [-4.60, +2.51] | -4.20 |
| surge_orr_north | heavy | `fixed_webster` | 10 | **-2.82** [-5.51, -0.30] | -2.23 [-5.16, +0.59] | -4.18 |
| surge_orr_north | heavy | `adaptive` | 10 | **-4.45** [-7.24, -0.83] | -4.21 [-7.54, -0.29] | -4.39 |
| surge_orr_north | heavy | `pressure` | 10 | **-1.63** [-4.62, +1.75] | -0.82 [-4.65, +3.15] | -4.31 |
| surge_orr_north | heavy | `rl_dqn` | 10 | **-4.80** [-8.29, -1.58] | -4.38 [-8.53, -0.51] | -4.59 |

## 5. Paired Statistical Best Policy & Tie Analysis (Within-Seed Bootstrapping)

To eliminate inter-seed variance, candidates are compared by bootstrapping the paired difference in waiting time
across identical simulation seeds: $\Delta_{\text{paired}}(s) = \text{Wait}_{\text{leader}}(s) - \text{Wait}_{\text{runner\_up}}(s)$.
If 0 is included within the 95% paired bootstrap confidence interval ($B=10,000$), the outcome is classified as a
**Statistical Tie** (`leader ~ runner_up`, $p > 0.05$). If $\text{CI}_{\text{upper}} < 0$, the primary leader is
statistically significantly superior ($p < 0.05$).

| Pattern | Demand Level | Primary Leader | Secondary Candidate | Outcome Classification | Paired Delta [95% CI] | Statistical Evidence |
|---|---|---|---|---|---:|---|
| balanced | low | `adaptive` (7.5s) | `pressure` (7.6s) | **TIE (`adaptive` ~ `pressure`)** | **-0.12s** [-0.41, +0.18] | Paired delta: -0.12s [-0.41, +0.18] includes 0 (p > 0.05) |
| balanced | medium | `pressure` (37.1s) | `rl_dqn` (39.0s) | **TIE (`pressure` ~ `rl_dqn`)** | **-1.91s** [-5.10, +0.91] | Paired delta: -1.91s [-5.10, +0.91] includes 0 (p > 0.05) |
| balanced | heavy | `fixed_webster` (105.5s) | `rl_dqn` (105.9s) | **TIE (`fixed_webster` ~ `rl_dqn`)** | **-0.35s** [-2.52, +1.81] | Paired delta: -0.35s [-2.52, +1.81] includes 0 (p > 0.05) |
| imbalanced_orr | low | `pressure` (9.2s) | `fixed_webster` (9.2s) | **TIE (`pressure` ~ `fixed_webster`)** | **-0.06s** [-0.92, +0.80] | Paired delta: -0.06s [-0.92, +0.80] includes 0 (p > 0.05) |
| imbalanced_orr | medium | `pressure` (41.8s) | `fixed_webster` (42.2s) | **TIE (`pressure` ~ `fixed_webster`)** | **-0.39s** [-3.46, +2.54] | Paired delta: -0.39s [-3.46, +2.54] includes 0 (p > 0.05) |
| imbalanced_orr | heavy | `rl_dqn` (103.7s) | `adaptive` (104.2s) | **TIE (`rl_dqn` ~ `adaptive`)** | **-0.51s** [-2.98, +1.77] | Paired delta: -0.51s [-2.98, +1.77] includes 0 (p > 0.05) |
| imbalanced_varthur | low | `rl_dqn` (10.8s) | `pressure` (11.2s) | **TIE (`rl_dqn` ~ `pressure`)** | **-0.42s** [-1.18, +0.19] | Paired delta: -0.42s [-1.18, +0.19] includes 0 (p > 0.05) |
| imbalanced_varthur | medium | `pressure` (65.7s) | `adaptive` (66.8s) | **TIE (`pressure` ~ `adaptive`)** | **-1.14s** [-4.78, +3.05] | Paired delta: -1.14s [-4.78, +3.05] includes 0 (p > 0.05) |
| imbalanced_varthur | heavy | `rl_dqn` (127.5s) | `adaptive` (129.3s) | **TIE (`rl_dqn` ~ `adaptive`)** | **-1.83s** [-7.03, +4.08] | Paired delta: -1.83s [-7.03, +4.08] includes 0 (p > 0.05) |
| surge_orr_north | low | `pressure` (8.5s) | `fixed_webster` (8.6s) | **TIE (`pressure` ~ `fixed_webster`)** | **-0.18s** [-0.67, +0.29] | Paired delta: -0.18s [-0.67, +0.29] includes 0 (p > 0.05) |
| surge_orr_north | medium | `adaptive` (37.2s) | `fixed_webster` (37.3s) | **TIE (`adaptive` ~ `fixed_webster`)** | **-0.13s** [-2.39, +2.31] | Paired delta: -0.13s [-2.39, +2.31] includes 0 (p > 0.05) |
| surge_orr_north | heavy | `rl_dqn` (95.1s) | `adaptive` (95.5s) | **TIE (`rl_dqn` ~ `adaptive`)** | **-0.35s** [-4.30, +3.21] | Paired delta: -0.35s [-4.30, +3.21] includes 0 (p > 0.05) |

## 6. Directional Service Disparity & Approach Wait Gaps

Service disparity measures the imbalance in waiting times between competing directions:
$$\text{Disparity} = |\text{Wait}_{\text{NS}} - \text{Wait}_{\text{EW}}|$$
$$\text{Wait Gap} = \max(\text{Wait}_{\text{approach}}) - \min(\text{Wait}_{\text{approach}})$$

| Pattern | Level | Policy | Wait NS (s) | Wait EW (s) | Direction Disparity (s) | Approach Gap (s) |
|---|---|---|---:|---:|---:|---:|
| balanced | heavy | `adaptive` | 112.4 | 102.5 | 17.2 | 63.2 |
| balanced | heavy | `fixed` | 113.7 | 102.7 | 17.8 | 52.6 |
| balanced | heavy | `fixed_webster` | 113.8 | 97.5 | 23.3 | 63.4 |
| balanced | heavy | `pressure` | 112.6 | 102.2 | 18.1 | 61.0 |
| balanced | heavy | `rl_dqn` | 115.5 | 96.5 | 23.6 | 65.1 |
| balanced | low | `adaptive` | 7.4 | 7.5 | 0.9 | 2.8 |
| balanced | low | `fixed` | 14.3 | 16.0 | 2.5 | 5.9 |
| balanced | low | `fixed_webster` | 8.3 | 8.2 | 1.6 | 3.8 |
| balanced | low | `pressure` | 7.7 | 7.4 | 0.8 | 2.4 |
| balanced | low | `rl_dqn` | 8.7 | 7.7 | 1.7 | 3.5 |
| balanced | medium | `adaptive` | 46.8 | 33.9 | 13.7 | 45.7 |
| balanced | medium | `fixed` | 44.6 | 38.4 | 8.8 | 36.9 |
| balanced | medium | `fixed_webster` | 47.7 | 33.7 | 14.5 | 45.3 |
| balanced | medium | `pressure` | 40.9 | 33.4 | 10.3 | 37.7 |
| balanced | medium | `rl_dqn` | 44.2 | 34.0 | 10.4 | 42.9 |
| imbalanced_orr | heavy | `adaptive` | 73.4 | 183.9 | 110.5 | 146.9 |
| imbalanced_orr | heavy | `fixed` | 76.0 | 193.8 | 117.8 | 152.3 |
| imbalanced_orr | heavy | `fixed_webster` | 73.6 | 184.0 | 110.4 | 146.4 |
| imbalanced_orr | heavy | `pressure` | 76.3 | 184.9 | 108.7 | 140.2 |
| imbalanced_orr | heavy | `rl_dqn` | 72.5 | 184.5 | 112.0 | 152.1 |
| imbalanced_orr | low | `adaptive` | 6.3 | 17.2 | 10.9 | 14.8 |
| imbalanced_orr | low | `fixed` | 13.4 | 23.6 | 10.2 | 13.8 |
| imbalanced_orr | low | `fixed_webster` | 5.5 | 18.6 | 13.1 | 17.8 |
| imbalanced_orr | low | `pressure` | 6.2 | 16.9 | 10.7 | 14.8 |
| imbalanced_orr | low | `rl_dqn` | 5.9 | 17.9 | 12.0 | 15.7 |
| imbalanced_orr | medium | `adaptive` | 22.1 | 95.0 | 73.0 | 98.5 |
| imbalanced_orr | medium | `fixed` | 26.9 | 96.6 | 69.7 | 93.4 |
| imbalanced_orr | medium | `fixed_webster` | 19.9 | 100.2 | 80.4 | 105.0 |
| imbalanced_orr | medium | `pressure` | 20.8 | 96.3 | 75.5 | 100.8 |
| imbalanced_orr | medium | `rl_dqn` | 21.4 | 98.6 | 77.2 | 106.9 |
| imbalanced_varthur | heavy | `adaptive` | 233.4 | 91.1 | 142.3 | 199.4 |
| imbalanced_varthur | heavy | `fixed` | 236.7 | 97.3 | 139.3 | 199.7 |
| imbalanced_varthur | heavy | `fixed_webster` | 237.1 | 92.6 | 144.6 | 207.1 |
| imbalanced_varthur | heavy | `pressure` | 241.6 | 88.3 | 153.2 | 215.8 |
| imbalanced_varthur | heavy | `rl_dqn` | 232.8 | 88.8 | 144.0 | 202.1 |
| imbalanced_varthur | low | `adaptive` | 22.6 | 7.1 | 15.5 | 23.2 |
| imbalanced_varthur | low | `fixed` | 26.6 | 16.6 | 10.0 | 18.0 |
| imbalanced_varthur | low | `fixed_webster` | 24.6 | 6.5 | 18.0 | 27.1 |
| imbalanced_varthur | low | `pressure` | 21.9 | 7.1 | 14.8 | 21.6 |
| imbalanced_varthur | low | `rl_dqn` | 22.0 | 6.5 | 15.5 | 21.7 |
| imbalanced_varthur | medium | `adaptive` | 156.2 | 32.7 | 123.5 | 159.7 |
| imbalanced_varthur | medium | `fixed` | 160.9 | 39.4 | 121.5 | 159.3 |
| imbalanced_varthur | medium | `fixed_webster` | 163.4 | 34.3 | 129.0 | 165.3 |
| imbalanced_varthur | medium | `pressure` | 153.8 | 32.0 | 121.8 | 160.9 |
| imbalanced_varthur | medium | `rl_dqn` | 159.2 | 32.1 | 127.0 | 164.8 |
| surge_orr_north | heavy | `adaptive` | 88.3 | 106.4 | 18.2 | 55.1 |
| surge_orr_north | heavy | `fixed` | 93.0 | 110.5 | 18.5 | 46.8 |
| surge_orr_north | heavy | `fixed_webster` | 89.1 | 109.3 | 21.6 | 59.7 |
| surge_orr_north | heavy | `pressure` | 88.7 | 113.0 | 27.8 | 63.6 |
| surge_orr_north | heavy | `rl_dqn` | 87.1 | 107.3 | 24.6 | 55.8 |
| surge_orr_north | low | `adaptive` | 6.8 | 12.1 | 5.3 | 8.6 |
| surge_orr_north | low | `fixed` | 14.4 | 19.2 | 5.0 | 9.8 |
| surge_orr_north | low | `fixed_webster` | 6.0 | 12.6 | 6.6 | 9.6 |
| surge_orr_north | low | `pressure` | 6.5 | 11.5 | 5.0 | 8.4 |
| surge_orr_north | low | `rl_dqn` | 7.0 | 12.8 | 5.8 | 9.6 |
| surge_orr_north | medium | `adaptive` | 28.7 | 50.3 | 21.7 | 43.3 |
| surge_orr_north | medium | `fixed` | 31.6 | 58.5 | 26.9 | 49.2 |
| surge_orr_north | medium | `fixed_webster` | 27.9 | 51.8 | 23.9 | 44.6 |
| surge_orr_north | medium | `pressure` | 29.7 | 51.1 | 21.6 | 45.5 |
| surge_orr_north | medium | `rl_dqn` | 30.0 | 54.5 | 24.5 | 45.4 |

## 7. Known Trade-Offs & Honest Limitations

1. **Imbalance vs Surge Behavior:** Adaptive and pressure policies offer substantial reductions in vehicle delay under sustained demand imbalance (`imbalanced_ns`, `imbalanced_ew`). However, during temporary surges (`surge_north`), rapid queue clearance may incur switching lost time unless bounded by queue-extension or learned phase holding.
2. **Simulation Boundaries:** Experiments were executed on synthetic 300 m approach links with 150 m detector coverage. Unobserved queues beyond 150 m are not measured by sensors.
3. **Fixed-Time Baseline Adaptation:** The fixed-time plan is adapted from BTP Marathahalli Bridge junction schedule with clearance intervals (3s yellow, 2s all-red), omitting the pedestrian-only phase.

## 8. Artifact Manifest

- `manifest.json`: Complete execution metadata and environment configuration.
- `raw_runs.csv`: Unaggregated per-run metrics for every completed cell.
- `aggregate.csv`: Grouped means and standard deviations.
- `paired_deltas.csv`: Paired per-seed differences with bootstrap confidence intervals.
- `paired_ties.csv`: Paired within-seed bootstrap comparisons and tie classifications.
- `fairness_by_approach.csv`: Approach-level vehicle counts, delays, and detector queues.
- `fairness_by_direction.csv`: NS vs EW directional disparity summaries.
- `matrix_status.csv`: Cell-by-cell lifecycle tracking.
- `plots/`: Rendered figures (including `paired_best_ties.png`).
