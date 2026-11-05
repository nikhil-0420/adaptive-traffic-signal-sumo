# DP1 Research Pre-Registration

## 1. Research Question
"Does queue-aware adaptive control improve p95 waiting time, peak queue and directional fairness under non-stationary demand, without a mean-waiting-time penalty versus Webster-based fixed-time control?"

## 2. Seed Roles and Partitioning
- **Seeds 101–105 (Development)**: Algorithm design, iterative prototyping, debugging, hyperparameter tuning, and UI testing.
- **Seeds 106–110 (Validation)**: Hypothesis testing, model selection, and gating rung-by-rung ablation accept/reject decisions.
- **Seeds 121–130 (Exploratory / Burned)**: Pre-existing pilot evaluation data (`exp_marathahalli_hybrid_840`). Strictly exploratory; never used for tuning, selection, or acceptance.
- **Seeds 131–150 (Final Evaluation)**: Held-out final benchmark evaluation. Untouched until Phase 14; never opened, simulated, or analyzed during development or validation.

## 3. Metric Hierarchy
- **Primary Metrics**:
  1. `p95 wait` (95th percentile vehicle waiting time in seconds)
  2. `max queue` (peak approach queue length in metres, MAX over lane queue extents)
  3. `approach wait gap` (directional fairness: max approach mean wait minus min approach mean wait in seconds)
- **Secondary Metrics**:
  - `mean wait` (seconds)
  - `mean queue` (metres)
  - `throughput` (completed trips per hour)
  - `completion rate` (percentage of departed vehicles that reached their destination)
  - `unfinished vehicles` (number of vehicles remaining on the network at sim termination)
  - `switches per hour` (signal cycle switching frequency)
- **Context Only**:
  - `time loss` (SUMO simulated delay; not renamed signal delay)
  - `trip duration` (seconds)

## 4. Reference Policies for Paired Deltas
- **Primary Reference**: `webster_measured` (dynamically matched Webster timing using measured approach arrivals, defined in Phase 9).
- **Secondary Reference**: `fixed` (BTP-adapted fixed-time baseline: 105 s EW green, 95 s NS green, 3 s yellow, 2 s all-red).

## 5. Statistical Protocol
- **Bootstrap Method**: Paired bootstrap percentile confidence intervals.
- **Resamples**: 10,000 resamples per comparison.
- **Fixed Bootstrap Random Seed**: `42` (recorded in `dp1/config.py:RESEARCH.bootstrap_seed` and in this protocol).
- **Multiple Comparisons Correction**: Holm–Bonferroni correction applied across the 3 primary metrics.
- **Sample Reporting**: Report exact paired sample counts ($N$).
- **Inference Invariant**: A paired confidence interval spanning zero denotes that the difference is **"not distinguished"** under the test, **never** that the policies are "equal".

## 6. Acceptance Rule for Ablation Rungs
When comparing a candidate rung against the immediately preceding rung on validation seeds (106–110):
- **Keep candidate rung if and only if**:
  1. At least one primary metric improves with its paired bootstrap 95% confidence interval strictly excluding zero; **AND**
  2. Grand-mean waiting time does not degrade by more than 1.0%; **AND**
  3. Network completion rate does not decrease and unfinished vehicle count does not increase.

## 7. Final Evaluation Matrix (To Be Frozen in Phase 13)
- **Main Evaluation Matrix**:
  - 10 Main Policies $\times$ 18 Demand Conditions (12 stationary [4 patterns $\times$ 3 levels] + 6 non-stationary [ramp_peak, surge_shift, lane_closure $\times$ levels]) $\times$ 20 Seeds (131–150) = **3,600 runs**.
- **Ablation Sub-Matrix**:
  - 3 Ablation Variants $\times$ 9 Selected Conditions $\times$ 20 Seeds (131–150) = **540 runs**.
- **Total Final Benchmark Runs**: **4,140 runs**.

## 8. Integrity and Transparency Statement
All experimental cells will be reported in full. Unfavourable, neutral, or negative results will be presented transparently without selective omission, post-hoc metric reweighting, or synthetic manipulation.
