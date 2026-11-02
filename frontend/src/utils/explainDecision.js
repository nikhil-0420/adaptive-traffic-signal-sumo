/**
 * DP1 Traffic Intelligence — Decision Explainer Utility
 * Transforms structured controller decision records into clear, human-readable prose.
 * Strict rules: Outcome first, reason second, numbers with units, plain words (no >= or >= symbols in prose).
 */

export function getAxisName(axis) {
  if (!axis) return 'current direction';
  const clean = String(axis).toUpperCase();
  if (clean === 'NS') return 'north–south';
  if (clean === 'EW') return 'east–west';
  return clean;
}

export function getCompetingAxisName(axis) {
  if (!axis) return 'opposing direction';
  const clean = String(axis).toUpperCase();
  if (clean === 'NS') return 'east–west';
  if (clean === 'EW') return 'north–south';
  return 'opposing direction';
}

export function formatSeconds(s) {
  if (s === null || s === undefined || s === 'n/a') return 'n/a';
  const num = Number(s);
  if (isNaN(num)) return 'n/a';
  return `${num.toFixed(1)} s`;
}

export function formatMeters(m) {
  if (m === null || m === undefined || m === 'n/a') return 'n/a';
  const val = Number(m);
  if (isNaN(val)) return 'n/a';
  if (val >= 149.9) return '150 m (sensor capped)';
  return `${val.toFixed(1)} m`;
}

/**
 * Turns structured decision fields into plain, human-friendly text.
 * @param {Object} d Structured decision record
 * @returns {Object} { headline, prose, codeLabel, type, outcome, rawCode, deltaS, targetS, maxS }
 */
export function explainDecision(d) {
  if (!d) {
    return {
      headline: 'No decision data',
      prose: 'Decision telemetry is pending or missing from the simulation record.',
      codeLabel: 'NO_DATA',
      type: 'neutral',
      outcome: 'PENDING',
      rawCode: 'NONE',
      deltaS: 'n/a'
    };
  }

  // Derive per-approach queues if only directional detector measurements exist
  let qActive = d.q_active_m != null ? Number(d.q_active_m) : null;
  let qCompeting = d.q_competing_m != null ? Number(d.q_competing_m) : null;
  const isNS = String(d.axis || 'NS').toUpperCase() === 'NS';
  if (qActive == null && (d.q_N_m != null || d.q_S_m != null || d.q_E_m != null || d.q_W_m != null)) {
    const qN = Number(d.q_N_m || 0);
    const qS = Number(d.q_S_m || 0);
    const qE = Number(d.q_E_m || 0);
    const qW = Number(d.q_W_m || 0);
    qActive = isNS ? Math.max(qN, qS) : Math.max(qE, qW);
    qCompeting = isNS ? Math.max(qE, qW) : Math.max(qN, qS);
  }
  qActive = qActive ?? 0;
  qCompeting = qCompeting ?? 0;

  const rawCode = d.decision_outcome || d.reason_code || d.action || (d.actual_green_s != null ? 'CHOSE_GREEN' : 'UNKNOWN');
  const action = (d.applied_action || d.action || d.proposed_action || (d.actual_green_s != null ? 'CYCLE_ALLOCATION' : '')).toUpperCase();
  const axis = getAxisName(d.axis);
  const compAxis = getCompetingAxisName(d.axis);

  const hasExtensionConcept = d.delta_g_app_s !== undefined || d.g_extra_s !== undefined || rawCode.includes('EXTEND');
  const deltaS = hasExtensionConcept ? Number(d.delta_g_app_s ?? d.g_extra_s ?? 0) : 'n/a';
  const targetS = Number(d.target_green_s ?? d.actual_green_s ?? d.green_s ?? 15);
  const elapsedS = Number(d.elapsed_s ?? 0);
  const maxS = 60; // Max green ceiling bound in DP1 hybrid controller
  const minS = 10; // Min green floor bound in DP1 hybrid controller

  // 0. ARCHIVED CYCLE AUDIT (Controllers with no extension concept, e.g. Fixed, Webster, Adaptive-Queue, Max-Pressure)
  if (rawCode === 'CHOSE_GREEN' || (action === 'CYCLE_ALLOCATION' && !hasExtensionConcept) || (d.actual_green_s != null && !d.applied_action)) {
    const chosenGreen = Number(d.actual_green_s ?? d.green_s ?? 10);
    const qActRound = Math.round(qActive);
    const qCompRound = Math.round(qCompeting);
    return {
      headline: `Chose ${chosenGreen} s of green`,
      prose: `Chose ${chosenGreen} s of green: own queue ${qActRound} m vs ${qCompRound} m on ${compAxis}.`,
      codeLabel: 'Cycle allocation',
      type: 'cycle_choice',
      outcome: 'CHOSE_GREEN',
      rawCode: 'CYCLE_ALLOCATION',
      deltaS: 'n/a',
      targetS: chosenGreen,
      maxS
    };
  }

  // 1. EMERGENCY PREEMPTION
  if (rawCode.includes('EMERGENCY') || action.includes('EMERGENCY') || d.is_emergency) {
    return {
      headline: 'Emergency preemption granted',
      prose: `Granted immediate green to ${axis} priority route. Emergency vehicle detected within clearance corridor; normal cycle interrupted with all-red safety buffer.`,
      codeLabel: 'Emergency vehicle priority',
      type: 'emergency',
      outcome: 'PREEMPTION',
      rawCode,
      deltaS,
      targetS,
      maxS
    };
  }

  // 2. GAP OUT (Ended green early)
  if (rawCode.includes('GAP_OUT') || action === 'GAP_OUT') {
    const holdSecs = formatSeconds(d.gap_out_elapsed_s ?? 3.0);
    const plannedTarget = Number(d.target_green_s ?? 60);
    const actualElapsed = Number(elapsedS || targetS || 27);
    const saved = plannedTarget > actualElapsed ? (plannedTarget - actualElapsed) : (d.seconds_saved ? Number(d.seconds_saved) : 33.0);
    return {
      headline: 'Ended green early (no cars waiting)',
      prose: `Terminated ${axis} green after ${formatSeconds(elapsedS || targetS)}. Zero vehicles were detected for ${holdSecs} while ${compAxis} was queued with ${formatMeters(qCompeting)}.`,
      codeLabel: 'Ended green early (no cars waiting)',
      type: 'gap_out',
      outcome: 'SWITCH_GAP_OUT',
      rawCode,
      deltaS: -saved,
      savedS: saved,
      targetS: elapsedS || targetS,
      maxS
    };
  }

  // 3. EXTEND / ADDED GREEN TIME
  if (rawCode.includes('EXTEND_APPROVED') || (action === 'EXTEND' && deltaS > 0)) {
    const addVal = deltaS > 0 ? deltaS : (d.delta_g_req_s || 3.0);
    return {
      headline: 'Added green time',
      prose: `Added ${formatSeconds(addVal)} to ${axis} green (now ${formatSeconds(targetS)} of a ${maxS} s maximum). ${axis} still had ${formatMeters(qActive)} of queue, and ${compAxis} was waiting with ${formatMeters(qCompeting)}, within the fairness limit.`,
      codeLabel: 'Added green time',
      type: 'extend',
      outcome: 'EXTEND_APPROVED',
      rawCode,
      deltaS: addVal,
      targetS,
      maxS
    };
  }

  // 4. SWITCH REFUSED (Minimum green floor not reached)
  if (rawCode.includes('MIN_GREEN') || rawCode.includes('REJECTED_MIN_GREEN')) {
    return {
      headline: 'Switch refused (minimum green not reached)',
      prose: `Maintained ${axis} green. Elapsed time of ${formatSeconds(elapsedS)} is below the mandatory safety minimum of ${minS} s.`,
      codeLabel: 'Switch refused (minimum green not reached)',
      type: 'rejected',
      outcome: 'REJECTED_MIN_GREEN',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  // 5. SWITCH ON FAIRNESS WAIT LIMIT OR COMPETING DEMAND
  if (rawCode.includes('FAIRNESS_WAIT_LIMIT') || rawCode.includes('SWITCH_FAIRNESS')) {
    return {
      headline: 'Changed phase (fairness limit reached)',
      prose: `Terminated ${axis} green. Vehicles waiting on ${compAxis} reached the maximum allowable red-wait threshold of 35 s with ${formatMeters(qCompeting)} queued.`,
      codeLabel: 'Changed phase',
      type: 'switch',
      outcome: 'SWITCH_FAIRNESS_WAIT_LIMIT',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  // 6. SWITCH ON MAXIMUM CEILING
  if (rawCode.includes('MAX_GREEN') || rawCode.includes('CEILING_REACHED') || d.is_max_green) {
    return {
      headline: 'Changed phase (maximum green ceiling)',
      prose: `Terminated ${axis} green upon reaching the maximum allowable ceiling of ${maxS} s to prevent opposing phase starvation.`,
      codeLabel: 'Changed phase',
      type: 'switch',
      outcome: 'SWITCH_MAX_GREEN',
      rawCode,
      deltaS: 0,
      targetS: maxS,
      maxS
    };
  }

  // 7. SWITCH ON DEMAND EXHAUSTED
  if (rawCode.includes('DEMAND_EXHAUSTED')) {
    return {
      headline: 'Ended green (demand exhausted)',
      prose: `Terminated ${axis} green after ${formatSeconds(targetS)}. Queue dropped to ${formatMeters(qActive)} with no new arrivals detected.`,
      codeLabel: 'Changed phase',
      type: 'switch',
      outcome: 'SWITCH_DEMAND_EXHAUSTED',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  // 8. ENTER GREEN (BASELINE START)
  if (rawCode.includes('BASELINE_ENTRY') || action === 'ENTER_GREEN' || action === 'SWITCH_TO_GREEN') {
    return {
      headline: 'Started green',
      prose: `Initiated green phase for ${axis} with a baseline allocation of ${formatSeconds(targetS)} following clearance.`,
      codeLabel: 'Started green',
      type: 'enter',
      outcome: 'BASELINE_ENTRY',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  // 9. HOLD / KEEPING CURRENT GREEN
  if (rawCode.includes('HOLD') || action === 'HOLD') {
    let holdProse = '';
    if (elapsedS > targetS && targetS > 0) {
      holdProse = `Green has run ${formatSeconds(elapsedS)} against a planned ${formatSeconds(targetS)}; it stays green until the queue gaps out or ${maxS} s is reached.`;
    } else {
      holdProse = `Keeping ${axis} green: ${formatSeconds(elapsedS)} elapsed so far of target ${formatSeconds(targetS)}, monitoring detector gap.`;
    }
    return {
      headline: 'Kept current green',
      prose: holdProse,
      codeLabel: 'Kept current green',
      type: 'hold',
      outcome: 'HOLD',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  // Default generic change/hold
  if (action === 'REQUEST_SWITCH' || action === 'SWITCH') {
    return {
      headline: 'Changed phase',
      prose: `Initiated transition to yellow clearance from ${axis} to prepare green service for ${compAxis}.`,
      codeLabel: 'Changed phase',
      type: 'switch',
      outcome: 'SWITCH',
      rawCode,
      deltaS: 0,
      targetS,
      maxS
    };
  }

  return {
    headline: 'Controller step evaluated',
    prose: `Evaluated ${axis} conditions at ${formatSeconds(d.t)}. Active queue: ${formatMeters(qActive)}, competing queue: ${formatMeters(qCompeting)}.`,
    codeLabel: rawCode,
    type: 'neutral',
    outcome: rawCode,
    rawCode,
    deltaS,
    targetS,
    maxS
  };
}

/**
 * Collapses consecutive HOLD decisions into a single summary entry per cycle/axis run.
 * @param {Array} decisions List of decision objects
 * @returns {Array} List of filtered/collapsed decision items
 */
export function collapseHolds(decisions) {
  if (!Array.isArray(decisions)) return [];
  const collapsed = [];
  let currentHoldGroup = null;

  for (const d of decisions) {
    const explained = explainDecision(d);
    if (explained.type === 'hold') {
      if (!currentHoldGroup || currentHoldGroup.axis !== d.axis || currentHoldGroup.cycle !== d.cycle) {
        if (currentHoldGroup) {
          collapsed.push(currentHoldGroup);
        }
        currentHoldGroup = {
          ...d,
          isCollapsedHold: true,
          holdCount: 1,
          startT: d.t,
          endT: d.t,
          maxElapsed: d.elapsed_s || 0,
          explained
        };
      } else {
        currentHoldGroup.holdCount += 1;
        currentHoldGroup.endT = d.t;
        currentHoldGroup.maxElapsed = Math.max(currentHoldGroup.maxElapsed, d.elapsed_s || 0);
        currentHoldGroup.explained = {
          ...explained,
          prose: `Keeping ${getAxisName(d.axis)} green: ${formatSeconds(currentHoldGroup.maxElapsed)} so far, waiting for a gap.`
        };
      }
    } else {
      if (currentHoldGroup) {
        collapsed.push(currentHoldGroup);
        currentHoldGroup = null;
      }
      collapsed.push({
        ...d,
        isCollapsedHold: false,
        explained
      });
    }
  }

  if (currentHoldGroup) {
    collapsed.push(currentHoldGroup);
  }

  return collapsed;
}
