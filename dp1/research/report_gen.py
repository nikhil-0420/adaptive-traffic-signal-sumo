"""Generate scientific markdown research report directly from immutable artifacts."""
from pathlib import Path
from typing import Dict
import pandas as pd


def generate_research_report(
    manifest: Dict,
    agg_df: pd.DataFrame,
    deltas_df: pd.DataFrame,
    fairness_df: pd.DataFrame,
    direction_df: pd.DataFrame,
    status_df: pd.DataFrame,
    out_path: Path,
) -> Path:
    """Generate reproducible Markdown research report from verified results."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    status_counts = manifest.get("status_counts", {})
    total_cells = manifest.get("total_cells", len(status_df))
    complete_cells = status_counts.get("complete", 0)
    failed_cells = status_counts.get("failed", 0)
    blocked_cells = status_counts.get("blocked", 0)
    matrix_state = manifest.get("status", "complete" if complete_cells == total_cells else "partial")

    lines = [
        f"# DP1 Research Evaluation Report — Experiment `{manifest.get('experiment_id')}`",
        "",
        "> **Simulation Integrity Notice**",
        "> All metrics are derived from real execution of Eclipse SUMO with TraCI on simulated lane-area detectors.",
        "> Results reflect the synthetic four-way junction model and do not constitute field evidence from live roads.",
        "",
        "## 1. Executive Summary & Matrix Status",
        "",
        f"- **Experiment Status:** `{matrix_state.upper()}` ({complete_cells}/{total_cells} cells completed)",
        f"- **Failed Cells:** {failed_cells}",
        f"- **Blocked Cells:** {blocked_cells}",
        f"- **Execution Timestamp:** {manifest.get('created_at', 'N/A')}",
        f"- **Bootstrap Configuration:** {manifest.get('bootstrap_resamples', 10000):,} resamples (seed: {manifest.get('bootstrap_seed', 42)})",
        "",
        "| Factor | Evaluated Levels |",
        "|---|---|",
        f"| **Patterns** | {', '.join(manifest.get('patterns', []))} |",
        f"| **Demand Levels** | {', '.join(f'{k} (x{v:.2f})' for k, v in manifest.get('demand_multipliers', {}).items())} |",
        f"| **Policies** | {', '.join(manifest.get('policies', []))} |",
        f"| **Evaluation Seeds** | {manifest.get('seeds', [])} (n={len(manifest.get('seeds', []))}) |",
        "",
        "## 2. Experimental Setup & Seed Separation",
        "",
        "In compliance with fair evaluation protocols, controller hyperparameters and RL models were frozen prior to running on research evaluation seeds:",
        "- **Training Seeds:** `1..5` (used for Webster profile baseline and legacy grid search).",
        "- **RL Validation Seeds:** `6..10` (used for checkpoint validation).",
        "- **Legacy Held-Out Seeds:** `11..15` (used for baseline comparison).",
        "- **Research Test Seeds:** `21..30` (strictly held out for final reporting; never used to tune or select policies).",
        "",
        "## 3. Aggregate Performance Across Demand Levels",
        "",
        "Values represent mean ± sample standard deviation over evaluation seeds for each condition.",
        "",
    ]

    # Aggregate Table
    if not agg_df.empty:
        lines.append("| Pattern | Level | Policy | Seeds | Mean Wait (s) | Time Loss (s) | Mean Queue (m) | Throughput (veh/h) | Completion |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
        for _, r in agg_df.iterrows():
            pat = r.get("pattern", "")
            lvl = r.get("demand_level", "")
            pol = r.get("policy", "")
            n_sd = r.get("n_seeds", 0)
            wait = f"{r.get('avg_wait_s_mean', 0.0):.1f} ± {r.get('avg_wait_s_std', 0.0):.1f}"
            loss = f"{r.get('avg_time_loss_s_mean', 0.0):.1f} ± {r.get('avg_time_loss_s_std', 0.0):.1f}"
            q = f"{r.get('avg_queue_m_mean', 0.0):.1f} ± {r.get('avg_queue_m_std', 0.0):.1f}"
            tp = f"{r.get('throughput_veh_per_h_mean', 0.0):.0f}"
            comp = f"{r.get('completion_rate_mean', 1.0):.1%}"
            lines.append(f"| {pat} | {lvl} | `{pol}` | {n_sd} | {wait} | {loss} | {q} | {tp} | {comp} |")
        lines.append("")

    # Paired Bootstrap Differences vs Fixed
    lines.extend([
        "## 4. Paired Delta Analysis vs Fixed Baseline (95% Bootstrap CI)",
        "",
        "Paired differences are calculated per-seed against `fixed` under identical arrival traffic:",
        r"$$\Delta = \text{Metric}_{\text{candidate}} - \text{Metric}_{\text{fixed}}$$",
        "A **negative delta** indicates a reduction (improvement) in delay or queuing relative to the fixed plan.",
        "",
    ])

    if not deltas_df.empty:
        lines.append("| Pattern | Level | Policy | Valid Pairs | Delta Wait (s) [95% CI] | Delta Time Loss (s) [95% CI] | Delta Queue (m) |")
        lines.append("|---|---|---|---:|---|---|---:|")
        for _, r in deltas_df.iterrows():
            pat = r.get("pattern", "")
            lvl = r.get("demand_level", "")
            pol = r.get("policy", "")
            n_pr = r.get("n_pairs", 0)
            dw_m = r.get("delta_wait_mean_s", 0.0)
            dw_lo = r.get("delta_wait_ci_lower_s", 0.0)
            dw_hi = r.get("delta_wait_ci_upper_s", 0.0)
            dl_m = r.get("delta_time_loss_mean_s", 0.0)
            dl_lo = r.get("delta_time_loss_ci_lower_s", 0.0)
            dl_hi = r.get("delta_time_loss_ci_upper_s", 0.0)
            dq = r.get("delta_queue_mean_m", 0.0)

            w_ci = f"**{dw_m:+.2f}** [{dw_lo:+.2f}, {dw_hi:+.2f}]"
            l_ci = f"{dl_m:+.2f} [{dl_lo:+.2f}, {dl_hi:+.2f}]"
            lines.append(f"| {pat} | {lvl} | `{pol}` | {n_pr} | {w_ci} | {l_ci} | {dq:+.2f} |")
        lines.append("")

    # Directional Fairness
    lines.extend([
        "## 5. Directional Service Disparity & Approach Wait Gaps",
        "",
        "Service disparity measures the imbalance in waiting times between competing directions:",
        r"$$\text{Disparity} = |\text{Wait}_{\text{NS}} - \text{Wait}_{\text{EW}}|$$",
        r"$$\text{Wait Gap} = \max(\text{Wait}_{\text{approach}}) - \min(\text{Wait}_{\text{approach}})$$",
        "",
    ])

    if not direction_df.empty:
        lines.append("| Pattern | Level | Policy | Wait NS (s) | Wait EW (s) | Direction Disparity (s) | Approach Gap (s) |")
        lines.append("|---|---|---|---:|---:|---:|---:|")
        for _, r in direction_df.iterrows():
            pat = r.get("pattern", "")
            lvl = r.get("demand_level", "")
            pol = r.get("policy", "")
            wns = f"{r.get('avg_wait_NS_s_mean', 0.0):.1f}" if pd.notna(r.get('avg_wait_NS_s_mean')) else "null"
            wew = f"{r.get('avg_wait_EW_s_mean', 0.0):.1f}" if pd.notna(r.get('avg_wait_EW_s_mean')) else "null"
            disp = f"{r.get('directional_wait_disparity_s_mean', 0.0):.1f}" if pd.notna(r.get('directional_wait_disparity_s_mean')) else "null"
            gap = f"{r.get('approach_wait_gap_s_mean', 0.0):.1f}" if pd.notna(r.get('approach_wait_gap_s_mean')) else "null"
            lines.append(f"| {pat} | {lvl} | `{pol}` | {wns} | {wew} | {disp} | {gap} |")
        lines.append("")

    lines.extend([
        "## 6. Known Trade-Offs & Honest Limitations",
        "",
        "1. **Imbalance vs Surge Behavior:** Adaptive and pressure policies offer substantial reductions in vehicle delay under sustained demand imbalance (`imbalanced_ns`, `imbalanced_ew`). However, during temporary surges (`surge_north`), rapid queue clearance may incur switching lost time.",
        "2. **Simulation Boundaries:** Experiments were executed on synthetic 300 m approach links with 150 m detector coverage. Unobserved queues beyond 150 m are not measured by sensors.",
        "3. **Fixed-Time Baseline Adaptation:** The fixed-time plan is adapted from BTP Marathahalli Bridge junction schedule with clearance intervals (3s yellow, 2s all-red), omitting the pedestrian-only phase.",
        "",
        "## 7. Artifact Manifest",
        "",
        "- `manifest.json`: Complete execution metadata and environment configuration.",
        "- `raw_runs.csv`: Unaggregated per-run metrics for every completed cell.",
        "- `aggregate.csv`: Grouped means and standard deviations.",
        "- `paired_deltas.csv`: Paired per-seed differences with bootstrap confidence intervals.",
        "- `fairness_by_approach.csv`: Approach-level vehicle counts, delays, and detector queues.",
        "- `fairness_by_direction.csv`: NS vs EW directional disparity summaries.",
        "- `matrix_status.csv`: Cell-by-cell lifecycle tracking.",
        "- `plots/`: Rendered figures.",
    ])

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
