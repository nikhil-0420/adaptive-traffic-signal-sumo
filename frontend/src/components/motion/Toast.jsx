import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { SignalHead } from './SignalHead';

export function DecisionToast({
  toast,
  onDismiss,
  className = ''
}) {
  if (!toast) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 15, scale: 0.95 }}
        transition={{ type: 'spring', stiffness: 450, damping: 30 }}
        className={clsx(
          'fixed bottom-6 right-6 z-50 max-w-sm w-full p-4 rounded-xl',
          'bg-panel border border-hairline shadow-2xl flex items-start gap-3',
          className
        )}
      >
        <SignalHead phase={toast.phase || 'GREEN'} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink uppercase tracking-wide">
              {toast.title || 'Decision Actuated'}
            </span>
            <span className="text-[10px] font-mono text-ink-2">
              t = {Number(toast.time || 0).toFixed(1)}s
            </span>
          </div>
          <p className="text-xs text-ink-2 mt-1 leading-snug line-clamp-2">
            {toast.prose || toast.message}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default DecisionToast;
