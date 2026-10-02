---
trigger: always_on
description: Never fabricate results; keep the comparison fair and the safety invariant intact
---
- Results must come from real runs of `python -m dp1.cli`. Never invent or hand-edit numbers, tables or plots.
- Sensors are simulated. The fixed-time plan is a placeholder until docs/SOURCES.md records a real BTP source.
- Every switch must be GREEN -> YELLOW -> ALL_RED -> GREEN. Run `pytest -q` after any controller or network change.
- Same scenario + seed = same demand for both policies. Report means over multiple seeds, not single runs.
- Tune on seeds 1-5, report on held-out seeds 11-15.
