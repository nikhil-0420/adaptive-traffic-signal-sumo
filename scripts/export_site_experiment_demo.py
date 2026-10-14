import csv
import json
import shutil
from pathlib import Path

def export_experiment(exp_name: str):
    src_dir = Path("results/research") / exp_name
    dest_dir = Path("frontend/public/demo-data/experiments") / exp_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.exists():
        print(f"Source dir {src_dir} does not exist.")
        return

    csv_files = [
        "aggregate.csv",
        "raw_runs.csv",
        "matrix_status.csv",
        "fairness_by_approach.csv",
        "paired_deltas.csv",
        "paired_summary.csv",
        "raw_emergency_runs.csv",
    ]
    for fname in csv_files:
        fpath = src_dir / fname
        if fpath.exists():
            shutil.copy2(fpath, dest_dir / fname)
            # convert to json
            with open(fpath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            json_fname = fname.replace(".csv", ".json")
            with open(dest_dir / json_fname, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2)
            print(f"Exported {fname} and {json_fname} ({len(rows)} rows)")

    # copy json and md files directly
    for fname in ["manifest.json", "report.md"]:
        fpath = src_dir / fname
        if fpath.exists():
            shutil.copy2(fpath, dest_dir / fname)
            print(f"Copied {fname}")

if __name__ == "__main__":
    export_experiment("exp_marathahalli_site")
    export_experiment("exp_marathahalli_emergency_360")
