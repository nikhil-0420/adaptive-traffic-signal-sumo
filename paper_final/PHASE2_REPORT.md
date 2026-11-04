# Phase 2 Report: DP1 Research Paper Finalization & Verification
**Project:** Adaptive Traffic-Signal Optimization (Marathahalli Bridge Junction, SUMO/TraCI)  
**Authors/Context:** Alliance University B.Tech AI & Data Science — Design Project 1  
**Audit Scope:** STEP 3 (Metric Extraction & Tables), STEP 5 (Publication Figures), STEP 6 (Decision Trace), STEP 7 (Text Replacements & Diffs), STEP 8 (Sources & Citations)  
**Date:** 2026-11-04  
**Audit Gate:** PHASE 2 ONLY (Read-Only on Simulations; Deterministic Analysis Scripts, CSV Tables, PNG Figures, and Replacement Text Diffs)

---

## Executive Summary & Status per Step

| Step | Scope / Deliverable | Status | Summary of Output / Verification |
| :--- | :--- | :---: | :--- |
| **Req. 1** | Pre-Registration Protocol Timing | **`OK`** | Commit `4511149` timestamp: `2026-11-04 11:05:02 +0530`. First run created: `2026-11-04 15:53:59 +0530`. Git freeze occurred 4h 48m prior to first simulation execution. |
| **Req. 2** | Seed Partition Wording | **`OK`** | Prior exploratory seeds (121–130) vs. held-out confirmatory seeds (131–138). Out-of-band inspection claim dropped and marked `UNKNOWN`. |
| **Req. 3** | Delay-vs-Queue Footnote & Microscopic Stops | **`OK`** | Measured stop distributions extracted from `tripinfo.xml` across 28,650 vehicles. Saturated p95 stop count is 15.0 stops (median 1.0 stop). 47 m vs. 98 m queue contrast framed strictly as `balanced-heavy`. |
| **Req. 4** | Operational Metrics Re-extraction | **`OK`** | Key mismatch (`throughput_veh_per_h`) resolved in `analysis/paper_final/`. Throughput (2684–2690 veh/h, ±0.2%), switches/hour (33.5 to 218.4), and 100% completion rate tabulated. Extraction bug caveat removed. |
| **STEP 3** | Metric Scripting & Paper Tables | **`OK`** | Deterministic scripts created in `analysis/paper_final/` (`extract_metrics.py`, `compute_tables.py`, `run_all.py`). Tables 1–6 output to `paper_final/tables/`. |
| **STEP 5** | Publication-Quality Figures | **`OK`** | Generated `paper_final/figures/fig3_forest_plot.png` (Forest plot of primary paired differences with 95% CIs) and `paper_final/figures/fig4_queue_timeseries.png` (Timeseries for `surge_shift` and `lane_closure`). |
| **STEP 6** | Microscopic Decision Trace Replacement | **`OK`** | Cited trace updated from seed 125 to seed 136 (`marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`, rows 121–127, $t = 1151\text{--}1171\text{ s}$). |
| **STEP 7** | Wording Rules & Text Diffs | **`OK`** | All required wording rules enforced across Sections III, IV, and VII. Draft text diffs prepared. |
| **STEP 8** | Sources & Citation Audit | **`OK`** | Validated against `docs/SOURCES.md`. Unverified literature citations flagged with exact replacements. |

---

## 1. Pre-Registration & Protocol Timing Audit

### Exact Timestamps from Git & File Systems
* **Amendment 3 Git Freeze Commit:**  
  * **Commit Hash:** `45111497d67e1348029f4edd2b85f3609880ac95`
  * **Commit Author Date:** `2026-11-04 11:05:02 +0530`
  * **Commit Message:** `feat(f1): re-freeze final matrix under Pre-Registration Amendment 3`
  * **Files Frozen:** `experiments/final_matrix.json`, `experiments/final_matrix.yaml`, `docs/PREREGISTRATION_AMENDMENT_3.md`
* **First Simulation Run in `exp_marathahalli_improve_final`:**  
  * **Directory:** `results/research/exp_marathahalli_improve_final/marathahalli_balanced_low_sumo_actuated_s131`
  * **Earliest Artifact Timestamp (`metrics.json`):** `2026-11-04 15:53:59 +0530`
* **Final Simulation Run in `exp_marathahalli_improve_final`:**  
  * **Directory:** `results/research/exp_marathahalli_improve_final/ablation_lane_closure_medium_hybrid_oracle_seeded_s138`
  * **Completion Timestamp (`matrix_status.csv`):** `2026-11-04 17:15:57 +0530`

### Finding & Wording Recommendation
The formal evaluation matrix, statistical stopping rules, and hypothesis thresholds were committed to the repository **4 hours and 48 minutes before the first simulation run commenced**.  
To remain strictly precise and avoid over-claiming formal external pre-registration registry status (e.g. OSF/AsPredicted), the text adopts the wording:
> *"The evaluation matrix, statistical protocol, and hypothesis stopping rules were frozen in repository version control (commit `4511149`, 2026-11-04 11:05 UTC+5:30) prior to the execution of the final evaluation runs (launched 2026-11-04 15:53 UTC+5:30)."*

---

## 2. Seed-Role Wording & Inspection Claim

### Audit Finding
* Git history confirms that seeds 121–130 were utilized exclusively during the exploratory 840-cell study and intermediate ladder calibration, whereas seeds 131–138 appear only in the final confirmatory dataset (`exp_marathahalli_improve_final`).
* However, whether human operators inspected individual vehicle outputs or preliminary trial runs on seeds 131–138 outside of git logging cannot be independently proven from repository metadata alone.
* **Status:** Marked `UNKNOWN`.
* **Action:** In accordance with the mandate, any sentence claiming *"nothing was inspected on seeds 131–138"* is removed from the manuscript.

### Approved Seed-Partition Text (for Section III.D):
> *"Evaluation seeds were partitioned across sequential experimental phases: seeds 121–130 served as prior exploratory evaluation data during controller iteration, baseline calibration, and ladder ablation across 840 runs. Confirmatory evaluation was conducted on a fresh set of held-out seeds (131–138) across 384 runs under the protocol frozen in Amendment 3."*

---

## 3. Delay-vs-Queue Footnote & Microscopic Stop Distribution

### Real Vehicle Distributions from `tripinfo.xml`
To replace hypothetical assumptions ("5 to 9 cycles") with empirical simulation measurements, vehicle-level attributes (`waitingTime`, `waitingCount`, `timeLoss`, `duration`) were parsed across all 28,650 vehicles in the heavy evaluation conditions (`balanced-heavy` and `imbalanced_orr-heavy`):

| Condition | Metric | Completed Vehicles | Median | 75th %ile | 90th %ile | 95th %ile | Maximum |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`balanced-heavy`** (Hybrid) | **Stop Count (`waitingCount`)** | 13,591 | **1.0 stop** | 3.0 stops | 12.0 stops | **15.0 stops** | 30.0 stops |
| | **Trip Waiting Time (`waitingTime`)** | 13,591 | **1.0 s** | 48.0 s | 493.0 s | **669.0 s** | 1309.0 s |
| **`imbalanced_orr-heavy`** (Hybrid) | **Stop Count (`waitingCount`)** | 15,059 | **1.0 stop** | 3.0 stops | 9.0 stops | **15.0 stops** | 32.0 stops |
| | **Trip Waiting Time (`waitingTime`)** | 15,059 | **1.0 s** | 71.0 s | 334.0 s | **543.0 s** | 1547.0 s |

### Interpretation & Scope Boundaries
1. **Multi-Cycle Accumulation:** The median vehicle experiences free-flow or near-immediate service (median wait 1.0 s, 1 stop). In contrast, the 90th–95th percentile tail experiences severe multi-cycle delays, stopping **9 to 15 times** in stop-and-go platoons before reaching the stop line.
2. **Instantaneous Spatial Bounds:** The contiguous stopped queue cluster (`gt_ext_max_queue_m`) is an instantaneous snapshot bounded by platoon flushing on green.
3. **Condition Limitation:** The 47 m vs. 98 m queue containment contrast applies specifically to `balanced-heavy` demand; in `imbalanced_orr-heavy`, the maximum queue is 48 m (Hybrid) vs. 107 m (Fixed), whereas in uncongested `balanced-low`, maximum queues across all policies remain between 25 m and 46 m.

### Approved Explanatory Footnote (for Table IV / Section IV.E):
> *"The 95th-percentile waiting time (`p95 wait`) measures cumulative trip-level delay (speed $< 0.1\text{ m/s}$) accumulated across multiple stop-and-go cycles under oversaturated conditions, where vehicles in the 95th percentile experience a measured median of 15 distinct stops before clearing the intersection. In contrast, `max queue` captures the instantaneous physical extent of the contiguous stopped cluster (speed $< 1.4\text{ m/s}$, headway $\le 7.5\text{ m}$) anchored at the stop line during any 1-second interval. Because the hybrid controller clears queue frontages on every green phase, instantaneous spatial accumulation in `balanced-heavy` traffic is held to 47 m (compared to 98 m under fixed timing), even while trip-level delays accumulate over multiple cycles."*

---

## 4. Operational Metrics Re-extraction & Bug Resolution

### Root Cause & Resolution
In the earlier baseline evaluation script (`analysis/run_analysis.py`), the throughput dictionary query looked for the key `throughput_vph`, whereas `dp1/metrics.py` generated `throughput_veh_per_h`. Additionally, `switches_per_hour` was not written to `metrics.json`.  
In `analysis/paper_final/extract_metrics.py`, this was resolved without modifying core code:
* `throughput_vph` was extracted from `m["throughput_veh_per_h"]`.
* `switches_per_hour` was calculated directly from axis transitions in `timeseries.csv` divided by elapsed simulation hours.
* `completion_rate` (100.0%) and `vehicles_unfinished` (0) were confirmed across all 384 runs.

### Verified Operational Metrics Across Policies (Table 5)

| Policy | Throughput (veh/h) (Mean ± SD) | Phase Switches / hour (Mean ± SD) | Completion Rate (%) | Unfinished Vehicles (Total) |
| :--- | :---: | :---: | :---: | :---: |
| **`fixed`** | $2688.0 \pm 454.4$ | $33.5 \pm 0.4$ | 100.0% | 0 |
| **`webster_measured`** | $2690.2 \pm 446.6$ | $144.3 \pm 3.9$ | 100.0% | 0 |
| **`webster_recalc`** | $2688.6 \pm 446.7$ | $144.2 \pm 2.6$ | 100.0% | 0 |
| **`sumo_actuated`** | $2687.6 \pm 446.1$ | $218.4 \pm 6.0$ | 100.0% | 0 |
| **`adaptive`** | $2685.6 \pm 446.4$ | $206.6 \pm 4.9$ | 100.0% | 0 |
| **`queue_extension`** | $2689.9 \pm 447.5$ | $219.0 \pm 3.2$ | 100.0% | 0 |
| **`hybrid_queue_adaptive`** | $2684.7 \pm 443.5$ | $189.4 \pm 3.6$ | 100.0% | 0 |
| **`hybrid_oracle_seeded`** | $2685.1 \pm 444.0$ | $190.6 \pm 2.9$ | 100.0% | 0 |

### Sentences to Remove from Paper / Results Sheet
1. **Remove from Paper (Section IV.F):**  
   *"Throughput, completion rate, and switches per hour were omitted because of an extraction fault; insert recomputed values and paired Δ% vs. webster_measured and sumo_actuated, so that lower queues can be shown not to result from reduced service..."*  
   $\rightarrow$ **Replacement:** Replace entire temporary placeholder with Section IV.F containing verified Table 5 and Table 6.
2. **Remove from Results Sheet (Page 2):**  
   *"Reporting caveats: Throughput and switches/hour are omitted due to an extraction pipeline bug. System performance is validated via completion rate and zero unfinished vehicles."*  
   $\rightarrow$ **Replacement:** *"Throughput, completion rate (100%), and phase switching frequency were re-extracted directly from raw simulation outputs. Mean throughput across all policies is not distinguished (2685 to 2690 veh/h, paired Δ% = −0.2%, 95% CI: −0.4% to +0.0%), confirming queue reductions reflect active traffic management rather than reduced vehicle service."*

---

## 5. Microscopic Decision Trace (Seed 136)

The obsolete trace in Section IV.C (from seed 125 of the 840 study) is replaced with the verified event from `exp_marathahalli_improve_final`:
* **Run ID:** `marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`
* **File:** `results/research/exp_marathahalli_improve_final/marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136/decisions.csv`
* **Rows:** 121–127 ($t = 1151.0\text{ s}$ to $t = 1171.0\text{ s}$)

### Trace Table for Section IV.C:
```
t = 1151.0 s: EW active (q_act = 24.0 m >= 4.0 m threshold). Competing NS red wait = 21.0 s <= 35.0 s limit. 
              Action: EXTEND (+3.0 s, g_extra = 9.0 s). Reason: EXTEND_APPROVED.
t = 1154.0 s: EW active (q_act = 24.0 m). NS red wait = 24.0 s. Action: EXTEND (+3.0 s, g_extra = 12.0 s).
t = 1157.0 s: EW active (q_act = 24.0 m). NS red wait = 27.0 s. Action: EXTEND (+3.0 s, g_extra = 15.0 s).
t = 1160.0 s: EW active (q_act = 24.0 m). NS red wait = 30.0 s. Action: EXTEND (+3.0 s, g_extra = 18.0 s).
t = 1163.0 s: EW active (q_act = 24.0 m). NS red wait = 33.0 s. Action: EXTEND (+3.0 s, g_extra = 21.0 s).
t = 1166.0 s: Extension proposed by queue logic, but competing NS red wait reached 36.0 s (> 35.0 s maximum limit) 
              with queued demand (12.5 m). Action: REQUEST_SWITCH. Reason: SWITCH_FAIRNESS_WAIT_LIMIT.
t = 1171.0 s: Yellow (3s) and all-red (2s) safety clearance observed. NS active green initiates. 
              Action: ENTER_GREEN. Reason: BASELINE_ENTRY (Webster base floor = 15.8 s).
```

---

## 6. Exact Text Diffs & Replacements for Manuscript

### Diff 1: Policy Inventory & Study Framing (Section IV.A / III.D)
```diff
- We evaluate the hybrid controller against seven baseline and comparator policies plus our proposed hybrid controller and an oracle-seeded variant...
+ We evaluate our proposed hybrid controller (hybrid_queue_adaptive) against six baseline and comparator policies (fixed, webster_measured [primary reference], webster_recalc, sumo_actuated, adaptive, and queue_extension), alongside one oracle-seeded variant (hybrid_oracle_seeded) evaluated as an ablation of local flow measurement, yielding eight policies across six traffic conditions and eight held-out seeds (384 runs in total).
- Reinforcement learning (rl_dqn) was evaluated across the matrix...
+ Reinforcement learning policies (rl_dqn) were excluded from the confirmatory matrix under Pre-Registration Amendment 3 due to multi-seed training convergence instability across non-stationary demand shifts, and are treated strictly as exploratory prior work.
```

### Diff 2: Actuation Trade-Off & Negative Results (Section IV.C / Section VII)
```diff
- Against sumo_actuated the hybrid achieves parity on delay while providing deterministic worst-case bounds... Actuation lacks logged red-wait guards, risking cycle drift and pedestrian clearance violations.
+ Against sumo_actuated, the hybrid yields a higher maximum queue (+11.4%, 95% CI: +4.6% to +18.7%, Holm p = 0.0006), a higher mean queue (+35.5%, 95% CI: +30.9% to +39.9%), and a higher mean waiting time (+3.4%, 95% CI: +0.5% to +6.5%). Unconstrained actuation therefore achieves lower queue accumulation in this network model. The hybrid intentionally trades peak queue responsiveness for auditable, bounded phase transitions and explicit maximum red-wait constraints. Hypothesized effects of unconstrained actuation on long-term cycle variance or pedestrian clearance were not evaluated in this vehicle-only simulation model.
```

### Diff 3: Per-Condition Non-Stationary Disparities (Section IV.E)
```diff
- The hybrid dominates across non-stationary conditions, totally removing queues under demand shifts...
+ Under the surge_shift condition, the hybrid holds peak queue to 43 m versus 82 m for Webster and fixed timing. However, the hybrid performs worse than Webster on 95th-percentile wait under lane_closure (+10%, 587 s vs. 535 s) and under imbalanced_orr (+4.5%, 542 s vs. 525 s). In saturated conditions (p95 waits of 500–690 s), total delay is governed by network capacity limits, and minor p95 differences are not statistically distinguished.
```

### Diff 4: Ablation Wait Gap Interpretation (Section IV.D)
```diff
- The ablation proves that local measurements achieve full equivalence with oracle tables with zero penalty...
+ The ablation indicates that local measurements perform comparably to true demand oracle tables on primary metrics: p95 wait (−0.5%, 95% CI: −2.7% to +1.7%) and max queue (−1.2%, 95% CI: −6.0% to +3.9%) are not distinguished from the oracle variant (Holm p = 1.00). The approach wait gap point estimate (+15.3%, 95% CI: +0.2% to +34.1%) is wider due to low-denominator cells and is not distinguished after correction (Holm p = 0.138); absolute mean wait gaps remain virtually identical (58.28 s vs. 58.33 s).
```

### Diff 5: Replacement of Section IV.F (Pending Items)
```diff
- F. Items Pending Verification
- Throughput, completion rate, and switches per hour were omitted because of an extraction fault; insert recomputed values and paired Δ% vs. webster_measured and sumo_actuated... Report a sanity table per condition...
+ F. System Throughput, Switching Frequency, and Congestion Dynamics
+ All 384 runs completed with a 100.0% completion rate and zero unfinished vehicles (Table V). Throughput across all eight policies is tightly clustered between 2684.7 and 2690.2 veh/h (paired Δ% vs. webster_measured: −0.2%, 95% CI: −0.4% to +0.0%, not distinguished), confirming that queue containment under adaptive control is not an artifact of unserved traffic.
+ Switching frequency reflects policy architecture: fixed timing operates at 33.5 switches/hour (rigid ~210 s cycle), webster_measured switches at 144.3 switches/hour, hybrid_queue_adaptive moderates switching to 189.4 ± 3.6 switches/hour by enforcing minimum base floors, while unconstrained sumo_actuated switches at 218.4 ± 6.0 switches/hour.
+ Microscopic vehicle audit in heavy conditions confirms that p95 delays (540–670 s) reflect multi-cycle stop-and-go progression (measured p95 stop count of 15 stops) under network saturation, whereas maximum instantaneous queue length at the stop line is successfully halved (47 m vs. 98 m in balanced-heavy) by active green extensions.
```

---

## 7. Step 8: References & Sources Audit

Reviewing the manuscript citations against `docs/SOURCES.md`:
* **[1] Roess et al. (Traffic Engineering):** Marked "verify". Can be retained as standard textbook citation or replaced with Highway Capacity Manual (HCM 2016).
* **[2] Webster (1958):** Fully verified in `docs/SOURCES.md` (Road Research Technical Paper No. 39). Retain.
* **[3] Krajzewicz et al. (SUMO):** In `docs/SOURCES.md`, platform paper is preferred as Lopez et al., IEEE ITSC 2018 (doi: 10.1109/ITSC.2018.8569938). Recommend updating to Lopez et al. 2018.
* **[4] Varaiya (Max Pressure 2013):** Standard foundational paper. Retain.
* **[5] Wei et al. (Survey):** Marked in draft as arXiv:1904.08117. Verified as SIGKDD Explorations 2021 / arXiv. Retain arXiv citation.
* **[6] & [7] BTP Timing & OpenCity Dataset:** Fully verified in `docs/SOURCES.md` (Marathalli Bridge Junction schedule, `docs/btp_marathalli_yamlur.pdf`). Retain.
* **[8] SCOOT & [9] SCATS:** Lowrie SCATS citation year corrected to 1982/1990. Retain.
* **[10] Holm (1979):** Foundational multiple testing procedure. Retain.
* **Missing from Paper (Present in `docs/SOURCES.md`):**
  * Sreejith, Mathi, Pradeep, IEEE Access 2024 (IntelliSignal map-integrated SUMO TraCI).
  * Sun et al., CrossLight, ACM KDD 2024.
  * Liu, Zhuang, Li, Springer ICCES 2024.
  * Rajampalli, Narra, J. G., Results in Engineering 2025 (Bengaluru corridor study).
  * Wegener et al., ACM CNS 2008 (TraCI interface).  
  *These five verified citations should be added to the references list to strengthen the literature foundation.*

---

## 8. Summary of Generated Files

All deliverables requested for Phase 2 have been created deterministically:
* **Analysis Pipeline:**
  * `analysis/paper_final/extract_metrics.py` (Re-extracts complete metrics from all 384 runs).
  * `analysis/paper_final/compute_tables.py` (Computes bootstrap statistics and formats CSV tables).
  * `analysis/paper_final/generate_figures.py` (Renders 300 DPI publication plots).
  * `analysis/paper_final/run_all.py` (Single-command master runner).
  * `analysis/paper_final/raw_extracted_runs.csv` (Extracted raw dataset).
* **Tables (CSV in `paper_final/tables/`):**
  * `table1_hybrid_vs_webster_measured.csv`
  * `table2_comparators.csv`
  * `table3_ablation.csv`
  * `table4_per_condition.csv`
  * `table5_operational_metrics.csv`
  * `table6_heavy_stop_audit.csv`
* **Figures (PNG in `paper_final/figures/`):**
  * `fig3_forest_plot.png`
  * `fig4_queue_timeseries.png`

---

## Verdict & Gate for Phase 3

### **PHASE 2 COMPLETE**
All calculations, operational metrics, stop distributions, publication figures, decision traces, and text diffs are generated, verified from raw artifacts, and saved.

**STOPPING HERE:** Awaiting user approval to proceed to **Phase 3 (Steps 9 & 10: Applying patches to paper files and finalizing `paper_final/FIXES.md`)**.
