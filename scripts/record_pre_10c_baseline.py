import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path("E:/dp1-traffic-signal")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp1.runner import run_simulation

PRE_DIR = Path("results/regression_10c_pre")
PRE_DIR.mkdir(parents=True, exist_ok=True)

test_cases = [
    ("balanced", "medium", "hybrid_queue_adaptive", 101),
    ("imbalanced_orr", "heavy", "hybrid_queue_adaptive", 101),
    ("balanced", "medium", "hybrid_oracle_seeded", 101),
]

manifest = {}
for sc, dl, pol, seed in test_cases:
    case_name = f"{sc}_{dl}_{pol}_s{seed}"
    out_dir = PRE_DIR / case_name
    print(f"Running PRE-change baseline: {case_name}...")
    res = run_simulation(
        scenario=sc,
        demand_level=dl,
        policy=pol,
        seed=seed,
        network="marathahalli",
        out_dir=out_dir,
    )
    dec_file = out_dir / "decisions.csv"
    sha = hashlib.sha256(dec_file.read_bytes()).hexdigest()
    manifest[case_name] = {
        "decisions_sha256": sha,
        "metrics": res,
    }
    print(f"  {case_name}: decisions SHA256 = {sha}")

with open(PRE_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("\nPRE-change baselines captured successfully.")
