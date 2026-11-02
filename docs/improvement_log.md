# DP1 Improvement Log

## Initial Environment Baseline (Phase 0 Setup)

- **Date**: 2026-11-02
- **Git Branch**: `dp1-improve`
- **Git Commit**: `c18a808c3a5b5c391e001793ef2ed368eedfb5f6`
- **SUMO Version**: Eclipse SUMO sumo 1.28.0 (`E:\dp1-traffic-signal\.venv\Scripts\sumo.exe`)
  - Build features: `Windows-10.0.26100 AMD64 MSVC 19.51.36260.0 Release FMI Proj GUI FMT Intl SWIG Parquet Eigen GDAL FFmpeg OSG GL2PS JuPedSim`
- **Python Version**: `3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]` (Virtual environment: `E:\dp1-traffic-signal\.venv`)
- **Node Version**: `v24.16.0`
- **npm Version**: `11.13.0`

### Network Version and Identifier (Marathahalli)
- **Network Name**: `marathahalli`
- **Network Model Version**: `1.0.0`
- **Source Snapshot ID**: `opencity_bbmp_20261014`
- **Signal Plan ID**: `btp_airport_ps_marathahalli_v1`
- **Controlled TLS Node**: `marathahalli_tls`
- **Source Metadata Reference**: [`network/marathahalli/source/source_metadata.json`](../network/marathahalli/source/source_metadata.json)
- **Experiment Manifest Reference**: [`results/research/exp_marathahalli_hybrid_840/manifest.json`](../results/research/exp_marathahalli_hybrid_840/manifest.json)

### Package Freeze (Relevant Packages)
- `eclipse-sumo`: 1.28.0
- `traci`: 1.28.0
- `sumolib`: 1.28.0
- `numpy`: 2.4.6
- `pandas`: 3.0.6
- `scipy`: NOT INSTALLED
- `fastapi`: 0.143.0
- `torch`: 2.14.1
- `stable_baselines3`: 2.9.0
- `gymnasium`: 1.4.0
- `matplotlib`: 3.11.2
- `uvicorn`: 0.54.0
- `pytest`: 9.1.1
