/**
 * replayConstants.js - Single source of truth for saved demo replays
 *
 * Implements Task 7:
 * - 3 dev-seed replays (balanced-medium, imbalanced_orr-heavy, ramp_peak-medium)
 *   from existing smoke runs, clearly labelled as replays.
 */

export const DEMO_REPLAYS = [
  {
    id: 'marathahalli_balanced_medium_hybrid_queue_adaptive_s101',
    label: 'Balanced Load',
    sublabel: 'Medium 1.0x · Seed 101 · 1,901 frames',
    scenario: 'balanced',
    demand: 'medium',
    policy: 'hybrid_queue_adaptive',
    badge: 'dev smoke replay, not final results'
  },
  {
    id: 'marathahalli_imbalanced_orr_heavy_hybrid_queue_adaptive_s102',
    label: 'Imbalanced ORR (Peak North)',
    sublabel: 'Heavy 1.3x · Seed 102 · 2,089 frames',
    scenario: 'imbalanced_orr',
    demand: 'heavy',
    policy: 'hybrid_queue_adaptive',
    badge: 'dev smoke replay, not final results'
  },
  {
    id: 'marathahalli_ramp_peak_medium_hybrid_queue_adaptive_s101',
    label: 'Ramp Peak (Rush-Hour Surge)',
    sublabel: 'Medium 1.0x · Seed 101 · 1,926 frames',
    scenario: 'ramp_peak',
    demand: 'medium',
    policy: 'hybrid_queue_adaptive',
    badge: 'dev smoke replay, not final results'
  }
];
