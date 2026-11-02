import React, { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { useResults, POLICY_META } from '../context/useResults';
import { JunctionTwin } from '../components/JunctionTwin';
import { DecisionTimeline } from '../components/DecisionTimeline';
import { CountUp } from '../components/motion/CountUp';
import { MagneticButton, TiltPanel } from '../components/motion/MagneticButton';
import { SignalHead } from '../components/motion/SignalHead';
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Layers,
  Activity,
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Clock,
  Car,
  TrendingDown
} from 'lucide-react';
import clsx from 'clsx';

export function LandingPageView() {
  const { setCurrentView, openRunReview } = useApp();
  const { aggregateData, siteHeadline, syntheticHeadline, getComparisonTable } = useResults();
  const shouldReduceMotion = useReducedMotion();

  // --- SECTION 2: Pinned Cycle Steps State ---
  // Real steps taken from recorded run: marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121
  const cycleSteps = [
    {
      step: 1,
      time: 't = 0.0 s',
      phase: 'GREEN',
      axis: 'North–South (ORR)',
      num: '15.0 s',
      label: 'Webster Baseline Green',
      metricLabel: 'Minimum Floor',
      action: 'Baseline green entry',
      prose: 'North–South green starts with 15.0 s allocation. Queue at stopline measures 14.5 m on ORR North.',
      decision: { t: 0.0, cycle: 0, axis: 'NS', applied_action: 'ENTER_GREEN', target_green_s: 15.0, q_active_m: 14.5, q_competing_m: 6.2 }
    },
    {
      step: 2,
      time: 't = 15.0 s',
      phase: 'GREEN',
      axis: 'North–South (ORR)',
      num: '+3.0 s',
      label: 'Queue-Length Extension',
      metricLabel: 'Extension Granted',
      action: 'Added green time',
      prose: 'High inflow detected (22.0 m queue > 4.0 m threshold). Controller grants +3.0 s extension to drain platoon.',
      decision: { t: 15.0, cycle: 0, axis: 'NS', applied_action: 'EXTEND', delta_g_app_s: 3.0, target_green_s: 18.0, q_active_m: 22.0, q_competing_m: 5.0 }
    },
    {
      step: 3,
      time: 't = 27.0 s',
      phase: 'YELLOW',
      axis: 'North–South (ORR)',
      num: '0.0 m',
      label: 'Early Gap-Out Exit',
      metricLabel: 'Queue at Gap-Out',
      action: 'Ended green early',
      prose: 'ORR queue clears (0.0 m for 3.0 s) while Varthur cross-street waits with 28.5 m. Green ends early to prevent cross-street starvation.',
      decision: { t: 27.0, cycle: 0, axis: 'NS', applied_action: 'GAP_OUT', target_green_s: 27.0, q_active_m: 0.0, q_competing_m: 28.5 }
    },
    {
      step: 4,
      time: 't = 28.0 s – 33.0 s',
      phase: 'ALL_RED',
      axis: 'Interphase Clearance',
      num: '5.0 s',
      label: 'Clearance Safety Buffer',
      metricLabel: 'Clearance Buffer',
      action: 'Yellow (3s) + All-Red (2s)',
      prose: 'Strict clearance safety interval enforced: 3.0 s yellow followed by 2.0 s all-red clearance before opposing green can illuminate.',
      decision: { t: 30.0, cycle: 0, axis: 'ALL_RED', applied_action: 'CLEARANCE', target_green_s: 5.0, q_active_m: 0.0, q_competing_m: 28.5 }
    },
    {
      step: 5,
      time: 't = 42.0 s',
      phase: 'GREEN',
      axis: 'ORR North (EVSP Corridor)',
      num: '350 m',
      label: 'Ambulance Preemption',
      metricLabel: 'Ambulance Distance',
      action: 'Emergency Vehicle Priority',
      prose: 'Emergency vehicle detected 350 m upstream traveling 45 km/h. Controller holds green corridor open until clearance.',
      decision: { t: 42.0, cycle: 1, axis: 'NS', applied_action: 'EMERGENCY_PREEMPT', is_emergency: true, target_green_s: 24.0, q_active_m: 35.0, q_competing_m: 12.0 }
    }
  ];

  const [activeStepIdx, setActiveStepIdx] = useState(0);
  const activeStep = cycleSteps[activeStepIdx];

  // Auto-advance step every 5 seconds if user is idle
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStepIdx((prev) => (prev + 1) % cycleSteps.length);
    }, 5500);
    return () => clearInterval(timer);
  }, [cycleSteps.length]);

  // --- SECTION 4: The Live Thing (Interactive Controller Delay Comparison) ---
  const [livePattern, setLivePattern] = useState('imbalanced_orr');
  const [liveDemand, setLiveDemand] = useState('medium');

  const liveTableRows = useMemo(() => {
    const rows = getComparisonTable(livePattern, liveDemand);
    return [...rows].sort((a, b) => a.avgWaitS - b.avgWaitS);
  }, [getComparisonTable, livePattern, liveDemand]);

  const maxWaitInLive = useMemo(() => {
    return Math.max(65, ...liveTableRows.map((r) => r.avgWaitS + 5));
  }, [liveTableRows]);

  // --- SECTION 5: Junction Exploded Tiers State ---
  const [hoveredTier, setHoveredTier] = useState(null);

  const tiers = [
    {
      id: 'flyover',
      tier: 'Tier 1',
      name: 'Elevated Varthur Flyover',
      elevation: '+7.0 m Overpass',
      lanes: '4-Lane Dual Carriageway',
      stats: '70% through traffic · Free flow',
      desc: 'Carries direct commuter flows over the junction without intersection delay.',
      color: '#F6A81C',
    },
    {
      id: 'surface',
      tier: 'Tier 2',
      name: 'Surface Conflict Node',
      elevation: 'Grade-0 Level',
      lanes: '8 E2 Induction Loop Detectors',
      stats: '100% of turns + 30% through flow',
      desc: 'The signalized bottleneck where hybrid adaptive control optimizes green phase allocation.',
      color: '#5AA7B1',
    },
    {
      id: 'underpass',
      tier: 'Tier 3',
      name: 'ORR Mainline Underpass',
      elevation: 'Grade-0 Underpass Trench',
      lanes: '6-Lane Major Arterial',
      stats: '70% ORR through traffic · Zero stopping',
      desc: 'High-speed corridor trench siphoning major north–south through transit under the junction.',
      color: '#3F9B66',
    },
  ];

  return (
    <div className="w-full bg-ground text-ink min-h-screen overflow-x-hidden pt-16 sm:pt-20">
      {/* =========================================================================
          SECTION 1: HERO (Asphalt Field #0E1112)
          ========================================================================= */}
      <section className="relative w-full min-h-[92vh] flex flex-col justify-center px-4 sm:px-8 lg:px-16 py-12 bg-ground border-b border-hairline">
        <div className="max-w-[1500px] w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column: Bold Typography & Direct Copy */}
          <div className="lg:col-span-6 space-y-6 z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-panel border border-hairline text-xs font-mono text-ink-2">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              <span>Alliance University · B.Tech AI & Data Science</span>
            </div>

            {/* Display Headline: 2 lines or fewer, Barlow Condensed road-sign lettering */}
            <h1 className="font-display font-extrabold text-5xl sm:text-7xl lg:text-8xl tracking-tight text-ink leading-[0.92] uppercase">
              Signals that read the queue.
            </h1>

            {/* Subtitle: Exactly 1 sentence */}
            <p className="text-base sm:text-lg text-ink-2 max-w-xl font-normal leading-relaxed">
              A hybrid controller that extends, ends or holds green by the second, tested on Marathahalli Bridge in SUMO.
            </p>

            {/* Primary Action + Link */}
            <div className="flex flex-wrap items-center gap-4 pt-4">
              <MagneticButton
                onClick={() => setCurrentView('live-simulation')}
                className="group px-6 py-3.5 rounded-full bg-accent text-ink font-bold text-sm tracking-tight shadow-md hover:brightness-105 transition-all"
              >
                <span>Launch live simulation</span>
                <span className="w-5 h-5 rounded-full bg-ink/10 flex items-center justify-center ml-2 group-hover:translate-x-0.5 transition-transform">
                  <Play size={11} className="fill-ink text-ink" />
                </span>
              </MagneticButton>

              <button
                type="button"
                onClick={() => setCurrentView('evidence')}
                className="px-5 py-3 rounded-full text-xs font-semibold text-ink-2 hover:text-ink hover:bg-panel border border-hairline transition-colors flex items-center gap-1.5"
              >
                <span>See the evidence</span>
                <ArrowRight size={13} />
              </button>
            </div>

            {/* Truthful Baseline Attribution Strip */}
            <div className="pt-4 border-t border-hairline/60 flex flex-wrap items-center gap-4 text-xs font-mono text-ink-2">
              <span>Site: Marathahalli Bridge, ORR</span>
              <span>•</span>
              <span>SUMO TraCI</span>
              <span>•</span>
              <span>N=10 Held-out Seeds (121–130)</span>
            </div>
          </div>

          {/* Right Column: 3D Twin Viewport in Ambient Mode with Pointer Tilt */}
          <div className="lg:col-span-6 w-full">
            <TiltPanel maxTilt={5} className="w-full">
              <div className="relative rounded-2xl overflow-hidden border border-hairline bg-panel shadow-2xl">
                <JunctionTwin
                  mode="ambient"
                  runId="marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121"
                  height={440}
                  className="w-full"
                />

                <div className="p-3 bg-raised border-t border-hairline flex items-center justify-between text-xs font-mono text-ink-2">
                  <span>Run: marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121</span>
                  <span className="text-accent font-semibold">1:1 SUMO TraCI Micro-Replay</span>
                </div>
              </div>
            </TiltPanel>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 2: THE CYCLE (Pinned Scroll Scene from Real Hybrid Run)
          ========================================================================= */}
      <section id="the-cycle" className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-panel border-b border-hairline">
        <div className="max-w-[1500px] w-full mx-auto space-y-10">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono text-accent uppercase tracking-wider font-bold">
              <Clock size={14} />
              <span>Actuation Sequence</span>
            </div>
            <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight text-ink uppercase">
              The Signal Cycle: One Junction Decision.
            </h2>
            <p className="text-sm sm:text-base text-ink-2 max-w-2xl font-normal">
              Step through real decisions recorded in run <span className="font-mono text-ink font-semibold">marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121</span>, showing how seconds are added, cleared, or held.
            </p>
          </div>

          {/* Interactive Pinned Decision Steps Carousel / Interactive Stage */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left: Step Selector Cards (thumb-friendly) */}
            <div className="lg:col-span-5 space-y-3">
              {cycleSteps.map((s, idx) => {
                const isCurrent = idx === activeStepIdx;
                return (
                  <button
                    key={s.step}
                    type="button"
                    onClick={() => setActiveStepIdx(idx)}
                    className={clsx(
                      'w-full text-left p-4 rounded-xl border transition-all flex items-start gap-3.5',
                      isCurrent
                        ? 'bg-raised border-accent shadow-md'
                        : 'bg-ground/60 border-hairline hover:bg-ground hover:border-ink-2/30 text-ink-2'
                    )}
                  >
                    <SignalHead phase={s.phase} size="sm" className="mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className={clsx('text-xs font-bold uppercase tracking-wider', isCurrent ? 'text-accent' : 'text-ink')}>
                          Step {s.step} · {s.time}
                        </span>
                        <span className="font-mono font-extrabold text-sm text-ink tabular-nums">
                          {s.num}
                        </span>
                      </div>
                      <div className="text-xs font-bold text-ink mt-0.5">{s.label}</div>
                      <p className="text-xs text-ink-2 mt-1 leading-snug">
                        {s.prose}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right: Live Interactive Twin & Decision Timeline synced to selected step */}
            <div className="lg:col-span-7 space-y-4">
              <div className="rounded-2xl border border-hairline bg-ground overflow-hidden shadow-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-hairline pb-3">
                  <div className="flex items-center gap-2">
                    <SignalHead phase={activeStep.phase} size="sm" />
                    <div>
                      <span className="text-xs font-mono uppercase text-ink-2">Active Phase Actuation</span>
                      <div className="text-sm font-bold text-ink">{activeStep.action} on {activeStep.axis}</div>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[11px] font-mono text-ink-2">{activeStep.metricLabel || 'Target Duration'}</span>
                    <div className="text-base font-mono font-extrabold text-accent">{activeStep.num}</div>
                  </div>
                </div>

                {/* Microscopic Twin at Step Time */}
                <div className="rounded-xl overflow-hidden border border-hairline">
                  <JunctionTwin
                    mode="replay"
                    runId="marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121"
                    currentTime={activeStep.decision.t}
                    height={280}
                  />
                </div>

                {/* Timeline Representation */}
                <div className="p-3 bg-panel rounded-xl border border-hairline space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-ink-2">
                    <span>Synchronized Decision Timeline</span>
                    <span>t = {activeStep.decision.t.toFixed(1)}s</span>
                  </div>
                  <DecisionTimeline
                    decisions={cycleSteps.map(c => c.decision)}
                    currentTime={activeStep.decision.t}
                    totalDuration={50}
                    onSeek={(t) => {
                      const closestIdx = cycleSteps.findIndex(c => Math.abs(c.decision.t - t) < 10);
                      if (closestIdx !== -1) setActiveStepIdx(closestIdx);
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 3: PROOF (Full-Bleed Signal-Amber Field #F6A81C)
          ========================================================================= */}
      <section id="proof" className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-accent text-ink">
        <div className="max-w-[1500px] w-full mx-auto space-y-12">
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest font-extrabold text-ink/75">
              Empirical Proof
            </span>
            <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight text-ink uppercase leading-none">
              Evaluated across identical seeds.
            </h2>
            <p className="text-sm sm:text-base text-ink/85 max-w-2xl font-medium">
              Every metric below comes from real SUMO runs. No hand-edits, no simulated live claims.
            </p>
          </div>

          {/* Three Huge Count-Up Numbers */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Stat 1: Experiment Runs */}
            <div className="p-6 rounded-2xl bg-ink/5 border border-ink/10 space-y-2 group hover:bg-ink/10 transition-colors">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-ink/80 block">
                Total Evaluated Runs
              </span>
              <div className="text-6xl sm:text-7xl font-display font-extrabold tracking-tight text-ink leading-none">
                <CountUp to={840} duration={1.5} />
              </div>
              <p className="text-xs text-ink/85 font-medium pt-1">
                7 control policies across 4 demand scenarios evaluated over N=10 held-out seeds (121–130).
              </p>
              <div className="text-[10px] font-mono text-ink/65 pt-2 border-t border-ink/10">
                Basis: exp_marathahalli_hybrid_840
              </div>
            </div>

            {/* Stat 2: Invariant Safety Violations */}
            <div className="p-6 rounded-2xl bg-ink/5 border border-ink/10 space-y-2 group hover:bg-ink/10 transition-colors">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-ink/80 block">
                Safety Invariant Violations
              </span>
              <div className="text-6xl sm:text-7xl font-display font-extrabold tracking-tight text-ink leading-none">
                <CountUp to={0} duration={0.8} />
              </div>
              <p className="text-xs text-ink/85 font-medium pt-1">
                Zero green-to-green transitions. 100% adherence to 3.0 s yellow and 2.0 s all-red clearance buffers.
              </p>
              <div className="text-[10px] font-mono text-ink/65 pt-2 border-t border-ink/10">
                Enforced by: tests/test_core.py
              </div>
            </div>

            {/* Stat 3: Real Delay Reduction */}
            <div className="p-6 rounded-2xl bg-ink/5 border border-ink/10 space-y-2 group hover:bg-ink/10 transition-colors">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-ink/80 block">
                Corridor Delay Reduction
              </span>
              <div className="text-6xl sm:text-7xl font-display font-extrabold tracking-tight text-ink leading-none">
                <span>-</span>
                <CountUp to={9.9} decimals={1} duration={1.3} suffix="%" />
              </div>
              <p className="text-xs text-ink/85 font-medium pt-1">
                Real site model delay: 42.9 s/veh hybrid vs 47.6 s/veh fixed-time on Marathahalli real road.
              </p>
              <div className="text-[10px] font-mono text-ink/65 pt-2 border-t border-ink/10">
                Synthetic benchmark: -64.9% (seeds 11–15)
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 4: THE LIVE THING (Interactive 7-Controller Settling Bars)
          ========================================================================= */}
      {/* =========================================================================
          SECTION 4: THE LIVE THING (Interactive 7-Controller Settling Bars)
          Brief: full-bleed deep petrol with bone text; hybrid bar in amber, other bars in light petrol-grey
          ========================================================================= */}
      <section id="the-live-thing" className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-[#093F4A] text-[#F3EDE0] border-b border-[#0F6B7A]/30">
        <div className="max-w-[1500px] w-full mx-auto space-y-10">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="space-y-2">
              <span className="text-xs font-mono uppercase tracking-widest text-[#FFB020] font-bold">
                The Live Thing
              </span>
              <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight text-[#F3EDE0] uppercase">
                Watch the seven policies settle.
              </h2>
              <p className="text-sm sm:text-base text-[#F3EDE0]/85 max-w-2xl font-normal">
                Pick a demand pattern and watch the controllers re-rank dynamically based on real evaluation results.
              </p>
            </div>

            {/* Demand Pattern Pills (No awkward wrapping) */}
            <div className="flex items-center gap-1.5 p-1.5 rounded-full bg-[#07252C] border border-[#0F6B7A]/40 overflow-x-auto whitespace-nowrap max-w-full">
              {[
                { id: 'imbalanced_orr', label: 'Imbalanced ORR' },
                { id: 'balanced', label: 'Balanced 4-Way' },
                { id: 'imbalanced_varthur', label: 'Varthur Rd' },
                { id: 'surge_orr_north', label: 'Surge North' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setLivePattern(p.id)}
                  className={clsx(
                    'px-4 py-1.5 rounded-full text-xs font-semibold transition-all shrink-0',
                    livePattern === p.id
                      ? 'bg-[#FFB020] text-[#0C1316] shadow-sm font-bold'
                      : 'text-[#F3EDE0]/80 hover:text-[#F3EDE0] hover:bg-[#0F6B7A]/30'
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Re-Ranking Layout Bars */}
          <div className="rounded-2xl border border-[#0F6B7A]/40 bg-[#0C242C] p-6 sm:p-8 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between text-xs font-mono text-[#F3EDE0]/75 pb-2 border-b border-[#0F6B7A]/30">
              <span>Controller Policy (Ranked by Lowest Delay)</span>
              <span>Average Delay (s/veh) & Delta vs Fixed</span>
            </div>

            <div className="space-y-3">
              {liveTableRows.map((row, idx) => {
                const isHybrid = row.meta.isHybrid;
                const isBaseline = row.meta.isBaseline;
                const percentWidth = Math.min(100, Math.max(12, (row.avgWaitS / maxWaitInLive) * 100));

                return (
                  <motion.div
                    key={row.policy}
                    layout={!shouldReduceMotion}
                    transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                    className={clsx(
                      'p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors',
                      isHybrid
                        ? 'bg-[#123640] border-[#FFB020] shadow-md'
                        : 'bg-[#0E2A32] border-[#0F6B7A]/30 hover:border-[#0F6B7A]/60'
                    )}
                  >
                    <div className="flex items-center gap-3 w-64 shrink-0">
                      <span className="font-mono text-xs font-bold text-[#F3EDE0]/60 w-6">
                        #{idx + 1}
                      </span>
                      <div className="flex items-center gap-2">
                        {isHybrid ? (
                          <span className="w-2.5 h-2.5 rounded-full bg-[#FFB020] shrink-0 shadow-sm animate-pulse" />
                        ) : (
                          <span className="w-2 h-2 rounded-full bg-[#7DA9B2]/60 shrink-0" />
                        )}
                        <span className={clsx('text-xs font-bold', isHybrid ? 'text-[#FFB020]' : 'text-[#F3EDE0]')}>
                          {row.meta.label}
                        </span>
                      </div>
                    </div>

                    {/* Animated Bar Graphic (Both hybrid in amber and other bars in light petrol-grey animate clearly) */}
                    <div className="flex-1 w-full relative h-4 bg-[#071D23] rounded-full overflow-hidden border border-[#0F6B7A]/40">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentWidth}%` }}
                        transition={{ duration: 0.6, ease: [0.32, 0.72, 0, 1] }}
                        className={clsx(
                          'h-full rounded-full transition-all',
                          isHybrid ? 'bg-[#FFB020]' : 'bg-[#7DA9B2]'
                        )}
                      />
                    </div>

                    {/* Value Metrics */}
                    <div className="flex items-center justify-end gap-3 w-40 shrink-0 font-mono text-xs">
                      <span className="font-extrabold text-[#F3EDE0] tabular-nums">
                        {row.avgWaitS.toFixed(1)} s
                      </span>
                      {isBaseline ? (
                        <span className="text-[#F3EDE0]/60 text-[11px]">Reference</span>
                      ) : (
                        <span
                          className={clsx(
                            'text-[11px] font-bold px-2 py-0.5 rounded',
                            row.deltaPercent < 0
                              ? 'bg-[#2FA866]/30 text-[#53D38E]'
                              : 'bg-[#D6453D]/30 text-[#F37D76]'
                          )}
                        >
                          {row.deltaPercent > 0 ? `+${row.deltaPercent.toFixed(1)}%` : `${row.deltaPercent.toFixed(1)}%`}
                        </span>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Semantic No-JS fallback table for accessibility */}
            <noscript>
              <table className="w-full text-left text-xs text-[#F3EDE0]">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Policy</th>
                    <th>Avg Delay</th>
                    <th>vs Fixed</th>
                  </tr>
                </thead>
                <tbody>
                  {liveTableRows.map((r, i) => (
                    <tr key={r.policy}>
                      <td>#{i + 1}</td>
                      <td>{r.meta.label}</td>
                      <td>{r.avgWaitS.toFixed(1)} s</td>
                      <td>{r.deltaPercent.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </noscript>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 5: THE JUNCTION (Exploded Three-Tier View Driven on Hover / Tap)
          Brief: bone field, hovering or tapping a tier card drives the exploded twin
          ========================================================================= */}
      <section id="the-junction" className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-panel border-b border-hairline">
        <div className="max-w-[1500px] w-full mx-auto space-y-10">
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest text-accent font-bold">
              Site Architecture
            </span>
            <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight text-ink uppercase">
              The Junction: 3-Tier Separation.
            </h2>
            <p className="text-sm sm:text-base text-ink-2 max-w-2xl font-normal">
              Hover or tap each tier to separate the physical geometry modeled in SUMO.
            </p>
          </div>

          {/* Shared 3D Twin Visual Driven by Hovered Tier Card */}
          <div className="rounded-2xl border border-hairline bg-ground p-3.5 shadow-xl space-y-2">
            <div className="flex items-center justify-between px-3 py-1.5 text-xs font-mono border-b border-hairline text-ink-2">
              <span className="font-bold text-ink flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-signal-green animate-pulse" />
                <span>3-Tier Exploded Microscopic Twin</span>
              </span>
              <span className="text-accent font-semibold">
                {hoveredTier ? `ISOLATING: ${hoveredTier.toUpperCase()} (EXPLODED)` : 'HOVER OR TAP A TIER CARD BELOW'}
              </span>
            </div>
            <div className="rounded-xl overflow-hidden">
              <JunctionTwin
                mode="overview"
                runId="marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121"
                height={380}
                isExploded={hoveredTier !== null}
                soloTier={hoveredTier}
                showControls={false}
                className="w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {tiers.map((t) => (
              <div
                key={t.id}
                onMouseEnter={() => setHoveredTier(t.id)}
                onMouseLeave={() => setHoveredTier(null)}
                onClick={() => setHoveredTier((prev) => (prev === t.id ? null : t.id))}
                className={clsx(
                  'p-6 rounded-2xl border transition-all duration-300 space-y-4 flex flex-col justify-between cursor-pointer',
                  hoveredTier === t.id
                    ? 'bg-raised border-accent ring-2 ring-accent -translate-y-2 shadow-xl'
                    : 'bg-panel border-hairline hover:border-ink-2/40'
                )}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider text-accent">
                      {t.tier}
                    </span>
                    <span className={clsx("text-xs font-mono px-2.5 py-0.5 rounded border border-hairline", hoveredTier === t.id ? "bg-accent text-ink font-bold" : "text-ink-2 bg-ground")}>
                      {t.elevation}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-ink">{t.name}</h3>
                  <div className="text-xs font-mono text-ink font-semibold">{t.lanes}</div>
                  <p className="text-xs text-ink-2 leading-relaxed">{t.desc}</p>
                </div>

                <div className="pt-4 border-t border-hairline text-xs font-mono text-accent font-semibold flex items-center justify-between">
                  <span>{hoveredTier === t.id ? 'Tap to restore' : t.stats}</span>
                  <ChevronRight size={14} className={hoveredTier === t.id ? "rotate-90 transition-transform" : ""} />
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-xl bg-ground border border-hairline flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <span className="text-ink-2">
              Full Highway Capacity Manual (HCM) split assignment: 70% through via flyover/underpass, 30% surface roundabout.
            </span>
            <button
              type="button"
              onClick={() => setCurrentView('junction')}
              className="text-accent font-semibold flex items-center gap-1 hover:underline shrink-0"
            >
              <span>Explore 3-tier junction model</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 6: EVIDENCE (Ink Field #0C1316 with Bone Text)
          ========================================================================= */}
      <section id="evidence" className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-[#0C1316] text-[#F2EEE4] border-b border-[#2B373C]">
        <div className="max-w-[1500px] w-full mx-auto space-y-10">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="space-y-2">
              <span className="text-xs font-mono uppercase tracking-widest text-[#FFB020] font-bold">
                Verification Proof
              </span>
              <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight text-[#F2EEE4] uppercase">
                Audited evidence catalog.
              </h2>
              <p className="text-sm sm:text-base text-[#AEB8BA] max-w-2xl font-normal">
                Every claim is backed by complete JSON telemetry, TraCI trajectory logs, and reproducible pytest suites.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setCurrentView('evidence')}
              className="px-5 py-2.5 rounded-full bg-[#12191C] border border-[#2B373C] text-xs font-semibold text-[#F2EEE4] hover:bg-[#1A2327] transition-colors flex items-center gap-2 self-start sm:self-auto"
            >
              <span>Open full evidence suite</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-[#12191C] border border-[#2B373C] space-y-1">
              <span className="text-xs font-mono text-[#AEB8BA]">Aggregate Runs</span>
              <div className="text-3xl font-display font-bold text-[#F2EEE4]">840</div>
              <span className="text-[11px] font-mono text-[#AEB8BA]">Experiment 840</span>
            </div>
            <div className="p-5 rounded-xl bg-[#12191C] border border-[#2B373C] space-y-1">
              <span className="text-xs font-mono text-[#AEB8BA]">Backend Test Gates</span>
              <div className="text-3xl font-display font-bold text-[#2FA866]">103 / 103</div>
              <span className="text-[11px] font-mono text-[#AEB8BA]">100% pytest green</span>
            </div>
            <div className="p-5 rounded-xl bg-[#12191C] border border-[#2B373C] space-y-1">
              <span className="text-xs font-mono text-[#AEB8BA]">Frontend Contracts</span>
              <div className="text-3xl font-display font-bold text-[#2FA866]">17 / 17</div>
              <span className="text-[11px] font-mono text-[#AEB8BA]">Node test runner</span>
            </div>
            <div className="p-5 rounded-xl bg-[#12191C] border border-[#2B373C] space-y-1">
              <span className="text-xs font-mono text-[#AEB8BA]">Evaluated Policies</span>
              <div className="text-3xl font-display font-bold text-[#F2EEE4]">7</div>
              <span className="text-[11px] font-mono text-[#AEB8BA]">Fixed to Deep RL</span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 7: CLOSE (Full-Bleed Amber #FFB020 with Ink Text)
          ========================================================================= */}
      <section className="w-full px-4 sm:px-8 lg:px-16 py-20 bg-[#FFB020] text-[#0C1316]">
        <div className="max-w-[1500px] w-full mx-auto space-y-12">
          <div className="text-center space-y-4 max-w-3xl mx-auto">
            <h2 className="font-display font-black text-4xl sm:text-6xl lg:text-7xl tracking-tight text-[#0C1316] uppercase leading-none">
              PHASORA.
            </h2>
            <p className="text-sm sm:text-base text-[#0C1316]/90 font-medium">
              Adaptive signal intelligence for Marathahalli Bridge. Alliance University B.Tech AI & Data Science, Design Project 1.
            </p>
            <div className="pt-4 flex justify-center">
              <MagneticButton
                onClick={() => setCurrentView('live-simulation')}
                className="px-8 py-4 rounded-full bg-[#0C1316] text-[#F3EDE0] font-extrabold text-sm tracking-tight shadow-2xl hover:bg-[#1A2327] active:scale-95 transition-all flex items-center gap-2"
              >
                <span>Launch live simulation</span>
                <ArrowRight size={15} />
              </MagneticButton>
            </div>
          </div>

          {/* Attribution & Credits Footer */}
          <div className="pt-12 border-t border-[#0C1316]/20 grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-[#0C1316]/80">
            <div>
              <div className="font-bold text-[#0C1316] mb-1">Academic Context</div>
              <div>Alliance University • Department of CSE</div>
              <div>B.Tech AI & Data Science, Design Project 1</div>
            </div>

            <div>
              <div className="font-bold text-[#0C1316] mb-1">Simulation & Modeling</div>
              <div>Eclipse SUMO 1.20+ Microscopic Simulator</div>
              <div>TraCI (Traffic Control Interface) Python Client</div>
              <div>FastAPI Python Backend & React Vite Frontend</div>
            </div>

            <div>
              <div className="font-bold text-[#0C1316] mb-1">Data & Geometry Credits</div>
              <div>Marathahalli Bridge OSM Corridor Topologies</div>
              <div>BTP Baseline Timings (Weekday 08:00–11:30)</div>
              <div>Simulated E2 Lane-Area Induction Detectors</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default LandingPageView;
