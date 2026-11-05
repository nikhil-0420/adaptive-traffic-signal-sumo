import React, { useState } from 'react';
import clsx from 'clsx';
import { useApp } from '../context/AppContext';
import {
  IconOverview,
  IconJunction,
  IconOperations,
  IconLiveSim,
  IconCompare,
  IconEvidence,
  IconMenu,
  IconX,
  IconInfo,
  IconSun,
  IconMoon
} from './icons';

export function Sidebar() {
  const { currentView, setCurrentView, connectionStatus, connectionInfo, theme, toggleTheme, isDark } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navGroups = [
    {
      label: 'Understand',
      items: [
        { id: 'overview', label: 'Overview', icon: IconOverview },
        { id: 'junction', label: 'Junction', icon: IconJunction },
      ],
    },
    {
      label: 'Operate',
      items: [
        { id: 'operations', label: 'Operations', icon: IconOperations },
        { id: 'live-simulation', label: 'Live simulation', icon: IconLiveSim },
      ],
    },
    {
      label: 'Evaluate',
      items: [
        { id: 'controller-comparison', label: 'Controller comparison', icon: IconCompare },
        { id: 'evidence', label: 'Evidence', icon: IconEvidence }, // Must be LAST!
      ],
    },
  ];

  const handleNavClick = (id) => {
    setCurrentView(id);
    setMobileOpen(false);
  };

  const navContent = (
    <div className="flex flex-col h-full justify-between p-3.5 bg-ground select-none overflow-y-auto">
      {/* Product Mark + Top Theme Toggle */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-hairline mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-petrol inline-block shrink-0" />
              <span className="font-bold text-sm text-ink tracking-tight">
                Phasora
              </span>
            </div>
            <p className="text-[11px] text-ink-secondary mt-0.5 font-mono">
              Adaptive signal intelligence
            </p>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Quick Header Theme Toggle */}
            <button
              id="theme-toggle-header"
              type="button"
              onClick={toggleTheme}
              className="p-1.5 rounded bg-panel hover:bg-inset border border-hairline text-ink transition-colors cursor-pointer"
              title={`Switch to ${isDark ? 'Light' : 'Dark'} theme`}
              aria-label="Toggle theme"
            >
              {isDark ? (
                <IconMoon size={14} className="text-petrol" />
              ) : (
                <IconSun size={14} className="text-signal-yellow" />
              )}
            </button>

            {/* Close button for mobile drawer */}
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="lg:hidden p-1.5 rounded bg-inset border border-hairline text-ink-secondary"
              aria-label="Close navigation"
            >
              <IconX size={16} />
            </button>
          </div>
        </div>

        {/* Grouped Navigation Links */}
        <nav className="space-y-4">
          {navGroups.map((group) => (
            <div key={group.label}>
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-muted px-2.5 mb-1">
                {group.label}
              </div>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentView === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => handleNavClick(item.id)}
                        className={clsx(
                          'w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs transition-colors',
                          isActive
                            ? 'bg-panel text-ink font-semibold border border-hairline shadow-xs'
                            : 'text-ink-secondary hover:text-ink hover:bg-inset border border-transparent'
                        )}
                      >
                        <Icon size={15} className={clsx(isActive ? 'text-ink' : 'text-ink-secondary')} />
                        <span>{item.label}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </div>

      {/* Sidebar Footer with Live/Snapshot Indicator & Jargon Note */}
      <div className="pt-3 border-t border-hairline mt-4 space-y-2.5">
        {/* System connection indicator */}
        <div className="bg-panel border border-hairline p-2 rounded text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-ink-muted uppercase">Backend Status</span>
            <div className="flex items-center gap-1.5">
              <span
                className={clsx(
                  'w-2 h-2 rounded-full',
                  connectionStatus === 'api' ? 'bg-signal-green' : 'bg-signal-yellow'
                )}
              />
              <span className="text-[11px] font-semibold text-ink">
                {connectionStatus === 'api' ? 'API Live' : 'Snapshot'}
              </span>
            </div>
          </div>
          <div className="text-[10px] text-ink-secondary mt-0.5 truncate">
            {connectionStatus === 'api' ? 'FastAPI TraCI connected' : 'Verified repo artifacts'}
          </div>
        </div>

        {/* Theme Mode Toggle (Light / Dark) */}
        <button
          id="theme-toggle-btn"
          data-testid="theme-toggle"
          type="button"
          onClick={toggleTheme}
          className="w-full flex items-center justify-between p-2 rounded bg-panel border border-hairline text-xs font-mono text-ink hover:bg-inset transition-colors cursor-pointer"
          title={`Switch to ${isDark ? 'Light' : 'Dark'} theme`}
        >
          <div className="flex items-center gap-2">
            {isDark ? (
              <IconMoon size={14} className="text-petrol" />
            ) : (
              <IconSun size={14} className="text-signal-yellow" />
            )}
            <span className="font-medium">{isDark ? 'Dark Mode' : 'Light Mode'}</span>
          </div>
          <span className="text-[10px] text-ink-muted uppercase bg-inset px-2 py-0.5 rounded border border-hairline">
            {isDark ? '🌙 Dark' : '☀️ Light'}
          </span>
        </button>

        {/* Jargon explainer footnote */}
        <div className="text-[10px] text-ink-muted leading-tight px-1 flex items-start gap-1.5">
          <IconInfo size={12} className="shrink-0 mt-0.5" />
          <span>
            <strong>EVSP</strong> = emergency priority • <strong>E2</strong> = lane-area detector.
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Top Bar with Hamburger */}
      <div className="lg:hidden flex items-center justify-between p-3 bg-ground border-b border-hairline sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-petrol inline-block" />
          <span className="font-bold text-xs text-ink">Phasora</span>
        </div>
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="p-1.5 rounded bg-panel border border-hairline text-ink"
          aria-label="Open navigation menu"
        >
          <IconMenu size={18} />
        </button>
      </div>

      {/* Desktop Fixed Left Sidebar */}
      <aside className="hidden lg:block w-64 h-screen sticky top-0 border-r border-hairline bg-ground shrink-0 z-30">
        {navContent}
      </aside>

      {/* Mobile Off-Canvas Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-ink/30 transition-opacity"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative w-72 max-w-[85vw] h-full bg-ground border-r border-hairline shadow-xl z-50 animate-fade-up">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
}
export default Sidebar;
