# Phase 12: Short-Horizon Queue Projection Specification

**Status:** Pre-Registered & Frozen Specification  
**Parent Documents:** [`docs/SPEC.md`](file:///e:/dp1-traffic-signal/docs/SPEC.md), [`docs/ablation_ladder.md`](file:///e:/dp1-traffic-signal/docs/ablation_ladder.md), [`configs/final_hybrid_queue_adaptive.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_queue_adaptive.yaml)

---

## 1. Overview & Research Objective

Phase 12 investigates a localized, legitimate **Short-Horizon Predictive Intervention** for the explainable hybrid traffic signal controller (`hybrid_queue_adaptive`). 

Unlike black-box or non-causal forecasting models (LSTM, GRU, XGBoost, or long-horizon predictors), this feature operates strictly within the causal boundary of the physical controller: **only sensor measurements available up to the current simulation second $t$ are utilized**.

The objective is to test whether short-horizon linear rate projection ($h = 3\text{--}12\text{ s}$) improves signal decision-making—particularly by anticipating competing queue accumulation during extended green phases—or whether measurement noise and detector truncation render reactive control superior.

---

## 2. Version A: Measured-Rate Projection (No New Sensors)

Version A uses strictly existing stop-line E2 lane-area detector queue readings and phase state machine timings.

### 2.1 Arrival Rate Estimation $\lambda_i(t)$

For approach $i \in \{\text{N}, \text{S}, \text{E}, \text{W}\}$ over a sliding window $W$ (default $W = 15\text{ s}$):

#### A. When Approach $i$ is RED:
During the red phase, vehicles cannot discharge through the intersection ($\mu_i = 0$). Any increase in the measured queue length $\Delta q_i$ over a time interval $\Delta t$ is strictly driven by incoming arrivals:
$$\lambda_i^{\text{red}}(t) = \frac{\max(0, q_i(t) - q_i(t - W_{\text{red}}))}{W_{\text{red}}} \quad [\text{m/s}]$$

#### B. When Approach $i$ is GREEN:
During the green phase, vehicles discharge across the stop-line at rate $\mu_i$ while new vehicles may join the rear of the queue. By hydrodynamic queue conservation:
$$\frac{dq_i}{dt} = \lambda_i - \mu_i \implies \lambda_i^{\text{green}}(t) = \max\left(0, \frac{q_i(t) - q_i(t - W_{\text{green}})}{W_{\text{green}}} + \mu_i(t)\right) \quad [\text{m/s}]$$

To maintain numerical stability, $\lambda_i(t)$ is maintained as an exponential moving average (EMA) of recent arrival rate samples:
$$\bar{\lambda}_i(t) = (1 - \beta) \cdot \bar{\lambda}_i(t - 1) + \beta \cdot \lambda_i(t), \quad \beta = \frac{1}{\max(1, W)}$$

#### C. Approximation Errors & Sensor Limitations:
1. **Detector Truncation / Saturation:** The stop-line E2 detectors span $24.4\text{ m}$ on Marathahalli approaches. When the physical queue exceeds $24.4\text{ m}$, the detector reports saturation ($24.4\text{ m}$), causing $\Delta q_i = 0$. Under saturation, arrivals occurring beyond $24.4\text{ m}$ are invisible to stop-line sensors. The estimator holds the last valid pre-saturation arrival rate $\lambda_i^{\text{last}}$ rather than falsely estimating zero arrivals.
2. **Platoon Dispersion:** Arrivals at the rear of the queue are unmeasured until vehicles decelerate into the queue detection zone ($v < 1.4\text{ m/s}$).

---

### 2.2 Discharge Rate Estimation $\mu_i(t)$

Discharge represents queue clearance capacity during green service:

1. **Observed Discharge Rate:** When approach $i$ is GREEN and $q_i(t) > 0$:
   $$\mu_i^{\text{obs}}(t) = \max\left(0, \frac{q_i(t - \Delta t) - q_i(t)}{\Delta t}\right) \quad [\text{m/s}]$$
2. **Saturation Flow Fallback ($\mu_{\text{sat}}$):** When queue discharge fluctuates or when green phase initiates from rest, the controller falls back to the theoretical saturation flow rate used by Webster's formula in `dp1/config.py`:
   - Saturation flow per lane: $s = 1800\text{ veh/hr/lane} = 0.5\text{ veh/s/lane}$.
   - For a 2-lane approach: $S = 1.0\text{ veh/s}$.
   - Nominal space headway / effective vehicle length: $L_{\text{veh}} = 7.5\text{ m/veh}$.
   - Saturation discharge rate in queue metres:
     $$\mu_{\text{sat}} = 1.0\text{ veh/s} \times 7.5\text{ m/veh} = 7.5\text{ m/s}$$
   - When active queue is positive during green, $\mu_i(t) = \mu_{\text{sat}}$ unless free-flow clearance is observed.

---

### 2.3 Short-Horizon Projection Formula

For each approach $i$, the projected queue $q_{\text{pred}, i}$ over horizon $h$ [seconds] is defined as:

$$q_{\text{pred}, i}(t + h) = \max\left(0, q_i(t) + \bar{\lambda}_i(t) \cdot h - \mu_i(t) \cdot g_i(h)\right) \quad [\text{metres}]$$

Where:
- $q_i(t)$: Current measured queue on approach $i$ [m].
- $\bar{\lambda}_i(t)$: Estimated arrival rate on approach $i$ [m/s].
- $h$: Short prediction horizon [s] ($h \in [3.0, 12.0\text{ s}]$).
- $\mu_i(t)$: Estimated discharge rate on approach $i$ [m/s].
- $g_i(h)$: Planned service time granted to approach $i$ over horizon $h$ [s]:
  - If approach $i$ is **ACTIVE (GREEN)**: $g_i(h) = \min(h, \text{remaining approved green headroom})$.
  - If approach $i$ is **COMPETING (RED)**: $g_i(h) = 0\text{ s}$ (no service during red, $\mu_i \cdot g_i = 0$).
  - Therefore, on red: $q_{\text{pred}, i} = q_i + \bar{\lambda}_i \cdot h$.

---

### 2.4 Queue Blending & Saturation Invariant

The effective queue $q_{\text{eff}, i}$ used by the controller is a linear convex combination of measured queue $q_i$ and projected queue $q_{\text{pred}, i}$:

$$q_{\text{eff}, i} = (1 - \alpha) \cdot q_i + \alpha \cdot q_{\text{pred}, i}, \quad \alpha \in [0.0, 1.0]$$

#### Saturation Guard:
If the measured queue is saturated ($q_i \ge 24.0\text{ m}$ on Marathahalli):
- The controller flags `is_saturated = True`.
- Projection is clamped: $q_{\text{pred}, i} \le q_{\text{sat}} + \bar{\lambda}_i \cdot h \le 24.4\text{ m} + 15.0\text{ m} = 39.4\text{ m}$.
- The controller never treats saturated readings as unbounded linear extrapolations.

---

### 2.5 Auditability & Counterfactual Decision Logging

Every controller evaluation step logs both the actual projected decision and the **counterfactual non-projected decision** (evaluated with $\alpha = 0$):
- `lambda_N`, `lambda_S`, `lambda_E`, `lambda_W`: Estimated arrival rates [m/s].
- `mu_active`: Active discharge rate [m/s].
- `q_pred_N`, `q_pred_S`, `q_pred_E`, `q_pred_W`: Projected queue lengths [m].
- `projection_divergence`: Boolean (`True` if $q_{\text{pred}}$ caused an action different from pure $q$).
- `counterfactual_action`: What the controller would have done without projection (`HOLD`, `EXTEND`, `SWITCH_DEMAND_FAIRNESS`, etc.).
- `projection_reason`: Explains the predictive contribution (e.g. *"Competing East–West queue projected to reach 18.2m within 6s; triggered proactive demand fairness switch"*).

---

## 3. Version B: Upstream Detector Model (Future Work Specification)

Version B is **NOT implemented** in Phase 12 per pre-registration instructions. The requirements for future implementation are:
1. **Network Geometry Changes:** Add advance inductive loop detectors (`det_adv_*`) placed $80\text{--}120\text{ m}$ upstream of each junction approach.
2. **SUMO Network Recompilation:** Update `sumo/marathahalli.net.xml` and `sumo/marathahalli.det.xml` with E1 induction loops.
3. **Travel-Time Propagation Model:** Measure speed $v_{\text{adv}}$ at the upstream detector and propagate arrivals using ballistic delay: $t_{\text{arrive}} = t + d_{\text{advance}} / v_{\text{adv}}$.

---

## 4. Pre-Registered Search Space & Acceptance Rule

### Hyperparameter Search Space (Tuned on Seeds 101–105):
All baseline hybrid parameters (from [`configs/final_hybrid_queue_adaptive.yaml`](file:///e:/dp1-traffic-signal/configs/final_hybrid_queue_adaptive.yaml)) remain **strictly frozen**. Only 3 projection parameters are tuned:

| Parameter | Type | Min | Max | Default | Scale | Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `projection_window_s` ($W$) | float | 10.0 | 30.0 | 15.0 | Linear | Sliding window for arrival rate smoothing. |
| `projection_horizon_s` ($h$) | float | 3.0 | 12.0 | 6.0 | Linear | Lookahead horizon for predictive intervention. |
| `projection_blend_alpha` ($\alpha$) | float | 0.2 | 0.8 | 0.5 | Linear | Weight given to projected queue vs measured queue. |

### Pre-Registered Acceptance Rule (Gated on Validation Seeds 106–110):
- **KEEP Criteria:**
  1. Mean Composite Score on validation seeds 106–110 improves over frozen baseline by $\ge 1.0\%$ ($\Delta \text{Composite} \le -0.010$).
  2. Approach wait gap does not worsen by $> 2.0\%$ ($\Delta \text{Gap} \le +0.02 \times \text{Gap}_{\text{base}}$).
  3. No safety invariant violations (zero clearance violations, zero direct green-to-green transitions).
- **CUT Criteria:**
  - If composite score improves by $< 1.0\%$, worsens, or causes instability, projection is declared **CUT**.
  - It will **not** be rescued by retuning. It will be reported honestly as a negative finding, recommending the paper wording *"proactive, state-aware intervention"*.
