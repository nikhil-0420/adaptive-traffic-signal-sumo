import React, { useRef, useMemo } from 'react';
import clsx from 'clsx';
import { explainDecision, getAxisName } from '../utils/explainDecision';

/**
 * DecisionTimeline — Concentric Double-Bezel #3 of 3
 * Two lanes (North–South, East–West) coloured by green/yellow/all-red.
 * Decision markers above, queue-length trends beneath, emergency windows shaded.
 * Interactive playhead synced with simulation playback.
 */
export function DecisionTimeline({
  decisions = [],
  currentTime = 0,
  totalDuration = 720,
  onSeek = null,
  onSelectDecision = null,
  selectedDecisionIndex = null,
  emergencyEvents = [],
  className = ''
}) {
  const containerRef = useRef(null);

  const duration = Math.max(60, totalDuration || (decisions.length > 0 ? decisions[decisions.length - 1].t + 30 : 720));

  // Compute signal intervals for NS and EW
  const intervals = useMemo(() => {
    if (!decisions || decisions.length === 0) return { ns: [], ew: [] };

    const ns = [];
    const ew = [];

    // Derive contiguous intervals for both axes across time
    for (let i = 0; i < decisions.length; i++) {
      const d = decisions[i];
      const nextT = i < decisions.length - 1 ? decisions[i + 1].t : duration;
      const length = Math.max(0.2, nextT - d.t);
      const isNS = d.axis === 'NS';
      const isEW = d.axis === 'EW';
      const code = String(d.decision_outcome || d.applied_action || d.action || '').toUpperCase();

      let activeState = 'green';
      if (code.includes('GAP_OUT') || code.includes('SWITCH') || code.includes('YELLOW') || code.includes('CLEARANCE')) {
        activeState = 'yellow';
      } else if (code.includes('ALL_RED')) {
        activeState = 'red';
      }

      if (isNS) {
        ns.push({
          startT: d.t,
          endT: nextT,
          length,
          state: activeState,
          decision: d,
          index: i
        });
        ew.push({
          startT: d.t,
          endT: nextT,
          length,
          state: 'red',
          decision: d,
          index: i
        });
      } else if (isEW) {
        ew.push({
          startT: d.t,
          endT: nextT,
          length,
          state: activeState,
          decision: d,
          index: i
        });
        ns.push({
          startT: d.t,
          endT: nextT,
          length,
          state: 'red',
          decision: d,
          index: i
        });
      } else {
        // Interphase all-red
        ns.push({
          startT: d.t,
          endT: nextT,
          length,
          state: 'red',
          decision: d,
          index: i
        });
        ew.push({
          startT: d.t,
          endT: nextT,
          length,
          state: 'red',
          decision: d,
          index: i
        });
      }
    }

    return { ns, ew };
  }, [decisions, duration]);

  // Click on timeline to seek
  const handleTimelineClick = (e) => {
    if (!onSeek || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, clickX / rect.width));
    const seekTime = pct * duration;
    onSeek(Number(seekTime.toFixed(1)));
  };

  const playheadPct = Math.min(100, Math.max(0, (currentTime / duration) * 100));

  return (
    <div className={clsx('double-bezel-outer', className)}>
      <div className="double-bezel-inner bg-panel p-4 sm:p-5 select-none rounded-2xl border border-hairline shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-hairline">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-ink uppercase tracking-wider font-display text-sm">
              Decision & Phase Timeline
            </span>
            <span className="text-[11px] font-mono text-ink-2 bg-inset px-2 py-0.5 rounded border border-hairline">
              Synchronized Dual-Axis State Display
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#2FA866] inline-block shadow-xs" />
              <span className="text-ink-2 text-[11px]">Green</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#F2C230] inline-block shadow-xs" />
              <span className="text-ink-2 text-[11px]">Yellow (3s)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#D6453D] inline-block shadow-xs" />
              <span className="text-ink-2 text-[11px]">All-Red (2s)</span>
            </div>
            <div className="flex items-center gap-1.5 pl-2 border-l border-hairline">
              <span className="text-ink-2 text-[11px]">Playhead:</span>
              <span className="font-bold text-petrol tabular-nums">{currentTime.toFixed(1)}s / {duration.toFixed(0)}s</span>
            </div>
          </div>
        </div>

        {/* Timeline Interactive Canvas Area */}
        <div
          ref={containerRef}
          onClick={handleTimelineClick}
          className="relative w-full cursor-pointer py-3 bg-ground rounded-xl border border-hairline px-3 overflow-hidden shadow-inner"
          style={{ minHeight: '140px' }}
        >
          {/* Shaded Emergency Preemption Windows */}
          {emergencyEvents.map((ev, idx) => {
            const startPct = (ev.startT / duration) * 100;
            const widthPct = Math.max(1, ((ev.endT - ev.startT) / duration) * 100);
            return (
              <div
                key={idx}
                className="absolute top-0 bottom-0 bg-[#D6453D]/20 border-x border-[#D6453D]/40 pointer-events-none z-0"
                style={{ left: `${startPct}%`, width: `${widthPct}%` }}
                title="Emergency vehicle priority preemption window"
              >
                <div className="text-[9px] font-mono text-white bg-[#D6453D] px-1.5 py-0.5 rounded shadow absolute top-1 left-1 whitespace-nowrap">
                  Emergency Preempt
                </div>
              </div>
            );
          })}

          {/* Lane 1: North–South (ORR) */}
          <div className="relative mb-4 z-10">
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-2 mb-1">
              <span className="font-bold text-ink">North–South (ORR Mainline & Slips)</span>
              <span>Phase 1 Axis</span>
            </div>
            <div className="relative h-6 bg-inset rounded border border-hairline overflow-hidden">
              {intervals.ns.map((item, idx) => {
                const leftPct = (item.startT / duration) * 100;
                const widthPct = (item.length / duration) * 100;

                return (
                  <div
                    key={idx}
                    style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                    className={clsx(
                      'absolute top-0 bottom-0 transition-colors border-r border-black/10',
                      item.state === 'green' && 'bg-[#2FA866]',
                      item.state === 'yellow' && 'bg-[#F2C230]',
                      item.state === 'red' && 'bg-[#D6453D]'
                    )}
                    title={`NS Phase: ${item.state.toUpperCase()} (${item.startT.toFixed(1)}s - ${item.endT.toFixed(1)}s)`}
                  />
                );
              })}
            </div>
          </div>

          {/* Lane 2: East–West (Varthur Rd) */}
          <div className="relative mb-2 z-10">
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-2 mb-1">
              <span className="font-bold text-ink">East–West (Varthur Rd Surface)</span>
              <span>Phase 2 Axis</span>
            </div>
            <div className="relative h-6 bg-inset rounded border border-hairline overflow-hidden">
              {intervals.ew.map((item, idx) => {
                const leftPct = (item.startT / duration) * 100;
                const widthPct = (item.length / duration) * 100;

                return (
                  <div
                    key={idx}
                    style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                    className={clsx(
                      'absolute top-0 bottom-0 transition-colors border-r border-black/10',
                      item.state === 'green' && 'bg-[#2FA866]',
                      item.state === 'yellow' && 'bg-[#F2C230]',
                      item.state === 'red' && 'bg-[#D6453D]'
                    )}
                    title={`EW Phase: ${item.state.toUpperCase()} (${item.startT.toFixed(1)}s - ${item.endT.toFixed(1)}s)`}
                  />
                );
              })}
            </div>
          </div>

          {/* Decision Markers Layer */}
          <div className="relative h-5 w-full pointer-events-auto z-20">
            {decisions.slice(0, 80).map((d, idx) => {
              const leftPct = (d.t / duration) * 100;
              const exp = explainDecision(d);
              const isSelected = selectedDecisionIndex === idx;

              let markerColor = 'bg-ink-secondary';
              if (exp.type === 'extend') markerColor = 'bg-signal-green';
              if (exp.type === 'gap_out') markerColor = 'bg-signal-yellow';
              if (exp.type === 'rejected') markerColor = 'bg-signal-red';
              if (exp.type === 'emergency') markerColor = 'bg-signal-red';

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onSeek) onSeek(d.t);
                    if (onSelectDecision) onSelectDecision(idx, d);
                  }}
                  className={clsx(
                    'absolute top-0 -translate-x-1/2 w-2 h-3.5 rounded-xs transition-transform',
                    markerColor,
                    isSelected ? 'ring-2 ring-petrol scale-125 z-30' : 'hover:scale-125'
                  )}
                  style={{ left: `${leftPct}%` }}
                  title={`[t=${d.t.toFixed(1)}s] ${exp.headline}: ${exp.prose}`}
                />
              );
            })}
          </div>

          {/* Vertical Playhead Scrubber */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-petrol pointer-events-none z-30 transition-all duration-75"
            style={{ left: `${playheadPct}%` }}
          >
            <div className="absolute -top-1 -translate-x-1/2 bg-petrol text-white text-[10px] font-mono px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap">
              {currentTime.toFixed(1)}s
            </div>
          </div>
        </div>

        {/* Timeline Axis Ticks */}
        <div className="flex justify-between text-[10px] font-mono text-ink-secondary mt-1.5 px-2">
          <span>0s</span>
          <span>{(duration * 0.25).toFixed(0)}s</span>
          <span>{(duration * 0.5).toFixed(0)}s</span>
          <span>{(duration * 0.75).toFixed(0)}s</span>
          <span>{duration.toFixed(0)}s</span>
        </div>
      </div>
    </div>
  );
}
export default DecisionTimeline;
