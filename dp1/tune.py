"""Hyperparameter tuning for AdaptiveQueueController over training seeds.

Evaluates parameter combinations across all 4 demand scenarios on TRAIN seeds (1-5).
Selects the configuration minimizing mean waiting time, then evaluates both default
and best parameters on HELD-OUT seeds (11-15).
"""
from concurrent.futures import ProcessPoolExecutor
import csv
import itertools
from pathlib import Path
import random
import shutil
import time
import pandas as pd

from . import config as C
from .network import build_network
from .runner import run_simulation


def get_search_grid():
    """Generate all 180 parameter configurations from C.TUNE_SEARCH_SPACE."""
    grid = []
    space = C.TUNE_SEARCH_SPACE
    for cid, (k, max_g, min_g, gap) in enumerate(itertools.product(
        space["k_s_per_m"],
        space["max_green_s"],
        space["min_green_s"],
        space["gap_out_s"],
    )):
        grid.append({
            "config_id": cid,
            "k_s_per_m": float(k),
            "max_green_s": int(max_g),
            "min_green_s": int(min_g),
            "gap_out_s": int(gap),
        })
    return grid


def _tune_worker(job):
    """Worker function for ProcessPoolExecutor: run one simulation and return summary metrics."""
    cfg_id, scenario, seed, cfg_dict, scratch_dir_str = job
    out_dir = Path(scratch_dir_str) / f"c{cfg_id}_{scenario}_s{seed}"
    cfg = C.AdaptiveConfig(**cfg_dict)
    time.sleep(random.uniform(0.01, 0.25))
    try:
        m = run_simulation(scenario, "adaptive", seed, out_dir=out_dir, policy_kwargs={"cfg": cfg})
        return {
            "config_id": cfg_id,
            "scenario": scenario,
            "seed": seed,
            "avg_wait_s": float(m["avg_wait_s"]),
            "avg_queue_m": float(m["avg_queue_m"]),
            "completion_rate": float(m["completion_rate"]),
        }
    finally:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)


def load_existing_results(csv_path: Path):
    """Load already evaluated configs from results/tuning.csv if present."""
    if not csv_path.exists():
        return {}
    try:
        df = pd.read_csv(csv_path)
        if df.empty or "config_id" not in df.columns:
            return {}
        return {int(row["config_id"]): row.to_dict() for _, row in df.iterrows()}
    except Exception:
        return {}


def evaluate_configs_batch(configs, scenarios=None, seeds=C.TRAIN_SEEDS, jobs=8):
    """Evaluate a list of configuration dicts on the given scenarios and seeds using parallel workers."""
    scenarios = scenarios or list(C.scenarios().keys())
    scratch_base = C.RESULTS_DIR / "tune_scratch"
    scratch_base.mkdir(parents=True, exist_ok=True)

    job_list = []
    for cfg in configs:
        cid = cfg["config_id"]
        cfg_params = {k: v for k, v in cfg.items() if k != "config_id"}
        for scen in scenarios:
            for sd in seeds:
                job_list.append((cid, scen, sd, cfg_params, str(scratch_base)))

    print(f"  Dispatching {len(job_list)} simulation runs across {jobs} workers...")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(_tune_worker, job_list))
    elapsed = time.time() - t0
    print(f"  Finished {len(job_list)} runs in {elapsed:.1f}s ({len(job_list)/elapsed:.2f} runs/s).")

    # Clean up scratch base directory
    shutil.rmtree(scratch_base, ignore_errors=True)

    # Aggregate by config_id
    by_cfg = {}
    for r in results:
        cid = r["config_id"]
        by_cfg.setdefault(cid, []).append(r)

    rows = []
    for cfg in configs:
        cid = cfg["config_id"]
        c_results = by_cfg[cid]
        scen_waits = {}
        for scen in scenarios:
            s_waits = [r["avg_wait_s"] for r in c_results if r["scenario"] == scen]
            scen_waits[scen] = sum(s_waits) / len(s_waits)

        mean_wait = sum(scen_waits.values()) / len(scen_waits)
        mean_queue = sum(r["avg_queue_m"] for r in c_results) / len(c_results)
        comp_rate = sum(r["completion_rate"] for r in c_results) / len(c_results)

        row = {
            "config_id": cid,
            "k_s_per_m": cfg["k_s_per_m"],
            "max_green_s": cfg["max_green_s"],
            "min_green_s": cfg["min_green_s"],
            "gap_out_s": cfg["gap_out_s"],
            "mean_wait_s": round(mean_wait, 2),
            "balanced_wait_s": round(scen_waits.get("balanced", 0.0), 2),
            "imbalanced_ns_wait_s": round(scen_waits.get("imbalanced_ns", 0.0), 2),
            "imbalanced_ew_wait_s": round(scen_waits.get("imbalanced_ew", 0.0), 2),
            "surge_north_wait_s": round(scen_waits.get("surge_north", 0.0), 2),
            "mean_queue_m": round(mean_queue, 2),
            "completion_rate": round(comp_rate, 4),
        }
        rows.append(row)

    return rows


def save_tuning_results(evaluated_dict: dict, csv_path: Path):
    """Save all evaluated results to tuning.csv, sorted by mean_wait_s ascending."""
    df = pd.DataFrame(list(evaluated_dict.values()))
    rank_cols = [c for c in df.columns if c.startswith("rank")]
    if rank_cols:
        df = df.drop(columns=rank_cols)
    df = df.sort_values("mean_wait_s", ascending=True).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    df.to_csv(csv_path, index=False)
    return df


def evaluate_heldout_comparison(best_cfg_dict, default_cfg_dict, jobs=8):
    """Evaluate default vs best configuration on held-out seeds 11-15."""
    scenarios = list(C.scenarios().keys())
    held_seeds = C.HELD_OUT_SEEDS
    scratch_base = C.RESULTS_DIR / "tune_scratch"
    scratch_base.mkdir(parents=True, exist_ok=True)

    items = [
        ("default", default_cfg_dict),
        ("tuned_best", best_cfg_dict),
    ]

    job_list = []
    for label, cfg in items:
        cfg_params = {k: v for k, v in cfg.items() if k in {"k_s_per_m", "max_green_s", "min_green_s", "gap_out_s"}}
        for scen in scenarios:
            for sd in held_seeds:
                job_list.append((label, scen, sd, cfg_params, str(scratch_base)))

    print(f"\nEvaluating HELD-OUT seeds ({held_seeds}) for default vs best ({len(job_list)} runs)...")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(_tune_worker, job_list))
    elapsed = time.time() - t0
    print(f"Held-out evaluation finished in {elapsed:.1f}s.")
    shutil.rmtree(scratch_base, ignore_errors=True)

    df_runs = pd.DataFrame(results)
    # Aggregate by (label, scenario)
    summary = df_runs.groupby(["config_id", "scenario"])[["avg_wait_s", "avg_queue_m", "completion_rate"]].mean()
    return summary.unstack("config_id")


def write_tuning_markdown(tuning_df, heldout_summary, best_cfg, default_cfg, out_path: Path):
    """Generate results/tuning.md detailing search space, train results, and held-out evaluation."""
    def_wait = tuning_df[
        (tuning_df["k_s_per_m"] == default_cfg["k_s_per_m"]) &
        (tuning_df["max_green_s"] == default_cfg["max_green_s"]) &
        (tuning_df["min_green_s"] == default_cfg["min_green_s"]) &
        (tuning_df["gap_out_s"] == default_cfg["gap_out_s"])
    ]
    def_row = def_wait.iloc[0] if not def_wait.empty else None
    best_row = tuning_df.iloc[0]

    scenarios = list(C.scenarios().keys())
    lines = [
        "# Adaptive Controller Tuning Results",
        "",
        "## Search Space & Methodology",
        "- **Grid Search Size**: 180 combinations ($5 \\times 4 \\times 3 \\times 3$)",
        "  - `k_s_per_m`: {0.15, 0.20, 0.30, 0.40, 0.50}",
        "  - `max_green_s`: {30, 40, 45, 60}",
        "  - `min_green_s`: {8, 10, 12}",
        "  - `gap_out_s`: {2, 3, 5}",
        "- **Training Seeds**: 1, 2, 3, 4, 5 (used for hyperparameter optimisation)",
        "- **Held-Out Seeds**: 11, 12, 13, 14, 15 (evaluated strictly post-tuning)",
        "- **Objective**: Minimize mean waiting time across all 4 scenarios on training seeds.",
        "",
        "## Selected Parameters: Default vs Tuned Best",
        "| Parameter | Default Value | Tuned Best Value |",
        "|---|---|---|",
        f"| `k_s_per_m` | `{default_cfg['k_s_per_m']}` | **`{best_cfg['k_s_per_m']}`** |",
        f"| `max_green_s` | `{default_cfg['max_green_s']}` | **`{best_cfg['max_green_s']}`** |",
        f"| `min_green_s` | `{default_cfg['min_green_s']}` | **`{best_cfg['min_green_s']}`** |",
        f"| `gap_out_s` | `{default_cfg['gap_out_s']}` | **`{best_cfg['gap_out_s']}`** |",
        "",
        "## 1. Training Seeds (1–5) Performance",
        "| Scenario | Default Wait (s) | Tuned Best Wait (s) | Improvement (%) |",
        "|---|---|---|---|",
    ]

    for s in scenarios:
        d_val = def_row[f"{s}_wait_s"] if def_row is not None else float("nan")
        b_val = best_row[f"{s}_wait_s"]
        chg = ((d_val - b_val) / d_val * 100) if d_val > 0 else 0.0
        lines.append(f"| `{s}` | {d_val:.2f} | {b_val:.2f} | {chg:+.1f}% |")

    d_mean = def_row["mean_wait_s"] if def_row is not None else float("nan")
    b_mean = best_row["mean_wait_s"]
    chg_mean = ((d_mean - b_mean) / d_mean * 100) if d_mean > 0 else 0.0
    lines.append(f"| **Overall Mean** | **{d_mean:.2f}** | **{b_mean:.2f}** | **{chg_mean:+.1f}%** |")
    lines.append("")

    lines.extend([
        "## 2. Held-Out Seeds (11–15) Evaluation (Generalisation Test)",
        "> *Note: Seeds 11–15 were never seen during grid selection. This confirms whether gains transfer to unseen traffic arrivals.*",
        "",
        "| Scenario | Default Wait (s) | Tuned Best Wait (s) | Wait Change (%) | Default Queue (m) | Tuned Queue (m) |",
        "|---|---|---|---|---|---|",
    ])

    held_def_waits, held_best_waits = [], []
    for s in scenarios:
        dw = heldout_summary.loc[s, ("avg_wait_s", "default")]
        bw = heldout_summary.loc[s, ("avg_wait_s", "tuned_best")]
        dq = heldout_summary.loc[s, ("avg_queue_m", "default")]
        bq = heldout_summary.loc[s, ("avg_queue_m", "tuned_best")]
        chg = ((dw - bw) / dw * 100) if dw > 0 else 0.0
        held_def_waits.append(dw)
        held_best_waits.append(bw)
        lines.append(f"| `{s}` | {dw:.2f} | {bw:.2f} | {chg:+.1f}% | {dq:.2f} | {bq:.2f} |")

    h_d_mean = sum(held_def_waits) / len(held_def_waits)
    h_b_mean = sum(held_best_waits) / len(held_best_waits)
    h_chg = ((h_d_mean - h_b_mean) / h_d_mean * 100) if h_d_mean > 0 else 0.0
    lines.append(f"| **Overall Mean** | **{h_d_mean:.2f}** | **{h_b_mean:.2f}** | **{h_chg:+.1f}%** | - | - |")
    lines.append("")

    lines.extend([
        "## 3. Top 5 Configurations on Training Seeds",
        "| Rank | k_s_per_m | max_green_s | min_green_s | gap_out_s | Mean Wait (s) | Balanced | Imbal NS | Imbal EW | Surge North |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])

    for i in range(min(5, len(tuning_df))):
        r = tuning_df.iloc[i]
        lines.append(
            f"| {i+1} | {r['k_s_per_m']} | {int(r['max_green_s'])} | {int(r['min_green_s'])} | "
            f"{int(r['gap_out_s'])} | {r['mean_wait_s']:.2f} | {r['balanced_wait_s']:.2f} | "
            f"{r['imbalanced_ns_wait_s']:.2f} | {r['imbalanced_ew_wait_s']:.2f} | {r['surge_north_wait_s']:.2f} |"
        )
    lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote tuning report to {out_path}")


def run_tune(jobs=8, chunk_size=20, eval_heldout_flag=False):
    """Main entrypoint for tuning search and evaluation."""
    build_network()
    csv_path = C.RESULTS_DIR / "tuning.csv"
    md_path = C.RESULTS_DIR / "tuning.md"
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    grid = get_search_grid()
    existing = load_existing_results(csv_path)

    default_cfg = {
        "k_s_per_m": C.ADAPTIVE.k_s_per_m,
        "max_green_s": C.ADAPTIVE.max_green_s,
        "min_green_s": C.ADAPTIVE.min_green_s,
        "gap_out_s": C.ADAPTIVE.gap_out_s,
    }

    # Find remaining configs
    remaining = [cfg for cfg in grid if cfg["config_id"] not in existing]
    print(f"Tuning Search Space: {len(grid)} total configs | {len(existing)} already evaluated | {len(remaining)} remaining.")

    if remaining and not eval_heldout_flag:
        batch = remaining if (chunk_size <= 0 or chunk_size >= len(remaining)) else remaining[:chunk_size]
        print(f"\n--- Running chunk of {len(batch)} configurations ({len(batch)*20} runs) on {jobs} workers ---")
        new_rows = evaluate_configs_batch(batch, jobs=jobs)
        for r in new_rows:
            existing[r["config_id"]] = r
        tuning_df = save_tuning_results(existing, csv_path)
        print(f"Updated {csv_path} (now {len(existing)}/{len(grid)} completed).")
        best = tuning_df.iloc[0]
        print(f"Current best so far: k={best['k_s_per_m']}, max_g={int(best['max_green_s'])}, "
              f"min_g={int(best['min_green_s'])}, gap={int(best['gap_out_s'])} -> mean_wait = {best['mean_wait_s']:.2f}s")

    # If all configs are evaluated (or eval_heldout_flag requested), run held-out evaluation
    tuning_df = save_tuning_results(existing, csv_path) if existing else None
    if tuning_df is not None and (len(existing) == len(grid) or eval_heldout_flag):
        best_cfg = {
            "k_s_per_m": float(tuning_df.iloc[0]["k_s_per_m"]),
            "max_green_s": int(tuning_df.iloc[0]["max_green_s"]),
            "min_green_s": int(tuning_df.iloc[0]["min_green_s"]),
            "gap_out_s": int(tuning_df.iloc[0]["gap_out_s"]),
        }
        print(f"\nAll configurations evaluated (or held-out evaluation requested).")
        print(f"Best configuration on TRAIN seeds 1-5: {best_cfg} (wait: {tuning_df.iloc[0]['mean_wait_s']:.2f}s)")
        print(f"Default configuration: {default_cfg}")

        heldout_summary = evaluate_heldout_comparison(best_cfg, default_cfg, jobs=jobs)
        write_tuning_markdown(tuning_df, heldout_summary, best_cfg, default_cfg, md_path)

        # Print train vs held-out comparison directly
        print("\n" + "=" * 65)
        print("TUNING SUMMARY: TRAIN (seeds 1-5) vs HELD-OUT (seeds 11-15)")
        print("=" * 65)
        print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="tune")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--eval-heldout", action="store_true")
    args = ap.parse_args()
    run_tune(jobs=args.jobs, chunk_size=args.chunk_size, eval_heldout_flag=args.eval_heldout)
