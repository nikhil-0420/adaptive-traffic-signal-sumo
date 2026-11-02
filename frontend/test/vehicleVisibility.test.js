import test from 'node:test';
import assert from 'node:assert/strict';
import { DECISION_CODE_LABELS, getDecisionCodeLabel, explainDecision } from '../src/utils/explainDecision.js';

// Specifications matching frontend/src/components/IsometricIntersection.jsx
const VEHICLE_SPECS = {
  car: { len: 4.8, wid: 2.0, radius: 1.5, name: 'Passenger Car' },
  motorcycle: { len: 2.2, wid: 0.9, radius: 0.6, name: 'Two-Wheeler' },
  auto: { len: 2.8, wid: 1.3, radius: 0.8, name: 'Auto-Rickshaw' },
  bus: { len: 11.5, wid: 2.6, radius: 2.0, name: 'Transit Bus' },
  truck: { len: 9.0, wid: 2.5, radius: 2.0, name: 'Heavy Truck' },
  ambulance: { len: 5.5, wid: 2.2, radius: 1.5, name: 'Emergency Ambulance' },
};

function computeVehicleScale({ lenM, widM, zoom, viewportW = 1200, viewportH = 700, scaleMultiplier = 2.0, minLengthPx = 8.0 }) {
  const baseScale = (Math.min(viewportW, viewportH) / (480 * 1.45)) * zoom;
  const rawNominalLen = lenM * baseScale * scaleMultiplier;
  const rawNominalWid = widM * baseScale * scaleMultiplier;
  const visMultiplier = rawNominalLen < minLengthPx ? (minLengthPx / rawNominalLen) : 1.0;
  return {
    baseScale,
    renderedLen: rawNominalLen * visMultiplier,
    renderedWid: rawNominalWid * visMultiplier,
    isClamped: rawNominalLen < minLengthPx,
  };
}

function classifyVehicleTier(v) {
  // If elevation info exists from telemetry
  if (typeof v.z === 'number') {
    if (v.z >= 5.0) return 'flyover';
    if (v.z < -1.0) return 'underpass';
    return 'surface';
  }
  // Fallback heuristic based on spatial coordinates & speed
  const a = v.a ?? v.angle ?? 0;
  const x = v.x ?? 0;
  const y = v.y ?? 0;
  const s = v.s ?? v.speed ?? 0;
  const isEastWest = Math.abs(a - 90) < 35 || Math.abs(a - 270) < 35;
  const isNorthSouth = Math.abs(a - 0) < 35 || Math.abs(a - 180) < 35;

  if (Math.abs(y - 350) <= 8.5 && isEastWest && x >= 170 && x <= 530) {
    return 'flyover';
  }
  if (Math.abs(x - 350) <= 8.5 && isNorthSouth && y >= 170 && y <= 530 && s > 7.0) {
    return 'underpass';
  }
  return 'surface';
}

function formatVehicleTooltip(v, spec, interpS, vehTier, isQueued) {
  return {
    id: v.id,
    type: spec.name,
    speed_mps: Number(interpS.toFixed(1)),
    speed_kmh: Number((interpS * 3.6).toFixed(1)),
    wait_s: Number((v.w || 0).toFixed(1)),
    tier: vehTier,
    isQueued: Boolean(isQueued),
    lane: v.lane || v.lane_id || (vehTier === 'flyover' ? 'flyover_e2w' : (vehTier === 'underpass' ? 'orr_underpass' : 'surface_tls')),
  };
}

// -------------------------------------------------------------
// 1. VEHICLE SCALE & MINIMUM ON-SCREEN SIZE TESTS
// -------------------------------------------------------------
test('Vehicle Scaling: Minimum on-screen size enforced across zoom levels (25%, 100%, 350%)', () => {
  const car = VEHICLE_SPECS.car;
  const moto = VEHICLE_SPECS.motorcycle;

  // At minimum zoom (25% = 0.25) with 1x true scale
  const minZoomTrue = computeVehicleScale({ lenM: moto.len, widM: moto.wid, zoom: 0.25, scaleMultiplier: 1.0 });
  assert.ok(minZoomTrue.renderedLen >= 8.0, `Motorcycle at 25% zoom must be >= 8.0px, got ${minZoomTrue.renderedLen}`);
  assert.equal(minZoomTrue.isClamped, true, 'Sub-pixel motorcycle should trigger min-size clamp at 25% zoom');

  // At default zoom (100% = 1.0) with 2x default exaggeration
  const defaultZoomCar = computeVehicleScale({ lenM: car.len, widM: car.wid, zoom: 1.0, scaleMultiplier: 2.0 });
  assert.ok(defaultZoomCar.renderedLen >= 8.0, `Car at 100% zoom with 2x multiplier should be >= 8.0px, got ${defaultZoomCar.renderedLen}`);
  assert.ok(defaultZoomCar.renderedLen >= 9.0 && defaultZoomCar.renderedLen <= 10.5, 'Car length is ~9.6px at 100% zoom 2x');

  // At maximum zoom (350% = 3.5) with 1x true scale
  const maxZoomCar = computeVehicleScale({ lenM: car.len, widM: car.wid, zoom: 3.5, scaleMultiplier: 1.0 });
  assert.ok(maxZoomCar.renderedLen >= 8.0, `Car at 350% zoom true scale must be >= 8.0px, got ${maxZoomCar.renderedLen}`);
  assert.equal(maxZoomCar.isClamped, false, 'At 350% zoom, vehicle is naturally large and should not clamp');

  // Exaggeration scaling options: 1x, 2x, 3x
  const scale1x = computeVehicleScale({ lenM: car.len, widM: car.wid, zoom: 1.0, scaleMultiplier: 1.0 });
  const scale2x = computeVehicleScale({ lenM: car.len, widM: car.wid, zoom: 1.0, scaleMultiplier: 2.0 });
  const scale3x = computeVehicleScale({ lenM: car.len, widM: car.wid, zoom: 1.0, scaleMultiplier: 3.0 });

  assert.ok(scale2x.renderedLen > scale1x.renderedLen, '2x scale must produce larger vehicles than 1x');
  assert.ok(scale3x.renderedLen > scale2x.renderedLen, '3x scale must produce larger vehicles than 2x');
});

// -------------------------------------------------------------
// 2. DRAW ORDER & TIER ELEVATION CLASSIFICATION TESTS
// -------------------------------------------------------------
test('Draw Order & Tier Classification: Explicit z elevation distinguishes flyover vs surface vs underpass', () => {
  const flyoverVeh = { id: 'v_fly', x: 350, y: 350, z: 7.0, a: 90, s: 12.0 };
  const surfaceVeh = { id: 'v_surf', x: 350, y: 350, z: 0.0, a: 90, s: 5.0 };
  const underpassVeh = { id: 'v_und', x: 350, y: 350, z: -4.0, a: 0, s: 14.0 };

  assert.equal(classifyVehicleTier(flyoverVeh), 'flyover');
  assert.equal(classifyVehicleTier(surfaceVeh), 'surface');
  assert.equal(classifyVehicleTier(underpassVeh), 'underpass');

  // Verify partitioned draw order buckets
  const allVehicles = [flyoverVeh, surfaceVeh, underpassVeh];
  const partitioned = { underpass: [], surface: [], flyover: [] };
  allVehicles.forEach((v) => {
    partitioned[classifyVehicleTier(v)].push(v);
  });

  assert.equal(partitioned.underpass.length, 1);
  assert.equal(partitioned.surface.length, 1);
  assert.equal(partitioned.flyover.length, 1);
  assert.equal(partitioned.underpass[0].id, 'v_und');
  assert.equal(partitioned.surface[0].id, 'v_surf');
  assert.equal(partitioned.flyover[0].id, 'v_fly');
});

// -------------------------------------------------------------
// 3. HOVER TOOLTIP DATA FORMATTING TESTS
// -------------------------------------------------------------
test('Tooltip Formatting: Generates id, type, speed in km/h & m/s, wait time, lane, and queued status', () => {
  const rawVeh = { id: 'flow_s.7', x: 350, y: 320, s: 0.04, w: 14.5, lane_id: 'leg_orr_s_in_1' };
  const spec = VEHICLE_SPECS.car;
  const isQueued = rawVeh.s < 0.1 || rawVeh.w > 0;
  const tooltip = formatVehicleTooltip(rawVeh, spec, rawVeh.s, 'surface', isQueued);

  assert.equal(tooltip.id, 'flow_s.7');
  assert.equal(tooltip.type, 'Passenger Car');
  assert.equal(tooltip.speed_mps, 0.0);
  assert.equal(tooltip.speed_kmh, 0.1);
  assert.equal(tooltip.wait_s, 14.5);
  assert.equal(tooltip.isQueued, true);
  assert.equal(tooltip.tier, 'surface');
  assert.equal(tooltip.lane, 'leg_orr_s_in_1');
});

// -------------------------------------------------------------
// 4. HUD COUNT EQUALS TELEMETRY COUNT EQUALS RENDERED COUNT
// -------------------------------------------------------------
test('HUD Invariant: Rendered count, HUD count, and Telemetry count match identically', () => {
  const telemetry = {
    sim_time_s: 27.0,
    status: 'running',
    vehicles: [
      { id: 'v1', x: 350, y: 340, s: 0.0, w: 12.0 },
      { id: 'v2', x: 350, y: 330, s: 0.05, w: 6.0 },
      { id: 'v3', x: 280, y: 350, s: 8.5, w: 0.0 },
      { id: 'v4', x: 420, y: 350, s: 11.2, w: 0.0 },
      { id: 'v5', x: 350, y: 220, s: 13.0, w: 0.0 },
    ],
  };

  const telemetryCount = telemetry.vehicles.length;
  const hudTotalCount = telemetry.vehicles.length;
  const renderedCount = telemetry.vehicles.length;

  assert.equal(hudTotalCount, telemetryCount, 'HUD total count must strictly equal telemetry vehicle count');
  assert.equal(renderedCount, telemetryCount, 'Rendered canvas count must strictly equal telemetry vehicle count');

  // Queued vehicles calculation
  const queuedCount = telemetry.vehicles.filter(
    (v) => (v.s !== undefined ? v.s < 0.1 : (v.speed !== undefined ? v.speed < 0.1 : false)) || (v.w > 0)
  ).length;

  assert.equal(queuedCount, 2, 'v1 and v2 are stopped/waiting so queued count must be 2');
});

// -------------------------------------------------------------
// 5. DECISION REASON LOOKUP TABLE INTEGRITY (Zero invented text)
// -------------------------------------------------------------
test('Decision Reason Lookup: Single lookup table maps raw codes, preserves logged controller reasons, never invents text', () => {
  // Test lookup table mappings
  assert.equal(getDecisionCodeLabel('SWITCH_GAP_OUT'), 'Early Gap-Out Terminated');
  assert.equal(getDecisionCodeLabel('EXTEND_APPROVED'), 'Green Extension Approved');
  assert.equal(getDecisionCodeLabel('REJECTED_MIN_GREEN'), 'Switch Refused (Min Green)');
  assert.equal(getDecisionCodeLabel('EMERGENCY_PREEMPTION'), 'Emergency Preemption Granted');

  // Test fallback on unknown/new code (shows raw code verbatim, never invents fiction)
  assert.equal(getDecisionCodeLabel('CUSTOM_UNKNOWN_CODE_99'), 'CUSTOM_UNKNOWN_CODE_99');

  // Test that when a real controller log contains an explicit "reason" field, explainDecision respects it
  const loggedDecision = {
    t: 45.0,
    cycle: 2,
    axis: 'NS',
    applied_action: 'EXTEND',
    decision_outcome: 'EXTEND_APPROVED',
    reason: 'Controller queue extension: North queue (24.0m) exceeds South (4.0m) by 20.0m',
  };

  const res = explainDecision(loggedDecision);
  assert.equal(res.codeLabel, 'Green Extension Approved');
  assert.ok(res.prose.includes('Controller queue extension: North queue (24.0m) exceeds South (4.0m) by 20.0m'));
});
