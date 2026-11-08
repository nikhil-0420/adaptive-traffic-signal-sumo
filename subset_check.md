# DP1 Paper Verification Pass: Subset Rows and Replication Audit

**Commit Hash**: `698808901c418a433734899e4b297c48600ef3d9`  
**Git Push Status**: Local commit only (not pushed to remote).  
**Parent Commit**: `6a15db3d784a4fdffc23d73e3932761480e9bea5`  
**Execution Environment**: Python virtual environment (`.venv\Scripts\python.exe`)  
**Data Source**: `analysis/paper_final/raw_extracted_runs.csv` (384 runs from `results/research/exp_marathahalli_improve_final`)  
**Output Table**: `paper_final/tables/seed_clustered_bootstrap_comparison.csv`  

---

## 1. Subset Rows from `seed_clustered_bootstrap_comparison.csv`

The table below reports all 5 evaluated metrics across both condition subsets (`3_non_stationary` and `3_stationary`, $n = 8$ seed clusters $\times$ 3 conditions = 24 pairs per comparison) for the four requested baseline comparisons.

### 1.1 `hybrid_queue_adaptive` vs `fixed`

#### Subset: `3_non_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 487.40 | 462.47 | **+5.1%** | **[+1.1, +8.7]** | 0.011 | **0.022** |
| **extended max queue ($Q_{\text{ext}}$, m)** | 44.72 | 89.28 | -48.3% | [-53.3, -42.3] | 0.000 | 0.000 |
| **wait gap (s)** | 56.57 | 54.41 | +3.3% | [-2.4, +8.5] | 0.256 | 0.256 |
| **mean wait (s)** | 81.43 | 85.24 | -4.9% | [-6.2, -3.6] | 0.000 | n/a (secondary) |
| **mean queue (m)** | 2.63 | 8.88 | -70.3% | [-71.2, -69.3] | 0.000 | n/a (secondary) |

#### Subset: `3_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 417.26 | 401.96 | **-10.6%** | **[-12.5, -8.3]** | 0.000 | **0.000** |
| **extended max queue ($Q_{\text{ext}}$, m)** | 39.77 | 83.44 | -49.1% | [-54.1, -44.0] | 0.000 | 0.000 |
| **wait gap (s)** | 59.99 | 65.09 | -0.7% | [-12.4, +11.9] | 0.890 | 0.890 |
| **mean wait (s)** | 71.97 | 77.83 | -18.4% | [-20.3, -16.6] | 0.000 | n/a (secondary) |
| **mean queue (m)** | 2.41 | 9.04 | -73.0% | [-73.9, -72.1] | 0.000 | n/a (secondary) |

---

### 1.2 `hybrid_queue_adaptive` vs `hybrid_oracle_seeded`

#### Subset: `3_non_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 487.40 | 489.28 | -0.3% | [-3.4, +2.8] | 0.852 | 1.000 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 44.72 | 46.60 | -3.3% | [-7.6, +1.8] | 0.198 | 0.593 |
| **wait gap (s)** | 56.57 | 55.80 | **+0.2%** | **[-8.1, +6.9]** | 0.905 | **1.000** |
| **mean wait (s)** | 81.43 | 81.56 | -0.3% | [-2.4, +1.8] | 0.750 | n/a (secondary) |
| **mean queue (m)** | 2.63 | 2.69 | -0.3% | [-5.1, +3.4] | 0.940 | n/a (secondary) |

#### Subset: `3_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 417.26 | 422.45 | -0.7% | [-5.5, +2.6] | 0.796 | 1.000 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 39.77 | 40.21 | +0.8% | [-4.5, +6.4] | 0.784 | 1.000 |
| **wait gap (s)** | 59.99 | 60.86 | **+30.4%** | **[+6.5, +56.7]** | 0.009 | **0.027** |
| **mean wait (s)** | 71.97 | 71.26 | +1.3% | [-1.5, +3.8] | 0.342 | n/a (secondary) |
| **mean queue (m)** | 2.41 | 2.41 | -0.4% | [-2.8, +1.7] | 0.789 | n/a (secondary) |

---

### 1.3 `hybrid_queue_adaptive` vs `sumo_actuated`

#### Subset: `3_non_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 487.40 | 495.68 | -1.6% | [-5.8, +1.7] | 0.423 | 0.846 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 44.72 | 41.59 | +7.5% | [+2.9, +12.7] | 0.000 | 0.000 |
| **wait gap (s)** | 56.57 | 58.50 | -3.8% | [-13.4, +7.8] | 0.466 | 0.846 |
| **mean wait (s)** | 81.43 | 82.10 | -0.7% | [-2.5, +1.0] | 0.429 | n/a (secondary) |
| **mean queue (m)** | 2.63 | 2.02 | +33.4% | [+28.0, +39.9] | 0.000 | n/a (secondary) |

#### Subset: `3_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 417.26 | 408.62 | +3.5% | [-0.2, +7.4] | 0.066 | 0.068 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 39.77 | 34.82 | +15.3% | [+9.2, +21.1] | 0.000 | 0.000 |
| **wait gap (s)** | 59.99 | 60.38 | +33.4% | [+1.9, +72.9] | 0.034 | 0.068 |
| **mean wait (s)** | 71.97 | 69.28 | +7.6% | [+3.0, +11.9] | 0.001 | n/a (secondary) |
| **mean queue (m)** | 2.41 | 1.75 | +37.7% | [+33.0, +42.5] | 0.000 | n/a (secondary) |

---

### 1.4 `hybrid_queue_adaptive` vs `webster_recalc`

#### Subset: `3_non_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 487.40 | 487.42 | -0.1% | [-3.8, +3.2] | 0.951 | 0.951 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 44.72 | 64.80 | -26.1% | [-33.1, -19.1] | 0.000 | 0.000 |
| **wait gap (s)** | 56.57 | 54.64 | +34.4% | [-7.7, +108.6] | 0.413 | 0.827 |
| **mean wait (s)** | 81.43 | 82.80 | -1.8% | [-3.8, +0.4] | 0.105 | n/a (secondary) |
| **mean queue (m)** | 2.63 | 3.88 | -31.1% | [-33.2, -28.5] | 0.000 | n/a (secondary) |

#### Subset: `3_stationary`
| Metric | Hybrid Mean | Ref Mean | $\Delta\%$ | 95% Cluster CI | Raw $p$ | Holm $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **p95 wait (s)** | 417.26 | 420.50 | -4.8% | [-7.7, -1.7] | 0.002 | 0.004 |
| **extended max queue ($Q_{\text{ext}}$, m)** | 39.77 | 61.58 | -30.5% | [-37.8, -22.3] | 0.000 | 0.000 |
| **wait gap (s)** | 59.99 | 65.80 | +0.7% | [-14.6, +16.5] | 0.942 | 0.942 |
| **mean wait (s)** | 71.97 | 72.51 | -4.4% | [-7.6, -1.1] | 0.008 | n/a (secondary) |
| **mean queue (m)** | 2.41 | 3.75 | -35.3% | [-37.2, -33.2] | 0.000 | n/a (secondary) |

---

## 2. Comparison Against Target Values and Discrepancy Flags

| Comparison & Metric | Extracted Value | Target Benchmark | Diff Flag | Status |
| :--- | :---: | :---: | :---: | :---: |
| **vs fixed, non-stationary p95** | `+5.1% [+1.1, +8.7]`, Holm 0.022 | `+5.1% [+1.1, +8.7]`, Holm 0.022 | **None** | **EXACT MATCH** |
| **vs fixed, stationary p95** | `-10.6% [-12.5, -8.3]`, Holm 0.000 | `−10.6% [−12.5, −8.3]`, Holm < 0.001 | **None** | **EXACT MATCH** |
| **vs oracle, stationary wait gap** | `+30.4% [+6.5, +56.7]`, Holm 0.027 | `+30.4% [+6.5, +56.7]`, Holm 0.027 | **None** | **EXACT MATCH** |
| **vs oracle, non-stationary wait gap** | `+0.2% [-8.1, +6.9]`, Holm 1.000 | `+0.2% [−8.1, +6.9]` | **None** | **EXACT MATCH** |

**Conclusion**: All target subset cells match the earlier outputs exactly. No shifts occurred in $\Delta\%$, confidence intervals, or Holm-adjusted $p$-values.

---

## 3. Explanation of Pipeline Behavior: Why Stationary `webster_measured` p95 Appeared as `-0.6%`

In the previous turn's narrative summary, `hybrid vs webster_measured` stationary p95 wait was listed as `−0.6% [−2.6, +1.5]`, whereas `outputs_for_paper.md` reported `−4.2% [−7.8, −0.6]` ($p = 0.036$).

### Root Cause
This divergence was caused by a mathematical difference in aggregation formula between an ad-hoc calculation and the formal bootstrap pipeline:
1. **Ratio of Means (Ad-Hoc)**:
   The ad-hoc script computed the percentage change between the aggregated group means:
   $$\Delta\%_{\text{ratio}} = \frac{\bar{X}_{\text{hyb}} - \bar{X}_{\text{ref}}}{\bar{X}_{\text{ref}}} \times 100\% = \frac{417.26 - 420.61}{420.61} \times 100\% = -0.79\%$$
   (or when averaging per-seed ratios $\frac{\bar{x}_{\text{hyb}, s} - \bar{x}_{\text{ref}, s}}{\bar{x}_{\text{ref}, s}}$, $-0.62\%$).
2. **Mean of Paired Percentage Differences (Formal Pipeline)**:
   The pre-registered analysis pipeline in `extract_paper_outputs.py` and `seed_clustered_bootstrap.py` evaluates paired differences on each simulation run $(s, k)$:
   $$d_{s,k} = \frac{x_{\text{hyb}, s, k} - x_{\text{ref}, s, k}}{x_{\text{ref}, s, k}} \times 100\%$$
   Within each seed cluster $s$, condition differences are averaged: $\bar{d}_s = \frac{1}{K}\sum_{k=1}^K d_{s,k}$.
   The cluster sample estimate is $\bar{D} = \frac{1}{n}\sum_{s=1}^n \bar{d}_s$.
   Across the stationary conditions (`balanced-low`, `balanced-heavy`, `imbalanced_orr-heavy`), the relative benefit in lighter scenarios carries equal weight to heavy scenarios, yielding:
   $$\bar{D} = \mathbf{-4.17\% \approx -4.2\%}, \quad 95\% \text{ CI: } [-7.8\%, -0.6\%], \quad \text{Holm } p = 0.036$$

### Impact on Other Comparisons
**Zero impact.** The four comparisons above were computed directly through the paired percentage difference bootstrap pipeline in `extract_paper_outputs.py`. Because their formula was identical from the outset, every cell matches the benchmark.

---

## 4. Condition String Verification & Typo Audit

### Exact Strings in Code
In [`analysis/paper_final/seed_clustered_bootstrap.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/seed_clustered_bootstrap.py#L32-L36) and [`analysis/paper_final/extract_paper_outputs.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/extract_paper_outputs.py#L65-L70):
```python
SUBSETS = {
    "all_6_pooled": None,
    "3_non_stationary": ["ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"],
    "3_stationary": ["balanced-low", "balanced-heavy", "imbalanced_orr-heavy"],
}
```

### Dataset Check
In [`analysis/paper_final/raw_extracted_runs.csv`](file:///e:/dp1-traffic-signal/analysis/paper_final/raw_extracted_runs.csv):
```text
condition              count
balanced-heavy          64
balanced-low            64
imbalanced_orr-heavy    64
lane_closure-medium     64
ramp_peak-medium        64
surge_shift-medium      64
```
Total runs = $64 \times 6 = 384$.

### Typo Confirmation
The appearance of `surge_shift_heavy` and `lane_closure_heavy` in the previous markdown summary was **strictly a typographical error in the prose text**. No such conditions exist in the simulation database, and the evaluation scripts have only ever executed against `surge_shift-medium` and `lane_closure-medium`.

---

## 5. Verification of Pooled `all_6_pooled` Rows Across All 5 Comparators

All pooled rows were regenerated via `run_all.py` on commit `6988089`. All point estimates, 95% cluster CIs, and Holm $p$-values remain completely stable:

| Comparator | Metric | Extracted Value | Target Checklist | Status |
| :--- | :--- | :---: | :---: | :---: |
| **`webster_measured`** | p95 wait | -0.9% [-2.8, +1.1] | -0.9% [-2.8, +1.1] | **Unchanged** |
| | max queue | -28.8% [-33.7, -23.4] | -28.8% [-33.7, -23.4] | **Unchanged** |
| | wait gap | +3.0% [-7.1, +16.6] | +3.0% [-7.1, +16.6] | **Unchanged** |
| **`webster_recalc`** | p95 wait | -2.5% [-4.6, -0.3] | -2.5% [-4.6, -0.3] | **Unchanged** |
| | max queue | -28.3% [-33.9, -22.5] | -28.3% [-33.9, -22.5] | **Unchanged** |
| | wait gap | +17.5% [-8.3, +57.2] | +17.5% [-8.3, +57.2] | **Unchanged** |
| **`fixed`** | p95 wait | -2.8% [-4.8, -0.9] | -2.8% [-4.8, -0.9] | **Unchanged** |
| | max queue | -48.7% [-52.5, -44.7] | -48.7% [-52.5, -44.7] | **Unchanged** |
| | wait gap | +1.3% [-6.4, +8.8] | +1.3% [-6.4, +8.8] | **Unchanged** |
| **`sumo_actuated`** | p95 wait | +1.0% [-2.0, +4.0] | +1.0% [-2.0, +4.0] | **Unchanged** |
| | max queue | +11.4% [+7.1, +15.1] | +11.4% [+7.1, +15.1] | **Unchanged** |
| | wait gap | +14.8% [-2.6, +34.8] | +14.8% [-2.6, +34.8] | **Unchanged** |
| **`hybrid_oracle_seeded`** | p95 wait | -0.5% [-2.9, +1.9] | -0.5% [-2.9, +1.9] | **Unchanged** |
| | max queue | -1.2% [-5.1, +2.5] | -1.2% [-5.1, +2.5] | **Unchanged** |
| | wait gap | +15.3% [+4.1, +28.2], Holm 0.010 | +15.3% [+4.1, +28.2], Holm 0.010 | **Unchanged** |

---

## 6. Regeneration of `sumo_actuated` Mean Wait and Mean Queue Rows

Across all 48 pooled runs ($N = 48$ pairs, seeds 131–138):
- **Mean Wait (`mean_wait_s`)**:
  - Hybrid Mean = 76.70 s, `sumo_actuated` Mean = 75.69 s
  - **$\Delta\%$**: **+3.4%**
  - **95% Cluster CI**: **[+0.8%, +5.9%]** ($p = 0.010$)
  - **95% Pair-Level CI**: **[+0.6%, +6.4%]** (in `table2_comparators.csv`: `+3.4% (+0.5, +6.5)`)
- **Mean Queue (`gt_ext_avg_queue_m`)**:
  - Hybrid Mean = 2.52 m, `sumo_actuated` Mean = 1.89 m
  - **$\Delta\%$**: **+35.5%**
  - **95% Cluster CI**: **[+31.4%, +39.5%]** ($p = 0.000$)
  - **95% Pair-Level CI**: **[+30.9%, +39.9%]** (in `table2_comparators.csv`: `+35.5% (+30.9, +39.9)`)

### Note on Paper Citation (`+3.4% [+1.3, +5.7]` and `+35.5% [+27.6, +43.7]`)
The intervals `[+1.3, +5.7]` and `[+27.6, +43.7]` were generated during the exploratory Phase 9 baseline study (commit `cda9433`). In the confirmatory study `exp_marathahalli_improve_final` (frozen seeds 131–138 under Amendment 3):
- Point estimates are **identical**: **+3.4%** and **+35.5%**.
- Confirmatory Pair-Level CIs are: **[+0.6%, +6.4%]** and **[+30.9%, +39.9%]**.
- Confirmatory Seed-Clustered CIs are: **[+0.8%, +5.9%]** and **[+31.4%, +39.5%]**.

---

## 7. Git Commit Audit

- **New Commit Hash**: `698808901c418a433734899e4b297c48600ef3d9`
- **Branch**: `dp1-improve`
- **Commit Message**: `Add paper analysis outputs and verification ledgers`
- **Committed Files** (29 files, 4,808 insertions):
  - `analysis/paper_final/` (`compute_tables.py`, `extract_metrics.py`, `extract_paper_outputs.py`, `generate_figures.py`, `generate_outputs_v2.py`, `patch_paper.py`, `raw_extracted_runs.csv`, `run_all.py`, `seed_clustered_bootstrap.py`)
  - `paper_final/` (Tables, figures, DOCX manuscript variants, `FIXES.md`, reports)
  - `outputs_for_paper.md`
  - `outputs_for_paper_v2.md`
  - `reference_check.md`
- **Untracked / Preserved**:
  - `qa/qa_harness_summary.json` was left uncommitted per instructions.
  - No remote push was executed.
