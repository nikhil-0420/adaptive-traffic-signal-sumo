"""compute_bootstrap_v2.py
Seed-clustered bootstrap analysis for DP1 final evaluation (Seeds 131-138).

Implements:
- OUTPUT 1: Primary comparisons (all_6_pooled, stationary, non-stationary)
  - Delta %, seed-clustered CI, raw p, Holm-Bonferroni p across 3 primary metrics
  - Absolute means for Hybrid and Ref
  - Absolute difference (seconds) with seed-clustered bootstrap CI for wait gap
  - Pair-level bootstrap sensitivity analysis and comparison of significance verdicts
- OUTPUT 2: Secondary metrics (mean wait, mean queue) with documented definitions

Assertions:
- Subsets asserted against exact strings:
  stationary = ["balanced-low", "balanced-heavy", "imbalanced_orr-heavy"]
  non_stationary = ["ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"]
- Assert that pooled values equal the mean of the subset values (fail loudly if violated).
"""
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path("E:/dp1-traffic-signal")
DATA_CSV = REPO_ROOT / "analysis/paper_final_v2/raw_extracted_runs.csv"
TABLES_DIR = REPO_ROOT / "paper_final_v2/tables"

COMPARATORS = [
    "webster_measured",
    "webster_recalc",
    "fixed",
    "sumo_actuated",
    "hybrid_oracle_seeded",
]

SUBSETS = {
    "all_6_pooled": None,
    "3_stationary": ["balanced-low", "balanced-heavy", "imbalanced_orr-heavy"],
    "3_non_stationary": ["ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"],
}

PRIMARY_METRICS = ["p95_wait_s", "gt_ext_max_queue_m", "approach_wait_gap_s"]
SECONDARY_METRICS = ["mean_wait_s", "gt_ext_avg_queue_m"]
ALL_METRICS = PRIMARY_METRICS + SECONDARY_METRICS

METRIC_LABELS = {
    "p95_wait_s": "p95 wait (s)",
    "gt_ext_max_queue_m": "extended max queue (m)",
    "approach_wait_gap_s": "wait gap (s)",
    "mean_wait_s": "mean wait (s)",
    "gt_ext_avg_queue_m": "mean queue (m)",
}

METRIC_DEFINITIONS = {
    "p95_wait_s": "95th percentile vehicle waiting time (SUMO tripinfo waitingTime, speed < 0.1 m/s)",
    "gt_ext_max_queue_m": "Maximum over time of approach-maximum extended queue (Qgt_ext)",
    "approach_wait_gap_s": "Disparity: maximum approach mean waiting time minus minimum approach mean waiting time",
    "mean_wait_s": "Space-time average vehicle waiting time (tripinfo waitingTime, speed < 0.1 m/s)",
    "gt_ext_avg_queue_m": "Space-time average of Qgt_ext across all time steps and approaches",
}

def run_bootstrap():
    df = pd.read_csv(DATA_CSV)
    print(f"[BOOTSTRAP] Loaded {len(df)} records from {DATA_CSV}")

    # Assert exact subset strings
    stat_conds = SUBSETS["3_stationary"]
    nonstat_conds = SUBSETS["3_non_stationary"]
    assert set(stat_conds) == {"balanced-low", "balanced-heavy", "imbalanced_orr-heavy"}
    assert set(nonstat_conds) == {"ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"}

    n_boot = 10000
    rng = np.random.default_rng(42)
    unique_seeds = np.array(sorted(df["seed"].unique()))
    n_seeds = len(unique_seeds)
    boot_indices = rng.integers(0, n_seeds, size=(n_boot, n_seeds))

    results_all = []
    verdict_comparisons = []

    # Store for subset assertions: { (comp, metric): { 'all_6_pooled': val, '3_stationary': val, '3_non_stationary': val } }
    subset_check_deltas = {}
    subset_check_hyb_means = {}
    subset_check_ref_means = {}

    for comp in COMPARATORS:
        for sub_name, conds in SUBSETS.items():
            if conds is not None:
                sub_df = df[df["condition"].isin(conds)].copy()
            else:
                sub_df = df.copy()

            prop_df = sub_df[sub_df["policy"] == "hybrid_queue_adaptive"]
            comp_df = sub_df[sub_df["policy"] == comp]
            merged = pd.merge(prop_df, comp_df, on=["condition", "seed"], suffixes=("_hyb", "_ref"))

            hyb_means = {m: float(merged[f"{m}_hyb"].mean()) for m in ALL_METRICS}
            ref_means = {m: float(merged[f"{m}_ref"].mean()) for m in ALL_METRICS}

            # Per-seed cluster averages of percentage differences and absolute differences
            seed_deltas = {m: [] for m in ALL_METRICS}
            pair_deltas = {m: [] for m in ALL_METRICS}
            seed_abs_diffs = {m: [] for m in ALL_METRICS}
            pair_abs_diffs = {m: [] for m in ALL_METRICS}

            for s in unique_seeds:
                s_rows = merged[merged["seed"] == s]
                for m in ALL_METRICS:
                    vh = s_rows[f"{m}_hyb"].to_numpy(dtype=float)
                    vr = s_rows[f"{m}_ref"].to_numpy(dtype=float)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        d_pct = np.where(vr != 0, ((vh - vr) / vr) * 100.0, 0.0)
                    seed_deltas[m].append(np.mean(d_pct))
                    pair_deltas[m].extend(d_pct.tolist())

                    d_abs = vh - vr
                    seed_abs_diffs[m].append(np.mean(d_abs))
                    pair_abs_diffs[m].extend(d_abs.tolist())

            sub_res = {}
            for m in ALL_METRICS:
                s_arr = np.array(seed_deltas[m])  # shape (n_seeds,)
                cluster_sample_delta = float(np.mean(s_arr))
                pair_sample_delta = float(np.mean(pair_deltas[m]))

                # Record for pooled assertion check
                key = (comp, m)
                if key not in subset_check_deltas:
                    subset_check_deltas[key] = {}
                    subset_check_hyb_means[key] = {}
                    subset_check_ref_means[key] = {}
                subset_check_deltas[key][sub_name] = cluster_sample_delta
                subset_check_hyb_means[key][sub_name] = hyb_means[m]
                subset_check_ref_means[key][sub_name] = ref_means[m]

                # Bootstrap distribution of cluster mean
                boot_means = np.mean(s_arr[boot_indices], axis=1)
                ci_low = float(np.percentile(boot_means, 2.5))
                ci_high = float(np.percentile(boot_means, 97.5))

                # Two-sided empirical p-value for cluster bootstrap
                if cluster_sample_delta >= 0:
                    raw_p = 2.0 * float(np.mean(boot_means <= 0))
                else:
                    raw_p = 2.0 * float(np.mean(boot_means >= 0))
                raw_p = min(1.0, max(0.0, raw_p))

                # Absolute difference bootstrap (for wait gap and others)
                s_abs_arr = np.array(seed_abs_diffs[m])
                cluster_sample_abs = float(np.mean(s_abs_arr))
                boot_abs_means = np.mean(s_abs_arr[boot_indices], axis=1)
                ci_abs_low = float(np.percentile(boot_abs_means, 2.5))
                ci_abs_high = float(np.percentile(boot_abs_means, 97.5))
                if cluster_sample_abs >= 0:
                    raw_abs_p = 2.0 * float(np.mean(boot_abs_means <= 0))
                else:
                    raw_abs_p = 2.0 * float(np.mean(boot_abs_means >= 0))
                raw_abs_p = min(1.0, max(0.0, raw_abs_p))

                # Pair-level bootstrap (independent pair resampling)
                pair_arr = np.array(pair_deltas[m])
                rng_pair = np.random.default_rng(42)
                pair_boot_idx = rng_pair.integers(0, len(pair_arr), size=(n_boot, len(pair_arr)))
                pair_boot_means = np.mean(pair_arr[pair_boot_idx], axis=1)
                pair_ci_low = float(np.percentile(pair_boot_means, 2.5))
                pair_ci_high = float(np.percentile(pair_boot_means, 97.5))
                if pair_sample_delta >= 0:
                    pair_raw_p = 2.0 * float(np.mean(pair_boot_means <= 0))
                else:
                    pair_raw_p = 2.0 * float(np.mean(pair_boot_means >= 0))
                pair_raw_p = min(1.0, max(0.0, pair_raw_p))

                # Pair absolute difference bootstrap
                pair_abs_arr = np.array(pair_abs_diffs[m])
                pair_abs_boot_means = np.mean(pair_abs_arr[pair_boot_idx], axis=1)
                pair_abs_ci_low = float(np.percentile(pair_abs_boot_means, 2.5))
                pair_abs_ci_high = float(np.percentile(pair_abs_boot_means, 97.5))

                sub_res[m] = {
                    "hyb_mean": hyb_means[m],
                    "ref_mean": ref_means[m],
                    "delta_pct": cluster_sample_delta,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "raw_p": raw_p,
                    "abs_diff": cluster_sample_abs,
                    "abs_ci_low": ci_abs_low,
                    "abs_ci_high": ci_abs_high,
                    "abs_raw_p": raw_abs_p,
                    "pair_delta_pct": pair_sample_delta,
                    "pair_ci_low": pair_ci_low,
                    "pair_ci_high": pair_ci_high,
                    "pair_raw_p": pair_raw_p,
                    "pair_abs_diff": float(np.mean(pair_abs_arr)),
                    "pair_abs_ci_low": pair_abs_ci_low,
                    "pair_abs_ci_high": pair_abs_ci_high,
                }

            # Step-down Holm-Bonferroni correction across the 3 PRIMARY metrics within this comparison + subset
            primary_p_tuples = [(m, sub_res[m]["raw_p"]) for m in PRIMARY_METRICS]
            primary_p_tuples.sort(key=lambda x: x[1])
            holm_p_dict = {}
            m_tests = len(PRIMARY_METRICS)
            running_max = 0.0
            for rank, (m, p) in enumerate(primary_p_tuples):
                adj_p = min(1.0, p * (m_tests - rank))
                adj_p = max(adj_p, running_max)
                running_max = adj_p
                holm_p_dict[m] = adj_p

            # Also compute pair-level Holm p for sensitivity comparison
            pair_primary_p_tuples = [(m, sub_res[m]["pair_raw_p"]) for m in PRIMARY_METRICS]
            pair_primary_p_tuples.sort(key=lambda x: x[1])
            pair_holm_p_dict = {}
            running_max_pair = 0.0
            for rank, (m, p) in enumerate(pair_primary_p_tuples):
                adj_p = min(1.0, p * (m_tests - rank))
                adj_p = max(adj_p, running_max_pair)
                running_max_pair = adj_p
                pair_holm_p_dict[m] = adj_p

            for m in ALL_METRICS:
                is_primary = m in PRIMARY_METRICS
                h_p = holm_p_dict.get(m, np.nan)
                pair_h_p = pair_holm_p_dict.get(m, np.nan)
                r = sub_res[m]

                # Check verdict: statistically significant at alpha = 0.05
                clust_sig = bool(h_p < 0.05) if is_primary else bool(r["raw_p"] < 0.05)
                pair_sig = bool(pair_h_p < 0.05) if is_primary else bool(r["pair_raw_p"] < 0.05)
                verdict_changed = clust_sig != pair_sig

                if is_primary:
                    verdict_comparisons.append({
                        "Comparison": f"hybrid vs {comp}",
                        "Subset": sub_name,
                        "Metric": METRIC_LABELS[m],
                        "Cluster Holm p": h_p,
                        "Cluster Sig (alpha=0.05)": clust_sig,
                        "Pair Holm p": pair_h_p,
                        "Pair Sig (alpha=0.05)": pair_sig,
                        "Verdict Changed": verdict_changed,
                    })

                results_all.append({
                    "Comparison": f"hybrid vs {comp}",
                    "Comparator": comp,
                    "Subset": sub_name,
                    "Metric_Key": m,
                    "Metric": METRIC_LABELS[m],
                    "Is_Primary": is_primary,
                    "Hybrid Mean": r["hyb_mean"],
                    "Ref Mean": r["ref_mean"],
                    "Delta %": r["delta_pct"],
                    "Cluster 95% CI Low": r["ci_low"],
                    "Cluster 95% CI High": r["ci_high"],
                    "Cluster Raw p": r["raw_p"],
                    "Cluster Holm p": h_p if is_primary else np.nan,
                    "Cluster Significant": clust_sig,
                    "Abs Diff": r["abs_diff"],
                    "Abs Diff 95% CI Low": r["abs_ci_low"],
                    "Abs Diff 95% CI High": r["abs_ci_high"],
                    "Abs Raw p": r["abs_raw_p"],
                    "Pair-Level Delta %": r["pair_delta_pct"],
                    "Pair-Level 95% CI Low": r["pair_ci_low"],
                    "Pair-Level 95% CI High": r["pair_ci_high"],
                    "Pair-Level Raw p": r["pair_raw_p"],
                    "Pair-Level Holm p": pair_h_p if is_primary else np.nan,
                    "Pair-Level Significant": pair_sig,
                })

    df_full = pd.DataFrame(results_all)
    df_verdicts = pd.DataFrame(verdict_comparisons)

    # --------------------------------------------------------------------------
    # LOUD ASSERTION: POOLED VALUES EQUAL MEAN OF SUBSET VALUES
    # --------------------------------------------------------------------------
    print("[BOOTSTRAP] Checking assertion: Pooled value == (Stationary + Non-Stationary) / 2...")
    for (comp, m), vals in subset_check_deltas.items():
        pooled = vals["all_6_pooled"]
        stat = vals["3_stationary"]
        nonstat = vals["3_non_stationary"]
        expected_pooled = (stat + nonstat) / 2.0
        diff = abs(pooled - expected_pooled)
        assert diff < 1e-4, f"Pooled delta assertion failed for ({comp}, {m}): pooled={pooled:.6f}, expected={expected_pooled:.6f}, diff={diff:.6f}"

    for (comp, m), vals in subset_check_hyb_means.items():
        pooled = vals["all_6_pooled"]
        stat = vals["3_stationary"]
        nonstat = vals["3_non_stationary"]
        expected_pooled = (stat + nonstat) / 2.0
        diff = abs(pooled - expected_pooled)
        assert diff < 1e-4, f"Pooled Hybrid Mean assertion failed for ({comp}, {m}): pooled={pooled:.6f}, expected={expected_pooled:.6f}, diff={diff:.6f}"

    for (comp, m), vals in subset_check_ref_means.items():
        pooled = vals["all_6_pooled"]
        stat = vals["3_stationary"]
        nonstat = vals["3_non_stationary"]
        expected_pooled = (stat + nonstat) / 2.0
        diff = abs(pooled - expected_pooled)
        assert diff < 1e-4, f"Pooled Ref Mean assertion failed for ({comp}, {m}): pooled={pooled:.6f}, expected={expected_pooled:.6f}, diff={diff:.6f}"

    print("[BOOTSTRAP] SUCCESS: All pooled value assertions verified perfectly!")

    # Format Table 2: Primary comparisons
    df_t2_raw = df_full[df_full["Is_Primary"]].copy()
    t2_rows = []
    for _, r in df_t2_raw.iterrows():
        row_dict = {
            "Comparison": r["Comparison"],
            "Subset": r["Subset"],
            "Metric": r["Metric"],
            "Hybrid Mean": f"{r['Hybrid Mean']:.2f}",
            "Ref Mean": f"{r['Ref Mean']:.2f}",
            "Delta %": f"{r['Delta %']:+.1f}%",
            "Seed-Clustered 95% CI": f"[{r['Cluster 95% CI Low']:+.1f}, {r['Cluster 95% CI High']:+.1f}]",
            "Cluster Raw p": f"{r['Cluster Raw p']:.3f}",
            "Cluster Holm p": f"{r['Cluster Holm p']:.3f}",
            "Significant": "Yes" if r["Cluster Significant"] else "No",
            "Pair Delta %": f"{r['Pair-Level Delta %']:+.1f}%",
            "Pair 95% CI": f"[{r['Pair-Level 95% CI Low']:+.1f}, {r['Pair-Level 95% CI High']:+.1f}]",
            "Pair Raw p": f"{r['Pair-Level Raw p']:.3f}",
            "Pair Holm p": f"{r['Pair-Level Holm p']:.3f}",
        }
        if r["Metric_Key"] == "approach_wait_gap_s":
            row_dict["Abs Diff (s)"] = f"{r['Abs Diff']:+.2f} s"
            row_dict["Abs Diff 95% CI"] = f"[{r['Abs Diff 95% CI Low']:+.2f}, {r['Abs Diff 95% CI High']:+.2f}]"
        else:
            row_dict["Abs Diff (s)"] = "n/a"
            row_dict["Abs Diff 95% CI"] = "n/a"
        t2_rows.append(row_dict)
    df_t2 = pd.DataFrame(t2_rows)

    # Format Table 3: Secondary metrics
    df_t3_raw = df_full[~df_full["Is_Primary"]].copy()
    t3_rows = []
    for _, r in df_t3_raw.iterrows():
        t3_rows.append({
            "Comparison": r["Comparison"],
            "Subset": r["Subset"],
            "Metric": r["Metric"],
            "Definition": METRIC_DEFINITIONS[r["Metric_Key"]],
            "Hybrid Mean": f"{r['Hybrid Mean']:.2f}",
            "Ref Mean": f"{r['Ref Mean']:.2f}",
            "Delta %": f"{r['Delta %']:+.1f}%",
            "Seed-Clustered 95% CI": f"[{r['Cluster 95% CI Low']:+.1f}, {r['Cluster 95% CI High']:+.1f}]",
            "Cluster Raw p": f"{r['Cluster Raw p']:.3f}",
            "Pair Delta %": f"{r['Pair-Level Delta %']:+.1f}%",
            "Pair 95% CI": f"[{r['Pair-Level 95% CI Low']:+.1f}, {r['Pair-Level 95% CI High']:+.1f}]",
            "Pair Raw p": f"{r['Pair-Level Raw p']:.3f}",
        })
    df_t3 = pd.DataFrame(t3_rows)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df_full.to_csv(TABLES_DIR / "seed_clustered_bootstrap_full.csv", index=False)
    df_t2.to_csv(TABLES_DIR / "table2_primary_comparisons.csv", index=False)
    df_t3.to_csv(TABLES_DIR / "table3_secondary_metrics.csv", index=False)
    df_verdicts.to_csv(TABLES_DIR / "sensitivity_verdict_comparison.csv", index=False)

    print(f"[BOOTSTRAP] Tables saved successfully to {TABLES_DIR}:")
    print(f"  - table2_primary_comparisons.csv ({len(df_t2)} rows)")
    print(f"  - table3_secondary_metrics.csv ({len(df_t3)} rows)")
    print(f"  - sensitivity_verdict_comparison.csv ({len(df_verdicts)} rows)")

    # Print any verdict changes
    changed = df_verdicts[df_verdicts["Verdict Changed"]]
    print(f"[BOOTSTRAP] Verdict changes between cluster and pair bootstrap: {len(changed)}")
    if len(changed) > 0:
        print(changed.to_string())

    return df_full, df_t2, df_t3, df_verdicts

if __name__ == "__main__":
    run_bootstrap()
