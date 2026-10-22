import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { Search, Download, AlertCircle, Siren, Clock, FileText, CheckCircle2, ArrowRight } from 'lucide-react';

export function RunExplorerView() {
  const { allRuns, selectedRunId, setSelectedRunId, setCurrentView } = useApp();
  const [runDetails, setRunDetails] = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  const marathahalliRuns = allRuns.filter((r) => r.network === 'marathahalli');
  const syntheticRuns = allRuns.filter((r) => r.network !== 'marathahalli');

  useEffect(() => {
    let isMounted = true;
    async function loadRunData() {
      setLoading(true);
      try {
        const [rData, tsData, decData] = await Promise.all([
          api.getRun(selectedRunId),
          api.getTimeseries(selectedRunId, 2), // step 2 for smooth rendering
          api.getDecisions(selectedRunId),
        ]);
        if (isMounted) {
          setRunDetails(rData);
          setTimeseries(tsData.points || []);
          setDecisions(decData.decisions || []);
        }
      } catch (err) {
        console.error('Failed to load run:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadRunData();
    return () => { isMounted = false; };
  }, [selectedRunId]);

  const metrics = runDetails?.metrics;

  return (
    <div className="space-y-6">
      {/* Top Selector & Run Summary Banner */}
      <div className="dp1-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Search size={18} className="text-blue-400" />
            <span>Simulation Run Explorer</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit second-by-second detector readings, signal phase transitions, and adaptive green allocation decisions.
          </p>
        </div>

        {/* Run Selector & Twin Launcher */}
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-mono text-slate-400">Select Run:</label>
          <select
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="dp1-select text-xs font-mono max-w-[320px]"
          >
            {marathahalliRuns.length > 0 && (
              <optgroup label="Marathahalli Bridge Site (Real Road - 720 Runs)">
                {marathahalliRuns.map((r) => {
                  const id = r.run_id || `${r.scenario}_${r.policy}_s${r.seed}`;
                  return <option key={id} value={id}>{id}</option>;
                })}
              </optgroup>
            )}
            <optgroup label="Synthetic 4-Way Junction (80 Runs)">
              {syntheticRuns.map((r) => {
                const id = r.run_id || `${r.scenario}_${r.policy}_s${r.seed}`;
                return <option key={id} value={id}>{id}</option>;
              })}
            </optgroup>
          </select>

          <button
            onClick={() => setCurrentView('live-monitor')}
            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 transition-colors shadow"
          >
            <span>Simulation Twin</span>
            <ArrowRight size={13} />
          </button>
        </div>
      </div>

      {/* Run Summary Metrics Strip */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Average Wait</div>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {metrics.avg_wait_s ? `${metrics.avg_wait_s.toFixed(1)}s` : '—'}
            </div>
            <div className="text-[10px] text-slate-500">p95: {metrics.p95_wait_s ? `${metrics.p95_wait_s.toFixed(1)}s` : '—'}</div>
          </div>

          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Peak Jam Queue</div>
            <div className="text-xl font-bold font-mono text-amber-400 mt-1">
              {metrics.max_queue_m ? `${metrics.max_queue_m.toFixed(1)}m` : '—'}
            </div>
            <div className="text-[10px] text-slate-500">Mean: {metrics.avg_queue_m ? `${metrics.avg_queue_m.toFixed(1)}m` : '—'}</div>
          </div>

          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Throughput</div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
              {metrics.throughput_veh_per_h || '—'}
            </div>
            <div className="text-[10px] text-slate-500">veh / hour</div>
          </div>

          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Vehicles Arrived</div>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {metrics.vehicles_arrived || metrics.vehicles_total || '—'}
            </div>
            <div className="text-[10px] text-emerald-400">100% Completion</div>
          </div>

          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Cycles Executed</div>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {metrics.cycles || decisions.length || '—'}
            </div>
            <div className="text-[10px] text-slate-500">End: {metrics.sim_end_s ? `${metrics.sim_end_s}s` : '—'}</div>
          </div>

          <div className="dp1-card py-2.5 px-3">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Directional Disparity</div>
            <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {metrics.directional_wait_disparity_s ? `${metrics.directional_wait_disparity_s.toFixed(1)}s` : '—'}
            </div>
            <div className="text-[10px] text-slate-500">|W_NS - W_EW|</div>
          </div>
        </div>
      )}

      {/* Emergency Callout (if present) */}
      {metrics?.emergency_event && (
        <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-lg flex items-center justify-between text-xs text-red-200">
          <div className="flex items-center gap-2">
            <Siren size={18} className="text-red-400" />
            <span className="font-semibold">Emergency Ambulance Priority Study:</span>
            <span>
              Departed at {metrics.emergency_depart_s || 300}s on Approach {metrics.emergency_approach || 'N'}.
              Ambulance trip duration: <strong className="font-mono text-white">{metrics.emergency_trip_s ? `${metrics.emergency_trip_s.toFixed(1)}s` : 'N/A'}</strong> (Wait: {metrics.emergency_wait_s ? `${metrics.emergency_wait_s.toFixed(1)}s` : 'N/A'}).
            </span>
          </div>
          <span className="dp1-badge dp1-badge-red text-[10px]">
            {metrics.emergency_priority ? 'Signal Priority Enabled' : 'No Priority (Baseline)'}
          </span>
        </div>
      )}

      {/* Second-by-Second Timeseries Chart */}
      <div className="dp1-card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Approach Queue Lengths Over Time (Metres)
            </h3>
            <p className="text-[11px] text-slate-400">
              Sensor readings from lane-area detectors (det_N, det_S, det_E, det_W) along 150m approach arms
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> North (Main)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-400" /> South (Main)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> East (Cross)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-400" /> West (Cross)</span>
          </div>
        </div>

        <div className="h-[320px] w-full">
          {timeseries.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeseries} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="t" tick={{ fill: '#94a3b8', fontSize: 11 }} unit="s" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} unit="m" domain={[0, 150]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.1)', fontSize: '12px' }}
                  formatter={(val, name) => [`${val}m`, name.replace('q_', 'Queue ')]}
                  labelFormatter={(t) => `Simulation Time: ${t}s`}
                />
                <Line type="monotone" dataKey="q_N" stroke="#3b82f6" dot={false} strokeWidth={1.5} name="Queue North" />
                <Line type="monotone" dataKey="q_S" stroke="#38bdf8" dot={false} strokeWidth={1.5} name="Queue South" />
                <Line type="monotone" dataKey="q_E" stroke="#f59e0b" dot={false} strokeWidth={1.5} name="Queue East" />
                <Line type="monotone" dataKey="q_W" stroke="#fb923c" dot={false} strokeWidth={1.5} name="Queue West" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs font-mono">
              {loading ? 'Loading simulation timeseries...' : 'No timeseries recorded for this run.'}
            </div>
          )}
        </div>
      </div>

      {/* Cycle Decision Log Table */}
      <div className="dp1-card">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Cycle-by-Cycle Green Time Decision Audit
            </h3>
            <p className="text-[11px] text-slate-400">
              Detector queue state observed at decision epoch &rarr; Green duration selected by controller
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-500">{decisions.length} Cycles</span>
        </div>

        <div className="dp1-table-wrapper max-h-[300px]">
          <table className="dp1-table">
            <thead>
              <tr>
                <th>Cycle #</th>
                <th>Time (s)</th>
                <th>Active Axis</th>
                <th>Queue N (m)</th>
                <th>Queue S (m)</th>
                <th>Queue E (m)</th>
                <th>Queue W (m)</th>
                <th>Chosen Green (s)</th>
                <th>Decision Logic</th>
              </tr>
            </thead>
            <tbody>
              {decisions.slice(0, 30).map((d, i) => {
                const maxOwn = d.axis === 'NS' ? Math.max(d.q_N_m || 0, d.q_S_m || 0) : Math.max(d.q_E_m || 0, d.q_W_m || 0);
                const maxOther = d.axis === 'NS' ? Math.max(d.q_E_m || 0, d.q_W_m || 0) : Math.max(d.q_N_m || 0, d.q_S_m || 0);
                return (
                  <tr key={i}>
                    <td className="font-mono text-xs font-semibold text-slate-400">{d.cycle || i + 1}</td>
                    <td className="font-mono text-xs text-slate-300">{d.t}s</td>
                    <td>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                        d.axis === 'NS' ? 'bg-blue-950/60 text-blue-400' : 'bg-amber-950/60 text-amber-400'
                      }`}>
                        {d.axis}
                      </span>
                    </td>
                    <td className="font-mono text-xs">{d.q_N_m?.toFixed(1) || 0}m</td>
                    <td className="font-mono text-xs">{d.q_S_m?.toFixed(1) || 0}m</td>
                    <td className="font-mono text-xs">{d.q_E_m?.toFixed(1) || 0}m</td>
                    <td className="font-mono text-xs">{d.q_W_m?.toFixed(1) || 0}m</td>
                    <td className="font-mono text-xs font-bold text-emerald-400">{d.green_s}s</td>
                    <td className="font-mono text-[11px] text-slate-400">
                      own queue {maxOwn.toFixed(1)}m vs {maxOther.toFixed(1)}m &rarr; green {d.green_s}s
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
