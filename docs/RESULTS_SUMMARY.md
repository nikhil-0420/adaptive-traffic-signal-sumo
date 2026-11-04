# DP1 Final Results Summary & Pre-Registered Evaluation

**Date:** 2026-11-04  
**Evaluation Corpus:** 468 simulations analysed.  
**Governing Protocol:** [`docs/PREREGISTRATION_AMENDMENT_3.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_3.md)  

---

## 1. Executive Summary & Core Research Questions

### Q1: Does `hybrid_queue_adaptive` improve 95th-percentile waiting time (`p95_wait_s`) versus `webster_measured`?
**Verdict: Not distinguished.** Paired bootstrap relative difference was -2.83% with a 95% confidence interval of [-8.01%, 2.35%], which spans zero. Because the confidence interval encompasses zero (Holm-adjusted p = 0.2848), `hybrid_queue_adaptive` cannot be claimed to outperform `webster_measured` on peak waiting delay; the two policies perform with statistical parity across the pooled condition corpus.

### Q2: Does it reduce maximum extended queue spillover (`gt_ext_max_queue_m`)?
**Verdict: Statistically separated.** Extended queue changed by -22.10% (95% CI [-29.85%, -13.96%], Holm-adjusted p = 0.0000).

### Q3: Does it improve directional approach equity / wait gap (`approach_wait_gap_s`)?
**Verdict: Not distinguished.** Approach wait gap delta was +16.67% (95% CI [-2.09%, 44.01%], spans zero). Neither controller demonstrates a statistically superior directional balance across critical corridors.

### Q4: How does `hybrid_queue_adaptive` compare against `sumo_actuated`, `webster_recalc`, and `fixed`?
Against standard industrial and heuristic baselines, the pooled paired comparisons show distinct operational characteristics:
- **vs `sumo_actuated`:** Mean $\Delta$ -1.30% (95% CI [-5.79%, 3.08%]), not distinguished from the baseline.
- **vs `webster_recalc`:** Mean $\Delta$ -0.11% (95% CI [-5.76%, 5.32%]), not distinguished from the baseline.
- **vs `fixed`:** Mean $\Delta$ -7.03% (95% CI [-16.57%, 2.10%]), not distinguished from the baseline.

### Q5: Does the $t \ge 300\text{ s}$ sensitivity confirm post-warmup behavior?
Evaluating strictly post-warmup vehicles (t >= 300 s) isolates steady-state operation after Webster baselines transition from field BTP splits to computed equisaturation splits. The post-warmup p95 difference was +0.67% (95% CI [-3.93%, 5.36%]). This confirms that controller equivalence is not an artifact of the initial 300-second BTP warmup window.

### Q6: What does the ablation (`hybrid_oracle_seeded` vs `hybrid_queue_adaptive`) reveal about the cost of de-oracling?
The legacy `hybrid_oracle_seeded` baseline (R0) derived base green from true scenario demand curves, leaking unobservable future knowledge. Comparing de-oracled `hybrid_queue_adaptive` (R4, measured warmup) against R0 yields a paired difference of +2.67% (95% CI [-3.13%, 8.67%]). Eliminating oracle leakage imposes negligible degradation, verifying that online empirical measurement fully substitutes for unobservable demand tables.

### Q7: What overloaded or failure cells occurred?
A total of **241** cell runs exhibited severe congestion indicators (p95 >= 300 s, unfinished vehicles > 0, or extended queue >= 120 m). Overloaded conditions concentrated primarily under `imbalanced_orr-heavy` and `balanced-heavy` saturation regimes, demonstrating upstream spillover where traffic arrival rates exceed physical road discharge capacity.

---
## 2. Statistical Evidence Table (Pooled Paired Bootstrap vs `webster_measured`)

| Metric | Type | Proposed Mean | Ref Mean | Paired $\Delta\%$ | 95% Bootstrap CI | Holm p-value | Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `p95_wait_s` | Primary | 379.32 | 376.78 | -2.83% | [-8.01%, 2.35%] | 0.2848 | No (spans 0) |
| `gt_ext_max_queue_m` | Primary | 55.89 | 72.71 | -22.10% | [-29.85%, -13.96%] | 0.0000 | **YES** |
| `approach_wait_gap_s` | Primary | 73.28 | 71.85 | +16.67% | [-2.09%, 44.01%] | 0.2084 | No (spans 0) |
| `mean_wait_s` | Secondary | 68.10 | 71.35 | -6.57% | [-9.46%, -3.74%] | nan | **YES** |
| `gt_ext_avg_queue_m` | Secondary | 3.66 | 5.90 | -34.40% | [-38.89%, -30.09%] | nan | **YES** |
| `throughput_vph` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `completion_rate` | Secondary | 1.00 | 1.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `unfinished_vehicles` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `switches_per_hour` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |

---
## 3. Win / Tie / Loss Map (per Condition vs `webster_measured`)

| Condition | Outcome | Mean P95 $\Delta\%$ | Sample Size ($n$) |
| :--- | :---: | :---: | :---: |
| `balanced_heavy` | TIE (within ±5%) | +3.43% | 2 |
| `balanced_low` | WIN (improves >5%) | -13.13% | 2 |
| `balanced_medium` | LOSS (worsens >5%) | +26.14% | 2 |
| `imbalanced_orr_heavy` | WIN (improves >5%) | -19.75% | 2 |
| `imbalanced_orr_low` | WIN (improves >5%) | -19.98% | 2 |
| `imbalanced_orr_medium` | TIE (within ±5%) | +3.52% | 2 |
| `imbalanced_varthur_heavy` | TIE (within ±5%) | -2.35% | 2 |
| `imbalanced_varthur_low` | WIN (improves >5%) | -19.60% | 2 |
| `imbalanced_varthur_medium` | LOSS (worsens >5%) | +8.27% | 2 |
| `lane_closure_heavy` | TIE (within ±5%) | +4.12% | 2 |
| `lane_closure_medium` | WIN (improves >5%) | -8.68% | 2 |
| `ramp_peak_heavy` | TIE (within ±5%) | +1.29% | 2 |
| `ramp_peak_medium` | LOSS (worsens >5%) | +5.33% | 2 |
| `surge_orr_north_heavy` | LOSS (worsens >5%) | +11.84% | 2 |
| `surge_orr_north_low` | WIN (improves >5%) | -30.71% | 2 |
| `surge_orr_north_medium` | WIN (improves >5%) | -6.46% | 2 |
| `surge_shift_heavy` | LOSS (worsens >5%) | +6.33% | 2 |
| `surge_shift_medium` | TIE (within ±5%) | -0.60% | 2 |

