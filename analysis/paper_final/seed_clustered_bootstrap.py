"""Seed-clustered bootstrap analysis for DP1 final evaluation (Seeds 131-138).

Resamples at the cluster (seed) level: draws whole seeds with replacement,
preserving within-seed correlation across traffic demand conditions.

Subsets:
1. all_6_pooled (all 6 conditions, n = 8 clusters x 6 = 48 pairs)
2. 3_non_stationary (ramp_peak-medium, surge_shift-medium, lane_closure-medium, n = 8 clusters x 3 = 24 pairs)
3. 3_stationary (balanced-low, balanced-heavy, imbalanced_orr-heavy, n = 8 clusters x 3 = 24 pairs)

Metrics:
- p95_wait_s: p95 wait (s)
- gt_ext_max_queue_m: extended max queue (m)
- approach_wait_gap_s: wait gap (s)
- mean_wait_s: mean wait (s)
- gt_ext_avg_queue_m: mean queue (m)

10,000 resamples, seed = 42.
Step-down Holm-Bonferroni correction applied across the 3 primary metrics within each comparison & subset.
"""
from pathlib import Path
import pandas as pd
import numpy as np

DATA_CSV = Path("analysis/paper_final/raw_extracted_runs.csv")
OUT_CSV = Path("paper_final/tables/seed_clustered_bootstrap_comparison.csv")

COMPARATORS = [
    "webster_measured",
    "webster_recalc",
    "fixed",
    "sumo_actuated",
    "hybrid_oracle_seeded",
]

SUBSETS = {
    "all_6_pooled": None,
    "3_non_stationary": ["ramp_peak-medium", "surge_shift-medium", "lane_closure-medium"],
    "3_stationary": ["balanced-low", "balanced-heavy", "imbalanced_orr-heavy"],
}

PRIMARY_METRICS = ["p95_wait_s", "gt_ext_max_queue_m", "approach_wait_gap_s"]
ALL_METRICS = [
    "p95_wait_s",
    "gt_ext_max_queue_m",
    "approach_wait_gap_s",
    "mean_wait_s",
    "gt_ext_avg_queue_m",
]

METRIC_LABELS = {
    "p95_wait_s": "p95 wait (s)",
    "gt_ext_max_queue_m": "extended max queue (m)",
    "approach_wait_gap_s": "wait gap (s)",
    "mean_wait_s": "mean wait (s)",
    "gt_ext_avg_queue_m": "mean queue (m)",
}

def run_seed_clustered_bootstrap(df, n_boot=10000, seed=42):
    rng = np.random.default_rng(seed)
    unique_seeds = np.array(sorted(df["seed"].unique()))
    n_seeds = len(unique_seeds)
    boot_indices = rng.integers(0, n_seeds, size=(n_boot, n_seeds))
    
    rows = []
    
    for comp in COMPARATORS:
        for sub_name, conds in SUBSETS.items():
            if conds is not None:
                sub_df = df[df["condition"].isin(conds)].copy()
            else:
                sub_df = df.copy()
                
            prop_df = sub_df[sub_df["policy"] == "hybrid_queue_adaptive"]
            comp_df = sub_df[sub_df["policy"] == comp]
            merged = pd.merge(prop_df, comp_df, on=["condition", "seed"], suffixes=("_hyb", "_ref"))
            
            seed_deltas = {m: [] for m in ALL_METRICS}
            pair_deltas = {m: [] for m in ALL_METRICS}
            hyb_means = {m: float(merged[f"{m}_hyb"].mean()) for m in ALL_METRICS}
            ref_means = {m: float(merged[f"{m}_ref"].mean()) for m in ALL_METRICS}
            
            for s in unique_seeds:
                s_rows = merged[merged["seed"] == s]
                for m in ALL_METRICS:
                    vh = s_rows[f"{m}_hyb"].to_numpy(dtype=float)
                    vr = s_rows[f"{m}_ref"].to_numpy(dtype=float)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        d = np.where(vr != 0, ((vh - vr) / vr) * 100.0, 0.0)
                    seed_deltas[m].append(np.mean(d))
                    pair_deltas[m].extend(d.tolist())
                    
            sub_res = {}
            for m in ALL_METRICS:
                s_arr = np.array(seed_deltas[m]) # shape (n_seeds,)
                cluster_sample_delta = float(np.mean(s_arr))
                pair_sample_delta = float(np.mean(pair_deltas[m]))
                matches_pair = "Y" if abs(cluster_sample_delta - pair_sample_delta) < 1e-4 else "N"
                
                # Bootstrap distribution of cluster mean
                boot_means = np.mean(s_arr[boot_indices], axis=1)
                ci_low = float(np.percentile(boot_means, 2.5))
                ci_high = float(np.percentile(boot_means, 97.5))
                
                # Two-sided empirical p-value
                if cluster_sample_delta >= 0:
                    raw_p = 2.0 * float(np.mean(boot_means <= 0))
                else:
                    raw_p = 2.0 * float(np.mean(boot_means >= 0))
                raw_p = min(1.0, max(0.0, raw_p))
                
                # Pair-level bootstrap (independent pair resampling)
                pair_arr = np.array(pair_deltas[m])
                rng_pair = np.random.default_rng(seed)
                pair_boot_idx = rng_pair.integers(0, len(pair_arr), size=(n_boot, len(pair_arr)))
                pair_boot_means = np.mean(pair_arr[pair_boot_idx], axis=1)
                pair_ci_low = float(np.percentile(pair_boot_means, 2.5))
                pair_ci_high = float(np.percentile(pair_boot_means, 97.5))
                if pair_sample_delta >= 0:
                    pair_raw_p = 2.0 * float(np.mean(pair_boot_means <= 0))
                else:
                    pair_raw_p = 2.0 * float(np.mean(pair_boot_means >= 0))
                pair_raw_p = min(1.0, max(0.0, pair_raw_p))
                
                sub_res[m] = {
                    "hyb_mean": hyb_means[m],
                    "ref_mean": ref_means[m],
                    "delta_pct": cluster_sample_delta,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "raw_p": raw_p,
                    "matches_pair": matches_pair,
                    "pair_delta_pct": pair_sample_delta,
                    "pair_ci_low": pair_ci_low,
                    "pair_ci_high": pair_ci_high,
                    "pair_raw_p": pair_raw_p,
                }
                
            # Holm-Bonferroni correction across the 3 PRIMARY metrics within this comparison + subset
            primary_p_tuples = [(m, sub_res[m]["raw_p"]) for m in PRIMARY_METRICS]
            primary_p_tuples.sort(key=lambda x: x[1])
            holm_p_dict = {}
            m_tests = len(PRIMARY_METRICS) # 3
            running_max = 0.0
            for rank, (m, p) in enumerate(primary_p_tuples):
                adj_p = min(1.0, p * (m_tests - rank))
                adj_p = max(adj_p, running_max)
                running_max = adj_p
                holm_p_dict[m] = adj_p
                
            for m in ALL_METRICS:
                h_p = holm_p_dict.get(m, "n/a (secondary)")
                r = sub_res[m]
                rows.append({
                    "Comparison": f"hybrid vs {comp}",
                    "Subset": sub_name,
                    "Metric": METRIC_LABELS[m],
                    "Hybrid Mean": f"{r['hyb_mean']:.2f}",
                    "Ref Mean": f"{r['ref_mean']:.2f}",
                    "Delta %": f"{r['delta_pct']:+.1f}%",
                    "Cluster 95% CI": f"[{r['ci_low']:+.1f}, {r['ci_high']:+.1f}]",
                    "Cluster Raw p": f"{r['raw_p']:.3f}",
                    "Cluster Holm p": f"{h_p:.3f}" if isinstance(h_p, float) else h_p,
                    "Delta Matches Pair (Y/N)": r["matches_pair"],
                    "Pair-Level Delta %": f"{r['pair_delta_pct']:+.1f}%",
                    "Pair-Level 95% CI": f"[{r['pair_ci_low']:+.1f}, {r['pair_ci_high']:+.1f}]",
                    "Pair-Level Raw p": f"{r['pair_raw_p']:.3f}",
                })
                
    return pd.DataFrame(rows)

def main():
    df = pd.read_csv(DATA_CSV)
    print(f"Loaded {len(df)} records from {DATA_CSV}")
    res_df = run_seed_clustered_bootstrap(df)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(OUT_CSV, index=False)
    print(f"Saved {len(res_df)} rows to {OUT_CSV}")

if __name__ == "__main__":
    main()
