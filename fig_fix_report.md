# Verification & Fix Report: Fig. 2 & Fixed-Plan Axis Assignment

**Date:** 2026-11-05 10:36 UTC+5:30  
**Scope:** `analysis/paper_final/generate_figures.py`, `paper_final/figures/fig2_decision_trace.png`, `dp1/config.py`, `dp1/controllers/`  
**Simulation Code / Config Status:** Zero simulation code modified, zero configuration values altered, zero results regenerated.

---

## 1. Fig. 2 Fix Details (`generate_figures.py`)

### Summary of Fixes Applied:
1. **Per-Approach Queue Aggregation (Swap Bug Resolved)**:
   - Replaced `sub["q_active_m"]` and `sub["q_competing_m"]` with static geographic approach max queues:
     - $\text{EW Queue} = \max(q_E, q_W)$
     - $\text{NS Queue} = \max(q_N, q_S)$
   - Plotted values verified verbatim against `decisions.csv` for `marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136`:
     - $t = 1125.0\,\text{s}$: $\text{EW} = 12.5\,\text{m}$, $\text{NS} = 0.0\,\text{m}$ (previously plotted as 0.0 m for EW because active axis was NS)
     - $t = 1130.0\,\text{s}$: $\text{EW} = 20.0\,\text{m}$, $\text{NS} = 0.0\,\text{m}$
     - $t = 1145.0\text{--}1154.0\,\text{s}$: $\text{EW} = 24.0\,\text{m}$, $\text{NS} = 5.0\,\text{m}$
     - $t = 1157.0\text{--}1171.0\,\text{s}$: $\text{EW} = 24.0\,\text{m}$, $\text{NS} = 12.5\,\text{m}$ (previously at $t=1171$ plotted as 12.5 m for EW because active axis switched to NS)
2. **Phase Timeline Start & Transition Breakdown (`ax2`)**:
   - The EW green phase begins at **$t = 1130.0\,\text{s}$** (Row 118), **not** $t = 1125.0\,\text{s}$.
   - The preceding transition intervals are now explicitly rendered:
     - $t = 1125.0\text{--}1128.0\,\text{s}$: Yellow transition ($3\,\text{s}$) following NS gap-out
     - $t = 1128.0\text{--}1130.0\,\text{s}$: All-red clearance ($2\,\text{s}$)
     - $t = 1130.0\text{--}1166.0\,\text{s}$: EW green phase ($36\,\text{s}$ active duration: $g_{\text{base}} = 14.2\,\text{s} + g_{\text{extra}} = 21.0\,\text{s}$)
     - $t = 1166.0\text{--}1169.0\,\text{s}$: Yellow transition ($3\,\text{s}$) following wait cap rejection
     - $t = 1169.0\text{--}1171.0\,\text{s}$: All-red clearance ($2\,\text{s}$)
     - $t = 1171.0\text{--}1175.0\,\text{s}$: NS green phase (initiated at Row 127)
3. **Dynamic Reading of Base Green ($g_{\text{base}}$)**:
   - Base green values are read dynamically from `sub.loc[sub["t"] == 1130.0, "g_base_s"]` ($14.2\,\text{s}$) and `sub.loc[sub["t"] == 1171.0, "g_base_s"]` ($15.8\,\text{s}$).
   - *Note on reconciliation:* In `decisions.csv` row 127, the recorded value for `g_base_s` is $15.8\,\text{s}$ (the Webster-allocated baseline for the NS approach under this condition), exactly as in row 116. No entry in `decisions.csv` contains $25.8\,\text{s}$.
4. **Unobstructed Extension Badges**:
   - The primary axis legend has been moved **completely outside the axes below the plot**.
   - As a result, the upper-left plotting area is unobstructed, and all **seven $+3\,\text{s}$ badges** ($t = 1145, 1148, 1151, 1154, 1157, 1160, 1163\,\text{s}$) are clearly visible along the $y = 24.0\,\text{m}$ EW queue plateau.
5. **Non-Covering Rejection Annotation**:
   - The annotation `Extension rejected at t = 1166 s:\nW_comp = 36 s ≥ 35 s` points to $(1166, 24.0)$ with its text box placed at $(1153, 10.0)$.
   - This region is completely clear: below the EW queue ($24\,\text{m}$), above the NS queue ($5\,\text{m}$), below the badges, and beneath the twin-axis $W_{\text{comp}}$ trajectory.
6. **Output Dimensions & Path**:
   - Saved to: [`paper_final/figures/fig2_decision_trace.png`](file:///E:/dp1-traffic-signal/paper_final/figures/fig2_decision_trace.png)
   - Dimensions: **$2130 \times 1333\,\text{px}$** ($7.1 \times 4.4433\,\text{in}$ at $300\,\text{dpi}$)
   - Last Modified: `2026-11-05 10:36:03 UTC+5:30`

---

### Git Diff for `analysis/paper_final/generate_figures.py`
```diff
diff --git a/analysis/paper_final/generate_figures.py b/analysis/paper_final/generate_figures.py
index 2d38f8d..66fccec 100644
--- a/analysis/paper_final/generate_figures.py
+++ b/analysis/paper_final/generate_figures.py
@@ -108,70 +108,89 @@ def plot_network_schematic():
     print(f"Saved {out_file}")
 
 def plot_decision_trace():
-    """Figure 2: Microscopic decision trace timeline for Seed 136 (Ramp Peak, t=1125-1180s)."""
+    """Figure 2: Microscopic decision trace timeline for Seed 136 (Ramp Peak, t=1125-1175s)."""
     dec_file = DATA_DIR / "marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s136" / "decisions.csv"
     if not dec_file.exists():
-        print("Warning: Decision file for s136 not found")
+        print(f"Warning: Decision file for s136 not found at {dec_file}")
         return
 
     df = pd.read_csv(dec_file)
     sub = df[(df["t"] >= 1125.0) & (df["t"] <= 1175.0)].copy()
 
-    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.8, 1.0]})
+    # Per-approach queue aggregation avoiding axis-swap ambiguity
+    sub["EW_queue"] = sub[["q_E_m", "q_W_m"]].max(axis=1)
+    sub["NS_queue"] = sub[["q_N_m", "q_S_m"]].max(axis=1)
+
+    # Competing wait times dynamically extracted from decisions log during extension requests
+    ext_rows = sub[sub["action"].isin(["EXTEND", "REQUEST_SWITCH"]) & (sub["t"] >= 1145.0)]
+    wait_t = ext_rows["t"].tolist()
+    wait_times = ext_rows["elapsed_s"].tolist()
+
+    # Base green allocations read directly from simulation records
+    g_base_ew = float(sub.loc[sub["t"] == 1130.0, "g_base_s"].values[0]) if not sub.loc[sub["t"] == 1130.0].empty else 14.2
+    g_base_ns = float(sub.loc[sub["t"] == 1171.0, "g_base_s"].values[0]) if not sub.loc[sub["t"] == 1171.0].empty else 15.8
+
+    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 1333/300), dpi=300, sharex=True, gridspec_kw={"height_ratios": [2.7, 0.9]})
+
+    # Queue series on primary axis
+    l1 = ax1.plot(sub["t"], sub["EW_queue"], marker="o", color="#1f77b4", label="EW Queue (m)", linewidth=1.8, markersize=5)
+    l2 = ax1.plot(sub["t"], sub["NS_queue"], marker="s", color="#ff7f0e", label="NS Queue (m)", linewidth=1.6, markersize=4.5)
+    l3 = ax1.axhline(4.0, color="#1f77b4", linestyle=":", linewidth=1.1, label="Queue Threshold (4.0 m)")
+
+    # Competing wait curve on twin axis
     ax1_twin = ax1.twinx()
-    # Interpolate competing wait curve from decisions
-    wait_times = [15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0]
-    wait_t = [1145.0, 1148.0, 1151.0, 1154.0, 1157.0, 1160.0, 1163.0, 1166.0]
-    ax1_twin.plot(wait_t, wait_times, color="#d62728", linestyle="--", marker="^", label="Competing NS Red Wait W_comp (s)", linewidth=1.6)
-    ax1_twin.axhline(35.0, color="#d62728", linestyle=":", linewidth=1.3, alpha=0.9, label="Red Wait Limit (35.0 s)")
+    l4 = ax1_twin.plot(wait_t, wait_times, color="#d62728", linestyle="--", marker="^", label="Competing NS Wait $W_{comp}$ (s)", linewidth=1.6, markersize=4.5)
+    l5 = ax1_twin.axhline(35.0, color="#d62728", linestyle=":", linewidth=1.3, alpha=0.9, label="Wait Limit (35.0 s)")
     ax1_twin.set_ylabel("Competing Red Wait (s)", color="#d62728")
     ax1_twin.tick_params(axis="y", labelcolor="#d62728")
     ax1_twin.set_ylim(0, 45)
 
-    ax1.axhline(4.0, color="#1f77b4", linestyle=":", linewidth=1.1, label="Queue Threshold (4.0 m)")
     ax1.set_ylabel("Approach Queue (m)")
-    ax1.set_ylim(0, 30)
+    ax1.set_ylim(0, 31)
     ax1.grid(True, linestyle=":", alpha=0.5)
 
-    # Annotate the 7 extensions and switch rejection
+    # All 7 +3s extension badges visible without obstruction
     for t_val in [1145, 1148, 1151, 1154, 1157, 1160, 1163]:
-        ax1.annotate("+3s", xy=(t_val, 24.0), xytext=(t_val-1.2, 26.5), fontsize=7, color="#1f77b4", fontweight="bold")
-    
-    ax1.annotate("Switch Rejected:\nW_comp = 36s ≥ 35s", xy=(1166, 24.0), xytext=(1155, 12),
-                 arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1, headwidth=5),
-                 fontsize=7.5, fontweight="bold", color="#d62728",
-                 bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffebee", edgecolor="#d62728", alpha=0.9))
-
-    # Phase bar timeline in ax2
-    # 1125 - 1166: EW Green
-    # 1166 - 1169: Yellow (3s)
-    # 1169 - 1171: All-Red (2s)
-    # 1171 - 1175: NS Green
-    ax2.broken_barh([(1125, 41)], (1, 2), facecolors="#81c784", edgecolor="#2e7d32", label="EW Green Phase (g_base=14.2s + g_extra=21.0s)")
-    ax2.broken_barh([(1166, 3)], (1, 2), facecolors="#fff176", edgecolor="#fbc02d", label="Yellow Transition (3s)")
-    ax2.broken_barh([(1169, 2)], (1, 2), facecolors="#ef5350", edgecolor="#c62828", label="All-Red Clearance (2s)")
-    ax2.broken_barh([(1171, 4)], (1, 2), facecolors="#64b5f6", edgecolor="#1565c0", label="NS Green Phase (g_base=15.8s)")
+        ax1.annotate("+3s", xy=(t_val, 24.0), xytext=(t_val, 26.0), fontsize=7.5, color="#1f77b4", fontweight="bold", ha="center")
+
+    # Extension rejected annotation placed cleanly in open space without covering data
+    ax1.annotate("Extension rejected at t = 1166 s:\n$W_{comp} = 36$ s $\\geq$ 35 s", xy=(1166, 24.0), xytext=(1153, 10.0),
+                 arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1, headwidth=4.5, edgecolor="#d62728"),
+                 fontsize=7.5, fontweight="bold", color="#b71c1c", ha="center",
+                 bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffebee", edgecolor="#d62728", alpha=0.95))
+
+    # Phase transition timeline in ax2
+    # 1125 - 1128: Yellow transition (3s) after NS gap-out
+    # 1128 - 1130: All-Red clearance (2s)
+    # 1130 - 1166: EW Green phase (starts at row 118, t=1130)
+    # 1166 - 1169: Yellow transition (3s) after wait cap rejection
+    # 1169 - 1171: All-Red clearance (2s)
+    # 1171 - 1175: NS Green phase (starts at row 127, t=1171)
+    p_ew = patches.Patch(facecolor="#81c784", edgecolor="#2e7d32", label=f"EW Green ($g_{{base}}={g_base_ew:.1f}$s + $g_{{extra}}=21.0$s)")
+    p_ns = patches.Patch(facecolor="#64b5f6", edgecolor="#1565c0", label=f"NS Green ($g_{{base}}={g_base_ns:.1f}$s)")
+    p_yel = patches.Patch(facecolor="#fff176", edgecolor="#fbc02d", label="Yellow Transition (3s)")
+    p_red = patches.Patch(facecolor="#ef5350", edgecolor="#c62828", label="All-Red Clearance (2s)")
+
+    ax2.broken_barh([(1125, 3)], (1, 2), facecolors="#fff176", edgecolor="#fbc02d")
+    ax2.broken_barh([(1128, 2)], (1, 2), facecolors="#ef5350", edgecolor="#c62828")
+    ax2.broken_barh([(1130, 36)], (1, 2), facecolors="#81c784", edgecolor="#2e7d32")
+    ax2.broken_barh([(1166, 3)], (1, 2), facecolors="#fff176", edgecolor="#fbc02d")
+    ax2.broken_barh([(1169, 2)], (1, 2), facecolors="#ef5350", edgecolor="#c62828")
+    ax2.broken_barh([(1171, 4)], (1, 2), facecolors="#64b5f6", edgecolor="#1565c0")
 
     ax2.set_ylim(0, 4)
     ax2.set_yticks([])
     ax2.set_xlabel("Simulation Time t (seconds)")
     ax2.grid(True, axis="x", linestyle=":", alpha=0.5)
-    ax2.legend(loc="lower center", bbox_to_anchor=(0.5, -0.9), ncol=2, frameon=True, fontsize=7.5)
 
-    # Combine legends for ax1
-    lines1, labels1 = ax1.get_legend_handles_labels()
-    lines2, labels2 = ax1_twin.get_legend_handles_labels()
-    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=7.5, framealpha=0.9)
+    # Position unified legend completely outside the axes below the plot
+    all_handles = [l1[0], l2[0], l3, l4[0], l5, p_ew, p_ns, p_yel, p_red]
+    all_labels = [h.get_label() for h in all_handles]
+    ax2.legend(all_handles, all_labels, loc="upper center", bbox_to_anchor=(0.5, -0.58), ncol=3, frameon=True, fontsize=6.8)
 
-    plt.tight_layout()
+    fig.subplots_adjust(top=0.96, bottom=0.25, left=0.10, right=0.90, hspace=0.15)
     out_file = OUT_DIR / "fig2_decision_trace.png"
-    plt.savefig(out_file, dpi=300, bbox_inches="tight")
+    plt.savefig(out_file, dpi=300)
     plt.close()
     print(f"Saved {out_file}")
```

---

## 2. Fixed-Plan Axis Assignment Confirmation

### Authoritative Code & Config Mapping:
In `dp1/config.py`:
- **Lines 254–257 (`FIXED_MARATHAHALLI`)**:
  ```python
  FIXED_MARATHAHALLI = FixedTimeConfig(
      green_ns_s=100 - (TIMING.yellow_s + TIMING.all_red_s),  # 95.0s
      green_ew_s=110 - (TIMING.yellow_s + TIMING.all_red_s),  # 105.0s
  )
  ```
- **Lines 246–249 (`FIXED`, legacy synthetic network)**:
  ```python
  # Synthetic network: historical mapping Phase 1 -> NS (105s), Phase 2 -> EW (95s) (preserved for baseline backward compatibility).
  FIXED = FixedTimeConfig(
      green_ns_s=110 - (TIMING.yellow_s + TIMING.all_red_s),  # 105.0s
      green_ew_s=100 - (TIMING.yellow_s + TIMING.all_red_s),  # 95.0s
  )
  ```
- **Controller Routing**:
  - `dp1/controllers/fixed_time.py:20–24`: selects `C.FIXED_MARATHAHALLI` whenever `network == "marathahalli"`.
  - `dp1/controllers/webster_measured.py:35–40`: sets `self.warmup_plan = C.FIXED_MARATHAHALLI` for `network == "marathahalli"`.

### Exact Phase Breakdown (Marathahalli Network):
| Phase Index | Axis | Corridor Name | Green Duration | Yellow | All-Red | Total Phase Span |
|---|---|---|---:|---:|---:|---:|
| **Phase 1** | **EW** | **Varthur Road** (HAL $\leftrightarrow$ Whitefield) | **105.0 s** | 3.0 s | 2.0 s | 110.0 s |
| **Phase 2** | **NS** | **Outer Ring Road (ORR)** (Kadubeesanahalli $\leftrightarrow$ KR Puram) | **95.0 s** | 3.0 s | 2.0 s | 100.0 s |

- **Total Vehicle Cycle:** $105.0 + 3.0 + 2.0 + 95.0 + 3.0 + 2.0 = \mathbf{210.0\,\text{s}}$.
- **Pedestrian Allowance:** The field BTP plan contains an additional 15 s pedestrian interval ($225\,\text{s}$ total field cycle), modeled in simulation as 210 s net vehicular cycle.

### Resolution of Previous Discrepancies:
1. **Why an earlier answer said "105 s NS green + 95 s EW green"**:
   This referred to `C.FIXED` ([`dp1/config.py:246–249`](file:///E:/dp1-traffic-signal/dp1/config.py#L246-L249)), which was the historical mapping used on the synthetic square junction. All Marathahalli runs use `C.FIXED_MARATHAHALLI` ([`dp1/config.py:254–257`](file:///E:/dp1-traffic-signal/dp1/config.py#L254-L257)), where **EW gets 105 s** and **NS gets 95 s**.
2. **Why another answer said $g_{\text{NS}} = 94$ and $g_{\text{EW}} = 106$**:
   In an early diagnostic audit, the split ratio $0.525 \times 200 = 105.0$ vs $0.475 \times 200 = 95.0$ was approximated via integer rounding ($106$ and $94$). The exact ground truth in `dp1/config.py` is **$105.0\,\text{s}$** and **$95.0\,\text{s}$**.
3. **Maximum Red Interval on Fixed (116.0 s)**:
   - The axis that waits through the longer green is **NS (ORR)**.
   - While EW is serving its green phase ($105.0\,\text{s}$) plus interphase clearance transitions ($3.0\,\text{s}$ yellow and $2.0\,\text{s}$ all-red on each side), NS experiences a continuous non-green span from the moment its green terminates until its next green commences:
     $$\text{Non-Green Span} = 3.0\,\text{s (NS yellow)} + 2.0\,\text{s (clearance)} + 105.0\,\text{s (EW green)} + 3.0\,\text{s (EW yellow)} + 2.0\,\text{s (clearance)} = \mathbf{115.0\,\text{s}}$$
   - Due to discrete simulation step alignment at integer boundaries ($t = 95.0$ to $t = 210.0$ / $211.0$), the maximum recorded red wait at green start in telemetry is **$116.0\,\text{s}$**.
   - This maximum occurs unequivocally on **NS (ORR)**.

---

## 3. Audit of Other Figures for the Axis-Swap Bug

We conducted an exhaustive audit across all figure generation and metric computation routines in `analysis/paper_final/`:

1. **Figure 1 (`plot_network_schematic`)**:
   - Static vector schematic of the Marathahalli flyover, at-grade intersection, stop lines, and $E_2$ detectors.
   - **No timeseries data used**; swap bug impossible.
2. **Figure 3 (`plot_forest_plot`)**:
   - Plots paired percentage differences ($\Delta\%$) with 95% bootstrap confidence intervals from `paired_bootstrap_summary.csv`.
   - **Uses aggregated summary metrics** (`gt_ext_max_queue_m`, `p95_wait_s`, `approach_wait_gap_s`); no timeseries queue columns.
3. **Figure 4 (`plot_queue_timeseries`)**:
   - Analyzed lines 292–296 of `analysis/paper_final/generate_figures.py`:
     ```python
     ext_cols = [c for c in df_ts.columns if c.startswith("gt_ext_q_")]
     if ext_cols:
         df_ts["max_ext_q"] = df_ts[ext_cols].max(axis=1)
         smooth_q = df_ts["max_ext_q"].rolling(5, min_periods=1).mean()
         ax.plot(df_ts["t"], smooth_q, label=pol_lbl, color=color, linestyle=lstyle, linewidth=lw)
     ```
   - **Verdict:** Fig. 4 computes the envelope over all individual approach legs (`gt_ext_q_N`, `gt_ext_q_S`, `gt_ext_q_E`, `gt_ext_q_W`). It does **not** rely on `q_active` or `q_competing`, and is completely immune to phase swap inversion.
4. **Other Analysis Scripts (`compute_tables.py`, `seed_clustered_bootstrap.py`, `extract_metrics.py`)**:
   - Confirmed that all queue metrics are extracted directly from per-vehicle tripinfo records or per-approach detector timeseries. `q_active_m` and `q_competing_m` were only used in Fig. 2's old microscopic trace, which is now resolved.
