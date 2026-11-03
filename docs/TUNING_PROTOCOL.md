# Pre-Registered Tuning Protocol: Equal-Budget Policy Optimization (Phase 11)

**Date:** 2026-11-03  
**Status:** Frozen and Pre-Registered (Prior to Search Execution)  
**Parent Documents:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md), [`docs/PREREGISTRATION_AMENDMENT_1.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_1.md), [`docs/PREREGISTRATION_AMENDMENT_2.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_2.md), [`docs/ablation_ladder.md`](file:///e:/dp1-traffic-signal/docs/ablation_ladder.md)

---

## 1. Research Objective & Equal-Budget Guarantee

The objective of Phase 11 is to tune the proposed controller (`hybrid_queue_adaptive`, with kept-rung R4 de-oracling) and its closest adaptive competitors (`queue_extension`, `adaptive`) under an **identical evaluation budget**. 

By allocating the exact same number of trials, identical condition matrices, identical training seeds, and identical sampling mechanisms across all policies, any performance advantage observed in Phase 12+ benchmarking reflects **genuine architectural merit**, not disparate hyperparameter optimization effort.

---

## 2. Policies & Search Method

### Tuned Policies (3):
1. **`hybrid_queue_adaptive`**: Proposed hybrid controller with kept rung `rungs = ("R4",)` (empirical 300s warm-up Webster base green; R1, R2, R3, R5 cut).
2. **`queue_extension`**: Closest competitor; dynamic queue extension with anti-monopoly bounding.
3. **`adaptive`**: Baseline queue-proportional adaptive controller.
*(Note: `pressure` is excluded per user instruction unless explicitly requested).*

### Search Algorithm:
- **Method:** Reproducible Random Search with fixed pseudorandom number generator seed (`numpy.random.default_rng(202611)`).
- **Parity:** Evaluates the identical number of candidate configurations ($K = 30$) for every policy.
- **Trial Identifier:** Monotonically increasing integers `trial_00` to `trial_29` per policy.

---

## 3. Equal Budget Specification

### Per-Run Timing Benchmark (Marathahalli Network, SUMO 1.28):
- 1 simulation run: $\approx 0.30\text{ s}$ CPU time ($\sim 0.075\text{ s}$ wallclock with 4 parallel worker processes).
- 1 trial = 18 demand conditions $\times$ 5 training seeds (101–105) = **90 simulation runs**.
- Wallclock time per trial: $90 \times 0.075\text{ s} \approx 6.75\text{ s}$.

### Total Tuning Budget Table:

| Policy | Trials ($K$) | Conditions | Train Seeds | Total Runs | Wallclock Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `hybrid_queue_adaptive` | 30 | 18 | 5 (101–105) | 2,700 | $\approx 3.4\text{ min}$ |
| `queue_extension` | 30 | 18 | 5 (101–105) | 2,700 | $\approx 3.4\text{ min}$ |
| `adaptive` | 30 | 18 | 5 (101–105) | 2,700 | $\approx 3.4\text{ min}$ |
| **Search Phase Total** | **90** | **18** | **5** | **8,100** | **$\approx 10.2\text{ min}$ (0.17 h)** |

### Top-3 Validation Budget:
- Top 3 candidates per policy evaluated on **Validation Seeds (106–110)**:
  - 3 candidates $\times$ 18 conditions $\times$ 5 validation seeds = **270 runs per policy** ($\approx 20\text{ s}$ per policy $\implies \approx 1.0\text{ min}$ total).
- **Grand Total Phase 11 Simulation Runs:** $8,100 + 810 = 8,910$ runs ($\approx 11.2\text{ min}$ total runtime).

---

## 4. Search Spaces per Policy

All parameters are strictly bounded to physically viable and stable ranges. Safety constants are fixed.

### Policy 1: `hybrid_queue_adaptive` (Kept Rungs: R4 de-oracle active)
*Note: Hard cap (35s) and max green (60s) are safety invariants and held fixed.*

| Parameter | Type | Min | Max | Default | Scale | Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `extend_step_s` | float | 1.0 | 5.0 | 3.0 | Linear | Extension increment granted per evaluation. Balances fine granularity vs switching stability. |
| `extend_threshold_m` | float | 2.0 | 10.0 | 4.0 | Linear | Minimum active queue required to justify extension. |
| `fairness_ratio` | float | 0.8 | 2.0 | 1.2 | Linear | Ratio of competing queue accumulation vs active queue triggering demand fairness switch. |
| `gap_out_s` | float | 1.5 | 5.0 | 3.0 | Linear | Persistent vacancy duration required to trigger early gap-out switch. |
| `min_competing_queue_m` | float | 1.0 | 5.0 | 2.0 | Linear | Opposing queue threshold required before anti-monopoly / fairness checks activate. |
| `max_competing_wait_s` | float | 20.0 | 45.0 | 35.0 | Linear | Soft wait limit and urgency denominator scaling opposing corridor red delay. |
| `r4_warmup_s` | float | 180.0 | 420.0 | 300.0 | Linear | Duration of warm-up arrival counting window before solving Webster baseline green. |
| `demand_weight_active` | float | 0.5 | 1.5 | 1.0 | Linear | Weight on active approach queue in demand score. |
| `demand_weight_competing`| float | 0.5 | 1.5 | 1.0 | Linear | Weight on competing approach queue in demand score. |
| `arrival_detection_threshold` | float | 0.2 | 1.5 | 0.5 | Linear | Minimum queue increment $\Delta Q$ to detect incoming arrivals. |

### Policy 2: `queue_extension`

| Parameter | Type | Min | Max | Default | Scale | Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `initial_green_s` | float | 10.0 | 25.0 | 15.0 | Linear | Baseline green allocated upon phase entry prior to dynamic extensions. |
| `extend_step_s` | float | 1.0 | 5.0 | 3.0 | Linear | Extension increment granted per evaluation. |
| `extend_threshold_m` | float | 2.0 | 10.0 | 4.0 | Linear | Minimum active queue required to justify extension. |
| `min_competing_queue_m` | float | 1.0 | 5.0 | 2.0 | Linear | Competing queue threshold required before fairness switches activate. |
| `max_competing_wait_s` | float | 20.0 | 45.0 | 35.0 | Linear | Maximum red wait time for competing axis before switch is forced. |
| `fairness_ratio` | float | 0.8 | 2.0 | 1.2 | Linear | Ratio of competing queue pressure vs active queue triggering switch. |
| `gap_out_s` | float | 1.5 | 5.0 | 3.0 | Linear | Vacancy duration required to trigger early gap-out switch. |

### Policy 3: `adaptive`

| Parameter | Type | Min | Max | Default | Scale | Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `k_s_per_m` | float | 0.10 | 0.60 | 0.30 | Linear | Green scaling sensitivity factor (seconds of green per metre of queue). |
| `extend_threshold_m` | float | 5.0 | 25.0 | 15.0 | Linear | Queue threshold to continue extending green while queue is long. |
| `gap_out_s` | float | 1.0 | 5.0 | 3.0 | Linear | Time threshold to terminate green early once own queue is cleared. |
| `min_competing_queue_m` | float | 0.5 | 4.0 | 1.0 | Linear | Minimum competing queue required to permit gap-out switch. |

### Safety Invariants (Fixed Constants Across All Policies):
- `min_green_s`: **10.0 s**
- `max_green_s`: **60.0 s**
- `yellow_s`: **3.0 s**
- `all_red_s`: **2.0 s**

---

## 5. Trial Validity Constraints & Pruning

A trial configuration is strictly **invalid** and pruned without simulation if:
1. `min_green_s < 10.0` or `max_green_s > 60.0` or `min_green_s >= max_green_s`.
2. Any parameter falls outside its defined `[min, max]` search range.
3. Clearance intervals violate $\text{yellow} = 3.0\text{ s}$ or $\text{all\_red} = 2.0\text{ s}$.

### Crash & Timeout Failure Definition:
- A trial is flagged as **FAILED (CRASHED)** if:
  - Any simulation run exits with a non-zero exit code or SUMO runtime exception.
  - Simulation execution hangs or exceeds $2\times$ the maximum expected drain duration ($> 3600\text{ s}$).
  - A failed trial is **never deleted**; it is recorded in `results/tuning/<policy>/trials.csv` with status `FAILED`, and assigned a penalty composite of $\infty$.

---

## 6. Frozen Evaluation Objective

The tuning objective function is **frozen** and evaluates multi-objective traffic efficiency and equity normalized against the field-deployable measured Webster baseline:

$$\text{Composite Score} = \frac{1}{18} \sum_{c=1}^{18} \left( 0.4 \times \frac{\bar{W}_{c}}{\bar{W}_{c}^{\text{webster\_measured}}} + 0.3 \times \frac{P95_{c}}{P95_{c}^{\text{webster\_measured}}} + 0.3 \times \frac{\text{Gap}_{c}}{\text{Gap}_{c}^{\text{webster\_measured}}} \right)$$

Where for each demand condition $c \in \{1, \dots, 18\}$ across training seeds 101–105:
- $\bar{W}_{c}$: Mean waiting time across departed vehicles.
- $P95_{c}$: 95th percentile vehicle waiting time.
- $\text{Gap}_{c}$: Approach wait gap ($\max_a \bar{w}_a - \min_a \bar{w}_a$).
- $\bar{W}_{c}^{\text{webster\_measured}}, P95_{c}^{\text{webster\_measured}}, \text{Gap}_{c}^{\text{webster\_measured}}$: Reference performance of `webster_measured` on the exact same condition $c$ and seeds 101–105.

**Optimization Direction:** Minimize composite score (lower is better; score $< 1.0$ indicates superior performance relative to `webster_measured`).

---

## 7. Model Selection & Gating Protocol

1. **Training Phase (Seeds 101–105):**
   - Each policy executes 30 trials across all 18 demand conditions on training seeds 101–105.
   - Trials are ranked by training composite score.
   - The top 3 candidates per policy are identified.

2. **Validation Gating (Seeds 106–110):**
   - Top 3 candidates are evaluated across all 18 conditions on **held-out validation seeds 106–110** ($n=5$).
   - The final winning configuration is selected strictly by **lowest validation composite score**.
   - **Tie-Breaker:** If validation composite scores differ by $< 0.005$, the candidate with lower validation $p_{95}$ wait is chosen.

3. **Freezing Artifacts:**
   - Winning configurations are frozen as:
     - `configs/final_hybrid_queue_adaptive.yaml`
     - `configs/final_queue_extension.yaml`
     - `configs/final_adaptive.yaml`
   - Containing: exact parameters, trial ID, training composite, validation composite, git commit SHA, and timestamp.
   - **Zero tuning or modifications** are permitted after freezing.
   - Evaluation seeds (121–130, 131–150) remain strictly untouched.
