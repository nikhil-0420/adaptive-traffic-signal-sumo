"""Command line:  python -m dp1.cli <build | run | compare | demo>"""
import argparse
from . import config as C
from .network import build_network
from .runner import run_simulation


def main():
    ap = argparse.ArgumentParser(prog="dp1")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="generate the junction network + detectors")

    r = sub.add_parser("run", help="run one simulation")
    r.add_argument("--scenario", default="imbalanced_ns", choices=list(C.scenarios()))
    r.add_argument("--policy", default="adaptive", choices=["fixed", "fixed_webster", "adaptive", "pressure"])
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--gui", action="store_true", help="watch it in sumo-gui")

    c = sub.add_parser("compare", help="compare policies over scenarios and seeds")
    c.add_argument("--seeds", type=int, default=len(C.SIM.seeds))
    c.add_argument("--held-out", action="store_true", help="use held-out seeds (11-15)")
    c.add_argument("--scenarios", nargs="*", default=None)
    c.add_argument("--policies", nargs="*", default=None, choices=["fixed", "fixed_webster", "adaptive", "pressure"])
    c.add_argument("--jobs", type=int, default=1)

    sub.add_parser("demo", help="quick fixed-vs-adaptive run on the imbalanced scenario")

    t = sub.add_parser("tune", help="tune adaptive parameters on train seeds and evaluate on held-out seeds")
    t.add_argument("--jobs", type=int, default=8, help="number of parallel workers")
    t.add_argument("--chunk-size", type=int, default=20, help="number of configs to evaluate in this run (0 for all)")
    t.add_argument("--eval-heldout", action="store_true", help="evaluate best and default configs on held-out seeds 11-15")
    t.add_argument("--all", action="store_true", help="evaluate all remaining configs without chunk limit")

    rep = sub.add_parser("report", help="generate results/report.md from CSV data")
    rep.add_argument("--csv", type=str, default=None, help="path to results CSV (default results/all_runs.csv)")
    rep.add_argument("--out", type=str, default=None, help="path for output markdown report (default results/report.md)")
    a = ap.parse_args()

    if a.cmd == "build":
        print("built:", build_network())
    elif a.cmd == "run":
        m = run_simulation(a.scenario, a.policy, a.seed, gui=a.gui)
        for k, v in m.items():
            print(f"{k:>22}: {v:.2f}" if isinstance(v, float) else f"{k:>22}: {v}")
    elif a.cmd == "demo":
        build_network()
        for pol in ("fixed", "adaptive"):
            m = run_simulation("imbalanced_ns", pol, 1)
            print(f"{pol:>9}: wait {m['avg_wait_s']:.1f}s | queue {m['avg_queue_m']:.1f}m | "
                  f"done {m['completion_rate']:.0%} | cycles {m['cycles']}")
    elif a.cmd == "compare":
        from . import compare as cmp
        build_network()
        seeds = C.HELD_OUT_SEEDS if a.held_out else tuple(range(1, a.seeds + 1))
        policies = tuple(a.policies) if a.policies else ("fixed", "fixed_webster", "adaptive", "pressure")
        df = cmp.run_matrix(a.scenarios, policies=policies, seeds=seeds, jobs=a.jobs)
        cmp.aggregate(df)
        print("\n", cmp.improvement_table(df).to_string())
        cmp.plot_all(df)
        try:
            cmp.plot_queue_timeseries()
        except FileNotFoundError:
            pass
        print(f"\nResults written to {C.RESULTS_DIR}")
    elif a.cmd == "tune":
        from . import tune
        build_network()
        tune.run_tune(
            jobs=a.jobs,
            chunk_size=0 if a.all else a.chunk_size,
            eval_heldout_flag=a.eval_heldout,
        )
    elif a.cmd == "report":
        from . import report
        out = report.generate_report(csv_file=a.csv, out_file=a.out)
        print(f"Report written to {out}")


if __name__ == "__main__":
    main()
