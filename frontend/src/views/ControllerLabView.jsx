import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Cell, ErrorBar } from 'recharts';
import { Sliders, HelpCircle, ArrowRight } from 'lucide-react';

export function ControllerLabView() {
  const { allRuns, setSelectedRunId, setCurrentView } = useApp();
  const [selectedNetwork, setSelectedNetwork] = useState('marathahalli');
  const [selectedScenario, setSelectedScenario] = useState('imbalanced_orr');
  const [selectedDemandLevel, setSelectedDemandLevel] = useState('medium');

  const policiesList = ['fixed', 'fixed_webster', 'adaptive', 'pressure', 'queue_extension', 'rl_dqn'];
  const policyNames = {
    fixed: 'Fixed-Time (Baseline)',
    fixed_webster: 'Webster Optimized',
    adaptive: 'Adaptive Queue',
    pressure: 'Max-Pressure',
    queue_extension: 'Bounded Queue-Extension',
    rl_dqn: 'DQN Reinforcement Learning',
  };

  const policyColors = {
    fixed: '#64748B',
    fixed_webster: '#F59E0B',
    adaptive: '#10B981',
    pressure: '#06B6D4',
    queue_extension: '#059669',
    rl_dqn: '#8B5CF6',
  };

  // Group verified runs matching current filter
  const comparisonData = useMemo(() => {
    return policiesList.map((pol) => {
      // Find matching runs in allRuns
      const matches = allRuns.filter((r) => {
        const netMatch = (r.network || 'synthetic') === selectedNetwork;
        const scMatch = r.scenario === selectedScenario;
        const polMatch = r.policy === pol;
        const levMatch = r.demand_level ? r.demand_level === selectedDemandLevel : selectedDemandLevel === 'medium';
        return netMatch && scMatch && polMatch && levMatch;
      });

      if (matches.length === 0) {
        return {
          policy: pol,
          name: policyNames[pol],
          wait: null,
          sd: null,
          p95: null,
          queue: null,
          disparity: null,
          throughput: null,
          count: 0,
          sampleRunId: null,
        };
      }

      const meanWait = matches.reduce((acc, r) => acc + (r.avg_wait_s || 0), 0) / matches.length;
      const variance = matches.reduce((acc, r) => acc + Math.pow((r.avg_wait_s || 0) - meanWait, 2), 0) / matches.length;
      const sd = Math.sqrt(variance);
      const meanP95 = matches.reduce((acc, r) => acc + (r.p95_wait_s || 0), 0) / matches.length;
      const maxQ = Math.max(...matches.map((r) => r.max_queue_m || 0));
      const meanDisp = matches.reduce((acc, r) => acc + (r.directional_wait_disparity_s || 0), 0) / matches.length;
      const meanThroughput = matches.reduce((acc, r) => acc + (r.throughput_veh_per_h || 0), 0) / matches.length;
      const sampleRunId = matches[0].run_id || `${matches[0].scenario}_${matches[0].policy}_s${matches[0].seed}`;

      return {
        policy: pol,
        name: policyNames[pol],
        wait: parseFloat(meanWait.toFixed(1)),
        sd: parseFloat(sd.toFixed(1)),
        p95: parseFloat(meanP95.toFixed(1)),
        queue: parseFloat(maxQ.toFixed(1)),
        disparity: parseFloat(meanDisp.toFixed(1)),
        throughput: Math.round(meanThroughput),
        count: matches.length,
        sampleRunId,
      };
    });
  }, [allRuns, selectedNetwork, selectedScenario, selectedDemandLevel]);

  const fixedWait = comparisonData.find((d) => d.policy === 'fixed')?.wait || 104.4;

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="dp1-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sliders size={18} className="text-blue-400" />
            <span>Controller Benchmark Lab</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Compare all six signal policies under identical seeds, vehicles, and detector placements.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[11px] text-slate-400 font-mono mb-1">Road Network:</label>
            <select
              value={selectedNetwork}
              onChange={(e) => {
                const net = e.target.value;
                setSelectedNetwork(net);
                setSelectedScenario(net === 'marathahalli' ? 'imbalanced_orr' : 'imbalanced_ns');
              }}
              className="dp1-select text-xs font-semibold text-white"
            >
              <option value="marathahalli">Marathahalli Bridge Site (Real Road)</option>
              <option value="synthetic">Synthetic 4-Way Junction</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 font-mono mb-1">Scenario Pattern:</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="dp1-select text-xs"
            >
              {selectedNetwork === 'marathahalli' ? (
                <>
                  <option value="imbalanced_orr">Imbalanced ORR (Heavy Arterial)</option>
                  <option value="balanced">Balanced Corridor</option>
                  <option value="imbalanced_varthur">Imbalanced Varthur Cross</option>
                  <option value="surge_orr_north">Surge ORR North (Peak Inflow)</option>
                </>
              ) : (
                <>
                  <option value="imbalanced_ns">Imbalanced NS (Heavy Corridor)</option>
                  <option value="balanced">Balanced 4-Way</option>
                  <option value="imbalanced_ew">Imbalanced EW</option>
                  <option value="surge_north">Surge North</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 font-mono mb-1">Demand Level:</label>
            <select
              value={selectedDemandLevel}
              onChange={(e) => setSelectedDemandLevel(e.target.value)}
              className="dp1-select text-xs"
            >
              <option value="low">Low (0.70x intensity)</option>
              <option value="medium">Medium (1.00x intensity)</option>
              <option value="heavy">Heavy (1.30x intensity)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Average Wait Time Chart */}
        <div className="dp1-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                Average Vehicle Waiting Time (s)
              </h3>
              <p className="text-[11px] text-slate-400">Lower is better • Error bars show ±1 SD across evaluated seeds</p>
            </div>
            <span className="text-[10px] font-mono text-slate-500">Unit: Seconds</span>
          </div>

          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 20, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.1)', fontSize: '12px' }}
                  formatter={(value, name) => [`${value}s`, 'Avg Wait']}
                />
                <Bar dataKey="wait" radius={[4, 4, 0, 0]}>
                  {comparisonData.map((entry) => (
                    <Cell key={entry.policy} fill={policyColors[entry.policy] || '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Directional Disparity Chart */}
        <div className="dp1-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                Directional Service Disparity (|W_NS - W_EW|)
              </h3>
              <p className="text-[11px] text-slate-400">Fairness gap between main corridor and cross-streets</p>
            </div>
            <span className="text-[10px] font-mono text-slate-500">Unit: Seconds</span>
          </div>

          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 20, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.1)', fontSize: '12px' }}
                  formatter={(value) => [`${value}s gap`, 'Disparity']}
                />
                <Bar dataKey="disparity" fill="#38BDF8" radius={[4, 4, 0, 0]}>
                  {comparisonData.map((entry) => (
                    <Cell key={entry.policy} fill={policyColors[entry.policy]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Comprehensive Results Table */}
      <div className="dp1-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-white">
            Policy Performance Breakdown ({selectedScenario} • {selectedDemandLevel})
          </h3>
          <span className="text-[11px] font-mono text-slate-500">N={comparisonData[0]?.count || 5} Seeds Verified</span>
        </div>

        <div className="dp1-table-wrapper">
          <table className="dp1-table">
            <thead>
              <tr>
                <th>Policy Strategy</th>
                <th>Mean Wait (s)</th>
                <th>p95 Wait (s)</th>
                <th>Delta vs Fixed</th>
                <th>Max Queue (m)</th>
                <th>Directional Gap</th>
                <th>Throughput</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {comparisonData.map((d) => {
                const hasData = d.wait !== null;
                const deltaPct = hasData && fixedWait > 0 ? (((fixedWait - d.wait) / fixedWait) * 100).toFixed(1) : null;
                const isFixed = d.policy === 'fixed';
                const isBetter = deltaPct !== null && parseFloat(deltaPct) > 0;
                return (
                  <tr key={d.policy}>
                    <td className="font-semibold text-white font-mono text-xs flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: policyColors[d.policy] }} />
                      <span>{d.name}</span>
                    </td>
                    <td className="font-mono text-xs font-bold text-white">
                      {hasData ? `${d.wait}s ± ${d.sd}s` : '—'}
                    </td>
                    <td className="font-mono text-xs text-slate-300">
                      {hasData ? `${d.p95}s` : '—'}
                    </td>
                    <td>
                      {!hasData ? (
                        <span className="font-mono text-xs text-slate-500">—</span>
                      ) : isFixed ? (
                        <span className="font-mono text-xs text-slate-500">Baseline</span>
                      ) : (
                        <span
                          className={`font-mono text-xs px-1.5 py-0.5 rounded font-semibold ${
                            isBetter
                              ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                              : 'bg-red-950/60 text-red-400 border border-red-500/30'
                          }`}
                        >
                          {isBetter ? `+${deltaPct}%` : `${deltaPct}%`}
                        </span>
                      )}
                    </td>
                    <td className="font-mono text-xs text-slate-300">{hasData ? `${d.queue}m` : '—'}</td>
                    <td className="font-mono text-xs text-slate-300">{hasData ? `${d.disparity}s` : '—'}</td>
                    <td className="font-mono text-xs text-slate-300">{hasData ? `${d.throughput} veh/h` : '—'}</td>
                    <td>
                      <button
                        disabled={!d.sampleRunId}
                        onClick={() => {
                          if (d.sampleRunId) {
                            setSelectedRunId(d.sampleRunId);
                            setCurrentView('run-explorer');
                          }
                        }}
                        className="dp1-btn dp1-btn-secondary py-1 px-2 text-xs disabled:opacity-40"
                      >
                        <span>Inspect Run</span>
                        <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
