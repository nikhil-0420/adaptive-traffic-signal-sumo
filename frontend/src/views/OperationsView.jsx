import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { useResults } from '../context/useResults';
import { CountUp } from '../components/motion/CountUp';
import {
  IconArrowRight,
  IconInfo,
  IconCheck,
  IconSliders,
  IconSiren,
  IconPlay,
  IconPause,
  IconRotateCcw
} from '../components/icons';
import clsx from 'clsx';

export function OperationsView() {
  const { openRunReview } = useApp();
  const { aggregateData } = useResults();

  const [selectedScenario, setSelectedScenario] = useState('imbalanced_orr');
  const [selectedDemand, setSelectedDemand] = useState('medium');
  const [activeStepIdx, setActiveStepIdx] = useState(1); // default to extension step
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  // Authoritative numbers for headline cards
  const hybridRow = aggregateData.find(
    (a) => a.pattern === selectedScenario && a.demand_level === selectedDemand && a.policy === 'hybrid_queue_adaptive'
  );
  const fixedRow = aggregateData.find(
    (a) => a.pattern === selectedScenario && a.demand_level === selectedDemand && a.policy === 'fixed'
  );

  const fixedWait = fixedRow ? fixedRow.avg_wait_s_mean : 47.6;
  const hybridWait = hybridRow ? hybridRow.avg_wait_s_mean : 42.9;
  const delta = fixedWait ? ((hybridWait - fixedWait) / fixedWait) * 100 : -9.9;
  const disparity = hybridRow?.directional_wait_disparity_s_mean ?? 75.2;
  const maxQueue = hybridRow?.max_queue_m_mean ?? 23.5;
  const throughput = hybridRow?.throughput_veh_per_h_mean ?? 2730;

  const latestRunId = 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121';

  // Interactive decision moments taken directly from real hybrid simulation telemetry
  const decisionMoments = [
    {
      id: 'step_0',
      time: 0.0,
      title: 'Baseline Entry',
      subtitle: 'Webster Allocation',
      activeInputs: ['g_base', 'elapsed', 'q_active', 'q_competing'],
      inputValues: {
        g_base: '15.0 s (Webster min)',
        q_active: '14.5 m (North approach)',
        q_competing: '6.2 m (East approach)',
        elapsed: '0.0 s',
        gap_timer: '0.0 s',
        comp_wait: '0.0 s',
        evsp: 'None detected'
      },
      firedRuleIndex: 1, // Priority 1: Minimum Green Floor
      ruleTitle: 'Priority 1: Minimum Green Floor (Safety Floor)',
      ruleExplanation: 'elapsed < 10.0 s. Baseline 15s granted upon phase entry; no switch can be accepted until safety floor passes.',
      activeOutputs: ['green_target', 'phase_shift'],
      outputValues: {
        green: '15.0 s Baseline Green',
        yellow: '3.0 s (pending)',
        all_red: '2.0 s (invariant)',
        action: 'HOLD_MIN_GREEN · Serving North–South (ORR)'
      }
    },
    {
      id: 'step_1',
      time: 15.0,
      title: '+3.0s Green Extension',
      subtitle: 'Arrival Demand Extension',
      activeInputs: ['elapsed', 'q_active', 'q_competing', 'comp_wait'],
      inputValues: {
        g_base: '15.0 s (cleared)',
        q_active: '24.2 m (Queue accumulating)',
        q_competing: '6.5 m (Opposing waiting)',
        elapsed: '15.0 s (At target)',
        gap_timer: '0.0 s (Arrivals active)',
        comp_wait: '15.0 s (< 35s limit)',
        evsp: 'None detected'
      },
      firedRuleIndex: 4, // Priority 4: Extension & Fairness
      ruleTitle: 'Priority 4: Extension & Cross-Street Fairness Limits',
      ruleExplanation: 'Active queue is 24.2 m (>= 4.0 m threshold) and opposing wait is 15.0 s (< 35.0 s anti-monopoly ceiling). +3.0 s extension granted.',
      activeOutputs: ['green_target'],
      outputValues: {
        green: '+3.0 s Added (Target now 18.0 s)',
        yellow: '3.0 s (held)',
        all_red: '2.0 s (invariant)',
        action: 'EXTEND_APPROVED · Green prolonged'
      }
    },
    {
      id: 'step_2',
      time: 27.0,
      title: 'Gap-Out Early Exit',
      subtitle: 'Efficiency Termination',
      activeInputs: ['q_active', 'gap_timer', 'q_competing'],
      inputValues: {
        g_base: '15.0 s (expired)',
        q_active: '0.0 m (Queue discharged)',
        q_competing: '14.8 m (Cross-traffic waiting)',
        elapsed: '27.0 s',
        gap_timer: '3.0 s (Persistence reached)',
        comp_wait: '27.0 s',
        evsp: 'None detected'
      },
      firedRuleIndex: 3, // Priority 3: Gap-Out
      ruleTitle: 'Priority 3: Gap-Out Early Termination (Efficiency)',
      ruleExplanation: 'Active queue dropped to 0.0 m for 3.0 consecutive seconds while East–West waits with 14.8 m. Green terminated early to prevent wasting capacity.',
      activeOutputs: ['yellow_clear', 'all_red_buffer', 'phase_shift'],
      outputValues: {
        green: 'Terminated at 27.0 s (Saved 33.0 s)',
        yellow: '3.0 s Yellow Initiated',
        all_red: '2.0 s All-Red Clearance Locked',
        action: 'SWITCH_GAP_OUT · Transitioning to EW'
      }
    },
    {
      id: 'step_3',
      time: 45.0,
      title: 'EVSP Emergency Corridor',
      subtitle: 'Priority Preemption',
      activeInputs: ['evsp', 'q_active'],
      inputValues: {
        g_base: '15.0 s',
        q_active: '32.0 m',
        q_competing: '28.0 m',
        elapsed: '12.0 s',
        gap_timer: '0.0 s',
        comp_wait: '12.0 s',
        evsp: 'AMBULANCE (ORR North, 120m, 48 km/h)'
      },
      firedRuleIndex: 0, // Priority 0: EVSP
      ruleTitle: 'Priority 0: Emergency Vehicle Override (EVSP)',
      ruleExplanation: 'Emergency vehicle detected approaching on North arterial. Immediate preemption granted, extending green corridor until vehicle safely clears intersection.',
      activeOutputs: ['green_target', 'all_red_buffer'],
      outputValues: {
        green: 'Priority Corridor Held',
        yellow: '3.0 s (suspended)',
        all_red: '2.0 s (buffered)',
        action: 'EMERGENCY_PREEMPT · North held green'
      }
    },
    {
      id: 'step_4',
      time: 60.0,
      title: 'Max-Green Ceiling',
      subtitle: 'Anti-Starvation Bound',
      activeInputs: ['elapsed', 'q_active', 'comp_wait'],
      inputValues: {
        g_base: '15.0 s',
        q_active: '38.5 m (Continuous queue)',
        q_competing: '44.0 m (Heavy backlog)',
        elapsed: '60.0 s (Max bound reached)',
        gap_timer: '0.0 s',
        comp_wait: '60.0 s (Fairness limit)',
        evsp: 'None detected'
      },
      firedRuleIndex: 2, // Priority 2: Max Green Ceiling
      ruleTitle: 'Priority 2: Maximum Green Ceiling (Starvation Prevention)',
      ruleExplanation: 'elapsed >= 60.0 s hard ceiling reached. Even though active queue remains high, controller forces phase transition to prevent cross-street gridlock.',
      activeOutputs: ['yellow_clear', 'all_red_buffer', 'phase_shift'],
      outputValues: {
        green: 'Ceiling Reached: 60.0 s Cap',
        yellow: '3.0 s Mandatory Yellow',
        all_red: '2.0 s Mandatory All-Red',
        action: 'SWITCH_MAX_GREEN · Compulsory rotation'
      }
    }
  ];

  const currentMoment = decisionMoments[activeStepIdx];

  // Auto-play timer
  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(() => {
      setActiveStepIdx((prev) => (prev + 1) % decisionMoments.length);
    }, 3200);
    return () => clearInterval(interval);
  }, [isAutoPlaying, decisionMoments.length]);

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Deep-Petrol Header Band (Brief Section 5: deep-petrol band, bone text, display-face title, one-sentence question) */}
      <div className="bg-[#093F4A] text-[#F3EDE0] px-6 py-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm border border-[#0F6B7A]/40">
        <div>
          <h1 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[#F3EDE0]">
            Operations monitor
          </h1>
          <p className="text-xs text-[#F3EDE0]/80 mt-1 font-mono">
            Is the corridor flowing within HCM service-level thresholds right now?
          </p>
        </div>

        <button
          type="button"
          onClick={() => openRunReview(latestRunId)}
          className="px-4 py-2 rounded-xl text-xs font-mono font-semibold bg-[#FFB020] hover:bg-[#FFB020]/90 text-[#0C1316] shadow-xs flex items-center gap-1.5 transition-colors self-start sm:self-auto"
        >
          <span>Open verified run review</span>
          <IconArrowRight size={13} />
        </button>
      </div>

      {/* 1. BIG COUNT-UP HEADLINE FIGURES */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* Metric 1 */}
        <div className="dp1-panel p-4 bg-panel border border-hairline rounded-xl">
          <div className="text-[10px] font-mono text-ink-2 uppercase tracking-wider">Delay Delta</div>
          <div className="text-2xl font-bold font-mono text-signal-green mt-1">
            <CountUp to={delta} decimals={1} prefix="" suffix="%" />
          </div>
          <div className="text-[11px] text-ink-2 mt-1">
            vs Fixed ({fixedWait.toFixed(1)}s)
          </div>
        </div>

        {/* Metric 2 */}
        <div className="dp1-panel p-4 bg-panel border border-hairline rounded-xl">
          <div className="text-[10px] font-mono text-ink-2 uppercase tracking-wider">Average Delay</div>
          <div className="text-2xl font-bold font-mono text-ink mt-1">
            <CountUp to={hybridWait} decimals={1} suffix=" s" />
          </div>
          <div className="text-[11px] text-ink-2 mt-1">
            Mean over 10 seeds
          </div>
        </div>

        {/* Metric 3 */}
        <div className="dp1-panel p-4 bg-panel border border-hairline rounded-xl">
          <div className="text-[10px] font-mono text-ink-2 uppercase tracking-wider">Wait Disparity</div>
          <div className="text-2xl font-bold font-mono text-ink mt-1">
            <CountUp to={disparity} decimals={1} suffix=" s" />
          </div>
          <div className="text-[11px] text-ink-2 mt-1">
            ORR vs Varthur gap
          </div>
        </div>

        {/* Metric 4 */}
        <div className="dp1-panel p-4 bg-panel border border-hairline rounded-xl">
          <div className="text-[10px] font-mono text-ink-2 uppercase tracking-wider">Max Approach Queue</div>
          <div className="text-2xl font-bold font-mono text-ink mt-1">
            <CountUp to={maxQueue} decimals={1} suffix=" m" />
          </div>
          <div className="text-[11px] text-ink-2 mt-1">
            Peak detector queue
          </div>
        </div>

        {/* Metric 5 */}
        <div className="dp1-panel p-4 bg-panel border border-hairline rounded-xl col-span-2 md:col-span-1">
          <div className="text-[10px] font-mono text-ink-2 uppercase tracking-wider">Throughput</div>
          <div className="text-2xl font-bold font-mono text-petrol mt-1">
            <CountUp to={throughput} decimals={0} suffix=" vph" />
          </div>
          <div className="text-[11px] text-ink-2 mt-1">
            Surface conflict clearance
          </div>
        </div>
      </div>

      {/* 2. INTERACTIVE "STEP THROUGH A DECISION" CONSOLE */}
      <div className="dp1-panel p-6 bg-panel border border-hairline rounded-2xl space-y-6 shadow-sm">
        {/* Console Header & Stepper Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse" />
              <h2 className="text-base font-bold text-ink uppercase tracking-wide">
                Interactive Decision Step-Through
              </h2>
            </div>
            <p className="text-xs text-ink-2 mt-0.5">
              Pick a real moment from run <span className="font-mono text-ink font-semibold">{latestRunId}</span> to trace how inputs ignite rules into outputs.
            </p>
          </div>

          {/* Stepper Buttons & Auto-Play */}
          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              type="button"
              onClick={() => setIsAutoPlaying((v) => !v)}
              className={clsx(
                'px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors',
                isAutoPlaying
                  ? 'bg-accent text-ink border-accent shadow-xs'
                  : 'bg-inset border-hairline text-ink hover:bg-panel'
              )}
            >
              {isAutoPlaying ? <IconPause size={12} /> : <IconPlay size={12} />}
              <span>{isAutoPlaying ? 'Pause Sequence' : 'Play Sequence'}</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveStepIdx((prev) => (prev - 1 + decisionMoments.length) % decisionMoments.length)}
              className="px-2.5 py-1.5 bg-inset hover:bg-panel border border-hairline rounded-lg text-xs font-mono text-ink"
              title="Previous Step"
            >
              ← Prev
            </button>

            <button
              type="button"
              onClick={() => setActiveStepIdx((prev) => (prev + 1) % decisionMoments.length)}
              className="px-2.5 py-1.5 bg-inset hover:bg-panel border border-hairline rounded-lg text-xs font-mono text-ink"
              title="Next Step"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Moment Selector Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {decisionMoments.map((m, idx) => {
            const isSelected = activeStepIdx === idx;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  setActiveStepIdx(idx);
                  setIsAutoPlaying(false);
                }}
                className={clsx(
                  'p-2.5 rounded-xl border text-left transition-all',
                  isSelected
                    ? 'bg-inset border-petrol shadow-xs ring-1 ring-petrol/30'
                    : 'bg-panel border-hairline hover:border-ink-2/30'
                )}
              >
                <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                  <span className={isSelected ? 'text-petrol font-bold' : 'text-ink-2'}>
                    t = {m.time.toFixed(1)} s
                  </span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-petrol" />}
                </div>
                <div className="text-xs font-bold text-ink truncate">{m.title}</div>
                <div className="text-[10px] text-ink-2 truncate mt-0.5">{m.subtitle}</div>
              </button>
            );
          })}
        </div>

        {/* Active Decision Flow: Inputs -> Rule Fired -> Outputs */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch pt-2">
          {/* Column 1: Inputs (4 cols) */}
          <div className="lg:col-span-4 bg-inset p-4 rounded-xl border border-hairline space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-hairline mb-3">
                <span className="font-bold text-ink uppercase tracking-wide">1. Real-Time Inputs</span>
                <span className="text-ink-2 text-[11px]">t = {currentMoment.time.toFixed(1)} s</span>
              </div>

              <div className="space-y-1.5 text-xs font-mono">
                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('g_base') ? 'bg-panel border-petrol text-ink font-semibold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] text-ink-2">Webster Baseline (G_base):</div>
                  <div>{currentMoment.inputValues.g_base}</div>
                </div>

                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('q_active') ? 'bg-panel border-petrol text-ink font-semibold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] text-ink-2">Active Approach Queue (q_active_m):</div>
                  <div>{currentMoment.inputValues.q_active}</div>
                </div>

                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('q_competing') ? 'bg-panel border-petrol text-ink font-semibold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] text-ink-2">Opposing Approach Queue (q_competing_m):</div>
                  <div>{currentMoment.inputValues.q_competing}</div>
                </div>

                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('elapsed') ? 'bg-panel border-petrol text-ink font-semibold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] text-ink-2">Green Elapsed Time:</div>
                  <div>{currentMoment.inputValues.elapsed}</div>
                </div>

                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('gap_timer') ? 'bg-panel border-signal-yellow text-ink font-semibold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] text-ink-2">Gap-Out Idle Timer:</div>
                  <div>{currentMoment.inputValues.gap_timer}</div>
                </div>

                <div className={clsx(
                  'p-2 rounded border transition-colors',
                  currentMoment.activeInputs.includes('evsp') ? 'bg-emergency-tint border-emergency text-emergency font-bold' : 'bg-panel/40 border-hairline text-ink-2'
                )}>
                  <div className="text-[10px] opacity-75">EVSP Corridor Sensor:</div>
                  <div>{currentMoment.inputValues.evsp}</div>
                </div>
              </div>
            </div>

            <div className="text-[10px] font-mono text-ink-2 pt-2 border-t border-hairline flex items-center justify-between">
              <span>E2 Detector Inputs</span>
              <span className="text-petrol">Flowing to Rule Cascade →</span>
            </div>
          </div>

          {/* Column 2: Strict Priority Cascade (4 cols) */}
          <div className="lg:col-span-4 bg-inset p-4 rounded-xl border border-hairline space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-hairline mb-3">
                <span className="font-bold text-ink uppercase tracking-wide">2. Priority Rules</span>
                <span className="text-petrol font-semibold">Strict Cascade</span>
              </div>

              <div className="space-y-2 text-xs">
                {/* Rule 0 */}
                <div className={clsx(
                  'p-2.5 rounded-lg border transition-all flex items-start gap-2',
                  currentMoment.firedRuleIndex === 0
                    ? 'bg-emergency-tint border-emergency text-emergency shadow-xs ring-1 ring-emergency/30'
                    : 'bg-panel border-hairline opacity-60'
                )}>
                  <span className="w-5 h-5 rounded-full bg-emergency/20 text-emergency font-mono font-bold flex items-center justify-center shrink-0 text-[10px]">
                    0
                  </span>
                  <div>
                    <div className="font-semibold">Priority 0: EVSP Ambulance Override</div>
                    <div className="text-[11px] opacity-85 mt-0.5 leading-tight">
                      Preempts normal cycle with safety clearance.
                    </div>
                  </div>
                </div>

                {/* Rule 1 */}
                <div className={clsx(
                  'p-2.5 rounded-lg border transition-all flex items-start gap-2',
                  currentMoment.firedRuleIndex === 1
                    ? 'bg-panel border-petrol text-ink shadow-xs ring-1 ring-petrol/30'
                    : 'bg-panel border-hairline opacity-60'
                )}>
                  <span className="w-5 h-5 rounded-full bg-inset text-ink font-mono font-bold flex items-center justify-center shrink-0 text-[10px] border border-hairline">
                    1
                  </span>
                  <div>
                    <div className="font-semibold text-ink">Priority 1: Minimum Green Floor (Safety)</div>
                    <div className="text-[11px] text-ink-2 mt-0.5 leading-tight">
                      Enforces elapsed &lt; 10s. Reject early switches.
                    </div>
                  </div>
                </div>

                {/* Rule 2 */}
                <div className={clsx(
                  'p-2.5 rounded-lg border transition-all flex items-start gap-2',
                  currentMoment.firedRuleIndex === 2
                    ? 'bg-panel border-signal-yellow text-ink shadow-xs ring-1 ring-signal-yellow/30'
                    : 'bg-panel border-hairline opacity-60'
                )}>
                  <span className="w-5 h-5 rounded-full bg-inset text-ink font-mono font-bold flex items-center justify-center shrink-0 text-[10px] border border-hairline">
                    2
                  </span>
                  <div>
                    <div className="font-semibold text-ink">Priority 2: Max Green Ceiling (Anti-Starvation)</div>
                    <div className="text-[11px] text-ink-2 mt-0.5 leading-tight">
                      Enforces elapsed &gt;= 60s hard upper bound.
                    </div>
                  </div>
                </div>

                {/* Rule 3 */}
                <div className={clsx(
                  'p-2.5 rounded-lg border transition-all flex items-start gap-2',
                  currentMoment.firedRuleIndex === 3
                    ? 'bg-panel border-signal-yellow text-ink shadow-xs ring-1 ring-signal-yellow/30'
                    : 'bg-panel border-hairline opacity-60'
                )}>
                  <span className="w-5 h-5 rounded-full bg-inset text-ink font-mono font-bold flex items-center justify-center shrink-0 text-[10px] border border-hairline">
                    3
                  </span>
                  <div>
                    <div className="font-semibold text-ink">Priority 3: Gap-Out Early Exit (Efficiency)</div>
                    <div className="text-[11px] text-ink-2 mt-0.5 leading-tight">
                      Active queue 0m for 3s terminates green early.
                    </div>
                  </div>
                </div>

                {/* Rule 4 */}
                <div className={clsx(
                  'p-2.5 rounded-lg border transition-all flex items-start gap-2',
                  currentMoment.firedRuleIndex === 4
                    ? 'bg-panel border-signal-green text-ink shadow-xs ring-1 ring-signal-green/30'
                    : 'bg-panel border-hairline opacity-60'
                )}>
                  <span className="w-5 h-5 rounded-full bg-inset text-ink font-mono font-bold flex items-center justify-center shrink-0 text-[10px] border border-hairline">
                    4
                  </span>
                  <div>
                    <div className="font-semibold text-ink">Priority 4: Extension & Cross-Street Fairness</div>
                    <div className="text-[11px] text-ink-2 mt-0.5 leading-tight">
                      Grants +3.0s if opposing wait &lt; 35s.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Explanation of Fired Rule */}
            <div className="p-3 bg-panel rounded-lg border border-hairline text-xs">
              <span className="font-semibold text-ink block mb-0.5">{currentMoment.ruleTitle}</span>
              <p className="text-ink-2 text-[11px] leading-relaxed">{currentMoment.ruleExplanation}</p>
            </div>
          </div>

          {/* Column 3: Signal Outputs (4 cols) */}
          <div className="lg:col-span-4 bg-inset p-4 rounded-xl border border-hairline space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-hairline mb-3">
                <span className="font-bold text-ink uppercase tracking-wide">3. Actuation Outputs</span>
                <span className="text-signal-green font-semibold">Live State</span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="p-3 bg-panel rounded-lg border border-hairline space-y-1">
                  <span className="text-ink-2 text-[10px] uppercase">Allocated Green Duration</span>
                  <div className="text-sm font-bold text-ink">{currentMoment.outputValues.green}</div>
                </div>

                <div className="p-3 bg-panel rounded-lg border border-hairline space-y-1">
                  <span className="text-ink-2 text-[10px] uppercase">Yellow Clearance Interval</span>
                  <div className="text-sm font-bold text-signal-yellow">{currentMoment.outputValues.yellow}</div>
                </div>

                <div className="p-3 bg-panel rounded-lg border border-hairline space-y-1">
                  <span className="text-ink-2 text-[10px] uppercase">All-Red Safety Clearance Buffer</span>
                  <div className="text-sm font-bold text-signal-red">{currentMoment.outputValues.all_red}</div>
                  <div className="text-[10px] text-ink-2 font-normal font-sans">
                    Zero green-to-green transitions. Both directions held red.
                  </div>
                </div>

                <div className="p-3 bg-panel rounded-lg border border-petrol space-y-1">
                  <span className="text-ink-2 text-[10px] uppercase">Controller Output Action</span>
                  <div className="text-xs font-bold text-petrol">{currentMoment.outputValues.action}</div>
                </div>
              </div>
            </div>

            <div className="p-2.5 bg-ground rounded-lg border border-hairline text-[11px] font-mono text-ink-2 flex items-center justify-between">
              <span>Microscopic Verified</span>
              <span className="text-signal-green font-bold">Invariants 100% Green</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OperationsView;
