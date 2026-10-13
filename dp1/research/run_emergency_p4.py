"""Run paired emergency priority experiment across 5 seeds for Phase P4.

Evaluates fixed, pressure, and rl_dqn with emergency priority OFF vs ON on imbalanced_ns.
Saves raw paired results to results/research/emergency_p4_paired.csv.
"""
from pathlib import Path
import pandas as pd
from dp1.runner import run_simulation
from dp1 import config as C

SEEDS = [1, 2, 3, 4, 5]
POLICIES = ["fixed", "pressure", "rl_dqn"]
SCENARIO = "imbalanced_ns"
MODEL_PATH = C.RESULTS_DIR / "models" / "test_smoke_dqn.zip"

records = []

print(f"Running Phase P4 Paired Emergency Priority Experiment...")
print(f"Scenario: {SCENARIO}, Seeds: {SEEDS}, Policies: {POLICIES}")

out_base = C.RESULTS_DIR / "research" / "emergency_p4"
out_base.mkdir(parents=True, exist_ok=True)

for policy in POLICIES:
    policy_kwargs = {"model_path": str(MODEL_PATH)} if policy == "rl_dqn" else None
    for seed in SEEDS:
        print(f"\n--- Policy: {policy}, Seed: {seed} ---")
        
        # 1. Priority OFF
        dir_off = out_base / f"{SCENARIO}_{policy}_s{seed}_pri_off"
        m_off = run_simulation(
            scenario=SCENARIO,
            policy=policy,
            seed=seed,
            out_dir=dir_off,
            policy_kwargs=policy_kwargs,
            emergency_event=True,
            emergency_priority=False,
        )
        
        # 2. Priority ON
        dir_on = out_base / f"{SCENARIO}_{policy}_s{seed}_pri_on"
        m_on = run_simulation(
            scenario=SCENARIO,
            policy=policy,
            seed=seed,
            out_dir=dir_on,
            policy_kwargs=policy_kwargs,
            emergency_event=True,
            emergency_priority=True,
        )

        rec = {
            "policy": policy,
            "seed": seed,
            "route_hash_off": m_off["route_hash"],
            "route_hash_on": m_on["route_hash"],
            "routes_identical": m_off["route_hash"] == m_on["route_hash"],
            
            # Ambulance metrics
            "em_wait_off_s": m_off["emergency_wait_s"],
            "em_wait_on_s": m_on["emergency_wait_s"],
            "em_wait_delta_s": round(m_on["emergency_wait_s"] - m_off["emergency_wait_s"], 2) if m_off["emergency_wait_s"] is not None and m_on["emergency_wait_s"] is not None else None,
            
            "em_time_loss_off_s": m_off["emergency_time_loss_s"],
            "em_time_loss_on_s": m_on["emergency_time_loss_s"],
            "em_time_loss_delta_s": round(m_on["emergency_time_loss_s"] - m_off["emergency_time_loss_s"], 2) if m_off["emergency_time_loss_s"] is not None and m_on["emergency_time_loss_s"] is not None else None,
            
            "em_trip_off_s": m_off["emergency_trip_s"],
            "em_trip_on_s": m_on["emergency_trip_s"],
            "em_trip_delta_s": round(m_on["emergency_trip_s"] - m_off["emergency_trip_s"], 2) if m_off["emergency_trip_s"] is not None and m_on["emergency_trip_s"] is not None else None,
            
            # Non-emergency background traffic metrics
            "bg_wait_off_s": round(m_off["non_emergency_avg_wait_s"], 2),
            "bg_wait_on_s": round(m_on["non_emergency_avg_wait_s"], 2),
            "bg_wait_delta_s": round(m_on["non_emergency_avg_wait_s"] - m_off["non_emergency_avg_wait_s"], 2),
            
            "avg_queue_off_m": round(m_off["avg_queue_m"], 2),
            "avg_queue_on_m": round(m_on["avg_queue_m"], 2),
            "avg_queue_delta_m": round(m_on["avg_queue_m"] - m_off["avg_queue_m"], 2),
            
            "throughput_off": round(m_off["throughput_veh_per_h"], 1),
            "throughput_on": round(m_on["throughput_veh_per_h"], 1),
        }
        records.append(rec)
        print(f"  Ambulance trip time: {rec['em_trip_off_s']:.1f}s (off) -> {rec['em_trip_on_s']:.1f}s (on) [delta: {rec['em_trip_delta_s']:+.1f}s]")
        print(f"  Ambulance wait time: {rec['em_wait_off_s']:.1f}s (off) -> {rec['em_wait_on_s']:.1f}s (on) [delta: {rec['em_wait_delta_s']:+.1f}s]")
        print(f"  Background avg wait: {rec['bg_wait_off_s']:.2f}s (off) -> {rec['bg_wait_on_s']:.2f}s (on) [delta: {rec['bg_wait_delta_s']:+.2f}s]")

df = pd.DataFrame(records)
csv_path = C.RESULTS_DIR / "research" / "emergency_p4_paired.csv"
df.to_csv(csv_path, index=False)
print(f"\nPaired results successfully saved to: {csv_path}")

# Print summary table by policy
print("\n" + "="*80)
print("PHASE P4 EMERGENCY PRIORITY EVALUATION SUMMARY (MEAN OVER SEEDS 1..5)")
print("="*80)
for p in POLICIES:
    pdf = df[df["policy"] == p]
    mean_em_trip_off = pdf["em_trip_off_s"].mean()
    mean_em_trip_on = pdf["em_trip_on_s"].mean()
    mean_em_trip_delta = pdf["em_trip_delta_s"].mean()
    
    mean_em_loss_off = pdf["em_time_loss_off_s"].mean()
    mean_em_loss_on = pdf["em_time_loss_on_s"].mean()
    mean_em_loss_delta = pdf["em_time_loss_delta_s"].mean()
    
    mean_bg_wait_off = pdf["bg_wait_off_s"].mean()
    mean_bg_wait_on = pdf["bg_wait_on_s"].mean()
    mean_bg_wait_delta = pdf["bg_wait_delta_s"].mean()
    
    mean_queue_off = pdf["avg_queue_off_m"].mean()
    mean_queue_on = pdf["avg_queue_on_m"].mean()
    
    print(f"\nPolicy: {p.upper()}")
    print(f"  Ambulance Trip Duration : {mean_em_trip_off:.1f}s -> {mean_em_trip_on:.1f}s (delta: {mean_em_trip_delta:+.1f}s)")
    print(f"  Ambulance SUMO TimeLoss : {mean_em_loss_off:.1f}s -> {mean_em_loss_on:.1f}s (delta: {mean_em_loss_delta:+.1f}s)")
    print(f"  Background Traffic Wait : {mean_bg_wait_off:.2f}s -> {mean_bg_wait_on:.2f}s (delta: {mean_bg_wait_delta:+.2f}s)")
    print(f"  Mean Intersection Queue : {mean_queue_off:.2f}m -> {mean_queue_on:.2f}m")
