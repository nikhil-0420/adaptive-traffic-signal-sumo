"""Deterministic master runner for all DP1 paper final analysis, tables, and figures.

Usage:
    python analysis/paper_final/run_all.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_step(script_name: str, desc: str):
    print(f"\n==========================================")
    print(f"[RUN_ALL] Executing: {desc} ({script_name})")
    print(f"==========================================")
    cmd = [sys.executable, str(ROOT / script_name)]
    res = subprocess.run(cmd, check=True)
    if res.returncode != 0:
        raise RuntimeError(f"Step {script_name} failed with code {res.returncode}")

def main():
    run_step("extract_metrics.py", "Step 1: Extract complete verified simulation metrics")
    run_step("compute_tables.py", "Step 2: Generate paper tables (CSV)")
    run_step("seed_clustered_bootstrap.py", "Step 2b: Compute seed-clustered bootstrap comparisons (CSV)")
    run_step("generate_figures.py", "Step 3: Render publication-quality figures (PNG)")
    run_step("patch_paper.py", "Step 4: Patch IEEE manuscript DOCX with final text, tables & figures")
    run_step("extract_paper_outputs.py", "Step 5: Generate outputs_for_paper.md verified data ledger")
    print("\n[RUN_ALL] SUCCESS: All paper tables, figures, artifacts, and DOCX generated in paper_final/")

if __name__ == "__main__":
    main()
