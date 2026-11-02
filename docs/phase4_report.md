# Phase 4 Report: 3D Scene for Road Topology

## 1. Environment & Provenance
- **Date**: 2026-11-02
- **Git Commit Baseline**: `600c281` (tagged `dp1-phase3`)
- **Branch**: `dp1-improve`
- **React Version**: `18.3.1`
- **Three.js Stack**: `three@0.160.0`, `@react-three/fiber@8.17.10`, `@react-three/drei@9.121.5`
- **Vite Version**: `5.4.21`
- **SUMO Version**: `Eclipse SUMO sumo 1.28.0`
- **Python Version**: `3.11.9`
- **Node Version**: `v24.16.0` | **npm Version**: `11.1.0`
- **Source Geometry File**: `frontend/public/network3d.json`
- **Elevation Source**: `"modelled_config"`
- **Elevation Disclaimer**: *"Modelled elevation; synthetic demand. Never present geometry as surveyed."*

---

## 2. Summary of Work Done

### 2.1 3D Stack & Lazy-Loading Architecture
- Integrated `three`, `@react-three/fiber`, and `@react-three/drei` configured for React 18.
- Code-split the 3D scene using `React.lazy(() => import('./Network3DScene'))` and React `Suspense`.
- **Bundle Chunk Isolation**:
  - Main bundle: `dist/assets/index-BDPeBfua.js` (unchanged core logic)
  - 3D chunk: `dist/assets/Network3DScene-BRcBKEPO.js` (**172.24 kB** uncompressed / **55.12 kB** gzipped)
  - When viewing 2.5D or Top-Down modes, the 3D WebGL bundle is never loaded into browser memory.

### 2.2 View Mode Integration & WebGL Fallback Guard
- Added a third view mode **"3D"** alongside "2.5D Iso" and "Top-Down" in the monitor header toolbar.
- Added client-side WebGL detection helper `isWebGLAvailable()`.
- If WebGL is unavailable or fails to initialize, the UI automatically falls back to 2.5D mode and displays a persistent dismissible amber banner:
  *"WebGL 3D acceleration is not available in your browser or hardware environment. Automatically falling back to the 2.5D Isometric view."*
- When switching to 3D mode, the 2.5D HTML5 canvas requestAnimationFrame loop is cleanly paused to prevent redundant rendering cycles.

### 2.3 Road Ribbons, Markings & Controlled Node Topology
- Built 3D ribbon geometries from lane polylines (`frontend/src/utils/network3dGeometry.js`):
  - Extrudes perpendicular edge vertices along polyline normals based on each lane's true SUMO width ($3.2$m default, $6.8$m dual corridors).
  - Surface roads (elevation $0.0$m), Varthur flyover deck ($+6.5$m to $+7.0$m), and ORR mainline underpass ($0.0$m, tier underpass).
- Lane Markings:
  - White solid edge lines along outer lane boundaries ($0.18$m width, raised $+0.04$m).
  - White dashed center lane dividers ($3.0$m mark, $6.0$m gap, $0.14$m width).
  - Bold red/white transverse stop lines ($0.6$m depth) placed at all approach legs of the controlled junction `marathahalli_tls`.
- Junction Surfaces:
  - Extruded 3D polygons for intersection conflict areas matching SUMO junction boundaries.

### 2.4 Flyover Deck, Barriers & Support Pillar Clearance Audit
- **Deck Structure**:
  - Extruded concrete deck thickness slab ($0.6$m vertical depth) underneath flyover lanes with chamfered fascia.
  - Concrete crash barriers / parapet walls ($0.8$m height, $0.3$m width) along both outer edges of the flyover deck.
- **Pillar Clearance Audit (`auditBridgePillars()`)**:
  - Evaluated candidate pier locations at regular 25m intervals along the flyover centerline ($Z_{three} = 0$).
  - **Results**:
    - **Total candidate piers evaluated**: 9 stations ($X \in \{-100, -65, -45, -25, -5, 0, +5, +25, +45, +65, +100\}$).
    - **Clear Portal Piers**: 6 stations ($X \in \{-65, -45, -25, +25, +45, +65\}$) located on open ground with $>10.0$m clearance from any surface lane.
    - **Intersecting Centerline Piers**: 3 candidate stations ($X = -5.0$m, $0.0$m, $+5.0$m) conflict directly with surface traffic:
      - $X = -5.0$m: intersects `orr_mainline_sb_1` and `leg_orr_n_in_0` (penetration up to $2.40$m).
      - $X = 0.0$m: intersects ORR median and through-traffic lanes.
      - $X = +5.0$m: intersects `orr_mainline_nb_1` and `leg_orr_n_out_0` (penetration up to $2.40$m).
  - **Structural Reporting**:
    In accordance with civil engineering reality, Marathahalli Bridge features a portal / clear span over the ORR surface junction. The 3D scene renders the 6 valid clear piers and provides an interactive "Pillar Audit" badge that displays the exact conflict coordinates and affected lane IDs.

### 2.5 Lighting, Shading & Theme Adaptation
- Lighting model:
  - Soft ambient / hemisphere light (`skyColor="#94a3b8"`, `groundColor="#1e293b"`, intensity $0.9$).
  - Single directional fill light from top-west (`position={[80, 140, 60]}`, intensity $0.85$, shadow-free).
  - Ensures clean legibility on road surfaces without confusing cast shadows.
- Theme support:
  - Dark Theme: slate road asphalt (`#1e293b`), flyover deck (`#334155`), underpass (`#0f172a`), crisp white/slate lane markings, deep navy canvas (`#090d16`).
  - Light Theme: soft gray road asphalt (`#cbd5e1`), flyover deck (`#94a3b8`), clean white lane markings, bright slate canvas (`#f8fafc`).

### 2.6 Interactive Controls & Tier Separation
- **See-Through Flyover Toggle**:
  - Decreases flyover deck, barrier, and pillar opacity to $35\%$ (`transparent: true, opacity: 0.35`) so surface junction movements beneath the bridge are completely visible.
- **Explode 3-Tier View in 3D**:
  - Smoothly translates the vertical Y-offset of the 3 network tiers:
    - Flyover Tier: shifted upward by $+18.0$m.
    - Surface Tier: maintained at $0.0$m baseline.
    - Underpass Tier: shifted downward by $-18.0$m.
  - Renders floating HTML badges in 3D space (`@react-three/drei` `Html`) identifying each tier.
- **Camera Navigation & Presets**:
  - Includes smooth OrbitControls with damped rotation, pan, zoom (distance bounded between $15$m and $650$m).
  - 4 one-click preset buttons:
    1. **Iso SW**: Classic junction overview `[75, 65, 85]` -> `[0, 2, 0]`.
    2. **Iso NE**: Reverse angle showing east flyover ramp `[-75, 65, -85]` -> `[0, 2, 0]`.
    3. **Top-Down 3D**: Direct orthographic-style overhead `[0, 160, 0.01]` -> `[0, 0, 0]`.
    4. **Flyover Eye-Level**: Driver's eye perspective on the deck `[-60, 12, 10]` -> `[0, 7, 0]`.
- **Area Labels**:
  - Spatial HTML badges placed at key landmarks, all strictly marked **"(approximate)"**:
    - *Marathahalli Bridge (approximate)*
    - *Varthur Road (approximate)*
    - *Outer Ring Road (approximate)*
    - *marathahalli_tls (Controlled)*
- **Mandatory Footer Tooltip**:
  - Permanent disclaimer rendered in the bottom status strip:
    *"Modelled elevation; synthetic demand. Never present geometry as surveyed."*

### 2.7 Draw-Call Optimization & Performance
- Instead of mounting $166$ separate lane meshes (which would create $166+$ draw calls and degrade mobile/integrated GPUs), static geometry is merged via `BufferGeometryUtils.mergeGeometries` into **exactly 8 categorized static meshes**:
  1. `surfaceRoads`
  2. `flyoverRoads`
  3. `underpassRoads`
  4. `markings` (edge lines, dashed lines, stop lines)
  5. `junctions` (intersection surface polygons)
  6. `deckThickness` (extruded slab)
  7. `barriers` (concrete parapet walls)
  8. `pillars` (cylindrical bridge piers)
- Performance safeguards:
  - `frameloop="demand"`: renders only on camera movement or state updates; idle CPU/GPU usage is $0\%$.
  - `dpr={Math.min(window.devicePixelRatio || 1, 2)}`: prevents excessive pixel-fill on high-DPI retina displays.

---

## 3. Visual Verification (4 Camera Angles in Dark & Light Themes)

All 8 verification vectors were rendered via Three.js perspective projection matrix mathematics and saved to `docs/artifacts/phase4/`:

| Camera Angle | Dark Theme Artifact | Light Theme Artifact | Key Visible Features |
|---|---|---|---|
| **Iso SW** | [`phase4_3d_isoSW_dark.svg`](artifacts/phase4/phase4_3d_isoSW_dark.svg) | [`phase4_3d_isoSW_light.svg`](artifacts/phase4/phase4_3d_isoSW_light.svg) | Classic 4-way surface intersection, Varthur flyover overpass, stop lines, area labels |
| **Iso NE** | [`phase4_3d_isoNE_dark.svg`](artifacts/phase4/phase4_3d_isoNE_dark.svg) | [`phase4_3d_isoNE_light.svg`](artifacts/phase4/phase4_3d_isoNE_light.svg) | Reverse angle showing eastern ascending ramp, crash barriers, bridge support piers |
| **Top-Down 3D** | [`phase4_3d_topDown_dark.svg`](artifacts/phase4/phase4_3d_topDown_dark.svg) | [`phase4_3d_topDown_light.svg`](artifacts/phase4/phase4_3d_topDown_light.svg) | True orthogonal road ribbons, lane markings, stop lines at `marathahalli_tls`, turning radii |
| **Flyover Eye-Level** | [`phase4_3d_flyoverEye_dark.svg`](artifacts/phase4/phase4_3d_flyoverEye_dark.svg) | [`phase4_3d_flyoverEye_light.svg`](artifacts/phase4/phase4_3d_flyoverEye_light.svg) | Close-up of deck slab thickness ($0.6$m), parapet crash barriers ($0.8$m), bridge piers |

---

## 4. Test Verification Results

### 4.1 Frontend Unit & Snapshot Tests (`node --test test/*.test.js`)
- **Total Tests**: **41 passed**, 0 failed (**100% green**, runtime: $448$ms).
- **Phase 4 Specific Tests (`frontend/test/network3dScene.test.js`)**:
  - `3D Coordinate Transforms - 1 unit = 1 metre bidirectional mapping`: PASS (origin at $350,350$, Y-up elevation, round-trip tolerance $< 10^{-4}$).
  - `Mesh-Count Snapshot Test - Static geometry merges into exactly 8 categorized meshes`: PASS (all 8 categories non-empty BufferGeometries).
  - `Bridge Support Pillars - Geometric clearance audit and surface lane collisions`: PASS (evaluates 9 grid points, verifies 6 clear portal piers and 3 intersecting centerline points at $X \in \{-5, 0, +5\}$).
  - `Camera Presets - Four distinct viewing angles configured with target centers`: PASS (`isoSW`, `isoNE`, `topDown`, `flyoverEye`).
  - `WebGL Context Lifecycle - Mounts, disposes, and cleans up without memory leak`: PASS (8 meshes mounted, geometries and materials cleanly disposed).
  - `WebGL Availability Guard - Function returns boolean and does not throw`: PASS.

### 4.2 Python Pytest Gate (`pytest -q`)
- **Total Tests**: **113 passed**, 1 deprecation warning, 0 failed (**100% green**, runtime: $945.49$s).
- All signal safety invariants, clearance intervals, TraCI controllers, export validators, and microscopic SUMO simulations passed without regression.

### 4.3 Production Build Verification (`npm run build --prefix frontend`)
- Built cleanly with Vite in $29.33$s.
- `Network3DScene` dynamically isolated into `dist/assets/Network3DScene-BRcBKEPO.js` ($172.24$ kB / $55.12$ kB gzip).

---

## 5. Files Created & Modified

| File | Status | Description |
|---|---|---|
| `frontend/src/utils/network3dGeometry.js` | Created | Three.js geometry compilation engine (ribbons, markings, barriers, deck, pillar audit, coordinate transforms) |
| `frontend/src/components/Network3DScene.jsx` | Created | React Three Fiber 3D Scene component with camera presets, lighting, explode view, transparency, and labels |
| `frontend/src/components/IsometricIntersection.jsx` | Modified | Added 3D view toggle, `React.lazy` + `Suspense` loading, and WebGL availability guard |
| `frontend/test/network3dScene.test.js` | Created | Automated tests for transforms, 8-mesh snapshot, pillar collision audit, presets, and WebGL lifecycle |
| `frontend/scripts/generate_3d_snapshots.js` | Created | Script generating the 8 vector snapshots from 4 camera angles in dark and light themes |
| `docs/artifacts/phase4/*.svg` | Created | 8 visual verification vector snapshots |
| `frontend/package.json` | Modified | Added `three`, `@react-three/fiber`, and `@react-three/drei` dependencies |
| `docs/phase4_report.md` | Created | Phase 4 deliverable report |
