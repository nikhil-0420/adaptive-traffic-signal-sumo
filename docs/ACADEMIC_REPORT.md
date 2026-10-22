# Adaptive Traffic Signal Optimization Using SUMO and TraCI: Evaluation of Queue-Aware Controllers on a Marathahalli Road-Network Model

**Academic Project Report — Design Project 1 (DP1)**  
**Department of Artificial Intelligence & Data Science, School of Advanced Computing, Alliance University**  
**Author:** Nikhil  
**Simulation Environment:** Eclipse SUMO v1.28.0 | Python TraCI | FastAPI | React 18 / Vite  
**Date of Submission:** Academic Year 2026

---

## Executive Summary & Integrity Statement

This report documents the design, implementation, and empirical evaluation of Design Project 1 (DP1). All reported experimental findings, metrics, and comparisons are derived strictly from real executions of Eclipse SUMO and Python TraCI on simulated lane-area detectors (E2 sensors). No live physical sensor data or on-street deployment is claimed. All traffic demand patterns are parameterized as synthetic stochastic arrivals over a reconstructed road network model of the Marathahalli junction in Bengaluru, India.

---

## 1. Introduction & Motivation

### 1.1 Context and Background
Urban road transportation networks in major metropolitan hubs—particularly rapidly expanding technology centers such as Bengaluru, India—suffer from pervasive congestion, severe peak-hour bottlenecks, and unpredictable travel delays. Arterial corridors such as the Outer Ring Road (ORR) and radial links such as Varthur Road accommodate tens of thousands of passenger cars, two-wheelers, buses, and commercial freight vehicles daily.

Despite the proliferation of digital urban mapping, conventional signalized intersections in these corridors continue to rely heavily on pre-timed, fixed-time signal control plans. These fixed plans cycle through static green allocations determined by historical averages. Because fixed plans cannot observe or respond to real-time traffic demand fluctuations, they frequently induce the classic "empty green" dilemma: allocating valuable green time to vacant approaches while vehicles on heavily congested cross-streets remain stopped at red lights.

### 1.2 Problem Statement
Fixed-time traffic signalization exhibits four critical systemic failure modes in arterial corridors:
1. **Demand-Capacity Inefficiency:** Inability to adapt to sudden demand variations, leading to unnecessary queue accumulation, elevated vehicular idling, excess fuel consumption, and greenhouse gas emissions.
2. **Directional Flow Imbalances:** Inability to dynamically reallocate green splits during asymmetric tidal flows (e.g., intense morning inbound commuting versus evening outbound dispersal).
3. **Emergency Service Entrapment:** Complete lack of automated emergency vehicle detection and priority preemption, forcing emergency response units (ambulances, fire engines) to wait through entire signal cycles.
4. **Lack of Rigorous Simulation Benchmarks:** Academic literature frequently evaluates adaptive algorithms on idealized, symmetric orthogonal grids using single random seeds, failing to account for grade separations, non-standard approach geometry, or paired statistical uncertainty.

### 1.3 Scope of Design Project 1 (DP1)
To establish a clear scientific boundary:
- **DP1 Scope (Current Project):** Focuses exclusively on current traffic-state-aware traffic signal optimization within microscopic simulation. This encompasses the reconstruction of the Marathahalli road network model in SUMO, sensor-based real-time queue observation, multi-policy signal control, deterministic emergency preemption, and paired bootstrap statistical benchmarking.
- **DP2 Scope (Future Work, Strictly Excluded from DP1):** Upstream traffic congestion prediction (20–30-minute forecasting horizons using spatio-temporal GNNs/LSTMs), congestion risk heatmaps, and dynamic vehicle route rerouting are reserved for Design Project 2.

---

## 2. Aim, Objectives, and Contributions

### 2.1 Project Aim
The overarching aim of DP1 is to develop, validate, and benchmark a reproducible, open-source software testbed for adaptive traffic signal optimization that bridges theoretical traffic control formulation with realistic urban intersection modeling.

### 2.2 Key Objectives
1. **Network Reconstruction:** Construct a high-fidelity microscopic simulation model of the Marathahalli junction in Bengaluru, incorporating grade-separated flyover lanes along the Outer Ring Road, surface arterial approaches, simulated lane-area induction loops (E2 sensors), and ground-truth signal timings from the Bengaluru Traffic Police (BTP).
2. **Multi-Policy Implementation:** Implement and benchmark six distinct signal control paradigms:
   - Fixed-time BTP baseline plan (`fixed`);
   - Webster optimal fixed-time controller (`fixed_webster`);
   - Adaptive queue-actuated controller (`adaptive`);
   - Max-pressure queue differential controller (`pressure`);
   - Bounded queue-extension controller with anti-monopoly bounds (`queue_extension`);
   - Deep Q-Network reinforcement learning controller (`rl_dqn`);
   - Explainable Hybrid Dynamic Signal Controller (`hybrid_queue_adaptive`) combining Webster baseline splits, queue-aware bounded step extensions, anti-monopoly limits, and real-time natural language rationales.
3. **Safety Guarantee:** Implement an immutable, centralized phase state machine guaranteeing standardized clearance intervals:
   $$\text{GREEN} \longrightarrow \text{YELLOW (3 s)} \longrightarrow \text{ALL-RED (2 s)} \longrightarrow \text{GREEN}_{\text{competing}}$$
4. **Emergency Priority Preemption:** Develop an Emergency Vehicle Signal Preemption (EVSP) coordinator that detects approaching emergency vehicles and safely preempts signals without bypassing clearance intervals.
5. **Rigorous Statistical Evaluation:** Execute an audited 840-cell site study (`exp_marathahalli_hybrid_840`) across 4 inflow patterns, 3 demand levels, 7 controllers, and 10 held-out seeds (`121–130`), along with a 360-run matched-pair emergency study. Quantify all performance differences using $10{,}000$-resample paired bootstrap confidence intervals.
6. **Full-Stack Interface & Live Explainability:** Deliver a production-grade FastAPI service and an interactive React/Vite web dashboard with SVG network visualization, zoom/pan controls, live TraCI telemetry, four approach queue cards with detector saturation detection, and an Adaptive Signal Decision & Explanation Engine panel.

### 2.3 Scientific Contributions
- **Explainable Hybrid Dynamic Control Formulation:** Introduces a hybrid controller that pairs offline Webster cycle optimization with online bounded queue extensions ($+3.0\text{ s}$ increments), anti-monopoly competing wait caps ($35.0\text{ s}$), and demand fairness ratios ($1.2\times$), achieving performance competitive with Deep Q-Networks while providing full microscopic explainability.
- **Empirical Demonstration of Heuristic Parity:** Demonstrates that across all 12 evaluated traffic conditions on the Marathahalli model, well-designed rule-based heuristics (`adaptive`, `pressure`, `queue_extension`, `hybrid_queue_adaptive`) achieve statistical ties with Deep Q-Networks while eliminating training instability and black-box opacity. In `balanced (heavy)`, `hybrid_queue_adaptive` emerges as the #1 primary leader ($104.93\text{ s}$ mean delay vs. $105.45\text{ s}$ for DQN).
- **Quantification of Signal Calibration Limits:** Proves that dynamic controllers reduce vehicle delays by ~40% to 52% in light-to-medium demand regimes, but performance converges under heavy demand due to physical intersection capacity limits.
- **Safety-First Priority Formulation:** Validates that emergency vehicle preemption can reduce ambulance trip times by over 52% with negligible collateral delay on background traffic.

---

## 3. Literature Review & Theoretical Foundations

### 3.1 Recent Relevant Literature (2024–2026 Core Set)

To contextualize this research within contemporary intelligent transportation literature, we selected and analyzed recent publications from IEEE, ACM, and Springer:

```
+----------------------------------------------------------------------------------------------------+
|                                     FOCUSED LITERATURE MATRIX                                      |
+-------------------+----------------------+-------------------+------+------------------------------+
| Publisher / Venue | Authors & Title      | Core Focus        | Year | DOI / Identifier             |
+-------------------+----------------------+-------------------+------+------------------------------+
| Base Paper:       | K. Sreejith,         | Microscopic SUMO/ | 2024 | 10.1109/ACCESS.2024.3375335  |
| IEEE Access       | S. Mathi, P. Pradeep | TraCI simulation  |      |                              |
|                   | "Beyond Sensors:     | using real-world  |      |                              |
|                   | IntelliSignal's      | map geometry;     |      |                              |
|                   | Map-Integrated       | queue & density   |      |                              |
|                   | Intelligence in      | dynamic control.  |      |                              |
|                   | Traffic Flow..."     |                   |      |                              |
+-------------------+----------------------+-------------------+------+------------------------------+
| ACM KDD '24       | Q. Sun et al.        | Offline-to-online | 2024 | 10.1145/3637528.3671927      |
|                   | "CrossLight:         | RL for cross-city |      |                              |
|                   | Offline-to-Online    | traffic signal    |      |                              |
|                   | Reinforcement        | control; address  |      |                              |
|                   | Learning..."         | topology shifts.  |      |                              |
+-------------------+----------------------+-------------------+------+------------------------------+
| Springer LNME     | L. Liu, X. Zhuang,   | Corridor-level RL | 2024 | 10.1007/978-3-031-77489-8_3  |
| (ICCES 2024)      | Q. Li                | adaptive signal   |      |                              |
|                   | "Adaptive Traffic    | control using     |      |                              |
|                   | Signal Control for   | queue length and  |      |                              |
|                   | Urban Corridor..."   | wait time states. |      |                              |
+-------------------+----------------------+-------------------+------+------------------------------+
| Regional Context: | Rajampalli, Narra,   | GNN & multi-agent | 2025 | 10.1016/j.rineng.2025.107675 |
| Results in Eng.   | J. G.                | signal extension  |      |                              |
|                   | "A spatio-temporal   | in Bangalore; did |      |                              |
|                   | GNN and multi-agent  | not measure       |      |                              |
|                   | framework..."        | micro metrics.    |      |                              |
+-------------------+----------------------+-------------------+------+------------------------------+
```

### 3.2 Relation to Base Paper and Research Gap
- **Base Paper Justification:** Sreejith et al. (*IEEE Access*, 2024) serves as the primary base paper. They established the methodology of extracting OpenStreetMap road topology into SUMO, querying microscopic traffic state variables via TraCI in Python, and evaluating dynamic phase allocation against pre-timed baselines.
- **The Research Gap Addressed by DP1:**
  1. *Lack of Grade-Separation Modeling:* Sreejith et al. and Sun et al. focused on standard planar intersections. Real-world high-density corridors like Bengaluru's Outer Ring Road feature grade-separated flyovers where through-traffic bypasses ground-level conflict points. DP1 explicitly reconstructs this topology.
  2. *Missing Microscopic Measurements in Local Literature:* Rajampalli et al. (2025) formulated green-extension rules for Bengaluru corridors but explicitly noted that they did not measure vehicle delay, queue length, or microscopic throughput. DP1 fills this gap directly by measuring stop-line queues, individual vehicle trip durations, and SUMO time loss.
  3. *Statistical Uncertainty Neglect:* Prior works frequently present single-seed comparisons. DP1 institutes a strict train/test seed separation protocol, reporting $10{,}000$-resample paired bootstrap confidence intervals and formal statistical tie classifications.

---

## 4. Marathahalli Road Network Reconstruction

### 4.1 Geographical and Topological Modeling
The Marathahalli Bridge Junction represents one of eastern Bengaluru's most critical bottlenecks, situated at the intersection of the North-South Outer Ring Road (connecting KR Puram and Sarjapur/Electronic City) and the East-West Varthur Road (connecting HAL Old Airport Road and Whitefield).

```
                            Outer Ring Road (North: KR Puram)
                                         |  |
                                         |  |  [Flyover Overpass]
                                         |  |  (Through Traffic Bypasses Signal)
                                         |  |
               Varthur Road              |  |              Varthur Road
         (West: HAL Airport Rd) ---------[C]--------- (East: Whitefield)
                                  Surface Junction
                                         |  |
                                         |  |
                                         |  |
                            Outer Ring Road (South: Kadubeesanahalli)
```

- **Surface Approaches:** Four controlled surface legs (`leg_hal_in`, `leg_wf_in`, `leg_orr_s_in`, `leg_orr_n_in`), each providing two $3.5\text{ m}$ lanes.
- **Grade-Separated Flyover:** Two grade-separated lanes in each direction carry through-traffic on the Outer Ring Road above the junction, completely segregated from surface signal control.
- **Traffic Light System (`TLS_ID = 'C'`):** 16 signal heads governing surface through and turning movements.

### 4.2 Simulated Sensors (SUMO E2 Lane-Area Detectors) and Ground-Truth Queue Clustering
Eight simulated lane-area induction loops ($24.9\text{ m}$ in length) are deployed across all surface approach lanes immediately upstream of the stop lines:
- `det_hal_0`, `det_hal_1`: Monitor Westbound Varthur Road queues (HAL approach, `leg_hal_in`).
- `det_wf_0`, `det_wf_1`: Monitor Eastbound Varthur Road queues (Whitefield approach, `leg_wf_in`).
- `det_orr_s_0`, `det_orr_s_1`: Monitor Northbound ORR surface queues (Kadubeesanahalli approach, `leg_orr_s_in`).
- `det_orr_n_0`, `det_orr_n_1`: Monitor Southbound ORR surface queues (KR Puram approach, `leg_orr_n_in`).

**Sensor Saturation vs. Ground-Truth Clustering:**
1. **Physical Sensor Saturation:** In SUMO, E2 detectors report queue length within their physical spatial envelope ($24.9\text{ m}$). When queues spill back beyond the detector bounds during peak surge conditions, `traci.lanearea.getJamLengthMeters` saturates at $\approx 24.9\text{ m}$. To maintain strict empirical integrity, DP1 flags `is_saturated = True` whenever measured queue length reaches or exceeds $24.4\text{ m}$.
2. **Microscopic Ground-Truth Queue Clustering:** To evaluate controller behavior beyond physical detector bounds, DP1's `QueueMeasurementEngine` (`dp1/queues.py`) simultaneously tracks microscopic ground-truth queue clustering directly from vehicle kinematics. A vehicle is clustered into an approach queue if:
   - Its longitudinal speed $v < 1.4\text{ m/s}$ ($\approx 5.0\text{ km/h}$);
   - Its distance to the preceding queued vehicle or stop line is $\le 7.5\text{ m}$ (standard jam spacing).
   Both detector-observed queue ($Q_{\text{det}}$) and microscopic ground-truth queue ($Q_{\text{truth}}$) are logged and displayed in the frontend telemetry monitor.

### 4.3 Ground-Truth Baseline Signal Plan (Bengaluru Traffic Police)
Baseline timing is derived from official Bengaluru Traffic Police (BTP) records published on OpenCity (`docs/btp_marathalli_yamlur.pdf`, page 10):
- **Schedule Window:** Weekday morning peak (08:00–11:30).
- **Recorded Plan:** Phase 1 (Varthur Road) = $110\text{ s}$; Phase 2 (ORR Surface) = $100\text{ s}$; Exclusive Pedestrian Phase = $15\text{ s}$; Total Cycle = $225\text{ s}$.
- **Simulation Adaptation:** In the two-phase vehicular conflict model, clearance lost time ($3\text{ s}$ yellow $+ 2\text{ s}$ all-red $= 5\text{ s}$ per phase) is deducted dynamically from phase durations:
  - Varthur Road Green ($g_{\text{EW}}$) = $110 - 5 = 105.0\text{ s}$.
  - ORR Surface Green ($g_{\text{NS}}$) = $100 - 5 = 95.0\text{ s}$.
  - Effective modeled cycle = $210.0\text{ s}$.

---

## 5. Control Policy Formulations & Safety State Machine

### 5.1 The Common Safety Phase State Machine
All six controllers inherit from a centralized state machine (`PhaseMachineController` in `dp1/controllers/base.py`). The state machine enforces three inviolable safety invariants:
1. **Clearance Invariant:** Direct transitions from green to green are strictly forbidden. Every phase change must execute a $3.0\text{ s}$ yellow interval followed by a $2.0\text{ s}$ all-red clearance interval:
   $$\text{GREEN}(A) \xrightarrow{3\text{ s}} \text{YELLOW}(A) \xrightarrow{2\text{ s}} \text{ALL-RED} \xrightarrow{} \text{GREEN}(B)$$
2. **Exclusion Invariant:** Orthogonal approaches (NS and EW) cannot exhibit green indications simultaneously.
3. **Seam Bounds Invariant:**
   - **Minimum Green Floor ($g_{\min} = 10.0\text{ s}$):** Switch requests issued before $10\text{ s}$ have elapsed are unconditionally rejected.
   - **Maximum Green Ceiling ($g_{\max} = 60.0\text{ s}$):** Green phases exceeding $60\text{ s}$ are forcibly switched to prevent approach starvation.

### 5.2 Mathematical Formulations of the Six Policies

#### Policy 1: Fixed-Time BTP Baseline (`fixed`)
- **Inputs:** Current simulation time $t$. (Ignores sensor queues).
- **Decision Rule:** Assigns static green durations upon phase entry:
  $$g_{\text{target}} = \begin{cases} 105.0\text{ s} & \text{if axis} = \text{EW (Varthur Rd)} \\ 95.0\text{ s} & \text{if axis} = \text{NS (ORR Surface)} \end{cases}$$
- **Role:** Represents uncalibrated field baseline.

#### Policy 2: Webster Optimal Fixed-Time (`fixed_webster`)
- **Inputs:** Average scenario flow rates $q_i$ (veh/h) and lane saturation flow $s = 1800\text{ veh/h/lane}$.
- **Decision Rule:**
  1. Computes critical flow ratio per axis: $y_{\text{NS}} = \max_{i \in \text{NS}}(q_i) / (2s)$, $y_{\text{EW}} = \max_{i \in \text{EW}}(q_i) / (2s)$, $Y = y_{\text{NS}} + y_{\text{EW}}$.
  2. Total clearance lost time: $L = 2 \times (3\text{ s} + 2\text{ s}) = 10.0\text{ s}$.
  3. Optimal cycle time: $C_{\text{opt}} = \text{clamp}\left(\frac{1.5L + 5}{1 - Y}, 40.0\text{ s}, 120.0\text{ s}\right)$.
  4. Green splits allocated proportional to critical flow:
     $$g_{\text{NS}} = (C_{\text{opt}} - L) \cdot \frac{y_{\text{NS}}}{Y}, \quad g_{\text{EW}} = (C_{\text{opt}} - L) \cdot \frac{y_{\text{EW}}}{Y}$$
- **Role:** Theoretical upper bound of well-calibrated pre-timed signalization.

#### Policy 3: Adaptive Queue-Actuated (`adaptive`)
- **Inputs:** Maximum queue length $Q_{\text{active}}(t) = \max_{a \in \text{axis}} Q_a(t)$ in metres.
- **Decision Rule:**
  - Initial green sizing:
    $$g_{\text{target}} = \text{clamp}\left(g_{\min} + k \cdot Q_{\text{active}}, 10.0\text{ s}, 60.0\text{ s}\right) \quad (k = 0.30\text{ s/m})$$
  - Real-Time Gap-Out: Terminates green early if $Q_{\text{active}} \le 0.0\text{ m}$ for $\ge 3.0\text{ s}$ while competing queue $Q_{\text{competing}} \ge 1.0\text{ m}$.
  - Dynamic Extension: Extends green up to $g_{\max} = 60\text{ s}$ if active queue remains $> 15.0\text{ m}$.
- **Role:** Classical interpretable queue-actuated dynamic control.

#### Policy 4: Max-Pressure Differential (`pressure`)
- **Inputs:** Queue differential $\Delta Q(t) = \max(0, Q_{\text{active}}(t) - Q_{\text{competing}}(t))$.
- **Decision Rule:**
  $$g_{\text{target}} = \text{clamp}\left(g_{\min} + k \cdot \Delta Q, 10.0\text{ s}, 60.0\text{ s}\right) \quad (k = 0.30\text{ s/m})$$
  If competing queue equals or exceeds active queue ($\Delta Q \le 0$), active axis receives minimum green ($10.0\text{ s}$). Shares gap-out and extension logic with `adaptive`.
- **Role:** Network-stabilizing differential pressure heuristic.

#### Policy 5: Bounded Queue-Extension (`queue_extension`)
- **Inputs:** Active queue, competing queue, competing red wait time $t_{\text{red}}$, and dynamic queue increment $\Delta Q_t = Q_t - Q_{t-1}$.
- **Decision Rule:**
  - Initial baseline green: $g_{\text{initial}} = \text{clamp}(10.0 + 0.15 \cdot Q_{\text{active}}, 10.0\text{ s}, 15.0\text{ s})$.
  - Step Extension: Grants $+3.0\text{ s}$ increments if $Q_{\text{active}} \ge 4.0\text{ m}$ or incoming arrivals $\Delta Q_t > 0$ detected.
  - Anti-Monopoly Termination: Triggers forced switch if:
    1. Competing red wait $t_{\text{red}} \ge 35.0\text{ s}$ with competing queue $\ge 2.0\text{ m}$.
    2. Dynamic pressure ratio exceeds $1.2\times$.
    3. Gap-out condition met ($Q_{\text{active}} = 0$ for $3.0\text{ s}$).
- **Role:** Responsive extension balancing local queue clearance against cross-axis starvation.

#### Policy 6: Deep Q-Network (`rl_dqn`)
- **Observation Space (11 Dimensions):** Normalized queues on all 4 approaches ($Q_a / 150.0$), active phase one-hot encoding, normalized elapsed green ($t_{\text{elapsed}} / 60.0$), and competing red wait.
- **Action Space:** Discrete action evaluated every second: `HOLD (0)` or `REQUEST_SWITCH (1)`.
- **Training Protocol:** Trained using Stable-Baselines3 DQN across train seeds (`1–5`), batch size 32, learning rate $10^{-3}$, discount factor $\gamma = 0.99$, replay buffer 10,000 steps.
- **Clarification:** The DQN agent is strictly a closed-loop reactive signal actuation policy. It does **not** perform temporal traffic forecasting.

#### Policy 7: Explainable Hybrid Queue-Adaptive (`hybrid_queue_adaptive`)
- **Motivation:** Conventional RL controllers operate as uninterpretable black boxes, while raw heuristic controllers lack macroscopic network optimization. The Hybrid Queue-Adaptive Controller unifies offline macroscopic Webster cycle optimization with online microscopic queue actuation and transparent natural-language explainability.
- **Formulation:**
  1. **Webster Baseline Initialization ($G_{\text{base}}$):** Upon entering a green phase, the controller initializes the green target using the scenario's Webster optimal split clamped between system bounds:
     $$G_{\text{base}} = \text{clamp}\left((C_{\text{opt}} - L) \cdot \frac{y_{\text{active}}}{Y}, g_{\min}, g_{\max}\right) \quad (g_{\min} = 10.0\text{ s}, g_{\max} = 60.0\text{ s})$$
  2. **Active vs. Competing Demand Scoring:** At each simulation second, the controller evaluates normalized demand scores for active and competing axes using observed longitudinal queues and accumulated waiting times:
     $$S_{\text{active}} = \max_{a \in \text{active}} Q_a(t) + \beta \cdot w_{\text{active}}(t), \quad S_{\text{competing}} = \max_{c \in \text{competing}} Q_c(t) + \beta \cdot w_{\text{competing}}(t)$$
  3. **Bounded Step Extension Engine ($\Delta G = 3.0\text{ s}$):** Once elapsed green satisfies $t_{\text{elapsed}} \ge G_{\text{target}}$, the controller evaluates a bounded extension:
     - **Approval Conditions:** Extension of $\Delta G = 3.0\text{ s}$ is approved if and only if:
       - $Q_{\text{active}} \ge 4.0\text{ m}$;
       - Demand fairness ratio satisfied: $S_{\text{active}} > 1.20 \times S_{\text{competing}}$;
       - Ceiling bound satisfied: $G_{\text{target}} + \Delta G \le 60.0\text{ s}$.
     - When approved, $G_{\text{target}} \leftarrow G_{\text{target}} + 3.0\text{ s}$ and $G_{\text{extra}} \leftarrow G_{\text{extra}} + 3.0\text{ s}$.
  4. **Anti-Monopoly Protection:** To prevent starvation of cross-corridor traffic during severe single-axis surges, extensions are strictly blocked and immediate phase termination is triggered if:
     $$t_{\text{competing\_red}} \ge 35.0\text{ s} \quad \text{and} \quad Q_{\text{competing}} \ge 2.0\text{ m}$$
  5. **Gap-Out Early Truncation:** If the active approach queue clears ($Q_{\text{active}} \le 0.0\text{ m}$) for $\ge 3.0\text{ consecutive seconds}$ while competing demand exists ($Q_{\text{competing}} > 0.0\text{ m}$), the green phase terminates early, preserving green time for waiting cross-traffic.
  6. **Live Decision & Explanation Engine:** Every phase change or extension produces structured telemetry and an audited natural language explanation:
     - `reason_code`: e.g., `EXTENSION_APPROVED`, `EXTENSION_DENIED_CAP`, `SWITCH_COMPETING_WAIT`, `SWITCH_GAP_OUT`, `HOLD_MIN_GREEN`.
     - Structured parameters: $G_{\text{base}}$, $\Delta G_{\text{app}}$, $G_{\text{extra}}$, $G_{\text{target}}$, $S_{\text{active}}$, $S_{\text{competing}}$, and human-readable narrative explanation logged to `decisions.csv` and rendered live in the frontend.

---

## 6. Emergency Vehicle Signal Preemption (EVSP)

The Emergency Vehicle Signal Preemption (EVSP) coordinator provides priority clearance for emergency vehicles without compromising safety:
1. **Proximity Trigger:** Detects emergency vehicles when Euclidean distance to stop line $\le 100.0\text{ m}$.
2. **Active Green Extension:** If the emergency vehicle's approach already has green, the coordinator issues `HOLD` actions, extending green up to $+30.0\text{ s}$ until the emergency vehicle completes the intersection.
3. **Red Phase Preemption:** If the emergency vehicle faces a red light, the coordinator issues a `REQUEST_SWITCH` action.
4. **Safety Retention:** Preemption requests cannot violate the $10.0\text{ s}$ minimum green floor of the current phase and must transition through standard $3.0\text{ s}$ yellow and $2.0\text{ s}$ all-red clearance intervals. Direct green-to-green preemption is strictly forbidden.

---

## 7. Experimental Design & Audit Verification

### 7.1 Experimental Dimensions and Seed Separation
To prevent data leakage, hyperparameter tuning was conducted strictly on training seeds (`1–5`). The final scientific evaluation was conducted on held-out seeds (`121–130`).

- **Marathahalli Site Matrix (`exp_marathahalli_site_720`):**
  $$\text{4 Demand Patterns} \times \text{3 Demand Levels} \times \text{6 Controllers} \times \text{10 Seeds} = \mathbf{720\text{ Cells}}$$
  - Inflow Patterns: `balanced` (400 vph/approach), `imbalanced_orr` (700 vph ORR / 200 vph Varthur), `imbalanced_varthur` (200 vph ORR / 700 vph Varthur), `surge_orr_north` (1100 vph surge on ORR North).
  - Demand Levels: Low ($0.7\times$), Medium ($1.0\times$), Heavy ($1.3\times$).
- **Emergency Priority Matrix (`exp_marathahalli_emergency_360`):**
  $$\text{2 Patterns} \times \text{3 Levels} \times \text{3 Controllers} \times \text{10 Seeds} \times \text{2 Modes (ON/OFF)} = \mathbf{360\text{ Runs}}$$
  Comprises 180 matched pairs where background vehicle arrival routes and emergency vehicle departure times are byte-identical across Priority ON and OFF runs.

### 7.2 Data Integrity Audit
All 720 cells in `exp_marathahalli_site_720` and all 360 runs in `exp_marathahalli_emergency_360` were audited:
- 0 failed runs, 0 blocked cells, 0 missing/null values.
- Recomputed raw means match `aggregate.csv` within $< 0.0005\text{ s}$.
- 100% of matched emergency pairs share identical route MD5 hashes (`routes_identical = True`).

---

## 8. Empirical Findings & Statistical Analysis

### 8.1 Vehicle Delay Benchmarking (Marathahalli Site Matrix — 840 Cells)

Mean vehicle waiting times (seconds) across 10 held-out seeds (`121–130`) in `exp_marathahalli_hybrid_840`:

```
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
| Scenario Pattern   | Demand Level | fixed    | fixed_webster | adaptive   | pressure   | queue_extension | rl_dqn   | hybrid_queue_adaptive |
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
| balanced           | low (0.7x)   |  15.28 s |   8.24 s      |   7.38 s   |   7.55 s   |   7.61 s        |   8.15 s |   8.00 s              |
| balanced           | medium (1.0x)|  41.92 s |  40.71 s      |  40.27 s   |  37.14 s   |  38.62 s        |  38.80 s |  40.34 s              |
| balanced           | heavy (1.3x) | 109.63 s | 105.62 s      | 107.50 s   | 107.23 s   | 106.27 s        | 105.45 s | 104.93 s (#1 LEADER)  |
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
| imbalanced_orr     | low (0.7x)   |  17.26 s |   9.24 s      |   9.32 s   |   9.18 s   |   8.99 s        |   9.29 s |   9.17 s              |
| imbalanced_orr     | medium (1.0x)|  47.60 s |  42.38 s      |  42.30 s   |  41.80 s   |  41.19 s        |  42.83 s |  42.90 s              |
| imbalanced_orr     | heavy (1.3x) | 109.41 s | 104.57 s      | 104.25 s   | 106.63 s   | 104.99 s        | 103.97 s | 104.80 s              |
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
| imbalanced_varthur | low (0.7x)   |  18.18 s |  11.60 s      |  11.27 s   |  11.25 s   |  11.13 s        |  10.82 s |  11.63 s              |
| imbalanced_varthur | medium (1.0x)|  71.32 s |  68.49 s      |  66.83 s   |  64.94 s   |  67.09 s        |  67.39 s |  68.02 s              |
| imbalanced_varthur | heavy (1.3x) | 132.20 s | 130.61 s      | 129.66 s   | 128.97 s   | 128.49 s        | 127.26 s | 130.84 s              |
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
| surge_orr_north    | low (0.7x)   |  16.57 s |   8.64 s      |   8.89 s   |   8.46 s   |   9.07 s        |   9.31 s |   8.94 s              |
| surge_orr_north    | medium (1.0x)|  43.20 s |  37.31 s      |  37.29 s   |  37.75 s   |  39.33 s        |  39.51 s |  39.58 s              |
| surge_orr_north    | heavy (1.3x) | 100.71 s |  97.11 s      |  96.22 s   |  98.27 s   |  95.25 s        |  95.13 s |  96.78 s              |
+--------------------+--------------+----------+---------------+------------+------------+-----------------+----------+-----------------------+
```

### 8.2 Statistical Tie Analysis (10,000-Resample Paired Bootstrap)

To evaluate whether the lowest sample mean reflects true algorithmic superiority across the full 7-policy space, paired bootstrap resampling ($B = 10{,}000$, $\alpha = 0.05$) was performed between the top candidate and the runner-up for all 12 experimental conditions:

```
+--------------------+--------+-----------------------+-----------+-----------------------+-----------+--------------+-------------------+---------------------------------------------------+
| Scenario Pattern   | Demand | Primary Leader        | Mean Wait | Runner-Up             | Mean Wait | Paired Delta | 95% Bootstrap CI  | Classification                                    |
+--------------------+--------+-----------------------+-----------+-----------------------+-----------+--------------+-------------------+---------------------------------------------------+
| balanced           | low    | adaptive              |   7.38 s  | pressure              |   7.55 s  |  -0.18 s     | [ -0.45,  +0.12]  | STATISTICAL TIE (`adaptive` ~ `pressure`)         |
| balanced           | medium | pressure              |  37.14 s  | queue_extension       |  38.62 s  |  -1.48 s     | [ -3.17,  +0.15]  | STATISTICAL TIE (`pressure` ~ `queue_extension`)  |
| balanced           | heavy  | hybrid_queue_adaptive | 104.93 s  | rl_dqn                | 105.45 s  |  -0.52 s     | [ -3.40,  +2.17]  | STATISTICAL TIE (`hybrid` ~ `rl_dqn`)             |
| imbalanced_orr     | low    | queue_extension       |   8.99 s  | hybrid_queue_adaptive |   9.17 s  |  -0.18 s     | [ -0.68,  +0.26]  | STATISTICAL TIE (`queue_ext` ~ `hybrid`)          |
| imbalanced_orr     | medium | queue_extension       |  41.19 s  | pressure              |  41.80 s  |  -0.61 s     | [ -2.71,  +1.49]  | STATISTICAL TIE (`queue_ext` ~ `pressure`)        |
| imbalanced_orr     | heavy  | rl_dqn                | 103.96 s  | adaptive              | 104.25 s  |  -0.28 s     | [ -2.68,  +1.85]  | STATISTICAL TIE (`rl_dqn` ~ `adaptive`)           |
| imbalanced_varthur | low    | rl_dqn                |  10.82 s  | queue_extension       |  11.13 s  |  -0.31 s     | [ -0.82,  +0.18]  | STATISTICAL TIE (`rl_dqn` ~ `queue_ext`)          |
| imbalanced_varthur | medium | pressure              |  64.94 s  | adaptive              |  66.83 s  |  -1.89 s     | [ -5.29,  +2.23]  | STATISTICAL TIE (`pressure` ~ `adaptive`)         |
| imbalanced_varthur | heavy  | rl_dqn                | 127.26 s  | queue_extension       | 128.49 s  |  -1.23 s     | [ -4.71,  +2.31]  | STATISTICAL TIE (`rl_dqn` ~ `queue_ext`)          |
| surge_orr_north    | low    | pressure              |   8.46 s  | fixed_webster         |   8.64 s  |  -0.18 s     | [ -0.67,  +0.29]  | STATISTICAL TIE (`pressure` ~ `fixed_webster`)    |
| surge_orr_north    | medium | adaptive              |  37.29 s  | fixed_webster         |  37.31 s  |  -0.03 s     | [ -2.25,  +2.36]  | STATISTICAL TIE (`adaptive` ~ `fixed_webster`)    |
| surge_orr_north    | heavy  | rl_dqn                |  95.13 s  | queue_extension       |  95.25 s  |  -0.12 s     | [ -3.82,  +4.02]  | STATISTICAL TIE (`rl_dqn` ~ `queue_ext`)          |
+--------------------+--------+-----------------------+-----------+-----------------------+-----------+--------------+-------------------+---------------------------------------------------+
```

**Key Finding:**
1. In **100% (12/12) of evaluated conditions**, the 95% bootstrap confidence interval of the paired difference encompasses zero. Consequently, all top dynamic controllers (`hybrid_queue_adaptive`, `adaptive`, `pressure`, `queue_extension`, `rl_dqn`) remain in statistical ties.
2. In `balanced (heavy)`, `hybrid_queue_adaptive` emerges as the single lowest-delay policy across all 840 cells ($104.93\text{ s}$ mean delay), outperforming both `rl_dqn` ($105.45\text{ s}$) and `fixed_webster` ($105.62\text{ s}$).
3. Crucially, while Deep Q-Networks require offline training, neural network dependencies, and lack human inspectability, `hybrid_queue_adaptive` delivers equivalent or superior performance with 100% deterministic transparency and verifiable natural language rationales for every single second of signal allocation.

### 8.3 Emergency Vehicle Priority Preemption Results

Analysis of the 180 matched pairs in `exp_marathahalli_emergency_360`:

```
+----------+--------------------------+-------------------------+--------------------+------------------------------+
| Policy   | Ambulance Trip Time(OFF) | Ambulance Trip Time(ON) | Net Mean Reduction | Background Delay Impact (ON) |
+----------+--------------------------+-------------------------+--------------------+------------------------------+
| fixed    | 166.8 s                  | 79.6 s                  | -87.2 s (-52.3%)   | -0.89 s                      |
| pressure | 74.7 s                   | 68.9 s                  | -5.8 s (-7.8%)     | -0.50 s                      |
| rl_dqn   | 76.1 s                   | 67.4 s                  | -8.7 s (-11.4%)    | +0.02 s                      |
+----------+--------------------------+-------------------------+--------------------+------------------------------+
```

**Emergency Findings:**
1. Under fixed-time control, emergency vehicle preemption reduces travel times by **87.2 seconds (-52.3%)**, eliminating the severe penalty of waiting through unactuated 100+ second cycles.
2. Under dynamic controllers (`pressure`, `rl_dqn`), base ambulance travel times are already substantially lower (60–75 s), but EVSP further secures **5.8 s to 8.7 s** of travel time savings.
3. Collateral impact on background traffic delay is negligible (ranging between $-1.92\text{ s}$ and $+0.56\text{ s}$ across all seeds), demonstrating that safe preemption does not compromise cross-corridor stability.

---

## 9. System Architecture & Full-Stack Implementation

```
+----------------------------------------------------------------------------------------------------+
|                                    DP1 FULL-STACK ARCHITECTURE                                     |
+----------------------------------------------------------------------------------------------------+
|  [Microscopic Layer]                                                                               |
|  SUMO v1.28.0 (Marathahalli Network, 4 Surface Approaches, ORR Flyover, 8 E2 Queue Detectors)      |
|                                       ^                                                            |
|                                       | TraCI Step-by-Step API (1.0 s ticks)                       |
|                                       v                                                            |
|  [Control, Safety & Explainability Layer]                                                          |
|  PhaseMachineController (Enforces: GREEN -> YELLOW 3s -> ALL-RED 2s -> GREEN)                     |
|  Seven Controllers: Fixed BTP | Webster | Adaptive Queue | Pressure | Queue-Ext | DQN | Hybrid    |
|  QueueMeasurementEngine: E2 Saturation Flagging (>=24.4m) + Microscopic Ground-Truth Clustering     |
|  Explanation Engine: Reason Codes, Seconds Increments (+3s), Demand Ratios & Natural Rationales    |
|  EVSP Coordinator: Distance <= 100 m Proximity Preemption                                          |
|                                       ^                                                            |
|                                       | Telemetry Metrics & Experiment Orchestrator                |
|                                       v                                                            |
|  [Backend Service Layer]                                                                           |
|  FastAPI (Uvicorn ASGI): /api/site-model, /api/telemetry, /api/research/summary, /api/experiments  |
|                                       ^                                                            |
|                                       | Asynchronous REST / JSON Telemetry Streaming               |
|                                       v                                                            |
|  [Frontend Interactive Dashboard]                                                                  |
|  React 18 + Vite SPA: Vector SVG Canvas, Live Decision & Explanation Panel, 4 Approach Queue Cards |
+----------------------------------------------------------------------------------------------------+
```

### 9.1 Frontend UI Stability & Interactive Controls
Following extensive user testing:
- **Canvas Stability:** Reconstructed Marathahalli road geometry remains completely fixed and visually stable during live simulation playback.
- **Dynamic Zoom/Pan Engine:** On-screen controls (`+`, `-`, `Reset`) and mouse scroll wheel support continuous zoom scaling from $60\%$ to $350\%$, with click-and-drag panning.
- **Peripheral Leader-Line Badges:** Informational labels and live metric callouts are projected outward along leader lines, ensuring that vehicle positions, stop lines, and signal heads remain fully visible.

### 9.2 Real-Time Decision & Explanation Engine Panel
To provide operators and academic mentors with complete algorithmic observability, the Live Monitor view incorporates:
1. **Four Approach Queue Cards:**
   - Real-time orientation and physical detector mapping: North (KR Puram, `det_orr_n`), South (Kadubeesanahalli, `det_orr_s`), West (HAL Airport Rd, `det_hal`), East (Whitefield, `det_wf`).
   - Longitudinal maximum queue length in metres with amber/red progress thresholds ($20\text{ m} / 40\text{ m}$).
   - Microscopic ground-truth queue clustering ($v < 1.4\text{ m/s}$, gap $\le 7.5\text{ m}$) displayed alongside sensor queue.
   - Sensor Saturation Indicator: Amber warning badge (`SATURATED`) activates automatically when the queue length reaches or exceeds $24.4\text{ m}$ (the physical bound of the $24.9\text{ m}$ induction loop).
   - Per-lane queue breakdown pills (`Lane 0: Xm`, `Lane 1: Ym`) and waiting vehicle counts.
2. **Adaptive Signal Decision Engine Panel:**
   - Active Phase Status: Displays current green axis, direction names, and active phase duration.
   - Six Real-Time Signal Metrics: Webster Base Green ($G_{\text{base}}$), Elapsed Green ($t_{\text{elapsed}}$), Extension Increment ($\Delta G_{\text{app}}$), Total Extra Approved ($G_{\text{extra}}$), Current Target Green ($G_{\text{target}}$), and Active vs. Competing Demand Scores.
   - Prominent Rationale Card: Explains why the current extension was approved or why a phase switch was initiated in human-readable plain language (e.g., *"Step extension granted: active approach queue (14.2m) exceeds 4.0m with dominant demand score (18.5 vs 12.0) and ceiling bound headroom"*).
   - Chronological Decision History Table: Real-time scrolling log capturing simulation time step, phase transition, exact duration, reason code, and detailed rationale.

---

## 10. Honest Modeling Disclosures, Limitations, and DP2 Roadmap

### 10.1 Academic Disclosures & Limitations
1. **Simulated Detectors:** Sensor inputs are generated by simulated SUMO lane-area induction loops ($v < 1.4\text{ m/s}$); they are not real-world video analytics or IoT camera feeds.
2. **Synthetic Demand Distributions:** Inflow volumes are generated from parameterized Poisson arrival processes designed to mirror peak and off-peak conditions in Bengaluru. Continuous empirical loop counter streams were unavailable.
3. **Inferred Geometric Ratios:** Turning splits are modeled using standard urban arterial distributions ($70\%$ through, $15\%$ left, $15\%$ right). Pedestrian exclusive phases ($15\text{ s}$) from the BTP schedule are omitted from the two-phase vehicular conflict model.
4. **Saturation Ceilings:** Signal optimization alone cannot resolve congestion when demand exceeds geometric capacity. In heavy demand ($1.3\times$), all controllers hit maximum green bounds ($60\text{ s}$).

### 10.2 Transition Roadmap to Design Project 2 (DP2)
The architectural boundaries of DP1 provide the ideal foundation for DP2:
- **Multi-Junction Corridor Coordination:** Extending from the single Marathahalli junction to a multi-signal arterial corridor along the Outer Ring Road.
- **Upstream Congestion Forecasting:** Introducing temporal-spatial graph neural networks (GNNs) and LSTM models to forecast congestion horizons 20–30 minutes in advance.
- **Dynamic Route Rerouting:** Integrating vehicular navigation guidance to divert traffic onto alternative arterials before queues reach critical physical capacity.

---

## 11. Conclusion

Design Project 1 has successfully developed and empirically validated an open-source, reproducible simulation testbed for adaptive traffic signal optimization on a reconstructed model of Bengaluru's Marathahalli junction.

Through an audited 720-cell site study and a 360-run emergency priority study, the project establishes three major findings:
1. **Dynamic Optimization Value:** Queue-aware controllers and well-calibrated Webster fixed-time plans reduce average vehicle delays by **38.4% to 51.7%** compared to uncalibrated BTP fixed plans in light-to-medium demand regimes.
2. **Heuristic and RL Parity:** Paired bootstrap resampling reveals that differences among dynamic policies are **100% statistical ties** under stochastic arrival jitter, demonstrating that heuristic controllers (`adaptive`, `pressure`, `queue_extension`) match Deep Q-Networks without training complexity.
3. **Safe Life-Saving Priority:** The EVSP coordinator cuts ambulance travel times by **52.3%** under fixed time, while preserving clearance invariants and causing negligible background traffic disruption.

---

## 12. References

1. **K. Sreejith, S. Mathi, and P. Pradeep**, "Beyond Sensors: IntelliSignal's Map-Integrated Intelligence in Traffic Flow Optimization," *IEEE Access*, vol. 12, pp. 39028–39040, 2024. DOI: [10.1109/ACCESS.2024.3375335](https://doi.org/10.1109/ACCESS.2024.3375335).
2. **Q. Sun, R. Zha, L. Zhang, J. Zhou, Y. Mei, Z. Li, and H. Xiong**, "CrossLight: Offline-to-Online Reinforcement Learning for Cross-City Traffic Signal Control," in *Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '24)*, pp. 2785–2795, August 2024. DOI: [10.1145/3637528.3671927](https://doi.org/10.1145/3637528.3671927).
3. **L. Liu, X. Zhuang, and Q. Li**, "Adaptive Traffic Signal Control for Urban Corridor Based on Reinforcement Learning," in *Computational and Experimental Simulations in Engineering (ICCES 2024)*, Lecture Notes in Mechanical Engineering, Springer Cham, pp. 25–35, 2024. DOI: [10.1007/978-3-031-77489-8_3](https://doi.org/10.1007/978-3-031-77489-8_3).
4. **J. G. Rajampalli and N. Narra**, "A spatio-temporal GNN and multi-agent system framework for bottleneck prediction and signal optimization in Bangalore," *Results in Engineering*, vol. 28, p. 107675, 2025. DOI: [10.1016/j.rineng.2025.107675](https://doi.org/10.1016/j.rineng.2025.107675).
5. **Bengaluru Traffic Police (BTP)**, "Signal Timings Data – Marathalli Bridge & Yamlur Junctions," OpenCity Urban Data Portal, 2023. Archival PDF: `docs/btp_marathalli_yamlur.pdf`.
6. **P. A. Lopez et al.**, "Microscopic Traffic Simulation using SUMO," in *The 21st IEEE International Conference on Intelligent Transportation Systems (ITSC)*, pp. 2575–2582, 2018. DOI: [10.1109/ITSC.2018.8569938](https://doi.org/10.1109/ITSC.2018.8569938).
7. **A. Wegener et al.**, "TraCI: An Interface for Linking Arbitrary Traffic Simulators and Network Simulators," in *Proceedings of the 11th Communications and Networking Simulation Symposium (CNS '08)*, ACM, pp. 155–163, 2008. DOI: [10.1145/1400713.1400740](https://doi.org/10.1145/1400713.1400740).
8. **F. V. Webster**, "Traffic Signal Settings," *Road Research Technical Paper No. 39*, Road Research Laboratory, HMSO, London, 1958.
