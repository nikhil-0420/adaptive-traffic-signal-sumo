"""Phase 10 Sequential Ablation Ladder Experiment Orchestrator.

Runs:
1. R2 Experiment: hybrid_r2 vs hybrid_queue_adaptive (R0) and webster_measured.
   Evaluates Keep/Cut on validation seeds 106-110 across 18 conditions.
2. R3 Experiment: candidate (with R3) vs previous baseline and webster_measured.
   Evaluates Keep/Cut.
3. R4 Experiment: candidate (with R4) vs previous baseline and webster_measured.
   Evaluates Keep/Cut.
4. Generates docs/ablation_ladder.md with one row per rung.
"""

import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_ablation_ladder import (
    execute_policy_matrix,
    copy_or_link_results,
    evaluate_rung_pair,
    evaluate_vs_webster,
    CONDITIONS,
    VALIDATION_SEEDS,
)

BASE_CACHE_DIR = Path("results/research/cache_val_106_110")
RESEARCH_DIR = Path("results/research")
NUM_WORKERS = 4


def main():
    t_start = time.time()
    print("=================================================================")
    print("PHASE 10: ABLATION LADDER EVALUATION ON VALIDATION SEEDS 106-110")
    print("Conditions: 12 stationary + 6 non-stationary = 18 conditions")
    print("Seeds: 106, 107, 108, 109, 110 (5 validation seeds)")
    print("=================================================================\n")

    ladder_rows = []

    # -------------------------------------------------------------
    # Rung 0: Reference Baseline (untouched hybrid)
    # -------------------------------------------------------------
    print("--- [RUNG 0] Reference Baseline: hybrid_queue_adaptive (R0) ---")
    execute_policy_matrix("hybrid_queue_adaptive", BASE_CACHE_DIR, max_workers=NUM_WORKERS)
    print("--- [REFERENCE] webster_measured ---")
    execute_policy_matrix("webster_measured", BASE_CACHE_DIR, max_workers=NUM_WORKERS)

    ladder_rows.append({
        "rung": "R0",
        "name": "Current Frozen Hybrid",
        "change": "Reference hybrid controller untouched (flags off).",
        "status": "REFERENCE",
        "primary_deltas": "Baseline (0.00)",
        "bootstrap_ci": "N/A",
        "verdict": "REFERENCE",
        "reason": "Frozen reference baseline for ablation comparisons.",
    })

    # -------------------------------------------------------------
    # Rung 1: Gap-out + HOLD default (NOT JUSTIFIED)
    # -------------------------------------------------------------
    print("\n--- [RUNG 1] Gap-out + HOLD default ---")
    print("Status: NOT JUSTIFIED per docs/diagnostics_report.md (Table line 438).")
    print("Reason: D10 confirms gap-out is already active in 36.54% of decisions; min green 13.0s enforced. Skipped.")
    ladder_rows.append({
        "rung": "R1",
        "name": "Gap-out + HOLD default",
        "change": "Early gap-out request and default HOLD when no demand.",
        "status": "NOT JUSTIFIED",
        "primary_deltas": "Skipped",
        "bootstrap_ci": "Skipped",
        "verdict": "SKIPPED",
        "reason": "NOT JUSTIFIED per Phase 7 diagnostics: D10 proved gap-out is already active in 36.54% of decisions; min green of 13.0s is already enforced.",
    })

    # -------------------------------------------------------------
    # Rung 2: Comparative Extension
    # -------------------------------------------------------------
    print("\n--- [RUNG 2] Evaluating R2: Comparative Extension ---")
    r2_exp_dir = RESEARCH_DIR / "exp_ladder_R2_val"
    r2_exp_dir.mkdir(parents=True, exist_ok=True)

    # Copy shared baselines
    copy_or_link_results("hybrid_queue_adaptive", BASE_CACHE_DIR, r2_exp_dir)
    copy_or_link_results("webster_measured", BASE_CACHE_DIR, r2_exp_dir)

    # Run hybrid_r2
    execute_policy_matrix("hybrid_r2", BASE_CACHE_DIR, max_workers=NUM_WORKERS)
    copy_or_link_results("hybrid_r2", BASE_CACHE_DIR, r2_exp_dir)

    # Evaluate R2 vs R0
    v_r2 = evaluate_rung_pair(
        candidate_policy="hybrid_r2",
        baseline_policy="hybrid_queue_adaptive",
        exp_dir=r2_exp_dir,
    )
    vs_web_r2 = evaluate_vs_webster("hybrid_r2", r2_exp_dir)

    p_r2 = v_r2["metrics"]["p95_wait_s"]
    q_r2 = v_r2["metrics"]["max_queue_m"]
    g_r2 = v_r2["metrics"]["approach_wait_gap_s"]
    w_r2 = v_r2["metrics"]["avg_wait_s"]

    r2_deltas_str = f"P95: {p_r2['delta_mean']:+.2f}s, MaxQ: {q_r2['delta_mean']:+.2f}m, Gap: {g_r2['delta_mean']:+.2f}s, MeanWait: {w_r2['delta_mean']:+.2f}s ({w_r2['pct_change']:+.2f}%)"
    r2_ci_str = f"P95 CI: [{p_r2['ci_95_low']:.2f}, {p_r2['ci_95_high']:.2f}], MaxQ CI: [{q_r2['ci_95_low']:.2f}, {q_r2['ci_95_high']:.2f}], Gap CI: [{g_r2['ci_95_low']:.2f}, {g_r2['ci_95_high']:.2f}]"

    print(f"\n[RUNG 2 VERDICT]: {v_r2['verdict']}")
    print(f"  Primary deltas: {r2_deltas_str}")
    print(f"  Confidence intervals: {r2_ci_str}")
    print(f"  Reasons: {'; '.join(v_r2['reasons'])}\n")

    ladder_rows.append({
        "rung": "R2",
        "name": "Comparative Extension",
        "change": "Extend only if score_active > margin * score_competing + switch_cost (5.0m = 5s lost time). Replaces fixed 4m threshold.",
        "status": "JUSTIFIED",
        "primary_deltas": r2_deltas_str,
        "bootstrap_ci": r2_ci_str,
        "verdict": v_r2["verdict"],
        "reason": "; ".join(v_r2["reasons"]),
    })

    active_baseline = "hybrid_r2" if v_r2["verdict"] == "KEEP" else "hybrid_queue_adaptive"

    # -------------------------------------------------------------
    # Rung 3: Queue-Aware Fairness
    # -------------------------------------------------------------
    print(f"\n--- [RUNG 3] Evaluating R3: Queue-Aware Fairness (Baseline: {active_baseline}) ---")
    candidate_r3 = "hybrid_r2_r3" if v_r2["verdict"] == "KEEP" else "hybrid_r3"
    r3_exp_dir = RESEARCH_DIR / "exp_ladder_R3_val"
    r3_exp_dir.mkdir(parents=True, exist_ok=True)

    # Copy shared baselines
    copy_or_link_results(active_baseline, BASE_CACHE_DIR, r3_exp_dir)
    copy_or_link_results("webster_measured", BASE_CACHE_DIR, r3_exp_dir)

    # Run candidate R3
    execute_policy_matrix(candidate_r3, BASE_CACHE_DIR, max_workers=NUM_WORKERS)
    copy_or_link_results(candidate_r3, BASE_CACHE_DIR, r3_exp_dir)

    # Evaluate R3 vs active baseline
    v_r3 = evaluate_rung_pair(
        candidate_policy=candidate_r3,
        baseline_policy=active_baseline,
        exp_dir=r3_exp_dir,
    )
    vs_web_r3 = evaluate_vs_webster(candidate_r3, r3_exp_dir)

    p_r3 = v_r3["metrics"]["p95_wait_s"]
    q_r3 = v_r3["metrics"]["max_queue_m"]
    g_r3 = v_r3["metrics"]["approach_wait_gap_s"]
    w_r3 = v_r3["metrics"]["avg_wait_s"]

    r3_deltas_str = f"P95: {p_r3['delta_mean']:+.2f}s, MaxQ: {q_r3['delta_mean']:+.2f}m, Gap: {g_r3['delta_mean']:+.2f}s, MeanWait: {w_r3['delta_mean']:+.2f}s ({w_r3['pct_change']:+.2f}%)"
    r3_ci_str = f"P95 CI: [{p_r3['ci_95_low']:.2f}, {p_r3['ci_95_high']:.2f}], MaxQ CI: [{q_r3['ci_95_low']:.2f}, {q_r3['ci_95_high']:.2f}], Gap CI: [{g_r3['ci_95_low']:.2f}, {g_r3['ci_95_high']:.2f}]"

    print(f"\n[RUNG 3 VERDICT]: {v_r3['verdict']}")
    print(f"  Primary deltas: {r3_deltas_str}")
    print(f"  Confidence intervals: {r3_ci_str}")
    print(f"  Reasons: {'; '.join(v_r3['reasons'])}\n")

    ladder_rows.append({
        "rung": "R3",
        "name": "Queue-Aware Fairness",
        "change": "Scale soft competing wait limit by competing queue size; no switch if empty; retain 35s hard cap.",
        "status": "JUSTIFIED",
        "primary_deltas": r3_deltas_str,
        "bootstrap_ci": r3_ci_str,
        "verdict": v_r3["verdict"],
        "reason": "; ".join(v_r3["reasons"]),
    })

    if v_r3["verdict"] == "KEEP":
        active_baseline = candidate_r3
    else:
        # Keep previous active baseline
        pass

    # -------------------------------------------------------------
    # Rung 4: Measured Webster Base Green
    # -------------------------------------------------------------
    print(f"\n--- [RUNG 4] Evaluating R4: Measured Webster Base Green (Baseline: {active_baseline}) ---")
    if active_baseline == "hybrid_r2_r3":
        candidate_r4 = "hybrid_r2_r3_r4"
    elif active_baseline == "hybrid_r2":
        candidate_r4 = "hybrid_r2_r4" # or run with cfg rungs=("R2", "R4")
    elif active_baseline == "hybrid_r3":
        candidate_r4 = "hybrid_r3_r4"
    else:
        candidate_r4 = "hybrid_r4"

    # If candidate_r4 is hybrid_r2_r3_r4 it's registered; otherwise registered as hybrid_r4
    r4_exp_dir = RESEARCH_DIR / "exp_ladder_R4_val"
    r4_exp_dir.mkdir(parents=True, exist_ok=True)

    # Copy shared baselines
    copy_or_link_results(active_baseline, BASE_CACHE_DIR, r4_exp_dir)
    copy_or_link_results("webster_measured", BASE_CACHE_DIR, r4_exp_dir)

    # Run candidate R4
    execute_policy_matrix(candidate_r4, BASE_CACHE_DIR, max_workers=NUM_WORKERS)
    copy_or_link_results(candidate_r4, BASE_CACHE_DIR, r4_exp_dir)

    # Evaluate R4 vs active baseline
    v_r4 = evaluate_rung_pair(
        candidate_policy=candidate_r4,
        baseline_policy=active_baseline,
        exp_dir=r4_exp_dir,
    )
    vs_web_r4 = evaluate_vs_webster(candidate_r4, r4_exp_dir)

    p_r4 = v_r4["metrics"]["p95_wait_s"]
    q_r4 = v_r4["metrics"]["max_queue_m"]
    g_r4 = v_r4["metrics"]["approach_wait_gap_s"]
    w_r4 = v_r4["metrics"]["avg_wait_s"]

    r4_deltas_str = f"P95: {p_r4['delta_mean']:+.2f}s, MaxQ: {q_r4['delta_mean']:+.2f}m, Gap: {g_r4['delta_mean']:+.2f}s, MeanWait: {w_r4['delta_mean']:+.2f}s ({w_r4['pct_change']:+.2f}%)"
    r4_ci_str = f"P95 CI: [{p_r4['ci_95_low']:.2f}, {p_r4['ci_95_high']:.2f}], MaxQ CI: [{q_r4['ci_95_low']:.2f}, {q_r4['ci_95_high']:.2f}], Gap CI: [{g_r4['ci_95_low']:.2f}, {g_r4['ci_95_high']:.2f}]"

    print(f"\n[RUNG 4 VERDICT]: {v_r4['verdict']}")
    print(f"  Primary deltas: {r4_deltas_str}")
    print(f"  Confidence intervals: {r4_ci_str}")
    print(f"  Reasons: {'; '.join(v_r4['reasons'])}\n")

    ladder_rows.append({
        "rung": "R4",
        "name": "Measured Webster Base Green",
        "change": "De-oracle base green: derive from 300s warm-up measured arrival flows at cycle boundary.",
        "status": "JUSTIFIED",
        "primary_deltas": r4_deltas_str,
        "bootstrap_ci": r4_ci_str,
        "verdict": v_r4["verdict"],
        "reason": "; ".join(v_r4["reasons"]),
    })

    # -------------------------------------------------------------
    # Rung 5: Longer Detectors (NOT JUSTIFIED)
    # -------------------------------------------------------------
    print("\n--- [RUNG 5] Longer Detectors ---")
    print("Status: NOT JUSTIFIED per docs/diagnostics_report.md (Table line 442).")
    print("Reason: D8 proves physical edge headroom is only 6.6m–9.2m before upstream merge junctions. Skipped.")
    ladder_rows.append({
        "rung": "R5",
        "name": "Longer Detectors",
        "change": "Physically extend E2 lane-area detectors upstream.",
        "status": "NOT JUSTIFIED",
        "primary_deltas": "Skipped",
        "bootstrap_ci": "Skipped",
        "verdict": "SKIPPED",
        "reason": "NOT JUSTIFIED per Phase 7 diagnostics: D8 proved physical edge headroom before upstream merge junctions is only 6.6m–9.2m (~1 vehicle). Geometrically unviable without crossing merge nodes.",
    })

    # -------------------------------------------------------------
    # Output docs/ablation_ladder.md
    # -------------------------------------------------------------
    docs_path = Path("docs/ablation_ladder.md")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write("# DP1 Ablation Ladder: Hybrid Controller Improvements\n\n")
        f.write("Evaluated on **validation seeds (106–110)** across all 18 demand conditions (12 stationary + 6 non-stationary).\n")
        f.write("All keep/cut decisions strictly follow the pre-registered protocol in `docs/PREREGISTRATION.md`.\n\n")
        f.write("| Rung | Name | Status | Change Description | Validation Deltas (vs Prev Rung) | 95% Bootstrap CI | Verdict | Rule Evaluation / Reason |\n")
        f.write("| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- |\n")
        for r in ladder_rows:
            f.write(f"| **{r['rung']}** | {r['name']} | {r['status']} | {r['change']} | {r['primary_deltas']} | {r['bootstrap_ci']} | **{r['verdict']}** | {r['reason']} |\n")
        f.write("\n---\n")

    elapsed_total = round(time.time() - t_start, 1)
    print("\n=================================================================")
    print(f"ABLATION LADDER EXECUTION COMPLETED in {elapsed_total}s.")
    print("Results written to:")
    print("  - docs/ablation_ladder.md")
    print("  - results/research/exp_ladder_R2_val")
    print("  - results/research/exp_ladder_R3_val")
    print("  - results/research/exp_ladder_R4_val")
    print("=================================================================")


if __name__ == "__main__":
    main()
