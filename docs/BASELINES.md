# Reference Baselines for Adaptive Traffic Signal Optimization

This document specifies the exact algorithms, mathematical formulations, parameters, and citations for all reference baselines implemented in Phase 9.

All baselines strictly enforce the shared safety state machine (`dp1/controllers/base.py`):
$$\text{GREEN}(\text{axis}) \xrightarrow{3\text{ s yellow}} \text{YELLOW}(\text{axis}) \xrightarrow{2\text{ s all-red}} \text{ALL\_RED} \xrightarrow{} \text{GREEN}(\text{other axis})$$
- Green never switches to green directly.
- Yellow is always exactly 3.0 s (`config.TIMING.yellow_s`).
- All-red is always exactly 2.0 s (`config.TIMING.all_red_s`).
- Both axes are never simultaneously green.

---

## 1. `webster_measured` (Measured-Flow Webster Fixed Baseline)

### Algorithm
1. **Warm-up Window ($t < 300\text{ s}$)**:
   - Operates under the BTP-adapted fixed baseline plan (`C.FIXED_MARATHAHALLI`: NS = 95.0 s, EW = 105.0 s; or `C.FIXED` for synthetic).
   - Measures arrival events on each approach leg ($\text{leg\_hal\_in}$, $\text{leg\_wf\_in}$, $\text{leg\_orr\_s\_in}$, $\text{leg\_orr\_n\_in}$) during $t \in [0, 300\text{ s}]$.
   - Approach arrival flow rate:
     $$q_a = N_a \times \frac{3600}{\Delta t} \quad (\text{vph})$$
     where $N_a$ is the count of unique vehicles entering approach $a$ during the warm-up window of duration $\Delta t = 300\text{ s}$.
2. **Webster Solution ($t = 300\text{ s}$)**:
   - Uses the canonical Webster formula identical to `site_webster_plan` / `FixedWebsterController`:
     - Saturation flow per approach leg (2 lanes): $S = s_{\text{lane}} \times 2 = 1800 \times 2 = 3600\text{ vph}$.
     - Critical flow ratios:
       $$y_{\text{ns}} = \frac{\max(q_N, q_S)}{S}, \quad y_{\text{ew}} = \frac{\max(q_W, q_E)}{S}$$
       $$Y = y_{\text{ns}} + y_{\text{ew}}$$
     - Total lost time per cycle:
       $$L = 2 \times (t_{\text{yellow}} + t_{\text{all\_red}}) = 2 \times (3 + 2) = 10.0\text{ s}$$
     - Optimal cycle length:
       $$c_{\text{opt}} = \begin{cases} \frac{1.5 L + 5.0}{1.0 - Y} & \text{if } Y < 1.0 \\ c_{\text{max}} = 120.0\text{ s} & \text{if } Y \ge 1.0 \end{cases}$$
       $$C = \max(c_{\text{min}}, \min(c_{\text{max}}, c_{\text{opt}})), \quad [c_{\text{min}}, c_{\text{max}}] = [40.0\text{ s}, 120.0\text{ s}]$$
     - Effective total green:
       $$G_{\text{total}} = \max(0.0, C - L)$$
     - Split allocation:
       $$g_{\text{ns}} = \max\left(10.0, G_{\text{total}} \times \frac{y_{\text{ns}}}{Y}\right), \quad g_{\text{ew}} = \max\left(10.0, G_{\text{total}} \times \frac{y_{\text{ew}}}{Y}\right)$$
       (if $Y = 0$, splits are $G_{\text{total}} / 2$).
3. **Legal Cycle Boundary Transition**:
   - The newly solved plan is staged as `pending_plan`.
   - The ongoing cycle is **never truncated mid-phase or mid-cycle**.
   - The new plan is applied strictly when the ongoing cycle completes and the signal machine enters `NS` GREEN at the start of the next cycle.
   - Once applied, the plan remains fixed for the rest of the simulation.
4. **Plan Log**:
   - Emitted to `plan_log.json` detailing the initial BTP plan and the measured Webster plan with measured approach flows.

### Justification of Warm-up Window (300 s / 5 min)
- At medium demand (~1400 vph total), ~115 vehicles arrive across 4 approaches in 300 s (~20–40 per approach), providing statistically sufficient samples to compute flow ratios $y_{\text{ns}}, y_{\text{ew}}$ while leaving 1500 s (83% of the 1800 s demand horizon) to evaluate the measured fixed plan.

---

## 2. `webster_recalc` (Periodically Recalculated Webster Baseline)

### Algorithm
1. **Periodic Evaluation Interval**: $N = 300\text{ s}$ (5 minutes).
2. **Sliding Measurement Window**: $W = 300\text{ s}$ (5 minutes).
3. **Execution**:
   - During $t < 300\text{ s}$, executes the baseline BTP plan.
   - At each evaluation timestamp $t_k \in \{300, 600, 900, 1200, 1500\text{ s}\}$, extracts arrivals in the sliding window $[t_k - W, t_k]$.
   - Solves the canonical Webster formula (identical to Section 1).
   - Staged as `pending_plan`.
4. **Legal Cycle Boundary Transition**:
   - Staged plans are applied **only at the subsequent transition to NS GREEN** (a legal cycle boundary).
   - If multiple recalculations occur before a long cycle finishes (rare), the latest valid solution takes effect.
5. **Plan Log**:
   - Logs every plan adjustment, transition timestamp, cycle index, and measured approach flows into `plan_log.json`.

---

## 3. `fixed_matched_cycle` (Cycle-Matched BTP Split Baseline)

### Algorithm & Purpose
- **Purpose**: Separates the benefit of **cycle length optimization** from **directional split adaptation**.
- **Cycle Length**: Matches the exact Webster optimal cycle $C_{\text{webster}}$ for the given scenario and demand level:
  $$C_{\text{matched}} = g_{\text{ns, webster}} + g_{\text{ew, webster}} + 10.0\text{ s}$$
- **Split Ratio**: Fixed to the field-measured BTP split ratio of 105 s : 95 s:
  - Total effective green: $G_{\text{total}} = C_{\text{matched}} - 10.0\text{ s}$.
  - Marathahalli real-road site:
    - Varthur Road (EW) is Phase 1 (105 s): $f_{\text{EW}} = 105 / 200 = 0.525$ (52.5%).
    - Outer Ring Road (NS) is Phase 2 (95 s): $f_{\text{NS}} = 95 / 200 = 0.475$ (47.5%).
    $$g_{\text{ew}} = \max(10.0, \text{round}(0.525 \times G_{\text{total}}, 1))$$
    $$g_{\text{ns}} = \max(10.0, \text{round}(G_{\text{total}} - g_{\text{ew}}, 1))$$
  - Synthetic network:
    - Phase 1 mapped to NS (52.5%), Phase 2 to EW (47.5%).
- Remains fixed for the entire simulation run.
- Emits `plan_log.json` containing the matched cycle, split percentages, and Webster original splits.

---

## 4. `sumo_actuated` (SUMO Native Actuated Logic with Detectors)

### Specification & Parameter Provenance
SUMO's built-in `type="actuated"` logic operates natively within SUMO's microsimulation kernel while wrapped by `PhaseMachineController` to track phase decisions and assert safety invariants:

| Parameter | Value | Description | Provenance / Citation |
|---|---|---|---|
| `minDur` | 10.0 s | Minimum green duration before gap-out | Project safety lower bound (`C.ACTION.min_green_s`, `C.ADAPTIVE.min_green_s`) |
| `maxDur` | 60.0 s | Maximum green duration before forced switch | Project safety upper bound (`C.ACTION.max_green_s`, `C.ADAPTIVE.max_green_s`) |
| `max-gap` | 3.0 s | Max headway between vehicles to extend green | Eclipse SUMO documentation default for actuated controllers |
| `detector-gap` | 3.0 s | Distance / time threshold for detector activation | Eclipse SUMO documentation default |
| `yellow` | 3.0 s | Yellow clearance interval | Fixed safety invariant (`config.TIMING.yellow_s`) |
| `all-red` | 2.0 s | All-red clearance interval | Fixed safety invariant (`config.TIMING.all_red_s`) |

**Citation**:
- Eclipse SUMO User Documentation: *Simulation / Traffic Lights - Actuated Traffic Lights*, SUMO v1.21.0. https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#actuated_traffic_lights

---

## 5. `webster_oracle` (Diagnostic Ground-Truth Webster Baseline)

### Specification
- **Label**: Explicitly designated as `[ORACLE]` across all code, logs, and artifacts.
- **Diagnostic Role**: Excluded from the competitive evaluation matrix.
- **Algorithm**: Uses `FixedWebsterController` with mathematical arrival curves derived from offline ground-truth scenario definitions (`dp1/site_scenarios.py:SITE_DEMAND_PATTERNS`).
- **Purpose**: Establishes the theoretical upper bound for static Webster optimization when the arrival distribution is known perfectly a priori without measurement delay or sensor error.
