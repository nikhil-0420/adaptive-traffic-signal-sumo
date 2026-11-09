"""Item 5: Parameter Sensitivity Analysis (Exploratory, Seeds 101-110).

Evaluates one-at-a-time variations from v1 defaults:
- step_2s, step_4s: extension step 2.0s, 4.0s (default 3.0s)
- thresh_3m, thresh_6m: extension threshold 3.0m, 6.0m (default 4.0m)
- wait_30s, wait_45s: red-wait limit 30s, 45s (default 35s)
- comp_q_1m, comp_q_4m: competing-queue threshold 1.0m, 4.0m (default 2.0m)
- default_v1: v1 baseline reference
vs fresh webster_measured on the same seeds 101-110.

Computes:
- Delta% and seed-clustered 95% CIs for extended max queue, p95 wait, wait gap.
- Maximum observed red interval across simulations vs analytic bound (W_limit + step + 10s).
- Assessment of whether max-queue reduction stays negative and statistically significant.
- Identification of most sensitive parameter.

Produces:
- Summary table: table_xai_parameter_sensitivity.csv
- Figures: fig_xai_parameter_sensitivity_single.png (3.5 in), fig_xai_parameter_sensitivity_double.png (7.1 in) at 300 dpi
- Numbers logged to numbers_xai.json
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SENSITIVITY_DIR = ROOT_DIR / "results" / "research" / "exp_xai_exploratory" / "sensitivity"
ABLATION_DIR = ROOT_DIR / "results" / "research" / "exp_xai_exploratory" / "ablation"
OUT_DIR = Path(__file__).resolve().parent
NUMBERS_JSON = OUT_DIR / "numbers_xai.json"

SEEDS = list(range(101, 111))
CONDITIONS = [
    "balanced-low",
    "balanced-heavy",
    "imbalanced_orr-heavy",
    "ramp_peak-medium",
    "surge_shift-medium",
    "lane_closure-medium",
]

VARIANTS = [
    "default_v1",
    "step_2s",
    "step_4s",
    "thresh_3m",
    "thresh_6m",
    "wait_30s",
    "wait_45s",
    "comp_q_1m",
    "comp_q_4m",
]

VARIANT_SPECS = {
    "default_v1": {"param": "default", "val": "v1 (3.0s, 4.0m, 35s, 2.0m)", "W_limit": 35.0, "step": 3.0},
    "step_2s": {"param": "extension_step", "val": "2.0 s (vs 3.0s)", "W_limit": 35.0, "step": 2.0},
    "step_4s": {"param": "extension_step", "val": "4.0 s (vs 3.0s)", "W_limit": 35.0, "step": 4.0},
    "thresh_3m": {"param": "extension_threshold", "val": "3.0 m (vs 4.0m)", "W_limit": 35.0, "step": 3.0},
    "thresh_6m": {"param": "extension_threshold", "val": "6.0 m (vs 4.0m)", "W_limit": 35.0, "step": 3.0},
    "wait_30s": {"param": "red_wait_limit", "val": "30 s (vs 35s)", "W_limit": 30.0, "step": 3.0},
    "wait_45s": {"param": "red_wait_limit", "val": "45 s (vs 35s)", "W_limit": 45.0, "step": 3.0},
    "comp_q_1m": {"param": "competing_threshold", "val": "1.0 m (vs 2.0m)", "W_limit": 35.0, "step": 3.0},
    "comp_q_4m": {"param": "competing_threshold", "val": "4.0 m (vs 2.0m)", "W_limit": 35.0, "step": 3.0},
}

PRIMARY_METRICS = ["gt_ext_max_queue_m", "p95_wait_s", "approach_wait_gap_s"]
METRIC_LABELS = {
    "gt_ext_max_queue_m": "Extended Max Queue (m)",
    "p95_wait_s": "p95 Wait Time (s)",
    "approach_wait_gap_s": "Approach Wait Gap (s)",
}


def compute_max_observed_red_interval(run_dir: Path) -> float:
    """Compute maximum observed red interval for either axis from timeseries.csv."""
    ts_file = run_dir / "timeseries.csv"
    if not ts_file.exists():
        return 0.0
    try:
        df = pd.read_csv(ts_file)
        if "axis" not in df or "t" not in df:
            return 0.0
        # Red on NS is when axis == 'EW' (or non-green)
        max_red = 0.0
        for target_axis in ["NS", "EW"]:
            is_red = (df["axis"] != target_axis)
            # Find continuous blocks of True
            blocks = (~is_red).cumsum()[is_red]
            if not blocks.empty:
                lengths = blocks.value_counts()
                # Assuming 1s steps in SUMO simulation
                if not lengths.empty:
                    max_red = max(max_red, float(lengths.max()))
        return max_red
    except Exception:
        return 0.0


def load_sensitivity_data():
    records = []

    # 1. Load webster_measured from sensitivity directory
    for run_dir in SENSITIVITY_DIR.glob("marathahalli_*_webster_measured_s*"):
        m_file = run_dir / "metrics.json"
        if not m_file.exists():
            continue
        try:
            m = json.loads(m_file.read_text(encoding="utf-8"))
            seed = int(m.get("seed"))
            if not (101 <= seed <= 110):
                continue
            scen = m.get("scenario")
            dem = m.get("demand_level")
            cond = f"{scen}-{dem}"
            records.append({
                "run_id": run_dir.name,
                "variant": "webster_measured",
                "condition": cond,
                "seed": seed,
                "gt_ext_max_queue_m": float(m.get("gt_ext_max_queue_m", m.get("max_queue_m"))),
                "p95_wait_s": float(m.get("p95_wait_s")),
                "approach_wait_gap_s": float(m.get("approach_wait_gap_s")),
                "run_dir": run_dir,
            })
        except Exception:
            pass

    # 2. Load 8 sensitivity variants
    for run_dir in SENSITIVITY_DIR.glob("marathahalli_*_s*"):
        if "webster_measured" in run_dir.name:
            continue
        m_file = run_dir / "metrics.json"
        if not m_file.exists():
            continue
        try:
            m = json.loads(m_file.read_text(encoding="utf-8"))
            seed = int(m.get("seed"))
            if not (101 <= seed <= 110):
                continue
            scen = m.get("scenario")
            dem = m.get("demand_level")
            cond = f"{scen}-{dem}"
            # Extract variant name
            prefix = run_dir.name.rsplit("_s", 1)[0]
            variant = None
            for v in VARIANTS:
                if prefix.endswith(f"_{v}"):
                    variant = v
                    break
            if variant is None:
                continue

            records.append({
                "run_id": run_dir.name,
                "variant": variant,
                "condition": cond,
                "seed": seed,
                "gt_ext_max_queue_m": float(m.get("gt_ext_max_queue_m", m.get("max_queue_m"))),
                "p95_wait_s": float(m.get("p95_wait_s")),
                "approach_wait_gap_s": float(m.get("approach_wait_gap_s")),
                "run_dir": run_dir,
            })
        except Exception:
            pass

    # 3. Load default_v1 from ablation directory (all_on variant)
    for run_dir in ABLATION_DIR.glob("marathahalli_*_all_on_s*"):
        m_file = run_dir / "metrics.json"
        if not m_file.exists():
            continue
        try:
            m = json.loads(m_file.read_text(encoding="utf-8"))
            seed = int(m.get("seed"))
            if not (101 <= seed <= 110):
                continue
            scen = m.get("scenario")
            dem = m.get("demand_level")
            cond = f"{scen}-{dem}"
            records.append({
                "run_id": run_dir.name,
                "variant": "default_v1",
                "condition": cond,
                "seed": seed,
                "gt_ext_max_queue_m": float(m.get("gt_ext_max_queue_m", m.get("max_queue_m"))),
                "p95_wait_s": float(m.get("p95_wait_s")),
                "approach_wait_gap_s": float(m.get("approach_wait_gap_s")),
                "run_dir": run_dir,
            })
        except Exception:
            pass

    return pd.DataFrame(records)


def compute_parameter_sensitivity():
    df = load_sensitivity_data()
    print(f"[Item 5] Loaded {len(df)} sensitivity simulation records.")

    wm_df = df[df["variant"] == "webster_measured"]
    print(f"Loaded {len(wm_df)} webster_measured baseline runs.")

    n_boot = 10000
    rng = np.random.default_rng(42)
    unique_seeds = np.array(sorted(df["seed"].unique()))
    n_seeds = len(unique_seeds)
    boot_indices = rng.integers(0, n_seeds, size=(n_boot, n_seeds))

    summary_rows = []

    for v in VARIANTS:
        v_df = df[df["variant"] == v]
        if v_df.empty:
            print(f"Warning: No runs found for variant {v}")
            continue

        merged = pd.merge(v_df, wm_df, on=["condition", "seed"], suffixes=("_var", "_wm"))

        # Compute max observed red interval
        observed_max_red = 0.0
        for r_dir in v_df["run_dir"]:
            red_val = compute_max_observed_red_interval(r_dir)
            observed_max_red = max(observed_max_red, red_val)

        # Analytic estimate: W_limit + step + 10s
        spec = VARIANT_SPECS[v]
        analytic_bound = spec["W_limit"] + spec["step"] + 10.0

        v_metrics = {}
        for m in PRIMARY_METRICS:
            vh = merged[f"{m}_var"].to_numpy(dtype=float)
            vr = merged[f"{m}_wm"].to_numpy(dtype=float)

            seed_deltas = []
            for s in unique_seeds:
                s_rows = merged[merged["seed"] == s]
                s_vh = s_rows[f"{m}_var"].to_numpy(dtype=float)
                s_vr = s_rows[f"{m}_wm"].to_numpy(dtype=float)
                with np.errstate(divide="ignore", invalid="ignore"):
                    d_pct = np.where(s_vr != 0, ((s_vh - s_vr) / s_vr) * 100.0, 0.0)
                seed_deltas.append(np.mean(d_pct))

            s_arr = np.array(seed_deltas)
            delta_pct = float(np.mean(s_arr))
            boot_means = np.mean(s_arr[boot_indices], axis=1)
            ci_low = float(np.percentile(boot_means, 2.5))
            ci_high = float(np.percentile(boot_means, 97.5))

            if delta_pct >= 0:
                raw_p = 2.0 * float(np.mean(boot_means <= 0))
            else:
                raw_p = 2.0 * float(np.mean(boot_means >= 0))
            raw_p = min(1.0, max(0.0, raw_p))

            v_metrics[m] = {
                "delta_pct": delta_pct,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "raw_p": raw_p,
                "sig": raw_p < 0.05,
            }

        # Step-down Holm across 3 metrics
        p_tuples = [(m, v_metrics[m]["raw_p"]) for m in PRIMARY_METRICS]
        p_tuples.sort(key=lambda x: x[1])
        m_tests = len(PRIMARY_METRICS)
        running_max = 0.0
        for rank, (m, p) in enumerate(p_tuples):
            adj_p = min(1.0, p * (m_tests - rank))
            adj_p = max(adj_p, running_max)
            running_max = adj_p
            v_metrics[m]["holm_p"] = adj_p
            v_metrics[m]["sig_holm"] = adj_p < 0.05

        summary_rows.append({
            "variant": v,
            "parameter": spec["param"],
            "value_description": spec["val"],
            "max_queue_delta_pct": round(v_metrics["gt_ext_max_queue_m"]["delta_pct"], 2),
            "max_queue_ci_low": round(v_metrics["gt_ext_max_queue_m"]["ci_low"], 2),
            "max_queue_ci_high": round(v_metrics["gt_ext_max_queue_m"]["ci_high"], 2),
            "max_queue_holm_p": round(v_metrics["gt_ext_max_queue_m"]["holm_p"], 4),
            "max_queue_sig": v_metrics["gt_ext_max_queue_m"]["sig_holm"],
            "p95_wait_delta_pct": round(v_metrics["p95_wait_s"]["delta_pct"], 2),
            "p95_wait_ci_low": round(v_metrics["p95_wait_s"]["ci_low"], 2),
            "p95_wait_ci_high": round(v_metrics["p95_wait_s"]["ci_high"], 2),
            "wait_gap_delta_pct": round(v_metrics["approach_wait_gap_s"]["delta_pct"], 2),
            "wait_gap_ci_low": round(v_metrics["approach_wait_gap_s"]["ci_low"], 2),
            "wait_gap_ci_high": round(v_metrics["approach_wait_gap_s"]["ci_high"], 2),
            "observed_max_red_s": round(observed_max_red, 1),
            "analytic_red_bound_s": round(analytic_bound, 1),
            "label": "exploratory; development/validation seeds 101-110",
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(OUT_DIR / "table_xai_parameter_sensitivity.csv", index=False)

    # Check sensitivity range
    # Variation in max_queue_delta_pct across variants
    mq_deltas = {r["variant"]: r["max_queue_delta_pct"] for r in summary_rows}
    all_sig = all(r["max_queue_sig"] and r["max_queue_delta_pct"] < 0 for r in summary_rows)

    # Calculate parameter impact ranges
    param_ranges = {
        "extension_step": abs(mq_deltas.get("step_4s", 0) - mq_deltas.get("step_2s", 0)),
        "extension_threshold": abs(mq_deltas.get("thresh_6m", 0) - mq_deltas.get("thresh_3m", 0)),
        "red_wait_limit": abs(mq_deltas.get("wait_45s", 0) - mq_deltas.get("wait_30s", 0)),
        "competing_threshold": abs(mq_deltas.get("comp_q_4m", 0) - mq_deltas.get("comp_q_1m", 0)),
    }
    most_sensitive_param = max(param_ranges.items(), key=lambda x: x[1])[0]

    # --- 3. Compact Dot-Plot Figure of Max-Queue Delta% by Variant ---
    variant_display_labels = [
        "v1 Default Reference",
        "Step: 2.0 s",
        "Step: 4.0 s",
        "Ext Thresh: 3.0 m",
        "Ext Thresh: 6.0 m",
        "Wait Cap: 30 s",
        "Wait Cap: 45 s",
        "Comp Thresh: 1.0 m",
        "Comp Thresh: 4.0 m",
    ]

    for fig_type, width in [("single", 3.5), ("double", 7.1)]:
        fig, ax = plt.subplots(figsize=(width, 3.2 if width == 3.5 else 3.6), dpi=300)

        y = np.arange(len(summary_rows))
        deltas = [r["max_queue_delta_pct"] for r in summary_rows]
        err_low = [deltas[i] - r["max_queue_ci_low"] for i, r in enumerate(summary_rows)]
        err_high = [r["max_queue_ci_high"] - deltas[i] for i, r in enumerate(summary_rows)]

        ax.errorbar(
            deltas, y, xerr=[err_low, err_high], fmt="o", color="#2b5c8f",
            ecolor="#2b5c8f", capsize=2.5, markersize=4.5 if width == 3.5 else 5.5, elinewidth=1.0
        )
        ax.axvline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)
        # Highlight default v1 reference
        if len(summary_rows) > 0:
            ax.axvline(summary_rows[0]["max_queue_delta_pct"], color="red", linestyle=":", linewidth=0.8, label="v1 Default Delta%")

        ax.set_yticks(y)
        ax.set_yticklabels(variant_display_labels[:len(summary_rows)], fontsize=6.5 if width == 3.5 else 7.5)
        ax.invert_yaxis()  # top down
        ax.set_xlabel("Extended Max Queue $\\Delta\\%$ vs Webster-m [Seed-Clustered 95% CI]", fontsize=7 if width == 3.5 else 8, fontweight="bold")
        ax.set_title("Parameter Sensitivity on Extended Max Queue (Seeds 101–110, Exploratory)", fontsize=7.5 if width == 3.5 else 9, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.tick_params(axis="both", which="major", labelsize=6.5 if width == 3.5 else 7.5)
        ax.legend(fontsize=6 if width == 3.5 else 7, loc="lower right", framealpha=0.9)

        plt.tight_layout()
        fig.savefig(OUT_DIR / f"fig_xai_parameter_sensitivity_{fig_type}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    # --- 4. Save Numbers ---
    numbers = {}
    if NUMBERS_JSON.exists():
        try:
            numbers = json.loads(NUMBERS_JSON.read_text(encoding="utf-8"))
        except Exception:
            numbers = {}

    numbers["item_5_parameter_sensitivity"] = {
        "script": "analysis/xai/parameter_sensitivity.py",
        "function": "compute_parameter_sensitivity",
        "label": "exploratory; development/validation seeds 101-110",
        "summary": summary_rows,
        "max_queue_reduction_all_negative_and_sig": all_sig,
        "parameter_impact_ranges": param_ranges,
        "most_sensitive_parameter": most_sensitive_param,
    }

    NUMBERS_JSON.write_text(json.dumps(numbers, indent=2), encoding="utf-8")
    print("Item 5 Parameter Sensitivity completed successfully.")


if __name__ == "__main__":
    compute_parameter_sensitivity()
