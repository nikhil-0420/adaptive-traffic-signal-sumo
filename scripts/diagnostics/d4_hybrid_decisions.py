"""Diagnostic D4: Hybrid Controller Decision Breakdown and Reason Distribution.

D4: Hybrid decisions:
    - % approved extensions, rejected extensions, HOLD, switch requests per condition.
    - Reason-code distribution.
    - Fraction approved purely because queue >= extension threshold with no comparison to the competing score.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np


def analyze_hybrid_decisions(exp_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_csv = exp_dir / "raw_runs.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw_runs.csv at {raw_csv}")
    raw_df = pd.read_csv(raw_csv)
    hybrid_df = raw_df[raw_df["policy"] == "hybrid_queue_adaptive"]

    all_dec_records = []
    reason_records = []
    comparative_check_records = []

    for _, row in hybrid_df.iterrows():
        cell_id = row["cell_id"]
        pattern = row["pattern"]
        demand_level = row["demand_level"]
        seed = row["seed"]

        dec_path = exp_dir / "runs" / cell_id / "decisions.csv"
        if not dec_path.exists():
            continue

        df_dec = pd.read_csv(dec_path)
        if df_dec.empty:
            continue

        total_dec = len(df_dec)
        
        # Categorize actions/outcomes
        # Actions: ENTER_GREEN, HOLD, EXTEND, REQUEST_SWITCH
        # Outcomes / reason_codes:
        # EXTEND_APPROVED
        # SWITCH_MAX_GREEN, SWITCH_GAP_OUT, SWITCH_CEILING_REACHED, SWITCH_FAIRNESS_WAIT_LIMIT, SWITCH_DEMAND_FAIRNESS, SWITCH_DEMAND_EXHAUSTED
        # HOLD_MIN_GREEN, HOLD_CLEARING, HOLD_SERVICING, BASELINE_ENTRY

        approved_ext = int((df_dec["reason_code"] == "EXTEND_APPROVED").sum())
        rejected_ext = int(df_dec["reason_code"].isin([
            "SWITCH_CEILING_REACHED",
            "SWITCH_FAIRNESS_WAIT_LIMIT",
            "SWITCH_DEMAND_FAIRNESS",
            "SWITCH_DEMAND_EXHAUSTED",
        ]).sum())
        holds = int(df_dec["reason_code"].str.startswith("HOLD").sum())
        switches = int(df_dec["reason_code"].str.startswith("SWITCH").sum())
        baseline_entries = int((df_dec["reason_code"] == "BASELINE_ENTRY").sum())

        all_dec_records.append({
            "cell_id": cell_id,
            "pattern": pattern,
            "demand_level": demand_level,
            "seed": seed,
            "total_decisions": total_dec,
            "approved_ext": approved_ext,
            "rejected_ext": rejected_ext,
            "holds": holds,
            "switches": switches,
            "baseline_entries": baseline_entries,
        })

        # Reason code counts
        for rc, cnt in df_dec["reason_code"].value_counts().items():
            reason_records.append({
                "pattern": pattern,
                "demand_level": demand_level,
                "reason_code": rc,
                "count": cnt,
            })

        # For EXTEND_APPROVED, check whether competing score played a role or if queue >= threshold was solely responsible
        ext_rows = df_dec[df_dec["reason_code"] == "EXTEND_APPROVED"]
        for _, er in ext_rows.iterrows():
            q_active = er.get("q_active_m", 0.0)
            q_comp = er.get("q_competing_m", 0.0)
            score_active = er.get("score_active", 0.0)
            score_comp = er.get("score_competing", 0.0)
            # In hybrid controller: extension is checked against extend_threshold_m (10m)
            # Competing check is score_competing > score_active * fairness_ratio (1.5)
            # If q_comp < min_competing_queue_m (5m), competing check was completely inactive!
            no_competing_pressure = (q_comp < 5.0) or (score_comp <= 0.0)
            comparative_check_records.append({
                "pattern": pattern,
                "demand_level": demand_level,
                "q_active": q_active,
                "q_comp": q_comp,
                "score_active": score_active,
                "score_comp": score_comp,
                "approved_without_competing_pressure": no_competing_pressure,
            })

    summary_df = pd.DataFrame(all_dec_records)
    agg_dec = summary_df.groupby(["pattern", "demand_level"]).agg(
        total_decisions=("total_decisions", "sum"),
        approved_ext=("approved_ext", "sum"),
        rejected_ext=("rejected_ext", "sum"),
        holds=("holds", "sum"),
        switches=("switches", "sum"),
    ).reset_index()

    agg_dec["approved_ext_pct"] = (agg_dec["approved_ext"] / agg_dec["total_decisions"]) * 100.0
    agg_dec["rejected_ext_pct"] = (agg_dec["rejected_ext"] / agg_dec["total_decisions"]) * 100.0
    agg_dec["holds_pct"] = (agg_dec["holds"] / agg_dec["total_decisions"]) * 100.0
    agg_dec["switches_pct"] = (agg_dec["switches"] / agg_dec["total_decisions"]) * 100.0

    # Reason distribution
    df_reasons = pd.DataFrame(reason_records).groupby(["pattern", "demand_level", "reason_code"])["count"].sum().reset_index()

    # Comparative evaluation
    df_comp = pd.DataFrame(comparative_check_records)
    if not df_comp.empty:
        comp_agg = df_comp.groupby(["pattern", "demand_level"]).agg(
            total_approved=("approved_without_competing_pressure", "count"),
            approved_without_competing=("approved_without_competing_pressure", "sum"),
        ).reset_index()
        comp_agg["pct_without_competing_pressure"] = (
            comp_agg["approved_without_competing"] / comp_agg["total_approved"]
        ) * 100.0
    else:
        comp_agg = pd.DataFrame()

    return agg_dec, df_reasons, comp_agg


def main():
    parser = argparse.ArgumentParser(description="Compute D4 hybrid controller decision diagnostics.")
    parser.add_argument("--exp-dir", type=str, default="results/research/exp_diag_dev_101_110",
                        help="Path to experiment directory")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    print(f"Running D4 diagnostics on: {exp_dir}")
    agg_dec, df_reasons, comp_agg = analyze_hybrid_decisions(exp_dir)

    print("\n" + "=" * 80)
    print("D4: HYBRID DECISION ACTION PERCENTAGES BY CONDITION")
    print("=" * 80)
    print(agg_dec.to_string(index=False))

    print("\n" + "=" * 80)
    print("D4: REASON-CODE DISTRIBUTION BY CONDITION")
    print("=" * 80)
    print(df_reasons.to_string(index=False))

    if not comp_agg.empty:
        print("\n" + "=" * 80)
        print("D4: EXTENSIONS APPROVED WITHOUT COMPETING OPPOSING DEMAND (q_comp < 5m)")
        print("=" * 80)
        print(comp_agg.to_string(index=False))


if __name__ == "__main__":
    main()
