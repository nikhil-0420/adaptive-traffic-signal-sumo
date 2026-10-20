# DP1 Final Presentation Deck: Academic Submission

**Title:** Adaptive Traffic Signal Optimization Using SUMO and TraCI: Evaluation of Queue-Aware Controllers on a Marathahalli Road-Network Model  
**Author:** Nikhil (Alliance University, School of Advanced Computing)  
**Program:** B.Tech in Artificial Intelligence & Data Science  
**Course:** Design Project 1 (DP1) — Academic Year 2026  

---

## Slide 1: Title & Project Identity

### Adaptive Traffic Signal Optimization Using SUMO and TraCI
**Microscopic Simulation and Rigorous Benchmarking of Queue-Aware Controllers on a Marathahalli Road-Network Model**

- **Student Researcher:** Nikhil (Reg: B.Tech AI & DS)
- **Institution:** Alliance University, School of Advanced Computing
- **Simulation Platform:** Eclipse SUMO v1.28.0 + Python TraCI
- **Scope Distinction:** Current traffic-state-aware microscopic control (DP1).  
  *(Future congestion forecasting and dynamic rerouting reserved for DP2).*

---

## Slide 2: Problem Statement & Motivation

### The Urban Mobility Crisis in Metropolitan Corridors
- **Arterial Congestion:** Rapidly urbanizing Indian tech corridors (e.g., Bengaluru's Outer Ring Road) experience severe peak-hour bottlenecks and long vehicle queues.
- **Flaws of Static Signalization:**
  - Real-world signals frequently execute fixed-time cyclic schedules regardless of immediate demand.
  - Leads to the classic "empty green" dilemma: green signals service empty lanes while orthogonal queues grow.
  - Traps emergency services (ambulances) in general traffic.
- **Scientific Gap:** Prior adaptive studies often evaluate algorithms on idealized synthetic grids, omit grade separations, report anecdotal single-seed runs, or claim algorithmic dominance without paired confidence intervals.

---

## Slide 3: Aim, Objectives, and Methodological Scope

### Transforming Traffic Control from Static Scheduling to Sensor-Driven Adaptation
- **Aim:** Build an open-source, reproducible simulation framework to evaluate queue-aware adaptive signal controllers and emergency vehicle preemption on real-world arterial road geometry.
- **Core Objectives:**
  1. Reconstruct the Marathahalli junction in SUMO with grade-separated flyover and simulated E2 sensors.
  2. Implement and benchmark seven control policies (including an explainable hybrid controller) under identical demand distributions.
  3. Enforce an architectural safety invariant: `GREEN -> YELLOW (3s) -> ALL-RED (2s) -> GREEN`.
  4. Develop an Emergency Vehicle Signal Preemption (EVSP) coordinator.
  5. Conduct paired bootstrap statistical analysis ($B = 10{,}000$) across 840 site cells and 360 emergency runs.
  6. Deliver a live interactive React/Vite dashboard backed by a FastAPI REST engine.

---

## Slide 4: Marathahalli Network & Ground Truth Provenance

### Grounded Microscopic Modeling of Bengaluru's High-Density Arterial
- **Geometry & Traffic Segregation:**
  - **Outer Ring Road (North-South):** 2 surface lanes each direction + 2 grade-separated flyover lanes bypassing the surface conflict point.
  - **Varthur Road (East-West):** 2 surface lanes connecting HAL Old Airport Road to Whitefield.
- **Real-World BTP Signal Timing Plan:**
  - Ground truth from Bengaluru Traffic Police (BTP) signal timings published via OpenCity (`btp_marathalli_yamlur.pdf`).
  - Weekday 08:00–11:30 schedule: Varthur Rd (Phase 1) = 110 s; ORR Surface (Phase 2) = 100 s; Pedestrian = 15 s.
  - Modeled effective vehicle green: Varthur Rd = 105 s, ORR = 95 s (accounting for 5 s lost time per phase).
- **Simulated Sensors:**
  - 8 simulated E2 lane-area induction loops ($24.9\text{ m}$ length) measuring queue lengths in metres at stop lines.

---

## Slide 5: Architectural Safety Invariant & Action Seam

### Centralized State Machine Enforcing Signal Legality
- **Immutable State Machine:**
  - Transitions strictly follow:  
    $$\text{GREEN(axis)} \xrightarrow{\text{clearance}} \text{YELLOW (3 s)} \xrightarrow{\text{clearance}} \text{ALL-RED (2 s)} \xrightarrow{\text{clearance}} \text{GREEN(other axis)}$$
  - Direct green-to-green transitions are impossible.
  - Orthogonal simultaneous green indications are impossible.
- **Action Seam Interface:**
  - Controllers only issue discrete intents during green: `HOLD (0)` or `REQUEST_SWITCH (1)`.
  - **Minimum Green Guard:** Switches requested before $10.0\text{ s}$ elapsed are rejected.
  - **Maximum Green Limit:** Green phases exceeding $60.0\text{ s}$ are forcibly terminated to prevent starvation.

---

## Slide 6: The Six Evaluated Control Policies

### Comprehensive Spectrum from Static Heuristics to Deep RL
1. **Fixed BTP Baseline (`fixed`):** Uncalibrated static plan (105 s EW / 95 s NS green); ignores traffic state.
2. **Webster Optimal Fixed-Time (`fixed_webster`):** Classical cycle and split optimization from saturation flow ($s=1800\text{ vph/lane}$); cycle clamped [40s, 120s]; split proportional to critical flow.
3. **Adaptive Queue-Actuated (`adaptive`):** Proportional green allocation ($g = \text{clamp}(10 + 0.3 \cdot q_{\max}, 10, 60)$) with real-time gap-out when own queue clears.
4. **Max-Pressure Differential (`pressure`):** Green allocated from queue difference ($\Delta q = \max(0, q_{\text{own}} - q_{\text{competing}})$); balances network-wide queue buildup.
5. **Bounded Queue-Extension (`queue_extension`):** Dynamically extends green in 3 s steps if queue $\ge 4\text{ m}$ or dynamic arrivals detected; terminates on competing red wait exceeding 35 s.
6. **Deep Q-Network (`rl_dqn`):** Reinforcement learning agent observing 11-dimensional state vector (queues, active axis, elapsed time); selects `HOLD` or `SWITCH`. *(Closed-loop controller; not a forecaster).*

---

## Slide 7: Emergency Vehicle Signal Preemption (EVSP)

### Priority Preemption Without Sacrificing Safety
- **Coordinator Logic:**
  - Continuously monitors approaching emergency vehicles (e.g., ambulance traveling North on ORR).
  - Triggers priority action when distance to stop line $\le 100\text{ m}$.
- **Preemption Handling:**
  - If approach already has GREEN: Extends green phase (up to $+30\text{ s}$) until the ambulance clears the intersection.
  - If approach has RED: Requests immediate phase switch via the action seam.
  - Standard amber ($3\text{ s}$) and all-red ($2\text{ s}$) clearance are strictly maintained.
- **Fairness Recovery:** Resets priority flags immediately upon vehicle clearance.

---

## Slide 8: Experimental Matrix & Statistical Methodology

### Disciplined Experimental Rigor
- **Site Experiment Matrix (`exp_marathahalli_site_720`):**
  - **4 Inflow Patterns:** `balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`
  - **3 Demand Levels:** Low ($0.7\times$), Medium ($1.0\times$), Heavy ($1.3\times$)
  - **6 Control Policies:** `fixed`, `fixed_webster`, `adaptive`, `pressure`, `queue_extension`, `rl_dqn`
  - **10 Held-Out Seeds:** Seeds `121–130` (models tuned strictly on train seeds `1–5`)
  - **Total:** $4 \times 3 \times 6 \times 10 = \mathbf{720\text{ cells}}$ (100% complete, 0 missing values).
- **Emergency Priority Matrix (`exp_marathahalli_emergency_360`):**
  - 2 patterns $\times$ 3 levels $\times$ 3 policies $\times$ 10 seeds $\times$ 2 modes (ON / OFF) = $\mathbf{360\text{ runs}}$ (180 matched pairs with byte-identical background traffic routes).
- **Statistical Uncertainty:**
  - $10{,}000$ paired bootstrap resamples per condition.
  - Differences reported with 95% confidence intervals; intervals spanning 0 classified as statistical ties.

---

## Slide 10: Experimental Findings: Vehicle Delay Comparison

### Dramatic Reductions in Light-to-Medium Regimes; Saturation Ceilings in Heavy
- **Low Demand Regime (0.7x):**
  - BTP Fixed Plan: Average delay **$15.28\text{ s} - 18.18\text{ s}$**.
  - Dynamic Policies: Average delay **$7.38\text{ s} - 11.27\text{ s}$** (**$38.4\% - 51.7\%$ reduction**).
  - Root cause: Fixed plan traps cars on red while the cross-street is completely empty.
- **Medium Demand Regime (1.0x):**
  - BTP Fixed Plan: Delay $41.92\text{ s} - 71.32\text{ s}$.
  - Dynamic Policies: Delay $37.14\text{ s} - 67.39\text{ s}$ (delay reduced by $3.0\text{ s} - 6.4\text{ s}$ per vehicle).
- **Heavy Saturated Regime (1.3x):**
  - Severe queue buildup across all approaches.
  - Delays converge across all policies: $95.1\text{ s} - 132.2\text{ s}$.
  - Demonstrates physical bottleneck saturation where green time alone cannot overcome road geometry capacity.

---

## Slide 11: Statistical Tie Analysis

### Rigorous Bootstrap Hypothesis Testing
- **100% Statistical Ties Between Top Dynamic Controllers:**
  - Across all 12 evaluated conditions, the paired difference between the numerical leader and runner-up includes zero in its 95% bootstrap confidence interval.
  - Examples:
    - *Balanced Low:* `adaptive` (7.38s) vs `pressure` (7.55s) $\rightarrow \Delta = -0.18\text{s}$, $95\%\text{ CI } [-0.45\text{s}, +0.12\text{s}]$ $\Rightarrow$ **TIE**
    - *Imbalanced ORR Medium:* `queue_extension` (41.19s) vs `pressure` (41.80s) $\rightarrow \Delta = -0.61\text{s}$, $95\%\text{ CI } [-2.71\text{s}, +1.49\text{s}]$ $\Rightarrow$ **TIE**
    - *Surge ORR Heavy:* `rl_dqn` (95.13s) vs `queue_extension` (95.24s) $\rightarrow \Delta = -0.12\text{s}$, $95\%\text{ CI } [-3.82\text{s}, +4.02\text{s}]$ $\Rightarrow$ **TIE**
- **Scientific Takeaway:** Under stochastic arrival variance, well-calibrated heuristics (`adaptive`, `pressure`, `queue_extension`) perform on par with deep reinforcement learning, offering much lower computational overhead.

---

## Slide 12: Emergency Priority Performance (EVSP)

### Life-Saving Preemption with Negligible Background Disruption
- **Massive Ambulance Delay Reduction:**
  - Under `fixed`: Mean ambulance trip drops from **$166.8\text{ s} \rightarrow 79.6\text{ s}$** (**$-87.2\text{ s}$ / $-52.3\%$**).
  - Under `pressure`: Mean trip drops from **$74.7\text{ s} \rightarrow 68.9\text{ s}$** (**$-5.8\text{ s}$**).
  - Under `rl_dqn`: Mean trip drops from **$76.1\text{ s} \rightarrow 67.4\text{ s}$** (**$-8.7\text{ s}$**).
- **Impact on Non-Emergency Background Traffic:**
  - Net background traffic delay difference is negligible:
    - `fixed`: $-0.89\text{ s}$
    - `pressure`: $-0.50\text{ s}$
    - `rl_dqn`: $+0.02\text{ s}$
- **Conclusion:** Priority preemption dramatically benefits emergency vehicles without causing gridlock on competing approaches.

---

## Slide 13: Architecture, Limitations, and Conclusion

### Academic Conclusions & Path to DP2
- **Full-Stack Implementation:**
  - High-performance FastAPI server + React/Vite interactive dashboard with SVG topology, pan/zoom canvas, and live TraCI playback.
- **Key Scientific Contributions:**
  1. High-fidelity Marathahalli junction reconstruction with real BTP timing baseline.
  2. Strict architectural separation of policy logic and safety state machines.
  3. Empirical proof that dynamic control cuts delay by ~50% in low demand, while identifying statistical parity between heuristics and RL.
  4. Demonstrated that emergency priority cuts travel times by 52.3% without background congestion penalties.
- **Modeling Limitations Disclosed:**
  - Inferred vehicle turning ratios ($70\%$ through, $15\%$ left, $15\%$ right).
  - Simulated E2 sensors (not live camera feeds); synthetic Poisson inflows.
- **Roadmap to DP2:**
  - Multi-junction corridor coordination along the Outer Ring Road.
  - Upstream congestion forecasting (20–30 min horizon) and dynamic vehicle rerouting.

---
**Thank You! Questions & Discussion Welcomed.**
