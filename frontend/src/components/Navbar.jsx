import React from 'react';
import { useApp } from '../context/AppContext';
import {
  Activity,
  Sliders,
  Search,
  FlaskConical,
  Radio,
  RefreshCw,
  AlertCircle,
  Database,
  Compass,
  Layers,
  Sparkles
} from 'lucide-react';

export function Navbar() {
  const { currentView, setCurrentView, connectionStatus, connectionInfo, refreshConnection, loading } = useApp();

  const navItems = [
    { id: 'landing', label: 'Product Overview', icon: Compass },
    { id: 'overview', label: 'Operations Overview', icon: Activity },
    { id: 'site-model', label: 'Site Model', icon: Layers },
    { id: 'controller-lab', label: 'Controller Lab', icon: Sliders },
    { id: 'run-explorer', label: 'Run Explorer', icon: Search },
    { id: 'research', label: 'Research & Evaluation', icon: FlaskConical },
    { id: 'live-monitor', label: 'Live Twin Monitor', icon: Radio },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-[#080d17]/95 backdrop-blur-md px-4 lg:px-8 py-3">
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Identity */}
        <button
          onClick={() => setCurrentView('landing')}
          className="flex items-center gap-3 text-left group transition-transform active:scale-[0.98]"
        >
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 border border-blue-400/30 flex items-center justify-center text-white font-extrabold font-mono text-sm shadow-[0_0_16px_rgba(37,99,235,0.35)] group-hover:border-blue-400">
            DP1
          </div>
          <div>
            <div className="font-bold tracking-tight text-white flex items-center gap-2">
              <span className="text-sm sm:text-base">Traffic Intelligence</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium">
                v1.0
              </span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <span>Alliance University AI & DS</span>
              <span>•</span>
              <span className="text-slate-500">TraCI Engine</span>
            </div>
          </div>
        </button>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto max-w-full pb-1 md:pb-0 scrollbar-none" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all whitespace-nowrap ${
                  active
                    ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30'
                    : 'text-slate-300 hover:text-white hover:bg-white/5 font-medium'
                }`}
              >
                <Icon size={14} className={active ? 'text-white' : 'text-slate-400'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Connection Mode Status Pill */}
        <div className="flex items-center gap-2">
          {connectionStatus === 'api' && (
            <div className="px-2.5 py-1 rounded-full bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-1.5 font-mono shadow-sm">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-semibold">API Live</span>
              <span className="hidden sm:inline text-[10px] text-emerald-400/80">
                ({connectionInfo?.sumo_version?.split(' ')[2] || 'SUMO'})
              </span>
            </div>
          )}

          {connectionStatus === 'snapshot' && (
            <div className="px-2.5 py-1 rounded-full bg-amber-950/60 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-1.5 font-mono shadow-sm">
              <Database size={12} className="text-amber-400 shrink-0" />
              <span className="font-semibold">Verified Snapshot</span>
              <span className="hidden sm:inline text-[10px] text-amber-400/80">(Vercel Ready)</span>
            </div>
          )}

          {connectionStatus === 'degraded_api' && (
            <div className="px-2.5 py-1 rounded-full bg-red-950/60 border border-red-500/30 text-red-300 text-xs flex items-center gap-1.5 font-mono">
              <AlertCircle size={12} className="text-red-400 shrink-0" />
              <span>SUMO Missing (503)</span>
            </div>
          )}

          {connectionStatus === 'disconnected' && (
            <div className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 text-xs flex items-center gap-1.5 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-500"></span>
              <span>Offline</span>
            </div>
          )}

          <button
            onClick={refreshConnection}
            disabled={loading}
            title="Refresh system connection"
            aria-label="Refresh connection"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg border border-white/5 hover:border-white/10 transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-blue-400' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
