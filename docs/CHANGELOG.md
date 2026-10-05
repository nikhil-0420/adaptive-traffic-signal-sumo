# Changelog

## v0.3 - real BTP fixed-time baseline (Marathalli Bridge Junction)
- Replaced placeholder 30/30 fixed-time plan with verified BTP timing: "Marathalli Bridge Junction, Airport Police Station – FIXED" (Varthur Rd × Outer Ring Rd Jn), weekday 08:00–11:30 (Phase 1 = 110 s, Phase 2 = 100 s, exclusive pedestrian = 15 s, cycle = 225 s) from OpenCity / BTP (`docs/btp_marathalli_yamlur.pdf`, page 10).
- Modelling decisions:
  1. Phase 1 mapped to NS axis and Phase 2 mapped to EW axis (adopting BTP's timing structure onto the junction).
  2. Clearance intervals: Subtracted yellow (3 s) and all-red (2 s) from phase durations dynamically via `config.TIMING`, yielding `FIXED.green_ns_s = 105 s` and `FIXED.green_ew_s = 95 s`.
  3. Pedestrian phase: 15 s exclusive pedestrian phase is not modelled; modelled cycle is 210 s vs 225 s real.
  4. Old 30/30 plan preserved in `config.py` as `FIXED_PLACEHOLDER`.
- Updated `test_fixed_green_is_constant` in `tests/test_core.py` to assert NS == 105 s and EW == 95 s.

## v0.2 - two lanes per approach (found by checking queue symmetry before the demo)
Problem found: with identical demand and identical green on all four approaches (balanced scenario, fixed plan), queues were
lopsided in v0.1 (single lane per approach): mean queue N 59 m, S 17 m, E 36 m, W 19 m (3 seeds).
Cause (tested): permissive left-turners blocking the single shared lane. With left turns removed, queues were symmetric
(N 9.9, S 9.0, E 8.1, W 8.8 m). It affected both policies equally (paired comparison stayed valid) but inflated absolute numbers.
Fix: 2 lanes per approach (lane 0 right+straight, lane 1 left+straight), one detector per lane, approach queue = max over lanes,
demand x1.7 (DEMAND_SCALE) so the junction is loaded comparably.
Check after fix (12 seeds, balanced, fixed): N 17.6, S 18.4, E 17.9, W 22.7 m; gaps scatter around zero.
New regression test: test_no_systematic_approach_bias_in_balanced_demand.
Effect on results: surge_north went from -9.8% (adaptive worse) to +1.0%; imbalanced gains rose from ~52% to ~63%.
Lesson for the report: validate the simulation model (symmetry, conservation) before trusting controller comparisons.

## v0.1 - first scaffold (single lane per approach), 11 tests.
