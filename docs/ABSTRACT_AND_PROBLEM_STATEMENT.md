# Project Abstract and Problem Statement

**Project Title:**  
Adaptive Traffic Signal Optimization Using SUMO and TraCI: Evaluation of Queue-Aware Controllers on a Marathahalli Road-Network Model

**Institutional Affiliation:**  
Alliance University, School of Advanced Computing  
Department of Artificial Intelligence & Data Science  
Design Project 1 (DP1) — Academic Submission Package

---

## 1. Project Abstract

Urban signalized intersections in rapidly growing metropolitan corridors frequently operate under severe congestion caused by fixed-time signal scheduling that cannot respond to time-varying traffic demand, directional flow imbalances, or emergency service dispatches. This study presents an open-source, reproducible simulation framework for adaptive traffic signal control developed using the Simulation of Urban MObility (SUMO) micro-simulator and its Python Traffic Control Interface (TraCI). 

We reconstruct a high-fidelity microscopic simulation model of the Marathahalli junction in Bengaluru, India—a critical arterial intersection characterized by heavy bidirectional flows along the Outer Ring Road (ORR) and Varthur Road, a grade-separated flyover bypassing surface conflict points, and real-world signal plans published by the Bengaluru Traffic Police (BTP) via the OpenCity repository. We formulate, implement, and benchmark six distinct signal control policies:
1. An adapted BTP fixed-time baseline plan (105 s / 95 s green split; 210 s effective vehicle cycle);
2. A Webster optimal fixed-time controller calculated from saturation flow rates;
3. An adaptive queue-actuated controller with dynamic green scaling and gap-out clearance;
4. A max-pressure differential controller based on cross-axis queue differences;
5. A bounded queue-extension controller featuring anti-monopoly waiting-time bounds; and
6. An optional Deep Q-Network (DQN) reinforcement learning agent operating through a discrete action seam.

Every controller is strictly constrained by a centralized phase state machine that guarantees the immutable safety invariant:
$$\text{GREEN} \longrightarrow \text{YELLOW (3 s)} \longrightarrow \text{ALL-RED (2 s)} \longrightarrow \text{GREEN}_{\text{competing}}$$
Direct green-to-green phase changes, concurrent conflicting green indications, and clearance interval violations are mathematically and architecturally prohibited.

We evaluate performance across an independently audited 720-cell experimental matrix spanning four directional demand patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`), three demand intensities (`low`, `medium`, `heavy`), and ten held-out random seeds (`121–130`). In addition, we execute a 360-run matched-pair emergency study evaluating an Emergency Vehicle Signal Preemption (EVSP) coordinator under identical traffic generation routes.

Empirical evaluation reveals that under low-to-medium demand regimes, dynamic queue-aware policies and Webster-optimized plans reduce average vehicle delay by **38.4% to 51.7%** compared to the uncalibrated BTP fixed-time baseline (e.g., from 15.28 s down to 7.38 s in balanced low demand). Under heavy, near-saturated conditions, physical intersection capacity bounds performance across all policies (average delay 95.1 s – 132.2 s). Pairwise bootstrap resampling ($B = 10{,}000$, 95% confidence intervals) across all 12 experimental conditions indicates that differences between top-performing dynamic controllers (`adaptive`, `pressure`, `queue_extension`, and `rl_dqn`) span zero, demonstrating statistical ties under arrival randomness rather than artificial algorithmic superiority. 

In the emergency evaluation, EVSP priority preemption slashes ambulance travel times by **52.3%** under fixed-time operation (a mean reduction of 87.2 s) and by **0.75 s to 12.65 s** under dynamic policies, while imposing a negligible impact on background traffic delay ($-1.92\text{ s}$ to $+0.56\text{ s}$). The system is exposed via a production-grade FastAPI REST backend and visualized through a modern React/Vite dashboard featuring SVG network topologies, interactive zoom/pan controls, and live TraCI telemetry.

---

## 2. Problem Statement and Motivation

### 2.1 Problem Statement
Conventional urban traffic control in Indian metropolitan centers relies predominantly on pre-timed (fixed-time) signal plans that execute rigid cyclic timing schedules regardless of immediate vehicular arrival rates. When applied to complex arterial corridors such as Bengaluru's Outer Ring Road, fixed-time schedules suffer from fundamental systemic deficiencies:
1. **Demand-Capacity Mismatch:** Signals allocate green time to empty approaches while heavily queued opposing corridors experience forced idling, resulting in elevated delays, increased stop-and-go cycles, excess fuel consumption, and unnecessary tailpipe emissions.
2. **Inability to Adapt to Directional Imbalances:** Asymmetric peak-hour commuting patterns (e.g., intense morning inbound flow toward IT corridors followed by evening reversals) are poorly accommodated by static splits, leading to severe queue spillbacks.
3. **Emergency Dispatch Impediment:** Emergency response vehicles (ambulances, fire engines) are frequently trapped in general queue queues at surface junctions, with no automated preemption mechanisms to grant safe clearance before arrival.
4. **Lack of Rigorous Microscopic Evaluation:** Prior adaptive signal studies often evaluate algorithms on idealized synthetic orthogonal grids, omit realistic road network features (grade separations, dedicated turning bays), rely on single random seeds, or report marginal mean gains without paired statistical uncertainty quantification.

### 2.2 Project Motivation
The primary motivation of Design Project 1 (DP1) is to design, implement, and validate an open, reliable, and reproducible software testbed for evaluating real-time, sensor-aware traffic signal optimization algorithms. By anchoring the simulation on the Marathahalli junction model in Bengaluru, this project bridges the critical divide between theoretical control formulation and practical urban roadway modeling.

Crucially, DP1 establishes a disciplined scientific framework:
- **Simulation Integrity:** Simulated lane-area induction loop detectors (SUMO E2 sensors) provide queue-length measurements. Traffic demand is systematically parameterized as synthetic Poisson arrival profiles on the Marathahalli road network model. No claim of live real-world sensor telemetry or field deployment is made.
- **Safety Guarantee:** Control algorithms are strictly confined to deciding green durations or requesting phase transitions; all physical signal actuations are mediated by an immutable state machine enforcing standardized amber and all-red clearance intervals.
- **Statistical Rigor:** Algorithms are tuned exclusively on training seeds (`1–5`) and evaluated on held-out seeds (`121–130`). Hypotheses are evaluated using paired bootstrap difference distributions and confidence intervals rather than anecdotal single-seed runs.
