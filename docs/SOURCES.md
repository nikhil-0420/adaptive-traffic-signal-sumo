# Sources (only cite what is listed here)

## Baseline signal timing (BTP) - LOADED
- Dataset: Bengaluru City Traffic Signal Data, Bengaluru Traffic Police (BTP), published via OpenCity (data.opencity.in).
- Junction chosen: Marathalli Bridge Junction, Airport Police Station – FIXED (Varthur Rd × Outer Ring Rd Jn).
- Source document: "Signal Timings Data – Marathalli Bridge & Yamlur Junctions", page 10. Saved locally at `docs/btp_marathalli_yamlur.pdf`.
- Verified values: Weekday 08:00–11:30 schedule: Phase 1 = 110 s, Phase 2 = 100 s, exclusive pedestrian phase = 15 s, total cycle = 225 s.
- Modelling decisions:
  1. Phase mapping: Phase 1 → NS axis, Phase 2 → EW axis. This adopts BTP's real-world timing split structure onto the synthetic 4-way network, not its literal physical geometry.
  2. Clearance intervals: The sheet does not specify whether phase durations subsume amber/all-red clearance intervals. We assume they do, calculating `FIXED.green_ns_s = 110 - (yellow_s + all_red_s) = 105 s` and `FIXED.green_ew_s = 100 - (yellow_s + all_red_s) = 95 s` dynamically from `config.TIMING`.
  3. Pedestrian phase limitation: The 15 s exclusive pedestrian phase is not simulated in the two-phase vehicle model, resulting in an effective modelled cycle of 210 s vs 225 s real.
  4. Reference plan: The original 30/30 synthetic plan is preserved in `config.py` as `FIXED_PLACEHOLDER`.

## Literature (verified by Nikhil - add DOI after checking it resolves)
- Rajampalli, Narra, J. G., "A spatio-temporal GNN and multi-agent system framework for bottleneck prediction and signal
  optimization in Bangalore", Results in Engineering 28 (2025) 107675, doi 10.1016/j.rineng.2025.107675.
  Relevant: its green-extension rule has the same shape (bounded linear extension); it states it did not measure delay,
  throughput or queue length.
- SUMO: Lopez et al., ITSC 2018 doi 10.1109/ITSC.2018.8569938 | TraCI: Wegener et al., CNS 2008 doi 10.1145/1400713.1400740
- Webster, Traffic Signal Settings, Road Research Technical Paper 39, 1958 (fixed-time theory; not full-text verified)
