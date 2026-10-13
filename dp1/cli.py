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
    r.add_argument("--policy", default="adaptive", choices=["fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn"])
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--gui", action="store_true", help="watch it in sumo-gui")
    r.add_argument("--decisions", action="store_true", help="print first 10 signal decisions (queue per approach -> green s)")
    r.add_argument("--model-path", type=str, default=None, help="path to trained RL model for rl_dqn policy")
    r.add_argument("--emergency-event", action="store_true", help="insert deterministic emergency vehicle")
    r.add_argument("--emergency-priority", action="store_true", help="enable traffic signal priority for emergency vehicle")
    r.add_argument("--emergency-approach", default="N", choices=["N", "S", "E", "W"], help="approach for emergency vehicle")
    r.add_argument("--emergency-depart", type=float, default=300.0, help="departure time for emergency vehicle")
    r.add_argument("--demand-level", default=C.DEFAULT_DEMAND_LEVEL, choices=["low", "medium", "heavy"], help="traffic demand intensity level")
    r.add_argument("--record-vehicles", action="store_true", help="capture per-step microscopic vehicle coordinates in telemetry")

    c = sub.add_parser("compare", help="compare policies over scenarios and seeds")
    c.add_argument("--seeds", type=int, default=len(C.SIM.seeds))
    c.add_argument("--held-out", action="store_true", help="use held-out seeds (11-15)")
    c.add_argument("--scenarios", nargs="*", default=None)
    c.add_argument("--policies", nargs="*", default=None, choices=["fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn"])
    c.add_argument("--jobs", type=int, default=1)
    c.add_argument("--model-path", type=str, default=None, help="path to trained RL model for rl_dqn policy")

    sub.add_parser("demo", help="quick fixed-vs-adaptive run on the imbalanced scenario")

    trl = sub.add_parser("train-rl", help="train a DQN policy model using Gymnasium and Stable-Baselines3")
    trl.add_argument("--scenario", default="imbalanced_ns", choices=list(C.scenarios()))
    trl.add_argument("--seed", type=int, default=1)
    trl.add_argument("--timesteps", type=int, default=1000, help="training timesteps (default 1000 for smoke/test)")
    trl.add_argument("--out", type=str, default=None, help="output model path (.zip)")

    t = sub.add_parser("tune", help="tune adaptive parameters on train seeds and evaluate on held-out seeds")
    t.add_argument("--jobs", type=int, default=8, help="number of parallel workers")
    t.add_argument("--chunk-size", type=int, default=20, help="number of configs to evaluate in this run (0 for all)")
    t.add_argument("--eval-heldout", action="store_true", help="evaluate best and default configs on held-out seeds 11-15")
    t.add_argument("--all", action="store_true", help="evaluate all remaining configs without chunk limit")

    rep = sub.add_parser("report", help="generate results/report.md from CSV data")
    rep.add_argument("--csv", type=str, default=None, help="path to results CSV (default results/all_runs.csv)")
    rep.add_argument("--out", type=str, default=None, help="path for output markdown report (default results/report.md)")
    rep.add_argument("--pdf", action="store_true", help="compile markdown report to results/report.pdf")

    ev = sub.add_parser("evaluate-research", help="run the 600-run research-grade evaluation matrix and stats pipeline")
    ev.add_argument("--preset", default="full", choices=["full", "smoke", "custom"], help="matrix preset (default: full)")
    ev.add_argument("--dry-run", action="store_true", help="preview planned matrix cells without running SUMO")
    ev.add_argument("--no-resume", action="store_true", help="do not resume; start fresh")
    ev.add_argument("--limit", type=int, default=None, help="max cells to execute in this run (for bounded chunking)")
    ev.add_argument("--jobs", type=int, default=1, help="parallel worker processes")
    ev.add_argument("--experiment-id", type=str, default=None, help="unique experiment identifier")
    ev.add_argument("--model-path", type=str, default=None, help="trained DQN checkpoint path for rl_dqn")
    ev.add_argument("--patterns", nargs="*", default=None, help="scenario patterns filter")
    ev.add_argument("--levels", nargs="*", default=None, choices=["low", "medium", "heavy"], help="demand levels filter")
    ev.add_argument("--policies", nargs="*", default=None, help="policies filter")
    ev.add_argument("--seeds", nargs="*", type=int, default=None, help="seeds filter")
    ev.add_argument("--emergency-matrix", action="store_true", help="enable emergency matrix sub-study schema")

    a = ap.parse_args()

    if a.cmd == "build":
        print("built:", build_network())
    elif a.cmd == "run":
        em_cfg = C.EmergencyConfig(
            approach=a.emergency_approach,
            depart_time_s=a.emergency_depart,
            event_enabled=a.emergency_event,
            priority_enabled=a.emergency_priority,
        )
        policy_kwargs = {"model_path": a.model_path} if (a.policy == "rl_dqn" and a.model_path) else None
        m = run_simulation(
            a.scenario,
            a.policy,
            a.seed,
            gui=a.gui,
            policy_kwargs=policy_kwargs,
            demand_level=a.demand_level,
            emergency_event=a.emergency_event,
            emergency_priority=a.emergency_priority,
            emergency_cfg=em_cfg,
            record_vehicles=a.record_vehicles,
        )
        for k, v in m.items():
            print(f"{k:>26}: {v:.2f}" if isinstance(v, float) else f"{k:>26}: {v}")
        if a.decisions:
            import pandas as pd
            em_tag = ""
            if a.emergency_event:
                em_tag = "_em_pri" if a.emergency_priority else "_em"
            dec_file = C.RESULTS_DIR / "runs" / f"{a.scenario}_{a.policy}_s{a.seed}{em_tag}" / "decisions.csv"
            if dec_file.exists():
                df_dec = pd.read_csv(dec_file).head(10)
                print(f"\n{'='*78}\nFirst 10 Decisions: queue per approach (m) -> chosen green (s)\n{'='*78}")
                print(f"{'Cycle':>5} | {'Time':>6} | {'Axis':>4} | {'N':>6} | {'S':>6} | {'E':>6} | {'W':>6} | {'Green':>6} | Decision")
                print(f"{'-'*78}")
                for _, row in df_dec.iterrows():
                    ax = row["axis"]
                    if ax == "NS":
                        own_q = max(row["q_N_m"], row["q_S_m"])
                        other_q = max(row["q_E_m"], row["q_W_m"])
                    else:
                        own_q = max(row["q_E_m"], row["q_W_m"])
                        other_q = max(row["q_N_m"], row["q_S_m"])
                    if a.policy == "pressure":
                        diff = max(0.0, own_q - other_q)
                        expl = f"diff {diff:.1f}m ({own_q:.1f}m - {other_q:.1f}m) -> green {row['green_s']:.1f}s"
                    elif a.policy == "adaptive":
                        expl = f"queue {own_q:.1f}m -> green {row['green_s']:.1f}s"
                    elif a.policy == "rl_dqn":
                        expl = f"rl dqn policy -> nominal {row['green_s']:.1f}s (actual {row.get('actual_green_s', row['green_s']):.1f}s)"
                    else:
                        expl = f"fixed timing -> green {row['green_s']:.1f}s"
                    print(f"{int(row['cycle']):>5} | {row['t']:>5.0f}s | {ax:>4} | {row['q_N_m']:>5.1f}m | {row['q_S_m']:>5.1f}m | {row['q_E_m']:>5.1f}m | {row['q_W_m']:>5.1f}m | {row['green_s']:>5.1f}s | {expl}")
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
        df = cmp.run_matrix(a.scenarios, policies=policies, seeds=seeds, jobs=a.jobs, model_path=a.model_path)
        cmp.aggregate(df)
        print("\n", cmp.improvement_table(df).to_string())
        cmp.plot_all(df)
        try:
            cmp.plot_queue_timeseries()
        except FileNotFoundError:
            pass
        print(f"\nResults written to {C.RESULTS_DIR}")
    elif a.cmd == "train-rl":
        from .rl.train import train_dqn
        build_network()
        out_p, meta_p = train_dqn(scenario=a.scenario, seed=a.seed, timesteps=a.timesteps, out_path=a.out, verbose=1)
        print(f"Model saved: {out_p}")
        print(f"Metadata saved: {meta_p}")
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
        out = report.generate_report(csv_file=a.csv, out_file=a.out, pdf=a.pdf)
        print(f"Report written to {out}")
        if a.pdf:
            print(f"PDF written to {out.with_suffix('.pdf')}")
    elif a.cmd == "evaluate-research":
        from .research.orchestrator import run_research_experiment
        build_network()
        patterns = tuple(a.patterns) if a.patterns else None
        levels = tuple(a.levels) if a.levels else None
        policies = tuple(a.policies) if a.policies else None
        seeds = tuple(a.seeds) if a.seeds else None
        matrix, exp_dir = run_research_experiment(
            experiment_id=a.experiment_id,
            preset=a.preset,
            patterns=patterns,
            levels=levels,
            policies=policies,
            seeds=seeds,
            limit=a.limit,
            jobs=a.jobs,
            resume=not a.no_resume,
            dry_run=a.dry_run,
            model_path=a.model_path,
            emergency_matrix=a.emergency_matrix,
        )


if __name__ == "__main__":
    main()
