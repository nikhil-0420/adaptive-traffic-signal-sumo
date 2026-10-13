# Live Run Monitor & Intersection Schematic — Design Guidelines

## Purpose
Real-time simulation observatory driven by atomic telemetry from `GET /api/runs/{run_id}/telemetry`. Provides visual feedback on signal states, queues, and emergency preemption events.

## Components & Visual Hierarchy
1. **Simulation Status & Telemetry Header:**
   - Active Run ID.
   - Simulation Clock: `sim_time_s` in tabular monospace font.
   - Status badge: `RUNNING` (pulsing emerald dot), `COMPLETED`, `FAILED`, or `STALE` (amber warning if $> 5.0\text{s}$ elapsed since last update).
2. **Interactive 4-Way Intersection Schematic (SVG):**
   - Accurate junction topology representing the single 4-way junction simulated in SUMO.
   - 4 Approach Arms: North (`N_in`), South (`S_in`), East (`E_in`), West (`W_in`).
   - Signal Heads for NS and EW:
     - Active phase indicated by color (`GREEN`, `YELLOW`, `RED`).
     - Display of raw signal state string (e.g., `GGGgrrrrGGGgrrrr`).
   - Queue Bars per Approach:
     - Real-time queue length in metres displayed above each approach arm.
     - Proportional visual fill bar (0m to 150m detector length).
3. **Emergency Vehicle Radar / Priority Callout:**
   - If an emergency vehicle is detected approaching (`emergency_approaching: true`):
     - Displays pulsing warning banner with approach direction and distance in metres (e.g., "Ambulance approaching on North: 85.0m").
     - Visual indicator on the corresponding intersection arm.
     - Status of priority coordinator (`PREEMPTION_REQUESTED`, `EXTENDING_GREEN`, `PASSING`).
4. **Live Launch Control Drawer:**
   - Simple, validated form to launch a new single simulation run (`scenario`, `policy`, `seed`, optional `emergency` flags).
   - Only active when API is connected.
