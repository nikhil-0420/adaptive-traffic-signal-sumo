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
    pdf: bool = False,
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

    if pdf:
        pdf_out = out_path.with_suffix(".pdf")
        export_pdf(md_path=out_path, out_pdf=pdf_out)

    return out_path


def find_headless_browser() -> Optional[str]:
    """Locate an available Chromium-based browser (Chrome or Edge) for headless PDF export."""
    import shutil
    import os

    # 1. Check environment overrides
    env_bin = os.environ.get("CHROME_BIN") or os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if env_bin and Path(env_bin).exists():
        return env_bin

    # 2. Check PATH
    for name in ["chrome", "google-chrome", "chromium", "chromium-browser", "msedge"]:
        path = shutil.which(name)
        if path:
            return path

    # 3. Check well-known OS install locations
    candidate_paths = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for cp in candidate_paths:
        if os.path.exists(cp):
            return cp

    return None


def export_pdf(md_path: Optional[Path | str] = None, out_pdf: Optional[Path | str] = None) -> Path:
    """Compile markdown report to an executive, publication-grade PDF using headless Chrome/Edge."""
    import base64
    import re
    import subprocess

    md_file = Path(md_path) if md_path else C.RESULTS_DIR / "report.md"
    pdf_file = Path(out_pdf) if out_pdf else md_file.with_suffix(".pdf")
    html_file = md_file.with_suffix(".html")
    img_dir = md_file.parent

    if not md_file.exists():
        raise FileNotFoundError(f"Markdown report not found at {md_file}")

    browser_exe = find_headless_browser()
    if not browser_exe:
        raise RuntimeError("No supported Chromium browser (Chrome or Edge) found for PDF export.")

    md_text = md_file.read_text(encoding="utf-8")

    # Encode images as base64 data URIs for portable, self-contained rendering
    img_data = {}
    for img_name in ["wait_time.png", "queue_length.png", "queue_timeseries.png"]:
        p = img_dir / img_name
        if p.exists():
            encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
            img_data[img_name] = f"data:image/png;base64,{encoded}"

    def _format_cell(val: str, ctx: str) -> str:
        val = val.strip()
        if not val:
            return ""
        if "%" in val:
            if "-" in val:
                cls = "badge-green" if "Throughput" not in ctx else "badge-red"
            elif "+" in val:
                cls = "badge-green" if "Throughput" in ctx else "badge-blue"
            else:
                cls = "badge-neutral"
            return f'<span class="badge {cls}">{val}</span>'
        if "±" in val:
            parts = val.split("±")
            return f'<span class="stat-main">{parts[0].strip()}</span><span class="stat-std"> ± {parts[1].strip()}</span>'
        return val

    def _table_to_html(tbl_lines: list[str], ctx: str = "") -> str:
        if len(tbl_lines) < 2:
            return ""
        headers = [h.strip() for h in tbl_lines[0].strip("| \n").split("|")]
        h_html = ['<div class="table-container"><table><thead><tr>']
        for h in headers:
            align = "text-left" if h.lower() == "scenario" else "text-center"
            h_html.append(f'<th class="{align}">{h}</th>')
        h_html.append("</tr></thead><tbody>")
        for row in tbl_lines[2:]:
            row_s = row.strip("| \n")
            if not row_s:
                continue
            cells = [c.strip() for c in row_s.split("|")]
            h_html.append("<tr>")
            for idx, c in enumerate(cells):
                clean_c = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", c)
                align = "text-left font-semibold" if idx == 0 else "text-center font-mono"
                h_html.append(f'<td class="{align}">{_format_cell(clean_c, ctx)}</td>')
            h_html.append("</tr>")
        h_html.append("</tbody></table></div>")
        return "\n".join(h_html)

    # Extract tables
    tables = []
    cur_t = []
    for line in md_text.splitlines():
        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            cur_t.append(line)
        else:
            if cur_t:
                tables.append(list(cur_t))
                cur_t = []
    if cur_t:
        tables.append(list(cur_t))

    t1_html = _table_to_html(tables[0], "Waiting Time") if len(tables) > 0 else ""
    t2_html = _table_to_html(tables[1], "Queue Length") if len(tables) > 1 else ""
    t3_html = _table_to_html(tables[2], "Throughput") if len(tables) > 2 else ""

    limitations = [
        ("L1", "Approach Lane Geometry", "Simulated 4-way cross junction with synthetic 2-lane approaches, without dedicated turn bays or real-world lane tapers."),
        ("L2", "Detector Sensing Cap", "Lane-area detectors cover 150 m before the stop line; queues spilling beyond 150 m saturate sensor jam readings."),
        ("L3", "No Pedestrian Modelling", "Pedestrian crossing phases are omitted (e.g., the 15 s exclusive pedestrian phase present in the BTP Marathalli plan is excluded from the modelled cycle)."),
        ("L4", "Simple Two-Phase Plan", "Traffic signal operates two alternating phases (NS and EW) with permissive turning rather than multi-phase protected right-turns."),
        ("L5", "Simulator vs Field Telemetry", "All sensor measurements and driver behaviours originate from SUMO micro-simulation, not real-world street cameras or loop detector feeds."),
    ]
    lim_html = "\n".join([
        f'<div class="limitation-card"><div class="lim-badge">{code}</div><div class="lim-body"><div class="lim-title">{title}</div><div class="lim-desc">{desc}</div></div></div>'
        for code, title, desc in limitations
    ])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DP1 Simulation Experiment Report</title>
<style>
@page {{
    size: A4 portrait;
    margin: 12mm 14mm 12mm 14mm;
    @bottom-center {{
        content: "Alliance University • Department of AI & Data Science • DP1 Report";
        font-size: 7.5pt;
        color: #94a3b8;
    }}
}}
*, *:before, *:after {{ box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #0f172a;
    background: #ffffff;
    line-height: 1.35;
    font-size: 8.5pt;
    margin: 0; padding: 0;
}}
.page {{ page-break-after: always; break-after: page; }}
.page:last-child {{ page-break-after: avoid; break-after: avoid; }}
.report-header {{ border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 10px; }}
.university-bar {{
    display: flex; justify-content: space-between; align-items: center;
    font-size: 8pt; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
    color: #475569; margin-bottom: 4px; border-bottom: 1px solid #e2e8f0; padding-bottom: 3px;
}}
.report-title {{ font-size: 17pt; font-weight: 800; color: #0f172a; margin: 0 0 2px 0; letter-spacing: -0.02em; line-height: 1.2; }}
.report-subtitle {{ font-size: 9.5pt; color: #475569; margin: 0 0 6px 0; font-weight: 500; }}
.badge-row {{ display: flex; flex-wrap: wrap; gap: 5px; }}
.meta-pill {{
    display: inline-block; font-size: 7pt; font-weight: 600; padding: 2px 6px; border-radius: 4px;
    background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;
}}
.meta-pill.accent {{ background: #e0f2fe; color: #0369a1; border-color: #bae6fd; }}
.meta-pill.success {{ background: #dcfce7; color: #15803d; border-color: #bbf7d0; }}
h2.section-title {{
    font-size: 11pt; font-weight: 700; color: #0f172a; border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 3px; margin-top: 10px; margin-bottom: 6px; letter-spacing: -0.01em;
}}
h3.subsection-title {{ font-size: 9pt; font-weight: 700; color: #1e293b; margin-top: 8px; margin-bottom: 2px; }}
p.intro-text {{ margin: 0 0 6px 0; color: #475569; font-size: 8pt; }}
.table-note {{ font-size: 7.5pt; color: #64748b; font-style: italic; margin-bottom: 4px; }}
.table-container {{ margin-bottom: 8px; }}
table {{
    width: 100%; border-collapse: collapse; font-size: 7.5pt; background: #ffffff;
    border: 1px solid #cbd5e1; border-radius: 4px; overflow: hidden;
}}
thead tr {{ background: #0f172a; color: #ffffff; }}
th {{ padding: 5px 6px; font-weight: 600; font-size: 7pt; text-transform: uppercase; letter-spacing: 0.02em; border-right: 1px solid #334155; }}
th:last-child {{ border-right: none; }}
td {{ padding: 4px 6px; border-top: 1px solid #e2e8f0; border-right: 1px solid #f1f5f9; }}
td:last-child {{ border-right: none; }}
tbody tr:nth-child(even) {{ background-color: #f8fafc; }}
.text-left {{ text-align: left; }}
.text-center {{ text-align: center; }}
.font-semibold {{ font-weight: 600; color: #0f172a; }}
.font-mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
.stat-main {{ font-weight: 600; color: #0f172a; }}
.stat-std {{ font-size: 6.8pt; color: #64748b; }}
.badge {{ display: inline-block; padding: 1px 4px; border-radius: 3px; font-weight: 700; font-size: 7pt; }}
.badge-green {{ background: #dcfce7; color: #15803d; }}
.badge-blue {{ background: #e0f2fe; color: #0369a1; }}
.badge-red {{ background: #fee2e2; color: #b91c1c; }}
.badge-neutral {{ background: #f1f5f9; color: #475569; }}
.figures-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
.figure-box {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px; background: #ffffff; text-align: center; }}
.figure-box.full-width {{ grid-column: span 2; }}
.figure-img {{ width: 100%; height: auto; display: block; border-radius: 3px; }}
.figure-caption {{ font-size: 7.2pt; color: #475569; font-weight: 600; margin-top: 4px; }}
.limitations-container {{ display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }}
.limitation-card {{ display: flex; align-items: flex-start; gap: 8px; background: #f8fafc; border-left: 3.5px solid #2563eb; border-radius: 0 4px 4px 0; padding: 6px 8px; }}
.lim-badge {{ background: #dbeafe; color: #1e40af; font-weight: 800; font-size: 7pt; padding: 2px 5px; border-radius: 3px; flex-shrink: 0; }}
.lim-title {{ font-weight: 700; font-size: 8pt; color: #0f172a; display: inline; }}
.lim-desc {{ font-size: 7.8pt; color: #334155; display: inline; }}
.config-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.config-card {{ border: 1px solid #e2e8f0; border-radius: 5px; padding: 7px 9px; background: #ffffff; }}
.config-card-header {{ font-size: 8pt; font-weight: 700; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 3px; margin-bottom: 5px; display: flex; justify-content: space-between; }}
.config-item {{ font-size: 7.5pt; color: #334155; margin-bottom: 2px; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 7.2pt; background: #f1f5f9; padding: 0 3px; border-radius: 2px; color: #0f172a; border: 1px solid #e2e8f0; }}
</style>
</head>
<body>

<!-- PAGE 1: Experimental Tables -->
<div class="page">
    <div class="report-header">
        <div class="university-bar">
            <span>Alliance University • Department of Artificial Intelligence & Data Science</span>
            <span>B.Tech AI & DS • Design Project 1</span>
        </div>
        <h1 class="report-title">Adaptive Traffic Signal Optimisation</h1>
        <div class="report-subtitle">Simulation Experiment Report: Multi-Policy Evaluation vs BTP Fixed-Time Baseline</div>
        <div class="badge-row">
            <span class="meta-pill accent">Simulator: SUMO v1.28.0 + TraCI</span>
            <span class="meta-pill success">Baseline: BTP Marathahalli Bridge (210s)</span>
            <span class="meta-pill">Policies: Fixed, Webster, Adaptive, Pressure</span>
            <span class="meta-pill">Evaluated Seeds: 1–5 & Held-Out 11–15</span>
            <span class="meta-pill">Scale: 1.7× Demand</span>
        </div>
    </div>
    <p class="intro-text">This report is generated dynamically from simulation run results (<code>results/all_runs.csv</code>). It provides a rigorous, fair comparison across traffic demand scenarios between the fixed-time baseline and adaptive signal control policies.</p>
    <h2 class="section-title">1. Experimental Results & Scenario Comparison</h2>
    <h3 class="subsection-title">1.1 Average Waiting Time per Vehicle (s)</h3>
    <div class="table-note">Lower is better. Values represent Mean ± Standard Deviation over all evaluated seeds.</div>
    {t1_html}
    <h3 class="subsection-title">1.2 Average Queue Length (m)</h3>
    <div class="table-note">Lower is better. Jam length measured back from the stop line by lane-area detectors.</div>
    {t2_html}
    <h3 class="subsection-title">1.3 System Throughput (veh/h)</h3>
    <div class="table-note">Higher is better. Completed vehicles per hour during the evaluation window.</div>
    {t3_html}
</div>

<!-- PAGE 2: Performance Visualizations -->
<div class="page">
    <div class="university-bar">
        <span>Alliance University • Department of Artificial Intelligence & Data Science</span>
        <span>DP1 Simulation Report • Section 2: Visualizations</span>
    </div>
    <h2 class="section-title" style="margin-top: 6px;">2. Performance Visualizations</h2>
    <p class="intro-text">Comparative performance charts generated dynamically across all demand scenarios and control policies:</p>
    <div class="figures-grid">
        <div class="figure-box">
            <img src="{img_data.get('wait_time.png', '')}" class="figure-img" alt="Average Waiting Time" />
            <div class="figure-caption">Figure 1: Average Waiting Time per Vehicle (s) by Scenario and Policy</div>
        </div>
        <div class="figure-box">
            <img src="{img_data.get('queue_length.png', '')}" class="figure-img" alt="Average Queue Length" />
            <div class="figure-caption">Figure 2: Average Queue Length (m) by Scenario and Policy</div>
        </div>
        <div class="figure-box full-width" style="margin-top: 4px;">
            <img src="{img_data.get('queue_timeseries.png', '')}" class="figure-img" style="max-height: 240px; object-fit: contain;" alt="Queue Timeseries" />
            <div class="figure-caption">Figure 3: Queue Length Dynamics Timeseries Comparison across Approaches (Fixed vs Adaptive)</div>
        </div>
    </div>
</div>

<!-- PAGE 3: Limitations & Experimental Configuration -->
<div class="page">
    <div class="university-bar">
        <span>Alliance University • Department of Artificial Intelligence & Data Science</span>
        <span>DP1 Simulation Report • Section 3 & 4: Methodology & Settings</span>
    </div>
    <h2 class="section-title" style="margin-top: 6px;">3. Known Limitations (docs/SPEC.md Section 9)</h2>
    <p class="intro-text">As explicitly documented in <code>docs/SPEC.md</code> section 9, the following limitations govern this phase of the study:</p>
    <div class="limitations-container">
        {lim_html}
    </div>
    <h2 class="section-title" style="margin-top: 10px;">4. Experimental Setup & Configuration Values</h2>
    <div style="margin-bottom: 8px; font-size: 7.5pt; color: #475569;">
        <strong>Evaluated Seeds:</strong> <code>[1, 2, 3, 4, 5]</code> &nbsp;|&nbsp; 
        <strong>Demand Scenarios:</strong> <code>['balanced', 'imbalanced_ns', 'imbalanced_ew', 'surge_north']</code> &nbsp;|&nbsp; 
        <strong>Policies:</strong> <code>['fixed', 'fixed_webster', 'adaptive', 'pressure']</code> &nbsp;|&nbsp; 
        <strong>Duration:</strong> <code>1800 s</code> (Drain: <code>3600 s</code>) &nbsp;|&nbsp; 
        <strong>Scale:</strong> <code>1.7</code>
    </div>
    <div class="config-grid">
        <div class="config-card">
            <div class="config-card-header">
                <span>Signal Timing & Clearance Invariants</span>
                <code>dp1.config.TIMING</code>
            </div>
            <div class="config-item">• Yellow Duration: <code>3 s</code></div>
            <div class="config-item">• All-Red Clearance: <code>2 s</code></div>
            <div class="config-item">• Safety Invariant: Strict <code>Green &rarr; Yellow &rarr; All-Red &rarr; Green</code></div>
        </div>
        <div class="config-card">
            <div class="config-card-header">
                <span>Baseline Fixed-Time Controller</span>
                <code>dp1.config.FIXED</code>
            </div>
            <div class="config-item">• Calibration: BTP Marathahalli Bridge (Varthur x ORR)</div>
            <div class="config-item">• NS Green: <code>105 s</code> | EW Green: <code>95 s</code></div>
            <div class="config-item">• Modelled Cycle: <code>210 s</code> (Phase 1: 110s, Phase 2: 100s)</div>
        </div>
        <div class="config-card">
            <div class="config-card-header">
                <span>Adaptive Queue Controller</span>
                <code>dp1.config.ADAPTIVE</code>
            </div>
            <div class="config-item">• Green Bounds: <code>10 s</code> min &le; green &le; <code>60 s</code> max</div>
            <div class="config-item">• Queue Scaling factor (<code>k_s_per_m</code>): <code>0.3 s/m</code></div>
            <div class="config-item">• Gap-out Duration: <code>3 s</code></div>
            <div class="config-item">• Extend / Competing Queue Thresholds: <code>15.0 m</code> / <code>1.0 m</code></div>
        </div>
        <div class="config-card">
            <div class="config-card-header">
                <span>Adaptive Pressure Controller</span>
                <code>dp1.config.PRESSURE</code>
            </div>
            <div class="config-item">• Green Bounds: <code>10 s</code> min &le; green &le; <code>60 s</code> max</div>
            <div class="config-item">• Queue Difference factor (<code>k_s_per_m</code>): <code>0.3 s/m</code></div>
            <div class="config-item">• Gap-out Duration: <code>3 s</code></div>
            <div class="config-item">• Extend / Competing Queue Thresholds: <code>15.0 m</code> / <code>1.0 m</code></div>
        </div>
        <div class="config-card" style="grid-column: span 2;">
            <div class="config-card-header">
                <span>Network Geometry & Webster Plan Configuration</span>
                <code>dp1.config.NET & WEBSTER</code>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div class="config-item">• Lanes per approach: <code>2</code> (Lane 0: Right+Through, Lane 1: Left+Through)</div>
                    <div class="config-item">• Approach / Detector length: <code>300.0 m</code> / <code>150.0 m</code></div>
                </div>
                <div>
                    <div class="config-item">• Speed limit: <code>13.89 m/s</code> (50 km/h)</div>
                    <div class="config-item">• Webster saturation flow: <code>1800 veh/h/lane</code> (cycle clamped 40–120s)</div>
                </div>
            </div>
        </div>
    </div>
</div>

</body>
</html>
"""

    html_file.write_text(html_content, encoding="utf-8")

    cmd = [
        browser_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_file}",
        str(html_file),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not pdf_file.exists():
        raise RuntimeError(f"Browser PDF printing failed: {res.stderr}")

    return pdf_file


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate results/report.md from CSV data")
    parser.add_argument("--csv", type=str, default=None, help="path to all_runs.csv")
    parser.add_argument("--out", type=str, default=None, help="output markdown file path")
    parser.add_argument("--pdf", action="store_true", help="compile markdown report to PDF")
    args = parser.parse_args()

    out = generate_report(args.csv, args.out, pdf=args.pdf)
    print(f"Report generated successfully: {out}")
    if args.pdf:
        print(f"PDF compiled successfully: {out.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
