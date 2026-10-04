# Changelog

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
