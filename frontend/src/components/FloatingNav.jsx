import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import {
  Sun,
  Moon,
  ArrowRight,
  List,
  X,
  Play,
  Activity,
  Layers,
  GitCommit,
  BarChart2,
  FileText,
  Radio
} from 'lucide-react';
import clsx from 'clsx';

export function FloatingNav() {
  const { currentView, setCurrentView, theme, toggleTheme, connectionStatus } = useApp();
  const shouldReduceMotion = useReducedMotion();

  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hoveredLink, setHoveredLink] = useState(null);

  // Signal Head cycling state (Green -> Yellow -> Red -> Green)
  const [signalState, setSignalState] = useState('GREEN');

  useEffect(() => {
    const cycle = [
      { phase: 'GREEN', duration: 3200 },
      { phase: 'YELLOW', duration: 1200 },
      { phase: 'ALL_RED', duration: 1000 },
    ];
    let idx = 0;
    let timerId = null;

    const tick = () => {
      idx = (idx + 1) % cycle.length;
      setSignalState(cycle[idx].phase);
      timerId = setTimeout(tick, cycle[idx].duration);
    };

    timerId = setTimeout(tick, cycle[0].duration);
    return () => clearTimeout(timerId);
  }, []);

  // Condense on scroll down, expand on scroll up
  const lastScrollY = useRef(0);
  useEffect(() => {
    const handleScroll = () => {
      const y = window.scrollY;
      if (y > 60 && y > lastScrollY.current) {
        setIsScrolled(true);
      } else if (y < lastScrollY.current - 10 || y <= 30) {
        setIsScrolled(false);
      }
      lastScrollY.current = y;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isLanding = currentView === 'overview';

  const dashboardLinks = [
    { id: 'junction', label: 'Junction', desc: '3-tier flyover, underpass & surface conflict node' },
    { id: 'operations', label: 'Operations', desc: 'Interactive step-through of queue decisions & rules' },
    { id: 'live-simulation', label: 'Live simulation', desc: 'Real-time TraCI micro-simulation & green extensions' },
    { id: 'controller-comparison', label: 'Controller comparison', desc: '7-policy empirical evaluation across 4 scenarios' },
    { id: 'evidence', label: 'Evidence', desc: 'Verified run catalog, experiment manifests & code proof' },
  ];

  const landingAnchors = [
    { id: '#the-cycle', label: 'The Cycle', desc: 'Step-by-step controller actuation scene' },
    { id: '#proof', label: 'Proof', desc: 'Evaluated metrics across identical seeds' },
    { id: '#the-live-thing', label: 'Live comparison', desc: 'Interactive delay bars settling across 7 controllers' },
    { id: '#the-junction', label: 'The Junction', desc: '3-tier grade separation exploded model' },
    { id: '#evidence', label: 'Evidence', desc: 'Data layer counts and verification artifacts' },
  ];

  const handleAnchorClick = (anchorId) => {
    if (!isLanding) {
      setCurrentView('overview');
      setTimeout(() => {
        const el = document.querySelector(anchorId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      const el = document.querySelector(anchorId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
    setMobileMenuOpen(false);
  };

  const navSpring = {
    type: 'spring',
    stiffness: 400,
    damping: 32,
  };

  return (
    <>
      <header
        className={clsx(
          'fixed top-3 sm:top-5 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 pointer-events-auto',
          'w-max max-w-[calc(100vw-24px)] sm:max-w-[calc(100vw-48px)]'
        )}
      >
        <motion.nav
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={navSpring}
          className={clsx(
            'flex items-center gap-1 sm:gap-2 px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-full',
            'border border-hairline bg-[var(--color-panel-glass)] backdrop-blur-md shadow-xl',
            isScrolled ? 'py-1 sm:py-1.5 shadow-md' : 'py-1.5 sm:py-2'
          )}
          style={{
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          {/* 1. PRODUCT MARK: Cycling Signal Head + Phasora Wordmark */}
          <button
            type="button"
            onClick={() => setCurrentView('overview')}
            aria-label="Phasora: Adaptive Signal Intelligence Home"
            className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-full hover:bg-inset/60 transition-colors shrink-0 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {/* Animated Signal Head Motif */}
            <div className="w-4 h-9 bg-ground border border-hairline rounded-full flex flex-col items-center justify-between p-0.5 shrink-0 shadow-inner">
              <span
                className={clsx(
                  'w-2 h-2 rounded-full transition-opacity duration-300',
                  signalState === 'ALL_RED' ? 'bg-signal-red opacity-100' : 'bg-signal-red/20 opacity-40'
                )}
              />
              <span
                className={clsx(
                  'w-2 h-2 rounded-full transition-opacity duration-300',
                  signalState === 'YELLOW' ? 'bg-signal-yellow opacity-100' : 'bg-signal-yellow/20 opacity-40'
                )}
              />
              <span
                className={clsx(
                  'w-2 h-2 rounded-full transition-opacity duration-300',
                  signalState === 'GREEN' ? 'bg-signal-green opacity-100' : 'bg-signal-green/20 opacity-40'
                )}
              />
            </div>

            <div className="flex flex-col text-left">
              <span className="font-display font-extrabold text-sm sm:text-base tracking-tight text-ink leading-none">
                Phasora
              </span>
              <span className="text-[9px] uppercase tracking-wider font-semibold text-ink-2 leading-tight hidden md:inline">
                Adaptive signal intelligence
              </span>
            </div>
          </button>

          <div className="w-[1px] h-5 bg-hairline mx-0.5 hidden sm:block" />

          {/* 2. DESKTOP NAVIGATION LINKS */}
          <div className="hidden lg:flex items-center gap-0.5 relative">
            {isLanding
              ? landingAnchors.map((item) => (
                  <div
                    key={item.id}
                    className="relative"
                    onMouseEnter={() => setHoveredLink(item.id)}
                    onMouseLeave={() => setHoveredLink(null)}
                  >
                    <button
                      type="button"
                      onClick={() => handleAnchorClick(item.id)}
                      className="px-3 py-1.5 rounded-full text-xs font-medium text-ink-2 hover:text-ink transition-colors relative"
                    >
                      {item.label}
                    </button>

                    {/* One-line popover description */}
                    <AnimatePresence>
                      {hoveredLink === item.id && !shouldReduceMotion && (
                        <motion.div
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 4 }}
                          transition={{ duration: 0.15 }}
                          className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-2.5 py-1 rounded bg-raised border border-hairline text-[11px] text-ink whitespace-nowrap shadow-lg pointer-events-none z-50"
                        >
                          {item.desc}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))
              : dashboardLinks.map((link) => {
                  const isActive = currentView === link.id;
                  return (
                    <div
                      key={link.id}
                      className="relative"
                      onMouseEnter={() => setHoveredLink(link.id)}
                      onMouseLeave={() => setHoveredLink(null)}
                    >
                      <button
                        type="button"
                        onClick={() => setCurrentView(link.id)}
                        className={clsx(
                          'px-3 py-1.5 rounded-full text-xs font-medium transition-colors relative z-10',
                          isActive ? 'text-ink font-semibold' : 'text-ink-2 hover:text-ink'
                        )}
                      >
                        {link.label}
                        {isActive && (
                          <motion.div
                            layoutId="active-pill"
                            className="absolute inset-0 bg-inset rounded-full -z-10 border border-hairline shadow-sm"
                            transition={navSpring}
                          />
                        )}
                      </button>

                      {/* One-line hover description popover */}
                      <AnimatePresence>
                        {hoveredLink === link.id && !isActive && !shouldReduceMotion && (
                          <motion.div
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 4 }}
                            transition={{ duration: 0.15 }}
                            className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-2.5 py-1 rounded bg-raised border border-hairline text-[11px] text-ink whitespace-nowrap shadow-lg pointer-events-none z-50"
                          >
                            {link.desc}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
          </div>

          <div className="w-[1px] h-5 bg-hairline mx-0.5 hidden sm:block" />

          {/* 3. BACKEND STATUS INDICATOR PILL */}
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-inset/70 text-[10px] sm:text-[11px] font-mono border border-hairline shrink-0"
            title={
              connectionStatus === 'api'
                ? 'Backend live: TraCI & SUMO active'
                : 'Snapshot mode (backend offline): viewing verified simulation results'
            }
          >
            <span
              className={clsx(
                'w-1.5 h-1.5 rounded-full shrink-0',
                connectionStatus === 'api' ? 'bg-signal-green animate-pulse' : 'bg-signal-yellow'
              )}
            />
            <span className="text-ink-2 hidden sm:inline">
              {connectionStatus === 'api' ? 'TraCI Live' : 'Snapshot Mode'}
            </span>
          </div>

          {/* 4. THEME TOGGLE */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            className="p-1.5 sm:p-2 rounded-full text-ink-2 hover:text-ink hover:bg-inset transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          {/* 5. PRIMARY ACTION BUTTON */}
          {isLanding ? (
            <button
              type="button"
              onClick={() => setCurrentView('junction')}
              className={clsx(
                'group flex items-center gap-1.5 px-3 sm:px-4 py-1.5 rounded-full',
                'bg-accent text-ink font-semibold text-xs tracking-tight shadow-sm hover:brightness-105 active:scale-95 transition-all'
              )}
            >
              <span>Open dashboard</span>
              <span className="w-4 h-4 rounded-full bg-ink/10 flex items-center justify-center group-hover:translate-x-0.5 transition-transform">
                <ArrowRight size={11} className="text-ink" />
              </span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setCurrentView('live-simulation')}
              className={clsx(
                'group flex items-center gap-1.5 px-3 sm:px-4 py-1.5 rounded-full',
                'bg-accent text-ink font-semibold text-xs tracking-tight shadow-sm hover:brightness-105 active:scale-95 transition-all'
              )}
            >
              <span>Launch live run</span>
              <span className="w-4 h-4 rounded-full bg-ink/10 flex items-center justify-center group-hover:translate-x-0.5 transition-transform">
                <Play size={10} className="fill-ink text-ink" />
              </span>
            </button>
          )}

          {/* 6. MOBILE HAMBURGER BUTTON */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((o) => !o)}
            aria-label="Toggle navigation menu"
            className="lg:hidden p-1.5 rounded-full text-ink hover:bg-inset transition-colors"
          >
            {mobileMenuOpen ? <X size={18} /> : <List size={18} />}
          </button>
        </motion.nav>
      </header>

      {/* MOBILE FULL-SCREEN OVERLAY MENU */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-ground/95 backdrop-blur-xl flex flex-col justify-between p-6 pt-24 lg:hidden"
          >
            <div className="space-y-6">
              <div className="text-xs font-mono uppercase tracking-wider text-ink-2">
                Navigation
              </div>

              <div className="flex flex-col gap-2">
                {isLanding ? (
                  landingAnchors.map((item, idx) => (
                    <motion.button
                      key={item.id}
                      initial={{ opacity: 0, x: -16 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05, duration: 0.25 }}
                      onClick={() => handleAnchorClick(item.id)}
                      className="text-left py-3 border-b border-hairline group flex items-center justify-between"
                    >
                      <div>
                        <div className="text-lg font-bold text-ink">{item.label}</div>
                        <div className="text-xs text-ink-2 mt-0.5">{item.desc}</div>
                      </div>
                      <ArrowRight size={16} className="text-ink-2 group-hover:text-accent transition-colors" />
                    </motion.button>
                  ))
                ) : (
                  dashboardLinks.map((link, idx) => {
                    const isActive = currentView === link.id;
                    return (
                      <motion.button
                        key={link.id}
                        initial={{ opacity: 0, x: -16 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.05, duration: 0.25 }}
                        onClick={() => {
                          setCurrentView(link.id);
                          setMobileMenuOpen(false);
                        }}
                        className={clsx(
                          'text-left py-3 border-b border-hairline group flex items-center justify-between',
                          isActive ? 'text-accent' : 'text-ink'
                        )}
                      >
                        <div>
                          <div className="text-lg font-bold">{link.label}</div>
                          <div className="text-xs text-ink-2 mt-0.5">{link.desc}</div>
                        </div>
                        <ArrowRight size={16} className="text-ink-2 group-hover:text-accent transition-colors" />
                      </motion.button>
                    );
                  })
                )}
              </div>
            </div>

            <div className="pt-6 border-t border-hairline space-y-4">
              <button
                type="button"
                onClick={() => {
                  setCurrentView(isLanding ? 'junction' : 'live-simulation');
                  setMobileMenuOpen(false);
                }}
                className="w-full py-3 rounded-full bg-accent text-ink font-bold text-sm flex items-center justify-center gap-2 shadow-md"
              >
                <span>{isLanding ? 'Open Dashboard' : 'Launch Live Run'}</span>
                <ArrowRight size={14} />
              </button>

              <div className="flex items-center justify-between text-xs font-mono text-ink-2">
                <span>Alliance University</span>
                <span>{connectionStatus === 'api' ? 'TraCI Live' : 'Snapshot Mode'}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default FloatingNav;
