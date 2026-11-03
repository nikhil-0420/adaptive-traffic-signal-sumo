# DP1 Ablation Ladder: Hybrid Controller Improvements

Evaluated on **validation seeds (106–110)** across all 18 demand conditions (12 stationary + 6 non-stationary).
All keep/cut decisions strictly follow the pre-registered protocol in `docs/PREREGISTRATION.md`.

| Rung | Name | Status | Change Description | Validation Deltas (vs Prev Rung) | 95% Bootstrap CI | Verdict | Rule Evaluation / Reason |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| **R0** | Current Frozen Hybrid | REFERENCE | Reference hybrid controller untouched (flags off). | Baseline (0.00) | N/A | **REFERENCE** | Frozen reference baseline for ablation comparisons. |
| **R1** | Gap-out + HOLD default | NOT JUSTIFIED | Early gap-out request and default HOLD when no demand. | Skipped | Skipped | **SKIPPED** | NOT JUSTIFIED per Phase 7 diagnostics: D10 proved gap-out is already active in 36.54% of decisions; min green of 13.0s is already enforced. |
| **R2** | Comparative Extension | JUSTIFIED | Extend only if score_active > margin * score_competing + switch_cost (5.0m = 5s lost time). Replaces fixed 4m threshold. | P95: +1.01s, MaxQ: +0.01m, Gap: +0.74s, MeanWait: +0.08s (+0.12%) | P95 CI: [-2.85, 4.90], MaxQ CI: [-0.05, 0.06], Gap CI: [-0.64, 2.22] | **CUT** | No primary metric 95% CI strictly excludes zero in favor of candidate |
| **R3** | Queue-Aware Fairness | JUSTIFIED | Scale soft competing wait limit by competing queue size; no switch if empty; retain 35s hard cap. | P95: +0.22s, MaxQ: -0.01m, Gap: -1.23s, MeanWait: -0.33s (-0.48%) | P95 CI: [-3.75, 3.93], MaxQ CI: [-0.06, 0.03], Gap CI: [-2.48, 0.04] | **CUT** | No primary metric 95% CI strictly excludes zero in favor of candidate |
| **R4** | Measured Webster Base Green | JUSTIFIED | De-oracle base green: derive from 300s warm-up measured arrival flows at cycle boundary. | P95: -1.17s, MaxQ: +0.13m, Gap: +0.68s, MeanWait: -0.25s (-0.36%) | P95 CI: [-9.40, 6.46], MaxQ CI: [-0.16, 0.41], Gap CI: [-2.06, 3.45] | **CUT** | No primary metric 95% CI strictly excludes zero in favor of candidate |
| **R5** | Longer Detectors | NOT JUSTIFIED | Physically extend E2 lane-area detectors upstream. | Skipped | Skipped | **SKIPPED** | NOT JUSTIFIED per Phase 7 diagnostics: D8 proved physical edge headroom before upstream merge junctions is only 6.6m–9.2m (~1 vehicle). Geometrically unviable without crossing merge nodes. |

---
