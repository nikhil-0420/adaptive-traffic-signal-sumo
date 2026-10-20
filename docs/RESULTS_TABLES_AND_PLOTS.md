# DP1 Research Results: Audited Tables, Plots, and Statistical Analysis

This document compiles the independently audited empirical findings from the **720-cell Marathahalli Site Evaluation Matrix** (`exp_marathahalli_site_720`) and the **360-run Emergency Vehicle Priority Evaluation** (`exp_marathahalli_emergency_360`), alongside historical and synthetic baseline comparisons.

> **Data Integrity Certification:**  
> All numbers presented here are derived directly from real execution traces of Eclipse SUMO v1.28.0 and TraCI in the `results/research/` directory. Zero values are fabricated, extrapolated, or hand-edited.

---

## 1. Experimental Setup and Dimension Verification

### 1.1 Study Matrix Dimensions

| Study Identifier | Network Model | Inflow Patterns | Demand Levels | Control Policies | Held-Out Seeds | Total Cells | Status |
|---|---|---|---|---|---|---|:---:|
| **`exp_marathahalli_hybrid_840`** | Marathahalli Junction | 4 patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`) | 3 levels (`low`, `medium`, `heavy`) | 7 policies (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `queue_extension`, `rl_dqn`, `hybrid_queue_adaptive`) | 10 seeds (`121–130`) | **840** | **Complete (100%)** |
| **`exp_marathahalli_site_720`** | Marathahalli Junction | 4 patterns | 3 levels | 6 policies | 10 seeds (`121–130`) | **720** | **Complete (100%)** |
| **`exp_marathahalli_emergency_360`** | Marathahalli Junction | 2 patterns (`balanced`, `surge_orr_north`) | 3 levels (`low`, `medium`, `heavy`) | 3 policies (`fixed`, `pressure`, `rl_dqn`) | 10 seeds (`121–130`) | **360** (180 matched pairs) | **Complete (100%)** |
| **`exp_marathahalli_site` (Historical)** | Marathahalli Junction | 4 patterns | 3 levels | 5 policies (without `queue_extension`) | 10 seeds (`121–130`) | **600** | **Archived** |
| **`exp_primary_720` (Synthetic)** | Synthetic 4-Way | 4 patterns | 3 levels | 6 policies | 10 seeds (`21–30`) | **720** | **Complete (100%)** |

### 1.2 Data Integrity Audit
An automated verification script (`scratch/audit_experiments.py`) verified the datasets:
- **Missing / Null Values:** 0 nulls across all critical metrics (`avg_wait_s`, `avg_time_loss_s`, `avg_queue_m`, `throughput_veh_per_h`, `completion_rate`).
- **Duplicate Runs:** 0 duplicate condition keys.
- **Parametric Agreement:** Recomputed raw means from `raw_runs.csv` agree with `aggregate.csv` to within $< 0.0005\text{ s}$.
- **Emergency Route Invariance:** In `exp_marathahalli_emergency_360`, 100% of the 180 matched pairs share identical MD5 route hashes between Priority ON and Priority OFF runs (`routes_identical = True`).

---

## 2. Marathahalli Site Matrix (`exp_marathahalli_site_720`): 720 Cells

### 2.1 Average Vehicle Waiting Time (seconds) Across All 12 Conditions

Means computed over 10 held-out random seeds (`121–130`):

| Demand Pattern | Demand Level | `fixed` (BTP Plan) | `fixed_webster` | `adaptive` (Queue) | `pressure` (Max-P) | `queue_extension` | `rl_dqn` (DQN) | Best Mean Leader |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| **`balanced`** | `low` | 15.28 s | 8.24 s | **7.38 s** | 7.55 s | 7.61 s | 8.15 s | `adaptive` (7.38 s) |
| **`balanced`** | `medium` | 41.92 s | 40.71 s | 40.27 s | **37.14 s** | 38.62 s | 38.80 s | `pressure` (37.14 s) |
| **`balanced`** | `heavy` | 109.63 s | 105.62 s | 107.50 s | 107.23 s | 106.27 s | **105.45 s** | `rl_dqn` (105.45 s) |
| **`imbalanced_orr`** | `low` | 17.26 s | 9.24 s | 9.32 s | 9.18 s | **8.99 s** | 9.29 s | `queue_extension` (8.99 s) |
| **`imbalanced_orr`** | `medium` | 47.60 s | 42.38 s | 42.30 s | 41.80 s | **41.19 s** | 42.83 s | `queue_extension` (41.19 s) |
| **`imbalanced_orr`** | `heavy` | 109.41 s | 104.57 s | 104.25 s | 106.63 s | 104.99 s | **103.96 s** | `rl_dqn` (103.96 s) |
| **`imbalanced_varthur`** | `low` | 18.18 s | 11.60 s | 11.27 s | 11.25 s | 11.13 s | **10.82 s** | `rl_dqn` (10.82 s) |
| **`imbalanced_varthur`** | `medium` | 71.32 s | 68.49 s | 66.83 s | **64.94 s** | 67.09 s | 67.39 s | `pressure` (64.94 s) |
| **`imbalanced_varthur`** | `heavy` | 132.20 s | 130.61 s | 129.66 s | 128.97 s | 128.49 s | **127.26 s** | `rl_dqn` (127.26 s) |
| **`surge_orr_north`** | `low` | 16.57 s | 8.64 s | 8.89 s | **8.46 s** | 9.07 s | 9.31 s | `pressure` (8.46 s) |
| **`surge_orr_north`** | `medium` | 43.20 s | 37.31 s | **37.29 s** | 37.75 s | 39.33 s | 39.51 s | `adaptive` (37.29 s) |
| **`surge_orr_north`** | `heavy` | 100.71 s | 97.11 s | 96.22 s | 98.27 s | 95.24 s | **95.13 s** | `rl_dqn` (95.13 s) |

---

### 2.2 Paired Bootstrap Resampling & Statistical Tie Analysis

To prevent declaring algorithmic superiority based on minor sample mean differences, we performed pairwise bootstrap resampling ($B = 10{,}000$, $\alpha = 0.05$) between the numerical leader and the secondary candidate for each condition.

| Scenario Pattern | Demand Level | Primary Leader | Primary Mean Wait | Secondary Candidate | Secondary Mean Wait | Paired Delta Mean ($\Delta$) | 95% Bootstrap CI | Statistical Classification |
|---|---|---|---:|---|---:|---:|:---:|:---:|
| `balanced` | `low` | `adaptive` | 7.38 s | `pressure` | 7.55 s | -0.18 s | `[-0.45, +0.12]` | **STATISTICAL TIE** |
| `balanced` | `medium` | `pressure` | 37.14 s | `queue_extension` | 38.62 s | -1.48 s | `[-3.17, +0.15]` | **STATISTICAL TIE** |
| `balanced` | `heavy` | `rl_dqn` | 105.45 s | `fixed_webster` | 105.62 s | -0.17 s | `[-2.61, +2.26]` | **STATISTICAL TIE** |
| `imbalanced_orr` | `low` | `queue_extension` | 8.99 s | `pressure` | 9.18 s | -0.19 s | `[-0.90, +0.41]` | **STATISTICAL TIE** |
| `imbalanced_orr` | `medium` | `queue_extension` | 41.19 s | `pressure` | 41.80 s | -0.61 s | `[-2.71, +1.49]` | **STATISTICAL TIE** |
| `imbalanced_orr` | `heavy` | `rl_dqn` | 103.96 s | `adaptive` | 104.25 s | -0.28 s | `[-2.68, +1.85]` | **STATISTICAL TIE** |
| `imbalanced_varthur` | `low` | `rl_dqn` | 10.82 s | `queue_extension` | 11.13 s | -0.31 s | `[-0.82, +0.18]` | **STATISTICAL TIE** |
| `imbalanced_varthur` | `medium` | `pressure` | 64.94 s | `adaptive` | 66.83 s | -1.89 s | `[-5.29, +2.23]` | **STATISTICAL TIE** |
| `imbalanced_varthur` | `heavy` | `rl_dqn` | 127.26 s | `queue_extension` | 128.49 s | -1.23 s | `[-4.71, +2.31]` | **STATISTICAL TIE** |
| `surge_orr_north` | `low` | `pressure` | 8.46 s | `fixed_webster` | 8.64 s | -0.18 s | `[-0.67, +0.29]` | **STATISTICAL TIE** |
| `surge_orr_north` | `medium` | `adaptive` | 37.29 s | `fixed_webster` | 37.31 s | -0.03 s | `[-2.25, +2.36]` | **STATISTICAL TIE** |
| `surge_orr_north` | `heavy` | `rl_dqn` | 95.13 s | `queue_extension` | 95.24 s | -0.12 s | `[-3.82, +4.02]` | **STATISTICAL TIE** |

> **Key Finding:** In **100% (12 out of 12)** of the evaluated experimental conditions, the 95% bootstrap confidence interval of the paired difference spans zero. While dynamic controllers and Webster fixed-time significantly outperform the rigid BTP baseline, no single dynamic policy statistically dominates across all scenarios.

---

### 2.3 Secondary Metrics Summary (Means over 10 Seeds)

#### Average Queue Length (metres)
| Pattern | Level | `fixed` | `fixed_webster` | `adaptive` | `pressure` | `queue_extension` | `rl_dqn` |
|---|---|---:|---:|---:|---:|---:|---:|
| `balanced` | `low` | 4.88 m | 2.50 m | 2.21 m | 2.29 m | 2.30 m | 2.50 m |
| `balanced` | `medium` | 18.23 m | 17.55 m | 17.38 m | 15.68 m | 16.48 m | 16.63 m |
| `balanced` | `heavy` | 69.34 m | 65.62 m | 67.29 m | 67.14 m | 66.27 m | 65.48 m |
| `surge_orr_north` | `low` | 5.38 m | 2.68 m | 2.76 m | 2.60 m | 2.82 m | 2.92 m |
| `surge_orr_north` | `medium` | 19.33 m | 15.89 m | 15.86 m | 16.14 m | 16.98 m | 17.15 m |
| `surge_orr_north` | `heavy` | 60.10 m | 57.06 m | 56.29 m | 57.85 m | 55.48 m | 55.39 m |

#### Total System Throughput (vehicles per hour)
Under all demand levels, vehicle completion rate was $100\%$ ($1.00$) across all policies, verifying that the simulation drain-time cap ($3600\text{ s}$) allowed all spawned trips to exit the network without unhandled dropouts.

---

## 3. Emergency Priority Study (`exp_marathahalli_emergency_360`): 360 Runs

### 3.1 Paired Emergency Preemption Performance (Means over 10 Seeds)

| Demand Pattern | Demand Level | Policy | Ambulance Trip (OFF) | Ambulance Trip (ON) | Emergency Trip Delta ($\Delta_{\text{em}}$) | Background Delay (OFF) | Background Delay (ON) | Background Delay Delta ($\Delta_{\text{bg}}$) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `balanced` | `low` | `fixed` | 163.0 s | 72.9 s | **-90.1 s (-55.3%)** | 15.2 s | 15.7 s | +0.45 s |
| `balanced` | `low` | `pressure` | 65.7 s | 64.5 s | **-1.2 s (-1.8%)** | 7.9 s | 7.8 s | -0.04 s |
| `balanced` | `low` | `rl_dqn` | 63.0 s | 59.2 s | **-3.8 s (-6.0%)** | 8.2 s | 8.8 s | +0.68 s |
| `balanced` | `medium` | `fixed` | 158.8 s | 77.3 s | **-81.5 s (-51.3%)** | 43.0 s | 41.3 s | -1.73 s |
| `balanced` | `medium` | `pressure` | 73.7 s | 64.8 s | **-8.9 s (-12.1%)** | 38.3 s | 39.1 s | +0.82 s |
| `balanced` | `medium` | `rl_dqn` | 77.1 s | 63.4 s | **-13.7 s (-17.8%)** | 38.4 s | 37.3 s | -1.13 s |
| `balanced` | `heavy` | `fixed` | 162.8 s | 95.5 s | **-67.3 s (-41.3%)** | 110.3 s | 107.9 s | -2.49 s |
| `balanced` | `heavy` | `pressure` | 94.3 s | 80.0 s | **-14.3 s (-15.2%)** | 108.0 s | 107.7 s | -0.26 s |
| `balanced` | `heavy` | `rl_dqn` | 92.7 s | 79.1 s | **-13.6 s (-14.7%)** | 106.1 s | 107.5 s | +1.42 s |
| `surge_orr_north` | `low` | `fixed` | 163.1 s | 77.0 s | **-86.1 s (-52.8%)** | 16.5 s | 15.7 s | -0.77 s |
| `surge_orr_north` | `low` | `pressure` | 60.3 s | 60.0 s | **-0.3 s (-0.5%)** | 8.6 s | 8.5 s | -0.08 s |
| `surge_orr_north` | `low` | `rl_dqn` | 68.0 s | 64.1 s | **-3.9 s (-5.7%)** | 9.2 s | 9.7 s | +0.45 s |
| `surge_orr_north` | `medium` | `fixed` | 173.6 s | 77.1 s | **-96.5 s (-55.6%)** | 42.3 s | 42.8 s | +0.57 s |
| `surge_orr_north` | `medium` | `pressure` | 73.6 s | 66.7 s | **-6.9 s (-9.4%)** | 38.1 s | 37.5 s | -0.60 s |
| `surge_orr_north` | `medium` | `rl_dqn` | 74.2 s | 68.8 s | **-5.4 s (-7.3%)** | 38.9 s | 38.9 s | -0.08 s |
| `surge_orr_north` | `heavy` | `fixed` | 179.4 s | 77.6 s | **-101.8 s (-56.7%)** | 99.7 s | 98.3 s | -1.35 s |
| `surge_orr_north` | `heavy` | `pressure` | 80.5 s | 77.6 s | **-2.9 s (-3.6%)** | 98.9 s | 96.1 s | -2.82 s |
| `surge_orr_north` | `heavy` | `rl_dqn` | 81.5 s | 69.8 s | **-11.7 s (-14.4%)** | 96.7 s | 95.5 s | -1.21 s |

### 3.2 Overall Policy Summary for Emergency Dispatch

| Controller | Mean Ambulance Trip Time (Priority OFF) | Mean Ambulance Trip Time (Priority ON) | Net Mean Travel Time Reduction | Mean Non-Emergency Background Delay Impact |
|---|---:|---:|---:|---:|
| `fixed` | 166.8 s | 79.6 s | **-87.2 s (-52.3%)** | -0.89 s |
| `pressure` | 74.7 s | 68.9 s | **-5.8 s (-7.8%)** | -0.50 s |
| `rl_dqn` | 76.1 s | 67.4 s | **-8.7 s (-11.4%)** | +0.02 s |

---

## 4. Discussion of Research Insights

1. **Why Fixed Time Fails in Low/Medium Regimes:**  
   The BTP fixed-time plan allocates 105 s to Varthur Road and 95 s to the ORR surface approaches (effective cycle: 210 s). In low demand, vehicles arrive infrequently; holding an approach red for 105 s forces arriving vehicles to sit at a vacant intersection, leading to average delays of ~15–18 s. Dynamic controllers recognize zero queues, trigger gap-out after 3 s, and clear queues with ~7–11 s delays.
2. **Why Webster Fixed Time Performs Well in Balanced Conditions:**  
   When traffic patterns match the assumed saturation and critical flow calculations, Webster's cycle optimization drops cycle times from 210 s to 40–60 s in low demand. This yields delays closely matching dynamic controllers, demonstrating that much of the fixed-time penalty stems from poor cycle calibration rather than dynamic control superiority.
3. **Capacity Ceiling at Heavy Demand:**  
   When vehicular inflow approaches lane saturation capacity ($\approx 1800\text{ vph/lane}$), all queues grow steadily, and controllers hit maximum green boundaries ($60\text{ s}$). Consequently, all controllers exhibit delays between 95 s and 132 s.
4. **Emergency Priority Preemption:**  
   Under fixed time, an approaching ambulance often arrives during red and must wait through long phases. EVSP detects the vehicle $100\text{ m}$ away, initiates yellow/all-red clearance, and gives immediate green, saving 87.2 s. Under dynamic controllers, average ambulance travel times are already low (60–75 s), but EVSP further secures an additional 5.8 s to 8.7 s saving without measurable background delay degradation.
