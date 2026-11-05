import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('Geometry Validation Overlay - Vehicles align within SUMO lane polygons', () => {
  const geomPath = path.resolve(__dirname, '../src/data/marathahalli_geometry.json');
  assert.ok(fs.existsSync(geomPath), 'marathahalli_geometry.json must exist');

  const geom = JSON.parse(fs.readFileSync(geomPath, 'utf8'));
  assert.ok(geom.lanes.length > 50, 'Must have exported lanes');
  assert.ok(geom.detectors.length === 8, 'Must have 8 E2 detectors');
  assert.ok(geom.stop_lines.length === 8, 'Must have 8 approach stop lines');

  // Load recorded replay run
  const replayPath = path.resolve(
    __dirname,
    '../public/demo-data/runs/marathahalli_imbalanced_orr_medium_hybrid_queue_adaptive_s121/replay.json'
  );
  assert.ok(fs.existsSync(replayPath), 'replay.json must exist');
  const replay = JSON.parse(fs.readFileSync(replayPath, 'utf8'));

  function pointToSegmentDist(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
    t = Math.max(0, Math.min(1, t));
    const cx = x1 + t * dx;
    const cy = y1 + t * dy;
    return Math.hypot(px - cx, py - cy);
  }

  function minDistToAnyLane(px, py) {
    let minD = 999999;
    for (const lane of geom.lanes) {
      const pts = lane.shape;
      const halfW = (lane.width || 3.2) / 2.0;
      for (let i = 0; i < pts.length - 1; i++) {
        const d = pointToSegmentDist(px, py, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]);
        const laneD = Math.max(0, d - halfW);
        if (laneD < minD) minD = laneD;
      }
    }
    return minD;
  }

  let totalVehicles = 0;
  let insideVehicles = 0;

  // Validate across sample frames (first 50 frames)
  for (const frame of replay.frames.slice(0, 50)) {
    for (const v of frame.vehicles) {
      totalVehicles++;
      const dist = minDistToAnyLane(v.x, v.y);
      if (dist <= 0.5) {
        insideVehicles++;
      }
    }
  }

  assert.ok(totalVehicles > 100, `Expected at least 100 vehicles tested, got ${totalVehicles}`);
  const insideRatio = insideVehicles / totalVehicles;
  assert.ok(
    insideRatio >= 0.99,
    `Expected >=99% vehicles inside lane polygons, got ${(insideRatio * 100).toFixed(2)}% (${insideVehicles}/${totalVehicles})`
  );
});
