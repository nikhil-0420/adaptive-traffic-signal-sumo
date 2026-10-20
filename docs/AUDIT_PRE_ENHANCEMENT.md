# DP1 Pre-Enhancement Architectural Audit & Defect Log

**Date:** 2026-10-20  
**Phase:** Mentor-Requested Enhancement: Hybrid Dynamic Signal Control with Exact Explanations  
**Author:** Nikhil (DP1 Implementation Engineer)

---

## 1. Verified Architecture & Existing Behavior

1. **Road Network Model (`network/marathahalli/`):**
   - Central node: `marathahalli_tls` at Cartesian coordinates `(0.0, -18.0)`.
   - **Grade-Separated Flyover (East-West):** Four elevated lanes carry Varthur Road through-traffic between HAL Airport Road (`node_hal_split`, $x = -180$) and Whitefield (`node_wf_split`, $x = +180$) with a vertical clearance of $+7.0\text{ m}$.
   - **Grade-Separated ORR Mainline (North-South):** Six mainline lanes pass beneath the flyover between ORR South (`node_orr_s_split`, $y = -180$) and ORR North (`node_orr_n_split`, $y = +180$), completely bypassing the surface signal.
   - **Surface Signalized Junction:** 4 surface legs (`leg_hal_in`, `leg_wf_in`, `leg_orr_s_in`, `leg_orr_n_in`), each providing two $3.5\text{ m}$ lanes governed by 16 signal heads.

2. **Controlled Approaches & Orientation:**
   - **North Approach (N):** KR Puram / ORR North $\rightarrow$ edge `leg_orr_n_in` (from $y = +25.0$ to $y = -18.0$). Controlled by detectors `det_orr_n_0` (lane 0) and `det_orr_n_1` (lane 1).
   - **South Approach (S):** Kadubeesanahalli / ORR South $\rightarrow$ edge `leg_orr_s_in` (from $y = -60.0$ to $y = -18.0$). Controlled by detectors `det_orr_s_0` (lane 0) and `det_orr_s_1` (lane 1).
   - **East Approach (E):** Whitefield Road $\rightarrow$ edge `leg_wf_in` (from $x = +45.0$ to $x = 0.0$). Controlled by detectors `det_wf_0` (lane 0) and `det_wf_1` (lane 1).
   - **West Approach (W):** HAL Old Airport Road $\rightarrow$ edge `leg_hal_in` (from $x = -45.0$ to $x = 0.0$). Controlled by detectors `det_hal_0` (lane 0) and `det_hal_1` (lane 1).

3. **Signal Phases & Clearances (`SignalStates` / `marathahalli.tll.xml`):**
   - Phase 0: East-West Green (`rrrrGGGgrrrrGGGg`), duration $105.0\text{ s}$ (BTP Phase 1 adapted).
   - Phase 1: East-West Yellow (`rrrryyyyrrrryyyy`), duration $3.0\text{ s}$.
   - Phase 2: All-Red Clearance (`rrrrrrrrrrrrrrrr`), duration $2.0\text{ s}$.
   - Phase 3: North-South Green (`GGGgrrrrGGGgrrrr`), duration $95.0\text{ s}$ (BTP Phase 2 adapted).
   - Phase 4: North-South Yellow (`yyyyrrrryyyyrrrr`), duration $3.0\text{ s}$.
   - Phase 5: All-Red Clearance (`rrrrrrrrrrrrrrrr`), duration $2.0\text{ s}$.
   - Total effective vehicle cycle: $210.0\text{ s}$. Total clearance lost time: $10.0\text{ s}$.

4. **Safety Invariants (`controllers/base.py`):**
   - Minimum green floor: $g_{\min} = 10.0\text{ s}$. Requests to terminate green before $10\text{ s}$ elapsed are rejected.
   - Maximum green ceiling: $g_{\max} = 60.0\text{ s}$. Green phases exceeding $60\text{ s}$ are forcibly switched.
   - Standard clearance: $\text{GREEN} \rightarrow \text{YELLOW (3s)} \rightarrow \text{ALL-RED (2s)} \rightarrow \text{GREEN}$. Direct green-to-green transitions or simultaneous orthogonal greens are impossible.

---

## 2. Confirmed Implementation Defects

### Defect 1: Inverted North/South Detector Labeling in `LiveMonitorView.jsx`
- **Location:** `frontend/src/views/LiveMonitorView.jsx`, lines 273–274.
- **Current Defective Code:**
  ```javascript
  { id: 'det_orr_s', label: 'North Approach (det_orr_s / Kadubeesanahalli)', val: telemetry?.queues_m?.N || 0, axis: 'NS' },
  { id: 'det_orr_n', label: 'South Approach (det_orr_n / KR Puram)', val: telemetry?.queues_m?.S || 0, axis: 'NS' },
  ```
- **Analysis:**
  - `det_orr_s` is located on `leg_orr_s_in` (coming from Kadubeesanahalli in the South). But the dashboard labeled it as "North Approach" while assigning it `telemetry?.queues_m?.N`!
  - `det_orr_n` is located on `leg_orr_n_in` (coming from KR Puram in the North). But the dashboard labeled it as "South Approach" while assigning it `telemetry?.queues_m?.S`!
  - In `runner.py`:
    - `"N": max(traci.lanearea.getJamLengthMeters("det_orr_n_0"), traci.lanearea.getJamLengthMeters("det_orr_n_1"))` (Correctly reads North).
    - `"S": max(traci.lanearea.getJamLengthMeters("det_orr_s_0"), traci.lanearea.getJamLengthMeters("det_orr_s_1"))` (Correctly reads South).
- **Corrected Mapping:**
  ```javascript
  { id: 'det_orr_n', label: 'North Approach (det_orr_n / KR Puram)', val: telemetry?.queues_m?.N || 0, axis: 'NS' },
  { id: 'det_orr_s', label: 'South Approach (det_orr_s / Kadubeesanahalli)', val: telemetry?.queues_m?.S || 0, axis: 'NS' },
  ```

### Defect 2: E2 Detector Length Coverage Limitation
- **Location:** `network/marathahalli/build/detectors.add.xml`.
- **Analysis:**
  - E2 detectors span from `pos="-25.0"` to `endPos="-0.1"` (length: $24.9\text{ m}$).
  - A detector jam length measurement cannot exceed $24.9\text{ m}$. If a queue stretches $50\text{ m}$, the detector reports $24.9\text{ m}$.
  - In `runner.py`, `read_queues()` previously treated this raw detector reading as the entire approach queue without exposing a saturation indicator or computing microscopic ground-truth queue extent.
- **Resolution Plan:**
  - Create a structured queue extraction module `dp1/queues.py`.
  - Expose per-lane detector queue length, per-lane vehicle count, saturation status (`is_saturated`), and approach-level ground-truth queue extent using vehicle positions and speeds ($v < 0.1\text{ m/s}$, contiguous gap $\le 7.5\text{ m}$).
  - Controller logic must explicitly document which measurement it consumes (sensor-visible vs ground truth).

---

## 3. Scope & Files Involved in Enhancement

1. `dp1/config.py`: Add `HybridQueueAdaptiveConfig` and register policy.
2. `dp1/queues.py` (New): Detailed per-lane, per-approach queue measurement engine.
3. `dp1/controllers/hybrid_queue_adaptive.py` (New): The proposed hybrid controller.
4. `dp1/controllers/__init__.py`: Register `hybrid_queue_adaptive`.
5. `dp1/runner.py`: Integrate queue telemetry and rich decision explanations.
6. `backend/schemas.py` & `backend/routes/`: Expose approach cards and decision explanation in API.
7. `frontend/src/views/LiveMonitorView.jsx`: Fix inverted labels, add 4 approach cards, add Adaptive Signal Decision panel with chronological history.
8. `tests/test_hybrid_controller.py` (New): Dedicated test suite.
9. `exp_marathahalli_hybrid_840`: New 840-cell experimental matrix.
