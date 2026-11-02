import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient } from '../src/api/client.js';
import { explainDecision } from '../src/utils/explainDecision.js';

test('Live Run → Review Handoff: Decisions > 0, Vehicles > 0, Deduplication & Timeline mapping', async () => {
  const client = new ApiClient();

  // 1. Simulate a live run with decisions, extensions, and vehicle frames
  const runId = 'live_imbalanced_orr_hybrid_queue_adaptive_s121';
  const liveRunData = {
    run_id: runId,
    scenario: 'imbalanced_orr',
    policy: 'hybrid_queue_adaptive',
    seed: 121,
    decisions: [
      {
        t: 0,
        cycle: 0,
        axis: 'NS',
        applied_action: 'ENTER_GREEN',
        decision_outcome: 'BASELINE_ENTRY',
        elapsed_s: 0,
        target_green_s: 15.0,
        g_base_s: 15.0,
        q_active_m: 14.5,
        q_competing_m: 6.2
      },
      {
        t: 15.0,
        cycle: 0,
        axis: 'NS',
        applied_action: 'EXTEND',
        decision_outcome: 'EXTEND_APPROVED',
        delta_g_app_s: 3.0,
        target_green_s: 18.0,
        q_active_m: 22.0,
        q_competing_m: 5.0
      },
      // Intentionally duplicated event at t=15s to verify store-level deduplication
      {
        t: 15.0,
        cycle: 0,
        axis: 'NS',
        applied_action: 'EXTEND',
        decision_outcome: 'EXTEND_APPROVED',
        delta_g_app_s: 3.0,
        target_green_s: 18.0,
        q_active_m: 22.0,
        q_competing_m: 5.0
      },
      {
        t: 27.0,
        cycle: 0,
        axis: 'NS',
        applied_action: 'GAP_OUT',
        decision_outcome: 'SWITCH_GAP_OUT',
        elapsed_s: 27.0,
        target_green_s: 27.0,
        q_active_m: 0.0,
        q_competing_m: 28.5
      },
      {
        t: 30.0,
        cycle: 0,
        axis: 'EW',
        applied_action: 'ENTER_GREEN',
        decision_outcome: 'BASELINE_ENTRY',
        elapsed_s: 0,
        target_green_s: 15.0,
        q_active_m: 28.5,
        q_competing_m: 0.0
      },
      {
        t: 45.0,
        cycle: 0,
        axis: 'EW',
        applied_action: 'EXTEND',
        decision_outcome: 'EXTEND_APPROVED',
        delta_g_app_s: 3.0,
        target_green_s: 18.0,
        q_active_m: 18.0,
        q_competing_m: 12.0
      }
    ],
    replay: {
      run_id: runId,
      total_frames: 2,
      frames: [
        {
          t: 0,
          phase: 'GREEN',
          axis: 'NS',
          vehicles: [
            { id: 'veh_0', x: 350, y: 500, z: 0, speed: 12.5, angle: 180 },
            { id: 'veh_1', x: 350, y: 200, z: 0, speed: 11.0, angle: 0 }
          ]
        },
        {
          t: 15.0,
          phase: 'GREEN',
          axis: 'NS',
          vehicles: [
            { id: 'veh_0', x: 350, y: 380, z: 0, speed: 8.0, angle: 180 },
            { id: 'veh_1', x: 350, y: 320, z: 0, speed: 0.0, angle: 0 },
            { id: 'veh_2', x: 500, y: 350, z: 0, speed: 0.0, angle: 270 }
          ]
        }
      ]
    }
  };

  // 2. Persist the live run into recorded-run store
  const saved = client.saveLiveRun(liveRunData);
  assert.ok(saved, 'Run should be saved into liveRunStore');
  assert.equal(saved.status, 'completed', 'Run status must be completed');

  // 3. Query getDecisions for the live run
  const decisionsRes = await client.getDecisions(runId);
  assert.ok(decisionsRes.total_decisions > 0, 'Total decisions must be > 0');
  // 6 events minus 1 duplicate = 5 unique decisions
  assert.equal(decisionsRes.decisions.length, 5, 'Deduplication by (time, axis, type, run) must remove duplicate at t=15');

  // 4. Verify decisions on both timeline lanes (NS and EW)
  const nsDecisions = decisionsRes.decisions.filter(d => String(d.axis).toUpperCase() === 'NS');
  const ewDecisions = decisionsRes.decisions.filter(d => String(d.axis).toUpperCase() === 'EW');
  assert.ok(nsDecisions.length > 0, 'North-South lane must have timeline decisions drawn');
  assert.ok(ewDecisions.length > 0, 'East-West lane must have timeline decisions drawn');

  // 5. Query getReplay for the live run and assert vehicle trajectories
  const replayRes = await client.getReplay(runId);
  assert.ok(replayRes, 'Replay data must not be null');
  assert.ok(replayRes.frames && replayRes.frames.length > 0, 'Replay frames must be > 0');
  const totalVehicles = replayRes.frames.reduce((sum, f) => sum + (f.vehicles ? f.vehicles.length : 0), 0);
  assert.ok(totalVehicles > 0, 'Replay must contain active vehicle trajectories (> 0 vehicles)');

  // 6. Verify explanation prose doesn't show 0 for n/a delta
  const explainedExtend = explainDecision(decisionsRes.decisions[1]);
  assert.equal(explainedExtend.deltaS, 3.0);
  assert.match(explainedExtend.prose, /Added 3\.0 s to north–south green/);
});
