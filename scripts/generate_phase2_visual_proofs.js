import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const geomPath = path.resolve(__dirname, '../frontend/src/data/marathahalli_geometry.json');
const geom = JSON.parse(fs.readFileSync(geomPath, 'utf8'));

const replayPath = path.resolve(
  __dirname,
  '../frontend/public/demo-data/runs/marathahalli_imbalanced_orr_medium_hybrid_queue_adaptive_s121/replay.json'
);
const replay = JSON.parse(fs.readFileSync(replayPath, 'utf8'));

const outDir = path.resolve(__dirname, '../docs/artifacts/phase2');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

function worldToScreen(wx, wy, z = 0, tier = 'surface', zoom = 1.0, isExploded = false, width = 1200, height = 700) {
  const origX = 350;
  const origY = 350;
  const cx = width / 2;
  const cy = height / 2;
  const baseScale = (Math.min(width, height) / (480 * 1.45)) * zoom;

  const u = wx - origX;
  const v = wy - origY;

  let tierOffsetY = 0;
  if (isExploded) {
    if (tier === 'flyover') tierOffsetY = -72;
    else if (tier === 'underpass') tierOffsetY = 65;
  }

  const cos30 = Math.cos(Math.PI / 6);
  const sin30 = Math.sin(Math.PI / 6);
  const isoX = (u - v) * cos30;
  const isoY = (u + v) * sin30;

  return {
    x: cx + isoX * baseScale,
    y: cy - isoY * baseScale * 0.72 - z * baseScale * 1.85 + tierOffsetY,
  };
}

function renderVisualSvg({
  mode = 'after', // 'before' | 'after'
  theme = 'dark', // 'dark' | 'light'
  zoom = 1.0,
  scaleMultiplier = 2.0,
  seeThroughFlyover = true,
  showTrails = true,
  selectedVehId = null,
  title = '',
  viewW = 1200,
  viewH = 700,
}) {
  const isDark = theme === 'dark';
  const bgColor = isDark ? '#0D1417' : '#F1F5F9';
  const asphaltColor = isDark ? '#29343A' : '#475569';
  const roadMarkingColor = isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(255, 255, 255, 0.8)';
  const baseScale = (Math.min(viewW, viewH) / (480 * 1.45)) * zoom;

  // Frame sample at t=30s
  const frame = replay.frames[28] || replay.frames[0];
  const activeVehicles = frame.vehicles || [];

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${viewW} ${viewH}" width="${viewW}" height="${viewH}" style="background-color: ${bgColor}; font-family: monospace;">\n`;
  svg += `<defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>\n`;

  // Background
  svg += `<rect width="${viewW}" height="${viewH}" fill="${bgColor}" />\n`;

  // Surface Roadways
  for (const lane of geom.lanes.filter((l) => l.tier === 'surface')) {
    if (lane.shape && lane.shape.length >= 2) {
      const pts = lane.shape
        .map((p) => {
          const pt = worldToScreen(p[0], p[1], 0, 'surface', zoom, false, viewW, viewH);
          return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
        })
        .join(' ');
      svg += `<polyline points="${pts}" stroke="${asphaltColor}" stroke-width="${(lane.width || 3.2) * baseScale}" stroke-linecap="round" fill="none" />\n`;
      if (!lane.is_internal) {
        svg += `<polyline points="${pts}" stroke="${roadMarkingColor}" stroke-width="1.2" stroke-dasharray="4,4" fill="none" opacity="0.6" />\n`;
      }
    }
  }

  // Draw flyover ground shadow
  for (const lane of geom.lanes.filter((l) => l.tier === 'flyover')) {
    if (lane.shape && lane.shape.length >= 2) {
      const shadowPts = lane.shape
        .map((p) => {
          const pt = worldToScreen(p[0], p[1], 0, 'surface', zoom, false, viewW, viewH);
          return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
        })
        .join(' ');
      svg += `<polyline points="${shadowPts}" stroke="rgba(0,0,0,0.4)" stroke-width="${((lane.width || 3.2) + 1.5) * baseScale}" stroke-linecap="round" fill="none" />\n`;
    }
  }

  // DRAW ORDER LOGIC:
  // In 'after': draw surface vehicles BEFORE flyover deck
  // In 'before': flyover deck is drawn first, then vehicles in batch over everything
  const drawVehicles = (vehs, isFlyoverTier = false) => {
    let s = '';
    for (const v of vehs) {
      const isEastWest = Math.abs((v.a || 0) - 90) < 35 || Math.abs((v.a || 0) - 270) < 35;
      const isNorthSouth = Math.abs((v.a || 0) - 0) < 35 || Math.abs((v.a || 0) - 180) < 35;
      let tier = 'surface';
      let zVal = 0.0;
      if (Math.abs(v.y - 350) <= 8.5 && isEastWest && v.x >= 170 && v.x <= 530) {
        tier = 'flyover';
        zVal = 7.0;
      } else if (Math.abs(v.x - 350) <= 8.5 && isNorthSouth && v.y >= 170 && v.y <= 530 && v.s > 7.0) {
        tier = 'underpass';
        zVal = -4.0;
      }

      if (isFlyoverTier && tier !== 'flyover') continue;
      if (!isFlyoverTier && tier === 'flyover') continue;

      const pt = worldToScreen(v.x, v.y, zVal, tier, zoom, false, viewW, viewH);
      const isQueued = (v.s < 0.1) || (v.w > 0);
      const isAmbulance = v.id.includes('em') || v.type === 'ambulance';

      let vLen, vWid, fillCol, strokeCol;
      if (mode === 'before') {
        // Before Phase 2: fixed 13px stretch at 100%, low contrast colors
        vLen = 13.0;
        vWid = 5.2;
        fillCol = isAmbulance ? '#FFFFFF' : (isQueued ? '#FFB020' : '#3B82F6'); // low contrast blue
        strokeCol = '#0C1316';
      } else {
        // After Phase 2: Exaggerate scaling with min 8px clamp & high contrast
        const nomLen = 4.8 * baseScale * scaleMultiplier;
        const nomWid = 2.0 * baseScale * scaleMultiplier;
        const clampMult = nomLen < 8.0 ? (8.0 / nomLen) : 1.0;
        vLen = nomLen * clampMult;
        vWid = nomWid * clampMult;

        strokeCol = isDark ? '#FFFFFF' : '#0F172A';
        if (isAmbulance) {
          fillCol = '#FFFFFF';
        } else if (isQueued) {
          fillCol = '#F59E0B'; // warm amber
        } else {
          fillCol = isDark ? '#38BDF8' : '#0284C7'; // high contrast cyan
        }

        // Trails
        if (showTrails && v.s > 1.0) {
          s += `<circle cx="${pt.x - 10}" cy="${pt.y + 4}" r="${vWid * 0.4}" fill="${isDark ? 'rgba(56,189,248,0.25)' : 'rgba(2,132,199,0.25)'}" />\n`;
          s += `<circle cx="${pt.x - 5}" cy="${pt.y + 2}" r="${vWid * 0.5}" fill="${isDark ? 'rgba(56,189,248,0.45)' : 'rgba(2,132,199,0.45)'}" />\n`;
        }
      }

      // Ambulance halo
      if (isAmbulance && mode === 'after') {
        s += `<circle cx="${pt.x}" cy="${pt.y}" r="${Math.max(vLen, vWid) * 1.2}" fill="none" stroke="#EF4444" stroke-width="2" filter="url(#glow)" />\n`;
      }

      // Vehicle body
      s += `<rect x="${pt.x - vLen / 2}" y="${pt.y - vWid / 2}" width="${vLen}" height="${vWid}" rx="2" fill="${fillCol}" stroke="${strokeCol}" stroke-width="1.0" />\n`;

      // Roof arrow & headlights
      if (mode === 'after') {
        s += `<polygon points="${pt.x + vLen * 0.2},${pt.y} ${pt.x},${pt.y - 1.5} ${pt.x},${pt.y + 1.5}" fill="${isDark ? '#FFFFFF' : '#0F172A'}" />\n`;
        if (v.s > 1.0 && isDark) {
          s += `<polygon points="${pt.x + vLen / 2},${pt.y - 1} ${pt.x + vLen / 2 + 12},${pt.y - 4} ${pt.x + vLen / 2 + 12},${pt.y + 4} ${pt.x + vLen / 2},${pt.y + 1}" fill="rgba(56,189,248,0.15)" />\n`;
        }
      }

      // Selection ring
      if (v.id === selectedVehId) {
        s += `<circle cx="${pt.x}" cy="${pt.y}" r="${vLen * 0.9}" fill="none" stroke="#38BDF8" stroke-width="2" stroke-dasharray="4,4" />\n`;
      }
    }
    return s;
  };

  if (mode === 'after') {
    // 1. Draw Surface Traffic first
    svg += drawVehicles(activeVehicles, false);

    // 2. Draw Flyover Deck (ghosted with seeThroughFlyover)
    const deckOpacity = seeThroughFlyover ? '0.35' : '1.0';
    for (const lane of geom.lanes.filter((l) => l.tier === 'flyover')) {
      if (lane.shape && lane.shape.length >= 2) {
        const deckPts = lane.shape
          .map((p) => {
            const pt = worldToScreen(p[0], p[1], 7.0, 'flyover', zoom, false, viewW, viewH);
            return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
          })
          .join(' ');
        svg += `<polyline points="${deckPts}" stroke="${asphaltColor}" stroke-width="${(lane.width || 3.2) * baseScale}" stroke-linecap="round" fill="none" opacity="${deckOpacity}" />\n`;
        svg += `<polyline points="${deckPts}" stroke="#FFB020" stroke-width="1.5" fill="none" opacity="${deckOpacity}" />\n`;
      }
    }

    // 3. Draw Flyover Traffic on top of the deck
    svg += drawVehicles(activeVehicles, true);
  } else {
    // Before mode: Flyover deck drawn BEFORE vehicles, but all vehicles drawn on top in single loop
    for (const lane of geom.lanes.filter((l) => l.tier === 'flyover')) {
      if (lane.shape && lane.shape.length >= 2) {
        const deckPts = lane.shape
          .map((p) => {
            const pt = worldToScreen(p[0], p[1], 7.0, 'flyover', zoom, false, viewW, viewH);
            return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
          })
          .join(' ');
        svg += `<polyline points="${deckPts}" stroke="${asphaltColor}" stroke-width="${(lane.width || 3.2) * baseScale}" stroke-linecap="round" fill="none" opacity="1.0" />\n`;
        svg += `<polyline points="${deckPts}" stroke="#FFB020" stroke-width="1.5" fill="none" opacity="1.0" />\n`;
      }
    }
    svg += drawVehicles(activeVehicles, false);
    svg += drawVehicles(activeVehicles, true);
  }

  // Overlay HUD
  const queuedCount = activeVehicles.filter((v) => (v.s < 0.1) || (v.w > 0)).length;
  svg += `<g transform="translate(16, 20)">
    <rect width="320" height="34" rx="17" fill="rgba(12, 19, 22, 0.9)" stroke="rgba(255,255,255,0.15)" />
    <circle cx="20" cy="17" r="4" fill="#10B981" />
    <text x="32" y="21" fill="#F3EDE0" font-size="12" font-weight="bold">PHASORA DIGITAL TWIN</text>
    <text x="180" y="21" fill="#94A3B8" font-size="11">${activeVehicles.length} in network (${queuedCount} queued)</text>
  </g>\n`;

  // Title badge
  svg += `<g transform="translate(16, 64)">
    <rect width="280" height="24" rx="6" fill="rgba(0,0,0,0.75)" />
    <text x="12" y="16" fill="${mode === 'after' ? '#38BDF8' : '#F59E0B'}" font-size="11" font-weight="bold">${title}</text>
  </g>\n`;

  // Legend (if after mode)
  if (mode === 'after') {
    svg += `<g transform="translate(16, ${viewH - 140})">
      <rect width="200" height="124" rx="8" fill="rgba(12, 19, 22, 0.95)" stroke="rgba(255,255,255,0.15)" />
      <text x="12" y="18" fill="#F3EDE0" font-size="10" font-weight="bold">MAP LEGEND (PHASE 2)</text>
      <rect x="12" y="28" width="12" height="7" rx="1" fill="#38BDF8" stroke="#FFFFFF" stroke-width="0.8" />
      <text x="32" y="35" fill="#E2E8F0" font-size="10">Moving Traffic</text>
      <rect x="12" y="44" width="12" height="7" rx="1" fill="#F59E0B" stroke="#FFFFFF" stroke-width="0.8" />
      <text x="32" y="51" fill="#E2E8F0" font-size="10">Queued / Stopped</text>
      <rect x="12" y="60" width="12" height="7" rx="1" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.2" />
      <text x="32" y="67" fill="#E2E8F0" font-size="10">Emergency (Halo)</text>
      <line x1="12" y1="78" x2="188" y2="78" stroke="rgba(255,255,255,0.1)" />
      <rect x="12" y="86" width="12" height="4" rx="1" fill="#10B981" />
      <text x="32" y="91" fill="#94A3B8" font-size="9">E2 Zero (Clear)</text>
      <rect x="12" y="100" width="12" height="4" rx="1" fill="#F59E0B" />
      <text x="32" y="105" fill="#94A3B8" font-size="9">E2 Measuring</text>
    </g>\n`;
  }

  // Hover Tooltip mockup (when vehicle selected)
  if (selectedVehId && mode === 'after') {
    svg += `<g transform="translate(680, 260)">
      <rect width="220" height="110" rx="10" fill="rgba(12, 19, 22, 0.95)" stroke="#38BDF8" stroke-width="1.5" />
      <text x="14" y="22" fill="#38BDF8" font-size="12" font-weight="bold">${selectedVehId}</text>
      <rect x="140" y="10" width="66" height="18" rx="4" fill="rgba(255,255,255,0.1)" />
      <text x="173" y="23" fill="#E2E8F0" font-size="9" text-anchor="middle">TRANSIT BUS</text>
      <text x="14" y="48" fill="#94A3B8" font-size="9">SPEED</text>
      <text x="14" y="64" fill="#FFFFFF" font-size="12" font-weight="bold">32.4 km/h <tspan fill="#94A3B8" font-size="10">(9.0 m/s)</tspan></text>
      <text x="110" y="48" fill="#94A3B8" font-size="9">WAIT TIME</text>
      <text x="110" y="64" fill="#F59E0B" font-size="12" font-weight="bold">14.0 s <tspan fill="#94A3B8" font-size="9">QUEUED</tspan></text>
      <line x1="14" y1="76" x2="206" y2="76" stroke="rgba(255,255,255,0.1)" />
      <text x="14" y="94" fill="#94A3B8" font-size="10">Tier: <tspan fill="#FFFFFF" font-weight="bold">SURFACE</tspan></text>
      <rect x="135" y="82" width="70" height="20" rx="4" fill="#38BDF8" />
      <text x="170" y="96" fill="#0C1316" font-size="10" font-weight="bold" text-anchor="middle">FOLLOWING</text>
    </g>\n`;
  }

  svg += `</svg>\n`;
  return svg;
}

// Generate the full suite of visual proof artifacts
const specs = [
  { file: '01_scale_before_100pct.svg', title: 'Phase 1: Scale 100% (Sub-pixel 4.8px cars)', mode: 'before', theme: 'dark', zoom: 1.0 },
  { file: '02_scale_after_100pct_2x.svg', title: 'Phase 2: Scale 100% (2x Default + Min 8px Clamp)', mode: 'after', theme: 'dark', zoom: 1.0, scaleMultiplier: 2.0 },
  { file: '03_scale_after_350pct_3x.svg', title: 'Phase 2: Scale 350% Zoom (3x Max Exaggeration)', mode: 'after', theme: 'dark', zoom: 3.5, scaleMultiplier: 3.0 },
  { file: '04_contrast_before_dark.svg', title: 'Phase 1: Low Contrast Dark Road & Paint (2.07:1)', mode: 'before', theme: 'dark', zoom: 1.0 },
  { file: '05_contrast_after_dark.svg', title: 'Phase 2: High Contrast Cyan/Amber + Halos (5.6:1)', mode: 'after', theme: 'dark', zoom: 1.0, scaleMultiplier: 2.0 },
  { file: '06_contrast_after_light.svg', title: 'Phase 2: Light Mode Road Contrast + Dark Outlines', mode: 'after', theme: 'light', zoom: 1.0, scaleMultiplier: 2.0 },
  { file: '07_draw_order_before_flyover_overlap.svg', title: 'Phase 1: Buggy Draw Order (Surface over Flyover)', mode: 'before', theme: 'dark', zoom: 1.2 },
  { file: '08_draw_order_after_seethrough_flyover.svg', title: 'Phase 2: Ghosted Flyover Deck (See-Through ON)', mode: 'after', theme: 'dark', zoom: 1.2, seeThroughFlyover: true, scaleMultiplier: 2.0 },
  { file: '09_tooltip_and_camera_follow.svg', title: 'Phase 2: Interactive Hover Tooltip & Follow Camera', mode: 'after', theme: 'dark', zoom: 1.2, selectedVehId: 'flow_orr_n.3', scaleMultiplier: 2.0 },
  { file: '10_heavy_demand_seed101_replay.svg', title: 'Phase 2: Heavy Demand Seed 101 Replay Verification', mode: 'after', theme: 'dark', zoom: 1.0, scaleMultiplier: 2.0 },
];

for (const s of specs) {
  const content = renderVisualSvg(s);
  const targetPath = path.join(outDir, s.file);
  fs.writeFileSync(targetPath, content, 'utf8');
  console.log(`Generated: ${s.file}`);
}

console.log(`Successfully generated ${specs.length} visual verification artifacts in docs/artifacts/phase2/`);
