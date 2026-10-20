# DP1 Final Mentor Demo Script (7–8 Minute End-to-End Walkthrough)

**Project Title:** Adaptive Traffic Signal Optimization Using SUMO and TraCI: Evaluation of Queue-Aware Controllers on a Marathahalli Road-Network Model
**Presenter:** Nikhil (B.Tech AI & DS, School of Advanced Computing, Alliance University)
**Target Duration:** 7–8 Minutes

---

## 0. Pre-Flight Checklist (Run Before Demo Starts)
- [x] Python virtual environment active (`.venv\Scripts\Activate.ps1`).
- [x] Quality Gate verified: `pytest -q` is 100% green (97 passed in ~170s).
- [x] Frontend tests verified: `cd frontend; npm test` (7 passed) and production build `npm run build` succeeds.
- [x] Backend running on `http://127.0.0.1:8000` (`python -m uvicorn backend.main:app --port 8000`).
- [x] Frontend running on `http://localhost:5173` (`cd frontend; npm run dev`).
- [x] Browser open to `http://localhost:5173` with developer tools closed.

---

## 1. Problem Statement & Ground-Truth Baseline (60 Seconds)

### What to Say:
> "Good morning, respected mentors. Urban traffic congestion in rapidly expanding corridors like Bengaluru's Outer Ring Road is severely exacerbated by static, pre-timed traffic signals. When traffic surges on one arterial corridor, fixed-time signals continue allocating green time to empty cross-streets, causing avoidable idling, excess emissions, and trapping emergency vehicles.
>
> In DP1, we built an open-source, scientifically disciplined microscopic simulation testbed in Eclipse SUMO and Python TraCI. We reconstructed the critical **Marathahalli Bridge Junction** (Outer Ring Road $\times$ Varthur Road).
>
> As our baseline, we loaded the official Bengaluru Traffic Police (BTP) signal timing schedule from OpenCity, which assigns 105 seconds to Varthur Road and 95 seconds to the Outer Ring Road. Our objective is to evaluate whether real-time, queue-aware dynamic controllers can significantly reduce vehicle delays without ever compromising safety."

---

## 2. Road Network Reconstruction & Safety Invariant (60 Seconds)

### What to Show & Say:
*(Point to the Web Dashboard or SUMO GUI running the Marathahalli network)*

> "Notice the physical realism of our Marathahalli reconstruction:
> 1. **Grade Separation:** The North-South Outer Ring Road flyover allows uninterrupted through-traffic, while the surface roads intersect at grade.
> 2. **Simulated Sensors:** Eight simulated E2 lane-area detectors measure queue lengths in metres at the stop lines.
>
> Crucially, safety is an immutable architectural guarantee. In `controllers/base.py`, our phase state machine enforces:
> $$\text{GREEN} \longrightarrow \text{YELLOW (3 s)} \longrightarrow \text{ALL-RED (2 s)} \longrightarrow \text{GREEN(competing axis)}$$
> Direct green-to-green phase changes or simultaneous orthogonal greens are mathematically impossible. No controller—not even deep reinforcement learning—can bypass these clearance intervals."

### Command to demonstrate terminal decision trace:
```bash
python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy hybrid_queue_adaptive --seed 121 --decisions
```

---

## 3. The Seven Control Policies & Live Demonstration (90 Seconds)

### What to Say:
> "We implemented and benchmarked seven distinct control policies under identical vehicle demand:
> 1. `fixed`: The adapted BTP plan.
> 2. `fixed_webster`: Delay-minimizing cycle splits derived from saturation flow theory.
> 3. `adaptive`: Queue-actuated green allocation with real-time gap-out.
> 4. `pressure`: Max-pressure queue differential balancing.
> 5. `queue_extension`: Bounded dynamic green extensions with anti-monopoly fairness bounds.
> 6. `rl_dqn`: A Deep Q-Network reinforcement learning agent operating through a discrete action seam.
> 7. `hybrid_queue_adaptive`: Our mentor-requested **Explainable Hybrid Dynamic Controller**, which blends queue-proportional dynamic extensions, gap-out early termination, and anti-monopoly fairness switches with natural-language explainability."

### Run Live Comparison in SUMO-GUI:
```bash
# Launch Explainable Hybrid Controller on Marathahalli in SUMO-GUI:
python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy hybrid_queue_adaptive --seed 121 --gui
```
**Point to the Screen:**
- Watch the queue build up on the surface Outer Ring Road approaches.
- Point out how the hybrid controller calculates the queue difference and dynamically allocates green increments (+3s) to relieve the congestion.
- When the active queue clears, notice the 3-second gap-out smoothly clearing the intersection.

---

## 3.1 Explainable Signal Control & Live Decision Panel (60 Seconds)

### What to Show on `http://localhost:5173` (Live Monitor View):
*(Switch to the browser and point to the Live Monitor View)*

> "Unlike black-box AI controllers, traffic operators require auditable justification for every signal state change. On the Live Monitor dashboard:
> 1. **Adaptive Decision & Explanation Panel:** Every tick displays the exact controller action (`HOLD_MIN_GREEN`, `EXTEND_ACTIVE`, `SWITCH_GAP_OUT`, `SWITCH_DEMAND_FAIRNESS`, `SWITCH_FAIRNESS_WAIT_LIMIT`, or `SWITCH_MAX_GREEN`), the applied extension in seconds (e.g. `+3.0 s`), accumulated extra green, active and competing queue scores, and a concise human-readable rationale.
> 2. **Four Approach Queue Cards:** Explicit real-time cards for North (ORR-N), South (ORR-S), East (Whitefield / Varthur), and West (HAL Airport Road) showing queue lengths in metres, vehicle counts, and detector saturation indicators (`SATURATED >= 24.4m` vs `CLEAR`)."

---

## 4. Emergency Vehicle Signal Preemption (EVSP) (75 Seconds)

### What to Say:
> "In Phase P4, we implemented an Emergency Vehicle Signal Preemption (EVSP) coordinator. When an ambulance approaches within 100 metres of the junction, the coordinator safely requests green preemption. If the competing approach is green, the coordinator enforces the 10-second minimum green floor, transitions through standard yellow and all-red, and holds green until the ambulance clears."

### Run Emergency Priority Demo with GUI:
```bash
python -m dp1.cli run --network marathahalli --scenario balanced --policy fixed --seed 121 --emergency-event --emergency-priority --gui
```

### Point to Audited Metrics:
- **Ambulance Travel Time:** Cut by **52.3%** under fixed-time (dropping from **166.8 s down to 79.6 s**—a saving of **87.2 seconds**).
- **Background Traffic Impact:** Cross-axis non-emergency delay impact is negligible ($-0.89\text{ s}$ change), proving that life-saving preemption does not cause corridor gridlock.

---

## 5. Research Matrix & Statistical Tie Findings (90 Seconds)

### What to Say:
*(Navigate to the Research Workspace tab on the web dashboard)*

> "To guarantee scientific integrity:
> - All policies were tuned strictly on training seeds (`1–5`).
> - Final benchmarking was executed on held-out seeds (`121–130`).
> - We completed a 720-cell site baseline study and an **840-cell hybrid evaluation study (`exp_marathahalli_hybrid_840`)** across 4 inflow patterns, 3 demand levels, and 7 policies.
>
> Here are our key scientific discoveries:
> 1. **Low/Medium Demand:** Dynamic policies cut average vehicle delay by **38% to 52%** compared to the uncalibrated BTP fixed plan (e.g., in balanced low demand, delay drops from 15.28 s to 8.00 s).
> 2. **Heavy Saturation & Hybrid Performance:** At heavy balanced demand, `hybrid_queue_adaptive` achieves the **#1 primary ranking across all 7 policies** with **104.93 s** average delay (outperforming `rl_dqn` 105.45 s, `fixed_webster` 105.62 s, `queue_extension` 106.27 s, `pressure` 107.23 s, `adaptive` 107.50 s, and `fixed` 109.63 s).
> 3. **Statistical Parity:** When performing $10{,}000$ paired bootstrap resamples, the top dynamic controllers achieve statistical parity within 95% confidence intervals, but `hybrid_queue_adaptive` provides 100% determinism, exact seconds increments, and auditable natural-language rationales."

---

## 6. Interactive Dashboard & Visualizations (60 Seconds)

### What to Show on `http://localhost:5173`:
1. **Network Topology Canvas:** Demonstrate smooth SVG pan and zoom controls ($60\% - 350\%$), non-overlapping road labels, and active signal indications.
2. **Telemetry & Metric Trends:** Point to real-time Recharts plots tracking queue lengths and cumulative delay.
3. **Research Matrix Explorer:** Show the interactive forest plot of paired deltas and confidence intervals across all 7 policies.

---

## 7. Honest Limitations & Transition to DP2 (45 Seconds)

### What to Say (Proactively Disclosing Constraints):
> "To maintain strict academic honesty, we explicitly disclose our modeling constraints:
> 1. **Simulated Sensors:** Detectors are simulated SUMO E2 lane-area sensors; they are not live video camera feeds.
> 2. **Synthetic Demand:** Demand flows are modeled as synthetic Poisson arrivals based on Bengaluru arterial characteristics, as live per-second volume counts were unavailable.
> 3. **Isolated Junction Scope:** DP1 focuses entirely on current traffic-state-aware control at a single reconstructed junction.
>
> In **DP2**, we will scale this testbed to a multi-junction corridor along the Outer Ring Road, incorporating 20–30 minute upstream congestion forecasting and dynamic route rerouting."

---

## 8. Mentor Q&A Quick Reference
- **Q: Did you train the RL model on the test data?**
  *A:* "No. We enforced strict train/test separation: DQN was trained on seeds 1–5, validated on seeds 6–10, and reported exclusively on held-out seeds 121–130."
- **Q: Can the priority controller or hybrid controller cause a collision or skip yellow lights?**
  *A:* "Never. The clearance intervals (3s yellow, 2s all-red) are hard-coded in the centralized phase state machine in `controllers/base.py` and can never be skipped or compressed."
- **Q: Why choose the hybrid controller over Deep Q-Learning?**
  *A:* "Hybrid Queue-Adaptive delivers delay parity with DQN (and ranks #1 in heavy balanced traffic at 104.93s) while guaranteeing full transparency, zero training sample complexity, and exact natural language explanations for every signal transition."

