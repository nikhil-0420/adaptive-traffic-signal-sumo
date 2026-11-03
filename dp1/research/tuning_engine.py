"""Phase 11: Equal-Budget Policy Optimization Engine.

Implements the pre-registered protocol in docs/TUNING_PROTOCOL.md:
1. Reference baseline calculation (webster_measured on all 18 conditions, seeds 101-110).
2. Equal-budget random search (30 trials per policy) on training seeds 101-105.
3. Top-3 candidate validation on seeds 106-110.
4. Selection and freezing of winning configs to configs/final_<policy>.yaml.
5. Parameter sensitivity analysis.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import dataclasses
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def dump_yaml(data: dict, indent: int = 0) -> str:
    """Format dict as clean YAML string without external dependencies."""
    lines = []
    prefix = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(dump_yaml(v, indent + 1))
        elif isinstance(v, (list, tuple)):
            lines.append(f"{prefix}{k}:")
            for item in v:
                lines.append(f"{prefix}  - {item}")
        elif isinstance(v, str):
            lines.append(f"{prefix}{k}: \"{v}\"")
        elif isinstance(v, bool):
            lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{prefix}{k}: null")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1 import config as C
from dp1.config import AdaptiveConfig, QueueExtensionConfig, HybridQueueAdaptiveConfig
from dp1.runner import run_simulation

NETWORK = "marathahalli"
NUM_WORKERS = 4
N_TRIALS = 30
RNG_SEED = 202611

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

TUNING_BASE_DIR = Path("results/tuning")
REF_DIR = TUNING_BASE_DIR / "reference_webster"


# -----------------------------------------------------------------------------
# Worker Function
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Step 0: Reference Baseline Generator
# -----------------------------------------------------------------------------
def generate_reference_baselines():
    print("=== Step 0: Generating / Loading Reference Baselines (webster_measured) ===")
    REF_DIR.mkdir(parents=True, exist_ok=True)
    all_seeds = list(TRAIN_SEEDS) + list(VAL_SEEDS)
    tasks = []
    for sc, dl in CONDITIONS:
        for s in all_seeds:
            run_dir = REF_DIR / f"{NETWORK}_{sc}_{dl}_webster_measured_s{s}"
            tasks.append((sc, dl, s, "webster_measured", None, str(run_dir)))

    completed = 0
    total = len(tasks)
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_map = {executor.submit(run_cell_worker, t): t for t in tasks}
        for future in as_completed(future_map):
            completed += 1
            if completed % 30 == 0 or completed == total:
                print(f"  Reference runs: [{completed}/{total}] done...")

    # Load results
    ref_records = []
    for sc, dl in CONDITIONS:
        for s in all_seeds:
            run_dir = REF_DIR / f"{NETWORK}_{sc}_{dl}_webster_measured_s{s}"
            with open(run_dir / "metrics.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            d["scenario"] = sc
            d["demand_level"] = dl
            d["seed"] = s
            ref_records.append(d)

    ref_df = pd.DataFrame(ref_records)

    # Compute reference norms per condition for train (101-105) and val (106-110)
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


# -----------------------------------------------------------------------------
# Step 1: Candidate Sampling
# -----------------------------------------------------------------------------
def sample_configurations() -> Dict[str, List[Dict[str, Any]]]:
    rng = np.random.default_rng(RNG_SEED)

    # 1. Hybrid Queue Adaptive (Kept Rungs: ("R4",))
    hybrid_trials = []
    for i in range(N_TRIALS):
        if i == 0:
            # Default configuration as trial 0
            cfg = {
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
            }
        else:
            cfg = {
                "extend_step_s": round(float(rng.uniform(1.0, 5.0)), 1),
                "extend_threshold_m": round(float(rng.uniform(2.0, 10.0)), 1),
                "fairness_ratio": round(float(rng.uniform(0.8, 2.0)), 2),
                "gap_out_s": round(float(rng.uniform(1.5, 5.0)), 1),
                "min_competing_queue_m": round(float(rng.uniform(1.0, 5.0)), 1),
                "max_competing_wait_s": round(float(rng.uniform(20.0, 45.0)), 1),
                "r4_warmup_s": round(float(rng.uniform(180.0, 420.0)), 0),
                "demand_weight_active": round(float(rng.uniform(0.5, 1.5)), 2),
                "demand_weight_competing": round(float(rng.uniform(0.5, 1.5)), 2),
                "arrival_detection_threshold": round(float(rng.uniform(0.2, 1.5)), 2),
            }
        hybrid_trials.append(cfg)

    # 2. Queue Extension
    qext_trials = []
    for i in range(N_TRIALS):
        if i == 0:
            cfg = {
                "initial_green_s": 15.0,
                "extend_step_s": 3.0,
                "extend_threshold_m": 4.0,
                "min_competing_queue_m": 2.0,
                "max_competing_wait_s": 35.0,
                "fairness_ratio": 1.2,
                "gap_out_s": 3.0,
            }
        else:
            cfg = {
                "initial_green_s": round(float(rng.uniform(10.0, 25.0)), 1),
                "extend_step_s": round(float(rng.uniform(1.0, 5.0)), 1),
                "extend_threshold_m": round(float(rng.uniform(2.0, 10.0)), 1),
                "min_competing_queue_m": round(float(rng.uniform(1.0, 5.0)), 1),
                "max_competing_wait_s": round(float(rng.uniform(20.0, 45.0)), 1),
                "fairness_ratio": round(float(rng.uniform(0.8, 2.0)), 2),
                "gap_out_s": round(float(rng.uniform(1.5, 5.0)), 1),
            }
        qext_trials.append(cfg)

    # 3. Adaptive
    adapt_trials = []
    for i in range(N_TRIALS):
        if i == 0:
            cfg = {
                "k_s_per_m": 0.30,
                "extend_threshold_m": 15.0,
                "gap_out_s": 3,
                "min_competing_queue_m": 1.0,
            }
        else:
            cfg = {
                "k_s_per_m": round(float(rng.uniform(0.10, 0.60)), 2),
                "extend_threshold_m": round(float(rng.uniform(5.0, 25.0)), 1),
                "gap_out_s": int(rng.integers(1, 6)),
                "min_competing_queue_m": round(float(rng.uniform(0.5, 4.0)), 1),
            }
        adapt_trials.append(cfg)

    return {
        "hybrid_queue_adaptive": hybrid_trials,
        "queue_extension": qext_trials,
        "adaptive": adapt_trials,
    }


# -----------------------------------------------------------------------------
# Step 2 & 3: Evaluation Engine
# -----------------------------------------------------------------------------
def evaluate_policy_batch(policy: str, trial_id: str, param_dict: Dict[str, Any], seeds: Tuple[int, ...], ref_norm: Dict[Tuple[str, str], Dict[str, float]], trial_out_dir: Path) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]]]:
    trial_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct config object
    if policy == "hybrid_queue_adaptive":
        cfg_obj = HybridQueueAdaptiveConfig(rungs=("R4",), **param_dict)
    elif policy == "queue_extension":
        cfg_obj = QueueExtensionConfig(**param_dict)
    elif policy == "adaptive":
        cfg_obj = AdaptiveConfig(**param_dict)
    else:
        raise ValueError(f"Unknown policy {policy}")

    policy_kwargs = {"cfg": cfg_obj}
    tasks = []
    for sc, dl in CONDITIONS:
        for s in seeds:
            run_dir = trial_out_dir / f"{NETWORK}_{sc}_{dl}_{policy}_s{s}"
            tasks.append((sc, dl, s, policy, policy_kwargs, str(run_dir)))

    # Execute simulation runs in parallel
    results = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_map = {executor.submit(run_cell_worker, t): t for t in tasks}
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)

    # Check for crashes
    crashed = any(r.get("status") == "FAILED" for r in results)
    if crashed:
        return float("inf"), {"status": "FAILED"}, []

    # Aggregate by condition
    cond_metrics = []
    composite_components = []
    for sc, dl in CONDITIONS:
        matching = [r for r in results if r["scenario"] == sc and r["demand_level"] == dl]
        m_wait = float(np.mean([r["avg_wait_s"] for r in matching]))
        p95_w = float(np.mean([r["p95_wait_s"] for r in matching]))
        gap_w = float(np.mean([r["approach_wait_gap_s"] for r in matching]))
        max_q = float(np.max([r.get("gt_ext_max_queue_m") or r.get("max_queue_m", 0.0) for r in matching]))

        ref = ref_norm[(sc, dl)]
        norm_mean = m_wait / max(0.1, ref["mean_wait"])
        norm_p95 = p95_w / max(0.1, ref["p95_wait"])
        norm_gap = gap_w / max(0.1, ref["approach_wait_gap"])

        cond_composite = 0.4 * norm_mean + 0.3 * norm_p95 + 0.3 * norm_gap
        composite_components.append(cond_composite)

        cond_metrics.append({
            "scenario": sc,
            "demand_level": dl,
            "mean_wait_s": round(m_wait, 2),
            "p95_wait_s": round(p95_w, 2),
            "approach_wait_gap_s": round(gap_w, 2),
            "max_queue_m": round(max_q, 2),
            "cond_composite": round(cond_composite, 4),
        })

    composite_score = float(np.mean(composite_components))
    summary = {
        "status": "COMPLETED",
        "composite": round(composite_score, 4),
        "mean_wait_grand": round(float(np.mean([cm["mean_wait_s"] for cm in cond_metrics])), 2),
        "p95_wait_grand": round(float(np.mean([cm["p95_wait_s"] for cm in cond_metrics])), 2),
        "gap_grand": round(float(np.mean([cm["approach_wait_gap_s"] for cm in cond_metrics])), 2),
        "max_queue_grand": round(float(np.max([cm["max_queue_m"] for cm in cond_metrics])), 2),
    }
    return composite_score, summary, cond_metrics


# -----------------------------------------------------------------------------
# Main Orchestrator
# -----------------------------------------------------------------------------
def main():
    t_start = time.time()
    print("================================================================================")
    print("PHASE 11: EQUAL-BUDGET POLICY OPTIMIZATION")
    print(f"Policies: hybrid_queue_adaptive, queue_extension, adaptive")
    print(f"Trials per Policy: {N_TRIALS} | Conditions: {len(CONDITIONS)} | Workers: {NUM_WORKERS}")
    print("================================================================================\n")

    # Step 0: Reference Baselines
    ref_train, ref_val = generate_reference_baselines()

    # Step 1: Sample configurations
    sampled_configs = sample_configurations()

    policies = ["hybrid_queue_adaptive", "queue_extension", "adaptive"]
    tuning_results = {}
    top3_per_policy = {}

    # Step 2: Training Search across 30 Trials per Policy
    for pol in policies:
        print(f"\n================================================================================")
        print(f"SEARCHING POLICY: {pol} (30 Trials on Training Seeds 101-105)")
        print(f"================================================================================")
        pol_dir = TUNING_BASE_DIR / pol
        pol_dir.mkdir(parents=True, exist_ok=True)
        trial_records = []

        trials = sampled_configs[pol]
        for t_idx, params in enumerate(trials):
            t_id = f"trial_{t_idx:02d}"
            t_dir = pol_dir / t_id
            t0 = time.time()
            score, summary, _ = evaluate_policy_batch(
                policy=pol,
                trial_id=t_id,
                param_dict=params,
                seeds=TRAIN_SEEDS,
                ref_norm=ref_train,
                trial_out_dir=t_dir,
            )
            elapsed = time.time() - t0
            rec = {
                "trial_id": t_id,
                "status": summary["status"],
                "composite": score,
                "mean_wait_s": summary.get("mean_wait_grand", float("nan")),
                "p95_wait_s": summary.get("p95_wait_grand", float("nan")),
                "approach_wait_gap_s": summary.get("gap_grand", float("nan")),
                "max_queue_m": summary.get("max_queue_grand", float("nan")),
                "elapsed_s": round(elapsed, 1),
                **params,
            }
            trial_records.append(rec)
            is_default = " [DEFAULT]" if t_idx == 0 else ""
            print(f"  [{pol}] {t_id}{is_default}: Composite={score:.4f} | Wait={rec['mean_wait_s']:.1f}s | P95={rec['p95_wait_s']:.1f}s | Gap={rec['approach_wait_gap_s']:.1f}s ({elapsed:.1f}s)")

        trials_df = pd.DataFrame(trial_records)
        trials_df.to_csv(pol_dir / "trials.csv", index=False)
        tuning_results[pol] = trials_df

        # Rank valid trials
        valid_df = trials_df[trials_df["status"] == "COMPLETED"].sort_values("composite")
        top3 = valid_df.head(3).to_dict(orient="records")
        top3_per_policy[pol] = top3
        print(f"\n  Top 3 Candidates for {pol} (Train Seeds 101-105):")
        for rank, c in enumerate(top3, start=1):
            print(f"    #{rank} {c['trial_id']}: Composite={c['composite']:.4f} | Wait={c['mean_wait_s']:.1f}s | P95={c['p95_wait_s']:.1f}s | Gap={c['approach_wait_gap_s']:.1f}s")

    # Step 3: Validation Gating of Top 3 on Seeds 106-110
    print(f"\n================================================================================")
    print(f"VALIDATION GATING ON HELD-OUT SEEDS 106-110 (Top 3 per Policy)")
    print(f"================================================================================")
    
    winners = {}
    default_vs_tuned = {}

    for pol in policies:
        print(f"\n--- Validating {pol} ---")
        val_records = []
        
        # Also evaluate default configuration (trial_00) on validation seeds for baseline reference
        default_params = sampled_configs[pol][0]
        def_dir = TUNING_BASE_DIR / pol / "val_default"
        def_score, def_sum, _ = evaluate_policy_batch(
            policy=pol,
            trial_id="val_default",
            param_dict=default_params,
            seeds=VAL_SEEDS,
            ref_norm=ref_val,
            trial_out_dir=def_dir,
        )
        print(f"  Default Configuration Validation: Composite={def_score:.4f} | Wait={def_sum['mean_wait_grand']:.1f}s | P95={def_sum['p95_wait_grand']:.1f}s")

        for cand in top3_per_policy[pol]:
            t_id = cand["trial_id"]
            # Extract only policy params
            params = {k: cand[k] for k in cand if k not in ("trial_id", "status", "composite", "mean_wait_s", "p95_wait_s", "approach_wait_gap_s", "max_queue_m", "elapsed_s")}
            val_dir = TUNING_BASE_DIR / pol / f"val_{t_id}"
            val_score, val_sum, _ = evaluate_policy_batch(
                policy=pol,
                trial_id=f"val_{t_id}",
                param_dict=params,
                seeds=VAL_SEEDS,
                ref_norm=ref_val,
                trial_out_dir=val_dir,
            )
            val_rec = {
                "trial_id": t_id,
                "train_composite": cand["composite"],
                "val_composite": val_score,
                "val_mean_wait_s": val_sum["mean_wait_grand"],
                "val_p95_wait_s": val_sum["p95_wait_grand"],
                "val_approach_wait_gap_s": val_sum["gap_grand"],
                "val_max_queue_m": val_sum["max_queue_grand"],
                "params": params,
            }
            val_records.append(val_rec)
            print(f"  Candidate {t_id}: Train Comp={cand['composite']:.4f} -> Val Comp={val_score:.4f} | Val Wait={val_sum['mean_wait_grand']:.1f}s | Val P95={val_sum['p95_wait_grand']:.1f}s")

        # Select winner: lowest val_composite (tie break: lower val_p95_wait_s)
        val_df = pd.DataFrame(val_records).sort_values(by=["val_composite", "val_p95_wait_s"])
        val_df.to_csv(TUNING_BASE_DIR / pol / "validation_candidates.csv", index=False)
        winner = val_df.iloc[0].to_dict()
        winners[pol] = winner
        print(f"  >>> WINNER for {pol}: {winner['trial_id']} (Val Composite={winner['val_composite']:.4f})")

        default_vs_tuned[pol] = {
            "default": {
                "composite": def_score,
                "mean_wait_s": def_sum["mean_wait_grand"],
                "p95_wait_s": def_sum["p95_wait_grand"],
                "approach_wait_gap_s": def_sum["gap_grand"],
                "max_queue_m": def_sum["max_queue_grand"],
            },
            "tuned": {
                "trial_id": winner["trial_id"],
                "composite": winner["val_composite"],
                "mean_wait_s": winner["val_mean_wait_s"],
                "p95_wait_s": winner["val_p95_wait_s"],
                "approach_wait_gap_s": winner["val_approach_wait_gap_s"],
                "max_queue_m": winner["val_max_queue_m"],
            },
            "delta_composite": round(winner["val_composite"] - def_score, 4),
            "delta_mean_wait_s": round(winner["val_mean_wait_s"] - def_sum["mean_wait_grand"], 2),
            "delta_p95_wait_s": round(winner["val_p95_wait_s"] - def_sum["p95_wait_grand"], 2),
            "delta_gap_s": round(winner["val_approach_wait_gap_s"] - def_sum["gap_grand"], 2),
        }

    # Step 4: Freeze Winning Configurations
    print(f"\n================================================================================")
    print(f"STEP 4: FREEZING WINNERS AS configs/final_<policy>.yaml")
    print(f"================================================================================")
    configs_dir = Path("configs")
    configs_dir.mkdir(parents=True, exist_ok=True)

    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    timestamp_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for pol, win in winners.items():
        cfg_path = configs_dir / f"final_{pol}.yaml"
        doc = {
            "policy": pol,
            "trial_id": win["trial_id"],
            "git_commit": git_sha,
            "frozen_at": timestamp_now,
            "train_composite": float(win["train_composite"]),
            "validation_composite": float(win["val_composite"]),
            "validation_metrics": {
                "mean_wait_s": float(win["val_mean_wait_s"]),
                "p95_wait_s": float(win["val_p95_wait_s"]),
                "approach_wait_gap_s": float(win["val_approach_wait_gap_s"]),
                "max_queue_m": float(win["val_max_queue_m"]),
            },
            "parameters": win["params"],
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(dump_yaml(doc) + "\n")
        print(f"  Frozen: {cfg_path}")

    # Step 5: Parameter Sensitivity Analysis for Hybrid
    print(f"\n================================================================================")
    print(f"STEP 5: HYBRID PARAMETER SENSITIVITY ANALYSIS")
    print(f"================================================================================")
    hyb_df = tuning_results["hybrid_queue_adaptive"]
    hyb_params = [
        "extend_step_s", "extend_threshold_m", "fairness_ratio", "gap_out_s",
        "min_competing_queue_m", "max_competing_wait_s", "r4_warmup_s",
        "demand_weight_active", "demand_weight_competing", "arrival_detection_threshold"
    ]
    corrs = []
    for p in hyb_params:
        r = float(hyb_df[p].corr(hyb_df["composite"]))
        corrs.append({"parameter": p, "correlation_with_composite": round(r, 3)})

    corr_df = pd.DataFrame(corrs).sort_values(by="correlation_with_composite", key=abs, ascending=False)
    corr_df.to_csv(TUNING_BASE_DIR / "hybrid_queue_adaptive" / "parameter_sensitivity.csv", index=False)
    print(corr_df.to_string(index=False))

    total_time_s = time.time() - t_start
    print(f"\nPhase 11 Search Completed in {total_time_s:.1f}s ({total_time_s/60.0:.1f} min).")

    # Save complete default vs tuned summary
    with open(TUNING_BASE_DIR / "default_vs_tuned_summary.json", "w", encoding="utf-8") as f:
        json.dump(default_vs_tuned, f, indent=2)

    return default_vs_tuned, corr_df


if __name__ == "__main__":
    main()
