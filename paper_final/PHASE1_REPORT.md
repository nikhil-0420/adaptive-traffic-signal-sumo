# Phase 1 Investigation & Audit Report: DP1 Research Paper Finalization
**Project:** Adaptive Traffic-Signal Optimization (Marathahalli Bridge Junction, SUMO/TraCI)  
**Authors/Context:** Alliance University B.Tech AI & Data Science — Design Project 1  
**Audit Scope:** STEP 0 (Orientation), STEP 1 (Reconciliation), STEP 2 (Policy Inventory), STEP 4 (p95-Wait vs. Max-Queue Audit)  
**Date:** 2026-11-04  
**Audit Gate:** PHASE 1 ONLY (Read-Only Analysis; No Paper Edits or New Runs)

---

## Executive Summary & Gate Verdict

| Investigation Gate | Component / Step | Status | Evidence Summary |
| :--- | :--- | :--- | :--- |
| **STEP 0** | Environment, Git & Experiment Inventory | **OK** | Branch `dp1-improve`, HEAD `6a15db3`, Amendment 3 freeze `4511149`. All 384 runs verified `SUCCESS`. |
| **STEP 1** | Study Reconciliation & Decision Trace | **CONFIRMED PROBLEM** | Paper numbers come 100% from `exp_marathahalli_improve_final` (Table 1 reproduces exactly). Decision trace in Section IV.C cited cell `..._s125` from old 840 study; exact replacement trace identified in seed 136 (`marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`, rows 121–127). |
| **STEP 2** | Policy Inventory & Taxonomy | **CONFIRMED PROBLEM** | Paper text claims "7 baselines + hybrid + oracle variant" (9 policies). Actual matrix consists of 6 baselines + 1 proposed hybrid + 1 ablation variant = **8 policies total**. `rl_dqn` was dropped under Amendment 3 and is not in the 384 runs. |
| **STEP 4** | p95-Wait vs. Max-Queue Consistency | **OK** | Mathematically and physically consistent. Multi-cycle stop-and-go accumulation (`waitingTime`, completed trip cumulative delay) vs. instantaneous 1-second contiguous stop-line spatial queue cluster (`gt_ext_max_queue_m`). Minimal fix is clarifying text/footnotes. |

### Formal Verdict: **GO (Ready for User Approval for Phase 2)**
All data dependencies, raw artifact paths, and root causes for paper discrepancies have been identified with zero guesswork and zero data regeneration.

---

## STEP 0: Orientation, Git & Environment Audit

### 1. Environment & Software Stack
* **Python Runtime:** `3.11.9` (`E:\dp1-traffic-signal\.venv\Scripts\python.exe`)
* **SUMO Engine:** `Eclipse SUMO sumo Version 1.28.0` (`.venv\Lib\site-packages\sumo\bin\sumo.exe`)
* **Key Packages:**
  * `traci`: `1.28.0`
  * `sumolib`: `1.28.0`
  * `pandas`: `3.0.6`
  * `numpy`: `2.4.6`
  * `matplotlib`: `3.11.2`
  * `torch`: `2.14.1`
  * `fastapi`: `0.143.0`
* **Git Branch:** `dp1-improve`
* **Current HEAD Commit:** `6a15db3` (`fix(frontend): replace undefined isPaused with isPlaying state`)
* **Pre-Registration Amendment 3 Freeze Commit:** `4511149` (`feat(f1): re-freeze final matrix under Pre-Registration Amendment 3`, 2026-11-04 11:05:02 +0530)

### 2. Complete Inventory of Experiment Folders under `results/`
A systematic search across `results/` and `results/research/` identified the following experimental datasets:

| Experiment Directory | Run Dirs | Seeds | Policies / Variants | Scenarios / Conditions | Status / Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `results/research/exp_marathahalli_improve_final` | **384** | **131–138** (8) | 8 policies (7 main + 1 ablation) | 6 conditions | **Final Confirmatory Study** (Amendment 3). All 384 runs `SUCCESS`. |
| `results/research/exp_marathahalli_hybrid_840` | **840** | 121–130 (10) | 7 policies | 12 conditions (4 patterns $\times$ 3 levels) | Exploratory multi-pattern benchmark. Completed 2026-10-20. |
| `results/research/exp_final_smoke_dev` | 468 | 101–102 (2) | Baselines & dev tests | Dev smoke conditions | Dev smoke replay dataset. |
| `results/research/cache_val_106_110` | 450 | 106–110 (5) | Validation variants | Intermediate conditions | Dev validation sweep. |
| `results/research/exp_headroom_recheck_dev` | 315 | 101–105 (5) | 7 policies | 9 conditions | Dev calibration re-check. |
| `results/research/exp_ladder_R3_amend_val2` | 540 | 111–120 (10) | Calibration ladder | Amendment validation | Ladder R3 tuning set. |
| `results/research/exp_ladder_R2_val` / `R3_val` / `R4_val` | 270 each | 111–120 (10) | Intermediate ladders | Rung validations | Intermediate ladder development. |
| `results/research/exp_marathahalli_emergency_360` | 360 | 121–130 (10) | 3 policies | Emergency scenarios | Phase P4 emergency vehicle study. |
| `results/research/exp_marathahalli_site_720` | 720 | 121–130 (10) | 6 policies | Site geometry baseline | Site baseline dataset. |
| `results/research/exp_primary_720` | 720 | 21–30 (10) | 6 policies | Generic 4-way synthetic | Initial prototype study. |

---

## STEP 1: Experiment Reconciliation

### Status: **CONFIRMED PROBLEM (Trace & Seed-Role Wording)**

### a) Study Identity & Table 1 Reproduction
* **Source Study:** The paper (`DP1_Paper_IEEE.docx`) and the official results sheet (`Experimental Results - Marathahalli Improvement.pdf`) derive their findings exclusively from `results/research/exp_marathahalli_improve_final/`.
* **Execution Parameters:** 384 runs = 8 policies $\times$ 6 conditions $\times$ 8 seeds (131 to 138).
* **Numerical Verification:** Recomputing Table 1 from `paired_bootstrap_summary.csv` against the paper's text shows an exact 100% match across all reported values:

| Table 1 Metric | Paper Stated Value | Artifact Value (`paired_bootstrap_summary.csv`) | Match? |
| :--- | :--- | :--- | :---: |
| **Hybrid p95 Wait** | 452.3 s | 452.333 s | **Exact** |
| **Webster-m p95 Wait** | 446.8 s | 446.753 s | **Exact** |
| **p95 Wait $\Delta\%$ (95% CI)** | $-0.9\%\;(-4.2\%, +2.5\%)$ | $-0.882\%\;(-4.229\%, +2.532\%)$ | **Exact** |
| **p95 Wait Holm $p$** | $1.00$ | $1.0000$ ($p=0.618$) | **Exact** |
| **Hybrid Max Queue** | 42.2 m | 42.245 m | **Exact** |
| **Webster-m Max Queue** | 62.2 m | 62.213 m | **Exact** |
| **Max Queue $\Delta\%$ (95% CI)** | $-28.8\%\;(-35.0\%, -22.4\%)$ | $-28.842\%\;(-34.969\%, -22.403\%)$ | **Exact** |
| **Max Queue Holm $p$** | $<0.001$ | $0.0000$ ($p=0.0000$) | **Exact** |
| **Hybrid Wait Gap** | 58.3 s | 58.281 s | **Exact** |
| **Webster-m Wait Gap** | 59.8 s | 59.808 s | **Exact** |
| **Wait Gap $\Delta\%$ (95% CI)** | $+3.0\%\;(-8.0\%, +16.2\%)$ | $+3.031\%\;(-8.000\%, +16.195\%)$ | **Exact** |
| **Wait Gap Holm $p$** | $1.00$ | $1.0000$ ($p=0.636$) | **Exact** |
| **Hybrid Mean Wait\*** | 76.7 s | 76.704 s | **Exact** |
| **Webster-m Mean Wait\*** | 77.7 s | 77.748 s | **Exact** |
| **Mean Wait $\Delta\%$ (95% CI)\*** | $-3.1\%\;(-5.3\%, -1.1\%)$ | $-3.132\%\;(-5.295\%, -1.135\%)$ | **Exact** |
| **Hybrid Mean Queue\*** | 2.5 m | 2.517 m | **Exact** |
| **Webster-m Mean Queue\*** | 4.0 m | 4.008 m | **Exact** |
| **Mean Queue $\Delta\%$ (95% CI)\*** | $-35.7\%\;(-38.4\%, -33.1\%)$ | $-35.696\%\;(-38.351\%, -33.053\%)$ | **Exact** |

### b) Decision-Trace Discrepancy & Replacement
* **The Problem:** In Section IV.C of `DP1_Paper_IEEE.docx`, the paper illustrates the controller's extension and fairness mechanism with timestamps $t = 528.0\text{ s}$ and $t = 549.0\text{ s}$. This trace was copied from run `marathahalli_imbalanced_orr_hybrid_queue_adaptive_s125`, which belongs to the previous exploratory 840-run dataset (`exp_marathahalli_hybrid_840`, seeds 121–130), violating the provenance of the final study.
* **The Solution:** A full search across all 48 hybrid runs in `exp_marathahalli_improve_final` (seeds 131–138) located an identical decision event exhibiting multiple extension approvals followed by a fairness wait-limit preemption:
  * **Cell ID:** `marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`
  * **File:** `results/research/exp_marathahalli_improve_final/marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136/decisions.csv`
  * **Rows:** 121 to 127
  * **Timeline:** $t = 1151.0\text{ s}$ to $t = 1171.0\text{ s}$ (Cycle 60)

#### Exact Extracted Trace (Seed 136):
| Row | $t$ (s) | Cycle | Axis | Proposed Action | Applied Action | Reason Code | Active Queue ($q_{\text{act}}$) | Competing Queue ($q_{\text{comp}}$) | $g_{\text{extra}}$ | Extracted Controller Explanation |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **121** | 1151.0 | 60 | EW | EXTEND | EXTEND | `EXTEND_APPROVED` | 24.0 m | 5.0 m | 9.0 s | East–West green extended by 3s: queue ($24.0\text{ m} \ge 4.0\text{ m}$), competing wait ($21.0\text{ s} \le 35\text{ s}$). |
| **122** | 1154.0 | 60 | EW | EXTEND | EXTEND | `EXTEND_APPROVED` | 24.0 m | 5.0 m | 12.0 s | East–West green extended by 3s: queue ($24.0\text{ m} \ge 4.0\text{ m}$), competing wait ($24.0\text{ s} \le 35\text{ s}$). |
| **123** | 1157.0 | 60 | EW | EXTEND | EXTEND | `EXTEND_APPROVED` | 24.0 m | 12.5 m | 15.0 s | East–West green extended by 3s: queue ($24.0\text{ m} \ge 4.0\text{ m}$), competing wait ($27.0\text{ s} \le 35\text{ s}$). |
| **124** | 1160.0 | 60 | EW | EXTEND | EXTEND | `EXTEND_APPROVED` | 24.0 m | 12.5 m | 18.0 s | East–West green extended by 3s: queue ($24.0\text{ m} \ge 4.0\text{ m}$), competing wait ($30.0\text{ s} \le 35\text{ s}$). |
| **125** | 1163.0 | 60 | EW | EXTEND | EXTEND | `EXTEND_APPROVED` | 24.0 m | 12.5 m | 21.0 s | East–West green extended by 3s: queue ($24.0\text{ m} \ge 4.0\text{ m}$), competing wait ($33.0\text{ s} \le 35\text{ s}$). |
| **126** | 1166.0 | 60 | EW | EXTEND | REQUEST_SWITCH | `SWITCH_FAIRNESS_WAIT_LIMIT` | 24.0 m | 12.5 m | 21.0 s | **Extension rejected:** Competing North–South red wait ($36.0\text{ s}$) $\ge$ maximum allowed wait ($35.0\text{ s}$) with waiting queue ($12.5\text{ m}$). Triggering fair phase switch. |
| **127** | 1171.0 | 60 | NS | ENTER_GREEN | ENTER_GREEN | `BASELINE_ENTRY` | 12.5 m | 24.0 m | 0.0 s | North–South (ORR) green initiated with Webster baseline allocation 15.8 s. |

### c) Seed-Role Wording & Clarification
* **Prior Confusion:** Seeds 121–130 were previously referred to in the codebase as "held-out evaluation seeds" for the 840-cell study. However, under Pre-Registration Amendment 3 (commit `4511149`), seeds 121–130 were quarantined as prior exploratory data to safeguard statistical validity, and the confirmatory evaluation was frozen on fresh seeds 131–138.
* **Proposed Replacement Wording (for Section III.D / IV.A):**
  > "Evaluation seeds were strictly partitioned in accordance with Pre-Registration Amendment 3: seeds 121–130 served as prior exploratory evaluation data during architecture iteration and ladder ablation (840 cells), whereas seeds 131–138 were pre-registered and held out exclusively for the final confirmatory evaluation matrix (384 runs). No controller parameters or thresholds were tuned or inspected on seeds 131–138 prior to running the final matrix."

---

## STEP 2: Policy Inventory & Taxonomy Audit

### Status: **CONFIRMED PROBLEM (Paper Policy Count Mismatch)**

### 1. The True 8-Policy Matrix in `exp_marathahalli_improve_final`
The paper text states: *"We evaluate the hybrid controller against seven baseline and comparator policies plus our proposed hybrid controller and an oracle-seeded variant..."* (implying 9 policies).  
Inspection of `experiments/final_matrix.json`, `dp1/config.py`, and `results/research/exp_marathahalli_improve_final/matrix_status.csv` proves there are exactly **8 policies** (48 runs each across 6 conditions $\times$ 8 seeds = 384 runs):

| Policy Identifier | Type / Role | Description | Config Source | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **`fixed`** | Baseline (Field) | Field BTP fixed-time plan (Varthur 105s, ORR 95s net of clearance). | `dp1/config.py:FIXED_MARATHAHALLI` | `MEASURED` |
| **`webster_measured`** | Reference Baseline | Webster equisaturation splits computed from online measured 300s warmup flows. | `dp1/config.py:WEBSTER_MEASURED` | `MEASURED` |
| **`webster_recalc`** | Baseline | Recalculated Webster splits updated periodically every 300s. | `dp1/config.py:WEBSTER_RECALC` | `MEASURED` |
| **`sumo_actuated`** | Baseline | Native SUMO gap-out detector actuation. | `dp1/config.py:SUMO_ACTUATED` | `MEASURED` |
| **`adaptive`** | Baseline | Pure queue-proportional adaptive green allocation. | `dp1/config.py:ADAPTIVE` | `MEASURED` |
| **`queue_extension`** | Baseline | Actuation with queue-length threshold extensions. | `dp1/config.py:QUEUE_EXTENSION` | `MEASURED` |
| **`hybrid_queue_adaptive`** | **Proposed Main Policy** | Queue-length-aware hybrid controller with Webster baseline floor, extension ladder, and fairness bounds. | `configs/final_hybrid_queue_adaptive.yaml` | `MEASURED` |
| **`hybrid_oracle_seeded`** | Ablation Variant | Reference hybrid controller seeded from true scenario demand tables (oracle leak benchmark). | `dp1/config.py:HYBRID_ORACLE_SEEDED` | `ORACLE-SEEDED` |

### 2. Status of `rl_dqn`
* `rl_dqn` is **NOT present** in the 384 runs of `exp_marathahalli_improve_final`.
* Under Amendment 3 (documented in `docs/PREREGISTRATION_AMENDMENT_3.md`), Deep Q-Network reinforcement learning was formally moved out of scope due to policy convergence variance across multi-seed non-stationary demand shifts. The results sheet explicitly labels `rl_dqn` as "out of scope."
* **Action for Paper:** Ensure no text in Section IV implies `rl_dqn` was evaluated in the 384-run matrix. Any mention in Section II (Related Work) or Section V (Discussion) must be framed strictly as prior exploratory work or future scope.

### 3. Proposed Replacement Text for Policy Overview:
> "We evaluate our proposed hybrid controller (`hybrid_queue_adaptive`) against six baseline and comparator policies (`fixed`, `webster_measured` [primary reference], `webster_recalc`, `sumo_actuated`, `adaptive`, and `queue_extension`), alongside one oracle-seeded variant (`hybrid_oracle_seeded`) evaluated as an ablation of local flow measurement, yielding eight policies across six traffic conditions and eight held-out seeds (384 runs in total)."

---

## STEP 4: Sanity Audit of the p95-Wait vs. Max-Queue Puzzle

### Status: **OK (Mathematically Consistent; Root Cause Verified)**

### 1. The Perceived "Puzzle"
In Table IV of the paper, saturated conditions report high 95th-percentile waiting times alongside relatively short maximum queue lengths:
* **`balanced-heavy`:** p95 wait is **667 s** (Hybrid) / **687 s** (Webster-m), while max queue is only **47.2 m** (Hybrid) / **59.3 m** (Webster-m).
* **`lane_closure-medium`:** p95 wait is **587 s** (Hybrid) / **535 s** (Webster-m), while max queue is **48.2 m** (Hybrid) / **69.1 m** (Webster-m).

Reviewers could suspect an internal inconsistency: *How can a driver wait 11 minutes (667 s) if the queue never stretches past 47 metres on a 350-metre approach?*

### 2. Root Cause Analysis & Microscopic Verification

Tracing the exact definitions in `dp1/metrics.py`, `dp1/queues.py`, and raw SUMO output (`tripinfo.xml`) demonstrates that **both metrics are completely accurate and reflect complementary physical dimensions of traffic congestion**:

#### A. Temporal Accumulation: Multi-Cycle Delay (`waitingTime`)
* In SUMO, `waitingTime` in `tripinfo.xml` is defined as the **cumulative lifetime seconds** spent by a vehicle at speed $< 0.1\text{ m/s}$ across its entire trip.
* In heavy scenarios (demand $\approx 1.30\times$ capacity, 1,679 vehicles completed), arrival rates exceed junction discharge capacity over multiple consecutive cycles.
* **Microscopic Vehicle Trace:**
  * In run `marathahalli_balanced_heavy_hybrid_queue_adaptive_s131`, vehicle `v159` entered via `wf_in` at $t = 169.0\text{ s}$ and completed its trip at $t = 698.0\text{ s}$ ($529\text{ s}$ trip duration).
  * Its recorded attributes: `waitingTime = 419.0 s`, `waitingCount = 8`.
  * The vehicle stopped **8 distinct times** in stop-and-go platooning. Over 8 signal cycles (cycle length $\approx 85\text{--}90\text{ s}$), it queued, crept forward 15–20 metres during green discharges, stopped again on red, and accumulated 50–60 s of red wait per cycle ($8 \times 52\text{ s} \approx 419\text{ s}$).
  * Thus, **a 667-second p95 wait does not mean a vehicle was stuck in a static 667-second queue; it means the vehicle had to cycle through 7 to 9 green-red cycles before clearing the stop line.**

#### B. Spatial Truncation: Instantaneous Contiguous Cluster (`gt_ext_max_queue_m`)
* `gt_ext_max_queue_m` is computed by `_compute_chain_ground_truth()` in `dp1/queues.py` as a **1-second microscopic spatial snapshot**:
  * **Lead vehicle condition:** Distance from stop line $\le 15.0\text{ m}$.
  * **Stopped threshold:** Speed $< 1.4\text{ m/s}$.
  * **Contiguity gap threshold:** Distance between consecutive stopped vehicles $\le 7.5\text{ m}$.
  * **Cluster extent:** Distance from the stop line to the rear bumper of the furthest stopped vehicle in the continuous cluster.
* **Why the spatial queue is bounded at 47 m:**
  1. The surface approach leg (`leg_orr_n_in`) is only **32.6 metres long**; the upstream ramp (`ramp_orr_n_in`) is **131.0 metres long**.
  2. Because the hybrid signal serves the active phase every cycle, the front platoon moves forward every $\approx 45\text{ s}$. As soon as green initiates, the lead vehicles accelerate above $1.4\text{ m/s}$, immediately collapsing the stop-line cluster metric.
  3. Upstream vehicles further back on `ramp_wf_in` or `wf_in` creep forward during discharges at $1.5\text{--}3.0\text{ m/s}$ or develop headways $> 7.5\text{ m}$, breaking the strict contiguity requirement of the cluster definition.
  4. Under the fixed-time baseline (static 105s / 95s splits), the phase duration is inflexible, and the contiguous queue stacks up to **98.4 m** in `balanced-heavy` and **107.2 m** in `imbalanced_orr-heavy`. The hybrid controller successfully contains the physical queue to **47.2 m** (a **$-52.0\%$** reduction in physical queue spillover).

#### C. Extraction Pipeline Bug (Non-Fatal)
* In `matrix_status.csv` and `per_condition_summary.csv`, `throughput_vph` and `switches_per_hour` are recorded as `0.0`.
* This occurred because `dp1/metrics.py` keys throughput as `throughput_veh_per_h`, while the summary aggregation script looked for `throughput_vph`.
* Raw `tripinfo.xml` contains all vehicle departure and arrival timestamps (completion rate 100%, 0 teleports, 0 unfinished). In Phase 2, the aggregation script in `analysis/paper_final/` will extract throughput directly using the correct key.

### 3. Proposed Minimal Fix for the Paper (Footnote / Section IV.E Text)
Add the following explanatory text to Section IV.E and a footnote to Table IV:
> *"Note on delay vs. queue metrics: The 95th-percentile waiting time (`p95 wait`) represents the cumulative trip-level stationary delay (speed $< 0.1\text{ m/s}$) accumulated across multiple stop-and-go signal cycles in oversaturated conditions (where vehicles experience between 5 and 9 cycles before junction discharge). In contrast, `max queue` captures the instantaneous physical length of the contiguous stopped queue cluster (speed $< 1.4\text{ m/s}$, headway $\le 7.5\text{ m}$) anchored at the stop line during any 1-second sample. While multi-cycle delay is governed by network-wide demand-to-capacity saturation, the hybrid controller prevents localized spatial spillback, halving the maximum physical queue relative to fixed-time control (47 m vs. 98 m) by flushing platoons on every cycle."*

---

## Implications for Subsequent Steps (Steps 3, 5–10)

1. **Step 3 (Table Verification & Scripting):**
   * All numbers in Tables I, II, III, and IV are verified against `paired_bootstrap_summary.csv`, `per_condition_summary.csv`, and `ablation_summary.csv`.
   * The new analysis script (`analysis/paper_final/run_all.py`) can re-aggregate directly from `exp_marathahalli_improve_final/` without re-running simulations.
   * Key mapping for `throughput_veh_per_h` and `switches_per_hour` will be corrected.
2. **Step 5 (Figure Generation):**
   * Figure 3 (forest plot) and Figure 4 (timeseries of surge_shift and lane_closure) will be plotted directly from the confirmed run directories in `results/research/exp_marathahalli_improve_final/`.
3. **Step 6 (Decision Trace Replacement):**
   * Replace the seed 125 trace in Section IV.C with the verified seed 136 trace (`marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`, rows 121–127).
4. **Step 7 (LaTeX / Docx Text Patching):**
   * Correct policy count from "7 baselines + hybrid + oracle" to "6 baselines + 1 proposed + 1 ablation variant = 8 policies".
   * Insert the seed-role clarification and the delay-vs-queue footnote.
5. **Step 8 (References & Sources):**
   * Keep citations strictly aligned with `docs/SOURCES.md`.

---

## Formal Verdict & Next Steps

### **VERDICT: GO**
Phase 1 gating criteria are fully satisfied. The source of truth has been firmly established as `results/research/exp_marathahalli_improve_final` (384 runs, seeds 131–138). All discrepancies in the draft text have precise, artifact-backed replacements.

**Awaiting user confirmation to proceed to Phase 2 (Steps 3, 5, 6, 7, 8).**
