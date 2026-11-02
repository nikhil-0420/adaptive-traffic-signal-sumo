import React from 'react';
import clsx from 'clsx';

/**
 * ResultsStrip — Concentric Double-Bezel KPI Headline Strip (#1 of 3 Double-Bezels)
 * Type in a divided horizontal strip: label over value, no icons, no sparklines.
 * Numbers right-aligned with units in secondary ink.
 * Mandatory basis badge on every stat.
 * Delta convention: negative change in delay = improvement (green tint), positive = worse (red tint).
 */
export function ResultsStrip({
  items = [],
  basis = '',
  className = '',
  title = null
}) {
  return (
    <div className={clsx('double-bezel-outer', className)}>
      <div className="double-bezel-inner bg-panel p-4 sm:p-5">
        {(title || basis) && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 pb-3.5 mb-3.5 border-b border-hairline">
            {title && (
              <span className="text-xs font-semibold text-ink tracking-tight">
                {title}
              </span>
            )}
            {basis && (
              <span className="text-[11px] font-mono text-ink-secondary bg-inset px-2.5 py-0.5 rounded border border-hairline inline-block">
                Basis: {basis}
              </span>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-hairline">
          {items.map((item, idx) => {
            const isDelta = item.isDelta || item.deltaPercent !== undefined;
            const deltaVal = item.deltaPercent ?? (item.value != null && typeof item.value === 'number' ? item.value : null);
            const isNegativeBetter = item.lowerIsBetter ?? true;
            const isGood = isNegativeBetter ? deltaVal < 0 : deltaVal > 0;
            const isBad = isNegativeBetter ? deltaVal > 0 : deltaVal < 0;

            return (
              <div
                key={item.label || idx}
                className={clsx(
                  'flex flex-col justify-between py-2 sm:py-0 px-3 first:pl-0 last:pr-0',
                  idx > 0 && 'md:pl-4',
                  idx < items.length - 1 && 'md:pr-4'
                )}
              >
                <div className="text-[12px] font-medium text-ink-secondary mb-1.5 tracking-normal">
                  {item.label}
                </div>

                <div className="flex items-baseline justify-end gap-1.5 mt-auto">
                  {isDelta ? (
                    <span
                      className={clsx(
                        'text-xl font-bold font-mono tracking-tight px-1.5 py-0.5 rounded',
                        isGood && 'bg-signal-green-tint text-signal-green-text border border-signal-green/20',
                        isBad && 'bg-signal-red-tint text-signal-red-text border border-signal-red/20',
                        !isGood && !isBad && 'bg-inset text-ink border border-hairline'
                      )}
                    >
                      {deltaVal > 0 ? `+${deltaVal.toFixed(1)}%` : `${deltaVal != null ? deltaVal.toFixed(1) : '—'}%`}
                    </span>
                  ) : (
                    <span className="text-xl font-bold font-mono text-ink tracking-tight">
                      {item.value != null ? item.value : '—'}
                    </span>
                  )}

                  {item.unit && (
                    <span className="text-xs font-mono text-ink-secondary">
                      {item.unit}
                    </span>
                  )}
                </div>

                {item.subtext && (
                  <div className="text-[11px] font-mono text-ink-secondary text-right mt-1">
                    {item.subtext}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export default ResultsStrip;
