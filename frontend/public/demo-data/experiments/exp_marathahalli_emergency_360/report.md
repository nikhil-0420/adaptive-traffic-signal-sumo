# DP1 Authoritative Emergency-Priority Research Report (`exp_marathahalli_emergency_360`)

> **Simulation Integrity Notice**
> All metrics are derived from real execution of Eclipse SUMO on simulated detectors.
> Network: marathahalli. Emergency vehicle arrival is deterministic and background routes are byte-identical across pairs.

## 1. Executive Summary & Completion

- **Network:** `marathahalli`
- **Total Prescribed Cells:** 360
- **Completed Cells:** 360
- **Failed Cells:** 0
- **Valid Matched Pairs:** 180 (100% paired)
- **RL Model Checkpoint:** `E:\dp1-traffic-signal\models\dqn_marathahalli_site_best.zip`
- **Evaluation Seeds:** [121, 122, 123, 124, 125, 126, 127, 128, 129, 130]

## 2. Paired Comparison Summary by Condition (Mean over Seeds 121..130)

| Pattern | Level | Policy | Ambulance Trip (OFF) | Ambulance Trip (ON) | Emergency Delta | Background Wait (OFF) | Background Wait (ON) | Background Delta | Routes Identical |
|---|---|---|---:|---:|---:|---:|---:|---:|:---:|
| balanced | low | `fixed` | 163.0s | 72.9s | **-90.1s** | 15.2s | 15.7s | +0.45s | True |
| balanced | low | `pressure` | 65.7s | 64.5s | **-1.2s** | 7.9s | 7.8s | -0.04s | True |
| balanced | low | `rl_dqn` | 63.0s | 59.2s | **-3.8s** | 8.2s | 8.8s | +0.68s | True |
| balanced | medium | `fixed` | 158.8s | 77.3s | **-81.5s** | 43.0s | 41.3s | -1.73s | True |
| balanced | medium | `pressure` | 73.7s | 64.8s | **-8.9s** | 38.3s | 39.1s | +0.82s | True |
| balanced | medium | `rl_dqn` | 77.1s | 63.4s | **-13.7s** | 38.4s | 37.3s | -1.13s | True |
| balanced | heavy | `fixed` | 162.8s | 95.5s | **-67.3s** | 110.3s | 107.9s | -2.49s | True |
| balanced | heavy | `pressure` | 94.3s | 80.0s | **-14.3s** | 108.0s | 107.7s | -0.26s | True |
| balanced | heavy | `rl_dqn` | 92.7s | 79.1s | **-13.6s** | 106.1s | 107.5s | +1.42s | True |
| surge_orr_north | low | `fixed` | 163.1s | 77.0s | **-86.1s** | 16.5s | 15.7s | -0.77s | True |
| surge_orr_north | low | `pressure` | 60.3s | 60.0s | **-0.3s** | 8.6s | 8.5s | -0.08s | True |
| surge_orr_north | low | `rl_dqn` | 68.0s | 64.1s | **-3.9s** | 9.2s | 9.7s | +0.45s | True |
| surge_orr_north | medium | `fixed` | 173.6s | 77.1s | **-96.5s** | 42.3s | 42.8s | +0.57s | True |
| surge_orr_north | medium | `pressure` | 73.6s | 66.7s | **-6.9s** | 38.1s | 37.5s | -0.60s | True |
| surge_orr_north | medium | `rl_dqn` | 74.2s | 68.8s | **-5.4s** | 38.9s | 38.9s | -0.08s | True |
| surge_orr_north | heavy | `fixed` | 179.4s | 77.6s | **-101.8s** | 99.7s | 98.3s | -1.35s | True |
| surge_orr_north | heavy | `pressure` | 80.5s | 77.6s | **-2.9s** | 98.9s | 96.1s | -2.82s | True |
| surge_orr_north | heavy | `rl_dqn` | 81.5s | 69.8s | **-11.7s** | 96.7s | 95.5s | -1.21s | True |

## 3. Overall Policy Mean Comparison

| Policy | Mean Ambulance Trip (OFF) | Mean Ambulance Trip (ON) | Net Mean Delta | Mean Non-Emergency Background Delay Delta |
|---|---:|---:|---:|---:|
| `fixed` | 166.8s | 79.6s | **-87.2s** | -0.89s |
| `pressure` | 74.7s | 68.9s | **-5.8s** | -0.50s |
| `rl_dqn` | 76.1s | 67.4s | **-8.7s** | +0.02s |