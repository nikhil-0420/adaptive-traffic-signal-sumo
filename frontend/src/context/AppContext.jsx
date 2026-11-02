import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);

const HASH_TO_VIEW = {
  '#': 'overview',
  '#overview': 'overview',
  '#junction': 'junction',
  '#site': 'junction',
  '#site-model': 'junction',
  '#operations': 'operations',
  '#live': 'live-simulation',
  '#live-simulation': 'live-simulation',
  '#live-monitor': 'live-simulation',
  '#compare': 'controller-comparison',
  '#controller-comparison': 'controller-comparison',
  '#lab': 'controller-comparison',
  '#evidence': 'evidence',
  '#research': 'evidence',
  '#runs': 'evidence',
  '#review': 'run-review',
  '#run-review': 'run-review',
};

const VIEW_TO_HASH = {
  'overview': '#overview',
  'junction': '#junction',
  'operations': '#operations',
  'live-simulation': '#live',
  'controller-comparison': '#compare',
  'evidence': '#evidence',
  'run-review': '#review',
};

export function AppProvider({ children }) {
  const getInitialView = () => {
    if (typeof window !== 'undefined' && window.location.hash) {
      const target = HASH_TO_VIEW[window.location.hash.toLowerCase()];
      if (target) return target;
    }
    return 'overview';
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

  // Active run review telemetry if user enters review mode
  const [activeReviewRun, setActiveReviewRun] = useState(null);

  // Theme State: 'light' | 'dark'
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('dp1_theme');
      if (saved === 'dark' || saved === 'light') return saved;
    }
    return 'dark';
  });

  const isDark = theme === 'dark';

  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      if (theme === 'dark') {
        root.classList.add('dark');
        root.setAttribute('data-theme', 'dark');
        root.style.setProperty('--color-ground', '#0E1112');
        root.style.setProperty('--color-panel', '#161A1C');
        root.style.setProperty('--color-raised', '#1D2326');
        root.style.setProperty('--color-inset', '#1D2326');
        root.style.setProperty('--color-hairline', '#252C30');
        root.style.setProperty('--color-ink', '#F1EEE6');
        root.style.setProperty('--color-ink-2', '#A8ADA6');
        root.style.setProperty('--color-ink-secondary', '#A8ADA6');
        root.style.setProperty('--color-ink-muted', '#70756F');
        root.style.setProperty('--color-accent', '#F6A81C');
        root.style.setProperty('--color-accent-hover', '#D99212');
        root.style.setProperty('--color-petrol', '#5AA7B1');
        root.style.setProperty('--color-petrol-hover', '#4A919A');
        root.style.setProperty('--color-petrol-subtle', '#182C30');
        root.style.setProperty('--color-petrol-tint', '#20393E');
        root.style.setProperty('--color-signal-green', '#3F9B66');
        root.style.setProperty('--color-signal-green-tint', '#1B3324');
        root.style.setProperty('--color-signal-green-text', '#5FC28A');
        root.style.setProperty('--color-signal-yellow', '#D9A521');
        root.style.setProperty('--color-signal-yellow-tint', '#382B12');
        root.style.setProperty('--color-signal-yellow-text', '#F2BD3F');
        root.style.setProperty('--color-signal-red', '#C0443C');
        root.style.setProperty('--color-signal-red-tint', '#361917');
        root.style.setProperty('--color-signal-red-text', '#E86B63');
        root.style.setProperty('--color-emergency', '#C0443C');
        root.style.setProperty('--color-emergency-tint', '#361917');
      } else {
        root.classList.remove('dark');
        root.setAttribute('data-theme', 'light');
        root.style.setProperty('--color-ground', '#EFEBE0');
        root.style.setProperty('--color-panel', '#F8F5EC');
        root.style.setProperty('--color-raised', '#E6E1D3');
        root.style.setProperty('--color-inset', '#E6E1D3');
        root.style.setProperty('--color-hairline', '#D9D3C5');
        root.style.setProperty('--color-ink', '#14181A');
        root.style.setProperty('--color-ink-2', '#585C57');
        root.style.setProperty('--color-ink-secondary', '#585C57');
        root.style.setProperty('--color-ink-muted', '#80857E');
        root.style.setProperty('--color-accent', '#F6A81C');
        root.style.setProperty('--color-accent-hover', '#DF9411');
        root.style.setProperty('--color-petrol', '#0F5F73');
        root.style.setProperty('--color-petrol-hover', '#0B4A5A');
        root.style.setProperty('--color-petrol-subtle', '#E2F1F5');
        root.style.setProperty('--color-petrol-tint', '#C5E3EB');
        root.style.setProperty('--color-signal-green', '#3F9B66');
        root.style.setProperty('--color-signal-green-tint', '#E8F5EE');
        root.style.setProperty('--color-signal-green-text', '#22633E');
        root.style.setProperty('--color-signal-yellow', '#D9A521');
        root.style.setProperty('--color-signal-yellow-tint', '#FBF6E7');
        root.style.setProperty('--color-signal-yellow-text', '#7A5506');
        root.style.setProperty('--color-signal-red', '#C0443C');
        root.style.setProperty('--color-signal-red-tint', '#F9ECEB');
        root.style.setProperty('--color-signal-red-text', '#731C18');
        root.style.setProperty('--color-emergency', '#C0443C');
        root.style.setProperty('--color-emergency-tint', '#F9ECEB');
      }
      localStorage.setItem('dp1_theme', theme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.__setTheme = setTheme;
      window.__toggleTheme = toggleTheme;
    }
  }, []);

  const initData = async () => {
    setLoading(true);
    try {
      const conn = await api.checkConnection();
      setConnectionStatus(conn.mode);
      setConnectionInfo(conn.data || conn.manifest || null);

      const runs = await api.getAllRuns();
      setAllRuns(runs);

      if (runs.length > 0 && !runs.some((r) => r.run_id === selectedRunId)) {
        const preferred =
          runs.find((r) => r.run_id === 'marathahalli_imbalanced_orr_adaptive_s121') ||
          runs.find((r) => r.network === 'marathahalli' && r.policy === 'hybrid_queue_adaptive') ||
          runs.find((r) => r.network === 'marathahalli') ||
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

  const openRunReview = (run) => {
    if (typeof run === 'string') {
      setSelectedRunId(run);
      setActiveReviewRun(allRuns.find((r) => r.run_id === run) || { run_id: run });
    } else if (run) {
      setSelectedRunId(run.run_id);
      setActiveReviewRun(run);
    }
    setCurrentView('run-review');
  };

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
        openRunReview,
        activeReviewRun,
        theme,
        setTheme,
        toggleTheme,
        isDark,
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
