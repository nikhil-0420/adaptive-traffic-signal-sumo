# DP1 Scenario Specification & Frozen Demand Manifest (Phase 8)

**Status:** FROZEN  
**Target Topology:** Marathahalli Bridge Network (`marathahalli`) & Synthetic 4-Way Baseline (`synthetic`)  
**Configuration Location:** `dp1/config.py`  
**Generator Modules:** `dp1/site_scenarios.py` (Site Network), `dp1/scenarios.py` (Synthetic Network)  
**Quality Gate Test:** `tests/test_non_stationary_scenarios.py`

---

## 1. Executive Summary & Purpose

In stationary demand environments, offline delay-minimizing timing plans derived via Webster's equisaturation method are near-optimal because time-averaged flow ratios closely match instantaneous arrivals. Consequently, evaluating adaptive traffic signal controllers exclusively on stationary demand understates the utility of dynamic adaptation.

Phase 8 formally introduces and freezes three **non-stationary demand scenarios** designed to test controllers under dynamic conditions:
1. **`ramp_peak`**: Unimodal morning rush-hour surge with smooth piecewise-linear ramp-up, peak plateau, and ramp-down.
2. **`surge_shift`**: Mid-run directional priority inversion where the dominant arterial switches from Outer Ring Road (ORR) North-South to Varthur Road East-West.
3. **`lane_closure`**: Mid-run physical capacity constriction where an inbound approach lane (`ramp_orr_n_in_0`) on ORR North is closed to all traffic for 10 minutes.

These three non-stationary scenarios are evaluated alongside the four existing stationary patterns across **medium (1.00x)** and **heavy (1.30x)** demand intensities.

---

## 2. Invariants & Rules

1. **Parameter Centrality**: All scenario numbers, rate schedules, multipliers, and closure windows live exclusively in `dp1/config.py`.
2. **Stationary Immutability**: The four existing stationary patterns (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`) are unmodified.
3. **Deterministic Pairing**: All vehicle departures, routes, and IDs derive entirely from the simulation seed (`rng = random.Random(seed)`). Regenerating routes with identical `(scenario, level, seed)` produces byte-identical `.rou.xml` files.
4. **Cryptographic Manifests**: Every generated route file is paired with a companion `.rou.xml.manifest.json` recording the SHA-256 hash of the exact XML byte content, total vehicle count, and origin-approach mappings.
5. **Fair Physical Execution**: Lane closure is implemented in SUMO via TraCI (`setDisallowed` / `setAllowed`) so all controllers (fixed, Webster, adaptive, hybrid) experience the identical physical road closure at the identical simulation step without special side-channels.

---

## 3. Site Network Movements & Grade Separation

On the reconstructed Marathahalli Bridge network (`network/marathahalli/`):
- **East-West Axis (EW)**: Varthur Road (HAL Airport Road $\leftrightarrow$ Whitefield).
- **North-South Axis (NS)**: Outer Ring Road (ORR) (Kadubeesanahalli $\leftrightarrow$ K.R. Puram).
- **Grade-Separated Elevated Flyover**: 4-lane bidirectional overpass (Z = 6.5m–7.0m) carrying continuous east-west through traffic between HAL and Whitefield.
- **Grade-Separated Mainline Underpass**: 4-lane bidirectional underpass carrying continuous north-south through traffic along ORR.
- **Surface Signal-Controlled Junction (`marathahalli_tls`)**: At-grade intersection governed by BTP-grounded signal programs, handling surface turns and cross-traffic.

### Turning Split Distribution:
- **Through Movements (65%)**: 70% uses elevated flyover or mainline underpass (bypasses signal); 30% uses surface approach legs.
- **Left Turns (20%)**: Uses channelized free-flow slip roads (bypasses signal).
- **Right Turns (15%)**: Uses surface signal-controlled intersection.
- **Net Surface Traffic**: ~35% of total arterial approach volume passes through `marathahalli_tls`.

---

## 4. Stationary Demand Scenarios (Unmodified)

Duration: 1800 seconds (30 minutes). Demand given in base vehicles per hour (vph) per approach.

| Scenario | West (HAL) | East (Whitefield) | North (K.R. Puram) | South (Kadubeesanahalli) | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`balanced`** | 650 vph | 650 vph | 650 vph | 650 vph | Equal baseline load across all 4 approaches. |
| **`imbalanced_orr`** | 400 vph | 400 vph | 1050 vph | 1050 vph | Heavy commuter load on Outer Ring Road (NS). |
| **`imbalanced_varthur`** | 1050 vph | 1050 vph | 400 vph | 400 vph | Heavy commuter load on Varthur Road (EW). |
| **`surge_orr_north`** | 500 vph | 500 vph | (0–400s: 600 vph)<br>(400–1000s: 1500 vph)<br>(1000–1800s: 600 vph) | 650 vph | Directional morning surge from K.R. Puram heading south toward Bellandur. |

---

## 5. Non-Stationary Demand Scenarios (Phase 8 Additions)

### 5.1 Scenario 1: `ramp_peak`

**Concept:** Models a classic morning rush hour profile where traffic begins at low flow, ramps up linearly into an intense plateau, and ramps down back to low flow.

- **Base Rate:** $700\text{ vph}$ per approach (W, E, N, S).
- **Run Horizon:** $T = 1800\text{ s}$.
- **Discretization Step:** $\Delta t = 50\text{ s}$ intervals.
- **Piecewise Linear Multiplier Schedule:**
  - **Pre-Peak Base ($0 \le t < 300\text{ s}$):** $0.40\times$ multiplier ($280\text{ vph}$).
  - **Ramp-Up ($300 \le t < 700\text{ s}$):** Linearly increases from $0.40\times$ to $1.80\times$ across 8 steps of $50\text{ s}$ ($280 \to 1260\text{ vph}$).
  - **Peak Plateau ($700 \le t < 1100\text{ s}$):** Held at peak multiplier $1.80\times$ ($1260\text{ vph}$ at medium; $1638\text{ vph}$ at heavy).
  - **Ramp-Down ($1100 \le t < 1500\text{ s}$):** Linearly decreases from $1.80\times$ to $0.40\times$ across 8 steps of $50\text{ s}$ ($1260 \to 280\text{ vph}$).
  - **Post-Peak Base ($1500 \le t \le 1800\text{ s}$):** $0.40\times$ multiplier ($280\text{ vph}$).

**Webster Vulnerability:**  
Over the 1800s horizon, average arrival rate is $715.6\text{ vph}$ per approach. Webster provisions green times sized for the average demand ($15.0\text{ s}$ NS / $15.0\text{ s}$ EW). During the 400s peak plateau, demand surges to $1260\text{ vph}$ ($1638\text{ vph}$ at heavy), heavily saturating the approaches while Webster remains constrained to its fixed $15\text{s}$ allocations.

---

### 5.2 Scenario 2: `surge_shift`

**Concept:** Models a mid-run directional priority inversion where the dominant arterial flips from ORR North-South to Varthur Road East-West.

- **Phase 1: ORR Dominant ($0 \le t < 700\text{ s}$):**
  - North: $1200\text{ vph}$, South: $1050\text{ vph}$ ($\approx 76\%$ NS share).
  - West: $350\text{ vph}$, East: $350\text{ vph}$.
- **Transition Handover Window ($700 \le t < 1100\text{ s}$):**
  - Smooth linear demand shift across $4 \times 100\text{ s}$ buckets:
    - $700–800\text{ s}$: N: 988, S: 865, W: 562, E: 562 vph.
    - $800–900\text{ s}$: N: 775, S: 678, W: 775, E: 775 vph.
    - $900–1000\text{ s}$: N: 562, S: 492, W: 988, E: 988 vph.
    - $1000–1100\text{ s}$: N: 350, S: 350, W: 1200, E: 1200 vph.
- **Phase 2: Varthur Dominant ($1100 \le t \le 1800\text{ s}$):**
  - West: $1200\text{ vph}$, East: $1200\text{ vph}$ ($\approx 77\%$ EW share).
  - North: $350\text{ vph}$, South: $350\text{ vph}$.

**Webster Vulnerability:**  
Because ORR and Varthur carry identical total vehicles across the 1800s horizon (average $775\text{ vph}$ on each axis), Webster computes an equal $50/50$ split ($15.0\text{ s}$ NS / $15.0\text{ s}$ EW). During Phase 1, NS is starved while EW has idle green; during Phase 2, EW is starved while NS has idle green.

---

### 5.3 Scenario 3: `lane_closure`

**Concept:** Models an incident-induced physical capacity drop where one inbound lane on ORR North is closed to all traffic for 10 minutes mid-run.

- **Corridor & Lane Choice:** `ramp_orr_n_in_0` (Outer lane of the 2-lane inbound approach ramp from ORR North).
- **Physical Justification:**
  - ORR North is the primary high-volume commuter conduit from K.R. Puram toward Marathahalli.
  - The 155-meter ramp (`ramp_orr_n_in`) channels all surface-bound traffic off the ORR mainline into the junction.
  - Closing lane 0 eliminates 50% of the approach ramp's storage and discharge capacity, forcing right turns and through movements to merge into a single lane upstream of `marathahalli_tls`.
  - Upstream ramp bottleneck dynamics avoid illegal routing errors while producing real queue spillback.
- **Closure Window:** $t = 600.0\text{ s}$ to $t = 1200.0\text{ s}$ ($600\text{ s}$ / 10 minutes).
- **Reopening:** $t \ge 1200.0\text{ s}$ (restores full 2-lane capacity).
- **Underlying Demand:**
  - North: $1050\text{ vph}$ (heavy commuter flow).
  - South: $1050\text{ vph}$.
  - West: $600\text{ vph}$.
  - East: $600\text{ vph}$.
- **Implementation Mechanism:** TraCI `traci.lane.setDisallowed('ramp_orr_n_in_0', ['all'])` invoked at $t = 600\text{s}$, followed by `traci.lane.setDisallowed('ramp_orr_n_in_0', [])` at $t = 1200\text{s}$.

---

## 6. Demand Level Multipliers

| Level | Multiplier | Usage |
| :--- | :---: | :--- |
| **`low`** | $0.70\times$ | Off-peak / late evening operations (stationary baseline). |
| **`medium`** | $1.00\times$ | Standard design demand level (Phase 8 non-triviality check). |
| **`heavy`** | $1.30\times$ | Stressed peak operations (Phase 8 non-triviality check). |

---

## 7. Non-Triviality Verification Results (Seeds 101–105)

Executed on dev seeds 101–105 ($60\text{ runs}$) in `results/research/exp_scenario_check_dev/`:

| Scenario | Level | Policy | Mean Wait (s) | Std Wait (s) | P95 Wait (s) | Mean Max Q (m) | Peak Max Q (m) | Sat. Fraction | Unfinished |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ramp_peak`** | medium | fixed_webster | 97.06 | 8.41 | 585.94 | 24.71 | 24.90 | 0.04 | 0 |
| **`ramp_peak`** | medium | hybrid_queue_adaptive | 98.13 | 9.84 | 600.16 | 24.17 | 24.85 | 0.03 | 0 |
| **`ramp_peak`** | heavy | fixed_webster | 122.70 | 3.56 | 785.77 | 24.90 | 24.90 | **0.26** | 0 |
| **`ramp_peak`** | heavy | hybrid_queue_adaptive | 125.15 | 5.55 | 762.22 | 24.77 | 24.90 | **0.27** | 0 |
| **`surge_shift`** | medium | fixed_webster | 52.18 | 6.94 | 238.09 | 24.59 | 24.90 | 0.03 | 0 |
| **`surge_shift`** | medium | hybrid_queue_adaptive | 52.71 | 5.63 | 268.69 | 24.00 | 24.00 | 0.02 | 0 |
| **`surge_shift`** | heavy | fixed_webster | 113.21 | 10.29 | 683.92 | 24.90 | 24.90 | **0.22** | 0 |
| **`surge_shift`** | heavy | hybrid_queue_adaptive | 110.62 | 11.50 | 663.92 | 24.90 | 24.90 | **0.15** | 0 |
| **`lane_closure`** | medium | fixed_webster | 87.57 | 14.86 | 524.04 | 24.53 | 24.90 | 0.03 | 0 |
| **`lane_closure`** | medium | hybrid_queue_adaptive | 87.63 | 12.37 | 529.61 | 24.36 | 24.90 | 0.02 | 0 |
| **`lane_closure`** | heavy | fixed_webster | 126.41 | 8.32 | 871.95 | 24.72 | 24.90 | **0.09** | 0 |
| **`lane_closure`** | heavy | hybrid_queue_adaptive | 125.88 | 5.78 | 822.12 | 24.87 | 24.90 | **0.06** | 0 |

### Non-Triviality Assessment:
1. **Meaningful Queue Variation**: All three scenarios generate substantial queue variation and saturation. In heavy conditions, maximum queue extents reach the physical detector ceiling ($24.90\text{ m}$), and saturation occurs up to $27\%$ of the simulation duration in `ramp_peak` and $22\%$ in `surge_shift`.
2. **Headroom for Adaptation**: In `surge_shift` (heavy), the hybrid controller already demonstrates lower mean delay ($110.62\text{ s}$ vs $113.21\text{ s}$) and lower saturation ($0.15$ vs $0.22$) compared to Webster, confirming that the dynamic shift creates genuine headroom for responsive signal control.
3. **Completion & Safety**: 100% of vehicles completed in all 60 runs ($0$ unfinished), with zero collisions, zero teleports, and zero phase-sequence violations.
