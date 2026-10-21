import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { IsometricIntersection } from '../components/IsometricIntersection';
import {
  Layers,
  MapPin,
  ShieldCheck,
  AlertCircle,
  FileText,
  Compass,
  ArrowRight,
  TrendingDown,
  Activity,
  Sliders,
  CheckCircle2,
  ExternalLink,
  Info,
  Maximize2,
  Minimize2,
  Play,
  Terminal,
  Copy,
  Check,
  Sparkles,
} from 'lucide-react';

export function SiteModelView() {
  const { setCurrentView, setSelectedRunId, connectionStatus } = useApp();
  const [siteData, setSiteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('topology'); // 'topology' | 'grade_separation' | 'signal_plan' | 'provenance' | 'simulation_runner'
  const [selectedMovement, setSelectedMovement] = useState('all');
  const [zoomedImage, setZoomedImage] = useState(null);
  const [selectedTopologyRun, setSelectedTopologyRun] = useState('marathahalli_imbalanced_orr_adaptive_s121');

  // Simulation Runner State
  const [simPolicy, setSimPolicy] = useState('hybrid_queue_adaptive');
  const [simScenario, setSimScenario] = useState('imbalanced_orr');
  const [simDemand, setSimDemand] = useState('medium');
  const [simSeed, setSimSeed] = useState(121);
  const [simLaunching, setSimLaunching] = useState(false);
  const [simError, setSimError] = useState(null);
  const [simConflictRunId, setSimConflictRunId] = useState(null);
  const [copiedCmd, setCopiedCmd] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const handleLaunchSimulation = async () => {
    setSimLaunching(true);
    setSimError(null);
    setSimConflictRunId(null);
    try {
      const res = await api.launchRun({
        network: 'marathahalli',
        scenario: simScenario,
        policy: simPolicy,
        seed: Number(simSeed) || 121,
        demand_level: simDemand,
      });
      if (res && res.run_id) {
        setSelectedRunId(res.run_id);
        setCurrentView('live-monitor');
      }
    } catch (err) {
      const msg = err.message || 'Failed to launch simulation on Marathahalli.';
      setSimError(msg);
      if (err.isConflict || msg.includes('already actively running') || msg.includes('already running')) {
        const netTag = 'marathahalli_';
        const targetId = simDemand === 'medium'
          ? `${netTag}${simScenario}_${simPolicy}_s${simSeed}`
          : `${netTag}${simScenario}_${simDemand}_${simPolicy}_s${simSeed}`;
        setSimConflictRunId(targetId);
      }
    } finally {
      setSimLaunching(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const data = await api.getSiteModel();
        if (mounted) setSiteData(data);
      } catch (err) {
        console.error('Failed to load site model:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading || !siteData) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
          <div className="text-sm font-medium text-slate-400">Loading Marathahalli Site Model Data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono font-medium flex items-center gap-1.5">
              <Layers size={13} />
              Phase 7B Verified Site Architecture
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-medium flex items-center gap-1.5">
              <ShieldCheck size={13} />
              OpenCity GIS & OSM Grounded
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white">
            Marathahalli Bridge Network Architecture
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl flex items-center gap-2">
            <MapPin size={14} className="text-slate-500 shrink-0" />
            <span>{siteData.location}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('simulation_runner')}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all active:scale-[0.98]"
          >
            <Play size={14} />
            <span>Run Simulation Live</span>
          </button>
          <button
            onClick={() => setCurrentView('research')}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-blue-600/20 transition-all active:scale-[0.98]"
          >
            <span>Explore Site Research Matrix</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Top 4 Key Facts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f172a]/70 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-400">Total Road Corridors</div>
          <div className="mt-2 text-2xl font-bold font-mono text-white">16 Lanes</div>
          <div className="mt-1 text-xs text-slate-400">4 Flyover • 6 Underpass • 6 Surface</div>
        </div>

        <div className="bg-[#0f172a]/70 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-400">Grade Separation</div>
          <div className="mt-2 text-2xl font-bold font-mono text-cyan-400">3 Tiers</div>
          <div className="mt-1 text-xs text-slate-400">Elevated + Grade Mainline + Signal</div>
        </div>

        <div className="bg-[#0f172a]/70 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-400">Controlled Node</div>
          <div className="mt-2 text-2xl font-bold font-mono text-amber-400">marathahalli_tls</div>
          <div className="mt-1 text-xs text-slate-400">8 E2 Lane-Area Induction Detectors</div>
        </div>

        <div className="bg-[#0f172a]/70 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-400">Clearance Invariant</div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">3s Y / 2s AR</div>
          <div className="mt-1 text-xs text-slate-400">100% Phase Safety Guaranteed</div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2 overflow-x-auto scrollbar-none">
        {[
          { id: 'simulation_runner', label: 'Run Simulation & Optimization', icon: Play },
          { id: 'topology', label: 'Network Schematic & SUMO GUI', icon: Compass },
          { id: 'grade_separation', label: '3-Tier Grade Separation', icon: Layers },
          { id: 'signal_plan', label: 'Signal Phasing & Clearance', icon: Sliders },
          { id: 'provenance', label: 'Truth & Provenance Matrix', icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-xs font-medium flex items-center gap-2 transition-all whitespace-nowrap ${
                active
                  ? 'bg-blue-600/20 border border-blue-500/40 text-blue-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <Icon size={14} className={active ? 'text-blue-400' : 'text-slate-500'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab: Run Simulation & Optimization */}
      {activeTab === 'simulation_runner' && (
        <div className="space-y-6">
          {/* Card 1: In-View Simulation Twin on Marathahalli Topology (Explicitly Labelled Preview) */}
          <div className="bg-[#0f172a]/90 border border-white/10 rounded-2xl p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Play size={18} className="text-blue-400" />
                  <span>Marathahalli Topology & Vehicle Dynamics Preview</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                    Recorded Sample Preview
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Pre-recorded reference demonstration of vehicles navigating <code className="text-amber-300">marathahalli_tls</code> across sample controllers. This is a reference preview, not an active simulation.
                </p>
              </div>

              <div className="flex items-center gap-1.5 bg-black/40 p-1 rounded-lg border border-white/10">
                {[
                  { id: 'marathahalli_imbalanced_orr_adaptive_s121', label: 'Adaptive' },
                  { id: 'marathahalli_imbalanced_orr_fixed_webster_s121', label: 'Webster' },
                  { id: 'marathahalli_imbalanced_orr_queue_extension_s121', label: 'Queue Ext' },
                  { id: 'marathahalli_imbalanced_orr_fixed_s121', label: 'Fixed Plan' },
                ].map((run) => (
                  <button
                    key={run.id}
                    onClick={() => setSelectedTopologyRun(run.id)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      selectedTopologyRun === run.id
                        ? 'bg-blue-600 text-white font-bold'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {run.label}
                  </button>
                ))}
              </div>
            </div>

            <IsometricIntersection
              runId={selectedTopologyRun}
              network="marathahalli"
              modeLabel="Recorded Sample Preview (Historical Replay)"
              availableRuns={[
                { id: 'marathahalli_imbalanced_orr_adaptive_s121', label: 'Adaptive Queue • Imbalanced ORR (s121)' },
                { id: 'marathahalli_imbalanced_orr_fixed_webster_s121', label: 'Webster Delay-Optimal (s121)' },
                { id: 'marathahalli_imbalanced_orr_queue_extension_s121', label: 'Bounded Queue-Extension (s121)' },
                { id: 'marathahalli_imbalanced_orr_fixed_s121', label: 'BTP Fixed-Time Baseline (s121)' },
              ]}
              onRunChange={(id) => setSelectedTopologyRun(id)}
              className="w-full"
            />
          </div>

          {/* Card 2: Interactive Browser Simulation Launcher & Controller Selector */}
          <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4 mb-6">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Play size={18} className="text-emerald-400" />
                  <span>Interactive TraCI Simulation Launcher</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                    Real Road Engine
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Launch a live microscopic simulation on the Marathahalli road construction. When launched, you will transition to Live Twin Monitor to observe live step-by-step telemetry.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded text-xs font-mono font-medium flex items-center gap-1.5 ${
                  connectionStatus === 'api'
                    ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-950/60 text-amber-300 border border-amber-500/30'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${connectionStatus === 'api' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                  {connectionStatus === 'api' ? 'SUMO Engine Live & Connected' : 'Saved Simulation Snapshot'}
                </span>
              </div>
            </div>

            {simError && (
              <div className="p-3.5 bg-amber-950/60 border border-amber-500/40 rounded-xl text-amber-200 text-xs space-y-2 mb-4 animate-fade-in">
                <div className="flex items-center gap-2">
                  <AlertCircle size={15} className="shrink-0 text-amber-400" />
                  <span className="font-medium">{simError}</span>
                </div>
                {simConflictRunId && (
                  <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-amber-500/20">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedRunId(simConflictRunId);
                        setCurrentView('live-monitor');
                      }}
                      className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors flex items-center gap-1.5 shadow"
                    >
                      <Activity size={13} />
                      <span>Reconnect to Live Simulation</span>
                    </button>
                    <button
                      type="button"
                      onClick={async () => {
                        await api.stopRun(simConflictRunId);
                        setSimConflictRunId(null);
                        setSimError(null);
                        handleLaunchSimulation();
                      }}
                      className="px-3 py-1 rounded bg-red-600/30 hover:bg-red-600/50 text-red-200 border border-red-500/40 font-medium text-xs transition-colors"
                    >
                      <span>Stop Simulation & Launch Fresh</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Policy */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-300 flex items-center justify-between">
                  <span>Signal Policy:</span>
                  <span className="text-[10px] text-blue-400">Optimization</span>
                </label>
                <select
                  value={simPolicy}
                  onChange={(e) => setSimPolicy(e.target.value)}
                  className="dp1-select w-full text-xs font-medium text-white"
                >
                  <option value="hybrid_queue_adaptive">Hybrid Queue-Adaptive (Mentor Enhanced)</option>
                  <option value="adaptive">Adaptive Queue-Length</option>
                  <option value="fixed_webster">Webster Delay-Optimal Fixed-Time</option>
                  <option value="queue_extension">Bounded Queue-Extension</option>
                  <option value="pressure">Max-Pressure Controller</option>
                  <option value="rl_dqn">DQN Reinforcement Learning</option>
                  <option value="fixed">BTP Fixed-Time Baseline</option>
                </select>
                <p className="text-[11px] text-slate-400">
                  {simPolicy === 'hybrid_queue_adaptive' && 'Combines bounded queue-length extension with minimum-green guarantees and all-red clearance enforcement.'}
                  {simPolicy === 'adaptive' && 'Sizes green dynamically based on stop-line E2 queue lengths (min 10s, max 60s).'}
                  {simPolicy === 'fixed_webster' && 'Applies Webster formula C_opt = (1.5L + 5)/(1 - Y) using 35% surface flow split.'}
                  {simPolicy === 'queue_extension' && 'Dynamically extends green while approach queues persist until gap-out or cap.'}
                  {simPolicy === 'pressure' && 'Balances upstream approach queue against downstream capacity.'}
                  {simPolicy === 'rl_dqn' && 'Evaluates Deep Q-Network trained on Marathahalli junction states.'}
                  {simPolicy === 'fixed' && 'Simulates static BTP field plan: 105s EW (HAL/WF) / 95s NS (ORR).'}
                </p>
              </div>

              {/* Scenario */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-300 flex items-center justify-between">
                  <span>Demand Scenario:</span>
                  <span className="text-[10px] text-emerald-400">Marathahalli</span>
                </label>
                <select
                  value={simScenario}
                  onChange={(e) => setSimScenario(e.target.value)}
                  className="dp1-select w-full text-xs font-medium text-white"
                >
                  <option value="imbalanced_orr">Imbalanced ORR (Heavy Arterial)</option>
                  <option value="balanced">Balanced Corridor</option>
                  <option value="imbalanced_varthur">Imbalanced Varthur Cross</option>
                  <option value="surge_orr_north">Surge ORR North (Morning Peak)</option>
                </select>
                <p className="text-[11px] text-slate-400">
                  {simScenario === 'imbalanced_orr' && 'Heavy Outer Ring Road volume (1003 vehicles) vs Varthur cross-traffic (441 vehicles).'}
                  {simScenario === 'balanced' && 'Equal flow distributed across both ORR underpass/slips and Varthur flyover/surface.'}
                  {simScenario === 'imbalanced_varthur' && 'Asymmetric congestion on HAL Airport Road and Whitefield approaches.'}
                  {simScenario === 'surge_orr_north' && 'Morning peak inbound rush from KR Puram southbound towards Bellandur.'}
                </p>
              </div>

              {/* Demand Level */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-300 flex items-center justify-between">
                  <span>Traffic Intensity:</span>
                  <span className="text-[10px] text-slate-400">Volume Scale</span>
                </label>
                <select
                  value={simDemand}
                  onChange={(e) => setSimDemand(e.target.value)}
                  className="dp1-select w-full text-xs font-medium text-white"
                >
                  <option value="low">Low (0.70x baseline)</option>
                  <option value="medium">Medium (1.00x baseline)</option>
                  <option value="heavy">Heavy (1.30x baseline)</option>
                </select>
                <p className="text-[11px] text-slate-400">
                  Medium demand delivers ~1,444 vehicles across the 1,800s demand window.
                </p>
              </div>

              {/* Seed & Launch */}
              <div className="space-y-1.5 flex flex-col justify-between">
                <div>
                  <label className="text-xs font-mono text-slate-300 flex items-center justify-between">
                    <span>Evaluation Seed:</span>
                    <span className="text-[10px] text-amber-400 font-mono">121..130 Held-Out</span>
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="999"
                    value={simSeed}
                    onChange={(e) => setSimSeed(parseInt(e.target.value, 10) || 121)}
                    className="dp1-input w-full text-xs font-mono"
                  />
                </div>

                <button
                  onClick={handleLaunchSimulation}
                  disabled={simLaunching}
                  className="w-full mt-2 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 transition-all active:scale-[0.98]"
                >
                  {simLaunching ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Launching TraCI Run...</span>
                    </>
                  ) : (
                    <>
                      <Play size={14} />
                      <span>Run Simulation on Marathahalli</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <Sparkles size={16} className="text-amber-400 shrink-0" />
                <span>
                  <strong>Tip:</strong> Launching switches directly to the <strong>Live Monitor Twin</strong> to track detector occupancy meters, phase switching, and queue clearance in real time.
                </span>
              </div>
              <button
                onClick={() => {
                  setSelectedRunId('marathahalli_imbalanced_orr_medium_adaptive_s121');
                  setCurrentView('live-monitor');
                }}
                className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-mono text-[11px] shrink-0"
              >
                <span>View Default Adaptive Run (s121)</span>
                <ArrowRight size={12} />
              </button>
            </div>
          </div>

          {/* Card 2: Desktop Eclipse SUMO-GUI Terminal Runner */}
          <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Terminal size={18} className="text-blue-400" />
                  <span>Desktop Eclipse SUMO-GUI Microscopic Simulation</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Run the real-road Marathahalli reconstruction directly in Eclipse SUMO GUI to view 3D/2D microscopic vehicles, flyover grade-separation, and queue detectors.
                </p>
              </div>
              <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded-lg border border-white/5">
                Windows / Linux / macOS
              </span>
            </div>

            <div className="space-y-4">
              {[
                {
                  id: 'cmd_adaptive',
                  label: 'Adaptive Queue-Length Optimization (Recommended)',
                  policy: 'adaptive',
                  cmd: '.venv\\Scripts\\python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy adaptive --seed 121 --gui',
                  desc: 'Dynamically scales green time based on real-time slip-road E2 queue measurements. Cuts delay by 11.1%.',
                  badge: 'Adaptive',
                  badgeColor: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
                },
                {
                  id: 'cmd_webster',
                  label: 'Webster Delay-Optimal Fixed Plan',
                  policy: 'fixed_webster',
                  cmd: '.venv\\Scripts\\python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy fixed_webster --seed 121 --gui',
                  desc: 'Computes optimal cycle time C_opt = (1.5L + 5)/(1 - Y) matching the 35% surface flow split. Cuts delay by 11.0%.',
                  badge: 'Webster',
                  badgeColor: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
                },
                {
                  id: 'cmd_queue_ext',
                  label: 'Bounded Queue-Extension Policy',
                  policy: 'queue_extension',
                  cmd: '.venv\\Scripts\\python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy queue_extension --seed 121 --gui',
                  desc: 'Extends green dynamically in 3s steps while approach queue exceeds threshold, with gap-out cap. Cuts delay by 13.4%.',
                  badge: 'Queue Ext',
                  badgeColor: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10',
                },
                {
                  id: 'cmd_fixed',
                  label: 'BTP Static Fixed-Time Baseline (Field Timing Plan)',
                  policy: 'fixed',
                  cmd: '.venv\\Scripts\\python -m dp1.cli run --network marathahalli --scenario imbalanced_orr --policy fixed --seed 121 --gui',
                  desc: 'Official Bengaluru Traffic Police baseline timings: 105s net green for HAL/Whitefield (EW) and 95s net green for ORR (NS).',
                  badge: 'Baseline',
                  badgeColor: 'border-slate-500/30 text-slate-400 bg-slate-500/10',
                },
              ].map((item) => (
                <div key={item.id} className="p-4 rounded-xl bg-slate-900 border border-white/5 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold border ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                      <span className="text-xs font-bold text-white">{item.label}</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(item.cmd, item.id)}
                      className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-[11px] font-mono flex items-center gap-1.5 transition-colors self-start sm:self-auto"
                    >
                      {copiedCmd === item.id ? (
                        <>
                          <Check size={12} className="text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy Command</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="font-mono text-xs text-blue-300 bg-black/50 p-2.5 rounded-lg border border-white/10 select-all overflow-x-auto">
                    {item.cmd}
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>

            {/* SUMO GUI User Guide */}
            <div className="mt-5 p-4 rounded-xl bg-blue-950/20 border border-blue-500/20 space-y-2 text-xs text-slate-300">
              <div className="font-bold text-white flex items-center gap-1.5">
                <Info size={14} className="text-blue-400" />
                <span>How to inspect the Marathahalli simulation in SUMO-GUI:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
                <li>Run one of the commands above in your PowerShell or terminal.</li>
                <li>When the <strong>Eclipse SUMO GUI</strong> window opens, adjust the <strong>Delay</strong> slider (top toolbar) to <strong>50ms</strong> for smooth human-observable simulation speed.</li>
                <li>Click the green <strong>Play</strong> button to begin microscopic vehicle movement.</li>
                <li>Notice the <strong>4-lane elevated Varthur flyover</strong> (elevation +6m) and <strong>6-lane ORR underpass</strong> flowing continuously, while surface slip roads queue at <code className="text-slate-300">marathahalli_tls</code> where 8 induction detectors regulate signals.</li>
              </ul>
            </div>
          </div>

          {/* Card 3: Empirical Optimization Effectiveness on Marathahalli Topology */}
          <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Activity size={18} className="text-amber-400" />
                  <span>Real Performance Comparison on Marathahalli Topology</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Empirical metrics across 720 cells (10 held-out evaluation seeds 121..130, Medium demand intensity).
                </p>
              </div>
              <button
                onClick={() => setCurrentView('controller-lab')}
                className="text-xs text-blue-400 hover:text-blue-300 font-mono flex items-center gap-1"
              >
                <span>Full Benchmark Lab</span>
                <ArrowRight size={13} />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900 border-b border-white/10 text-slate-400 font-mono text-[11px]">
                  <tr>
                    <th className="py-2.5 px-4">Signal Policy</th>
                    <th className="py-2.5 px-4">Policy Class</th>
                    <th className="py-2.5 px-4">Avg Wait Time</th>
                    <th className="py-2.5 px-4">Reduction vs Fixed</th>
                    <th className="py-2.5 px-4">Peak Queue (m)</th>
                    <th className="py-2.5 px-4">Wait Disparity</th>
                    <th className="py-2.5 px-4">Throughput</th>
                    <th className="py-2.5 px-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {[
                    {
                      policy: 'queue_extension',
                      name: 'Bounded Queue-Extension',
                      type: 'Actuated / Dynamic',
                      wait: '41.2s',
                      sd: '± 1.4s',
                      delta: '+13.4%',
                      queue: '24.0m',
                      disp: '49.3s',
                      tput: '2,728 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_queue_extension_s121',
                      isBest: true,
                    },
                    {
                      policy: 'pressure',
                      name: 'Max-Pressure Controller',
                      type: 'Network-Aware',
                      wait: '41.8s',
                      sd: '± 1.2s',
                      delta: '+12.2%',
                      queue: '23.5m',
                      disp: '51.2s',
                      tput: '2,715 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_pressure_s121',
                    },
                    {
                      policy: 'adaptive',
                      name: 'Adaptive Queue-Length',
                      type: 'Queue-Proportional',
                      wait: '42.3s',
                      sd: '± 1.5s',
                      delta: '+11.1%',
                      queue: '24.0m',
                      disp: '56.7s',
                      tput: '2,704 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_adaptive_s121',
                    },
                    {
                      policy: 'fixed_webster',
                      name: 'Webster Delay-Optimal',
                      type: 'Cycle-Optimized Fixed',
                      wait: '42.4s',
                      sd: '± 1.3s',
                      delta: '+11.0%',
                      queue: '24.0m',
                      disp: '59.1s',
                      tput: '2,710 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_fixed_webster_s121',
                    },
                    {
                      policy: 'rl_dqn',
                      name: 'DQN Reinforcement Learning',
                      type: 'Deep Neural Net',
                      wait: '43.0s',
                      sd: '± 1.8s',
                      delta: '+9.7%',
                      queue: '24.0m',
                      disp: '58.4s',
                      tput: '2,690 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_rl_dqn_s121',
                    },
                    {
                      policy: 'fixed',
                      name: 'Fixed Baseline (BTP Field)',
                      type: 'Static Field Timing',
                      wait: '47.6s',
                      sd: '± 2.1s',
                      delta: 'Baseline',
                      queue: '24.9m',
                      disp: '63.0s',
                      tput: '2,682 veh/h',
                      runId: 'marathahalli_imbalanced_orr_medium_fixed_s121',
                      isBaseline: true,
                    },
                  ].map((row) => (
                    <tr key={row.policy} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-4 font-semibold text-white font-sans flex items-center gap-2">
                        <span>{row.name}</span>
                        {row.isBest && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono">
                            Top
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans text-xs">{row.type}</td>
                      <td className="py-3 px-4 font-bold text-white">{row.wait} <span className="text-slate-500 text-[10px]">{row.sd}</span></td>
                      <td className="py-3 px-4">
                        {row.isBaseline ? (
                          <span className="text-slate-500">Reference</span>
                        ) : (
                          <span className="text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30">
                            {row.delta}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{row.queue}</td>
                      <td className="py-3 px-4 text-slate-300">{row.disp}</td>
                      <td className="py-3 px-4 text-slate-300">{row.tput}</td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => {
                            setSelectedRunId(row.runId);
                            setCurrentView('run-explorer');
                          }}
                          className="px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 text-[11px] font-sans flex items-center gap-1 border border-blue-500/30"
                        >
                          <span>Explore</span>
                          <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Why optimization succeeds on Marathahalli */}
            <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-900 border border-white/5 space-y-1.5">
                <div className="font-bold text-emerald-400">1. Grade Separation Relief</div>
                <p className="text-slate-400 leading-relaxed">
                  Flyover (+6m) and Underpass (grade 0) siphon 65% of corridor flow completely off the signal, avoiding all stopping delay.
                </p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900 border border-white/5 space-y-1.5">
                <div className="font-bold text-amber-400">2. Webster Cycle Sizing</div>
                <p className="text-slate-400 leading-relaxed">
                  Webster calculates optimal cycle C_opt matching the remaining 35% surface traffic, eliminating 40s+ of static BTP red delay.
                </p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900 border border-white/5 space-y-1.5">
                <div className="font-bold text-blue-400">3. Adaptive Queue Allocation</div>
                <p className="text-slate-400 leading-relaxed">
                  Lane-area E2 detectors measure slip-road queues in real time, granting green only while queues exist and clearing the junction faster.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 1: Topology & SUMO GUI Render */}
      {activeTab === 'topology' && (
        <div className="space-y-6">
          {/* 1:1 Live Simulation Twin Viewport of actual Marathahalli Topology */}
          <div className="bg-[#0f172a]/90 border border-white/10 rounded-2xl p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Compass size={18} className="text-blue-400" />
                  <span>Marathahalli Junction Topology Simulation Twin</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                    700m × 700m SUMO Net
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Microscopic TraCI vehicle trajectories rendered in 2.5D Isometric (Flyover Z=+7m, Underpass grade-0) & Top-Down orthographic camera angles.
                </p>
              </div>

              {/* Policy Quick-Switch Buttons */}
              <div className="flex items-center gap-1.5 bg-black/40 p-1 rounded-lg border border-white/10 overflow-x-auto">
                {[
                  { id: 'marathahalli_imbalanced_orr_adaptive_s121', label: 'Adaptive (s121)' },
                  { id: 'marathahalli_imbalanced_orr_fixed_webster_s121', label: 'Webster (s121)' },
                  { id: 'marathahalli_imbalanced_orr_queue_extension_s121', label: 'Queue Ext' },
                  { id: 'marathahalli_imbalanced_orr_fixed_s121', label: 'Fixed Baseline' },
                ].map((run) => (
                  <button
                    key={run.id}
                    onClick={() => setSelectedTopologyRun(run.id)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                      selectedTopologyRun === run.id
                        ? 'bg-blue-600 text-white font-bold shadow'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span>{run.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <IsometricIntersection
              runId={selectedTopologyRun}
              network="marathahalli"
              availableRuns={[
                { id: 'marathahalli_imbalanced_orr_adaptive_s121', label: 'Adaptive Queue • Imbalanced ORR (s121)' },
                { id: 'marathahalli_imbalanced_orr_fixed_webster_s121', label: 'Webster Delay-Optimal (s121)' },
                { id: 'marathahalli_imbalanced_orr_queue_extension_s121', label: 'Bounded Queue-Extension (s121)' },
                { id: 'marathahalli_imbalanced_orr_fixed_s121', label: 'BTP Fixed-Time Baseline (s121)' },
              ]}
              onRunChange={(id) => setSelectedTopologyRun(id)}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Visual Schematic Diagram */}
            <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-5 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Reconstructed Junction Topology</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                      matplotlib 1:1 vector
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Geometric layout showing HAL (West), Whitefield (East), ORR North, and ORR South corridors.
                  </p>
                </div>
              </div>

              <div className="relative rounded-xl overflow-hidden border border-white/10 bg-slate-950 flex items-center justify-center min-h-[360px] group">
                <img
                  src={siteData.topology_image_url}
                  alt="Marathahalli Network Topology"
                  className="w-full h-auto max-h-[460px] object-contain transition-transform group-hover:scale-[1.01]"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = '/network/marathahalli/marathahalli_network_topology.png';
                  }}
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>Legend: Cyan = Varthur Flyover • Emerald = ORR Mainline • Amber = Ramps • Coral = Surface Legs • Red = Signal Node</span>
                <a
                  href={siteData.topology_image_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 hover:underline flex items-center gap-1 font-mono text-[11px]"
                >
                  <ExternalLink size={12} /> View Full Vector
                </a>
              </div>
            </div>

            {/* SUMO-GUI Simulated Microscopic Rendering */}
            <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-5 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Eclipse SUMO TraCI Simulation Model</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                      SUMO 1.28 Net & E2 Detectors
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Microscopic traffic network with configured 25m stop-line queue detectors and vehicle lane assignments.
                  </p>
                </div>
              </div>

              <div className="relative rounded-xl overflow-hidden border border-white/10 bg-slate-950 flex items-center justify-center min-h-[360px] group">
                <img
                  src={siteData.sumo_gui_image_url}
                  alt="SUMO GUI Render"
                  className="w-full h-auto max-h-[460px] object-contain transition-transform group-hover:scale-[1.01]"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = '/network/marathahalli/sumo_gui_render.png';
                  }}
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>Lane-Area Detectors: det_hal_0..1, det_wf_0..1, det_orr_s_0..1, det_orr_n_0..1</span>
                <span className="text-slate-500 font-mono text-[11px]">8 Detectors Active</span>
              </div>
            </div>
          </div>

          {/* Movement Flow Explanations */}
          <div className="bg-[#0f172a]/50 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-3">Road Geometry & Approach Alignments</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <div className="font-semibold text-blue-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-blue-400"></span>
                  West Approach (HAL)
                </div>
                <div className="text-slate-300">Varthur Road from HAL Airport</div>
                <div className="text-slate-500">2 Flyover lanes + 2 Surface legs + 1 North Slip Road</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <div className="font-semibold text-blue-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-blue-400"></span>
                  East Approach (Whitefield)
                </div>
                <div className="text-slate-300">Varthur Road from ITPL / Whitefield</div>
                <div className="text-slate-500">2 Flyover lanes + 2 Surface legs + 1 South Slip Road</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                  North Approach (K.R. Puram)
                </div>
                <div className="text-slate-300">Outer Ring Road (ORR North)</div>
                <div className="text-slate-500">3 Underpass lanes + 2 Service ramp legs + 1 East Slip</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                  South Approach (Kadubeesanahalli)
                </div>
                <div className="text-slate-300">Outer Ring Road (ORR South / Bellandur)</div>
                <div className="text-slate-500">3 Underpass lanes + 2 Service ramp legs + 1 West Slip</div>
              </div>
            </div>

            {/* Geometry Extents Distinction: Network Span vs GIS Crop */}
            <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-blue-500/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-blue-300">SUMO Simulation Network Span</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">700m × 700m</span>
                </div>
                <div className="text-slate-400 text-[11px] leading-relaxed">
                  Local Cartesian coordinates: <span className="font-mono text-slate-300">X ∈ [0.0, 700.0]m, Y ∈ [0.0, 700.0]m</span>.
                  Surface signal junction is centered at <span className="font-mono text-slate-300">(350.0, 332.0)</span> with 350m approach arms extending to arterial boundaries.
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-emerald-500/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-emerald-300">OpenCity GIS Crop Bounding Box</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">1.52km × 1.55km</span>
                </div>
                <div className="text-slate-400 text-[11px] leading-relaxed">
                  Geographic crop coordinates: <span className="font-mono text-slate-300">lat ∈ [12.950, 12.964]° N, lon ∈ [77.694, 77.708]° E</span> (0.014° × 0.014°).
                  Source extent used to filter and extract road centerline and road-width vectors from statewide OpenCity datasets.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Grade Separation Deep-Dive */}
      {activeTab === 'grade_separation' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1: Flyover */}
            <div className="bg-gradient-to-b from-blue-950/40 to-slate-900/80 border border-blue-500/20 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-10">
                <Layers size={100} className="text-blue-400" />
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[10px] uppercase font-bold">
                  Tier 1 • Elevated
                </span>
              </div>
              <h3 className="text-base font-bold text-white">{siteData.grade_separation.flyover.name}</h3>
              <div className="text-xs text-blue-300/80 mt-1 font-mono">{siteData.grade_separation.flyover.lanes} Lanes • Bidirectional</div>

              <p className="text-xs text-slate-300 mt-4 leading-relaxed">
                {siteData.grade_separation.flyover.function}
              </p>

              <div className="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Corridor:</span>
                  <span className="text-slate-200 font-medium">Varthur Main Road</span>
                </div>
                <div className="flex justify-between">
                  <span>Speed Limit:</span>
                  <span className="text-slate-200 font-mono">60 km/h (16.67 m/s)</span>
                </div>
                <div className="flex justify-between">
                  <span>Signals Encountered:</span>
                  <span className="text-emerald-400 font-semibold">0 (Free Flow)</span>
                </div>
              </div>
            </div>

            {/* Tier 2: Surface Signal */}
            <div className="bg-gradient-to-b from-amber-950/40 to-slate-900/80 border border-amber-500/20 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-10">
                <Sliders size={100} className="text-amber-400" />
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] uppercase font-bold">
                  Tier 2 • Surface Level
                </span>
              </div>
              <h3 className="text-base font-bold text-white">{siteData.grade_separation.surface_level.name}</h3>
              <div className="text-xs text-amber-300/80 mt-1 font-mono">2 Lanes per Leg • 8 Total Legs</div>

              <p className="text-xs text-slate-300 mt-4 leading-relaxed">
                {siteData.grade_separation.surface_level.function}
              </p>

              <div className="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Controlled Node:</span>
                  <span className="text-amber-300 font-mono">marathahalli_tls</span>
                </div>
                <div className="flex justify-between">
                  <span>Optimization:</span>
                  <span className="text-slate-200 font-medium">Fixed / Webster / Adaptive / DQN</span>
                </div>
                <div className="flex justify-between">
                  <span>Priority Override:</span>
                  <span className="text-emerald-400 font-semibold">Ambulance Preemption</span>
                </div>
              </div>
            </div>

            {/* Tier 3: Underpass */}
            <div className="bg-gradient-to-b from-emerald-950/40 to-slate-900/80 border border-emerald-500/20 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-10">
                <Layers size={100} className="text-emerald-400" />
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] uppercase font-bold">
                  Tier 3 • Underpass Mainline
                </span>
              </div>
              <h3 className="text-base font-bold text-white">{siteData.grade_separation.underpass.name}</h3>
              <div className="text-xs text-emerald-300/80 mt-1 font-mono">{siteData.grade_separation.underpass.lanes} Lanes • Dual Carriageway</div>

              <p className="text-xs text-slate-300 mt-4 leading-relaxed">
                {siteData.grade_separation.underpass.function}
              </p>

              <div className="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Corridor:</span>
                  <span className="text-slate-200 font-medium">Outer Ring Road (ORR)</span>
                </div>
                <div className="flex justify-between">
                  <span>Speed Limit:</span>
                  <span className="text-slate-200 font-mono">60 km/h (16.67 m/s)</span>
                </div>
                <div className="flex justify-between">
                  <span>Signals Encountered:</span>
                  <span className="text-emerald-400 font-semibold">0 (Free Flow)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Traffic Engineering Split Callout */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-white/10 flex items-start gap-3 text-xs text-slate-300">
            <Info size={16} className="text-blue-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white font-semibold">Traffic Assignment Logic:</strong> In alignment with standard Highway Capacity Manual (HCM) grade-separated junction standards, 70% of through movements on Varthur Road take the flyover and 70% of through movements on the Outer Ring Road take the mainline underpass. 100% of turning traffic (including right-turns onto the IT corridor) and the remaining 30% of through movements utilize the surface signalized junction (<span className="font-mono text-amber-300">marathahalli_tls</span>).
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Signal Phasing & Clearance */}
      {activeTab === 'signal_plan' && (
        <div className="space-y-6">
          <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-1">Surface Signal Phasing Machine (<span className="font-mono text-amber-400">marathahalli_tls</span>)</h3>
            <p className="text-xs text-slate-400 mb-6">
              The surface intersection strictly follows the project safety invariant. All phase transitions execute: GREEN → YELLOW (3.0s) → ALL_RED (2.0s) → GREEN (other axis).
            </p>

            <div className="space-y-3">
              {siteData.surface_junction.stages.map((stage, idx) => {
                const isGreen = stage.phase.includes('GREEN');
                const isYellow = stage.phase.includes('YELLOW');
                const isRed = stage.phase.includes('ALL_RED');
                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs ${
                      isGreen
                        ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-100'
                        : isYellow
                        ? 'bg-amber-950/20 border-amber-500/30 text-amber-100'
                        : 'bg-red-950/20 border-red-500/30 text-red-100'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold w-6 text-slate-500">#{idx + 1}</span>
                      <span
                        className={`h-3 w-3 rounded-full shrink-0 ${
                          isGreen ? 'bg-emerald-400 animate-pulse' : isYellow ? 'bg-amber-400' : 'bg-red-400'
                        }`}
                      ></span>
                      <div>
                        <div className="font-semibold text-white">{stage.phase}</div>
                        <div className="text-[11px] text-slate-400">{stage.movements || `${stage.duration_s}s Safe Clearance`}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {stage.duration_s && (
                        <div className="font-mono font-semibold text-slate-300">
                          Duration: {stage.duration_s}s
                        </div>
                      )}
                      <div className="font-mono text-[11px] px-2 py-1 rounded bg-black/40 border border-white/10 tracking-widest text-slate-300">
                        {stage.state_string}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detector Map */}
          <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-1">Queue Length Detectors (SUMO Lane-Area E2)</h3>
            <p className="text-xs text-slate-400 mb-4">
              Real-time queues are measured in meters along the 25-meter approach zones upstream of the stop lines.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {siteData.surface_junction.detectors.map((det) => (
                <div key={det.id} className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <div className="font-mono font-semibold text-amber-300">{det.id}</div>
                  <div className="text-slate-400">Approach: <span className="text-white font-medium">{det.approach}</span> • Lane: <span className="text-white font-mono">{det.lane}</span></div>
                  <div className="text-slate-500 text-[11px]">Span: {det.length_m}m stop-line detection</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Truth & Provenance Matrix */}
      {activeTab === 'provenance' && (
        <div className="space-y-6">
          <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-6 overflow-hidden">
            <h3 className="text-sm font-bold text-white mb-1">Scientific Integrity & Verification Matrix</h3>
            <p className="text-xs text-slate-400 mb-6">
              Following project rules, all assumptions are classified as Verified, Inferred, or Unknown to prevent hallucinations.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900/80 border-b border-white/10 text-slate-400 font-mono text-[11px]">
                  <tr>
                    <th className="py-2.5 px-4">Network Attribute</th>
                    <th className="py-2.5 px-4">Verification Status</th>
                    <th className="py-2.5 px-4">Authoritative Source</th>
                    <th className="py-2.5 px-4">Scientific Grounding Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {siteData.provenance_table.map((row, idx) => {
                    const isVerified = row.status === 'Verified';
                    const isInferred = row.status === 'Inferred';
                    return (
                      <tr key={idx} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-4 font-medium text-white">{row.attribute}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                              isVerified
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : isInferred
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                : 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                            }`}
                          >
                            {row.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-medium">{row.source}</td>
                        <td className="py-3 px-4 text-slate-400">{row.notes}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sources Inventory */}
          <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-3">Grounding Document Inventory</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {siteData.grounding_sources.map((src, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-900 border border-white/5 space-y-1.5 text-xs">
                  <div className="font-bold text-white">{src.name}</div>
                  <div className="text-blue-400 font-mono text-[11px]">{src.type}</div>
                  <div className="text-slate-400 leading-relaxed">{src.detail}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SiteModelView;
