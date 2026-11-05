# Phase 3 Report: Export Network Geometry for 3D

## 1. Environment & Provenance
- **Date**: 2026-11-02
- **Git Commit Baseline**: `d95f82fdbf7f1ecb6dcd11e33986493d03f84ec4`
- **SUMO Version**: `Eclipse SUMO sumo 1.28.0`
- **Python Version**: `3.11.9`
- **Key Python Packages**: `sumolib 1.28.0`, `traci 1.28.0`, `numpy 2.2.3`, `scipy 1.15.2`, `pandas 2.2.3`, `fastapi 0.115.11`
- **Node Version**: `v20.18.0` | **npm Version**: `10.8.2`
- **Source Network File**: `network/marathahalli/dist/marathahalli.net.xml` (`MARATHAHALLI_NET_FILE` in `dp1.site_network`)
- **Source Detector File**: `network/marathahalli/build/detectors.add.xml`
- **Source Signal Logic File**: `network/marathahalli/build/marathahalli.tll.xml`
- **Output 3D File**: `frontend/public/network3d.json`
- **Elevation Source**: `"modelled_config"`
- **Elevation Disclaimer**: *Elevation is a modelling assumption inferred from BTP / BBMP grade separation documentation (+6.5m to +7.0m deck, 0.0m surface), never survey data.*

---

## 2. Summary of Work Done
1. **Network Path Confirmation**:
   - Confirmed canonical source network file paths in `dp1/site_network.py` and `network/marathahalli/dist/marathahalli.net.xml`.
2. **Backend Export Script (`scripts/export_network3d.py`)**:
   - Developed a standalone CLI and library export script utilizing `sumolib`.
   - Extracted 166 lanes (72 normal edge lanes + 94 junction internal lanes) with 3D polyline coordinates `(x, y, z)`, lane widths, speed limits, allowed vehicle classes, and lengths.
   - Extracted 16 junctions with 3D polygon shapes and elevation coordinates.
   - Extracted all 16 controlled signal connections at `marathahalli_tls` (links 0 to 15), linking each connection to its approach label (N/S/E/W), phase group (NS/EW), and individual phase signal states.
   - Extracted all 8 E2 lane-area detectors (2 per approach leg) with positions (`pos=-25.0`, `endPos=-0.1`), approach labels, and 3D detector segment polylines along lane curves.
   - Classified grade-separated elements: 4 elevated bridge deck edges (+6.5m to +7.0m), 12 ramp edges with calculated gradients, 2 mainline underpass bypass edges, and 4 channelized slip roads.
   - Defined network bounding box, origin center (`[350.0, 350.0, 3.5]`), and coordinate transformation matrices (1 unit = 1 metre, 4x4 Three.js Y-up transformation matrix and Scene Z-up matrix).
   - Attached comprehensive provenance block with git commit, SUMO version, file sources, and mandatory `elevation_source: "modelled_config"`.
3. **Geometric & Safety Validations**:
   - **Polyline Continuity**: Tested all 178 edge-to-internal-to-edge transitions across the network; confirmed 0 gaps > 0.005 m (max gap across network is exactly `0.000000 m`).
   - **Ramp Z-Monotonicity**: Checked all 8 lanes across 4 flyover ramp edges; confirmed 100% strict monotonicity (ascending eastbound/westbound ramps and descending eastbound/westbound ramps).
   - **Lane Crossings**: Formally computed 2D line-segment intersections between all pairs of lanes. Normal edge lanes have **0** same-z crossings and **41** grade-separated (diff-z) crossings. Internal lanes have **115** same-z crossings (controlled intersection turning paths).
   - **Starting Prompt Cross-Check**: Verified all 16 link indices against the specification in the Starting Prompt (`docs/AGENT_CONTEXT.md`):
     - Links 0–3: North (`leg_orr_n_in`), NS phase group -> **MATCH**
     - Links 4–7: East (`leg_wf_in`), EW phase group -> **MATCH**
     - Links 8–11: South (`leg_orr_s_in`), NS phase group -> **MATCH**
     - Links 12–15: West (`leg_hal_in`), EW phase group -> **MATCH**
     - Phase 0 (EW green: `rrrrGGGgrrrrGGGg`, 105s) -> **MATCH**
     - Phase 3 (NS green: `GGGgrrrrGGGgrrrr`, 95s) -> **MATCH**
     - **Mismatches found: 0**
4. **Target Size & Schema Validation**:
   - Generated `frontend/public/network3d.json` with a file size of **0.244 MB (255,958 bytes)**, comfortably below the 3.0 MB target (saving > 91% headroom without needing lossy polyline simplification; tolerance 0.0m lossless).
5. **Automated Test Suites**:
   - Created `tests/test_export_network3d.py` with 10 test functions covering provenance, schema, bounds, connections, detectors, flyover classification, and continuity.
   - Created `frontend/test/network3dSchema.test.js` adding 9 tests to the frontend test runner.

---

## 3. Files Created & Modified

| File | Status | Description |
|---|---|---|
| `scripts/export_network3d.py` | Created | Standalone Python export script using `sumolib` with validation and CLI |
| `frontend/public/network3d.json` | Created | 3D geometry JSON payload (0.244 MB) |
| `tests/test_export_network3d.py` | Created | Pytest test suite for 3D network export validation |
| `frontend/test/network3dSchema.test.js` | Created | Node.js test suite for `network3d.json` schema validation |
| `docs/phase3_report.md` | Created | Phase 3 deliverable report |

---

## 4. Exact Commands Run

```powershell
# 1. Run export script
.venv\Scripts\python.exe scripts/export_network3d.py

# 2. Run backend pytest validation
.venv\Scripts\python.exe -m pytest tests/test_export_network3d.py -v

# 3. Run full targeted pytest gate
.venv\Scripts\python.exe -m pytest tests/test_export_network3d.py tests/test_action_seam.py -v

# 4. Run frontend test runner
npm test --prefix frontend
```

---

## 5. Raw Validation Results & Metrics

### 5.1 Export Component Counts
*Source: `frontend/public/network3d.json`*

| Component | Normal Edges | Internal Lanes / Nodes | Total Exported |
|---|---|---|---|
| Lanes | 72 | 94 | 166 |
| Junctions | 16 | 0 | 16 |
| Controlled Connections (`marathahalli_tls`) | 16 | 0 | 16 (links 0–15) |
| E2 Detectors | 8 | 0 | 8 |
| Elevated Flyover Deck Edges | 4 | 0 | 4 |
| Flyover Ramp Edges | 4 | 0 | 4 |
| Surface Connector Ramp Edges | 8 | 0 | 8 |
| Underpass Mainline Bypass Edges | 2 | 0 | 2 |
| Channelized Slip Road Edges | 4 | 0 | 4 |

### 5.2 Geometric Validation Metrics
*Source: `network3d.json["validation"]`*

| Invariant | Value | Target | Status |
|---|---|---|---|
| Polyline Continuity Max Gap | `0.000000 m` | < 0.005 m | **PASS** |
| Polyline Transitions Tested | 178 | All connections | **PASS** |
| Ramp Z-Monotonicity | 100% (8/8 lanes) | Monotone | **PASS** |
| Normal Edges Same-Z Crossings | 0 | 0 | **PASS** |
| Normal Edges Diff-Z (Grade-Separated) | 41 | Expected | **PASS** |
| Junction Internal Same-Z Crossings | 115 | Controlled turns | **PASS** |
| Starting Prompt Mismatches | 0 | 0 | **PASS** |
| JSON File Size | 0.244 MB (255,958 B) | < 3.0 MB | **PASS** |
| Polyline Simplification Tolerance | 0.0 m (lossless) | Optimal | **PASS** |

### 5.3 Controlled Signal Links & Approach Mapping vs Starting Prompt
*Source: `network/marathahalli/build/marathahalli.con.xml` & `network3d.json["connections"]`*

| Link Index | From Edge | To Edge | Turn Dir | Approach Label | Phase Group | Phase 0 State (EW Green, 105s) | Phase 3 State (NS Green, 95s) | Starting Prompt Match |
|---|---|---|---|---|---|---|---|---|
| 0 | `leg_orr_n_in_0` | `leg_hal_out_0` | Right | **North (N)** | **NS** | `r` | `G` | **MATCH** |
| 1 | `leg_orr_n_in_0` | `leg_orr_s_out_0` | Straight | **North (N)** | **NS** | `r` | `G` | **MATCH** |
| 2 | `leg_orr_n_in_1` | `leg_orr_s_out_1` | Straight | **North (N)** | **NS** | `r` | `G` | **MATCH** |
| 3 | `leg_orr_n_in_1` | `leg_wf_out_1` | Left | **North (N)** | **NS** | `r` | `g` | **MATCH** |
| 4 | `leg_wf_in_0` | `leg_orr_n_out_0` | Right | **East (E)** | **EW** | `G` | `r` | **MATCH** |
| 5 | `leg_wf_in_0` | `leg_hal_out_0` | Straight | **East (E)** | **EW** | `G` | `r` | **MATCH** |
| 6 | `leg_wf_in_1` | `leg_hal_out_1` | Straight | **East (E)** | **EW** | `G` | `r` | **MATCH** |
| 7 | `leg_wf_in_1` | `leg_orr_s_out_1` | Left | **East (E)** | **EW** | `g` | `r` | **MATCH** |
| 8 | `leg_orr_s_in_0` | `leg_wf_out_0` | Right | **South (S)** | **NS** | `r` | `G` | **MATCH** |
| 9 | `leg_orr_s_in_0` | `leg_orr_n_out_0` | Straight | **South (S)** | **NS** | `r` | `G` | **MATCH** |
| 10 | `leg_orr_s_in_1` | `leg_orr_n_out_1` | Straight | **South (S)** | **NS** | `r` | `G` | **MATCH** |
| 11 | `leg_orr_s_in_1` | `leg_hal_out_1` | Left | **South (S)** | **NS** | `r` | `g` | **MATCH** |
| 12 | `leg_hal_in_0` | `leg_orr_s_out_0` | Right | **West (W)** | **EW** | `G` | `r` | **MATCH** |
| 13 | `leg_hal_in_0` | `leg_wf_out_0` | Straight | **West (W)** | **EW** | `G` | `r` | **MATCH** |
| 14 | `leg_hal_in_1` | `leg_wf_out_1` | Straight | **West (W)** | **EW** | `G` | `r` | **MATCH** |
| 15 | `leg_hal_in_1` | `leg_orr_n_out_1` | Left | **West (W)** | **EW** | `g` | `r` | **MATCH** |

### 5.4 Flyover Deck & Ramp Elevation Profile
*Source: `network3d.json["flyover_bypass"]`*

| Edge ID | Category | Start Node (Z) | End Node (Z) | Deck Height / Z Range | Length (m) | Calculated Gradient | Direction |
|---|---|---|---|---|---|---|---|
| `flyover_eb_1` | `flyover_ramp` | `node_hal_split` (0.0m) | `node_bridge_w` (6.5m) | 0.0m → 6.5m | 73.1m | +8.89% (+0.0889 m/m) | Ascending (Eastbound) |
| `flyover_eb_2` | `flyover_deck` | `node_bridge_w` (6.5m) | `node_bridge_mid` (7.0m) | 6.5m → 7.0m (mean 6.75m) | 75.0m | +0.67% | Bridge Deck (Eastbound) |
| `flyover_eb_3` | `flyover_deck` | `node_bridge_mid` (7.0m) | `node_bridge_e` (6.5m) | 7.0m → 6.5m (mean 6.75m) | 75.0m | -0.67% | Bridge Deck (Eastbound) |
| `flyover_eb_4` | `flyover_ramp` | `node_bridge_e` (6.5m) | `node_wf_split` (0.0m) | 6.5m → 0.0m | 82.7m | -7.86% (-0.0786 m/m) | Descending (Eastbound) |
| `flyover_wb_1` | `flyover_ramp` | `node_wf_split` (0.0m) | `node_bridge_e` (6.5m) | 0.0m → 6.5m | 81.8m | +7.95% (+0.0795 m/m) | Ascending (Westbound) |
| `flyover_wb_2` | `flyover_deck` | `node_bridge_e` (6.5m) | `node_bridge_mid` (7.0m) | 6.5m → 7.0m (mean 6.75m) | 75.0m | +0.67% | Bridge Deck (Westbound) |
| `flyover_wb_3` | `flyover_deck` | `node_bridge_mid` (7.0m) | `node_bridge_w` (6.5m) | 7.0m → 6.5m (mean 6.75m) | 75.0m | -0.67% | Bridge Deck (Westbound) |
| `flyover_wb_4` | `flyover_ramp` | `node_bridge_w` (6.5m) | `node_hal_split` (0.0m) | 6.5m → 0.0m | 72.3m | -8.98% (-0.0898 m/m) | Descending (Westbound) |

### 5.5 E2 Detectors Summary
*Source: `network3d.json["detectors"]`*

| Detector ID | Approach | Target Lane | Position (pos / endPos) | Span Length | 3D Span Polyline (Start → Stop-Line) |
|---|---|---|---|---|---|
| `det_hal_0` | West (W) | `leg_hal_in_0` | `-25.0` / `-0.1` | 24.9 m | `[314.60, 327.20, 0.0]` → `[339.50, 327.20, 0.0]` |
| `det_hal_1` | West (W) | `leg_hal_in_1` | `-25.0` / `-0.1` | 24.9 m | `[314.60, 330.40, 0.0]` → `[339.50, 330.40, 0.0]` |
| `det_wf_0` | East (E) | `leg_wf_in_0` | `-25.0` / `-0.1` | 24.9 m | `[385.40, 336.80, 0.0]` → `[360.50, 336.80, 0.0]` |
| `det_wf_1` | East (E) | `leg_wf_in_1` | `-25.0` / `-0.1` | 24.9 m | `[385.40, 333.60, 0.0]` → `[360.50, 333.60, 0.0]` |
| `det_orr_s_0` | South (S) | `leg_orr_s_in_0` | `-25.0` / `-0.1` | 24.9 m | `[354.80, 296.50, 0.0]` → `[354.80, 321.40, 0.0]` |
| `det_orr_s_1` | South (S) | `leg_orr_s_in_1` | `-25.0` / `-0.1` | 24.9 m | `[351.60, 296.50, 0.0]` → `[351.60, 321.40, 0.0]` |
| `det_orr_n_0` | North (N) | `leg_orr_n_in_0` | `-25.0` / `-0.1` | 24.9 m | `[345.20, 367.50, 0.0]` → `[345.20, 342.60, 0.0]` |
| `det_orr_n_1` | North (N) | `leg_orr_n_in_1` | `-25.0` / `-0.1` | 24.9 m | `[348.40, 367.50, 0.0]` → `[348.40, 342.60, 0.0]` |

---

## 6. Problems, Surprises, and Verifications

1. **Multi-Part Internal Lane Connections**:
   - In SUMO, left turns across junctions with internal waiting areas split into two consecutive internal lanes (e.g. `:marathahalli_tls_3_0` connects to `:marathahalli_tls_16_0`, which then connects to `leg_wf_out_1`).
   - A naive query of `conn.getViaLaneID()` only yields the first internal segment, giving a false appearance of a gap between the first internal lane end and the target lane start.
   - We implemented full internal-lane graph traversal (`get_full_internal_chain()`). When evaluated along the full chain, the maximum gap between any lane and its connected successor is **`0.000000 m`** across all 178 transitions.
2. **Same-Z Lane Crossings**:
   - Analysis confirms that normal edge lanes have **0** same-z intersections.
   - The 41 crossings on normal edge lanes are all grade-separated (`diff_z >= 3.25 m`), confirming the flyover structure flies cleanly over the ORR mainline and surface legs.
   - The 115 same-z crossings are strictly located within junction boundaries where turning vehicle streams cross each other at grade. This matches physical traffic reality and is safely resolved by signal phases.
3. **Starting Prompt Compliance**:
   - Zero discrepancies were found between the network definitions and the Starting Prompt. Link indices 0–15, approach mappings, and phase strings match with 100% fidelity.
4. **JSON Payload Size**:
   - At 0.244 MB, the full network geometry is well below the 3.0 MB target (< 8.2% of allowance). Lossless precision (`tolerance = 0.0 m`) was preserved.

---

## 7. Decision Needed Items
- None. Everything matches the authoritative specification and pre-registered protocol.

---

## 8. Integrity & Protocol Checklist

- [x] Seed rules respected (no simulation runs performed; seeds 131–150 untouched).
- [x] Backend export script only (simulation code, controllers, queue measurement completely untouched).
- [x] No experiment results or runs overwritten.
- [x] Full test suites passing (19/19 pytest, 35/35 npm test).
- [x] Provenance block clearly identifies `elevation_source: "modelled_config"` and disclaims survey data.
- [x] JSON size under 3 MB target verified (0.244 MB).
