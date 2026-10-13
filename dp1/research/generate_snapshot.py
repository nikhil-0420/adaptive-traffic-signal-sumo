"""Generate a verified static demo-data snapshot from actual repository artifacts.

Writes outputs to frontend/public/demo-data/ with a complete manifest.
"""
import csv
import json
import time
from pathlib import Path

from dp1 import config as C

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results"
DEMO_DIR = REPO_ROOT / "frontend" / "public" / "demo-data"


def _read_csv(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = []
        for r in reader:
            rec = {}
            for k, v in r.items():
                if v == "" or v is None:
                    rec[k] = None
                else:
                    try:
                        rec[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        if v.lower() == "true":
                            rec[k] = True
                        elif v.lower() == "false":
                            rec[k] = False
                        else:
                            rec[k] = v
            records.append(rec)
        return records


def generate_snapshot():
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    source_paths = []

    # 1. all_runs.csv -> all_runs.json
    all_runs_file = RESULTS_DIR / "all_runs.csv"
    runs_data = []
    if all_runs_file.exists():
        runs_data = _read_csv(all_runs_file)
        for r in runs_data:
            if "run_id" not in r or not r["run_id"]:
                r["run_id"] = f"{r.get('scenario')}_{r.get('policy')}_s{r.get('seed')}"
        source_paths.append(str(all_runs_file.relative_to(REPO_ROOT)))
        with open(DEMO_DIR / "all_runs.json", "w", encoding="utf-8") as f:
            json.dump(runs_data, f, indent=2)

    # 2. summary.json
    summary = {
        "total_runs": len(runs_data),
        "total_runs_evaluated": len(runs_data),
        "total_experiments": 1,
        "scenarios": list(C.scenarios()),
        "policies": ["fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn"],
        "demand_levels": ["low", "medium", "heavy"],
        "dataset_label": "Saved simulation snapshot",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(DEMO_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 3. Sample runs with timeseries and decisions
    sample_run_ids = [
        "imbalanced_ns_adaptive_s1",
        "imbalanced_ns_fixed_s1",
        "balanced_adaptive_s1",
        "imbalanced_ns_fixed_s999",
        "imbalanced_ns_adaptive_s1_em_pri",
        "imbalanced_ns_fixed_s1_em",
        "surge_north_pressure_s1",
    ]
    sample_runs_dir = DEMO_DIR / "runs"
    sample_runs_dir.mkdir(parents=True, exist_ok=True)

    for run_id in sample_run_ids:
        src_dir = RESULTS_DIR / "runs" / run_id
        if not src_dir.exists():
            continue
        dest_dir = sample_runs_dir / run_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        # timeseries.csv -> timeseries.json (downsampled by 5 for compact static bundle)
        ts_csv = src_dir / "timeseries.csv"
        if ts_csv.exists():
            ts_records = _read_csv(ts_csv)
            source_paths.append(str(ts_csv.relative_to(REPO_ROOT)))
            # Downsample to ~300 points for web performance
            step = max(1, len(ts_records) // 300)
            sampled = ts_records[::step]
            with open(dest_dir / "timeseries.json", "w", encoding="utf-8") as f:
                json.dump({"run_id": run_id, "total_points": len(sampled), "points": sampled}, f)

        # decisions.csv -> decisions.json
        dec_csv = src_dir / "decisions.csv"
        if dec_csv.exists():
            dec_records = _read_csv(dec_csv)
            source_paths.append(str(dec_csv.relative_to(REPO_ROOT)))
            with open(dest_dir / "decisions.json", "w", encoding="utf-8") as f:
                json.dump({"run_id": run_id, "total_decisions": len(dec_records), "decisions": dec_records}, f)

        # metrics.json
        met_json = src_dir / "metrics.json"
        if met_json.exists():
            with open(met_json, "r", encoding="utf-8") as f:
                m_data = json.load(f)
            source_paths.append(str(met_json.relative_to(REPO_ROOT)))
            with open(dest_dir / "metrics.json", "w", encoding="utf-8") as f:
                json.dump(m_data, f, indent=2)

    # 4. Research experiment: exp_smoke_test
    exp_src = RESULTS_DIR / "research" / "exp_smoke_test"
    if exp_src.exists():
        exp_dest = DEMO_DIR / "experiments" / "exp_smoke_test"
        exp_dest.mkdir(parents=True, exist_ok=True)

        for fname in [
            "manifest.json", "report.md", "aggregate.csv", "raw_runs.csv",
            "paired_deltas.csv", "fairness_by_approach.csv", "matrix_status.csv"
        ]:
            src_file = exp_src / fname
            if src_file.exists():
                source_paths.append(str(src_file.relative_to(REPO_ROOT)))
                if fname.endswith(".csv"):
                    records = _read_csv(src_file)
                    json_name = fname.replace(".csv", ".json")
                    with open(exp_dest / json_name, "w", encoding="utf-8") as f:
                        json.dump(records, f, indent=2)
                    # Also write raw CSV for browser file downloads
                    with open(exp_dest / fname, "w", encoding="utf-8") as f:
                        f.write(src_file.read_text(encoding="utf-8"))
                elif fname.endswith(".json"):
                    with open(src_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(exp_dest / fname, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                elif fname.endswith(".md"):
                    with open(src_file, "r", encoding="utf-8") as f:
                        md_data = f.read()
                    with open(exp_dest / fname, "w", encoding="utf-8") as f:
                        f.write(md_data)

    # 5. Write manifest.json
    manifest = {
        "schema_version": "dp1.v1",
        "dataset_label": "DP1 Verified Simulation Snapshot",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_repository": "Alliance University DP1 Traffic Signal Optimization",
        "verified": True,
        "total_runs": len(runs_data),
        "runs": [r["run_id"] for r in runs_data],
        "experiments": ["exp_smoke_test"],
        "source_paths": source_paths,
    }
    with open(DEMO_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated static demo snapshot with {len(source_paths)} verified source artifacts into {DEMO_DIR}")


if __name__ == "__main__":
    generate_snapshot()
