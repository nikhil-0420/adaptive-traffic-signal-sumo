# Pre-Registration Amendment 3: Final Experiment Matrix, Evaluation Protocol, and Scope Boundaries

**Date:** 2026-11-04  
**Status:** Frozen and Pre-Registered (Phase F1)  
**Parent Documents:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md), [`docs/PREREGISTRATION_AMENDMENT_1.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_1.md), [`docs/PREREGISTRATION_AMENDMENT_2.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_2.md)

---

## 1. Executive Summary and Scope Definition

This amendment defines the final frozen experiment matrix, evaluation protocols, and pre-declared statistical analyses for the DP1 research benchmark on the Marathahalli junction model.

- **Proposed Policy:** `hybrid_queue_adaptive` (R4 de-oracled measured base green, no projection, default parameters).
- **Primary Reference Baseline:** `webster_measured` (realistic, online measured Webster cycle calculation).
- **Secondary Comparators:** `sumo_actuated`, `webster_recalc`, and `fixed`.
- **Ablation Baseline:** `hybrid_oracle_seeded` (R0 legacy oracle-seeded base green).
- **Execution Protocol:** Seed-major execution across seeds 131–138 (6 conditions $\times$ 8 seeds = 48 runs per seed block; 384 total simulations).

---

## 2. Final Experiment Matrix

### 2.1 Main Policies ($K = 7$)
1. `fixed`: Fixed-time BTP baseline plan (`config.FIXED`).
2. `webster_measured`: Online measured Webster timing based on observed approach flows during the first 300 s.
3. `webster_recalc`: Online periodic Webster recalculation every 300 s.
4. `sumo_actuated`: SUMO built-in gap-based actuated controller (`type="actuated"`).
5. `adaptive`: Baseline queue-proportional adaptive controller.
6. `queue_extension`: Actuated queue-extension controller with green cap.
7. `hybrid_queue_adaptive`: Proposed policy (R4 de-oracled base green + state-aware queue extension + max-green safety guard).

### 2.2 Ablation Policy ($K_{\text{abl}} = 1$)
8. `hybrid_oracle_seeded`: R0 oracle-seeded base green benchmark, evaluated on the exact same 6 conditions and seeds to isolate the benefit/cost of removing the scenario demand oracle.

### 2.3 Evaluation Conditions ($C = 6$)
The benchmark tests 6 representative conditions capturing stationary, asymmetric, transient peak, directional surge, and degraded capacity regimes:
1. `balanced-low`: Stationary balanced low demand (off-peak).
2. `balanced-heavy`: Stationary balanced heavy demand (peak saturation).
3. `imbalanced_orr-heavy`: Asymmetric high demand along the Outer Ring Road (ORR) corridor.
4. `ramp_peak-medium`: Non-stationary ramp peak replicating sudden arterial arrival surge.
5. `surge_shift-medium`: Dynamic corridor peak shift between North-South and East-West corridors.
6. `lane_closure-medium`: Capacity reduction bottleneck simulating lane closure.

### 2.4 Final Seeds and Seed-Major Ordering
- **Final Evaluation Seeds:** 131, 132, 133, 134, 135, 136, 137, 138 ($N = 8$ held-out seeds).
- **Seed Reserve Isolation:** Seeds 101–105 (dev), 106–110 (validation-1), 111–120 (validation-2), 121–130 (burned). Seeds 139–150 are strictly excluded and never used.
- **Execution Order:** **Seed-Major**. All 42 main cells ($7 \text{ policies} \times 6 \text{ conditions}$) plus 6 ablation cells ($1 \text{ policy} \times 6 \text{ conditions}$) are executed for seed 131 before proceeding to seed 132, ensuring complete multi-policy seed blocks.
- **Total Run Count:**
  $$\text{Main: } 7 \times 6 \times 8 = 336 \text{ runs}$$
  $$\text{Ablation: } 1 \times 6 \times 8 = 48 \text{ runs}$$
  $$\text{Total Matrix: } 384 \text{ runs}$$

---

## 3. Stopping Rule and Resumption Policy

- **Stopping Rule:** `--max-hours` wall-clock limit. If execution reaches the wall-clock limit, the runner completes the currently running seed block in its entirety and terminates gracefully.
- **Valid Analysis Constraint:** Statistical evaluation requires a minimum of 6 fully completed seed blocks (e.g., seeds 131–136). Partial or incomplete seed blocks are excluded from paired bootstrap analysis to preserve balance.
- **Integrity Rule:** The simulation execution may never be stopped, modified, or truncated based on intermediate metric values.
- **Resumption Rule:** If interrupted, the runner resumes only crashed or unexecuted cells. Already completed runs with valid `metrics.json` and `timeseries.csv` are never rerun or overwritten.

---

## 4. Dropped Variants and Mandatory Disclosures

In accordance with scientific integrity and pre-registration transparency, the following dropped avenues are formally disclosed:
1. **Reinforcement Learning (`rl_dqn`):** Excluded from the final benchmark matrix due to lack of convergence stability and unverified safety invariants on non-stationary traffic regimes.
2. **Max-Pressure (`pressure`):** Excluded due to detector horizon limitations and absence of downstream queue visibility at Marathahalli ramps.
3. **Oracle-Cycle Fixed Control (`fixed_matched_cycle` / `ORACLE-CYCLE`):** Dropped from the main comparison matrix and relabeled as `ORACLE-CYCLE` because it requires exact prior knowledge of unobservable scenario flows.
4. **Oracle Webster (`webster_oracle`):** Dropped in favour of the realistic `webster_measured`.
5. **Equal-Budget Hyperparameter Tuning:** Not conducted. All controllers are evaluated using their default frozen parameters to avoid overfitting and preserve auditability.
6. **R3 Minimum-Phase Duration Modulation (`hybrid_r3`):** CUT during Phase 11 ladder evaluation due to degradation on asymmetric flows.
7. **Queue Projection (`hybrid_queue_adaptive_proj`):** CUT during Phase 12 validation. All 95% confidence intervals on primary metrics spanned zero (Rule 1 FAIL). Projection remains disabled by default.
8. **Seeds 139–150:** Dropped to respect computation constraints and pre-freeze an 8-seed sample.
9. **Original 18-Condition Matrix:** Reduced to the representative 6-condition design to focus statistical power on core congestion failure modes.

---

## 5. Statistical Analysis Protocol

### 5.1 Metric Hierarchy
- **Primary Metrics:**
  1. `p95_wait_s`: 95th percentile vehicle waiting time across all completed trips.
  2. `gt_ext_max_queue_m`: Extended ground-truth maximum queue length (metres) across approach legs and inbound ramps.
  3. `approach_wait_gap_s`: Disparity in mean waiting time between critical approach corridors (fairness indicator).
- **Secondary Metrics:**
  - `mean_wait_s`: Overall average vehicle waiting time (seconds).
  - `gt_ext_avg_queue_m`: Time-averaged extended ground-truth queue (metres).
  - `throughput_vph`: Total completed vehicle trips normalised to vehicles per hour.
  - `completion_rate`: Fraction of inserted vehicles completing their journeys ($N_{\text{completed}} / N_{\text{inserted}}$).
  - `unfinished_vehicles`: Total count of vehicles remaining stalled or en-route at simulation conclusion.
  - `switches_per_hour`: Signal switching frequency (surrogate for equipment wear and transition overhead).

### 5.2 Hypotheses and Comparison Framework
- **Primary Test:** Paired comparison of `hybrid_queue_adaptive` vs `webster_measured` across paired $(c, s)$ cells ($N = 6 \text{ conditions} \times N_{\text{seeds}}$ pairs).
- **Secondary Tests:** Paired comparison of `hybrid_queue_adaptive` vs `sumo_actuated`, `webster_recalc`, and `fixed`.
- **Pooled Paired Percent-Difference Bootstrap:**
  - 10,000 bootstrap resamples with replacement over paired run deltas.
  - Fixed bootstrap random seed: **`seed = 42`**.
  - 95% percentile bootstrap confidence intervals.
  - Multiplicity control: **Holm-Bonferroni correction** applied across the three primary metrics (`p95_wait_s`, `gt_ext_max_queue_m`, `approach_wait_gap_s`).
  - Reporting rule: If a confidence interval spans zero, the result must be documented as "not distinguished". No claim of "outperforms" or "superiority" may be made without Holm-adjusted significance strictly excluding zero.
- **Descriptive Tables:** Per-condition tables reporting Mean, Standard Deviation (SD), and sample size $n$ are strictly descriptive and exploratory.

### 5.3 Pre-Declared Sensitivity: Post-Warmup Analysis ($t \ge 300\text{ s}$)
Because `webster_measured` and `webster_recalc` require an initial observation window of $300\text{ s}$ during which they execute the baseline BTP fixed-time plan:
- A mandatory pre-declared sensitivity analysis evaluates only vehicles departing at or after $t = 300\text{ s}$, and queues measured at $t \ge 300\text{ s}$.
- This verifies whether controller advantages or parity persist once measured cycle calculators transition to their calculated timings.

### 5.4 Overloaded and Boundary Cell Reporting
All unfavourable and boundary cells will be explicitly tabulated in `docs/RESULTS_SUMMARY.md`:
- Unfinished vehicle count $> 0$.
- Extended queue approaching ramp storage capacity ($> 120\text{ m}$).
- Extreme 95th percentile waiting times ($p95 > 300\text{ s}$).
