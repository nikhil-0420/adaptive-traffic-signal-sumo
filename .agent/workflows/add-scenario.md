---
description: Add a new demand scenario safely
---
1. Add the scenario to `scenarios()` in `dp1/config.py` as per-approach (t_start, t_end, vph) segments.
2. Add it to the `choices` automatically via the CLI (it reads `config.scenarios()`).
3. Run `python -m dp1.cli run --scenario <name> --policy fixed` and `--policy adaptive`.
4. Add or extend a test in `tests/test_core.py` and run `pytest -q`.
5. Report the fixed vs adaptive result for 5 seeds.
