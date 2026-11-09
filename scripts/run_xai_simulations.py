"""Master runner for exploratory XAI simulations (Items 4 and 5).
Seeds: 101-110 ONLY.
Outputs: results/research/exp_xai_exploratory/
"""
import concurrent.futures
import csv
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Any

# Root setup
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dp1.runner import run_simulation
from dp1 import config as C

EXP_BASE = ROOT_DIR / "results" / "research" / "exp_xai_exploratory"
ABLATION_DIR = EXP_BASE / "ablation"
SENSITIVITY_DIR = EXP_BASE / "sensitivity"

ABLATION_DIR.mkdir(parents=True, exist_ok=True)
SENSITIVITY_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = [
    {"scenario": "balanced", "demand_level": "low", "key": "balanced-low"},
    {"scenario": "balanced", "demand_level": "heavy", "key": "balanced-heavy"},
    {"scenario": "imbalanced_orr", "demand_level": "heavy", "key": "imbalanced_orr-heavy"},
    {"scenario": "ramp_peak", "demand_level": "medium", "key": "ramp_peak-medium"},
    {"scenario": "surge_shift", "demand_level": "medium", "key": "surge_shift-medium"},
    {"scenario": "lane_closure", "demand_level": "medium", "key": "lane_closure-medium"},
]

DEV_SEEDS = [101, 102, 103, 104, 105]
VAL_SEEDS = [106, 107, 108, 109, 110]
SEEDS = DEV_SEEDS + VAL_SEEDS

# Item 4: 8 ablation subsets of {R-base, R-ext, R-guard}
ABLATION_VARIANTS = {
    "all_off": {"r_base": False, "r_ext": False, "r_guard": False},
    "base_only": {"r_base": True, "r_ext": False, "r_guard": False},
    "ext_only": {"r_base": False, "r_ext": True, "r_guard": False},
    "guard_only": {"r_base": False, "r_ext": False, "r_guard": True},
    "base_ext": {"r_base": True, "r_ext": True, "r_guard": False},
    "base_guard": {"r_base": True, "r_ext": False, "r_guard": True},
    "ext_guard": {"r_base": False, "r_ext": True, "r_guard": True},
    "all_on": {"r_base": True, "r_ext": True, "r_guard": True},
}

# Item 5: 8 parameter variants + webster_measured
SENSITIVITY_VARIANTS = {
    "step_2s": {"extend_step_s": 2.0},
    "step_4s": {"extend_step_s": 4.0},
    "thresh_3m": {"extend_threshold_m": 3.0},
    "thresh_6m": {"extend_threshold_m": 6.0},
    "wait_30s": {"max_competing_wait_s": 30.0},
    "wait_45s": {"max_competing_wait_s": 45.0},
    "comp_q_1m": {"min_competing_queue_m": 1.0},
    "comp_q_4m": {"min_competing_queue_m": 4.0},
}


def build_work_items() -> List[Dict[str, Any]]:
    items = []

    # Item 4 items (480 runs)
    for seed in SEEDS:
        if not (101 <= seed <= 110):
            raise ValueError(f"Strict safety violation: seed {seed} not permitted in exploratory XAI.")
        for cond in CONDITIONS:
            for v_name, kwargs in ABLATION_VARIANTS.items():
                run_id = f"marathahalli_{cond['scenario']}_{cond['demand_level']}_{v_name}_s{seed}"
                out_dir = ABLATION_DIR / run_id
                items.append({
                    "item_type": "ablation",
                    "variant": v_name,
                    "policy": "hybrid_queue_adaptive_ablation",
                    "policy_kwargs": kwargs,
                    "scenario": cond["scenario"],
                    "demand_level": cond["demand_level"],
                    "cond_key": cond["key"],
                    "seed": seed,
                    "run_id": run_id,
                    "out_dir": out_dir,
                })

    # Item 5 items (540 runs)
    for seed in SEEDS:
        if not (101 <= seed <= 110):
            raise ValueError(f"Strict safety violation: seed {seed} not permitted in exploratory XAI.")
        for cond in CONDITIONS:
            # 8 parameter variants
            for v_name, kwargs in SENSITIVITY_VARIANTS.items():
                run_id = f"marathahalli_{cond['scenario']}_{cond['demand_level']}_{v_name}_s{seed}"
                out_dir = SENSITIVITY_DIR / run_id
                items.append({
                    "item_type": "sensitivity",
                    "variant": v_name,
                    "policy": "hybrid_queue_adaptive_ablation",
                    "policy_kwargs": kwargs,
                    "scenario": cond["scenario"],
                    "demand_level": cond["demand_level"],
                    "cond_key": cond["key"],
                    "seed": seed,
                    "run_id": run_id,
                    "out_dir": out_dir,
                })

            # Fresh webster_measured baseline
            wm_id = f"marathahalli_{cond['scenario']}_{cond['demand_level']}_webster_measured_s{seed}"
            wm_out_dir = SENSITIVITY_DIR / wm_id
            items.append({
                "item_type": "sensitivity",
                "variant": "webster_measured",
                "policy": "webster_measured",
                "policy_kwargs": None,
                "scenario": cond["scenario"],
                "demand_level": cond["demand_level"],
                "cond_key": cond["key"],
                "seed": seed,
                "run_id": wm_id,
                "out_dir": wm_out_dir,
            })

    return items


def run_single_item(item: Dict[str, Any]) -> Dict[str, Any]:
    seed = item["seed"]
    if not (101 <= seed <= 110):
        raise ValueError(f"Strict safety violation: seed {seed} not permitted in exploratory XAI.")

    out_dir = item["out_dir"]
    metrics_file = out_dir / "metrics.json"

    # Check if already completed successfully
    if metrics_file.exists():
        try:
            m = json.loads(metrics_file.read_text(encoding="utf-8"))
            m["status"] = "SUCCESS"
            m["cached"] = True
            m["item_type"] = item["item_type"]
            m["variant"] = item["variant"]
            m["cond_key"] = item["cond_key"]
            m["seed"] = seed
            m["run_id"] = item["run_id"]
            return m
        except Exception:
            pass

    out_dir.mkdir(parents=True, exist_ok=True)

    # Attempt execution with 1 retry on failure
    max_attempts = 2
    last_exc = None
    for attempt in range(max_attempts):
        t0 = time.time()
        try:
            m = run_simulation(
                scenario=item["scenario"],
                policy=item["policy"],
                seed=seed,
                demand_level=item["demand_level"],
                network="marathahalli",
                out_dir=out_dir,
                policy_kwargs=item["policy_kwargs"],
                port=None,
            )
            elapsed = time.time() - t0
            m["status"] = "SUCCESS"
            m["cached"] = False
            m["runtime_s"] = round(elapsed, 2)
            m["item_type"] = item["item_type"]
            m["variant"] = item["variant"]
            m["cond_key"] = item["cond_key"]
            m["seed"] = seed
            m["run_id"] = item["run_id"]
            m["attempt"] = attempt + 1
            return m
        except Exception as exc:
            last_exc = exc
            time.sleep(1.0)

    return {
        "status": "FAILED",
        "error": str(last_exc),
        "item_type": item["item_type"],
        "variant": item["variant"],
        "cond_key": item["cond_key"],
        "seed": seed,
        "run_id": item["run_id"],
    }


def main():
    items = build_work_items()
    print(f"Total work items built: {len(items)}")
    assert len(items) == 1020, f"Expected 1020 items, got {len(items)}"

    workers = 8
    print(f"Starting execution with {workers} parallel workers...")
    t_start = time.time()

    completed = 0
    failed = 0
    cached = 0

    status_file = EXP_BASE / "matrix_status.csv"
    with open(status_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "item_type", "variant", "cond_key", "seed", "status", "runtime_s", "error"])

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(run_single_item, item): item for item in items}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            completed += 1
            if res.get("status") == "SUCCESS":
                if res.get("cached"):
                    cached += 1
            else:
                failed += 1

            # Log to status CSV incrementally
            with open(status_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    res.get("run_id"),
                    res.get("item_type"),
                    res.get("variant"),
                    res.get("cond_key"),
                    res.get("seed"),
                    res.get("status"),
                    res.get("runtime_s", 0.0),
                    res.get("error", ""),
                ])

            if completed % 20 == 0 or completed == len(items):
                elapsed_min = (time.time() - t_start) / 60.0
                print(f"[{completed}/{len(items)}] Success: {completed - failed}, Failed: {failed}, Cached: {cached} ({elapsed_min:.1f} min)")

    print(f"Completed all {len(items)} simulations in {(time.time() - t_start) / 60.0:.2f} min. Total failed: {failed}")


if __name__ == "__main__":
    main()
