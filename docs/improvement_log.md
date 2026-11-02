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


