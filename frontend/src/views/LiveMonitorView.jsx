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
} from 'lucide-react';

export function LiveMonitorView() {
  const { allRuns, selectedRunId, setSelectedRunId, connectionStatus, connectionInfo } = useApp();

  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [launchParams, setLaunchParams] = useState({
    network: 'marathahalli',
    scenario: 'imbalanced_orr',
    policy: 'adaptive',
    seed: 121,
    emergency_priority: false,
    emergency_approach: 'N',
  });
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState(null);
  const [pollError, setPollError] = useState(null);

  const isLiveApi = connectionStatus === 'api';
  const pollTimerRef = useRef(null);

  // Fetch telemetry
  const fetchTelemetry = async () => {
    try {
      setPollError(null);
      const data = await api.getTelemetry(selectedRunId);
      setTelemetry(data);
    } catch (err) {
      console.warn('Telemetry poll error:', err.message);
      setPollError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Setup polling
  useEffect(() => {
    setLoading(true);
    fetchTelemetry();

    if (isLiveApi) {
      pollTimerRef.current = setInterval(fetchTelemetry, 1500);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [selectedRunId, isLiveApi]);

  // Handle launch run
  const handleLaunch = async (e) => {
    e.preventDefault();
    if (!isLiveApi) return;

    setLaunching(true);
    setLaunchError(null);

    try {
      const res = await api.launchRun(launchParams);
      if (res && res.run_id) {
        setSelectedRunId(res.run_id);
        setIsDrawerOpen(false);
        fetchTelemetry();
      }
    } catch (err) {
      setLaunchError(err.message || 'Simulation launch failed.');
    } finally {
      setLaunching(false);
    }
  };

  // Determine staleness
  const nowSec = Date.now() / 1000;
  const isStale =
    telemetry?.is_stale ||
    (isLiveApi && telemetry?.updated_at && nowSec - telemetry.updated_at > 5.0);

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
            ) : telemetry?.status === 'running' ? (
              <span className="dp1-badge dp1-badge-green text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 dp1-pulse" />
                <span>RUNNING</span>
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
            isLiveMode={isLiveApi && telemetry?.status === 'running'}
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
          {/* Approach Queues Detail Table */}
          <div className="dp1-card p-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-3">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                Lane-Area Detectors (E2)
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {isMarathahalli ? '25m Stop-Line Span' : '150m Length'}
              </span>
            </div>

            <div className="space-y-3">
              {(isMarathahalli
                ? [
                    { id: 'det_orr_s', label: 'North Approach (det_orr_s / Kadubeesanahalli)', val: telemetry?.queues_m?.N || 0, axis: 'NS' },
                    { id: 'det_orr_n', label: 'South Approach (det_orr_n / KR Puram)', val: telemetry?.queues_m?.S || 0, axis: 'NS' },
                    { id: 'det_wf', label: 'East Approach (det_wf / Whitefield)', val: telemetry?.queues_m?.E || 0, axis: 'EW' },
                    { id: 'det_hal', label: 'West Approach (det_hal / HAL Airport Rd)', val: telemetry?.queues_m?.W || 0, axis: 'EW' },
                  ]
                : [
                    { id: 'det_N', label: 'North Approach (det_N)', val: telemetry?.queues_m?.N || 0, axis: 'NS' },
                    { id: 'det_S', label: 'South Approach (det_S)', val: telemetry?.queues_m?.S || 0, axis: 'NS' },
                    { id: 'det_E', label: 'East Approach (det_E)', val: telemetry?.queues_m?.E || 0, axis: 'EW' },
                    { id: 'det_W', label: 'West Approach (det_W)', val: telemetry?.queues_m?.W || 0, axis: 'EW' },
                  ]
              ).map((arm) => {
                const pct = Math.min(100, Math.max(0, (arm.val / maxDetectorLen) * 100));
                const isArmGreen = telemetry?.axis === arm.axis && telemetry?.phase === 'GREEN';
                return (
                  <div key={arm.id} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span className={`w-2 h-2 rounded-full ${isArmGreen ? 'bg-emerald-400' : 'bg-red-400'}`} />
                        <span className="text-slate-300">{arm.label}</span>
                      </div>
                      <span className="font-mono font-bold text-white">{arm.val.toFixed(1)} m</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          arm.axis === 'NS' ? 'bg-blue-500' : 'bg-cyan-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
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
                  <div className="p-2.5 bg-red-950/50 border border-red-500/40 rounded text-red-200 flex items-center gap-2">
                    <AlertCircle size={14} className="shrink-0" />
                    <span>{launchError}</span>
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
