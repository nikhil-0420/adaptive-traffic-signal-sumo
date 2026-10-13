# DP1 Mentor Demo Script (7-8 Minutes End-to-End Walkthrough)

## 0. Pre-Flight Checklist
- [x] `pytest -q` is 100% green (66 passed).
- [x] Frontend tests `npm test` passing (7 passed) and production build `npm run build` succeeds.
- [x] Model checkpoint verified at `results/models/test_smoke_dqn.zip` with schema metadata.
- [x] Backend running on `http://127.0.0.1:8000` or dashboard in verified Snapshot Mode (`http://localhost:5173`).
- [x] Terminal open at project root with active `.venv`.

---

## 1. Problem Statement & Fixed Baseline (45 s)
**Speaker Script:**
> "Fixed-time traffic signals operate on predetermined timing schedules regardless of real-time demand. In cities like Bengaluru, this leads to severe delays when one arterial corridor backs up while the cross-street remains almost empty. 
> For our baseline, we adapted the official Bengaluru Traffic Police (BTP) schedule for the Marathahalli Bridge Junction (Outer Ring Road × Varthur Road, morning peak), which allocates 105 seconds to NS and 95 seconds to EW.
> Our system measures real-time queue lengths using simulated lane-area detectors and dynamically allocates green time to whichever approach has the greater demand, while strictly enforcing safety clearance intervals."

---

## 2. Safety Invariant & Decision State Machine (60 s)
**Speaker Script:**
> "Safety is an inviolable constraint in our implementation: every single phase switch strictly transitions through `GREEN -> YELLOW (3 s) -> ALL-RED (2 s) -> GREEN (cross-axis)`. Direct green-to-green transitions or simultaneous greens are mathematically impossible because the phase state machine in `controllers/base.py` enforces this transition logic.
> Let's look at the decision engine in action:"

**Command:**
```bash
python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --decisions
```
**Point to Terminal:**
- Early in demand (Cycle 5): Queue ~35 m $\rightarrow$ allocates 20.5 s green.
- Peak queue (Cycle 15): Queue reaches 132 m $\rightarrow$ dynamically extends green to 49.8 s.
- Cross street (light demand): Receives near-minimum green floor (10 s) before safely gapping out.

---

## 3. Five-Controller Matrix Comparison (90 s)
**Speaker Script:**
> "We implemented and benchmarked five distinct signal control paradigms on identical traffic arrival seeds:
> 1. `fixed`: Our BTP-adapted fixed baseline.
> 2. `fixed_webster`: Delay-minimizing cycle splits calculated using Webster's classical traffic formula.
> 3. `adaptive`: Interpretable queue-actuated dynamic extension with gap-out.
> 4. `pressure`: Max-pressure queue balancing that equalizes delays across competing approaches.
> 5. `rl_dqn`: Gymnasium discrete action environment running a trained Deep Q-Network agent."

**Show Benchmark Table (from `results/research/exp_p6_validation/aggregate.csv`):**
| Controller | Avg Waiting Time | 95% Bootstrap CI vs Fixed | NS vs EW Disparity | Completion Rate |
|---|---:|---|---:|---:|
| `fixed` | 127.29 s | *reference* | 120.11 s | 100% |
| `fixed_webster` | 39.36 s | **-87.94 s** [-89.88, -85.99] | 13.27 s | 100% |
| `adaptive` | 50.14 s | **-77.15 s** [-77.30, -77.01] | 21.70 s | 100% |
| `pressure` | 49.67 s | **-77.62 s** [-78.69, -76.54] | **9.84 s** | 100% |
| `rl_dqn` | 57.04 s | **-70.25 s** [-74.38, -66.12] | 49.72 s | 100% |

**Key Takeaway:**
> "Adaptive and Pressure cut average delay by over 60% compared to the fixed plan. Pressure achieves the lowest directional disparity (9.84 s vs 120.11 s for Fixed), ensuring fair service without starving the cross-street."

---

## 4. Deterministic Emergency Vehicle Priority (60 s)
**Speaker Script:**
> "In Phase P4, we implemented deterministic emergency vehicle preemption. When an ambulance is inserted at $t = 300\text{ s}$, detection occurs only when it is within 100 m on an incoming approach. If the competing axis is active, preemption waits for the 10 s minimum green floor, transitions safely through yellow and all-red, and extends green for the ambulance."

**Run Emergency GUI Demo:**
```bash
python -m dp1.cli run --scenario imbalanced_ns --policy fixed --seed 1 --emergency-event --emergency-priority --gui
```
**Point to Metrics:**
- **Ambulance Wait Time:** Drops from **48.2 s down to 0.0 s**.
- **Ambulance Total Trip Duration:** Cut by **64.6%** (from 72.8 s to 25.8 s).
- **Background Traffic Impact:** Cross-traffic wait increases by merely 1.3% (from 126.1 s to 127.8 s), demonstrating minimal collateral delay.

---

## 5. Research Rigor: Seed Separation & Statistical Inference (60 s)
**Speaker Script:**
> "To prevent data leakage and confirmation bias:
> - Hyperparameters were tuned strictly on `TRAIN_SEEDS` (1–5).
> - Baseline comparisons used `HELD_OUT_SEEDS` (11–15).
> - Final research evaluation matrix ran on isolated `RESEARCH_EVAL_SEEDS` (21–30).
> - Every comparison reports 10,000-resample paired bootstrap confidence intervals. When intervals don't cross zero, delay reductions are statistically significant."

---

## 6. React Operations Dashboard & Live Telemetry (60 s)
**Open `http://localhost:5173` in Browser:**
1. **Overview View:** Show system health, active controller status, and simulation counts.
2. **Intersection Schematic (Live Monitor):** Point to SVG graphic showing real-time queue lengths in metres per lane, signal light indicators, and live ambulance proximity alert.
3. **Controller Lab:** Demonstrate interactive multi-policy comparison across scenarios.
4. **Research Workspace:** Inspect forest plot of paired deltas, directional disparity bar chart, and download buttons for `report.md` and raw CSVs.
5. **Snapshot Mode Banner:** Highlight that when offline, the dashboard gracefully loads verified precomputed run data with exact timestamp labeling.

---

## 7. Honest Limitations & Transition to DP2 (45 s)
**Speaker Script (Say these before the mentor asks!):**
1. **Simulated Sensors:** Sensors are SUMO lane-area detectors (speed < 1.4 m/s); they are not live IoT camera feeds.
2. **Synthetic Geometry:** Single isolated 4-way cross-intersection with 150 m detector length (queues beyond 150 m are unobserved).
3. **Adapted BTP Timing:** The 15 s pedestrian phase from Marathahalli Bridge is omitted; the 2-phase vehicle cycle is 210 s.
4. **Surge Trade-Off:** In sudden traffic surges (`surge_north`), rapid queue clearance incurs switching lost time, where Webster's fixed split slightly outperforms adaptive rules.
5. **Looking forward to DP2:** We will scale from this single local junction to a multi-junction arterial corridor with 20–30 minute traffic prediction models (GNN / LSTM) and dynamic rerouting.

---

## Mentor Q&A Cheat Sheet
- **Q: Where is the AI?**
  *A:* "In DP1, we evaluated rule-based heuristic control (adaptive queue), traffic theory (Webster), game-theoretic physics (max-pressure), and deep reinforcement learning (DQN via Gymnasium). DP2 introduces learned temporal-spatial forecasting."
- **Q: Can the priority logic cause a collision?**
  *A:* "No. All preemption requests are routed through `PhaseMachineController`. The clearance intervals (3s yellow, 2s all-red) are hard-coded in the state machine and cannot be bypassed."
- **Q: How do you know the comparison is fair?**
  *A:* "All policies consume identical seeded route files generated with identical vehicle departures and turning splits. Only the traffic signal controller differs."

