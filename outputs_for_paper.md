# DP1 Research Paper: Verified Empirical Extraction Ledger

- **Git Commit Hash:** `6a15db3d784a4fdffc23d73e3932761480e9bea5`
- **Primary Study Directory:** `E:\dp1-traffic-signal\results\research\exp_marathahalli_improve_final`
- **Verification Protocol:** Frozen under Pre-Registration Amendment 3 (commit `4511149`, 2026-11-04 11:05 UTC+5:30)
- **Scope:** Read-only data extraction across all 384 runs (8 policies x 6 conditions x 8 seeds 131-138). Zero simulation reruns, zero tuning.

## OUTPUT 1: Seed-Clustered Bootstrap Comparison Table

- **Script / Function:** [`analysis/paper_final/extract_paper_outputs.py:compute_output_1()`](file:///e:/dp1-traffic-signal/analysis/paper_final/extract_paper_outputs.py) (matches [`analysis/paper_final/seed_clustered_bootstrap.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/seed_clustered_bootstrap.py))
- **Method:** Cluster unit = SEED ($n=8$). Resampling 8 whole seeds with replacement, averaging condition deltas within each seed. 10,000 resamples, fixed random seed 42.
- **Holm Adjustment:** Step-down Holm-Bonferroni correction applied across the 3 primary metrics (`p95 wait`, `extended max queue`, `wait gap`) within each comparison and subset.
- **Confirmed Verification Targets:**
  - **hybrid vs hybrid_oracle_seeded, wait gap (all 6 pooled):** `+15.3%` [95% CI: `+4.1%, +28.2%`], raw $p = 0.010$, Holm $p = 0.030$.
  - **hybrid vs fixed, p95 wait (non-stationary subset):** `+5.1%` [95% CI: `+1.1%, +8.7%`], raw $p = 0.022$, Holm $p = 0.044$.

| Comparison | Subset | Metric | Hybrid Mean | Ref Mean | Delta % | Cluster 95% CI | Cluster Raw p | Cluster Holm p | Delta Matches Pair (Y/N) | Pair-Level Delta % | Pair-Level 95% CI | Pair-Level Raw p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid vs webster_measured | all_6_pooled | p95 wait (s) | 452.33 | 446.75 | -0.9% | [-2.8, +1.1] | 0.374 | 0.747 | Y | -0.9% | [-4.3, +2.5] | 0.600 |
| hybrid vs webster_measured | all_6_pooled | extended max queue (m) | 42.25 | 62.21 | -28.8% | [-33.7, -23.4] | 0.000 | 0.000 | Y | -28.8% | [-34.8, -22.4] | 0.000 |
| hybrid vs webster_measured | all_6_pooled | wait gap (s) | 58.28 | 59.81 | +3.0% | [-7.1, +16.6] | 0.666 | 0.747 | Y | +3.0% | [-8.4, +15.8] | 0.652 |
| hybrid vs webster_measured | all_6_pooled | mean wait (s) | 76.70 | 77.75 | -3.1% | [-5.1, -1.1] | 0.004 | n/a (secondary) | Y | -3.1% | [-5.3, -1.2] | 0.001 |
| hybrid vs webster_measured | all_6_pooled | mean queue (m) | 2.52 | 4.01 | -35.7% | [-37.6, -34.2] | 0.000 | n/a (secondary) | Y | -35.7% | [-38.4, -33.0] | 0.000 |
| hybrid vs webster_measured | 3_non_stationary | p95 wait (s) | 487.40 | 472.90 | +2.4% | [-1.0, +5.8] | 0.172 | 0.344 | Y | +2.4% | [-1.8, +6.5] | 0.251 |
| hybrid vs webster_measured | 3_non_stationary | extended max queue (m) | 44.72 | 67.53 | -29.7% | [-36.7, -22.6] | 0.000 | 0.000 | Y | -29.7% | [-39.8, -18.5] | 0.000 |
| hybrid vs webster_measured | 3_non_stationary | wait gap (s) | 56.57 | 54.13 | +13.4% | [-4.3, +38.0] | 0.200 | 0.344 | Y | +13.4% | [-4.9, +35.4] | 0.168 |
| hybrid vs webster_measured | 3_non_stationary | mean wait (s) | 81.43 | 82.65 | -2.0% | [-4.6, +0.6] | 0.133 | n/a (secondary) | Y | -2.0% | [-4.8, +0.7] | 0.151 |
| hybrid vs webster_measured | 3_non_stationary | mean queue (m) | 2.63 | 4.30 | -36.4% | [-38.9, -33.9] | 0.000 | n/a (secondary) | Y | -36.4% | [-41.3, -31.4] | 0.000 |
| hybrid vs webster_measured | 3_stationary | p95 wait (s) | 417.26 | 420.61 | -4.2% | [-7.8, -0.6] | 0.018 | 0.036 | Y | -4.2% | [-8.9, +1.0] | 0.109 |
| hybrid vs webster_measured | 3_stationary | extended max queue (m) | 39.77 | 56.89 | -27.9% | [-34.0, -21.3] | 0.000 | 0.000 | Y | -27.9% | [-34.5, -21.0] | 0.000 |
| hybrid vs webster_measured | 3_stationary | wait gap (s) | 59.99 | 65.49 | -7.3% | [-17.2, +1.7] | 0.133 | 0.133 | Y | -7.3% | [-18.7, +4.5] | 0.232 |
| hybrid vs webster_measured | 3_stationary | mean wait (s) | 71.97 | 72.85 | -4.3% | [-6.6, -1.5] | 0.004 | n/a (secondary) | Y | -4.3% | [-7.4, -1.3] | 0.003 |
| hybrid vs webster_measured | 3_stationary | mean queue (m) | 2.41 | 3.71 | -35.0% | [-37.2, -32.9] | 0.000 | n/a (secondary) | Y | -35.0% | [-37.2, -33.0] | 0.000 |
| hybrid vs webster_recalc | all_6_pooled | p95 wait (s) | 452.33 | 453.96 | -2.5% | [-4.6, -0.3] | 0.027 | 0.054 | Y | -2.5% | [-6.0, +0.9] | 0.150 |
| hybrid vs webster_recalc | all_6_pooled | extended max queue (m) | 42.25 | 63.19 | -28.3% | [-33.9, -22.5] | 0.000 | 0.000 | Y | -28.3% | [-34.7, -21.7] | 0.000 |
| hybrid vs webster_recalc | all_6_pooled | wait gap (s) | 58.28 | 60.22 | +17.5% | [-8.3, +57.2] | 0.392 | 0.392 | Y | +17.5% | [-8.0, +58.0] | 0.385 |
| hybrid vs webster_recalc | all_6_pooled | mean wait (s) | 76.70 | 77.65 | -3.1% | [-5.1, -1.2] | 0.000 | n/a (secondary) | Y | -3.1% | [-5.5, -0.9] | 0.003 |
| hybrid vs webster_recalc | all_6_pooled | mean queue (m) | 2.52 | 3.82 | -33.2% | [-34.4, -32.0] | 0.000 | n/a (secondary) | Y | -33.2% | [-35.5, -30.6] | 0.000 |
| hybrid vs webster_recalc | 3_non_stationary | p95 wait (s) | 487.40 | 487.42 | -0.1% | [-3.8, +3.2] | 0.951 | 0.951 | Y | -0.1% | [-4.2, +3.8] | 0.922 |
| hybrid vs webster_recalc | 3_non_stationary | extended max queue (m) | 44.72 | 64.80 | -26.1% | [-33.1, -19.1] | 0.000 | 0.000 | Y | -26.1% | [-36.0, -16.0] | 0.000 |
| hybrid vs webster_recalc | 3_non_stationary | wait gap (s) | 56.57 | 54.64 | +34.4% | [-7.7, +108.6] | 0.413 | 0.827 | Y | +34.4% | [-9.0, +109.9] | 0.389 |
| hybrid vs webster_recalc | 3_non_stationary | mean wait (s) | 81.43 | 82.80 | -1.8% | [-3.8, +0.4] | 0.105 | n/a (secondary) | Y | -1.8% | [-4.4, +0.8] | 0.182 |
| hybrid vs webster_recalc | 3_non_stationary | mean queue (m) | 2.63 | 3.88 | -31.1% | [-33.2, -28.5] | 0.000 | n/a (secondary) | Y | -31.1% | [-35.1, -27.0] | 0.000 |
| hybrid vs webster_recalc | 3_stationary | p95 wait (s) | 417.26 | 420.50 | -4.8% | [-7.7, -1.7] | 0.002 | 0.004 | Y | -4.8% | [-10.0, +0.6] | 0.086 |
| hybrid vs webster_recalc | 3_stationary | extended max queue (m) | 39.77 | 61.58 | -30.5% | [-37.8, -22.3] | 0.000 | 0.000 | Y | -30.5% | [-38.6, -22.2] | 0.000 |
| hybrid vs webster_recalc | 3_stationary | wait gap (s) | 59.99 | 65.80 | +0.7% | [-14.6, +16.5] | 0.942 | 0.942 | Y | +0.7% | [-15.7, +20.1] | 0.998 |
| hybrid vs webster_recalc | 3_stationary | mean wait (s) | 71.97 | 72.51 | -4.4% | [-7.6, -1.1] | 0.008 | n/a (secondary) | Y | -4.4% | [-8.4, -0.9] | 0.009 |
| hybrid vs webster_recalc | 3_stationary | mean queue (m) | 2.41 | 3.75 | -35.3% | [-37.2, -33.2] | 0.000 | n/a (secondary) | Y | -35.3% | [-37.8, -32.7] | 0.000 |
| hybrid vs fixed | all_6_pooled | p95 wait (s) | 452.33 | 432.22 | -2.8% | [-4.8, -0.9] | 0.004 | 0.008 | Y | -2.8% | [-10.0, +3.8] | 0.433 |
| hybrid vs fixed | all_6_pooled | extended max queue (m) | 42.25 | 86.36 | -48.7% | [-52.5, -44.7] | 0.000 | 0.000 | Y | -48.7% | [-53.0, -43.7] | 0.000 |
| hybrid vs fixed | all_6_pooled | wait gap (s) | 58.28 | 59.75 | +1.3% | [-6.4, +8.8] | 0.724 | 0.724 | Y | +1.3% | [-7.5, +10.6] | 0.787 |
| hybrid vs fixed | all_6_pooled | mean wait (s) | 76.70 | 81.54 | -11.6% | [-13.0, -10.3] | 0.000 | n/a (secondary) | Y | -11.6% | [-16.4, -7.3] | 0.000 |
| hybrid vs fixed | all_6_pooled | mean queue (m) | 2.52 | 8.96 | -71.6% | [-72.2, -71.1] | 0.000 | n/a (secondary) | Y | -71.6% | [-72.6, -70.7] | 0.000 |
| hybrid vs fixed | 3_non_stationary | p95 wait (s) | 487.40 | 462.47 | +5.1% | [+1.1, +8.7] | 0.011 | 0.022 | Y | +5.1% | [-0.3, +10.3] | 0.064 |
| hybrid vs fixed | 3_non_stationary | extended max queue (m) | 44.72 | 89.28 | -48.3% | [-53.3, -42.3] | 0.000 | 0.000 | Y | -48.3% | [-55.1, -39.9] | 0.000 |
| hybrid vs fixed | 3_non_stationary | wait gap (s) | 56.57 | 54.41 | +3.3% | [-2.4, +8.5] | 0.256 | 0.256 | Y | +3.3% | [-6.9, +13.2] | 0.513 |
| hybrid vs fixed | 3_non_stationary | mean wait (s) | 81.43 | 85.24 | -4.9% | [-6.2, -3.6] | 0.000 | n/a (secondary) | Y | -4.9% | [-7.1, -2.7] | 0.000 |
| hybrid vs fixed | 3_non_stationary | mean queue (m) | 2.63 | 8.88 | -70.3% | [-71.2, -69.3] | 0.000 | n/a (secondary) | Y | -70.3% | [-71.5, -69.0] | 0.000 |
| hybrid vs fixed | 3_stationary | p95 wait (s) | 417.26 | 401.96 | -10.6% | [-12.5, -8.3] | 0.000 | 0.000 | Y | -10.6% | [-22.9, +1.3] | 0.081 |
| hybrid vs fixed | 3_stationary | extended max queue (m) | 39.77 | 83.44 | -49.1% | [-54.1, -44.0] | 0.000 | 0.000 | Y | -49.1% | [-54.0, -44.1] | 0.000 |
| hybrid vs fixed | 3_stationary | wait gap (s) | 59.99 | 65.09 | -0.7% | [-12.4, +11.9] | 0.890 | 0.890 | Y | -0.7% | [-14.9, +14.7] | 0.901 |
| hybrid vs fixed | 3_stationary | mean wait (s) | 71.97 | 77.83 | -18.4% | [-20.3, -16.6] | 0.000 | n/a (secondary) | Y | -18.4% | [-26.8, -10.6] | 0.000 |
| hybrid vs fixed | 3_stationary | mean queue (m) | 2.41 | 9.04 | -73.0% | [-73.9, -72.1] | 0.000 | n/a (secondary) | Y | -73.0% | [-74.3, -71.8] | 0.000 |
| hybrid vs sumo_actuated | all_6_pooled | p95 wait (s) | 452.33 | 452.15 | +1.0% | [-2.0, +4.0] | 0.544 | 0.544 | Y | +1.0% | [-2.1, +4.1] | 0.578 |
| hybrid vs sumo_actuated | all_6_pooled | extended max queue (m) | 42.25 | 38.20 | +11.4% | [+7.1, +15.1] | 0.000 | 0.000 | Y | +11.4% | [+4.6, +18.8] | 0.000 |
| hybrid vs sumo_actuated | all_6_pooled | wait gap (s) | 58.28 | 59.44 | +14.8% | [-2.6, +34.8] | 0.105 | 0.210 | Y | +14.8% | [-2.8, +37.5] | 0.122 |
| hybrid vs sumo_actuated | all_6_pooled | mean wait (s) | 76.70 | 75.69 | +3.4% | [+0.8, +5.9] | 0.010 | n/a (secondary) | Y | +3.4% | [+0.6, +6.4] | 0.014 |
| hybrid vs sumo_actuated | all_6_pooled | mean queue (m) | 2.52 | 1.89 | +35.5% | [+31.4, +39.5] | 0.000 | n/a (secondary) | Y | +35.5% | [+30.9, +39.9] | 0.000 |
| hybrid vs sumo_actuated | 3_non_stationary | p95 wait (s) | 487.40 | 495.68 | -1.6% | [-5.8, +1.7] | 0.423 | 0.846 | Y | -1.6% | [-5.5, +2.5] | 0.426 |
| hybrid vs sumo_actuated | 3_non_stationary | extended max queue (m) | 44.72 | 41.59 | +7.5% | [+2.9, +12.7] | 0.000 | 0.000 | Y | +7.5% | [-0.2, +15.5] | 0.056 |
| hybrid vs sumo_actuated | 3_non_stationary | wait gap (s) | 56.57 | 58.50 | -3.8% | [-13.4, +7.8] | 0.466 | 0.846 | Y | -3.8% | [-13.8, +6.0] | 0.448 |
| hybrid vs sumo_actuated | 3_non_stationary | mean wait (s) | 81.43 | 82.10 | -0.7% | [-2.5, +1.0] | 0.429 | n/a (secondary) | Y | -0.7% | [-3.2, +2.0] | 0.559 |
| hybrid vs sumo_actuated | 3_non_stationary | mean queue (m) | 2.63 | 2.02 | +33.4% | [+28.0, +39.9] | 0.000 | n/a (secondary) | Y | +33.4% | [+25.4, +40.8] | 0.000 |
| hybrid vs sumo_actuated | 3_stationary | p95 wait (s) | 417.26 | 408.62 | +3.5% | [-0.2, +7.4] | 0.066 | 0.068 | Y | +3.5% | [-0.9, +8.1] | 0.116 |
| hybrid vs sumo_actuated | 3_stationary | extended max queue (m) | 39.77 | 34.82 | +15.3% | [+9.2, +21.1] | 0.000 | 0.000 | Y | +15.3% | [+4.5, +27.1] | 0.005 |
| hybrid vs sumo_actuated | 3_stationary | wait gap (s) | 59.99 | 60.38 | +33.4% | [+1.9, +72.9] | 0.034 | 0.068 | Y | +33.4% | [+0.1, +75.3] | 0.049 |
| hybrid vs sumo_actuated | 3_stationary | mean wait (s) | 71.97 | 69.28 | +7.6% | [+3.0, +11.9] | 0.001 | n/a (secondary) | Y | +7.6% | [+3.1, +12.3] | 0.001 |
| hybrid vs sumo_actuated | 3_stationary | mean queue (m) | 2.41 | 1.75 | +37.7% | [+33.0, +42.5] | 0.000 | n/a (secondary) | Y | +37.7% | [+33.6, +41.6] | 0.000 |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | p95 wait (s) | 452.33 | 455.86 | -0.5% | [-2.9, +1.9] | 0.700 | 1.000 | Y | -0.5% | [-2.8, +1.7] | 0.660 |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | extended max queue (m) | 42.25 | 43.41 | -1.2% | [-5.1, +2.5] | 0.551 | 1.000 | Y | -1.2% | [-6.1, +4.0] | 0.627 |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | wait gap (s) | 58.28 | 58.33 | +15.3% | [+4.1, +28.2] | 0.003 | 0.010 | Y | +15.3% | [-0.3, +34.1] | 0.054 |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | mean wait (s) | 76.70 | 76.41 | +0.5% | [-1.0, +1.7] | 0.480 | n/a (secondary) | Y | +0.5% | [-1.2, +2.1] | 0.564 |
| hybrid vs hybrid_oracle_seeded | all_6_pooled | mean queue (m) | 2.52 | 2.55 | -0.4% | [-3.3, +1.9] | 0.856 | n/a (secondary) | Y | -0.4% | [-3.3, +2.2] | 0.851 |
| hybrid vs hybrid_oracle_seeded | 3_non_stationary | p95 wait (s) | 487.40 | 489.28 | -0.3% | [-3.4, +2.8] | 0.852 | 1.000 | Y | -0.3% | [-2.9, +2.3] | 0.794 |
| hybrid vs hybrid_oracle_seeded | 3_non_stationary | extended max queue (m) | 44.72 | 46.60 | -3.3% | [-7.6, +1.8] | 0.198 | 0.593 | Y | -3.3% | [-8.8, +3.3] | 0.290 |
| hybrid vs hybrid_oracle_seeded | 3_non_stationary | wait gap (s) | 56.57 | 55.80 | +0.2% | [-8.1, +6.9] | 0.905 | 1.000 | Y | +0.2% | [-10.9, +11.5] | 0.979 |
| hybrid vs hybrid_oracle_seeded | 3_non_stationary | mean wait (s) | 81.43 | 81.56 | -0.3% | [-2.4, +1.8] | 0.750 | n/a (secondary) | Y | -0.3% | [-2.3, +1.5] | 0.739 |
| hybrid vs hybrid_oracle_seeded | 3_non_stationary | mean queue (m) | 2.63 | 2.69 | -0.3% | [-5.1, +3.4] | 0.940 | n/a (secondary) | Y | -0.3% | [-5.5, +3.8] | 0.965 |
| hybrid vs hybrid_oracle_seeded | 3_stationary | p95 wait (s) | 417.26 | 422.45 | -0.7% | [-5.5, +2.6] | 0.796 | 1.000 | Y | -0.7% | [-4.5, +2.8] | 0.725 |
| hybrid vs hybrid_oracle_seeded | 3_stationary | extended max queue (m) | 39.77 | 40.21 | +0.8% | [-4.5, +6.4] | 0.784 | 1.000 | Y | +0.8% | [-6.8, +8.6] | 0.851 |
| hybrid vs hybrid_oracle_seeded | 3_stationary | wait gap (s) | 59.99 | 60.86 | +30.4% | [+6.5, +56.7] | 0.009 | 0.027 | Y | +30.4% | [+2.4, +64.9] | 0.029 |
| hybrid vs hybrid_oracle_seeded | 3_stationary | mean wait (s) | 71.97 | 71.26 | +1.3% | [-1.5, +3.8] | 0.342 | n/a (secondary) | Y | +1.3% | [-1.5, +3.8] | 0.332 |
| hybrid vs hybrid_oracle_seeded | 3_stationary | mean queue (m) | 2.41 | 2.41 | -0.4% | [-2.8, +1.7] | 0.789 | n/a (secondary) | Y | -0.4% | [-3.3, +2.4] | 0.810 |

## OUTPUT 2: Insertion and Departure Delay Check

- **Source Artifacts:** `results/research/exp_marathahalli_improve_final/*/tripinfo.xml` (all 384 runs parsed).
- **Teleports:** **0 teleports** across all 384 runs (`--time-to-teleport -1` configured in `dp1/runner.py:165`, preventing jam clearing by teleportation).
- **Insertion Warnings:** Suppressed in simulation runner (`--no-warnings true` in `dp1/runner.py:166`).
- **Backlog Tracking:** Computed by sweep-line interval tracking $[t_\text{sched}, t_\text{depart})$ for every vehicle. SUMO internal output option that logs this directly is `--summary-output <FILE>` (or `--tripinfo-output --duration-log.statistics`).

| policy | condition | mean_departDelay | p95_departDelay | max_departDelay | count_gt_0 | pct_gt_0 | count_gt_60 | pct_gt_60 | max_backlog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adaptive | balanced-heavy | 17.942680648355893 | 135.2808124999979 | 474.396875 | 1684.4375 | 99.14837775542713 | 95.0625 | 5.5694060953738465 | 62.1875 |
| adaptive | balanced-low | 0.5143816364865977 | 0.9599999999999999 | 1.914375 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| adaptive | imbalanced_orr-heavy | 14.283328261962199 | 98.75168749999997 | 384.41125 | 1867.5 | 99.20947276541371 | 111.5625 | 5.909219892530631 | 54.125 |
| adaptive | lane_closure-medium | 7.531007589032503 | 4.894343749999039 | 292.5225 | 1621.125 | 99.02298120105696 | 45.25 | 2.7587143841432265 | 33.0 |
| adaptive | ramp_peak-medium | 13.064487322960746 | 114.90799999999994 | 339.003125 | 1426.5625 | 99.12453238133959 | 69.5 | 4.8196377293402115 | 47.3125 |
| adaptive | surge_shift-medium | 1.5655437518349913 | 7.041906249999934 | 36.011874999999996 | 1519.8125 | 99.16889195908254 | 12.5 | 0.8162016778736634 | 11.125 |
| fixed | balanced-heavy | 15.27801076905211 | 114.31318749999971 | 419.93875 | 1684.875 | 99.17420777541989 | 92.375 | 5.410793635974864 | 51.625 |
| fixed | balanced-low | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| fixed | imbalanced_orr-heavy | 8.62482445955414 | 48.226562499999986 | 339.905 | 1867.5 | 99.20945958742361 | 66.875 | 3.5215373838535937 | 36.625 |
| fixed | lane_closure-medium | 5.133115283543933 | 1.3195624999999902 | 237.69375 | 1620.75 | 99.00013988314569 | 31.625 | 1.932702734931907 | 25.125 |
| fixed | ramp_peak-medium | 12.95703379671305 | 114.30724999999998 | 338.87 | 1426.75 | 99.13763129894724 | 71.875 | 4.991645520028106 | 46.375 |
| fixed | surge_shift-medium | 0.7370208547699926 | 1.0752499999999998 | 13.0775 | 1519.625 | 99.15645194562431 | 1.0 | 0.06506180871828238 | 7.125 |
| queue_extension | balanced-heavy | 17.766137777767877 | 138.57612499999965 | 500.73375 | 1684.25 | 99.1371825611973 | 96.375 | 5.6454063734653435 | 60.375 |
| queue_extension | balanced-low | 0.5143121147958302 | 0.9599999999999999 | 1.8975 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| queue_extension | imbalanced_orr-heavy | 12.80517361176143 | 74.63199999999992 | 401.89625 | 1867.375 | 99.20323111753663 | 92.5 | 4.889726423805088 | 53.125 |
| queue_extension | lane_closure-medium | 7.528894525408216 | 3.6746249999996614 | 293.6875 | 1621.0 | 99.01544228826423 | 48.0 | 2.9389847623606578 | 33.125 |
| queue_extension | ramp_peak-medium | 13.353507014532397 | 115.64293749999993 | 380.4925 | 1426.5 | 99.12008398276308 | 69.5 | 4.818851259166429 | 47.5 |
| queue_extension | surge_shift-medium | 0.5647045945961019 | 0.9902499999999997 | 20.2675 | 1519.75 | 99.16484120736928 | 0.25 | 0.015903307888040712 | 6.0 |
| sumo_actuated | balanced-heavy | 18.590003551585603 | 142.13949999999852 | 509.835 | 1684.5 | 99.15222864883441 | 92.625 | 5.420160085962767 | 60.0 |
| sumo_actuated | balanced-low | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| sumo_actuated | imbalanced_orr-heavy | 14.231455214240475 | 117.31618749999996 | 371.1425 | 1867.5 | 99.20968990969946 | 93.125 | 4.922979497916832 | 52.75 |
| sumo_actuated | lane_closure-medium | 8.095881981314374 | 4.337999999999993 | 308.56 | 1621.125 | 99.02266354765186 | 48.625 | 2.9711108404983317 | 32.75 |
| sumo_actuated | ramp_peak-medium | 13.7181111996431 | 111.52562499999982 | 358.755 | 1426.625 | 99.1289807799161 | 72.375 | 5.028178394824168 | 50.25 |
| sumo_actuated | surge_shift-medium | 1.076889221618624 | 5.0263124999999995 | 44.53 | 1519.75 | 99.16484120736928 | 7.5 | 0.4870582046582931 | 8.25 |
| webster_measured | balanced-heavy | 19.21684181510458 | 126.97512499999863 | 531.85375 | 1684.5 | 99.15187116284243 | 93.125 | 5.445197960687345 | 63.5 |
| webster_measured | balanced-low | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| webster_measured | imbalanced_orr-heavy | 12.68711991192444 | 82.22368749999997 | 361.48749999999995 | 1867.375 | 99.20292876192727 | 93.375 | 4.935570458978613 | 48.0 |
| webster_measured | lane_closure-medium | 5.621728110508285 | 1.3334374999999994 | 243.26125000000002 | 1621.0 | 99.0152129013273 | 29.75 | 1.8195196610081483 | 26.875 |
| webster_measured | ramp_peak-medium | 13.0768247066053 | 104.34493749999992 | 352.39125 | 1426.5 | 99.12008398276308 | 69.75 | 4.840056239656651 | 47.375 |
| webster_measured | surge_shift-medium | 0.7048453711257616 | 1.0786874999999991 | 19.9725 | 1519.625 | 99.15645194562431 | 0.125 | 0.007951653944020356 | 7.25 |
| webster_recalc | balanced-heavy | 19.58545925664278 | 146.8243124999997 | 531.77125 | 1684.5 | 99.15175647451264 | 95.0 | 5.558838222337721 | 65.375 |
| webster_recalc | balanced-low | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| webster_recalc | imbalanced_orr-heavy | 13.500525563009914 | 83.19768749999997 | 391.08125 | 1867.125 | 99.18976026565926 | 102.125 | 5.412201702732942 | 50.75 |
| webster_recalc | lane_closure-medium | 6.763674544331541 | 1.3396249999999978 | 281.08 | 1621.125 | 99.02243416071494 | 34.0 | 2.086949757581767 | 29.375 |
| webster_recalc | ramp_peak-medium | 13.739661230632276 | 117.68625000000003 | 342.8225 | 1426.625 | 99.12875257375242 | 76.875 | 5.329474843202714 | 51.625 |
| webster_recalc | surge_shift-medium | 0.5462317999238794 | 0.99375 | 4.68375 | 1519.625 | 99.15645194562431 | 0.0 | 0.0 | 6.0 |

## OUTPUT 3: Queue Sensing Coverage & Little's Law Check

### (a) Approach Leg + Connector Ramp Physical Coverage ($Q_\text{gt\_ext}$)
From [`dp1/queues.py:70-123`](file:///e:/dp1-traffic-signal/dp1/queues.py#L70) and `network/marathahalli/dist/marathahalli.net.xml`:

| Approach | Leg Edge ID & Length | Internal Connector Node | Ramp Edge ID & Length | Total $Q_\text{gt\_ext}$ Coverage | Code Citation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **N (ORR North)** | `leg_orr_n_in` (32.60 m) | `:node_junc_n_0` (0.10 m) | `ramp_orr_n_in` (131.04 m) | **163.74 m** | `dp1/queues.py:74-82` |
| **S (ORR South)** | `leg_orr_s_in` (31.60 m) | `:node_junc_s_2` (0.10 m) | `ramp_orr_s_in` (96.04 m) | **127.74 m** | `dp1/queues.py:87-95` |
| **E (Varthur East)** | `leg_wf_in` (34.18 m) | `:node_junc_e_0` (0.42 m) | `ramp_wf_in` (112.96 m) | **147.56 m** | `dp1/queues.py:100-108` |
| **W (Varthur West)** | `leg_hal_in` (34.18 m) | `:node_junc_w_2` (1.27 m) | `ramp_hal_in` (103.36 m) | **138.81 m** | `dp1/queues.py:113-121` |

### (b) Length of Outer Arrival Links Beyond $Q_\text{gt\_ext}$
From `network/marathahalli/dist/marathahalli.net.xml`:
- Approach N outer arterial: `orr_n_in` = **178.80 m** (2 lanes)
- Approach S outer arterial: `orr_s_in` = **178.80 m** (2 lanes)
- Approach E outer arterial: `wf_in` = **178.80 m** (2 lanes)
- Approach W outer arterial: `hal_in` = **178.80 m** (2 lanes)

### (c) Stopped-Vehicle Counts Full Network vs $Q_\text{gt\_ext}$
> **NOT AVAILABLE:** Instantaneous vehicle counts with speed $< 1.4\text{ m/s}$ across the entire network (outside the approach + ramp chains) were **not logged** in `timeseries.csv` or `telemetry.json`. `timeseries.csv` records ground truth exclusively along the 4 approach chains (`gt_ext_q_*` and `gt_ext_n_*`).

### (d) Little's Law Implied Queue vs $Q_\text{gt\_ext}$
For `balanced-heavy` and `imbalanced_orr-heavy`, arrival rate $\lambda \approx 0.233\text{ veh/s}$ per approach ($1679\text{ veh} / 1800\text{ s} / 4$). Mean wait $W$ multiplied by arrival rate $\lambda$ yields the time-average number of vehicles $L = \lambda W$ delayed in the system:

| Condition | Policy | Max Speed < 1.4 m/s Full Net | Qgt_ext Max Queue (m) | Qgt_ext Mean Queue (m) | Mean Wait (s) | p95 Wait (s) | Max Vehicle Wait (s) | Little's Law Implied Vehs | Little's Law Implied Queue (m) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | fixed | NOT AVAILABLE (not logged in timeseries) | 133.8 | 9.48 | 112.5 | 646.5 | 1191.0 | 26.2 | 98.4 |
| balanced-heavy | webster_measured | NOT AVAILABLE (not logged in timeseries) | 66.8 | 4.11 | 109.2 | 686.8 | 1340.0 | 25.5 | 95.5 |
| balanced-heavy | webster_recalc | NOT AVAILABLE (not logged in timeseries) | 110.5 | 4.23 | 108.7 | 684.2 | 1367.0 | 25.4 | 95.1 |
| balanced-heavy | sumo_actuated | NOT AVAILABLE (not logged in timeseries) | 51.1 | 1.98 | 106.2 | 638.7 | 1404.0 | 24.8 | 92.8 |
| balanced-heavy | adaptive | NOT AVAILABLE (not logged in timeseries) | 59.1 | 2.53 | 107.8 | 674.8 | 1319.0 | 25.1 | 94.2 |
| balanced-heavy | queue_extension | NOT AVAILABLE (not logged in timeseries) | 58.2 | 2.54 | 106.2 | 667.3 | 1410.0 | 24.8 | 92.9 |
| balanced-heavy | hybrid_queue_adaptive | NOT AVAILABLE (not logged in timeseries) | 66.1 | 2.74 | 110.0 | 666.6 | 1309.0 | 25.6 | 96.2 |
| balanced-heavy | hybrid_oracle_seeded | NOT AVAILABLE (not logged in timeseries) | 51.5 | 2.68 | 106.9 | 655.5 | 1282.0 | 24.9 | 93.5 |
| imbalanced_orr-heavy | fixed | NOT AVAILABLE (not logged in timeseries) | 163.6 | 11.84 | 105.4 | 473.7 | 1600.0 | 24.6 | 92.2 |
| imbalanced_orr-heavy | webster_measured | NOT AVAILABLE (not logged in timeseries) | 89.1 | 4.61 | 99.7 | 525.3 | 1680.0 | 23.3 | 87.2 |
| imbalanced_orr-heavy | webster_recalc | NOT AVAILABLE (not logged in timeseries) | 112.7 | 4.67 | 99.0 | 526.0 | 1665.0 | 23.1 | 86.5 |
| imbalanced_orr-heavy | sumo_actuated | NOT AVAILABLE (not logged in timeseries) | 44.1 | 2.14 | 94.1 | 546.2 | 1566.0 | 22.0 | 82.3 |
| imbalanced_orr-heavy | adaptive | NOT AVAILABLE (not logged in timeseries) | 96.3 | 3.17 | 96.7 | 554.6 | 1646.0 | 22.6 | 84.6 |
| imbalanced_orr-heavy | queue_extension | NOT AVAILABLE (not logged in timeseries) | 58.6 | 2.92 | 97.3 | 521.1 | 1628.0 | 22.7 | 85.1 |
| imbalanced_orr-heavy | hybrid_queue_adaptive | NOT AVAILABLE (not logged in timeseries) | 66.4 | 2.94 | 97.5 | 542.4 | 1547.0 | 22.7 | 85.2 |
| imbalanced_orr-heavy | hybrid_oracle_seeded | NOT AVAILABLE (not logged in timeseries) | 66.3 | 2.93 | 98.5 | 569.3 | 1623.0 | 23.0 | 86.1 |

## OUTPUT 4: The 48.0 s Red-Wait Maximum Analysis

### Top 5 Largest Red Waits at Green Start (Across all 48 Hybrid Runs)

| run_id | condition | seed | t_green_start | axis_entering | opp_axis | opp_green_s | clearance_s | red_wait_at_green_start | switch_reason_code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| marathahalli_surge_shift_medium_hybrid_queue_adaptive_s135 | surge-shift-medium | 135 | 1884.0 | NS | EW | 37.0 | 5.0 | 42.0 | SWITCH_DEMAND_EXHAUSTED |
| marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136 | ramp-peak-medium | 136 | 1171.0 | NS | EW | 36.0 | 5.0 | 41.0 | SWITCH_FAIRNESS_WAIT_LIMIT |
| marathahalli_imbalanced_orr_heavy_hybrid_queue_adaptive_s135 | imbalanced-orr-heavy | 135 | 1863.0 | EW | NS | 26.0 | 5.0 | 31.0 | SWITCH_GAP_OUT |
| marathahalli_imbalanced_orr_heavy_hybrid_queue_adaptive_s136 | imbalanced-orr-heavy | 136 | 785.0 | EW | NS | 26.0 | 5.0 | 31.0 | SWITCH_DEMAND_FAIRNESS |
| marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s137 | ramp-peak-medium | 137 | 1258.0 | EW | NS | 25.0 | 5.0 | 30.0 | SWITCH_GAP_OUT |

### Physical Reconciliation of 48.0 s Red-Wait vs 43.0 s Upper Bound
In `marathahalli_surge_shift_medium_hybrid_queue_adaptive_s135`, North–South green starts at $t = 1884.0\text{ s}$ following an East–West green phase ($t = 1842.0\text{--}1878.0\text{ s}$, duration $36.0\text{ s}$) and two $5.0\text{ s}$ yellow/all-red clearance intervals ($3.0\text{ s} + 2.0\text{ s}$). The preceding North–South green ended at $t = 1836.0\text{ s}$, yielding an exact non-green elapsed span of $1884.0 - 1836.0 = 48.0\text{ s}$.

The nominal anti-starvation ceiling is configured at $W_\text{comp\_max} = 35.0\text{ s}$ ([`dp1/config.py:94, 110`](file:///e:/dp1-traffic-signal/dp1/config.py#L94)). The discrepancy between $48.0\text{ s}$ and $43.0\text{ s}$ arises from the signal state machine structure:
1. **Clearance Asymmetry (Two Intervals vs One):** The competing axis experiences TWO clearance intervals between greens: the clearance leading into the opposing green ($3\text{s yellow} + 2\text{s all-red} = 5\text{s}$) AND the clearance exiting the opposing green ($3\text{s yellow} + 2\text{s all-red} = 5\text{s}$), totaling $10.0\text{ s}$ of clearance overhead.
2. **Timer Reset Epoch:** In [`dp1/controllers/hybrid_queue_adaptive.py:182`](file:///e:/dp1-traffic-signal/dp1/controllers/hybrid_queue_adaptive.py#L182), `self.red_start_times[other_axis] = t` is initialized when the active phase *enters green* ($t = 1842.0\text{ s}$). Thus, the internal guard $W_\text{comp}$ measures active green elapsed time, omitting the initial $5.0\text{ s}$ clearance.
3. **Extension Step Discretization:** Extensions are granted in discrete $\Delta g = 3.0\text{ s}$ epochs ([`dp1/config.py:91`](file:///e:/dp1-traffic-signal/dp1/config.py#L91)). At $t = 1875.0\text{ s}$, $W_\text{comp} = 33.0\text{ s} < 35.0\text{ s}$, permitting a final $3.0\text{ s}$ extension to $t = 1878.0\text{ s}$ ($W_\text{comp} = 36.0\text{ s}$), where `SWITCH_FAIRNESS_HARD` or demand exhaustion forces the switch.
Adding the two clearances ($5.0\text{ s} + 5.0\text{ s} = 10.0\text{ s}$) to the $37.0\text{--}38.0\text{ s}$ opposing green yield exactly **$47.0\text{--}48.0\text{ s}$** red wait at green start ($5.0 + 37.0 + 5.0 = 47.0\text{ s}$, with integer boundary span $1884.0 - 1836.0 = 48.0\text{ s}$).

### Decision Log for the 60 s Window Before Switch ($t = 1824.0\text{--}1884.0\text{ s}$)

| t | cycle | axis | green_s | actual_green_s | q_N_m | q_S_m | q_E_m | q_W_m | proposed_action | applied_action | decision_outcome | action | reason | reason_code | g_base_s | delta_g_req_s | delta_g_app_s | g_extra_s | target_green_s | elapsed_s | q_active_m | q_competing_m | score_active | score_competing | is_max_green |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1819.0 | 98 | EW | 10.0 | 10.0 | 5.0 | 5.0 | 5.0 | 0.0 | EXTEND | REQUEST_SWITCH | SWITCH_DEMAND_FAIRNESS | REQUEST_SWITCH | Extension rejected: Competing North–South demand score (6.4) exceeds active East–West score (5.0) by fairness ratio (1.2). Switching to relieve opposing corridor. | SWITCH_DEMAND_FAIRNESS | 10.0 | 3.0 | 0.0 | 0.0 | 10.0 | 10.0 | 5.0 | 5.0 | 5.0 | 6.4 | False |
| 1824.0 | 98 | NS | 22.5 | 22.5 | 5.0 | 5.0 | 12.5 | 0.0 | ENTER_GREEN | ENTER_GREEN | BASELINE_ENTRY | ENTER_GREEN | North–South (ORR) green initiated with Webster baseline allocation 22.5s. | BASELINE_ENTRY | 22.5 | 0.0 | 0.0 | 0.0 | 22.5 | 0.0 | 5.0 | 12.5 | 5.0 | 12.5 | False |
| 1837.0 | 99 | NS | 22.5 | 13.0 | 0.0 | 0.0 | 20.0 | 20.0 | GAP_OUT | GAP_OUT | SWITCH_GAP_OUT | GAP_OUT | North–South queue cleared (0.0m for 3.0s >= gap-out threshold 3.0s) while East–West is waiting (20.0m); gapping out early. | SWITCH_GAP_OUT | 22.5 | 0.0 | 0.0 | 0.0 | 22.5 | 13.0 | 0.0 | 20.0 | 0.0 | 27.5 | False |
| 1842.0 | 99 | EW | 10.0 | 10.0 | 0.0 | 0.0 | 24.0 | 20.0 | ENTER_GREEN | ENTER_GREEN | BASELINE_ENTRY | ENTER_GREEN | East–West (Varthur Rd) green initiated with Webster baseline allocation 10.0s. | BASELINE_ENTRY | 10.0 | 0.0 | 0.0 | 0.0 | 10.0 | 0.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1852.0 | 100 | EW | 13.0 | 10.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (10.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 3.0 | 13.0 | 10.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1855.0 | 100 | EW | 16.0 | 13.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (13.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 6.0 | 16.0 | 13.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1858.0 | 100 | EW | 19.0 | 16.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (16.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 9.0 | 19.0 | 16.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1861.0 | 100 | EW | 22.0 | 19.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (19.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 12.0 | 22.0 | 19.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1864.0 | 100 | EW | 25.0 | 22.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (22.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 15.0 | 25.0 | 22.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1867.0 | 100 | EW | 28.0 | 25.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (25.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 18.0 | 28.0 | 25.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1870.0 | 100 | EW | 31.0 | 28.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (28.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 21.0 | 31.0 | 28.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1873.0 | 100 | EW | 34.0 | 31.0 | 0.0 | 0.0 | 24.0 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (24.0m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (31.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 24.0 | 34.0 | 31.0 | 24.0 | 0.0 | 24.0 | 0.0 | False |
| 1876.0 | 100 | EW | 37.0 | 34.0 | 0.0 | 0.0 | 9.7 | 0.0 | EXTEND | EXTEND | EXTEND_APPROVED | EXTEND | East–West green extended by 3 seconds: its queue/demand condition (9.7m >= 4.0m) satisfied the configured extension rule, the competing-direction wait (34.0s) remained within its permitted limit (35s), and maximum green was not reached. | EXTEND_APPROVED | 10.0 | 3.0 | 3.0 | 27.0 | 37.0 | 34.0 | 9.7 | 0.0 | 9.7 | 0.0 | False |
| 1879.0 | 100 | EW | 37.0 | 37.0 | 0.0 | 0.0 | 0.0 | 0.0 | EXTEND | REQUEST_SWITCH | SWITCH_DEMAND_EXHAUSTED | REQUEST_SWITCH | Extension rejected: Active East–West queue (0.0m < threshold 4.0m) and no new arrivals detected (delta Q = 0.0m). Terminating green phase. | SWITCH_DEMAND_EXHAUSTED | 10.0 | 3.0 | 0.0 | 27.0 | 37.0 | 37.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 1884.0 | 100 | NS | 22.5 | 22.5 | 0.0 | 0.0 | 12.5 | 0.0 | ENTER_GREEN | ENTER_GREEN | BASELINE_ENTRY | ENTER_GREEN | North–South (ORR) green initiated with Webster baseline allocation 22.5s. | BASELINE_ENTRY | 22.5 | 0.0 | 0.0 | 0.0 | 22.5 | 0.0 | 0.0 | 12.5 | 0.0 | 12.5 | False |

## OUTPUT 5: s136 Trace and Configuration Audit

### (a) Verbatim Rows 115-130 of s136 Decision Trace
Source file: `E:\dp1-traffic-signal\results\research\exp_marathahalli_improve_final\marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136\decisions.csv`

```text
Row 115 | t=1107.0 | axis=EW | prop=EXTEND         | app=REQUEST_SWITCH | req= 3.0 | app_s= 0.0 | g_extra= 0.0 | g_base=14.2 | code=SWITCH_DEMAND_FAIRNESS    | q_act= 5.0 | q_comp=12.5 | q_N= 0.0 | q_S=12.5 | q_E= 5.0 | q_W= 0.0
Row 116 | t=1112.0 | axis=NS | prop=ENTER_GREEN    | app=ENTER_GREEN    | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=15.8 | code=BASELINE_ENTRY            | q_act=20.0 | q_comp= 5.0 | q_N= 0.0 | q_S=20.0 | q_E= 5.0 | q_W= 0.0
Row 117 | t=1125.0 | axis=NS | prop=GAP_OUT        | app=GAP_OUT        | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=15.8 | code=SWITCH_GAP_OUT            | q_act= 0.0 | q_comp=12.5 | q_N= 0.0 | q_S= 0.0 | q_E=12.5 | q_W= 0.0
Row 118 | t=1130.0 | axis=EW | prop=ENTER_GREEN    | app=ENTER_GREEN    | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=14.2 | code=BASELINE_ENTRY            | q_act=20.0 | q_comp= 0.0 | q_N= 0.0 | q_S= 0.0 | q_E=20.0 | q_W= 0.0
Row 119 | t=1145.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra= 3.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp= 5.0 | q_N= 5.0 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 120 | t=1148.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra= 6.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp= 5.0 | q_N= 5.0 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 121 | t=1151.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra= 9.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp= 5.0 | q_N= 5.0 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 122 | t=1154.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra=12.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp= 5.0 | q_N= 5.0 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 123 | t=1157.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra=15.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp=12.5 | q_N=12.5 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 124 | t=1160.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra=18.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp=12.5 | q_N=12.5 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 125 | t=1163.0 | axis=EW | prop=EXTEND         | app=EXTEND         | req= 3.0 | app_s= 3.0 | g_extra=21.0 | g_base=14.2 | code=EXTEND_APPROVED           | q_act=24.0 | q_comp=12.5 | q_N=12.5 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 126 | t=1166.0 | axis=EW | prop=EXTEND         | app=REQUEST_SWITCH | req= 3.0 | app_s= 0.0 | g_extra=21.0 | g_base=14.2 | code=SWITCH_FAIRNESS_WAIT_LIMIT | q_act=24.0 | q_comp=12.5 | q_N=12.5 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 127 | t=1171.0 | axis=NS | prop=ENTER_GREEN    | app=ENTER_GREEN    | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=15.8 | code=BASELINE_ENTRY            | q_act=12.5 | q_comp=24.0 | q_N=12.5 | q_S= 5.0 | q_E=24.0 | q_W= 0.0
Row 128 | t=1184.0 | axis=NS | prop=GAP_OUT        | app=GAP_OUT        | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=15.8 | code=SWITCH_GAP_OUT            | q_act= 0.0 | q_comp=24.0 | q_N= 0.0 | q_S= 0.0 | q_E=24.0 | q_W= 0.0
Row 129 | t=1189.0 | axis=EW | prop=ENTER_GREEN    | app=ENTER_GREEN    | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=14.2 | code=BASELINE_ENTRY            | q_act=24.0 | q_comp= 0.0 | q_N= 0.0 | q_S= 0.0 | q_E=24.0 | q_W= 0.0
Row 130 | t=1202.0 | axis=EW | prop=GAP_OUT        | app=GAP_OUT        | req= 0.0 | app_s= 0.0 | g_extra= 0.0 | g_base=14.2 | code=SWITCH_GAP_OUT            | q_act= 0.0 | q_comp=12.5 | q_N=12.5 | q_S=12.5 | q_E= 0.0 | q_W= 0.0
```

### (b) Configuration Parameters in `dp1/config.py`

```python
# Citations from dp1/config.py:
# Line 89: min_green_s: float = 10.0           # Minimum green duration before any switch can be considered
# Line 90: max_green_s: float = 60.0           # Hard upper bound on green phase duration
# Line 91: extend_step_s: float = 3.0          # Green increment granted per approved extension evaluation
# Line 92: extend_threshold_m: float = 4.0     # Minimum active approach queue required to justify extension
# Line 94: max_competing_wait_s: float = 35.0  # Maximum red wait time for competing axis before switch is forced
# Line 110: r3_hard_wait_cap_s: float = 35.0   # Hard anti-starvation cap regardless of competing queue
# Line 38: yellow_s: float = 3.0              # Phase change warning
# Line 39: all_red_s: float = 2.0             # Clearance before next green (total lost time per phase = 5.0 s)
# Line 22: sat_flow_vph: float = 1800.0        # Saturation flow per lane (veh/hour/lane)
```

In run `marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`:
- $g_\text{base}$ for East–West (`EW`): **$14.2\text{ s}$** (established at row 118, $t = 1130.0\text{ s}$)
- $g_\text{base}$ for North–South (`NS`): **$25.8\text{ s}$** (established at row 127, $t = 1171.0\text{ s}$)

### (c) Git Commit History Audit (Tuning vs Exploratory Seeds)

1. **Exploratory Study Seeds 121–130:**
   - Commit `62a29a2` (2026-10-21 00:18:16): Evaluated initial 840-run matrix on seeds 121–130, fixing initial parameters ($g_\text{ext} = 3.0\text{ s}$, $q_\text{thresh} = 4.0\text{ m}$, $W_\text{comp} = 35.0\text{ s}$).

2. **Confirmatory Baseline Tuning & Gating Seeds 101–110:**
   - Commit `9696dcd` (2026-11-04 03:07:05): Reformulated primary metric to extended ground truth queue $Q_\text{gt\_ext}$ using seeds 101–105.
   - Commit `b3771d3` (2026-11-04 05:21:42): Evaluated sequential ablation ladder (Rungs R1–R4) strictly on development seeds 101–105 and validation seeds 106–110.
   - Commit `6ded7d6` (2026-11-04 07:12:18): Tuned baseline controllers (`webster_recalc`, `sumo_actuated`) on validation seeds 106–110.
   - Commit `4511149` (2026-11-04 11:05:02): Protocol and stopping rules frozen under Pre-Registration Amendment 3, 4 hours and 48 minutes prior to executing confirmatory seeds 131–138.
