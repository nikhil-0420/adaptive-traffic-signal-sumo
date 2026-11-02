import React from 'react';
import clsx from 'clsx';
import { explainDecision } from '../utils/explainDecision';

export function DecisionExplainer({ decision, className = '', compact = false }) {
  const d = explainDecision(decision);

  const typeStyles = {
    extend: 'signal-badge-green',
    gap_out: 'signal-badge-yellow',
    switch: 'signal-badge-yellow',
    rejected: 'signal-badge-red',
    emergency: 'signal-badge-red',
    enter: 'signal-badge-green',
    hold: 'signal-badge-neutral',
    neutral: 'signal-badge-neutral',
  };

  const badgeClass = typeStyles[d.type] || 'signal-badge-neutral';

  if (compact) {
    return (
      <div className={clsx('flex items-center justify-between gap-3 p-2.5 rounded bg-panel border border-hairline', className)}>
        <div className="flex items-center gap-2">
          <span className={clsx('px-2 py-0.5 rounded text-[11px] font-mono font-medium', badgeClass)}>
            {d.codeLabel}
          </span>
          <span className="text-xs text-ink truncate max-w-[340px]" title={d.prose}>
            {d.prose}
          </span>
        </div>
        <span className="text-[10px] font-mono text-ink-secondary shrink-0" title={`Reason code: ${d.rawCode}`}>
          {d.rawCode}
        </span>
      </div>
    );
  }

  return (
    <div className={clsx('dp1-panel p-4 bg-panel', className)}>
      <div className="flex items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-hairline">
        <div className="flex items-center gap-2">
          <span className={clsx('px-2.5 py-0.5 rounded text-xs font-mono font-medium', badgeClass)}>
            {d.codeLabel}
          </span>
          {decision?.axis && (
            <span className="text-xs font-mono text-ink-secondary">
              Axis: <strong className="text-ink">{decision.axis === 'NS' ? 'North–South (ORR)' : 'East–West (Varthur)'}</strong>
            </span>
          )}
        </div>
        <span
          className="text-[11px] font-mono text-ink-secondary bg-inset px-2 py-0.5 rounded border border-hairline cursor-help"
          title={`Raw internal controller code: ${d.rawCode}`}
        >
          {d.rawCode}
        </span>
      </div>

      <p className="text-sm text-ink leading-relaxed font-sans mb-3">
        {d.prose}
      </p>

      {/* Structured telemetry pills */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-hairline text-xs font-mono">
        <div className="bg-inset p-2 rounded border border-hairline">
          <div className="text-[10px] text-ink-secondary">Target Green</div>
          <div className="text-sm font-semibold text-ink mt-0.5">{d.targetS ? `${d.targetS.toFixed(1)} s` : '—'}</div>
        </div>
        <div className="bg-inset p-2 rounded border border-hairline">
          <div className="text-[10px] text-ink-secondary">Added Seconds</div>
          <div className="text-sm font-semibold text-ink mt-0.5">
            {d.deltaS > 0 ? `+${d.deltaS.toFixed(1)} s` : '0.0 s'}
          </div>
        </div>
        <div className="bg-inset p-2 rounded border border-hairline">
          <div className="text-[10px] text-ink-secondary">Active Queue</div>
          <div className="text-sm font-semibold text-ink mt-0.5">
            {decision?.q_active_m != null ? `${Number(decision.q_active_m).toFixed(1)} m` : '—'}
          </div>
        </div>
        <div className="bg-inset p-2 rounded border border-hairline">
          <div className="text-[10px] text-ink-secondary">Opposing Queue</div>
          <div className="text-sm font-semibold text-ink mt-0.5">
            {decision?.q_competing_m != null ? `${Number(decision.q_competing_m).toFixed(1)} m` : '—'}
          </div>
        </div>
      </div>
    </div>
  );
}
export default DecisionExplainer;
