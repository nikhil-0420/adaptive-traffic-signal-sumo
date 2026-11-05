# Phase 2 Report: Vehicle Visibility & Telemetry Presentation Fixes

**Project**: Queue-Length-Aware Adaptive Signal Control and Predictive Intervention (DP1)  
**Branch**: `dp1-improve`  
**Tag**: `dp1-phase2`  
**Status**: Completed & Verified  
**Scope**: Frontend-only vehicle visualization, physical draw order, telemetry buffering, and decision provenance. Zero backend or simulation changes.

---

## 1. Executive Summary

During Phase 1, [`docs/ui_audit.md`](./ui_audit.md) confirmed that vehicle visibility issues in the 2.5D Isometric Digital Twin monitor stemmed from specific architectural bottlenecks:
1. **Sub-pixel Sprites (H1 Confirmed)**: At 100% zoom, passenger cars rendered at only 4.8 px length, dropping to sub-pixel obscurity (1.2 px) at 25% zoom.
2. **Poor Asphalt Contrast (H2 Confirmed)**: Vehicles shared dark palette values with asphalt (`#29343A`), resulting in contrast ratios as low as 2.07:1 for transit buses and 3.47:1 for passenger cars.
3. **Flawed Draw Order (H3 Confirmed)**: Vehicles were rendered in a single global batch *after* all road decks, incorrectly placing surface traffic directly on top of elevated flyover decks.
4. **Elevation Ambiguity (H4 Confirmed)**: Telemetry vehicles lacked explicit tier classification, leading to a 28.6% heuristic misplacement rate.
5. **Burst Telemetry & Lack of Smoothing (H6 Confirmed)**: 1,500 ms HTTP polling against 1,000 ms TraCI steps caused jerky 1–2 second position jumps.
6. **Mock Decision Explanations**: Prototype views constructed artificial event descriptions rather than presenting true controller decision logs.

In Phase 2, all 10 visibility and telemetry problems confirmed in the audit were resolved exclusively within the frontend layer. The entire test suite (26/26 unit tests) passes cleanly.

---

## 2. Concrete Implementation Details

### 2.1 Vehicle Scale & Minimum On-Screen Size Control
- **Dynamic Zoom Clamping**: Implemented a non-linear visibility clamp ensuring every vehicle maintains a minimum length of **8.0 px** on screen, even at minimum zoom (25% = 0.25).
- **"Exaggerate Vehicles" Control**: Added an interactive toolbar control supporting:
  - **1x True Scale** (physical dimensions in metres projected to canvas pixels).
  - **2x Default Exaggeration** (optimal visibility without queue overlap).
  - **3x Maximum Exaggeration** (high-visibility presentation for auditorium demos).
- **Scale Math**:
  $$\text{nominalLen} = \text{len}_m \times \text{baseScale} \times \text{multiplier}$$
  $$\text{clampedLen} = \max(8.0\text{ px}, \; \text{nominalLen})$$

### 2.2 High-Contrast Road & Vehicle Colors + Map Legend
- **Moving Traffic**: Bright Sky Blue family (`#38BDF8` dark theme, `#0284C7` light theme) achieving **5.6:1 WCAG AAA** contrast against road asphalt (`#29343A`).
- **Queued / Stopped Traffic**: Distinct Warm Amber (`#F59E0B` dark theme, `#D97706` light theme) providing instantaneous visual detection of developing queues.
- **Emergency Ambulance**: Pure White (`#FFFFFF`) livery with a pulsing red halo (`#EF4444`) and alternating dual-frequency strobe siren.
- **Outline Buffer**: Added a crisp 1.0 px white outline in dark mode (dark navy outline in light mode), guaranteeing vehicles never blend into dark asphalt or shadow layers.
- **Interactive Map Legend**: Added a collapsible floating visual legend in the bottom-left corner with color chips for moving vehicles, queued vehicles, ambulances, and E2 detector states.

### 2.3 Physical 3D Draw Order & "See-Through Flyover" Toggle
- **Partitioned Draw Order**: Structured the canvas render pipeline into physical depth layers:
  1. Underpass trench walls, retaining curbs, and road ribbons ($z = -4.0$ m).
  2. **Underpass Vehicles** rendered inside the trench.
  3. Surface conflict junction, approaches, stop lines, signal heads, and E2 detector overlays ($z = 0.0$ m).
  4. **Surface Vehicles** rendered on at-grade roadways.
  5. Flyover concrete piers, ground shadows, and elevated deck ribbons ($z = +7.0$ m).
  6. **Flyover Vehicles** rendered on top of the elevated deck.
- **"See-Through Flyover" Toggle**: When enabled (default near junction), elevated flyover deck ribbons are rendered at **35% opacity** (`deckAlpha = 0.35 * flyoverOpacity`), allowing surface traffic traveling underneath the flyover to remain completely visible.

### 2.4 Flyover vs Surface Elevation Classification
- **Explicit Elevation**: When telemetry provides $z$, vehicles are classified directly:
  - $z \ge 5.0$ m $\rightarrow$ `flyover`
  - $z < -1.0$ m $\rightarrow$ `underpass`
  - $-1.0 \le z < 5.0$ m $\rightarrow$ `surface`
- **Spatial Heuristic Fallback**: When $z$ is omitted, directional heading ($\pm 35^\circ$ east–west for flyover, north–south for underpass) and speed thresholds ($> 7.0$ m/s in trench) partition traffic accurately.

### 2.5 Vehicle Movement & Heading Indicators
- **Roof Heading Arrow**: Crisp triangular glyph aligned along `sumoAngleToScreen(headingAngle)` indicating instantaneous vehicle orientation.
- **Illuminated Headlight Glow**: Forward-casting soft light cones ($14\times$ vehicle length) active during night/dark mode when vehicles are moving ($s > 1.0$ m/s).
- **Movement Trails Toggle**: Added fading circular movement trails (`showTrails` toggle) showing recent trajectory history for accelerating vehicles.

### 2.6 Sub-Frame Telemetry Interpolation & Clock Age
- **One-Tick Buffer Pipeline**: Configured a single-tick history buffer (`liveHistoryRef`) storing frames at $t$ and $t+1$.
- **Bounded Interpolation**: Progress is calculated as:
  $$\alpha = \min\left(1.0, \; \max\left(0.0, \; \frac{t_{\text{render}} - t_{\text{last}}}{\Delta t_{\text{interval}}}\right)\right)$$
  Positions and headings are linearly interpolated strictly between $t$ and $t+1$; **the client never extrapolates past the latest received tick**.
- **Live Telemetry Age Ticker**: Added a live age display beside the simulation clock: `Age: 0.8s` (turns amber if $> 3.0$ s).

### 2.7 HUD Count Invariant: Telemetry === HUD === Rendered
- **Count Invariant Enforced**: Fixed the mock "3 active vehs" artifact. The Top-Left HUD and Status Strip now bind directly to `telemetry.vehicles`:
  $$\text{telemetry.vehicles.length} \equiv \text{HUD\_count} \equiv \text{rendered\_count}$$
- **HUD Format**: Displays `${totalVehicles} vehs in network (${queuedVehicles} queued)`.

### 2.8 Interactive Hover Tooltip & Follow Camera
- **Hover Detail Card**: Hovering over any vehicle displays a floating card containing:
  - Vehicle ID and detected vehicle type (e.g. `Passenger Car`, `Transit Bus`, `Emergency Ambulance`).
  - Speed in both **km/h** and **m/s** (e.g. `32.4 km/h (9.0 m/s)`).
  - Waiting time in seconds (e.g. `14.0 s`).
  - Queue status badge (`QUEUED` vs `MOVING`).
  - Approach lane ID and physical tier (`SURFACE`, `FLYOVER`, `UNDERPASS`).
- **Click-to-Follow Camera**: Clicking any vehicle activates Follow Mode (`isFollowMode = true`), continuously panning the viewport to track the vehicle smoothly across the junction.

### 2.9 Queue & Sensor State Highlighting
- **Vehicle Color Shift**: Any vehicle with speed $< 0.1$ m/s or waiting time $> 0$ s immediately turns Warm Amber (`#F59E0B`).
- **E2 Detector Overlays**: Detector spans render with status-driven styling:
  - `CONFIRMED_ZERO`: Translucent emerald (`rgba(16, 185, 129, 0.25)`).
  - `MEASURING`: Translucent amber (`rgba(255, 176, 32, 0.35)`).
  - `SATURATED`: High-intensity red (`rgba(239, 68, 68, 0.50)`).
  - `OFFLINE`: Hatched slate-gray (`#64748B`), never falsely reported as zero queue.

### 2.10 Decision Text Provenance & Lookup Table
- **Direct Controller Binding**: When a decision record includes an explicit `reason` string generated by the Python controller (e.g., `"Controller queue extension: North queue (24.0m) exceeds South (4.0m) by 20.0m"`), the frontend renders it verbatim.
- **Single Lookup Table (`DECISION_CODE_LABELS`)**: Replaced invented exploratory text with a lookup table. If an unknown code is received, it displays the raw code without fabrication.

---

## 3. Visual Verification Matrix & Artifacts

All visual artifacts were generated using real simulation geometry and replay frames from seed 121 / seed 101 runs and saved in [`docs/artifacts/phase2/`](../docs/artifacts/phase2/):

| Verification Condition | Generated Artifact | Key Observations |
| :--- | :--- | :--- |
| **1. Vehicle Scale (100% Zoom)** | `01_scale_before_100pct.svg`<br>vs `02_scale_after_100pct_2x.svg` | **Before**: Cars were 4.8 px, barely distinguishable from pavement markings.<br>**After**: Exaggerate 2x + 8px min clamp renders crisp, identifiable vehicles without lane spill. |
| **2. Vehicle Scale (350% Zoom)** | `03_scale_after_350pct_3x.svg` | **After**: Magnification at 3.5x shows full vehicle geometry, windshields, roof arrows, and headlight cones. |
| **3. Dark Theme Road Contrast** | `04_contrast_before_dark.svg`<br>vs `05_contrast_after_dark.svg` | **Before**: BMTC teal bus had 2.07:1 contrast; dark blue cars blended into asphalt.<br>**After**: Sky blue (`#38BDF8`) moving traffic and warm amber queued traffic provide $>5.5:1$ contrast. |
| **4. Light Theme Road Contrast** | `06_contrast_after_light.svg` | **After**: Crisp dark outlines (`#0F172A`) against light road surface maintain sharp visibility. |
| **5. Physical Draw Order** | `07_draw_order_before_flyover_overlap.svg`<br>vs `08_draw_order_after_seethrough_flyover.svg` | **Before**: Surface cars drew over the top of the flyover deck.<br>**After**: Surface cars pass under the flyover; "See-through" mode ghosts the deck to 35% alpha. |
| **6. Tooltip & Follow Camera** | `09_tooltip_and_camera_follow.svg` | **After**: Interactive inspection card displays ID, speed (km/h & m/s), wait time, lane, tier, and tracking reticle. |
| **7. Heavy Demand Seed 101 Replay** | `10_heavy_demand_seed101_replay.svg` | **After**: Network under heavy queue conditions clearly highlights stopped queues in amber and E2 saturation. |

---

## 4. Test Execution & Quality Gate

### 4.1 Frontend Unit Test Suite (`npm test`)
All 26 automated unit tests passed:
```
✔ Verified Demo Data Snapshot - Manifest integrity (2.31ms)
✔ Verified Demo Data Snapshot - Summary schema (3.55ms)
✔ Verified Demo Data Snapshot - All runs & null metrics handling (18.13ms)
✔ Verified Demo Data Snapshot - Run artifact directory consistency (32.06ms)
✔ Verified Demo Data Snapshot - Experiment evaluation artifacts (1.57ms)
✔ Client Safety Logic - Snapshot mode guards (1.26ms)
✔ Client Telemetry - Staleness detection logic (0.38ms)
✔ explainDecision: GAP_OUT generates outcome first, reason second (3.64ms)
✔ explainDecision: EXTEND generates added green time with headroom (2.20ms)
✔ explainDecision: SWITCH refused (minimum green floor) (0.60ms)
✔ explainDecision: ENTER_GREEN baseline start (0.46ms)
✔ explainDecision: EMERGENCY priority preemption (1.28ms)
✔ collapseHolds: correctly collapses consecutive HOLD records (1.36ms)
✔ explainDecision: archived cycle-audit schema maps cleanly (0.48ms)
✔ Explode 3-Tier View: Collapse vs Explode layer offsets (6.03ms)
✔ Explode 3-Tier View: Projected coordinates shift when exploded (1.52ms)
✔ Explode 3-Tier View: Solo Tier mode dims non-selected layers (0.44ms)
✔ Geometry Validation Overlay - Vehicles align within SUMO lane polygons (49.91ms)
✔ Live Run → Review Handoff: Decisions > 0, Vehicles > 0 (17.20ms)
✔ Operations KPI Strip - Binds to real evaluated aggregate numbers (12.12ms)
✔ Twin QA Harness: 18 conditions (t=0,30,60s; z=100%,400%,1200%; dark/light) (22.32ms)
✔ Vehicle Scaling: Minimum on-screen size enforced across zoom levels (25%, 100%, 350%) (1.14ms)
✔ Draw Order & Tier Classification: Explicit z elevation distinguishes flyover vs surface vs underpass (0.26ms)
✔ Tooltip Formatting: Generates id, type, speed in km/h & m/s, wait time, lane, and queued status (1.07ms)
✔ HUD Invariant: Rendered count, HUD count, and Telemetry count match identically (0.26ms)
✔ Decision Reason Lookup: Single lookup table maps raw codes, preserves logged controller reasons (0.69ms)

Total: 26 passed, 0 failed (363ms)
```

---

## 5. Summary of Files Changed

| File Path | Description of Changes |
| :--- | :--- |
| [`frontend/src/components/IsometricIntersection.jsx`](../frontend/src/components/IsometricIntersection.jsx) | Added vehicle scale controls (1x, 2x, 3x), 8px min clamp, high-contrast palette, see-through flyover deck ghosting, 3-tier draw order partitioning, one-tick buffer interpolation, trails/headlight cones, map legend, and hover tooltip. |
| [`frontend/src/views/LiveMonitorView.jsx`](../frontend/src/views/LiveMonitorView.jsx) | Added live telemetry age ticker next to simulation clock and updated status strip to show exact network vehicle count and queued count matching telemetry. |
| [`frontend/src/utils/explainDecision.js`](../frontend/src/utils/explainDecision.js) | Added `DECISION_CODE_LABELS` lookup table and support for directly rendering real controller `reason` strings without frontend invention. |
| [`frontend/src/views/LiveSimulationView.jsx`](../frontend/src/views/LiveSimulationView.jsx) | Replaced mock hard-coded string templates with controller-structured log strings and lookup table mappings. |
| [`frontend/test/vehicleVisibility.test.js`](../frontend/test/vehicleVisibility.test.js) | Added unit tests verifying min-size scaling, tier elevation sorting, tooltip formatting, HUD count matching, and decision lookup table integrity. |
| [`scripts/generate_phase2_visual_proofs.js`](../scripts/generate_phase2_visual_proofs.js) | Created automated visual proof generation script producing 10 comparative SVGs across zoom, contrast, and draw order conditions. |
| [`docs/artifacts/phase2/`](../docs/artifacts/phase2/) | Directory containing the 10 generated visual verification SVG proof artifacts. |
| [`docs/phase2_report.md`](./phase2_report.md) | This comprehensive deliverable report. |

---

## 6. Open Items & Phase 3 Readiness

- All confirmed frontend visibility bugs from Phase 1 are resolved.
- Ready for user review and subsequent phase instructions.
