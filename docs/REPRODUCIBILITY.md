# DP1 Reproducibility Guide & Execution Runbook

**Project:** Adaptive Traffic Signal Optimization Using SUMO and TraCI: Evaluation of Queue-Aware Controllers on a Marathahalli Road-Network Model  
**Author:** Nikhil (Alliance University, School of Advanced Computing)  
**Academic Year:** 2026

This guide provides end-to-end instructions for reproducing all simulation runs, verifying the quality test suite, running the FastAPI backend and React frontend, and launching interactive GUI demonstrations.

---

## 1. Environment & Prerequisites

### 1.1 System Requirements
- **Operating System:** Windows 10/11, Ubuntu 22.04 LTS, or macOS (Sonoma/Sequoia).
- **Python:** Python 3.10 or 3.11 (tested on Python 3.11.9).
- **SUMO:** Eclipse SUMO v1.28.0 (with `SUMO_HOME` environment variable configured and added to system `PATH`).
- **Node.js:** Node.js v18.0+ or v20.0+ with npm.

### 1.2 Python Virtual Environment Setup
From the project root directory:

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 2. Install primary simulation dependencies
pip install -r requirements.txt

# 3. (Optional) Install RL training & inference dependencies
pip install -r requirements-rl.txt
```

### 1.3 Verify SUMO Installation
Run:
```bash
sumo --version
```
Ensure that SUMO reports version 1.28.0 or newer and that `traci` can be imported cleanly in Python:
```bash
python -c "import traci; print('TraCI is available!')"
```

---

## 2. Quality Assurance & Test Gate

Before running experiments, execute the automated test suite to verify the core safety invariants, detector geometries, controller state machines, and API endpoints:

```bash
# Run all unit and integration tests (Quality Gate)
pytest -q
```
Expected output:
```text
97 passed, 1 warning in ~170s (100% GREEN)
```

To run fast targeted subsets:
```bash
# Test explainable hybrid controller decision logic and bounded step extensions:
pytest tests/test_hybrid_controller.py -q

# Test safety invariants and state machine transitions:
pytest tests/test_core.py tests/test_action_seam.py -q

# Test Marathahalli road network model and detectors:
pytest tests/test_marathahalli_network.py -q

# Test emergency priority preemption logic:
pytest tests/test_emergency.py -q

# Test FastAPI routes:
pytest tests/test_api.py -q
```

---

## 3. Running Microscopic Simulations via CLI

### 3.1 Single Simulation Runs (Headless or GUI)

#### Marathahalli Junction (Real-Road Reconstruction):
```bash
# 1. Run Explainable Hybrid Dynamic Signal Controller on Marathahalli model with GUI:
python -m dp1.cli run --network marathahalli --scenario balanced --policy hybrid_queue_adaptive --seed 121 --gui

# 2. Run Fixed-time BTP baseline on Marathahalli model with GUI:
python -m dp1.cli run --network marathahalli --scenario balanced --policy fixed --seed 121 --gui

# 3. Run Max-Pressure adaptive controller:
python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy pressure --seed 121

# 4. Run Bounded Queue-Extension controller:
python -m dp1.cli run --network marathahalli --scenario surge_orr_north --policy queue_extension --seed 121

# 5. Run Deep Q-Network policy (uses trained Marathahalli checkpoint):
python -m dp1.cli run --network marathahalli --scenario balanced --policy rl_dqn --seed 121

# 6. Run Emergency Preemption Demo with SUMO GUI:
python -m dp1.cli run --network marathahalli --scenario balanced --policy fixed --seed 121 --emergency-event --emergency-priority --gui
```

#### Synthetic 4-Way Junction:
```bash
# Run adaptive controller on synthetic network:
python -m dp1.cli run --network synthetic --scenario imbalanced_ns --policy adaptive --seed 1
```

---

## 4. Reproducing the Academic Experiment Matrices

The project includes batch orchestration tools to execute the full evaluation matrices across multi-core processor pools.

> **Note on Existing Artifacts:**  
> The repository already contains precomputed, audited research datasets in `results/research/`. You do not need to rerun them to inspect the findings. To regenerate them from scratch, execute:

### 4.1 Marathahalli 840-Cell Hybrid Study (`exp_marathahalli_hybrid_840`)
Matrix: 4 inflow patterns $\times$ 3 demand levels $\times$ 7 control policies $\times$ 10 held-out seeds (`121–130`).
```bash
python -m dp1.research.run_hybrid_study 4
```
Artifacts produced:
- Raw runs: `results/research/exp_marathahalli_hybrid_840/raw_runs.csv` (840 rows)
- Aggregate statistics: `results/research/exp_marathahalli_hybrid_840/aggregate.csv`
- Paired bootstrap deltas vs Webster: `results/research/exp_marathahalli_hybrid_840/paired_deltas.csv`
- Paired best policy tie analysis: `results/research/exp_marathahalli_hybrid_840/paired_best_policy.csv`
- Comparative figures: `results/research/exp_marathahalli_hybrid_840/plots/`
- Markdown research report: `results/research/exp_marathahalli_hybrid_840/report.md`

### 4.2 Marathahalli 720-Cell Site Study (`exp_marathahalli_site_720`)
Matrix: 4 inflow patterns $\times$ 3 demand levels $\times$ 6 control policies $\times$ 10 held-out seeds (`121–130`).
```bash
python -m dp1.cli research-matrix --network marathahalli --seeds 121-130 --jobs 4
```
Artifacts produced:
- Raw runs: `results/research/exp_marathahalli_site_720/raw_runs.csv`
- Aggregate statistics: `results/research/exp_marathahalli_site_720/aggregate.csv`
- Paired bootstrap statistical ties: `results/research/exp_marathahalli_site_720/paired_ties.csv`
- Comparative plots: `results/research/exp_marathahalli_site_720/plots/`

### 4.3 Emergency Priority 360-Run Study (`exp_marathahalli_emergency_360`)
Matrix: 2 patterns $\times$ 3 levels $\times$ 3 policies $\times$ 10 seeds (`121–130`) $\times$ 2 modes (Priority ON vs OFF).
```bash
python -m dp1.cli run-emergency-matrix --network marathahalli --seeds 121-130 --jobs 4
```
Artifacts produced:
- Raw emergency runs: `results/research/exp_marathahalli_emergency_360/raw_emergency_runs.csv`
- Matched pair summary: `results/research/exp_marathahalli_emergency_360/paired_summary.csv`
- Research report: `results/research/exp_marathahalli_emergency_360/report.md`

### 4.3 Auditing Dataset Integrity
Run the built-in audit script to independently verify run counts, seed coverage, missing values, and parametric agreement:
```bash
python scratch/audit_experiments.py
```
Expected output:
```text
ALL RESEARCH AUDITS PASSED WITH 100% INTEGRITY!
```

---

## 5. Launching the Full-Stack Application

### 5.1 Backend REST Service (FastAPI)
The backend service manages live TraCI runs, streams telemetry, and serves research datasets.
```bash
# From project root:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check endpoint: `http://127.0.0.1:8000/health`
- Marathahalli site model spec: `http://127.0.0.1:8000/api/site-model`

### 5.2 Frontend Interactive Dashboard (React + Vite)
In a separate terminal:
```bash
cd frontend

# Install Node dependencies:
npm install

# Run frontend tests:
npm test

# Build production bundle:
npm run build

# Start local development server:
npm run dev
```
Open your browser to:
```text
http://localhost:5173
```

### 5.3 Operating the Web Dashboard
1. **Network Topology Canvas:** View the reconstructed Marathahalli junction in crisp vector SVG, featuring the North-South Outer Ring Road, the grade-separated flyover lanes, the East-West Varthur Road, signal head indicators, and dynamic queue heatmaps.
2. **Interactive Navigation:** Use the on-canvas controls (`+`, `-`, `Reset`) or mouse scroll wheel to zoom ($60\% - 350\%$). Click and drag the canvas background to pan across the approaches.
3. **Controller Selection:** Select between `fixed`, `fixed_webster`, `adaptive`, `pressure`, `queue_extension`, and `rl_dqn` to observe live signal phase adaptations.
4. **Emergency Dispatch:** Trigger an emergency vehicle arrival and observe the EVSP coordinator grant preemptive clearance while preserving amber/all-red safety sequences.
5. **Research Matrix Explorer:** Inspect paired delta forest plots, bootstrap confidence intervals, and download Markdown/CSV scientific reports.
