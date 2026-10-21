import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);

const HASH_TO_VIEW = {
  '#': 'landing',
  '#landing': 'landing',
  '#overview': 'overview',
  '#site': 'site-model',
  '#site-model': 'site-model',
  '#lab': 'controller-lab',
  '#controller-lab': 'controller-lab',
  '#runs': 'run-explorer',
  '#run-explorer': 'run-explorer',
  '#research': 'research',
  '#live': 'live-monitor',
  '#live-monitor': 'live-monitor',
};

const VIEW_TO_HASH = {
  'landing': '',
  'overview': '#overview',
  'site-model': '#site',
  'controller-lab': '#lab',
  'run-explorer': '#runs',
  'research': '#research',
  'live-monitor': '#live',
};

export function AppProvider({ children }) {
  const getInitialView = () => {
    if (typeof window !== 'undefined' && window.location.hash) {
      const target = HASH_TO_VIEW[window.location.hash.toLowerCase()];
      if (target) return target;
    }
    return 'landing';
  };

  const [currentView, setCurrentViewState] = useState(getInitialView);

  const setCurrentView = (view) => {
    setCurrentViewState(view);
    if (typeof window !== 'undefined') {
      const targetHash = VIEW_TO_HASH[view] ?? '';
      if (window.location.hash !== targetHash) {
        window.history.pushState(null, '', targetHash || window.location.pathname);
      }
    }
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.toLowerCase();
      const target = HASH_TO_VIEW[hash];
      if (target && target !== currentView) {
        setCurrentViewState(target);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [currentView]);

  const [connectionStatus, setConnectionStatus] = useState('checking'); // 'api' | 'snapshot' | 'degraded_api' | 'disconnected'
  const [connectionInfo, setConnectionInfo] = useState(null);
  const [allRuns, setAllRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState('marathahalli_imbalanced_orr_adaptive_s121');
  const [selectedScenario, setSelectedScenario] = useState('imbalanced_orr');
  const [selectedDemandLevel, setSelectedDemandLevel] = useState('medium');
  const [loading, setLoading] = useState(true);

  const initData = async () => {
    setLoading(true);
    try {
      const conn = await api.checkConnection();
      setConnectionStatus(conn.mode);
      setConnectionInfo(conn.data || conn.manifest || null);

      const runs = await api.getAllRuns();
      setAllRuns(runs);

      if (runs.length > 0 && !runs.some((r) => r.run_id === selectedRunId)) {
        // Find flagship Marathahalli run or first available
        const preferred =
          runs.find((r) => r.run_id === 'marathahalli_imbalanced_orr_medium_adaptive_s121') ||
          runs.find((r) => r.run_id === 'marathahalli_imbalanced_orr_adaptive_s121') ||
          runs.find((r) => r.network === 'marathahalli' && r.policy === 'adaptive') ||
          runs.find((r) => r.scenario === 'imbalanced_ns' && r.policy === 'adaptive') ||
          runs[0];
        const prefId = preferred.run_id || `${preferred.scenario}_${preferred.policy}_s${preferred.seed}`;
        setSelectedRunId(prefId);
      }
    } catch (err) {
      console.error('Initialization error:', err);
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initData();
  }, []);


  return (
    <AppContext.Provider
      value={{
        currentView,
        setCurrentView,
        connectionStatus,
        connectionInfo,
        allRuns,
        selectedRunId,
        setSelectedRunId,
        selectedScenario,
        setSelectedScenario,
        selectedDemandLevel,
        setSelectedDemandLevel,
        loading,
        refreshConnection: initData,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
