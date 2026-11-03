# DP1 Ablation Ladder: Hybrid Controller Improvements

> [!WARNING]
> **Phase 10B/10C Measurement & Oracle Notice**:
> 1. **Detector-Clipped Metrics in Phase 10**: All `MaxQ` deltas from the original Phase 10 evaluation were derived from E2 detector measurements clipped at $\approx 24.00$\,m (lead-vehicle stopline setback) and are invalid for claims.
> 2. **Phase 10C Extended Ground-Truth Queue**: Ground-truth queue measurement is extended across approach legs ($31.6\text{ m}–34.2\text{ m}$) through internal connectors onto inbound approach ramps ($127.7\text{ m}–163.7\text{ m}$ total horizon). Primary max queue is now `gt_ext_max_queue_m` per Pre-Registration Amendment 2 (`docs/PREREGISTRATION_AMENDMENT_2.md`).
> 3. **R0 was Oracle-Seeded**: The original R0 reference baseline was seeded via `site_webster_plan(scenario, demand_level)`, reading true scenario tables (`SITE_DEMAND_PATTERNS`). It is relabelled `hybrid_oracle_seeded` [ORACLE-SEEDED].
> 4. **R4 Adopted as Validity Fix**: Although R4 failed the strict performance improvement threshold on Phase 10 validation seeds, it was adopted by design mandate as a **VALIDITY FIX** to remove oracle scenario leakage. The de-oracled R4 version is the default `hybrid_queue_adaptive`.

Evaluated on **validation seeds (106–110)** (Phase 10) and **validation-2 seeds (111–120)** (Phase 10B R3 amendment) across all 18 demand conditions (12 stationary + 6 non-stationary).
All keep/cut decisions strictly follow the pre-registered protocol in `docs/PREREGISTRATION.md`, `docs/PREREGISTRATION_AMENDMENT_1.md`, and `docs/PREREGISTRATION_AMENDMENT_2.md`.

| Rung | Name | Status | Change Description | Validation Deltas (vs Prev Rung) | 95% Bootstrap CI | Verdict | Rule Evaluation / Reason |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| **R0** | Legacy Frozen Hybrid | REFERENCE [ORACLE-SEEDED] | Reference hybrid controller (flags off). Leaked scenario demand via `site_webster_plan`. | Baseline (0.00) | N/A | **REFERENCE** | Frozen reference baseline for retrospective comparisons. Relabelled `hybrid_oracle_seeded`. |
| **R1** | Gap-out + HOLD default | NOT JUSTIFIED | Early gap-out request and default HOLD when no demand. | Skipped | Skipped | **SKIPPED** | NOT JUSTIFIED per Phase 7 diagnostics: D10 proved gap-out is already active in 36.54% of decisions; min green of 13.0s is already enforced. |
| **R2** | Comparative Extension | JUSTIFIED | Extend only if score_active > margin * score_competing + switch_cost (5.0m = 5s lost time). Replaces fixed 4m threshold. | P95: +1.01s, MaxQ*: +0.01m, Gap: +0.74s, MeanWait: +0.08s (+0.12%) | P95 CI: [-2.85, 4.90], MaxQ* CI: [-0.05, 0.06], Gap CI: [-0.64, 2.22] | **CUT** | No primary metric 95% CI strictly excludes zero in favor of candidate. (*MaxQ was detector-clipped). |
| **R3** | Queue-Aware Fairness (Phase 10) | JUSTIFIED | Scale soft competing wait limit by competing queue size; no switch if empty; retain 35s hard cap. | P95: +0.22s, MaxQ*: -0.01m, Gap: -1.23s, MeanWait: -0.33s (-0.48%) | P95 CI: [-3.75, 3.93], MaxQ* CI: [-0.06, 0.03], Gap CI: [-2.48, 0.04] | **CUT (Phase 10)** | Failed on 5 validation seeds (106–110); approach gap CI touched zero (+0.04s). Retested under Phase 10B amendment. |
| **R3 (Amend)** | Queue-Aware Fairness (Phase 10B Retest) | AMENDMENT RETEST | Evaluated on validation-2 block (seeds 111–120, n=10, 180 pairs) on top of de-oracled default (R4) with ground-truth MaxQ. | Gap: -0.09s (-0.13%), P95: +0.29s (+0.07%), GT MaxQ: +0.00m (+0.01%), MeanWait: -0.12s (-0.17%) | Gap CI: [-0.90, +0.73], P95 CI: [-2.89, +3.50], GT MaxQ CI: [-0.07, +0.09] | **PERMANENTLY CUT** | Rule 1 FAIL: No primary metric 95% CI strictly excludes zero in favor of candidate. (p=0.8222 vs alpha_holm=0.0167). Permanently cut; not rescued. |
| **R4** | Measured Webster Base Green | VALIDITY FIX | De-oracle base green: derive from 300s warm-up measured arrival flows at cycle boundary. | P95: -1.17s, MaxQ*: +0.13m, Gap: +0.68s, MeanWait: -0.25s (-0.36%) | P95 CI: [-9.40, 6.46], MaxQ* CI: [-0.16, 0.41], Gap CI: [-2.06, 3.45] | **ADOPTED AS VALIDITY FIX** | Adopted as new default `hybrid_queue_adaptive`. Exempt from performance rule; mandatory validity fix removing oracle information. |
| **R5** | Longer Detectors | NOT JUSTIFIED | Physically extend E2 lane-area detectors upstream. | Skipped | Skipped | **SKIPPED** | NOT JUSTIFIED per Phase 7 diagnostics: D8 proved physical edge headroom before upstream merge junctions is only 6.6m–9.2m (~1 vehicle). Geometrically unviable. |

---

## Final Policy State After Ablation Ladder
- **Default Policy (`hybrid_queue_adaptive`)**: R4 (De-oracled empirical base green via 300s warm-up + cycle boundary Webster calculation).
- **R1, R2, R3, R5**: All rejected / cut.
- **Oracle Baseline (`hybrid_oracle_seeded`)**: Retained strictly as benchmark comparator for retrospective analyses.
- **Phase 10C Extended Ground-Truth Queue Re-Analysis**: Evaluated across 9 conditions on dev seeds (101–105). `hybrid_queue_adaptive` demonstrates statistically significant queue length reductions over measured Webster baselines ($\Delta = -22.07\text{ m}$ vs `webster_measured`, 95% CI $[-30.86, -14.55]\text{ m}$; $\Delta = -23.13\text{ m}$ vs `webster_recalc`, 95% CI $[-32.60, -14.82]\text{ m}$) while matching oracle-seeded performance ($\Delta = -0.42\text{ s}$ mean wait vs `hybrid_oracle_seeded`).

