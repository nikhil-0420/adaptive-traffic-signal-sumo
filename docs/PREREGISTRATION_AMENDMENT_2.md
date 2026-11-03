# Pre-Registration Amendment 2: Extended Ground-Truth Queue Metric and Spillover Horizon

**Date:** 2026-11-03  
**Status:** Frozen and Pre-Registered (Phase 10C)  
**Parent Documents:** [`docs/PREREGISTRATION.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION.md), [`docs/PREREGISTRATION_AMENDMENT_1.md`](file:///e:/dp1-traffic-signal/docs/PREREGISTRATION_AMENDMENT_1.md)

---

## 1. Motivation and Context

In Pre-Registration Amendment 1, the primary queue metric was updated from detector-visible queue (`max_queue_m`, clipped at $\approx 24.00\text{ m}$) to microscopic ground-truth queue on the approach legs (`gt_max_queue_m`). However, the approach legs at the Marathahalli junction are physically bounded by their stop-line-to-ramp boundary lengths ($31.60\text{ m}$ to $34.18\text{ m}$). 

Diagnostic analysis revealed:
1. In heavy traffic conditions (e.g. `imbalanced_orr` heavy), queues regularly spilled upstream beyond the junction leg onto the predecessor approach ramps (`ramp_orr_n_in`, `ramp_orr_s_in`, `ramp_wf_in`, `ramp_hal_in`).
2. Under such spillover, `gt_max_queue_m` was artificially capped at the physical leg boundary ($31.6\text{ m}–34.2\text{ m}$), compressing differences between policies during severe congestion.

Phase 10C resolves this by extending microscopic ground-truth queue tracking across the approach leg, junction internal connector lanes, and the upstream inbound ramp edges.

---

## 2. Primary Metric Formal Redefinition: Extended Ground-Truth Maximum Queue

The primary metric **`max queue`** is hereby formally redefined as **`gt_ext_max_queue_m`** (extended ground-truth maximum queue length in metres across the approach leg and upstream ramp).

### Metric Hierarchy:
- **Primary Metric:** `gt_ext_max_queue_m` (evaluation-only microscopic extent across approach leg + internal connector + upstream ramp).
- **Secondary Reference Metrics:**
  - `gt_ext_avg_queue_m`: Time-averaged extended ground-truth queue across all four approaches.
  - `gt_max_queue_m`: Approach leg ground-truth queue (evaluation-only, bounded at $31.60\text{ m}–34.18\text{ m}$).
  - `max_queue_m`: Sensor-visible detector queue (controller-visible, clipped at $\approx 24.00\text{ m}$).

---

## 3. Microscopic Queue Definition and Propagation Rules

The extended queue is computed at every simulation step by `QueueMeasurementEngine._compute_chain_ground_truth(lane_chain)` using the following rules:

1. **Halting Speed Threshold:**
   A vehicle is classified as stopped/queued if its instantaneous velocity satisfies:
   $$v < 1.4\text{ m/s}\quad (5.04\text{ km/h})$$
   (standard SUMO halting threshold).

2. **Stop-Line Anchorage Condition:**
   The lead vehicle of the cluster must be within $15.0\text{ m}$ of the approach stop line. If no stopped vehicle is present within $15.0\text{ m}$ of the stop line, the queue for that lane chain is $0.0\text{ m}$.

3. **Contiguous Cluster Headway Rule:**
   Successive stopped vehicles belong to the same contiguous queue if and only if the bumper-to-bumper gap satisfies:
   $$\text{gap} = \text{dist\_to\_front}_{i} - \text{dist\_to\_back}_{i-1} \le 7.5\text{ m}$$
   If any gap exceeds $7.5\text{ m}$, or if an intermediate vehicle is moving at $v \ge 1.4\text{ m/s}$, the queue cluster terminates immediately.

4. **Multi-Lane Extent Horizon across Inbound Chains:**
   Vehicles are tracked along continuous physical lane chains ordered from stop line upstream:
   $$\text{chain} = [\text{leg\_lane}, \text{internal\_connector\_lane}, \text{ramp\_lane}]$$
   Cumulative distance is calculated from the junction stop line:
   - **North Approach (ORR North / K.R. Puram):**
     - `leg_orr_n_in` ($32.60\text{ m}$) $\xrightarrow{:node\_junc\_n\_0}$ ($0.10\text{ m}$) $\xrightarrow{}$ `ramp_orr_n_in` ($131.04\text{ m}$)
     - Total measurement extent: **$163.74\text{ m}$**
   - **South Approach (ORR South / Kadubeesanahalli):**
     - `leg_orr_s_in` ($31.60\text{ m}$) $\xrightarrow{:node\_junc\_s\_2}$ ($0.10\text{ m}$) $\xrightarrow{}$ `ramp_orr_s_in` ($96.04\text{ m}$)
     - Total measurement extent: **$127.74\text{ m}$**
   - **East Approach (Varthur Rd / Whitefield):**
     - `leg_wf_in` ($34.18\text{ m}$) $\xrightarrow{:node\_junc\_e\_0}$ ($0.42\text{ m}$) $\xrightarrow{}$ `ramp_wf_in` ($112.96\text{ m}$)
     - Total measurement extent: **$147.56\text{ m}$**
   - **West Approach (Varthur Rd / HAL Old Airport Rd):**
     - `leg_hal_in` ($34.18\text{ m}$) $\xrightarrow{:node\_junc\_w\_2}$ ($1.27\text{ m}$) $\xrightarrow{}$ `ramp_hal_in` ($103.36\text{ m}$)
     - Total measurement extent: **$138.81\text{ m}$**

5. **Approach Aggregation:**
   Longitudinal approach queue is the **maximum** across parallel lanes of that approach (NEVER summed):
   $$Q_{\text{ext, approach}} = \max_{\text{chain} \in \text{approach}} Q_{\text{ext, chain}}$$

---

## 4. Remaining Physical Limit and Spillover Boundary

While the extended queue horizon expands visibility by approximately $4\times$ to $5\times$ over the approach leg, an ultimate physical boundary remains:
- **Boundary Horizon:** If a queue backs up beyond the upstream ramp entry point ($127.74\text{ m}$ to $163.74\text{ m}$ depending on approach), stopped vehicles spill onto the mainline arterial merges (`orr_n_in`, `orr_s_in`, `wf_in`, `hal_in`).
- **Empirical Boundedness:** In Phase 10C regression tests under heavy demand (`imbalanced_orr` heavy, seed 101), the observed maximum extended queue was $58.62\text{ m}$ (on Approach N). Across all tested validation cells, the queue remains strictly bounded within the $127.74\text{ m}–163.74\text{ m}$ ramp horizon.
- If in extreme overload conditions a queue exceeds this horizon, the metric reports the maximum extent within the tracked chain and flags the boundary condition.

---

## 5. Strict Sensor Boundary Invariant

As required by core safety and fairness rules:
- **Controllers still receive ONLY the detector queue:** The sensor readings provided to controllers via `q[approach]` originate strictly from the physical E2 lane-area detectors ($24.9\text{ m}$ span).
- The extended ground-truth metric (`gt_ext_max_queue_m`) is strictly an **evaluation-only** metric logged to `timeseries.csv` (`gt_ext_q_N/S/E/W`) and `metrics.json`.
- Decision logic in controllers is completely untouched and possesses zero knowledge of upstream ramp vehicle queues.
