/**
 * signalAndQueue3d.js - 3D Traffic Signals, Queue Volumes & Decision Callouts
 *
 * Implements Phase 5:
 * - 3D Signal Heads at stop lines derived from actual SUMO signal state strings (never client timers)
 * - Phase group labels (NS/EW), yellow and all-red visibly distinct
 * - Countdown only if target green provided; otherwise elapsed time
 * - 3D Translucent Queue Bars over the 24.9m detector spans
 * - Status colors: CONFIRMED_ZERO, MEASURING, SATURATED warning, OFFLINE (never zero)
 * - Floating approach queue metric labels
 * - Decision callout displaying logged reason with separate requested vs applied increments
 */

import * as THREE from 'three';
import { sumoToThree } from './network3dGeometry.js';

/** Stop line locations and orientations for the 4 controlled approaches of marathahalli_tls */
export const SIGNAL_APPROACH_CONFIG = {
  N: {
    approach: 'N',
    name: 'North (ORR Southbound)',
    phaseGroup: 'NS',
    links: [0, 1, 2, 3],
    // Stop line center at sumo [346.8, 342.5, 0.0] -> Three.js [-3.2, 0.0, 7.5]
    stopLinePos: [-3.2, 0.0, 7.5],
    signalHeadPos: [-7.5, 4.2, 7.5], // Pole placed at curb side
    rotationY: Math.PI, // Facing incoming Southbound traffic (looking North)
    detectorStart: [-3.2, 0.0, -17.4], // y=367.4 -> Z=-17.4
    detectorEnd: [-3.2, 0.0, 7.5],     // y=342.5 -> Z=+7.5
    detectorLength: 24.9,
    width: 6.4,
    axisDir: [0, 0, 1], // Inbound moves along +Z
  },
  S: {
    approach: 'S',
    name: 'South (ORR Northbound)',
    phaseGroup: 'NS',
    links: [8, 9, 10, 11],
    // Stop line center at sumo [353.2, 321.5, 0.0] -> Three.js [3.2, 0.0, 28.5]
    stopLinePos: [3.2, 0.0, 28.5],
    signalHeadPos: [7.5, 4.2, 28.5],
    rotationY: 0, // Facing incoming Northbound traffic (looking South)
    detectorStart: [3.2, 0.0, 53.4], // y=296.6 -> Z=53.4
    detectorEnd: [3.2, 0.0, 28.5],   // y=321.5 -> Z=28.5
    detectorLength: 24.9,
    width: 6.4,
    axisDir: [0, 0, -1], // Inbound moves along -Z
  },
  E: {
    approach: 'E',
    name: 'East (Varthur Westbound)',
    phaseGroup: 'EW',
    links: [4, 5, 6, 7],
    // Stop line center at sumo [360.5, 335.2, 0.0] -> Three.js [10.5, 0.0, 14.8]
    stopLinePos: [10.5, 0.0, 14.8],
    signalHeadPos: [10.5, 4.2, 10.5],
    rotationY: -Math.PI / 2, // Facing Westbound traffic (looking East)
    detectorStart: [35.4, 0.0, 14.8], // x=385.4 -> X=35.4
    detectorEnd: [10.5, 0.0, 14.8],   // x=360.5 -> X=10.5
    detectorLength: 24.9,
    width: 6.4,
    axisDir: [-1, 0, 0], // Inbound moves along -X
  },
  W: {
    approach: 'W',
    name: 'West (HAL Eastbound)',
    phaseGroup: 'EW',
    links: [12, 13, 14, 15],
    // Stop line center at sumo [339.5, 328.8, 0.0] -> Three.js [-10.5, 0.0, 21.2]
    stopLinePos: [-10.5, 0.0, 21.2],
    signalHeadPos: [-10.5, 4.2, 25.5],
    rotationY: Math.PI / 2, // Facing Eastbound traffic (looking West)
    detectorStart: [-35.4, 0.0, 21.2], // x=314.6 -> X=-35.4
    detectorEnd: [-10.5, 0.0, 21.2],   // x=339.5 -> X=-10.5
    detectorLength: 24.9,
    width: 6.4,
    axisDir: [1, 0, 0], // Inbound moves along +X
  },
};

/** Decode signal state string into approach colors */
export function decodeSignalStateString(stateString) {
  const defaultState = 'rrrrrrrrrrrrrrrr';
  const str = (stateString || defaultState).padEnd(16, 'r');

  const result = {};
  const isAllRed = !str.includes('G') && !str.includes('g') && !str.includes('y') && !str.includes('Y');

  for (const [approachKey, cfg] of Object.entries(SIGNAL_APPROACH_CONFIG)) {
    const chars = cfg.links.map((idx) => str[idx] || 'r');
    let colorName = 'RED';
    let hex = '#ef4444';

    if (chars.some((c) => c === 'G' || c === 'g')) {
      colorName = 'GREEN';
      hex = '#22c55e';
    } else if (chars.some((c) => c === 'y' || c === 'Y')) {
      colorName = 'YELLOW';
      hex = '#eab308';
    } else if (isAllRed) {
      colorName = 'ALL_RED';
      hex = '#dc2626';
    }

    result[approachKey] = {
      colorName,
      hex,
      chars: chars.join(''),
      phaseGroup: cfg.phaseGroup,
    };
  }

  return {
    raw: str,
    isAllRed,
    approaches: result,
  };
}

/** Compute timer display (countdown or elapsed) */
export function computeSignalTimer(adaptiveDecision, activePhase, simTime = 0) {
  if (!adaptiveDecision) {
    return {
      type: 'elapsed',
      label: 'ELAPSED',
      value: Math.floor(simTime % 60),
      text: `${Math.floor(simTime % 60)}s`,
    };
  }

  const { target_green_s, elapsed_s } = adaptiveDecision;
  const isGreen = activePhase === 'GREEN';

  if (isGreen && typeof target_green_s === 'number' && typeof elapsed_s === 'number' && target_green_s > 0) {
    const remaining = Math.max(0, Math.round(target_green_s - elapsed_s));
    return {
      type: 'countdown',
      label: 'COUNTDOWN',
      value: remaining,
      text: `${remaining}s`,
    };
  }

  const elapsed = typeof elapsed_s === 'number' ? Math.round(elapsed_s) : Math.floor(simTime % 60);
  return {
    type: 'elapsed',
    label: isGreen ? 'ELAPSED' : activePhase,
    value: elapsed,
    text: `${elapsed}s`,
  };
}

/** Queue sensor status styling */
export const SENSOR_STATUS_STYLES = {
  CONFIRMED_ZERO: {
    color: '#10b981', // Emerald green
    fillOpacity: 0.25,
    border: '#059669',
    label: 'CONFIRMED ZERO',
    isWarning: false,
  },
  MEASURING: {
    color: '#06b6d4', // Bright cyan
    fillOpacity: 0.65,
    border: '#0891b2',
    label: 'MEASURING',
    isWarning: false,
  },
  SATURATED: {
    color: '#f59e0b', // Unmistakable warning amber
    pulseColor: '#ef4444',
    fillOpacity: 0.85,
    border: '#dc2626',
    label: 'SATURATED ⚠',
    isWarning: true,
  },
  OFFLINE: {
    color: '#64748b', // Slate gray hatched/fault
    fillOpacity: 0.75,
    border: '#475569',
    label: 'OFFLINE ✖',
    isWarning: true,
    isOffline: true,
  },
};

/**
 * Determine queue display parameters for an approach.
 * Enforces: OFFLINE is NEVER rendered as zero.
 */
export function getApproachQueueDisplay(approachKey, approachQueues, queues_m = {}) {
  const cfg = SIGNAL_APPROACH_CONFIG[approachKey];
  const appData = approachQueues?.[approachKey];

  let rawQueueM = 0.0;
  let rawVehCount = 0;
  let sensorStatus = 'MEASURING';

  if (appData) {
    rawQueueM = appData.total_queue_m ?? appData.longitudinal_queue_m ?? 0.0;
    rawVehCount = appData.total_queued_vehicles ?? appData.ground_truth_veh_count ?? 0;
    sensorStatus = appData.sensor_status || (appData.is_saturated ? 'SATURATED' : 'MEASURING');
    if (appData.data_valid === false || appData.is_offline) {
      sensorStatus = 'OFFLINE';
    }
  } else if (queues_m[approachKey] !== undefined) {
    rawQueueM = Number(queues_m[approachKey]) || 0.0;
    rawVehCount = Math.round(rawQueueM / 7.0);
  }

  // Safety Invariant: OFFLINE status is NEVER rendered as zero
  let renderQueueM = rawQueueM;
  let isOffline = false;
  if (sensorStatus === 'OFFLINE' || sensorStatus === 'FAULT') {
    isOffline = true;
    sensorStatus = 'OFFLINE';
    // Display full detector span as offline hatched volume (never 0)
    renderQueueM = cfg.detectorLength;
  } else if (rawQueueM <= 0.1) {
    sensorStatus = 'CONFIRMED_ZERO';
  }

  const style = SENSOR_STATUS_STYLES[sensorStatus] || SENSOR_STATUS_STYLES.MEASURING;

  return {
    approach: approachKey,
    name: cfg.name,
    queue_m: rawQueueM,
    renderQueueM,
    vehCount: rawVehCount,
    sensorStatus,
    style,
    isOffline,
    isSaturated: sensorStatus === 'SATURATED',
  };
}
