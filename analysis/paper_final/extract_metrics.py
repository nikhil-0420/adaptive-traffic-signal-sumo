"""Extract complete verified metrics from raw simulation runs (Amendment 3).

Reads from results/research/exp_marathahalli_improve_final/ and produces
analysis/paper_final/raw_extracted_runs.csv with full operational metrics:
- Throughput (veh/h) correctly mapped from throughput_veh_per_h
- Switching frequency (switches/hour) computed from timeseries axis transitions
- Completion rate and unfinished vehicle counts
- Ground-truth extended queues and waiting time percentiles
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

EXP_DIR = Path("results/research/exp_marathahalli_improve_final")
OUTPUT_CSV = Path("analysis/paper_final/raw_extracted_runs.csv")

KNOWN_SCENARIOS = [
    "balanced",
    "imbalanced_orr",
    "imbalanced_varthur",
    "surge_orr_north",
    "ramp_peak",
    "surge_shift",
    "lane_closure",
]

def parse_run_name(name: str):
    is_ablation = name.startswith("ablation_")
    clean = name.replace("marathahalli_", "").replace("ablation_", "")
    parts = clean.split("_")
    seed_str = parts[-1]
    seed = int(seed_str.replace("s", ""))

    sc = None
    for s in sorted(KNOWN_SCENARIOS, key=len, reverse=True):
        if clean.startswith(s + "_"):
            sc = s
            break
    
    remainder = clean[len(sc) + 1:]
    subparts = remainder.split("_")
    # demand_level is next
    demand_level = subparts[0]
    policy = "_".join(subparts[1:-1])
    condition = f"{sc}-{demand_level}"
    return {
        "run_id": name,
        "is_ablation": is_ablation,
        "scenario": sc,
        "demand_level": demand_level,
        "condition": condition,
        "policy": policy,
        "seed": seed,
    }

def process_all_runs():
    records = []
    run_dirs = [d for d in EXP_DIR.iterdir() if d.is_dir() and d.name not in ("analysis", "logs", "plots", "checkpoints")]
    print(f"Found {len(run_dirs)} run directories in {EXP_DIR}")

    for r_dir in sorted(run_dirs, key=lambda p: p.name):
        meta = parse_run_name(r_dir.name)
        metrics_file = r_dir / "metrics.json"
        ts_file = r_dir / "timeseries.csv"
        tripinfo_file = r_dir / "tripinfo.xml"

        if not metrics_file.exists():
            continue

        with open(metrics_file, "r", encoding="utf-8") as f:
            m = json.load(f)

        # Core wait and queue metrics
        mean_wait = float(m.get("mean_waiting_time_s", m.get("avg_wait_s", 0.0)))
        p95_wait = float(m.get("p95_wait_s", m.get("p95_waiting_time_s", 0.0)))
        gap = float(m.get("approach_wait_gap_s", m.get("directional_wait_disparity_s", 0.0)))
        gt_ext_max_q = float(m.get("gt_ext_max_queue_m", m.get("max_queue_m", 0.0)))
        gt_ext_avg_q = float(m.get("gt_ext_avg_queue_m", m.get("mean_queue_m", 0.0)))

        # Correct throughput mapping
        throughput_vph = float(m.get("throughput_veh_per_h", m.get("throughput_vph", 0.0)))
        completion = float(m.get("completion_rate", 1.0))
        vehs_total = int(m.get("vehicles_total", 0))
        vehs_arrived = int(m.get("vehicles_arrived", 0))
        vehs_unfinished = int(m.get("vehicles_unfinished", 0))
        sim_end_s = float(m.get("sim_end_s", 2100.0))

        # Re-extract switches per hour from timeseries.csv
        switches_ph = 0.0
        det_full_frac = 0.0
        if ts_file.exists():
            try:
                df_ts = pd.read_csv(ts_file)
                if "axis" in df_ts.columns and len(df_ts) > 1:
                    axis_changes = (df_ts["axis"] != df_ts["axis"].shift()).sum() - 1
                    duration_h = (df_ts["t"].iloc[-1] - df_ts["t"].iloc[0]) / 3600.0
                    if duration_h > 0:
                        switches_ph = float(axis_changes) / duration_h

                det_cols = [c for c in df_ts.columns if c.startswith("det_full_")]
                if det_cols:
                    det_full_rows = df_ts[det_cols].any(axis=1).sum()
                    det_full_frac = float(det_full_rows) / max(1, len(df_ts))
            except Exception as e:
                print(f"Error reading timeseries {ts_file}: {e}")

        # Tripinfo stop distributions for heavy audit
        stops_med = np.nan
        stops_p95 = np.nan
        stops_max = np.nan
        wait_max = np.nan
        if tripinfo_file.exists() and "heavy" in meta["condition"]:
            try:
                tree = ET.parse(tripinfo_file)
                v_stops = []
                v_waits = []
                for ti in tree.getroot().iter("tripinfo"):
                    v_stops.append(int(ti.get("waitingCount", 0)))
                    v_waits.append(float(ti.get("waitingTime", 0.0)))
                if v_stops:
                    stops_med = float(np.median(v_stops))
                    stops_p95 = float(np.percentile(v_stops, 95))
                    stops_max = float(np.max(v_stops))
                if v_waits:
                    wait_max = float(np.max(v_waits))
            except Exception as e:
                print(f"Error parsing tripinfo {tripinfo_file}: {e}")

        row = {
            **meta,
            "p95_wait_s": p95_wait,
            "mean_wait_s": mean_wait,
            "approach_wait_gap_s": gap,
            "gt_ext_max_queue_m": gt_ext_max_q,
            "gt_ext_avg_queue_m": gt_ext_avg_q,
            "throughput_vph": throughput_vph,
            "completion_rate": completion,
            "vehicles_total": vehs_total,
            "vehicles_arrived": vehs_arrived,
            "vehicles_unfinished": vehs_unfinished,
            "switches_per_hour": switches_ph,
            "detector_full_frac": det_full_frac,
            "sim_end_s": sim_end_s,
            "stops_median": stops_med,
            "stops_p95": stops_p95,
            "stops_max": stops_max,
            "wait_max_s": wait_max,
        }
        records.append(row)

    df_out = pd.DataFrame(records)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df_out)} extracted run records to {OUTPUT_CSV}")
    return df_out

if __name__ == "__main__":
    process_all_runs()
