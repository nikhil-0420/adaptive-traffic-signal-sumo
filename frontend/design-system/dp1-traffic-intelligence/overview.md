# Operations Overview — Workspace Guidelines

## Purpose
The primary landing view for traffic operations engineers and researchers. Displays high-level simulation health, quick KPI stats, comparison summary across standard scenarios, and immediate access to recent runs.

## Components & Layout
1. **System Connection Banner:**
   - Real-time indicator: Connected to Local API (`http://127.0.0.1:8000`) vs. Read-Only Simulation Snapshot.
   - If connected, shows SUMO binary status and version.
   - If in snapshot mode, shows timestamp of generated snapshot and notice that live runs require local Python/SUMO.
2. **Key Metric Summary Cards (4 KPIs):**
   - **Average Waiting Time:** Mean wait in seconds (with % improvement of Adaptive vs Fixed).
   - **Throughput:** Average vehicles arrived per hour.
   - **Maximum Queue Length:** Peak jam length observed across detectors (metres).
   - **Directional Disparity:** Gap between NS and EW waiting times (fairness indicator).
3. **Primary Scenario Comparison Table:**
   - Balanced, Imbalanced NS, Imbalanced EW, Surge North.
   - Columns: Scenario, Baseline Fixed Wait (s), Adaptive Wait (s), Webster Wait (s), Relative Delta (%).
   - Clickable row navigates directly to Controller Lab or Run Explorer with pre-filtered scenario.
4. **Recent Simulation Runs:**
   - Table displaying recent run IDs, scenario, policy, seed, completion status, and action button to inspect traces.
