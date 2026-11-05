# Phase 9 Report: Reference Baselines

**Date:** 2026-11-02  
**Status:** Completed  
**Git Tag:** `dp1-phase9-baselines`  
**Quality Gate:** `pytest -q` 141/141 passed (100% green); `pytest -v tests/test_baselines.py` 9/9 passed.

---

## 1. Executive Summary

Phase 9 implements four reference baselines and one diagnostic oracle controller for benchmark comparison against the adaptive control system (`hybrid_queue_adaptive`). All baselines strictly adhere to the shared safety state machine in `dp1/controllers/base.py`, preserving the safety invariant:
$$\text{GREEN} \xrightarrow{3\text{ s yellow}} \text{YELLOW} \xrightarrow{2\text{ s all-red}} \text{ALL\_RED} \xrightarrow{} \text{GREEN}(\text{other axis})$$
No conflicting greens are ever shown, no green-to-green transitions occur directly, and plan updates are applied strictly at legal cycle boundaries.

Detailed mathematical descriptions and parameter justifications are documented in [`docs/BASELINES.md`](file:///e:/dp1-traffic-signal/docs/BASELINES.md).

---

## 2. Reference Baselines Implemented

| Controller Policy | Description | Timing Mechanism | Plan Log |
| :--- | :--- | :--- | :--- |
| `webster_measured` | Webster cycle/splits solved from arrival flows measured in a 300 s warm-up window; fixed thereafter. | 300 s warm-up on BTP baseline; switches at cycle boundary. | Emits `plan_log.json` |
| `webster_recalc` | Periodically re-solves Webster cycle/splits every $N=300\text{ s}$ from a sliding measurement window $W=300\text{ s}$. | Evaluates every 300 s; applies update only at the next legal cycle boundary. | Emits `plan_log.json` |
| `fixed_matched_cycle` | Fixed-time plan with the same cycle length as Webster (50.0 s on Marathahalli) but using the BTP split ratio (105:95 $\approx$ 52.5% EW : 47.5% NS). | Constant fixed timing throughout run; isolates cycle length effect from split adaptation. | Emits `plan_log.json` |
| `sumo_actuated` | Native SUMO gap-out actuated logic (`type="actuated"` in additional XML) using lane-area detectors. | Min green 10 s, max green 60 s, max-gap 3.0 s, detector-gap 3.0 s, yellow 3 s, all-red 2 s. | Standard metrics |
| `webster_oracle` *(Diagnostic)* | Webster plan computed from true scenario arrival rates (identical to `fixed_webster`). Labeled `[ORACLE]` everywhere. | Fixed-time oracle baseline for diagnostic headroom benchmarking. | Emits `plan_log.json` |

All fixed-time variants (`fixed`, `fixed_webster`, `fixed_matched_cycle`, `webster_measured`, `webster_recalc`, `webster_oracle`) emit `plan_log.json` records documenting `t_applied_s`, `cycle_index`, `cycle_s`, `green_ns_s`, `green_ew_s`, `yellow_s`, `all_red_s`, `split_ns_pct`, and `split_ew_pct`.

---

## 3. Decisions & Approved Parameters

1. **`webster_measured` Warm-up Duration**:
   - **Value:** 300 s (5 minutes).
   - **Justification:** At medium demand (~1400 vph total), ~115 vehicles arrive across the 4 approach legs in 300 s (~20–40 vehicles per approach), providing statistically adequate counts to estimate flow ratios ($y_{\text{ns}}, y_{\text{ew}}$) without consuming more than 16.7% of the 1800 s demand horizon.
2. **`webster_recalc` Recalculation Cadence and Window**:
   - **Cadence ($N$):** 300 s (5 minutes).
   - **Sliding Window ($W$):** 300 s (5 minutes).
   - **Cycle Boundary Rule:** Re-solved plans are staged as pending and applied exclusively when the current cycle ends and the signal enters `NS` GREEN at the next cycle boundary.
3. **`fixed_matched_cycle` Cycle and Split**:
   - **Cycle Length:** Matches canonical Webster optimal cycle length for the network geometry (50.0 s for Marathahalli).
   - **Split Ratio:** Preserves BTP ratio 105:95 (effective greens $g_{\text{ew}} = 21.0\text{ s}$, $g_{\text{ns}} = 19.0\text{ s}$, yellow = 3.0 s, all-red = 2.0 s).
4. **`sumo_actuated` Parameters & Documentation**:
   - Generated via dedicated XML `<tlLogic type="actuated">` passed to SUMO `-a`.
   - Clearances: `yellow = 3.0 s`, `all_red = 2.0 s` (identical to all other policies).
   - Min green = 10.0 s, Max green = 60.0 s.
   - Gap-out parameters: `max-gap = 3.0 s`, `detector-gap = 3.0 s`.
   - Documented with citations to SUMO documentation (SUMO User Documentation, Section *Traffic Lights / Actuated Traffic Lights*).
5. **DQN Status & Plan**:
   - Existing model was verified against the Phase 8 non-stationary scenarios (`ramp_peak`, `surge_shift`, `lane_closure`).
   - Runs cleanly without schema errors, tensor shape mismatches, or crashes.
   - Retraining specification defined: Train on dev seeds 101–105, validate on dev seeds 106–110 with state vector including queue metrics.
   - **Decision:** Evaluated as-is without premature retraining.

---

## 4. Verification and Quality Gate

### 4.1 Pytest Suite
- Full test suite: **141 passed in 696.47s** (`pytest -q`).
- Dedicated baseline test suite: **9 passed in 4.70s** (`pytest -v tests/test_baselines.py`):
  1. `test_webster_utils_solver`: Solves canonical Webster cycle and splits accurately against hand-calculated bounds.
  2. `test_all_baselines_safety_invariants`: Verifies zero conflicting greens, zero direct green-to-green transitions, and strict 3s yellow / 2s all-red across all baseline controllers.
  3. `test_webster_measured_cycle_boundary`: Asserts that `webster_measured` executes BTP during warm-up and applies new plans strictly at a legal cycle boundary.
  4. `test_webster_recalc_cycle_boundary`: Asserts periodic evaluation and strict cycle boundary application.
  5. `test_fixed_matched_cycle_timing`: Asserts cycle length equals 50.0 s and splits match BTP ratio 105:95.
  6. `test_sumo_actuated_xml_generation`: Verifies `<tlLogic type="actuated">` additional XML generation and clearance invariants.
  7. `test_measured_variants_seed_determinism`: Asserts that identical seeds produce byte-identical measured flows and plan logs.
  8. `test_webster_oracle_labeled_oracle`: Confirms `webster_oracle` is labeled oracle and matches scenario rates.
  9. `test_runner_integration_baselines`: End-to-end simulation runner verification for all baselines producing valid metrics and plan logs.

---

## 5. Phase 9 Smoke Test Audit

### 5.1 Experiment Matrix
- **Experiment Path:** `results/research/exp_baselines_smoke_dev`
- **Scenarios:** `ramp_peak`, `surge_shift`, `lane_closure` (Phase 8 non-stationary scenarios)
- **Demand Levels:** `medium`, `heavy`
- **Seeds:** `101`, `102` (dev seeds)
- **Policies (7):**
  1. `webster_measured`
  2. `webster_recalc`
  3. `fixed_matched_cycle`
  4. `sumo_actuated`
  5. `fixed` (BTP baseline)
  6. `fixed_webster` (Webster baseline)
  7. `hybrid_queue_adaptive` (Adaptive controller)
- **Total Executions:** $3 \times 2 \times 2 \times 7 = 84$ runs.

### 5.2 Audit Verification Summary
From [`results/research/exp_baselines_smoke_dev/smoke_audit.json`](file:///e:/dp1-traffic-signal/results/research/exp_baselines_smoke_dev/smoke_audit.json):
```json
{
  "total_runs": 84,
  "completed_runs": 84,
  "failed_runs": 0,
  "route_hash_conditions_checked": 12,
  "route_hash_mismatches": 0,
  "nan_mean_waiting_count": 0,
  "nan_max_queue_count": 0,
  "total_unfinished_vehicles": 0
}
```

- **Run Completion:** 84 / 84 runs completed successfully (100% completion rate).
- **Route Hash Consistency:** Checked across all 12 experimental condition groups (`scenario` $\times$ `demand_level` $\times$ `seed`). Exactly 1 unique route hash per group across all 7 policies (**0 hash mismatches**). Vehicle insertion is identical across policies.
- **Data Integrity:** **0 NaN values** for `mean_waiting_s` or `max_queue_m`.
- **Unfinished Vehicles:** **0 unfinished vehicles** across all 84 runs.
- **Plan Logs:** 12/12 plan logs present for every fixed-variant policy (`fixed`, `fixed_matched_cycle`, `fixed_webster`, `webster_measured`, `webster_recalc`).

### 5.3 Smoke Test Real Metric Summary (Seeds 101, 102)

*(Verification and correctness only; no performance claims are drawn.)*

#### Mean Waiting Time (s)
| Scenario | Demand Level | `fixed` | `fixed_matched_cycle` | `fixed_webster` | `hybrid_queue_adaptive` | `sumo_actuated` | `webster_measured` | `webster_recalc` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`lane_closure`** | heavy | 133.05 | 123.82 | 129.20 | 125.40 | 124.01 | 127.32 | 127.47 |
| | medium | 87.15 | 84.43 | 87.01 | 80.67 | 89.73 | 88.50 | 88.98 |
| **`ramp_peak`** | heavy | 128.54 | 124.02 | 122.35 | 127.59 | 123.08 | 123.15 | 122.34 |
| | medium | 102.19 | 95.09 | 93.46 | 95.56 | 96.70 | 97.39 | 94.98 |
| **`surge_shift`** | heavy | 123.74 | 119.63 | 121.27 | 119.84 | 120.50 | 119.34 | 120.00 |
| | medium | 52.96 | 49.32 | 47.95 | 51.43 | 48.14 | 50.53 | 49.94 |

#### Mean Max Queue Length (m)
| Scenario | Demand Level | `fixed` | `fixed_matched_cycle` | `fixed_webster` | `hybrid_queue_adaptive` | `sumo_actuated` | `webster_measured` | `webster_recalc` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`lane_closure`** | heavy | 24.90 | 24.90 | 24.90 | 24.90 | 24.21 | 24.45 | 24.45 |
| | medium | 24.90 | 24.00 | 24.56 | 24.00 | 24.00 | 24.90 | 24.90 |
| **`ramp_peak`** | heavy | 24.90 | 24.90 | 24.90 | 24.90 | 24.69 | 24.90 | 24.90 |
| | medium | 24.90 | 24.84 | 24.88 | 24.00 | 24.00 | 24.45 | 24.83 |
| **`surge_shift`** | heavy | 24.90 | 24.45 | 24.90 | 24.90 | 24.90 | 24.90 | 24.90 |
| | medium | 24.00 | 24.45 | 24.90 | 24.00 | 24.00 | 24.51 | 24.00 |

---

## 6. Deliverables Summary

1. **Controllers & Utilities:**
   - [`dp1/controllers/webster_utils.py`](file:///e:/dp1-traffic-signal/dp1/controllers/webster_utils.py): Canonical Webster solver and plan formatter.
   - [`dp1/controllers/webster_measured.py`](file:///e:/dp1-traffic-signal/dp1/controllers/webster_measured.py): Measured Webster controller (300 s warm-up, cycle boundary transition).
   - [`dp1/controllers/webster_recalc.py`](file:///e:/dp1-traffic-signal/dp1/controllers/webster_recalc.py): Periodic Webster controller ($N=300\text{ s}$, $W=300\text{ s}$).
   - [`dp1/controllers/fixed_matched_cycle.py`](file:///e:/dp1-traffic-signal/dp1/controllers/fixed_matched_cycle.py): Matched cycle controller (Webster cycle length, BTP split).
   - [`dp1/controllers/sumo_actuated.py`](file:///e:/dp1-traffic-signal/dp1/controllers/sumo_actuated.py): SUMO native actuated XML logic generator and controller.
   - [`dp1/controllers/fixed_webster.py`](file:///e:/dp1-traffic-signal/dp1/controllers/fixed_webster.py): Added plan logging and diagnostic `WebsterOracleController`.
   - [`dp1/controllers/fixed_time.py`](file:///e:/dp1-traffic-signal/dp1/controllers/fixed_time.py): Added plan logging.
2. **Registry & Runner Integration:**
   - [`dp1/controllers/__init__.py`](file:///e:/dp1-traffic-signal/dp1/controllers/__init__.py): Registered all new baselines.
   - [`dp1/runner.py`](file:///e:/dp1-traffic-signal/dp1/runner.py): Integrated actuated logic injection and plan log file emission (`plan_log.json`).
   - [`dp1/config.py`](file:///e:/dp1-traffic-signal/dp1/config.py): Defined configurations `WEBSTER_MEASURED`, `WEBSTER_RECALC`, `FIXED_MATCHED_CYCLE`, `SUMO_ACTUATED`, `BASELINE_POLICIES`, and `ALL_POLICIES`.
   - [`dp1/cli.py`](file:///e:/dp1-traffic-signal/dp1/cli.py) & [`backend/config.py`](file:///e:/dp1-traffic-signal/backend/config.py): Registered all policies in CLI and backend configurations.
3. **Tests:**
   - [`tests/test_baselines.py`](file:///e:/dp1-traffic-signal/tests/test_baselines.py): 9 comprehensive unit and integration tests passing.
4. **Documentation:**
   - [`docs/BASELINES.md`](file:///e:/dp1-traffic-signal/docs/BASELINES.md): Detailed algorithm specifications, mathematical formulations, parameter derivations, and literature citations.
   - [`docs/phase9_report.md`](file:///e:/dp1-traffic-signal/docs/phase9_report.md): Phase 9 verification report.
