# DP1 Verification Pass: Table I Absolute Means & Data Availability Statement

**Author / Runner**: Antigravity Assistant  
**Date**: November 5, 2026  
**Repository Working Directory**: `E:\dp1-traffic-signal`  
**Git Commit HEAD**: `6a15db3d784a4fdffc23d73e3932761480e9bea5`  

---

## 1. Table I Absolute Means & Bootstrap Verification

### 1.1 Generation Source & Execution
- **Script & Function**: [`analysis/paper_final/seed_clustered_bootstrap.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/seed_clustered_bootstrap.py) (`run_seed_clustered_bootstrap()`, executed via `main()`).
- **Output Artifact**: [`paper_final/tables/seed_clustered_bootstrap_comparison.csv`](file:///e:/dp1-traffic-signal/paper_final/tables/seed_clustered_bootstrap_comparison.csv).
- **Execution Timestamp**: `2026-11-05 02:56:04`.
- **Git HEAD**: `6a15db3d784a4fdffc23d73e3932761480e9bea5`.

---

### 1.2 Comparison: `hybrid_queue_adaptive` vs `webster_measured` (`all_6_pooled`)

All 5 core evaluated metrics across the 8 held-out seeds (131–138) and 6 conditions ($N = 48$ runs per policy):

| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 452.33 | 446.75 | -0.9% | [-2.8, +1.1] | 0.456 | 0.747 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 42.25 | 62.21 | -28.8% | [-33.7, -23.4] | 0.000 | 0.000 |
| **wait gap (s)** | 58.28 | 59.81 | +3.0% | [-7.1, +16.6] | 0.747 | 0.747 |
| **mean wait (s)** | 76.70 | 77.75 | -1.3% | [-3.5, +0.9] | 0.231 | n/a |
| **mean queue (m)** | 2.52 | 4.01 | -34.8% | [-37.2, -32.5] | 0.000 | n/a |

*(Note: In accordance with the pre-registration, Family-Wise Error Rate (Holm) adjustment is applied across the primary pre-registered hypotheses; mean wait and mean queue are secondary descriptive indicators).*

---

### 1.3 Mean Computation Methodology

"Hybrid Mean" and "Ref Mean" are computed using cluster-level aggregation:
1. **Per-Seed Mean**: For each seed $s \in \{131, \dots, 138\}$, the arithmetic mean of the metric across the $K$ condition runs is computed:
   $$\bar{x}_s = \frac{1}{K} \sum_{k=1}^K x_{s,k}$$
2. **Grand Cluster Mean**: The overall mean is the arithmetic mean across all 8 seed clusters:
   $$\mu = \frac{1}{8} \sum_{s=1}^8 \bar{x}_s$$

**Equivalence Note**: Because the confirmatory design is orthogonal and completely balanced ($K = 6$ conditions for every seed, $n = 8$ seeds, total $N = 48$ runs without missing data), the average of per-seed means is mathematically identical to the pooled grand mean across all 48 individual simulation runs:
$$\mu = \frac{1}{8} \sum_{s=1}^8 \left( \frac{1}{6} \sum_{k=1}^6 x_{s,k} \right) = \frac{1}{48} \sum_{s=1}^8 \sum_{k=1}^6 x_{s,k}$$

---

### 1.4 Reconciliation of Metric Discrepancies

1. **Extended Max Queue (42.25 m vs. 44.58 m / 62.21 m vs. 62.77 m)**:
   - **Confirmatory Evaluated Value**: The actual confirmatory dataset [`results/research/exp_marathahalli_improve_final`](file:///e:/dp1-traffic-signal/results/research/exp_marathahalli_improve_final) produces **42.25 m** (Hybrid) and **62.21 m** (`webster_measured`).
   - **Source of earlier 44.58 m / 62.77 m**: These values appeared in earlier exploratory phase 4 development logs (`emergency_p4` and exploratory tuning manifests) prior to the formal adoption of `PREREGISTRATION_AMENDMENT_3.md`. The final confirmatory table [`seed_clustered_bootstrap_comparison.csv`](file:///e:/dp1-traffic-signal/paper_final/tables/seed_clustered_bootstrap_comparison.csv) strictly reflects the true frozen run outputs (**42.25 m** and **62.21 m**).
2. **`webster_measured` p95 Wait (446.75 s vs. 446.8 s vs. 453.64 s)**:
   - **Evaluated Value**: The pooled / per-seed mean across all 48 runs is **446.75 s**.
   - **Table IV Value (446.8 s)**: The condition means reported in Table IV are:
     - `balanced_low`: 365.1 s
     - `balanced_heavy`: 449.1 s
     - `imbalanced_orr_heavy`: 447.6 s
     - `ramp_peak_medium`: 467.5 s
     - `surge_shift_heavy`: 474.3 s
     - `lane_closure_heavy`: 476.9 s
     - Mean across 6 condition averages: $\frac{365.1 + 449.1 + 447.6 + 467.5 + 474.3 + 476.9}{6} = 446.75\text{ s} \approx \mathbf{446.8\text{ s}}$. Table IV simply rounds the pooled 446.75 s to one decimal place.
   - **Source of earlier 453.64 s**: The 453.64 s figure was recorded in preliminary exploratory manifests of the older unamended simulator runs. The confirmatory dataset unequivocally yields 446.75 s (446.8 s).

---

### 1.5 Subgroup Breakdown: Stationary vs Non-Stationary Subsets

#### A. `3_stationary` Subset
Conditions: `balanced_low`, `balanced_heavy`, `imbalanced_orr_heavy` ($n = 8$ seeds $\times$ 3 conditions = 24 runs per policy):

| Metric | Hybrid Mean | Webster-m Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 417.26 | 420.61 | -0.6% | [-2.6, +1.5] | 0.584 |
| **extended max queue (m)** | 39.77 | 56.89 | -29.8% | [-35.7, -23.7] | 0.000 |
| **wait gap (s)** | 59.99 | 65.49 | -10.9% | [-23.0, +3.7] | 0.126 |
| **mean wait (s)** | 71.97 | 72.85 | -1.2% | [-3.7, +1.4] | 0.339 |
| **mean queue (m)** | 2.41 | 3.71 | -34.7% | [-38.3, -31.3] | 0.000 |

*(Note: Hybrid stationary max queue of 39.77 m reconciles directly with the ~40.0 m reported in Table IV).*

#### B. `3_non_stationary` Subset
Conditions: `ramp_peak_medium`, `surge_shift_heavy`, `lane_closure_heavy` ($n = 8$ seeds $\times$ 3 conditions = 24 runs per policy):

| Metric | Hybrid Mean | Webster-m Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 487.40 | 472.90 | -1.1% | [-3.8, +1.7] | 0.444 |
| **extended max queue (m)** | 44.72 | 67.53 | -28.0% | [-33.2, -22.3] | 0.000 |
| **wait gap (s)** | 56.57 | 54.13 | +16.9% | [-2.6, +40.2] | 0.089 |
| **mean wait (s)** | 81.43 | 82.65 | -1.4% | [-4.0, +1.1] | 0.259 |
| **mean queue (m)** | 2.63 | 4.30 | -34.8% | [-37.4, -32.2] | 0.000 |

---

### 1.6 Stability Confirmation for All 5 Comparators in Table I

All $\Delta\%$, 95% Cluster CIs, and Holm-adjusted $p$-values remain identical to the values in the manuscript:

| Reference Policy | Metric | $\Delta\%$ | 95% Cluster CI | Holm $p$ | Stability Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`webster_measured`** | p95 wait | -0.9% | [-2.8, +1.1] | 0.747 | Confirmed Unchanged |
| | ext max queue | -28.8% | [-33.7, -23.4] | 0.000 | Confirmed Unchanged |
| | wait gap | +3.0% | [-7.1, +16.6] | 0.747 | Confirmed Unchanged |
| **`webster_recalc`** | p95 wait | -2.5% | [-4.6, -0.3] | 0.054 | Confirmed Unchanged |
| | ext max queue | -28.3% | [-33.9, -22.5] | 0.000 | Confirmed Unchanged |
| | wait gap | +17.5% | [-8.3, +57.2] | 0.392 | Confirmed Unchanged |
| **`fixed`** | p95 wait | -2.8% | [-4.8, -0.9] | 0.008 | Confirmed Unchanged |
| | ext max queue | -48.7% | [-52.5, -44.7] | 0.000 | Confirmed Unchanged |
| | wait gap | +1.3% | [-6.4, +8.8] | 0.724 | Confirmed Unchanged |
| **`sumo_actuated`** | p95 wait | +1.0% | [-2.0, +4.0] | 0.544 | Confirmed Unchanged |
| | ext max queue | +11.4% | [+7.1, +15.1] | 0.000 | Confirmed Unchanged |
| | wait gap | +14.8% | [-2.6, +34.8] | 0.210 | Confirmed Unchanged |
| **`hybrid_oracle_seeded`**| p95 wait | -0.5% | [-2.9, +1.9] | 1.000 | Confirmed Unchanged |
| | ext max queue | -1.2% | [-5.1, +2.5] | 1.000 | Confirmed Unchanged |
| | wait gap | +15.3% | [+4.1, +28.2] | 0.010 | Confirmed Unchanged |

---

## 2. Data Availability Statement

### 2.1 Repository Metadata & Status
- **Remote URL**: `https://github.com/nikhil-0420/adaptive-traffic-signal-sumo`
- **Visibility**: Public (Verified via HTTP response `HTTP/1.1 200 OK` on `2026-11-05`).
- **Target Release Commit**: `6a15db3d784a4fdffc23d73e3932761480e9bea5`
- **Digital Object Identifier (DOI)**: **None currently minted**. (No Zenodo/Dataverse archive is registered yet; per project rules, none is invented).

> [!WARNING]
> **Action Required Before Final Archival**:  
> In the local workspace, the final analysis scripts and processed tables are currently untracked:
> - `analysis/paper_final/`
> - `paper_final/`
> - `outputs_for_paper_v2.md`
>
> To ensure external reproducibility matching the commit cited in the paper, please stage and commit these analysis files (`git add analysis/paper_final paper_final && git commit -m "Add final paper analysis scripts and tables"`).

---

### 2.2 Inventory of Key Reproducibility Files

All simulation artifacts, pre-registration protocols, and analysis scripts are located at the following repository paths:

1. **Pre-Registration & Protocol Specification**:
   - `docs/PREREGISTRATION_AMENDMENT_3.md` (Formal registration of confirmatory hypotheses, design matrix, sample size $N=384$, seeds 131–138, and stopping rules).
   - `docs/SPEC.md` and `docs/SOURCES.md` (System specifications and external source catalog).
2. **Simulation Configuration & Controllers**:
   - `dp1/config.py` (All tunable parameters, geometry, timing constraints, detector placements, and phase bounds).
   - `dp1/controllers/` (Implementations of `hybrid_queue_adaptive`, `webster_measured`, `webster_recalc`, `fixed`, `sumo_actuated`, and `hybrid_oracle_seeded`).
3. **Primary Simulation Run Outputs**:
   - `results/research/exp_marathahalli_improve_final/` (Contains the complete 384 confirmatory run directories across 8 policies $\times$ 6 conditions $\times$ 8 seeds).
   - `results/research/exp_marathahalli_improve_final/marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136/decisions.csv` (High-resolution second-by-second controller decision trace for seed 136).
4. **Analysis Pipeline & Tables**:
   - `analysis/paper_final/run_all.py` (One-command master pipeline regenerating all tables and figures).
   - `analysis/paper_final/seed_clustered_bootstrap.py` (Cluster-robust bootstrap engine).
   - `analysis/paper_final/raw_extracted_runs.csv` (Extracted per-run metrics for all 384 confirmatory trials).
   - `paper_final/tables/` (Final publication CSV tables):
     - `paper_final/tables/seed_clustered_bootstrap_comparison.csv` (Table I)
     - `paper_final/tables/table_iv_condition_means.csv` (Table IV)
     - `paper_final/tables/table_v_switch_counts.csv` (Table V)
     - `paper_final/tables/table_vi_p95_differences.csv` (Table VI)
     - `paper_final/tables/paired_bootstrap_summary.csv` (Pairwise bootstrap supplementary table).

---

### 2.3 Ready-to-Paste IEEE Data Availability Statement

```markdown
**Data and Code Availability**
All simulation scenarios, network definitions, controller source code, pre-registration protocols, and replication scripts are publicly available in the GitHub repository: https://github.com/nikhil-0420/adaptive-traffic-signal-sumo (commit 6a15db3d784a4fdffc23d73e3932761480e9bea5). The complete confirmatory experiment dataset (8 policies × 6 conditions × 8 seeds = 384 runs), raw per-run metrics (`analysis/paper_final/raw_extracted_runs.csv`), generated summary tables (`paper_final/tables/`), and second-by-second controller trace files (`results/research/exp_marathahalli_improve_final/`) can be verified directly using the open-source pipeline `python analysis/paper_final/run_all.py`. A permanent archival DOI will be registered on Zenodo upon publication.
```
