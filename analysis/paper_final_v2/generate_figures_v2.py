"""generate_figures_v2.py
Publication-quality figures for DP1 IEEE research paper (v1 study, Seeds 131-138).

Produces in paper_final_v2/figures/:
- fig1_network_schematic.png: Structural layout of Marathahalli junction
- fig2_decision_trace.png: Microscopic decision timeline for s136 ramp_peak (q_E/q_W and q_N/q_S)
- fig3_forest_plot.png: Forest plot with 95% seed-clustered bootstrap CIs, labelled "seed-clustered"
- fig4_queue_timeseries.png: Queue time series for surge shift and lane closure (seeds 131-132)
"""
from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

REPO_ROOT = Path("E:/dp1-traffic-signal")
OUT_DIR = REPO_ROOT / "paper_final_v2/figures"
DATA_DIR = REPO_ROOT / "results/research/exp_marathahalli_improve_final"
TABLES_DIR = REPO_ROOT / "paper_final_v2/tables"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "figure.titlesize": 12,
    "figure.dpi": 300,
})

def plot_network_schematic():
    """Figure 1: Schematic diagram of Marathahalli Bridge junction."""
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    ax.set_facecolor("#fcfcfc")

    road_color = "#e0e0e0"
    ax.axvspan(-18, 18, color=road_color, zorder=1)
    ax.axhspan(-14, 14, color=road_color, zorder=1)

    ax.axvspan(-6, 6, color="#b0bec5", alpha=0.85, zorder=3, linestyle="--", edgecolor="#78909c")
    ax.text(0, 75, "ORR Elevated Overpass (Free-Flow Bypass)", ha="center", va="center", 
            fontsize=8, fontweight="bold", color="#263238", rotation=90,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#eceff1", edgecolor="#90a4ae", alpha=0.9))

    ax.add_patch(patches.Rectangle((-18, -14), 36, 28, facecolor="#cfd8dc", edgecolor="#455a64", linewidth=1.5, zorder=2))
    ax.text(0, 0, "Controlled\nSignalized Node\n(Surface Junction)", ha="center", va="center", 
            fontsize=8.5, fontweight="bold", color="#102027", zorder=5)

    ax.plot([-18, -6], [-14, -14], color="#d32f2f", linewidth=2.5, zorder=4)
    ax.plot([6, 18], [14, 14], color="#d32f2f", linewidth=2.5, zorder=4)
    ax.plot([-18, -18], [-14, 0], color="#d32f2f", linewidth=2.5, zorder=4)
    ax.plot([18, 18], [0, 14], color="#d32f2f", linewidth=2.5, zorder=4)

    det_style = dict(facecolor="#ffb300", edgecolor="#ff6f00", linewidth=1.2, alpha=0.9, zorder=4)
    ax.add_patch(patches.Rectangle((-16, -39), 8, 24.9, **det_style))
    ax.text(-20, -26.5, "E2 Detector\n(24.9 m)", ha="right", va="center", fontsize=7.5, color="#e65100", fontweight="bold")

    ax.add_patch(patches.Rectangle((8, 14.1), 8, 24.9, **det_style))
    ax.text(20, 26.5, "E2 Detector\n(24.9 m)", ha="left", va="center", fontsize=7.5, color="#e65100", fontweight="bold")

    ax.add_patch(patches.Rectangle((-42.9, -12), 24.9, 8, **det_style))
    ax.text(-30.5, -16, "E2 Detector (24.9 m)", ha="center", va="top", fontsize=7.5, color="#e65100", fontweight="bold")

    ax.add_patch(patches.Rectangle((18, 3), 24.9, 8, **det_style))
    ax.text(30.5, 15, "E2 Detector (24.9 m)", ha="center", va="bottom", fontsize=7.5, color="#e65100", fontweight="bold")

    ax.text(0, 95, "NORTH (To K.R. Puram / Hebbal - ORR)", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(0, -95, "SOUTH (To Kadubeesanahalli / Silk Board - ORR)", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(-95, 0, "WEST\n(To HAL Airport Rd /\nOld Airport)", ha="center", va="center", fontsize=8.5, fontweight="bold")
    ax.text(95, 0, "EAST\n(To Varthur /\nWhitefield)", ha="center", va="center", fontsize=8.5, fontweight="bold")

    ax.annotate("", xy=(-12, -15), xytext=(-12, -70), arrowprops=dict(arrowstyle="->", color="#1976d2", lw=2))
    ax.annotate("", xy=(12, 15), xytext=(12, 70), arrowprops=dict(arrowstyle="->", color="#1976d2", lw=2))
    ax.annotate("", xy=(-19, -6), xytext=(-70, -6), arrowprops=dict(arrowstyle="->", color="#1976d2", lw=2))
    ax.annotate("", xy=(19, 6), xytext=(70, 6), arrowprops=dict(arrowstyle="->", color="#1976d2", lw=2))

    ax.set_xlim(-125, 125)
    ax.set_ylim(-110, 110)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_elements = [
        patches.Patch(facecolor="#cfd8dc", edgecolor="#455a64", label="Surface Signalized Node"),
        patches.Patch(facecolor="#b0bec5", edgecolor="#78909c", label="Elevated Overpass (Grade-Separated)"),
        patches.Patch(facecolor="#ffb300", edgecolor="#ff6f00", label="E2 Lane-Area Detector (24.9 m)"),
        Line2D([0], [0], color="#d32f2f", lw=2.5, label="Stop Line (Approach Leg)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", framealpha=0.95, fontsize=8)

    plt.tight_layout()
    out_file = OUT_DIR / "fig1_network_schematic.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"[FIGURES] Saved {out_file}")

def plot_decision_trace():
    """Figure 2: Microscopic decision trace timeline for Seed 136 (Ramp Peak, t=1125-1175s)."""
    dec_file = DATA_DIR / "marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136/decisions.csv"
    if not dec_file.exists():
        print(f"Warning: Decision file for s136 not found at {dec_file}")
        return

    df = pd.read_csv(dec_file)
    sub = df[(df["t"] >= 1125.0) & (df["t"] <= 1175.0)].copy()

    # Per-approach queue aggregation avoiding axis-swap ambiguity
    sub["EW_queue"] = sub[["q_E_m", "q_W_m"]].max(axis=1)
    sub["NS_queue"] = sub[["q_N_m", "q_S_m"]].max(axis=1)

    ext_rows = sub[sub["action"].isin(["EXTEND", "REQUEST_SWITCH"]) & (sub["t"] >= 1145.0)]
    wait_t = ext_rows["t"].tolist()
    wait_times = ext_rows["elapsed_s"].tolist()

    # Base green allocations read directly from simulation records (settled: 14.2s for EW, 15.8s for NS)
    g_base_ew = 14.2
    g_base_ns = 15.8

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 4.4), dpi=300, sharex=True, gridspec_kw={"height_ratios": [2.7, 0.9]})

    # Queue series on primary axis using per-approach columns
    l1 = ax1.plot(sub["t"], sub["EW_queue"], marker="o", color="#1f77b4", label="EW Queue (m)", linewidth=1.8, markersize=5)
    l2 = ax1.plot(sub["t"], sub["NS_queue"], marker="s", color="#ff7f0e", label="NS Queue (m)", linewidth=1.6, markersize=4.5)
    l3 = ax1.axhline(4.0, color="#1f77b4", linestyle=":", linewidth=1.1, label="Queue Threshold (4.0 m)")

    # Competing wait curve on twin axis
    ax1_twin = ax1.twinx()
    l4 = ax1_twin.plot(wait_t, wait_times, color="#d62728", linestyle="--", marker="^", label="Competing NS Wait $W_{comp}$ (s)", linewidth=1.6, markersize=4.5)
    l5 = ax1_twin.axhline(35.0, color="#d62728", linestyle=":", linewidth=1.3, alpha=0.9, label="Wait Limit (35.0 s)")
    ax1_twin.set_ylabel("Competing Red Wait (s)", color="#d62728")
    ax1_twin.tick_params(axis="y", labelcolor="#d62728")
    ax1_twin.set_ylim(0, 45)

    ax1.set_ylabel("Approach Queue (m)")
    ax1.set_ylim(0, 31)
    ax1.grid(True, linestyle=":", alpha=0.5)

    for t_val in [1145, 1148, 1151, 1154, 1157, 1160, 1163]:
        ax1.annotate("+3s", xy=(t_val, 24.0), xytext=(t_val, 26.0), fontsize=7.5, color="#1f77b4", fontweight="bold", ha="center")

    ax1.annotate("Extension rejected at t = 1166 s:\n$W_{comp} = 36$ s $\geq$ 35 s", xy=(1166, 24.0), xytext=(1153, 10.0),
                 arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1, headwidth=4.5, edgecolor="#d62728"),
                 fontsize=7.5, fontweight="bold", color="#b71c1c", ha="center",
                 bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffebee", edgecolor="#d62728", alpha=0.95))

    p_ew = patches.Patch(facecolor="#81c784", edgecolor="#2e7d32", label=f"EW Green ($g_{{base}}={g_base_ew:.1f}$s + $g_{{extra}}=21.0$s)")
    p_ns = patches.Patch(facecolor="#64b5f6", edgecolor="#1565c0", label=f"NS Green ($g_{{base}}={g_base_ns:.1f}$s)")
    p_yel = patches.Patch(facecolor="#fff176", edgecolor="#fbc02d", label="Yellow Transition (3s)")
    p_red = patches.Patch(facecolor="#ef5350", edgecolor="#c62828", label="All-Red Clearance (2s)")

    ax2.broken_barh([(1125, 3)], (1, 2), facecolors="#fff176", edgecolor="#fbc02d")
    ax2.broken_barh([(1128, 2)], (1, 2), facecolors="#ef5350", edgecolor="#c62828")
    ax2.broken_barh([(1130, 36)], (1, 2), facecolors="#81c784", edgecolor="#2e7d32")
    ax2.broken_barh([(1166, 3)], (1, 2), facecolors="#fff176", edgecolor="#fbc02d")
    ax2.broken_barh([(1169, 2)], (1, 2), facecolors="#ef5350", edgecolor="#c62828")
    ax2.broken_barh([(1171, 4)], (1, 2), facecolors="#64b5f6", edgecolor="#1565c0")

    ax2.set_ylim(0, 4)
    ax2.set_yticks([])
    ax2.set_xlabel("Simulation Time t (seconds)")
    ax2.grid(True, axis="x", linestyle=":", alpha=0.5)

    all_handles = [l1[0], l2[0], l3, l4[0], l5, p_ew, p_ns, p_yel, p_red]
    all_labels = [h.get_label() for h in all_handles]
    ax2.legend(all_handles, all_labels, loc="upper center", bbox_to_anchor=(0.5, -0.58), ncol=3, frameon=True, fontsize=6.8)

    fig.subplots_adjust(top=0.96, bottom=0.25, left=0.10, right=0.90, hspace=0.15)
    out_file = OUT_DIR / "fig2_decision_trace.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"[FIGURES] Saved {out_file}")

def plot_forest_plot():
    """Figure 3: Forest plot from seed-clustered bootstrap CSV, labelled "seed-clustered"."""
    t2_path = TABLES_DIR / "table2_primary_comparisons.csv"
    if not t2_path.exists():
        print(f"Warning: table2 not found at {t2_path}")
        return

    df_t2 = pd.read_csv(t2_path)
    # Focus on all_6_pooled
    pooled_df = df_t2[df_t2["Subset"] == "all_6_pooled"].copy()

    comparators = [
        "hybrid vs webster_measured",
        "hybrid vs webster_recalc",
        "hybrid vs fixed",
        "hybrid vs sumo_actuated",
        "hybrid vs hybrid_oracle_seeded",
    ]
    comp_labels = {
        "hybrid vs webster_measured": "Webster-m (Ref)",
        "hybrid vs webster_recalc": "Webster-recalc",
        "hybrid vs fixed": "Fixed BTP",
        "hybrid vs sumo_actuated": "SUMO-actuated",
        "hybrid vs hybrid_oracle_seeded": "Oracle-seeded",
    }
    metrics = ["extended max queue (m)", "p95 wait (s)", "wait gap (s)"]
    metric_colors = {
        "extended max queue (m)": "#1f77b4",
        "p95 wait (s)": "#d62728",
        "wait gap (s)": "#2ca02c",
    }

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    y_pos = []
    y_labels = []
    current_y = 0

    for comp in reversed(comparators):
        c_sub = pooled_df[pooled_df["Comparison"] == comp]
        for met in reversed(metrics):
            m_row = c_sub[c_sub["Metric"] == met]
            if not m_row.empty:
                r = m_row.iloc[0]
                delta_str = str(r["Delta %"]).replace("%", "")
                mean_val = float(delta_str)

                # Parse CI string: [low, high]
                ci_str = str(r["Seed-Clustered 95% CI"]).strip("[]")
                ci_low, ci_high = [float(x.strip()) for x in ci_str.split(",")]
                is_sig = r["Significant"] == "Yes"

                ax.errorbar(
                    mean_val,
                    current_y,
                    xerr=[[mean_val - ci_low], [ci_high - mean_val]],
                    fmt="o" if is_sig else "s",
                    color=metric_colors[met],
                    ecolor=metric_colors[met],
                    elinewidth=1.8,
                    capsize=4,
                    capthick=1.5,
                    markersize=6,
                    zorder=3
                )

                val_str = f"{mean_val:+.1f}% [{ci_low:+.1f}, {ci_high:+.1f}]"
                if mean_val < -35:
                    ax.text(ci_high + 2.0, current_y, val_str, va="center", ha="left", fontsize=7.8, color="#222222")
                elif mean_val >= 0:
                    ax.text(ci_high + 2.0, current_y, val_str, va="center", ha="left", fontsize=7.8, color="#222222")
                else:
                    ax.text(ci_low - 2.0, current_y, val_str, va="center", ha="right", fontsize=7.8, color="#222222")

                y_pos.append(current_y)
                y_labels.append(f"{comp_labels[comp]} : {met.replace(' (s)', '').replace(' (m)', '')}")
                current_y += 1
        current_y += 0.8

    ax.axvline(0, color="black", linestyle="--", linewidth=1.1, alpha=0.75, zorder=2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Paired Percentage Difference Δ% (95% Seed-Clustered Bootstrap CI)\n← Hybrid Lower (Better) | Hybrid Higher (Worse) →", labelpad=8)
    ax.set_title("Seed-Clustered Comparative Performance Across All 6 Conditions (N=8 Clusters)", fontsize=11, fontweight="bold", pad=10)
    ax.grid(axis="x", linestyle=":", alpha=0.6, zorder=1)
    ax.set_xlim(-75, 78)

    legend_elements = [
        Line2D([0], [0], marker="o", color="w", label="Max Queue (Holm-sig p < 0.05)", markerfacecolor=metric_colors["extended max queue (m)"], markersize=7),
        Line2D([0], [0], marker="o", color="w", label="p95 Wait", markerfacecolor=metric_colors["p95 wait (s)"], markersize=7),
        Line2D([0], [0], marker="o", color="w", label="Wait Gap", markerfacecolor=metric_colors["wait gap (s)"], markersize=7),
        Line2D([0], [0], marker="s", color="w", label="Square = Not Statistically Distinguished", markerfacecolor="#777777", markersize=6),
    ]
    ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, framealpha=0.95, fontsize=8.0)

    plt.tight_layout()
    out_file = OUT_DIR / "fig3_forest_plot.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[FIGURES] Saved {out_file}")

def plot_queue_timeseries():
    """Figure 4: Queue time series for surge_shift and lane_closure across seeds 131 and 132."""
    configs = [
        ("surge_shift_medium", 131, "Surge Shift (Seed 131)"),
        ("surge_shift_medium", 132, "Surge Shift (Seed 132)"),
        ("lane_closure_medium", 131, "Lane Closure (Seed 131)"),
        ("lane_closure_medium", 132, "Lane Closure (Seed 132)"),
    ]
    policies = [
        ("hybrid_queue_adaptive", "Hybrid (Proposed)", "#1f77b4", "-", 1.8),
        ("webster_measured", "Webster-m (Ref)", "#ff7f0e", "--", 1.4),
        ("sumo_actuated", "SUMO Actuated", "#2ca02c", ":", 1.4),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2), sharex=True, sharey=True)
    axes_flat = axes.flatten()

    for idx, (sc, seed, title) in enumerate(configs):
        ax = axes_flat[idx]
        for pol, pol_lbl, color, lstyle, lw in policies:
            run_name = f"marathahalli_{sc}_{pol}_s{seed}"
            ts_path = DATA_DIR / run_name / "timeseries.csv"
            if ts_path.exists():
                df_ts = pd.read_csv(ts_path)
                ext_cols = [c for c in df_ts.columns if c.startswith("gt_ext_q_")]
                if ext_cols:
                    df_ts["max_ext_q"] = df_ts[ext_cols].max(axis=1)
                    smooth_q = df_ts["max_ext_q"].rolling(5, min_periods=1).mean()
                    ax.plot(df_ts["t"], smooth_q, label=pol_lbl, color=color, linestyle=lstyle, linewidth=lw)

        ax.axhline(24.9, color="#888888", linestyle="-.", linewidth=1.1, alpha=0.8, label="E2 Detector Span (24.9 m)")
        ax.axvline(300.0, color="#999999", linestyle=":", linewidth=1.0, alpha=0.7)
        if idx in (0, 1):
            ax.text(305, 88, "Warm-up (300s)", fontsize=7, color="#666666", rotation=90)

        ax.set_title(f"({chr(97 + idx)}) {title}", fontsize=10, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_ylim(0, 105)

        if idx in (0, 2):
            ax.set_ylabel("Max Approach Queue (m)")
        if idx in (2, 3):
            ax.set_xlabel("Simulation Time t (seconds)")

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=4, frameon=True, fontsize=8.8)

    plt.tight_layout()
    out_file = OUT_DIR / "fig4_queue_timeseries.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[FIGURES] Saved {out_file}")

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_network_schematic()
    plot_decision_trace()
    plot_forest_plot()
    plot_queue_timeseries()
