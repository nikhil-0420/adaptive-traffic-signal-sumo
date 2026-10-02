# AGENTS.md - hard rules for every agent working in this repo

## Integrity (most important)
1. NEVER fabricate or hand-edit results, metrics, tables or plots. Every number must come from a real run
   of `python -m dp1.cli ...`. If a run fails, report the failure; do not estimate.
2. Sensor data is SIMULATED (SUMO lane-area detectors). Never describe it as live Bengaluru data.
3. The fixed-time plan in `config.FIXED` is a PLACEHOLDER until a real BTP/OpenCity plan is loaded.
   Never claim it is a BTP plan unless the source file/URL and junction name are recorded in docs/SOURCES.md.
4. Report negative results honestly (e.g. the adaptive controller is currently worse in `surge_north`).
5. Do not cite papers or datasets from memory. Only cite items already in docs/SOURCES.md.

## Safety invariant (must never break)
Every phase change is GREEN -> YELLOW -> ALL_RED -> GREEN(other axis). Never switch green-to-green
directly and never show green on both axes. `tests/test_core.py` enforces this.

## Fair comparison
- Fixed and adaptive controllers share the same yellow/all-red timing (`config.TIMING`) and the same
  demand (same scenario + seed => identical vehicles).
- Compare over multiple seeds (default 5). Never present a single seed as a result.
- Tune parameters on TRAIN seeds (1-5) and report on HELD-OUT seeds (11-15). Never tune on the reporting seeds.

## Code rules
- All tunable numbers live in `dp1/config.py`. No magic numbers in other files.
- Controllers only decide green duration; the phase state machine lives in `controllers/base.py`.
- Never hard-code SUMO phase indices; use `SignalStates`.
- Generated files (`sumo/*.xml`, `results/`) are never edited by hand and never committed.
- Keep `pytest -q` green. Do not delete or weaken tests; add tests for new behaviour.
- Python 3.10+, type hints where cheap, short docstrings, no new heavy dependencies without asking.
- Windows + macOS + Linux must work: use `pathlib`, no shell-only commands in code.

## How to report back after each task
1. What changed (files). 2. How you verified (commands + pass/fail). 3. Real numbers produced.
4. Anything surprising, risky, or left undone.
