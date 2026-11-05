/**
 * policyProvenance.js - Centralized Policy Provenance & Integrity Badges
 *
 * Defines explicit provenance classification across all evaluated traffic signal controllers:
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
  webster_oracle: 'ORACLE',
  fixed_matched_cycle: 'ORACLE',
  hybrid_oracle_seeded: 'ORACLE-SEEDED',
  rl_dqn: 'LEARNED',
  nn_supervised: 'LEARNED',
  rl: 'LEARNED',
  pressure: 'MEASURED',
};

/**
 * Resolve provenance category for a given policy name.
 */
export function getPolicyProvenance(policyName, apiProvenance = null) {
  if (apiProvenance) return apiProvenance;
  if (!policyName) return 'UNKNOWN';
  return POLICY_PROVENANCE[policyName] || 'UNKNOWN';
}

/**
 * Return Tailwind CSS style classes for a provenance badge.
 */
export function getProvenanceBadgeClass(provenance) {
  switch (provenance) {
    case 'MEASURED':
      return 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40';
    case 'ORACLE':
      return 'bg-amber-950/80 text-amber-300 border-amber-500/40';
    case 'ORACLE-SEEDED':
      return 'bg-purple-950/80 text-purple-300 border-purple-500/40';
    case 'LEARNED':
      return 'bg-blue-950/80 text-blue-300 border-blue-500/40';
    default:
      return 'bg-slate-800 text-slate-300 border-slate-600';
  }
}
