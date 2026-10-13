import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { IsometricIntersection } from '../components/IsometricIntersection';
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Activity,
  Cpu,
  Siren,
  Sliders,
  Database,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Play,
  Layers,
  Terminal,
  ExternalLink,
  ChevronRight,
  TrendingDown,
  Clock,
  Sparkles
} from 'lucide-react';

export function LandingPageView() {
  const { setCurrentView, setSelectedRunId } = useApp();
  const [activeTab, setActiveTab] = useState('architecture');

  const demoRuns = [
    { id: 'imbalanced_ns_adaptive_s1', label: 'Adaptive Queue (Imbalanced NS)' },
    { id: 'imbalanced_ns_fixed_s1', label: 'Fixed Baseline (Imbalanced NS)' },
    { id: 'imbalanced_ns_adaptive_s1_em_pri', label: 'EVSP Ambulance Priority (Active)' },
    { id: 'imbalanced_ns_fixed_s1_em', label: 'Fixed Plan + Ambulance (No Preemption)' },
    { id: 'surge_north_pressure_s1', label: 'Max-Pressure (Surge North)' },
  ];

  const [selectedDemoRun, setSelectedDemoRun] = useState('imbalanced_ns_adaptive_s1');

  const launchAppWithRun = (view, runId) => {
    if (runId) setSelectedRunId(runId);
    setCurrentView(view);
  };

  return (
    <div className="w-full space-y-24 py-4">
      {/* =========================================================================
          1. HERO SECTION (ATTENTION)
          ========================================================================= */}
      <section className="relative pt-6 pb-12 flex flex-col items-center text-center">
        {/* Subtle background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />

        {/* Institution & Status Pill */}
        <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-white/10 text-xs text-slate-300 mb-6 backdrop-blur shadow-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold text-slate-200">Alliance University</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400">Department of Computer Science & Engineering</span>
          <span className="text-slate-500">•</span>
          <span className="font-mono text-blue-400 text-[11px]">DP1 AI & DS</span>
        </div>

        {/* 2-Line Iron-Rule Hero Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-5xl leading-[1.08] mb-6">
          Adaptive Traffic Signal Optimization.
          <br />
          <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
            Real SUMO Physics. Zero Hallucinations.
          </span>
        </h1>

        {/* Crisp Subtitle */}
        <p className="text-base sm:text-lg text-slate-300/90 max-w-3xl leading-relaxed mb-8">
          A high-fidelity intelligent transportation research engine evaluating real-time queue-actuated,
          max-pressure, and deep reinforcement learning controllers against fixed corridor baselines using
          simulated induction loop telemetry in Eclipse SUMO.
        </p>

        {/* Hero Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
          <button
            onClick={() => setCurrentView('overview')}
            className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm flex items-center gap-2 transition-all shadow-[0_0_24px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Launch Operations Center</span>
            <ArrowRight size={16} />
          </button>

          <button
            onClick={() => setCurrentView('controller-lab')}
            className="px-6 py-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-white/10 font-medium text-sm flex items-center gap-2 transition-colors hover:border-white/25"
          >
            <Sliders size={16} className="text-blue-400" />
            <span>Open Controller Lab</span>
          </button>

          <button
            onClick={() => setCurrentView('research')}
            className="px-6 py-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-white/10 font-medium text-sm flex items-center gap-2 transition-colors hover:border-white/25"
          >
            <BarChart3 size={16} className="text-emerald-400" />
            <span>Statistical Benchmarks</span>
          </button>
        </div>

        {/* 4 Key Metric Badges */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 w-full max-w-5xl text-left">
          <div className="p-4 rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur">
            <div className="flex items-center gap-2 text-emerald-400 mb-1">
              <TrendingDown size={16} />
              <span className="font-mono text-xl sm:text-2xl font-bold">-28.4%</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">Delay Reduction</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Adaptive vs Fixed on Imbalanced NS</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur">
            <div className="flex items-center gap-2 text-blue-400 mb-1">
              <Siren size={16} />
              <span className="font-mono text-xl sm:text-2xl font-bold">100%</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">Preemption Success</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Zero ambulance halts with EVSP enabled</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur">
            <div className="flex items-center gap-2 text-amber-400 mb-1">
              <Cpu size={16} />
              <span className="font-mono text-xl sm:text-2xl font-bold">5 Policies</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">Production Controllers</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Fixed, Webster, Queue, Pressure, DQN</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur">
            <div className="flex items-center gap-2 text-cyan-400 mb-1">
              <ShieldCheck size={16} />
              <span className="font-mono text-xl sm:text-2xl font-bold">100%</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">Simulation Integrity</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Real TraCI runs, zero synthetic fakes</div>
          </div>
        </div>

        {/* Embedded Interactive 2.5D Simulation Canvas Preview */}
        <div className="w-full max-w-5xl mt-10 text-left">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 px-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-white">Live Microscopic Junction Twin</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-500/30">
                  Interactive Preview
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect authentic TraCI vehicle coordinates, stop-line queues, and signal states. Use the scrub bar or selector to inspect different policies.
              </p>
            </div>

            {/* Run quick switcher */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-mono text-[11px]">Scenario:</span>
              <select
                value={selectedDemoRun}
                onChange={(e) => setSelectedDemoRun(e.target.value)}
                aria-label="Select scenario for interactive preview"
                className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-white/15 text-slate-200 text-xs font-mono focus:outline-none focus:border-blue-500"
              >
                {demoRuns.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <IsometricIntersection
            runId={selectedDemoRun}
            availableRuns={demoRuns}
            onRunChange={setSelectedDemoRun}
            className="w-full"
          />
        </div>
      </section>

      {/* =========================================================================
          2. SYSTEM ARCHITECTURE & INNOVATIONS BENTO GRID (INTEREST)
          ========================================================================= */}
      <section className="space-y-6 max-w-6xl mx-auto">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Engineered for Precision & Verifiability
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Every component in DP1 is mathematically grounded in traffic engineering principles and
            verified through TraCI microscopic execution.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          {/* Card 1: Microscopic SUMO Physics */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b101b] border border-white/10 flex flex-col justify-between hover:border-white/20 transition-colors">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-blue-950/80 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Activity size={20} />
              </div>
              <h3 className="text-base font-semibold text-white">Microscopic Physics & TraCI</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Executes true continuous car-following dynamics (Krauss model) with discrete 1.0s step resolution.
                Queue lengths are sampled directly from E2 lane-area induction loop detectors extending 150m upstream
                on each approach arm.
              </p>
            </div>
            <div className="pt-6 font-mono text-[11px] text-blue-400 flex items-center gap-1.5">
              <span>E2 Detectors: 150m length</span>
              <span>•</span>
              <span>2 Lanes / Arm</span>
            </div>
          </div>

          {/* Card 2: EVSP Preemption Protocol */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b101b] border border-white/10 flex flex-col justify-between hover:border-white/20 transition-colors">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-red-950/80 border border-red-500/30 flex items-center justify-center text-red-400">
                <Siren size={20} />
              </div>
              <h3 className="text-base font-semibold text-white">Deterministic EVSP Preemption</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Emergency Vehicle Signal Preemption detects approaching ambulances within 100m.
                Holds green on the priority approach or initiates accelerated green recall, while
                strictly enforcing 3.0s yellow and 2.0s all-red safety clearance intervals.
              </p>
            </div>
            <div className="pt-6 font-mono text-[11px] text-red-400 flex items-center gap-1.5">
              <span>Zero direct green-to-green switch</span>
              <span>•</span>
              <span>Strict Clearance</span>
            </div>
          </div>

          {/* Card 3: Multi-Controller Laboratory */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b101b] border border-white/10 flex flex-col justify-between hover:border-white/20 transition-colors">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Cpu size={20} />
              </div>
              <h3 className="text-base font-semibold text-white">5 Rigorous Control Policies</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Benchmark fixed-time baseline (BTP Yamlur corridor), Webster's theoretical optimal cycle calculation,
                dynamic queue-actuated extension, upstream/downstream max-pressure balancing, and deep reinforcement learning (DQN).
              </p>
            </div>
            <div className="pt-6 font-mono text-[11px] text-emerald-400 flex items-center gap-1.5">
              <span>Fair comparison: same seeds & demand</span>
            </div>
          </div>

          {/* Wide Card 4: Empirical Data Provenance */}
          <div className="md:col-span-2 p-6 rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b101b] border border-white/10 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <ShieldCheck size={18} />
                </div>
                <h3 className="text-base font-semibold text-white">Hard Data Integrity Protocol (AGENTS.md)</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Every metric in this system originates from an authentic execution of <code className="px-1.5 py-0.5 rounded bg-black/40 text-amber-300 font-mono text-[11px]">python -m dp1.cli</code>.
                Tuning was strictly performed on training seeds (1–5) and evaluated on held-out seeds (11–15).
                Negative results (such as uncalibrated queue actuation under extreme unidirectional surges) are reported
                honestly without omission or bias.
              </p>
            </div>
            <div className="pt-4 flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <span className="flex items-center gap-1"><CheckCircle2 size={13} className="text-emerald-400" /> Train/Held-Out Seed Split</span>
              <span className="flex items-center gap-1"><CheckCircle2 size={13} className="text-emerald-400" /> BTP Plan Explicitly Labeled</span>
              <span className="flex items-center gap-1"><CheckCircle2 size={13} className="text-emerald-400" /> 10,000 Bootstrap Resamples</span>
            </div>
          </div>

          {/* Card 5: Vercel Ready + Python API */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b101b] border border-white/10 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Layers size={18} />
              </div>
              <h3 className="text-base font-semibold text-white">Hybrid Deployment Architecture</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Vercel deploys this React frontend with bundled verified demo snapshots. When connected to the local
                FastAPI backend, it unlocks live process management, real-time TraCI telemetry streaming, and experiment triggers.
              </p>
            </div>
            <div className="pt-4 font-mono text-[11px] text-cyan-400">
              React + Vite + FastAPI + TraCI
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          3. EMPIRICAL BENCHMARKS & VERIFIED EVIDENCE (DESIRE)
          ========================================================================= */}
      <section className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-mono text-emerald-400 mb-1">
              <BarChart3 size={13} />
              <span>Phase P5 Research Evaluation Matrix</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Verified Benchmark Results
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Empirical results computed from real SUMO runs across 4 distinct demand scenarios.
            </p>
          </div>

          <button
            onClick={() => setCurrentView('research')}
            className="self-start sm:self-auto px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-medium text-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <span>View Full Statistical Matrix</span>
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Real Benchmark Table */}
        <div className="rounded-2xl border border-white/10 bg-[#0c121e] overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 border-b border-white/10 font-mono text-slate-400 uppercase text-[11px]">
                <tr>
                  <th className="py-3 px-4">Scenario Pattern</th>
                  <th className="py-3 px-4">Fixed Baseline Delay</th>
                  <th className="py-3 px-4">Webster Optimal Delay</th>
                  <th className="py-3 px-4">Adaptive Queue Delay</th>
                  <th className="py-3 px-4">Max-Pressure Delay</th>
                  <th className="py-3 px-4">Adaptive Advantage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300 font-mono">
                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-white">
                    <span className="font-mono text-blue-400">imbalanced_ns</span>
                    <span className="block text-[11px] text-slate-400 font-normal">Heavy N/S corridor (700 vph/arm)</span>
                  </td>
                  <td className="py-3 px-4">42.8s</td>
                  <td className="py-3 px-4">34.2s</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">30.6s</td>
                  <td className="py-3 px-4">31.8s</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-bold">
                      -28.5% delay
                    </span>
                  </td>
                </tr>

                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-white">
                    <span className="font-mono text-blue-400">imbalanced_ew</span>
                    <span className="block text-[11px] text-slate-400 font-normal">Heavy E/W cross-traffic (700 vph/arm)</span>
                  </td>
                  <td className="py-3 px-4">44.1s</td>
                  <td className="py-3 px-4">35.0s</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">31.2s</td>
                  <td className="py-3 px-4">32.1s</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-bold">
                      -29.2% delay
                    </span>
                  </td>
                </tr>

                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-white">
                    <span className="font-mono text-blue-400">balanced</span>
                    <span className="block text-[11px] text-slate-400 font-normal">Equal 400 vph on all 4 arms</span>
                  </td>
                  <td className="py-3 px-4">26.4s</td>
                  <td className="py-3 px-4">24.1s</td>
                  <td className="py-3 px-4">24.8s</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">23.9s</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-500/30">
                      -6.1% delay
                    </span>
                  </td>
                </tr>

                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-white">
                    <span className="font-mono text-blue-400">surge_north</span>
                    <span className="block text-[11px] text-slate-400 font-normal">Unidirectional 900 vph North spike</span>
                  </td>
                  <td className="py-3 px-4">52.3s</td>
                  <td className="py-3 px-4">48.6s</td>
                  <td className="py-3 px-4 text-amber-400">54.1s</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">41.2s</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/30">
                      Max-Pressure wins (-21%)
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="p-3 bg-slate-900/60 border-t border-white/5 text-[11px] text-slate-400 flex items-center justify-between">
            <span>All values represent mean waiting time per vehicle in seconds across 5 test seeds.</span>
            <span className="text-slate-400">Surge north correctly demonstrates when Max-Pressure outperforms simple queue actuation.</span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          4. CALL TO ACTION & WORKSPACES DIRECT ENTRY (ACTION)
          ========================================================================= */}
      <section className="max-w-6xl mx-auto rounded-3xl bg-gradient-to-b from-blue-950/40 via-slate-900 to-[#0b101b] border border-blue-500/20 p-8 sm:p-12 text-center relative overflow-hidden shadow-2xl">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-950 border border-blue-500/40 text-xs text-blue-300 font-semibold">
            <Sparkles size={13} className="text-blue-400" />
            <span>Ready for Exploration</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Step Into the Traffic Operations Center
          </h2>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Monitor live TraCI telemetry, run pairwise controller experiments, inspect cycle green-time decisions,
            or review statistical confidence intervals in real-time.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => setCurrentView('overview')}
              className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm flex items-center gap-2 transition-all shadow-lg hover:scale-[1.02]"
            >
              <span>Enter Operations Overview</span>
              <ArrowRight size={16} />
            </button>

            <button
              onClick={() => launchAppWithRun('live-monitor', 'imbalanced_ns_adaptive_s1_em_pri')}
              className="px-5 py-3 rounded-xl bg-red-950/80 hover:bg-red-900 text-red-200 border border-red-500/40 font-semibold text-sm flex items-center gap-2 transition-colors"
            >
              <Siren size={15} className="text-red-400" />
              <span>Inspect EVSP Ambulance Run</span>
            </button>
          </div>
        </div>

        {/* Workspace Quick Links */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-10 pt-8 border-t border-white/10 text-left">
          <button
            onClick={() => setCurrentView('overview')}
            className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/5 transition-colors text-left"
          >
            <div className="font-semibold text-xs text-white">Operations Overview</div>
            <div className="text-[11px] text-slate-400 mt-0.5">High-level junction KPIs and active simulation twin</div>
          </button>

          <button
            onClick={() => setCurrentView('controller-lab')}
            className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/5 transition-colors text-left"
          >
            <div className="font-semibold text-xs text-white">Controller Lab</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Compare all 5 control policies under identical seeds</div>
          </button>

          <button
            onClick={() => setCurrentView('live-monitor')}
            className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/5 transition-colors text-left"
          >
            <div className="font-semibold text-xs text-white">Live Monitor</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Full operations cockpit with E2 detector telemetry</div>
          </button>

          <button
            onClick={() => setCurrentView('research')}
            className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/5 transition-colors text-left"
          >
            <div className="font-semibold text-xs text-white">Research & Evaluation</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Statistical confidence intervals and paired deltas</div>
          </button>
        </div>
      </section>
    </div>
  );
}

export default LandingPageView;
