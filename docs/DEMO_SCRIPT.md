# Monday demo script (about 6 minutes)

## 0. Before you walk in
`pytest -q` green. `results/` freshly generated. GUI tested once. Terminal and results/ open. Phone charged for backup video.

## 1. Problem (30 s)
"Fixed-time signals give every approach a preset green. If one road has a long queue and the other is almost empty, both
still get the same time. We measure queue length in metres and give green to the longer queue, always with an all-red
clearance before switching."

## 2. Live run (90 s)
`python -m dp1.cli run --scenario imbalanced_ns --policy fixed --seed 1 --gui`, then the same with `--policy adaptive`.
Point at: queue building on N/S under fixed; shorter queues under adaptive.

## 3. The decision logic (60 s)
Show decisions.csv: "N queue 111 m -> green 43 s; E queue 20 m -> green 20 s. Heavy side gets extra green, the other waits longer."
Show the safety rule: green -> yellow -> all-red -> green, enforced and tested (`pytest -q`).

## 4. Results (90 s)
Show results/wait_time.png and improvement.csv. Say the numbers from YOUR run. Then say:
"Balanced traffic: about the same. Imbalanced: waiting time roughly halves. Surge scenario: adaptive is currently not better;
we are tuning it." Showing the weak case builds credibility.

## 5. Honest limits (30 s)
Sensors are simulated; junction is synthetic until the real OSM junction is imported; baseline timing is [BTP plan for
<junction> / a placeholder - say which]; single lane per approach.

## 6. Next (30 s)
DP2: predict congestion 20-30 min ahead and reroute, using these optimised signals as the new baseline.

## Likely questions
- Where is the AI? -> The controller is a transparent rule with parameters tuned by search on train seeds and checked on
  held-out seeds; we also test a pressure variant. DP2 adds learned prediction. (Do not claim deep learning in DP1.)
- Are the sensors real? -> No, SUMO lane-area detectors measure queue length in metres; this is how a loop/camera sensor
  would report it. No claim of live Bengaluru data.
- Is the comparison fair? -> Same demand, same seeds, same yellow/all-red, 5+ seeds, held-out seeds for tuned settings.
- Why not just one junction? -> Prove the control logic first; corridor and rerouting are DP2.
- Why is surge worse? -> A long green on the surging approach also holds its opposite approach, which has little traffic,
  so green is partly wasted; tuning/pressure variant addresses this (state the result you actually got).
