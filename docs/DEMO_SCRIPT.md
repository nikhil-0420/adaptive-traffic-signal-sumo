# Monday demo script (about 6 minutes)

## 0. Before you walk in
`pytest -q` green (22 passed). `results/demo/` freshly generated. GUI tested once. Terminal and `results/demo/` open. Phone charged for backup video.

## 1. Problem (30 s)
"Fixed-time signals give every approach a preset green. If one road has a long queue and the other is almost empty, both
still get predetermined green time. We measure queue length in metres and give green to the longer queue, always with an all-red
clearance before switching."

## 2. Live run (90 s)
`python -m dp1.cli run --scenario imbalanced_ns --policy fixed --seed 1 --gui`, then the same with `--policy adaptive`.
Point at: queue building on N/S under fixed; shorter queues and dynamic green extensions under adaptive.

## 3. The decision logic (60 s)
Show live decisions in terminal:
`python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --decisions`
Point at the table (first 10 decisions on screen):
- "Cycle 5: queue 35.1 m -> green 20.5 s"
- "Cycle 7: queue 72.5 m -> green 31.8 s"
- "Cycle 9: queue 57.5 m -> green 27.3 s"
(and later in `decisions.csv` at Cycle 15 as queues peak: queue 132.8 m -> green 49.8 s).
"Heavy side gets extra green, the other side waits longer on red. Switches strictly enforce Green -> Yellow (3 s) -> All-Red (2 s) -> Green, guaranteed by `PhaseMachineController` and tested by `pytest`."

## 4. Results (90 s)
Show `results/demo/wait_time.png` and `results/demo/improvement.csv`. Cite the real numbers:
- Balanced: Fixed 43.0 s -> Adaptive 18.4 s (-57.2%) | Pressure 15.6 s (-63.7%)
- Imbalanced NS: Fixed 125.6 s -> Adaptive 44.5 s (-64.6%) | Pressure 42.7 s (-66.0%)
- Imbalanced EW: Fixed 151.8 s -> Adaptive 45.6 s (-70.0%) | Pressure 43.9 s (-71.1%)
- Surge North: Fixed 76.3 s -> Adaptive 55.2 s (-27.7%) | Pressure 57.7 s (-24.5%)
"Against the BTP fixed-time plan, both adaptive and pressure controllers cut delay by 64-70% in imbalanced corridors and also beat fixed on the surge by ~25%. Against Webster's theoretical optimal fixed plan, Webster achieves 54.8 s on surge, slightly edging out adaptive (55.2 s)."

## 5. Honest limits (30 s)
1. Sensors are simulated: SUMO lane-area detectors measure queue in metres; loop/camera feeds would provide this in field.
2. Junction geometry is synthetic: 2-lane 4-way isolated cross junction without turn tapers.
3. Baseline timing: Calibrated from official BTP sheet for Marathalli Bridge Junction (Varthur Rd x ORR, weekday 08:00-11:30; 105 s NS / 95 s EW).
4. Exclusions: 15 s BTP pedestrian phase is omitted; simple 2-phase plan with permissive turns.

## 6. Next (30 s)
DP2: predict congestion 20-30 min ahead and dynamic corridor rerouting, using these optimised local signals as the new baseline.

## Likely questions
- Where is the AI? -> The controller is a transparent rule with parameters tuned by grid search on train seeds (1-5) and checked on held-out seeds (11-15); we also test a pressure variant. DP2 adds learned traffic forecasting. (Do not claim deep learning in DP1.)
- Are the sensors real? -> No, SUMO lane-area detectors measure queue length in metres (jam speed < 1.4 m/s). No claim of live Bengaluru data.
- Is the comparison fair? -> Same demand, same seeds, same yellow (3 s) and all-red (2 s), evaluated across multiple seeds.
- Why only one junction? -> Prove the sensing and control logic first; multi-junction corridors and rerouting are DP2.
