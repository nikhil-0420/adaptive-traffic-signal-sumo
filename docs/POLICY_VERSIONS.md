# DP1 Policy Version Registry & Lineage

This document tracks the explicit definition, provenance, and experimental history of all traffic signal controller policies in the DP1 repository. It records where meanings evolved, which earlier experiments used oracle-seeded baselines, and the exact git tags where policy definitions changed.

---

## Policy Version Table

| Policy Identifier | Version | Meaning / Implementation | Experiments Used In | Git Tag Transition | Oracle Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fixed` | v1.0 | Static fixed-time plan (BTP baseline: 95s NS / 105s EW for Marathahalli). | Phases 1–10B (all runs) | `dp1-v1.0` | Non-oracle |
| `fixed_webster` | v1.0 | Fixed-time Webster plan derived from offline mathematical scenario demand curves. | Phases 1–10B | `dp1-v1.0` | **ORACLE** |
| `webster_oracle` | v1.0 | Explicit alias for `fixed_webster` to denote true offline mathematical scenario demand curves. | Phase 9–10B | `cda9433` | **ORACLE** |
| `webster_measured` | v1.0 | Fixed-time Webster plan with flows measured empirically during a 300 s warm-up window (BTP warm-up plan: 19s NS / 21s EW). Non-oracle reference. | Phases 9–10B | `cda9433` | Non-oracle |
| `webster_recalc` | v1.0 | Recalculated Webster baseline updated every 300 s using a 300 s sliding window of measured vehicle arrivals. | Phases 9–10B | `cda9433` | Non-oracle |
| `fixed_matched_cycle` | v1.0 | Fixed-time plan matching scenario Webster cycle length with BTP split ratio (47.5% NS / 52.5% EW). | Phases 9–10B | `cda9433` | Semi-oracle (cycle from scenario demand) |
| `sumo_actuated` | v1.0 | SUMO native detector-actuated logic (minDur=10s, maxDur=60s, max-gap=3.0s). Non-oracle reference. | Phases 9–10B | `cda9433` | Non-oracle |
| `adaptive` | v1.0 | Queue-proportional green allocation ($G = G_{min} + k \cdot Q$). | Phases 1–10B | `dp1-v1.0` | Non-oracle |
| `pressure` | v1.0 | Queue-differential green allocation ($G = G_{min} + k \cdot \Delta Q$). | Phases 1–10B | `dp1-v1.0` | Non-oracle |
| `queue_extension` | v1.0 | Bounded queue-extension with anti-monopoly waiting limits and 3s increments. | Phases 2–10B | `dp1-v2.0` | Non-oracle |
| `rl_dqn` | v1.0 | Trained Deep Q-Network discrete action policy ($HOLD=0, SWITCH=1$). | Phases 6–10B | `dp1-v6.0` | Non-oracle |
| `hybrid_oracle_seeded` | v1.0 | **Legacy Hybrid Policy**: Base green ($G_{base}$) seeded directly from `site_webster_plan` / `SITE_DEMAND_PATTERNS` table. | Phase 7B, Phase 8 (`exp_marathahalli_hybrid_840`), Phase 10 (`R0`) | `f7ec5a6` (introduced), renamed in `dp1-phase10b-policy` | **ORACLE-SEEDED** |
| `hybrid_queue_adaptive` | v1.0 (Deprecated) | Former name for `hybrid_oracle_seeded`. Leaked true scenario demand table into base green. | Phase 7B, Phase 8 (`exp_marathahalli_hybrid_840`), Phase 10 (`R0`) | Deprecated at `dp1-phase10b-policy` | **ORACLE-SEEDED** |
| `hybrid_queue_adaptive` | **v2.0 (Current Default)** | **De-oracled Proposed Policy**: Base green initialized to non-oracle empirical baseline (19s NS / 21s EW, matching BTP ratio). Measured flows over 300 s warm-up derive Webster cycle/split; applied at next cycle boundary. Rungs: `("R4",)`. | Phase 10B onwards (`exp_ladder_R3_amend_val2`, `exp_headroom_recheck_dev`) | `dp1-phase10b-policy` | **Non-oracle** |
| `hybrid_r2` | v1.0 | Hybrid with R2: Comparative extension ($score_{act} > margin \cdot score_{comp} + switch\_cost$). | Phase 10 | `b3771d3` | Evaluated (CUT) |
| `hybrid_r3` | v2.0 | Hybrid with R3 amendment: Evaluated on top of de-oracled default (R4 + R3 queue-aware fairness). | Phase 10B | `dp1-phase10b-policy` | Non-oracle |
| `hybrid_r4` | v1.0 | Explicit alias for `hybrid_queue_adaptive` v2.0 (R4 measured base green). | Phase 10 (evaluated), Phase 10B (promoted to default) | `b3771d3` | Non-oracle |

---

## Key Transitions & Historical Clarification

1. **Phase 8 Non-Triviality & Headroom Comparison (`exp_marathahalli_hybrid_840`)**:
   - The hybrid policy evaluated in Phase 8 was `hybrid_queue_adaptive` **v1.0 (Oracle-Seeded)**.
   - Its baseline green $G_{base}$ was seeded directly from `site_webster_plan(scenario, demand_level)`.
   - The comparison baseline was `fixed_webster` (also oracle-seeded).
   - Furthermore, all queue metrics in Phase 8 were detector-clipped at $\approx 24.0\text{ m}$.
   - **Conclusion**: Phase 8 headroom conclusions are invalidated and replaced by Phase 10B Task 5 de-oracled evaluations.

2. **Phase 10 Ablation Ladder (`R0`–`R5`)**:
   - `R0` reference policy was `hybrid_queue_adaptive` **v1.0 (Oracle-Seeded)**.
   - `R4` tested measured base green ($300\text{ s}$ warm-up), which successfully eliminated oracle leakage.
   - In Phase 10B, `R4` was adopted as an architectural validity fix, making it the new default `hybrid_queue_adaptive` (v2.0).

3. **Manifest Integration**:
   - All experiment manifests generated from Phase 10B onwards record explicit `policy_versions` mapping to eliminate ambiguity regarding which policy version executed each run.
