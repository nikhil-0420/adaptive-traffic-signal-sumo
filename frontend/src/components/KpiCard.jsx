import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

export function KpiCard({ title, value, unit = '', sub, delta, icon: Icon, higherIsBetter = false, provenance }) {
  const isNumeric = typeof value === 'number';
  const displayVal = isNumeric ? value.toFixed(1) : (value ?? '—');

  let deltaColor = 'text-slate-400 bg-slate-800/50';
  let DeltaIcon = Minus;

  if (delta && delta.value !== undefined) {
    const isFavorable = higherIsBetter ? delta.value > 0 : delta.value < 0;
    if (delta.value !== 0) {
      deltaColor = isFavorable
        ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-500/20'
        : 'text-red-400 bg-red-950/40 border border-red-500/20';
      DeltaIcon = delta.value > 0 ? ArrowUpRight : ArrowDownRight;
    }
  }

  return (
    <div className="dp1-card flex flex-col justify-between">
      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
        <span className="font-medium tracking-wide uppercase text-[11px] text-slate-400">{title}</span>
        {Icon && <Icon size={16} className="text-slate-500" />}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-3xl font-bold font-mono tracking-tight text-white">{displayVal}</span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5 text-xs">
        {delta ? (
          <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono ${deltaColor}`}>
            <DeltaIcon size={12} />
            <span>{delta.label || `${delta.value > 0 ? '+' : ''}${delta.value}%`}</span>
          </div>
        ) : (
          <span className="text-[11px] text-slate-500">{sub || '—'}</span>
        )}

        {provenance && (
          <span className="text-[10px] text-slate-500 font-mono tracking-tight" title="Data provenance">
            {provenance}
          </span>
        )}
      </div>
    </div>
  );
}
