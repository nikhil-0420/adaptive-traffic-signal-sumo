# Phase 0 Report: Setup, Context File, Pre-Registration

## 1. What Was Done
- **Checked Working Tree & Preserved State**: Inspected `git status` on branch `upgrade-2-marathahalli`. Identified 16 modified files and 26 untracked files. Consulted user and followed refined option: branched to `dp1-improve`, staged all pre-existing files, committed as a baseline checkpoint, and created git tag `dp1-baseline-start`.
- **Created Verbatim Agent Context**: Saved the full starting prompt verbatim into [`docs/AGENT_CONTEXT.md`](../docs/AGENT_CONTEXT.md) and committed it for future agent sessions.
- **Audited & Recorded Environment Baseline**: Documented exact versions of SUMO (1.28.0), Python (3.11.9), pip package freeze, Node (`v24.16.0`), npm (`11.13.0`), and the Marathahalli network identifiers into [`docs/improvement_log.md`](../docs/improvement_log.md).
- **Formalized Research Pre-Registration**: Formulated [`docs/PREREGISTRATION.md`](../docs/PREREGISTRATION.md) covering the pre-registered research question, strict seed partitioning (101–105 dev, 106–110 val, 121–130 exploratory/burned, 131–150 final evaluation), primary/secondary/context metrics, reference policies, paired bootstrap protocol ($B=10,000$, fixed seed 42, Holm correction), rung acceptance criteria, and final matrix (4,140 total benchmark runs). Committed as its own commit `"Pre-register DP1 improvement protocol"`.
- **Recomputation Verification (READ-ONLY)**: Recomputed per-condition means across all 84 conditions from [`results/research/exp_marathahalli_hybrid_840/raw_runs.csv`](../results/research/exp_marathahalli_hybrid_840/raw_runs.csv) and evaluated differences against [`aggregate.csv`](../results/research/exp_marathahalli_hybrid_840/aggregate.csv).
- **Executed Full Test Suite**: Ran both backend (pytest) and frontend (node test) suites to ensure clean quality gates before any Phase 1 improvements begin.

---

## 2. Files Created / Changed
- **Created**:
  - [`docs/AGENT_CONTEXT.md`](../docs/AGENT_CONTEXT.md) (verbatim starting agent prompt)
  - [`docs/improvement_log.md`](../docs/improvement_log.md) (environment baseline and package freeze)
  - [`docs/PREREGISTRATION.md`](../docs/PREREGISTRATION.md) (formal research pre-registration)
  - [`docs/phase0_report.md`](../docs/phase0_report.md) (this deliverable report)
- **Committed via Initial Baseline Checkpoint on `dp1-improve`**:
  - Pre-existing working tree state on `upgrade-2-marathahalli` (16 modified files including `dp1/runner.py`, `frontend/src/*`, and 26 untracked files including `dp1/demo_scenarios.py`, frontend views, and tests).

---

## 3. Exact Commands Run

```powershell
# 1. Branching, Checkpoint, and Tagging
git checkout -b dp1-improve
git add -A
git commit -m "feat(checkpoint): preserve pre-existing Marathahalli frontend and demo scenario additions"
git tag dp1-baseline-start

# 2. Verbatim Context File
git add docs/AGENT_CONTEXT.md; git commit -m "docs: add verbatim starting agent context prompt"

# 3. Environment Audit
python -c "import sys; print(sys.version)"
.\.venv\Scripts\python.exe -c "from dp1.sumo_utils import binary; import subprocess; print(subprocess.check_output([binary('sumo'), '--version']).decode())"
node --version
npm --version
.\.venv\Scripts\python.exe -m pip freeze
git add docs/improvement_log.md; git commit -m "docs: add improvement_log.md with environment baseline"

# 4. Pre-Registration Protocol Standalone Commit
git add docs/PREREGISTRATION.md; git commit -m "Pre-register DP1 improvement protocol"

# 5. Read-Only Verification of 840-Cell Experiment Recomputation
.\.venv\Scripts\python.exe -c "
import pandas as pd
import numpy as np

raw = pd.read_csv('results/research/exp_marathahalli_hybrid_840/raw_runs.csv')
agg = pd.read_csv('results/research/exp_marathahalli_hybrid_840/aggregate.csv')
group_cols = ['pattern', 'demand_level', 'policy']
mean_cols = [c for c in agg.columns if c.endswith('_mean')]
base_cols = [c[:-5] for c in mean_cols]

recomputed = raw.groupby(group_cols, as_index=False)[base_cols].mean()
merged = pd.merge(agg, recomputed, on=group_cols, suffixes=('_agg', '_recomputed'))

diffs = {c: np.abs(merged[c + '_mean'] - merged[c]).max() for c in base_cols}
diffs_rounded = {c: np.abs(merged[c + '_mean'] - merged[c].round(3)).max() for c in base_cols}

print('Max raw float difference:', max(diffs.values()))
print('Max diff matching 3-decimal rounding:', max(diffs_rounded.values()))
"

# 6. Test Suites
# Frontend:
npm test  # (in frontend/)
# Backend:
.\.venv\Scripts\python.exe -m pytest -q
```

---

## 4. Results

### Environment Baseline Table
*(Source: System execution logs & [`docs/improvement_log.md`](../docs/improvement_log.md))*

| Component | Identifier / Version | Location / Source |
| :--- | :--- | :--- |
| **Git Branch** | `dp1-improve` | Working branch |
| **Baseline Tag** | `dp1-baseline-start` | Commit `230520b` |
| **Pre-reg Commit** | `9a0d476` | Commit `"Pre-register DP1 improvement protocol"` |
| **SUMO Engine** | Eclipse SUMO sumo 1.28.0 | `E:\dp1-traffic-signal\.venv\Scripts\sumo.exe` |
| **Python** | 3.11.9 (64-bit AMD64) | `E:\dp1-traffic-signal\.venv\Scripts\python.exe` |
| **Node.js** | v24.16.0 | System PATH |
| **npm** | 11.13.0 | System PATH |
| **Network Model**| `marathahalli` (v1.0.0) | [`network/marathahalli/source/source_metadata.json`](../network/marathahalli/source/source_metadata.json) |
| **Source Snapshot**| `opencity_bbmp_20261014` | OpenCity BBMP Road Centerline & Width Data |
| **Signal Plan** | `btp_airport_ps_marathahalli_v1`| BTP Airport Police Station (105s EW / 95s NS) |
| **Controlled TLS**| `marathahalli_tls` | Surface junction node |

### Key Package Freeze Table
*(Source: `pip freeze` in `.venv`)*

| Package | Version | Status |
| :--- | :--- | :--- |
| `eclipse-sumo` | 1.28.0 | Verified |
| `traci` | 1.28.0 | Verified |
| `sumolib` | 1.28.0 | Verified |
| `numpy` | 2.4.6 | Verified |
| `pandas` | 3.0.6 | Verified |
| `scipy` | *Not Installed* | Verified absent (`ModuleNotFoundError`) |
| `fastapi` | 0.143.0 | Verified |
| `torch` | 2.14.1 | Verified |
| `stable_baselines3` | 2.9.0 | Verified |
| `gymnasium` | 1.4.0 | Verified |
| `matplotlib` | 3.11.2 | Verified |
| `uvicorn` | 0.54.0 | Verified |
| `pytest` | 9.1.1 | Verified |

### 840-Cell Recomputation Verification Table
*(Source: [`results/research/exp_marathahalli_hybrid_840/raw_runs.csv`](../results/research/exp_marathahalli_hybrid_840/raw_runs.csv) vs [`aggregate.csv`](../results/research/exp_marathahalli_hybrid_840/aggregate.csv))*

| Metric Recomputed | Raw Max Abs Difference | Discrepancy After 3-Decimal Match | Status |
| :--- | :--- | :--- | :--- |
| `avg_trip_s_mean` | $4.975453 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `avg_wait_s_mean` | $4.959676 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `avg_wait_EW_s_mean` | $4.954694 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `avg_time_loss_s_mean` | $4.951127 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `avg_queue_m_mean` | $4.919316 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `avg_wait_NS_s_mean` | $4.583429 \times 10^{-4}$ | $0.000000$ | Exact match to CSV storage precision |
| `p95_wait_s_mean` | $1.136868 \times 10^{-12}$ | $0.000000$ | Exact match |
| `approach_wait_gap_s_mean` | $2.842171 \times 10^{-14}$ | $0.000000$ | Exact match |
| `directional_wait_disparity_s_mean` | $1.421085 \times 10^{-14}$ | $0.000000$ | Exact match |
| `max_queue_m_mean` | $3.552714 \times 10^{-15}$ | $0.000000$ | Exact match |

*Conclusion: The raw experiment artifact reproduces `aggregate.csv` with 0.0 deviation when taking into account the 3-decimal rounding formatted in `aggregate.csv`.*

### Test Suite Execution Summary
*(Source: Execution of backend pytest and frontend node test runner)*

| Test Suite | Total Tests | Passed | Failed | Skipped | Duration |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Frontend** (`node --test test/*.test.js`) | 21 | 21 | 0 | 0 | 0.97 s |
| **Backend** (`pytest -q`) | 103 | 103 | 0 | 0 | 1208.34 s (20m 08s) |
| **Total Quality Gate** | **124** | **124** | **0** | **0** | **PASS** |

---

## 5. Problems, Surprises, Anything Contradicting the Plan
- **SUMO Binary Location**: `sumo` was not directly on the system PowerShell path, but is present inside the virtual environment at `E:\dp1-traffic-signal\.venv\Scripts\sumo.exe` (installed via `eclipse-sumo==1.28.0`), which `dp1.sumo_utils.binary()` correctly discovers.
- **Package Status**: `scipy` is listed in the prompt instructions as a candidate package, but is not installed in the `.venv` environment. Documented accurately as `NOT INSTALLED`.
- **Backend Test Duration**: Full backend test suite includes multiple microscopic 1800s SUMO simulations (`test_core.py`, `test_emergency.py`, etc.), requiring ~20 minutes on this machine. All 103 tests passed without a single failure.

---

## 6. DECISION NEEDED Items
- **None at this stage**. The starting point is verified, pre-registration is committed, quality gates are fully green, and git tag `dp1-phase0` is ready to be finalized.

---

## 7. Checklist
- [x] **Seed rules respected?** (No runs executed on seeds 106–110, 121–130, or 131–150 during Phase 0).
- [x] **No experiment overwritten?** (`results/research/exp_marathahalli_hybrid_840` read in READ ONLY mode; zero files modified or created in `results/`).
- [x] **Tests passing?** (Frontend: 21/21 passed; Backend: 103/103 passed).
