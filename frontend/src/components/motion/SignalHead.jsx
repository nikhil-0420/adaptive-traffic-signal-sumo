import React from 'react';
import clsx from 'clsx';

/**
 * SignalHead Component
 * Physical 3-aspect traffic signal head with realistic hood bezels and semantic active illumination.
 */
export function SignalHead({
  phase = 'GREEN', // 'GREEN' | 'YELLOW' | 'ALL_RED' | 'OFF'
  size = 'md',     // 'sm' | 'md' | 'lg'
  orientation = 'vertical',
  className = ''
}) {
  const isRed = phase === 'ALL_RED' || phase === 'RED';
  const isYellow = phase === 'YELLOW';
  const isGreen = phase === 'GREEN';

  const sizeClasses = {
    sm: { box: 'w-4 h-10 p-0.5', lamp: 'w-2.5 h-2.5' },
    md: { box: 'w-6 h-14 p-1', lamp: 'w-3.5 h-3.5' },
    lg: { box: 'w-8 h-20 p-1.5', lamp: 'w-5 h-5' },
  }[size] || { box: 'w-6 h-14 p-1', lamp: 'w-3.5 h-3.5' };

  return (
    <div
      className={clsx(
        'bg-[#121415] border border-hairline/80 rounded-full flex justify-between items-center shadow-md shrink-0',
        orientation === 'vertical' ? `flex-col ${sizeClasses.box}` : `flex-row ${sizeClasses.box}`,
        className
      )}
    >
      {/* Red aspect */}
      <div
        className={clsx(
          'rounded-full transition-all duration-300',
          sizeClasses.lamp,
          isRed
            ? 'bg-signal-red ring-2 ring-signal-red/30 shadow-[0_0_8px_rgba(192,68,60,0.4)]'
            : 'bg-signal-red/15 opacity-40'
        )}
      />
      {/* Yellow aspect */}
      <div
        className={clsx(
          'rounded-full transition-all duration-300',
          sizeClasses.lamp,
          isYellow
            ? 'bg-signal-yellow ring-2 ring-signal-yellow/30 shadow-[0_0_8px_rgba(217,165,33,0.4)]'
            : 'bg-signal-yellow/15 opacity-40'
        )}
      />
      {/* Green aspect */}
      <div
        className={clsx(
          'rounded-full transition-all duration-300',
          sizeClasses.lamp,
          isGreen
            ? 'bg-signal-green ring-2 ring-signal-green/30 shadow-[0_0_8px_rgba(63,155,102,0.4)]'
            : 'bg-signal-green/15 opacity-40'
        )}
      />
    </div>
  );
}

export default SignalHead;
