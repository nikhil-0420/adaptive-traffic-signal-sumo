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

## Literature (verified - 2024-2026 IEEE, ACM, Springer core set)
- Base Paper (IEEE): K. Sreejith, S. Mathi, P. Pradeep, "Beyond Sensors: IntelliSignal's Map-Integrated Intelligence in Traffic Flow Optimization," IEEE Access, vol. 12, pp. 39028–39040, 2024. doi: 10.1109/ACCESS.2024.3375335.
  Relevance: Integrates real-world map road geometry into microscopic simulation (SUMO) via TraCI, comparing real-time queue/density adaptive phase selection against static time plans. Serves as direct architectural predecessor for DP1.
- ACM Paper: Q. Sun, R. Zha, L. Zhang, J. Zhou, Y. Mei, Z. Li, H. Xiong, "CrossLight: Offline-to-Online Reinforcement Learning for Cross-City Traffic Signal Control," in Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '24), pp. 2785–2795, Aug. 2024. doi: 10.1145/3637528.3671927.
  Relevance: Addresses RL generalization across asymmetric intersection topologies and varying traffic demand matrices; provides foundation for benchmarking policy behavior on multi-phase urban junctions.
- Springer Paper: L. Liu, X. Zhuang, Q. Li, "Adaptive Traffic Signal Control for Urban Corridor Based on Reinforcement Learning," in Computational and Experimental Simulations in Engineering (ICCES 2024), Lecture Notes in Mechanical Engineering, Springer, Cham, pp. 25–35, 2024. doi: 10.1007/978-3-031-77489-8_3.
  Relevance: Investigates queue length and waiting time state representations for corridor-level adaptive signal optimization in micro-simulation.
- Local Bengaluru Reference: Rajampalli, Narra, J. G., "A spatio-temporal GNN and multi-agent system framework for bottleneck prediction and signal optimization in Bangalore," Results in Engineering 28 (2025) 107675, doi: 10.1016/j.rineng.2025.107675.
  Relevance: Bengaluru corridor analysis; its green-extension rule shares bounded linear properties, but explicitly states it did not measure delay, throughput, or microscopic queue lengths—a gap DP1 addresses directly.
- Platform Foundations:
  - SUMO: Lopez et al., "Microscopic Traffic Simulation using SUMO," IEEE ITSC 2018, doi: 10.1109/ITSC.2018.8569938.
  - TraCI: Wegener et al., "TraCI: An Interface for Linking Arbitrary Traffic Simulators and Network Simulators," ACM CNS 2008, doi: 10.1145/1400713.1400740.
  - Webster: F. V. Webster, "Traffic Signal Settings," Road Research Technical Paper No. 39, Road Research Laboratory, HMSO, London, 1958.
