# Run Explorer & Trace Inspector — Design Guidelines

## Purpose
Second-by-second inspection of individual simulation runs. Allows researchers to audit why a controller made specific green-duration choices and examine the detector queues.

## Key Components
1. **Run Selector & Filter:**
   - Dropdown or searchable filter by scenario, policy, seed, and emergency flag.
   - Run metadata badge: Seed, Total Cycles, Completion Rate (100%), Total Vehicles Arrived.
2. **Second-by-Second Queue Length Timeseries (Recharts):**
   - Multi-line chart displaying queues per approach:
     - `q_N`: Blue line
     - `q_S`: Cyan line
     - `q_E`: Orange line
     - `q_W`: Amber line
   - Zoom/Pan or downsample step control for long simulations.
3. **Signal Phase Timeline & Active Axis Strip:**
   - Visual band below queue chart showing active phase (`GREEN`, `YELLOW`, `ALL_RED`) and active axis (`NS` vs `EW`).
4. **Cycle-by-Cycle Decision Log Table:**
   - Table displaying: Cycle #, Time (s), Axis, Detected Queues (N, S, E, W), Green Duration Allocated (s), Actual Green (s).
   - Shows decision explanation logic (e.g., "Queue 112m -> Allocated 55s green").
5. **Emergency Vehicle Event Callout (when present):**
   - If run contains an emergency event, displays ambulance departure time, arrival time, total wait time, and whether preemption/extension was engaged.
6. **Artifact Downloads:**
   - Direct download links for `timeseries.csv`, `decisions.csv`, and `tripinfo.xml`.
