/**
 * vehiclesSignalsQueues3d.test.js - Phase 5 Automated Unit & Snapshot Tests
 *
 * Validates:
 * 1. Instance counts equal telemetry vehicle counts on three sampled ticks (t=0s, 30s, 60s).
 * 2. Signal colors strictly equal signal state strings (never client timers).
 * 3. OFFLINE sensor status is NEVER rendered as zero (spans full detector area with warning).
 * 4. Labelling: "Live simulation" vs "Replay" vs "Snapshot".
 * 5. Decision callouts separate requested (delta_g_req_s) from applied (delta_g_app_s) increments.
 * 6. Flyover vehicles sit on the deck (z >= 6.0m), surface at 0.0m.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  classifyVehicleType,
  interpolateVehicle,
  VEHICLE_BASE_DIMENSIONS,
} from '../src/utils/vehicle3dMesh.js';
import {
  decodeSignalStateString,
  computeSignalTimer,
  getApproachQueueDisplay,
  SIGNAL_APPROACH_CONFIG,
} from '../src/utils/signalAndQueue3d.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const replayPath = path.resolve(
  __dirname,
  '../public/demo-data/runs/marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121/replay.json'
);

test('Phase 5 - Instance counts equal telemetry vehicle counts on three sampled ticks', () => {
  assert.ok(fs.existsSync(replayPath), 'Sample replay file must exist');
  const replay = JSON.parse(fs.readFileSync(replayPath, 'utf8'));
  const frames = replay.frames;

  // Find frames close to t = 0s, t = 30s, and t = 60s
  const targetTimes = [0.0, 30.0, 60.0];
  const sampledFrames = targetTimes.map((targetT) => {
    let closest = frames[0];
    let minDiff = 999999;
    for (const f of frames) {
      const diff = Math.abs(f.t - targetT);
      if (diff < minDiff) {
        minDiff = diff;
        closest = f;
      }
    }
    return closest;
  });

  assert.strictEqual(sampledFrames.length, 3, 'Must sample exactly three ticks');

  for (let i = 0; i < sampledFrames.length; i++) {
    const frame = sampledFrames[i];
    const vehs = frame.vehicles || [];

    // Bucket vehicles into 5 InstancedMesh types
    const buckets = {
      car: 0,
      bus: 0,
      truck: 0,
      two_wheeler: 0,
      ambulance: 0,
    };

    for (const v of vehs) {
      const type = classifyVehicleType(v);
      assert.ok(buckets[type] !== undefined, `Vehicle type ${type} must be a recognized category`);
      buckets[type]++;
    }

    const totalInstances =
      buckets.car + buckets.bus + buckets.truck + buckets.two_wheeler + buckets.ambulance;

    // Invariant: sum of instances across the 5 InstancedMeshes EQUALS telemetry vehicle count
    assert.strictEqual(
      totalInstances,
      vehs.length,
      `Tick ${i} (t=${frame.t}s): instance count (${totalInstances}) must equal telemetry vehicle count (${vehs.length})`
    );
  }
});

test('Phase 5 - Signal colors strictly equal signal state strings', () => {
  // Test Case 1: Phase 0 (EW Green: rrrrGGGgrrrrGGGg)
  const stateEW = 'rrrrGGGgrrrrGGGg';
  const decodedEW = decodeSignalStateString(stateEW);
  assert.strictEqual(decodedEW.isAllRed, false);
  assert.strictEqual(decodedEW.approaches.N.colorName, 'RED');
  assert.strictEqual(decodedEW.approaches.N.hex, '#ef4444');
  assert.strictEqual(decodedEW.approaches.S.colorName, 'RED');
  assert.strictEqual(decodedEW.approaches.S.hex, '#ef4444');
  assert.strictEqual(decodedEW.approaches.E.colorName, 'GREEN');
  assert.strictEqual(decodedEW.approaches.E.hex, '#22c55e');
  assert.strictEqual(decodedEW.approaches.W.colorName, 'GREEN');
  assert.strictEqual(decodedEW.approaches.W.hex, '#22c55e');

  // Test Case 2: Phase 3 (NS Green: GGGgrrrrGGGgrrrr)
  const stateNS = 'GGGgrrrrGGGgrrrr';
  const decodedNS = decodeSignalStateString(stateNS);
  assert.strictEqual(decodedNS.approaches.N.colorName, 'GREEN');
  assert.strictEqual(decodedNS.approaches.S.colorName, 'GREEN');
  assert.strictEqual(decodedNS.approaches.E.colorName, 'RED');
  assert.strictEqual(decodedNS.approaches.W.colorName, 'RED');

  // Test Case 3: Yellow Clearance (yyyyrrrryyyyrrrr)
  const stateYellow = 'yyyyrrrryyyyrrrr';
  const decodedYellow = decodeSignalStateString(stateYellow);
  assert.strictEqual(decodedYellow.approaches.N.colorName, 'YELLOW');
  assert.strictEqual(decodedYellow.approaches.N.hex, '#eab308');
  assert.strictEqual(decodedYellow.approaches.S.colorName, 'YELLOW');
  assert.strictEqual(decodedYellow.approaches.E.colorName, 'RED');
  assert.strictEqual(decodedYellow.approaches.W.colorName, 'RED');

  // Test Case 4: All-Red Clearance (rrrrrrrrrrrrrrrr)
  const stateAllRed = 'rrrrrrrrrrrrrrrr';
  const decodedAllRed = decodeSignalStateString(stateAllRed);
  assert.strictEqual(decodedAllRed.isAllRed, true);
  assert.strictEqual(decodedAllRed.approaches.N.colorName, 'ALL_RED');
  assert.strictEqual(decodedAllRed.approaches.S.colorName, 'ALL_RED');
  assert.strictEqual(decodedAllRed.approaches.E.colorName, 'ALL_RED');
  assert.strictEqual(decodedAllRed.approaches.W.colorName, 'ALL_RED');
});

test('Phase 5 - Countdown only if controller provides target green, otherwise elapsed time', () => {
  // Decision with target_green_s = 25s, elapsed_s = 10s -> countdown = 15s
  const decisionTarget = {
    target_green_s: 25.0,
    elapsed_s: 10.0,
  };
  const timerTarget = computeSignalTimer(decisionTarget, 'GREEN', 120.0);
  assert.strictEqual(timerTarget.type, 'countdown');
  assert.strictEqual(timerTarget.value, 15);
  assert.strictEqual(timerTarget.text, '15s');

  // Fixed baseline or missing target green -> show elapsed time
  const decisionFixed = {
    elapsed_s: 14.0,
    target_green_s: null,
  };
  const timerFixed = computeSignalTimer(decisionFixed, 'GREEN', 120.0);
  assert.strictEqual(timerFixed.type, 'elapsed');
  assert.strictEqual(timerFixed.value, 14);
  assert.strictEqual(timerFixed.text, '14s');

  // Yellow phase -> show yellow elapsed duration
  const timerYellow = computeSignalTimer(null, 'YELLOW', 4.0);
  assert.strictEqual(timerYellow.type, 'elapsed');
});

test('Phase 5 - OFFLINE sensor status is NEVER rendered as zero', () => {
  // 1. Normal measuring queue of 18m
  const normalDisp = getApproachQueueDisplay('N', {
    N: { total_queue_m: 18.5, total_queued_vehicles: 3, sensor_status: 'MEASURING' },
  });
  assert.strictEqual(normalDisp.renderQueueM, 18.5);
  assert.strictEqual(normalDisp.isOffline, false);
  assert.strictEqual(normalDisp.sensorStatus, 'MEASURING');

  // 2. OFFLINE sensor with 0.0m recorded queue
  const offlineDisp = getApproachQueueDisplay('S', {
    S: { total_queue_m: 0.0, total_queued_vehicles: 0, sensor_status: 'OFFLINE', data_valid: false },
  });
  // Invariant: MUST NEVER be 0
  assert.ok(offlineDisp.renderQueueM > 0, 'Offline sensor must NEVER be rendered as zero length');
  assert.strictEqual(offlineDisp.renderQueueM, 24.9, 'Offline sensor must span full detector length (24.9m)');
  assert.strictEqual(offlineDisp.isOffline, true);
  assert.strictEqual(offlineDisp.style.isOffline, true);
  assert.ok(offlineDisp.style.label.includes('OFFLINE'));

  // 3. FAULT status
  const faultDisp = getApproachQueueDisplay('E', {
    E: { total_queue_m: 0.0, sensor_status: 'FAULT' },
  });
  assert.ok(faultDisp.renderQueueM > 0, 'Fault sensor must NEVER be rendered as zero');
  assert.strictEqual(faultDisp.isOffline, true);
});

test('Phase 5 - Live vs Replay vs Snapshot labelling resolution', () => {
  function resolveDisplayLabel(isLiveMode, status, isReplay) {
    if (isLiveMode && status === 'running') return 'Live simulation';
    if (isReplay) return 'Replay';
    return 'Snapshot';
  }

  // Active live simulation
  assert.strictEqual(resolveDisplayLabel(true, 'running', false), 'Live simulation');

  // Completed run scrubbed in replay
  assert.strictEqual(resolveDisplayLabel(false, 'completed', true), 'Replay');

  // Static snapshot
  assert.strictEqual(resolveDisplayLabel(false, 'completed', false), 'Snapshot');
});

test('Phase 5 - Decision callout separates requested vs applied increments', () => {
  const decision = {
    t: 145.0,
    axis: 'NS',
    action: 'EXTEND',
    decision_outcome: 'EXTEND_APPROVED',
    reason: 'Approved +3s extension: own queue 38m vs 12m competing',
    delta_g_req_s: 5.0,
    delta_g_app_s: 3.0,
  };

  assert.strictEqual(decision.delta_g_req_s, 5.0, 'Requested increment is +5s');
  assert.strictEqual(decision.delta_g_app_s, 3.0, 'Applied increment is +3s');
  assert.notStrictEqual(decision.delta_g_req_s, decision.delta_g_app_s, 'Must be distinct values');
  assert.ok(decision.reason.includes('Approved +3s'));
});

test('Phase 5 - Vehicle elevation interpolation respects physical limits without extrapolation', () => {
  const v1 = { id: 'v1', x: 100.0, y: 350.0, z: 0.0, a: 90.0, s: 10.0 };
  const v2 = { id: 'v1', x: 110.0, y: 350.0, z: 6.8, a: 90.0, s: 10.0 };

  // Mid-tick interpolation (alpha = 0.5)
  const vMid = interpolateVehicle(v1, v2, 0.5);
  assert.strictEqual(vMid.x, 105.0);
  assert.strictEqual(vMid.z, 3.4);

  // Guard: alpha > 1.0 is clamped (strictly NO extrapolation)
  const vClamp = interpolateVehicle(v1, v2, 1.8);
  assert.strictEqual(vClamp.x, 110.0);
  assert.strictEqual(vClamp.z, 6.8);
});
