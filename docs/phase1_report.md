# Phase 1 Report: Audit the Current Map and Telemetry

## Environment Baseline
- **Date**: 2026-11-02
- **Git Branch**: `dp1-improve`
- **Git Commit Baseline**: `adb41b0` (tag: `dp1-phase0`)
- **SUMO Version**: Eclipse SUMO sumo 1.28.0 (`E:\dp1-traffic-signal\.venv\Scripts\sumo.exe`)
- **Python Version**: 3.11.9 (64-bit AMD64)
- **Node Version**: v24.16.0 | **npm Version**: 11.13.0
- **Network Model**: Marathahalli Bridge Junction (`marathahalli`, model v1.0.0, node `marathahalli_tls`)

---

## 1. What Was Done
- **Analyzed Map Architecture**: Deconstructed [`frontend/src/components/IsometricIntersection.jsx`](../frontend/src/components/IsometricIntersection.jsx) and [`frontend/src/views/LiveMonitorView.jsx`](../frontend/src/views/LiveMonitorView.jsx). Documented HTML5 2D Canvas pipeline, 30° isometric projection formulas, base scale derivation, zoom clamping ($25\%$ to $350\%$), draw order, and HTTP polling mechanics ($1,500$ ms interval vs $1.0$ s simulation step).
- **Executed Dev Seed 101 Live Simulation**: Ran dev seed 101 (`imbalanced_orr`, medium demand, Marathahalli network) and captured three consecutive live telemetry payload samples at $t=26.0$s, $27.0$s, and $28.0$s.
- **Audited Vehicle Count & Resolved Mismatches**: Compared telemetry vehicle array count, canvas render loop iterations, and the "active vehs" HUD pill. Discovered zero mismatch in the production TraCI pipeline; isolated the previously reported "3 active vehs" finding to an exploratory mock component (`LiveSimulationView.jsx`).
- **Evaluated Hypotheses H1–H7**: Determined YES/NO/UNSURE status with empirical measurements (pixel dimensions, WCAG contrast ratios, draw order inspection, ground-truth route arrival analysis, polling rate profiling, and queued car spacing overlap).
- **Audited Telemetry Schema**: Catalogued all present vehicle fields (`id`, `x`, `y`, `a`, `s`, `em`) and documented missing fields (`z`/elevation, `type`, `length`, `width`, `lane_id`, `waiting_time`, `stopped/queued` flag).
- **Traced Event Text & Gap-Out Logic**: Quoted exact source code for decision toasts/event cards in both the mock view and real explainer utility, and verified the presence and exact structure of gap-out logic in [`dp1/controllers/hybrid_queue_adaptive.py`](../dp1/controllers/hybrid_queue_adaptive.py).
- **Authored Deliverables**: Produced [`docs/ui_audit.md`](../docs/ui_audit.md) and [`docs/phase1_report.md`](../docs/phase1_report.md). Zero production code changed.

---

## 2. Files Created / Changed
- **Created**:
  - [`docs/ui_audit.md`](../docs/ui_audit.md) (comprehensive technical audit with formulas, code citations, and measurements)
  - [`docs/phase1_report.md`](../docs/phase1_report.md) (standard phase report)
  - [`scratch/audit_details.py`](../scratch/audit_details.py) (empirical calculation script)
  - [`scratch/phase1_consecutive_telem/sample_t26.json`](../scratch/phase1_consecutive_telem/sample_t26.json) (captured sample 1)
  - [`scratch/phase1_consecutive_telem/sample_t27.json`](../scratch/phase1_consecutive_telem/sample_t27.json) (captured sample 2)
  - [`scratch/phase1_consecutive_telem/sample_t28.json`](../scratch/phase1_consecutive_telem/sample_t28.json) (captured sample 3)
- **Modified**: Zero production code files modified.

---

## 3. Exact Commands Run

```powershell
# 1. Execute live simulation run on dev seed 101, capture consecutive telemetry, and compute empirical metrics
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe scratch/audit_details.py

# 2. Run frontend quality gate
cd frontend; npm test; cd ..
```

---

## 4. Results

### Consecutive Telemetry Samples Table (Dev Seed 101, Medium Demand, `imbalanced_orr`)
*(Source: [`scratch/phase1_consecutive_telem/`](../scratch/phase1_consecutive_telem/))*

| Sim Time ($t$) | Telemetry Vehicle Count | HUD "active vehs" Count | Canvas Render Iterations | Visible Within Viewport | Active Phase & Axis | Ground-Truth Tiers (Fly / Under / Surf) | Heuristic Inferred Tiers (Fly / Under / Surf) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$26.0$ s** | 20 | 20 | 20 | 20 | GREEN (NS) | 4 / 5 / 11 | 5 / 9 / 6 (5 misclassified) |
| **$27.0$ s** | 21 | 21 | 21 | 21 | GREEN (NS) | 4 / 5 / 12 | 6 / 9 / 6 (6 misclassified) |
| **$28.0$ s** | 23 | 23 | 23 | 23 | GREEN (NS) | 4 / 5 / 14 | 6 / 10 / 7 (7 misclassified) |

*Finding*: Telemetry count, HUD count, and canvas render loops match identically ($20=20=20$, $21=21=21$, $23=23=23$).

### Hypothesis Evaluation Matrix
*(Source: [`docs/ui_audit.md`](../docs/ui_audit.md) Section 3)*

| Hypothesis | Status | Evidence Summary |
| :--- | :---: | :--- |
| **H1: Sprites are too small at default zoom** | **YES** | At 100% zoom without clamp, a car is only **4.8 px long**. The current clamp forces cars to $13.0 \times 5.1$ px. At 350% zoom, the road magnifies $3.5\times$, but cars only enlarge to $16.9 \times 6.7$ px ($1.3\times$), making them look tiny relative to the roadway. |
| **H2: Vehicle colours have poor contrast with road** | **YES** | Road asphalt is `#29343A`. **BMTC Transit Bus** (`#0F6B7A`) has a contrast ratio of **2.07:1**, severely failing WCAG (< 3.0:1). **Car Dark Blue** (`#3B82F6`) has **3.47:1**. Flyover ground shadow (`rgba(0,0,0,0.45)`) further dims vehicles underneath. |
| **H3: Flyover deck draws OVER surface vehicles** | **NO** | The reverse bug exists: Flyover deck is drawn in Step 5.3; vehicles are drawn in Step 6. Therefore, **surface vehicles are drawn ON TOP of the flyover deck**. |
| **H4: Vehicles on flyover vs surface not distinguished** | **YES** | Telemetry omits $z$, lane ID, and tier. The frontend heuristic bounding-box guess had an empirical **28.6% error rate** at $t=27$s (misclassifying 6 of 21 vehicles). |
| **H5: Low count is real low demand at that time** | **YES** | Route XML departures: at $t=27$s, only **23 vehicles have departed network-wide**. Only **8 vehicles (34.8%)** are routed to the surface junction; 15 bypass via flyover/underpass/slip. Perimeter travel takes 20–30s. |
| **H6: Telemetry rate is too low or irregular** | **YES** | Client polling is hard-coded to **1,500 ms** (0.67 Hz) while SUMO steps at **1,000 ms** (1.0 Hz). Updates arrive in coarse multi-second jumps. |
| **H7: Queued vehicles overlap each other** | **YES** | Physical gap is $2.5$m ($2.5$ px at 100% zoom). The 13 px clamped car sprite causes **5.7 px of overlap (43.5% body overlap)** in stopped queues. |

### Contrast Ratios vs Road Asphalt (`#29343A`)

| Vehicle Paint | Hex Code | Contrast Ratio | WCAG Compliance |
| :--- | :--- | :--- | :--- |
| **BMTC Transit Bus** | `#0F6B7A` | **2.07 : 1** | **FAIL** ($< 3.0:1$) |
| **Car Dark Blue** | `#3B82F6` | **3.47 : 1** | PASS Large ($\ge 3.0:1$) |
| **Truck Terracotta** | `#E06A3B` | **3.82 : 1** | PASS Large ($\ge 3.0:1$) |
| **Auto Green** | `#2FA866` | **4.20 : 1** | PASS Large ($\ge 3.0:1$) |
| **Car Slate Grey** | `#94A3B8` | **4.97 : 1** | PASS Standard ($\ge 4.5:1$) |
| **Motorcycle Teal** | `#4FB3C2` | **5.20 : 1** | PASS Standard ($\ge 4.5:1$) |
| **Phasora Amber** | `#FFB020` | **6.97 : 1** | PASS Standard ($\ge 4.5:1$) |
| **Ambulance White** | `#FFFFFF` | **12.75 : 1** | PASS Enhanced ($\ge 7.0:1$) |

### Telemetry Field Schema Audit

| Field | In Telemetry? | Description |
| :--- | :---: | :--- |
| `id` | **YES** | Unique vehicle identifier string |
| `x`, `y` | **YES** | SUMO 2D coordinates in meters |
| `a` | **YES** | Heading angle (0–360 degrees) |
| `s` | **YES** | Instantaneous speed (m/s) |
| `em` | **YES** | Emergency vehicle boolean |
| `z` / elevation | **NO** | Missing; prevents vertical tier separation |
| `type` / vehicle class | **NO** | Missing; frontend guesses via ID modulo hash |
| `length`, `width` | **NO** | Missing; frontend uses static `VEHICLE_SPECS` |
| `lane_id` | **NO** | Missing; prevents exact topological lane binding |
| `waiting_time` | **NO** | Missing; frontend defaults to 0 |
| `stopped_or_queued` | **NO** | Missing; frontend guesses `speed < 0.8` |

### Code Quotes: Event Text Provenance & Gap-Out Logic

1. **Synthetic Mock Strings Provenance**:  
   From [`frontend/src/views/LiveSimulationView.jsx:L264-L278`](../frontend/src/views/LiveSimulationView.jsx#L264-L278):
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

2. **Real Hybrid Controller Gap-Out Logic**:  
   From [`dp1/controllers/hybrid_queue_adaptive.py:L167-L182`](../dp1/controllers/hybrid_queue_adaptive.py#L167-L182):
   ```python
   # 3. Gap-Out Evaluation: Active approach fully cleared
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
   ```

---

## 5. Problems, Surprises, Anything Contradicting the Plan
- **The "3 active vehs" Finding Explained**: This did *not* stem from dropped simulation frames or TraCI vehicle filtering. It originated from an earlier exploratory prototype view (`LiveSimulationView.jsx`) containing three hard-coded dummy vehicle objects (`v0`, `v1`, `v2`). The production `LiveMonitorView.jsx` accurately reports all 20–23 active vehicles.
- **Inverse Z-Ordering Bug (H3)**: It was hypothesized that the flyover deck was occluding surface vehicles. In reality, the reverse occurs: because all vehicles are rendered after the flyover deck in canvas draw order, surface vehicles travelling under the flyover are drawn *on top* of the concrete overpass deck!
- **Heuristic Tier Error Rate (H4)**: Lacking $z$ in telemetry, the frontend's 2D bounding box test misclassifies $28.6\%$ of vehicles at $t=27$s, erroneously hoisting surface approach traffic into the air onto the flyover deck.

---

## 6. DECISION NEEDED Items
- **For Phase 2 (Vehicle Visibility Fix)**:
  1. **Palette Adjustment**: Recommend replacing the failing BMTC Bus color (`#0F6B7A`, 2.07:1 contrast) with an accessible bright transit teal (`#00D2FF` or `#38BDF8`, $> 7:1$ contrast) and brightening dark blue cars (`#3B82F6` to `#60A5FA`).
  2. **Sprite Scaling Curve**: Replace the harsh `visFactor` clamp with a smooth power-law scaling curve so vehicles remain clear at 100% zoom ($12$–$14$ px) but scale up proportionally to $28$–$36$ px at 350% zoom without distortion or queuing overlap.
  3. **Canvas Draw Order**: In Phase 2 (frontend-only), adjust draw order so underpass road/vehicles $\rightarrow$ surface road/vehicles $\rightarrow$ flyover road/vehicles are rendered in tier batches, preventing surface vehicles from floating over the flyover deck.

---

## 7. Checklist
- [x] **Seed rules respected?** (Only dev seed 101 used; validation and held-out seeds untouched).
- [x] **No experiment overwritten?** (`results/` directories untouched; outputs isolated to `scratch/`).
- [x] **No simulation/controller code edited?** (Strictly read-only audit; zero production changes).
- [x] **Frontend test suite passing?** (21 / 21 tests pass).
