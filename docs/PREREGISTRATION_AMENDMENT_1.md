# Pre-Registration Amendment 1: Ground-Truth Queue Metric, De-Oracled Controller, and R3 Amendment Protocol

**Date:** 2026-11-03  
**Status:** Frozen and Pre-Registered (Prior to Phase 10B Execution)  
**Parent Document:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md)

---

## 1. Motivation and Empirical Context

Diagnostic investigations and empirical findings from Phases 7B, 8, and 10 identified four critical methodological and architectural issues that require a formal, pre-registered amendment prior to Phase 11 hyperparameter tuning:

1. **Detector Jam-Length Clipping & Ineffective Saturation Flag**:
   - In SUMO, the E2 lane-area detector's measured jam length caps at approximately $24.00\text{ m}$ on Marathahalli's $24.9\text{ m}$ detectors due to the stop-bar setback (the lead vehicle stops before the junction entry, meaning its nose clears the stop line while its rear occupies the downstream end of the detector).
   - The controller-facing `SATURATED` flag was configured to trip only at $\text{det\_length} - 0.5\text{ m} = 24.4\text{ m}$. Consequently, the flag virtually never fired ($0.00\%–0.02\%$ in Phase 7B diagnostics), even though the detector was physically 100% full between $4.0\%$ and $14.0\%$ of the time in heavy traffic cells (Diagnostics D1 and D7).
   - Because `max_queue_m` was defined as the maximum detector-measured queue, it was artificially clipped at $\approx 24.00\text{ m}$ across almost all conditions (e.g., in Phase 10, the grand baseline mean was $23.83\text{ m}$ and candidate was $23.84\text{ m}$, yielding a compressed, meaningless $\Delta = +0.01\text{ m}$).
2. **Oracle Demand Leakage in the Proposed Hybrid Controller**:
   - In Phase 10 and earlier, `hybrid_queue_adaptive` seeded its base green splits through `site_webster_plan(scenario, demand_level)`. This function reads the true scenario demand table (`SITE_DEMAND_PATTERNS`) and the runtime `demand_level` parameter from `dp1/config.py`.
   - As established in Phase 7B Diagnostic D0, this gave the proposed controller omniscient oracle knowledge of future arrival rates and scenario identity that an in-situ traffic controller in Bengaluru would never possess.
3. **Marginal Inconclusive Result for R3 Under Small Sample Size ($n=5$)**:
   - In Phase 10, candidate R3 (Queue-Aware Fairness) yielded substantial directional improvements on directional delay equity (approach wait gap $\Delta = -1.23\text{ s}$, a $-1.79\%$ reduction) and grand-mean wait ($\Delta = -0.33\text{ s}$), but its paired bootstrap 95% confidence interval `[-2.48, +0.04]` touched zero. With only 5 validation seeds (106–110), statistical power was limited.
4. **Uncertainty of Phase 8 Headroom Claims**:
   - Phase 8 claims of "hybrid headroom over Webster" rested on $n=5$ seed differences that were smaller than the seed-to-seed standard deviation, and compared the hybrid against an oracle-seeded Webster plan rather than a field-deployable measured baseline.

---

## 2. Metric Definition Amendments

### Primary Metric Redefinition: Ground-Truth Maximum Queue
- The primary metric **`max queue`** is hereby formally redefined as **`gt_max_queue_m`** (ground-truth maximum queue length in metres), computed from microscopic vehicle positions and kinematics for evaluation purposes only.
- The detector-visible maximum queue (`max_queue_m`) is demoted to a **secondary metric** for sensor observability tracking.

### Exact Microscopic Ground-Truth Queue Specification
Ground-truth queue measurement is computed at each simulation step by `QueueMeasurementEngine._compute_lane_ground_truth(lane_id)` according to the following invariants:
1. **Halting Speed Threshold**: A vehicle is considered queued/stopped if its instantaneous speed satisfies $v < 1.4\text{ m/s}$ ($5.04\text{ km/h}$, SUMO standard halting definition).
2. **Stop-Line Boundary Condition**: The first queued vehicle in a lane must be within $15.0\text{ m}$ of the approach stop line. If no stopped vehicle is present within $15.0\text{ m}$, the ground-truth queue for that lane is $0.0\text{ m}$.
3. **Contiguous Cluster Headway Gap**: Successive stopped vehicles belong to the same contiguous queue if the longitudinal bumper-to-bumper distance satisfies:
   $$\text{gap} = \text{dist\_to\_front}_{i} - \text{dist\_to\_back}_{i-1} \le 7.5\text{ m}$$
   Any vehicle separated by $> 7.5\text{ m}$ terminates the queue cluster.
4. **Queue Extent**: The lane queue extent is the distance from the stop line to the rear bumper of the furthest vehicle in the cluster:
   $$\text{extent} = \max_{i \in \text{cluster}} (\text{dist\_to\_front}_i + \text{length}_i)$$
5. **Approach Aggregation**: The approach ground-truth queue is the **maximum** across all lanes of that approach leg:
   $$Q_{\text{approach}}^{\text{GT}} = \max_{\text{lane} \in \text{approach}} Q_{\text{lane}}^{\text{GT}}$$
6. **Covered Spatial Extent & Physical Boundary**:
   - The measurement spans the four controlled approach intersection legs of the Marathahalli junction:
     - North (`leg_orr_n_in`): physical edge length $34.2\text{ m}$
     - South (`leg_orr_s_in`): physical edge length $34.2\text{ m}$
     - East (`leg_wf_in`): physical edge length $31.6\text{ m}$
     - West (`leg_hal_in`): physical edge length $31.6\text{ m}$
   - **Boundary Limitation**: If a queue spills upstream beyond the junction leg onto the approach ramps (`ramp_orr_n_in`, `ramp_orr_s_in`, `ramp_wf_in`, `ramp_hal_in`), vehicles on the ramp are outside the covered extent of `leg_*_in`. Therefore, `gt_max_queue_m` is physically bounded by $31.6\text{ m}–34.2\text{ m}$ unless the evaluation logger explicitly queries upstream ramp edges.

---

## 3. Seed Partitioning Update: Validation-2 Block

To test the R3 amendment with adequate statistical power without compromising evaluation integrity, the seed space is updated:
- **Seeds 101–105**: Development / Prototyping (dev).
- **Seeds 106–110**: Validation-1 (used in Phase 10; burned for Phase 10 decisions).
- **Seeds 111–120**: **Validation-2 ($n=10$)**. Dedicated **exclusively** to the Phase 10B R3 amendment retest in Task 4.
- **Seeds 121–130**: Exploratory / Pilot (burned in earlier exploratory work; never used for acceptance).
- **Seeds 131–150**: Final Benchmark Evaluation (held out; strictly untouched until Phase 14).

---

## 4. De-Oracling: R4 Adopted as Architectural Validity Fix

1. The R4 mechanism (measured Webster base green derived from a $300\text{ s}$ empirical warm-up window) is adopted as the **new default `hybrid_queue_adaptive`**.
2. This change is classified as an **architectural validity fix** (restoring scientific validity by removing illegal oracle demand information), not an optimization rung. It is therefore adopted independently of performance acceptance rules.
3. The previous oracle-seeded hybrid is renamed to `hybrid_oracle_seeded` and labeled `ORACLE-SEEDED` in all records and documentation.
4. Warm-up behavior of the de-oracled hybrid uses a fixed un-oracled plan ($19.0\text{ s}$ NS / $21.0\text{ s}$ EW on Marathahalli) prior to $t=300\text{ s}$ without inspecting runtime scenarios.

---

## 5. Protocol for the R3 Amendment Retest

Candidate R3 (Queue-Aware Fairness) is granted a single pre-registered retest under the following conditions:
1. **Baseline**: The new de-oracled default hybrid (`hybrid_queue_adaptive` with R4 measured base green).
2. **Candidate**: The new de-oracled hybrid with R3 queue-aware fairness enabled (`rungs=("R3",)`).
3. **Evaluation Set**: Seeds 111–120 ($n=10$ seeds $\times$ 18 demand conditions = 180 runs per policy; 540 runs total including `webster_measured`).
4. **Primary Metrics Evaluated**:
   - `p95 wait` (`p95_wait_s`)
   - `ground-truth max queue` (`gt_max_queue_m`)
   - `approach wait gap` (`approach_wait_gap_s`)
5. **Acceptance Rule**: Exactly as defined in Section 6 of `docs/PREREGISTRATION.md`:
   - At least one primary metric must improve with paired bootstrap 95% CI (10,000 resamples, seed `42`, Holm-corrected) strictly excluding zero;
   - Grand-mean waiting time must not degrade by $> 1.0\%$;
   - Completion rate must not decrease and unfinished vehicles must not increase.
6. **Finality**: This is the sole retest permitted for R3. If it fails, R3 is **permanently cut** from the baseline hybrid and cannot be resurrected.
7. **Exclusions**: R2 is not retested (no evidence of benefit in Phase 10). R1 and R5 remain permanently skipped.

---

## 6. Invalidation of Prior Detector-Clipped Queue Data

All numerical results, tables, and claims in documentation from Phases 7 through 10 regarding `max_queue_m` reflect sensor clipping at the detector lead-vehicle setback ($\approx 24.00\text{ m}$) rather than unconstrained physical queue extent. 

They are hereby recognized as detector-clipped artifact measurements and shall not be cited as physical queue bounds or evidence of queue suppression. All subsequent queue assessments will be based on microscopic ground-truth tracking.
