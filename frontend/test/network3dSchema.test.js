import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const network3dPath = path.resolve(__dirname, '../public/network3d.json');

test('Network3D Schema - File exists and is well under 3 MB', () => {
  assert.ok(fs.existsSync(network3dPath), 'frontend/public/network3d.json must exist');
  const stat = fs.statSync(network3dPath);
  const sizeMb = stat.size / (1024 * 1024);
  assert.ok(sizeMb < 3.0, `File size ${sizeMb.toFixed(2)} MB must be under 3.0 MB target`);
  assert.ok(stat.size > 50000, `File size ${stat.size} bytes is unexpectedly small`);
});

test('Network3D Schema - Provenance block and modelled elevation source', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const prov = data.provenance;
  assert.ok(prov, 'Must have provenance block');
  assert.strictEqual(prov.elevation_source, 'modelled_config', 'elevation_source must be modelled_config');
  assert.ok(
    prov.elevation_disclaimer.includes('never survey data'),
    'Disclaimer must state elevation is a modelling assumption, never survey data'
  );
  assert.ok(prov.source_net_file.includes('marathahalli.net.xml'), 'Source net file path required');
  assert.ok(prov.source_detector_file.includes('detectors.add.xml'), 'Source detector path required');
  assert.ok(prov.source_tllogic_file.includes('marathahalli.tll.xml'), 'Source tllogic path required');
  assert.ok(prov.sumo_version.length > 0, 'SUMO version required');
  assert.ok(prov.git_commit.length > 0, 'Git commit required');
  assert.strictEqual(prov.polyline_simplification.tolerance_m, 0.0, 'Default tolerance must be 0.0 (lossless)');
});

test('Network3D Schema - Coordinate transform and bounding box', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const bounds = data.bounds;
  assert.ok(bounds, 'Must have bounds block');
  assert.deepStrictEqual(bounds.bbox_sumo.min, [0, 0, 0]);
  assert.deepStrictEqual(bounds.bbox_sumo.max, [700, 700, 7]);
  assert.deepStrictEqual(bounds.center, [350, 350, 3.5]);
  assert.strictEqual(bounds.controlled_junction.id, 'marathahalli_tls');
  assert.deepStrictEqual(bounds.controlled_junction.coord, [350, 332, 0]);

  const xform = data.coordinate_transform;
  assert.ok(xform, 'Must have coordinate_transform');
  assert.strictEqual(xform.scale, 1.0, '1 unit = 1 metre');
  assert.strictEqual(xform.unit, 'metre');
  assert.strictEqual(xform.matrix_sumo_to_threejs_y_up.length, 16, 'Three.js 4x4 matrix');
  assert.strictEqual(xform.matrix_sumo_to_scene_z_up.length, 16, 'Scene 4x4 matrix');
});

test('Network3D Schema - Lanes structure and 3D polylines', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const lanes = data.lanes;
  assert.ok(Array.isArray(lanes) && lanes.length >= 160, 'Must have >= 160 lanes (normal + internal)');

  for (const lane of lanes) {
    assert.ok(lane.id, 'Lane id required');
    assert.ok(lane.edge_id, 'Edge id required');
    assert.ok(Array.isArray(lane.polyline) && lane.polyline.length >= 2, `Lane ${lane.id} polyline must have >=2 points`);
    assert.ok(lane.width > 0, 'Width must be positive');
    assert.ok(Array.isArray(lane.allowed_vehicle_classes) && lane.allowed_vehicle_classes.length > 0, 'Allowed classes required');
    assert.ok(lane.speed_limit > 0, 'Speed limit must be positive');
    assert.ok(lane.length > 0, 'Length must be positive');

    for (const pt of lane.polyline) {
      assert.strictEqual(pt.length, 3, `Point in lane ${lane.id} must be [x, y, z]`);
      assert.ok(typeof pt[0] === 'number' && typeof pt[1] === 'number' && typeof pt[2] === 'number');
    }
  }
});

test('Network3D Schema - Junctions shape polygons with z', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const junctions = data.junctions;
  assert.strictEqual(junctions.length, 16, 'Must export exactly 16 junctions');

  const juncMap = new Map(junctions.map((j) => [j.id, j]));
  assert.ok(juncMap.has('marathahalli_tls'));
  assert.strictEqual(juncMap.get('marathahalli_tls').coord[2], 0.0);
  assert.strictEqual(juncMap.get('node_bridge_w').coord[2], 6.5);
  assert.strictEqual(juncMap.get('node_bridge_mid').coord[2], 7.0);
  assert.strictEqual(juncMap.get('node_bridge_e').coord[2], 6.5);

  for (const j of junctions) {
    assert.ok(j.shape.length >= 3, `Junction ${j.id} must have >= 3 polygon points`);
    for (const pt of j.shape) {
      assert.strictEqual(pt.length, 3, `Junction shape point must be [x, y, z]`);
    }
  }
});

test('Network3D Schema - Controlled connections at marathahalli_tls match Starting Prompt', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const conns = data.connections;
  assert.strictEqual(conns.length, 16, 'Must have exactly 16 controlled connections');

  for (let i = 0; i < 16; i++) {
    const c = conns[i];
    assert.strictEqual(c.link_index, i, `Link index must be ${i}`);
    if (i < 4) {
      assert.strictEqual(c.approach, 'N');
      assert.strictEqual(c.from_edge, 'leg_orr_n_in');
      assert.strictEqual(c.phase_group, 'NS');
      assert.strictEqual(c.tls_phases['3'].toUpperCase(), 'G', 'NS green in phase 3');
      assert.strictEqual(c.tls_phases['0'].toLowerCase(), 'r', 'NS red in phase 0');
    } else if (i < 8) {
      assert.strictEqual(c.approach, 'E');
      assert.strictEqual(c.from_edge, 'leg_wf_in');
      assert.strictEqual(c.phase_group, 'EW');
      assert.strictEqual(c.tls_phases['0'].toUpperCase(), 'G', 'EW green in phase 0');
      assert.strictEqual(c.tls_phases['3'].toLowerCase(), 'r', 'EW red in phase 3');
    } else if (i < 12) {
      assert.strictEqual(c.approach, 'S');
      assert.strictEqual(c.from_edge, 'leg_orr_s_in');
      assert.strictEqual(c.phase_group, 'NS');
      assert.strictEqual(c.tls_phases['3'].toUpperCase(), 'G', 'NS green in phase 3');
      assert.strictEqual(c.tls_phases['0'].toLowerCase(), 'r', 'NS red in phase 0');
    } else {
      assert.strictEqual(c.approach, 'W');
      assert.strictEqual(c.from_edge, 'leg_hal_in');
      assert.strictEqual(c.phase_group, 'EW');
      assert.strictEqual(c.tls_phases['0'].toUpperCase(), 'G', 'EW green in phase 0');
      assert.strictEqual(c.tls_phases['3'].toLowerCase(), 'r', 'EW red in phase 3');
    }
  }
});

test('Network3D Schema - E2 Detectors coverage and 3D span', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const dets = data.detectors;
  assert.strictEqual(dets.length, 8, 'Must have 8 E2 detectors');

  for (const d of dets) {
    assert.strictEqual(d.pos, -25.0);
    assert.strictEqual(d.endPos, -0.1);
    assert.strictEqual(d.length_m, 24.9);
    assert.ok(['N', 'E', 'S', 'W'].includes(d.approach));
    assert.strictEqual(d.polyline.length, 2);
    const p1 = d.polyline[0];
    const p2 = d.polyline[1];
    const dist = Math.hypot(p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]);
    assert.ok(Math.abs(dist - 24.9) < 0.1, `Detector span must be ~24.9m, got ${dist.toFixed(2)}m`);
  }
});

test('Network3D Schema - Flyover/Bypass classification and deck heights', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const fb = data.flyover_bypass;
  assert.ok(fb);
  assert.strictEqual(fb.elevated_edges.length, 4, '4 elevated deck edges');
  for (const e of fb.elevated_edges) {
    assert.ok(e.deck_height_m >= 6.5 && e.deck_height_m <= 7.0);
  }
  assert.strictEqual(fb.ramp_edges.length, 12, '12 ramp edges');
  assert.strictEqual(fb.mainline_edges.length, 2, '2 mainline underpass edges');
  assert.strictEqual(fb.slip_roads.length, 4, '4 channelized slip roads');
});

test('Network3D Schema - Validation invariants: continuity, monotonicity, crossings', () => {
  const data = JSON.parse(fs.readFileSync(network3dPath, 'utf8'));
  const val = data.validation;
  assert.ok(val);
  assert.strictEqual(val.polyline_continuity.status, 'PASS');
  assert.strictEqual(val.polyline_continuity.gaps_above_5mm, 0);
  assert.ok(val.polyline_continuity.max_gap_m < 0.005);

  assert.strictEqual(val.ramp_z_monotonicity.status, 'PASS');
  assert.strictEqual(val.ramp_z_monotonicity.all_monotone, true);

  assert.strictEqual(val.lane_crossings.normal_edges_same_z_count, 0, 'Normal edges must have 0 same-z crossings');
  assert.strictEqual(val.lane_crossings.normal_edges_diff_z_count, 41, 'Normal edges have 41 grade-separated crossings');
  assert.strictEqual(val.starting_prompt_mapping.status, 'PASS');
  assert.strictEqual(val.starting_prompt_mapping.mismatch_count, 0);
  assert.strictEqual(val.file_size.status, 'PASS');
});
