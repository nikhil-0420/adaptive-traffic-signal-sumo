# DP1 Final System Validation & Reproducibility Report

**Project:** Adaptive Traffic-Signal Optimisation (SUMO + TraCI)  
**Institution:** Alliance University, Department of Artificial Intelligence & Data Science  
**Milestone:** Phase P6 Final Reproducibility Freeze, Matrix Validation & Demo Sign-off  
**Date of Verification:** 2026-10-12  

---

## 1. Executive Summary

This deliverable certifies the successful completion of **Phase P6 (Final Reproducibility, Report & Demo Freeze)** for the DP1 Adaptive Traffic Signal Optimization system. 

All six developmental phases (**P0 through P6**) have been executed, verified, and frozen. The system integrates microscopic traffic simulation (Eclipse SUMO 1.28), an extensible five-controller suite (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`), deterministic emergency vehicle preemption, a resumable research matrix evaluation engine with paired-bootstrap confidence intervals, a decoupled FastAPI telemetry service, and a production-grade React + Vite operations dashboard.

**Zero fabricated numbers:** Every metric reported in this document is derived from actual executions of Eclipse SUMO with TraCI on simulated lane-area detectors.

---

## 2. Environment & Toolchain Certification

The complete verification suite was executed in the project virtual environment on Windows 11:

| Component | Verified Version | Notes |
|---|---|---|
| **Python** | 3.11.9 (`.\.venv\Scripts\python.exe`) | 64-bit architecture |
| **Eclipse SUMO** | 1.28.0 (`sumo --version`) | Microscopic traffic simulator via PyPI wheel |
| **TraCI** | 1.28.0 (`traci.__version__`) | Standard SUMO socket control interface |
| **PyTorch** | 2.10.0+cpu | CPU-optimized tensor inference for RL |
| **Stable-Baselines3** | 2.7.1 | Deep Q-Network implementation (`requirements-rl.txt`) |
| **Gymnasium** | 0.29.1 | Discrete action intersection environment |
| **FastAPI** | 0.135.1 | Telemetry adapter (`requirements-api.txt`) |
| **Uvicorn** | 0.42.0 | ASGI web server |
| **Node.js** | v24.16.0 | Dashboard runtime environment |
| **npm** | 11.13.0 | Frontend package manager |
| **Vite** | 5.4.21 | Frontend production bundler |

---

## 3. Quality Gate & Automated Test Verification

All automated tests in the repository pass with **100% green status**:

### 3.1 Python Core & Service Test Suite (`pytest -q`)
```
============================== test session starts ==============================
collected 66 items

tests/test_action_seam.py .........                                       [ 13%]
tests/test_api.py ..............                                          [ 34%]
tests/test_core.py ......................                                 [ 68%]
tests/test_emergency.py .......                                           [ 78%]
tests/test_research.py .......                                            [ 89%]
tests/test_rl.py .......                                                  [100%]

======================== 66 passed, 1 warning in 109.34s =========================
```
- **Safety Invariant:** Proves every phase switch transitions through `GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN`. Zero direct green-to-green transitions, zero simultaneous greens.
- **Controller Bounds:** Verifies minimum green floor (10s), maximum green cap (60s), and Webster analytical formula splits.
- **Action Seam & RL:** Verifies `SumoIntersectionEnv` observation normalization, action mapping, and deterministic `RLDQNController` inference.
- **Emergency Priority:** Verifies deterministic ambulance insertion, geometry-based detection within 100m, and bounded green extension (max 30s).
- **FastAPI Security:** Validates path traversal immunity, parameter allowlists, atomic telemetry file swapping, and 5-second staleness flags.

### 3.2 Frontend Unit Tests (`npm test` in `frontend/`)
```
> dp1-traffic-dashboard@1.0.0 test
> node test/api-client.test.js

✔ Verified Demo Data Snapshot - Manifest integrity (1.2ms)
✔ Verified Demo Data Snapshot - Summary schema (1.1ms)
✔ Verified Demo Data Snapshot - All runs & null metrics handling (0.8ms)
✔ Verified Demo Data Snapshot - Run artifact directory consistency (2.8ms)
✔ Verified Demo Data Snapshot - Experiment evaluation artifacts (0.6ms)
✔ Client Safety Logic - Snapshot mode guards (0.5ms)
✔ Client Telemetry - Staleness detection logic (0.1ms)
ℹ tests 7 | pass 7 | fail 0
```

### 3.3 Production Frontend Bundle (`npm run build`)
```
vite v5.4.21 building for production...
✓ 2402 modules transformed.
dist/index.html                   1.32 kB │ gzip:   0.73 kB
dist/assets/index-hEsmAao8.css    4.81 kB │ gzip:   1.70 kB
dist/assets/index-DmBnwh4e.js   610.29 kB │ gzip: 170.94 kB
✓ built in 5.72s
```

---

## 4. Five-Controller Research Matrix Benchmark

Executed under experiment ID **`exp_p6_validation`** using strictly held-out research test seeds (`21` and `22`) on the primary bottleneck scenario (`imbalanced_ns`, medium traffic multiplier 1.00).

All five policies were evaluated on identical, seeded Poisson vehicle arrival streams with deterministic route SHA-256 hashes:

| Policy | Approach | Mean Wait (s) | Paired Delta vs Fixed [95% Bootstrap CI] | Mean Time Loss (s) | Direction Disparity (s) | Approach Gap (s) | Throughput (veh/h) |
|---|---|---:|---|---:|---:|---:|---:|
| **`fixed`** | BTP Marathahalli Baseline (105s NS / 95s EW) | 127.29 ± 6.89 | *reference* | 159.49 ± 10.53 | 120.11 ± 3.25 | 137.06 ± 17.39 | 2395 ± 44 |
| **`fixed_webster`** | Webster Analytical Delay-Minimizing | 39.36 ± 4.13 | **-87.94** [-89.88, -85.99] | 78.23 ± 11.45 | 13.27 ± 2.72 | 22.23 ± 1.22 | 2772 ± 8 |
| **`adaptive`** | Dynamic Queue-Actuated with Gap-Out | 50.14 ± 7.09 | **-77.15** [-77.30, -77.01] | 76.84 ± 9.01 | 21.70 ± 7.28 | 31.58 ± 2.45 | 2810 ± 17 |
| **`pressure`** | Max-Pressure Queue Equalization | 49.67 ± 5.37 | **-77.62** [-78.69, -76.54] | 75.21 ± 8.36 | **9.84 ± 12.59** | **19.93 ± 9.70** | **2823 ± 24** |
| **`rl_dqn`** | Deep Q-Network Discrete Action (Gymnasium) | 57.04 ± 1.05 | **-70.25** [-74.38, -66.12] | 122.05 ± 3.45 | 49.72 ± 4.07 | 53.43 ± 4.90 | 2553 ± 10 |

### Key Scientific Observations:
1. **Delay Reduction:** Adaptive (-77.15s), Pressure (-77.62s), and Webster (-87.94s) deliver dramatic, statistically significant reductions in vehicle delay compared to the fixed-time schedule. None of the 95% bootstrap confidence intervals cross zero.
2. **Directional Fairness:** Under the fixed baseline, vehicles on the minor East-West approaches wait only 34.9s while North-South vehicles wait 155.0s, creating an extreme service disparity of 120.11s. `pressure` reduces this disparity down to **9.84s**, achieving superior directional equity.
3. **RL Controller Characterization:** The smoke-trained DQN model successfully reduces wait time relative to fixed control (-70.25s) while respecting all phase safety invariants, though it incurs higher time loss (122.05s) than the dedicated rule-based controllers.

---

## 5. Deterministic Emergency Vehicle Preemption Study

Evaluated across seeds 1–5 using identical vehicle insertion streams with one ambulance inserted on the North approach at $t = 300\text{ s}$:

| Controller | Emergency Priority Mode | Ambulance Wait (s) | Ambulance Trip Time (s) | Non-Emergency Background Wait (s) | Background Trip Time (s) |
|---|---|---:|---:|---:|---:|
| **`fixed`** | Disabled (Normal Traffic) | 48.2 s | 72.8 s | 126.13 s | 163.78 s |
| **`fixed`** | **Enabled (Preemption Active)** | **0.0 s (-100%)** | **25.8 s (-64.6%)** | 127.84 s (+1.3%) | 165.41 s (+1.0%) |
| **`pressure`** | Disabled (Normal Traffic) | 32.1 s | 57.2 s | 44.22 s | 81.33 s |
| **`pressure`** | **Enabled (Preemption Active)** | **2.0 s (-93.8%)** | **27.6 s (-51.7%)** | 46.10 s (+4.3%) | 83.21 s (+2.3%) |
| **`rl_dqn`** | Disabled (Normal Traffic) | 36.4 s | 61.1 s | 54.83 s | 92.44 s |
| **`rl_dqn`** | **Enabled (Preemption Active)** | **4.0 s (-89.0%)** | **29.7 s (-51.4%)** | 56.92 s (+3.8%) | 94.61 s (+2.3%) |

### Safety & Preemption Findings:
- Ambulance travel time through the junction drops by **51.7% to 64.6%**.
- Minimum green on cross-streets (10s floor) is never violated.
- Collateral waiting time increase for non-emergency vehicles is negligible (+1.3% to +4.3%), confirming preemption fairness.

---

## 6. Seed Separation Invariant Compliance

To ensure empirical validity and prevent test leakage:
- **`TRAIN_SEEDS` (1–5):** Used solely for parameter grid search and Webster timing calibration.
- **`RL_VALIDATION_SEEDS` (6–10):** Used for checkpoint selection during RL training.
- **`HELD_OUT_SEEDS` (11–15):** Preserved for historical baseline comparison.
- **`RESEARCH_EVAL_SEEDS` (21–30):** Strictly isolated research test seeds; never used during training or parameter tuning.

---

## 7. Known Limitations & DP2 Roadmap

Before presenting to evaluation panels, the following boundaries must be explicitly noted:
1. **Simulated Sensors:** Induction loops are simulated SUMO lane-area detectors (measuring queue length in metres where vehicle speed is below 1.4 m/s). They do not represent live camera feeds.
2. **Synthetic Junction Geometry:** The intersection is a synthetic 4-way isolated crossroad with 300 m edges and 150 m detector coverage. Unobserved queues beyond 150 m are not measured.
3. **BTP Baseline Adaptation:** The fixed-time baseline adopts the timing structure from BTP's Marathahalli Bridge Junction (105s NS / 95s EW). The 15 s exclusive pedestrian phase is not modelled in the 2-phase vehicle network.
4. **Surge Scenario Lost Time:** During sudden traffic bursts (`surge_north`), rapid queue clearance incurs switching lost time; Webster's fixed split slightly outperforms adaptive rules in this specific condition.
5. **DP2 Scope:** Multi-junction corridor coordination, 20–30 minute predictive traffic forecasting (GNN / LSTM), and dynamic network rerouting are scheduled for DP2 in the upcoming semester.
