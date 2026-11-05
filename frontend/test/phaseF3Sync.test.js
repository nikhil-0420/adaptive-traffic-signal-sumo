import test, { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  POLICIES,
  POLICY_PROVENANCE,
  DEFAULT_POLICY_ID,
  getPolicyConfig,
  getPolicyProvenance
} from '../src/utils/policyConstants.js';
import {
  SCENARIOS,
  DEMAND_LEVELS,
  AMENDMENT_3_CONDITIONS
} from '../src/utils/scenarioConstants.js';
import {
  explainDecision,
  getDecisionCodeLabel
} from '../src/utils/explainDecision.js';
import {
  SMOKE_DEV_META,
  SMOKE_PAIRED_SUMMARY,
  SMOKE_WIN_TIE_LOSS,
  SMOKE_OVERLOADED_CELLS
} from '../src/data/smokeDevEvidence.js';
import { DEMO_REPLAYS } from '../src/utils/replayConstants.js';

describe('Phase F3: Frontend Sync with Final Backend Study Matrix', () => {
  describe('Task 1: Policy selector & Provenance Badges', () => {
    it('defaults to hybrid_queue_adaptive (proposed policy)', () => {
      assert.equal(DEFAULT_POLICY_ID, 'hybrid_queue_adaptive');
      const def = getPolicyConfig(DEFAULT_POLICY_ID);
      assert.equal(def.id, 'hybrid_queue_adaptive');
      assert.equal(def.provenance, 'MEASURED');
      assert.equal(def.role, 'proposed');
      assert.equal(def.isBenchmarkOnly, false);
    });

    it('contains all 7 main policies with correct provenance', () => {
      const expected7 = [
        'fixed',
        'webster_measured',
        'webster_recalc',
        'sumo_actuated',
        'adaptive',
        'queue_extension',
        'hybrid_queue_adaptive'
      ];
      for (const pid of expected7) {
        const p = getPolicyConfig(pid);
        assert.ok(p, `Policy ${pid} should be defined`);
        assert.equal(p.provenance, 'MEASURED', `Policy ${pid} should have MEASURED provenance`);
      }
    });

    it('contains ablation policy hybrid_oracle_seeded with ORACLE-SEEDED provenance', () => {
      const p = getPolicyConfig('hybrid_oracle_seeded');
      assert.equal(p.provenance, 'ORACLE-SEEDED');
      assert.equal(p.role, 'ablation');
    });

    it('marks oracle policies as benchmark only', () => {
      const oraclePolicies = ['fixed_webster', 'fixed_matched_cycle'];
      for (const op of oraclePolicies) {
        const p = getPolicyConfig(op);
        assert.equal(p.provenance, 'ORACLE');
        assert.equal(p.isBenchmarkOnly, true);
        assert.ok(p.badge.includes('BENCHMARK'));
      }
    });

    it('includes dropped learned policy rl_dqn with LEARNED provenance', () => {
      const p = getPolicyConfig('rl_dqn');
      assert.equal(p.provenance, 'LEARNED');
      assert.equal(p.badge, 'DROPPED');
    });
  });

  describe('Task 2: Scenario selector & Descriptions', () => {
    it('includes all 3 non-stationary scenarios with 1-line descriptions from docs/SCENARIOS.md', () => {
      const nonStationary = ['ramp_peak', 'surge_shift', 'lane_closure'];
      for (const scId of nonStationary) {
        const sc = SCENARIOS.find((s) => s.id === scId);
        assert.ok(sc, `Scenario ${scId} should exist`);
        assert.equal(sc.isNonStationary, true);
        assert.equal(typeof sc.description, 'string');
        assert.ok(sc.description.length > 15);
      }
    });

    it('defines 3 demand levels: low (0.70x), medium (1.00x), heavy (1.30x)', () => {
      assert.equal(DEMAND_LEVELS.find((d) => d.id === 'low')?.multiplier, 0.7);
      assert.equal(DEMAND_LEVELS.find((d) => d.id === 'medium')?.multiplier, 1.0);
      assert.equal(DEMAND_LEVELS.find((d) => d.id === 'heavy')?.multiplier, 1.3);
    });

    it('defines the 6 representative Amendment 3 conditions', () => {
      assert.equal(AMENDMENT_3_CONDITIONS.length, 6);
      const conditionIds = AMENDMENT_3_CONDITIONS.map((c) => c.id);
      assert.ok(conditionIds.includes('balanced-low'));
      assert.ok(conditionIds.includes('balanced-heavy'));
      assert.ok(conditionIds.includes('imbalanced_orr-heavy'));
      assert.ok(conditionIds.includes('ramp_peak-medium'));
      assert.ok(conditionIds.includes('surge_shift-medium'));
      assert.ok(conditionIds.includes('lane_closure-medium'));
    });
  });

  describe('Task 3: Decision Panel Reason Code Lookup', () => {
    it('maps known reason codes to concise human labels', () => {
      assert.equal(getDecisionCodeLabel('QUEUE_DRAIN'), 'Queue-Length Extension');
      assert.equal(getDecisionCodeLabel('GAP_OUT'), 'Early Gap-Out Terminated');
      assert.equal(getDecisionCodeLabel('MAX_GREEN'), 'Maximum Green Ceiling Reached');
      assert.equal(getDecisionCodeLabel('EMERGENCY_PREEMPT'), 'Emergency Preemption Granted');
      assert.equal(getDecisionCodeLabel('BASE_MIN'), 'Baseline Green Entry');
    });

    it('falls back to raw code for unknown reason codes', () => {
      assert.equal(getDecisionCodeLabel('UNKNOWN_NEW_CODE_XYZ'), 'UNKNOWN_NEW_CODE_XYZ');
      assert.equal(getDecisionCodeLabel(''), 'Decision Evaluated');
    });

    it('explains decision with proposed vs applied action and delta_g', () => {
      const decision = {
        t: 45.0,
        axis: 'NS',
        reason_code: 'QUEUE_DRAIN',
        reason: 'North approach queue 18.5m exceeds clearance threshold',
        proposed_action: 'EXTEND_3S',
        applied_action: 'EXTEND_3S',
        delta_g_req_s: 3.0,
        delta_g_app_s: 3.0,
        g_extra_s: 6.0,
      };
      const explained = explainDecision(decision);
      assert.equal(explained.code, 'QUEUE_DRAIN');
      assert.equal(explained.codeLabel, 'Queue-Length Extension');
      assert.equal(explained.proposedAction, 'EXTEND_3S');
      assert.equal(explained.appliedAction, 'EXTEND_3S');
      assert.equal(explained.deltaGReqS, 3.0);
      assert.equal(explained.deltaGAppS, 3.0);
      assert.equal(explained.gExtraS, 6.0);
      assert.ok(explained.prose.includes('North approach queue'));
    });
  });

  describe('Task 6: Research / Evidence View Smoke Preview', () => {
    it('loads verified smoke dev metadata with dev smoke tag', () => {
      assert.equal(SMOKE_DEV_META.experimentId, 'exp_final_smoke_dev');
      assert.equal(SMOKE_DEV_META.isFinal, false);
      assert.ok(SMOKE_DEV_META.note.toLowerCase().includes('dev smoke replay, not final results'));
      assert.deepEqual(SMOKE_DEV_META.seeds, [101, 102]);
    });

    it('contains paired bootstrap differences vs webster_measured', () => {
      assert.ok(SMOKE_PAIRED_SUMMARY.length > 0);
      const p95Row = SMOKE_PAIRED_SUMMARY.find(
        (r) => r.comparator === 'webster_measured' && r.metric === 'p95_wait_s'
      );
      assert.ok(p95Row);
      assert.equal(p95Row.is_primary, 'True');
      assert.ok(p95Row.ci_95_low);
      assert.ok(p95Row.ci_95_high);
    });

    it('contains Win/Tie/Loss condition map', () => {
      assert.ok(Object.keys(SMOKE_WIN_TIE_LOSS).length >= 6);
      assert.ok(SMOKE_WIN_TIE_LOSS['balanced_heavy']);
      assert.ok(SMOKE_WIN_TIE_LOSS['balanced_heavy'].outcome.includes('TIE'));
    });

    it('contains overloaded cells list', () => {
      assert.ok(SMOKE_OVERLOADED_CELLS.length > 0);
      const first = SMOKE_OVERLOADED_CELLS[0];
      assert.ok(first.run_id);
      assert.ok(first.det_full_frac);
    });
  });

  describe('Task 7: Demo Replay Picker', () => {
    it('provides exactly 3 dev-seed replays covering balanced, imbalanced, and ramp_peak', () => {
      assert.equal(DEMO_REPLAYS.length, 3);
      const scenarios = DEMO_REPLAYS.map((r) => r.scenario);
      assert.ok(scenarios.includes('balanced'));
      assert.ok(scenarios.includes('imbalanced_orr'));
      assert.ok(scenarios.includes('ramp_peak'));
      for (const r of DEMO_REPLAYS) {
        assert.equal(r.badge, 'dev smoke replay, not final results');
      }
    });
  });
});
