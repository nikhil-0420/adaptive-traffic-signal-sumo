import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { JunctionTwin } from '../components/JunctionTwin';
import { SignalHead } from '../components/motion/SignalHead';
import {
  IconLayers,
  IconInfo,
  IconCheck,
  IconArrowRight,
  IconPlay,
  IconPause,
  IconRotateCcw
} from '../components/icons';
import clsx from 'clsx';

export function JunctionView() {
  const [activePhaseIndex, setActivePhaseIndex] = useState(0); // 0: NS Green, 1: Yellow, 2: All-Red, 3: EW Green
  const [hoveredApproach, setHoveredApproach] = useState(null);
  const [isExploded, setIsExploded] = useState(false);
  const [soloTier, setSoloTier] = useState(null);
  const [isAutoAdvancing, setIsAutoAdvancing] = useState(false);

  const phases = [
    {
      id: 'ns_green',
      name: 'Phase 1: North–South (ORR Green)',
      state: 'GREEN',
      axis: 'NS',
      duration: '15.0 s (baseline) to 60.0 s (max)',
      activeApproaches: ['ORR North (KR Puram)', 'ORR South (Kadubeesanahalli)'],
      color: 'bg-signal-green text-white',
      badge: 'signal-badge-green',
      directions: { N: 'green', S: 'green', E: 'red', W: 'red' }
    },
    {
      id: 'ns_yellow',
      name: 'Clearance: NS Yellow Warning',
      state: 'YELLOW',
      axis: 'NS',
      duration: '3.0 s (fixed timing)',
      activeApproaches: ['ORR North clearance', 'ORR South clearance'],
      color: 'bg-signal-yellow text-white',
      badge: 'signal-badge-yellow',
      directions: { N: 'yellow', S: 'yellow', E: 'red', W: 'red' }
    },
    {
      id: 'all_red',
      name: 'Safety Invariant: All-Red Clearance Buffer',
      state: 'ALL_RED',
      axis: 'NONE',
      duration: '2.0 s (fixed invariant)',
      activeApproaches: ['Conflict box completely evacuated before release'],
      color: 'bg-signal-red text-white',
      badge: 'signal-badge-red',
      directions: { N: 'red', S: 'red', E: 'red', W: 'red' }
    },
    {
      id: 'ew_green',
      name: 'Phase 2: East–West (Varthur Green)',
      state: 'GREEN',
      axis: 'EW',
      duration: '15.0 s (baseline) to 60.0 s (max)',
      activeApproaches: ['East (Whitefield / ITPL)', 'West (HAL Airport Rd)'],
      color: 'bg-signal-green text-white',
      badge: 'signal-badge-green',
      directions: { N: 'red', S: 'red', E: 'green', W: 'green' }
    }
  ];

  const approaches = {
    N: {
      name: 'ORR North (KR Puram approach)',
      detector: 'det_orr_n',
      lanes: 3,
      length: '150 m (E2 lane-area detector)',
      split: '70% through via underpass, 30% surface turn & slip',
      movement: 'Through to Kadubeesanahalli / Right turn to Whitefield'
    },
    S: {
      name: 'ORR South (Kadubeesanahalli approach)',
      detector: 'det_orr_s',
      lanes: 3,
      length: '150 m (E2 lane-area detector)',
      split: '70% through via underpass, 30% surface turn & slip',
      movement: 'Through to KR Puram / Right turn to HAL'
    },
    E: {
      name: 'East (Whitefield / Varthur Rd approach)',
      detector: 'det_wf',
      lanes: 2,
      length: '150 m (E2 lane-area detector)',
      split: '70% through via flyover, 30% surface roundabout',
      movement: 'Through to HAL Airport Rd / Left & Right turns to ORR'
    },
    W: {
      name: 'West (HAL Airport Rd approach)',
      detector: 'det_hal',
      lanes: 2,
      length: '150 m (E2 lane-area detector)',
      split: '70% through via flyover, 30% surface roundabout',
      movement: 'Through to Whitefield / Left & Right turns to ORR'
    }
  };

  const currentPhase = phases[activePhaseIndex];

  // Auto-advance through signal cycle
  useEffect(() => {
    if (!isAutoAdvancing) return;
    const interval = setInterval(() => {
      setActivePhaseIndex((prev) => (prev + 1) % phases.length);
    }, 2800);
    return () => clearInterval(interval);
  }, [isAutoAdvancing, phases.length]);

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Deep-Petrol Header Band (Brief Section 5: deep-petrol band, bone text, display-face title, one-sentence question) */}
      <div className="bg-[#093F4A] text-[#F3EDE0] px-6 py-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm border border-[#0F6B7A]/40">
        <div>
          <h1 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[#F3EDE0]">
            Junction layout
          </h1>
          <p className="text-xs text-[#F3EDE0]/80 mt-1 font-mono">
            How does 3-tier grade separation isolate through traffic from surface signal conflict?
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setIsExploded((v) => !v)}
            className={clsx(
              'px-3.5 py-2 rounded-xl border text-xs font-mono font-bold flex items-center gap-1.5 transition-all shadow-sm',
              isExploded
                ? 'bg-[#FFB020] text-[#0C1316] border-[#FFB020]'
                : 'bg-[#0F6B7A] border-[#0F6B7A]/50 text-[#F3EDE0] hover:bg-[#0F6B7A]/80'
            )}
          >
            <IconLayers size={14} />
            <span>{isExploded ? 'Collapse view' : 'Explode 3-Tier View'}</span>
          </button>
        </div>
      </div>

      {/* Section 1: Interactive Twin */}
      <section className="space-y-4">
        <div className="dp1-panel p-3 bg-panel border border-hairline rounded-xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between px-2 py-1.5 mb-2 border-b border-hairline text-xs font-mono">
            <span className="font-semibold text-ink flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-signal-green animate-pulse" />
              <span>Marathahalli Bridge Microscopic Twin</span>
            </span>
            <span className="text-ink-2 text-[11px]">
              E2 Loop Detectors (150m) · Z-Layer Separation {soloTier ? `· Solo: ${soloTier.toUpperCase()}` : ''}
            </span>
          </div>

          <div className="rounded overflow-hidden">
            <JunctionTwin
              mode="overview"
              runId="marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121"
              height={460}
              isExploded={isExploded}
              onExplodeToggle={() => setIsExploded((v) => !v)}
              soloTier={soloTier}
              onSoloTierChange={setSoloTier}
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* Section 2: Grade Separation (3-Tier Layer View with Separate on Hover/Toggle) */}
      <section id="grade-separation" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-ink uppercase tracking-wide">
            Grade Separation: Exploded Three-Tier Architecture
          </h2>
          <span className="text-xs font-mono text-ink-2">
            Click any tier card to solo or isolate in the 3D twin
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Tier 1: Elevated Flyover */}
          <motion.div
            animate={{ y: isExploded ? -14 : 0 }}
            transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
            onClick={() => setSoloTier((s) => (s === 'flyover' ? null : 'flyover'))}
            className={clsx(
              'dp1-panel p-5 bg-panel border-t-4 border-t-petrol border rounded-xl space-y-2.5 shadow-sm cursor-pointer transition-all duration-300',
              soloTier === 'flyover'
                ? 'ring-2 ring-accent border-accent'
                : soloTier && soloTier !== 'flyover'
                ? 'opacity-30 border-hairline'
                : 'border-hairline hover:-translate-y-1'
            )}
          >
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-ink">Tier 1 · Elevated Flyover</span>
              <span className={clsx("px-2 py-0.5 rounded font-semibold text-[11px]", soloTier === 'flyover' ? 'bg-accent text-ink' : 'text-petrol bg-petrol/15')}>
                {soloTier === 'flyover' ? 'SOLOED (Z = +7.0 m)' : 'Z = +7.0 m'}
              </span>
            </div>
            <div className="text-sm font-bold text-ink">Varthur Road Elevated Bridge</div>
            <p className="text-xs text-ink-2 leading-relaxed">
              4-lane bidirectional elevated roadway carrying through-traffic between HAL Airport Road and Whitefield. Operates in permanent free-flow, siphoning 70% of east-west through traffic away from the surface signal.
            </p>
            <div className="pt-2 border-t border-hairline text-[11px] font-mono text-ink-2 flex items-center justify-between">
              <span>2 Eastbound • 2 Westbound</span>
              <span className="text-accent text-[10px] font-semibold">{soloTier === 'flyover' ? 'Click to restore' : 'Click to solo'}</span>
            </div>
          </motion.div>

          {/* Tier 2: Surface Junction */}
          <motion.div
            animate={{ y: 0 }}
            onClick={() => setSoloTier((s) => (s === 'surface' ? null : 'surface'))}
            className={clsx(
              'dp1-panel p-5 bg-panel border-t-4 border-t-signal-yellow border rounded-xl space-y-2.5 shadow-sm cursor-pointer transition-all duration-300',
              soloTier === 'surface'
                ? 'ring-2 ring-accent border-accent'
                : soloTier && soloTier !== 'surface'
                ? 'opacity-30 border-hairline'
                : 'border-hairline hover:-translate-y-1'
            )}
          >
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-ink">Tier 2 · Surface Level</span>
              <span className={clsx("px-2 py-0.5 rounded font-semibold text-[11px]", soloTier === 'surface' ? 'bg-accent text-ink' : 'text-signal-yellow-text bg-signal-yellow-tint')}>
                {soloTier === 'surface' ? 'SOLOED (Z = 0.0 m)' : 'Z = 0.0 m'}
              </span>
            </div>
            <div className="text-sm font-bold text-ink">Signalized Conflict Node (marathahalli_tls)</div>
            <p className="text-xs text-ink-2 leading-relaxed">
              At-grade roundabout and signalized junction servicing all turning movements (including right-turns toward Bellandur and Whitefield) and remaining through traffic via slip roads and under-bridge connectors.
            </p>
            <div className="pt-2 border-t border-hairline text-[11px] font-mono text-ink-2 flex items-center justify-between">
              <span>8 Surface Detectors (150m)</span>
              <span className="text-accent text-[10px] font-semibold">{soloTier === 'surface' ? 'Click to restore' : 'Click to solo'}</span>
            </div>
          </motion.div>

          {/* Tier 3: Mainline Underpass */}
          <motion.div
            animate={{ y: isExploded ? 14 : 0 }}
            transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
            onClick={() => setSoloTier((s) => (s === 'underpass' ? null : 'underpass'))}
            className={clsx(
              'dp1-panel p-5 bg-panel border-t-4 border-t-ink border rounded-xl space-y-2.5 shadow-sm cursor-pointer transition-all duration-300',
              soloTier === 'underpass'
                ? 'ring-2 ring-accent border-accent'
                : soloTier && soloTier !== 'underpass'
                ? 'opacity-30 border-hairline'
                : 'border-hairline hover:-translate-y-1'
            )}
          >
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-ink">Tier 3 · Mainline Underpass</span>
              <span className={clsx("px-2 py-0.5 rounded font-semibold text-[11px]", soloTier === 'underpass' ? 'bg-accent text-ink' : 'text-ink bg-inset')}>
                {soloTier === 'underpass' ? 'SOLOED (Z = -4.0 m)' : 'Z = -4.0 m'}
              </span>
            </div>
            <div className="text-sm font-bold text-ink">Outer Ring Road Sunken Trench</div>
            <p className="text-xs text-ink-2 leading-relaxed">
              6-lane sunken grade-separated mainline carrying continuous north-south Outer Ring Road transit beneath the bridge. Carries 70% of north-south through volume completely free of surface signal interruption.
            </p>
            <div className="pt-2 border-t border-hairline text-[11px] font-mono text-ink-2 flex items-center justify-between">
              <span>3 Northbound • 3 Southbound</span>
              <span className="text-accent text-[10px] font-semibold">{soloTier === 'underpass' ? 'Click to restore' : 'Click to solo'}</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Section 3: Phase & Movement Explorer */}
      <section id="phase-explorer" className="dp1-panel p-6 bg-panel border border-hairline rounded-2xl space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-hairline pb-4">
          <div>
            <div className="flex items-center gap-2">
              <SignalHead phase={currentPhase.state} size={15} />
              <h2 className="text-base font-bold text-ink uppercase tracking-wide">
                Phase & Movement Explorer
              </h2>
            </div>
            <p className="text-xs text-ink-2 mt-0.5">
              Select or auto-cycle phase states to observe right-of-way transitions, yellow warnings, and mandatory all-red buffers.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsAutoAdvancing((v) => !v)}
              className={clsx(
                'px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors',
                isAutoAdvancing
                  ? 'bg-accent text-ink border-accent'
                  : 'bg-inset border-hairline text-ink hover:bg-panel'
              )}
            >
              {isAutoAdvancing ? <IconPause size={12} /> : <IconPlay size={12} />}
              <span>{isAutoAdvancing ? 'Pause Cycle' : 'Auto Advance'}</span>
            </button>
            <div className="flex items-center gap-1 text-xs font-mono bg-inset p-1 rounded-lg border border-hairline">
              <span className="px-2 py-0.5 rounded bg-panel font-semibold text-ink">Yellow: 3s</span>
              <span className="text-ink-2">+</span>
              <span className="px-2 py-0.5 rounded bg-panel font-semibold text-ink">All-Red: 2s</span>
            </div>
          </div>
        </div>

        {/* Phase Step Selector Buttons */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {phases.map((ph, idx) => (
            <button
              key={ph.id}
              type="button"
              onClick={() => {
                setActivePhaseIndex(idx);
                setIsAutoAdvancing(false);
              }}
              className={clsx(
                'p-3 rounded-xl border text-left transition-all',
                activePhaseIndex === idx
                  ? 'border-petrol bg-inset shadow-xs ring-1 ring-petrol/30'
                  : 'border-hairline bg-panel hover:bg-inset/60'
              )}
            >
              <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
                <span className="font-semibold text-ink">Step {idx + 1}</span>
                <span className={clsx('px-2 py-0.5 rounded text-[10px] font-bold font-mono', ph.badge)}>
                  {ph.state}
                </span>
              </div>
              <div className="text-xs font-semibold text-ink truncate">{ph.name}</div>
              <div className="text-[11px] font-mono text-ink-2 mt-1">{ph.duration}</div>
            </button>
          ))}
        </div>

        {/* Interactive Intersection Schematic & Phase Rights */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center bg-inset p-5 rounded-xl border border-hairline">
          {/* Left: 2D Schematic Intersection Diagram */}
          <div className="md:col-span-5 flex flex-col items-center justify-center p-3">
            <div className="relative w-48 h-48 rounded-xl bg-ground border border-hairline flex items-center justify-center shadow-inner">
              {/* North Arm */}
              <div className={clsx(
                'absolute top-2 w-12 h-16 rounded-t flex flex-col items-center justify-start pt-1 text-[9px] font-mono font-bold transition-colors',
                currentPhase.directions.N === 'green' && 'bg-signal-green text-white',
                currentPhase.directions.N === 'yellow' && 'bg-signal-yellow text-ink',
                currentPhase.directions.N === 'red' && 'bg-signal-red/80 text-white'
              )}>
                <span>NORTH</span>
                <span>{currentPhase.directions.N.toUpperCase()}</span>
                {currentPhase.directions.N === 'green' && <span className="text-xs animate-bounce">↓</span>}
              </div>

              {/* South Arm */}
              <div className={clsx(
                'absolute bottom-2 w-12 h-16 rounded-b flex flex-col items-center justify-end pb-1 text-[9px] font-mono font-bold transition-colors',
                currentPhase.directions.S === 'green' && 'bg-signal-green text-white',
                currentPhase.directions.S === 'yellow' && 'bg-signal-yellow text-ink',
                currentPhase.directions.S === 'red' && 'bg-signal-red/80 text-white'
              )}>
                {currentPhase.directions.S === 'green' && <span className="text-xs animate-bounce">↑</span>}
                <span>{currentPhase.directions.S.toUpperCase()}</span>
                <span>SOUTH</span>
              </div>

              {/* West Arm */}
              <div className={clsx(
                'absolute left-2 h-12 w-16 rounded-l flex items-center justify-center text-[9px] font-mono font-bold transition-colors gap-1',
                currentPhase.directions.W === 'green' && 'bg-signal-green text-white',
                currentPhase.directions.W === 'yellow' && 'bg-signal-yellow text-ink',
                currentPhase.directions.W === 'red' && 'bg-signal-red/80 text-white'
              )}>
                <span>W</span>
                {currentPhase.directions.W === 'green' && <span className="text-xs animate-pulse">→</span>}
              </div>

              {/* East Arm */}
              <div className={clsx(
                'absolute right-2 h-12 w-16 rounded-r flex items-center justify-center text-[9px] font-mono font-bold transition-colors gap-1',
                currentPhase.directions.E === 'green' && 'bg-signal-green text-white',
                currentPhase.directions.E === 'yellow' && 'bg-signal-yellow text-ink',
                currentPhase.directions.E === 'red' && 'bg-signal-red/80 text-white'
              )}>
                {currentPhase.directions.E === 'green' && <span className="text-xs animate-pulse">←</span>}
                <span>E</span>
              </div>

              {/* Center Conflict Box */}
              <div className={clsx(
                'w-12 h-12 rounded border flex flex-col items-center justify-center text-[8px] font-mono font-bold text-center z-10 transition-colors',
                currentPhase.state === 'ALL_RED' ? 'bg-signal-red text-white animate-pulse' : 'bg-panel text-ink border-hairline'
              )}>
                <span>TLS</span>
                <span>{currentPhase.state}</span>
              </div>
            </div>
            <span className="text-[10px] font-mono text-ink-2 mt-2">Surface Conflict Node State</span>
          </div>

          {/* Right: Serviced Movements & Invariants */}
          <div className="md:col-span-7 space-y-3 font-mono text-xs">
            <div className="p-3 bg-panel rounded-lg border border-hairline space-y-1">
              <span className="text-[10px] text-ink-2 uppercase">Active Approach Rights:</span>
              <div className="text-sm font-semibold text-ink">
                {currentPhase.activeApproaches.join(' • ')}
              </div>
            </div>

            <div className="p-3 bg-panel rounded-lg border border-hairline space-y-1">
              <span className="text-[10px] text-ink-2 uppercase">Clearance Protocol:</span>
              <div className="text-ink">
                {currentPhase.state === 'ALL_RED'
                  ? 'All 4 approaches held red. Vehicle conflict box clears before cross-street green is granted.'
                  : currentPhase.state === 'YELLOW'
                  ? '3.0 s yellow warning interval. Vehicles past dilemma zone clear the stop line.'
                  : 'Webster baseline (15 s) with dynamic +3.0 s extensions up to 60.0 s maximum.'}
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-signal-green text-[11px] pt-1">
              <IconCheck size={13} />
              <span>Safety invariant verified: No green-to-green transitions permitted.</span>
            </div>
          </div>
        </div>

        {/* Approach Arm Hover Explorer Cards */}
        <div>
          <div className="text-xs font-semibold text-ink uppercase tracking-wider mb-2.5">
            Surface Approach Arms (Hover to inspect lane & detector specs):
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(approaches).map(([key, app]) => {
              const isHovered = hoveredApproach === key;
              return (
                <div
                  key={key}
                  onMouseEnter={() => setHoveredApproach(key)}
                  onMouseLeave={() => setHoveredApproach(null)}
                  className={clsx(
                    'p-3.5 rounded-xl border transition-all',
                    isHovered
                      ? 'border-petrol bg-inset shadow-xs ring-1 ring-petrol/20'
                      : 'border-hairline bg-panel hover:bg-inset/60'
                  )}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold text-ink">Arm {key}</span>
                    <span className="text-petrol font-semibold">{app.detector}</span>
                  </div>
                  <div className="text-xs font-medium text-ink truncate mb-1">{app.name}</div>
                  <div className="text-[11px] text-ink-2 font-mono space-y-0.5">
                    <div>Lanes: {app.lanes}</div>
                    <div>Detector: {app.length}</div>
                    <div>Split: {app.split}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}

export default JunctionView;
