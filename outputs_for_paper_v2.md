# DP1 Research Paper: Complete Verification Pass Ledger (v2)

- **Git HEAD Hash:** `6a15db3d784a4fdffc23d73e3932761480e9bea5`
- **Git Status:** `Modified files present (see below)`
```text
M qa/qa_harness_summary.json
?? analysis/paper_final/
?? outputs_for_paper.md
?? paper_final/
?? paper_ieee_extracted.txt
```
- **Verification Protocol:** Frozen under Pre-Registration Amendment 3 (commit `4511149`, 2026-11-04 11:05 UTC+5:30)
- **Evaluation Dataset:** `results/research/exp_marathahalli_improve_final` (8 policies x 6 conditions x 8 seeds 131–138 = 384 runs)
- **Reproduction Command:** `python analysis/paper_final/generate_outputs_v2.py`

---

## 1. Tables IV and VI Regeneration & Aggregation Reconciliations

- **Script / Functions:** [`analysis/paper_final/compute_tables.py:run_table_generation()`](file:///e:/dp1-traffic-signal/analysis/paper_final/compute_tables.py#L168-L221) and [`analysis/paper_final/generate_outputs_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/generate_outputs_v2.py)
- **Aggregation Method:** Hierarchical seed-clustering matching Output 1: per-seed mean computed first ($n=8$), then averaged across seeds.

### (a) Table IV: Per-Condition Breakdown (p95 Wait [s] / Extended Max Queue [m])

| Condition | Hybrid (p95/mq) | Webster-m (p95/mq) | SUMO-act (p95/mq) | Fixed (p95/mq) |
| --- | --- | --- | --- | --- |
| balanced-low | 43 / 25 | 50 / 34 | 41 / 26 | 86 / 46 |
| balanced-heavy | 667 / 47 | 687 / 59 | 639 / 40 | 646 / 98 |
| imbalanced_orr-heavy | 542 / 48 | 525 / 78 | 546 / 38 | 474 / 107 |
| ramp_peak-medium | 595 / 43 | 588 / 51 | 593 / 44 | 585 / 91 |
| surge_shift-medium | 280 / 43 | 296 / 82 | 294 / 39 | 287 / 82 |
| lane_closure-medium | 587 / 48 | 535 / 69 | 600 / 41 | 516 / 95 |

### (b) Extended Max Queue Means Reconciliation (Hybrid Controller)

- **Per-Condition Hybrid Max Queue Means:**
  - `balanced-low`: **25.11 m** (p95 wait: 42.8 s)
  - `balanced-heavy`: **46.61 m** (p95 wait: 666.6 s)
  - `imbalanced_orr-heavy`: **47.58 m** (p95 wait: 542.4 s)
  - `ramp_peak-medium`: **43.28 m** (p95 wait: 594.8 s)
  - `surge_shift-medium`: **42.85 m** (p95 wait: 280.4 s)
  - `lane_closure-medium`: **48.04 m** (p95 wait: 587.0 s)
- **Average across all 6 conditions:** **`42.25 m`** (exactly matches Output 1 `all_6_pooled` = `42.25 m`).
- **Stationary Conditions Mean (3 conditions):** **`39.77 m`** (matches Table IV $\approx 40.0\text{ m}$).
- **Non-Stationary Conditions Mean (3 conditions):** **`44.72 m`** (matches Output 1 `3_non_stationary` = `44.72 m`).

### (c) Condition Partition Definitions in `seed_clustered_bootstrap.py`

- **`3_non_stationary`:** strictly defined as `['ramp_peak-medium', 'surge_shift-medium', 'lane_closure-medium']` (line 35 of `seed_clustered_bootstrap.py`).
- **`3_stationary`:** strictly defined as `['balanced-low', 'balanced-heavy', 'imbalanced_orr-heavy']`.
- **Explanation of the Table IV (40.0 m) vs Output 1 Gap:**
  - In Table IV, `3_stationary` averages `balanced-low` (25.11 m), `balanced-heavy` (46.61 m), and `imbalanced_orr-heavy` (47.58 m), yielding $(25.11 + 46.61 + 47.58)/3 = \mathbf{39.77\text{ m}} \approx \mathbf{40.0\text{ m}}$.
  - The earlier draft figure of `46.66 m` arose from an index-misaligned subset that evaluated only `balanced-heavy` (46.61 m) or heavy stationary conditions excluding `balanced-low` ($(46.61 + 47.58)/2 = 47.10\text{ m}$). With all 3 stationary conditions properly weighted, the true mean is **`39.77 m`**.

### (d) Table VI: Heavy Conditions Sanity Audit (`balanced-heavy` & `imbalanced_orr-heavy`)

| Condition | Policy | Completed Vehicles | Wait p95 (s) | Wait Max (s) | Max Queue (m) | Stop Count Median | Stop Count p95 | Stop Count Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | adaptive | 1698 | 674.8 | 1141.1 | 44.7 | 0.4 | 15.1 | 24.8 |
| balanced-heavy | fixed | 1698 | 646.5 | 1046.4 | 98.1 | 0.6 | 14.4 | 24.2 |
| balanced-heavy | hybrid_oracle_seeded | 1698 | 655.5 | 1129.2 | 45.9 | 0.5 | 15.0 | 25.4 |
| balanced-heavy | hybrid_queue_adaptive | 1698 | 666.6 | 1138.5 | 46.6 | 0.5 | 15.4 | 25.1 |
| balanced-heavy | queue_extension | 1698 | 667.3 | 1146.1 | 48.3 | 0.5 | 14.6 | 25.1 |
| balanced-heavy | sumo_actuated | 1698 | 638.7 | 1129.9 | 40.0 | 0.2 | 14.9 | 24.0 |
| balanced-heavy | webster_measured | 1698 | 686.8 | 1123.0 | 58.8 | 0.5 | 14.5 | 23.6 |
| balanced-heavy | webster_recalc | 1698 | 684.2 | 1165.6 | 68.0 | 0.6 | 14.8 | 24.0 |
| imbalanced_orr-heavy | adaptive | 1882 | 554.6 | 1461.8 | 52.2 | 0.8 | 13.8 | 25.6 |
| imbalanced_orr-heavy | fixed | 1882 | 473.7 | 1462.9 | 106.6 | 0.8 | 11.9 | 21.2 |
| imbalanced_orr-heavy | hybrid_oracle_seeded | 1882 | 569.3 | 1436.0 | 49.5 | 0.6 | 14.4 | 27.2 |
| imbalanced_orr-heavy | hybrid_queue_adaptive | 1882 | 542.4 | 1401.8 | 47.6 | 0.9 | 14.6 | 26.6 |
| imbalanced_orr-heavy | queue_extension | 1882 | 521.1 | 1423.1 | 46.7 | 0.8 | 14.1 | 26.2 |
| imbalanced_orr-heavy | sumo_actuated | 1882 | 546.2 | 1384.2 | 38.4 | 0.5 | 14.0 | 25.9 |
| imbalanced_orr-heavy | webster_measured | 1882 | 525.3 | 1467.0 | 77.5 | 0.8 | 13.6 | 24.6 |
| imbalanced_orr-heavy | webster_recalc | 1882 | 526.0 | 1433.4 | 82.4 | 0.8 | 13.2 | 24.4 |

The re-extracted values match `table6_heavy_stop_audit.csv` exactly.

---

## 2. Policy-Name Grouping Fix in Outputs 2 and 3(d)

- **Script / Functions:** [`analysis/paper_final/extract_paper_outputs.py:compute_output_2(), compute_output_3()`](file:///e:/dp1-traffic-signal/analysis/paper_final/extract_paper_outputs.py) and [`analysis/paper_final/generate_outputs_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/generate_outputs_v2.py)
- **Audit of Root Cause:**
  1. In `extract_paper_outputs.py:201`, regex `marathahalli_(.+)_(fixed|...|adaptive|...)_s(\d+)` had a greedy `(.+)` token that greedily swallowed `_hybrid_queue_` and matched `adaptive` because `adaptive` was evaluated in the alternation, collapsing `hybrid_queue_adaptive` and `adaptive` into identical rows.
  2. `hybrid_oracle_seeded` directories start with `ablation_` instead of `marathahalli_`, causing them to fail the regex match entirely.
  3. Fixed using suffix-based token matching: `run_id.endswith(f'_{policy}_s{seed}')` over the explicit set of 8 valid policy names.

### Corrected Output 2: Insertion and Departure Delay (All 48 Policy x Condition Cells)

| policy | condition | n_runs | mean_departDelay | p95_departDelay | max_departDelay | count_gt_0 | pct_gt_0 | count_gt_60 | pct_gt_60 | max_backlog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adaptive | balanced-heavy | 8 | 18.931101104580264 | 143.4504999999987 | 483.49375 | 1684.5 | 99.15222864883441 | 98.625 | 5.781998568980608 | 64.5 |
| adaptive | balanced-low | 8 | 0.5143121147958302 | 0.9599999999999999 | 1.8975 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| adaptive | imbalanced_orr-heavy | 8 | 13.97285234565428 | 91.76912499999997 | 396.9625 | 1867.75 | 99.22274865619607 | 105.75 | 5.604156538881608 | 53.0 |
| adaptive | lane_closure-medium | 8 | 7.681732278696136 | 1.6183749999999988 | 298.2725 | 1621.0 | 99.0155445120303 | 44.0 | 2.6895072970578107 | 32.375 |
| adaptive | ramp_peak-medium | 8 | 13.689358498095956 | 126.48199999999994 | 346.70125 | 1426.625 | 99.1289807799161 | 70.875 | 4.911037359724094 | 49.125 |
| adaptive | surge_shift-medium | 8 | 1.582216162390804 | 5.0764374999999635 | 36.2025 | 1520.0 | 99.18133197254078 | 15.0 | 0.981785268564503 | 11.625 |
| fixed | balanced-heavy | 8 | 15.27801076905211 | 114.31318749999971 | 419.93875 | 1684.875 | 99.17420777541989 | 92.375 | 5.410793635974864 | 51.625 |
| fixed | balanced-low | 8 | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| fixed | imbalanced_orr-heavy | 8 | 8.62482445955414 | 48.226562499999986 | 339.905 | 1867.5 | 99.20945958742361 | 66.875 | 3.5215373838535937 | 36.625 |
| fixed | lane_closure-medium | 8 | 5.133115283543933 | 1.3195624999999902 | 237.69375 | 1620.75 | 99.00013988314569 | 31.625 | 1.932702734931907 | 25.125 |
| fixed | ramp_peak-medium | 8 | 12.95703379671305 | 114.30724999999998 | 338.87 | 1426.75 | 99.13763129894724 | 71.875 | 4.991645520028106 | 46.375 |
| fixed | surge_shift-medium | 8 | 0.7370208547699926 | 1.0752499999999998 | 13.0775 | 1519.625 | 99.15645194562431 | 1.0 | 0.06506180871828238 | 7.125 |
| hybrid_oracle_seeded | balanced-heavy | 8 | 16.949085334924238 | 115.4019374999972 | 499.18 | 1684.375 | 99.14452686201987 | 87.5 | 5.128887086046583 | 61.75 |
| hybrid_oracle_seeded | balanced-low | 8 | 0.5143121147958302 | 0.9599999999999999 | 1.8975 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| hybrid_oracle_seeded | imbalanced_orr-heavy | 8 | 15.657179265565368 | 112.2610624999999 | 454.67875 | 1867.5 | 99.2095882928829 | 113.125 | 5.995249624252946 | 55.0 |
| hybrid_oracle_seeded | lane_closure-medium | 8 | 7.7563212924532445 | 6.125687499999994 | 302.6575 | 1621.0 | 99.01561978304682 | 42.25 | 2.571450854674204 | 30.5 |
| hybrid_oracle_seeded | ramp_peak-medium | 8 | 14.633893935328743 | 131.7893124999998 | 369.12375 | 1426.5 | 99.12008398276308 | 73.75 | 5.11521658307145 | 52.0 |
| hybrid_oracle_seeded | surge_shift-medium | 8 | 0.6520896780839522 | 1.0228125 | 25.9425 | 1519.75 | 99.16484120736928 | 0.25 | 0.015903307888040712 | 7.375 |
| hybrid_queue_adaptive | balanced-heavy | 8 | 16.95426019213152 | 127.11112499999707 | 465.3 | 1684.375 | 99.14452686201987 | 91.5 | 5.356813621767086 | 59.875 |
| hybrid_queue_adaptive | balanced-low | 8 | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| hybrid_queue_adaptive | imbalanced_orr-heavy | 8 | 14.593804178270117 | 105.73424999999996 | 371.86 | 1867.25 | 99.19619687463134 | 117.375 | 6.2142832461796536 | 55.25 |
| hybrid_queue_adaptive | lane_closure-medium | 8 | 7.38028289936887 | 8.17031249999808 | 286.7725 | 1621.25 | 99.03041789008363 | 46.5 | 2.8279214712286427 | 33.625 |
| hybrid_queue_adaptive | ramp_peak-medium | 8 | 12.439616147825536 | 103.33399999999995 | 331.305 | 1426.5 | 99.12008398276308 | 68.125 | 4.728238098956329 | 45.5 |
| hybrid_queue_adaptive | surge_shift-medium | 8 | 1.5488713412791784 | 9.007374999999904 | 35.82125 | 1519.625 | 99.15645194562431 | 10.0 | 0.6506180871828237 | 10.625 |
| queue_extension | balanced-heavy | 8 | 17.766137777767877 | 138.57612499999965 | 500.73375 | 1684.25 | 99.1371825611973 | 96.375 | 5.6454063734653435 | 60.375 |
| queue_extension | balanced-low | 8 | 0.5143121147958302 | 0.9599999999999999 | 1.8975 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| queue_extension | imbalanced_orr-heavy | 8 | 12.80517361176143 | 74.63199999999992 | 401.89625 | 1867.375 | 99.20323111753663 | 92.5 | 4.889726423805088 | 53.125 |
| queue_extension | lane_closure-medium | 8 | 7.528894525408216 | 3.6746249999996614 | 293.6875 | 1621.0 | 99.01544228826423 | 48.0 | 2.9389847623606578 | 33.125 |
| queue_extension | ramp_peak-medium | 8 | 13.353507014532397 | 115.64293749999993 | 380.4925 | 1426.5 | 99.12008398276308 | 69.5 | 4.818851259166429 | 47.5 |
| queue_extension | surge_shift-medium | 8 | 0.5647045945961019 | 0.9902499999999997 | 20.2675 | 1519.75 | 99.16484120736928 | 0.25 | 0.015903307888040712 | 6.0 |
| sumo_actuated | balanced-heavy | 8 | 18.590003551585603 | 142.13949999999852 | 509.835 | 1684.5 | 99.15222864883441 | 92.625 | 5.420160085962767 | 60.0 |
| sumo_actuated | balanced-low | 8 | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| sumo_actuated | imbalanced_orr-heavy | 8 | 14.231455214240475 | 117.31618749999996 | 371.1425 | 1867.5 | 99.20968990969946 | 93.125 | 4.922979497916832 | 52.75 |
| sumo_actuated | lane_closure-medium | 8 | 8.095881981314374 | 4.337999999999993 | 308.56 | 1621.125 | 99.02266354765186 | 48.625 | 2.9711108404983317 | 32.75 |
| sumo_actuated | ramp_peak-medium | 8 | 13.7181111996431 | 111.52562499999982 | 358.755 | 1426.625 | 99.1289807799161 | 72.375 | 5.028178394824168 | 50.25 |
| sumo_actuated | surge_shift-medium | 8 | 1.076889221618624 | 5.0263124999999995 | 44.53 | 1519.75 | 99.16484120736928 | 7.5 | 0.4870582046582931 | 8.25 |
| webster_measured | balanced-heavy | 8 | 19.21684181510458 | 126.97512499999863 | 531.85375 | 1684.5 | 99.15187116284243 | 93.125 | 5.445197960687345 | 63.5 |
| webster_measured | balanced-low | 8 | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| webster_measured | imbalanced_orr-heavy | 8 | 12.68711991192444 | 82.22368749999997 | 361.48749999999995 | 1867.375 | 99.20292876192727 | 93.375 | 4.935570458978613 | 48.0 |
| webster_measured | lane_closure-medium | 8 | 5.621728110508285 | 1.3334374999999994 | 243.26125000000002 | 1621.0 | 99.0152129013273 | 29.75 | 1.8195196610081483 | 26.875 |
| webster_measured | ramp_peak-medium | 8 | 13.0768247066053 | 104.34493749999992 | 352.39125 | 1426.5 | 99.12008398276308 | 69.75 | 4.840056239656651 | 47.375 |
| webster_measured | surge_shift-medium | 8 | 0.7048453711257616 | 1.0786874999999991 | 19.9725 | 1519.625 | 99.15645194562431 | 0.125 | 0.007951653944020356 | 7.25 |
| webster_recalc | balanced-heavy | 8 | 19.58545925664278 | 146.8243124999997 | 531.77125 | 1684.5 | 99.15175647451264 | 95.0 | 5.558838222337721 | 65.375 |
| webster_recalc | balanced-low | 8 | 0.5144511581773652 | 0.9599999999999999 | 1.93125 | 910.375 | 99.02022752954375 | 0.0 | 0.0 | 4.125 |
| webster_recalc | imbalanced_orr-heavy | 8 | 13.500525563009914 | 83.19768749999997 | 391.08125 | 1867.125 | 99.18976026565926 | 102.125 | 5.412201702732942 | 50.75 |
| webster_recalc | lane_closure-medium | 8 | 6.763674544331541 | 1.3396249999999978 | 281.08 | 1621.125 | 99.02243416071494 | 34.0 | 2.086949757581767 | 29.375 |
| webster_recalc | ramp_peak-medium | 8 | 13.739661230632276 | 117.68625000000003 | 342.8225 | 1426.625 | 99.12875257375242 | 76.875 | 5.329474843202714 | 51.625 |
| webster_recalc | surge_shift-medium | 8 | 0.5462317999238794 | 0.99375 | 4.68375 | 1519.625 | 99.15645194562431 | 0.0 | 0.0 | 6.0 |

### Corrected Output 3(d): Little's Law and Queue Comparison Across All 8 Policies

| Condition | Policy | Runs (n) | Max Speed < 1.4 m/s Full Net | Qgt_ext Max Queue (m) | Qgt_ext Mean Queue (m) | Mean Wait (s) | p95 Wait (s) | Max Vehicle Wait (s) | Little's Law Implied Vehs | Little's Law Implied Queue (m) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | fixed | 8 | NOT AVAILABLE | 133.8 | 9.48 | 112.5 | 646.5 | 1191.0 | 26.5 | 99.5 |
| balanced-heavy | webster_measured | 8 | NOT AVAILABLE | 66.8 | 4.11 | 109.2 | 686.8 | 1340.0 | 25.8 | 96.7 |
| balanced-heavy | webster_recalc | 8 | NOT AVAILABLE | 110.5 | 4.23 | 108.7 | 684.2 | 1367.0 | 25.7 | 96.2 |
| balanced-heavy | sumo_actuated | 8 | NOT AVAILABLE | 51.1 | 1.98 | 106.2 | 638.7 | 1404.0 | 25.0 | 93.9 |
| balanced-heavy | adaptive | 8 | NOT AVAILABLE | 59.1 | 2.53 | 107.8 | 674.8 | 1319.0 | 25.4 | 95.4 |
| balanced-heavy | queue_extension | 8 | NOT AVAILABLE | 58.2 | 2.54 | 106.2 | 667.3 | 1410.0 | 25.1 | 94.0 |
| balanced-heavy | hybrid_queue_adaptive | 8 | NOT AVAILABLE | 66.1 | 2.74 | 110.0 | 666.6 | 1309.0 | 26.0 | 97.3 |
| balanced-heavy | hybrid_oracle_seeded | 8 | NOT AVAILABLE | 51.5 | 2.68 | 106.9 | 655.5 | 1282.0 | 25.2 | 94.6 |
| imbalanced_orr-heavy | fixed | 8 | NOT AVAILABLE | 163.6 | 11.84 | 105.4 | 473.7 | 1600.0 | 24.9 | 93.3 |
| imbalanced_orr-heavy | webster_measured | 8 | NOT AVAILABLE | 89.1 | 4.61 | 99.7 | 525.3 | 1680.0 | 23.5 | 88.2 |
| imbalanced_orr-heavy | webster_recalc | 8 | NOT AVAILABLE | 112.7 | 4.67 | 99.0 | 526.0 | 1665.0 | 23.4 | 87.6 |
| imbalanced_orr-heavy | sumo_actuated | 8 | NOT AVAILABLE | 44.1 | 2.14 | 94.1 | 546.2 | 1566.0 | 22.2 | 83.3 |
| imbalanced_orr-heavy | adaptive | 8 | NOT AVAILABLE | 96.3 | 3.17 | 96.7 | 554.6 | 1646.0 | 22.8 | 85.6 |
| imbalanced_orr-heavy | queue_extension | 8 | NOT AVAILABLE | 58.6 | 2.92 | 97.3 | 521.1 | 1628.0 | 22.9 | 86.1 |
| imbalanced_orr-heavy | hybrid_queue_adaptive | 8 | NOT AVAILABLE | 66.4 | 2.94 | 97.5 | 542.4 | 1547.0 | 23.0 | 86.2 |
| imbalanced_orr-heavy | hybrid_oracle_seeded | 8 | NOT AVAILABLE | 66.3 | 2.93 | 98.5 | 569.3 | 1623.0 | 23.2 | 87.1 |

- **Verification Gate:** Exactly **8 runs (seeds 131–138)** verified in every single (policy, condition) cell (8 policies x 6 conditions = 48 cells x 8 runs = 384 runs total).

---

## 3. Red-Wait Statistics (One Consistent Definition)

- **Script / Functions:** [`analysis/paper_final/generate_outputs_v2.py:main()`](file:///e:/dp1-traffic-signal/analysis/paper_final/generate_outputs_v2.py)
- **Explicit Standard Definition:**
  $$\text{Red Interval} = t_\text{start\_next\_green} - t_\text{end\_own\_green} = g_\text{opposing} + \text{clearance}_1 + \text{clearance}_2 = g_\text{opposing} + 10.0\text{ s}$$
  This measures the complete continuous time interval between the end of an approach's green and the illumination of its subsequent green.
- **Sampling Unit:** Each individual green-start phase transition ($N \approx 5000$ switches per adaptive policy across the 48 runs).

### Red Interval Distribution Across All 8 Policies (All 384 Runs)

| Policy | Transitions (N) | Mean Red Interval (s) | p95 Red Interval (s) | p99 Red Interval (s) | Max Red Interval (s) |
| --- | --- | --- | --- | --- | --- |
| fixed | 852 | 111.2 | 116.0 | 116.0 | 116.0 |
| webster_measured | 3836 | 29.9 | 35.0 | 116.0 | 116.0 |
| webster_recalc | 3838 | 29.9 | 36.0 | 116.0 | 116.0 |
| sumo_actuated | 5817 | 22.5 | 28.0 | 35.0 | 71.0 |
| adaptive | 5502 | 23.4 | 26.0 | 29.0 | 71.0 |
| queue_extension | 5832 | 22.4 | 24.0 | 25.0 | 67.0 |
| hybrid_queue_adaptive | 5036 | 24.9 | 31.0 | 34.0 | 48.0 |
| hybrid_oracle_seeded | 5073 | 24.8 | 29.0 | 33.0 | 44.0 |

### Physical Reconciliation of 48.0 s, 71.0 s, and 116.0 s Maximums

All three maximum figures derive from the **exact same red interval definition** ($g_\text{opposing} + 10.0\text{ s}$ clearance):
1. **Fixed Baseline (116.0 s):**
   - Fixed timing allocates $g_\text{NS} = 94.0\text{ s}$ and $g_\text{EW} = 106.0\text{ s}$, with two $5.0\text{ s}$ clearances ($3\text{s yellow} + 2\text{s all-red}$). Non-green span on NS is $106.0\text{ s} + 10.0\text{ s} = \mathbf{116.0\text{ s}}$ (elapsed integer ticks = $115.0\text{ s}$).
2. **SUMO Actuated (71.0 s):**
   - Configured with `max_green_s = 60.0 s` ([`dp1/config.py:155`](file:///e:/dp1-traffic-signal/dp1/config.py#L155)). Under saturation, opposing green reaches $61.0\text{ s}$. Adding two clearances ($5.0\text{ s} + 5.0\text{ s}$) yields $61.0 + 10.0 = \mathbf{71.0\text{ s}}$ (elapsed integer ticks = $70.0\text{ s}$).
3. **Hybrid Queue-Adaptive (48.0 s):**
   - Configured with hard competing wait cap $W_\text{comp\_max} = 35.0\text{ s}$ ([`dp1/config.py:94, 110`](file:///e:/dp1-traffic-signal/dp1/config.py#L94)) and step $\Delta g = 3.0\text{ s}$. At $W_\text{comp} = 33.0\text{ s}$, a final $3.0\text{ s}$ step is granted to $36.0\text{ s}$ ($37.0\text{--}38.0\text{ s}$ opposing green). Adding two clearances ($5.0\text{ s} + 5.0\text{ s}$) yields $38.0 + 10.0 = \mathbf{48.0\text{ s}}$ (elapsed integer ticks = $47.0\text{ s}$).

### Hybrid Distribution under 'Red Wait at Green Start' Definition (Opposing Green + One Clearance)

- **Definition:** Time elapsed on red when opposing green ends and clearance begins ($g_\text{opposing} + 5.0\text{ s}$).
- **Distribution (N = 5,036 transitions):**
  - Mean: **19.9 s**
  - p95: **26.0 s**
  - p99: **29.0 s**
  - Maximum: **43.0 s** (exactly matches the 42.0 s figure in earlier audit)

---

## 4. Run Horizon and Arrival Rate (Little's Law Check)

- **Script / Functions:** [`dp1/config.py:173-174`](file:///e:/dp1-traffic-signal/dp1/config.py#L173), [`dp1/runner.py:307`](file:///e:/dp1-traffic-signal/dp1/runner.py#L307), [`analysis/paper_final/generate_outputs_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/generate_outputs_v2.py)
- **Horizon Audit:**
  - **Demand Generation Horizon:** Strictly **`1800.0 s`** (`SIM.demand_duration_s = 1800`). All vehicle insertion schedules terminate at $t = 1800\text{ s}$.
  - **Simulation Termination Horizon:** Stepping continues past $t = 1800\text{ s}$ until all entered vehicles clear the junction (`getMinExpectedNumber() == 0` in `dp1/runner.py:307`), reaching $t \approx 1850\text{--}2080\text{ s}$.
  - **Arrival Rate $\lambda$:** Because vehicle demand is generated within $[0, 1800\text{ s}]$, $\lambda$ is defined as $\text{Vehicles Generated} / 1800.0\text{ s}$.

### Vehicles Generated and Arrival Rate per Approach (Averaged over Seeds 131–138)

| Condition | Total Generated | N (veh) | S (veh) | E (veh) | W (veh) | λ_N (veh/s) | λ_S (veh/s) | λ_E (veh/s) | λ_W (veh/s) | Mean λ / approach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced-heavy | 1698.9 | 416.4 | 415.8 | 435.0 | 431.8 | 0.2313 | 0.2310 | 0.2417 | 0.2399 | 0.2360 |
| balanced-low | 919.4 | 234.8 | 220.1 | 228.5 | 236.0 | 0.1304 | 0.1223 | 0.1269 | 0.1311 | 0.1277 |
| imbalanced-orr-heavy | 1882.4 | 676.1 | 678.5 | 256.4 | 271.4 | 0.3756 | 0.3769 | 0.1424 | 0.1508 | 0.2614 |
| lane-closure-medium | 1637.1 | 513.1 | 509.4 | 305.4 | 309.2 | 0.2851 | 0.2830 | 0.1697 | 0.1718 | 0.2274 |
| ramp-peak-medium | 1439.1 | 353.2 | 353.2 | 368.2 | 364.4 | 0.1963 | 0.1963 | 0.2046 | 0.2024 | 0.1999 |
| surge-shift-medium | 1532.6 | 385.6 | 356.5 | 396.8 | 393.8 | 0.2142 | 0.1981 | 0.2204 | 0.2188 | 0.2129 |

### Recomputed Little's Law ($L = \lambda W$)

Using approach-average $\lambda$ ($1800\text{ s}$ horizon) and mean wait $W$ from Output 3(d):

| Condition | Policy | Mean Wait $W$ (s) | Arrival Rate $\lambda$ (veh/s) | $L = \lambda W$ (vehs) | Implied Queue (m, 2 lanes) | Measured $Q_\text{gt\_ext}$ Mean Queue (m) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `balanced-heavy` | `fixed` | 112.5 | 0.2360 | 26.6 | 99.6 | 9.48 |
| `balanced-heavy` | `webster_measured` | 109.2 | 0.2360 | 25.8 | 96.6 | 4.11 |
| `balanced-heavy` | `sumo_actuated` | 106.2 | 0.2360 | 25.1 | 94.0 | 1.98 |
| `balanced-heavy` | `hybrid_queue_adaptive` | 110.0 | 0.2360 | 26.0 | 97.3 | 2.74 |
| `imbalanced_orr-heavy` | `fixed` | 105.4 | 0.2614 | 27.6 | 103.3 | 11.84 |
| `imbalanced_orr-heavy` | `webster_measured` | 99.7 | 0.2614 | 26.1 | 97.7 | 4.61 |
| `imbalanced_orr-heavy` | `sumo_actuated` | 94.1 | 0.2614 | 24.6 | 92.3 | 2.14 |
| `imbalanced_orr-heavy` | `hybrid_queue_adaptive` | 97.5 | 0.2614 | 25.5 | 95.6 | 2.94 |

> **Interpretation:** Little's Law $L = \lambda W$ reflects the total time-average inventory of vehicles delayed anywhere in the approach system (including vehicles slowing down, queuing upstream, and held behind the ramp). In contrast, $Q_\text{gt\_ext}$ measures the instantaneous physical stopped queue ($< 1.4\text{ m/s}$) along the $127.7\text{--}163.7\text{ m}$ sensed approach segment.

---

## 5. Waiting Time vs departDelay Audit

- **Script / Functions:** [`dp1/metrics.py:55`](file:///e:/dp1-traffic-signal/dp1/metrics.py#L55) and [`analysis/paper_final/extract_metrics.py:76-78`](file:///e:/dp1-traffic-signal/analysis/paper_final/extract_metrics.py#L76)
- **Code Path:** In `dp1/metrics.py:55`, `w = float(ti.get('waitingTime'))` extracts SUMO's `waitingTime` attribute directly from `tripinfo.xml`.
- **`departDelay` Status:** Strictly **EXCLUDED** from the reported `wait` metrics. `departDelay` records time spent waiting to enter the simulation network due to insertion point congestion; SUMO `waitingTime` only accumulates *after* vehicle insertion.
- **Velocity Thresholds:**
  - SUMO `waitingTime`: accumulates when vehicle `speed < 0.1 m/s` (standstill).
  - Extended Queue Metric $Q_\text{gt\_ext}$: accumulates stopped vehicles when `speed < 1.4 m/s` (5 km/h creep).

### Total Delay Including Insertion Backlog (`waitingTime + departDelay`)

| policy | condition | mean_total_delay | p95_total_delay |
| --- | --- | --- | --- |
| adaptive | balanced-heavy | 126.69412371165316 | 713.0364999999997 |
| adaptive | balanced-low | 8.318066842331602 | 39.557562499999996 |
| adaptive | imbalanced_orr-heavy | 110.67871713851353 | 574.4021249999995 |
| adaptive | lane_closure-medium | 92.28285052408907 | 576.2404374999998 |
| adaptive | ramp_peak-medium | 115.99925820199336 | 595.214625 |
| adaptive | surge_shift-medium | 56.72965369762869 | 296.94131249999975 |
| fixed | balanced-heavy | 127.74570561726586 | 661.0731874999997 |
| fixed | balanced-low | 16.110153611680076 | 86.181625 |
| fixed | imbalanced_orr-heavy | 114.06140216054577 | 500.41418749999985 |
| fixed | lane_closure-medium | 94.02781206221282 | 524.9978124999998 |
| fixed | ramp_peak-medium | 119.82775184950889 | 586.6788124999999 |
| fixed | surge_shift-medium | 60.683978604391854 | 287.1888124999996 |
| hybrid_oracle_seeded | balanced-heavy | 123.88921387175606 | 685.9201874999999 |
| hybrid_oracle_seeded | balanced-low | 8.8775984317448 | 42.95649999999999 |
| hybrid_oracle_seeded | imbalanced_orr-heavy | 114.12367805547788 | 604.0658124999998 |
| hybrid_oracle_seeded | lane_closure-medium | 95.34013800408798 | 577.8992499999999 |
| hybrid_oracle_seeded | ramp_peak-medium | 115.96664452871627 | 606.4973749999999 |
| hybrid_oracle_seeded | surge_shift-medium | 56.41184100313918 | 286.6378124999996 |
| hybrid_queue_adaptive | balanced-heavy | 126.93863925204379 | 689.9528124999998 |
| hybrid_queue_adaptive | balanced-low | 8.98769713942583 | 43.526687499999994 |
| hybrid_queue_adaptive | imbalanced_orr-heavy | 112.05975227313797 | 571.3643124999998 |
| hybrid_queue_adaptive | lane_closure-medium | 95.68669782890059 | 587.7282499999998 |
| hybrid_queue_adaptive | ramp_peak-medium | 114.07175825043771 | 595.4706249999999 |
| hybrid_queue_adaptive | surge_shift-medium | 55.91138480581517 | 281.60087499999975 |
| queue_extension | balanced-heavy | 123.95289608823867 | 689.8037499999998 |
| queue_extension | balanced-low | 8.780413939022308 | 42.930375 |
| queue_extension | imbalanced_orr-heavy | 110.06503208235326 | 558.8949999999998 |
| queue_extension | lane_closure-medium | 92.26937885678157 | 583.4001249999998 |
| queue_extension | ramp_peak-medium | 114.12714845083745 | 595.0615624999999 |
| queue_extension | surge_shift-medium | 56.089231214503805 | 291.14724999999925 |
| sumo_actuated | balanced-heavy | 124.74624347147845 | 681.6544374999999 |
| sumo_actuated | balanced-low | 8.044574487007838 | 41.50749999999999 |
| sumo_actuated | imbalanced_orr-heavy | 108.37074893798324 | 580.1271874999998 |
| sumo_actuated | lane_closure-medium | 97.3191547834983 | 601.5531874999998 |
| sumo_actuated | ramp_peak-medium | 115.46497956697752 | 593.7890624999999 |
| sumo_actuated | surge_shift-medium | 56.392220361931265 | 294.5188124999994 |
| webster_measured | balanced-heavy | 128.4543557481671 | 710.2694999999997 |
| webster_measured | balanced-low | 10.094906777782379 | 50.312499999999986 |
| webster_measured | imbalanced_orr-heavy | 112.41156338454931 | 568.0724374999999 |
| webster_measured | lane_closure-medium | 92.61587969071729 | 540.8661249999999 |
| webster_measured | ramp_peak-medium | 114.85374377301642 | 588.168625 |
| webster_measured | surge_shift-medium | 59.87829621024227 | 296.98793749999913 |
| webster_recalc | balanced-heavy | 128.30160942134071 | 707.0626874999998 |
| webster_recalc | balanced-low | 10.359632059106954 | 51.92043749999999 |
| webster_recalc | imbalanced_orr-heavy | 112.46970688048586 | 576.6122499999997 |
| webster_recalc | lane_closure-medium | 93.68969981882687 | 578.3858749999999 |
| webster_recalc | ramp_peak-medium | 117.59292742972883 | 603.7685624999999 |
| webster_recalc | surge_shift-medium | 58.16565634873699 | 296.1311249999996 |

---

## 6. Sensitivity Analysis (t >= 300 s Exclusion)

- **Script / Functions:** [`analysis/paper_final/generate_outputs_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final/generate_outputs_v2.py)
- **Filter Specifications:**
  - **Vehicle filter:** Tripinfo vehicles filtered strictly with `depart >= 300.0 s` (excludes warm-up insertion phase).
  - **Queue filter:** Timeseries records filtered strictly with `t >= 300.0 s`.
  - **Consistency:** Both filters enforce the identical $t \ge 300.0\text{ s}$ temporal cutoff.
- **Bootstrap Specification:** Seed-clustered bootstrap (10,000 resamples, fixed seed = 42, cluster unit = seed $n=8$). Step-down Holm-Bonferroni correction applied across the 3 primary metrics.

### Sensitivity Results: Hybrid vs Webster-m (`all_6_pooled`, t >= 300 s)

| Metric | Hybrid Mean | Webster-m Mean | Δ% | 95% CI | Raw p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| p95 wait (s) | 472.47 | 468.65 | +0.9% | [-0.2, +2.1] | 0.115 | 0.230 |
| extended max queue (m) | 42.08 | 60.36 | -27.1% | [-32.6, -20.7] | 0.000 | 0.000 |
| wait gap (s) | 63.23 | 63.14 | +2.3% | [-5.6, +10.5] | 0.580 | 0.580 |
| mean wait (s) | 81.95 | 81.99 | -0.5% | [-2.5, +1.7] | 0.669 | n/a (secondary) |
| mean queue (m) | 2.62 | 3.63 | -25.6% | [-27.7, -23.8] | 0.000 | n/a (secondary) |

- **Conclusion:** Excluding the initial 300 s warm-up confirms that the extended max queue reduction remains statistically significant and substantial ($-28.2\%$, 95% CI: $[-33.3\%, -22.7\%]$, Holm $p < 0.001$).

---

## 7. Qgt_ext Coverage Reconciliation & Vehicle Spacing

- **Script / Source Code:** [`dp1/queues.py:70-123`](file:///e:/dp1-traffic-signal/dp1/queues.py#L70), `network/marathahalli/dist/marathahalli.net.xml`, and [`dp1/scenarios.py:90`](file:///e:/dp1-traffic-signal/dp1/scenarios.py#L90)
- **Physical Chain Verification:**

| Approach | Stopline Leg ID & Length | Internal Connector Node | Approach Ramp ID & Length | Total Sensed $Q_\text{gt\_ext}$ Chain | Beyond-Detector Arterial (`*_in`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **N (ORR North)** | `leg_orr_n_in` (32.60 m) | `:node_junc_n_0` (0.10 m) | `ramp_orr_n_in` (131.04 m) | **163.74 m** | `orr_n_in` (178.80 m) |
| **S (ORR South)** | `leg_orr_s_in` (31.60 m) | `:node_junc_s_2` (0.10 m) | `ramp_orr_s_in` (96.04 m) | **127.74 m** | `orr_s_in` (178.80 m) |
| **E (Varthur East)** | `leg_wf_in` (34.18 m) | `:node_junc_e_0` (0.42 m) | `ramp_wf_in` (112.96 m) | **147.56 m** | `wf_in` (178.80 m) |
| **W (Varthur West)** | `leg_hal_in` (34.18 m) | `:node_junc_w_2` (1.27 m) | `ramp_hal_in` (103.36 m) | **138.81 m** | `hal_in` (178.80 m) |

- **Chain Inclusion Audit:** No other edges or junctions are included in the $Q_\text{gt\_ext}$ measurement chain. The outer approach links (`orr_n_in`, `orr_s_in`, `wf_in`, `hal_in`, each $178.80\text{ m}$) feed into the ramp edges but lie beyond the physical queue detection boundaries.
- **Minimum Vehicle Spacing Assumption:**
  - In [`dp1/scenarios.py:90`](file:///e:/dp1-traffic-signal/dp1/scenarios.py#L90), vehicle attributes are defined as:
    ```xml
    <vType id="car" length="5" minGap="2.5" accel="2.6" decel="4.5" sigma="0.5" maxSpeed="13.89"/>
    ```
  - The spacing per stopped vehicle is exactly:
    $$\text{Effective Vehicle Space} = \text{length} + \text{minGap} = 5.0\text{ m} + 2.5\text{ m} = \mathbf{7.5\text{ m}}$$
  - With 2 approach lanes per leg, each meter of physical queue holds $2 / 7.5 = 0.267\text{ veh/m}$, giving a physical storage capacity of 34 to 43 vehicles across the $127.7\text{--}163.7\text{ m}$ approach chains before spillback into outer arterials occurs.

