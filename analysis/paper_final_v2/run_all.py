"""run_all.py
Deterministic Master Pipeline and Single Source of Truth for DP1 Final Analysis (v1 study).

Executes sequentially:
1. extract_metrics_v2.py: Extracts verified metrics from results/research/exp_marathahalli_improve_final/
   - Explicit suffix policy matching (fixes aliasing bug)
   - Loud assertions: exactly 48 cells, 8 runs/cell, 384 runs total
2. compute_bootstrap_v2.py: Seed-clustered and pair-level bootstrap (10,000 resamples, seed 42)
   - Loud assertions: exact subset strings, pooled value == (stat + nonstat) / 2
   - Step-down Holm correction across 3 primary metrics
   - Absolute difference and CI for wait gap
   - Sensitivity verdict comparison (cluster vs pair)
3. compute_tables_v2.py: Generates Tables 4 to 10 as CSV in paper_final_v2/tables/
   - Per-condition means, switching/green statistics, heavy audit, red-interval distributions,
     Little's Law check & edge breakdowns, insertion delay audit, 300s warm-up sensitivity
4. generate_figures_v2.py: Renders publication-quality PNGs in paper_final_v2/figures/
   - fig1_network_schematic.png, fig2_decision_trace.png, fig3_forest_plot.png, fig4_queue_timeseries.png
5. export_numbers_and_mappings.py: Exports numbers.json and generates PAPER_NUMBERS.md

Usage:
    python analysis/paper_final_v2/run_all.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_step(script_name: str, desc: str):
    print(f"\n================================================================================")
    print(f"[RUN_ALL_V2] {desc} ({script_name})")
    print(f"================================================================================")
    cmd = [sys.executable, str(ROOT / script_name)]
    res = subprocess.run(cmd, check=True)
    if res.returncode != 0:
        raise RuntimeError(f"Step {script_name} failed with code {res.returncode}")

def main():
    print("Starting DP1 Paper Final Analysis Master Pipeline v2...")
    run_step("extract_metrics_v2.py", "Step 1: Extract complete verified simulation metrics")
    run_step("compute_bootstrap_v2.py", "Step 2: Seed-clustered bootstrap and primary/secondary tables")
    run_step("compute_tables_v2.py", "Step 3: Generate per-condition, switching, audit, and delay tables")
    run_step("generate_figures_v2.py", "Step 4: Render publication-quality figures (PNG)")
    run_step("export_numbers_and_mappings.py", "Step 5: Export numbers.json and PAPER_NUMBERS.md")
    
    print("\n================================================================================")
    print("[RUN_ALL_V2] SUCCESS: All tables, figures, numbers.json, and PAPER_NUMBERS.md verified!")
    print("================================================================================\n")

if __name__ == "__main__":
    main()
