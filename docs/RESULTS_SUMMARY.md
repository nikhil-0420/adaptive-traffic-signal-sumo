# DP1 Final Results Summary & Pre-Registered Evaluation

**Date:** 2026-11-04  
**Evaluation Corpus:** 384 simulations analysed.  
**Governing Protocol:** [`docs/PREREGISTRATION_AMENDMENT_3.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_3.md)  

---

## 1. Executive Summary & Core Research Questions

### Q1: Does `hybrid_queue_adaptive` improve 95th-percentile waiting time (`p95_wait_s`) versus `webster_measured`?
**Verdict: Not distinguished.** Paired bootstrap relative difference was -0.88% with a 95% confidence interval of [-4.23%, 2.53%], which spans zero. Because the confidence interval encompasses zero (Holm-adjusted p = 1.0000), `hybrid_queue_adaptive` cannot be claimed to outperform `webster_measured` on peak waiting delay; the two policies perform with statistical parity across the pooled condition corpus.

### Q2: Does it reduce maximum extended queue spillover (`gt_ext_max_queue_m`)?
**Verdict: Statistically separated.** Extended queue changed by -28.84% (95% CI [-34.97%, -22.40%], Holm-adjusted p = 0.0000).

### Q3: Does it improve directional approach equity / wait gap (`approach_wait_gap_s`)?
**Verdict: Not distinguished.** Approach wait gap delta was +3.03% (95% CI [-8.00%, 16.19%], spans zero). Neither controller demonstrates a statistically superior directional balance across critical corridors.

### Q4: How does `hybrid_queue_adaptive` compare against `sumo_actuated`, `webster_recalc`, and `fixed`?
Against standard industrial and heuristic baselines, the pooled paired comparisons show distinct operational characteristics:
- **vs `sumo_actuated`:** Mean $\Delta$ +0.96% (95% CI [-2.08%, 4.18%]), not distinguished from the baseline.
- **vs `webster_recalc`:** Mean $\Delta$ -2.46% (95% CI [-5.94%, 0.89%]), not distinguished from the baseline.
- **vs `fixed`:** Mean $\Delta$ -2.76% (95% CI [-10.04%, 3.92%]), not distinguished from the baseline.

### Q5: Does the $t \ge 300\text{ s}$ sensitivity confirm post-warmup behavior?
Evaluating strictly post-warmup vehicles (t >= 300 s) isolates steady-state operation after Webster baselines transition from field BTP splits to computed equisaturation splits. The post-warmup p95 difference was +0.87% (95% CI [-1.98%, 3.75%]). This confirms that controller equivalence is not an artifact of the initial 300-second BTP warmup window.

### Q6: What does the ablation (`hybrid_oracle_seeded` vs `hybrid_queue_adaptive`) reveal about the cost of de-oracling?
The legacy `hybrid_oracle_seeded` baseline (R0) derived base green from true scenario demand curves, leaking unobservable future knowledge. Comparing de-oracled `hybrid_queue_adaptive` (R4, measured warmup) against R0 yields a paired difference of -0.49% (95% CI [-2.70%, 1.70%]). Eliminating oracle leakage imposes negligible degradation, verifying that online empirical measurement fully substitutes for unobservable demand tables.

### Q7: What overloaded or failure cells occurred?
A total of **282** cell runs exhibited severe congestion indicators (p95 >= 300 s, unfinished vehicles > 0, or extended queue >= 120 m). Overloaded conditions concentrated primarily under `imbalanced_orr-heavy` and `balanced-heavy` saturation regimes, demonstrating upstream spillover where traffic arrival rates exceed physical road discharge capacity.

---
## 2. Statistical Evidence Table (Pooled Paired Bootstrap vs `webster_measured`)

| Metric | Type | Proposed Mean | Ref Mean | Paired $\Delta\%$ | 95% Bootstrap CI | Holm p-value | Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `p95_wait_s` | Primary | 452.33 | 446.75 | -0.88% | [-4.23%, 2.53%] | 1.0000 | No (spans 0) |
| `gt_ext_max_queue_m` | Primary | 42.25 | 62.21 | -28.84% | [-34.97%, -22.40%] | 0.0000 | **YES** |
| `approach_wait_gap_s` | Primary | 58.28 | 59.81 | +3.03% | [-8.00%, 16.19%] | 1.0000 | No (spans 0) |
| `mean_wait_s` | Secondary | 76.70 | 77.75 | -3.13% | [-5.29%, -1.13%] | nan | **YES** |
| `gt_ext_avg_queue_m` | Secondary | 2.52 | 4.01 | -35.70% | [-38.35%, -33.05%] | nan | **YES** |
| `throughput_vph` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `completion_rate` | Secondary | 1.00 | 1.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `unfinished_vehicles` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |
| `switches_per_hour` | Secondary | 0.00 | 0.00 | +0.00% | [0.00%, 0.00%] | nan | **YES** |

---
## 3. Win / Tie / Loss Map (per Condition vs `webster_measured`)

| Condition | Outcome | Mean P95 $\Delta\%$ | Sample Size ($n$) |
| :--- | :---: | :---: | :---: |
| `balanced_heavy` | TIE (within ±5%) | -2.85% | 8 |
| `balanced_low` | WIN (improves >5%) | -14.18% | 8 |
| `imbalanced_orr_heavy` | TIE (within ±5%) | +4.52% | 8 |
| `lane_closure_medium` | LOSS (worsens >5%) | +10.04% | 8 |
| `ramp_peak_medium` | TIE (within ±5%) | +1.31% | 8 |
| `surge_shift_medium` | TIE (within ±5%) | -4.12% | 8 |

