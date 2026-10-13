import React from 'react';
import { Siren, ShieldAlert, ArrowDown, ArrowUp, ArrowLeft, ArrowRight } from 'lucide-react';

export function IntersectionSchematic({
  phase = 'GREEN',
  axis = 'NS',
  queues = { N: 0, S: 0, E: 0, W: 0 },
  trafficLightState = 'GGGgrrrrGGGgrrrr',
  emergencyApproaching = false,
  emergencyDist = null,
  emergencyApproach = 'N',
}) {
  const isNS = axis === 'NS';
  const isEW = axis === 'EW';

  // Light states
  const nsGreen = isNS && phase === 'GREEN';
  const nsYellow = isNS && phase === 'YELLOW';
  const nsRed = !isNS || phase === 'ALL_RED';

  const ewGreen = isEW && phase === 'GREEN';
  const ewYellow = isEW && phase === 'YELLOW';
  const ewRed = !isEW || phase === 'ALL_RED';

  const maxQueueLimit = 150.0; // 150m detector length
  const getQueuePercent = (q) => Math.min(100, Math.max(0, ((q || 0) / maxQueueLimit) * 100));

  return (
    <div className="dp1-card flex flex-col items-center justify-between p-4 relative overflow-hidden">
      {/* Top Header */}
      <div className="w-full flex items-center justify-between border-b border-white/5 pb-2 mb-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white tracking-wide uppercase text-[11px]">Junction Topology</span>
          <span className="font-mono text-[11px] text-slate-400">4-Way Single Intersection</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400">Active Axis:</span>
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
            phase === 'ALL_RED'
              ? 'bg-red-950/60 text-red-400 border border-red-500/30'
              : 'bg-blue-950/60 text-blue-400 border border-blue-500/30'
          }`}>
            {phase === 'ALL_RED' ? 'ALL-RED CLEARANCE' : axis}
          </span>
        </div>
      </div>

      {/* Emergency Siren Alert Banner */}
      {emergencyApproaching && (
        <div className="w-full mb-3 px-3 py-2 bg-red-950/50 border border-red-500/40 rounded flex items-center justify-between text-xs text-red-200 animate-pulse">
          <div className="flex items-center gap-2 font-medium">
            <Siren size={16} className="text-red-400" />
            <span>Priority Clearance: Emergency Vehicle Approaching on Approach {emergencyApproach}</span>
          </div>
          {emergencyDist !== null && (
            <span className="font-mono font-bold text-red-300">{emergencyDist}m to junction</span>
          )}
        </div>
      )}

      {/* 4-Way Intersection Diagram (SVG + HTML Overlays) */}
      <div className="relative w-full max-w-[380px] h-[340px] flex items-center justify-center my-2">
        {/* Road Surface Cross */}
        <div className="absolute w-[90px] h-full bg-slate-900 border-x border-dashed border-slate-700/60 flex flex-col justify-between items-center py-2">
          <span className="text-[10px] font-mono text-slate-400 tracking-wider">NORTH</span>
          <span className="text-[10px] font-mono text-slate-400 tracking-wider">SOUTH</span>
        </div>
        <div className="absolute h-[90px] w-full bg-slate-900 border-y border-dashed border-slate-700/60 flex justify-between items-center px-2">
          <span className="text-[10px] font-mono text-slate-400 tracking-wider">WEST</span>
          <span className="text-[10px] font-mono text-slate-400 tracking-wider">EAST</span>
        </div>

        {/* Junction Conflict Zone Center */}
        <div className="absolute w-[90px] h-[90px] bg-slate-800/80 border border-white/20 flex flex-col items-center justify-center p-1 text-center">
          <span className="text-[10px] font-mono text-slate-400">Junction Center</span>
          <span className={`text-[11px] font-bold font-mono ${
            phase === 'GREEN' ? 'text-emerald-400' : phase === 'YELLOW' ? 'text-amber-400' : 'text-red-400'
          }`}>
            {phase}
          </span>
        </div>

        {/* --- NORTH ARM DETECTOR & SIGNAL --- */}
        <div className="absolute top-2 flex flex-col items-center gap-1">
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-white/10 px-2 py-0.5 rounded text-[11px] font-mono">
            <span className="text-slate-400">det_N:</span>
            <span className="font-bold text-white">{queues.N?.toFixed(1) || 0}m</span>
            {emergencyApproaching && emergencyApproach === 'N' && (
              <Siren size={12} className="text-red-400 animate-bounce" />
            )}
          </div>
          {/* Queue visual bar */}
          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${getQueuePercent(queues.N)}%` }}
            />
          </div>
          {/* Signal Head */}
          <div className="flex items-center gap-1 bg-black/80 px-1.5 py-0.5 rounded-full border border-white/10">
            <span className={`w-2 h-2 rounded-full ${nsRed ? 'bg-red-500 shadow-[0_0_6px_#ef4444]' : 'bg-red-950'}`} />
            <span className={`w-2 h-2 rounded-full ${nsYellow ? 'bg-amber-400 shadow-[0_0_6px_#f59e0b]' : 'bg-amber-950'}`} />
            <span className={`w-2 h-2 rounded-full ${nsGreen ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-emerald-950'}`} />
          </div>
        </div>

        {/* --- SOUTH ARM DETECTOR & SIGNAL --- */}
        <div className="absolute bottom-2 flex flex-col items-center gap-1">
          {/* Signal Head */}
          <div className="flex items-center gap-1 bg-black/80 px-1.5 py-0.5 rounded-full border border-white/10">
            <span className={`w-2 h-2 rounded-full ${nsGreen ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-emerald-950'}`} />
            <span className={`w-2 h-2 rounded-full ${nsYellow ? 'bg-amber-400 shadow-[0_0_6px_#f59e0b]' : 'bg-amber-950'}`} />
            <span className={`w-2 h-2 rounded-full ${nsRed ? 'bg-red-500 shadow-[0_0_6px_#ef4444]' : 'bg-red-950'}`} />
          </div>
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-white/10 px-2 py-0.5 rounded text-[11px] font-mono">
            <span className="text-slate-400">det_S:</span>
            <span className="font-bold text-white">{queues.S?.toFixed(1) || 0}m</span>
            {emergencyApproaching && emergencyApproach === 'S' && (
              <Siren size={12} className="text-red-400 animate-bounce" />
            )}
          </div>
          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${getQueuePercent(queues.S)}%` }}
            />
          </div>
        </div>

        {/* --- WEST ARM DETECTOR & SIGNAL --- */}
        <div className="absolute left-2 flex items-center gap-2">
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-1 bg-slate-950/80 border border-white/10 px-1.5 py-0.5 rounded text-[11px] font-mono">
              <span className="text-slate-400">det_W:</span>
              <span className="font-bold text-white">{queues.W?.toFixed(1) || 0}m</span>
              {emergencyApproaching && emergencyApproach === 'W' && (
                <Siren size={12} className="text-red-400 animate-bounce" />
              )}
            </div>
            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-500 transition-all duration-300"
                style={{ width: `${getQueuePercent(queues.W)}%` }}
              />
            </div>
          </div>
          {/* Signal Head */}
          <div className="flex flex-col items-center gap-1 bg-black/80 p-0.5 rounded-full border border-white/10">
            <span className={`w-2 h-2 rounded-full ${ewRed ? 'bg-red-500 shadow-[0_0_6px_#ef4444]' : 'bg-red-950'}`} />
            <span className={`w-2 h-2 rounded-full ${ewYellow ? 'bg-amber-400 shadow-[0_0_6px_#f59e0b]' : 'bg-amber-950'}`} />
            <span className={`w-2 h-2 rounded-full ${ewGreen ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-emerald-950'}`} />
          </div>
        </div>

        {/* --- EAST ARM DETECTOR & SIGNAL --- */}
        <div className="absolute right-2 flex items-center gap-2">
          {/* Signal Head */}
          <div className="flex flex-col items-center gap-1 bg-black/80 p-0.5 rounded-full border border-white/10">
            <span className={`w-2 h-2 rounded-full ${ewGreen ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-emerald-950'}`} />
            <span className={`w-2 h-2 rounded-full ${ewYellow ? 'bg-amber-400 shadow-[0_0_6px_#f59e0b]' : 'bg-amber-950'}`} />
            <span className={`w-2 h-2 rounded-full ${ewRed ? 'bg-red-500 shadow-[0_0_6px_#ef4444]' : 'bg-red-950'}`} />
          </div>
          <div className="flex flex-col items-start gap-1">
            <div className="flex items-center gap-1 bg-slate-950/80 border border-white/10 px-1.5 py-0.5 rounded text-[11px] font-mono">
              <span className="text-slate-400">det_E:</span>
              <span className="font-bold text-white">{queues.E?.toFixed(1) || 0}m</span>
              {emergencyApproaching && emergencyApproach === 'E' && (
                <Siren size={12} className="text-red-400 animate-bounce" />
              )}
            </div>
            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-500 transition-all duration-300"
                style={{ width: `${getQueuePercent(queues.E)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Raw Signal State Code */}
      <div className="w-full flex items-center justify-between pt-2 border-t border-white/5 text-[11px] font-mono text-slate-400">
        <span>Signal Pattern State:</span>
        <span className="font-bold tracking-widest text-slate-200">{trafficLightState || 'GGggrrrrGGggrrrr'}</span>
      </div>
    </div>
  );
}
