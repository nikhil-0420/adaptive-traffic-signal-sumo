"""Generate results/report.md from simulation CSV data.

Reads metrics dynamically from results/all_runs.csv, formats comparison tables
(mean +/- std and % change vs fixed baseline), embeds plot references, records
the five limitations from docs/SPEC.md section 9, and documents exact seeds and
configuration values used.
"""
from pathlib import Path
from typing import Optional
import pandas as pd

from . import config as C


def _format_metric_table(
    df: pd.DataFrame,
    metric_col: str,
    metric_name: str,
    unit: str,
    lower_is_better: bool = True,
) -> str:
    """Build a markdown table comparing fixed vs each policy for a given metric."""
    scenarios = list(df["scenario"].unique())
    all_pols = list(df["policy"].unique())
    comp_pols = [p for p in ("adaptive", "pressure", "fixed_webster") if p in all_pols and p != "fixed"]
    for p in all_pols:
        if p != "fixed" and p not in comp_pols:
            comp_pols.append(p)

    has_fixed = "fixed" in all_pols
    stats = df.groupby(["scenario", "policy"])[metric_col].agg(["mean", "std"])

    # Header
    headers = ["Scenario"]
    if has_fixed:
        headers.append(f"Fixed ({unit})")
    for p in comp_pols:
        headers.append(f"{p.capitalize()} ({unit})")
        if has_fixed:
            headers.append(f"{p.capitalize()} vs Fixed (%)")

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join([":---"] + [":---:"] * (len(headers) - 1)) + " |")

    for scen in scenarios:
        row = [f"**{scen}**"]
        fx_mean = None
        if has_fixed:
            try:
                fx_mean = stats.loc[(scen, "fixed"), "mean"]
                fx_std = stats.loc[(scen, "fixed"), "std"]
                fx_std_val = 0.0 if pd.isna(fx_std) else fx_std
                row.append(f"{fx_mean:.2f} ± {fx_std_val:.2f}")
            except KeyError:
                row.append("N/A")

        for p in comp_pols:
            try:
                p_mean = stats.loc[(scen, p), "mean"]
                p_std = stats.loc[(scen, p), "std"]
                p_std_val = 0.0 if pd.isna(p_std) else p_std
                row.append(f"{p_mean:.2f} ± {p_std_val:.2f}")

                if has_fixed and fx_mean is not None and fx_mean > 0:
                    if lower_is_better:
                        # Negative means lower (better) for wait/queue
                        pct = (p_mean - fx_mean) / fx_mean * 100.0
                    else:
                        # Positive means higher (better) for throughput
                        pct = (p_mean - fx_mean) / fx_mean * 100.0
                    row.append(f"{pct:+.1f}%")
                elif has_fixed:
                    row.append("N/A")
            except KeyError:
                row.append("N/A")
                if has_fixed:
                    row.append("N/A")

        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def generate_report(
    csv_file: Optional[Path] = None,
    out_file: Optional[Path] = None,
) -> Path:
    """Read CSV results and generate the comprehensive markdown report."""
    csv_path = Path(csv_file) if csv_file else C.RESULTS_DIR / "all_runs.csv"
    out_path = Path(out_file) if out_file else C.RESULTS_DIR / "report.md"

    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found at {csv_path}. Run 'python -m dp1.cli compare' first.")

    df = pd.read_csv(csv_path)
    seeds = sorted(df["seed"].unique().tolist())
    scenarios = list(df["scenario"].unique())
    policies = list(df["policy"].unique())

    # Build markdown sections
    doc = []
    doc.append("# DP1 Simulation Experiment Report: Adaptive Traffic Signal Optimisation\n")
    doc.append(
        "This report is generated dynamically from simulation run results (`results/all_runs.csv`). "
        "It provides a rigorous, fair comparison across traffic demand scenarios between the fixed-time "
        "baseline and adaptive signal control policies.\n"
    )

    # 1. Performance Comparison Tables
    doc.append("## 1. Experimental Results & Scenario Comparison\n")

    doc.append("### 1.1 Average Waiting Time per Vehicle (s)\n")
    doc.append("*Lower is better. Values represent Mean ± Standard Deviation over all evaluated seeds.*\n")
    doc.append(_format_metric_table(df, "avg_wait_s", "Average Waiting Time", "s", lower_is_better=True))
    doc.append("\n")

    doc.append("### 1.2 Average Queue Length (m)\n")
    doc.append("*Lower is better. Jam length measured back from the stop line by lane-area detectors.*\n")
    doc.append(_format_metric_table(df, "avg_queue_m", "Average Queue Length", "m", lower_is_better=True))
    doc.append("\n")

    doc.append("### 1.3 System Throughput (veh/h)\n")
    doc.append("*Higher is better. Completed vehicles per hour during the evaluation window.*\n")
    doc.append(_format_metric_table(df, "throughput_veh_per_h", "Throughput", "veh/h", lower_is_better=False))
    doc.append("\n")

    # 2. Performance Visualizations
    doc.append("## 2. Performance Visualizations\n")
    doc.append("Comparative charts generated from the experiment matrix:\n")
    doc.append("![Average Waiting Time per Vehicle](wait_time.png)\n")
    doc.append("*Figure 1: Average waiting time per vehicle (s) by scenario and policy.*\n")
    doc.append("![Average Queue Length](queue_length.png)\n")
    doc.append("*Figure 2: Average queue length (m) by scenario and policy.*\n")

    ts_plot = C.RESULTS_DIR / "queue_timeseries.png"
    if ts_plot.exists():
        doc.append("![Queue Dynamics Timeseries](queue_timeseries.png)\n")
        doc.append("*Figure 3: Queue length timeseries comparison across approaches.*\n")

    # 3. Known Limitations (docs/SPEC.md Section 9)
    doc.append("## 3. Known Limitations (docs/SPEC.md Section 9)\n")
    doc.append(
        "As explicitly documented in `docs/SPEC.md` section 9, the following limitations govern this phase of the study:\n"
    )
    doc.append(
        "1. **Approach Lane Geometry**: Simulated 4-way cross junction with synthetic 2-lane approaches, "
        "without dedicated turn bays or real-world lane tapers.\n"
        "2. **Detector Sensing Cap**: Lane-area detectors cover 150 m before the stop line; queues spilling "
        "beyond 150 m saturate sensor jam readings.\n"
        "3. **No Pedestrian Modelling**: Pedestrian crossing phases are omitted (e.g., the 15 s exclusive pedestrian "
        "phase present in the BTP Marathalli plan is excluded from the modelled cycle).\n"
        "4. **Simple Two-Phase Plan**: Traffic signal operates two alternating phases (NS and EW) with permissive turning "
        "rather than multi-phase protected right-turns.\n"
        "5. **Simulator vs Field Telemetry**: All sensor measurements and driver behaviours originate from SUMO micro-simulation, "
        "not real-world street cameras or loop detector feeds.\n"
    )

    # 4. Experimental Setup, Exact Seeds & Configuration Values
    doc.append("## 4. Experimental Setup & Configuration Values\n")
    doc.append(f"- **Evaluated Seeds**: `{seeds}` ({len(seeds)} random seeds)")
    doc.append(f"- **Demand Scenarios Evaluated**: `{scenarios}`")
    doc.append(f"- **Policies Evaluated**: `{policies}`")
    doc.append(f"- **Demand Duration**: `{C.SIM.demand_duration_s} s` (Drain cap: `{C.SIM.max_sim_time_s} s`)")
    doc.append(f"- **Demand Scale Factor**: `{C.DEMAND_SCALE}`\n")

    doc.append("### Signal Timing & Invariant Clearances (`dp1.config.TIMING`)")
    doc.append(f"- Yellow Duration: `{C.TIMING.yellow_s} s`")
    doc.append(f"- All-Red Clearance: `{C.TIMING.all_red_s} s` (enforces strict Green -> Yellow -> All-Red -> Green invariant)\n")

    doc.append("### Baseline Fixed-Time Controller (`dp1.config.FIXED`)")
    doc.append("- Calibrated from BTP Marathalli Bridge Junction (Varthur Rd x ORR, weekday 08:00-11:30)")
    doc.append(f"- NS Green: `{C.FIXED.green_ns_s} s`")
    doc.append(f"- EW Green: `{C.FIXED.green_ew_s} s`")
    doc.append(
        f"- Modelled Cycle: `{C.FIXED.green_ns_s + C.FIXED.green_ew_s + 2 * (C.TIMING.yellow_s + C.TIMING.all_red_s)} s`\n"
    )

    doc.append("### Adaptive Queue Controller (`dp1.config.ADAPTIVE`)")
    doc.append(f"- Min Green: `{C.ADAPTIVE.min_green_s} s` | Max Green: `{C.ADAPTIVE.max_green_s} s`")
    doc.append(f"- Queue Scaling factor (`k_s_per_m`): `{C.ADAPTIVE.k_s_per_m} s/m`")
    doc.append(f"- Gap-out duration: `{C.ADAPTIVE.gap_out_s} s`")
    doc.append(f"- Extend threshold: `{C.ADAPTIVE.extend_threshold_m} m`")
    doc.append(f"- Competing queue threshold: `{C.ADAPTIVE.min_competing_queue_m} m`\n")

    doc.append("### Adaptive Pressure Controller (`dp1.config.PRESSURE`)")
    doc.append(f"- Min Green: `{C.PRESSURE.min_green_s} s` | Max Green: `{C.PRESSURE.max_green_s} s`")
    doc.append(f"- Pressure Queue Differential factor (`k_s_per_m`): `{C.PRESSURE.k_s_per_m} s/m`")
    doc.append(f"- Gap-out duration: `{C.PRESSURE.gap_out_s} s`")
    doc.append(f"- Extend threshold: `{C.PRESSURE.extend_threshold_m} m`")
    doc.append(f"- Competing queue threshold: `{C.PRESSURE.min_competing_queue_m} m`\n")

    doc.append("### Network Geometry (`dp1.config.NET`)")
    doc.append(f"- Lanes per approach: `{C.NET.lanes}`")
    doc.append(f"- Approach length: `{C.NET.approach_length_m} m`")
    doc.append(f"- Detector length: `{C.NET.detector_length_m} m`")
    doc.append(f"- Speed limit: `{C.NET.speed_mps} m/s` (50 km/h)\n")

    content = "\n".join(doc)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate results/report.md from CSV data")
    parser.add_argument("--csv", type=str, default=None, help="path to all_runs.csv")
    parser.add_argument("--out", type=str, default=None, help="output markdown file path")
    args = parser.parse_args()

    out = generate_report(args.csv, args.out)
    print(f"Report generated successfully: {out}")


if __name__ == "__main__":
    main()
