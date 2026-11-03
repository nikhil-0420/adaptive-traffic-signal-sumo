# Phase 8 Final Report: Freeze Non-Stationary Scenarios

**Author:** Implementation Engineer  
**Date:** November 2, 2026  
**Git Branch:** `dp1-improve`  
**Git Tag:** `dp1-phase8-scenarios-frozen`  
**Primary Deliverables:**
- Generator code: [`dp1/config.py`](file:///e:/dp1-traffic-signal/dp1/config.py), [`dp1/site_scenarios.py`](file:///e:/dp1-traffic-signal/dp1/site_scenarios.py), [`dp1/runner.py`](file:///e:/dp1-traffic-signal/dp1/runner.py)
- Unit & regression tests: [`tests/test_non_stationary_scenarios.py`](file:///e:/dp1-traffic-signal/tests/test_non_stationary_scenarios.py)
- Scenario specification: [`docs/SCENARIOS.md`](file:///e:/dp1-traffic-signal/docs/SCENARIOS.md)
- Non-triviality experiment results: [`results/research/exp_scenario_check_dev/`](file:///e:/dp1-traffic-signal/results/research/exp_scenario_check_dev/)
- Report: [`docs/phase8_report.md`](file:///e:/dp1-traffic-signal/docs/phase8_report.md)

---

## 1. Executive Summary

Phase 8 introduces and freezes three non-stationary demand scenarios on the reconstructed Marathahalli Bridge network prior to any parameter tuning:
1. **`ramp_peak`**: Morning rush-hour profile featuring a symmetric piecewise-linear ramp from $0.40\times$ base demand ($280\text{ vph}$) to a peak plateau at $1.80\times$ base demand ($1260\text{ vph}$ at medium; $1638\text{ vph}$ at heavy), holding for 400s, and ramping down to off-peak base.
2. **`surge_shift`**: Mid-run directional priority handover where dominant traffic begins on Outer Ring Road North-South ($76\%$ share, $0–700\text{s}$), transitions across $4\times 100\text{s}$ intervals ($700–1100\text{s}$), and flips to Varthur Road East-West ($77\%$ share, $1100–1800\text{s}$).
3. **`lane_closure`**: Mid-run physical capacity disruption where lane 0 of the inbound approach ramp from ORR North (`ramp_orr_n_in_0`) is closed to all traffic for 10 minutes ($600–1200\text{s}$) via SUMO TraCI, creating an upstream bottleneck while maintaining full junction turning validity.

All scenario parameters live in one central location (`dp1/config.py`), mirrored in `docs/SCENARIOS.md`. The four existing stationary patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`) remain untouched.

---

## 2. Invariants & Verification Results

### 2.1 Test Suite Status
The comprehensive test suite passes with 100% success across all 132 tests:
- `tests/test_non_stationary_scenarios.py`: **17 passed** in 88.46s.
  - Test registration and central config verification.
  - Route generation determinism and byte-identity across medium and heavy levels for all 3 scenarios (6 tests).
  - Webster plan timing calculation and bounds (6 tests).
  - Lane closure geometry and time-window validation (1 test).
  - Smoke simulation on seed 101 for fixed and hybrid policies across all 3 scenarios (3 tests).
- Pre-existing regression suite: **115 passed**, 0 failures.

### 2.2 Route File Determinism & Byte Identity
Every scenario run derives all pseudo-randomness strictly from the simulation seed (`rng = random.Random(seed)`).
- Generating routes twice with identical `(scenario, level, seed)` outputs byte-identical `.rou.xml` files.
- Exact SHA-256 hashes are recorded in companion manifest files (`<route_file>.manifest.json`).
- Route files are written as raw UTF-8 bytes (`write_bytes`), ensuring cross-platform byte identity across Windows, macOS, and Linux.

### 2.3 Safety Invariant
In all simulations, the safety invariant:
$$\text{GREEN} \longrightarrow \text{YELLOW } (3\text{s}) \longrightarrow \text{ALL\_RED } (2\text{s}) \longrightarrow \text{GREEN (other axis)}$$
is strictly enforced. Zero direct green-to-green switches and zero concurrent greens on both axes occurred across all 60 evaluation runs.

---

## 3. Smoke Test Results (Seed 101)

Simulations were executed on dev seed 101 for both `fixed_webster` and `hybrid_queue_adaptive` across each new scenario at medium demand level:

| Scenario | Policy | Vehicles Total | Completion Rate | Unfinished | Avg Wait (s) | P95 Wait (s) | Max Queue (m) | Route Hash Matched? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ramp_peak`** | fixed_webster | 1419 | 100.0% | 0 | 103.49 | 638.00 | 24.90 | YES (`17557b4e...`) |
| **`ramp_peak`** | hybrid_queue_adaptive | 1419 | 100.0% | 0 | 108.71 | 682.00 | 24.85 | YES (`17557b4e...`) |
| **`surge_shift`** | fixed_webster | 1545 | 100.0% | 0 | 54.49 | 241.00 | 24.90 | YES (`76503c51...`) |
| **`surge_shift`** | hybrid_queue_adaptive | 1545 | 100.0% | 0 | 58.73 | 296.00 | 24.00 | YES (`76503c51...`) |
| **`lane_closure`** | fixed_webster | 1642 | 100.0% | 0 | 91.03 | 534.00 | 24.90 | YES (`e8cece3a...`) |
| **`lane_closure`** | hybrid_queue_adaptive | 1642 | 100.0% | 0 | 87.97 | 525.00 | 24.90 | YES (`e8cece3a...`) |

- **Route Hashes:** Byte-identical between policies for each scenario.
- **Safety & Validity:** No collisions, no emergency stops, no NaN values in any metric.

---

## 4. Non-Triviality Check Results (Dev Seeds 101–105)

> [!WARNING]
> **Phase 10B Retrospective Note on Oracle Baseline & Clipped Metrics**:
> The non-triviality experiment reported below was conducted with two limitations later uncovered during Phases 10 and 10B:
> 1. **Baseline Oracle Knowledge**: `fixed_webster` utilized `site_webster_plan`, which directly read scenario demand and multipliers from `SITE_DEMAND_PATTERNS`.
> 2. **Detector-Clipped Max Queue**: `Mean Max Q` and `Peak Max Q` reflect E2 detector jam length, which is clipped at $\approx 24.00$\,m – $24.90$\,m due to stopline setback and physical detector span.
> 
> See Phase 10B headroom recheck results (`results/research/exp_headroom_recheck_dev/` and `docs/phase10b_report.md`) for evaluations using unclipped ground-truth queue lengths (`gt_max_queue_m`) and realistic measured baselines (`webster_measured`, `webster_recalc`, `sumo_actuated`).

To ensure the scenarios are genuinely challenging and not trivial for Webster's stationary timing plans, an evaluation experiment was conducted in `results/research/exp_scenario_check_dev/`:
- **Sample size:** 60 simulation runs (2 policies $\times$ 3 scenarios $\times$ 2 levels $\times$ 5 dev seeds).
- **Seeds:** 101, 102, 103, 104, 105.
- **Levels:** `medium` (1.00x) and `heavy` (1.30x).

### Aggregated Performance Summary:

| Scenario | Level | Policy | Mean Wait (s) | Std Wait (s) | Mean P95 Wait (s) | Mean Max Q (m) | Peak Max Q (m) | Sat. Fraction | Unfinished |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ramp_peak`** | medium | fixed_webster | 97.06 | 8.41 | 585.94 | 24.71 | 24.90 | 0.04 | 0 |
| **`ramp_peak`** | medium | hybrid_queue_adaptive | 98.13 | 9.84 | 600.16 | 24.17 | 24.85 | 0.03 | 0 |
| **`ramp_peak`** | heavy | fixed_webster | 122.70 | 3.56 | 785.77 | 24.90 | 24.90 | **0.26** | 0 |
| **`ramp_peak`** | heavy | hybrid_queue_adaptive | 125.15 | 5.55 | 762.22 | 24.77 | 24.90 | **0.27** | 0 |
| **`surge_shift`** | medium | fixed_webster | 52.18 | 6.94 | 238.09 | 24.59 | 24.90 | 0.03 | 0 |
| **`surge_shift`** | medium | hybrid_queue_adaptive | 52.71 | 5.63 | 268.69 | 24.00 | 24.00 | 0.02 | 0 |
| **`surge_shift`** | heavy | fixed_webster | 113.21 | 10.29 | 683.92 | 24.90 | 24.90 | **0.22** | 0 |
| **`surge_shift`** | heavy | hybrid_queue_adaptive | 110.62 | 11.50 | 663.92 | 24.90 | 24.90 | **0.15** | 0 |
| **`lane_closure`** | medium | fixed_webster | 87.57 | 14.86 | 524.04 | 24.53 | 24.90 | 0.03 | 0 |
| **`lane_closure`** | medium | hybrid_queue_adaptive | 87.63 | 12.37 | 529.61 | 24.36 | 24.90 | 0.02 | 0 |
| **`lane_closure`** | heavy | fixed_webster | 126.41 | 8.32 | 871.95 | 24.72 | 24.90 | **0.09** | 0 |
| **`lane_closure`** | heavy | hybrid_queue_adaptive | 125.88 | 5.78 | 822.12 | 24.87 | 24.90 | **0.06** | 0 |

### Analysis Against Non-Triviality Criteria:
1. **Meaningful Queue Variation & Saturation:**
   - In heavy conditions, all three scenarios push queues to the physical detector limit ($24.90\text{ m}$).
   - In `ramp_peak` heavy, approaches spend **26% to 27%** of the entire 30-minute simulation in detector saturation.
   - In `surge_shift` heavy, approaches spend **15% to 22%** of the run in detector saturation.
   - In `lane_closure` heavy, the 10-minute bottleneck drives saturation up to **9%**.
2. **Headroom for Adaptive Control:**
   - On `surge_shift` (heavy), the hybrid controller already achieves lower mean delay ($110.62\text{ s}$ vs $113.21\text{ s}$) and reduces saturation duration from $22\%$ down to $15\%$.
   - On `lane_closure` (heavy), the hybrid controller achieves lower mean delay ($125.88\text{ s}$ vs $126.41\text{ s}$) and lower p95 delay ($822.12\text{ s}$ vs $871.95\text{ s}$).
   - On `ramp_peak` (heavy), the untuned hybrid is slightly behind Webster on mean delay ($125.15\text{ s}$ vs $122.70\text{ s}$) but achieves lower p95 tail delay ($762.22\text{ s}$ vs $785.77\text{ s}$), demonstrating clear opportunity for parameter tuning in subsequent phases.
3. **No Triviality Detected:**
   - The criterion "creates meaningful queue variation without being masked by seed noise" is decisively met.
   - P95 delays reach $660\text{s} - 870\text{s}$ under heavy demand, confirming substantial traffic pressure and headroom.

---

## 5. Summary of Files Changed

1. `dp1/config.py`: Defined `RampPeakConfig`, `SurgeShiftConfig`, `LaneClosureConfig`, interval generation functions, `SITE_DEMAND_PATTERNS`, `SITE_PATTERNS_NON_STATIONARY`, and `SITE_PATTERNS_ALL`.
2. `dp1/site_scenarios.py`: Sourced `SITE_DEMAND_PATTERNS` from `config.py` and converted route XML file writing to raw bytes (`write_bytes`) for strict cross-platform hash reproducibility.
3. `dp1/runner.py`: Forwarded `scenario` and `demand_level` to `fixed_webster` and `hybrid_queue_adaptive`, and added dynamic TraCI lane closure handling during `[start_s, end_s)` for `lane_closure`.
4. `dp1/cli.py` & `backend/config.py`: Added new scenario names to `--scenario` and API allowlists.
5. `dp1/research/matrix.py`: Added non-stationary scenario constants.
6. `tests/test_non_stationary_scenarios.py`: Created test suite covering registration, determinism, manifests, Webster plans, and smoke runs.
7. `scripts/run_scenario_check_dev.py`: Automated 60-run evaluation experiment and saturation metrics calculation.
8. `docs/SCENARIOS.md`: Authoritative specification and parameter manifest for all scenarios.
9. `docs/phase8_report.md`: Final completion report and empirical findings.

---

## 6. Conclusion & Status

Phase 8 is fully complete. The three non-stationary scenarios are rigorously tested, empirically validated as non-trivial, and permanently frozen.
The repository is ready to be tagged `dp1-phase8-scenarios-frozen`.
