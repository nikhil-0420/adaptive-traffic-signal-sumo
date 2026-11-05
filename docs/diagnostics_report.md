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

- **Revised Finding (Phase 10B Correction)**: The initial conclusion that detector saturation was negligible (< 0.32%) was an artifact of a measurement mismatch: the controller-facing `SATURATED` flag fired only at $q \ge 24.4$\,m, whereas the detector's physical jam length caps at $\approx 24.00$\,m due to lead-vehicle stopline setback ($\approx 0.9$\,m). Consequently, the `SATURATED` flag almost never fired even while the detector was physically packed at capacity. When measured properly via evaluation-only detector-full fraction ($q \ge 24.0$\,m) and microscopic ground truth (`gt_q`), the detector is physically full **4% to 14% of the time** in heavy cells (and up to **26.5%** on South approach in `imbalanced_orr_heavy`). The legacy `SATURATED` flag never fired at the $24.0$\,m cap; detector-full fraction and ground truth are the authoritative measures.

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

- **Revised Finding (Phase 10B Correction)**: Sustained detector-full episodes ($q \ge 24.0$\,m) occur frequently in heavy-demand conditions (`imbalanced_varthur_heavy`, `surge_orr_north_heavy`, `imbalanced_orr_heavy`), with physical packing occurring up to 14% of the entire run duration. The previous metric underreported episode lengths because the threshold was placed above the physical jam length ceiling.

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

## Phase 7B: Diagnostic Gaps and Deep Reconciliations

### 1. Hybrid Base Green Inputs & Live Controller Information Audit

- **Exact Code Quote 1: `dp1/controllers/hybrid_queue_adaptive.py` (lines 41–54)**:
  ```python
  # 1. Establish Webster-derived baseline green plan
  if plan is not None:
      self.baseline_plan = plan
  elif network == "marathahalli" or scenario in ("imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
      from ..site_scenarios import site_webster_plan
      self.baseline_plan = site_webster_plan(scenario, demand_level=demand_level)
  else:
      self.baseline_plan = C.webster_plan(scenario, demand_level=demand_level)

  # Baseline targets clamped to [min_green, max_green]
  self.baseline_green_s = {
      "NS": max(self.cfg.min_green_s, min(self.cfg.max_green_s, self.baseline_plan.green_ns_s)),
      "EW": max(self.cfg.min_green_s, min(self.cfg.max_green_s, self.baseline_plan.green_ew_s)),
  }
  ```
- **Exact Code Quote 2: `dp1/site_scenarios.py` (lines 257–275)**:
  ```python
  def site_webster_plan(
      scenario: str,
      timing: Optional[C.SignalTiming] = None,
      cfg: Optional[C.WebsterConfig] = None,
      demand_level: str = C.DEFAULT_DEMAND_LEVEL,
  ) -> C.FixedTimeConfig:
      scens = get_site_scenarios(demand_level=demand_level)
      if scenario not in scens:
          raise KeyError(f"Unknown site scenario: {scenario}")
      prof = scens[scenario]
      timing = timing or C.TIMING
      cfg = cfg or C.WEBSTER
      duration = float(C.SIM.demand_duration_s)

      avg_flows = {}
      for a in SITE_APPROACHES:
          segments = prof[a]
          total_veh = sum((t1 - t0) * (vph / 3600.0) for t0, t1, vph in segments)
          avg_flows[a] = total_veh * (3600.0 / duration)
      ...
  ```
- **Does the hybrid have information a live controller would lack?**
  **YES**. The hybrid controller accepts the exact test `scenario` name (e.g. `"imbalanced_orr"`, `"surge_orr_north"`) and `demand_level` (`"low"`, `"medium"`, `"heavy"`) at initialization. Through `site_webster_plan`, it accesses `SITE_DEMAND_PATTERNS` directly, extracting the exact ground-truth vehicle generation rates over the entire 1,800\,s horizon, along with the exact modelled surface traffic split factor ($0.35$). A real-world physical controller installed at an intersection has zero prior knowledge of scenario labels, demand multipliers, or future surge arrival rates; seeding the base green with an offline scenario-oracle leaks global future demand into the adaptive controller.

---

### 2. Approved Extensions & Fairness Switches on Dev Seeds 101–110

- **Source Code**: `scripts/diagnostics/phase7b_gaps.py`
- **Data Source**: `decisions.csv` across all 120 hybrid runs in `results/research/exp_diag_dev_101_110/`.
- **Approved Extension Audit ($N = 969$ approved extensions)**:
  - Extensions where competing score > active score (`score_competing > score_active`): **82 events** (**8.46%**).
  - Mean competing red wait at the moment extension was approved: **23.42s** (min: 15.0s, max: 57.0s).
  - Mean competing red wait at the next phase switch (controller internal elapsed green): **34.91s** (min: 18.0s, max: 60.0s).
  - Mean competing red wait at the next phase switch (+5s yellow/all-red clearance): **39.91s**.
- **Fairness Switch Audit ($N = 417$ total fairness switches)**:
  - `SWITCH_DEMAND_FAIRNESS`: **327 switches**.
    - Competing queue $< 5.0$\,m: **0 switches** (**0.00%**).
    - Competing queue $< 10.0$\,m: **24 switches** (**7.34%**).
    - Competing queue range: min = $5.0$\,m, mean = $20.4$\,m, max = $24.7$\,m.
  - `SWITCH_FAIRNESS_WAIT_LIMIT`: **90 switches**.
    - Competing queue $< 5.0$\,m: **0 switches** (**0.00%**).
    - Competing queue $< 10.0$\,m: **43 switches** (**47.78%**).
    - Competing queue range: min = $5.0$\,m, mean = $9.2$\,m, max = $20.1$\,m.
- **Interpretation**: Both fairness rules in code (`hybrid_queue_adaptive.py` lines 227 & 239) enforce an explicit guard `comp_q >= c.min_competing_queue_m` ($5.0$\,m). Consequently, exactly **0.00%** of fairness switches occur when competing queue is strictly $< 5.0$\,m. However, for `SWITCH_FAIRNESS_WAIT_LIMIT` (30s red wait cap), **47.78%** trigger when the opposing queue is very light ($< 10.0$\,m, $\le 1$ car), unnecessarily chopping an active heavy green corridor.

---

### 3. Reconciling D1 vs D7: Saturation Fraction & Lead Vehicle Setback

- **Source Code**: `scripts/diagnostics/phase7b_gaps.py`, `scripts/diagnostics/d7_ground_truth.py`.
- **Per-Cell Saturation Comparison**:
  1. **`imbalanced_orr_heavy` (South Approach)**:
     - D1 Saturation Rate (rule: $q \ge 24.4$\,m): Dev seed 101 = **0.95%** (20 / 2,101 s); 10-seed mean = **0.18%**.
     - D7 Ground Truth Rate (rule: $\text{GT} > 24.9$\,m): Dev seed 101 = **17.6%**.
  2. **`surge_orr_north_heavy` (North Approach)**:
     - D1 Saturation Rate (rule: $q \ge 24.4$\,m): Dev seed 101 = **0.00%** (0 / 2,105 s); 10-seed mean = **0.33%**.
     - D7 Ground Truth Rate (rule: $\text{GT} > 24.9$\,m): Dev seed 101 = **9.8%**.
- **Root-Cause Reconciliation**:
  - The detector saturation rule in `dp1/queues.py` (line 152) was defined as:
    $$\text{sat\_threshold} = \text{det\_len} - 0.5 = 24.9 - 0.5 = 24.4\,\text{m}$$
  - In SUMO, an E2 lane-area detector (`traci.lanearea.getJamLengthMeters`) measures jam length strictly between the front of the lead queued vehicle and the back of the trailing vehicle *within the detector geometry*.
  - When vehicles halt before a red light, the lead vehicle stops $\sim 0.9$\,m to $1.0$\,m behind the detector end line (due to car-following headway and stopline margins).
  - Even when the queue backs up 30\,m to 34\,m (spilling far beyond the upstream end of the 24.9m detector), the maximum jam length the detector can physically report is bounded by $24.9 - 0.9 = \mathbf{24.00\,\text{m}}$.
  - Inspecting time-series value distributions:
    - In `imbalanced_orr_heavy_s101`, `q_S == 24.00m` occurs **271 times** ($12.9\%$ of the run). With $q \ge 24.0$\,m, the detector is packed **13.85%** of the time.
    - In `surge_orr_north_heavy_s101`, `q_N == 24.00m` occurs **293 times** ($13.92\%$ of the run). With $q \ge 24.0$\,m, the detector is packed **13.92%** of the time.
  - Because $24.00\,\text{m} < 24.40\,\text{m}$, the status was labeled `MEASURING` instead of `SATURATED`.
  - **Conclusion**: The detector was physically jammed for $13.8\% - 13.9\%$ of the simulation time, aligning closely with D7's ground-truth exceedance ($9.8\% - 17.6\%$). The apparent discrepancy was an artifact of the $24.4$\,m threshold ignoring lead-vehicle stopline setback.

---

### 4. Max Queue Source and Ground-Truth Queue Logging Proposal

- **Current Source of `max_queue_m`**:
  - In `dp1/metrics.py` (lines 90, 107), `max_queue_m` is computed from `series`:
    $$\text{max\_queue\_m} = \max(\text{q\_matrix})$$
  - In `dp1/runner.py` (lines 215–230), `series` records `q_{a}` from `q = queues_to_legacy_dict(app_queues)`, which uses `ApproachQueueInfo.longitudinal_queue_m`.
  - `longitudinal_queue_m` is strictly the E2 detector measurement (`traci.lanearea.getJamLengthMeters`).
  - **Verdict**: `max_queue_m` currently uses **DETECTOR QUEUE**, not ground truth. It is physically clipped at $\approx 24.0$\,m – $24.9$\,m.
- **Evaluation-Only Ground-Truth Queue Logging Proposal**:
  - `QueueMeasurementEngine.measure_all(t)` already computes `ground_truth_queue_m` per approach using non-invasive vehicle position and speed queries.
  - **Implementation**:
    1. In `dp1/runner.py` (line 230), record ground truth alongside detector queue in `series_rec`:
       ```python
       **{f"gt_q_{a}": round(app_queues[a].ground_truth_queue_m, 2) for a in C.APPROACHES}
       ```
    2. In `dp1/metrics.py`, expose `gt_max_queue_m = float(gt_q_matrix.max())` and `gt_avg_queue_m = float(gt_q_matrix.mean())` while preserving `max_queue_m` for backwards compatibility.
    3. Controller inputs remain strictly isolated: `ctl.step(t, q)` continues to receive `q` (detector queue).
  - **Determinism Proof**:
    - Add a regression test (`tests/test_evaluation_gt_queue_determinism.py`) executing seed 101 on `balanced_medium` with and without ground truth logging; assert `decisions.csv` and controller telemetry are **100% byte-identical** (SHA256 verified).

---

### 5. Balanced-Low: Hybrid vs Adaptive Green Length and Min Green

- **Source Code**: `scripts/diagnostics/phase7b_gaps.py`
- **Data Source**: Completed green phases across all seeds ($N = 989$ hybrid phases, $N = 1,108$ adaptive phases):

| Metric | Fixed Webster (dev seeds 101–110) | Hybrid Queue Adaptive (dev seeds 101–110) | Pure Adaptive (site seeds 121–130) |
| :--- | :---: | :---: | :---: |
| **Mean Green Length** | 14.99 s | **13.89 s** | **11.84 s** |
| **Median Green Length** | 15.00 s | **13.00 s** | **12.00 s** |
| **Minimum Green Length** | 14.00 s | **13.00 s** | **9.00 s** |
| **Maximum Green Length** | 15.00 s | 18.00 s | 18.00 s |
| **P10 Green Length** | 15.00 s | 13.00 s | 10.00 s |
| **P90 Green Length** | 15.00 s | 15.00 s | 13.00 s |
| **Phases $\le 10.0$\,s (%)** | **0.00%** | **0.00%** | **23.56%** |

- **Key Takeaways**:
  1. **Mean Green**: Hybrid holds green **+2.05s longer** than pure adaptive (13.89s vs 11.84s).
  2. **Minimum Green**: Hybrid never terminates green earlier than **13.0s** (10.0s minimum floor + 3.0s gap-out timer), whereas pure adaptive regularly collapses to **9.0s – 10.0s** (23.56% of phases).
  3. **Stability**: Hybrid green lengths are tightly centered between 13.0s and 15.0s, eliminating the rapid short-greening that degrades pure adaptive in low demand.

---

## Updated Decision Table: Improvement Ladder (R1 – R5)

Based on Phase 7 and Phase 7B evidence:

| Item | Proposed Improvement / Concern | Status | Diagnostic Evidence & Justification |
| :--- | :--- | :---: | :--- |
| **R1** | **Gap-Out + HOLD Default** | **NOT JUSTIFIED** | D10 confirms gap-out is already active in 36.54% of decisions. Phase 7B (Item 5) proves hybrid already enforces a 13.0s min green and holds greens longer than adaptive (13.89s vs 11.84s). Adding another gap-out trigger would increase chatter. |
| **R2** | **Comparative Extension** | **JUSTIFIED** | D4 and Phase 7B (Item 2) show that in `imbalanced_orr_heavy`, 51.6% of approved extensions occur when competing queue pressure is $< 5.0$\,m, and 8.46% occur even when competing demand score exceeds active score. Conditioning extensions on $q_{\text{active}} \ge q_{\text{comp}} + \Delta_q$ directly resolves this flaw. **Proceed to Phase 8**. |
| **R3** | **Queue-Aware Demand Fairness** | **JUSTIFIED** | Phase 7B (Item 2) confirms that while hard guard $q_{\text{comp}} \ge 5$\,m prevents switches at 0m, **47.78% of wait-limit fairness switches** occur when the opposing queue is very light ($< 10$\,m, $\le 1$ car), unnecessarily preempting heavy flow. Raising the competing queue threshold before triggering wait-limit fairness preserves heavy servicing. **Proceed to Phase 8**. |
| **R4** | **De-Oracle the Base Green** | **JUSTIFIED** | Phase 7B (Item 1) proves hybrid's base green is seeded via `site_webster_plan`, which extracts exact ground-truth scenario tables (`SITE_DEMAND_PATTERNS`) and demand multipliers. A live controller does not possess this information. Replacing this oracle plan with an empirical un-oracled baseline (e.g. fixed 15s/15s or online arrival estimation) is essential for research validity. **Proceed to Phase 8**. |
| **R5** | **Longer Detectors** | **NOT JUSTIFIED** | D8 proves available physical edge headroom before upstream merge junctions is only 6.6m–9.2m ($\sim 1$ vehicle). Physical extension is geometrically unviable on Marathahalli surface legs. |
| **Audit 1** | **Webster-Oracle Concern** | **CONFIRMED (YES)** | Confirmed in D6 and Phase 7B (Item 1). Webster uses global future scenario flow rates. |
| **Audit 2** | **Unfinished-Vehicle Bias** | **REFUTED (NO)** | Confirmed in D5. 100.0% completion rate (0 unfinished vehicles across 240 runs). |

---

---
 
 ## Phase 10C Diagnostic Resolution & Spillover Characterization
 
 In Phase 10C, the evaluation-only microscopic ground-truth queue was extended across the approach leg, junction internal connector lanes, and upstream inbound ramps (`ramp_orr_n_in`, `ramp_orr_s_in`, `ramp_wf_in`, `ramp_hal_in`), expanding the spatial measurement horizon from $31.6\text{ m}–34.2\text{ m}$ to $127.74\text{ m}–163.74\text{ m}$.
 
 ### Key Findings:
 1. **Leg Spillover Frequency**:
    - `balanced` (medium, s101): Extended queue exceeds the $31.6\text{ m}–34.2\text{ m}$ leg boundary only **0.32%** of the simulation ($6\text{ s} / 1888\text{ s}$), peaking at $36.14\text{ m}$.
    - `imbalanced_orr` (heavy, s101): Extended queue exceeds the leg boundary **2.57%** of the simulation ($54\text{ s} / 2098\text{ s}$), peaking at $58.62\text{ m}$ (Approach N) and $52.87\text{ m}$ (Approach S).
 2. **Physical Ramp Boundedness**:
    - Under all evaluated demand conditions (including stationary heavy and non-stationary surges), the maximum extended queue remains strictly within the $127.74\text{ m}–163.74\text{ m}$ physical ramp boundaries, confirming that queues are not artificially clipped by ramp upstream limits.
 3. **Non-Leakage Policy Certification**:
    - Full static audit verified that `adaptive`, `pressure`, `queue_extension`, `rl_dqn`, `webster_measured`, `webster_recalc`, `sumo_actuated`, and `fixed` have zero scenario or demand leakage.
    - `hybrid_queue_adaptive` receives only runtime identifier arguments and has zero reference to `site_webster_plan` or `SITE_DEMAND_PATTERNS`.
 4. **Headroom Re-Analysis with Extended Queue**:
    - Across 9 conditions on dev seeds 101–105 ($n=45$), `hybrid_queue_adaptive` delivers statistically significant reductions in extended maximum queue against measured Webster baselines ($\Delta = -22.07\text{ m}$ vs `webster_measured`, 95% CI $[-30.86, -14.55]\text{ m}$; $\Delta = -23.13\text{ m}$ vs `webster_recalc`, 95% CI $[-32.60, -14.82]\text{ m}$) while matching oracle-seeded performance ($\Delta = -0.42\text{ s}$ mean wait vs `hybrid_oracle_seeded`).


