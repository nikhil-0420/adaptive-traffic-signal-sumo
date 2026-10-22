# DP1 Research Evaluation Report — Experiment `exp_marathahalli_site_720`

> **Simulation Integrity Notice — Marathahalli Real-Road Site Model**
> All metrics are derived from real execution of Eclipse SUMO with TraCI on the Marathahalli Bridge junction model.
> Topology and grade-separation are grounded in OpenCity GIS and OSM centerlines; traffic demand is synthetic on real geometry.
> Controller models and timings reflect the physical site layout and do not constitute live traffic sensor telemetry.

## 1. Executive Summary & Matrix Status

- **Network:** `Marathahalli Bridge Real-Road Site`
- **Experiment Status:** `COMPLETE` (720/720 cells completed)
- **Failed Cells:** 0
- **Blocked Cells:** 0
- **Execution Timestamp:** 2026-10-14T15:19:38Z
- **Bootstrap Configuration:** 10,000 resamples (seed: 42)

| Factor | Evaluated Levels |
|---|---|
| **Patterns** | balanced, imbalanced_orr, imbalanced_varthur, surge_orr_north |
| **Demand Levels** | low (x0.70), medium (x1.00), heavy (x1.30) |
| **Policies** | fixed, fixed_webster, adaptive, pressure, queue_extension, rl_dqn |
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
| balanced | heavy | `adaptive` | 10 | 107.5 ± 7.0 | 138.1 ± 8.9 | 1.9 ± 0.1 | 2854 | 100.0% |
| balanced | heavy | `fixed` | 10 | 109.6 ± 8.6 | 139.3 ± 11.2 | 6.7 ± 0.5 | 2873 | 100.0% |
| balanced | heavy | `fixed_webster` | 10 | 105.6 ± 6.9 | 136.1 ± 9.6 | 2.2 ± 0.2 | 2870 | 100.0% |
| balanced | heavy | `pressure` | 10 | 107.2 ± 7.3 | 138.0 ± 9.9 | 1.9 ± 0.1 | 2855 | 100.0% |
| balanced | heavy | `queue_extension` | 10 | 106.3 ± 6.9 | 136.8 ± 9.6 | 1.9 ± 0.1 | 2863 | 100.0% |
| balanced | heavy | `rl_dqn` | 10 | 105.4 ± 8.1 | 135.4 ± 10.8 | 1.8 ± 0.1 | 2866 | 100.0% |
| balanced | low | `adaptive` | 10 | 7.4 ± 0.6 | 14.1 ± 0.7 | 1.1 ± 0.1 | 1781 | 100.0% |
| balanced | low | `fixed` | 10 | 15.3 ± 0.8 | 22.0 ± 1.0 | 4.7 ± 0.4 | 1767 | 100.0% |
| balanced | low | `fixed_webster` | 10 | 8.2 ± 0.8 | 15.0 ± 0.9 | 1.3 ± 0.1 | 1780 | 100.0% |
| balanced | low | `pressure` | 10 | 7.6 ± 0.7 | 14.3 ± 0.7 | 1.1 ± 0.1 | 1780 | 100.0% |
| balanced | low | `queue_extension` | 10 | 7.6 ± 0.8 | 14.4 ± 1.0 | 1.1 ± 0.1 | 1780 | 100.0% |
| balanced | low | `rl_dqn` | 10 | 8.1 ± 1.1 | 14.8 ± 1.2 | 1.3 ± 0.1 | 1777 | 100.0% |
| balanced | medium | `adaptive` | 10 | 40.3 ± 6.6 | 53.4 ± 8.4 | 1.6 ± 0.1 | 2456 | 100.0% |
| balanced | medium | `fixed` | 10 | 41.9 ± 6.1 | 54.0 ± 7.8 | 6.3 ± 0.3 | 2464 | 100.0% |
| balanced | medium | `fixed_webster` | 10 | 40.7 ± 8.0 | 53.8 ± 9.9 | 1.9 ± 0.1 | 2459 | 100.0% |
| balanced | medium | `pressure` | 10 | 37.1 ± 6.4 | 49.6 ± 8.3 | 1.6 ± 0.1 | 2464 | 100.0% |
| balanced | medium | `queue_extension` | 10 | 38.6 ± 6.7 | 51.6 ± 8.6 | 1.6 ± 0.1 | 2460 | 100.0% |
| balanced | medium | `rl_dqn` | 10 | 38.8 ± 7.7 | 51.8 ± 9.8 | 1.7 ± 0.1 | 2465 | 100.0% |
| imbalanced_orr | heavy | `adaptive` | 10 | 104.2 ± 13.1 | 136.1 ± 15.6 | 2.8 ± 1.2 | 3268 | 100.0% |
| imbalanced_orr | heavy | `fixed` | 10 | 109.4 ± 13.6 | 140.2 ± 15.6 | 7.2 ± 0.8 | 3280 | 100.0% |
| imbalanced_orr | heavy | `fixed_webster` | 10 | 104.6 ± 13.6 | 136.7 ± 16.3 | 2.8 ± 1.0 | 3263 | 100.0% |
| imbalanced_orr | heavy | `pressure` | 10 | 106.6 ± 12.3 | 139.8 ± 14.5 | 3.1 ± 1.6 | 3255 | 100.0% |
| imbalanced_orr | heavy | `queue_extension` | 10 | 105.0 ± 15.7 | 136.7 ± 18.6 | 2.7 ± 1.0 | 3271 | 100.0% |
| imbalanced_orr | heavy | `rl_dqn` | 10 | 104.0 ± 11.5 | 136.2 ± 14.7 | 2.4 ± 0.6 | 3267 | 100.0% |
| imbalanced_orr | low | `adaptive` | 10 | 9.3 ± 1.7 | 16.2 ± 2.0 | 1.2 ± 0.1 | 1966 | 100.0% |
| imbalanced_orr | low | `fixed` | 10 | 17.3 ± 1.6 | 24.2 ± 1.8 | 5.2 ± 0.3 | 1960 | 100.0% |
| imbalanced_orr | low | `fixed_webster` | 10 | 9.2 ± 2.0 | 16.0 ± 2.3 | 1.3 ± 0.1 | 1965 | 100.0% |
| imbalanced_orr | low | `pressure` | 10 | 9.2 ± 1.7 | 16.0 ± 1.9 | 1.2 ± 0.1 | 1966 | 100.0% |
| imbalanced_orr | low | `queue_extension` | 10 | 9.0 ± 1.5 | 15.9 ± 1.6 | 1.3 ± 0.1 | 1968 | 100.0% |
| imbalanced_orr | low | `rl_dqn` | 10 | 9.3 ± 2.0 | 16.1 ± 2.2 | 1.3 ± 0.1 | 1963 | 100.0% |
| imbalanced_orr | medium | `adaptive` | 10 | 42.3 ± 10.8 | 55.2 ± 12.7 | 1.9 ± 0.2 | 2723 | 100.0% |
| imbalanced_orr | medium | `fixed` | 10 | 47.6 ± 9.1 | 60.1 ± 10.3 | 6.4 ± 0.3 | 2728 | 100.0% |
| imbalanced_orr | medium | `fixed_webster` | 10 | 42.4 ± 10.1 | 55.0 ± 11.4 | 1.8 ± 0.2 | 2730 | 100.0% |
| imbalanced_orr | medium | `pressure` | 10 | 41.8 ± 9.9 | 54.7 ± 11.3 | 1.8 ± 0.2 | 2725 | 100.0% |
| imbalanced_orr | medium | `queue_extension` | 10 | 41.2 ± 10.9 | 53.9 ± 12.4 | 1.8 ± 0.2 | 2732 | 100.0% |
| imbalanced_orr | medium | `rl_dqn` | 10 | 42.8 ± 9.1 | 55.8 ± 10.4 | 1.7 ± 0.2 | 2729 | 100.0% |
| imbalanced_varthur | heavy | `adaptive` | 10 | 129.7 ± 14.6 | 171.2 ± 17.6 | 6.1 ± 1.3 | 3040 | 100.0% |
| imbalanced_varthur | heavy | `fixed` | 10 | 132.2 ± 12.6 | 172.2 ± 16.1 | 9.0 ± 1.0 | 3049 | 100.0% |
| imbalanced_varthur | heavy | `fixed_webster` | 10 | 130.6 ± 14.1 | 173.0 ± 18.9 | 5.9 ± 1.3 | 3046 | 100.0% |
| imbalanced_varthur | heavy | `pressure` | 10 | 129.0 ± 13.4 | 171.5 ± 15.1 | 6.1 ± 1.6 | 3045 | 100.0% |
| imbalanced_varthur | heavy | `queue_extension` | 10 | 128.5 ± 17.1 | 171.3 ± 21.5 | 5.8 ± 1.5 | 3032 | 100.0% |
| imbalanced_varthur | heavy | `rl_dqn` | 10 | 127.3 ± 17.1 | 169.8 ± 20.7 | 5.0 ± 1.2 | 3031 | 100.0% |
| imbalanced_varthur | low | `adaptive` | 10 | 11.3 ± 1.6 | 18.9 ± 2.0 | 1.3 ± 0.1 | 1976 | 100.0% |
| imbalanced_varthur | low | `fixed` | 10 | 18.2 ± 2.0 | 25.8 ± 2.6 | 4.8 ± 0.4 | 1958 | 100.0% |
| imbalanced_varthur | low | `fixed_webster` | 10 | 11.6 ± 2.7 | 19.2 ± 3.2 | 1.3 ± 0.1 | 1977 | 100.0% |
| imbalanced_varthur | low | `pressure` | 10 | 11.3 ± 1.9 | 18.8 ± 2.3 | 1.2 ± 0.1 | 1977 | 100.0% |
| imbalanced_varthur | low | `queue_extension` | 10 | 11.1 ± 1.2 | 18.7 ± 1.5 | 1.2 ± 0.1 | 1978 | 100.0% |
| imbalanced_varthur | low | `rl_dqn` | 10 | 10.8 ± 1.2 | 18.2 ± 1.4 | 1.3 ± 0.1 | 1975 | 100.0% |
| imbalanced_varthur | medium | `adaptive` | 10 | 66.8 ± 10.4 | 84.3 ± 12.4 | 2.0 ± 0.4 | 2685 | 100.0% |
| imbalanced_varthur | medium | `fixed` | 10 | 71.3 ± 11.4 | 88.1 ± 13.3 | 6.3 ± 0.5 | 2668 | 100.0% |
| imbalanced_varthur | medium | `fixed_webster` | 10 | 68.5 ± 11.9 | 86.1 ± 14.2 | 2.0 ± 0.6 | 2674 | 100.0% |
| imbalanced_varthur | medium | `pressure` | 10 | 64.9 ± 12.4 | 82.1 ± 13.9 | 2.2 ± 1.3 | 2684 | 100.0% |
| imbalanced_varthur | medium | `queue_extension` | 10 | 67.1 ± 12.2 | 84.2 ± 14.0 | 2.1 ± 0.7 | 2680 | 100.0% |
| imbalanced_varthur | medium | `rl_dqn` | 10 | 67.4 ± 11.8 | 84.4 ± 13.4 | 2.1 ± 1.0 | 2683 | 100.0% |
| surge_orr_north | heavy | `adaptive` | 10 | 96.2 ± 7.6 | 126.1 ± 9.5 | 2.6 ± 0.8 | 2945 | 100.0% |
| surge_orr_north | heavy | `fixed` | 10 | 100.7 ± 7.5 | 130.3 ± 9.6 | 7.2 ± 0.7 | 2960 | 100.0% |
| surge_orr_north | heavy | `fixed_webster` | 10 | 97.1 ± 8.7 | 127.2 ± 10.9 | 2.8 ± 0.6 | 2938 | 100.0% |
| surge_orr_north | heavy | `pressure` | 10 | 98.3 ± 5.1 | 128.7 ± 6.7 | 2.6 ± 0.7 | 2941 | 100.0% |
| surge_orr_north | heavy | `queue_extension` | 10 | 95.2 ± 6.9 | 125.2 ± 9.0 | 2.4 ± 0.5 | 2954 | 100.0% |
| surge_orr_north | heavy | `rl_dqn` | 10 | 95.1 ± 7.6 | 125.1 ± 10.0 | 2.4 ± 0.4 | 2947 | 100.0% |
| surge_orr_north | low | `adaptive` | 10 | 8.9 ± 1.5 | 15.8 ± 1.8 | 1.2 ± 0.1 | 1761 | 100.0% |
| surge_orr_north | low | `fixed` | 10 | 16.6 ± 2.1 | 23.6 ± 2.5 | 4.6 ± 0.4 | 1753 | 100.0% |
| surge_orr_north | low | `fixed_webster` | 10 | 8.6 ± 1.3 | 15.4 ± 1.5 | 1.3 ± 0.1 | 1762 | 100.0% |
| surge_orr_north | low | `pressure` | 10 | 8.5 ± 1.8 | 15.4 ± 2.1 | 1.1 ± 0.1 | 1761 | 100.0% |
| surge_orr_north | low | `queue_extension` | 10 | 9.1 ± 1.1 | 16.1 ± 1.4 | 1.1 ± 0.1 | 1761 | 100.0% |
| surge_orr_north | low | `rl_dqn` | 10 | 9.3 ± 1.5 | 16.2 ± 1.9 | 1.2 ± 0.1 | 1759 | 100.0% |
| surge_orr_north | medium | `adaptive` | 10 | 37.3 ± 8.2 | 51.1 ± 10.6 | 1.8 ± 0.3 | 2505 | 100.0% |
| surge_orr_north | medium | `fixed` | 10 | 43.2 ± 7.3 | 56.4 ± 8.9 | 6.1 ± 0.3 | 2502 | 100.0% |
| surge_orr_north | medium | `fixed_webster` | 10 | 37.3 ± 5.2 | 50.8 ± 6.5 | 1.9 ± 0.2 | 2508 | 100.0% |
| surge_orr_north | medium | `pressure` | 10 | 37.7 ± 8.9 | 51.4 ± 11.0 | 1.7 ± 0.3 | 2506 | 100.0% |
| surge_orr_north | medium | `queue_extension` | 10 | 39.3 ± 8.2 | 53.4 ± 10.2 | 1.7 ± 0.3 | 2503 | 100.0% |
| surge_orr_north | medium | `rl_dqn` | 10 | 39.5 ± 8.5 | 53.7 ± 10.8 | 1.7 ± 0.2 | 2507 | 100.0% |

## 4. Paired Delta Analysis vs Fixed Baseline (95% Bootstrap CI)

Paired differences are calculated per-seed against `fixed` under identical arrival traffic:
$$\Delta = \text{Metric}_{\text{candidate}} - \text{Metric}_{\text{fixed}}$$
A **negative delta** indicates a reduction (improvement) in delay or queuing relative to the fixed plan.

| Pattern | Level | Policy | Valid Pairs | Delta Wait (s) [95% CI] | Delta Time Loss (s) [95% CI] | Delta Queue (m) |
|---|---|---|---:|---|---|---:|
| balanced | low | `fixed_webster` | 10 | **-7.03** [-7.41, -6.70] | -7.06 [-7.47, -6.71] | -3.47 |
| balanced | low | `adaptive` | 10 | **-7.90** [-8.30, -7.51] | -7.97 [-8.43, -7.55] | -3.62 |
| balanced | low | `pressure` | 10 | **-7.72** [-8.21, -7.26] | -7.76 [-8.34, -7.23] | -3.62 |
| balanced | low | `queue_extension` | 10 | **-7.67** [-8.19, -7.09] | -7.68 [-8.24, -7.05] | -3.64 |
| balanced | low | `rl_dqn` | 10 | **-7.13** [-7.74, -6.48] | -7.21 [-7.85, -6.54] | -3.46 |
| balanced | medium | `fixed_webster` | 10 | **-1.21** [-4.99, +1.88] | -0.17 [-4.62, +3.56] | -4.47 |
| balanced | medium | `adaptive` | 10 | **-1.65** [-4.11, +0.43] | -0.61 [-3.68, +1.97] | -4.71 |
| balanced | medium | `pressure` | 10 | **-4.78** [-7.88, -2.00] | -4.41 [-8.28, -0.90] | -4.70 |
| balanced | medium | `queue_extension` | 10 | **-3.30** [-5.91, -0.66] | -2.40 [-5.83, +0.87] | -4.71 |
| balanced | medium | `rl_dqn` | 10 | **-3.12** [-5.19, -1.03] | -2.21 [-4.82, +0.30] | -4.64 |
| balanced | heavy | `fixed_webster` | 10 | **-4.01** [-6.33, -1.18] | -3.28 [-5.91, -0.06] | -4.48 |
| balanced | heavy | `adaptive` | 10 | **-2.13** [-5.35, +1.20] | -1.26 [-5.60, +3.03] | -4.79 |
| balanced | heavy | `pressure` | 10 | **-2.40** [-5.01, +0.22] | -1.38 [-4.72, +1.87] | -4.74 |
| balanced | heavy | `queue_extension` | 10 | **-3.36** [-6.25, -0.40] | -2.55 [-6.21, +1.26] | -4.75 |
| balanced | heavy | `rl_dqn` | 10 | **-4.18** [-7.03, -1.39] | -3.89 [-7.73, -0.20] | -4.83 |
| imbalanced_orr | low | `fixed_webster` | 10 | **-8.02** [-8.53, -7.56] | -8.22 [-8.80, -7.70] | -3.90 |
| imbalanced_orr | low | `adaptive` | 10 | **-7.94** [-8.62, -7.05] | -8.00 [-8.75, -6.96] | -3.95 |
| imbalanced_orr | low | `pressure` | 10 | **-8.08** [-8.74, -7.27] | -8.18 [-8.95, -7.21] | -3.94 |
| imbalanced_orr | low | `queue_extension` | 10 | **-8.27** [-8.55, -7.98] | -8.36 [-8.68, -8.03] | -3.92 |
| imbalanced_orr | low | `rl_dqn` | 10 | **-7.97** [-8.60, -7.36] | -8.16 [-8.89, -7.47] | -3.91 |
| imbalanced_orr | medium | `fixed_webster` | 10 | **-5.23** [-7.22, -3.01] | -5.07 [-7.13, -2.86] | -4.61 |
| imbalanced_orr | medium | `adaptive` | 10 | **-5.30** [-7.75, -3.02] | -4.90 [-7.76, -2.06] | -4.58 |
| imbalanced_orr | medium | `pressure` | 10 | **-5.80** [-7.33, -4.14] | -5.39 [-7.22, -3.41] | -4.61 |
| imbalanced_orr | medium | `queue_extension` | 10 | **-6.42** [-8.41, -4.45] | -6.16 [-8.36, -4.10] | -4.67 |
| imbalanced_orr | medium | `rl_dqn` | 10 | **-4.77** [-5.83, -3.53] | -4.23 [-5.50, -2.87] | -4.75 |
| imbalanced_orr | heavy | `fixed_webster` | 10 | **-4.84** [-8.70, -0.64] | -3.47 [-8.51, +2.19] | -4.42 |
| imbalanced_orr | heavy | `adaptive` | 10 | **-5.17** [-7.63, -2.43] | -4.13 [-7.27, -0.69] | -4.37 |
| imbalanced_orr | heavy | `pressure` | 10 | **-2.78** [-7.88, +2.51] | -0.41 [-6.48, +6.08] | -4.11 |
| imbalanced_orr | heavy | `queue_extension` | 10 | **-4.42** [-7.92, -0.65] | -3.56 [-8.22, +1.30] | -4.48 |
| imbalanced_orr | heavy | `rl_dqn` | 10 | **-5.45** [-8.84, -2.37] | -4.02 [-7.38, -0.68] | -4.76 |
| imbalanced_varthur | low | `fixed_webster` | 10 | **-6.58** [-7.64, -5.43] | -6.66 [-7.88, -5.34] | -3.53 |
| imbalanced_varthur | low | `adaptive` | 10 | **-6.91** [-7.97, -5.80] | -6.92 [-8.10, -5.70] | -3.56 |
| imbalanced_varthur | low | `pressure` | 10 | **-6.93** [-7.74, -6.12] | -6.99 [-7.90, -6.07] | -3.59 |
| imbalanced_varthur | low | `queue_extension` | 10 | **-7.05** [-7.83, -6.31] | -7.12 [-8.09, -6.23] | -3.58 |
| imbalanced_varthur | low | `rl_dqn` | 10 | **-7.36** [-8.27, -6.38] | -7.65 [-8.70, -6.53] | -3.54 |
| imbalanced_varthur | medium | `fixed_webster` | 10 | **-2.83** [-4.95, -0.54] | -2.01 [-4.58, +0.88] | -4.31 |
| imbalanced_varthur | medium | `adaptive` | 10 | **-4.49** [-7.33, -2.17] | -3.83 [-7.29, -0.81] | -4.30 |
| imbalanced_varthur | medium | `pressure` | 10 | **-6.38** [-8.14, -4.70] | -6.05 [-8.46, -3.87] | -4.13 |
| imbalanced_varthur | medium | `queue_extension` | 10 | **-4.23** [-6.29, -2.31] | -3.95 [-6.12, -1.84] | -4.26 |
| imbalanced_varthur | medium | `rl_dqn` | 10 | **-3.94** [-6.19, -1.48] | -3.71 [-6.18, -0.93] | -4.20 |
| imbalanced_varthur | heavy | `fixed_webster` | 10 | **-1.59** [-5.57, +2.08] | +0.76 [-4.32, +5.74] | -3.03 |
| imbalanced_varthur | heavy | `adaptive` | 10 | **-2.54** [-6.10, +0.97] | -1.07 [-4.96, +2.90] | -2.88 |
| imbalanced_varthur | heavy | `pressure` | 10 | **-3.23** [-6.78, +0.18] | -0.73 [-4.49, +3.17] | -2.86 |
| imbalanced_varthur | heavy | `queue_extension` | 10 | **-3.71** [-8.06, +0.28] | -0.89 [-6.06, +4.08] | -3.20 |
| imbalanced_varthur | heavy | `rl_dqn` | 10 | **-4.94** [-9.11, -0.89] | -2.47 [-7.58, +2.55] | -3.95 |
| surge_orr_north | low | `fixed_webster` | 10 | **-7.93** [-8.95, -6.95] | -8.14 [-9.38, -7.00] | -3.33 |
| surge_orr_north | low | `adaptive` | 10 | **-7.68** [-8.72, -6.69] | -7.74 [-8.89, -6.67] | -3.43 |
| surge_orr_north | low | `pressure` | 10 | **-8.11** [-9.08, -7.20] | -8.21 [-9.35, -7.17] | -3.52 |
| surge_orr_north | low | `queue_extension` | 10 | **-7.50** [-8.57, -6.56] | -7.51 [-8.74, -6.49] | -3.51 |
| surge_orr_north | low | `rl_dqn` | 10 | **-7.27** [-8.22, -6.39] | -7.41 [-8.56, -6.34] | -3.36 |
| surge_orr_north | medium | `fixed_webster` | 10 | **-5.89** [-8.08, -3.99] | -5.59 [-8.36, -3.24] | -4.21 |
| surge_orr_north | medium | `adaptive` | 10 | **-5.91** [-8.03, -3.89] | -5.22 [-8.02, -2.15] | -4.28 |
| surge_orr_north | medium | `pressure` | 10 | **-5.45** [-7.74, -3.30] | -4.92 [-7.67, -2.26] | -4.33 |
| surge_orr_north | medium | `queue_extension` | 10 | **-3.87** [-6.65, -0.61] | -2.95 [-6.48, +1.19] | -4.35 |
| surge_orr_north | medium | `rl_dqn` | 10 | **-3.69** [-6.12, -0.96] | -2.70 [-5.84, +0.75] | -4.33 |
| surge_orr_north | heavy | `fixed_webster` | 10 | **-3.60** [-6.12, -1.04] | -3.08 [-6.39, +0.14] | -4.40 |
| surge_orr_north | heavy | `adaptive` | 10 | **-4.49** [-7.19, -1.89] | -4.27 [-7.75, -0.87] | -4.54 |
| surge_orr_north | heavy | `pressure` | 10 | **-2.44** [-5.08, +0.13] | -1.63 [-5.05, +1.79] | -4.54 |
| surge_orr_north | heavy | `queue_extension` | 10 | **-5.47** [-8.86, -2.02] | -5.12 [-9.28, -0.61] | -4.77 |
| surge_orr_north | heavy | `rl_dqn` | 10 | **-5.58** [-9.16, -1.68] | -5.23 [-9.66, -0.53] | -4.81 |

## 5. Paired Statistical Best Policy & Tie Analysis (Within-Seed Bootstrapping)

To eliminate inter-seed variance, candidates are compared by bootstrapping the paired difference in waiting time
across identical simulation seeds: $\Delta_{\text{paired}}(s) = \text{Wait}_{\text{leader}}(s) - \text{Wait}_{\text{runner\_up}}(s)$.
If 0 is included within the 95% paired bootstrap confidence interval ($B=10,000$), the outcome is classified as a
**Statistical Tie** (`leader ~ runner_up`, 95% bootstrap CI spans zero). If $\text{CI}_{\text{upper}} < 0$, the primary leader
demonstrates a statistically distinguishable reduction in delay over the runner-up at the 95% confidence level.

| Pattern | Demand Level | Primary Leader | Secondary Candidate | Outcome Classification | Paired Delta [95% CI] | Statistical Evidence |
|---|---|---|---|---|---:|---|
| balanced | low | `adaptive` (7.4s) | `pressure` (7.5s) | **TIE (`adaptive` ~ `pressure`)** | **-0.18s** [-0.45, +0.12] | Paired delta: -0.18s [-0.45, +0.12] includes 0 (statistically indistinguishable at 95% CI) |
| balanced | medium | `pressure` (37.1s) | `queue_extension` (38.6s) | **TIE (`pressure` ~ `queue_extension`)** | **-1.48s** [-3.17, +0.15] | Paired delta: -1.48s [-3.17, +0.15] includes 0 (statistically indistinguishable at 95% CI) |
| balanced | heavy | `rl_dqn` (105.5s) | `fixed_webster` (105.6s) | **TIE (`rl_dqn` ~ `fixed_webster`)** | **-0.17s** [-2.61, +2.26] | Paired delta: -0.17s [-2.61, +2.26] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_orr | low | `queue_extension` (9.0s) | `pressure` (9.2s) | **TIE (`queue_extension` ~ `pressure`)** | **-0.19s** [-0.90, +0.41] | Paired delta: -0.19s [-0.90, +0.41] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_orr | medium | `queue_extension` (41.2s) | `pressure` (41.8s) | **TIE (`queue_extension` ~ `pressure`)** | **-0.61s** [-2.71, +1.49] | Paired delta: -0.61s [-2.71, +1.49] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_orr | heavy | `rl_dqn` (104.0s) | `adaptive` (104.2s) | **TIE (`rl_dqn` ~ `adaptive`)** | **-0.28s** [-2.68, +1.85] | Paired delta: -0.28s [-2.68, +1.85] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_varthur | low | `rl_dqn` (10.8s) | `queue_extension` (11.1s) | **TIE (`rl_dqn` ~ `queue_extension`)** | **-0.31s** [-0.82, +0.18] | Paired delta: -0.31s [-0.82, +0.18] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_varthur | medium | `pressure` (64.9s) | `adaptive` (66.8s) | **TIE (`pressure` ~ `adaptive`)** | **-1.89s** [-5.29, +2.23] | Paired delta: -1.89s [-5.29, +2.23] includes 0 (statistically indistinguishable at 95% CI) |
| imbalanced_varthur | heavy | `rl_dqn` (127.3s) | `queue_extension` (128.5s) | **TIE (`rl_dqn` ~ `queue_extension`)** | **-1.23s** [-4.71, +2.31] | Paired delta: -1.23s [-4.71, +2.31] includes 0 (statistically indistinguishable at 95% CI) |
| surge_orr_north | low | `pressure` (8.5s) | `fixed_webster` (8.6s) | **TIE (`pressure` ~ `fixed_webster`)** | **-0.18s** [-0.67, +0.29] | Paired delta: -0.18s [-0.67, +0.29] includes 0 (statistically indistinguishable at 95% CI) |
| surge_orr_north | medium | `adaptive` (37.3s) | `fixed_webster` (37.3s) | **TIE (`adaptive` ~ `fixed_webster`)** | **-0.03s** [-2.25, +2.36] | Paired delta: -0.03s [-2.25, +2.36] includes 0 (statistically indistinguishable at 95% CI) |
| surge_orr_north | heavy | `rl_dqn` (95.1s) | `queue_extension` (95.2s) | **TIE (`rl_dqn` ~ `queue_extension`)** | **-0.12s** [-3.82, +4.02] | Paired delta: -0.12s [-3.82, +4.02] includes 0 (statistically indistinguishable at 95% CI) |

## 6. Directional Service Disparity & Approach Wait Gaps

Service disparity measures the imbalance in waiting times between competing directions:
$$\text{Disparity} = |\text{Wait}_{\text{NS}} - \text{Wait}_{\text{EW}}|$$
$$\text{Wait Gap} = \max(\text{Wait}_{\text{approach}}) - \min(\text{Wait}_{\text{approach}})$$

| Pattern | Level | Policy | Wait NS (s) | Wait EW (s) | Direction Disparity (s) | Approach Gap (s) |
|---|---|---|---:|---:|---:|---:|
| balanced | heavy | `adaptive` | 112.2 | 102.8 | 16.4 | 61.5 |
| balanced | heavy | `fixed` | 119.6 | 99.8 | 24.6 | 55.6 |
| balanced | heavy | `fixed_webster` | 114.1 | 97.3 | 22.2 | 60.7 |
| balanced | heavy | `pressure` | 113.7 | 100.8 | 19.8 | 63.1 |
| balanced | heavy | `queue_extension` | 114.0 | 98.8 | 20.5 | 55.5 |
| balanced | heavy | `rl_dqn` | 114.3 | 96.8 | 22.6 | 62.8 |
| balanced | low | `adaptive` | 7.3 | 7.5 | 0.7 | 2.5 |
| balanced | low | `fixed` | 16.4 | 14.2 | 2.4 | 5.7 |
| balanced | low | `fixed_webster` | 8.3 | 8.2 | 1.6 | 3.8 |
| balanced | low | `pressure` | 7.7 | 7.4 | 0.8 | 2.4 |
| balanced | low | `queue_extension` | 7.7 | 7.5 | 1.1 | 2.8 |
| balanced | low | `rl_dqn` | 8.6 | 7.7 | 1.6 | 3.5 |
| balanced | medium | `adaptive` | 46.8 | 33.9 | 13.7 | 45.6 |
| balanced | medium | `fixed` | 47.9 | 36.0 | 14.0 | 39.5 |
| balanced | medium | `fixed_webster` | 47.3 | 34.2 | 13.7 | 44.0 |
| balanced | medium | `pressure` | 40.9 | 33.4 | 10.3 | 37.7 |
| balanced | medium | `queue_extension` | 42.6 | 34.6 | 12.7 | 42.0 |
| balanced | medium | `rl_dqn` | 43.9 | 33.7 | 10.4 | 42.6 |
| imbalanced_orr | heavy | `adaptive` | 73.4 | 183.9 | 110.5 | 146.9 |
| imbalanced_orr | heavy | `fixed` | 78.8 | 188.4 | 109.6 | 143.6 |
| imbalanced_orr | heavy | `fixed_webster` | 73.6 | 184.5 | 110.8 | 147.2 |
| imbalanced_orr | heavy | `pressure` | 76.3 | 184.9 | 108.6 | 140.2 |
| imbalanced_orr | heavy | `queue_extension` | 74.3 | 184.2 | 109.9 | 147.6 |
| imbalanced_orr | heavy | `rl_dqn` | 73.5 | 182.6 | 109.1 | 150.0 |
| imbalanced_orr | low | `adaptive` | 6.2 | 17.2 | 10.9 | 14.8 |
| imbalanced_orr | low | `fixed` | 15.4 | 21.9 | 6.5 | 9.4 |
| imbalanced_orr | low | `fixed_webster` | 5.5 | 18.6 | 13.1 | 17.8 |
| imbalanced_orr | low | `pressure` | 6.2 | 16.9 | 10.7 | 14.8 |
| imbalanced_orr | low | `queue_extension` | 6.2 | 16.1 | 9.9 | 13.8 |
| imbalanced_orr | low | `rl_dqn` | 5.9 | 17.9 | 12.0 | 15.7 |
| imbalanced_orr | medium | `adaptive` | 22.1 | 95.0 | 73.0 | 98.5 |
| imbalanced_orr | medium | `fixed` | 28.9 | 96.2 | 67.3 | 92.2 |
| imbalanced_orr | medium | `fixed_webster` | 20.2 | 99.9 | 79.7 | 105.0 |
| imbalanced_orr | medium | `pressure` | 20.8 | 96.3 | 75.5 | 100.8 |
| imbalanced_orr | medium | `queue_extension` | 20.8 | 93.9 | 73.1 | 98.4 |
| imbalanced_orr | medium | `rl_dqn` | 21.4 | 98.6 | 77.2 | 106.9 |
| imbalanced_varthur | heavy | `adaptive` | 236.8 | 90.2 | 146.6 | 201.8 |
| imbalanced_varthur | heavy | `fixed` | 235.7 | 94.2 | 141.6 | 206.2 |
| imbalanced_varthur | heavy | `fixed_webster` | 237.3 | 91.4 | 145.9 | 206.3 |
| imbalanced_varthur | heavy | `pressure` | 240.7 | 88.0 | 152.7 | 215.6 |
| imbalanced_varthur | heavy | `queue_extension` | 234.5 | 89.5 | 144.9 | 201.0 |
| imbalanced_varthur | heavy | `rl_dqn` | 232.8 | 88.5 | 144.2 | 202.8 |
| imbalanced_varthur | low | `adaptive` | 22.1 | 7.1 | 15.0 | 22.5 |
| imbalanced_varthur | low | `fixed` | 27.5 | 14.6 | 12.8 | 19.4 |
| imbalanced_varthur | low | `fixed_webster` | 24.6 | 6.6 | 18.1 | 26.9 |
| imbalanced_varthur | low | `pressure` | 22.0 | 7.1 | 14.8 | 22.2 |
| imbalanced_varthur | low | `queue_extension` | 21.6 | 7.2 | 14.4 | 22.1 |
| imbalanced_varthur | low | `rl_dqn` | 22.0 | 6.5 | 15.5 | 21.6 |
| imbalanced_varthur | medium | `adaptive` | 156.2 | 32.7 | 123.5 | 159.7 |
| imbalanced_varthur | medium | `fixed` | 160.6 | 37.2 | 123.4 | 159.1 |
| imbalanced_varthur | medium | `fixed_webster` | 161.2 | 33.0 | 128.2 | 162.2 |
| imbalanced_varthur | medium | `pressure` | 152.1 | 31.6 | 120.5 | 158.0 |
| imbalanced_varthur | medium | `queue_extension` | 156.5 | 32.9 | 123.7 | 163.4 |
| imbalanced_varthur | medium | `rl_dqn` | 156.9 | 33.1 | 123.7 | 162.4 |
| surge_orr_north | heavy | `adaptive` | 88.9 | 107.4 | 18.5 | 55.8 |
| surge_orr_north | heavy | `fixed` | 92.7 | 113.0 | 23.5 | 50.3 |
| surge_orr_north | heavy | `fixed_webster` | 89.1 | 109.3 | 21.6 | 59.7 |
| surge_orr_north | heavy | `pressure` | 88.7 | 112.9 | 27.6 | 63.4 |
| surge_orr_north | heavy | `queue_extension` | 87.2 | 107.5 | 24.7 | 54.3 |
| surge_orr_north | heavy | `rl_dqn` | 87.1 | 107.3 | 24.6 | 55.8 |
| surge_orr_north | low | `adaptive` | 6.8 | 12.1 | 5.3 | 8.6 |
| surge_orr_north | low | `fixed` | 16.2 | 17.0 | 2.5 | 7.1 |
| surge_orr_north | low | `fixed_webster` | 6.0 | 12.6 | 6.6 | 9.6 |
| surge_orr_north | low | `pressure` | 6.5 | 11.5 | 5.0 | 8.4 |
| surge_orr_north | low | `queue_extension` | 6.7 | 12.5 | 5.8 | 9.7 |
| surge_orr_north | low | `rl_dqn` | 7.0 | 12.8 | 5.8 | 9.6 |
| surge_orr_north | medium | `adaptive` | 28.8 | 50.4 | 21.6 | 43.1 |
| surge_orr_north | medium | `fixed` | 35.3 | 55.5 | 20.8 | 39.8 |
| surge_orr_north | medium | `fixed_webster` | 27.9 | 51.8 | 23.9 | 44.6 |
| surge_orr_north | medium | `pressure` | 29.5 | 50.5 | 21.3 | 45.5 |
| surge_orr_north | medium | `queue_extension` | 30.7 | 52.6 | 23.3 | 43.9 |
| surge_orr_north | medium | `rl_dqn` | 30.0 | 54.4 | 24.4 | 45.0 |

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
