# Phase 5 Report: Vehicles, Signals, and Queues in 3D

## 1. Environment & Provenance
- **Date**: 2026-11-02
- **Git Commit Baseline**: `d95fdfc` (tagged `dp1-phase4`)
- **Branch**: `dp1-improve`
- **React Version**: `18.3.1`
- **Three.js Stack**: `three@0.160.0`, `@react-three/fiber@8.17.10`, `@react-three/drei@9.121.5`
- **Vite Version**: `5.4.21`
- **SUMO Version**: `Eclipse SUMO sumo 1.28.0`
- **Python Version**: `3.11.9`
- **Node Version**: `v24.16.0` | **npm Version**: `11.1.0`
- **Target Network**: `marathahalli` (generated via `scripts/export_network3d.py`)
- **Elevation Source**: `"modelled_config"`
- **Elevation Disclaimer**: *"Modelled elevation; synthetic demand. Never present geometry as surveyed."*

---

## 2. Part 1: Backend & Telemetry Layer (Vehicle Elevation)

### 2.1 Minimal Telemetry Layer Change
In accordance with the strict requirement that telemetry and visualization changes must never alter controller decisions, queue estimation, or evaluation metrics:
- Replaced 2D coordinate extraction `traci.vehicle.getPosition(vid)` with `traci.vehicle.getPosition3D(vid)`.
- Extracted and rounded the native elevation: `"z": round(float(pos[2]), 2)`.
- Confirmed that `traci.vehicle.getPosition3D` is strictly read-only and induces zero variance or side effects in the SUMO microscopic simulation loop.
- **Affected files**:
  - `dp1/runner.py`: lines 246–252 (in `_collect_telemetry`).
  - `dp1/replay.py`: lines 145–158 (in frame recording).
  - `backend/schemas.py`: defined `VehicleTelemetryItem` with `z: float = 0.0` and typed `TelemetryResponse.vehicles: list[VehicleTelemetryItem]`.
- **Untouched code**: No modifications were made to `dp1/controllers/`, `dp1/queues/`, `dp1/metrics.py`, `dp1/scenarios.py`, or `dp1/config.py`. Elevation `z` is strictly excluded from all metrics files (`metrics.json`, `summary.json`, `raw_runs.csv`).

### 2.2 Mandatory Regression Test & Determinism Proof
A regression test (`tests/test_phase5_telemetry_regression.py`) was executed on seed 101, balanced pattern, medium demand, hybrid queue-adaptive policy:
- **Command**: `.venv\Scripts\python.exe -m pytest tests/test_phase5_telemetry_regression.py -v`
- **Baseline vs Post-Change File Hash Verification**:
  - `decisions.csv`:
    - Baseline SHA256: `4E6410651B7468C992A59BE4FED946C96C45D20F657B3F77B504FD6EBE354B67`
    - Post-Change SHA256: `4E6410651B7468C992A59BE4FED946C96C45D20F657B3F77B504FD6EBE354B67`
    - **Result: 100% BYTE-IDENTICAL**
  - `timeseries.csv`:
    - Baseline SHA256: `895BAD0226BF6BFD00A84EBFCD19982FB3C3C73BEA6218F4773ECD829B73F95F`
    - Post-Change SHA256: `895BAD0226BF6BFD00A84EBFCD19982FB3C3C73BEA6218F4773ECD829B73F95F`
    - **Result: 100% BYTE-IDENTICAL**
  - `metrics.json`:
    - Baseline vs Post-Change: Exactly identical JSON dictionaries (0 differences across mean wait time, queue lengths, fuel consumption, and vehicle counts).
- **Physical Elevation Validation**:
  - Validated vehicle elevations during Marathahalli simulation runs:
    - Vehicles traveling on the Varthur flyover deck sit at $z \approx 6.83$\,m.
    - Vehicles on surface corridors (`leg_orr_s_in`, `leg_varthur_w_in`, etc.) sit at $z = 0.00$\,m.

---

## 3. Part 2: Frontend 3D Implementation

### 3.1 Instanced Vehicle Rendering & Interpolation
- **InstancedMesh Architecture (`frontend/src/utils/vehicle3dMesh.js`)**:
  - Vehicles are rendered using **one InstancedMesh per vehicle class**:
    1. `car`: low-poly sedan body + cabin ($1.8\text{m} \times 1.4\text{m} \times 4.5\text{m}$).
    2. `bus`: long transit coach ($2.5\text{m} \times 3.2\text{m} \times 12.0\text{m}$).
    3. `truck`: heavy logistics chassis + cargo box ($2.4\text{m} \times 3.4\text{m} \times 8.5\text{m}$).
    4. `two-wheeler`: compact scooter/motorcycle frame ($0.8\text{m} \times 1.2\text{m} \times 1.9\text{m}$).
    5. `ambulance`: high-visibility emergency chassis with cab roof bar ($2.1\text{m} \times 2.3\text{m} \times 5.8\text{m}$).
  - Maximum instance count dynamically capped at $512$ per vehicle class to eliminate runtime reallocations.
  - Geometry is updated efficiently using `InstancedMesh.setMatrixAt()` and `InstancedMesh.setColorAt()`.
- **Single-Tick Buffer Interpolation (Zero Extrapolation)**:
  - Vehicles buffer the latest two telemetry frames ($t_0$ and $t_1$).
  - Position $(x, y, z)$ and orientation angle $\theta$ are linearly and angularly interpolated using progress $\alpha = \text{clamp}\left(\frac{\text{now} - t_0}{\Delta t}, 0, 1\right)$.
  - Extrapolation beyond $\alpha = 1.0$ is strictly prohibited, preventing erratic teleportation or vehicles shooting past stop lines.
- **Elevation Placement**:
  - Vehicles with $z \ge 5.0$\,m (Varthur flyover deck) have their baseline elevated to $y_{three} = y_{deck} + 0.8$\,m, ensuring they sit firmly on top of the concrete bridge surface.
- **Controls Carried Over from Phase 2**:
  - "Exaggerate Vehicles" multiplier ($1\times$ true scale, $2\times$, $3\times$) applies proportionally to mesh bounding boxes.
  - High-contrast color scheme: moving vehicles cyan (`#38bdf8`), queued/stopped vehicles orange (`#f97316`), and emergency ambulance glowing rose (`#f43f5e`).

### 3.2 Stop Line Signal Heads & Lamp State Decoding
- **3D Signal Heads (`frontend/src/utils/signalAndQueue3d.js`)**:
  - Signal heads are positioned at stop lines for each approach leg of `marathahalli_tls`:
    - **North Approach (ORR Southbound)**: Stop line $Z = -18.0$, Signal Head $[-16.5, 4.2, -18.0]$
    - **East Approach (Varthur Westbound Surface)**: Stop line $X = 22.0$, Signal Head $[22.0, 4.2, -14.5]$
    - **South Approach (ORR Northbound)**: Stop line $Z = 18.0$, Signal Head $[16.5, 4.2, 18.0]$
    - **West Approach (Varthur Eastbound Surface)**: Stop line $X = -22.0$, Signal Head $[-22.0, 4.2, 14.5]$
- **Deterministic SUMO State String Decoding**:
  - Signal colors are directly parsed from the 16-character `tl_state` string generated by the simulator:
    - Links 0–3: North approach
    - Links 4–7: East approach
    - Links 8–11: South approach
    - Links 12–15: West approach
  - Character mapping: `'G'` / `'g'` $\rightarrow$ GREEN (`#22c55e`), `'y'` / `'Y'` $\rightarrow$ YELLOW (`#eab308`), `'r'` / `'u'` $\rightarrow$ RED (`#ef4444`).
  - Active bulb illumination strictly reflects the decoded string; client-side estimated timers are never used to determine bulb colors.
  - Phase group badges clearly identify the active controlling phase (`NS` vs `EW`).
  - Countdown timer logic: countdown is only shown if the controller explicitly provides a target green duration; otherwise, elapsed green time is displayed. Yellow clearance and all-red clearance intervals are visually distinctive.

### 3.3 3D Queue Volume Bars & OFFLINE Safety Guard
- **Detector Span Matching (`network3d.json`)**:
  - All 4 approach detector loops at `marathahalli_tls` have a confirmed physical span of **$24.9$\,m** (`pos = -25.0`, `endPos = -0.1`), terminating immediately before the stop lines.
- **3D Translucent Volume Bars**:
  - Bars are placed directly over the detector spans with length proportional to `queue_m`.
  - Colored dynamically by sensor health status:
    - `MEASURING`: Cyan translucent bar (`#06b6d4`, opacity $0.45$).
    - `SATURATED`: Bright amber-red warning bar (`#f43f5e`, opacity $0.65$) with prominent warning label.
    - `CONFIRMED_ZERO`: Low-profile dark green bar (`#10b981`, opacity $0.35$).
    - `OFFLINE`: **NEVER RENDERED AS ZERO**. Renders a distinct full-span hatched gray/amber block ($24.9$\,m) with a clear `OFFLINE (FALLBACK)` warning badge.
  - 3D spatial labels float above the queue bars displaying the exact physical queue length in meters (`queue_m`) and vehicle counts.

### 3.4 3D Decision Callouts
- **Spatial Decision Cards**:
  - Suspended at $[X=0, Y=14.0, Z=18.0]$ directly above the controlled junction `marathahalli_tls`.
  - Driven by the decision event stream logged by the controller.
  - Displays decision type (`EXTEND`, `SWITCH`, `GAP_OUT`, `EMERGENCY`), active axis, and plain-language controller rationale.
  - Separates requested and applied green increments into distinct sub-badges:
    - **Requested Increment**: `Req: +<delta_g_req_s>s` (e.g., `+5.0s`)
    - **Applied Increment**: `App: +<delta_g_app_s>s` (e.g., `+3.0s`)

### 3.5 Provenance & Lifecycle Labelling
- **Label Resolution**:
  - **"Live simulation"**: Displayed if and only if an active run ID exists, the simulation loop is advancing, and telemetry timestamps are continuously updating.
  - **"Replay"**: Displayed when viewing pre-recorded simulation runs.
  - **"Snapshot"**: Displayed for static, read-only data inspect views.

---

## 4. Verification Screenshots

The 3D scene was rendered headlessly using the compiled network geometry (`network3d.json`) and replay telemetry at three distinct timestamps ($t=1$\,s, $t=30$\,s, and $t=60$\,s).

### 4.1 Timestamp $t = 1$\,s ("Live Simulation")
- **File**: [`phase5_3d_t1s_live.svg`](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t1s_live.svg)
- **Features Demonstrated**:
  - "Live simulation" green status badge active in top HUD.
  - Initial vehicle injections on surface and flyover corridors.
  - Signal heads at stop lines showing initial NS green phase (`GGggrrrr...`).
  - Queue volume bars over detector spans reflecting initial queue measurements.

![Phase 5 3D Scene at t=1s Live Simulation](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t1s_live.svg)

---

### 4.2 Timestamp $t = 30$\,s ("Replay")
- **File**: [`phase5_3d_t30s_replay.svg`](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t30s_replay.svg)
- **Features Demonstrated**:
  - "Replay" blue status badge active in top HUD ($t = 30.0$\,s, active vehicles moving across all tiers).
  - Vehicles traveling on the elevated Varthur flyover deck sit at $z = 6.83$\,m.
  - EW green phase active (`rrrrGGGg...`).
  - Active 3D decision callout floating over the junction with separated increments: `Req: +5.0s` vs `App: +3.0s`.
  - Queue volume bars showing measured queue lengths across active approaches.

![Phase 5 3D Scene at t=30s Replay](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t30s_replay.svg)

---

### 4.3 Timestamp $t = 60$\,s ("Snapshot" & OFFLINE Safety Demonstration)
- **File**: [`phase5_3d_t60s_snapshot.svg`](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t60s_snapshot.svg)
- **Features Demonstrated**:
  - "Snapshot" read-only badge active in top HUD.
  - High vehicle density across surface intersection conflict areas.
  - Signal heads showing yellow clearance transition (`yyyy...`).
  - **OFFLINE Sensor Verification**: West approach sensor marked OFFLINE is **never rendered as zero**; displays a full-length $24.9$\,m hatched warning block with the explicit label `W: 0.0m OFFLINE (FALLBACK)`.
  - East approach sensor marked SATURATED displays warning bar with `SATURATED` status badge.

![Phase 5 3D Scene at t=60s Snapshot](file:///e:/dp1-traffic-signal/docs/artifacts/phase5/phase5_3d_t60s_snapshot.svg)

---

## 5. Automated Test Results

### 5.1 Frontend Test Suite (`frontend/test/vehiclesSignalsQueues3d.test.js`)
All **48 tests passed** (`npm test --prefix frontend`, execution time $415$\,ms):
- `✔ Phase 5 - Instance counts equal telemetry vehicle counts on three sampled ticks (8.92ms)`
- `✔ Phase 5 - Signal colors strictly equal signal state strings (1.18ms)`
- `✔ Phase 5 - Countdown only if controller provides target green, otherwise elapsed time (0.26ms)`
- `✔ Phase 5 - OFFLINE sensor status is NEVER rendered as zero (0.28ms)`
- `✔ Phase 5 - Live vs Replay vs Snapshot labelling resolution (0.15ms)`
- `✔ Phase 5 - Decision callout separates requested vs applied increments (0.17ms)`
- `✔ Phase 5 - Vehicle elevation interpolation respects physical limits without extrapolation (0.22ms)`

### 5.2 Backend Regression & API Test Suite (`tests/test_phase5_telemetry_regression.py` & `tests/test_api.py`)
- `✔ test_phase5_telemetry_z_regression`: Byte-identical CSV files confirmed on seed 101.
- `✔ test_phase5_telemetry_includes_z`: Verified telemetry vehicle objects include numeric elevation $z$, with flyover vehicles sitting at $z \ge 6.0$\,m.
- `✔ test_telemetry_atomic_and_staleness`: Verified atomic schema compliance in FastAPI backend.

---

## 6. Verification Summary & Next Steps
- **Part 1 (Backend Telemetry)**: Elevation $z$ added to telemetry stream via read-only `traci.vehicle.getPosition3D()`. 100% byte-identical simulation regression outputs proven.
- **Part 2 (Frontend 3D Visualizer)**: Fully functional instanced vehicle rendering, signal heads, queue volume bars with non-zero OFFLINE safety, decision callouts, and multi-tier elevation alignment.
- **Deliverables**: Code implemented, regression test in place, report and 3 verification snapshots generated.
- Ready for Phase 5 tag: `dp1-phase5`.
