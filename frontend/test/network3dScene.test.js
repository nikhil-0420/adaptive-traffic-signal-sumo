import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';

import {
  sumoToThree,
  threeToSumo,
  compileNetwork3DGeometries,
  auditBridgePillars,
  CAMERA_PRESETS,
  isWebGLAvailable,
} from '../src/utils/network3dGeometry.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const network3dPath = path.resolve(__dirname, '../public/network3d.json');

test('3D Coordinate Transforms - 1 unit = 1 metre bidirectional mapping', () => {
  // Center maps to origin
  const centerThree = sumoToThree(350, 350, 0);
  assert.deepStrictEqual(centerThree, [0, 0, 0]);

  // Controlled junction marathahalli_tls (y=332 -> Z=+18)
  const tlsThree = sumoToThree(350, 332, 0);
  assert.deepStrictEqual(tlsThree, [0, 0, 18]);

  // Bridge crest (z=7.0m -> Y=+7)
  const crestThree = sumoToThree(350, 350, 7);
  assert.deepStrictEqual(crestThree, [0, 7, 0]);

  // Bidirectional round-trip check
  const testCoords = [
    [100, 200, 0],
    [350, 350, 7.0],
    [520, 332, 6.5],
    [0, 700, 3.2],
  ];
  for (const [x, y, z] of testCoords) {
    const t = sumoToThree(x, y, z);
    const s = threeToSumo(t[0], t[1], t[2]);
    assert.ok(Math.abs(s[0] - x) < 1e-4, `X roundtrip failed for ${x}`);
    assert.ok(Math.abs(s[1] - y) < 1e-4, `Y roundtrip failed for ${y}`);
    assert.ok(Math.abs(s[2] - z) < 1e-4, `Z roundtrip failed for ${z}`);
  }
});

test('Mesh-Count Snapshot Test - Static geometry merges into exactly 8 categorized meshes', () => {
  assert.ok(fs.existsSync(network3dPath), 'network3d.json must exist');
  const networkData = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));

  const compiled = compileNetwork3DGeometries(networkData);
  assert.ok(compiled, 'Compilation must return valid geometry dictionary');

  // Verify non-empty BufferGeometry for each merged category
  const categories = [
    'surfaceRoads',
    'flyoverRoads',
    'underpassRoads',
    'markings',
    'junctions',
    'deckThickness',
    'barriers',
    'pillars',
  ];

  let validMeshCount = 0;
  for (const cat of categories) {
    const geom = compiled[cat];
    assert.ok(geom instanceof THREE.BufferGeometry, `Category ${cat} must be a BufferGeometry`);
    const count = geom.attributes.position ? geom.attributes.position.count : 0;
    assert.ok(count > 0, `Category ${cat} must have vertices (got ${count})`);
    validMeshCount++;
  }

  // Snapshot: exactly 8 static merged mesh layers
  assert.strictEqual(
    validMeshCount,
    8,
    `Expected exactly 8 merged static meshes for optimal draw-call performance, got ${validMeshCount}`
  );
});

test('Bridge Support Pillars - Geometric clearance audit and surface lane collisions', () => {
  const networkData = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const audit = auditBridgePillars(networkData);

  assert.strictEqual(audit.totalChecked, 9, 'Evaluated 9 regular grid stations');
  assert.strictEqual(audit.clearPillars.length, 6, '6 portal piers clear surface traffic (>10m away)');
  assert.strictEqual(audit.intersectingPillars.length, 3, '3 centerline piers intersect surface lanes');

  // Verify the 3 intersecting stations are X = -5, 0, +5
  const intersectingXs = audit.intersectingPillars.map((p) => p.threeX).sort((a, b) => a - b);
  assert.deepStrictEqual(intersectingXs, [-5, 0, 5]);

  // Verify they collide with the ORR mainline and surface legs
  for (const p of audit.intersectingPillars) {
    assert.ok(p.conflicts.length > 0, `Pillar at X=${p.threeX} must list conflicting lanes`);
    const conflictLaneIds = p.conflicts.map((c) => c.laneId);
    const hasOrrConflict = conflictLaneIds.some(
      (id) => id.includes('orr_mainline') || id.includes('leg_orr_n')
    );
    assert.ok(hasOrrConflict, `Pillar at X=${p.threeX} must conflict with ORR lanes`);
  }
});

test('Camera Presets - Four distinct viewing angles configured with target centers', () => {
  const requiredPresets = ['isoSW', 'isoNE', 'topDown', 'flyoverEye'];
  for (const key of requiredPresets) {
    const preset = CAMERA_PRESETS[key];
    assert.ok(preset, `Preset ${key} must exist`);
    assert.strictEqual(preset.position.length, 3, 'Position must have [x, y, z]');
    assert.strictEqual(preset.target.length, 3, 'Target must have [x, y, z]');
    assert.ok(preset.name, 'Preset must have human-readable title');
  }

  // Check top-down perspective (looking down Y axis)
  assert.strictEqual(CAMERA_PRESETS.topDown.position[0], 0);
  assert.ok(CAMERA_PRESETS.topDown.position[1] >= 140, 'Top-down must be high above scene');
  assert.strictEqual(CAMERA_PRESETS.topDown.target[1], 0);

  // Check flyover eye-level perspective
  assert.ok(CAMERA_PRESETS.flyoverEye.position[1] <= 15, 'Flyover eye-level must be close to deck height');
});

test('WebGL Context Lifecycle - Mounts, disposes, and cleans up without memory leak', () => {
  const networkData = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const compiled = compileNetwork3DGeometries(networkData);

  // Instantiate Three.js scene
  const scene = new THREE.Scene();
  const meshes = [];

  const mat = new THREE.MeshBasicMaterial({ color: 0x334155 });

  for (const [key, geom] of Object.entries(compiled)) {
    if (geom instanceof THREE.BufferGeometry) {
      const mesh = new THREE.Mesh(geom, mat);
      scene.add(mesh);
      meshes.push(mesh);
    }
  }

  assert.strictEqual(scene.children.length, 8, '8 meshes mounted in scene');

  // Simulate unmount and dispose all geometries & materials
  for (const mesh of meshes) {
    scene.remove(mesh);
    mesh.geometry.dispose();
  }
  mat.dispose();

  assert.strictEqual(scene.children.length, 0, 'All meshes cleanly removed on unmount');
});

test('WebGL Availability Guard - Function returns boolean and does not throw', () => {
  const available = isWebGLAvailable();
  assert.strictEqual(typeof available, 'boolean');
});
