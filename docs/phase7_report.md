# Phase 7 Report: Research Baseline Tag and Diagnostics

## 1. Executive Summary & Objective

Phase 7 establishes the frozen research baseline and conducts a comprehensive diagnostic audit of the traffic simulation environment, sensor fidelity, and controller performance before undertaking any algorithmic modifications.

**Core Mandate**:
- Find out which suspected problems actually exist so only real ones are addressed.
- **Zero modification rule**: Do not change any controller, configuration, scenario, or detector in this phase.
- Execute analysis only; substantiate all claims with reproducible scripts and quantitative data across dev seeds 101–110.

---

## 2. Environment & Provenance Baseline

- **Date**: 2026-11-02
- **Pre-Improvement Baseline Commit**: `097f8ec`
- **Pre-Improvement Git Tag**: `dp1-pre-improvement`
- **Target Network**: `marathahalli` (v1.0.0, synthetic demand over Marathahalli junction topology)
- **SUMO Version**: Eclipse SUMO 1.28.0 (Windows 10.0.26100 AMD64)
- **Python Virtual Environment**: Python 3.11.9 (`.venv`)
- **Node / npm**: Node `v24.16.0` | npm `11.13.0`
- **Quality Gates at Start of Phase**:
  - `npm test --prefix frontend`: Passed 48/48 unit tests (100% green).
  - `python -m pytest -q`: Passed 115/115 unit and regression tests (100% green).
  - Determinism regression test (`test_phase5_telemetry_regression.py`): Passed; SHA256 hashes of `decisions.csv` and `timeseries.csv` confirmed 100% byte-identical.

---

## 3. Seed Allocation & Research Experiment Execution

To prevent data snooping and maintain research integrity:
- **Burned Seeds (121–130)**: Reserved strictly for hypothesis formulation.
- **Dev Seeds (101–110)**: Used for active diagnostic execution and decision evaluation.
- **Held-Out Test Seeds (131–150)**: Untouched and reserved for final verification.

### Experiment `exp_diag_dev_101_110` Execution:
- **CLI Command**:
  ```powershell
  .venv\Scripts\python.exe -m dp1.cli evaluate-research `
      --network marathahalli `
      --preset custom `
      --experiment-id exp_diag_dev_101_110 `
      --patterns balanced imbalanced_orr imbalanced_varthur surge_orr_north `
      --levels low medium heavy `
      --policies fixed_webster hybrid_queue_adaptive `
      --seeds 101 102 103 104 105 106 107 108 109 110 `
      --jobs 8
  ```
- **Execution Output**:
  - Total runs launched: 240
  - Completed runs: 240
  - Failed runs: 0 (100% success rate)
  - Data directory: `results/research/exp_diag_dev_101_110/` containing `raw_runs.csv`, `matrix_status.csv`, `aggregate.csv`, and per-cell artifacts.

---

## 4. Summary of Diagnostic Findings (D1 – D10)

Reproducible diagnostic scripts were created in `scripts/diagnostics/` and executed:

| Diagnostic | Focus | Key Quantitative Findings |
| :--- | :--- | :--- |
| **D1** | Detector Saturation Rate | Low demand = **0.000%**; Medium = $< \mathbf{0.026\%}$; Heavy = $\mathbf{0.007\% - 0.318\%}$. Saturation is negligible across normal operating regimes. |
| **D2** | Saturated Stretches | Stretches in low/medium are $\le 1$\,s transients. Heavy demand experiences sustained episodes only on East in `imbalanced_varthur` (max 54s) and North in `surge_orr_north` (max 39s). |
| **D3** | Switching in `balanced_low` | Hybrid switches **191.4 times/hr** (mean green 14.45s) vs Webster's **181.2 times/hr** (green 15.00s). Hybrid switches slightly more due to gap-out, but far less than pure adaptive (214.9 switches/hr, 11.84s green). |
| **D4** | Hybrid Decision Breakdown | Extensions approved: **0.0%** in low/medium; **7.8%** in `imbalanced_orr_heavy`, **24.1%** in `imbalanced_varthur_heavy`. Crucially, **51.6%** of approved extensions in `imbalanced_orr_heavy` occurred with no opposing queue pressure ($q_{\text{comp}} < 5$\,m). |
| **D5** | Unfinished-Vehicle Bias | `avg_wait_s` parses completed vehicles from `tripinfo.xml`. However, **0.0 unfinished vehicles** ($100.00\%$ completion) exist at simulation end across all 240 runs, eliminating wait-time truncation bias. |
| **D6** | Webster Baseline Quality | Webster computes cycle and green splits directly from the true scenario arrival tables in `SITE_DEMAND_PATTERNS` with a fixed 0.35 surface split. It is an **oracle baseline**. |
| **D7** | Detector vs Ground Truth | High fidelity across all approaches ($r = 0.939 - 0.981$, MAE $0.31 - 0.52$\,m). Under peak heavy surges, true queues exceed detector span 9.8% to 17.6% of the time, clipping at link boundaries ($\approx 31.6$\,m). |
| **D8** | Physical Geometry Headroom | Surface inbound legs are 31.6m to 34.2m long. Detectors are 24.9m. Feasible extension before hitting upstream merge junctions is only **6.6m to 9.2m** ($\approx 1$ vehicle), proving physical geometry cannot support long detectors. |
| **D9** | Headroom vs Webster | Hybrid beats Webster across all demand levels in `surge_orr_north` (up to -6.86s p95 wait) and in `balanced_heavy` (-3.20s mean wait, -31.21s p95 wait). Headroom for improvement is largest in `imbalanced_orr_heavy` and `balanced_medium`. |
| **D10** | Reason Code Audit | Controller implements real gap-out (`SWITCH_GAP_OUT`), accounting for **9,459 decisions (36.54%)**. The phrase `"early gap-out terminated"` was a frontend display string, not a logged reason code. |

---

## 5. Improvement Ladder Decisions (R1 – R5)

The Decision Table in [`docs/diagnostics_report.md`](./diagnostics_report.md) establishes:
- **R1 (Gap-Out + HOLD Default)**: **NOT JUSTIFIED** (Gap-out already active in 36.5% of decisions; adding more triggers increases switching churn).
- **R2 (Comparative Extension)**: **JUSTIFIED** (51.6% of extensions in `imbalanced_orr_heavy` are granted without opposing queue pressure; conditioning extensions on $q_{\text{active}} \ge q_{\text{comp}} + \Delta$ directly targets this flaw).
- **R3 (Queue-Aware Demand Fairness)**: **JUSTIFIED** (327 fairness switches occur; requiring minimum opposing queue threshold prevents premature interruption of active greens).
- **R4 (Webster-Seeded Base Green)**: **NOT JUSTIFIED** (Already implemented in `HybridQueueAdaptiveController` via `site_webster_plan`).
- **R5 (Longer Detectors)**: **NOT JUSTIFIED** (Saturation rate is $< 0.32\%$ and physical network geometry limits extension to $< 9.2$\,m).
- **Webster-Oracle Concern**: **CONFIRMED (YES)**.
- **Unfinished-Vehicle Bias Concern**: **REFUTED (NO)**.

---

## 6. Deliverables Created

1. `docs/diagnostics_report.md`: Complete report with detailed data tables and decision justifications.
2. `scripts/diagnostics/`: Reproducible test suite:
   - `d1_d2_saturation.py`
   - `d3_switching_and_greens.py`
   - `d4_hybrid_decisions.py`
   - `d5_unfinished_vehicles.py`
   - `d6_webster_audit.py`
   - `d7_ground_truth.py`
   - `d8_geometry.py`
   - `d9_headroom.py`
   - `d10_gap_out.py`
3. `results/research/exp_diag_dev_101_110/`: Full 240-run dataset on dev seeds.
4. `results/research/d7_ground_truth_summary.csv`: Ground-truth queue correlation metrics.
5. `docs/phase7_report.md`: This summary report.

---

## 7. Quality Gates & Final Git Tag

- Python test suite: 115/115 passed (`pytest -q`).
- Frontend test suite: 48/48 passed (`npm test --prefix frontend`).
- Pre-improvement tag: `dp1-pre-improvement` (at `097f8ec`).
- Post-diagnostics tag: `dp1-phase7`.
