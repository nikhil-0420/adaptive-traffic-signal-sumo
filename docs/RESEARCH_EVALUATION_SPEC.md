# DP1 Research & Evaluation — Implementation Specification

This is a required product feature, not just a report-writing requirement. Antigravity must implement the complete pipeline from configuration and SUMO runs through raw artifacts, aggregation, API endpoints, React UI, downloads, tests, and reproducible documentation.

## 1. Research questions

1. How do `fixed`, `fixed_webster`, `adaptive`, `pressure`, and trained `rl_dqn` compare under different traffic demand levels and four demand-pattern archetypes?
2. Are differences consistent across paired random seeds, or are apparent gains driven by one seed/scenario?
3. How do mean waiting time, tail waiting time, queues, throughput, completion rate, and per-direction service disparity trade off?
4. When emergency priority is enabled for the same ambulance event, how much does emergency delay change and what happens to ordinary traffic?

Keep statements bounded to SUMO simulation findings on the synthetic four-way junction. This study is not evidence of real-road performance.

## 2. Experimental factors

### Scenario patterns

Preserve and extend the existing patterns without renaming them:

- `balanced`
- `imbalanced_ns`
- `imbalanced_ew`
- `surge_north`

### Demand levels

Add a `demand_level` parameter to the current scenario/run pipeline, centralized in `dp1/config.py`:

| Level | Initial multiplier | Meaning |
|---|---:|---|
| `low` | 0.70 | Lower arrival rates relative to the current synthetic profile |
| `medium` | 1.00 | Exact current configured arrival rates; backward-compatible default |
| `heavy` | 1.30 | Higher arrival rates relative to the current synthetic profile |

Treat these as tunable experiment settings, not calibrated real-world traffic labels. `medium` must preserve current route-generation rates when the parameter is omitted or set to `medium`. `fixed_webster` must calculate its plan from the actual scaled profile for the selected pattern and demand level, not from the unscaled scenario by accident.

### Policies

Primary matrix: `fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`. The DQN model path and checksum/ID must be explicit in the manifest. If no trained model is available, do not silently skip the RL condition: mark it `blocked`/`not_run`, make the overall matrix partial, and explain what is missing.

### Seed split

- Existing `TRAIN_SEEDS = (1, 2, 3, 4, 5)` remain for existing tuning/training unless a specific training split is documented.
- Add `RL_VALIDATION_SEEDS = (6, 7, 8, 9, 10)` for checkpoint selection/hyperparameter decisions.
- Preserve the existing `HELD_OUT_SEEDS = (11, 12, 13, 14, 15)` and current CLI behaviour for compatibility.
- Add `RESEARCH_EVAL_SEEDS = (21, 22, 23, 24, 25, 26, 27, 28, 29, 30)` as the fresh final research test set.

Freeze all controller parameters and the chosen DQN model before running the 21–30 research matrix. Never use those final test results for model or parameter selection. Record the seed split and any deviations in every experiment manifest/report.

## 3. Matrix sizes and run modes

### Primary controller matrix

`4 patterns × 3 demand levels × 5 policies × 10 seeds = 600 policy runs`.

Add these execution options (exact CLI flags can follow current project conventions):

- `--preset smoke`: a tiny deterministic subset to verify the pipeline quickly.
- `--dry-run`: print the planned cells and expected run count without running SUMO.
- `--resume`: skip only cells whose successful artifacts and hashes validate against the active experiment configuration.
- `--limit` or equivalent: run a bounded number of remaining cells for development.
- `--jobs`: use the current parallel execution seam, with no shared-output collisions or unsafe TraCI port reuse.
- `--out-dir` / experiment ID: save to a unique `results/research/<experiment_id>/` directory.

A full run must be chunkable and resumable. Every requested matrix cell must end in an explicit status: `pending`, `running`, `complete`, `failed`, `blocked`, or `skipped`. The experiment itself is `complete` only when every requested cell has a valid successful result; otherwise it must say `partial` or `failed` and explain why.

### Emergency-priority matrix

Run a separately identified paired study:

`2 patterns (balanced, surge_north) × 3 demand levels × 3 policies (fixed, pressure, rl_dqn when trained) × 2 priority states × 10 seeds = 360 runs`.

The same condition/seed must use exactly the same ordinary-vehicle departures/routes and ambulance event in priority-off and priority-on variants. If deterministic route pairing requires separate output files, compare/store content hashes to prove ordinary traffic is unchanged. If the DQN isn't trained, mark those cells blocked rather than substituting another controller.

## 4. Reproducible pairing and artifacts

For every condition defined by `(pattern, demand_level, seed)`, route generation must be deterministic. All policies in that condition must receive identical background arrivals, IDs, routes, and departure times. Store a vehicle manifest that maps each vehicle ID to origin approach and whether it is the emergency vehicle. Store route-file hash(es) in each run row/manifest so pairing can be audited.

Write each experiment under:

```text
results/research/<experiment_id>/
  manifest.json
  config.json
  raw_runs.csv
  aggregate.csv
  paired_deltas.csv
  fairness_by_approach.csv
  fairness_by_direction.csv
  matrix_status.csv
  failures.jsonl
  plots/
  report.md
  report.pdf                 # if the existing exporter works
  logs/<cell_id>.log
  runs/<cell_id>/...         # per-run SUMO outputs
```

Adapt the names if the existing repository has a better naming pattern, but retain equivalent information. Never overwrite `results/baseline_pre_upgrade/`, prior research experiment folders, or historical artifacts. CSV/report generation must be deterministic for a given artifact set; never hand-edit measured output.

The manifest must include schema version, experiment ID, complete matrix dimensions, patterns/levels/multipliers/policies/seeds, actual CLI command/config, DQN model ID/path/checksum and training metadata when applicable, Python/SUMO/package versions, git commit when available, start/end timestamps, completed/failed/blocked counts, deterministic bootstrap seed and resample count, and a clear `complete` vs `partial` status. Store per-cell stdout/stderr/exit code and exception details.

## 5. Metric definitions

Keep current legacy metric column names and meanings intact. Add new names rather than silently redefining old ones.

| Metric | Definition / unit | Interpretation |
|---|---|---|
| `avg_wait_s` | Mean SUMO `waitingTime` among completed vehicles included by the current parser, seconds/vehicle | Lower is better; document population precisely |
| `avg_time_loss_s` | Mean SUMO `timeLoss`, seconds/vehicle | Lower is better; do not rename it “signal delay” |
| `avg_trip_s` | Mean completed trip duration, seconds/vehicle | Lower is generally better, read with completion rate |
| `p95_wait_s` | 95th percentile of vehicle `waitingTime` values used by the metric | Lower is better; report sample count |
| `avg_queue_m`, `max_queue_m` | Mean across recorded approach-by-time queue observations and observed maximum, metres | Lower is generally better; preserve legacy definition for existing CSVs |
| `throughput_veh_per_h` | Preserve the current calculation: number of completed vehicles whose SUMO arrival is within the demand window divided by demand-window hours | Higher is better; add `completed_in_demand_window` as an interpretable count |
| `completion_rate` | Completed trips / generated vehicles | Higher is better; include unfinished count |
| Per-approach wait | Mean and p95 completed-vehicle wait by origin approach N/S/E/W plus each sample count | Lower is better; null when no valid observations |
| Per-approach queue | Mean/max recorded detector queue by approach | Lower is generally better |
| Directional wait disparity | `abs(mean_wait_NS_origins - mean_wait_EW_origins)` over completed vehicles with known origin, seconds | Lower indicates more even observed waits; interpret beside demand and total wait |
| Approach wait gap | `max(per-approach mean wait) - min(per-approach mean wait)`, seconds, only when enough approach groups have data | Descriptive disparity; include per-approach counts and values |
| Emergency wait/time loss/trip duration/completion | Parsed from the actual ambulance's SUMO tripinfo plus completion state | Show only in emergency-enabled runs; include incomplete/timeout status. Label `timeLoss` as SUMO time loss, not a dispatch/real-world response-time measure. |
| Emergency priority effect | Paired priority-on minus priority-off delta in ambulance `waitingTime`, `timeLoss` and trip duration for the same pattern/level/seed/event | Negative delta favours priority for these delay metrics; also report change in ordinary-traffic outcomes |
| DQN reward | Logged training reward and components | Training diagnostic only; never mixed into traffic performance rankings |

Use the generated vehicle manifest for origin grouping; don't guess an origin from incomplete or ambiguous tripinfo fields. Incomplete vehicle wait summaries must not be presented as completed-trip wait; report incomplete counts explicitly. Missing subgroup observations are `null`, not `0`.

## 6. Statistical summary

For each `(pattern, demand_level, policy, metric)` condition, report valid seed count `n`, mean and sample standard deviation across seeds. Retain per-seed rows so every aggregate can be checked.

For each non-reference policy, create paired deltas against `fixed` for `avg_wait_s` and `avg_time_loss_s` (and optionally queue/throughput):

`delta_seed = candidate_metric(pattern, level, seed) - fixed_metric(same pattern, same level, same seed)`.

Calculate a 95% paired-bootstrap percentile interval by resampling the paired seed deltas, using a deterministic configurable bootstrap RNG seed and a documented resample count (default 10,000). Save the point estimate, lower/upper bounds, `n_pairs`, metric units and whether the interval is computable. For wait/time-loss, a negative delta favours the candidate; make that sign convention explicit in the table and chart. Missing pairs must be reported and excluded only with an explicit count; never silently substitute another seed or policy.

With ten test seeds, intervals are still estimates with limitations. Use them to show variation, not to make sweeping scientific claims. Don't equate a confidence interval with proof of real-world benefit, and don't use research test results to tune the controller.

## 7. Direction fairness report

Use origin-attributed completed vehicle records to report mean wait, p95 wait, and valid sample count for N, S, E, W; then aggregate origin N/S as NS and E/W as EW. Report directional waiting-time disparity and the approach wait gap for every policy and condition. Include demand rates/counts for each approach. Do not reduce fairness to one opaque score or optimize fairness disparity at the cost of severe total delay without showing the trade-off.

## 8. Generated research report

`report.md` must be generated from the immutable manifest plus raw run results and include:

1. Objective and simulated-system limitations.
2. Network, demand rates/multipliers, patterns, signal timings, policies, DQN model metadata, package versions and seed split.
3. Planned vs completed matrix size, missing/failed cells and whether the matrix is full or partial.
4. Metric definitions and exact sample populations.
5. Overall and per-condition mean ± standard deviation, paired per-seed differences and paired-bootstrap 95% intervals.
6. Per-approach and NS/EW fairness tables with sample counts.
7. Emergency priority off/on results and impact on ordinary traffic, if that experiment was run.
8. Plots with units, n, uncertainty and clear legend; raw and summary artifact paths.
9. Reproduction commands and caveats. Explicitly report cases where DQN or emergency priority is worse.

## 9. Required Research & Evaluation React workspace

Implement this as a real route/view in the React + Vite + JSX frontend, not merely a few charts on the overview page.

- **Experiment builder:** select smoke/full/custom preset, scenario patterns, demand levels, policies, seed set, model version and optional emergency sub-study. Show planned matrix size before launch. Require confirmation for a large full matrix; do not start work on page load.
- **Run queue/progress:** show experiment status, completed/total, running, failed, blocked and skipped cells; progress by matrix dimensions; allow polling while active and stop polling at terminal status. Show partial-run warnings and failure detail.
- **Results explorer:** filter by pattern, demand level, policy and metric. Show mean travel time (`avg_trip_s`), mean waiting time, throughput, queue length, emergency delay (`SUMO timeLoss`, with the exact label), emergency waiting/trip duration, paired priority-on/off deltas, `n` valid pairs, per-seed details, queue/time series where present and downloadable CSV/Markdown/PDF artifacts. Label what lower/higher means.
- **Fairness view:** compare N/S/E/W and NS/EW wait and queue data with sample counts; show directional disparity and approach wait gap with a short explanatory caption that considers demand imbalance.
- **Integrity cues:** visibly show model ID, seed set, demand multiplier, run timestamp, route hashes where useful, manifest completeness, API status and whether the UI is viewing a saved snapshot or a live-backed experiment.
- **Snapshot mode:** if API is missing, allow exploration of an explicitly generated snapshot of real result artifacts. Disable experiment-launch actions. Never fabricate research results to fill an empty screen.
- **Artifact export:** use safe API links for raw data, aggregate, paired deltas, fairness tables, manifest and report; the browser never chooses arbitrary filesystem paths.

## 10. Acceptance tests / definition of done

- Existing `pytest -q`, legacy run/compare/report commands, and all four existing policies still work.
- Default/medium route generation remains backwards-compatible; demand-level multipliers are config-driven and are represented in every run key and manifest.
- Same pattern/level/seed route hash is identical across policies; route hashes differ appropriately when the level changes.
- Dry-run reports exact expected cell count; smoke matrix runs; `--resume` skips only verified successful cells; failures remain inspectable; partial matrices remain partial.
- Train/validation/research-test splits are enforced and printed in the manifest.
- Metric unit tests cover tripinfo parsing, per-approach origin grouping, null subgroups, waiting disparity, p95, throughput window, unfinished counts, paired delta calculation and deterministic bootstrap intervals.
- The report and dashboard agree on aggregates; a value can be traced to raw rows and seed IDs.
- API tests cover creation/status/progress/results/artifact links, unknown IDs, request allowlists, safe artifact resolution, invalid matrix size, cancellation if implemented, and stale/failing workers.
- The React Research & Evaluation page is responsive and usable with successful, empty, partially failed, missing-DQN, stale, disconnected and large-matrix states.
- Final validation records exact commands, artifact paths, pass/fail output and limitations. No unsupported claim that AI always wins or that simulation proves real-world gains.
