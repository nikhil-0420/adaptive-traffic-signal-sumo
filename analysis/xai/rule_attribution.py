"""Item 4: Rule Attribution via Shapley Decomposition (Exploratory, Seeds 101-110).

Evaluates the 8 subsets of {R-base, R-ext, R-guard}:
- all_off: R-base=0, R-ext=0, R-guard=0 (Fixed 15s green, no extensions, no wait cap)
- base_only: R-base=1, R-ext=0, R-guard=0
- ext_only: R-base=0, R-ext=1, R-guard=0
- guard_only: R-base=0, R-ext=0, R-guard=1
- base_ext: R-base=1, R-ext=1, R-guard=0
- base_guard: R-base=1, R-ext=0, R-guard=1
- ext_guard: R-base=0, R-ext=1, R-guard=1
- all_on: R-base=1, R-ext=1, R-guard=1 (v1 baseline)

Produces:
- 8-row summary table: table_xai_ablation_8variants.csv
- Shapley attribution table with seed-clustered CIs: table_xai_shapley_attribution.csv
- Figures: fig_xai_shapley_single.png (3.5 in), fig_xai_shapley_double.png (7.1 in) at 300 dpi
- Numbers logged to numbers_xai.json
"""
import itertools
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
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

SUBSETS_8 = [
    "all_off",
    "base_only",
    "ext_only",
    "guard_only",
    "base_ext",
    "base_guard",
    "ext_guard",
    "all_on",
]

RULES = ["R_base", "R_ext", "R_guard"]
RULE_LABELS = {
    "R_base": "R-base (Webster Allocation)",
    "R_ext": "R-ext (+3s Extension)",
    "R_guard": "R-guard (35s Red-Wait Limit)",
}

PRIMARY_METRICS = ["gt_ext_max_queue_m", "p95_wait_s", "approach_wait_gap_s"]
METRIC_LABELS = {
    "gt_ext_max_queue_m": "Extended Max Queue (m)",
    "p95_wait_s": "p95 Wait Time (s)",
    "approach_wait_gap_s": "Approach Wait Gap (s)",
}


def load_ablation_data():
    """Load extracted metrics from all ablation runs."""
    records = []
    for run_dir in ABLATION_DIR.glob("marathahalli_*_s*"):
        if not run_dir.is_dir():
            continue
        m_file = run_dir / "metrics.json"
        if not m_file.exists():
            continue
        try:
            m = json.loads(m_file.read_text(encoding="utf-8"))
            d_name = run_dir.name
            # parse format: marathahalli_{scenario}_{demand}_{variant}_s{seed}
            parts = d_name.rsplit("_s", 1)
            seed = int(parts[1])
            if not (101 <= seed <= 110):
                continue
            prefix = parts[0]
            # determine variant and condition
            variant = None
            for v in SUBSETS_8:
                if prefix.endswith(f"_{v}"):
                    variant = v
                    cond_part = prefix[len("marathahalli_"):-len(f"_{v}")]
                    break
            if variant is None:
                continue

            # cond_part is e.g. balanced_heavy -> balanced-heavy
            # or lane_closure_medium -> lane_closure-medium
            scen = m.get("scenario")
            dem = m.get("demand_level")
            cond = f"{scen}-{dem}"

            records.append({
                "run_id": d_name,
                "variant": variant,
                "scenario": scen,
                "demand_level": dem,
                "condition": cond,
                "seed": seed,
                "gt_ext_max_queue_m": float(m.get("gt_ext_max_queue_m", m.get("max_queue_m"))),
                "p95_wait_s": float(m.get("p95_wait_s")),
                "approach_wait_gap_s": float(m.get("approach_wait_gap_s")),
                "gt_ext_avg_queue_m": float(m.get("gt_ext_avg_queue_m", m.get("avg_queue_m"))),
                "mean_wait_s": float(m.get("avg_wait_s", m.get("mean_wait_s", 0.0))),
            })
        except Exception:
            pass

    return pd.DataFrame(records)


def compute_shapley_values_for_sample(means_dict: dict, metrics: list) -> dict:
    """Compute Shapley values for 3 rules given mean metric values for each of 8 subsets.
    
    means_dict: {subset_name: {metric: float}}
    """
    # Mapping subset name to rule set
    subset_to_rules = {
        "all_off": set(),
        "base_only": {"R_base"},
        "ext_only": {"R_ext"},
        "guard_only": {"R_guard"},
        "base_ext": {"R_base", "R_ext"},
        "base_guard": {"R_base", "R_guard"},
        "ext_guard": {"R_ext", "R_guard"},
        "all_on": {"R_base", "R_ext", "R_guard"},
    }
    rules_to_subset = {frozenset(v): k for k, v in subset_to_rules.items()}

    shapley = {m: {r: 0.0 for r in RULES} for m in metrics}

    # Iterate over all 3! = 6 permutations of the 3 rules
    perms = list(itertools.permutations(RULES))
    n_perms = len(perms)

    for p in perms:
        current_set = set()
        for rule in p:
            next_set = current_set | {rule}
            sub_curr = rules_to_subset[frozenset(current_set)]
            sub_next = rules_to_subset[frozenset(next_set)]
            for m in metrics:
                val_curr = means_dict[sub_curr][m]
                val_next = means_dict[sub_next][m]
                marginal = val_next - val_curr
                shapley[m][rule] += marginal / n_perms
            current_set = next_set

    return shapley


def compute_rule_attribution():
    df = load_ablation_data()
    print(f"[Item 4] Loaded {len(df)} ablation simulation records.")

    # Check cell completeness
    cell_counts = df.groupby(["variant", "condition"])["seed"].count().unstack(fill_value=0)
    print("Cell counts (Variant x Condition):")
    print(cell_counts)

    # --- 1. 8-Variant Mean Summary Table ---
    pooled_means = df.groupby("variant")[PRIMARY_METRICS + ["gt_ext_avg_queue_m", "mean_wait_s"]].mean().reindex(SUBSETS_8)
    pooled_means.to_csv(OUT_DIR / "table_xai_ablation_8variants.csv")

    # Full means dict for sample
    sample_means_dict = {}
    for v in SUBSETS_8:
        v_df = df[df["variant"] == v]
        sample_means_dict[v] = {m: float(v_df[m].mean()) for m in PRIMARY_METRICS}

    sample_shapley = compute_shapley_values_for_sample(sample_means_dict, PRIMARY_METRICS)

    # --- 2. Seed-Clustered Bootstrap for Shapley Values ---
    n_boot = 10000
    rng = np.random.default_rng(42)
    unique_seeds = np.array(sorted(df["seed"].unique()))
    n_seeds = len(unique_seeds)
    boot_indices = rng.integers(0, n_seeds, size=(n_boot, n_seeds))

    # Pre-compute cluster means per seed and variant to accelerate bootstrap
    seed_variant_means = {}
    for s_idx, s in enumerate(unique_seeds):
        s_df = df[df["seed"] == s]
        seed_variant_means[s_idx] = {}
        for v in SUBSETS_8:
            v_df = s_df[s_df["variant"] == v]
            seed_variant_means[s_idx][v] = {m: float(v_df[m].mean()) for m in PRIMARY_METRICS}

    # Bootstrap distributions
    boot_shapley = {m: {r: [] for r in RULES} for m in PRIMARY_METRICS}
    for b in range(n_boot):
        b_idx = boot_indices[b]
        b_means_dict = {
            v: {m: sum(seed_variant_means[s_i][v][m] for s_i in b_idx) / n_seeds for m in PRIMARY_METRICS}
            for v in SUBSETS_8
        }
        b_shap = compute_shapley_values_for_sample(b_means_dict, PRIMARY_METRICS)
        for m in PRIMARY_METRICS:
            for r in RULES:
                boot_shapley[m][r].append(b_shap[m][r])

    shapley_rows = []
    for m in PRIMARY_METRICS:
        total_delta = sample_means_dict["all_on"][m] - sample_means_dict["all_off"][m]
        pct_base = (total_delta / sample_means_dict["all_off"][m]) * 100.0 if sample_means_dict["all_off"][m] != 0 else 0.0

        for r in RULES:
            val = sample_shapley[m][r]
            b_arr = np.array(boot_shapley[m][r])
            ci_low = float(np.percentile(b_arr, 2.5))
            ci_high = float(np.percentile(b_arr, 97.5))
            # Share of total change explained
            share_pct = (val / total_delta) * 100.0 if total_delta != 0 else 0.0

            shapley_rows.append({
                "metric": m,
                "metric_label": METRIC_LABELS[m],
                "rule": r,
                "rule_label": RULE_LABELS[r],
                "shapley_value": round(val, 3),
                "ci_low": round(ci_low, 3),
                "ci_high": round(ci_high, 3),
                "share_of_total_pct": round(share_pct, 1),
                "total_delta_all_on_vs_all_off": round(total_delta, 3),
                "label": "exploratory; development/validation seeds 101-110; not part of the pre-registered confirmatory study"
            })

    df_shapley = pd.DataFrame(shapley_rows)
    df_shapley.to_csv(OUT_DIR / "table_xai_shapley_attribution.csv", index=False)

    # --- 3. Interaction Terms (ANOVA Decomposition) ---
    # Total effect = I_A + I_B + I_C + I_AB + I_AC + I_BC + I_ABC
    interactions = {}
    for m in PRIMARY_METRICS:
        y0 = sample_means_dict["all_off"][m]
        yA = sample_means_dict["base_only"][m]
        yB = sample_means_dict["ext_only"][m]
        yC = sample_means_dict["guard_only"][m]
        yAB = sample_means_dict["base_ext"][m]
        yAC = sample_means_dict["base_guard"][m]
        yBC = sample_means_dict["ext_guard"][m]
        yABC = sample_means_dict["all_on"][m]

        IA = yA - y0
        IB = yB - y0
        IC = yC - y0
        IAB = yAB - yA - yB + y0
        IAC = yAC - yA - yC + y0
        IBC = yBC - yB - yC + y0
        IABC = yABC - (yAB + yAC + yBC) + (yA + yB + yC) - y0

        interactions[m] = {
            "main_R_base": round(IA, 3),
            "main_R_ext": round(IB, 3),
            "main_R_guard": round(IC, 3),
            "interaction_base_ext": round(IAB, 3),
            "interaction_base_guard": round(IAC, 3),
            "interaction_ext_guard": round(IBC, 3),
            "interaction_base_ext_guard": round(IABC, 3),
            "total_change": round(yABC - y0, 3),
        }

    # --- 4. Shapley Bar Figures (IEEE Single & Double Column) ---
    metrics_plot = ["gt_ext_max_queue_m", "p95_wait_s", "approach_wait_gap_s"]
    metric_titles = ["Extended Max Queue (m)", "p95 Wait Time (s)", "Wait Gap (s)"]
    rule_colors = ["#2b5c8f", "#d95f02", "#7570b3"]

    for fig_type, width in [("single", 3.5), ("double", 7.1)]:
        fig, axes = plt.subplots(
            1, 3, figsize=(width, 2.8 if width == 3.5 else 3.2), dpi=300, sharey=False
        )
        for idx, m in enumerate(metrics_plot):
            ax = axes[idx]
            vals = [sample_shapley[m][r] for r in RULES]
            errs_low = [vals[i] - float(np.percentile(boot_shapley[m][RULES[i]], 2.5)) for i in range(3)]
            errs_high = [float(np.percentile(boot_shapley[m][RULES[i]], 97.5)) - vals[i] for i in range(3)]

            x = np.arange(3)
            bars = ax.bar(x, vals, yerr=[errs_low, errs_high], capsize=2.5, color=rule_colors, width=0.55, edgecolor="black", linewidth=0.5)
            ax.axhline(0, color="black", linestyle="--", linewidth=0.7)
            ax.set_xticks(x)
            ax.set_xticklabels(["R-base", "R-ext", "R-guard"], fontsize=6.5 if width == 3.5 else 8)
            ax.set_title(metric_titles[idx], fontsize=7 if width == 3.5 else 8.5, fontweight="bold")
            ax.grid(axis="y", linestyle=":", alpha=0.5)
            ax.tick_params(axis="both", which="major", labelsize=6.5 if width == 3.5 else 7.5)

            if idx == 0:
                ax.set_ylabel("Shapley Value $\\phi_i$ (vs all-off)", fontsize=7 if width == 3.5 else 8, fontweight="bold")

        fig.suptitle(
            "Shapley Rule Attribution Decomposition (Seeds 101–110, Exploratory)",
            fontsize=7.5 if width == 3.5 else 9.5, fontweight="bold", y=1.02
        )
        plt.tight_layout()
        fig.savefig(OUT_DIR / f"fig_xai_shapley_{fig_type}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    # --- 5. Save Numbers ---
    numbers = {}
    if NUMBERS_JSON.exists():
        try:
            numbers = json.loads(NUMBERS_JSON.read_text(encoding="utf-8"))
        except Exception:
            numbers = {}

    numbers["item_4_rule_attribution"] = {
        "script": "analysis/xai/rule_attribution.py",
        "function": "compute_rule_attribution",
        "label": "exploratory; development/validation seeds 101-110; not part of the pre-registered confirmatory study",
        "cell_counts": cell_counts.to_dict(),
        "total_records": int(len(df)),
        "shapley_attribution": df_shapley.to_dict(orient="records"),
        "interaction_terms": interactions,
    }

    NUMBERS_JSON.write_text(json.dumps(numbers, indent=2), encoding="utf-8")
    print("Item 4 Rule Attribution completed successfully.")


if __name__ == "__main__":
    compute_rule_attribution()
