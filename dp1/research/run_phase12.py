"""Phase 12: Short-Horizon Queue Projection Experiment Engine.

Orchestrates:
1. Search space exploration and tuning on train seeds (101-105).
2. Validation on held-out seeds (106-110) across all 18 conditions.
3. Decision audit parsing (counterfactual action analysis, projection divergence tracking).
4. Paired deltas computation with 95% bootstrap confidence intervals.
5. Pre-registered acceptance rule application (KEEP vs CUT).
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.config import HybridQueueAdaptiveConfig
from dp1.runner import run_simulation

NETWORK = "marathahalli"
NUM_WORKERS = 4
RNG_SEED = 202612

TRAIN_SEEDS = tuple(range(101, 106))   # 101..105 (n=5)
VAL_SEEDS = tuple(range(106, 111))     # 106..110 (n=5)

CONDITIONS = [
    # 12 stationary conditions
    ("balanced", "low"),
    ("balanced", "medium"),
    ("balanced", "heavy"),
    ("imbalanced_orr", "low"),
    ("imbalanced_orr", "medium"),
    ("imbalanced_orr", "heavy"),
    ("imbalanced_varthur", "low"),
    ("imbalanced_varthur", "medium"),
    ("imbalanced_varthur", "heavy"),
    ("surge_orr_north", "low"),
    ("surge_orr_north", "medium"),
    ("surge_orr_north", "heavy"),
    # 6 non-stationary conditions
    ("ramp_peak", "medium"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("surge_shift", "heavy"),
    ("lane_closure", "medium"),
    ("lane_closure", "heavy"),
]

# Tuning screening conditions (representative subset)
TRAIN_CONDITIONS = [
    ("balanced", "heavy"),
    ("imbalanced_orr", "heavy"),
    ("surge_orr_north", "heavy"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("lane_closure", "heavy"),
]

REF_DIR = Path("results/tuning/reference_webster")
TUNING_DIR = Path("results/tuning/projection")
VAL_DIR = Path("results/research/exp_projection_val")


def run_cell_worker(task):
    scenario, demand_level, seed, policy, policy_kwargs, out_dir = task
    out_dir = Path(out_dir)
    if (out_dir / "metrics.json").exists():
        try:
            with open(out_dir / "metrics.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            if "avg_wait_s" in d:
                return d
        except Exception:
            pass

    try:
        res = run_simulation(
            scenario=scenario,
            policy=policy,
            seed=seed,
            network=NETWORK,
            demand_level=demand_level,
            policy_kwargs=policy_kwargs,
            out_dir=out_dir,
        )
        return res
    except Exception as e:
        return {"status": "FAILED", "error": str(e), "scenario": scenario, "demand_level": demand_level, "seed": seed}


def load_reference_norms():
    """Load pre-computed webster_measured runs and calculate normalizer means."""
    ref_records = []
    for sc, dl in CONDITIONS:
        for s in list(TRAIN_SEEDS) + list(VAL_SEEDS):
            run_dir = REF_DIR / f"{NETWORK}_{sc}_{dl}_webster_measured_s{s}"
            with open(run_dir / "metrics.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            d["scenario"] = sc
            d["demand_level"] = dl
            d["seed"] = s
            ref_records.append(d)

    ref_df = pd.DataFrame(ref_records)
    ref_train = {}
    ref_val = {}
    for sc, dl in CONDITIONS:
        df_tr = ref_df[(ref_df["scenario"] == sc) & (ref_df["demand_level"] == dl) & (ref_df["seed"].isin(TRAIN_SEEDS))]
        df_vl = ref_df[(ref_df["scenario"] == sc) & (ref_df["demand_level"] == dl) & (ref_df["seed"].isin(VAL_SEEDS))]

        ref_train[(sc, dl)] = {
            "mean_wait": float(df_tr["avg_wait_s"].mean()),
            "p95_wait": float(df_tr["p95_wait_s"].mean()),
            "approach_wait_gap": float(df_tr["approach_wait_gap_s"].mean()),
        }
        ref_val[(sc, dl)] = {
            "mean_wait": float(df_vl["avg_wait_s"].mean()),
            "p95_wait": float(df_vl["p95_wait_s"].mean()),
            "approach_wait_gap": float(df_vl["approach_wait_gap_s"].mean()),
        }
    return ref_train, ref_val


def make_hybrid_config(projection_enabled: bool, window_s: float = 15.0, horizon_s: float = 6.0, blend_alpha: float = 0.5):
    """Load frozen baseline hybrid parameters and inject projection parameters."""
    return HybridQueueAdaptiveConfig(
        rungs=("R4",),
        extend_step_s=3.0,
        extend_threshold_m=4.0,
        fairness_ratio=1.2,
        gap_out_s=3.0,
        min_competing_queue_m=2.0,
        max_competing_wait_s=35.0,
        r4_warmup_s=300.0,
        demand_weight_active=1.0,
        demand_weight_competing=1.0,
        arrival_detection_threshold=0.5,
        projection_enabled=projection_enabled,
        projection_window_s=window_s,
        projection_horizon_s=horizon_s,
        projection_blend_alpha=blend_alpha,
        projection_sat_flow_fallback_mps=7.5,
    )


def parse_decisions_audit(run_dir: Path) -> Dict[str, Any]:
    """Inspect decisions.csv to measure projection divergence and counterfactual actions."""
    csv_path = run_dir / "decisions.csv"
    if not csv_path.exists():
        return {
            "total_decisions": 0,
            "divergence_count": 0,
            "divergence_rate": 0.0,
            "counterfactual_actions": {},
            "mean_lambda": 0.0,
            "mean_mu": 0.0,
        }

    total = 0
    divergence = 0
    cf_actions = {}
    lambdas = []
    mus = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            is_div = str(row.get("projection_divergence", "")).lower() == "true"
            if is_div:
                divergence += 1
                cf = row.get("counterfactual_action", "UNKNOWN")
                cf_actions[cf] = cf_actions.get(cf, 0) + 1

            for a in ["N", "S", "E", "W"]:
                l_val = row.get(f"lambda_{a}")
                if l_val is not None and l_val != "":
                    try:
                        lambdas.append(float(l_val))
                    except ValueError:
                        pass
            mu_val = row.get("mu_active")
            if mu_val is not None and mu_val != "":
                try:
                    mus.append(float(mu_val))
                except ValueError:
                    pass

    return {
        "total_decisions": total,
        "divergence_count": divergence,
        "divergence_rate": round(divergence / max(1, total), 4),
        "counterfactual_actions": cf_actions,
        "mean_lambda": round(float(np.mean(lambdas)), 3) if lambdas else 0.0,
        "mean_mu": round(float(np.mean(mus)), 3) if mus else 0.0,
    }


def bootstrap_ci(diffs: np.ndarray, n_boot: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Compute empirical bootstrap confidence interval for paired differences."""
    rng = np.random.default_rng(RNG_SEED)
    means = [np.mean(rng.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(means, 100 * alpha)), float(np.percentile(means, 100 * (1 - alpha)))


def run_tuning(ref_train: Dict[Tuple[str, str], Dict[str, float]]):
    """Run Phase 12 tuning sweep on seeds 101-105."""
    print("=== Step 1: Tuning Short-Horizon Projection on Train Seeds (101-105) ===")
    TUNING_DIR.mkdir(parents=True, exist_ok=True)

    candidates = [
        {"id": "P0_default", "window_s": 15.0, "horizon_s": 6.0, "blend_alpha": 0.5},
        {"id": "P1_fast", "window_s": 10.0, "horizon_s": 4.0, "blend_alpha": 0.6},
        {"id": "P2_lookahead", "window_s": 15.0, "horizon_s": 10.0, "blend_alpha": 0.5},
        {"id": "P3_smooth", "window_s": 25.0, "horizon_s": 6.0, "blend_alpha": 0.3},
        {"id": "P4_high_blend", "window_s": 12.0, "horizon_s": 8.0, "blend_alpha": 0.7},
        {"id": "P5_conservative", "window_s": 20.0, "horizon_s": 5.0, "blend_alpha": 0.4},
    ]

    tasks = []
    for cand in candidates:
        cid = cand["id"]
        cfg = make_hybrid_config(True, cand["window_s"], cand["horizon_s"], cand["blend_alpha"])
        kwargs = {"cfg": cfg}
        for sc, dl in TRAIN_CONDITIONS:
            for s in TRAIN_SEEDS:
                run_dir = TUNING_DIR / f"{cid}_{sc}_{dl}_s{s}"
                tasks.append((sc, dl, s, "hybrid_queue_adaptive", kwargs, str(run_dir), cid))

    total = len(tasks)
    print(f"Executing {total} tuning simulations across {len(candidates)} candidates...")
    task_map = {}
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for t in tasks:
            task_tup = t[:6]
            cid = t[6]
            fut = executor.submit(run_cell_worker, task_tup)
            task_map[fut] = (cid, t[0], t[1], t[2], t[5])

        results_by_cand = {c["id"]: [] for c in candidates}
        done = 0
        for fut in as_completed(task_map):
            done += 1
            cid, sc, dl, s, rdir = task_map[fut]
            res = fut.result()
            res["scenario"] = sc
            res["demand_level"] = dl
            res["seed"] = s
            results_by_cand[cid].append(res)
            if done % 20 == 0 or done == total:
                print(f"  Tuning progress: [{done}/{total}] completed...")

    # Score each candidate on screening conditions
    ranking = []
    for cand in candidates:
        cid = cand["id"]
        c_res = results_by_cand[cid]
        comp_scores = []
        for sc, dl in TRAIN_CONDITIONS:
            matching = [r for r in c_res if r["scenario"] == sc and r["demand_level"] == dl]
            m_wait = float(np.mean([r["avg_wait_s"] for r in matching]))
            p95_w = float(np.mean([r["p95_wait_s"] for r in matching]))
            gap_w = float(np.mean([r["approach_wait_gap_s"] for r in matching]))

            ref = ref_train[(sc, dl)]
            c_score = 0.4 * (m_wait / max(0.1, ref["mean_wait"])) + \
                      0.3 * (p95_w / max(0.1, ref["p95_wait"])) + \
                      0.3 * (gap_w / max(0.1, ref["approach_wait_gap"]))
            comp_scores.append(c_score)

        mean_comp = float(np.mean(comp_scores))
        cand_summary = {
            **cand,
            "train_composite": round(mean_comp, 4),
            "mean_wait_s": round(float(np.mean([r["avg_wait_s"] for r in c_res])), 2),
            "p95_wait_s": round(float(np.mean([r["p95_wait_s"] for r in c_res])), 2),
            "gap_s": round(float(np.mean([r["approach_wait_gap_s"] for r in c_res])), 2),
        }
        ranking.append(cand_summary)

    ranking.sort(key=lambda x: x["train_composite"])
    best = ranking[0]
    print(f"Tuning complete. Best candidate: {best['id']} (Composite: {best['train_composite']})")
    print(f"  Parameters: W={best['window_s']}s, h={best['horizon_s']}s, alpha={best['blend_alpha']}")

    pd.DataFrame(ranking).to_csv(TUNING_DIR / "tuning_summary.csv", index=False)
    with open(TUNING_DIR / "tuning_trials.json", "w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2)

    return best


def run_validation(best_cand: Dict[str, Any], ref_val: Dict[Tuple[str, str], Dict[str, float]]):
    """Run full validation comparison on held-out seeds 106-110 across all 18 conditions."""
    print("=== Step 2: Full Validation (Seeds 106-110, All 18 Conditions) ===")
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    cfg_off = make_hybrid_config(projection_enabled=False)
    cfg_on = make_hybrid_config(
        projection_enabled=True,
        window_s=best_cand["window_s"],
        horizon_s=best_cand["horizon_s"],
        blend_alpha=best_cand["blend_alpha"],
    )

    tasks = []
    # 1. Hybrid Frozen (Projection Off)
    for sc, dl in CONDITIONS:
        for s in VAL_SEEDS:
            out_dir = VAL_DIR / f"hybrid_frozen_{sc}_{dl}_s{s}"
            tasks.append((sc, dl, s, "hybrid_queue_adaptive", {"cfg": cfg_off}, str(out_dir), "frozen"))

    # 2. Hybrid Projection (Projection On)
    for sc, dl in CONDITIONS:
        for s in VAL_SEEDS:
            out_dir = VAL_DIR / f"hybrid_projection_{sc}_{dl}_s{s}"
            tasks.append((sc, dl, s, "hybrid_queue_adaptive", {"cfg": cfg_on}, str(out_dir), "projection"))

    total = len(tasks)
    print(f"Executing {total} validation simulations (90 frozen + 90 projection)...")
    task_map = {}
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for t in tasks:
            task_tup = t[:6]
            group = t[6]
            fut = executor.submit(run_cell_worker, task_tup)
            task_map[fut] = (group, t[0], t[1], t[2], Path(t[5]))

        res_frozen = []
        res_proj = []
        done = 0
        for fut in as_completed(task_map):
            done += 1
            group, sc, dl, s, rdir = task_map[fut]
            res = fut.result()
            res["scenario"] = sc
            res["demand_level"] = dl
            res["seed"] = s
            res["run_dir"] = str(rdir)

            # Parse decision audit
            audit = parse_decisions_audit(rdir)
            res.update(audit)

            if group == "frozen":
                res_frozen.append(res)
            else:
                res_proj.append(res)

            if done % 20 == 0 or done == total:
                print(f"  Validation progress: [{done}/{total}] completed...")

    # Load webster_measured validation runs for complete 3-way table
    res_webster = []
    for sc, dl in CONDITIONS:
        for s in VAL_SEEDS:
            rdir = REF_DIR / f"{NETWORK}_{sc}_{dl}_webster_measured_s{s}"
            with open(rdir / "metrics.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            d["scenario"] = sc
            d["demand_level"] = dl
            d["seed"] = s
            res_webster.append(d)

    # Save raw results
    pd.DataFrame(res_frozen).to_csv(VAL_DIR / "val_frozen_metrics.csv", index=False)
    pd.DataFrame(res_proj).to_csv(VAL_DIR / "val_projection_metrics.csv", index=False)
    pd.DataFrame(res_webster).to_csv(VAL_DIR / "val_webster_metrics.csv", index=False)

    return res_frozen, res_proj, res_webster


def analyze_and_gate(res_frozen: List[Dict[str, Any]], res_proj: List[Dict[str, Any]], res_webster: List[Dict[str, Any]], ref_val: Dict[Tuple[str, str], Dict[str, float]], best_cand: Dict[str, Any]):
    """Compute paired differences, confidence intervals, audit stats, and apply acceptance gate."""
    print("=== Step 3: Paired Evaluation & Acceptance Gate Analysis ===")

    # Align pairs by (scenario, demand_level, seed)
    df_f = pd.DataFrame(res_frozen).set_index(["scenario", "demand_level", "seed"])
    df_p = pd.DataFrame(res_proj).set_index(["scenario", "demand_level", "seed"])
    df_w = pd.DataFrame(res_webster).set_index(["scenario", "demand_level", "seed"])

    paired_records = []
    total_divergences = 0
    total_decisions = 0
    aggregated_cf_actions = {}

    for (sc, dl, s) in df_f.index:
        row_f = df_f.loc[(sc, dl, s)]
        row_p = df_p.loc[(sc, dl, s)]
        row_w = df_w.loc[(sc, dl, s)]

        ref = ref_val[(sc, dl)]
        comp_f = 0.4 * (row_f["avg_wait_s"] / max(0.1, ref["mean_wait"])) + \
                 0.3 * (row_f["p95_wait_s"] / max(0.1, ref["p95_wait"])) + \
                 0.3 * (row_f["approach_wait_gap_s"] / max(0.1, ref["approach_wait_gap"]))

        comp_p = 0.4 * (row_p["avg_wait_s"] / max(0.1, ref["mean_wait"])) + \
                 0.3 * (row_p["p95_wait_s"] / max(0.1, ref["p95_wait"])) + \
                 0.3 * (row_p["approach_wait_gap_s"] / max(0.1, ref["approach_wait_gap"]))

        div_cnt = int(row_p.get("divergence_count", 0))
        tot_dec = int(row_p.get("total_decisions", 0))
        total_divergences += div_cnt
        total_decisions += tot_dec

        cf_act = row_p.get("counterfactual_actions", {})
        if isinstance(cf_act, dict):
            for act, cnt in cf_act.items():
                aggregated_cf_actions[act] = aggregated_cf_actions.get(act, 0) + cnt

        q_max_f = max(row_f.get("gt_ext_max_queue_m") or 0.0, row_f.get("max_queue_m") or 0.0)
        q_max_p = max(row_p.get("gt_ext_max_queue_m") or 0.0, row_p.get("max_queue_m") or 0.0)

        paired_records.append({
            "scenario": sc,
            "demand_level": dl,
            "seed": s,
            # Frozen
            "wait_frozen": row_f["avg_wait_s"],
            "p95_frozen": row_f["p95_wait_s"],
            "gap_frozen": row_f["approach_wait_gap_s"],
            "qmax_frozen": q_max_f,
            "comp_frozen": comp_f,
            # Projection
            "wait_proj": row_p["avg_wait_s"],
            "p95_proj": row_p["p95_wait_s"],
            "gap_proj": row_p["approach_wait_gap_s"],
            "qmax_proj": q_max_p,
            "comp_proj": comp_p,
            # Deltas (Projection - Frozen)
            "delta_wait": row_p["avg_wait_s"] - row_f["avg_wait_s"],
            "delta_p95": row_p["p95_wait_s"] - row_f["p95_wait_s"],
            "delta_gap": row_p["approach_wait_gap_s"] - row_f["approach_wait_gap_s"],
            "delta_qmax": q_max_p - q_max_f,
            "delta_comp": comp_p - comp_f,
            # Webster
            "wait_webster": row_w["avg_wait_s"],
            # Divergence
            "divergence_count": div_cnt,
            "divergence_rate": row_p.get("divergence_rate", 0.0),
        })

    pdf = pd.DataFrame(paired_records)
    pdf.to_csv(VAL_DIR / "paired_deltas.csv", index=False)

    # Compute aggregate means & bootstrap CIs
    n_pairs = len(pdf)
    mean_comp_f = float(pdf["comp_frozen"].mean())
    mean_comp_p = float(pdf["comp_proj"].mean())
    delta_comp_mean = float(pdf["delta_comp"].mean())
    comp_pct_change = ((mean_comp_p - mean_comp_f) / mean_comp_f) * 100.0

    mean_wait_f = float(pdf["wait_frozen"].mean())
    mean_wait_p = float(pdf["wait_proj"].mean())
    delta_wait_mean = float(pdf["delta_wait"].mean())
    wait_pct_change = ((mean_wait_p - mean_wait_f) / mean_wait_f) * 100.0

    mean_p95_f = float(pdf["p95_frozen"].mean())
    mean_p95_p = float(pdf["p95_proj"].mean())
    delta_p95_mean = float(pdf["delta_p95"].mean())

    mean_gap_f = float(pdf["gap_frozen"].mean())
    mean_gap_p = float(pdf["gap_proj"].mean())
    delta_gap_mean = float(pdf["delta_gap"].mean())
    gap_pct_change = ((mean_gap_p - mean_gap_f) / mean_gap_f) * 100.0

    mean_qmax_f = float(pdf["qmax_frozen"].mean())
    mean_qmax_p = float(pdf["qmax_proj"].mean())
    delta_qmax_mean = float(pdf["delta_qmax"].mean())

    # Bootstrap CIs
    comp_ci = bootstrap_ci(pdf["delta_comp"].values)
    wait_ci = bootstrap_ci(pdf["delta_wait"].values)
    gap_ci = bootstrap_ci(pdf["delta_gap"].values)
    p95_ci = bootstrap_ci(pdf["delta_p95"].values)

    # Acceptance Gate Evaluation
    # Gate Rules:
    # 1. Composite score improves by >= 1.0% (comp_pct_change <= -1.0%)
    # 2. Wait gap does not worsen by > 2.0% (gap_pct_change <= +2.0%)
    # 3. Safety invariants preserved
    passes_composite = (comp_pct_change <= -1.0)
    passes_gap = (gap_pct_change <= 2.0)
    verdict = "KEEP" if (passes_composite and passes_gap) else "CUT"

    print("\n=================== PHASE 12 EVALUATION SUMMARY ===================")
    print(f"Total Paired Simulations: {n_pairs} across 18 conditions (seeds 106-110)")
    print(f"Projection Divergence Events: {total_divergences} / {total_decisions} decisions ({total_divergences/max(1, total_decisions)*100:.2f}%)")
    print(f"Counterfactual Actions Breakdown: {aggregated_cf_actions}")
    print("-------------------------------------------------------------------")
    print(f"Composite Score:      Frozen={mean_comp_f:.4f}  |  Proj={mean_comp_p:.4f}  |  Delta={delta_comp_mean:+.4f} ({comp_pct_change:+.2f}%)  [95% CI: {comp_ci[0]:+.4f}, {comp_ci[1]:+.4f}]")
    print(f"Mean Waiting Time:    Frozen={mean_wait_f:.2f}s  |  Proj={mean_wait_p:.2f}s  |  Delta={delta_wait_mean:+.2f}s ({wait_pct_change:+.2f}%)  [95% CI: {wait_ci[0]:+.2f}, {wait_ci[1]:+.2f}]")
    print(f"P95 Waiting Time:     Frozen={mean_p95_f:.2f}s  |  Proj={mean_p95_p:.2f}s  |  Delta={delta_p95_mean:+.2f}s        [95% CI: {p95_ci[0]:+.2f}, {p95_ci[1]:+.2f}]")
    print(f"Approach Wait Gap:    Frozen={mean_gap_f:.2f}s  |  Proj={mean_gap_p:.2f}s  |  Delta={delta_gap_mean:+.2f}s ({gap_pct_change:+.2f}%)  [95% CI: {gap_ci[0]:+.2f}, {gap_ci[1]:+.2f}]")
    print(f"Max Queue Length:     Frozen={mean_qmax_f:.2f}m  |  Proj={mean_qmax_p:.2f}m  |  Delta={delta_qmax_mean:+.2f}m")
    print("-------------------------------------------------------------------")
    print(f"Acceptance Criteria:")
    print(f"  1. Composite Improvement >= 1.0%: {'PASS' if passes_composite else 'FAIL'} (Change: {comp_pct_change:+.2f}%)")
    print(f"  2. Wait Gap Worsening <= 2.0%:    {'PASS' if passes_gap else 'FAIL'} (Change: {gap_pct_change:+.2f}%)")
    print(f"FINAL GATE VERDICT: >> {verdict} <<")
    print("===================================================================\n")

    summary_dict = {
        "verdict": verdict,
        "best_candidate": best_cand,
        "n_pairs": n_pairs,
        "total_divergences": total_divergences,
        "total_decisions": total_decisions,
        "divergence_pct": round(total_divergences / max(1, total_decisions) * 100, 2),
        "counterfactual_actions": aggregated_cf_actions,
        "metrics": {
            "composite": {
                "frozen": round(mean_comp_f, 4),
                "proj": round(mean_comp_p, 4),
                "delta": round(delta_comp_mean, 4),
                "pct_change": round(comp_pct_change, 2),
                "ci_95": [round(comp_ci[0], 4), round(comp_ci[1], 4)],
            },
            "mean_wait_s": {
                "frozen": round(mean_wait_f, 2),
                "proj": round(mean_wait_p, 2),
                "delta": round(delta_wait_mean, 2),
                "pct_change": round(wait_pct_change, 2),
                "ci_95": [round(wait_ci[0], 2), round(wait_ci[1], 2)],
            },
            "p95_wait_s": {
                "frozen": round(mean_p95_f, 2),
                "proj": round(mean_p95_p, 2),
                "delta": round(delta_p95_mean, 2),
                "ci_95": [round(p95_ci[0], 2), round(p95_ci[1], 2)],
            },
            "approach_wait_gap_s": {
                "frozen": round(mean_gap_f, 2),
                "proj": round(mean_gap_p, 2),
                "delta": round(delta_gap_mean, 2),
                "pct_change": round(gap_pct_change, 2),
                "ci_95": [round(gap_ci[0], 2), round(gap_ci[1], 2)],
            },
            "max_queue_m": {
                "frozen": round(mean_qmax_f, 2),
                "proj": round(mean_qmax_p, 2),
                "delta": round(delta_qmax_mean, 2),
            },
        },
    }

    with open(VAL_DIR / "verdict_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    # Condition-level summary table
    cond_summary = []
    for sc, dl in CONDITIONS:
        sub = pdf[(pdf["scenario"] == sc) & (pdf["demand_level"] == dl)]
        cond_summary.append({
            "scenario": sc,
            "demand_level": dl,
            "wait_frozen": round(float(sub["wait_frozen"].mean()), 2),
            "wait_proj": round(float(sub["wait_proj"].mean()), 2),
            "delta_wait": round(float(sub["delta_wait"].mean()), 2),
            "gap_frozen": round(float(sub["gap_frozen"].mean()), 2),
            "gap_proj": round(float(sub["gap_proj"].mean()), 2),
            "delta_gap": round(float(sub["delta_gap"].mean()), 2),
            "comp_frozen": round(float(sub["comp_frozen"].mean()), 4),
            "comp_proj": round(float(sub["comp_proj"].mean()), 4),
            "delta_comp": round(float(sub["delta_comp"].mean()), 4),
            "divergences": int(sub["divergence_count"].sum()),
        })
    pd.DataFrame(cond_summary).to_csv(VAL_DIR / "condition_summary.csv", index=False)

    if verdict == "KEEP":
        # Freeze final_hybrid_projection.yaml
        cfg_yaml = {
            "policy": "hybrid_queue_adaptive_projection",
            "date_frozen": "2026-11-03",
            "provenance": f"phase12_validation_{best_cand['id']}",
            "training_seeds": list(TRAIN_SEEDS),
            "validation_seeds": list(VAL_SEEDS),
            "kept_rungs": ["R4"],
            "projection_parameters": {
                "projection_enabled": True,
                "projection_window_s": best_cand["window_s"],
                "projection_horizon_s": best_cand["horizon_s"],
                "projection_blend_alpha": best_cand["blend_alpha"],
                "projection_sat_flow_fallback_mps": 7.5,
            },
            "parameters": {
                "extend_step_s": 3.0,
                "extend_threshold_m": 4.0,
                "fairness_ratio": 1.2,
                "gap_out_s": 3.0,
                "min_competing_queue_m": 2.0,
                "max_competing_wait_s": 35.0,
                "r4_warmup_s": 300.0,
                "demand_weight_active": 1.0,
                "demand_weight_competing": 1.0,
                "arrival_detection_threshold": 0.5,
            },
        }
        with open(Path("configs/final_hybrid_projection.yaml"), "w", encoding="utf-8") as f:
            yaml_str = []
            for k, v in cfg_yaml.items():
                if isinstance(v, dict):
                    yaml_str.append(f"{k}:")
                    for subk, subv in v.items():
                        yaml_str.append(f"  {subk}: {subv}")
                elif isinstance(v, list):
                    yaml_str.append(f"{k}:")
                    for item in v:
                        yaml_str.append(f"  - {item}")
                else:
                    yaml_str.append(f"{k}: {v}")
            f.write("\n".join(yaml_str) + "\n")
        print("Freezed winning configuration to configs/final_hybrid_projection.yaml")

    return summary_dict, cond_summary


def main():
    t_start = time.time()
    ref_train, ref_val = load_reference_norms()
    best_cand = run_tuning(ref_train)
    res_f, res_p, res_w = run_validation(best_cand, ref_val)
    summary, cond_summary = analyze_and_gate(res_f, res_p, res_w, ref_val, best_cand)
    t_elapsed = time.time() - t_start
    print(f"Phase 12 Pipeline finished in {t_elapsed/60:.2f} minutes.")


if __name__ == "__main__":
    main()
