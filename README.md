# DP1 - Sensor-Based Adaptive Traffic-Signal Optimisation (SUMO + TraCI)

Simulated queue sensors (in metres) decide which approach gets extra green; every switch goes
yellow -> all-red -> green. Compared against a fixed-time baseline. DP2 (prediction + rerouting) comes later.

## Quick start
```bash
# 1) create and activate a virtual environment
python -m venv .venv
#   Windows:      .venv\Scripts\activate
#   macOS/Linux:  source .venv/bin/activate

# 2) install (SUMO itself comes from the pip wheel - no separate installer)
pip install -r requirements.txt
sumo --version

# 3) check everything
pytest -q                       # 11 tests, ~10 s
python -m dp1.cli demo          # fixed vs adaptive on one scenario
python -m dp1.cli compare --seeds 5 --jobs 4   # full experiment -> results/
python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --gui   # watch it
```
Messages like "Retrying in 1 seconds" or "Could not connect to TraCI server" during start-up are normal while SUMO boots;
the run only fails if it prints a RuntimeError.

## Open in Antigravity
File -> Open Folder -> this folder. Then follow docs/PROMPTS.md (P0, P1, ...). Rules and workflows are in `.agent/`
(rename to `.agents/` if your Antigravity version expects that).

## Layout
```
GEMINI.md  AGENTS.md  .agent/{rules,workflows}   <- instructions for the IDE agent
docs/SPEC.md BUILD_PLAN.md PROMPTS.md DEMO_SCRIPT.md SOURCES.md
dp1/config.py          every tunable number
dp1/network.py         4-way junction + 4 lane-area queue detectors
dp1/scenarios.py       seeded Poisson demand (balanced / imbalanced / surge)
dp1/signal_states.py   light strings derived from the net (no hard-coded phases)
dp1/controllers/       base state machine, fixed_time, adaptive_queue
dp1/runner.py          one TraCI run -> timeseries.csv, decisions.csv, tripinfo.xml
dp1/metrics.py  compare.py  cli.py
tests/test_core.py     quality gate (safety invariant etc.)
results/reference/     example outputs from the verification run
```

## Reference results (verification run: SUMO 1.28, seeds 1-5; regenerate on your machine)
| scenario | fixed wait (s) | adaptive wait (s) | change |
|---|---|---|---|
| balanced | 50.1 | 48.8 | +2.6% |
| imbalanced_ns | 104.4 | 50.8 | +51.4% |
| imbalanced_ew | 109.0 | 51.1 | +53.1% |
| surge_north | 67.6 | 74.2 | -9.8% (adaptive worse - tuning target) |

Honest notes: sensors are simulated; the junction is synthetic; the fixed-time plan (30 s / 30 s) is a PLACEHOLDER until a
real BTP plan is recorded in docs/SOURCES.md.
