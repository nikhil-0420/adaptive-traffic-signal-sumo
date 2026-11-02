import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('Operations KPI Strip - Binds to real evaluated aggregate numbers and resolves non-zero', () => {
  const aggPath = path.resolve(
    __dirname,
    '../public/demo-data/experiments/exp_marathahalli_hybrid_840/aggregate.json'
  );
  assert.ok(fs.existsSync(aggPath), 'aggregate.json must exist');
  const aggregateData = JSON.parse(fs.readFileSync(aggPath, 'utf8'));

  const selectedScenario = 'imbalanced_orr';
  const selectedDemand = 'medium';

  const hybridRow = aggregateData.find(
    (a) => a.pattern === selectedScenario && a.demand_level === selectedDemand && a.policy === 'hybrid_queue_adaptive'
  );
  const fixedRow = aggregateData.find(
    (a) => a.pattern === selectedScenario && a.demand_level === selectedDemand && a.policy === 'fixed'
  );

  assert.ok(hybridRow, 'Must have hybrid_queue_adaptive row');
  assert.ok(fixedRow, 'Must have fixed row');

  const fixedWait = fixedRow.avg_wait_s_mean;
  const hybridWait = hybridRow.avg_wait_s_mean;
  const delta = ((hybridWait - fixedWait) / fixedWait) * 100;
  const disparity = hybridRow.directional_wait_disparity_s_mean;
  const maxQueue = hybridRow.max_queue_m_mean;
  const throughput = hybridRow.throughput_veh_per_h_mean;

  // Real evaluated numbers verification
  assert.ok(delta < -5.0, `Delta must be reduction, got ${delta}%`);
  assert.ok(hybridWait > 35.0 && hybridWait < 55.0, `Hybrid wait must be around 42.9s, got ${hybridWait}`);
  assert.ok(disparity > 50.0, `Disparity must be > 50s, got ${disparity}`);
  assert.ok(maxQueue > 15.0 && maxQueue < 50.0, `Max queue must be real evaluated length (approx 23.5m), got ${maxQueue}`);
  assert.ok(throughput > 2000, `Throughput must be > 2000 vph, got ${throughput}`);

  // Test that neither delta, hybridWait, disparity, maxQueue nor throughput evaluates to 0.0
  assert.notEqual(Number(delta.toFixed(1)), 0.0);
  assert.notEqual(Number(hybridWait.toFixed(1)), 0.0);
  assert.notEqual(Number(disparity.toFixed(1)), 0.0);
  assert.notEqual(Number(maxQueue.toFixed(0)), 0);
  assert.notEqual(Number(throughput.toFixed(0)), 0);
});
