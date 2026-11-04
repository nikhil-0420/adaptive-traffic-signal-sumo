/**
 * scenarioConstants.js - Single source of truth for Traffic Scenarios & Demand Levels
 *
 * Implements Phase 8 & Pre-Registration Amendment 3:
 * - 4 Stationary Scenarios: balanced, imbalanced_orr, imbalanced_varthur, surge_orr_north.
 * - 3 Non-Stationary Scenarios: ramp_peak, surge_shift, lane_closure.
 * - 3 Demand Intensity Levels: low (0.70x), medium (1.00x), heavy (1.30x).
 * - Exact 1-line descriptions sourced faithfully from docs/SCENARIOS.md.
 */

export const SCENARIOS = [
  {
    id: 'ramp_peak',
    label: 'Ramp Peak (Rush-Hour Surge)',
    category: 'non_stationary',
    description: 'Unimodal morning rush-hour surge with smooth piecewise-linear ramp-up, peak plateau, and ramp-down.',
    axis: 'NS/EW',
    isNonStationary: true,
  },
  {
    id: 'surge_shift',
    label: 'Surge Shift (Arterial Inversion)',
    category: 'non_stationary',
    description: 'Mid-run directional priority inversion where the dominant arterial switches from Outer Ring Road (ORR) North-South to Varthur Road East-West.',
    axis: 'NS -> EW',
    isNonStationary: true,
  },
  {
    id: 'lane_closure',
    label: 'Lane Closure (Bottleneck)',
    category: 'non_stationary',
    description: 'Mid-run physical capacity constriction where an inbound approach lane (ramp_orr_n_in_0) on ORR North is closed to all traffic for 10 minutes.',
    axis: 'ORR North',
    isNonStationary: true,
  },
  {
    id: 'balanced',
    label: 'Balanced Load',
    category: 'stationary',
    description: 'Equal baseline load across all 4 approaches.',
    axis: 'All',
    isNonStationary: false,
  },
  {
    id: 'imbalanced_orr',
    label: 'Imbalanced ORR',
    category: 'stationary',
    description: 'Heavy commuter load on Outer Ring Road (NS).',
    axis: 'NS',
    isNonStationary: false,
  },
  {
    id: 'imbalanced_varthur',
    label: 'Imbalanced Varthur',
    category: 'stationary',
    description: 'Heavy commuter load on Varthur Road (EW).',
    axis: 'EW',
    isNonStationary: false,
  },
  {
    id: 'surge_orr_north',
    label: 'Surge ORR North',
    category: 'stationary',
    description: 'Directional morning surge from K.R. Puram heading south toward Bellandur.',
    axis: 'North',
    isNonStationary: false,
  },
];

export const DEMAND_LEVELS = [
  {
    id: 'medium',
    label: 'Medium (1.00x)',
    multiplier: 1.0,
    multiplierStr: '1.00x',
    description: 'Standard design demand level.',
  },
  {
    id: 'heavy',
    label: 'Heavy (1.30x)',
    multiplier: 1.3,
    multiplierStr: '1.30x',
    description: 'Stressed peak congestion operations.',
  },
  {
    id: 'low',
    label: 'Low (0.70x)',
    multiplier: 0.7,
    multiplierStr: '0.70x',
    description: 'Off-peak / late evening operations.',
  },
];

/** The 6 representative evaluation conditions in Pre-Registration Amendment 3 */
export const AMENDMENT_3_CONDITIONS = [
  {
    id: 'balanced-low',
    scenarioId: 'balanced',
    levelId: 'low',
    label: 'balanced-low',
    description: 'Stationary balanced low demand (off-peak baseline).',
  },
  {
    id: 'balanced-heavy',
    scenarioId: 'balanced',
    levelId: 'heavy',
    label: 'balanced-heavy',
    description: 'Stationary balanced heavy demand (peak saturation).',
  },
  {
    id: 'imbalanced_orr-heavy',
    scenarioId: 'imbalanced_orr',
    levelId: 'heavy',
    label: 'imbalanced_orr-heavy',
    description: 'Asymmetric high commuter load along Outer Ring Road (ORR) North-South.',
  },
  {
    id: 'ramp_peak-medium',
    scenarioId: 'ramp_peak',
    levelId: 'medium',
    label: 'ramp_peak-medium',
    description: 'Unimodal morning rush-hour surge with smooth piecewise-linear ramp-up, peak plateau, and ramp-down.',
  },
  {
    id: 'surge_shift-medium',
    scenarioId: 'surge_shift',
    levelId: 'medium',
    label: 'surge_shift-medium',
    description: 'Mid-run directional priority inversion where the dominant arterial switches from Outer Ring Road (ORR) North-South to Varthur Road East-West.',
  },
  {
    id: 'lane_closure-medium',
    scenarioId: 'lane_closure',
    levelId: 'medium',
    label: 'lane_closure-medium',
    description: 'Mid-run physical capacity constriction where an inbound approach lane (ramp_orr_n_in_0) on ORR North is closed to all traffic for 10 minutes.',
  },
];

/** Lookup scenario details by id */
export function getScenarioConfig(scenarioId) {
  return SCENARIOS.find((s) => s.id === scenarioId) || {
    id: scenarioId,
    label: scenarioId,
    category: 'custom',
    description: `Scenario ${scenarioId}`,
    isNonStationary: false,
  };
}

/** Lookup demand level details by id */
export function getDemandLevelConfig(levelId) {
  return DEMAND_LEVELS.find((d) => d.id === levelId) || {
    id: levelId,
    label: String(levelId),
    multiplier: 1.0,
    multiplierStr: '1.00x',
    description: 'Demand level',
  };
}
