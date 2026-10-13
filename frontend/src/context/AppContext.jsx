import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [currentView, setCurrentView] = useState('landing');
  const [connectionStatus, setConnectionStatus] = useState('checking'); // 'api' | 'snapshot' | 'degraded_api' | 'disconnected'
  const [connectionInfo, setConnectionInfo] = useState(null);
  const [allRuns, setAllRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState('imbalanced_ns_adaptive_s1');
  const [selectedScenario, setSelectedScenario] = useState('imbalanced_ns');
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

      if (runs.length > 0 && !runs.some(r => r.run_id === selectedRunId)) {
        // Find adaptive imbalanced_ns run or first available
        const preferred = runs.find(r => r.scenario === 'imbalanced_ns' && r.policy === 'adaptive') || runs[0];
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
