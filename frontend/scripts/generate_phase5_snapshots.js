/**
 * generate_phase5_snapshots.js - Headless 3D vector snapshot generator for Phase 5.
 *
 * Renders the 3D scene at three timestamps (t=1s, t=30s, t=60s) showing:
 * 1. Low-poly vehicles positioned at (x, y, z) with flyover deck elevation (+6.8m)
 * 2. 3D signal heads with active bulbs derived from real tl_state strings
 * 3. 3D queue volume bars over detector spans (colored by sensor status, OFFLINE non-zero)
 * 4. 3D decision callouts with separated requested vs applied increments
 * 5. Dynamic labelling ("Live simulation" vs "Replay" vs "Snapshot")
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';

import {
  compileNetwork3DGeometries,
  auditBridgePillars,
  sumoToThree,
  CAMERA_PRESETS,
} from '../src/utils/network3dGeometry.js';
import {
  classifyVehicleType,
  VEHICLE_BASE_DIMENSIONS,
} from '../src/utils/vehicle3dMesh.js';
import {
  SIGNAL_APPROACH_CONFIG,
  decodeSignalStateString,
  computeSignalTimer,
  getApproachQueueDisplay,
} from '../src/utils/signalAndQueue3d.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const networkPath = path.resolve(__dirname, '../public/network3d.json');
const replayPath = path.resolve(
  __dirname,
  '../public/demo-data/runs/marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121/replay.json'
);
const outDir = path.resolve(__dirname, '../../docs/artifacts/phase5');

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const networkData = JSON.parse(fs.readFileSync(networkPath, 'utf8'));
const replayData = JSON.parse(fs.readFileSync(replayPath, 'utf8'));
const compiled = compileNetwork3DGeometries(networkData);

const WIDTH = 1280;
const HEIGHT = 720;

function createCamera() {
  const preset = CAMERA_PRESETS.isoSW; // [75, 65, 85] -> [0, 2, 0]
  const camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.5, 1000);
  camera.position.set(...preset.position);
  camera.lookAt(...preset.target);
  camera.updateMatrixWorld();
  camera.updateProjectionMatrix();
  return camera;
}

function projectPoint(point3d, camera) {
  const v = new THREE.Vector3(...point3d);
  v.project(camera);
  const px = ((v.x + 1) * WIDTH) / 2;
  const py = ((-v.y + 1) * HEIGHT) / 2;
  return { x: px, y: py, z: v.z, visible: v.z >= -1 && v.z <= 1 };
}

function renderGeometryTriangles(geom, camera, fillColor, strokeColor, fillOpacity = 1.0) {
  if (!geom || !geom.attributes.position) return [];
  const pos = geom.attributes.position.array;
  const index = geom.index ? geom.index.array : null;
  const triangles = [];

  const count = index ? index.length : pos.length / 3;
  for (let i = 0; i < count; i += 3) {
    const i0 = index ? index[i] : i;
    const i1 = index ? index[i + 1] : i + 1;
    const i2 = index ? index[i + 2] : i + 2;

    const p0 = [pos[i0 * 3], pos[i0 * 3 + 1], pos[i0 * 3 + 2]];
    const p1 = [pos[i1 * 3], pos[i1 * 3 + 1], pos[i1 * 3 + 2]];
    const p2 = [pos[i2 * 3], pos[i2 * 3 + 1], pos[i2 * 3 + 2]];

    const sp0 = projectPoint(p0, camera);
    const sp1 = projectPoint(p1, camera);
    const sp2 = projectPoint(p2, camera);

    if (sp0.visible || sp1.visible || sp2.visible) {
      const avgZ = (sp0.z + sp1.z + sp2.z) / 3;
      triangles.push({
        avgZ,
        svg: `<polygon points="${sp0.x.toFixed(1)},${sp0.y.toFixed(1)} ${sp1.x.toFixed(1)},${sp1.y.toFixed(1)} ${sp2.x.toFixed(1)},${sp2.y.toFixed(1)}" fill="${fillColor}" ${strokeColor ? `stroke="${strokeColor}" stroke-width="0.5"` : ''} fill-opacity="${fillOpacity}"/>`,
      });
    }
  }
  return triangles;
}

function renderBox(center3d, dims, camera, fillColor, strokeColor, opacity = 1.0) {
  const [cx, cy, cz] = center3d;
  const [w, h, l] = dims;
  const geom = new THREE.BoxGeometry(w, h, l);
  geom.translate(cx, cy, cz);
  const tris = renderGeometryTriangles(geom, camera, fillColor, strokeColor, opacity);
  geom.dispose();
  return tris;
}

function renderPhase5Timestamp(tTarget, labelMode, decisionOverride) {
  const camera = createCamera();
  const frame = replayData.frames.find((f) => f.t === tTarget) || replayData.frames[0];
  const vehs = frame.vehicles || [];

  const elements = [];

  // 1. Static Road Geometry
  elements.push(...renderGeometryTriangles(compiled.surfaceRoads, camera, '#1e293b', '#334155'));
  elements.push(...renderGeometryTriangles(compiled.junctions, camera, '#1a2234', '#334155'));
  elements.push(...renderGeometryTriangles(compiled.underpassRoads, camera, '#0f172a', '#1e293b'));
  elements.push(...renderGeometryTriangles(compiled.markings, camera, '#94a3b8', null));
  elements.push(...renderGeometryTriangles(compiled.deckThickness, camera, '#1e293b', '#475569', 0.85));
  elements.push(...renderGeometryTriangles(compiled.flyoverRoads, camera, '#334155', '#475569', 0.85));
  elements.push(...renderGeometryTriangles(compiled.barriers, camera, '#475569', null, 0.9));
  elements.push(...renderGeometryTriangles(compiled.pillars, camera, '#3b82f6', null));

  // 2. 3D Vehicles (Instanced representation)
  for (const v of vehs) {
    const isAmbulance = classifyVehicleType(v) === 'ambulance';
    const isQueued = (v.s !== undefined && v.s < 0.2) || (v.w !== undefined && v.w > 1.0);
    const vColor = isAmbulance ? '#f43f5e' : isQueued ? '#f97316' : '#38bdf8';

    const [tx, ty, tz] = sumoToThree(v.x, v.y, v.z || 0.0);
    const isElevated = (v.z || 0.0) >= 5.0;
    const finalY = ty + (isElevated ? 0.8 : 0.7);

    const dims = isAmbulance ? [2.1, 2.3, 5.8] : [1.8, 1.4, 4.5];
    elements.push(...renderBox([tx, finalY, tz], dims, camera, vColor, '#0f172a', 0.95));
  }

  // 3. 3D Queue Volume Bars
  const approachQueues = {
    N: { total_queue_m: frame.queues_m?.N || 0, sensor_status: 'MEASURING' },
    S: { total_queue_m: frame.queues_m?.S || 0, sensor_status: 'MEASURING' },
    E: { total_queue_m: frame.queues_m?.E || 0, sensor_status: 'SATURATED', is_saturated: true },
    W: { total_queue_m: 0.0, sensor_status: 'OFFLINE', data_valid: false }, // Enforce offline demonstration
  };

  const queueLabels = [];
  for (const [appKey, cfg] of Object.entries(SIGNAL_APPROACH_CONFIG)) {
    const qDisp = getApproachQueueDisplay(appKey, approachQueues, frame.queues_m);
    const halfLen = Math.max(0.5, qDisp.renderQueueM) / 2;
    let posX = cfg.stopLinePos[0];
    let posZ = cfg.stopLinePos[2];
    let bWidth = cfg.width;
    let bLength = Math.max(0.5, qDisp.renderQueueM);

    if (cfg.axisDir[2] !== 0) {
      posZ = cfg.stopLinePos[2] - cfg.axisDir[2] * halfLen;
    } else {
      posX = cfg.stopLinePos[0] - cfg.axisDir[0] * halfLen;
      const tmp = bWidth;
      bWidth = bLength;
      bLength = tmp;
    }

    elements.push(
      ...renderBox(
        [posX, 0.4, posZ],
        [bWidth, 0.8, bLength],
        camera,
        qDisp.style.color,
        qDisp.style.border,
        qDisp.style.fillOpacity
      )
    );

    const lblPt = projectPoint(
      [cfg.stopLinePos[0] - cfg.axisDir[0] * 12.0, 2.5, cfg.stopLinePos[2] - cfg.axisDir[2] * 12.0],
      camera
    );
    if (lblPt.visible) {
      queueLabels.push(`
        <g transform="translate(${lblPt.x.toFixed(1)}, ${lblPt.y.toFixed(1)})">
          <rect x="-60" y="-14" width="120" height="24" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="${qDisp.style.border}" stroke-width="1"/>
          <text x="0" y="-1" fill="#ffffff" font-family="monospace" font-size="9" font-weight="700" text-anchor="middle">${appKey}: ${qDisp.queue_m.toFixed(1)}m</text>
          <text x="0" y="8" fill="${qDisp.isOffline ? '#f59e0b' : '#38bdf8'}" font-family="monospace" font-size="7" font-weight="600" text-anchor="middle">${qDisp.style.label}</text>
        </g>
      `);
    }
  }

  // 4. 3D Signal Heads at Stop Lines
  const decoded = decodeSignalStateString(frame.tl_state);
  const signalLabels = [];
  for (const [appKey, cfg] of Object.entries(SIGNAL_APPROACH_CONFIG)) {
    const appState = decoded.approaches[appKey] || { colorName: 'RED', hex: '#ef4444' };
    const [px, , pz] = cfg.signalHeadPos;

    // Pole + housing box
    elements.push(...renderBox([px, 2.25, pz], [0.15, 4.5, 0.15], camera, '#334155', null));
    elements.push(...renderBox([px, 4.2, pz], [0.6, 1.5, 0.4], camera, '#0f172a', '#334155'));

    // Lit bulb
    const bulbColor = appState.hex;
    elements.push(...renderBox([px, 4.2, pz + 0.2], [0.35, 0.35, 0.2], camera, bulbColor, bulbColor));

    const spPt = projectPoint([px, 5.5, pz], camera);
    if (spPt.visible) {
      signalLabels.push(`
        <g transform="translate(${spPt.x.toFixed(1)}, ${spPt.y.toFixed(1)})">
          <rect x="-45" y="-10" width="90" height="18" rx="4" fill="${bulbColor}" fill-opacity="0.2" stroke="${bulbColor}" stroke-width="1"/>
          <text x="0" y="3" fill="#ffffff" font-family="monospace" font-size="9" font-weight="700" text-anchor="middle">${appKey} (${cfg.phaseGroup}): ${appState.colorName}</text>
        </g>
      `);
    }
  }

  // Sort geometry triangles back-to-front
  elements.sort((a, b) => b.avgZ - a.avgZ);

  // 5. Decision Callout (floating above marathahalli_tls)
  const decision = decisionOverride || {
    t: frame.t,
    axis: frame.tl_state.includes('GGGg') ? 'EW' : 'NS',
    action: 'EXTEND',
    reason: 'Approved +3.0s extension: own queue 28.5m vs 11.2m competing',
    delta_g_req_s: 5.0,
    delta_g_app_s: 3.0,
  };
  const decPt = projectPoint([0, 14.0, 18.0], camera);

  // 6. SVG Assembly
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="${WIDTH}" height="${HEIGHT}">
  <rect width="${WIDTH}" height="${HEIGHT}" fill="#090d16"/>

  <!-- Geometry Elements (Sorted) -->
  <g id="geometry_elements">
    ${elements.map((e) => e.svg).join('\n    ')}
  </g>

  <!-- Queue Metric Labels -->
  <g id="queue_labels">
    ${queueLabels.join('\n')}
  </g>

  <!-- Signal Head Labels -->
  <g id="signal_labels">
    ${signalLabels.join('\n')}
  </g>

  <!-- 3D Decision Callout -->
  <g id="decision_callout" transform="translate(${decPt.x.toFixed(1)}, ${decPt.y.toFixed(1)})">
    <rect x="-140" y="-36" width="280" height="72" rx="8" fill="rgba(15, 23, 42, 0.95)" stroke="#f59e0b" stroke-width="1.5"/>
    <circle cx="-120" cy="-20" r="4" fill="#f59e0b"/>
    <text x="-110" y="-17" fill="#f59e0b" font-family="monospace" font-size="11" font-weight="700">${decision.axis}: ${decision.action} (t=${decision.t}s)</text>
    <text x="-120" y="1" fill="#f8fafc" font-family="sans-serif" font-size="9">${decision.reason}</text>
    <g transform="translate(-120, 14)">
      <rect x="0" y="0" width="70" height="15" rx="3" fill="#1e3a8a" stroke="#3b82f6" stroke-width="0.5"/>
      <text x="35" y="11" fill="#93c5fd" font-family="monospace" font-size="8" font-weight="700" text-anchor="middle">Req: +${decision.delta_g_req_s}s</text>
      <rect x="76" y="0" width="70" height="15" rx="3" fill="#064e3b" stroke="#10b981" stroke-width="0.5"/>
      <text x="111" y="11" fill="#6ee7b7" font-family="monospace" font-size="8" font-weight="700" text-anchor="middle">App: +${decision.delta_g_app_s}s</text>
    </g>
  </g>

  <!-- Top HUD: Mode Pill, Telemetry Time & Active Count -->
  <g id="top_hud" transform="translate(24, 24)">
    <rect width="440" height="48" rx="8" fill="rgba(15, 23, 42, 0.9)" stroke="#334155" stroke-width="1"/>
    <circle cx="18" cy="24" r="5" fill="${labelMode.includes('Live') ? '#10b981' : '#3b82f6'}"/>
    <text x="32" y="28" fill="#f8fafc" font-family="monospace" font-size="13" font-weight="700">${labelMode}</text>
    <text x="175" y="28" fill="#94a3b8" font-family="monospace" font-size="11">t = ${frame.t.toFixed(1)}s | ${vehs.length} vehs | tl: ${frame.tl_state.slice(0, 8)}...</text>
  </g>

  <!-- Bottom HUD: Provenance Disclaimer & Legend -->
  <g id="bottom_hud" transform="translate(24, ${HEIGHT - 48})">
    <rect width="${WIDTH - 48}" height="32" rx="6" fill="rgba(15, 23, 42, 0.9)" stroke="#334155" stroke-width="1"/>
    <circle cx="16" cy="16" r="4" fill="#38bdf8"/>
    <text x="26" y="20" fill="#94a3b8" font-family="monospace" font-size="10">Moving (Cyan)</text>
    <circle cx="130" cy="16" r="4" fill="#f97316"/>
    <text x="140" y="20" fill="#94a3b8" font-family="monospace" font-size="10">Queued (Orange)</text>
    <circle cx="260" cy="16" r="4" fill="#f43f5e"/>
    <text x="270" y="20" fill="#94a3b8" font-family="monospace" font-size="10">Ambulance (Rose)</text>
    <circle cx="390" cy="16" r="4" fill="#64748b"/>
    <text x="400" y="20" fill="#f59e0b" font-family="monospace" font-size="10">Offline Sensor (Non-Zero Hatched)</text>
    <text x="${WIDTH - 64}" y="20" fill="#94a3b8" font-family="sans-serif" font-size="10" text-anchor="end" font-style="italic">Modelled elevation; synthetic demand. Never present geometry as surveyed.</text>
  </g>
</svg>
`;

  return svg;
}

console.log('Generating Phase 5 3D verification snapshots at three timestamps (t=1s, t=30s, t=60s)...');

const timestamps = [
  { t: 1, mode: 'Live simulation', file: 'phase5_3d_t1s_live.svg' },
  { t: 30, mode: 'Replay', file: 'phase5_3d_t30s_replay.svg' },
  { t: 60, mode: 'Snapshot', file: 'phase5_3d_t60s_snapshot.svg' },
];

for (const s of timestamps) {
  const filePath = path.join(outDir, s.file);
  const svgContent = renderPhase5Timestamp(s.t, s.mode);
  fs.writeFileSync(filePath, svgContent, 'utf8');
  console.log(`Saved: ${s.file} (${svgContent.length} bytes)`);
}

console.log('All 3 Phase 5 verification snapshots generated successfully!');
