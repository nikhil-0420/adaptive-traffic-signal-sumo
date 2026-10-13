# DP1 - Sensor-Based Adaptive Traffic-Signal Optimisation (SUMO + TraCI)

Simulated lane-area queue sensors (in metres) dynamically allocate green splits to competing junction approaches; every phase transition strictly enforces clearance intervals (`GREEN -> YELLOW (3s) -> ALL-RED (2s) -> GREEN`). 

Developed for **Alliance University B.Tech AI & DS Design Project 1 (DP1)**. 
*(DP2 in subsequent semester: 20–30 min predictive congestion forecasting and corridor rerouting).*

---

## 1. System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │          React Operations Dashboard          │
                    │      (Overview, Lab, Explorer, Research)     │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTP / SSE / Telemetry
                    ┌──────────────────────▼───────────────────────┐
                    │        FastAPI Decoupled Backend             │
                    │      (Process Manager, Run Telemetry)        │
                    └──────────────────────┬───────────────────────┘
                                           │ Subprocess CLI / Signals
┌──────────────────────────────────────────▼──────────────────────────────────────────┐
│                             DP1 Simulation Engine (Python)                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ • Network: Synthetic 4-way 2-lane junction (300m edges, 150m detector coverage)     │
│ • Scenarios: Poisson demand (balanced, imbalanced_ns, imbalanced_ew, surge_north)  │
│ • Clearance Invariant: base.py enforces Green -> Yellow (3s) -> All-Red (2s)        │
│ • 5 Signal Controllers:                                                             │
│     1. fixed (BTP Marathahalli Bridge adapted baseline: 105s NS / 95s EW)           │
│     2. fixed_webster (Analytical delay-minimizing green splits)                     │
│     3. adaptive (Queue-actuated dynamic extension with gap-out)                     │
│     4. pressure (Max-pressure queue balancing across approaches)                    │
│     5. rl_dqn (Gymnasium discrete action RL controller with DQN inference)         │
│ • Deterministic Emergency Preemption: Ambulance detection within 100m               │
│ • Research Evaluation Suite: Bounded matrix, 95% bootstrap CIs, directional fairness│
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │ TraCI Socket Protocol
                    ┌──────────────────────▼───────────────────────┐
                    │               Eclipse SUMO 1.28              │
                    │     (Microscopic Traffic Flow Simulator)     │
                    └──────────────────────────────────────────────┘
```

---

## 2. Installation & Environments

The repository maintains strict modularity: core simulation requires only base Python packages, while RL and API modules are fully optional.

### 2.1 Core Simulation Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install core simulation dependencies (includes SUMO binaries via wheel)
pip install -r requirements.txt
sumo --version   # Confirms Eclipse SUMO is operational
```

### 2.2 Optional RL & API Dependencies
```bash
# Install Deep Q-Network & Gymnasium dependencies
pip install -r requirements-rl.txt

# Install FastAPI backend service dependencies
pip install -r requirements-api.txt
```

### 2.3 Operations Dashboard Setup
```bash
cd frontend
npm install
npm test         # Validates demo data snapshots and client logic (7/7 tests passed)
npm run build    # Produces optimized production bundle
```

---

## 3. Quick Start & Common Commands

All commands are executed from the repository root with `.venv` active:

### 3.1 Quality Gate Verification
```bash
# Run complete test suite (66 tests covering safety, controllers, RL, emergency, API, research)
pytest -q
```

### 3.2 Single Runs & GUI Simulation
```bash
# Watch adaptive controller in SUMO GUI on imbalanced demand
python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --gui

# Inspect live controller decisions in terminal
python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --decisions

# Run with deterministic emergency ambulance and priority preemption
python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1 --emergency-event --emergency-priority --gui
```

### 3.3 Fast Demo Comparison
```bash
# Run 4 scenarios comparing fixed vs adaptive vs pressure
python -m dp1.cli demo
```

### 3.4 Research Matrix Evaluation
```bash
# Preview planned matrix cells without running simulation
python -m dp1.cli evaluate-research --preset smoke --dry-run

# Run research matrix evaluation across designated research test seeds (seeds 21..30)
python -m dp1.cli evaluate-research --preset custom --patterns imbalanced_ns --levels medium --policies fixed fixed_webster adaptive pressure rl_dqn --seeds 21 22 --jobs 2
```

### 3.5 Launching Dashboard & API Service
```bash
# Terminal 1: Launch FastAPI Telemetry Backend (http://127.0.0.1:8000)
python -m backend

# Terminal 2: Launch React Dashboard (http://localhost:5173)
cd frontend
npm run dev
```
*(Note: If the backend is not running, the dashboard automatically operates in **Snapshot Mode** using verified repository demo runs).*

---

## 4. Rigorous Seed Separation Policy

To guarantee academic and empirical integrity, random seeds are strictly partitioned:
- **`TRAIN_SEEDS` (1–5)**: Hyperparameter exploration and Webster profile timing calibration.
- **`RL_VALIDATION_SEEDS` (6–10)**: RL training checkpoint evaluation.
- **`HELD_OUT_SEEDS` (11–15)**: Held-out benchmark seeds for comparative reporting.
- **`RESEARCH_EVAL_SEEDS` (21–30)**: Strictly isolated research test seeds; never used during training or parameter tuning.

---

## 5. Verified Real Simulation Results

*All metrics derived from verified Eclipse SUMO runs on identical synthetic arrival streams. No numbers are hand-edited.*

### 5.1 Controller Comparison on Imbalanced Demand (`imbalanced_ns`, Medium Demand, Held-Out Research Seeds)
| Policy | Avg Wait (s) | 95% Bootstrap CI vs Fixed | Avg Time Loss (s) | Direction Disparity (s) | Completion Rate |
|---|---:|---|---:|---:|---:|
| **`fixed`** (BTP baseline) | 127.29 s | *reference* | 159.49 s | 120.11 s | 100.0% |
| **`fixed_webster`** | 39.36 s | **-87.94 s** [-89.88, -85.99] | 78.23 s | 13.27 s | 100.0% |
| **`adaptive`** | 50.14 s | **-77.15 s** [-77.30, -77.01] | 76.84 s | 21.70 s | 100.0% |
| **`pressure`** | 49.67 s | **-77.62 s** [-78.69, -76.54] | 75.21 s | **9.84 s** | 100.0% |
| **`rl_dqn`** | 57.04 s | **-70.25 s** [-74.38, -66.12] | 122.05 s | 49.72 s | 100.0% |

### 5.2 Deterministic Emergency Vehicle Preemption (`imbalanced_ns`, Seed 1)
| Controller | Emergency Priority | Ambulance Wait (s) | Ambulance Trip Duration (s) | Background Avg Wait (s) |
|---|---|---:|---:|---:|
| **`fixed`** | Disabled | 48.2 s | 72.8 s | 126.1 s |
| **`fixed`** | **Enabled** | **0.0 s** | **25.8 s (-64.6%)** | 127.8 s (+1.3%) |
| **`pressure`** | Disabled | 32.1 s | 57.2 s | 44.2 s |
| **`pressure`** | **Enabled** | **2.0 s** | **27.6 s (-51.7%)** | 46.1 s (+4.3%) |

---

## 6. Known Limitations & Research Boundaries

1. **Simulated Sensor Readings**: Detectors are simulated SUMO lane-area induction loops measuring queue length in metres (jam speed < 1.4 m/s). They do not represent live IoT camera feeds.
2. **Synthetic Junction Geometry**: 4-way isolated intersection with two 300 m lanes per approach and 150 m detector coverage. Queues exceeding 150 m cannot be physically measured.
3. **BTP Baseline Adaptation**: The fixed plan is adapted from BTP's Marathahalli Bridge junction (105s NS / 95s EW). The 15 s exclusive pedestrian phase is not modelled in the 2-phase vehicle network.
4. **Surge Scenario Trade-off**: In transient surges (`surge_north`), rapid queue clearance may incur extra lost time due to frequent phase transitions; analytical Webster splits edge out adaptive rules in this specific condition.
5. **Simulated Environment**: All results demonstrate algorithmic performance under SUMO microscopic car-following models (Krauss) and do not constitute field-deployment certifications.
