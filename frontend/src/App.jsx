import React from 'react';
import { useApp } from './context/AppContext';
import { Navbar } from './components/Navbar';
import { OverviewView } from './views/OverviewView';
import { ControllerLabView } from './views/ControllerLabView';
import { RunExplorerView } from './views/RunExplorerView';
import { ResearchView } from './views/ResearchView';
import { LiveMonitorView } from './views/LiveMonitorView';
import { LandingPageView } from './views/LandingPageView';
import { SiteModelView } from './views/SiteModelView';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Database, ShieldCheck, AlertCircle, Info, ExternalLink } from 'lucide-react';

export function App() {
  const { currentView, connectionStatus, connectionInfo } = useApp();

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPageView />;
      case 'overview':
        return <OverviewView />;
      case 'site-model':
        return <SiteModelView />;
      case 'controller-lab':
        return <ControllerLabView />;
      case 'run-explorer':
        return <RunExplorerView />;
      case 'research':
        return <ResearchView />;
      case 'live-monitor':
        return <LiveMonitorView />;
      default:
        return <LandingPageView />;
    }
  };

  const snapshotTimestamp =
    connectionInfo?.generated_at || '2026-10-12T07:22:42Z';

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <Navbar />

      {/* Snapshot Mode Subheader Banner */}
      {connectionStatus === 'snapshot' && (
        <aside aria-label="Snapshot notice" className="bg-amber-950/20 border-b border-amber-500/20 px-4 lg:px-8 py-2">
          <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-amber-200/90">
            <div className="flex items-center gap-2">
              <Database size={13} className="text-amber-400 shrink-0" />
              <span>
                <strong className="text-amber-300 font-semibold">Saved Simulation Snapshot:</strong> All data loaded directly from verified repository artifacts (generated <span className="font-mono text-amber-100">{new Date(snapshotTimestamp).toUTCString()}</span>).
              </span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-amber-300/80">
              <ShieldCheck size={12} className="text-emerald-400" />
              <span>Zero fabricated metrics • Read-only exploration</span>
            </div>
          </div>
        </aside>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 lg:px-8 py-6">
        <ErrorBoundary key={currentView}>
          {renderView()}
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-[#080B11] px-4 lg:px-8 py-5 mt-auto text-xs text-slate-400">
        <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="space-y-0.5 text-center md:text-left">
            <div className="font-semibold text-slate-300">
              Alliance University • Department of Computer Science & Engineering
            </div>
            <div className="text-[11px] text-slate-400">
              B.Tech Artificial Intelligence & Data Science — Design Project 1 (DP1)
            </div>
          </div>

          <div className="flex items-center gap-4 text-[11px] text-slate-400">
            <span>Simulator: Eclipse SUMO + TraCI</span>
            <span>•</span>
            <span>Controller: Queue-Length / Max-Pressure / Webster / DQN</span>
            <span>•</span>
            <span className="text-slate-400">Placeholder fixed plan based on BTP Yamlur corridor</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
