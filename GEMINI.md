# DP1 - Adaptive Traffic-Signal Optimisation (SUMO + TraCI)

## What this project is
Alliance University Design Project 1 (DP1), B.Tech AI & DS. A single 4-way junction is simulated in SUMO.
Simulated sensors (lane-area detectors) measure queue length in metres per approach. The approach with the
longer queue gets extra green; the other approach waits longer on red; an all-red clearance is always held
before switching. The adaptive controller is compared against a fixed-time baseline.
DP2 (later, NOT in scope now): congestion prediction 20-30 min ahead + adaptive rerouting.

## How we work
Nikhil + Claude (outside the IDE) are the planners. You are the implementation engineer.
Do exactly what the current prompt asks, verify it, report numbers. Do not redesign the project.

## Read first, in this order
1. docs/SPEC.md  - what the system must do (authoritative)
2. docs/BUILD_PLAN.md - phases and what is already done
3. AGENTS.md - hard rules you must follow

## Commands (run from the project root, venv active)
- Setup: `pip install -r requirements.txt`
- Tests (quality gate): `pytest -q`
- One run: `python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 [--gui]`
- Quick demo: `python -m dp1.cli demo`
- Full comparison: `python -m dp1.cli compare --seeds 5 --jobs 4`

## Layout
dp1/config.py (ALL numbers) | network.py | scenarios.py | signal_states.py | controllers/ | runner.py | metrics.py | compare.py | cli.py
tests/test_core.py | docs/ | results/ (generated) | sumo/ (generated)
