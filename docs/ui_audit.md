# Phase 1: Comprehensive Map & Telemetry Audit

**Status**: Completed  
**Branch**: `dp1-improve`  
**Network**: Marathahalli Bridge Junction (`marathahalli`)  
**Scope**: Frontend map rendering components, telemetry pipeline, visibility bottlenecks, and controller decision logging provenance.  
**Constraint Enforced**: Strictly read-only audit. No production code changes made during this phase.

---

## 1. Map Component & Telemetry Architecture

### 1.1 Rendering Pipeline
- **Core Component**: [`frontend/src/components/IsometricIntersection.jsx`](../frontend/src/components/IsometricIntersection.jsx) (1,512 lines).
- **Hosting Views**:
  - Live Twin Monitoring: [`frontend/src/views/LiveMonitorView.jsx`](../frontend/src/views/LiveMonitorView.jsx)
  - Site Model View: [`frontend/src/views/SiteModelView.jsx`](../frontend/src/views/SiteModelView.jsx)
  - Operations / Replay Twin: [`frontend/src/components/JunctionTwin.jsx`](../frontend/src/components/JunctionTwin.jsx)
  - Synthetic Mock Sandbox (Exploratory): [`frontend/src/views/LiveSimulationView.jsx`](../frontend/src/views/LiveSimulationView.jsx)
- **Rendering Technology**: HTML5 2D Canvas (`<canvas>`, `canvas.getContext('2d')`) running at up to 60 FPS via `requestAnimationFrame` with high-DPI scaling (`window.devicePixelRatio` capped at 2.0).
- **Projections**:
  - **2.5D Isometric Mode (default)**: 30° orthographic tilt with screen coordinates derived as:
    $$\begin{aligned}
    u &= w_x - 350.0, \quad v = w_y - 350.0 \\
    x_{\text{iso}} &= (u - v) \cos(30^\circ) \\
    y_{\text{iso}} &= (u + v) \sin(30^\circ) \\
    x_{\text{screen}} &= c_x + x_{\text{iso}} \cdot \text{baseScale} \\
    y_{\text{screen}} &= c_y - y_{\text{iso}} \cdot \text{baseScale} \cdot 0.72 - z \cdot \text{baseScale} \cdot 1.85 + \text{tierOffsetY}
    \end{aligned}$$
  - **Top-Down Mode**: Plan-view orthographic projection ($x_{\text{screen}} = c_x + u \cdot \text{baseScale}, \; y_{\text{screen}} = c_y - v \cdot \text{baseScale}$).

### 1.2 Vehicle Drawing & Sizing
- **Geometry & Shape**: Rendered using rotated rounded rectangles (`drawSafeRoundRect`) aligned along `sumoAngleToScreen(headingAngle)`. Includes vehicle ground shadow (`rgba(0,0,0,0.45)`), body paint, roof glass, brake lights (illuminated below $0.8$ m/s), and headlight cones in dark mode.
- **Base Scale**:
  $$\text{baseScale} = \frac{\min(w, h)}{480 \times 1.45} \times \text{currentZoom} \approx 1.006 \times \text{currentZoom} \quad (\text{for } 1200 \times 700 \text{ viewport})$$
- **Visibility Scaling Clamping**: To prevent sub-pixel disappearance at 100% zoom, a visibility factor (`visFactor`) is computed:
  $$\text{visFactor} = \max\left(1.0, \frac{13.0\text{ px}}{4.8 \cdot \text{baseScale}}\right) \cdot (1 - t_{\text{ease}}) + 1.0 \cdot t_{\text{ease}}$$
  This inflates a car from nominal $4.8$ px up to $13.0$ px at 100% zoom ($2.693\times$ stretch), easing down to $1.0\times$ at 350% zoom.

### 1.3 Canvas Draw Order (Z-Ordering)
1. Canvas background fill (`#0D1417`) and engineering coordinate grid.
2. Exploded 3-Tier vertical dashed guideposts (when exploded).
3. **Tier 3 (Underpass trench)**: Asphalt ribbons, retaining walls, and dashed lane dividers for ORR mainline.
4. **Tier 2 (Surface level)**: Conflict junction polygons, surface approaches, yellow medians, lane markings, E2 detector translucent sensor overlays, and curb-mounted 3D signal heads / stop lines.
5. **Tier 1 (Elevated flyover)**: Ground shadow (`rgba(0,0,0,0.45)` at $z=0$), concrete support piers, elevated asphalt deck ($z=+7.0$m), and parapets.
6. **Vehicles**: Rendered in a single batch via `currentVehicles.forEach(v => ...)` in whatever arbitrary order TraCI returns IDs.
7. **Overlay UI**: 3D floating tier badges (when exploded), HUD status pills, and camera control icons.

### 1.4 Telemetry Polling Mechanics
- **Endpoint**: `GET /api/runs/{run_id}/telemetry` served by FastAPI [`backend/routes/runs.py`](../backend/routes/runs.py).
- **Backend File Source**: Atomic JSON snapshots written to `results/runs/{run_id}/telemetry.json` at each simulation step by `dp1.runner._write_atomic_telemetry`.
- **Polling Interval**: Set to **1,500 ms** (1.5 seconds) in `LiveMonitorView.jsx` (lines 107–108).
- **Simulation Step Rate**: TraCI runs at $1.0$ s steps ($\Delta t = 1.0$ s).
- **Resulting Behavior**: Telemetry arrives at $0.67$ Hz while simulation advances at $1.0$ Hz, causing discrete 1–2 second burst jumps that require client interpolation.

---

## 2. Dev Seed 101 Live Run Audit (Task 2)

**Setup**: Dev seed 101, medium demand, stationary scenario `imbalanced_orr`, Marathahalli network model, policy `hybrid_queue_adaptive`. Output: `scratch/phase1_consecutive_telem/`.

### Consecutive Telemetry Samples

#### Sample 1 ($t = 26.0$ s)
- **Status**: `running` | **Phase**: `GREEN` | **Active Axis**: `NS` (Kadubeesanahalli / KR Puram)
- **Queues (m)**: `N: 0.0`, `S: 0.0`, `E: 0.0`, `W: 0.0`
- **Signal Light State**: `GGGgrrrrGGGgrrrr`
- **Vehicle Count in Telemetry**: **20**
- **HUD "active vehs" Pill**: **20**
- **Canvas Render Loop Executions**: **20**
- **Inside Visible Viewport ($1200 \times 700$)**: **20**
- **Ground-Truth Tier Distribution**: 4 flyover, 5 underpass, 11 surface
- **Frontend Heuristic Tier Inference**: 5 flyover, 9 underpass, 6 surface (5 vehicles misclassified)

#### Sample 2 ($t = 27.0$ s)
- **Status**: `running` | **Phase**: `GREEN` | **Active Axis**: `NS`
- **Queues (m)**: `N: 0.0`, `S: 0.0`, `E: 0.0`, `W: 0.0`
- **Signal Light State**: `GGGgrrrrGGGgrrrr`
- **Vehicle Count in Telemetry**: **21**
- **HUD "active vehs" Pill**: **21**
- **Canvas Render Loop Executions**: **21**
- **Inside Visible Viewport**: **21**
- **Ground-Truth Tier Distribution**: 4 flyover, 5 underpass, 12 surface
- **Frontend Heuristic Tier Inference**: 6 flyover, 9 underpass, 6 surface (6 vehicles misclassified)

#### Sample 3 ($t = 28.0$ s)
- **Status**: `running` | **Phase**: `GREEN` | **Active Axis**: `NS`
- **Queues (m)**: `N: 0.0`, `S: 0.0`, `E: 0.0`, `W: 0.0`
- **Signal Light State**: `GGGgrrrrGGGgrrrr`
- **Vehicle Count in Telemetry**: **23**
- **HUD "active vehs" Pill**: **23**
- **Canvas Render Loop Executions**: **23**
- **Inside Visible Viewport**: **23**
- **Ground-Truth Tier Distribution**: 4 flyover, 5 underpass, 14 surface
- **Frontend Heuristic Tier Inference**: 6 flyover, 10 underpass, 7 surface (7 vehicles misclassified)

### Count Discrepancy Resolution
- **Telemetry vs HUD vs Canvas**: In the real TraCI pipeline, there is **zero count mismatch**: `len(telemetry.vehicles) == HUD_count == canvas_rendered_count`.
- **Origin of "3 active vehs" Finding**: Found hard-coded in the exploratory prototype file [`frontend/src/views/LiveSimulationView.jsx`](../frontend/src/views/LiveSimulationView.jsx#L304-L308):
  ```javascript
  vehicles: [
    { id: 'v0', x: 350, y: 350 + (simTime % 30) * 4, z: 0, s: 11.2, w: 0 },
    { id: 'v1', x: 350, y: 380 + (simTime % 30) * 3, z: 0, s: 9.5, w: 1 },
    { id: 'v2', x: 310 + (simTime % 40) * 5, y: 350, z: 7, s: 13.8, w: 0 },
  ]
  ```
  That mock sandbox generated exactly 3 artificial vehicles. The production TraCI monitor ([`LiveMonitorView.jsx`](../frontend/src/views/LiveMonitorView.jsx)) binds directly to `api.getTelemetry()` and accurately reflects ground-truth simulation counts (20–23 active vehicles at $t=26-28$s).

---

## 3. Evaluation of Hypotheses (Task 3)

| Hypothesis | Finding | Evidence & Metric |
| :--- | :---: | :--- |
| **H1: Sprites are too small at default zoom** | **YES** | At 100% zoom without clamp, a car is only **4.8 px long**. With the current 13px clamp, it renders at $13.0 \times 5.1$ px. At 350% zoom, the road magnifies by $3.5\times$, but cars only enlarge to $16.9 \times 6.7$ px ($1.3\times$). Vehicles appear tiny relative to the roadway. |
| **H2: Vehicle colours have poor road contrast** | **YES** | Road asphalt is `#29343A`. **BMTC Transit Bus** (`#0F6B7A`) has a contrast ratio of **2.07:1** (fails WCAG < 3.0:1 threshold). **Dark Blue Cars** (`#3B82F6`) have **3.47:1**. Flyover shadow (`rgba(0,0,0,0.45)`) further degrades luminance. |
| **H3: Flyover deck draws OVER surface vehicles** | **NO** | The reverse bug exists: Flyover deck is drawn in Step 5.3; vehicles are drawn in Step 6. Therefore, **surface vehicles are drawn ON TOP of the flyover deck**. Furthermore, vehicles lack depth sorting. |
| **H4: Flyover vs surface vehicles not distinguished** | **YES** | Telemetry omits $z$, lane ID, and tier. The frontend heuristic bounding-box guess had an empirical **28.6% error rate** at $t=27$s (misclassifying 6 of 21 vehicles, placing surface vehicles on the elevated deck). |
| **H5: Low vehicle count is genuine demand dynamics** | **YES** | Route file analysis reveals that by $t=27$s, only **23 vehicles have departed network-wide**. Only **8 vehicles (34.8%)** are routed to the surface junction; 15 bypass via flyover/underpass/slip. Physical transit from network perimeter takes 20–30s. |
| **H6: Telemetry rate is too low or irregular** | **YES** | Client polling is hard-coded to **1,500 ms** (0.67 Hz) while SUMO steps at **1,000 ms** (1.0 Hz). Updates arrive in discrete multi-second bursts. |
| **H7: Queued vehicles overlap each other** | **YES** | SUMO spacing is $5.0$m length + $2.5$m gap = $7.5$m ($7.3$ px at 100% zoom). The 13 px clamped car sprite causes **5.7 px of overlap (43.5% body overlap)** in stopped queues. |

### Quantitative Detail Tables

#### Vehicle Dimensions: 100% vs 350% Zoom
*(Calculated on $1200 \times 700$ Canvas, Base Scale: $1.006$ px/m at 100%, $3.520$ px/m at 350%)*

| Vehicle Type | World (L $\times$ W) | Rendered @ 100% Zoom | Rendered @ 350% Zoom | Nominal Len @ 100% | Clamp Inflation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Passenger Car** | $4.8\text{m} \times 1.9\text{m}$ | $13.0\text{ px} \times 5.1\text{ px}$ | $16.9\text{ px} \times 6.7\text{ px}$ | $4.8\text{ px}$ | $+170.8\%$ |
| **Motorcycle** | $2.2\text{m} \times 0.8\text{m}$ | $6.0\text{ px} \times 2.2\text{ px}$ | $7.7\text{ px} \times 2.8\text{ px}$ | $2.2\text{ px}$ | $+172.7\%$ |
| **Auto-Rickshaw** | $2.8\text{m} \times 1.4\text{m}$ | $7.6\text{ px} \times 3.8\text{ px}$ | $9.9\text{ px} \times 4.9\text{ px}$ | $2.8\text{ px}$ | $+171.4\%$ |
| **Transit Bus** | $11.5\text{m} \times 2.6\text{m}$ | $31.1\text{ px} \times 7.0\text{ px}$ | $40.5\text{ px} \times 9.2\text{ px}$ | $11.6\text{ px}$ | $+168.1\%$ |
| **Commercial Truck**| $9.5\text{m} \times 2.5\text{m}$ | $25.7\text{ px} \times 6.8\text{ px}$ | $33.4\text{ px} \times 8.8\text{ px}$ | $9.6\text{ px}$ | $+167.7\%$ |
| **Ambulance** | $6.5\text{m} \times 2.3\text{m}$ | $17.6\text{ px} \times 6.2\text{ px}$ | $22.9\text{ px} \times 8.1\text{ px}$ | $6.5\text{ px}$ | $+170.8\%$ |

#### Color Contrast Ratios (WCAG 2.1) Against Road Asphalt (`#29343A`)

| Vehicle Color / Role | Hex Code | Contrast vs Asphalt (`#29343A`) | Contrast vs Ground (`#0D1417`) | Compliance Status |
| :--- | :--- | :--- | :--- | :--- |
| **Ambulance White** | `#FFFFFF` | **12.75 : 1** | 18.59 : 1 | PASS (Enhanced $\ge 7:1$) |
| **Phasora Amber** | `#FFB020` | **6.97 : 1** | 10.17 : 1 | PASS ($\ge 4.5:1$) |
| **Motorcycle Teal** | `#4FB3C2` | **5.20 : 1** | 7.58 : 1 | PASS ($\ge 4.5:1$) |
| **Car Slate Grey** | `#94A3B8` | **4.97 : 1** | 7.25 : 1 | PASS ($\ge 4.5:1$) |
| **Auto Green** | `#2FA866` | **4.20 : 1** | 6.12 : 1 | PASS Large ($\ge 3:1$) |
| **Truck Terracotta** | `#E06A3B` | **3.82 : 1** | 5.57 : 1 | PASS Large ($\ge 3:1$) |
| **Car Dark Blue** | `#3B82F6` | **3.47 : 1** | 5.05 : 1 | PASS Large ($\ge 3:1$) |
| **BMTC Transit Bus** | `#0F6B7A` | **2.07 : 1** | 3.01 : 1 | **FAIL** ($< 3:1$) |

---

## 4. Telemetry Field Audit (Task 4)

### Fields Present in Vehicle Payload
- `id` (string): Vehicle unique identifier (e.g., `"v0"`).
- `x` (float): X coordinate in SUMO network meters (rounded to 0.1m).
- `y` (float): Y coordinate in SUMO network meters (rounded to 0.1m).
- `a` (float): Heading angle in degrees (0 = North, 90 = East, 180 = South, 270 = West).
- `s` (float): Current speed in m/s (rounded to 0.1 m/s).
- `em` (boolean): Flag indicating whether the vehicle is the designated emergency ambulance.

### Fields Missing in Vehicle Payload
1. **`z` / Elevation**: **MISSING**. TraCI `traci.vehicle.getPosition3D(vid)[2]` is not called. Without $z$, the UI cannot know whether a vehicle is at $-4.0$m (underpass), $0.0$m (surface), or $+7.0$m (flyover).
2. **`type` / Vehicle Class**: **MISSING**. The vehicle dictionary does not include the SUMO `vType` (e.g. `car`, `bus`, `truck`, `emergency`). The frontend currently generates fake vehicle classifications by hashing the ID string modulo 100.
3. **`length` & `width`**: **MISSING**. True physical bounding box dimensions from SUMO are not transmitted.
4. **`lane_id`**: **MISSING**. SUMO edge/lane ID is omitted, preventing exact topological alignment with lanes.
5. **`waiting_time`**: **MISSING**. SUMO accumulated waiting time (`traci.vehicle.getWaitingTime`) is not sent; frontend defaults to 0.
6. **`stopped_or_queued` flag**: **MISSING**. Whether the vehicle is part of a standing queue is not flagged; frontend uses heuristic `speed < 0.8` m/s.

---

## 5. Decision Event Text Provenance (Task 5)

Two separate mechanisms generate event text in the repository:

### 5.1 Hard-Coded Synthetic Mock Strings
Found directly inside [`frontend/src/views/LiveSimulationView.jsx`](../frontend/src/views/LiveSimulationView.jsx#L264-L278):
```javascript
} else if (simTime % 30 === 15) {
  outcome = 'EXTEND_APPROVED';
  action = 'EXTEND';
  deltaG = 3.0;
  setActiveToast({
    id: `toast_${simTime}`,
    title: '+3.0s Green Extended',
    text: `Continuous arrivals on ${currentAxis}; opposing queues within fairness bounds.`,
    type: 'green',
  });
} else if (simTime % 30 === 25) {
  outcome = 'SWITCH_GAP_OUT';
  action = 'GAP_OUT';
  setActiveToast({
    id: `toast_${simTime}`,
    title: 'Early Gap-Out Terminated',
    text: `No vehicles detected on stop-line detector for 3s; initiating yellow clearance.`,
    type: 'yellow',
  });
}
```
*Conclusion*: These exact strings were authored directly in the frontend inside an artificial mock simulation view used during early prototyping.

### 5.2 Real Controller Logged Reasons & Explainer Utility
In real TraCI simulation runs, the controller [`dp1/controllers/hybrid_queue_adaptive.py`](../dp1/controllers/hybrid_queue_adaptive.py) logs structured decision records containing `decision_outcome`, `reason_code`, and an explicit `reason` string:
- `reason_code = "SWITCH_GAP_OUT"`:
  `"North–South queue cleared (0.0m for 3.0s >= gap-out threshold 3.0s) while East–West is waiting (12.4m); gapping out early."`
- `reason_code = "EXTEND_APPROVED"`:
  `"North–South green extended by 3 seconds: its queue/demand condition (18.2m >= 15.0m) satisfied the configured extension rule, the competing-direction wait (14.0s) remained within its permitted limit (35s), and maximum green was not reached."`

The production dashboard uses [`frontend/src/utils/explainDecision.js`](../frontend/src/utils/explainDecision.js) to format these controller-generated records into plain-language prose with outcome-first headlines.

---

## 6. Hybrid Controller Gap-Out Implementation (Task 6)

Does `HybridQueueAdaptiveController` implement gap-out logic?  
**YES**. It is implemented in [`dp1/controllers/hybrid_queue_adaptive.py`](../dp1/controllers/hybrid_queue_adaptive.py#L167-L194):

```python
# -------------------------------------------------------------
# 3. Gap-Out Evaluation: Active approach fully cleared
# -------------------------------------------------------------
if own_q <= 0.0 and comp_q >= c.min_competing_queue_m:
    if self._empty_since is None:
        self._empty_since = t
    empty_duration = t - self._empty_since
    if empty_duration >= c.gap_out_s:
        rec = self._make_record(
            t, axis, "GAP_OUT",
            f"{axis_label} queue cleared (0.0m for {empty_duration:.1f}s >= gap-out threshold {c.gap_out_s:.1f}s) while {comp_label} is waiting ({comp_q:.1f}m); gapping out early.",
            "SWITCH_GAP_OUT", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False,
            proposed_action="GAP_OUT", applied_action="GAP_OUT", decision_outcome="SWITCH_GAP_OUT"
        )
        self.last_decision_record = rec
        self.decisions.append(rec)
        return True
    else:
        rec = self._make_record(
            t, axis, "HOLD",
            f"{axis_label} queue empty for {empty_duration:.1f}s (< gap-out persistence {c.gap_out_s:.1f}s); holding green for clearance.",
            "HOLD_CLEARING", 0.0, 0.0, elapsed, own_q, comp_q, score_active, score_competing, queues, False,
            proposed_action="GAP_OUT", applied_action="HOLD", decision_outcome="HOLD_CLEARING"
        )
        self.last_decision_record = rec
        return False
else:
    self._empty_since = None
```

### Architectural Implications for the Phase 10 Ablation Ladder
1. **Execution Point**: The gap-out check executes at Step 3 of `green_should_end()`, immediately following `min_green_s` enforcement (Step 1) and `max_green_s` enforcement (Step 2), but **before** target green duration evaluation (Step 4).
2. **Early Termination Impact**: If `own_q == 0` for 3 consecutive seconds after $t \ge 10$s, the controller triggers a switch to yellow even if the Webster baseline allocation was $15$s or $30$s.
3. **Competing Queue Requirement**: Gap-out requires `comp_q >= c.min_competing_queue_m` ($1.0$m). If opposing approaches have no queued vehicles, green is held.
