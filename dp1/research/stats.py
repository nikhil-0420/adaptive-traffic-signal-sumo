"""Statistical aggregation, paired bootstrap confidence intervals, and fairness metrics."""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .. import config as C

SUMMARY_METRICS = [
    "avg_wait_s",
    "avg_time_loss_s",
    "avg_trip_s",
    "p95_wait_s",
    "avg_queue_m",
    "max_queue_m",
    "throughput_veh_per_h",
    "completion_rate",
    "completed_in_demand_window",
    "avg_wait_NS_s",
    "avg_wait_EW_s",
    "directional_wait_disparity_s",
    "approach_wait_gap_s",
]


def bootstrap_percentile_ci(
    data: np.ndarray,
    n_resamples: int = 10_000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> Tuple[float, float, float]:
    """Compute deterministic paired-bootstrap percentile confidence interval.

    Returns:
        Tuple[float, float, float]: (point_estimate, ci_lower, ci_upper)
    """
    clean_data = data[~np.isnan(data)]
    n = len(clean_data)
    if n == 0:
        return float("nan"), float("nan"), float("nan")

    point_estimate = float(np.mean(clean_data))
    if n == 1:
        return point_estimate, point_estimate, point_estimate

    rng = np.random.default_rng(random_seed)
    # Generate bootstrap samples of shape (n_resamples, n)
    indices = rng.integers(0, n, size=(n_resamples, n))
    resample_means = np.mean(clean_data[indices], axis=1)

    alpha = 1.0 - confidence_level
    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_lower = float(np.percentile(resample_means, lower_pct))
    ci_upper = float(np.percentile(resample_means, upper_pct))
    return point_estimate, ci_lower, ci_upper


def compute_aggregates(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean and sample standard deviation over seeds for every condition."""
    if raw_df.empty:
        return pd.DataFrame()

    group_cols = ["pattern", "demand_level", "policy"]
    agg_funcs = {}
    for m in SUMMARY_METRICS:
        if m in raw_df.columns:
            agg_funcs[m] = ["mean", "std"]

    g = raw_df.groupby(group_cols, as_index=False).agg(agg_funcs)

    # Flatten hierarchical columns
    flat_cols = []
    for col in g.columns:
        if isinstance(col, tuple):
            if col[1]:
                flat_cols.append(f"{col[0]}_{col[1]}")
            else:
                flat_cols.append(col[0])
        else:
            flat_cols.append(col)
    g.columns = flat_cols

    # Add seed count
    counts = raw_df.groupby(group_cols)["seed"].count().reset_index().rename(columns={"seed": "n_seeds"})
    merged = pd.merge(counts, g, on=group_cols)
    return merged.round(3)


def compute_paired_deltas(
    raw_df: pd.DataFrame,
    reference_policy: str = "fixed",
    n_bootstrap: int = 10_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Compute paired candidate minus reference deltas and bootstrap 95% CIs.

    Sign convention: negative delta for avg_wait_s and avg_time_loss_s favors candidate.
    """
    if raw_df.empty:
        return pd.DataFrame()

    ref_df = raw_df[raw_df["policy"] == reference_policy]
    if ref_df.empty:
        return pd.DataFrame()

    rows = []
    patterns = raw_df["pattern"].unique()
    levels = raw_df["demand_level"].unique()
    candidates = [p for p in raw_df["policy"].unique() if p != reference_policy]

    for pat in patterns:
        for lvl in levels:
            ref_sub = ref_df[(ref_df["pattern"] == pat) & (ref_df["demand_level"] == lvl)]
            if ref_sub.empty:
                continue
            ref_by_seed = {r["seed"]: r for _, r in ref_sub.iterrows()}

            for cand in candidates:
                cand_sub = raw_df[(raw_df["pattern"] == pat) & (raw_df["demand_level"] == lvl) & (raw_df["policy"] == cand)]
                if cand_sub.empty:
                    continue

                paired_wait = []
                paired_loss = []
                paired_queue = []
                paired_tp = []

                for _, cr in cand_sub.iterrows():
                    sd = cr["seed"]
                    if sd in ref_by_seed:
                        rr = ref_by_seed[sd]
                        paired_wait.append(cr["avg_wait_s"] - rr["avg_wait_s"])
                        paired_loss.append(cr["avg_time_loss_s"] - rr["avg_time_loss_s"])
                        paired_queue.append(cr["avg_queue_m"] - rr["avg_queue_m"])
                        paired_tp.append(cr["throughput_veh_per_h"] - rr["throughput_veh_per_h"])

                n_pairs = len(paired_wait)
                missing = len(cand_sub) - n_pairs

                w_mean, w_lo, w_hi = bootstrap_percentile_ci(
                    np.array(paired_wait), n_resamples=n_bootstrap, random_seed=seed
                )
                l_mean, l_lo, l_hi = bootstrap_percentile_ci(
                    np.array(paired_loss), n_resamples=n_bootstrap, random_seed=seed + 1
                )

                rows.append({
                    "pattern": pat,
                    "demand_level": lvl,
                    "policy": cand,
                    "reference_policy": reference_policy,
                    "n_pairs": n_pairs,
                    "missing_pairs": missing,
                    # Wait deltas (s)
                    "delta_wait_mean_s": round(w_mean, 2),
                    "delta_wait_ci_lower_s": round(w_lo, 2),
                    "delta_wait_ci_upper_s": round(w_hi, 2),
                    # Time loss deltas (s)
                    "delta_time_loss_mean_s": round(l_mean, 2),
                    "delta_time_loss_ci_lower_s": round(l_lo, 2),
                    "delta_time_loss_ci_upper_s": round(l_hi, 2),
                    # Queue & Throughput deltas
                    "delta_queue_mean_m": round(float(np.mean(paired_queue)), 2) if paired_queue else float("nan"),
                    "delta_throughput_mean_vph": round(float(np.mean(paired_tp)), 2) if paired_tp else float("nan"),
                })

    return pd.DataFrame(rows)


def compute_fairness_by_approach(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Breakdown performance per approach (N, S, E, W) for each pattern x level x policy."""
    if raw_df.empty:
        return pd.DataFrame()

    rows = []
    group_cols = ["pattern", "demand_level", "policy"]
    grouped = raw_df.groupby(group_cols)

    for (pat, lvl, pol), grp in grouped:
        for a in C.APPROACHES:
            # Per-approach metrics
            n_col = f"n_completed_{a}"
            w_col = f"avg_wait_{a}_s"
            p95_col = f"p95_wait_{a}_s"
            q_mean_col = f"avg_queue_{a}_m"
            q_max_col = f"max_queue_{a}_m"

            n_val = grp[n_col].mean() if n_col in grp.columns else float("nan")
            w_val = grp[w_col].mean() if w_col in grp.columns else float("nan")
            p95_val = grp[p95_col].mean() if p95_col in grp.columns else float("nan")
            q_mean = grp[q_mean_col].mean() if q_mean_col in grp.columns else float("nan")
            q_max = grp[q_max_col].max() if q_max_col in grp.columns else float("nan")

            rows.append({
                "pattern": pat,
                "demand_level": lvl,
                "policy": pol,
                "approach": a,
                "n_completed_mean": round(n_val, 1) if not np.isnan(n_val) else None,
                "avg_wait_s": round(w_val, 2) if not np.isnan(w_val) else None,
                "p95_wait_s": round(p95_val, 2) if not np.isnan(p95_val) else None,
                "avg_queue_m": round(q_mean, 2) if not np.isnan(q_mean) else None,
                "max_queue_m": round(q_max, 2) if not np.isnan(q_max) else None,
            })

    return pd.DataFrame(rows)


def compute_fairness_by_direction(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Directional service disparity and approach wait gaps across seeds."""
    if raw_df.empty:
        return pd.DataFrame()

    group_cols = ["pattern", "demand_level", "policy"]
    agg_dict = {
        "avg_wait_NS_s": ["mean", "std"],
        "avg_wait_EW_s": ["mean", "std"],
        "directional_wait_disparity_s": ["mean", "std"],
        "approach_wait_gap_s": ["mean", "std"],
    }
    cols_to_agg = {k: v for k, v in agg_dict.items() if k in raw_df.columns}
    res = raw_df.groupby(group_cols, as_index=False).agg(cols_to_agg)

    flat_cols = []
    for col in res.columns:
        if isinstance(col, tuple):
            if col[1]:
                flat_cols.append(f"{col[0]}_{col[1]}")
            else:
                flat_cols.append(col[0])
        else:
            flat_cols.append(col)
    res.columns = flat_cols
    return res.round(2)


def compute_paired_best_policy_analysis(
    raw_df: pd.DataFrame,
    n_bootstrap: int = 10_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Perform paired statistical comparison between best candidate and runner-up per condition.

    Computes the exact paired difference per identical simulation seed:
        Delta_paired(seed) = Wait_best(seed) - Wait_runner_up(seed)
    and bootstraps the mean paired difference to form a 95% percentile confidence interval.
    If 0 is included in [CI_lower, CI_upper], the outcome is classified as a Statistical Tie.
    If CI_upper < 0, the primary candidate is statistically significantly superior (p < 0.05).
    """
    if raw_df.empty:
        return pd.DataFrame()

    results = []
    patterns = raw_df["pattern"].unique()
    levels = raw_df["demand_level"].unique()

    for pat in patterns:
        for lvl in levels:
            sub = raw_df[(raw_df["pattern"] == pat) & (raw_df["demand_level"] == lvl)]
            if sub.empty:
                continue

            pol_means = sub.groupby("policy")["avg_wait_s"].mean().sort_values()
            if len(pol_means) == 0:
                continue

            best_pol = pol_means.index[0]
            best_mean = pol_means.iloc[0]

            if len(pol_means) > 1:
                runner_up_pol = pol_means.index[1]
                runner_up_mean = pol_means.iloc[1]

                best_rows = {r["seed"]: r["avg_wait_s"] for _, r in sub[sub["policy"] == best_pol].iterrows()}
                runner_up_rows = {r["seed"]: r["avg_wait_s"] for _, r in sub[sub["policy"] == runner_up_pol].iterrows()}

                paired_diffs = []
                for sd, b_wait in best_rows.items():
                    if sd in runner_up_rows:
                        paired_diffs.append(b_wait - runner_up_rows[sd])

                if paired_diffs:
                    d_mean, d_lo, d_hi = bootstrap_percentile_ci(
                        np.array(paired_diffs), n_resamples=n_bootstrap, random_seed=seed
                    )
                    is_tie = (d_lo <= 0.0 <= d_hi)
                    if is_tie:
                        classification = f"TIE (`{best_pol}` ~ `{runner_up_pol}`)"
                        status = "TIE"
                        details = f"Paired delta: {d_mean:+.2f}s [{d_lo:+.2f}, {d_hi:+.2f}] includes 0 (statistically indistinguishable at 95% CI)"
                    else:
                        classification = f"WINNER (`{best_pol}`)"
                        status = "WINNER"
                        details = f"Paired delta: {d_mean:+.2f}s [{d_lo:+.2f}, {d_hi:+.2f}] strictly excludes 0 (statistically distinguishable at 95% CI)"

                    results.append({
                        "pattern": pat,
                        "demand_level": lvl,
                        "primary_leader": best_pol,
                        "primary_mean_wait_s": round(best_mean, 2),
                        "secondary_candidate": runner_up_pol,
                        "secondary_mean_wait_s": round(runner_up_mean, 2),
                        "paired_delta_mean_s": round(d_mean, 2),
                        "paired_delta_ci_lower_s": round(d_lo, 2),
                        "paired_delta_ci_upper_s": round(d_hi, 2),
                        "n_paired_seeds": len(paired_diffs),
                        "status": status,
                        "classification": classification,
                        "details": details,
                    })
            else:
                results.append({
                    "pattern": pat,
                    "demand_level": lvl,
                    "primary_leader": best_pol,
                    "primary_mean_wait_s": round(best_mean, 2),
                    "secondary_candidate": None,
                    "secondary_mean_wait_s": None,
                    "paired_delta_mean_s": 0.0,
                    "paired_delta_ci_lower_s": 0.0,
                    "paired_delta_ci_upper_s": 0.0,
                    "n_paired_seeds": len(sub),
                    "status": "SOLE_CANDIDATE",
                    "classification": f"`{best_pol}`",
                    "details": "Single policy evaluated",
                })

    return pd.DataFrame(results)

