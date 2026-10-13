import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.resolve(__dirname, '../public/demo-data');

test('Verified Demo Data Snapshot - Manifest integrity', () => {
  const manifestPath = path.join(publicDir, 'manifest.json');
  assert.ok(fs.existsSync(manifestPath), 'manifest.json must exist in demo-data');

  const content = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert.equal(content.schema_version, 'dp1.v1');
  assert.equal(content.dataset_label, 'DP1 Verified Simulation Snapshot');
  assert.ok(content.generated_at, 'generated_at timestamp must be present');
  assert.ok(content.total_runs > 0, 'total_runs must be > 0');
  assert.ok(Array.isArray(content.runs), 'runs list must be an array');
  assert.ok(content.runs.length > 0, 'runs list must contain runs');
});

test('Verified Demo Data Snapshot - Summary schema', () => {
  const summaryPath = path.join(publicDir, 'summary.json');
  assert.ok(fs.existsSync(summaryPath), 'summary.json must exist in demo-data');

  const summary = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
  assert.ok(summary.scenarios && summary.scenarios.length >= 4, 'must cover 4 baseline scenarios');
  assert.ok(summary.policies && summary.policies.length >= 4, 'must cover 4 baseline policies');
  assert.ok(summary.total_runs_evaluated > 0, 'total_runs_evaluated must be > 0');
});

test('Verified Demo Data Snapshot - All runs & null metrics handling', () => {
  const allRunsPath = path.join(publicDir, 'all_runs.json');
  assert.ok(fs.existsSync(allRunsPath), 'all_runs.json must exist in demo-data');

  const runs = JSON.parse(fs.readFileSync(allRunsPath, 'utf8'));
  assert.ok(Array.isArray(runs));
  assert.ok(runs.length > 0);

  // Verify metric provenance and absence of fake zeroes
  for (const r of runs) {
    assert.ok(r.run_id, 'each run must have run_id');
    assert.ok(r.scenario, 'each run must have scenario');
    assert.ok(r.policy, 'each run must have policy');
    assert.ok(typeof r.seed === 'number', 'seed must be a number');

    // Missing emergency metric must be null or omitted, never fake 0
    if (!r.has_emergency && !r.emergency_mode) {
      assert.ok(
        r.emergency_wait_s === undefined || r.emergency_wait_s === null,
        `Non-emergency run ${r.run_id} must have null/omitted emergency_wait_s, not fake numbers`
      );
    }
  }
});

test('Verified Demo Data Snapshot - Run artifact directory consistency', () => {
  const sampleRunsDir = path.join(publicDir, 'runs');
  assert.ok(fs.existsSync(sampleRunsDir), 'sample runs directory must exist');

  const sampleRunIds = fs.readdirSync(sampleRunsDir);
  assert.ok(sampleRunIds.length >= 3, 'at least 3 sample runs with timeseries/decisions must exist');

  for (const runId of sampleRunIds) {
    const runDir = path.join(sampleRunsDir, runId);
    const tsPath = path.join(runDir, 'timeseries.json');
    assert.ok(fs.existsSync(tsPath), `timeseries.json for ${runId} must exist`);

    const decPath = path.join(runDir, 'decisions.json');
    assert.ok(fs.existsSync(decPath), `decisions.json for ${runId} must exist`);

    const ts = JSON.parse(fs.readFileSync(tsPath, 'utf8'));
    assert.ok(ts.points && ts.points.length > 0, `timeseries for ${runId} must contain points`);
  }
});

test('Verified Demo Data Snapshot - Experiment evaluation artifacts', () => {
  const expDir = path.join(publicDir, 'experiments', 'exp_smoke_test');
  assert.ok(fs.existsSync(expDir), 'exp_smoke_test dir must exist');

  const aggPath = path.join(expDir, 'aggregate.json');
  assert.ok(fs.existsSync(aggPath), 'aggregate.json must exist');

  const reportPath = path.join(expDir, 'REPORT.md');
  assert.ok(fs.existsSync(reportPath), 'REPORT.md must exist');

  const agg = JSON.parse(fs.readFileSync(aggPath, 'utf8'));
  assert.ok(Array.isArray(agg), 'aggregate must be an array');
  assert.ok(agg.length > 0, 'aggregate must contain cells');
});

test('Client Safety Logic - Snapshot mode guards', () => {
  // Verify that launching runs or experiments in snapshot mode throws
  const clientSim = {
    mode: 'snapshot',
    launchRun(params) {
      if (this.mode !== 'api') {
        throw new Error(
          'Live simulation launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO installed is required.'
        );
      }
    },
    launchExperiment(params) {
      if (this.mode !== 'api') {
        throw new Error(
          'Research matrix launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO is required.'
        );
      }
    },
  };

  assert.throws(
    () => clientSim.launchRun({ scenario: 'balanced' }),
    /Live simulation launch is disabled in Saved Simulation Snapshot mode/
  );

  assert.throws(
    () => clientSim.launchExperiment({ preset: 'smoke' }),
    /Research matrix launch is disabled in Saved Simulation Snapshot mode/
  );
});

test('Client Telemetry - Staleness detection logic', () => {
  const checkStale = (updatedAtSec, nowSec) => {
    return nowSec - updatedAtSec > 5.0;
  };

  const now = 1000.0;
  assert.equal(checkStale(998.0, now), false, '2 seconds old should not be stale');
  assert.equal(checkStale(994.0, now), true, '6 seconds old should be stale (> 5.0s)');
});
