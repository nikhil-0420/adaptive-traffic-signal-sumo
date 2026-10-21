import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { IsometricIntersection } from '../components/IsometricIntersection';
import {
  Radio,
  Play,
  RotateCcw,
  AlertTriangle,
  Siren,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sliders,
  ChevronRight,
  ExternalLink,
  Activity,
  TrendingUp,
  Gauge,
  Info,
  ShieldCheck,
  Zap,
} from 'lucide-react';

export function LiveMonitorView() {
  const { allRuns, selectedRunId, setSelectedRunId, connectionStatus, connectionInfo, refreshConnection } = useApp();

  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [decisionsHistory, setDecisionsHistory] = useState([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [launchParams, setLaunchParams] = useState({
    network: 'marathahalli',
    scenario: 'imbalanced_orr',
    policy: 'hybrid_queue_adaptive',
    seed: 121,
    emergency_priority: false,
    emergency_approach: 'N',
  });
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState(null);
  const [pollError, setPollError] = useState(null);

  const [stopping, setStopping] = useState(false);
  const [activeBackendRun, setActiveBackendRun] = useState(null);

  const isLiveApi = connectionStatus === 'api';
  const pollTimeoutRef = useRef(null);
  const abortControllerRef = useRef(null);
  const consecutiveErrorsRef = useRef(0);
  const isMountedRef = useRef(true);

  // Check for active backend runs to support reconnecting
  useEffect(() => {
    if (!isLiveApi) return;
    let active = true;
    api.getActiveRuns()
      .then((res) => {
        if (!active) return;
        if (res?.active_runs?.length > 0) {
          const first = res.active_runs[0];
          setActiveBackendRun(first);
        } else {
          setActiveBackendRun(null);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [isLiveApi, selectedRunId]);

  // Bounded poll execution with exponential backoff and lifecycle cleanup
  const executePoll = async () => {
    if (!isMountedRef.current) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const data = await api.getTelemetry(selectedRunId, controller.signal);
      if (!isMountedRef.current) return;

      // Successful poll -> reset error counters
      if (consecutiveErrorsRef.current > 0) {
        consecutiveErrorsRef.current = 0;
      }
      setPollError(null);
      setTelemetry(data);

      if (data?.adaptive_decision && data.adaptive_decision.t !== undefined) {
        setDecisionsHistory((prev) => {
          const latest = data.adaptive_decision;
          if (prev.some((d) => d.t === latest.t && d.action === latest.action)) return prev;
          return [latest, ...prev].slice(0, 30);
        });
      }

      // Check if simulation has ended: stop polling if complete or failed
      const isFinished = data?.status === 'completed' || data?.status === 'failed' || data?.status === 'stopped';
      if (isLiveApi && !isFinished && isMountedRef.current) {
        const intervalMs = data?.status === 'starting' ? 1000 : 1500;
        pollTimeoutRef.current = setTimeout(executePoll, intervalMs);
      }
    } catch (err) {
      if (!isMountedRef.current || err.name === 'AbortError') return;

      consecutiveErrorsRef.current += 1;
      const errCount = consecutiveErrorsRef.current;

      // Log once on first failure for diagnostics without console spam
      if (errCount === 1) {
        console.warn(`[LiveMonitor] Telemetry poll failed for ${selectedRunId}:`, err.message);
      }

      if (errCount <= 3 && isLiveApi && isMountedRef.current) {
        // Bounded exponential backoff: 2s, 4s, 8s
        const backoffMs = Math.min(2000 * Math.pow(2, errCount - 1), 8000);
        setPollError(`Connection error: ${err.message}. Retrying in ${Math.round(backoffMs / 1000)}s (attempt ${errCount}/3)...`);
        pollTimeoutRef.current = setTimeout(executePoll, backoffMs);
      } else {
        setPollError('Connection to simulation backend lost. Polling suspended. Click retry to reconnect.');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  // Fetch decision history on run change with abort signal
  useEffect(() => {
    const controller = new AbortController();
    api.getDecisions(selectedRunId, controller.signal)
      .then((res) => {
        if (res?.decisions?.length > 0) {
          setDecisionsHistory([...res.decisions].reverse().slice(0, 30));
        } else {
          setDecisionsHistory([]);
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          // Keep decisionsHistory intact on error
        }
      });

    return () => {
      controller.abort();
    };
  }, [selectedRunId]);

  // Setup single polling loop per active run
  useEffect(() => {
    isMountedRef.current = true;
    consecutiveErrorsRef.current = 0;
    setPollError(null);
    setLoading(true);

    if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);
    if (abortControllerRef.current) abortControllerRef.current.abort();

    executePoll();

    return () => {
      isMountedRef.current = false;
      if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, [selectedRunId, isLiveApi]);

  const handleManualRetry = () => {
    consecutiveErrorsRef.current = 0;
    setPollError(null);
    setLoading(true);
    if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);
    if (refreshConnection) refreshConnection();
    executePoll();
  };

  // Handle stopping active simulation
  const handleStopRun = async (runIdToStop) => {
    const target = runIdToStop || selectedRunId;
    if (!target) return;
    setStopping(true);
    try {
      await api.stopRun(target);
      executePoll();
    } catch (err) {
      console.warn('Failed to stop run:', err);
    } finally {
      setStopping(false);
    }
  };

  // Handle launch run
  const handleLaunch = async (e, force = false) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!isLiveApi) return;

    setLaunching(true);
    setLaunchError(null);

    try {
      const res = await api.launchRun({ ...launchParams, force });
      if (res && res.run_id) {
        setSelectedRunId(res.run_id);
        setIsDrawerOpen(false);
        consecutiveErrorsRef.current = 0;
        setPollError(null);
        executePoll();
      }
    } catch (err) {
      if (err.isConflict) {
        setLaunchError({
          isConflict: true,
          message: err.message,
          activeRunId: err.activeRunId || selectedRunId,
        });
      } else {
        setLaunchError({
          isConflict: false,
          message: err.message || 'Simulation launch failed.',
        });
      }
    } finally {
      setLaunching(false);
    }
  };

  // Determine staleness (only active when running; completed runs are never marked stale)
  const nowSec = Date.now() / 1000;
  const isStale =
    telemetry?.status === 'running' &&
    (telemetry?.is_stale ||
      (isLiveApi && telemetry?.updated_at && nowSec - telemetry.updated_at > 8.0));

  const selectedRunData = allRuns.find((r) => r.run_id === selectedRunId);
  const isMarathahalli =
    selectedRunData?.network === 'marathahalli' ||
    telemetry?.network === 'marathahalli' ||
    Boolean(selectedRunId && selectedRunId.startsWith('marathahalli_'));
  const maxDetectorLen = isMarathahalli ? 25 : 150;

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Radio className="text-blue-400" size={20} />
              <span>Live Run Monitor & Intersection Telemetry</span>
            </h1>
            <span className="dp1-badge dp1-badge-blue text-[11px]">Real-Time TraCI</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            4-way junction detector occupancy, phase state transitions, and priority vehicle radar.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Run Selector */}
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono text-slate-400">Target Run:</label>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              aria-label="Select target run"
              className="dp1-select text-xs font-mono max-w-[340px]"
            >
              <optgroup label="Marathahalli Bridge Site (Real Road - 720 Runs)">
                {allRuns
                  .filter((r) => r.network === 'marathahalli')
                  .map((r) => (
                    <option key={r.run_id} value={r.run_id} className="bg-slate-900 text-white">
                      [Marathahalli] {r.scenario} • {r.policy} • s{r.seed} ({r.demand_level || 'med'})
                    </option>
                  ))}
              </optgroup>
              <optgroup label="Synthetic 4-Way Junction (80 Runs)">
                {allRuns
                  .filter((r) => r.network !== 'marathahalli')
                  .map((r) => (
                    <option key={r.run_id} value={r.run_id} className="bg-slate-900 text-white">
                      [Synthetic] {r.scenario} • {r.policy} • s{r.seed}
                    </option>
                  ))}
              </optgroup>
            </select>
          </div>

          {/* Launch Drawer Toggle */}
          <button
            onClick={() => setIsDrawerOpen(true)}
            className={`dp1-btn text-xs px-3 py-1.5 rounded-md flex items-center gap-1.5 font-medium ${
              isLiveApi
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-sm'
                : 'bg-white/5 text-slate-400 hover:text-slate-200 border border-white/10'
            }`}
          >
            <Play size={13} />
            <span>Launch Simulation</span>
          </button>
        </div>
      </div>

      {/* Active Live Simulation in Progress Banner */}
      {isLiveApi && (telemetry?.status === 'running' || telemetry?.status === 'starting') && (
        <div className="p-3.5 bg-emerald-950/40 border border-emerald-500/40 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-emerald-200">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <div>
              <span className="font-semibold text-emerald-300">
                Live Simulation Active: <span className="font-mono">{selectedRunId}</span>
              </span>
              <span className="text-emerald-400/80 ml-2">
                (Clock: {Number(telemetry?.sim_time_s || 0).toFixed(1)}s • Phase: {telemetry?.phase || 'GREEN'} {telemetry?.axis || 'NS'})
              </span>
            </div>
          </div>
          <button
            onClick={() => handleStopRun(selectedRunId)}
            disabled={stopping}
            className="px-3 py-1 bg-red-900/60 hover:bg-red-800 text-red-100 border border-red-500/40 rounded text-xs font-medium shrink-0 flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>{stopping ? 'Stopping...' : 'Stop Simulation'}</span>
          </button>
        </div>
      )}

      {/* Another Active Backend Run Detected Banner */}
      {activeBackendRun && activeBackendRun.run_id !== selectedRunId && activeBackendRun.is_alive && (
        <div className="p-3 bg-blue-950/60 border border-blue-500/40 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-blue-200">
          <div className="flex items-center gap-2">
            <Info size={16} className="text-blue-400 shrink-0" />
            <span>
              Another simulation is currently running: <strong className="font-mono text-white">{activeBackendRun.run_id}</strong>
            </span>
          </div>
          <button
            onClick={() => setSelectedRunId(activeBackendRun.run_id)}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium shrink-0 flex items-center justify-center gap-1.5 transition-colors"
          >
            <span>Monitor Active Run</span>
          </button>
        </div>
      )}

      {/* Snapshot / Offline Notice Banner */}
      {!isLiveApi && (
        <div className="p-3.5 bg-amber-950/30 border border-amber-500/30 rounded-lg flex items-start gap-3 text-xs text-amber-200">
          <AlertCircle size={16} className="text-amber-400 mt-0.5 shrink-0" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-300">Saved Simulation Snapshot Mode</span>
            <p className="text-amber-200/80 leading-relaxed">
              Displaying final recorded junction states from verified repository artifacts. Live interactive execution, real-time stepping, and process controls require a connected Python backend running Eclipse SUMO.
            </p>
          </div>
        </div>
      )}

      {/* API Connection Error / Disconnected Banner */}
      {pollError && (
        <div className="p-3 bg-amber-950/60 border border-amber-500/40 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-200 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400 shrink-0" />
            <span>{pollError}</span>
          </div>
          <button
            onClick={handleManualRetry}
            className="px-3 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 rounded text-xs font-medium shrink-0 flex items-center justify-center gap-1.5 transition-colors"
          >
            <RotateCcw size={12} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* Telemetry Status Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="dp1-card p-3">
          <span className="text-[11px] font-mono uppercase text-slate-400">Simulation Clock</span>
          <div className="flex items-baseline gap-1 mt-1 font-mono">
            <span className="text-xl font-bold text-white">
              {telemetry ? Number(telemetry.sim_time_s || 0).toFixed(1) : '—'}
            </span>
            <span className="text-xs text-slate-400">s</span>
          </div>
        </div>

        <div className="dp1-card p-3">
          <span className="text-[11px] font-mono uppercase text-slate-400">Run Status</span>
          <div className="mt-1 flex items-center gap-1.5">
            {isStale ? (
              <span className="dp1-badge dp1-badge-yellow text-xs">
                <AlertTriangle size={11} className="text-amber-400" />
                <span>STALE</span>
              </span>
            ) : telemetry?.status === 'starting' ? (
              <span className="dp1-badge dp1-badge-blue text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                <span>STARTING</span>
              </span>
            ) : telemetry?.status === 'running' ? (
              <span className="dp1-badge dp1-badge-green text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 dp1-pulse" />
                <span>RUNNING</span>
              </span>
            ) : telemetry?.status === 'stopped' ? (
              <span className="dp1-badge dp1-badge-yellow text-xs">
                <span>STOPPED</span>
              </span>
            ) : telemetry?.status === 'failed' ? (
              <span className="dp1-badge dp1-badge-red text-xs">
                <AlertCircle size={11} className="text-red-400" />
                <span>FAILED</span>
              </span>
            ) : (
              <span className="dp1-badge dp1-badge-blue text-xs">
                <CheckCircle2 size={11} className="text-blue-400" />
                <span>COMPLETED</span>
              </span>
            )}
          </div>
        </div>

        <div className="dp1-card p-3">
          <span className="text-[11px] font-mono uppercase text-slate-400">Active Phase / Axis</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-lg font-bold font-mono text-emerald-400">
              {telemetry?.phase || 'GREEN'}
            </span>
            <span className="text-xs font-mono text-slate-300">
              ({telemetry?.axis || 'NS'})
            </span>
          </div>
        </div>

        <div className="dp1-card p-3">
          <span className="text-[11px] font-mono uppercase text-slate-400">Max Queue Observed</span>
          <div className="flex items-baseline gap-1 mt-1 font-mono">
            <span className="text-xl font-bold text-white">
              {selectedRunData?.max_queue_m ? Number(selectedRunData.max_queue_m).toFixed(1) : '—'}
            </span>
            <span className="text-xs text-slate-400">m</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Schematic + Detailed Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Isometric Intersection Simulation Twin */}
        <div className="lg:col-span-7">
          <IsometricIntersection
            runId={selectedRunId}
            network={isMarathahalli ? 'marathahalli' : 'synthetic'}
            liveTelemetry={telemetry}
            isLiveMode={isLiveApi && (telemetry?.status === 'running' || telemetry?.status === 'starting')}
            modeLabel={
              isLiveApi && (telemetry?.status === 'running' || telemetry?.status === 'starting')
                ? 'REAL-TIME TRACI LIVE TWIN'
                : 'COMPLETED / RECORDED RUN'
            }
            availableRuns={allRuns.map((r) => ({
              id: r.run_id,
              label: `${r.network === 'marathahalli' ? '[Marathahalli] ' : ''}${r.scenario} • ${r.policy} (s${r.seed})`,
            }))}
            onRunChange={(newId) => setSelectedRunId(newId)}
            className="w-full"
          />
        </div>

        {/* Right Column: Detector Telemetry & Signal State Info */}
        <div className="lg:col-span-5 space-y-4">
          {/* Approach Queues Detail Table (4 Approach Cards) */}
          <div className="dp1-card p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Gauge size={14} className="text-blue-400" />
                <span>Approach Queue Telemetry</span>
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {isMarathahalli ? '24.9m E2 Detectors' : '150m Length'}
              </span>
            </div>

            <div className="space-y-3">
              {(isMarathahalli
                ? [
                    {
                      id: 'N',
                      det: 'det_orr_n',
                      label: 'North: ORR (KR Puram)',
                      edge: 'leg_orr_n_in',
                      axis: 'NS',
                      q: telemetry?.approach_queues?.N?.longitudinal_queue_m ?? telemetry?.queues_m?.N ?? 0,
                      vehs: telemetry?.approach_queues?.N?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.N?.is_saturated ?? ((telemetry?.queues_m?.N ?? 0) >= 24.4),
                      sensor_status: telemetry?.approach_queues?.N?.sensor_status,
                      data_valid: telemetry?.approach_queues?.N?.data_valid,
                      gt_q: telemetry?.approach_queues?.N?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.N?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.N?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.N?.lanes,
                    },
                    {
                      id: 'S',
                      det: 'det_orr_s',
                      label: 'South: ORR (Kadubeesanahalli)',
                      edge: 'leg_orr_s_in',
                      axis: 'NS',
                      q: telemetry?.approach_queues?.S?.longitudinal_queue_m ?? telemetry?.queues_m?.S ?? 0,
                      vehs: telemetry?.approach_queues?.S?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.S?.is_saturated ?? ((telemetry?.queues_m?.S ?? 0) >= 24.4),
                      sensor_status: telemetry?.approach_queues?.S?.sensor_status,
                      data_valid: telemetry?.approach_queues?.S?.data_valid,
                      gt_q: telemetry?.approach_queues?.S?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.S?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.S?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.S?.lanes,
                    },
                    {
                      id: 'E',
                      det: 'det_wf',
                      label: 'East: Varthur Rd (Whitefield)',
                      edge: 'leg_wf_in',
                      axis: 'EW',
                      q: telemetry?.approach_queues?.E?.longitudinal_queue_m ?? telemetry?.queues_m?.E ?? 0,
                      vehs: telemetry?.approach_queues?.E?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.E?.is_saturated ?? ((telemetry?.queues_m?.E ?? 0) >= 24.4),
                      sensor_status: telemetry?.approach_queues?.E?.sensor_status,
                      data_valid: telemetry?.approach_queues?.E?.data_valid,
                      gt_q: telemetry?.approach_queues?.E?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.E?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.E?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.E?.lanes,
                    },
                    {
                      id: 'W',
                      det: 'det_hal',
                      label: 'West: Varthur Rd (HAL Airport)',
                      edge: 'leg_hal_in',
                      axis: 'EW',
                      q: telemetry?.approach_queues?.W?.longitudinal_queue_m ?? telemetry?.queues_m?.W ?? 0,
                      vehs: telemetry?.approach_queues?.W?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.W?.is_saturated ?? ((telemetry?.queues_m?.W ?? 0) >= 24.4),
                      sensor_status: telemetry?.approach_queues?.W?.sensor_status,
                      data_valid: telemetry?.approach_queues?.W?.data_valid,
                      gt_q: telemetry?.approach_queues?.W?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.W?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.W?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.W?.lanes,
                    },
                  ]
                : [
                    {
                      id: 'N',
                      det: 'det_N',
                      label: 'North Approach',
                      edge: 'N_in',
                      axis: 'NS',
                      q: telemetry?.approach_queues?.N?.longitudinal_queue_m ?? telemetry?.queues_m?.N ?? 0,
                      vehs: telemetry?.approach_queues?.N?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.N?.is_saturated ?? false,
                      sensor_status: telemetry?.approach_queues?.N?.sensor_status,
                      data_valid: telemetry?.approach_queues?.N?.data_valid,
                      gt_q: telemetry?.approach_queues?.N?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.N?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.N?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.N?.lanes,
                    },
                    {
                      id: 'S',
                      det: 'det_S',
                      label: 'South Approach',
                      edge: 'S_in',
                      axis: 'NS',
                      q: telemetry?.approach_queues?.S?.longitudinal_queue_m ?? telemetry?.queues_m?.S ?? 0,
                      vehs: telemetry?.approach_queues?.S?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.S?.is_saturated ?? false,
                      sensor_status: telemetry?.approach_queues?.S?.sensor_status,
                      data_valid: telemetry?.approach_queues?.S?.data_valid,
                      gt_q: telemetry?.approach_queues?.S?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.S?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.S?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.S?.lanes,
                    },
                    {
                      id: 'E',
                      det: 'det_E',
                      label: 'East Approach',
                      edge: 'E_in',
                      axis: 'EW',
                      q: telemetry?.approach_queues?.E?.longitudinal_queue_m ?? telemetry?.queues_m?.E ?? 0,
                      vehs: telemetry?.approach_queues?.E?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.E?.is_saturated ?? false,
                      sensor_status: telemetry?.approach_queues?.E?.sensor_status,
                      data_valid: telemetry?.approach_queues?.E?.data_valid,
                      gt_q: telemetry?.approach_queues?.E?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.E?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.E?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.E?.lanes,
                    },
                    {
                      id: 'W',
                      det: 'det_W',
                      label: 'West Approach',
                      edge: 'W_in',
                      axis: 'EW',
                      q: telemetry?.approach_queues?.W?.longitudinal_queue_m ?? telemetry?.queues_m?.W ?? 0,
                      vehs: telemetry?.approach_queues?.W?.total_queued_vehicles ?? 0,
                      isSat: telemetry?.approach_queues?.W?.is_saturated ?? false,
                      sensor_status: telemetry?.approach_queues?.W?.sensor_status,
                      data_valid: telemetry?.approach_queues?.W?.data_valid,
                      gt_q: telemetry?.approach_queues?.W?.ground_truth_queue_m,
                      gt_v: telemetry?.approach_queues?.W?.ground_truth_veh_count,
                      wait_s: telemetry?.approach_queues?.W?.total_waiting_time_s,
                      lanes: telemetry?.approach_queues?.W?.lanes,
                    },
                  ]
              ).map((arm) => {
                const pct = Math.min(100, Math.max(0, (arm.q / maxDetectorLen) * 100));
                const isArmGreen = telemetry?.axis === arm.axis && telemetry?.phase === 'GREEN';
                const isArmYellow = telemetry?.axis === arm.axis && telemetry?.phase === 'YELLOW';
                return (
                  <div key={arm.id} className="p-2.5 bg-slate-900/80 border border-white/5 rounded space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            isArmGreen ? 'bg-emerald-400 dp1-pulse' : isArmYellow ? 'bg-amber-400' : 'bg-red-400'
                          }`}
                        />
                        <span className="font-semibold text-slate-200">{arm.label}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {arm.data_valid === false || arm.sensor_status === 'OFFLINE' ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            OFFLINE
                          </span>
                        ) : arm.isSat || arm.sensor_status === 'SATURATED' ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                            SATURATED
                          </span>
                        ) : arm.q === 0 ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            CLEAR
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20">
                            MEASURING
                          </span>
                        )}
                        <span className="font-mono font-bold text-white text-sm">{arm.q.toFixed(1)} m</span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          arm.isSat ? 'bg-amber-400' : arm.axis === 'NS' ? 'bg-blue-500' : 'bg-cyan-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>

                    {/* Secondary Metrics */}
                    <div className="grid grid-cols-3 gap-1 pt-1 text-[11px] font-mono text-slate-400 border-t border-white/5">
                      <div>
                        Queued: <span className="text-slate-200 font-bold">{arm.vehs} veh</span>
                      </div>
                      <div>
                        Wait: <span className="text-slate-200">{arm.wait_s !== undefined ? `${arm.wait_s}s` : '—'}</span>
                      </div>
                      <div className="text-right" title="Microscopic ground truth queue extent">
                        GT: <span className="text-blue-300">{arm.gt_q !== undefined ? `${arm.gt_q}m` : '—'}</span>
                      </div>
                    </div>

                    {/* Per-lane Breakdown (if available) */}
                    {arm.lanes && arm.lanes.length > 0 && (
                      <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 pt-0.5">
                        {arm.lanes.map((l, lIdx) => (
                          <span key={lIdx} className="bg-slate-950/60 px-1.5 py-0.5 rounded border border-white/5">
                            L{l.lane_index}: <strong className="text-slate-300">{l.detector_queue_m}m</strong> ({l.detector_veh_count}v, {l.mean_speed_mps}m/s)
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Safety Invariant & State Machine Contract */}
          <div className="dp1-card p-4 space-y-2.5">
            <span className="text-xs font-semibold text-white uppercase tracking-wider">
              Safety Invariant Compliance
            </span>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every phase transition strictly enforces the zero-collision cycle:
            </p>
            <div className="p-2.5 bg-slate-900 border border-white/5 rounded font-mono text-[11px] text-slate-300 flex items-center justify-between">
              <span className="text-emerald-400 font-bold">GREEN (10s min)</span>
              <span className="text-slate-500">→</span>
              <span className="text-amber-400 font-bold">YELLOW (3s)</span>
              <span className="text-slate-500">→</span>
              <span className="text-red-400 font-bold">ALL-RED (2s)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Simultaneous greens across perpendicular axes are physically barred in the base state machine (<code className="text-slate-300">dp1/controllers/base.py</code>).
            </p>
          </div>

          {/* Emergency Priority Status */}
          <div className="dp1-card p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Siren size={14} className="text-red-400" />
                <span>Emergency Preemption</span>
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {selectedRunData?.emergency_mode || (selectedRunData?.metrics?.has_emergency ? 'ACTIVE' : 'OFF')}
              </span>
            </div>
            {selectedRunData?.emergency_wait_s !== undefined && selectedRunData?.emergency_wait_s !== null ? (
              <div className="p-2.5 bg-red-950/20 border border-red-500/20 rounded space-y-1 text-xs">
                <div className="flex justify-between font-mono">
                  <span className="text-slate-400">Ambulance Wait:</span>
                  <span className="font-bold text-red-300">{Number(selectedRunData.emergency_wait_s).toFixed(1)}s</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-400">Ambulance Time Loss:</span>
                  <span className="font-bold text-red-300">
                    {selectedRunData.emergency_time_loss_s !== null ? `${Number(selectedRunData.emergency_time_loss_s).toFixed(1)}s` : '—'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                No active emergency vehicle in current simulation scenario.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Full-Width Adaptive Signal Decision & Explanation Panel */}
      <div className="dp1-card p-5 space-y-5 border-blue-500/30 bg-gradient-to-br from-[#0c1322] via-[#0E131F] to-[#0A0D14]">
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Zap size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">
                  Adaptive Signal Decision Engine
                </h2>
                <span className="dp1-badge dp1-badge-purple text-[10px] font-mono">
                  Hybrid Webster + Queue-Adaptive
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Live explainability supervisor: baseline allocation, dynamic extension approvals, fairness bounds, and clearance enforcement.
              </p>
            </div>
          </div>

          {/* Current Green Axis Badge */}
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">Current Phase:</span>
            <span
              className={`px-3 py-1 rounded-md font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                telemetry?.phase === 'GREEN'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : telemetry?.phase === 'YELLOW'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-red-500/20 text-red-300 border border-red-500/40'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  telemetry?.phase === 'GREEN'
                    ? 'bg-emerald-400 dp1-pulse'
                    : telemetry?.phase === 'YELLOW'
                    ? 'bg-amber-400'
                    : 'bg-red-400'
                }`}
              />
              <span>
                {telemetry?.phase || 'GREEN'}{' '}
                {telemetry?.axis === 'NS' ? '— North–South (ORR)' : telemetry?.axis === 'EW' ? '— East–West (Varthur)' : ''}
              </span>
            </span>
          </div>
        </div>

        {/* 6-Column Metrics Grid */}
        {(() => {
          const dec = telemetry?.adaptive_decision || (decisionsHistory.length > 0 ? decisionsHistory[0] : null);
          const gBase = dec?.g_base_s ?? (telemetry?.axis === 'NS' ? 20.0 : 20.0);
          const elapsed = dec?.elapsed_s ?? (telemetry?.sim_time_s ? (telemetry.sim_time_s % 60) : 0);
          const deltaGApp = dec?.delta_g_app_s ?? (dec?.applied_action === 'EXTEND' || dec?.action === 'EXTEND' ? 3.0 : 0.0);
          const deltaGReq = dec?.delta_g_req_s ?? (dec?.proposed_action === 'EXTEND' ? 3.0 : 0.0);
          const isRejected = (dec?.proposed_action === 'EXTEND' && (dec?.applied_action !== 'EXTEND' || String(dec?.decision_outcome || '').startsWith('SWITCH_')));
          const gExtra = dec?.g_extra_s ?? 0.0;
          const gTarget = dec?.target_green_s ?? (gBase + gExtra);
          const scoreActive = dec?.score_active ?? dec?.q_active_m ?? 0.0;
          const scoreComp = dec?.score_competing ?? dec?.q_competing_m ?? 0.0;

          return (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Webster Baseline (G_base)</div>
                  <div className="text-xl font-bold font-mono text-blue-300">{Number(gBase).toFixed(1)}s</div>
                  <div className="text-[10px] text-slate-500">Nominal cycle split</div>
                </div>

                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Elapsed Green (t_el)</div>
                  <div className="text-xl font-bold font-mono text-white">{Number(elapsed).toFixed(1)}s</div>
                  <div className="text-[10px] text-slate-500">Current green service</div>
                </div>

                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Approved Increment (ΔG)</div>
                  <div className={`text-xl font-bold font-mono ${deltaGApp > 0 ? 'text-emerald-400' : isRejected ? 'text-rose-400' : 'text-slate-400'}`}>
                    {deltaGApp > 0 ? `+${Number(deltaGApp).toFixed(1)}s` : isRejected ? '0.0s (Rejected)' : '0.0s'}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {isRejected ? 'Proposed +3.0s refused' : 'Step: 3.0s bounded'}
                  </div>
                </div>

                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Accumulated Extra (G_extra)</div>
                  <div className="text-xl font-bold font-mono text-cyan-300">+{Number(gExtra).toFixed(1)}s</div>
                  <div className="text-[10px] text-slate-500">Total approved bonus</div>
                </div>

                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Target Duration (G_target)</div>
                  <div className="text-xl font-bold font-mono text-indigo-300">{Number(gTarget).toFixed(1)}s</div>
                  <div className="text-[10px] text-slate-500">Max ceiling: 60s</div>
                </div>

                <div className="p-3 bg-slate-900/80 rounded-lg border border-white/5 space-y-1">
                  <div className="text-[11px] font-mono text-slate-400 uppercase">Active vs Opposing Score</div>
                  <div className="text-base font-bold font-mono text-amber-300 flex items-baseline gap-1 mt-1">
                    <span>{Number(scoreActive).toFixed(1)}</span>
                    <span className="text-slate-500 text-xs">/</span>
                    <span className="text-slate-400 text-xs">{Number(scoreComp).toFixed(1)}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">Fairness ratio: 1.2x</div>
                </div>
              </div>

              {/* Real-Time Explanation Card */}
              <div className="p-4 bg-slate-900/90 border border-blue-500/20 rounded-lg space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5 mr-1">
                      <Activity size={14} className="text-blue-400" />
                      <span>Latest Decision</span>
                    </span>
                    {dec?.proposed_action && (
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                        Req: {dec.proposed_action} {dec.delta_g_req_s > 0 ? `(+${Number(dec.delta_g_req_s).toFixed(1)}s)` : ''}
                      </span>
                    )}
                    {(dec?.applied_action || dec?.action) && (
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                          (dec.applied_action === 'EXTEND' || (!dec.applied_action && dec.action === 'EXTEND'))
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                            : (dec.applied_action === 'REQUEST_SWITCH' || dec.action === 'REQUEST_SWITCH')
                            ? (isRejected ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40')
                            : (dec.applied_action === 'GAP_OUT' || dec.action === 'GAP_OUT')
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                            : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                        }`}
                      >
                        App: {(dec.applied_action === 'REQUEST_SWITCH' || dec.action === 'REQUEST_SWITCH') && isRejected ? 'SWITCH (Rejected Ext)' : (dec.applied_action || dec.action)}
                      </span>
                    )}
                    {(dec?.decision_outcome || dec?.reason_code) && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 text-slate-300 border border-white/10">
                        {dec.decision_outcome || dec.reason_code}
                      </span>
                    )}
                  </div>
                  {dec?.t !== undefined && (
                    <span className="text-xs font-mono text-slate-400">
                      Sim Time: <strong className="text-slate-200">{Number(dec.t).toFixed(1)}s</strong> (Cycle {dec.cycle ?? 0})
                    </span>
                  )}
                </div>

                <div className="p-3 bg-slate-950/60 rounded border border-white/5 font-mono text-xs text-slate-200 leading-relaxed">
                  {dec?.reason || 'Monitoring approach demand and queue states...'}
                </div>
              </div>

              {/* Chronological Decision History Table */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock size={13} className="text-slate-400" />
                    <span>Chronological Decision Log (Recent Events)</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    Showing latest {decisionsHistory.length} events
                  </span>
                </div>

                {decisionsHistory.length === 0 ? (
                  <div className="p-4 bg-slate-900/40 rounded border border-white/5 text-center text-xs text-slate-500">
                    No decision events recorded yet. Run simulation with hybrid_queue_adaptive controller to observe real-time rationale stream.
                  </div>
                ) : (
                  <div className="overflow-x-auto max-h-64 border border-white/5 rounded-lg">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-900/90 text-[11px] text-slate-400 uppercase sticky top-0 border-b border-white/5">
                        <tr>
                          <th className="p-2.5">Time</th>
                          <th className="p-2.5">Axis</th>
                          <th className="p-2.5">Proposed</th>
                          <th className="p-2.5">Applied / Outcome</th>
                          <th className="p-2.5">ΔG (Req / App)</th>
                          <th className="p-2.5">G Target</th>
                          <th className="p-2.5">Active / Comp Queue</th>
                          <th className="p-2.5">Rule / Rationale</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5 bg-slate-950/40">
                        {decisionsHistory.map((d, idx) => {
                          const rowReq = d.proposed_action || (d.delta_g_req_s > 0 ? 'EXTEND' : d.action);
                          const rowApp = d.applied_action || d.action;
                          const rowOutcome = d.decision_outcome || d.reason_code;
                          const rowRejected = (rowReq === 'EXTEND' && (rowApp !== 'EXTEND' || String(rowOutcome || '').startsWith('SWITCH_')));

                          return (
                            <tr key={`${d.t}-${d.action}-${idx}`} className="hover:bg-white/[0.02]">
                              <td className="p-2.5 text-slate-300">{Number(d.t).toFixed(1)}s</td>
                              <td className="p-2.5">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] ${
                                    d.axis === 'NS' ? 'bg-blue-500/20 text-blue-300' : 'bg-cyan-500/20 text-cyan-300'
                                  }`}
                                >
                                  {d.axis}
                                </span>
                              </td>
                              <td className="p-2.5 text-slate-300">
                                <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                                  {rowReq}
                                </span>
                              </td>
                              <td className="p-2.5">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                    rowApp === 'EXTEND'
                                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                      : rowApp === 'REQUEST_SWITCH'
                                      ? (rowRejected ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40')
                                      : rowApp === 'GAP_OUT'
                                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                      : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                                  }`}
                                >
                                  {rowApp === 'REQUEST_SWITCH' && rowRejected ? 'SWITCH (Rejected)' : rowApp}
                                </span>
                              </td>
                              <td className="p-2.5 text-slate-300">
                                {d.delta_g_req_s !== undefined && d.delta_g_app_s !== undefined
                                  ? `${Number(d.delta_g_req_s).toFixed(1)}s / ${Number(d.delta_g_app_s).toFixed(1)}s`
                                  : d.delta_g_app_s > 0 ? `+${d.delta_g_app_s}s` : '0.0s'}
                              </td>
                              <td className="p-2.5 text-slate-300">{d.target_green_s ?? d.green_s ?? '—'}s</td>
                              <td className="p-2.5 text-slate-400">
                                {d.q_active_m !== undefined ? `${d.q_active_m}m / ${d.q_competing_m}m` : '—'}
                              </td>
                              <td className="p-2.5 text-slate-300 max-w-md truncate" title={d.reason}>
                                {d.reason}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>

      {/* Launch Simulation Drawer / Modal */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="dp1-card w-full max-w-lg p-6 bg-[#0E131F] border border-white/20 shadow-2xl relative space-y-5">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Sliders size={18} className="text-blue-400" />
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                  Simulation Launch Configuration
                </h2>
              </div>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-white/5"
              >
                Close
              </button>
            </div>

            {!isLiveApi ? (
              <div className="space-y-4">
                <div className="p-4 bg-amber-950/40 border border-amber-500/40 rounded-lg space-y-2 text-xs text-amber-200">
                  <div className="flex items-center gap-2 font-semibold text-amber-300">
                    <AlertTriangle size={16} />
                    <span>Live Launch Disabled in Snapshot Mode</span>
                  </div>
                  <p className="leading-relaxed">
                    Live simulation launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO installed and the DP1 backend service running (<code className="text-amber-100">python -m dp1.api.server</code>) is required.
                  </p>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <p className="font-medium text-slate-300">To start live runs on your workstation:</p>
                  <pre className="p-2.5 bg-slate-950 rounded border border-white/10 font-mono text-[11px] text-blue-300">
                    python -m dp1.cli run --scenario imbalanced_ns --policy adaptive --seed 1
                  </pre>
                </div>
              </div>
            ) : (
              <form onSubmit={handleLaunch} className="space-y-4 text-xs">
                {launchError && (
                  <div className="p-3 bg-red-950/50 border border-red-500/40 rounded space-y-2 text-red-200">
                    <div className="flex items-center gap-2">
                      <AlertCircle size={14} className="shrink-0 text-red-400" />
                      <span>{typeof launchError === 'string' ? launchError : launchError.message}</span>
                    </div>
                    {launchError?.isConflict && (
                      <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-red-500/20">
                        <button
                          type="button"
                          onClick={() => {
                            const target = launchError.activeRunId || selectedRunId;
                            if (target) setSelectedRunId(target);
                            setIsDrawerOpen(false);
                            setLaunchError(null);
                          }}
                          className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-medium"
                        >
                          Reconnect to Active Run
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            const target = launchError.activeRunId || selectedRunId;
                            if (target) {
                              await api.stopRun(target).catch(() => {});
                            }
                            setLaunchError(null);
                            handleLaunch(null, true);
                          }}
                          className="px-2.5 py-1 bg-red-800 hover:bg-red-700 text-white rounded text-[11px] font-medium"
                        >
                          Stop Active Run & Launch Fresh
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-slate-300 font-medium">Network Architecture</label>
                  <select
                    value={launchParams.network || 'synthetic'}
                    onChange={(e) => {
                      const net = e.target.value;
                      setLaunchParams({
                        ...launchParams,
                        network: net,
                        scenario: net === 'marathahalli' ? 'imbalanced_orr' : 'imbalanced_ns',
                      });
                    }}
                    className="w-full bg-slate-900 border border-white/10 rounded px-2.5 py-1.5 text-white"
                  >
                    <option value="synthetic">Synthetic 4-Way Junction</option>
                    <option value="marathahalli">Marathahalli Bridge Site (Real Road)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-300 font-medium">Scenario</label>
                  <select
                    value={launchParams.scenario}
                    onChange={(e) => setLaunchParams({ ...launchParams, scenario: e.target.value })}
                    className="w-full bg-slate-900 border border-white/10 rounded px-2.5 py-1.5 text-white"
                  >
                    {launchParams.network === 'marathahalli' ? (
                      <>
                        <option value="balanced">Balanced Corridor</option>
                        <option value="imbalanced_orr">Imbalanced ORR (Heavy Arterial)</option>
                        <option value="imbalanced_varthur">Imbalanced Varthur Cross</option>
                        <option value="surge_orr_north">Surge ORR North (Peak Inflow)</option>
                      </>
                    ) : (
                      <>
                        <option value="balanced">Balanced 4-Way</option>
                        <option value="imbalanced_ns">Imbalanced NS (Heavy Corridor)</option>
                        <option value="imbalanced_ew">Imbalanced EW</option>
                        <option value="surge_north">Surge North (Asymmetric Peak)</option>
                      </>
                    )}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-300 font-medium">Control Policy</label>
                  <select
                    value={launchParams.policy}
                    onChange={(e) => setLaunchParams({ ...launchParams, policy: e.target.value })}
                    className="w-full bg-slate-900 border border-white/10 rounded px-2.5 py-1.5 text-white"
                  >
                    <option value="hybrid_queue_adaptive">Hybrid Queue-Adaptive (Mentor Enhanced)</option>
                    <option value="fixed">Fixed-Time Baseline</option>
                    <option value="fixed_webster">Webster Optimal Fixed-Time</option>
                    <option value="adaptive">Adaptive Queue-Length</option>
                    <option value="pressure">Max-Pressure Controller</option>
                    <option value="queue_extension">Bounded Queue-Extension</option>
                    <option value="rl_dqn">DQN Reinforcement Learning</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-300 font-medium">Random Seed</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={launchParams.seed}
                    onChange={(e) => setLaunchParams({ ...launchParams, seed: parseInt(e.target.value, 10) || 1 })}
                    className="w-full bg-slate-900 border border-white/10 rounded px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                <div className="p-3 bg-slate-900/60 border border-white/5 rounded space-y-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="emg_priority"
                      checked={launchParams.emergency_priority}
                      onChange={(e) => setLaunchParams({ ...launchParams, emergency_priority: e.target.checked })}
                      className="rounded border-white/20 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <label htmlFor="emg_priority" className="text-slate-200 font-medium cursor-pointer">
                      Enable Emergency Vehicle Priority Preemption
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
                  <button
                    type="button"
                    onClick={() => setIsDrawerOpen(false)}
                    className="px-3 py-1.5 rounded bg-white/5 text-slate-300 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={launching}
                    className="px-4 py-1.5 rounded bg-blue-600 text-white font-medium hover:bg-blue-500 disabled:opacity-50"
                  >
                    {launching ? 'Launching TraCI...' : 'Start Simulation'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
