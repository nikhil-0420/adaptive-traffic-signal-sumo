"""Task 4: R3 Amendment Test on Validation-2 Seeds (111–120).

Evaluates:
- Baseline: new default hybrid (R4 measured base green, de-oracled).
- Candidate: new default + R3 (R4 + R3 queue-aware fairness).
- Reference: webster_measured.

Runs: 3 policies x 18 conditions x 10 seeds = 540 runs.
Directory: results/research/exp_ladder_R3_amend_val2
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.runner import run_simulation
from dp1.research.stats import bootstrap_percentile_ci

VALIDATION_2_SEEDS = tuple(range(111, 121))  # 111..120 (n=10)
NETWORK = "marathahalli"
EXP_DIR = Path("results/research/exp_ladder_R3_amend_val2")
NUM_WORKERS = 4

CONDITIONS = [
    # 12 Stationary conditions (4 patterns x 3 levels)
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
    # 6 Non-stationary conditions (3 scenarios x medium/heavy)
    ("ramp_peak", "medium"),
    ("ramp_peak", "heavy"),
    ("surge_shift", "medium"),
    ("surge_shift", "heavy"),
    ("lane_closure", "medium"),
    ("lane_closure", "heavy"),
]

PRIMARY_METRICS = [
    ("p95_wait_s", "P95 Wait (s)", True),
    ("gt_max_queue_m", "Ground-Truth Max Queue (m)", True),
    ("approach_wait_gap_s", "Approach Wait Gap (s)", True),
]

SECONDARY_METRICS = [
    ("avg_wait_s", "Mean Wait (s)", True),
    ("gt_avg_queue_m", "Ground-Truth Mean Queue (m)", True),
    ("max_queue_m", "Detector Max Queue (m) [Secondary]", True),
    ("avg_queue_m", "Detector Mean Queue (m) [Secondary]", True),
    ("completion_rate", "Completion Rate", False),
    ("unfinished_vehicles", "Unfinished Vehicles", True),
    ("switches_per_h", "Switches per Hour", None),
]


def run_cell_worker(task):
    scenario, demand_level, seed, policy, out_dir = task
    out_dir = Path(out_dir)
    if (out_dir / "metrics.json").exists():
        with open(out_dir / "metrics.json", "r", encoding="utf-8") as f:
            return json.load(f)

    t0 = time.time()
    res = run_simulation(
        scenario=scenario,
        policy=policy,
        seed=seed,
        network=NETWORK,
        demand_level=demand_level,
        out_dir=out_dir,
    )
    res["elapsed_wallclock_s"] = round(time.time() - t0, 1)
    return res


def execute_matrix(policies: List[str], max_workers: int = NUM_WORKERS):
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for pol in policies:
        for sc, dl in CONDITIONS:
            for s in VALIDATION_2_SEEDS:
                run_id = f"{NETWORK}_{sc}_{dl}_{pol}_s{s}"
                run_dir = EXP_DIR / run_id
                tasks.append((sc, dl, s, pol, str(run_dir)))

    total_tasks = len(tasks)
    print(f"Total simulations to execute: {total_tasks} across {len(policies)} policies, 18 conditions, 10 seeds.")
    completed = 0
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(run_cell_worker, task): task for task in tasks}
        for future in as_completed(future_map):
            completed += 1
            if completed % 30 == 0 or completed == total_tasks:
                elapsed = time.time() - t_start
                rate = completed / max(1.0, elapsed)
                remaining = (total_tasks - completed) / max(0.01, rate)
                print(f"[{completed}/{total_tasks}] runs finished ({rate:.1f} runs/s, ~{remaining:.0f}s remaining)...")


def compute_bootstrap_p_value(deltas: np.ndarray, n_resamples: int = 10_000, seed: int = 42) -> float:
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_means = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = np.mean(deltas[idx])
    # Two-sided empirical p-value for H0: mean delta == 0
    p_le = np.mean(boot_means <= 0.0)
    p_ge = np.mean(boot_means >= 0.0)
    return float(2.0 * min(p_le, p_ge))


def load_policy_dataframe(policy: str) -> pd.DataFrame:
    records = []
    for sc, dl in CONDITIONS:
        for s in VALIDATION_2_SEEDS:
            run_id = f"{NETWORK}_{sc}_{dl}_{policy}_s{s}"
            p_metrics = EXP_DIR / run_id / "metrics.json"
            with open(p_metrics, "r", encoding="utf-8") as f:
                d = json.load(f)
            d["policy"] = policy
            d["scenario"] = sc
            d["demand_level"] = dl
            d["seed"] = s
            # Derived switches per hour: 2 transitions per cycle over demand window (1800s = 0.5h)
            cycles = d.get("cycles", 0)
            d["switches_per_h"] = round(cycles * 2.0 / (C.SIM.demand_duration_s / 3600.0), 1)
            d["unfinished_vehicles"] = d.get("vehicles_unfinished", 0)
            records.append(d)
    df = pd.DataFrame(records)
    df.sort_values(by=["scenario", "demand_level", "seed"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def analyze_amendment():
    print("\n--- Loading simulation results from EXP_DIR ---")
    df_cand = load_policy_dataframe("hybrid_r3")
    df_base = load_policy_dataframe("hybrid_queue_adaptive")
    df_web = load_policy_dataframe("webster_measured")

    n_pairs = len(df_cand)
    assert len(df_base) == n_pairs == len(df_web) == 180, f"Expected 180 pairs, found {n_pairs}"

    # Save raw_runs.csv and aggregate.csv
    df_all = pd.concat([df_cand, df_base, df_web], ignore_index=True)
    df_all.to_csv(EXP_DIR / "raw_runs.csv", index=False)

    agg = df_all.groupby(["policy", "scenario", "demand_level"])[[
        "avg_wait_s", "p95_wait_s", "gt_max_queue_m", "gt_avg_queue_m",
        "approach_wait_gap_s", "max_queue_m", "completion_rate", "unfinished_vehicles", "switches_per_h"
    ]].mean().reset_index()
    agg.to_csv(EXP_DIR / "aggregate.csv", index=False)

    print(f"Total paired cells analyzed: {n_pairs} (18 conditions x 10 seeds)")

    # 1. Primary Metrics Analysis (R3 - Default)
    primary_results = []
    stats_summary = {}
    p_values = {}

    for metric_col, label, lower_is_better in PRIMARY_METRICS:
        deltas = df_cand[metric_col].values - df_base[metric_col].values
        point, ci_low, ci_high = bootstrap_percentile_ci(
            deltas, n_resamples=10_000, confidence_level=0.95, random_seed=C.RESEARCH.bootstrap_seed
        )
        pval = compute_bootstrap_p_value(deltas, n_resamples=10_000, seed=C.RESEARCH.bootstrap_seed)
        p_values[metric_col] = pval

        base_mean = float(df_base[metric_col].mean())
        cand_mean = float(df_cand[metric_col].mean())
        pct_change = ((cand_mean - base_mean) / abs(base_mean)) * 100.0 if base_mean != 0 else 0.0

        raw_improves = (ci_high < 0.0) if lower_is_better else (ci_low > 0.0)

        primary_results.append({
            "col": metric_col,
            "label": label,
            "lower_is_better": lower_is_better,
            "base_mean": base_mean,
            "cand_mean": cand_mean,
            "delta": point,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "pct_change": pct_change,
            "raw_improves": raw_improves,
            "pval": pval,
        })

    # Holm-Bonferroni correction across the 3 primary metrics
    # Sort by p-value ascending
    primary_results.sort(key=lambda x: x["pval"])
    m_tests = len(primary_results)
    for rank, res in enumerate(primary_results):
        alpha_holm = 0.05 / (m_tests - rank)
        res["rank"] = rank + 1
        res["alpha_holm"] = alpha_holm
        res["holm_significant"] = bool(res["pval"] <= alpha_holm and res["raw_improves"])

    # 2. Acceptance Rule Evaluation Step-by-Step
    # Rule 1: At least one primary metric strictly improves with 95% CI excluding zero
    # (and evaluated with Holm correction)
    improving_primaries = [r for r in primary_results if r["raw_improves"]]
    rule1_pass = len(improving_primaries) > 0

    # Rule 2: Grand-mean waiting time does not degrade by more than 1.0%
    base_grand_wait = float(df_base["avg_wait_s"].mean())
    cand_grand_wait = float(df_cand["avg_wait_s"].mean())
    grand_wait_degradation_pct = ((cand_grand_wait - base_grand_wait) / base_grand_wait) * 100.0
    rule2_pass = bool(grand_wait_degradation_pct <= 1.0)

    # Rule 3: Network completion rate does not decrease and unfinished vehicle count does not increase
    base_comp = float(df_base["completion_rate"].mean())
    cand_comp = float(df_cand["completion_rate"].mean())
    base_unf = int(df_base["unfinished_vehicles"].sum())
    cand_unf = int(df_cand["unfinished_vehicles"].sum())
    rule3_pass = bool(cand_comp >= base_comp and cand_unf <= base_unf)

    verdict = "KEEP" if (rule1_pass and rule2_pass and rule3_pass) else "CUT"

    # Secondary Metrics Analysis
    secondary_results = []
    for metric_col, label, lower_is_better in SECONDARY_METRICS:
        deltas = df_cand[metric_col].values - df_base[metric_col].values
        point, ci_low, ci_high = bootstrap_percentile_ci(
            deltas, n_resamples=10_000, confidence_level=0.95, random_seed=C.RESEARCH.bootstrap_seed
        )
        base_mean = float(df_base[metric_col].mean())
        cand_mean = float(df_cand[metric_col].mean())
        pct_change = ((cand_mean - base_mean) / abs(base_mean)) * 100.0 if base_mean != 0 else 0.0
        improves = False
        if lower_is_better is True:
            improves = (ci_high < 0.0)
        elif lower_is_better is False:
            improves = (ci_low > 0.0)

        secondary_results.append({
            "col": metric_col,
            "label": label,
            "base_mean": base_mean,
            "cand_mean": cand_mean,
            "delta": point,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "pct_change": pct_change,
            "improves": improves,
        })

    # Paired vs webster_measured comparison
    web_comparison = {}
    for pol_name, df_p in [("hybrid_r3", df_cand), ("hybrid_queue_adaptive", df_base)]:
        p_stats = {}
        for m_col, m_label, m_lower in PRIMARY_METRICS + SECONDARY_METRICS:
            deltas = df_p[m_col].values - df_web[m_col].values
            point, ci_low, ci_high = bootstrap_percentile_ci(
                deltas, n_resamples=10_000, confidence_level=0.95, random_seed=C.RESEARCH.bootstrap_seed
            )
            p_mean = float(df_p[m_col].mean())
            w_mean = float(df_web[m_col].mean())
            pct = ((p_mean - w_mean) / abs(w_mean)) * 100.0 if w_mean != 0 else 0.0
            p_stats[m_col] = {
                "label": m_label,
                "pol_mean": round(p_mean, 2),
                "web_mean": round(w_mean, 2),
                "delta": round(point, 2),
                "ci_low": round(ci_low, 2),
                "ci_high": round(ci_high, 2),
                "pct_change": round(pct, 2),
            }
        web_comparison[pol_name] = p_stats

    # Assemble manifest and report
    manifest = {
        "experiment_id": "exp_ladder_R3_amend_val2",
        "description": "Task 4 R3 Amendment Test on Validation-2 Seeds (111-120)",
        "policy_version": "v2_phase10b",
        "candidate": "hybrid_r3",
        "baseline": "hybrid_queue_adaptive",
        "reference": "webster_measured",
        "n_seeds": len(VALIDATION_2_SEEDS),
        "seeds": list(VALIDATION_2_SEEDS),
        "n_conditions": len(CONDITIONS),
        "n_pairs": n_pairs,
        "verdict": verdict,
        "rule1_primary_improved": rule1_pass,
        "rule2_wait_degradation_pass": rule2_pass,
        "rule3_completion_pass": rule3_pass,
        "grand_wait_degradation_pct": round(grand_wait_degradation_pct, 2),
        "primary_results": primary_results,
        "secondary_results": secondary_results,
        "vs_webster_measured": web_comparison,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(EXP_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Print summary to console
    print("\n=================================================================")
    print(f"R3 AMENDMENT TEST VERDICT: >>> {verdict} <<<")
    print("=================================================================")
    print(f"Step 1: Primary Metrics Improvement Check (n={n_pairs} pairs):")
    for r in primary_results:
        imp_str = "YES (EXCLUDES 0)" if r["raw_improves"] else "NO (includes 0)"
        holm_str = f"p={r['pval']:.4f} vs alpha_holm={r['alpha_holm']:.4f}"
        print(f"  - {r['label']}: Base={r['base_mean']:.2f}, Cand={r['cand_mean']:.2f}, Delta={r['delta']:.2f} (95% CI [{r['ci_low']:.2f}, {r['ci_high']:.2f}], {r['pct_change']:+.2f}%) | Improves: {imp_str} ({holm_str})")
    print(f"  -> Rule 1 Pass: {rule1_pass}")

    print(f"\nStep 2: Grand-Mean Wait Degradation Check:")
    print(f"  - Base Wait: {base_grand_wait:.2f} s | Cand Wait: {cand_grand_wait:.2f} s | Change: {grand_wait_degradation_pct:+.2f}%")
    print(f"  - Max allowed degradation: +1.00%")
    print(f"  -> Rule 2 Pass: {rule2_pass}")

    print(f"\nStep 3: Completion Rate & Unfinished Vehicles Check:")
    print(f"  - Completion Rate: Base={base_comp*100:.2f}%, Cand={cand_comp*100:.2f}%")
    print(f"  - Unfinished Vehicles: Base={base_unf}, Cand={cand_unf}")
    print(f"  -> Rule 3 Pass: {rule3_pass}")

    print(f"\nFINAL VERDICT: {verdict}")
    if verdict == "CUT":
        print("Verdict Reason: R3 failed pre-registered acceptance criteria on validation-2 block (seeds 111-120). It is permanently CUT.")
    else:
        print("Verdict Reason: R3 satisfied all pre-registered acceptance criteria on validation-2 block. It is KEPT.")

    return manifest


def main():
    t0 = time.time()
    execute_matrix(["hybrid_queue_adaptive", "hybrid_r3", "webster_measured"])
    manifest = analyze_amendment()
    elapsed = time.time() - t0
    print(f"\nTask 4 execution completed in {elapsed:.1f} s ({elapsed/60.0:.1f} min).")


if __name__ == "__main__":
    main()
