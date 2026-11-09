"""Item 1: Reason-Code Audit for DP1 Confirmatory Runs (Seeds 131-138).

Analyzes decisions.csv for hybrid_queue_adaptive and hybrid_oracle_seeded.
Produces:
- CSV tables: table_xai_reason_codes_hqa.csv, table_xai_reason_codes_hos.csv, table_xai_switch_triggers.csv
- Figures: fig_xai_reason_codes_single.png (3.5 in), fig_xai_reason_codes_double.png (7.1 in) at 300 dpi
- Numbers logged to numbers_xai.json
"""
import json
from pathlib import Path
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT_DIR / "results" / "research" / "exp_marathahalli_improve_final"
OUT_DIR = Path(__file__).resolve().parent
NUMBERS_JSON = OUT_DIR / "numbers_xai.json"

CONDITIONS = [
    "balanced-low",
    "balanced-heavy",
    "imbalanced_orr-heavy",
    "ramp_peak-medium",
    "surge_shift-medium",
    "lane_closure-medium",
]


def load_logs(policy: str) -> pd.DataFrame:
    """Load decisions.csv for a policy across all 48 runs (6 conditions x 8 seeds)."""
    if policy == "hybrid_queue_adaptive":
        pattern = "marathahalli_*_hybrid_queue_adaptive_s13[1-8]/decisions.csv"
        regex = r"marathahalli_([a-z_]+)_(low|medium|heavy)_hybrid_queue_adaptive_s(\d+)"
    elif policy == "hybrid_oracle_seeded":
        pattern = "ablation_*_hybrid_oracle_seeded_s13[1-8]/decisions.csv"
        regex = r"ablation_([a-z_]+)_(low|medium|heavy)_hybrid_oracle_seeded_s(\d+)"
    else:
        raise ValueError(f"Unknown policy: {policy}")

    files = sorted(list(BASE_DIR.glob(pattern)))
    assert len(files) == 48, f"Expected 48 files for {policy}, found {len(files)}"

    dfs = []
    for f in files:
        m = re.search(regex, f.parent.name)
        scen, dem, seed = m.groups()
        cond = f"{scen}-{dem}"
        df = pd.read_csv(f)
        df["policy"] = policy
        df["condition"] = cond
        df["seed"] = int(seed)
        df["run_id"] = f.parent.name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def compute_reason_code_audit():
    df_hqa = load_logs("hybrid_queue_adaptive")
    df_hos = load_logs("hybrid_oracle_seeded")

    # Distinct codes
    hqa_codes = sorted(df_hqa["decision_outcome"].unique().tolist())
    hos_codes = sorted(df_hos["decision_outcome"].unique().tolist())

    # --- 1. Reason Codes Table for HQA ---
    ct_hqa_counts = pd.crosstab(df_hqa["decision_outcome"], df_hqa["condition"])
    ct_hqa_counts["Pooled"] = df_hqa["decision_outcome"].value_counts()
    ct_hqa_counts.to_csv(OUT_DIR / "table_xai_reason_codes_hqa.csv")

    ct_hos_counts = pd.crosstab(df_hos["decision_outcome"], df_hos["condition"])
    ct_hos_counts["Pooled"] = df_hos["decision_outcome"].value_counts()
    ct_hos_counts.to_csv(OUT_DIR / "table_xai_reason_codes_hos.csv")

    # --- 2. Switch Trigger Breakdown ---
    switches_hqa = df_hqa[df_hqa["decision_outcome"].str.startswith("SWITCH_")].copy()
    trigger_counts = pd.crosstab(switches_hqa["decision_outcome"], switches_hqa["condition"])
    trigger_counts["Pooled"] = switches_hqa["decision_outcome"].value_counts()

    trigger_shares = pd.crosstab(switches_hqa["decision_outcome"], switches_hqa["condition"], normalize="columns") * 100
    trigger_shares["Pooled"] = (switches_hqa["decision_outcome"].value_counts() / len(switches_hqa)) * 100
    trigger_shares.to_csv(OUT_DIR / "table_xai_switch_triggers.csv")

    # --- 3. Fairness Guard Analysis ---
    guard_events = df_hqa[df_hqa["decision_outcome"] == "SWITCH_FAIRNESS_WAIT_LIMIT"]
    n_guard_switches = int(len(guard_events))
    runs_with_guard = df_hqa[df_hqa["decision_outcome"] == "SWITCH_FAIRNESS_WAIT_LIMIT"]["run_id"].nunique()
    share_runs_with_guard = float(runs_with_guard / 48)

    # Details of the guard event
    guard_details = {}
    if n_guard_switches > 0:
        row = guard_events.iloc[0]
        # Alternative remaining green until max_green ceiling 60s
        sec_earlier_vs_max_green = float(60.0 - row["elapsed_s"])
        sec_earlier_vs_step = float(row["delta_g_req_s"])
        guard_details = {
            "run_id": str(row["run_id"]),
            "t": float(row["t"]),
            "cycle": int(row["cycle"]),
            "axis": str(row["axis"]),
            "elapsed_s": float(row["elapsed_s"]),
            "q_active_m": float(row["q_active_m"]),
            "q_competing_m": float(row["q_competing_m"]),
            "seconds_earlier_vs_max_green": sec_earlier_vs_max_green,
            "seconds_earlier_vs_next_step": sec_earlier_vs_step,
        }

    # --- 4. Extensions Analysis ---
    # For each run and each green phase, count extensions
    # A green phase starts with BASELINE_ENTRY
    extension_stats_per_condition = {}
    pooled_total_greens = 0
    pooled_total_extensions = 0
    pooled_extra_green_s = 0.0
    pooled_zero_ext_greens = 0

    for cond in CONDITIONS:
        cond_df = df_hqa[df_hqa["condition"] == cond]
        greens_count = (cond_df["decision_outcome"] == "BASELINE_ENTRY").sum()
        ext_count = (cond_df["decision_outcome"] == "EXTEND_APPROVED").sum()
        extra_s = ext_count * 3.0

        # Greens with extensions: count how many cycles had at least one extension
        ext_cycles = set(cond_df[cond_df["decision_outcome"] == "EXTEND_APPROVED"][["run_id", "cycle"]].itertuples(index=False, name=None))
        greens_with_ext = len(ext_cycles)
        zero_ext = greens_count - greens_with_ext

        extension_stats_per_condition[cond] = {
            "total_greens": int(greens_count),
            "total_extensions": int(ext_count),
            "mean_extensions_per_green": float(ext_count / greens_count if greens_count else 0.0),
            "total_extra_green_s": float(extra_s),
            "mean_extra_green_s_per_run": float(extra_s / 8.0),
            "share_greens_zero_extensions": float(zero_ext / greens_count if greens_count else 1.0),
        }

        pooled_total_greens += greens_count
        pooled_total_extensions += ext_count
        pooled_extra_green_s += extra_s
        pooled_zero_ext_greens += zero_ext

    pooled_extension_stats = {
        "total_greens": int(pooled_total_greens),
        "total_extensions": int(pooled_total_extensions),
        "mean_extensions_per_green": float(pooled_total_extensions / pooled_total_greens),
        "total_extra_green_s": float(pooled_extra_green_s),
        "mean_extra_green_s_per_run": float(pooled_extra_green_s / 48.0),
        "share_greens_zero_extensions": float(pooled_zero_ext_greens / pooled_total_greens),
    }

    # --- 5. Generate Figures (IEEE single-column 3.5 in and double-column 7.1 in) ---
    plot_data = trigger_shares.drop(columns=["Pooled"])
    # Clean category names
    rename_map = {
        "SWITCH_GAP_OUT": "Gap-Out (Q_active = 0)",
        "SWITCH_DEMAND_EXHAUSTED": "Demand Exhausted (Q < 4m)",
        "SWITCH_DEMAND_FAIRNESS": "Demand Fairness Ratio",
        "SWITCH_FAIRNESS_WAIT_LIMIT": "Red-Wait Limit (35s)",
    }
    plot_data.index = [rename_map.get(i, i) for i in plot_data.index]

    cond_labels = [
        "Balanced\nLow",
        "Balanced\nHeavy",
        "Imbalanced\nORR Heavy",
        "Ramp Peak\nMedium",
        "Surge Shift\nMedium",
        "Lane Closure\nMedium",
    ]

    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#e7298a"]

    for fig_type, width in [("single", 3.5), ("double", 7.1)]:
        fig, ax = plt.subplots(figsize=(width, 3.2 if width == 3.5 else 3.4), dpi=300)
        bottom = np.zeros(len(CONDITIONS))
        x = np.arange(len(CONDITIONS))

        for idx, (trigger, row) in enumerate(plot_data.iterrows()):
            vals = [row.get(c, 0.0) for c in CONDITIONS]
            ax.bar(x, vals, bottom=bottom, label=trigger, color=colors[idx % len(colors)], width=0.62, edgecolor="black", linewidth=0.5)
            bottom += np.array(vals)

        ax.set_ylabel("Share of Phase Switches (%)", fontsize=8, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(cond_labels, fontsize=7)
        ax.set_ylim(0, 100)
        ax.tick_params(axis="both", which="major", labelsize=7)
        ax.grid(axis="y", linestyle=":", alpha=0.6)

        if width == 3.5:
            ax.legend(fontsize=6, loc="upper right", framealpha=0.9, bbox_to_anchor=(1.0, 1.0))
            ax.set_title("Phase Switch Triggers by Condition (Seeds 131-138)", fontsize=8, fontweight="bold")
        else:
            ax.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, -0.32), ncol=4, framealpha=0.9)
            ax.set_title("Distribution of Phase Switch Triggers Across Evaluation Conditions (Seeds 131–138)", fontsize=9, fontweight="bold")

        plt.tight_layout()
        out_path = OUT_DIR / f"fig_xai_reason_codes_{fig_type}.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    # --- 6. Save numbers to numbers_xai.json ---
    numbers = {}
    if NUMBERS_JSON.exists():
        try:
            numbers = json.loads(NUMBERS_JSON.read_text(encoding="utf-8"))
        except Exception:
            numbers = {}

    numbers["item_1_reason_code_audit"] = {
        "script": "analysis/xai/reason_code_audit.py",
        "function": "compute_reason_code_audit",
        "distinct_codes_hqa": hqa_codes,
        "distinct_codes_hos": hos_codes,
        "total_hqa_records": int(len(df_hqa)),
        "total_hqa_switches": int(len(switches_hqa)),
        "switch_trigger_counts_pooled": {k: int(v) for k, v in switches_hqa["decision_outcome"].value_counts().items()},
        "switch_trigger_shares_pooled_pct": {k: round(float(v / len(switches_hqa) * 100), 2) for k, v in switches_hqa["decision_outcome"].value_counts().items()},
        "fairness_guard": {
            "total_forced_switches": n_guard_switches,
            "share_of_runs_fired": share_runs_with_guard,
            "share_of_runs_fired_pct": round(share_runs_with_guard * 100, 2),
            "event_details": guard_details,
        },
        "extensions": {
            "pooled": pooled_extension_stats,
            "per_condition": extension_stats_per_condition,
        },
    }

    NUMBERS_JSON.write_text(json.dumps(numbers, indent=2), encoding="utf-8")
    print("Item 1 Reason-Code Audit completed successfully.")


if __name__ == "__main__":
    compute_reason_code_audit()
