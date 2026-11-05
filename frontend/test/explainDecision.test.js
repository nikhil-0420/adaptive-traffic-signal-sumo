import test from 'node:test';
import assert from 'node:assert/strict';
import { explainDecision, collapseHolds } from '../src/utils/explainDecision.js';

test('explainDecision: GAP_OUT generates outcome first, reason second, plain language without >=', () => {
  const decision = {
    t: 37.0,
    cycle: 2,
    axis: 'EW',
    applied_action: 'GAP_OUT',
    decision_outcome: 'SWITCH_GAP_OUT',
    elapsed_s: 17.0,
    q_active_m: 0.0,
    q_competing_m: 5.0,
    gap_out_elapsed_s: 3.0
  };

  const res = explainDecision(decision);
  assert.equal(res.codeLabel, 'Ended green early (no cars waiting)');
  assert.equal(res.type, 'gap_out');
  assert.ok(res.prose.startsWith('Terminated east–west green'), 'Outcome must be stated first');
  assert.ok(res.prose.includes('Zero vehicles were detected for 3.0 s'), 'Reason with units');
  assert.ok(res.prose.includes('5.0 m'), 'Includes opposing queue with units');
  assert.ok(!res.prose.includes('>='), 'Prose must not contain >=');
  assert.ok(!res.prose.includes('≥'), 'Prose must not contain ≥');
});

test('explainDecision: EXTEND generates added green time with headroom and opposing queue', () => {
  const decision = {
    t: 25.0,
    cycle: 1,
    axis: 'NS',
    applied_action: 'EXTEND',
    decision_outcome: 'EXTEND_APPROVED',
    delta_g_app_s: 3.0,
    target_green_s: 18.0,
    elapsed_s: 15.0,
    q_active_m: 24.0,
    q_competing_m: 5.0
  };

  const res = explainDecision(decision);
  assert.equal(res.codeLabel, 'Added green time');
  assert.equal(res.type, 'extend');
  assert.ok(res.prose.includes('Added 3.0 s to north–south green'), 'Outcome stated with units');
  assert.ok(res.prose.includes('18.0 s of a 60 s maximum'), 'Target and ceiling with units');
  assert.ok(res.prose.includes('24.0 m of queue'), 'Active queue with units');
  assert.ok(res.prose.includes('5.0 m'), 'Competing queue with units');
  assert.ok(!res.prose.includes('>='), 'Prose must not contain >=');
});

test('explainDecision: SWITCH refused (minimum green floor)', () => {
  const decision = {
    t: 8.0,
    cycle: 1,
    axis: 'NS',
    applied_action: 'HOLD',
    decision_outcome: 'REJECTED_MIN_GREEN',
    elapsed_s: 8.0
  };

  const res = explainDecision(decision);
  assert.equal(res.codeLabel, 'Switch refused (minimum green not reached)');
  assert.equal(res.type, 'rejected');
  assert.ok(res.prose.includes('Maintained north–south green'));
  assert.ok(res.prose.includes('8.0 s is below the mandatory safety minimum of 10 s'));
});

test('explainDecision: ENTER_GREEN baseline start', () => {
  const decision = {
    t: 20.0,
    cycle: 1,
    axis: 'EW',
    applied_action: 'ENTER_GREEN',
    decision_outcome: 'BASELINE_ENTRY',
    target_green_s: 15.0
  };

  const res = explainDecision(decision);
  assert.equal(res.codeLabel, 'Started green');
  assert.equal(res.type, 'enter');
  assert.ok(res.prose.includes('Initiated green phase for east–west with a baseline allocation of 15.0 s'));
});

test('explainDecision: EMERGENCY priority preemption', () => {
  const decision = {
    t: 85.0,
    cycle: 3,
    axis: 'NS',
    applied_action: 'EMERGENCY_PREEMPT',
    decision_outcome: 'EMERGENCY_PREEMPTION',
    is_emergency: true
  };

  const res = explainDecision(decision);
  assert.equal(res.codeLabel, 'Emergency vehicle priority');
  assert.equal(res.type, 'emergency');
  assert.ok(res.prose.includes('Granted immediate green to north–south priority route'));
  assert.ok(res.prose.includes('all-red safety buffer'));
});

test('collapseHolds: correctly collapses consecutive HOLD records into single updating line', () => {
  const rawDecisions = [
    { t: 1.0, cycle: 0, axis: 'NS', action: 'HOLD', decision_outcome: 'HOLD', elapsed_s: 1.0 },
    { t: 2.0, cycle: 0, axis: 'NS', action: 'HOLD', decision_outcome: 'HOLD', elapsed_s: 2.0 },
    { t: 3.0, cycle: 0, axis: 'NS', action: 'HOLD', decision_outcome: 'HOLD', elapsed_s: 3.0 },
    { t: 4.0, cycle: 0, axis: 'NS', action: 'EXTEND', decision_outcome: 'EXTEND_APPROVED', delta_g_app_s: 3.0, target_green_s: 18.0, q_active_m: 10.0, q_competing_m: 2.0 }
  ];

  const collapsed = collapseHolds(rawDecisions);
  assert.equal(collapsed.length, 2, 'Must collapse 3 holds into 1, plus 1 extend = 2 items');
  assert.ok(collapsed[0].isCollapsedHold);
  assert.equal(collapsed[0].holdCount, 3);
  assert.ok(collapsed[0].explained.prose.includes('Keeping north–south green: 3.0 s so far, waiting for a gap'));
  assert.equal(collapsed[1].isCollapsedHold, false);
  assert.equal(collapsed[1].explained.type, 'extend');
});

test('explainDecision: archived cycle-audit schema maps to "Chose 13 s of green: own queue 20 m vs 5 m" with n/a delta', () => {
  const archivedDecision = {
    t: 45.0,
    cycle: 4,
    axis: 'EW',
    green_s: 16.0,
    actual_green_s: 13.0,
    q_N_m: 5.0,
    q_S_m: 0.0,
    q_E_m: 20.0,
    q_W_m: 0.0
  };

  const res = explainDecision(archivedDecision);
  assert.equal(res.codeLabel, 'Cycle allocation');
  assert.equal(res.type, 'cycle_choice');
  assert.equal(res.headline, 'Chose 13 s of green');
  assert.equal(res.prose, 'Chose 13 s of green: own queue 20 m vs 5 m on north–south.');
  assert.equal(res.deltaS, 'n/a');
  assert.equal(res.targetS, 13);
});
