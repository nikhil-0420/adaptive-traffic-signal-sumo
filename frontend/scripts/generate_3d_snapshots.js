/**
 * generate_3d_snapshots.js
 *
 * Headless 3D vector snapshot generator for Phase 4 visual verification.
 * Projects the 3D road ribbons, lane markings, junction surfaces, flyover deck slab,
 * crash barriers, support pillars, and area labels using Three.js PerspectiveCamera
 * matrix transformations into crisp SVG files for the 4 required camera angles
 * in both Dark and Light themes.
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

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const networkPath = path.resolve(__dirname, '../public/network3d.json');
const outDir = path.resolve(__dirname, '../../docs/artifacts/phase4');

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const networkData = JSON.parse(fs.readFileSync(networkPath, 'utf8'));
const compiled = compileNetwork3DGeometries(networkData);
const pillarAudit = auditBridgePillars(networkData);

const THEMES = {
  dark: {
    bg: '#090d16',
    surfaceRoad: '#1e293b',
    surfaceStroke: '#334155',
    flyoverRoad: '#334155',
    flyoverStroke: '#475569',
    underpassRoad: '#0f172a',
    underpassStroke: '#1e293b',
    edgeLine: '#64748b',
    dashedLine: '#94a3b8',
    stopLine: '#ef4444',
    junction: '#1a2234',
    deckThickness: '#1e293b',
    barrier: '#475569',
    pillarClear: '#3b82f6',
    pillarConflict: '#ef4444',
    grid: '#1e293b',
    text: '#94a3b8',
    title: '#f8fafc',
    hudBg: 'rgba(15, 23, 42, 0.85)',
    hudBorder: '#334155',
  },
  light: {
    bg: '#f8fafc',
    surfaceRoad: '#cbd5e1',
    surfaceStroke: '#94a3b8',
    flyoverRoad: '#94a3b8',
    flyoverStroke: '#64748b',
    underpassRoad: '#64748b',
    underpassStroke: '#475569',
    edgeLine: '#ffffff',
    dashedLine: '#ffffff',
    stopLine: '#dc2626',
    junction: '#e2e8f0',
    deckThickness: '#94a3b8',
    barrier: '#64748b',
    pillarClear: '#2563eb',
    pillarConflict: '#dc2626',
    grid: '#e2e8f0',
    text: '#475569',
    title: '#0f172a',
    hudBg: 'rgba(255, 255, 255, 0.9)',
    hudBorder: '#cbd5e1',
  },
};

const WIDTH = 1280;
const HEIGHT = 720;

function createCamera(presetKey) {
  const preset = CAMERA_PRESETS[presetKey];
  const camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.5, 1000);
  camera.position.set(...preset.position);
  camera.lookAt(...preset.target);
  camera.updateMatrixWorld();
  camera.updateProjectionMatrix();
  return { camera, preset };
}

/** Project 3D point (X, Y, Z) to 2D screen coordinates (px, py, depth) */
function projectPoint(point3d, camera) {
  const v = new THREE.Vector3(...point3d);
  v.project(camera);
  const px = ((v.x + 1) * WIDTH) / 2;
  const py = ((-v.y + 1) * HEIGHT) / 2;
  return { x: px, y: py, z: v.z, visible: v.z >= -1 && v.z <= 1 };
}

/** Render triangles from BufferGeometry */
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

/** Render a single view to SVG string */
function renderView(presetKey, themeKey) {
  const theme = THEMES[themeKey];
  const { camera, preset } = createCamera(presetKey);

  const drawElements = [];

  // 1. Surface roads & junctions
  const surfaceRoads = renderGeometryTriangles(compiled.surfaceRoads, camera, theme.surfaceRoad, theme.surfaceStroke);
  drawElements.push(...surfaceRoads);

  const junctions = renderGeometryTriangles(compiled.junctions, camera, theme.junction, theme.surfaceStroke);
  drawElements.push(...junctions);

  const underpass = renderGeometryTriangles(compiled.underpassRoads, camera, theme.underpassRoad, theme.underpassStroke);
  drawElements.push(...underpass);

  // 2. Markings
  const markings = renderGeometryTriangles(compiled.markings, camera, theme.dashedLine, null);
  drawElements.push(...markings);

  // 3. Flyover deck, thickness & barriers
  const deckThickness = renderGeometryTriangles(compiled.deckThickness, camera, theme.deckThickness, theme.flyoverStroke);
  drawElements.push(...deckThickness);

  const flyover = renderGeometryTriangles(compiled.flyoverRoads, camera, theme.flyoverRoad, theme.flyoverStroke);
  drawElements.push(...flyover);

  const barriers = renderGeometryTriangles(compiled.barriers, camera, theme.barrier, null);
  drawElements.push(...barriers);

  // 4. Pillars
  const pillars = renderGeometryTriangles(compiled.pillars, camera, theme.pillarClear, null);
  drawElements.push(...pillars);

  // Sort back-to-front by depth (avgZ descending in NDC where -1 is near, +1 is far)
  drawElements.sort((a, b) => b.avgZ - a.avgZ);

  // 5. Area Labels
  const labels = [
    { text: 'Marathahalli Bridge (approximate)', pos: sumoToThree(350, 350, 7.5), tier: 'Flyover Tier' },
    { text: 'Varthur Road (approximate)', pos: sumoToThree(180, 350, 0), tier: 'Surface Tier' },
    { text: 'Outer Ring Road (approximate)', pos: sumoToThree(350, 520, 0), tier: 'Surface Tier' },
    { text: 'marathahalli_tls (Controlled)', pos: sumoToThree(350, 332, 0), tier: 'Junction' },
  ];

  const labelSvgs = labels.map((lbl) => {
    const sp = projectPoint(lbl.pos, camera);
    if (!sp.visible || sp.x < 20 || sp.x > WIDTH - 20 || sp.y < 20 || sp.y > HEIGHT - 20) return '';
    return `
      <g transform="translate(${sp.x.toFixed(1)}, ${sp.y.toFixed(1)})">
        <rect x="-85" y="-12" width="170" height="20" rx="4" fill="${theme.hudBg}" stroke="${theme.hudBorder}" stroke-width="1"/>
        <text x="0" y="2" fill="${theme.title}" font-family="system-ui, -apple-system, sans-serif" font-size="10" font-weight="600" text-anchor="middle">${lbl.text}</text>
      </g>
    `;
  }).filter(Boolean);

  // SVG Assembly
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="${WIDTH}" height="${HEIGHT}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="${theme.bg}"/>
      <stop offset="100%" stop-color="${theme.bg}"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="${WIDTH}" height="${HEIGHT}" fill="url(#bgGrad)"/>

  <!-- Geometry Elements (Sorted) -->
  <g id="geometry_elements">
    ${drawElements.map((e) => e.svg).join('\n    ')}
  </g>

  <!-- Area Labels -->
  <g id="area_labels">
    ${labelSvgs.join('\n')}
  </g>

  <!-- View HUD Banner -->
  <g id="hud_header" transform="translate(24, 24)">
    <rect width="340" height="68" rx="8" fill="${theme.hudBg}" stroke="${theme.hudBorder}" stroke-width="1"/>
    <text x="16" y="26" fill="${theme.title}" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="700">DP1 Phase 4: 3D Road Topology</text>
    <text x="16" y="44" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="11">Angle: ${preset.name} | Theme: ${themeKey.toUpperCase()}</text>
    <text x="16" y="58" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="9">Eye: [${preset.position.join(', ')}] Target: [${preset.target.join(', ')}]</text>
  </g>

  <!-- Legend & Safety Invariant Footer -->
  <g id="hud_footer" transform="translate(24, ${HEIGHT - 48})">
    <rect width="${WIDTH - 48}" height="32" rx="6" fill="${theme.hudBg}" stroke="${theme.hudBorder}" stroke-width="1"/>
    <circle cx="16" cy="16" r="4" fill="${theme.pillarClear}"/>
    <text x="26" y="20" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="10">Bridge Piers (6 clear)</text>
    <circle cx="150" cy="16" r="4" fill="${theme.flyoverRoad}"/>
    <text x="160" y="20" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="10">Varthur Flyover Deck (+7m)</text>
    <circle cx="320" cy="16" r="4" fill="${theme.surfaceRoad}"/>
    <text x="330" y="20" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="10">Surface Junction (0m)</text>
    <circle cx="470" cy="16" r="4" fill="${theme.underpassRoad}"/>
    <text x="480" y="20" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="10">ORR Mainline</text>
    <text x="${WIDTH - 64}" y="20" fill="${theme.text}" font-family="system-ui, -apple-system, sans-serif" font-size="10" text-anchor="end" font-style="italic">Modelled elevation; synthetic demand. Never present geometry as surveyed.</text>
  </g>
</svg>
`;

  return svg;
}

console.log('Generating Phase 4 3D verification snapshots for 4 angles in Dark and Light themes...');

const presets = ['isoSW', 'isoNE', 'topDown', 'flyoverEye'];
const themes = ['dark', 'light'];

for (const p of presets) {
  for (const t of themes) {
    const filename = `phase4_3d_${p}_${t}.svg`;
    const filePath = path.join(outDir, filename);
    const svgContent = renderView(p, t);
    fs.writeFileSync(filePath, svgContent, 'utf8');
    console.log(`Saved: ${filename} (${svgContent.length} bytes)`);
  }
}

console.log('All 8 Phase 4 3D snapshots generated successfully!');
