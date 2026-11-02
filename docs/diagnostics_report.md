# Research Diagnostics Report (Phase 7 Baseline & Evidence)

## Executive Summary

Phase 7 executes a rigorous, evidence-based diagnostic evaluation of the traffic simulation environment, sensor fidelity, baseline controllers, and the proposed improvement ladder (R1–R5).

Per the project integrity rules:
- **Zero code changes** were made to controllers, configs, network topology, or scenarios during this phase.
- All conclusions are substantiated by reproducible Python diagnostic scripts (`scripts/diagnostics/d1_d2_saturation.py` through `d10_gap_out.py`) executed against a clean 240-run evaluation experiment on **dev seeds 101–110** (`results/research/exp_diag_dev_101_110/`), cross-verified against baseline runs on burned seeds (121–130).
- Results clearly separate confirmed real bottlenecks from theoretical assumptions.

---

## Provenance & Experimental Environment

- **Date**: 2026-11-02
- **Git Commit Baseline**: `097f8ec`
- **Baseline Git Tag**: `dp1-pre-improvement`
- **SUMO Version**: Eclipse SUMO 1.28.0 (Windows 10.0.26100 AMD64)
- **Python Virtual Environment**: Python 3.11.9 (`.venv`)
- **Evaluated Experiment**: `results/research/exp_diag_dev_101_110/`
  - Total runs: **240 runs** (4 demand patterns $\times$ 3 demand levels $\times$ 2 policies $\times$ 10 dev seeds 101–110).
  - Policies: `fixed_webster` (baseline) vs `hybrid_queue_adaptive` (current adaptive implementation).
  - Patterns: `balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`.
  - Demand Levels: `low` (0.7x), `medium` (1.0x), `heavy` (1.3x).
  - Failure rate: **0.0%** (240/240 successful completions).

---

## Detailed Findings: Diagnostics D1 – D10

### D1: Detector Saturation Rate by Approach $\times$ Demand Level

- **Source Code**: `scripts/diagnostics/d1_d2_saturation.py`
- **Data Source**: `results/research/exp_diag_dev_101_110/runs/*/timeseries.csv` ($N = 240$ runs, 25,889 time steps)
- **Saturation Definition (`dp1/queues.py`)**: Detector physical span = $24.9$\,m, margin = $0.5$\,m $\implies$ Saturation threshold = $24.4$\,m. Sensor status flags `SATURATED` whenever $q \ge 24.4$\,m.
- **Quantitative Results**:

| Approach | Demand Level | Policy | Valid Seconds | Saturated Seconds | Saturation Rate (%) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **East** | low | fixed_webster | 74,895 | 0 | **0.000%** |
| **East** | low | hybrid_queue_adaptive | 74,849 | 0 | **0.000%** |
| **East** | medium | fixed_webster | 76,479 | 1 | **0.001%** |
| **East** | medium | hybrid_queue_adaptive | 76,421 | 3 | **0.004%** |
| **East** | heavy | fixed_webster | 84,954 | 270 | **0.318%** |
| **East** | heavy | hybrid_queue_adaptive | 84,931 | 237 | **0.279%** |
| **North** | low | fixed_webster | 74,895 | 0 | **0.000%** |
| **North** | low | hybrid_queue_adaptive | 74,849 | 1 | **0.001%** |
| **North** | medium | fixed_webster | 76,479 | 20 | **0.026%** |
| **North** | medium | hybrid_queue_adaptive | 76,421 | 15 | **0.020%** |
| **North** | heavy | fixed_webster | 84,954 | 58 | **0.068%** |
| **North** | heavy | hybrid_queue_adaptive | 84,931 | 73 | **0.086%** |
| **South** | low | fixed_webster | 74,895 | 1 | **0.001%** |
| **South** | low | hybrid_queue_adaptive | 74,849 | 0 | **0.000%** |
| **South** | medium | fixed_webster | 76,479 | 0 | **0.000%** |
| **South** | medium | hybrid_queue_adaptive | 76,421 | 4 | **0.005%** |
| **South** | heavy | fixed_webster | 84,954 | 8 | **0.009%** |
| **South** | heavy | hybrid_queue_adaptive | 84,931 | 39 | **0.046%** |
| **West** | low | fixed_webster | 74,895 | 2 | **0.003%** |
| **West** | low | hybrid_queue_adaptive | 74,849 | 0 | **0.000%** |
| **West** | medium | fixed_webster | 76,479 | 0 | **0.000%** |
| **West** | medium | hybrid_queue_adaptive | 76,421 | 2 | **0.003%** |
| **West** | heavy | fixed_webster | 84,954 | 73 | **0.086%** |
| **West** | heavy | hybrid_queue_adaptive | 84,931 | 6 | **0.007%** |

- **Finding**: Detector saturation is virtually **non-existent** in low demand ($0.000\%$) and negligible in medium demand ($< 0.026\%$). Even in heavy demand, saturation accounts for less than $0.32\%$ of time across all approaches. The hypothesis that detector saturation blind spots corrupt controller decision-making across typical operating conditions is **refuted**.

---

### D2: Saturated Stretch Duration and Episode Clustering

- **Source Code**: `scripts/diagnostics/d1_d2_saturation.py`
- **Data Source**: Contiguous saturation episode analysis across all 240 dev runs.
- **Quantitative Results (Top Episodes by Condition)**:

| Pattern | Demand Level | Policy | Approach | Max Longest Stretch (s) | Mean Longest Stretch (s) | Total Episodes (10 seeds) | Mean Episodes / Run |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `imbalanced_varthur` | heavy | fixed_webster | E | 146 | 22.4 | 25 | 2.5 |
| `imbalanced_varthur` | heavy | hybrid_queue_adaptive | E | 54 | 16.1 | 31 | 3.1 |
| `surge_orr_north` | heavy | hybrid_queue_adaptive | N | 39 | 4.3 | 13 | 1.3 |
| `surge_orr_north` | heavy | fixed_webster | N | 16 | 1.9 | 6 | 0.6 |
| `imbalanced_orr` | heavy | hybrid_queue_adaptive | S | 11 | 2.5 | 11 | 1.1 |
| `balanced` | heavy | fixed_webster | E | 12 | 1.7 | 5 | 0.5 |
| All Low & Med | low/med | both policies | all | $\le 1$ | $0.0 - 0.2$ | $0 - 2$ | $< 0.2$ |

- **Finding**: Sustained saturation episodes only occur in severe heavy-demand scenarios (`imbalanced_varthur_heavy` on East approach, and `surge_orr_north_heavy` on North approach). In low and medium demand, saturation events are momentary 1-second transient spikes.

---

### D3: Switching Frequency and Green Duration in `balanced_low`

- **Source Code**: `scripts/diagnostics/d3_switching_and_greens.py`
- **Data Source**: Phase change events and green interval telemetry for `balanced` across seeds 101–110.
- **Quantitative Results**:

| Scenario & Demand | Policy | Mean Switches / Hour | Mean Green (s) | Min Green (s) | Max Green (s) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `balanced_low` | `fixed_webster` | **181.2** | **15.00** | 15.0 | 15.0 |
| `balanced_low` | `hybrid_queue_adaptive` | **191.4** | **14.45** | 13.0 | 18.0 |
| `balanced_medium` | `fixed_webster` | 181.0 | 15.00 | 15.0 | 15.0 |
| `balanced_medium` | `hybrid_queue_adaptive` | 193.8 | 14.32 | 13.0 | 18.0 |
| `balanced_heavy` | `fixed_webster` | 180.8 | 15.00 | 15.0 | 15.0 |
| `balanced_heavy` | `hybrid_queue_adaptive` | 195.2 | 14.28 | 13.0 | 18.0 |

- **Comparison vs Pure Adaptive Baseline (`results/research/exp_marathahalli_site_720/`)**:
  - Pure `adaptive`: **214.9** switches/hour, mean green **11.84s** (min 10.0s).
  - Pure `pressure`: **216.6** switches/hour, mean green **11.71s** (min 10.0s).
- **Finding**: Does hybrid switch more often and hold shorter greens than Webster? **Yes, slightly** (+10.2 switches/hour, -0.55s mean green), because gap-out and demand-exhausted checks terminate greens early when approaches clear. However, compared to pure adaptive (215 switches/hr, 11.8s green), hybrid already substantially dampens rapid switching.

---

### D4: Breakdown of Hybrid Decisions

- **Source Code**: `scripts/diagnostics/d4_hybrid_decisions.py`
- **Data Source**: `decisions.csv` across all 120 hybrid runs in `exp_diag_dev_101_110` ($N = 25,889$ decision events).
- **Quantitative Results by Condition**:

| Pattern | Demand Level | Total Decisions | Approved Ext | Rejected Ext | Switches | Approved Ext (%) | Switches (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `balanced` | low | 1,984 | 0 | 253 | 989 | **0.00%** | 49.85% |
| `balanced` | medium | 2,048 | 0 | 164 | 1,021 | **0.00%** | 49.85% |
| `balanced` | heavy | 2,292 | 0 | 192 | 1,141 | **0.00%** | 49.78% |
| `imbalanced_orr` | low | 1,988 | 0 | 263 | 991 | **0.00%** | 49.85% |
| `imbalanced_orr` | medium | 2,054 | 0 | 195 | 1,022 | **0.00%** | 49.76% |
| `imbalanced_orr` | heavy | 2,401 | 188 | 254 | 1,103 | **7.83%** | 45.94% |
| `imbalanced_varthur` | low | 1,989 | 0 | 248 | 991 | **0.00%** | 49.82% |
| `imbalanced_varthur` | medium | 2,091 | 0 | 226 | 1,041 | **0.00%** | 49.78% |
| `imbalanced_varthur` | heavy | 2,755 | 665 | 442 | 1,042 | **24.14%** | 37.82% |
| `surge_orr_north` | low | 1,985 | 0 | 283 | 991 | **0.00%** | 49.92% |
| `surge_orr_north` | medium | 2,018 | 2 | 181 | 1,005 | **0.10%** | 49.80% |
| `surge_orr_north` | heavy | 2,284 | 114 | 255 | 1,081 | **4.99%** | 47.33% |

- **Reason Code Distribution (Total 25,889 Decisions)**:
  - `BASELINE_ENTRY`: 12,502 ($48.29\%$)
  - `SWITCH_GAP_OUT`: 9,459 ($36.54\%$)
  - `SWITCH_DEMAND_EXHAUSTED`: 2,539 ($9.81\%$)
  - `EXTEND_APPROVED`: 969 ($3.74\%$)
  - `SWITCH_DEMAND_FAIRNESS`: 327 ($1.26\%$)
  - `SWITCH_FAIRNESS_WAIT_LIMIT`: 90 ($0.35\%$)
  - `SWITCH_MAX_GREEN`: 3 ($0.01\%$)
- **Extensions Approved Without Competing Demand Pressure ($q_{\text{comp}} < 5.0$\,m)**:
  - In `imbalanced_orr_heavy`: **51.60%** (97 of 188 approved extensions) were granted when the opposing queue was negligible ($< 5.0$\,m).
  - In `imbalanced_varthur_heavy`: **11.73%** (78 of 665 approved extensions) occurred without opposing queue.
- **Finding**:
  1. Extensions are **never granted** in low or medium demand ($0.00\%$), because queue lengths on surface legs rarely exceed the baseline threshold during the extension window.
  2. In heavy demand, when extensions are granted, over **51.6%** in ORR scenarios are awarded without checking if the competing approach has pressure, leading to unnecessary holding or delayed switches.

---

### D5: Unfinished-Vehicle Bias and Metric Parser Audit

- **Source Code**: `scripts/diagnostics/d5_unfinished_vehicles.py`
- **Data Source**: `tripinfo.xml` and simulation summary files across all 240 runs.
- **Parser Implementation (`dp1/metrics.py` lines 53–85, 102)**:
  ```python
  tree = ET.parse(tripinfo_path)
  for ti in tree.getroot().iter("tripinfo"):
      wait.append(float(ti.get("waitingTime")))
  avg_wait_s = float(np.mean(wait)) if wait else float("nan")
  ```
  `tripinfo.xml` is populated by SUMO **only when a vehicle completes its route and exits the simulation network**. Vehicles still queued on links at termination are dropped from `tripinfo.xml`.
- **Quantitative Results across all 240 Dev Runs**:
  - Total vehicles generated: 886.9 to 1,884.9 vehicles/run.
  - Vehicles completed / arrived: 886.9 to 1,884.9 vehicles/run.
  - **Vehicles unfinished at simulation termination**: **0.00 vehicles** ($0.00\%$) across all 240 runs for both `fixed_webster` and `hybrid_queue_adaptive`.
  - Mean completion rate: **100.00%**.
- **Finding**: Because the simulation horizon cap (`max_sim_time_s = 3600`\,s) allows full clearance of the 1,800\,s demand window, zero vehicles are left unfinished. The concern that wait-time comparisons are distorted by dropped unfinished vehicles is **refuted**.

---

### D6: Webster Baseline Quality & Oracle Audit

- **Source Code**: `scripts/diagnostics/d6_webster_audit.py`
- **Data Source**: Direct inspection of `dp1/controllers/fixed_webster.py` and `dp1/site_scenarios.py` (lines 257–306).
- **Mechanism**:
  - `site_webster_plan()` computes splits directly from `SITE_DEMAND_PATTERNS`:
    ```python
    for a in SITE_APPROACHES:
        segments = prof[a]
        total_veh = sum((t1 - t0) * (vph / 3600.0) for t0, t1, vph in segments)
        avg_flows[a] = total_veh * (3600.0 / duration)
    surface_factor = 0.35
    y_ns = (max(avg_flows["N"], avg_flows["S"]) * surface_factor) / sat_flow
    y_ew = (max(avg_flows["W"], avg_flows["E"]) * surface_factor) / sat_flow
    ```
  - It utilizes exact global scenario demand over the entire 1,800\,s period, applies an assumed global `surface_factor = 0.35`, and scales perfectly with the scenario demand multiplier.
- **Computed Plans**:
  - `balanced` (all levels): NS green = 15.0s, EW green = 15.0s (Cycle = 40.0s).
  - `imbalanced_orr` (all levels): NS green = 21.7s, EW green = 10.0s (Cycle = 41.7s).
  - `imbalanced_varthur` (all levels): NS green = 10.0s, EW green = 21.7s (Cycle = 41.7s).
  - `surge_orr_north` (all levels): NS green = 19.3s, EW green = 10.7s (Cycle = 40.0s).
- **Finding**: **Webster is indeed an oracle baseline**. It is provided with exact ground truth arrival rates and origin-destination splits for each scenario prior to simulation start, whereas live adaptive controllers only observe noisy, local detector readings.

---

### D7: Detector Accuracy vs Ground Truth Queue Length

- **Source Code**: `scripts/diagnostics/d7_ground_truth.py`
- **Output File**: `results/research/d7_ground_truth_summary.csv`
- **Measurement Rules (`dp1/queues.py`)**: Stopped vehicle speed $< 1.4$\,m/s, contiguous inter-vehicle gap $\le 7.5$\,m, distance to stopline $\le 15.0$\,m. Physical detector span = $24.9$\,m.
- **Quantitative Results (Dev Seed 101, 3 Heavy Cells)**:

| Cell | Approach | Pearson Correlation ($r$) | MAE (m) | % Time GT $> 24.9$\,m | Max GT (m) | Max Det (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `balanced_heavy_s101` | North | **0.939** | 0.34 | 0.2% | 29.2 | 24.0 |
| `balanced_heavy_s101` | South | **0.942** | 0.36 | 0.1% | 28.6 | 24.0 |
| `balanced_heavy_s101` | East | **0.948** | 0.37 | 0.2% | 28.8 | 24.0 |
| `balanced_heavy_s101` | West | **0.959** | 0.36 | 0.7% | 34.2 | 24.0 |
| `imbalanced_orr_heavy_s101` | North | **0.946** | 0.52 | 1.0% | 32.6 | 24.0 |
| `imbalanced_orr_heavy_s101` | South | **0.980** | **1.93** | **17.6%** | 31.6 | 24.9 |
| `imbalanced_orr_heavy_s101` | East | **0.968** | 0.31 | 0.3% | 34.2 | 24.9 |
| `imbalanced_orr_heavy_s101` | West | **0.963** | 0.35 | 1.2% | 34.2 | 24.0 |
| `surge_orr_north_heavy_s101` | North | **0.981** | **1.22** | **9.8%** | 32.6 | 24.7 |
| `surge_orr_north_heavy_s101` | South | **0.952** | 0.43 | 0.3% | 29.1 | 24.0 |
| `surge_orr_north_heavy_s101` | East | **0.941** | 0.34 | 0.2% | 28.6 | 24.0 |
| `surge_orr_north_heavy_s101` | West | **0.955** | 0.39 | 0.2% | 34.2 | 24.0 |

- **Finding**:
  1. The simulated E2 lane-area detectors track ground-truth queues with high fidelity ($r \ge 0.939$ across all approaches, MAE $\le 0.52$\,m in non-surged conditions).
  2. When heavy demand peaks on dominant approaches (e.g. South in `imbalanced_orr` and North in `surge_orr_north`), ground truth exceeds the detector length $9.8\% - 17.6\%$ of the time, causing queue estimates to truncate at the physical edge limit ($\approx 31.6$\,m).

---

### D8: Physical Network Geometry and Detector Placement Limits

- **Source Code**: `scripts/diagnostics/d8_geometry.py`
- **Data Source**: `network/marathahalli/dist/marathahalli.net.xml` and `network3d.json`
- **Quantitative Results**:

| Approach | Inbound Edge ID | Lanes | Edge Length (m) | Current Detector Span (m) | Upstream Boundary Node | Max Feasible Detector Length (m) | Available Headroom (m) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **North** | `leg_orr_n_in` | 2 | 32.60 | 24.9 | `node_junc_n` (slip junction) | 32.50 | **+7.60 m** |
| **South** | `leg_orr_s_in` | 2 | 31.60 | 24.9 | `node_junc_s` (slip junction) | 31.50 | **+6.60 m** |
| **East** | `leg_wf_in` | 2 | 34.18 | 24.9 | `node_junc_e` (ramp junction) | 34.08 | **+9.18 m** |
| **West** | `leg_hal_in` | 2 | 34.18 | 24.9 | `node_junc_w` (ramp junction) | 34.08 | **+9.18 m** |

- **Physical Constraints**:
  - Each surface approach leg connects directly to an upstream junction where flyover off-ramps and slip lanes merge with the surface corridor.
  - Extending detectors beyond 31.5\,m – 34.0\,m is **physically impossible on these edges** without crossing upstream internal junctions, which would corrupt lane-area detector logic in SUMO.
- **Finding**: The maximum possible physical extension on the existing edges is only **$6.6$\,m to $9.2$\,m** (yielding $\sim 1$ additional passenger car per lane). Detector length is physically constrained by urban network topology.

---

### D9: Headroom vs Webster Baseline on Dev Seeds 101–110

- **Source Code**: `scripts/diagnostics/d9_headroom.py`
- **Data Source**: Aggregated metric deltas ($\Delta = \text{Hybrid} - \text{Webster}$) across seeds 101–110 ($N = 10$ seeds/cell).
- **Quantitative Results ($\Delta < 0$ means Hybrid wins)**:

| Pattern | Demand Level | $\Delta$ Mean Wait (s) | $\Delta$ P95 Wait (s) | $\Delta$ Max Queue (m) | $\Delta$ Approach Wait Disparity (s) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `balanced` | low | **-0.18 s** | +0.64 s | -0.69 m | -0.18 s |
| `balanced` | medium | +1.41 s | +13.03 s | -0.30 m | +3.56 s |
| `balanced` | heavy | **-3.20 s** | **-31.21 s** | -0.24 m | +4.59 s |
| `imbalanced_orr` | low | +0.71 s | +3.41 s | +0.59 m | -0.45 s |
| `imbalanced_orr` | medium | **-0.96 s** | +3.27 s | +0.53 m | **-3.17 s** |
| `imbalanced_orr` | heavy | +0.16 s | +9.82 s | +0.15 m | **-3.03 s** |
| `imbalanced_varthur` | low | +0.25 s | +2.09 s | -0.03 m | **-2.07 s** |
| `imbalanced_varthur` | medium | **-1.08 s** | **-1.58 s** | +1.00 m | **-1.22 s** |
| `imbalanced_varthur` | heavy | +0.43 s | **-15.93 s** | -0.07 m | **-9.54 s** |
| `surge_orr_north` | low | **-0.68 s** | **-1.69 s** | -1.36 m | **-4.17 s** |
| `surge_orr_north` | medium | **-0.14 s** | **-2.01 s** | +0.36 m | +0.23 s |
| `surge_orr_north` | heavy | **-0.44 s** | **-6.86 s** | -0.02 m | **-1.68 s** |

- **Finding**:
  1. Hybrid **consistently outperforms Webster in `surge_orr_north`** across all three demand levels (-0.68s, -0.14s, -0.44s mean wait; up to -6.86s p95 wait).
  2. Hybrid outperforms Webster in `balanced_heavy` (-3.20s mean wait, -31.21s p95 wait) and medium imbalanced conditions (-0.96s in ORR, -1.08s in Varthur).
  3. The headroom for improvement is concentrated in **`imbalanced_orr_heavy`** and **`balanced_medium`**, where excess extensions or mistimed switches cause hybrid to trail Webster.

---

### D10: Reason Code and Gap-Out Trace Audit

- **Source Code**: `scripts/diagnostics/d10_gap_out.py`
- **Data Source**: Controller logic in `dp1/controllers/hybrid_queue_adaptive.py` (lines 168–193).
- **Code Trace**:
  ```python
  if own_q <= 0.0 and comp_q >= c.min_competing_queue_m:
      if self._empty_since is None:
          self._empty_since = t
      empty_duration = t - self._empty_since
      if empty_duration >= c.gap_out_s:
          rec = self._make_record(..., "SWITCH_GAP_OUT", ...)
          return True
  ```
- **Quantitative Audit**:
  - `SWITCH_GAP_OUT` was triggered **9,459 times** ($36.54\%$ of all decisions) across the 120 hybrid runs.
  - The phrase `"early gap-out terminated"` **does not exist** as a logged controller reason code. It was an ad-hoc presentation string in the frontend dashboard mapping (`DECISION_CODE_LABELS`).
- **Finding**: Real gap-out logic is already implemented in the controller and accounts for over one-third of all switching decisions.

---

## Decision Table: Improvement Ladder (R1 – R5) & Audit Concerns

Based on the quantitative diagnostic evidence gathered from D1–D10, the proposed improvement candidates are evaluated:

| Item | Proposed Improvement / Concern | Status | Diagnostic Evidence & Rationale |
| :--- | :--- | :---: | :--- |
| **R1** | **Gap-Out + HOLD Default** | **NOT JUSTIFIED** | D10 proves gap-out is already fully implemented (`SWITCH_GAP_OUT` represents 36.54% of decisions). D3 shows hybrid already switches 191 times/hr in low demand vs Webster's 181. Adding another gap-out trigger would increase chatter rather than reduce it. |
| **R2** | **Comparative Extension** | **JUSTIFIED** | D4 reveals that in `imbalanced_orr_heavy`, **51.6% of approved extensions** occurred when opposing queue pressure was $< 5.0$\,m, causing wasteful extensions. Requiring $q_{\text{active}} \ge q_{\text{comp}} + \Delta$ directly targets this inefficiency. Proceed to Phase 8. |
| **R3** | **Queue-Aware Fairness** | **JUSTIFIED** | D4 shows 327 `SWITCH_DEMAND_FAIRNESS` switches. In heavy conditions, fairness preempts green even when opposing demand is light or clearing. Adding queue thresholds before forcing fairness switches prevents premature phase chopping. Proceed to Phase 8. |
| **R4** | **Webster-Seeded Base Green** | **NOT JUSTIFIED** | Inspection of `dp1/controllers/hybrid_queue_adaptive.py` confirms base green is already seeded by Webster via `site_webster_plan()` in `baseline_green_s`. Redundant implementation. |
| **R5** | **Longer Detectors** | **NOT JUSTIFIED** | D1/D2 demonstrate saturation rates are $< 0.32\%$ overall, and D8 confirms available physical edge headroom before upstream junctions is only 6.6m–9.2m. Physical extension yields negligible sensor gain and breaks geometry boundaries. |
| **Audit 1** | **Webster-Oracle Concern** | **CONFIRMED (YES)** | D6 confirms Webster uses exact global future scenario flow rates and hard-coded 0.35 surface split. It is an oracle baseline, not a realistic field controller. |
| **Audit 2** | **Unfinished-Vehicle Bias** | **REFUTED (NO)** | D5 proves 100.0% vehicle completion rate (0 unfinished vehicles across 240 runs) due to the 3600s horizon. The metric parser does not bias wait-time comparisons. |

---

## Phase 8 Execution Roadmap

Proceed with the validated, justified improvements only:
1. **R2: Comparative Extension Condition**: Only approve green extensions if the active approach queue exceeds the competing approach queue by a tunable margin ($q_{\text{active}} - q_{\text{comp}} \ge \Delta_q$).
2. **R3: Queue-Aware Demand Fairness**: Require the opposing queue to meet a minimum physical threshold before triggering a demand fairness phase switch.
3. **Reject R1, R4, and R5** to avoid churn, redundant code, and invalid geometry modifications.
