# Phase 12: Short-Horizon Queue Projection Specification (Negative Result & Archival)

**Status:** Evaluated and **CUT** (Negative Result)  
**Parent Documents:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md), [`docs/PREREGISTRATION_AMENDMENT_2.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_2.md), [`docs/phase12_report.md`](file:///e:/dp1-traffic-signal/docs/phase12_report.md)  
**Reference Config:** [`configs/experimental_hybrid_projection.yaml`](file:///e:/dp1-traffic-signal/configs/experimental_hybrid_projection.yaml)  

---

## 1. Research Summary & Negative Result Declaration

Phase 12 formulated and tested a causal, short-horizon predictive intervention ($h = 3\text{--}12\text{ s}$) using local stop-line detector observations.

### Rigorous Evaluation Outcome:
- **Verdict:** **CUT**.
- Under pre-registered acceptance criteria (`docs/PREREGISTRATION.md` Section 6), a feature is retained only if at least one primary metric demonstrates a statistically significant improvement whose 95% bootstrap confidence interval strictly excludes zero.
- On 90 paired validation runs (seeds 106–110 across all 18 conditions):
  - P95 waiting time delta: $-4.69\text{ s}$ (95% CI `[-13.69, +4.33] s`, spans zero).
  - Approach wait gap delta: $-0.43\text{ s}$ (95% CI `[-3.53, +2.60] s`, spans zero).
  - Extended max queue (`gt_ext_max_queue_m`): UNKNOWN (detector-visible `max_queue_m` worsened by $+3.96\text{ m}$).
  - Composite index delta: $-1.81\%$ (95% CI `[-0.0456, +0.0090]`, spans zero).
- Because no primary metric achieved statistically significant improvement, the feature is **CUT** from the production controller. `projection_enabled` is set to `False` by default in `dp1/config.py`.

### Recommended Academic Reporting Language:
When describing controller adaptations in the DP1 report or defense, do not claim predictive superiority or queue forecasting. Instead, characterize the hybrid controller as employing:
> **"A proactive, state-aware intervention"** (or *"real-time state-dependent phase extension"*).

---

## 2. Specification Formulation (Archival Reference)

The mathematical formulation below is preserved for research auditability and experimental reproduction.

### 2.1 Arrival Rate Estimation $\lambda_i(t)$
For approach $i \in \{\text{N}, \text{S}, \text{E}, \text{W}\}$ over sliding window $W = 15.0\text{ s}$:
- **During Red:** $\lambda_i^{\text{red}}(t) = \frac{\max(0, q_i(t) - q_i(t - W_{\text{red}}))}{W_{\text{red}}}$.
- **During Green:** $\lambda_i^{\text{green}}(t) = \max\left(0, \frac{q_i(t) - q_i(t - W_{\text{green}})}{W_{\text{green}}} + \mu_i(t)\right)$.
- Maintained as an exponential moving average (EMA) with $\beta = 1 / W$.
- **Sensor Limit:** The stop-line E2 detectors span $24.4\text{ m}$. When saturated ($q_i \ge 24.0\text{ m}$), new vehicle arrivals outside the detection area cannot be measured directly, so the estimator freezes its prior arrival rate.

### 2.2 Discharge Rate Estimation $\mu_i(t)$
- Measured discharge: $\mu_i^{\text{obs}}(t) = \max\left(0, \frac{q_i(t - \Delta t) - q_i(t)}{\Delta t}\right)$ during green.
- Physical fallback: Saturation flow rate $\mu_{\text{sat}} = 7.5\text{ m/s}$ (corresponding to two lanes at 1800 vph/lane and 7.5 m effective vehicle length).

### 2.3 Projected Queue Formulation
$$q_{\text{pred}, i}(t + h) = \max\left(0, q_i(t) + \bar{\lambda}_i(t) \cdot h - \mu_i(t) \cdot g_i(h)\right)$$
- Lookahead horizon: $h = 6.0\text{ s}$.
- Blending: $q_{\text{eff}, i} = (1 - \alpha) \cdot q_i + \alpha \cdot q_{\text{pred}, i}$ with $\alpha = 0.50$.

---

## 3. Findings & Limitations

1. **Short Detector Span:** At high saturation levels, the stop-line detector saturation boundary ($24.4\text{ m}$) blinds the projection model to upstream ramp accumulation.
2. **Platoon Dynamics:** In urban corridors like Marathahalli, vehicle arrivals are bursty and platooned rather than continuous Poisson streams. Linear rate projection over a 6-second window tends to over-react to momentary gaps or bursts.
3. **Reactive Control Sufficiency:** Reactive extension with comparative queue thresholding (`hybrid_queue_adaptive`) provides equivalent delay mitigation without the variance introduced by short-horizon arrival estimation.
