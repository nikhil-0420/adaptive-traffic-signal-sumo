import React from 'react';
import { HelpCircle, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

/**
 * QueuePanel - Side-by-side comparison of E2 Detector Queue vs Extended Ground-Truth Queue
 *
 * Implements Task 4:
 * - Per approach (N, S, E, W): detector queue and extended ground-truth queue (gt_ext_q_*)
 * - "Detector full" warning badge when det_full_* is true or detector queue >= 23.8m
 * - Explicit OFFLINE sensor status (NEVER displayed as zero)
 * - Single-sentence tooltip explaining the measurement difference
 */
export function QueuePanel({
  queues_m = {},
  gtExtQueues = {},
  detFull = {},
  sensorStatus = {},
  className = '',
  compact = false,
}) {
  const approaches = [
    { key: 'N', name: 'ORR North (KR Puram)', short: 'ORR North' },
    { key: 'S', name: 'ORR South (Bellandur)', short: 'ORR South' },
    { key: 'E', name: 'Varthur Rd (Whitefield)', short: 'Varthur E' },
    { key: 'W', name: 'HAL Old Airport Rd', short: 'HAL West' },
  ];

  return (
    <div
      className={clsx(
        'rounded-xl border border-hairline bg-panel p-3 text-xs font-mono shadow-xs backdrop-blur-md',
        className
      )}
    >
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-hairline">
        <div className="flex items-center gap-1.5 font-sans font-bold text-ink">
          <span>Approach Queue Telemetry</span>
          <span className="text-[10px] font-mono font-normal text-ink-2 bg-inset px-1.5 py-0.5 rounded">
            E2 vs Extended Ground-Truth
          </span>
        </div>

        {/* 1-sentence Tooltip */}
        <div className="group relative">
          <button
            type="button"
            className="text-ink-2 hover:text-ink transition-colors p-0.5"
            aria-label="Queue measurement explanation"
          >
            <HelpCircle size={13} />
          </button>
          <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block w-72 p-2.5 bg-raised border border-hairline rounded-lg shadow-xl text-[11px] font-sans font-normal text-ink leading-relaxed z-40 pointer-events-none">
            E2 induction detector measures physical stopline queue clipped at ~24.9 m sensor boundary; Extended Ground-Truth queue captures full upstream accumulation beyond detector range.
          </div>
        </div>
      </div>

      <div className={clsx('grid gap-2', compact ? 'grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4')}>
        {approaches.map(({ key, name, short }) => {
          const isOffline = sensorStatus[key] === 'offline' || sensorStatus[key] === 'OFFLINE';
          const detQ = queues_m[key];
          const extQ = gtExtQueues[key] ?? gtExtQueues[`gt_ext_q_${key}`];
          const isSaturated = Boolean(
            detFull[key] ||
            detFull[`det_full_${key}`] ||
            (typeof detQ === 'number' && detQ >= 23.8)
          );

          return (
            <div
              key={key}
              className={clsx(
                'p-2 rounded-lg border transition-colors',
                isSaturated
                  ? 'bg-rose-950/20 border-rose-500/40 text-ink'
                  : 'bg-inset/70 border-hairline text-ink'
              )}
            >
              <div className="flex items-center justify-between text-[11px] font-bold text-ink mb-1">
                <span title={name}>{compact ? short : name}</span>
                {isSaturated && (
                  <span className="flex items-center gap-0.5 px-1 py-0.2 rounded bg-rose-500/20 text-rose-400 text-[9px] font-bold tracking-tight">
                    <AlertTriangle size={10} />
                    FULL
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between text-[11px] pt-0.5">
                <div className="flex flex-col">
                  <span className="text-[9px] text-ink-2 uppercase tracking-wider">Detector</span>
                  <span className="font-bold tabular-nums">
                    {isOffline ? (
                      <span className="text-amber-400 font-semibold">OFFLINE</span>
                    ) : typeof detQ === 'number' ? (
                      `${detQ.toFixed(1)} m`
                    ) : (
                      '-- m'
                    )}
                  </span>
                </div>

                <div className="flex flex-col text-right">
                  <span className="text-[9px] text-ink-2 uppercase tracking-wider">GT Extended</span>
                  <span className="font-bold tabular-nums text-emerald-400">
                    {typeof extQ === 'number' ? `${extQ.toFixed(1)} m` : (typeof detQ === 'number' ? `${detQ.toFixed(1)} m` : '-- m')}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
export default QueuePanel;
