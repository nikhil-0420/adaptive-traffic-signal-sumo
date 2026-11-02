# DP1 Improvement Log

## Initial Environment Baseline (Phase 0 Setup)

- **Date**: 2026-11-02
- **Git Branch**: `dp1-improve`
- **Git Commit**: `c18a808c3a5b5c391e001793ef2ed368eedfb5f6`
- **SUMO Version**: Eclipse SUMO sumo 1.28.0 (`E:\dp1-traffic-signal\.venv\Scripts\sumo.exe`)
  - Build features: `Windows-10.0.26100 AMD64 MSVC 19.51.36260.0 Release FMI Proj GUI FMT Intl SWIG Parquet Eigen GDAL FFmpeg OSG GL2PS JuPedSim`
- **Python Version**: `3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]` (Virtual environment: `E:\dp1-traffic-signal\.venv`)
- **Node Version**: `v24.16.0`
- **npm Version**: `11.13.0`

### Network Version and Identifier (Marathahalli)
- **Network Name**: `marathahalli`
- **Network Model Version**: `1.0.0`
- **Source Snapshot ID**: `opencity_bbmp_20261014`
- **Signal Plan ID**: `btp_airport_ps_marathahalli_v1`
- **Controlled TLS Node**: `marathahalli_tls`
- **Source Metadata Reference**: [`network/marathahalli/source/source_metadata.json`](../network/marathahalli/source/source_metadata.json)
- **Experiment Manifest Reference**: [`results/research/exp_marathahalli_hybrid_840/manifest.json`](../results/research/exp_marathahalli_hybrid_840/manifest.json)

### Package Freeze (Relevant Packages)
- `eclipse-sumo`: 1.28.0
- `traci`: 1.28.0
- `sumolib`: 1.28.0
- `numpy`: 2.4.6
- `pandas`: 3.0.6
- `scipy`: NOT INSTALLED
- `fastapi`: 0.143.0
- `torch`: 2.14.1
- `stable_baselines3`: 2.9.0
- `gymnasium`: 1.4.0
- `matplotlib`: 3.11.2
- `uvicorn`: 0.54.0
- `pytest`: 9.1.1

## Phase 1: Audit The Current Map and Telemetry
- **Date**: 2026-11-02
- **Tag**: `dp1-phase1`
- **Report**: [`docs/ui_audit.md`](./ui_audit.md), [`docs/phase1_report.md`](./phase1_report.md)
- **Key Findings**: H1 confirmed (vehicles 2.8px at default zoom), H2 confirmed (vehicles drawn behind flyover without see-through), H3 confirmed (HUD vehicle count had mismatch with rendered vehicles), H4 confirmed (explanation text synthesized in UI rather than from controller log).

## Phase 2: Vehicle Visibility Fix in Current Map
- **Date**: 2026-11-02
- **Git Commit**: `d95f82fdbf7f1ecb6dcd11e33986493d03f84ec4`
- **Tag**: `dp1-phase2`
- **Report**: [`docs/phase2_report.md`](./phase2_report.md)
- **Changes**: Vehicle exaggeration control (1x/2x/3x, default 2x), see-through flyover deck ghosting (35% opacity), vehicle trails, high-contrast colours + dark asphalt outlines, HUD invariant check, real controller reason mapping (`DECISION_CODE_LABELS`). 26/26 frontend tests passed, 10 visual proof artifacts generated.

## Phase 3: Export Network Geometry for 3D
- **Date**: 2026-11-02
- **Git Commit Baseline**: `d95f82fdbf7f1ecb6dcd11e33986493d03f84ec4`
- **Tag**: `dp1-phase3`
- **Report**: [`docs/phase3_report.md`](./phase3_report.md)
- **Artifacts**: `scripts/export_network3d.py`, `frontend/public/network3d.json`, `tests/test_export_network3d.py`, `frontend/test/network3dSchema.test.js`
- **Key Metrics**:
  - Lanes: 166 (72 normal, 94 internal)
  - Junctions: 16
  - Controlled Links: 16 (links 0–15 at `marathahalli_tls`)
  - E2 Detectors: 8 (pos -25.0 to -0.1, 24.9m span)
  - Flyover Deck Edges: 4 (+6.5m to +7.0m elevation)
  - Ramps: 4 flyover ramps (+8.89% to -8.98% gradients, strictly z-monotone) + 8 connector ramps
  - Polyline Continuity: Max gap `0.000000 m` across 178 transitions
  - Lane Crossings: 0 same-z crossings on normal edges; 41 grade-separated flyover crossings; 115 junction internal same-z crossings
  - Starting Prompt Check: 16/16 links matched, 0 mismatches
  - File Size: 0.244 MB (< 3.0 MB target, lossless tolerance = 0.0m)
  - Tests: 19/19 pytest passed, 35/35 npm test passed

## 2026-11-02: Phase 4 - 3D Scene for Road Topology
- **Git Commit Baseline**: `600c281` (tagged `dp1-phase3`)
- **Key Packages**: `three@0.160.0`, `@react-three/fiber@8.17.10`, `@react-three/drei@9.121.5`
- **Frontend Changes**:
  - `frontend/src/utils/network3dGeometry.js`: 3D road ribbons, markings, junction surfaces, deck thickness, barriers, pillars, and geometry merger.
  - `frontend/src/components/Network3DScene.jsx`: Three.js / R3F Canvas with 4 camera presets, lighting, explode view, transparency, and area labels.
  - `frontend/src/components/IsometricIntersection.jsx`: Added "3D" view toggle, lazy-loaded via `React.lazy` + `Suspense`, with WebGL availability fallback guard.
  - `frontend/test/network3dScene.test.js`: Added 6 automated tests (transforms, 8-mesh snapshot, pillar collision audit, presets, WebGL lifecycle, availability guard).
  - `frontend/scripts/generate_3d_snapshots.js`: Script rendering vector snapshots for the 4 camera angles in Dark and Light themes into `docs/artifacts/phase4/`.
- **Validation & Metrics**:
  - Static Mesh Count: Exactly 8 merged categories (optimal draw-call performance).
  - Pillar Clearance Audit: 9 grid stations evaluated; 6 portal piers clear surface traffic (>10m); 3 centerline piers (X = -5, 0, +5m) conflict with ORR mainline and surface legs (up to 2.40m intrusion) and are reported in the UI audit modal.
  - Bundle Size: 3D Scene chunk isolated into `dist/assets/Network3DScene-BRcBKEPO.js` (172 kB uncompressed, 55 kB gzipped).
  - Area Labels: Marked "(approximate)".
  - Footer Disclaimer: *"Modelled elevation; synthetic demand. Never present geometry as surveyed."*
  - Tests: 41/41 npm tests passed (100% green), 113/113 pytest tests passed (100% green).

## 2026-11-02: Phase 5 - Vehicles, Signals and Queues in 3D
- **Git Commit Baseline**: `d95fdfc` (tagged `dp1-phase4`)
- **Tag**: `dp1-phase5`
- **Report**: [`docs/phase5_report.md`](./phase5_report.md)
- **Artifacts**:
  - `dp1/runner.py`, `dp1/replay.py`: read-only `traci.vehicle.getPosition3D()` telemetry extraction.
  - `backend/schemas.py`: `VehicleTelemetryItem` with `z: float = 0.0`.
  - `tests/test_phase5_telemetry_regression.py`: mandatory determinism regression test.
  - `frontend/src/utils/vehicle3dMesh.js`: InstancedMesh management for 5 vehicle classes, high-contrast colors, single-tick buffer interpolation without extrapolation.
  - `frontend/src/utils/signalAndQueue3d.js`: stop line configurations, SUMO 16-char `tl_state` decoder, signal timer logic (countdown vs elapsed), queue volume bar geometry, and non-zero OFFLINE safety enforcement.
  - `frontend/src/components/Network3DScene.jsx`: integrated 3D vehicles, signal heads with active bulbs, queue volume bars, floating metrics badges, and 3D decision callouts.
  - `frontend/test/vehiclesSignalsQueues3d.test.js`: 7 automated tests verifying instance counts, signal colors, timer logic, OFFLINE non-zero guard, labelling, and interpolation.
  - `docs/artifacts/phase5/`: vector verification snapshots at $t=1$s (Live), $t=30$s (Replay), and $t=60$s (Snapshot).
- **Validation & Metrics**:
  - Determinism Proof: Baseline vs post-change `decisions.csv` (SHA256: `4E6410651B7468C992A59BE4FED946C96C45D20F657B3F77B504FD6EBE354B67`) and `timeseries.csv` (SHA256: `895BAD0226BF6BFD00A84EBFCD19982FB3C3C73BEA6218F4773ECD829B73F95F`) are 100% byte-identical.
  - Metrics Isolation: Elevation `z` is excluded from all metrics files; zero changes to controller, queue, or metrics code.
  - Multi-tier Elevation: Flyover vehicles sit on the bridge deck at $z \approx 6.83$\,m; surface vehicles sit at $z = 0.00$\,m.
  - Non-Zero OFFLINE Sensor Safety: OFFLINE status is strictly guarded against rendering as 0m; displays a full-detector-span ($24.9$\,m) hatched block with `OFFLINE (FALLBACK)` warning badge.
  - Decision Increments: Requested (`Req: +<delta_g_req_s>s`) and applied (`App: +<delta_g_app_s>s`) increments displayed in separate sub-badges.
  - Tests: 48/48 frontend unit tests passed (100% green).

## 2026-11-02: Phase 6 - Camera Controls, Labels, Performance, and QA Polish
- **Git Commit Baseline**: `c817e7e` (tagged `dp1-phase5`)
- **Tag**: `dp1-phase6`
- **Changes**:
  - Camera presets (Top-Down, Iso, Junction Close-up, Flyover Side View, Approach Views N/S/E/W).
  - Orbit controls boundary clamping, follow-vehicle click interaction, zoom percentage sync.
  - UI labels: replaced synthetic text with "Live simulation view" and live TraCI connection status pill.
  - Colorblind palettes (Default, Deuteranopia, Tritanopia, Monochromatic) persisted in localStorage.
  - WebGL context recovery and graceful 2.5D fallback handling.
- **Validation**: 48/48 frontend tests passed, 115/115 pytest tests passed.

## 2026-11-02: Phase 7 - Research Baseline Tag and Diagnostics
- **Git Commit Baseline**: `097f8ec` (tagged `dp1-pre-improvement`)
- **Tag**: `dp1-phase7`
- **Reports**: [`docs/diagnostics_report.md`](./diagnostics_report.md), [`docs/phase7_report.md`](./phase7_report.md)
- **Artifacts**:
  - `results/research/exp_diag_dev_101_110/`: 240 evaluation runs (10 dev seeds 101–110, 4 patterns, 3 levels, 2 policies).
  - `scripts/diagnostics/`: 9 diagnostic scripts (`d1_d2_saturation.py` to `d10_gap_out.py`).
  - `results/research/d7_ground_truth_summary.csv`: ground-truth queue correlations ($r = 0.939 - 0.981$).
- **Key Findings & Evidence**:
  - D1/D2: Saturation rate is negligible (<0.026% in low/medium, <0.32% in heavy).
  - D3: Hybrid switches 191.4 times/hr in balanced-low (mean green 14.45s) vs Webster's 181.2 (15.00s).
  - D4: 51.6% of extensions in `imbalanced_orr_heavy` approved without opposing queue pressure.
  - D5: Zero unfinished vehicles across all 240 runs (100% completion rate); wait metrics are unbiased.
  - D6: Webster is confirmed to be an oracle baseline with exact prior knowledge of scenario arrival rates.
  - D7: Detectors correlate strongly with ground truth ($r \ge 0.939$, MAE $\le 0.52$m).
  - D8: Physical edge headroom is only 6.6m–9.2m before hitting upstream merge junctions.
  - D9: Hybrid consistently beats Webster in `surge_orr_north` (up to -6.86s p95 wait) and `balanced_heavy` (-31.21s p95 wait).
  - D10: Gap-out is already active in the controller (36.54% of decisions).
- **Decision Table Outcome**:
  - R2 (Comparative Extension), R3 (Queue-Aware Demand Fairness), and R4 (De-Oracle Base Green): **JUSTIFIED** $\rightarrow$ Proceed to Phase 8.
  - R1 (Gap-Out + HOLD Default) and R5 (Longer Detectors): **NOT JUSTIFIED** $\rightarrow$ Rejected.
- **Quality Gates**: 115/115 pytest green, 48/48 npm test green. Zero controller code modified.

## 2026-11-02: Phase 7B - Diagnostic Gaps and Deep Reconciliations
- **Tag**: `dp1-phase7b`
- **Script**: `scripts/diagnostics/phase7b_gaps.py`
- **Key Findings**:
  - Item 1: Base green inputs confirmed to be an oracle (`site_webster_plan` accesses `SITE_DEMAND_PATTERNS` directly by scenario name/demand level). Live controller lacks this info.
  - Item 2: Approved extensions: 8.46% occur when competing score > active score; mean competing wait at next switch is 34.91s (39.91s including clearance). Fairness switches: 0.00% have competing queue < 5m (guarded by code), but 47.78% of wait-limit switches occur with < 10m queue.
  - Item 3: D1 vs D7 reconciled: detector `det_q` values clip at 24.00m due to lead-vehicle stopline setback (~0.9m). Using 24.0m threshold shows detector is packed 13.85% (ORR South) and 13.92% (Surge North), matching ground-truth exceedance (17.6% and 9.8%).
  - Item 4: `max_queue_m` uses detector queue. Evaluation-only ground-truth logging proposed with byte-identical regression test.
  - Item 5: In balanced-low, hybrid mean green is 13.89s (min 13.0s) vs pure adaptive 11.84s (min 9.0s, 23.56% <= 10s).
  - Item 6: R4 updated to "De-oracle the base green" (JUSTIFIED).
