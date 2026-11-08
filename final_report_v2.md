# Final Report: DP1 Traffic-Signal Controller Evaluation & Replication (v2)

**Author:** Autonomous Implementation Engineer  
**Date:** November 8, 2026  
**Repository:** `dp1-traffic-signal`  
**Git Base Commit:** `6988089` (tag `paper-submission-v1`)  
**Current HEAD:** `b144c1d` (clean working tree with verified pipeline and candidate v2 models)  
**Execution Pipeline:** [`analysis/paper_final_v2/run_all.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/run_all.py)  

---

## 1. Executive Summary & Phase A2 Decision

### 1.1 Decision on Controller v2
**Decision: Controller v1 is FINAL.** Under the strict pre-registered selection rule, **no candidate v2 controller outperformed v1 on validation seeds 106–110**. As specified in the hard rules (*"If v2 does not clearly beat v1 on validation seeds, stop. Say so and report that v1 is final. That is an acceptable outcome, and I will then use only Part B"*), Phase A3 (pre-registration amendment) and Phase A4 (confirmatory testing) were skipped. Confirmatory seeds **151–160 remain completely untouched and 100% pristine**.

### 1.2 Quantitative Evidence from Phase A2 Ablation
Across 360 systematic simulation runs on seeds 101–110 (development seeds 101–105, validation seeds 106–110) in `results/research/exp_v2_ablation/`:
- **Baseline v1 (`hybrid_queue_adaptive`):**
  - Validation mean max queue: **42.68 m**
  - Validation p95 wait: **424.24 s**
  - Validation wait gap: **64.88 s**
- **Comparator (`sumo_actuated`):**
  - Validation mean max queue: **36.72 m**
  - Baseline max-queue gap to `sumo_actuated`: $42.68 - 36.72 = \mathbf{5.96\text{ m}}$
  - Pre-registered qualification threshold ($\ge 50\%$ reduction): target gap $\le \mathbf{2.98\text{ m}}$ (i.e. mean max queue $\le 39.70$ m)
- **Candidate Evaluation:**
  1. **Candidate (a) (`hybrid_v2_cand_a` — Rest-in-Green):**
     - Mean max queue: **42.36 m** (gap = 5.64 m vs target $\le 2.98$ m $\rightarrow$ **FAILS Criterion i**).
     - Pathological failure: Rest-in-green introduces severe minor-street starvation in `imbalanced_orr-heavy`. The worst-run max queue spikes to **111.05 m** (vs v1's 74.48 m), and validation p95 wait jumps by **+38.0 s** to **538.00 s**. It replicates the known failure mode of unconstrained `sumo_actuated`.
  2. **Candidate (b) (`hybrid_v2_cand_b` — Unconditional 35s Red Cap):**
     - Mean max queue: **41.89 m** (gap = 5.17 m vs target $\le 2.98$ m $\rightarrow$ **FAILS Criterion i**).
     - Behavior: Mathematically guarantees the 48.0 s red-interval bound under all conditions, but does not halve the queue gap.
  3. **Candidate (c) (`hybrid_v2_cand_c` — Pressure-Based Differential Extension):**
     - Mean max queue: **42.44 m** (gap = 5.72 m vs target $\le 2.98$ m $\rightarrow$ **FAILS Criterion i**).
  4. **Candidate (d) (`hybrid_v2_cand_d` — Rest-in-Green + Unconditional Cap):**
     - Mean max queue: **41.46 m** (gap = 4.74 m vs target $\le 2.98$ m $\rightarrow$ **FAILS Criterion i**).
     - Validation p95 wait: **434.71 s** (+2.47% higher than v1 $\rightarrow$ **FAILS Criterion ii**).
     - Worst-run max queue in `imbalanced_orr-heavy` spikes to **163.74 m**.

All candidate variants and validation metrics are permanently recorded in [`ablation_ledger.csv`](file:///e:/dp1-traffic-signal/ablation_ledger.csv).

---

## 2. Part B: Single Source of Truth Pipeline Architecture

The unified analysis pipeline [`analysis/paper_final_v2/run_all.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/run_all.py) was built and executed from scratch. It enforces loud assertions:
1. **No Suffix Aliasing Bug:** Policy labels are parsed by explicit longest-first suffix matching against the canonical list of policy names:
   `["hybrid_oracle_seeded", "hybrid_queue_adaptive", "queue_extension", "sumo_actuated", "webster_measured", "webster_recalc", "adaptive", "fixed"]`.
   This cleanly separates `adaptive`, `queue_extension`, `hybrid_queue_adaptive`, and `hybrid_oracle_seeded`.
2. **Cell Count Assertion:** Asserts exactly 8 runs per cell across 48 cells ($8 \times 48 = 384$ runs total, seeds 131–138). Zero teleports occurred across all 384 runs (`--time-to-teleport -1`).
3. **Exact Canonical Subset Strings:**
   - Stationary: `["balanced-low", "balanced-heavy", "imbalanced_orr-heavy"]`
   - Non-Stationary: `["ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"]`
4. **Mathematical Subset Pooled Assertion:** For every metric, comparator, and subset:
   $$\text{Pooled Value} = \frac{\text{Stationary Value} + \text{Non-Stationary Value}}{2}$$
   Verified with difference $< 10^{-4}$.
5. **Documented Metric Definitions:**
   - **Mean Wait ($W$):** Space-time average waiting time of completed trips (`tripinfo.xml` `waitingTime`, speed $< 0.1\text{ m/s}$).
   - **p95 Wait:** 95th-percentile vehicle waiting time from `tripinfo.xml`.
   - **Mean Queue ($Q_{\text{gt\_ext\_avg}}$):** Space-time average extended ground-truth queue across all seconds and approaches.
   - **Max Queue ($Q_{\text{gt\_ext\_max}}$):** Maximum over time of the approach-maximum extended queue.
   - **Wait Gap ($W_{\text{gap}}$):** Difference between maximum and minimum approach-mean waiting times: $\max_i \bar{W}_i - \min_i \bar{W}_i$.
   - **Red Interval:** Duration in seconds from the end of an axis's green phase to the start of its next green phase, encompassing both yellow and all-red clearance intervals: $5\text{ s} + G_{\text{opp}} + 5\text{ s}$.

---

## 3. Verified Numerical Results (The Full Number Ledger)

All numbers are exported to [`paper_final_v2/numbers.json`](file:///e:/dp1-traffic-signal/paper_final_v2/numbers.json) and mapped in [`PAPER_NUMBERS.md`](file:///e:/dp1-traffic-signal/PAPER_NUMBERS.md).

### 3.1 Table I: Hybrid vs. Measured-Flow Webster (Pooled, n=48 pairs, 8 clusters)
Generated by [`compute_bootstrap_v2.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/compute_bootstrap_v2.py) (10,000 seed-clustered bootstrap resamples, seed 42, step-down Holm correction across the 3 primary metrics):

| Metric | Hybrid Mean | Webster-m Mean | Seed-Clustered Delta % [95% CI] | Cluster Holm $p$ | Pair Delta % [95% CI] | Absolute Difference (Hybrid − Ref) [95% CI] | Status |
|---|---|---|---|---|---|---|---|
| **Extended Max Queue** | **42.18 m** | **62.24 m** | **−28.8%** [−35.0%, −22.4%] | **< 0.001** | −28.8% [−35.0%, −22.4%] | −20.06 m [−24.84, −15.34] | Statistically Significant |
| **p95 Wait** | **452.33 s** | **446.83 s** | **−0.9%** [−4.2%, +2.5%] | **1.000** | −0.9% [−4.2%, +2.5%] | +5.50 s [−12.24, +22.44] | Not Distinguished |
| **Wait Gap** | **58.28 s** | **59.82 s** | **+3.0%** [−8.0%, +16.2%] | **1.000** | +3.0% [−8.0%, +16.2%] | **−1.54 s** [−6.28, +3.19] ($p=0.518$) | Not Distinguished |
| **Mean Wait\*** | **76.74 s** | **77.72 s** | **−3.1%** [−5.3%, −1.1%] | unadjusted | −3.1% [−5.3%, −1.1%] | −0.98 s [−1.82, −0.17] | Secondary |
| **Mean Queue\*** | **2.46 m** | **3.99 m** | **−35.7%** [−38.4%, −33.1%] | unadjusted | −35.7% [−38.4%, −33.1%] | −1.53 m [−1.72, −1.34] | Secondary |

\*Secondary metrics unadjusted for multiplicity.

### 3.2 Table II: Alternative Baselines (All 6 Conditions Pooled)

| Comparator | Primary Metric | Hybrid Mean | Comparator Mean | Seed-Clustered Delta % [95% CI] | Cluster Holm $p$ | Significant? |
|---|---|---|---|---|---|---|
| **Webster-recalc** | Max Queue | 42.18 m | 61.64 m | **−28.3%** [−34.8%, −21.7%] | < 0.001 | Yes |
| | p95 Wait | 452.33 s | 457.94 s | **−2.5%** [−5.9%, +0.9%] | 0.177 | No |
| | Wait Gap | 58.28 s | 62.00 s | **+17.5%** [−7.8%, +60.2%] | 0.177 | No |
| **Fixed BTP** | Max Queue | 42.18 m | 82.52 m | **−48.7%** [−53.0%, −43.7%] | < 0.001 | Yes |
| | p95 Wait | 452.33 s | 468.22 s | **−2.8%** [−10.0%, +3.9%] | 0.008\* | Yes (Cluster) / No (Pair) |
| | Wait Gap | 58.28 s | 64.69 s | **+1.3%** [−7.3%, +10.6%] | 0.824 | No |
| **SUMO-actuated** | Max Queue | 42.18 m | 37.89 m | **+11.4%** [+4.6%, +18.7%] | 0.0006 | Yes (Worse) |
| | p95 Wait | 452.33 s | 446.40 s | **+1.0%** [−2.1%, +4.2%] | 0.536 | No |
| | Wait Gap | 58.28 s | 60.52 s | **+14.8%** [−2.9%, +37.7%] | 0.198 | No |

\*Note on Fixed BTP p95 wait: Under seed-clustered bootstrap, Holm $p = 0.008$ due to consistent within-seed ranking; under independent pair-level bootstrap, Holm $p = 0.866$. This sensitivity difference is explicitly noted.

### 3.3 Table III: Oracle-Seeded Variant Comparison

| Metric | Hybrid Mean | Oracle-Seeded Mean | Seed-Clustered Delta % [95% CI] | Cluster Holm $p$ | Pair Delta % [95% CI] | Absolute Difference [95% CI] |
|---|---|---|---|---|---|---|
| **Max Queue** | 42.18 m | 42.66 m | **−1.2%** [−6.0%, +3.9%] | 1.000 | −1.2% [−6.0%, +3.9%] | −0.48 m [−2.61, +1.52] |
| **p95 Wait** | 452.33 s | 453.75 s | **−0.5%** [−2.7%, +1.7%] | 1.000 | −0.5% [−2.7%, +1.7%] | −1.42 s [−8.90, +6.36] |
| **Wait Gap** | 58.28 s | 58.33 s | **+15.3%** [+0.2%, +34.1%] | 0.010\* | +15.3% [+0.2%, +34.1%] | **−0.05 s** [−4.17, +3.94] ($p=0.984$) |

\*Critical Insight: While the percentage delta (+15.3%) has a cluster bootstrap CI excluding zero due to ratios with small denominators in low-demand seeds, the **absolute difference in wait gap is exactly −0.05 s** (58.28 s vs 58.33 s), with a 95% CI of [−4.17 s, +3.94 s] ($p = 0.984$).

### 3.4 Table IV: Per-Condition Overview (p95 Wait [s] / Max Queue [m])

| Condition | Hybrid | Webster-m | SUMO-actuated | Fixed BTP |
|---|---|---|---|---|
| **balanced-low** | 42.8 ± 3.4 / 24.9 ± 0.0 | 50.1 ± 1.1 / 34.0 ± 2.6 | 40.7 ± 1.3 / 25.8 ± 1.2 | 86.4 ± 3.5 / 45.6 ± 1.7 |
| **balanced-heavy** | 667.1 ± 20.3 / 46.8 ± 3.6 | 686.9 ± 20.4 / 58.9 ± 3.9 | 638.6 ± 20.7 / 39.7 ± 1.5 | 645.6 ± 22.0 / 97.9 ± 12.0 |
| **imbalanced_orr-heavy** | 542.4 ± 19.3 / 47.9 ± 5.0 | 525.1 ± 20.1 / 78.4 ± 4.5 | 545.9 ± 19.5 / 37.8 ± 1.6 | 473.8 ± 27.6 / 107.1 ± 6.8 |
| **ramp_peak-medium** | 594.6 ± 17.0 / 42.6 ± 3.7 | 588.1 ± 16.5 / 50.8 ± 4.3 | 594.3 ± 17.6 / 38.6 ± 1.5 | 674.3 ± 20.7 / 82.5 ± 5.1 |
| **surge_shift-medium** | 503.4 ± 20.7 / 42.6 ± 4.5 | 490.8 ± 20.8 / 76.5 ± 4.1 | 500.5 ± 21.0 / 44.5 ± 2.7 | 546.6 ± 22.1 / 80.3 ± 4.2 |
| **lane_closure-medium** | 363.6 ± 13.5 / 48.3 ± 20.6 | 339.9 ± 15.6 / 74.8 ± 9.0 | 358.3 ± 14.8 / 40.9 ± 8.4 | 382.4 ± 14.7 / 81.6 ± 4.8 |

### 3.5 Table V: Operational Dynamics (Switches & Green Durations)

| Policy | Switches / Hour (Mean ± SD) | Switches / Hour (Median) | Green Duration (Mean ± Run SD) | Green Duration (Median) |
|---|---|---|---|---|
| **Fixed BTP** | 17.8 ± 0.0 | 17.8 | 96.0 ± 0.0 s | 95.0 s |
| **Webster-measured** | 80.0 ± 19.8 | 85.7 | 24.0 ± 7.0 s | 22.0 s |
| **Webster-recalc** | 80.1 ± 19.7 | 85.7 | 24.0 ± 7.0 s | 22.0 s |
| **SUMO-actuated** | 121.2 ± 9.8 | 120.9 | 15.2 ± 1.3 s | 15.0 s |
| **Adaptive (pure queue)** | 114.7 ± 11.2 | 114.9 | 16.4 ± 1.7 s | 16.0 s |
| **Queue-extension only** | 121.5 ± 9.0 | 121.7 | 15.1 ± 1.3 s | 15.0 s |
| **Hybrid (Proposed)** | 104.9 ± 11.3 | 104.6 | 17.7 ± 1.7 s | 17.0 s |
| **Hybrid Oracle-Seeded** | 105.7 ± 11.1 | 106.3 | 17.6 ± 1.7 s | 17.0 s |

### 3.6 Table VI: Heavy-Demand Audit (balanced-heavy & imbalanced_orr-heavy)

| Condition | Policy | Completed Trips | p95 Wait (s) | Max Vehicle Wait (s) | Max Queue (m) | Median Stops | p95 Stops | Max Stops |
|---|---|---|---|---|---|---|---|---|
| **balanced-heavy** | Hybrid | 1500.5 | 667.1 | 802.4 | 46.8 | 2.0 | 8.0 | 11.0 |
| | Webster-m | 1494.6 | 686.9 | 828.6 | 58.9 | 3.0 | 8.0 | 11.0 |
| | SUMO-actuated | 1508.8 | 638.6 | 761.4 | 39.7 | 2.0 | 7.0 | 11.0 |
| | Fixed BTP | 1506.0 | 645.6 | 772.4 | 97.9 | 2.0 | 7.0 | 10.0 |
| **imbalanced_orr-heavy** | Hybrid | 1679.9 | 542.4 | 694.0 | 47.9 | 2.0 | 7.0 | 11.0 |
| | Webster-m | 1684.2 | 525.1 | 688.1 | 78.4 | 2.0 | 7.0 | 10.0 |
| | SUMO-actuated | 1679.1 | 545.9 | 697.5 | 37.8 | 2.0 | 7.0 | 10.0 |
| | Fixed BTP | 1700.1 | 473.8 | 647.5 | 107.1 | 2.0 | 6.0 | 9.0 |

### 3.7 Table VII: Red-Interval Distributions & 48.0 s Bound Verification
Definition: Elapsed time from end of own green to start of next own green ($5\text{ s} + G_{\text{opp}} + 5\text{ s}$).  
Analytic maximum bound: $35\text{ s (guard)} + 3\text{ s (gap-out)} + 2 \times 5\text{ s (clearances)} = \mathbf{48.0\text{ s}}$.

| Policy | Observed Transitions ($N$) | Mean (s) | p95 (s) | p99 (s) | Max Observed (s) | Analytic Bound | Satisfies Bound? |
|---|---|---|---|---|---|---|---|
| **Fixed BTP** | 852 | 110.2 | 115.0 | 115.0 | 115.0 | n/a (static) | n/a |
| **Webster-measured** | 3,836 | 28.9 | 34.0 | 115.0 | 115.0 | n/a (pretimed) | n/a |
| **Webster-recalc** | 3,838 | 28.9 | 35.0 | 115.0 | 115.0 | n/a (pretimed) | n/a |
| **SUMO-actuated** | 5,817 | 21.5 | 27.0 | 34.0 | 70.0 | None (unbounded) | No |
| **Adaptive (pure queue)** | 5,502 | 22.4 | 25.0 | 28.0 | 70.0 | None | No |
| **Queue-extension only** | 5,832 | 21.4 | 23.0 | 24.0 | 66.0 | None | No |
| **Hybrid (Proposed)** | 5,036 | 23.9 | 30.0 | 33.0 | **47.0** | **48.0** | **YES (47.0 $\le$ 48.0)** |
| **Hybrid Oracle-Seeded** | 5,073 | 23.8 | 28.0 | 32.0 | **43.0** | **48.0** | **YES (43.0 $\le$ 48.0)** |

### 3.8 Table VIII & VIII-B: Little's Law Resolution & Edge Breakdown
- **Demand Horizon:** 1,800 s; **Simulation End:** 2,100 s.
- **Little's Law Paradox:** In heavy conditions, Little's Law implies $L = \lambda W \approx 19.7\text{--}22.8$ queued vehicles per approach. However, the space-time monitored queue $Q_{\text{gt\_ext}}$ registers only 2.5–12.0 m.
- **Physical Breakdown of Standing Vehicles (Speed $< 0.1\text{ m/s}$):**

| Condition | Policy | Approach Legs (31.6–34.2 m) | Connector Ramps (96.0–131.0 m) | Outer Arrival Links (178.8 m) | Total Network Halting | Outer Link Share % |
|---|---|---|---|---|---|---|
| **balanced-heavy** | Hybrid | 1.69 veh | 0.01 veh | **20.46 veh** | 22.16 veh | **92.3%** |
| | SUMO-actuated | 1.18 veh | 0.00 veh | **21.65 veh** | 22.83 veh | **94.8%** |
| **imbalanced_orr-heavy** | Hybrid | 1.90 veh | 0.02 veh | **17.76 veh** | 19.67 veh | **90.3%** |
| | SUMO-actuated | 1.96 veh | 0.59 veh | **18.50 veh** | 21.06 veh | **87.8%** |

**Conclusion:** **Over 90% of queued vehicles reside on the 178.8 m outer feeder links** (`orr_n_in`, `orr_s_in`, `wf_in`, `hal_in`) upstream of the approach ramps. The stopline detectors monitor only the downstream approach legs and connector ramps.

### 3.9 Table IX: Insertion Delay & Backlog Audit (Heavy Conditions)

| Condition | Policy | Mean departDelay (s) | p95 departDelay (s) | Max departDelay (s) | Share > 60s (%) | Max Concurrent Backlog | Mean Total Delay (Wait + departDelay) |
|---|---|---|---|---|---|---|---|
| **balanced-heavy** | Hybrid | 15.6 s | 69.0 s | 155.0 s | 5.8% | 23.8 veh | 118.0 s |
| | Webster-m | 15.8 s | 69.0 s | 156.0 s | 5.9% | 23.9 veh | 119.5 s |
| | SUMO-actuated | 15.3 s | 68.0 s | 148.0 s | 5.6% | 22.8 veh | 115.7 s |
| | Fixed BTP | 15.6 s | 69.0 s | 155.0 s | 5.8% | 23.8 veh | 120.3 s |
| **imbalanced_orr-heavy** | Hybrid | 12.3 s | 59.0 s | 145.0 s | 4.8% | 20.8 veh | 101.4 s |
| | Webster-m | 12.1 s | 58.0 s | 136.0 s | 4.6% | 20.4 veh | 100.9 s |
| | SUMO-actuated | 12.2 s | 58.0 s | 142.0 s | 4.7% | 20.8 veh | 101.7 s |
| | Fixed BTP | 11.2 s | 56.0 s | 129.0 s | 4.3% | 100.0 s |

### 3.10 Table X: Warm-up Sensitivity Analysis ($t \ge 300\text{ s}$ Exclusion)
Filtering trips with $\text{depart} \ge 300.0\text{ s}$ and queue samples with $t \ge 300.0\text{ s}$ across `all_6_pooled`:
- **Extended Max Queue:** **−28.2%** [95% CI: −33.3%, −22.7%], Holm $p < 0.001$ (**Significant**).
- **p95 Wait:** **+0.8%** [95% CI: −2.2%, +3.5%], Holm $p = 1.000$ (Not Significant).
- **Wait Gap:** **+4.1%** [95% CI: −7.8%, +17.2%], Holm $p = 1.000$ (Not Significant).
- **Verdict:** Queue reduction remains robust and statistically indistinguishable from the full-run effect (−28.8%).

---

## 4. Paper-versus-Code Discrepancies & Exact Text Updates

| Discrepancy Item | Code Location / Truth | Paper Manuscript Text | Exact Paper Sentence to Update |
|---|---|---|---|
| **1. Competing Red-Wait Guard Condition** | In `dp1/controllers/hybrid_queue_adaptive.py:453`, condition is `comp_q >= self.cfg.min_competing_queue_m` (2.0 m). | Section IV claims $Q_{\text{comp}} > 0$. | **Old:** *"The competing red-wait guard triggers a phase switch if opposing red wait exceeds 35 s while $Q_{\text{comp}} > 0$."*<br>**New:** *"The competing red-wait guard triggers a phase switch if opposing red wait exceeds 35 s while a competing queue of at least 2.0 m ($Q_{\text{comp}} \ge 2.0\text{ m}$) is detected."* |
| **2. s136 Ramp-Peak Baseline Allocation** | In `marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136/decisions.csv` row 127 ($t=1171$ s), `g_base_s = 15.8`, `actual_green_s = 15.8`. | Section VI-D text misprinted 25.8 s. | **Old:** *"North-South green initiated with baseline allocation 25.8 s..."*<br>**New:** *"North-South green initiated with baseline allocation 15.8 s..."* |
| **3. Fixed BTP Timing Plan Configuration** | In `dp1/config.py:270` (`FIXED_MARATHAHALLI`), timings are EW=105 s, NS=95 s (cycle=210 s). Generic placeholder `FIXED` (line 262) inverted this as NS=105 s, EW=95 s. Simulation used `FIXED_MARATHAHALLI`. | Section V mentions 105 s EW / 95 s NS. | **Old:** *"fixed: static BTP plan (105 s EW / 95 s NS)."*<br>**New:** *"fixed: static BTP plan (105 s EW / 95 s NS, as configured in FIXED_MARATHAHALLI)."* |
| **4. Wait Gap Relative Ratio vs Absolute Difference** | In `numbers.json`, relative wait gap delta vs oracle is +15.3%, but absolute mean difference is **−0.05 s** (58.28 s vs 58.33 s, $p = 0.984$). | Table III reports +15.3% (+0.2, +34.1). | **Add Footnote to Table III:** *"The relative delta (+15.3%) represents the unweighted mean of per-pair percentage ratios, which is inflated by small denominators in low-demand seeds. In absolute terms, the pooled mean wait gaps are virtually identical: 58.28 s for hybrid vs. 58.33 s for oracle (difference −0.05 s, 95% CI [−4.17, +3.94] s, p = 0.984)."* |
| **5. Little's Law Physical Location** | `table8b_edge_breakdown.csv` proves 90.3%–94.8% of standing vehicles are on outer arrival links (`orr_n_in`, `wf_in`, etc.), not the monitored approach legs. | Paper notes discrepancy between Little's Law and monitored queue without location. | **Add to Section VII Discussion:** *"The apparent divergence between Little's Law (19.7–22.8 standing vehicles) and the detector queue (2.5–12.0 m) is resolved by spatial analysis: 90.3% to 94.8% of halted vehicles accumulate on the 178.8 m outer feeder links upstream of the ramp merge, outside the coverage of the stopline E2 detectors."* |

---

## 5. Artifacts & Generated Files

All deliverables are generated and saved:
- Master Pipeline: [`analysis/paper_final_v2/run_all.py`](file:///e:/dp1-traffic-signal/analysis/paper_final_v2/run_all.py)
- Traceability Matrix: [`PAPER_NUMBERS.md`](file:///e:/dp1-traffic-signal/PAPER_NUMBERS.md)
- Complete Numbers JSON: [`paper_final_v2/numbers.json`](file:///e:/dp1-traffic-signal/paper_final_v2/numbers.json)
- Tables in `paper_final_v2/tables/`:
  - `table2_primary_comparisons.csv`
  - `table3_secondary_metrics.csv`
  - `table4_per_condition.csv`
  - `table5_switching_and_greens.csv`
  - `table6_heavy_audit.csv`
  - `table7_red_intervals.csv`
  - `table8_littles_law.csv`
  - `table8b_edge_breakdown.csv`
  - `table9_insertion_delay.csv`
  - `table10_sensitivity_300s.csv`
  - `sensitivity_verdict_comparison.csv`
- Publication Figures in `paper_final_v2/figures/`:
  - `fig1_network_schematic.png`
  - `fig2_decision_trace.png`
  - `fig3_forest_plot.png`
  - `fig4_queue_timeseries.png`

---

## 6. Verification & Quality Gates

1. **Deterministic Test Suite:** All unit tests pass cleanly:
   - `pytest tests/test_core.py`: PASSED (Safety invariants: no green-to-green transitions, clearance intervals enforced).
   - `pytest tests/test_hybrid_v2.py`: PASSED (4/4 candidate v2 behavioral tests).
   - `pytest tests/test_runner_determinism.py`: PASSED.
   - `pytest tests/test_phase5_telemetry_regression.py`: PASSED.
2. **Confirmatory Seed Purity:** Confirmatory seeds **151–160** remain completely untouched (verified 0 occurrences across all logs, scripts, and results).
3. **Paper Text & DOCX:** Unmodified in accordance with instructions.
