/**
 * policyConstants.js - Single source of truth for Policy definitions & provenance
 *
 * Implements Pre-Registration Amendment 3:
 * - 7 Main Policies: fixed, webster_measured (reference), webster_recalc, sumo_actuated,
 *   adaptive, queue_extension, hybrid_queue_adaptive (proposed).
 * - 1 Ablation Policy: hybrid_oracle_seeded.
 * - Oracle Benchmarks: fixed_webster, fixed_matched_cycle, webster_oracle (marked "benchmark only").
 * - Learned/Dropped: rl_dqn (Reinforcement Learning baseline).
 *
 * Provenance Categories:
 * - MEASURED: Field-adapted or online empirical measurement without future oracle info.
 * - ORACLE: Benchmark using offline scenario demand tables / omniscient cycle math.
 * - ORACLE-SEEDED: Legacy hybrid baseline with oracle initial green splits.
 * - LEARNED: Reinforcement learning (RL/DQN) policy.
 */

export const POLICY_PROVENANCE = {
  fixed: 'MEASURED',
  webster_measured: 'MEASURED',
  webster_recalc: 'MEASURED',
  sumo_actuated: 'MEASURED',
  adaptive: 'MEASURED',
  queue_extension: 'MEASURED',
  hybrid_queue_adaptive: 'MEASURED',
  fixed_webster: 'ORACLE',
  fixed_matched_cycle: 'ORACLE',
  webster_oracle: 'ORACLE',
  hybrid_oracle_seeded: 'ORACLE-SEEDED',
  rl_dqn: 'LEARNED',
};

export const POLICIES = [
  {
    id: 'hybrid_queue_adaptive',
    label: 'Hybrid Queue-Adaptive (Proposed)',
    shortLabel: 'Hybrid Adaptive',
    provenance: 'MEASURED',
    role: 'proposed',
    isBenchmarkOnly: false,
    badge: 'PROPOSED',
    badgeClass: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50',
    description: 'R4 de-oracled base green + state-aware queue extension + max-green ceiling.',
  },
  {
    id: 'webster_measured',
    label: 'Webster Measured (Reference)',
    shortLabel: 'Webster Measured',
    provenance: 'MEASURED',
    role: 'reference',
    isBenchmarkOnly: false,
    badge: 'REFERENCE',
    badgeClass: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/50',
    description: 'Online measured Webster timing based on observed approach flows during the first 300 s.',
  },
  {
    id: 'webster_recalc',
    label: 'Webster Periodic Recalc',
    shortLabel: 'Webster Recalc',
    provenance: 'MEASURED',
    role: 'comparator',
    isBenchmarkOnly: false,
    badge: 'COMPARATOR',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-600',
    description: 'Online periodic Webster recalculation every 300 s to track evolving flow rates.',
  },
  {
    id: 'sumo_actuated',
    label: 'SUMO Actuated (Gap-based)',
    shortLabel: 'SUMO Actuated',
    provenance: 'MEASURED',
    role: 'comparator',
    isBenchmarkOnly: false,
    badge: 'BASELINE',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-600',
    description: 'Standard built-in SUMO gap-based actuated controller without queue awareness.',
  },
  {
    id: 'adaptive',
    label: 'Queue-Proportional Adaptive',
    shortLabel: 'Adaptive Queue',
    provenance: 'MEASURED',
    role: 'comparator',
    isBenchmarkOnly: false,
    badge: 'BASELINE',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-600',
    description: 'Instantaneous queue-proportional split allocator.',
  },
  {
    id: 'queue_extension',
    label: 'Queue Extension (Green Cap)',
    shortLabel: 'Queue Extension',
    provenance: 'MEASURED',
    role: 'comparator',
    isBenchmarkOnly: false,
    badge: 'BASELINE',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-600',
    description: 'Actuated queue-extension controller with fixed maximum green ceiling.',
  },
  {
    id: 'fixed',
    label: 'Fixed-Time BTP Baseline',
    shortLabel: 'Fixed BTP',
    provenance: 'MEASURED',
    role: 'comparator',
    isBenchmarkOnly: false,
    badge: 'PLACEHOLDER',
    badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-500/50',
    description: 'Fixed-time plan (placeholder until verified BTP junction timing is sourced).',
  },
  {
    id: 'hybrid_oracle_seeded',
    label: 'Hybrid Oracle-Seeded (Ablation)',
    shortLabel: 'Hybrid Oracle-Seed',
    provenance: 'ORACLE-SEEDED',
    role: 'ablation',
    isBenchmarkOnly: false,
    badge: 'ABLATION',
    badgeClass: 'bg-purple-950/80 text-purple-300 border-purple-500/50',
    description: 'R0 legacy baseline with oracle initial green splits to isolate oracle dependence.',
  },
  {
    id: 'fixed_webster',
    label: 'Fixed Webster (Oracle Demand)',
    shortLabel: 'Webster Oracle',
    provenance: 'ORACLE',
    role: 'benchmark_only',
    isBenchmarkOnly: true,
    badge: 'BENCHMARK ONLY',
    badgeClass: 'bg-rose-950/80 text-rose-300 border-rose-500/50',
    description: 'Benchmark only: Uses omniscient scenario demand table to pre-calculate split.',
  },
  {
    id: 'fixed_matched_cycle',
    label: 'Fixed Matched Cycle (Oracle)',
    shortLabel: 'Matched Cycle',
    provenance: 'ORACLE',
    role: 'benchmark_only',
    isBenchmarkOnly: true,
    badge: 'BENCHMARK ONLY',
    badgeClass: 'bg-rose-950/80 text-rose-300 border-rose-500/50',
    description: 'Benchmark only: Fixed splits matching empirical cycle lengths.',
  },
  {
    id: 'rl_dqn',
    label: 'Deep Q-Network (RL / Learned)',
    shortLabel: 'RL (DQN)',
    provenance: 'LEARNED',
    role: 'dropped',
    isBenchmarkOnly: false,
    badge: 'DROPPED',
    badgeClass: 'bg-zinc-800 text-zinc-400 border-zinc-600',
    description: 'Reinforcement learning policy dropped due to stability and safety boundary constraints.',
  },
];

export const DEFAULT_POLICY_ID = 'hybrid_queue_adaptive';

/** Lookup policy configuration by id with resilient fallback */
export function getPolicyConfig(policyId) {
  if (!policyId) return POLICIES[0];
  const found = POLICIES.find((p) => p.id === policyId);
  if (found) return found;
  return {
    id: policyId,
    label: policyId,
    shortLabel: policyId,
    provenance: POLICY_PROVENANCE[policyId] || 'MEASURED',
    role: 'unknown',
    isBenchmarkOnly: false,
    badge: 'POLICY',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-600',
    description: `Policy ${policyId}`,
  };
}

/** Get provenance category for policy */
export function getPolicyProvenance(policyId) {
  return POLICY_PROVENANCE[policyId] || 'MEASURED';
}
