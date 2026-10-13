# Upgrade Baseline Audit (Phase P0)

**Date**: 2026-10-12  
**Corpus**: `nikhil-0420/adaptive-traffic-signal-sumo`  
**Purpose**: Establish and freeze the verified baseline prior to Phase P1-P6 upgrades. No DQN, emergency priority, or dashboard code added in this phase.

---

## 1. Environment & Package Audit

| Item | Value / Status |
|---|---|
| **Python Version** | `Python 3.11.9 (tags/v3.11.9:de54cf5, Apr 2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]` |
| **Active Interpreter** | `E:\dp1-traffic-signal\.venv\Scripts\python.exe` |
| **eclipse-sumo** | `1.28.0` |
| **traci** | `1.28.0` |
| **sumolib** | `1.28.0` |
| **pandas** | `3.0.6` |
| **numpy** | `2.4.6` |
| **matplotlib** | `3.11.2` |
| **pytest** | `9.1.1` |
| **SUMO Binary** | Not in global Windows system `PATH`; dynamically located by `dp1.sumo_utils.binary("sumo")` at `E:\dp1-traffic-signal\.venv\Lib\site-packages\sumo\bin\sumo.exe` |
| **SUMO Version** | `Eclipse SUMO sumo 1.28.0 (Windows-10.0.26100 AMD64 MSVC 19.51.36260.0 Release)` |

All core requirements from `requirements.txt` are installed and up-to-date in `.venv`.

---

## 2. Test Suite Execution (`pytest -q`)

- **Command**:
  ```powershell
  & .venv\Scripts\python.exe -m pytest -q
  ```
- **Output**:
  ```text
  ......................                                                   [100%]
  22 passed in 30.47s
  ```
- **Status**: PASS (22 passed, 0 failures, 0 warnings).

---

## 3. Policy Smoke Tests & Safety Invariant Verification

Each existing policy was executed on scenario `imbalanced_ns` with seed `1`:
```powershell
& .venv\Scripts\python.exe -m dp1.cli run --scenario imbalanced_ns --policy <policy> --seed 1
```

### Actual Summary Outputs (Seed 1, Scenario: `imbalanced_ns`)

| Metric | `fixed` | `fixed_webster` | `adaptive` | `pressure` |
|---|---|---|---|---|
| `vehicles_total` | 1536 | 1536 | 1536 | 1536 |
| `vehicles_arrived` | 1536 | 1536 | 1536 | 1536 |
| `completion_rate` | 100% | 100% | 100% | 100% |
| `avg_wait_s` | 126.13 | 37.82 | 47.90 | 44.22 |
| `avg_time_loss_s` | 156.68 | 75.35 | 72.16 | 66.83 |
| `avg_trip_s` | 201.96 | 120.63 | 117.45 | 112.12 |
| `p95_wait_s` | 608.50 | 222.25 | 271.25 | 246.25 |
| `avg_queue_m` | 57.26 | 45.96 | 50.48 | 49.60 |
| `max_queue_m` | 149.17 | 149.90 | 149.86 | 149.90 |
| `throughput_veh_per_h` | 2398.00 | 2744.00 | 2770.00 | 2796.00 |
| `sim_end_s` | 2564.00 | 2083.00 | 2054.00 | 2027.00 |
| `cycles` | 25 | 102 | 52 | 56 |

### Safety Invariant Check
Every policy's phase timeline (`timeseries.csv`) was programmatically checked for transition validity:
- Phase cycle: `GREEN -> YELLOW (3 s) -> ALL_RED (2 s) -> GREEN (other axis)`
- Result: **Strictly preserved across all 4 policies** (no green-to-green transitions, no concurrent green on both axes).

---

## 4. Regenerated Baseline Comparison Matrix (Held-out Seeds 11–15)

Full evaluation matrix: 4 scenarios (`balanced`, `imbalanced_ns`, `imbalanced_ew`, `surge_north`) × 4 policies (`fixed`, `fixed_webster`, `adaptive`, `pressure`) × 5 held-out seeds (`11, 12, 13, 14, 15`) = **80 simulation runs**.

- **Command**:
  ```powershell
  & .venv\Scripts\python.exe -m dp1.cli compare --held-out --jobs 4
  ```

### Real Generated Results Table (`results/improvement.csv`)

| Scenario | Fixed Wait (s) | Webster Wait (s) | Adaptive Wait (s) | Pressure Wait (s) | Adaptive vs Fixed (%) | Pressure vs Fixed (%) | Adaptive vs Webster (%) | Fixed Queue (m) | Adaptive Queue (m) | Fixed Thru (veh/h) | Adaptive Thru (veh/h) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `balanced` | 39.93 | 16.45 | 20.84 | 17.14 | +47.8% | +57.1% | -26.7% | 30.97 | 17.62 | 2532.8 | 2568.0 |
| `imbalanced_ew` | 153.32 | 41.51 | 46.96 | 42.26 | +69.4% | +72.4% | -13.1% | 62.91 | 52.13 | 2198.8 | 2801.2 |
| `imbalanced_ns` | 126.81 | 38.44 | 44.46 | 41.58 | +64.9% | +67.2% | -15.7% | 61.06 | 48.40 | 2409.2 | 2780.8 |
| `surge_north` | 73.84 | 51.95 | 56.80 | 57.72 | +23.1% | +21.8% | -9.3% | 56.16 | 47.90 | 2807.6 | 2837.6 |

*Note: In `% change` columns, positive (+) indicates reduction in waiting time / improvement.*

---

## 5. Frozen Baseline Artifacts

All generated comparison files have been copied to `results/baseline_pre_upgrade/` to prevent overwriting during subsequent upgrade phases:

- [`results/baseline_pre_upgrade/all_runs.csv`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/all_runs.csv)
- [`results/baseline_pre_upgrade/aggregate.csv`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/aggregate.csv)
- [`results/baseline_pre_upgrade/improvement.csv`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/improvement.csv)
- [`results/baseline_pre_upgrade/wait_time.png`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/wait_time.png)
- [`results/baseline_pre_upgrade/queue_length.png`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/queue_length.png)
- [`results/baseline_pre_upgrade/queue_timeseries.png`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/queue_timeseries.png)
- [`results/baseline_pre_upgrade/report.md`](file:///e:/dp1-traffic-signal/results/baseline_pre_upgrade/report.md)

---

## 6. Documentation Truth Audit & Reconciliations

1. **Fixed Baseline Timing**:
   - `README.md` and `docs/SPEC.md` had stale references claiming the fixed plan was a 30s/30s placeholder.
   - Code reality: Configured as 105 s NS / 95 s EW in `dp1/config.py` based on an explicitly documented BTP timing-structure adaptation (Marathahalli Bridge Junction, Airport Police Station schedule; see `docs/SOURCES.md` and `docs/btp_marathalli_yamlur.pdf`).
   - The 15 s exclusive pedestrian phase from BTP is omitted in the two-phase vehicular model.
   - Reconciled in `README.md` and `docs/SPEC.md`.

2. **Network Geometry**:
   - `docs/SPEC.md` stated 1 lane per approach.
   - Code reality: `dp1/config.py` specifies `NetworkConfig.lanes = 2` (two lanes per approach, 300 m length, 150 m queue detector).
   - Reconciled in `docs/SPEC.md`.

3. **Test Count**:
   - `README.md` listed 11 tests.
   - Code reality: Exactly 22 tests in `tests/test_core.py`, all passing.
   - Reconciled in `README.md` and `docs/SPEC.md`.

4. **Prompts & Instructions File**:
   - `README.md` referenced `docs/PROMPTS.md`.
   - The file was confirmed present at `E:\PROMPTS.md` and restored to `docs/PROMPTS.md`.

---

## 7. Simulation-Only Limitations

- **Simulated Detectors**: Sensors are SUMO E2/lane-area detectors (`traci.lanearea.getJamLengthMeters`), not physical loop or camera sensors on Bengaluru streets.
- **Synthetic Junction**: 4-way orthogonal intersection with 2 lanes per approach; does not model complex grade-separated structures, u-turns, or mixed multimodal traffic (auto-rickshaws, two-wheelers).
- **Pedestrian Clearance**: The 15 s BTP pedestrian phase is not simulated.
- **Traffic Demand**: Poisson arrival demand at fixed rates; does not capture rain, breakdowns, or road works.
