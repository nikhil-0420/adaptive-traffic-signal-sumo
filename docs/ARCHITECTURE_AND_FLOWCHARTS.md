# DP1 System Architecture and Workflow Flowcharts

This document specifies the authoritative system architecture, control execution loop, safety state machine, and research evaluation pipeline for Design Project 1 (DP1).

> **Scope Note:** DP1 focuses exclusively on current traffic-state-aware signal control using microscopic simulation (SUMO and TraCI). It does **not** include future-congestion prediction, LSTM/GRU/XGBoost forecasting, risk heatmaps, 20–30-minute forecasting, or route rerouting.

---

## 1. High-Level System Architecture and Data Flow

The DP1 architecture is organized into four modular layers:
1. **Simulation Environment (SUMO):** Microscopic simulation modeling road network geometry (Marathahalli corridor + flyover), multi-class vehicle dynamics, and simulated E2 lane-area queue detectors.
2. **Control & Safety Engine (Python/TraCI):** TraCI bridge querying sensor state, six signal optimization controllers, an emergency priority coordinator, and the immutable safety phase state machine.
3. **Application & API Service (FastAPI):** High-performance asynchronous REST and WebSocket API exposing simulation management, live telemetry streaming, and historical research datasets.
4. **Interactive Dashboard (React / Vite):** Modern web interface featuring SVG canvas visualization of road topology, dynamic zoom/pan controls, real-time signal heads, queue graphs, and metric comparisons.

```mermaid
graph TD
    subgraph Simulation_Layer["1. Microscopic Simulation Environment (SUMO)"]
        NET["Road Network Model<br/>(Marathahalli / Synthetic 4-Way)"]
        DEMAND["Synthetic Demand Generator<br/>(Poisson Inflow, 4 Patterns, 3 Levels)"]
        E2["Simulated E2 Lane-Area Detectors<br/>(Queue Length in Metres)"]
        TLS["Traffic Light Signal System<br/>(16 Signal Heads, 2-Phase + Clearances)"]
        EV["Emergency Vehicles<br/>(Ambulance Inflow & GPS Proximity)"]
        
        DEMAND --> NET
        EV --> NET
        NET --> E2
        TLS --> NET
    end

    subgraph Control_Layer["2. Python Control Engine (TraCI)"]
        TRACI["TraCI Python Interface<br/>(Step-by-Step Simulation Actuation)"]
        
        subgraph Policies["Control Policies"]
            P1["1. Fixed BTP Plan"]
            P2["2. Fixed Webster Plan"]
            P3["3. Adaptive Queue-Based"]
            P4["4. Max-Pressure Differential"]
            P5["5. Bounded Queue-Extension"]
            P6["6. RL DQN Agent (Inference)"]
            P7["7. Hybrid Queue-Adaptive (Explainable)"]
        end
        
        EVSP["Emergency Coordinator (EVSP)<br/>(Distance Threshold: 100m)"]
        SAFETY["Safety Phase State Machine<br/>(GREEN -> YELLOW 3s -> ALL-RED 2s -> GREEN)"]
        SEAM["Action Seam / Bounds Guard<br/>(min_green: 10s, max_green: 60s)"]
        
        E2 -->|Queue lengths (m)| TRACI
        TRACI -->|State vector / queues| Policies
        TRACI -->|Vehicle positions| EVSP
        Policies -->|Green duration / action| SEAM
        EVSP -->|Priority override action| SEAM
        SEAM -->|Validated transitions| SAFETY
        SAFETY -->|Light state string (e.g., rrrrGGGg...)| TRACI
        TRACI -->|Actuation commands| TLS
    end

    subgraph Service_Layer["3. Backend API Service (FastAPI)"]
        API["FastAPI REST & Telemetry Server<br/>(Uvicorn ASGI)"]
        METRICS["Metrics Collector<br/>(Waiting Time, Time Loss, Queues, Throughput)"]
        RESEARCH_STORE["Research Results Repository<br/>(CSVs, Manifests, Replays)"]
        
        TRACI --> METRICS
        METRICS --> API
        RESEARCH_STORE --> API
    end

    subgraph Frontend_Layer["4. Interactive Web Dashboard (React / Vite)"]
        UI["React 18 SPA + Vite"]
        CANVAS["SVG Network Canvas<br/>(Static Geometry, Pan/Zoom, Signal Heads)"]
        TELEMETRY_PANEL["Live Telemetry & Metrics Charts<br/>(Recharts Delay, Queue, EV Status)"]
        REPLAY_PANEL["Research Matrix Explorer<br/>(720-Cell & 360-Run Analysis)"]
        
        API -->|JSON REST / Streaming| UI
        UI --> CANVAS
        UI --> TELEMETRY_PANEL
        UI --> REPLAY_PANEL
    end
```

---

## 2. Microscopic Closed-Loop Execution Workflow

At every 1-second simulation time step, the system executes a deterministic sense-decide-act loop. The control algorithm only dictates green duration or discrete switch intents; the safety state machine strictly dictates whether a transition is legally permitted.

```mermaid
sequenceDiagram
    autonumber
    participant SUMO as SUMO Micro-Simulator
    participant TRACI as TraCI Python Client
    participant SENSORS as E2 Detector Monitor
    participant CTRL as Active Controller
    participant EVSP as EVSP Coordinator
    participant STATE as Safety State Machine

    SUMO->>TRACI: Simulation step completed (t -> t + 1s)
    TRACI->>SENSORS: Read detector queues (m) per lane
    SENSORS-->>CTRL: Provide current approach queue lengths Q(t)
    
    opt Emergency Vehicle in Simulation
        TRACI->>EVSP: Query vehicle positions & distance to stopline
        EVSP->>EVSP: Evaluate distance <= 100m & approach axis
    end

    alt During GREEN Phase
        CTRL->>CTRL: Evaluate decision logic (elapsed vs target / threshold)
        alt EVSP Priority Active
            EVSP->>STATE: Request Preemption (Hold or Switch)
        else Normal Policy Evaluation
            CTRL->>STATE: Action (HOLD or REQUEST_SWITCH)
        end
        
        STATE->>STATE: Check bounds: elapsed >= min_green (10s)?
        alt elapsed < min_green
            STATE->>STATE: Reject switch; Remain GREEN
        else elapsed >= max_green (60s) OR switch accepted
            STATE->>STATE: Transition to YELLOW (3s)
            STATE->>TRACI: Set Signal String (e.g., rrrryyyyrrrryyyy)
        end
    else During YELLOW Phase
        STATE->>STATE: Check elapsed yellow >= 3s?
        alt 3s Elapsed
            STATE->>STATE: Transition to ALL-RED (2s)
            STATE->>TRACI: Set Signal String (rrrrrrrrrrrrrrrr)
        end
    else During ALL-RED Phase
        STATE->>STATE: Check elapsed all-red >= 2s?
        alt 2s Elapsed
            STATE->>STATE: Transition to next legal GREEN(competing axis)
            STATE->>CTRL: Call decide_green(new_axis, Q(t))
            CTRL-->>STATE: Establish target green duration
            STATE->>TRACI: Set Signal String (e.g., GGGgrrrrGGGgrrrr)
        end
    end

    TRACI->>SUMO: Advance simulation with updated light state
```

---

## 3. Immutable Safety State Machine

Safety is enforced as an architectural invariant that cannot be circumvented by any algorithm (including reinforcement learning agents or priority preemption):
1. **Green-to-green transitions are impossible:** Every change in axis must transition through yellow and all-red.
2. **Conflicting greens are impossible:** Orthogonal approaches (NS and EW) can never have green simultaneously.
3. **Minimum green is guaranteed:** No switch can occur before at least $10.0\text{ s}$ of green has elapsed.
4. **Maximum green is enforced:** No phase can hold green longer than $60.0\text{ s}$, preventing corridor starvation.

```mermaid
stateDiagram-v2
    [*] --> Phase0_EW_Green: Initialize Simulation

    state Phase0_EW_Green {
        [*] --> Serving_EW
        Serving_EW --> Guard_Check: Every 1 s
        Guard_Check --> Serving_EW: elapsed < min_green (10 s)
        Guard_Check --> Forced_Switch: elapsed >= max_green (60 s)
        Guard_Check --> Voluntary_Switch: Policy REQUEST_SWITCH or Gap-Out
    }

    Phase0_EW_Green --> Phase1_EW_Yellow: Switch initiated
    
    state Phase1_EW_Yellow {
        [*] --> Yellow_Clearance_EW
        Yellow_Clearance_EW --> Yellow_Clearance_EW: elapsed < 3 s
    }

    Phase1_EW_Yellow --> Phase2_All_Red: 3 s yellow elapsed

    state Phase2_All_Red {
        [*] --> Intersection_Clearance_1
        Intersection_Clearance_1 --> Intersection_Clearance_1: elapsed < 2 s
    }

    Phase2_All_Red --> Phase3_NS_Green: 2 s all-red elapsed (Clearance Complete)

    state Phase3_NS_Green {
        [*] --> Serving_NS
        Serving_NS --> Guard_Check_NS: Every 1 s
        Guard_Check_NS --> Serving_NS: elapsed < min_green (10 s)
        Guard_Check_NS --> Forced_Switch_NS: elapsed >= max_green (60 s)
        Guard_Check_NS --> Voluntary_Switch_NS: Policy REQUEST_SWITCH or Gap-Out
    }

    Phase3_NS_Green --> Phase4_NS_Yellow: Switch initiated

    state Phase4_NS_Yellow {
        [*] --> Yellow_Clearance_NS
        Yellow_Clearance_NS --> Yellow_Clearance_NS: elapsed < 3 s
    }

    Phase4_NS_Yellow --> Phase5_All_Red: 3 s yellow elapsed

    state Phase5_All_Red {
        [*] --> Intersection_Clearance_2
        Intersection_Clearance_2 --> Intersection_Clearance_2: elapsed < 2 s
    }

    Phase5_All_Red --> Phase0_EW_Green: 2 s all-red elapsed (Cycle Re-entry)
```

---

## 4. Explainable Hybrid Dynamic Controller Decision Engine Flowchart

The Explainable Hybrid Controller (`hybrid_queue_adaptive`) integrates macroscopic Webster baseline splits with real-time microscopic queue step extensions, anti-monopoly bounds, and auditable natural-language rationale generation:

```mermaid
flowchart TD
    START(["Start Simulation Second t"]) --> PHASE_STATE{"Phase State?"}
    
    PHASE_STATE -->|"Entering GREEN"| INIT_BASE["Initialize Baseline Green:<br/>G_base = clamp(Webster_Split, 10s, 60s)<br/>G_target = G_base, G_extra = 0<br/>Reason: NEW_PHASE_BASE_ALLOCATION"]
    INIT_BASE --> APPLY["Send Action HOLD to Safety Machine"]

    PHASE_STATE -->|"In GREEN (t_elapsed < G_base)"| HOLD_BASE["Hold Green:<br/>Serving Webster Base Allocation<br/>Reason: SERVING_BASE_ALLOCATION"]
    HOLD_BASE --> APPLY

    PHASE_STATE -->|"In GREEN (t_elapsed >= G_target)"| CHECK_ANTIMONOPOLY{"Anti-Monopoly Trigger?<br/>Competing Red Wait >= 35s<br/>AND Competing Queue >= 2.0m?"}

    CHECK_ANTIMONOPOLY -->|"YES (Starvation Imminent)"| TERM_ANTIMONOPOLY["Terminate Phase Immediately:<br/>Reject Extension (+0s)<br/>Reason: SWITCH_COMPETING_WAIT"]
    TERM_ANTIMONOPOLY --> SWITCH["Send Action REQUEST_SWITCH to Safety Machine"]

    CHECK_ANTIMONOPOLY -->|"NO"| CHECK_GAPOUT{"Gap-Out Trigger?<br/>Active Queue == 0m for >= 3s<br/>AND Competing Demand > 0m?"}

    CHECK_GAPOUT -->|"YES (Empty Green Detected)"| TERM_GAPOUT["Terminate Phase Early:<br/>Reject Extension (+0s)<br/>Reason: SWITCH_GAP_OUT"]
    TERM_GAPOUT --> SWITCH

    CHECK_GAPOUT -->|"NO"| CHECK_CAP{"Ceiling Check:<br/>G_target + 3s > 60s?"}

    CHECK_CAP -->|"YES (Hit Max Green 60s)"| TERM_CAP["Terminate Phase:<br/>Max Green Reached (+0s)<br/>Reason: EXTENSION_DENIED_CAP"]
    TERM_CAP --> SWITCH

    CHECK_CAP -->|"NO"| CHECK_EXTENSION{"Step Extension Criteria Met?<br/>1. Active Queue >= 4.0m<br/>2. Active Score > 1.2x Competing Score?"}

    CHECK_EXTENSION -->|"YES (Dominant Active Queue)"| APPROVE_EXT["Approve Step Extension:<br/>Delta_G = +3.0s<br/>G_target += 3.0s, G_extra += 3.0s<br/>Reason: EXTENSION_APPROVED"]
    APPROVE_EXT --> APPLY

    CHECK_EXTENSION -->|"NO (Demand Balance Broken)"| TERM_DEMAND["Terminate Phase:<br/>Extension Criteria Not Met (+0s)<br/>Reason: SWITCH_COMPETING_DEMAND"]
    TERM_DEMAND --> SWITCH

    APPLY --> LOG_EXPLANATION["Log to decisions.csv & Broadcast Telemetry:<br/>{t, phase, G_base, Delta_G, G_extra, G_target, reason_code, reason_text}"]
    SWITCH --> LOG_EXPLANATION
    LOG_EXPLANATION --> END(["Advance to Next Step"])
```

---

## 5. Research Evaluation & Statistical Analysis Pipeline (840-Cell Matrix)

The empirical evaluation of DP1 follows a reproducible batch experimentation pipeline benchmarking 7 controllers across 840 independent simulation cells:

```mermaid
flowchart TD
    subgraph Config["1. Experimental Matrix Specification"]
        NETS["Network Models<br/>(Marathahalli Junction)"]
        PATS["4 Inflow Patterns<br/>(Balanced, Imbalanced ORR, Imbalanced Varthur, Surge ORR)"]
        LEVS["3 Demand Levels<br/>(Low 0.7x, Medium 1.0x, Heavy 1.3x)"]
        POLS["7 Controllers<br/>(Fixed, Webster, Adaptive, Pressure, Queue-Ext, DQN, Hybrid-Explainable)"]
        SEEDS["10 Held-Out Seeds<br/>(Seeds 121 - 130)"]
    end

    subgraph Exec["2. Batch Simulation Execution"]
        ORCH["Batch Orchestrator / Process Pool"]
        CELLS["840 Independent Simulation Cells<br/>(1800 s demand + drain time)"]
        EM_CELLS["360 Emergency Priority Runs<br/>(180 Matched Pairs: Priority ON vs OFF)"]
        SUMO_PROC["SUMO Headless Instances"]
        
        NETS & PATS & LEVS & POLS & SEEDS --> ORCH
        ORCH --> CELLS & EM_CELLS
        CELLS & EM_CELLS --> SUMO_PROC
    end

    subgraph Audit["3. Data Integrity & Validation"]
        RAW["Raw Runs CSV (`raw_runs.csv`)<br/>840 rows, 0 nulls, 0 duplicates"]
        RAW_EM["Raw Emergency CSV (`raw_emergency_runs.csv`)<br/>360 rows, 180 matched pairs"]
        CHECK["Integrity Gate: Assert Run Count == 840, Status == complete, Hash Match"]
        
        SUMO_PROC --> RAW & RAW_EM
        RAW & RAW_EM --> CHECK
    end

    subgraph Stats["4. Statistical Analysis & Hypothesis Testing"]
        AGG["Parametric Aggregation<br/>(Mean, Std Dev, Min, Max per Condition)"]
        BOOT["Paired Bootstrap Resampling<br/>(B = 10,000 resamples per pair, Seed 42)"]
        CI["95% Confidence Interval Estimation<br/>Delta = Policy_A - Policy_B"]
        TIE["Statistical Tie Classification<br/>(Span 0 => Indistinguishable at alpha = 0.05)"]
        
        CHECK --> AGG
        CHECK --> BOOT
        BOOT --> CI --> TIE
    end

    subgraph Deliverables["5. Scientific Artifacts & Visualizations"]
        REP["Markdown & PDF Academic Reports"]
        PLOTS["Comparative Distribution Plots<br/>(Delay Boxplots, Queue Curves, Scatter)"]
        WEB_DASH["Interactive Web Dashboard Replay & Live Explainability"]
        
        AGG & TIE --> REP & PLOTS & WEB_DASH
    end
```
