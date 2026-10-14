"""Generate research evaluation plots from experiment data."""
from pathlib import Path
from typing import Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

POLICY_COLORS = {
    "fixed": "#8A94A6",
    "fixed_webster": "#D97706",
    "adaptive": "#0E7C86",
    "pressure": "#7C3AED",
    "queue_extension": "#059669",
    "rl_dqn": "#2563EB",
}


def generate_research_plots(
    raw_df: pd.DataFrame,
    agg_df: pd.DataFrame,
    deltas_df: pd.DataFrame,
    out_dir: Path,
    paired_ties_df: Optional[pd.DataFrame] = None,
):
    """Generate comprehensive research figures and save them to out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if raw_df.empty:
        return

    patterns = list(raw_df["pattern"].unique())
    policies = [p for p in POLICY_COLORS.keys() if p in raw_df["policy"].unique()]
    levels = list(raw_df["demand_level"].unique())

    # 1. Waiting Time by Level & Pattern
    fig, axes = plt.subplots(len(levels), len(patterns), figsize=(3.8 * len(patterns), 3.2 * len(levels)), squeeze=False)
    for row_idx, lvl in enumerate(levels):
        for col_idx, pat in enumerate(patterns):
            ax = axes[row_idx][col_idx]
            sub = agg_df[(agg_df["demand_level"] == lvl) & (agg_df["pattern"] == pat)]
            if not sub.empty:
                x_pos = np.arange(len(policies))
                means = []
                stds = []
                for pol in policies:
                    pol_row = sub[sub["policy"] == pol]
                    means.append(pol_row["avg_wait_s_mean"].values[0] if not pol_row.empty else 0.0)
                    stds.append(pol_row["avg_wait_s_std"].values[0] if (not pol_row.empty and not np.isnan(pol_row["avg_wait_s_std"].values[0])) else 0.0)
                colors = [POLICY_COLORS.get(p, "#8A94A6") for p in policies]
                ax.bar(x_pos, means, yerr=stds, capsize=3, color=colors, alpha=0.9)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(policies, rotation=35, ha="right", fontsize=8)
            ax.set_title(f"{pat} ({lvl})", fontsize=10)
            ax.set_ylabel("Avg Wait (s)")
            ax.grid(axis="y", alpha=0.3)
    fig.suptitle("Mean Waiting Time per Vehicle (s) — Lower is Better", fontsize=13, y=1.01)
    fig.tight_layout()
    fig.savefig(out_dir / "wait_time_by_level.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 2. Paired Wait Delta vs Fixed with 95% Bootstrap CIs
    if not deltas_df.empty:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        sub_deltas = deltas_df.copy()
        sub_deltas["label"] = sub_deltas["pattern"] + "\n(" + sub_deltas["demand_level"] + ")"
        labels = sub_deltas["label"].unique()
        cands = [p for p in policies if p != "fixed" and p in sub_deltas["policy"].unique()]
        n_cands = len(cands)
        w = 0.8 / max(n_cands, 1)

        for i, cand in enumerate(cands):
            c_data = sub_deltas[sub_deltas["policy"] == cand]
            means = []
            err_low = []
            err_high = []
            for lab in labels:
                match = c_data[c_data["label"] == lab]
                if not match.empty:
                    m = match["delta_wait_mean_s"].values[0]
                    lo = match["delta_wait_ci_lower_s"].values[0]
                    hi = match["delta_wait_ci_upper_s"].values[0]
                    means.append(m)
                    err_low.append(abs(m - lo))
                    err_high.append(abs(hi - m))
                else:
                    means.append(0.0)
                    err_low.append(0.0)
                    err_high.append(0.0)

            x_locs = [x + (i - (n_cands - 1) / 2.0) * w for x in range(len(labels))]
            yerr = [err_low, err_high]
            ax.bar(
                x_locs, means, w, yerr=yerr, capsize=3,
                label=cand, color=POLICY_COLORS.get(cand, "#0E7C86"), alpha=0.85
            )

        ax.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_title("Paired Difference in Waiting Time vs Fixed Baseline (95% Bootstrap CI)\nNegative favors candidate policy", fontsize=11)
        ax.set_ylabel("Delta Wait (s)")
        ax.legend(title="Candidate Policy")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / "paired_wait_delta.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # 3. Queue Length by Demand Level
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for pol in policies:
        pol_sub = agg_df[agg_df["policy"] == pol]
        if not pol_sub.empty:
            lvl_means = []
            for lvl in levels:
                val = pol_sub[pol_sub["demand_level"] == lvl]["avg_queue_m_mean"].mean()
                lvl_means.append(val)
            ax.plot(levels, lvl_means, marker="o", label=pol, color=POLICY_COLORS.get(pol, "#8A94A6"), linewidth=2)
    ax.set_title("Average Queue Length Across Demand Levels (m) — Lower is Better")
    ax.set_xlabel("Demand Level")
    ax.set_ylabel("Avg Queue (m)")
    ax.legend(title="Policy")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "queue_length_by_level.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 4. Directional Wait Disparity
    if "directional_wait_disparity_s_mean" in agg_df.columns:
        fig, ax = plt.subplots(figsize=(8.5, 4.2))
        for pol in policies:
            pol_sub = agg_df[agg_df["policy"] == pol]
            if not pol_sub.empty:
                disp_means = []
                for pat in patterns:
                    val = pol_sub[pol_sub["pattern"] == pat]["directional_wait_disparity_s_mean"].mean()
                    disp_means.append(val)
                ax.plot(patterns, disp_means, marker="s", label=pol, color=POLICY_COLORS.get(pol, "#8A94A6"), linewidth=1.8)
        ax.set_title("Directional Service Disparity: |Wait(NS) - Wait(EW)| (s)")
        ax.set_xlabel("Scenario Pattern")
        ax.set_ylabel("Disparity (s)")
        ax.legend(title="Policy")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / "fairness_disparity.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # 5. Forest Plot of Paired Best-Policy Comparison and Statistical Ties
    if paired_ties_df is not None and not paired_ties_df.empty:
        comp_df = paired_ties_df[paired_ties_df["secondary_candidate"].notna()].copy()
        if not comp_df.empty:
            fig, ax = plt.subplots(figsize=(10, max(4.5, 0.45 * len(comp_df))))
            comp_df["cond_label"] = (
                comp_df["pattern"] + " (" + comp_df["demand_level"] + ")\n"
                + comp_df["primary_leader"] + " vs " + comp_df["secondary_candidate"]
            )
            y_pos = np.arange(len(comp_df))
            deltas = comp_df["paired_delta_mean_s"].values
            ci_low = comp_df["paired_delta_ci_lower_s"].values
            ci_high = comp_df["paired_delta_ci_upper_s"].values
            statuses = comp_df["status"].values

            colors = ["#D97706" if s == "TIE" else "#059669" for s in statuses]

            for y, d, lo, hi, c in zip(y_pos, deltas, ci_low, ci_high, colors):
                err_l = max(0.0, d - lo)
                err_r = max(0.0, hi - d)
                ax.errorbar(
                    d, y, xerr=[[err_l], [err_r]],
                    fmt="o", color=c, ecolor=c, elinewidth=2.5,
                    capsize=4, capthick=1.5, markersize=6.5, zorder=5
                )

            ax.axvline(0.0, color="#EF4444", linestyle="--", linewidth=1.5, alpha=0.8, label="Zero Difference (Tie Line)")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(comp_df["cond_label"].values, fontsize=8.5)
            ax.invert_yaxis()
            ax.set_xlabel("Paired Difference in Waiting Time: Leader - Runner-Up (s)\n(Negative values favor Primary Leader)", fontsize=9.5)
            ax.set_title("Paired Best-Policy Comparison & Statistical Ties (95% Bootstrap CI)\nGreen: Significant Winner (p < 0.05) | Amber: Statistical Tie (p > 0.05)", fontsize=11)
            ax.grid(axis="x", alpha=0.3)
            ax.legend(loc="lower left", fontsize=8.5)
            fig.tight_layout()
            fig.savefig(out_dir / "paired_best_ties.png", dpi=150, bbox_inches="tight")
            plt.close(fig)
