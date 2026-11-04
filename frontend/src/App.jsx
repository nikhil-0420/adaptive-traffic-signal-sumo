import React, { useState, useEffect } from 'react';
import { useApp } from './context/AppContext';
import { FloatingNav } from './components/FloatingNav';
import { CommandPalette } from './components/motion/CommandPalette';
import { LandingPageView } from './views/LandingPageView';
import { JunctionView } from './views/JunctionView';
import { OperationsView } from './views/OperationsView';
import { LiveSimulationView } from './views/LiveSimulationView';
import { ControllerComparisonView } from './views/ControllerComparisonView';
import { EvidenceView } from './views/EvidenceView';
import { RunReviewView } from './views/RunReviewView';
import { ErrorBoundary } from './components/ErrorBoundary';
import { formatExperimentFooter, loadFinalManifest } from './utils/manifestInfo';

export function App() {
  const { currentView } = useApp();
  const [footerExperimentText, setFooterExperimentText] = useState('Final results pending');

  useEffect(() => {
    let isMounted = true;
    loadFinalManifest().then((manifest) => {
      if (isMounted) {
        setFooterExperimentText(formatExperimentFooter(manifest));
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const isLanding = currentView === 'overview';

  const renderView = () => {
    switch (currentView) {
      case 'overview':
        return <LandingPageView />;
      case 'junction':
        return <JunctionView />;
      case 'operations':
        return <OperationsView />;
      case 'live-simulation':
        return <LiveSimulationView />;
      case 'controller-comparison':
        return <ControllerComparisonView />;
      case 'evidence':
        return <EvidenceView />;
      case 'run-review':
        return <RunReviewView />;
      default:
        return <LandingPageView />;
    }
  };

  return (
    <div className="min-h-screen bg-ground text-ink flex flex-col font-sans selection:bg-petrol-subtle selection:text-petrol relative">
      {/* Floating Glass Pill Navigation (Replaces Sidebar Everywhere) */}
      <FloatingNav />

      {/* Ctrl/Cmd+K Global Command Palette */}
      <CommandPalette />

      {/* Main Content Area */}
      {isLanding ? (
        <main className="w-full flex-1">
          <ErrorBoundary key={currentView}>
            {renderView()}
          </ErrorBoundary>
        </main>
      ) : (
        <div className="flex-1 flex flex-col min-h-screen pt-28 sm:pt-32">
          <main className="flex-1 max-w-[1500px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <ErrorBoundary key={currentView}>
              {renderView()}
            </ErrorBoundary>
          </main>

          {/* Clean Footer with Academic Attribution for Dashboard Views */}
          <footer className="border-t border-hairline bg-panel px-4 sm:px-6 lg:px-8 py-4 mt-auto text-xs text-ink-2">
            <div className="max-w-[1500px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="space-y-0.5 text-center sm:text-left">
                <span className="font-semibold text-ink">
                  Alliance University • Department of Computer Science & Engineering
                </span>
                <div className="text-[11px] text-ink-2">
                  B.Tech Artificial Intelligence & Data Science — Design Project 1
                </div>
              </div>

              <div className="flex items-center gap-3 text-[11px] font-mono text-ink-2">
                <span>Marathahalli Bridge (modelled elevation, synthetic demand)</span>
                <span>•</span>
                <span>SUMO + TraCI</span>
                <span>•</span>
                <span>{footerExperimentText}</span>
              </div>
            </div>
          </footer>
        </div>
      )}
    </div>
  );
}

export default App;
