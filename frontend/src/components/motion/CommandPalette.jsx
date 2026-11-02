import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../../context/AppContext';
import {
  Search,
  Play,
  RotateCcw,
  Sun,
  Moon,
  Layers,
  Activity,
  BarChart2,
  FileText,
  Sliders,
  ArrowRight,
  Command
} from 'lucide-react';
import clsx from 'clsx';

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { setCurrentView, toggleTheme, theme, allRuns, openRunReview } = useApp();

  // Listen for Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const actions = [
    { id: 'landing', label: 'Go to Landing Page', category: 'Navigation', icon: Layers, action: () => setCurrentView('overview') },
    { id: 'junction', label: 'Go to Junction View (3-Tier Model)', category: 'Navigation', icon: Layers, action: () => setCurrentView('junction') },
    { id: 'operations', label: 'Go to Operations (Decision Step-Through)', category: 'Navigation', icon: Sliders, action: () => setCurrentView('operations') },
    { id: 'live', label: 'Launch Live Simulation', category: 'Simulation', icon: Play, action: () => setCurrentView('live-simulation') },
    { id: 'compare', label: 'View Controller Comparison Matrix', category: 'Analysis', icon: BarChart2, action: () => setCurrentView('controller-comparison') },
    { id: 'evidence', label: 'Open Evidence & Data Catalog', category: 'Data', icon: FileText, action: () => setCurrentView('evidence') },
    {
      id: 'latest-run',
      label: 'Open Latest Verified Run Review',
      category: 'Review',
      icon: RotateCcw,
      action: () => {
        const latest = allRuns[0]?.run_id || 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121';
        openRunReview(latest);
      }
    },
    { id: 'theme', label: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`, category: 'Preferences', icon: theme === 'dark' ? Sun : Moon, action: toggleTheme },
  ];

  const filtered = actions.filter((a) =>
    a.label.toLowerCase().includes(query.toLowerCase()) ||
    a.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleSelect = (item) => {
    if (item && item.action) {
      item.action();
      setIsOpen(false);
      setQuery('');
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((idx) => (idx + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((idx) => (idx - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        handleSelect(filtered[selectedIndex]);
      }
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-ground/70 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl bg-panel border border-hairline rounded-2xl shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search Input Bar */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-hairline">
              <Search size={18} className="text-ink-2 shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Type a command or jump to page... (Esc to close)"
                autoFocus
                className="w-full bg-transparent text-sm text-ink placeholder:text-ink-2/60 focus:outline-none"
              />
              <span className="text-[10px] font-mono text-ink-2 bg-inset px-2 py-0.5 rounded border border-hairline">
                ESC
              </span>
            </div>

            {/* Command List */}
            <div className="max-h-80 overflow-y-auto p-2 divide-y divide-hairline/40">
              {filtered.length === 0 ? (
                <div className="py-8 text-center text-xs text-ink-2">
                  No matching commands found.
                </div>
              ) : (
                filtered.map((item, idx) => {
                  const Icon = item.icon;
                  const isSelected = idx === selectedIndex;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={clsx(
                        'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left text-xs transition-colors',
                        isSelected ? 'bg-inset text-ink font-semibold' : 'text-ink-2 hover:text-ink'
                      )}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon size={15} className={isSelected ? 'text-accent' : 'text-ink-2'} />
                        <span>{item.label}</span>
                      </div>
                      <span className="text-[10px] font-mono text-ink-2/70 uppercase tracking-wider">
                        {item.category}
                      </span>
                    </button>
                  );
                })
              )}
            </div>

            {/* Footer with Hint */}
            <div className="px-4 py-2 border-t border-hairline bg-inset/40 flex items-center justify-between text-[11px] font-mono text-ink-2">
              <span>Alliance University • Phasora</span>
              <span>Use ↑ ↓ to navigate · ↵ to select</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default CommandPalette;
