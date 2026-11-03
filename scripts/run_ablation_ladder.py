"""Phase 10 Ablation Ladder Runner and Statistical Evaluator.

Executes sequential ablation ladder evaluation on validation seeds (106–110)
across 18 demand conditions (12 stationary + 6 non-stationary).

Evaluates candidate rungs against the immediately preceding rung using the
pre-registered rule from docs/PREREGISTRATION.md:
- Keep candidate rung if and only if:
  1. At least one primary metric improves with its paired bootstrap 95% CI strictly excluding zero; AND
  2. Grand-mean waiting time does not degrade by more than 1.0%; AND
  3. Network completion rate does not decrease and unfinished vehicle count does not increase.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from dp1 import config as C
from dp1.runner import run_simulation
from dp1.research.stats import bootstrap_percentile_ci

VALIDATION_SEEDS = (106, 107, 108, 109, 110)
NETWORK = "marathahalli"

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
    ("p95_wait_s", "P95 Wait (s)", True),           # True = lower is better (delta < 0 is improvement)
    ("max_queue_m", "Max Queue (m)", True),          # True = lower is better
    ("approach_wait_gap_s", "Approach Gap (s)", True) # True = lower is better
]

SECONDARY_METRICS = [
    ("avg_wait_s", "Mean Wait (s)", True),
    ("avg_queue_m", "Mean Queue (m)", True),
    ("throughput_veh_per_h", "Throughput (veh/h)", False), # False = higher is better
    ("completion_rate", "Completion Rate", False),
    ("unfinished_vehicles", "Unfinished Vehicles", True),
    ("cycles", "Switch Cycles", None),
]


def run_cell_worker(task):
    """Execute single simulation run worker."""
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


def execute_policy_matrix(policy: str, out_base_dir: Path, max_workers: int = 4) -> List[Dict]:
    """Execute all 18 conditions x 5 seeds for a given policy in parallel."""
    out_base_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for sc, dl in CONDITIONS:
        for s in VALIDATION_SEEDS:
            run_id = f"{NETWORK}_{sc}_{dl}_{policy}_s{s}"
            run_dir = out_base_dir / run_id
            tasks.append((sc, dl, s, policy, str(run_dir)))

    print(f"[{policy}] Executing {len(tasks)} runs with {max_workers} processes...")
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_cell_worker, t): t for t in tasks}
        done_cnt = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done_cnt += 1
            if done_cnt % 18 == 0 or done_cnt == len(tasks):
                print(f"  [{policy}] Progress: {done_cnt}/{len(tasks)} runs completed.")

    return results


def copy_or_link_results(src_policy: str, src_dir: Path, dst_dir: Path):
    """Replicate completed runs from a shared cache directory to an experiment dir."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for sc, dl in CONDITIONS:
        for s in VALIDATION_SEEDS:
            run_id = f"{NETWORK}_{sc}_{dl}_{src_policy}_s{s}"
            src_run = src_dir / run_id
            dst_run = dst_dir / run_id
            if src_run.exists() and not dst_run.exists():
                shutil.copytree(src_run, dst_run)


def evaluate_rung_pair(
    candidate_policy: str,
    baseline_policy: str,
    exp_dir: Path,
) -> Dict:
    """Compute paired statistics and evaluate pre-registered keep/cut rule."""
    cand_records = []
    base_records = []

    for sc, dl in CONDITIONS:
        for s in VALIDATION_SEEDS:
            cand_id = f"{NETWORK}_{sc}_{dl}_{candidate_policy}_s{s}"
            base_id = f"{NETWORK}_{sc}_{dl}_{baseline_policy}_s{s}"

            cand_file = exp_dir / cand_id / "metrics.json"
            base_file = exp_dir / base_id / "metrics.json"

            if not cand_file.exists() or not base_file.exists():
                raise FileNotFoundError(f"Missing run file: {cand_file} or {base_file}")

            with open(cand_file, "r", encoding="utf-8") as f:
                c_m = json.load(f)
            with open(base_file, "r", encoding="utf-8") as f:
                b_m = json.load(f)

            cand_records.append(c_m)
            base_records.append(b_m)

    df_cand = pd.DataFrame(cand_records)
    df_base = pd.DataFrame(base_records)

    # Sort to guarantee exact paired alignment
    sort_keys = ["scenario", "demand_level", "seed"]
    df_cand.sort_values(by=sort_keys, inplace=True)
    df_base.sort_values(by=sort_keys, inplace=True)

    n_pairs = len(df_cand)
    assert n_pairs == len(df_base) == 90, f"Expected 90 paired runs, got {n_pairs}"

    # Compute paired deltas (candidate - baseline)
    stats_summary = {}
    primary_improvements = []

    # 1. Primary Metrics Check
    for metric_col, label, lower_is_better in PRIMARY_METRICS:
        deltas = df_cand[metric_col].values - df_base[metric_col].values
        point, ci_low, ci_high = bootstrap_percentile_ci(
            deltas, n_resamples=10_000, confidence_level=0.95, random_seed=42
        )
        base_mean = float(df_base[metric_col].mean())
        cand_mean = float(df_cand[metric_col].mean())
        pct_change = ((cand_mean - base_mean) / abs(base_mean)) * 100.0 if base_mean != 0 else 0.0

        improves = (ci_high < 0.0) if lower_is_better else (ci_low > 0.0)
        if improves:
            primary_improvements.append((metric_col, label, point, ci_low, ci_high))

        stats_summary[metric_col] = {
            "name": label,
            "is_primary": True,
            "base_mean": round(base_mean, 2),
            "cand_mean": round(cand_mean, 2),
            "delta_mean": round(point, 2),
            "ci_95_low": round(ci_low, 2),
            "ci_95_high": round(ci_high, 2),
            "pct_change": round(pct_change, 2),
            "strictly_improves": bool(improves),
        }

    # 2. Grand-Mean Waiting Time Degradation Check (Condition 2)
    base_grand_wait = float(df_base["avg_wait_s"].mean())
    cand_grand_wait = float(df_cand["avg_wait_s"].mean())
    grand_wait_degradation_pct = ((cand_grand_wait - base_grand_wait) / base_grand_wait) * 100.0
    wait_degradation_pass = (grand_wait_degradation_pct <= 1.0)

    # 3. Completion Rate & Unfinished Vehicles Check (Condition 3)
    base_comp = float(df_base["completion_rate"].mean())
    cand_comp = float(df_cand["completion_rate"].mean())
    base_unf = int(df_base["unfinished_vehicles"].sum()) if "unfinished_vehicles" in df_base else 0
    cand_unf = int(df_cand["unfinished_vehicles"].sum()) if "unfinished_vehicles" in df_cand else 0

    completion_pass = (cand_comp >= base_comp) and (cand_unf <= base_unf)

    # 4. Secondary Metrics
    for metric_col, label, lower_is_better in SECONDARY_METRICS:
        if metric_col in df_cand.columns and metric_col in df_base.columns:
            deltas = df_cand[metric_col].values - df_base[metric_col].values
            point, ci_low, ci_high = bootstrap_percentile_ci(
                deltas, n_resamples=10_000, confidence_level=0.95, random_seed=42
            )
            base_mean = float(df_base[metric_col].mean())
            cand_mean = float(df_cand[metric_col].mean())
            pct_change = ((cand_mean - base_mean) / abs(base_mean)) * 100.0 if base_mean != 0 else 0.0

            stats_summary[metric_col] = {
                "name": label,
                "is_primary": False,
                "base_mean": round(base_mean, 2),
                "cand_mean": round(cand_mean, 2),
                "delta_mean": round(point, 2),
                "ci_95_low": round(ci_low, 2),
                "ci_95_high": round(ci_high, 2),
                "pct_change": round(pct_change, 2),
                "strictly_improves": bool((ci_high < 0.0) if lower_is_better else (ci_low > 0.0)) if lower_is_better is not None else False,
            }

    # Evaluate Verdict
    rule1_pass = len(primary_improvements) > 0
    rule2_pass = wait_degradation_pass
    rule3_pass = completion_pass

    verdict = "KEEP" if (rule1_pass and rule2_pass and rule3_pass) else "CUT"
    reason = []
    if not rule1_pass:
        reason.append("No primary metric 95% CI strictly excludes zero in favor of candidate")
    if not rule2_pass:
        reason.append(f"Grand-mean wait degraded by {grand_wait_degradation_pct:.2f}% (> 1.0% tolerance)")
    if not rule3_pass:
        reason.append(f"Completion rate degraded or unfinished vehicles increased ({cand_unf} vs {base_unf})")
    if verdict == "KEEP":
        improved_names = [f"{l} (CI: [{low:.2f}, {high:.2f}])" for _, l, _, low, high in primary_improvements]
        reason.append(f"Primary metrics improved: {', '.join(improved_names)}; wait degradation {grand_wait_degradation_pct:.2f}% <= 1.0%; completion intact")

    verdict_record = {
        "candidate": candidate_policy,
        "baseline": baseline_policy,
        "n_pairs": n_pairs,
        "verdict": verdict,
        "rule1_primary_improved": rule1_pass,
        "rule2_wait_degradation_pass": rule2_pass,
        "rule3_completion_pass": rule3_pass,
        "grand_wait_degradation_pct": round(grand_wait_degradation_pct, 2),
        "primary_improvements": primary_improvements,
        "reasons": reason,
        "metrics": stats_summary,
    }

    with open(exp_dir / "verdict.json", "w", encoding="utf-8") as f:
        json.dump(verdict_record, f, indent=2)

    return verdict_record


def evaluate_vs_webster(candidate_policy: str, exp_dir: Path) -> Dict:
    """Compute paired statistics vs webster_measured reference on seeds 106-110."""
    cand_records = []
    web_records = []

    for sc, dl in CONDITIONS:
        for s in VALIDATION_SEEDS:
            cand_id = f"{NETWORK}_{sc}_{dl}_{candidate_policy}_s{s}"
            web_id = f"{NETWORK}_{sc}_{dl}_webster_measured_s{s}"

            with open(exp_dir / cand_id / "metrics.json", "r", encoding="utf-8") as f:
                c_m = json.load(f)
            with open(exp_dir / web_id / "metrics.json", "r", encoding="utf-8") as f:
                w_m = json.load(f)

            cand_records.append(c_m)
            web_records.append(w_m)

    df_cand = pd.DataFrame(cand_records)
    df_web = pd.DataFrame(web_records)

    sort_keys = ["scenario", "demand_level", "seed"]
    df_cand.sort_values(by=sort_keys, inplace=True)
    df_web.sort_values(by=sort_keys, inplace=True)

    vs_webster = {}
    for metric_col, label, _ in PRIMARY_METRICS + SECONDARY_METRICS:
        if metric_col in df_cand.columns and metric_col in df_web.columns:
            deltas = df_cand[metric_col].values - df_web[metric_col].values
            point, ci_low, ci_high = bootstrap_percentile_ci(
                deltas, n_resamples=10_000, confidence_level=0.95, random_seed=42
            )
            cand_mean = float(df_cand[metric_col].mean())
            web_mean = float(df_web[metric_col].mean())
            pct_change = ((cand_mean - web_mean) / abs(web_mean)) * 100.0 if web_mean != 0 else 0.0

            vs_webster[metric_col] = {
                "name": label,
                "cand_mean": round(cand_mean, 2),
                "webster_mean": round(web_mean, 2),
                "delta_mean": round(point, 2),
                "ci_95_low": round(ci_low, 2),
                "ci_95_high": round(ci_high, 2),
                "pct_change": round(pct_change, 2),
            }

    with open(exp_dir / "paired_vs_webster.json", "w", encoding="utf-8") as f:
        json.dump(vs_webster, f, indent=2)

    return vs_webster
