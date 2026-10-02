# DP1 Specification - Sensor-Based Adaptive Traffic-Signal Optimisation

## 1. Problem
Fixed-time signals give each approach a preset green regardless of demand. One approach can have a long
queue while another has a few vehicles, yet both get predetermined times, increasing waiting time and
congestion. DP1 measures queue length in real time (simulated sensors) and re-allocates green time, while
always holding an all-red clearance during transitions.

## 2. Scope
In scope (DP1): simulated queue sensors, queue comparison between approaches, dynamic green extension,
adjusted red for the other axis, all-red clearance, SUMO + TraCI, comparison against fixed-time.
Out of scope (DP2, later): congestion prediction 20-30 min ahead, adaptive rerouting, multi-junction corridor,
live sensors, signal hardware.

## 3. System loop
Sense (queue in metres per approach) -> Compare approaches -> Allocate green -> Yellow -> All-red -> Switch -> Measure.

## 4. Network (current: synthetic 4-way junction)
- Node `C` (traffic light), 4 approaches N/S/E/W, one lane per approach, 300 m long, 50 km/h.
- Detector per approach: SUMO lane-area detector covering the last 150 m before the stop line.
  Queue length = `traci.lanearea.getJamLengthMeters(det_<A>)` (jam = vehicles below ~1.4 m/s). Capped at 150 m.
- Two signal axes: NS (N+S together) and EW (E+W together). Left turns are permissive (yield).
- Later (BUILD_PLAN phase 6): replace with a real OSM junction. Controllers use `SignalStates`, not phase indices.

## 5. Controllers (both use the same yellow = 3 s and all-red = 2 s)
Fixed-time baseline: NS green 30 s, EW green 30 s (PLACEHOLDER until a real BTP plan is recorded in docs/SOURCES.md).

Adaptive (rule-based, interpretable):
- Axis queue = max queue of its two approaches.
- Green for the axis about to be served: `green = clamp(min_green + k * queue_m, min_green, max_green)`
  defaults: min 10 s, max 60 s, k = 0.30 s per metre (100 m queue -> 40 s).
- During green: keep extending (1 s at a time) while own queue > 15 m, up to max_green.
  End early (gap-out) if own queue has been 0 for 3 s and the other axis queue >= 1 m, after min_green.
- Consequence: heavy axis gets more green, the other axis waits longer on red; light axis gets near-minimum green.
- Safety: GREEN -> YELLOW -> ALL_RED -> GREEN(other axis). Enforced by `controllers/base.py` and tests.

"AI" element: the rule has tunable parameters; BUILD_PLAN phase 4 tunes them with a train/held-out seed split and
tests a pressure-based variant. Do not call the default rule "deep learning".

## 6. Scenarios (vehicles/hour per approach, 1800 s demand)
balanced (400 each) | imbalanced_ns (N,S 700; E,W 200) | imbalanced_ew (mirror) |
surge_north (all 400, N rises to 1100 between 600-1200 s). Turn split 70% straight / 15% left / 15% right.
Same scenario + seed produces identical vehicles for both policies (paired comparison).

## 7. Metrics (per run, then mean +/- std over seeds)
avg waiting time (s) | avg time loss (s) | avg & max queue (m) | p95 waiting time | throughput (vehicles finished inside
the demand window, per hour) | completion rate | cycles. Teleporting is disabled so jams are not hidden.

## 8. Acceptance criteria for DP1
1. `pytest -q` passes (safety invariant, limits, physical queue readings, heavy axis gets more green).
2. `compare` runs all scenarios x 2 policies x >= 5 seeds without failures.
3. Adaptive reduces waiting time vs fixed in imbalanced scenarios; balanced is not worse; surge result is reported honestly.
4. Each claim in the demo traces to a file in `results/`.
5. Limitations stated: simulated sensors, synthetic junction (until phase 6), placeholder baseline (until phase 3).

## 9. Known limitations (say them before the mentor does)
Single lane per approach; detector capped at 150 m; no pedestrians; simple two-phase plan; surge scenario currently
favours the fixed plan; results come from a simulator, not field data.
