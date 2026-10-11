# Adaptive Controller Tuning Results

## Search Space & Methodology
- **Grid Search Size**: 180 combinations ($5 \times 4 \times 3 \times 3$)
  - `k_s_per_m`: {0.15, 0.20, 0.30, 0.40, 0.50}
  - `max_green_s`: {30, 40, 45, 60}
  - `min_green_s`: {8, 10, 12}
  - `gap_out_s`: {2, 3, 5}
- **Training Seeds**: 1, 2, 3, 4, 5 (used for hyperparameter optimisation)
- **Held-Out Seeds**: 11, 12, 13, 14, 15 (evaluated strictly post-tuning)
- **Objective**: Minimize mean waiting time across all 4 scenarios on training seeds.

## Selected Parameters: Default vs Tuned Best
| Parameter | Default Value | Tuned Best Value |
|---|---|---|
| `k_s_per_m` | `0.3` | **`0.15`** |
| `max_green_s` | `60` | **`40`** |
| `min_green_s` | `10` | **`8`** |
| `gap_out_s` | `3` | **`2`** |

## 1. Training Seeds (1–5) Performance
| Scenario | Default Wait (s) | Tuned Best Wait (s) | Improvement (%) |
|---|---|---|---|
| `balanced` | 18.41 | 16.30 | +11.5% |
| `imbalanced_ns` | 44.47 | 42.51 | +4.4% |
| `imbalanced_ew` | 45.55 | 42.71 | +6.2% |
| `surge_north` | 55.22 | 54.88 | +0.6% |
| **Overall Mean** | **40.91** | **39.10** | **+4.4%** |

## 2. Held-Out Seeds (11–15) Evaluation (Generalisation Test)
> *Note: Seeds 11–15 were never seen during grid selection. This confirms whether gains transfer to unseen traffic arrivals.*

| Scenario | Default Wait (s) | Tuned Best Wait (s) | Wait Change (%) | Default Queue (m) | Tuned Queue (m) |
|---|---|---|---|---|---|
| `balanced` | 20.84 | 16.67 | +20.0% | 17.62 | 14.09 |
| `imbalanced_ns` | 44.46 | 43.38 | +2.4% | 48.40 | 49.27 |
| `imbalanced_ew` | 46.96 | 46.93 | +0.1% | 52.13 | 52.66 |
| `surge_north` | 56.80 | 53.23 | +6.3% | 47.90 | 45.76 |
| **Overall Mean** | **42.27** | **40.05** | **+5.2%** | - | - |

## 3. Top 5 Configurations on Training Seeds
| Rank | k_s_per_m | max_green_s | min_green_s | gap_out_s | Mean Wait (s) | Balanced | Imbal NS | Imbal EW | Surge North |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.15 | 40 | 8 | 2 | 39.10 | 16.30 | 42.51 | 42.71 | 54.88 |
| 2 | 0.3 | 45 | 8 | 2 | 39.38 | 17.33 | 44.32 | 42.58 | 53.28 |
| 3 | 0.15 | 45 | 8 | 2 | 39.43 | 16.89 | 40.91 | 42.83 | 57.08 |
| 4 | 0.15 | 45 | 8 | 5 | 39.46 | 16.95 | 43.07 | 43.21 | 54.62 |
| 5 | 0.2 | 40 | 8 | 2 | 39.52 | 16.61 | 44.49 | 42.91 | 54.07 |

