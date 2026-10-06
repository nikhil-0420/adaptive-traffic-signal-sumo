"""Run the full experiment matrix (scenarios x policies x seeds) and produce tables + plots."""
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config as C
from .runner import run_simulation

METRICS = ["avg_wait_s", "avg_time_loss_s", "avg_queue_m", "max_queue_m", "throughput_veh_per_h", "completion_rate"]


def _one(args):
    return run_simulation(*args)


def run_matrix(scenarios=None, policies=("fixed", "fixed_webster", "adaptive"), seeds=C.SIM.seeds, jobs=1):
    scenarios = scenarios or list(C.scenarios().keys())
    jobs_list = [(s, p, sd) for s in scenarios for p in policies for sd in seeds]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            rows = list(ex.map(_one, jobs_list))
    else:
        rows = []
        for j in jobs_list:
            r = run_simulation(*j)
            print(f"  {r['scenario']:<14} {r['policy']:<9} seed={r['seed']}  wait={r['avg_wait_s']:.1f}s  "
                  f"queue={r['avg_queue_m']:.1f}m  done={r['completion_rate']:.0%}")
            rows.append(r)
    df = pd.DataFrame(rows)
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.RESULTS_DIR / "all_runs.csv", index=False)
    return df


def aggregate(df):
    g = df.groupby(["scenario", "policy"])[METRICS].agg(["mean", "std"])
    g.columns = [f"{m}_{s}" for m, s in g.columns]
    g = g.reset_index()
    g.to_csv(C.RESULTS_DIR / "aggregate.csv", index=False)
    return g


def improvement_table(df):
    m = df.groupby(["scenario", "policy"])[["avg_wait_s", "avg_queue_m", "throughput_veh_per_h"]].mean().unstack("policy")
    out = pd.DataFrame(index=m.index)
    has_webster = ("avg_wait_s", "fixed_webster") in m.columns
    for col, better_low in (("avg_wait_s", True), ("avg_queue_m", True), ("throughput_veh_per_h", False)):
        fx = m[(col, "fixed")]
        ad = m[(col, "adaptive")]
        out[f"{col}_fixed"] = fx.round(2)
        if has_webster:
            wb = m[(col, "fixed_webster")]
            out[f"{col}_webster"] = wb.round(2)
        out[f"{col}_adaptive"] = ad.round(2)
        out[f"{col}_change_%"] = ((fx - ad) / fx * 100 if better_low else (ad - fx) / fx * 100).round(1)
        if has_webster:
            out[f"{col}_adv_vs_webster_%"] = ((wb - ad) / wb * 100 if better_low else (ad - wb) / wb * 100).round(1)
    out.to_csv(C.RESULTS_DIR / "improvement.csv")
    return out


def plot_all(df):
    scen = list(df["scenario"].unique())
    pols = [p for p in ("fixed", "fixed_webster", "adaptive") if p in df["policy"].unique()]
    colors = {"fixed": "#8A94A6", "fixed_webster": "#D97706", "adaptive": "#0E7C86"}
    for metric, title, fname in (("avg_wait_s", "Average waiting time per vehicle (s) - lower is better", "wait_time.png"),
                                 ("avg_queue_m", "Average queue length (m) - lower is better", "queue_length.png")):
        fig, ax = plt.subplots(figsize=(8.5, 4.2))
        n_pol = len(pols)
        w = 0.8 / n_pol
        for i, pol in enumerate(pols):
            sub = df[df.policy == pol].groupby("scenario")[metric].agg(["mean", "std"]).reindex(scen)
            ax.bar([x + (i - (n_pol - 1) / 2.0) * w for x in range(len(scen))], sub["mean"], w, yerr=sub["std"].fillna(0),
                   capsize=3, label=pol, color=colors.get(pol, "#8A94A6"))
        ax.set_xticks(range(len(scen))); ax.set_xticklabels(scen)
        ax.set_title(title); ax.legend(); ax.grid(axis="y", alpha=0.3)
        fig.tight_layout(); fig.savefig(C.RESULTS_DIR / fname, dpi=150); plt.close(fig)


def plot_queue_timeseries(scenario="imbalanced_ns", seed=1):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, pol in zip(axes, ("fixed", "adaptive")):
        ts = pd.read_csv(C.RESULTS_DIR / "runs" / f"{scenario}_{pol}_s{seed}" / "timeseries.csv")
        for a in C.APPROACHES:
            ax.plot(ts["t"], ts[f"q_{a}"], label=a, lw=1)
        ax.set_title(f"{pol}  ({scenario}, seed {seed})"); ax.set_xlabel("time (s)"); ax.grid(alpha=0.3)
    axes[0].set_ylabel("queue length (m)"); axes[0].legend(title="approach")
    fig.tight_layout(); fig.savefig(C.RESULTS_DIR / "queue_timeseries.png", dpi=150); plt.close(fig)
