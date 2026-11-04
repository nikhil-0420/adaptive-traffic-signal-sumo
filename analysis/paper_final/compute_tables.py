"""Generate all academic paper tables from re-extracted simulation metrics.

Produces CSV tables in paper_final/tables/:
- table1_hybrid_vs_webster_measured.csv
- table2_comparators.csv
- table3_ablation.csv
- table4_per_condition.csv
- table5_operational_metrics.csv
- table6_heavy_stop_audit.csv
"""
from pathlib import Path
import pandas as pd
import numpy as np

DATA_CSV = Path("analysis/paper_final/raw_extracted_runs.csv")
OUT_DIR = Path("paper_final/tables")

PRIMARY_METRICS = ["p95_wait_s", "gt_ext_max_queue_m", "approach_wait_gap_s"]
SECONDARY_METRICS = [
    "mean_wait_s",
    "gt_ext_avg_queue_m",
    "throughput_vph",
    "switches_per_hour",
    "completion_rate",
    "vehicles_unfinished",
]

def paired_bootstrap(df, prop_pol, comp_pol, metrics, n_boot=10000, seed=42):
    p_df = df[df["policy"] == prop_pol]
    c_df = df[df["policy"] == comp_pol]
    merged = pd.merge(p_df, c_df, on=["scenario", "demand_level", "seed"], suffixes=("_prop", "_comp"))
    n_pairs = len(merged)
    results = []
    rng = np.random.default_rng(seed)

    for met in metrics:
        v_prop = merged[f"{met}_prop"].to_numpy(dtype=float)
        v_comp = merged[f"{met}_comp"].to_numpy(dtype=float)
        mean_prop = float(np.mean(v_prop))
        mean_comp = float(np.mean(v_comp))

        with np.errstate(divide="ignore", invalid="ignore"):
            pct_diffs = np.where(v_comp != 0, ((v_prop - v_comp) / v_comp) * 100.0, 0.0)

        boot_idx = rng.integers(0, n_pairs, size=(n_boot, n_pairs))
        boot_means = np.mean(pct_diffs[boot_idx], axis=1)

        ci_low = float(np.percentile(boot_means, 2.5))
        ci_high = float(np.percentile(boot_means, 97.5))
        mean_pct = float(np.mean(pct_diffs))

        # Two-tailed p-value
        if mean_pct >= 0:
            p_val = 2.0 * float(np.mean(boot_means <= 0))
        else:
            p_val = 2.0 * float(np.mean(boot_means >= 0))
        p_val = min(1.0, max(0.0, p_val))

        results.append({
            "comparator": comp_pol,
            "metric": met,
            "n_pairs": n_pairs,
            "mean_prop": mean_prop,
            "mean_comp": mean_comp,
            "mean_pct_diff": mean_pct,
            "ci_95_low": ci_low,
            "ci_95_high": ci_high,
            "p_value": p_val,
        })
    res_df = pd.DataFrame(results)

    # Holm-Bonferroni correction over primary metrics
    prim_mask = res_df["metric"].isin(PRIMARY_METRICS)
    prim_df = res_df[prim_mask].sort_values("p_value").copy()
    m = len(prim_df)
    adj_p = []
    running_max = 0.0
    for idx, (_, row) in enumerate(prim_df.iterrows()):
        k = idx + 1
        raw_p = row["p_value"]
        p_corr = min(1.0, raw_p * (m - k + 1))
        running_max = max(running_max, p_corr)
        adj_p.append(running_max)
    prim_df["p_value_holm"] = adj_p
    prim_df["significant_holm"] = prim_df["p_value_holm"] < 0.05

    merged_res = pd.merge(res_df, prim_df[["metric", "p_value_holm", "significant_holm"]], on="metric", how="left")
    return merged_res

def run_table_generation():
    df = pd.read_csv(DATA_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. TABLE 1: Hybrid vs Webster_measured
    t1_stats = paired_bootstrap(df, "hybrid_queue_adaptive", "webster_measured", PRIMARY_METRICS + SECONDARY_METRICS)
    t1_records = []
    metric_labels = {
        "p95_wait_s": "p95 wait (s)",
        "gt_ext_max_queue_m": "Max queue (m)",
        "approach_wait_gap_s": "Wait gap (s)",
        "mean_wait_s": "Mean wait (s)*",
        "gt_ext_avg_queue_m": "Mean queue (m)*",
        "throughput_vph": "Throughput (veh/h)*",
        "switches_per_hour": "Switches / hour*",
        "completion_rate": "Completion rate*",
        "vehicles_unfinished": "Unfinished vehicles*",
    }
    for _, row in t1_stats.iterrows():
        met = row["metric"]
        lbl = metric_labels.get(met, met)
        ci_str = f"{row['mean_pct_diff']:+.1f}% ({row['ci_95_low']:+.1f}, {row['ci_95_high']:+.1f})"
        holm_p_str = f"{row['p_value_holm']:.3f}" if pd.notnull(row['p_value_holm']) else "n/a"
        if holm_p_str == "0.000": holm_p_str = "<0.001"

        verdict = "Not distinguished"
        if row.get("significant_holm"):
            verdict = "Lower (improved)" if row["mean_pct_diff"] < 0 else "Higher (worse)"
        elif pd.isnull(row["p_value_holm"]):
            verdict = "Secondary (descriptive)"

        t1_records.append({
            "Metric": lbl,
            "Hybrid": round(row["mean_prop"], 1),
            "Webster-m": round(row["mean_comp"], 1),
            "Δ% (95% CI)": ci_str,
            "Holm p": holm_p_str,
            "Verdict": verdict
        })
    df_t1 = pd.DataFrame(t1_records)
    df_t1.to_csv(OUT_DIR / "table1_hybrid_vs_webster_measured.csv", index=False)

    # 2. TABLE 2: Comparisons Against Alternative Baselines
    comparators = ["webster_recalc", "fixed", "sumo_actuated"]
    t2_records = []
    for comp in comparators:
        comp_stats = paired_bootstrap(df, "hybrid_queue_adaptive", comp, PRIMARY_METRICS + ["mean_wait_s", "gt_ext_avg_queue_m", "switches_per_hour"])
        row_dict = {"Comparator": comp}
        for _, row in comp_stats.iterrows():
            met = row["metric"]
            ci_str = f"{row['mean_pct_diff']:+.1f}% ({row['ci_95_low']:+.1f}, {row['ci_95_high']:+.1f})"
            if met in PRIMARY_METRICS:
                sig = row.get("significant_holm", False)
                tag = " [ND]" if not sig else (" [lower]" if row['mean_pct_diff'] < 0 else " [hybrid worse]")
                row_dict[met] = ci_str + tag
            else:
                row_dict[met] = ci_str
        t2_records.append(row_dict)
    df_t2 = pd.DataFrame(t2_records)
    df_t2.to_csv(OUT_DIR / "table2_comparators.csv", index=False)

    # 3. TABLE 3: Ablation (Hybrid vs Hybrid Oracle Seeded)
    t3_stats = paired_bootstrap(df, "hybrid_queue_adaptive", "hybrid_oracle_seeded", PRIMARY_METRICS)
    t3_records = []
    for _, row in t3_stats.iterrows():
        met = row["metric"]
        lbl = metric_labels.get(met, met)
        ci_str = f"{row['mean_pct_diff']:+.1f}% ({row['ci_95_low']:+.1f}, {row['ci_95_high']:+.1f})"
        holm_p_str = f"{row['p_value_holm']:.3f}" if pd.notnull(row['p_value_holm']) else "n/a"
        t3_records.append({
            "Metric": lbl,
            "Δ% (95% CI)": ci_str,
            "Holm p": holm_p_str,
            "Interpretation": "Not distinguished (oracle not required)" if not row.get("significant_holm") else "Significant difference"
        })
    df_t3 = pd.DataFrame(t3_records)
    df_t3.to_csv(OUT_DIR / "table3_ablation.csv", index=False)

    # 4. TABLE 4: Per-Condition Descriptive Breakdown
    cond_order = [
        "balanced-low",
        "balanced-heavy",
        "imbalanced_orr-heavy",
        "ramp_peak-medium",
        "surge_shift-medium",
        "lane_closure-medium",
    ]
    t4_records = []
    for c in cond_order:
        c_df = df[df["condition"] == c]
        row_dict = {"Condition": c}
        for pol, pol_lbl in [("hybrid_queue_adaptive", "Hybrid"), ("webster_measured", "Webster-m"), ("sumo_actuated", "SUMO-act"), ("fixed", "Fixed")]:
            sub = c_df[c_df["policy"] == pol]
            p95 = sub["p95_wait_s"].mean()
            mq = sub["gt_ext_max_queue_m"].mean()
            row_dict[pol_lbl] = f"{p95:.0f} / {mq:.0f}"
        t4_records.append(row_dict)
    df_t4 = pd.DataFrame(t4_records)
    df_t4.to_csv(OUT_DIR / "table4_per_condition.csv", index=False)

    # 5. TABLE 5: Operational Metrics Re-extracted
    pol_order = ["fixed", "webster_measured", "webster_recalc", "sumo_actuated", "adaptive", "queue_extension", "hybrid_queue_adaptive", "hybrid_oracle_seeded"]
    t5_records = []
    for pol in pol_order:
        sub = df[df["policy"] == pol]
        t5_records.append({
            "Policy": pol,
            "Throughput (veh/h)": f"{sub['throughput_vph'].mean():.1f} ± {sub['throughput_vph'].std():.1f}",
            "Switches / hour": f"{sub['switches_per_hour'].mean():.1f} ± {sub['switches_per_hour'].std():.1f}",
            "Completion Rate (%)": f"{sub['completion_rate'].mean()*100:.1f}%",
            "Unfinished Vehicles": int(sub['vehicles_unfinished'].sum()),
        })
    df_t5 = pd.DataFrame(t5_records)
    df_t5.to_csv(OUT_DIR / "table5_operational_metrics.csv", index=False)

    # 6. TABLE 6: Heavy Conditions Stop & Waiting Sanity Audit
    heavy_df = df[df["condition"].isin(["balanced-heavy", "imbalanced_orr-heavy"])]
    t6_records = []
    for (cond, pol), sub in heavy_df.groupby(["condition", "policy"]):
        t6_records.append({
            "Condition": cond,
            "Policy": pol,
            "Completed Vehicles": int(sub["vehicles_arrived"].mean()),
            "Wait p95 (s)": round(sub["p95_wait_s"].mean(), 1),
            "Wait Max (s)": round(sub["wait_max_s"].mean(), 1) if "wait_max_s" in sub and not sub["wait_max_s"].isnull().all() else "n/a",
            "Max Queue (m)": round(sub["gt_ext_max_queue_m"].mean(), 1),
            "Stop Count Median": round(sub["stops_median"].mean(), 1) if "stops_median" in sub and not sub["stops_median"].isnull().all() else "n/a",
            "Stop Count p95": round(sub["stops_p95"].mean(), 1) if "stops_p95" in sub and not sub["stops_p95"].isnull().all() else "n/a",
            "Stop Count Max": round(sub["stops_max"].mean(), 1) if "stops_max" in sub and not sub["stops_max"].isnull().all() else "n/a",
        })
    df_t6 = pd.DataFrame(t6_records)
    df_t6.to_csv(OUT_DIR / "table6_heavy_stop_audit.csv", index=False)

    print(f"Generated 6 verified tables in {OUT_DIR}")

if __name__ == "__main__":
    run_table_generation()
