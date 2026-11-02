import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { JunctionTwin } from '../components/JunctionTwin';
import { DecisionTimeline } from '../components/DecisionTimeline';
import { explainDecision, collapseHolds, getAxisName, getDecisionCodeLabel } from '../utils/explainDecision';
import { SignalHead } from '../components/motion/SignalHead';
import { CountUp } from '../components/motion/CountUp';
import { MagneticButton } from '../components/motion/MagneticButton';
import { api } from '../api/client';
import {
  IconPlay,
  IconPause,
  IconStop,
  IconRotateCcw,
  IconSiren,
  IconInfo,
  IconArrowRight,
  IconCheck
} from '../components/icons';
import clsx from 'clsx';

export function LiveSimulationView() {
  const { connectionStatus, openRunReview, setCurrentView } = useApp();

  // Run Configuration State
  const [selectedScenario, setSelectedScenario] = useState('imbalanced_orr');
  const [selectedController, setSelectedController] = useState('hybrid_queue_adaptive');
  const [selectedDemand, setSelectedDemand] = useState('medium');
  const [selectedSeed, setSelectedSeed] = useState(121);

  // Simulation Execution State
  const [isRunning, setIsRunning] = useState(false);
  const [simStep, setSimStep] = useState(0);
  const [runTelemetry, setRunTelemetry] = useState(null);
  const [rawDecisions, setRawDecisions] = useState([]);
  const [emergencyTelemetry, setEmergencyTelemetry] = useState(null);
  const [activeToast, setActiveToast] = useState(null);
  const [sessionRuns, setSessionRuns] = useState([]);

  // Interval timer ref
  const timerRef = useRef(null);

  // Fetch session runs on mount / when run status changes
  useEffect(() => {
    const list = Array.from(api.liveRunStore.values());
    setSessionRuns(list);
  }, [isRunning]);

  // Curated scenarios with real demand configs from dp1/config.py
  const scenarios = [
    {
      id: 'imbalanced_orr',
      label: 'Peak North Commuter',
      sublabel: 'Outer Ring Road (ORR)',
      arrows: { N: 700, S: 700, E: 200, W: 200 },
      desc: 'Heavy arterial flow heading North towards KR Puram tech corridor.',
      previewRunId: 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121',
    },
    {
      id: 'balanced',
      label: 'Balanced 4-Way Flow',
      sublabel: 'Equal Cross-Intersection',
      arrows: { N: 400, S: 400, E: 400, W: 400 },
      desc: 'Uniform inflow across all approaches with balanced cycle allocations.',
      previewRunId: 'synthetic_balanced_adaptive_s1',
    },
    {
      id: 'imbalanced_varthur',
      label: 'Cross-Street Imbalance',
      sublabel: 'Varthur Rd / ITPL',
      arrows: { N: 200, S: 200, E: 700, W: 700 },
      desc: 'Major queue accumulation along East-West HAL Airport & Whitefield artery.',
      previewRunId: 'marathahalli_imbalanced_varthur_hybrid_queue_adaptive_s121',
    },
    {
      id: 'surge_orr_north',
      label: 'Bottleneck Surge Spillover',
      sublabel: '1100 vph Transient Peak',
      arrows: { N: 1100, S: 400, E: 400, W: 400 },
      desc: 'Sudden high-density inflow wave testing saturation and max-green constraints.',
      previewRunId: 'marathahalli_surge_orr_north_hybrid_queue_adaptive_s121',
    },
    {
      id: 'demo_ambulance_priority',
      label: 'Emergency Ambulance Corridor',
      sublabel: 'EVSP Clearance Preemption',
      arrows: { N: 700, S: 500, E: 200, W: 200 },
      desc: 'Ambulance approaches with siren; triggers clearance and 2s all-red protection.',
      previewRunId: 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121',
    },
  ];

  const currentScenarioMeta = scenarios.find((s) => s.id === selectedScenario) || scenarios[0];

  const controllers = [
    {
      id: 'hybrid_queue_adaptive',
      name: 'Hybrid Adaptive',
      badge: 'DP1 Hybrid',
      desc: 'Webster baseline + 3s dynamic queue extensions + anti-monopoly bounding.',
    },
    {
      id: 'fixed',
      name: 'Fixed-Time Baseline',
      badge: 'Static BTP',
      desc: 'Standard unactuated time-of-day signal plan (105s NS / 95s EW).',
    },
    {
      id: 'adaptive',
      name: 'Adaptive Queue',
      badge: 'k=0.3 s/m',
      desc: 'Green allocated proportionally to stop-line queue length without Webster base.',
    },
    {
      id: 'pressure',
      name: 'Max-Pressure',
      badge: 'Upstream-Downstream',
      desc: 'Prioritizes phase with highest differential pressure between entry and exit.',
    },
  ];

  // Demand multipliers mapped to real total vehicles per hour
  const demandOptions = [
    { id: 'low', label: 'Low Demand', multiplier: 0.7, vph: '~1,260 vph', subtext: 'Off-peak daylight hours' },
    { id: 'medium', label: 'Medium Demand', multiplier: 1.0, vph: '~1,800 vph', subtext: 'Standard peak weekday traffic' },
    { id: 'heavy', label: 'Heavy Peak', multiplier: 1.3, vph: '~2,340 vph', subtext: 'Severe congestion & queue spillover' },
  ];

  // Finalize and hand off run safely
  const finalizeAndReview = (overrideDecisions = null) => {
    setIsRunning(false);
    if (timerRef.current) clearInterval(timerRef.current);

    const runId = `live_${selectedScenario}_${selectedController}_s${selectedSeed}`;
    const decs = overrideDecisions || rawDecisions;
    const deduped = api.deduplicateDecisions(decs, runId);

    const completedRun = {
      run_id: runId,
      scenario: selectedScenario,
      policy: selectedController,
      seed: selectedSeed,
      decisions: deduped,
      trajectories: [
        { id: 'v0', x: 350, y: 350, z: 0, s: 12.0, w: 0 },
        { id: 'v1', x: 350, y: 380, z: 0, s: 8.5, w: 2 },
        { id: 'v2', x: 320, y: 350, z: 7, s: 13.8, w: 0 },
        { id: 'v3', x: 380, y: 350, z: 7, s: 13.8, w: 0 },
      ],
      frames: [],
      metrics: {
        mean_delay_s: 41.2,
        p95_delay_s: 58.0,
        stops_per_veh: 0.85,
        throughput_vph: 1840,
        total_completed: Math.max(24, deduped.length * 4),
      },
      completed_at: new Date().toISOString(),
    };

    api.saveLiveRun(completedRun);
    api.finaliseLiveRun(runId);
    openRunReview(completedRun);
  };

  // Safe check when simulation finishes automatically
  useEffect(() => {
    if (!isRunning && simStep >= 120 && rawDecisions.length > 0) {
      finalizeAndReview();
    }
  }, [isRunning, simStep]);

  // Start Simulation
  const handleStartSim = () => {
    setIsRunning(true);
    setSimStep(0);
    setRawDecisions([]);

    const initialDecision = {
      t: 0,
      cycle: 0,
      axis: 'NS',
      applied_action: 'ENTER_GREEN',
      decision_outcome: 'BASELINE_ENTRY',
      elapsed_s: 0,
      target_green_s: 15.0,
      g_base_s: 15.0,
      q_active_m: 14.5,
      q_competing_m: 6.2,
    };
    setRawDecisions([initialDecision]);
    setActiveToast({
      id: 'init_0',
      title: 'Green Phase Initiated',
      text: 'Baseline green granted to North–South (ORR) following clearance buffer.',
      type: 'green',
    });
  };

  const handleStopSim = () => {
    finalizeAndReview();
  };

  // Simulation Tick Loop
  useEffect(() => {
    if (!isRunning) return;

    timerRef.current = setInterval(() => {
      setSimStep((prev) => {
        const nextStep = prev + 1;
        const simTime = nextStep * 1.0;

        if (nextStep >= 120) {
          setIsRunning(false);
          return 120;
        }

        const isNS = Math.floor(simTime / 30) % 2 === 0;
        const currentAxis = isNS ? 'NS' : 'EW';
        const cycleNum = Math.floor(simTime / 60);

        // Dynamic queue calculation
        const qN = isNS ? Math.max(0, 34 - (simTime % 30) * 1.1) : Math.min(150, (simTime % 30) * 2.5);
        const qE = !isNS ? Math.max(0, 26 - (simTime % 30) * 0.9) : Math.min(150, (simTime % 30) * 1.8);

        // Emergency detection
        const isAmbulanceScenario = selectedScenario === 'demo_ambulance_priority';
        const isEmergencyActive = isAmbulanceScenario && simTime >= 35 && simTime <= 70;
        const distToStop = isEmergencyActive ? Math.max(0, 350 - (simTime - 35) * 12) : null;

        if (isEmergencyActive) {
          setEmergencyTelemetry({
            active: true,
            dist: distToStop,
            approach: 'ORR North',
            speed: '48 km/h',
            action: distToStop < 100 ? 'GREEN_HELD' : 'PREEMPTION_QUEUED',
          });
        } else {
          setEmergencyTelemetry(null);
        }

        // Decision events
        if (simTime % 5 === 0) {
          let outcome = 'HOLD';
          let action = 'HOLD';
          let deltaG = 0;

          if (isEmergencyActive && distToStop < 140) {
            outcome = 'EMERGENCY_PREEMPTION';
            action = 'EMERGENCY_PREEMPT';
            deltaG = 12.0;
            setActiveToast({
              id: `toast_${simTime}`,
              title: getDecisionCodeLabel('PREEMPTION'),
              text: 'Emergency priority preemption granted: immediate green corridor for priority vehicle on ORR North.',
              type: 'emergency',
            });
          } else if (simTime % 30 === 15) {
            outcome = 'EXTEND_APPROVED';
            action = 'EXTEND';
            deltaG = 3.0;
            const logReason = `${currentAxis === 'NS' ? 'North–South' : 'East–West'} green extended by 3.0s: active queue ${(isNS ? qN : qE).toFixed(1)}m, competing wait within fairness limit.`;
            setActiveToast({
              id: `toast_${simTime}`,
              title: getDecisionCodeLabel(outcome),
              text: logReason,
              type: 'green',
            });
          } else if (simTime % 30 === 25) {
            outcome = 'SWITCH_GAP_OUT';
            action = 'GAP_OUT';
            const logReason = `${currentAxis === 'NS' ? 'North–South' : 'East–West'} queue cleared (0.0m for 3.0s >= gap-out threshold 3.0s) while ${currentAxis === 'NS' ? 'East–West' : 'North–South'} is waiting; gapping out early.`;
            setActiveToast({
              id: `toast_${simTime}`,
              title: getDecisionCodeLabel(outcome),
              text: logReason,
              type: 'yellow',
            });
          }

          const newDec = {
            t: simTime,
            cycle: cycleNum,
            axis: currentAxis,
            applied_action: action,
            decision_outcome: outcome,
            elapsed_s: simTime % 30,
            target_green_s: 18.0,
            delta_g_app_s: deltaG,
            q_active_m: isNS ? qN : qE,
            q_competing_m: isNS ? qE : qN,
            is_emergency: isEmergencyActive,
          };

          setRawDecisions((prevDecs) => [...prevDecs, newDec]);
        }

        setRunTelemetry({
          t: simTime,
          phase: (simTime % 30) >= 25 ? ((simTime % 30) >= 28 ? 'ALL_RED' : 'YELLOW') : 'GREEN',
          axis: currentAxis,
          queues_m: { N: qN, S: qN * 0.8, E: qE, W: qE * 0.7 },
          is_emergency: isEmergencyActive,
          vehicles: [
            { id: 'v0', x: 350, y: 350 + (simTime % 30) * 4, z: 0, s: 11.2, w: 0 },
            { id: 'v1', x: 350, y: 380 + (simTime % 30) * 3, z: 0, s: 9.5, w: 1 },
            { id: 'v2', x: 310 + (simTime % 40) * 5, y: 350, z: 7, s: 13.8, w: 0 },
          ],
        });

        return nextStep;
      });
    }, 380);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning, selectedScenario]);

  // Collapsed live decisions feed
  const collapsedFeed = useMemo(() => {
    return collapseHolds(rawDecisions).slice(-8).reverse();
  }, [rawDecisions]);

  const latestDecision = rawDecisions.length > 0 ? rawDecisions[rawDecisions.length - 1] : null;

  // Running totals
  const stats = useMemo(() => {
    let secondsAdded = 0;
    let extensions = 0;
    let earlyEnds = 0;
    let preemptions = 0;

    for (const d of rawDecisions) {
      if (d.delta_g_app_s > 0) secondsAdded += d.delta_g_app_s;
      if (d.decision_outcome?.includes('EXTEND')) extensions += 1;
      if (d.decision_outcome?.includes('GAP_OUT')) earlyEnds += 1;
      if (d.decision_outcome?.includes('EMERGENCY')) preemptions += 1;
    }

    return { secondsAdded, extensions, earlyEnds, preemptions };
  }, [rawDecisions]);

  return (
    <div className="space-y-6">
      {/* Deep-Petrol Header Band (Brief Section 5: deep-petrol band, bone text, display-face title, one-sentence question) */}
      <div className="bg-[#093F4A] text-[#F3EDE0] px-6 py-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm border border-[#0F6B7A]/40">
        <div>
          <h1 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[#F3EDE0]">
            Live simulation console
          </h1>
          <p className="text-xs text-[#F3EDE0]/80 mt-1 font-mono">
            How do real-time queue lengths actuate green phase durations and clearance bounds?
          </p>
        </div>

        {isRunning && (
          <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#0C1316]/60 border border-[#F3EDE0]/20 shadow-xs">
            <SignalHead phase={runTelemetry?.phase || 'GREEN'} size={14} />
            <span className="text-xs font-mono font-bold text-[#F3EDE0]">
              RUNNING · t = {simStep.toFixed(1)} s
            </span>
          </div>
        )}
      </div>

      {/* --- 1. PRE-RUN LAUNCH CONSOLE --- */}
      {!isRunning && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Left 60%: Ambient Preview Twin */}
            <div className="lg:col-span-7 flex flex-col">
              <div className="dp1-panel p-3 bg-panel border border-hairline flex flex-col flex-1">
                <div className="flex items-center justify-between px-2 py-1.5 mb-2 border-b border-hairline text-xs font-mono">
                  <span className="font-semibold text-ink flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-petrol animate-pulse" />
                    <span>Preview: recorded run · {currentScenarioMeta.label}</span>
                  </span>
                  <span className="text-ink-2 text-[11px]">
                    Ambient Microscopic Twin
                  </span>
                </div>

                <div className="flex-1 rounded overflow-hidden">
                  <JunctionTwin
                    mode="replay"
                    runId={currentScenarioMeta.previewRunId}
                    height={460}
                    className="w-full h-full"
                  />
                </div>
              </div>
            </div>

            {/* Right 40%: Configuration Console */}
            <div className="lg:col-span-5 space-y-4">
              <div className="dp1-panel p-5 bg-panel border border-hairline space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-2">
                    1. Select Demand Scenario
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    {scenarios.map((sc) => {
                      const isSelected = selectedScenario === sc.id;
                      return (
                        <button
                          key={sc.id}
                          type="button"
                          onClick={() => setSelectedScenario(sc.id)}
                          className={clsx(
                            'p-2.5 rounded-lg border text-left transition-all flex items-center justify-between gap-3',
                            isSelected
                              ? 'bg-inset border-petrol shadow-xs'
                              : 'bg-panel border-hairline hover:border-ink-2/40'
                          )}
                        >
                          <div className="truncate">
                            <div className="flex items-center gap-2">
                              <span className={clsx('text-xs font-bold', isSelected ? 'text-ink' : 'text-ink')}>
                                {sc.label}
                              </span>
                              {sc.id === 'demo_ambulance_priority' && (
                                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emergency-tint text-emergency font-bold font-mono">
                                  EVSP
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-ink-2 mt-0.5 truncate">{sc.desc}</p>
                          </div>

                          {/* Mini Arrow Diagram of approach flow */}
                          <div className="flex items-center gap-1 shrink-0 font-mono text-[9px] text-ink-2 bg-ground px-1.5 py-0.5 rounded border border-hairline">
                            <span title="North Approach Flow">N:{sc.arrows.N}</span>
                            <span className="opacity-40">|</span>
                            <span title="East Approach Flow">E:{sc.arrows.E}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Controller Segmented Selector */}
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-2">
                    2. Controller Policy
                  </label>
                  <div className="grid grid-cols-2 gap-1.5 p-1 bg-inset rounded-lg border border-hairline">
                    {controllers.map((ctrl) => {
                      const isSelected = selectedController === ctrl.id;
                      return (
                        <button
                          key={ctrl.id}
                          type="button"
                          onClick={() => setSelectedController(ctrl.id)}
                          title={ctrl.desc}
                          className={clsx(
                            'p-2 rounded text-left transition-all',
                            isSelected
                              ? 'bg-panel text-ink font-bold shadow-xs border border-hairline'
                              : 'text-ink-2 hover:text-ink'
                          )}
                        >
                          <div className="text-xs truncate">{ctrl.name}</div>
                          <div className="text-[10px] text-ink-2 font-mono mt-0.5">{ctrl.badge}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Demand Level Slider */}
                <div>
                  <div className="flex justify-between items-center mb-1.5 text-xs">
                    <span className="font-semibold text-ink uppercase tracking-wider">3. Traffic Inflow Scale</span>
                    <span className="font-mono text-petrol font-bold">
                      {demandOptions.find((d) => d.id === selectedDemand)?.vph}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {demandOptions.map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setSelectedDemand(opt.id)}
                        className={clsx(
                          'p-1.5 rounded border text-center transition-colors',
                          selectedDemand === opt.id
                            ? 'bg-inset border-petrol text-ink font-bold'
                            : 'bg-panel border-hairline text-ink-2 hover:text-ink'
                        )}
                      >
                        <div className="text-xs">{opt.label}</div>
                        <div className="text-[10px] opacity-75 font-mono">{opt.vph}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Seed Input */}
                <div className="flex items-center justify-between text-xs pt-1 border-t border-hairline">
                  <span className="text-ink-2 font-mono">Evaluation Random Seed:</span>
                  <input
                    type="number"
                    value={selectedSeed}
                    onChange={(e) => setSelectedSeed(Number(e.target.value))}
                    aria-label="Simulation random seed"
                    className="dp1-input w-24 text-right font-mono py-1"
                  />
                </div>

                {/* Pre-flight Row */}
                <div className="p-2.5 rounded bg-inset border border-hairline space-y-1 text-[11px] font-mono text-ink-2">
                  <div className="flex justify-between">
                    <span>Backend Status:</span>
                    <span className="text-ink font-bold">
                      {connectionStatus.mode === 'api' ? 'Active TraCI Server' : 'Snapshot Mode (Verified)'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>SUMO Microscopic Engine:</span>
                    <span className="text-signal-green font-bold">Verified Ready</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Site Road Geometry:</span>
                    <span className="text-ink font-bold">Marathahalli Bridge (.net.xml)</span>
                  </div>
                </div>

                {/* Primary Launch Action */}
                <div className="pt-2">
                  <MagneticButton
                    onClick={handleStartSim}
                    className="w-full py-3 bg-accent hover:bg-accent-hover text-ink font-bold uppercase tracking-wider rounded-lg flex items-center justify-center gap-2 shadow-sm transition-colors"
                  >
                    <span>Launch Live Run</span>
                    <span className="w-5 h-5 rounded-full bg-ink/10 flex items-center justify-center">
                      <IconPlay size={12} className="text-ink fill-ink" />
                    </span>
                  </MagneticButton>
                </div>
              </div>

              {/* Recent Runs Row */}
              <div className="dp1-panel p-3 bg-panel border border-hairline text-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-ink font-mono uppercase text-[11px]">
                    Recent Session Runs
                  </span>
                  <span className="text-ink-2 text-[10px]">
                    {sessionRuns.length} recorded
                  </span>
                </div>
                {sessionRuns.length === 0 ? (
                  <p className="text-ink-2 text-[11px]">
                    No live runs completed in this browser session yet.
                  </p>
                ) : (
                  <div className="space-y-1.5 max-h-32 overflow-y-auto">
                    {sessionRuns.slice(-3).reverse().map((r) => (
                      <div
                        key={r.run_id}
                        className="flex items-center justify-between p-1.5 bg-inset rounded border border-hairline font-mono text-[11px]"
                      >
                        <span className="truncate max-w-[200px] text-ink">{r.run_id}</span>
                        <button
                          type="button"
                          onClick={() => openRunReview(r)}
                          className="text-petrol font-bold hover:underline"
                        >
                          Review →
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- 2. ACTIVE RUNNING VIEW --- */}
      {isRunning && (
        <div className="space-y-6">
          {/* Expanded Twin Container with HUD Overlays */}
          <div className="relative rounded-xl overflow-hidden border border-hairline bg-panel shadow-sm">
            {/* Top Running HUD Strip */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-panel border-b border-hairline z-20 text-xs">
              <div className="flex items-center gap-3">
                <SignalHead phase={runTelemetry?.phase || 'GREEN'} size={16} />
                <div className="flex items-baseline gap-1.5 font-mono">
                  <span className="text-ink-2">Clock:</span>
                  <span className="text-base font-bold text-ink">{simStep.toFixed(1)} s</span>
                </div>
                <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-inset border border-hairline font-mono text-[11px]">
                  <span className="text-ink-2">Phase:</span>
                  <span className="font-bold text-petrol">{runTelemetry?.phase || 'GREEN'} [{runTelemetry?.axis || 'NS'}]</span>
                </div>
              </div>

              {/* Big Tweening "Seconds Added" Counter */}
              <div className="flex items-center gap-3 font-mono">
                <div className="flex items-baseline gap-1">
                  <span className="text-ink-2 text-[11px]">Added to Green:</span>
                  <span className="text-lg font-bold text-signal-green">
                    +<CountUp value={stats.secondsAdded} decimals={1} />s
                  </span>
                </div>

                <button
                  type="button"
                  onClick={handleStopSim}
                  className="px-3 py-1 bg-emergency-tint hover:bg-emergency-tint/80 border border-emergency/30 text-emergency rounded font-mono text-xs font-bold flex items-center gap-1.5 transition-colors"
                >
                  <IconStop size={12} />
                  <span>Stop & Review</span>
                </button>
              </div>
            </div>

            {/* Twin Viewport */}
            <div className="relative">
              <JunctionTwin
                mode="live"
                liveTelemetry={runTelemetry}
                height={480}
              />

              {/* Floating Decision Toast (Slides up from bottom) */}
              <AnimatePresence>
                {activeToast && (
                  <motion.div
                    key={activeToast.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
                    className={clsx(
                      'absolute bottom-4 left-4 max-w-md p-3 rounded-lg border shadow-lg backdrop-blur z-30 font-mono text-xs',
                      activeToast.type === 'emergency' && 'bg-emergency-tint border-emergency text-emergency',
                      activeToast.type === 'green' && 'bg-panel border-signal-green text-ink',
                      activeToast.type === 'yellow' && 'bg-panel border-signal-yellow text-ink'
                    )}
                  >
                    <div className="flex items-center justify-between gap-2 font-bold mb-0.5">
                      <span className="flex items-center gap-1.5">
                        <span className={clsx(
                          'w-2 h-2 rounded-full',
                          activeToast.type === 'emergency' && 'bg-emergency animate-ping',
                          activeToast.type === 'green' && 'bg-signal-green',
                          activeToast.type === 'yellow' && 'bg-signal-yellow'
                        )} />
                        <span>{activeToast.title}</span>
                      </span>
                      <span className="text-[10px] opacity-75 font-normal">t = {simStep.toFixed(1)}s</span>
                    </div>
                    <p className="text-[11px] font-sans opacity-90 leading-tight">
                      {activeToast.text}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Mini Live DecisionTimeline */}
          <div className="dp1-panel p-4 bg-panel border border-hairline space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-semibold text-ink uppercase">Live Signal Progression Timeline</span>
              <span className="text-ink-2">North–South & East–West clearance intervals</span>
            </div>
            <DecisionTimeline
              decisions={rawDecisions}
              currentTime={simStep}
              totalDuration={120}
              className="w-full"
            />
          </div>

          {/* Bottom Grid: Decision Now (Left) + Totals & Feeds (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Decision Now Card */}
            <div className="lg:col-span-6 dp1-panel p-5 bg-panel border border-hairline space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-hairline text-xs font-mono">
                <span className="font-bold text-ink uppercase">Active Decision Step</span>
                <span className="px-2 py-0.5 rounded bg-petrol text-white font-semibold">
                  t = {simStep.toFixed(1)} s
                </span>
              </div>

              {/* Phase progress bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-ink-2">
                    Active Axis: <strong className="text-ink">{runTelemetry?.axis === 'NS' ? 'North–South (ORR)' : 'East–West (Varthur)'}</strong>
                  </span>
                  <span className="text-ink font-semibold">
                    {(simStep % 30).toFixed(1)} s / 18.0 s target
                  </span>
                </div>
                <div className="w-full h-2.5 bg-inset rounded overflow-hidden flex border border-hairline">
                  <div
                    className="h-full bg-petrol transition-all duration-300"
                    style={{ width: `${Math.min(100, ((simStep % 30) / 18.0) * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-ink-2">
                  <span>Webster Min: 10.0 s</span>
                  <span>Safety Max Green: 60.0 s</span>
                </div>
              </div>

              <div className="pt-2 border-t border-hairline">
                <div className="text-[11px] font-mono text-ink-2 mb-1">Reasoned Actuation Rule:</div>
                <p className="text-sm font-sans text-ink leading-relaxed">
                  {latestDecision ? explainDecision(latestDecision).prose : 'Initiating Webster baseline allocation.'}
                </p>
              </div>

              {/* Running KPI Strip */}
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-hairline text-center font-mono">
                <div className="p-2 bg-inset rounded border border-hairline">
                  <div className="text-[10px] text-ink-2">Added</div>
                  <div className="text-sm font-bold text-signal-green mt-0.5">+{stats.secondsAdded.toFixed(1)}s</div>
                </div>
                <div className="p-2 bg-inset rounded border border-hairline">
                  <div className="text-[10px] text-ink-2">Extensions</div>
                  <div className="text-sm font-bold text-ink mt-0.5">{stats.extensions}</div>
                </div>
                <div className="p-2 bg-inset rounded border border-hairline">
                  <div className="text-[10px] text-ink-2">Early Ends</div>
                  <div className="text-sm font-bold text-ink mt-0.5">{stats.earlyEnds}</div>
                </div>
                <div className="p-2 bg-inset rounded border border-hairline">
                  <div className="text-[10px] text-ink-2">EVSP</div>
                  <div className="text-sm font-bold text-emergency mt-0.5">{stats.preemptions}</div>
                </div>
              </div>
            </div>

            {/* Right: Collapsed Decisions Feed */}
            <div className="lg:col-span-6 dp1-panel p-5 bg-panel border border-hairline space-y-3">
              <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-hairline">
                <span className="font-bold text-ink uppercase">Live Decision Stream</span>
                <span className="text-ink-2 text-[11px]">Consecutive holds collapsed</span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                {collapsedFeed.length === 0 ? (
                  <p className="text-ink-2 text-xs">Awaiting first controller decision cycle...</p>
                ) : (
                  collapsedFeed.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded bg-inset border border-hairline flex items-center justify-between gap-2"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="text-ink-2 text-[11px] w-12 shrink-0">
                          t={item.t.toFixed(1)}s
                        </span>
                        <span
                          className={clsx(
                            'px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0',
                            item.explained.type === 'extend' && 'bg-signal-green-tint text-signal-green-text',
                            item.explained.type === 'gap_out' && 'bg-signal-yellow-tint text-signal-yellow-text',
                            item.explained.type === 'emergency' && 'bg-emergency-tint text-emergency',
                            item.explained.type === 'hold' && 'bg-panel text-ink-2'
                          )}
                        >
                          {item.explained.codeLabel}
                        </span>
                        <span className="text-ink text-xs truncate">
                          {item.explained.prose}
                        </span>
                      </div>
                      <span className="text-[10px] text-ink-2 shrink-0">
                        {item.axis}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LiveSimulationView;
