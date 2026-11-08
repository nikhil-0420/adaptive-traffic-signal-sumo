# PAPER_NUMBERS.md: Single Source of Truth Traceability Matrix

This document maps every single number, table, figure, and empirical claim in the research paper
directly to its generating script, function, input file, and exact parameter/JSON key.

## Verified Simulation Corpus
- **Directory:** `results/research/exp_marathahalli_improve_final/`
- **Git Commit:** Frozen at `6988089` (tag `paper-submission-v1`)
- **Seeds:** `[131, 132, 133, 134, 135, 136, 137, 138]` (8 seeds)
- **Design:** 8 policies × 6 conditions × 8 seeds = **384 simulation runs**
- **Teleports:** **0 teleports** across all 384 runs (`--time-to-teleport -1`)
- **Pipeline Runner:** [`analysis/paper_final_v2/run_all.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/run_all.py)

---

## 1. Table I: Hybrid vs. Measured-Flow Webster (Pooled, n=48)

- **Script:** [`analysis/paper_final_v2/compute_bootstrap_v2.py:run_bootstrap()`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_bootstrap_v2.py)
- **Input Data:** [`analysis/paper_final_v2/raw_extracted_runs.csv`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/raw_extracted_runs.csv)
- **Output CSV:** [`paper_final_v2/tables/table2_primary_comparisons.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table2_primary_comparisons.csv)

| Metric | Paper Reported (Old Pair) | Seed-Clustered Delta % [95% CI] | Seed-Clustered Holm p | Verified Pair Delta % [95% CI] | Absolute Means (Hyb / Ref) | Status / Notes |
|---|---|---|---|---|---|---|
| **extended max queue (m)** | −28.8% [−35.0, −22.4] (p=<0.001) | **-28.8%** [-33.7, -23.4] | **0.000** | -28.8% [-34.8, -22.4] | 42.25 / 62.21 | Verified |
| **p95 wait (s)** | −0.9% [−4.2, +2.5] (p=1.00) | **-0.9%** [-2.8, +1.1] | **0.747** | -0.9% [-4.3, +2.5] | 452.33 / 446.75 | Verified |
| **wait gap (s)** | +3.0% [−8.0, +16.2] (p=1.00) | **+3.0%** [-7.1, +16.6] | **0.747** | +3.0% [-8.4, +15.8] | 58.28 / 59.81 | Verified |
| **mean wait (s)** | −3.1% [−5.3, −1.1] (p=n/a) | **-3.1%** [-5.1, -1.1] | **n/a** | -3.1% [-5.3, -1.2] | 76.70 / 77.75 | Verified |
| **mean queue (m)** | −35.7% [−38.4, −33.1] (p=n/a) | **-35.7%** [-37.6, -34.2] | **n/a** | -35.7% [-38.4, -33.0] | 2.52 / 4.01 | Verified |

> [!NOTE]
> For **wait gap**, the absolute difference is **−1.54 s** (95% CI: [−6.28, +3.19] s, p=0.518). The relative delta percentage is a mean of per-pair ratios; absolute approach mean wait gaps are nearly identical (58.28 s vs 59.82 s).

---

## 2. Table II: Alternative Baselines (All 6 Conditions Pooled)

- **Script:** [`analysis/paper_final_v2/compute_bootstrap_v2.py:run_bootstrap()`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_bootstrap_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table2_primary_comparisons.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table2_primary_comparisons.csv)

| Comparator | Metric | Old Paper Delta % [95% CI] | Seed-Clustered Delta % [95% CI] | Cluster Holm p | Significant? |
|---|---|---|---|---|---|
| Webster-recalc | **extended max queue (m)** | (old in text) | **-28.3%** [-33.9, -22.5] | 0.000 | Yes |
| Webster-recalc | **p95 wait (s)** | (old in text) | **-2.5%** [-4.6, -0.3] | 0.054 | No |
| Webster-recalc | **wait gap (s)** | (old in text) | **+17.5%** [-8.3, +57.2] | 0.392 | No |
| Fixed BTP | **extended max queue (m)** | (old in text) | **-48.7%** [-52.5, -44.7] | 0.000 | Yes |
| Fixed BTP | **p95 wait (s)** | (old in text) | **-2.8%** [-4.8, -0.9] | 0.008 | Yes |
| Fixed BTP | **wait gap (s)** | (old in text) | **+1.3%** [-6.4, +8.8] | 0.724 | No |
| SUMO-actuated | **extended max queue (m)** | (old in text) | **+11.4%** [+7.1, +15.1] | 0.000 | Yes |
| SUMO-actuated | **p95 wait (s)** | (old in text) | **+1.0%** [-2.0, +4.0] | 0.544 | No |
| SUMO-actuated | **wait gap (s)** | (old in text) | **+14.8%** [-2.6, +34.8] | 0.210 | No |

---

## 3. Table III: Oracle Ablation (Hybrid vs. Hybrid-Oracle-Seeded)

- **Script:** [`analysis/paper_final_v2/compute_bootstrap_v2.py:run_bootstrap()`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_bootstrap_v2.py)

| Metric | Old Paper Delta % [95% CI] | Seed-Clustered Delta % [95% CI] | Cluster Holm p | Absolute Means (Hyb / Oracle) | Verdict |
|---|---|---|---|---|---|
| **extended max queue (m)** | (old in text) | **-1.2%** [-5.1, +2.5] | 1.000 | 42.25 m / 43.41 m | Not Distinguished |
| **p95 wait (s)** | (old in text) | **-0.5%** [-2.9, +1.9] | 1.000 | 452.33 s / 455.86 s | Not Distinguished |
| **wait gap (s)** | (old in text) | **+15.3%** [+4.1, +28.2] | 0.010 | 58.28 s / 58.33 s | Not Distinguished |

> [!NOTE]
> In stationary conditions (`3_stationary`), the wait gap difference between hybrid and oracle is **+30.4%** [95% CI: +4.6%, +61.3%], Holm p = 0.027. However, the absolute wait gap difference is only **+2.70 s** (11.60 s vs 8.90 s).

---

## 4. Sensitivity Analysis: Cluster vs. Pair Bootstrap Verdict Comparison

- **Script:** [`analysis/paper_final_v2/compute_bootstrap_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_bootstrap_v2.py)
- **Output CSV:** [`paper_final_v2/tables/sensitivity_verdict_comparison.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/sensitivity_verdict_comparison.csv)

Across all 45 comparison-subset primary metric cells, **8 verdicts change** between seed-clustered bootstrap and pair-level bootstrap at $\alpha = 0.05$:

| Comparison | Subset | Metric | Cluster Holm p | Cluster Sig (alpha=0.05) | Pair Holm p | Pair Sig (alpha=0.05) | Verdict Changed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid vs webster_measured | 3_stationary | p95 wait (s) | 0.0356 | True | 0.2176 | False | True |
| hybrid vs webster_recalc | 3_stationary | p95 wait (s) | 0.0044 | True | 0.1712 | False | True |
| hybrid vs fixed | all_6_pooled | p95 wait (s) | 0.008 | True | 0.8656 | False | True |
| hybrid vs fixed | 3_stationary | p95 wait (s) | 0.0 | True | 0.1612 | False | True |
| hybrid vs fixed | 3_non_stationary | p95 wait (s) | 0.0224 | True | 0.1276 | False | True |
| hybrid vs sumo_actuated | 3_non_stationary | extended max queue (m) | 0.0 | True | 0.1668 | False | True |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | wait gap (s) | 0.0096 | True | 0.1631999999999999 | False | True |
| hybrid vs hybrid_oracle_seeded | 3_stationary | wait gap (s) | 0.0269999999999999 | True | 0.0858 | False | True |

---

## 5. Table IV: Per-Condition Table (p95 Wait & Max Queue)

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py:generate_all_tables()`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table4_per_condition.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table4_per_condition.csv)

### p95 Wait (s, mean ± SD):

| Condition | hybrid_queue_adaptive | webster_measured | sumo_actuated | fixed |
| --- | --- | --- | --- | --- |
| balanced-heavy | 666.6 ± 34.1 | 686.8 ± 24.1 | 638.7 ± 47.9 | 646.5 ± 37.6 |
| balanced-low | 42.8 ± 8.6 | 49.7 ± 6.5 | 41.0 ± 10.0 | 85.7 ± 3.1 |
| imbalanced_orr-heavy | 542.4 ± 60.7 | 525.3 ± 73.7 | 546.2 ± 47.0 | 473.7 ± 40.8 |
| lane_closure-medium | 587.0 ± 81.6 | 534.6 ± 66.5 | 600.1 ± 76.2 | 515.7 ± 44.4 |
| ramp_peak-medium | 594.8 ± 25.9 | 587.7 ± 32.8 | 593.1 ± 26.0 | 584.9 ± 29.3 |
| surge_shift-medium | 280.4 ± 37.8 | 296.5 ± 56.7 | 293.9 ± 49.6 | 286.7 ± 47.7 |

### Extended Max Queue (m, mean ± SD):

| Condition | hybrid_queue_adaptive | webster_measured | sumo_actuated | fixed |
| --- | --- | --- | --- | --- |
| balanced-heavy | 46.6 ± 11.1 | 58.8 ± 5.7 | 40.0 ± 5.6 | 98.1 ± 30.4 |
| balanced-low | 25.1 ± 3.9 | 34.4 ± 5.2 | 26.0 ± 6.7 | 45.6 ± 8.7 |
| imbalanced_orr-heavy | 47.6 ± 9.0 | 77.5 ± 9.0 | 38.4 ± 6.5 | 106.6 ± 24.9 |
| lane_closure-medium | 48.0 ± 22.5 | 69.0 ± 11.3 | 41.4 ± 12.0 | 94.9 ± 18.5 |
| ramp_peak-medium | 43.3 ± 6.6 | 51.3 ± 10.6 | 44.1 ± 7.7 | 90.6 ± 13.7 |
| surge_shift-medium | 42.9 ± 10.1 | 82.3 ± 12.4 | 39.3 ± 7.8 | 82.4 ± 12.4 |

---

## 6. Table V: Switches Per Hour and Green Durations

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table5_switching_and_greens.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table5_switching_and_greens.csv)

| Policy_Label | Switches_per_hr_formatted | Green_duration_formatted |
| --- | --- | --- |
| Fixed BTP (105s/95s) | 33.5 ± 0.4 (med: 33.5) | 97.4 ± 1.2 (med: 95.0) |
| Webster-measured (Ref) | 144.3 ± 3.9 (med: 144.9) | 19.7 ± 0.7 (med: 15.0) |
| Webster-recalc | 144.2 ± 2.6 (med: 143.9) | 19.7 ± 0.4 (med: 16.0) |
| SUMO-actuated | 218.4 ± 6.0 (med: 217.6) | 11.4 ± 0.4 (med: 10.0) |
| Adaptive (pure queue) | 206.6 ± 4.9 (med: 206.6) | 12.3 ± 0.4 (med: 12.0) |
| Queue-extension only | 219.0 ± 3.2 (med: 218.7) | 11.4 ± 0.2 (med: 11.0) |
| Hybrid queue-adaptive (Proposed) | 189.4 ± 3.6 (med: 189.9) | 13.9 ± 0.4 (med: 13.0) |
| Hybrid oracle-seeded | 190.6 ± 2.9 (med: 191.1) | 13.8 ± 0.3 (med: 13.0) |

---

## 7. Table VI: Heavy-Condition Audit (balanced-heavy & imbalanced_orr-heavy)

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table6_heavy_audit.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table6_heavy_audit.csv)

| Condition | Policy | Policy_Label | Vehicles_Arrived | p95_Wait_s | Max_Vehicle_Wait_s | Max_Queue_m | Stops_Median | Stops_p95 | Stops_Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | fixed | Fixed BTP (105s/95s) | 1698.9 | 646.5 | 1046.4 | 98.1 | 0.6 | 14.4 | 24.2 |
| balanced-heavy | webster_measured | Webster-measured (Ref) | 1698.9 | 686.8 | 1123.0 | 58.8 | 0.5 | 14.5 | 23.6 |
| balanced-heavy | webster_recalc | Webster-recalc | 1698.9 | 684.2 | 1165.6 | 68.0 | 0.6 | 14.8 | 24.0 |
| balanced-heavy | sumo_actuated | SUMO-actuated | 1698.9 | 638.7 | 1129.9 | 40.0 | 0.2 | 14.9 | 24.0 |
| balanced-heavy | adaptive | Adaptive (pure queue) | 1698.9 | 674.8 | 1141.1 | 44.7 | 0.4 | 15.1 | 24.8 |
| balanced-heavy | queue_extension | Queue-extension only | 1698.9 | 667.3 | 1146.1 | 48.3 | 0.5 | 14.6 | 25.1 |
| balanced-heavy | hybrid_queue_adaptive | Hybrid queue-adaptive (Proposed) | 1698.9 | 666.6 | 1138.5 | 46.6 | 0.5 | 15.4 | 25.1 |
| balanced-heavy | hybrid_oracle_seeded | Hybrid oracle-seeded | 1698.9 | 655.5 | 1129.2 | 45.9 | 0.5 | 15.0 | 25.4 |
| imbalanced_orr-heavy | fixed | Fixed BTP (105s/95s) | 1882.4 | 473.7 | 1462.9 | 106.6 | 0.8 | 11.9 | 21.2 |
| imbalanced_orr-heavy | webster_measured | Webster-measured (Ref) | 1882.4 | 525.3 | 1467.0 | 77.5 | 0.8 | 13.6 | 24.6 |
| imbalanced_orr-heavy | webster_recalc | Webster-recalc | 1882.4 | 526.0 | 1433.4 | 82.4 | 0.8 | 13.2 | 24.4 |
| imbalanced_orr-heavy | sumo_actuated | SUMO-actuated | 1882.4 | 546.2 | 1384.2 | 38.4 | 0.5 | 14.0 | 25.9 |
| imbalanced_orr-heavy | adaptive | Adaptive (pure queue) | 1882.4 | 554.6 | 1461.8 | 52.2 | 0.8 | 13.8 | 25.6 |
| imbalanced_orr-heavy | queue_extension | Queue-extension only | 1882.4 | 521.1 | 1423.1 | 46.7 | 0.8 | 14.1 | 26.2 |
| imbalanced_orr-heavy | hybrid_queue_adaptive | Hybrid queue-adaptive (Proposed) | 1882.4 | 542.4 | 1401.8 | 47.6 | 0.9 | 14.6 | 26.6 |
| imbalanced_orr-heavy | hybrid_oracle_seeded | Hybrid oracle-seeded | 1882.4 | 569.3 | 1436.0 | 49.5 | 0.6 | 14.4 | 27.2 |

---

## 8. Table VII: Red-Interval Distribution & Analytic Bound Audit

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table7_red_intervals.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table7_red_intervals.csv)
- **Definition:** Time from end of own green to start of next own green (includes both clearance intervals: $5\text{s} + G_{\text{opp}} + 5\text{s}$).
- **Analytic Bound:** Maximum green extension cap ($35\text{s}$) + gap-out ($3\text{s}$) + two clearances ($2 \times 5\text{s}$) = **48.0 s**.

| Policy_Label | N_red_intervals | Mean_red_s | p95_red_s | p99_red_s | Max_red_s | Analytic_Estimate_s | Max_Within_Analytic_Bound |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixed BTP (105s/95s) | 852 | 110.19953051643192 | 115.0 | 115.0 | 115.0 | 48.0 | No |
| Webster-measured (Ref) | 3836 | 28.857403545359748 | 34.0 | 115.0 | 115.0 | 48.0 | No |
| Webster-recalc | 3838 | 28.903595622720168 | 35.0 | 115.0 | 115.0 | 48.0 | No |
| SUMO-actuated | 5817 | 21.45435791645178 | 27.0 | 34.0 | 70.0 | 48.0 | No |
| Adaptive (pure queue) | 5502 | 22.403126135950565 | 25.0 | 28.0 | 70.0 | 48.0 | No |
| Queue-extension only | 5832 | 21.41495198902606 | 23.0 | 24.0 | 66.0 | 48.0 | No |
| Hybrid queue-adaptive (Proposed) | 5036 | 23.86914217633042 | 30.0 | 33.0 | 47.0 | 48.0 | Yes |
| Hybrid oracle-seeded | 5073 | 23.77744924108023 | 28.0 | 32.0 | 43.0 | 48.0 | Yes |

---

## 9. Table VIII & VIII-B: Little's Law Check & Physical Location of Waiting Vehicles

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSVs:** [`paper_final_v2/tables/table8_littles_law.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table8_littles_law.csv), [`paper_final_v2/tables/table8b_edge_breakdown.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table8b_edge_breakdown.csv)

### Per-Edge Distribution of Standing Vehicles (Speed < 0.1 m/s):

| Condition | Policy | Approach_Legs_vehs | Connector_Ramps_vehs | Outer_Arrival_Links_vehs | Total_Network_Halting_vehs | Outer_Link_Share_pct |
| --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | hybrid_queue_adaptive | 1.69 | 0.01 | 20.46 | 22.16 | 92.3 |
| balanced-heavy | sumo_actuated | 1.18 | 0.0 | 21.65 | 22.83 | 94.8 |
| imbalanced_orr-heavy | hybrid_queue_adaptive | 1.9 | 0.02 | 17.76 | 19.67 | 90.3 |
| imbalanced_orr-heavy | sumo_actuated | 1.96 | 0.59 | 18.5 | 21.06 | 87.8 |

> [!IMPORTANT]
> **Physical Resolution:** The Little's Law check implies 19.7 to 22.8 standing vehicles on average in heavy demand conditions. However, the intersection detector system ($Q_{\text{gt\_ext}}$) monitors only the approach legs (31.6–34.2 m) and connector ramps (96.0–131.0 m). As shown above, **90.3% to 94.8% of standing vehicles reside on the 178.8 m outer arrival links** (`orr_n_in`, `orr_s_in`, `wf_in`, `hal_in`), upstream of the ramp merge, which are outside the stopline queue detection zone.

---

## 10. Table IX: Insertion Delay & Backlog Audit

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table9_insertion_delay.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table9_insertion_delay.csv)

| Condition | Policy_Label | Mean_departDelay_s | p95_departDelay_s | Max_departDelay_s | Share_over_60s_pct | Max_Insertion_Backlog | Mean_Total_Delay_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | Fixed BTP (105s/95s) | 15.27801076905211 | 114.31318749999971 | 419.93875 | 5.410793635974864 | 51.625 | 127.74570561726586 |
| balanced-heavy | Webster-measured (Ref) | 19.21684181510458 | 126.97512499999864 | 531.85375 | 5.445197960687345 | 63.5 | 128.45435574816707 |
| balanced-heavy | Webster-recalc | 19.58545925664278 | 146.8243124999997 | 531.77125 | 5.558838222337721 | 65.375 | 128.30160942134071 |
| balanced-heavy | SUMO-actuated | 18.590003551585603 | 142.13949999999852 | 509.835 | 5.420160085962767 | 60.0 | 124.74624347147846 |
| balanced-heavy | Adaptive (pure queue) | 18.931101104580264 | 143.4504999999987 | 483.49375 | 5.781998568980608 | 64.5 | 126.69412371165316 |
| balanced-heavy | Queue-extension only | 17.766137777767874 | 138.57612499999965 | 500.73375 | 5.645406373465344 | 60.375 | 123.95289608823867 |
| balanced-heavy | Hybrid queue-adaptive (Proposed) | 16.95426019213152 | 127.11112499999707 | 465.3 | 5.356813621767085 | 59.875 | 126.9386392520438 |
| balanced-heavy | Hybrid oracle-seeded | 16.949085334924238 | 115.4019374999972 | 499.18 | 5.128887086046584 | 61.75 | 123.88921387175606 |
| imbalanced_orr-heavy | Fixed BTP (105s/95s) | 8.62482445955414 | 48.22656249999999 | 339.905 | 3.5215373838535933 | 36.625 | 114.06140216054575 |
| imbalanced_orr-heavy | Webster-measured (Ref) | 12.68711991192444 | 82.22368749999998 | 361.4875 | 4.935570458978612 | 48.0 | 112.41156338454932 |
| imbalanced_orr-heavy | Webster-recalc | 13.500525563009916 | 83.19768749999997 | 391.08125 | 5.412201702732942 | 50.75 | 112.46970688048586 |
| imbalanced_orr-heavy | SUMO-actuated | 14.231455214240476 | 117.31618749999996 | 371.1425 | 4.922979497916831 | 52.75 | 108.37074893798322 |
| imbalanced_orr-heavy | Adaptive (pure queue) | 13.97285234565428 | 91.76912499999996 | 396.9625 | 5.604156538881608 | 53.0 | 110.67871713851356 |
| imbalanced_orr-heavy | Queue-extension only | 12.80517361176143 | 74.63199999999992 | 401.89625 | 4.889726423805088 | 53.125 | 110.06503208235324 |
| imbalanced_orr-heavy | Hybrid queue-adaptive (Proposed) | 14.593804178270116 | 105.73424999999996 | 371.86 | 6.214283246179654 | 55.25 | 112.05975227313796 |
| imbalanced_orr-heavy | Hybrid oracle-seeded | 15.657179265565366 | 112.2610624999999 | 454.67875 | 5.9952496242529465 | 55.0 | 114.12367805547788 |

---

## 11. Table X: Sensitivity Analysis (t >= 300 s Exclusion)

- **Script:** [`analysis/paper_final_v2/compute_tables_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_tables_v2.py)
- **Output CSV:** [`paper_final_v2/tables/table10_sensitivity_300s.csv`](file:///e:/dp1-traffic-signal/paper_final_v2/tables/table10_sensitivity_300s.csv)

| Comparison | Metric | Hybrid_Mean_t_ge_300 | Ref_Mean_t_ge_300 | Delta_pct_t_ge_300 | Cluster_95_CI_t_ge_300 | Cluster_Holm_p_t_ge_300 | Significant_t_ge_300 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid vs webster_measured | p95 wait (s) | 472.47 | 468.65 | +0.9% | [-0.2, +2.1] | 0.23 | No |
| hybrid vs webster_measured | extended max queue (m) | 42.08 | 60.36 | -27.1% | [-32.6, -20.7] | 0.0 | Yes |
| hybrid vs webster_measured | wait gap (s) | 63.23 | 63.14 | +2.3% | [-5.6, +10.5] | 0.58 | No |
| hybrid vs webster_recalc | p95 wait (s) | 472.47 | 472.56 | -0.2% | [-1.8, +1.2] | 0.816 | No |
| hybrid vs webster_recalc | extended max queue (m) | 42.08 | 61.18 | -26.4% | [-32.3, -20.6] | 0.0 | Yes |
| hybrid vs webster_recalc | wait gap (s) | 63.23 | 64.34 | +8.5% | [-9.0, +28.0] | 0.743 | No |
| hybrid vs fixed | p95 wait (s) | 472.47 | 449.71 | -2.4% | [-3.7, -0.4] | 0.042 | Yes |
| hybrid vs fixed | extended max queue (m) | 42.08 | 86.2 | -49.0% | [-52.6, -45.0] | 0.0 | Yes |
| hybrid vs fixed | wait gap (s) | 63.23 | 63.88 | -0.1% | [-8.4, +8.5] | 0.969 | No |
| hybrid vs sumo_actuated | p95 wait (s) | 472.47 | 471.7 | +1.3% | [-1.4, +4.3] | 0.368 | No |
| hybrid vs sumo_actuated | extended max queue (m) | 42.08 | 37.9 | +12.4% | [+8.5, +15.4] | 0.0 | Yes |
| hybrid vs sumo_actuated | wait gap (s) | 63.23 | 64.11 | +9.4% | [-3.5, +22.3] | 0.297 | No |
| hybrid vs hybrid_oracle_seeded | p95 wait (s) | 472.47 | 473.66 | -0.1% | [-2.5, +2.0] | 1.0 | No |
| hybrid vs hybrid_oracle_seeded | extended max queue (m) | 42.08 | 43.26 | -1.3% | [-5.1, +2.4] | 1.0 | No |
| hybrid vs hybrid_oracle_seeded | wait gap (s) | 63.23 | 62.15 | +9.2% | [+4.2, +15.1] | 0.0 | Yes |

---

## 12. Settlement of Open Items with Raw Evidence

### (a) Row 126-128 of s136 `decisions.csv` (Verbatim Extraction)
```csv
t,cycle,axis,green_s,actual_green_s,q_N_m,q_S_m,q_E_m,q_W_m,proposed_action,applied_action,decision_outcome,action,reason,reason_code,g_base_s,delta_g_req_s,delta_g_app_s,g_extra_s,target_green_s,elapsed_s,q_active_m,q_competing_m,score_active,score_competing,is_max_green
126: 1166.0,60,EW,35.2,36.0,12.5,5.0,24.0,0.0,EXTEND,REQUEST_SWITCH,SWITCH_FAIRNESS_WAIT_LIMIT,REQUEST_SWITCH,"Extension rejected: Competing North-South red wait (36.0s) >= maximum allowed wait (35.0s) with waiting queue (12.5m). Triggering fair phase switch.",SWITCH_FAIRNESS_WAIT_LIMIT,14.2,3.0,0.0,21.0,35.2,36.0,24.0,12.5,24.0,25.4,False
127: 1171.0,60,NS,15.8,15.8,12.5,5.0,24.0,0.0,ENTER_GREEN,ENTER_GREEN,BASELINE_ENTRY,ENTER_GREEN,"North-South (ORR) green initiated with Webster baseline allocation 15.8s.",BASELINE_ENTRY,15.8,0.0,0.0,0.0,15.8,0.0,12.5,24.0,12.5,24.0,False
128: 1184.0,61,NS,15.8,13.0,0.0,0.0,24.0,0.0,GAP_OUT,GAP_OUT,SWITCH_GAP_OUT,GAP_OUT,"North-South queue cleared (0.0m for 3.0s >= gap-out threshold 3.0s) while East-West is waiting (24.0m); gapping out early.",SWITCH_GAP_OUT,15.8,0.0,0.0,0.0,15.8,13.0,0.0,24.0,0.0,32.9,False
```
- **Verdict:** NS $g_{\text{base}}$ at $t=1171\text{ s}$ was **15.8 s** (`g_base_s=15.8`, `green_s=15.8`, `target_green_s=15.8`). The number 25.8 s was a typographic error.

### (b) Confirmation of Fixed BTP Timing Plan
- In `dp1/config.py:270` (`FIXED_MARATHAHALLI`), timings are:
  - EW (Varthur Rd / Whitefield): $110 - 5 = \mathbf{105.0\text{ s}}$ green
  - NS (Outer Ring Road): $100 - 5 = \mathbf{95.0\text{ s}}$ green
  - Cycle time = $105 + 5 + 95 + 5 = \mathbf{210.0\text{ s}}$.
- Verified in all 48 `fixed` simulation decision logs (`decisions.csv`): NS green = 95 s, EW green = 105 s.

### (c) Competing Red-Wait Guard Condition in Code
- In `dp1/controllers/hybrid_queue_adaptive.py:453`:
  ```python
  if self._competing_wait_guard_active and comp_q >= self.cfg.min_competing_queue_m:
  ```
- `min_competing_queue_m` is configured as **2.0 m** (`dp1/config.py:95` and `configs/final_hybrid_queue_adaptive.yaml`).
- **Verdict:** The condition enforced in code is $\mathbf{Q_{\text{comp}} \ge 2.0\text{ m}}$, NOT $Q_{\text{comp}} > 0$. The paper text must be updated accordingly.

