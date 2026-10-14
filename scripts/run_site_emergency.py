import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dp1.research.emergency_matrix import run_emergency_evaluation

if __name__ == "__main__":
    print("Starting Marathahalli Site Emergency Matrix Evaluation (360 runs)...")
    res = run_emergency_evaluation(jobs=8, network="marathahalli")
    print(f"Done! Artifacts saved to: {res}")
