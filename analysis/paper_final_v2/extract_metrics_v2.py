"""extract_metrics_v2.py
Single source of truth metric extraction for DP1 Paper Final Analysis (v1 study, Seeds 131-138).

Reads directly from results/research/exp_marathahalli_improve_final/
Produces analysis/paper_final_v2/raw_extracted_runs.csv

Assertions:
- Policy names are matched via explicit suffix matching against KNOWN_POLICIES (longest first)
  to prevent substring aliasing bugs.
- Every (policy, condition) cell has exactly 8 runs (seeds 131-138), total 384 runs.
- Condition strings are asserted against the canonical 6 conditions.
"""
from pathlib import Path
import re
import json
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

REPO_ROOT = Path("E:/dp1-traffic-signal")
EXP_DIR = REPO_ROOT / "results/research/exp_marathahalli_improve_final"
OUTPUT_CSV = REPO_ROOT / "analysis/paper_final_v2/raw_extracted_runs.csv"

KNOWN_POLICIES = [
    "hybrid_oracle_seeded",
    "hybrid_queue_adaptive",
    "queue_extension",
    "sumo_actuated",
    "webster_measured",
    "webster_recalc",
    "adaptive",
    "fixed",
]

CANONICAL_CONDITIONS = [
    "balanced-low",
    "balanced-heavy",
    "imbalanced_orr-heavy",
    "ramp_peak-medium",
    "surge_shift-medium",
    "lane_closure-medium",
]

def parse_run_dir(dir_name: str):
    """Parse directory name using strict regex and explicit suffix matching."""
    m = re.match(r"^(?:ablation_|marathahalli_)?(.+)_s(\d+)$", dir_name)
    if not m:
        raise ValueError(f"Could not parse run directory: {dir_name}")
    body, seed_str = m.group(1), m.group(2)
    seed = int(seed_str)

    matched_pol = None
    matched_cond_raw = None
    for pol in sorted(KNOWN_POLICIES, key=len, reverse=True):
        if body.endswith("_" + pol):
            matched_pol = pol
            matched_cond_raw = body[:-len("_" + pol)]
            break
        elif body == pol:
            matched_pol = pol
            matched_cond_raw = ""
            break

    if not matched_pol:
        raise ValueError(f"Could not match known policy from {dir_name}")

    # Map condition raw to canonical hyphenated naming
    # scenarios: balanced_low, balanced_heavy, imbalanced_orr_heavy, ramp_peak_medium, surge_shift_medium, lane_closure_medium
    cond_mapping = {
        "balanced_low": "balanced-low",
        "balanced_heavy": "balanced-heavy",
        "imbalanced_orr_heavy": "imbalanced_orr-heavy",
        "ramp_peak_medium": "ramp_peak-medium",
        "surge_shift_medium": "surge_shift-medium",
        "lane_closure_medium": "lane_closure-medium",
    }
    if matched_cond_raw not in cond_mapping:
        raise ValueError(f"Unknown condition string '{matched_cond_raw}' in {dir_name}")
    condition = cond_mapping[matched_cond_raw]

    return matched_pol, condition, seed

def extract_all():
    run_dirs = [d for d in EXP_DIR.iterdir() if d.is_dir() and d.name not in ("analysis", "logs", "plots", "checkpoints")]
    print(f"[EXTRACT] Found {len(run_dirs)} candidate run directories in {EXP_DIR}")

    records = []
    for r_dir in sorted(run_dirs, key=lambda p: p.name):
        pol, cond, seed = parse_run_dir(r_dir.name)

        metrics_file = r_dir / "metrics.json"
        ts_file = r_dir / "timeseries.csv"
        tripinfo_file = r_dir / "tripinfo.xml"

        if not metrics_file.exists():
            raise FileNotFoundError(f"Missing metrics.json in {r_dir}")

        with open(metrics_file, "r", encoding="utf-8") as f:
            m = json.load(f)

        mean_wait = float(m.get("mean_waiting_time_s", m.get("avg_wait_s", 0.0)))
        p95_wait = float(m.get("p95_wait_s", m.get("p95_waiting_time_s", 0.0)))
        gap = float(m.get("approach_wait_gap_s", m.get("directional_wait_disparity_s", 0.0)))
        gt_ext_max_q = float(m.get("gt_ext_max_queue_m", m.get("max_queue_m", 0.0)))
        gt_ext_avg_q = float(m.get("gt_ext_avg_queue_m", m.get("mean_queue_m", 0.0)))

        throughput_vph = float(m.get("throughput_veh_per_h", m.get("throughput_vph", 0.0)))
        completion = float(m.get("completion_rate", 1.0))
        vehs_total = int(m.get("vehicles_total", 0))
        vehs_arrived = int(m.get("vehicles_arrived", 0))
        vehs_unfinished = int(m.get("vehicles_unfinished", 0))
        sim_end_s = float(m.get("sim_end_s", 2100.0))

        # Timeseries metrics
        switches_ph = 0.0
        det_full_frac = 0.0
        if ts_file.exists():
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

        # Parse tripinfo for departure delays, total delays, and stops
        dep_delays = []
        depart_intervals = []
        total_delays = []
        v_stops = []
        v_waits = []

        if tripinfo_file.exists():
            tree = ET.parse(tripinfo_file)
            for ti in tree.getroot().iter("tripinfo"):
                dep = float(ti.get("depart", 0.0))
                delay = float(ti.get("departDelay", 0.0))
                wait_t = float(ti.get("waitingTime", 0.0))
                stops = int(ti.get("waitingCount", 0))

                dep_delays.append(delay)
                total_delays.append(wait_t + delay)
                t_sched = max(0.0, dep - delay)
                depart_intervals.append((t_sched, dep))
                v_stops.append(stops)
                v_waits.append(wait_t)

        n_vehs = len(dep_delays)
        mean_delay = float(np.mean(dep_delays)) if n_vehs > 0 else 0.0
        p95_delay = float(np.percentile(dep_delays, 95)) if n_vehs > 0 else 0.0
        max_delay = float(np.max(dep_delays)) if n_vehs > 0 else 0.0
        count_gt_0 = int(np.sum(np.array(dep_delays) > 0.0)) if n_vehs > 0 else 0
        pct_gt_0 = (count_gt_0 / n_vehs * 100.0) if n_vehs > 0 else 0.0
        count_gt_60 = int(np.sum(np.array(dep_delays) > 60.0)) if n_vehs > 0 else 0
        pct_gt_60 = (count_gt_60 / n_vehs * 100.0) if n_vehs > 0 else 0.0

        # Sweep-line for max insertion backlog
        events = []
        for t_sched, t_dep in depart_intervals:
            if t_dep > t_sched:
                events.append((t_sched, +1))
                events.append((t_dep, -1))
        events.sort(key=lambda x: (x[0], x[1]))
        curr_b = 0
        max_b = 0
        for _, delta in events:
            curr_b += delta
            if curr_b > max_b:
                max_b = curr_b

        mean_tot_delay = float(np.mean(total_delays)) if n_vehs > 0 else 0.0
        p95_tot_delay = float(np.percentile(total_delays, 95)) if n_vehs > 0 else 0.0

        stops_med = float(np.median(v_stops)) if v_stops else np.nan
        stops_p95 = float(np.percentile(v_stops, 95)) if v_stops else np.nan
        stops_max = float(np.max(v_stops)) if v_stops else np.nan
        wait_max = float(np.max(v_waits)) if v_waits else np.nan

        records.append({
            "run_id": r_dir.name,
            "policy": pol,
            "condition": cond,
            "seed": seed,
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
            "depart_delay_mean": mean_delay,
            "depart_delay_p95": p95_delay,
            "depart_delay_max": max_delay,
            "depart_delay_count_gt_0": count_gt_0,
            "depart_delay_pct_gt_0": pct_gt_0,
            "depart_delay_count_gt_60": count_gt_60,
            "depart_delay_pct_gt_60": pct_gt_60,
            "max_insertion_backlog": max_b,
            "mean_total_delay": mean_tot_delay,
            "p95_total_delay": p95_tot_delay,
            "stops_median": stops_med,
            "stops_p95": stops_p95,
            "stops_max": stops_max,
            "wait_max_s": wait_max,
        })

    df = pd.DataFrame(records)
    print(f"[EXTRACT] Extracted {len(df)} total simulation records.")

    # --------------------------------------------------------------------------
    # LOUD ASSERTIONS
    # --------------------------------------------------------------------------
    assert len(df) == 384, f"Assertion failed: expected 384 runs, got {len(df)}"
    
    # Assert policy counts
    pol_counts = df["policy"].value_counts()
    for pol in KNOWN_POLICIES:
        assert pol in pol_counts, f"Missing policy: {pol}"
        assert pol_counts[pol] == 48, f"Policy {pol} count {pol_counts[pol]} != 48"

    # Assert condition counts
    cond_counts = df["condition"].value_counts()
    for cond in CANONICAL_CONDITIONS:
        assert cond in cond_counts, f"Missing condition: {cond}"
        assert cond_counts[cond] == 64, f"Condition {cond} count {cond_counts[cond]} != 64"

    # Assert cell counts: exactly 8 runs per (policy, condition) cell
    cell_counts = df.groupby(["policy", "condition"]).size()
    assert len(cell_counts) == 48, f"Expected 48 cells, got {len(cell_counts)}"
    for (pol, cond), count in cell_counts.items():
        assert count == 8, f"Cell ({pol}, {cond}) has {count} runs, expected exactly 8"

    # Assert seed set is exactly {131, 132, 133, 134, 135, 136, 137, 138}
    for (pol, cond), group in df.groupby(["policy", "condition"]):
        cell_seeds = sorted(group["seed"].tolist())
        assert cell_seeds == [131, 132, 133, 134, 135, 136, 137, 138], f"Cell ({pol}, {cond}) invalid seeds: {cell_seeds}"

    print("[EXTRACT] All assertions passed: exactly 8 runs per cell across 48 cells (384 runs total).")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[EXTRACT] Saved verified raw runs to {OUTPUT_CSV}")
    return df

if __name__ == "__main__":
    extract_all()
