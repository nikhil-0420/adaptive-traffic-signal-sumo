import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { FlaskConical, Play, Download, AlertTriangle, CheckCircle2, Clock, ShieldCheck, FileText, Ban } from 'lucide-react';

export function ResearchView() {
  const { connectionStatus } = useApp();
  const [experiments, setExperiments] = useState([]);
  const [selectedExpId, setSelectedExpId] = useState('exp_smoke_test');
  const [expStatus, setExpStatus] = useState(null);
  const [results, setResults] = useState({ aggregate: [], raw_runs: [] });
  const [loading, setLoading] = useState(true);

  // Matrix Launch Form State
  const [preset, setPreset] = useState('smoke');
  const [jobs, setJobs] = useState(2);
  const [limit, setLimit] = useState('');
  const [emergencyMatrix, setEmergencyMatrix] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [actionError, setActionError] = useState(null);

  // Load experiments list and results
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const exps = await api.getExperiments();
        if (isMounted) setExperiments(exps);

        const currentId = selectedExpId || exps[0]?.experiment_id || 'exp_smoke_test';
        const [st, res] = await Promise.all([
          api.getExperimentStatus(currentId),
          api.getExperimentResults(currentId),
        ]);
        if (isMounted) {
          setExpStatus(st);
          setResults(res);
        }
      } catch (err) {
        console.error('Error loading research data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, [selectedExpId]);

  const handleLaunch = async (e) => {
    e.preventDefault();
    setActionError(null);
    setLaunching(true);
    try {
      const res = await api.launchExperiment({
        preset,
        jobs: parseInt(jobs, 10),
        limit: limit ? parseInt(limit, 10) : undefined,
        emergency_matrix: emergencyMatrix,
      });
      setSelectedExpId(res.experiment_id);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setLaunching(false);
    }
  };

  const handleDownloadArtifact = async (artifactName) => {
    try {
      const content = await api.getExperimentArtifactContent(selectedExpId, artifactName);
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = artifactName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Could not download ${artifactName}: ${err.message}`);
    }
  };

  const isLive = connectionStatus === 'api';

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="dp1-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FlaskConical size={18} className="text-blue-400" />
            <span>Research & Matrix Evaluation Workspace</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Statistical hypothesis testing, 95% bootstrap percentile confidence intervals (B=10,000), paired delta benchmarks, and corridor disparity.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs font-mono text-slate-400">Experiment ID:</label>
          <select
            value={selectedExpId}
            onChange={(e) => setSelectedExpId(e.target.value)}
            className="dp1-select text-xs font-mono max-w-[240px]"
          >
            {experiments.map((e) => (
              <option key={e.experiment_id} value={e.experiment_id}>
                {e.experiment_id} ({e.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Launcher & Matrix Progress Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Experiment Launcher Panel */}
        <div className="dp1-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                Matrix Experiment Launcher
              </h3>
              {!isLive && (
                <span className="dp1-badge dp1-badge-yellow text-[10px]">Read-Only</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mb-4">
              {isLive
                ? 'Launch parameter grid evaluation in managed subprocess with automatic checkpointing.'
                : 'Execution disabled in Saved Snapshot Mode. A live SUMO environment is required.'}
            </p>

            <form onSubmit={handleLaunch} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Preset Design:</label>
                <select
                  value={preset}
                  onChange={(e) => setPreset(e.target.value)}
                  disabled={!isLive}
                  className="dp1-select w-full text-xs"
                >
                  <option value="smoke">Smoke Preset (3 cells • Quick Verify)</option>
                  <option value="full">Full Primary Matrix (600 cells • 4x3x5x10)</option>
                  <option value="custom">Custom Filter Matrix</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Workers (Jobs):</label>
                  <input
                    type="number"
                    min="1"
                    max="8"
                    value={jobs}
                    onChange={(e) => setJobs(e.target.value)}
                    disabled={!isLive}
                    className="dp1-input w-full text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Cell Limit (Optional):</label>
                  <input
                    type="number"
                    placeholder="Unlimited"
                    value={limit}
                    onChange={(e) => setLimit(e.target.value)}
                    disabled={!isLive}
                    className="dp1-input w-full text-xs"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="em-matrix"
                  checked={emergencyMatrix}
                  onChange={(e) => setEmergencyMatrix(e.target.checked)}
                  disabled={!isLive}
                  className="rounded bg-slate-800 border-white/20 text-blue-600 focus:ring-0"
                />
                <label htmlFor="em-matrix" className="text-xs text-slate-300">
                  Include Emergency Priority sub-study
                </label>
              </div>

              {actionError && (
                <div className="p-2 text-xs text-red-300 bg-red-950/50 border border-red-500/30 rounded flex items-center gap-1.5">
                  <AlertTriangle size={14} />
                  <span>{actionError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={!isLive || launching}
                className="dp1-btn dp1-btn-primary w-full mt-2"
              >
                <Play size={14} />
                <span>{launching ? 'Launching Matrix...' : 'Launch Matrix Evaluation'}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Matrix Progress & Status Monitor */}
        <div className="dp1-card lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                Execution Status: {selectedExpId}
              </h3>
              <span className={`dp1-badge ${
                expStatus?.status === 'complete' ? 'dp1-badge-green' : expStatus?.status === 'running' ? 'dp1-badge-blue' : 'dp1-badge-yellow'
              }`}>
                {expStatus?.status || 'unknown'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mb-4">
              Cell status tracking from <code className="font-mono text-slate-300">matrix_status.csv</code> and process manager.
            </p>

            {/* Cell Counts Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="p-2.5 rounded bg-slate-900 border border-white/5">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Total Planned</div>
                <div className="text-xl font-bold font-mono text-white mt-1">{expStatus?.total_cells || 0}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-emerald-500/20">
                <div className="text-[10px] font-mono text-emerald-400 uppercase">Completed</div>
                <div className="text-xl font-bold font-mono text-emerald-400 mt-1">{expStatus?.complete || 0}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-blue-500/20">
                <div className="text-[10px] font-mono text-blue-400 uppercase">Running</div>
                <div className="text-xl font-bold font-mono text-blue-400 mt-1">{expStatus?.running || 0}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-red-500/20">
                <div className="text-[10px] font-mono text-red-400 uppercase">Failed / Blocked</div>
                <div className="text-xl font-bold font-mono text-red-400 mt-1">
                  {(expStatus?.failed || 0) + (expStatus?.blocked || 0)}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>Matrix Completion</span>
                <span>
                  {expStatus?.total_cells
                    ? `${Math.round(((expStatus.complete || 0) / expStatus.total_cells) * 100)}%`
                    : '100%'}
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-300"
                  style={{
                    width: `${
                      expStatus?.total_cells ? ((expStatus.complete || 0) / expStatus.total_cells) * 100 : 100
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Artifact Download Buttons */}
          <div className="pt-4 border-t border-white/5 mt-4">
            <div className="text-[11px] font-mono text-slate-400 mb-2">Verified Output Artifacts:</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleDownloadArtifact('report.md')}
                className="dp1-btn dp1-btn-secondary text-xs py-1 px-2.5"
              >
                <FileText size={12} className="text-blue-400" />
                <span>report.md</span>
              </button>
              <button
                onClick={() => handleDownloadArtifact('aggregate.csv')}
                className="dp1-btn dp1-btn-secondary text-xs py-1 px-2.5"
              >
                <Download size={12} className="text-emerald-400" />
                <span>aggregate.csv</span>
              </button>
              <button
                onClick={() => handleDownloadArtifact('raw_runs.csv')}
                className="dp1-btn dp1-btn-secondary text-xs py-1 px-2.5"
              >
                <Download size={12} className="text-slate-400" />
                <span>raw_runs.csv</span>
              </button>
              <button
                onClick={() => handleDownloadArtifact('manifest.json')}
                className="dp1-btn dp1-btn-secondary text-xs py-1 px-2.5"
              >
                <Download size={12} className="text-amber-400" />
                <span>manifest.json</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Aggregate Statistics Table */}
      <div className="dp1-card">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Primary Aggregate Table (<code className="text-slate-300 font-mono">aggregate.csv</code>)
            </h3>
            <p className="text-[11px] text-slate-400">
              Aggregated across experimental cells. Waiting times report Mean ± SD with 95% bootstrap confidence intervals.
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-500">{results.aggregate.length} Conditions Evaluated</span>
        </div>

        <div className="dp1-table-wrapper max-h-[350px]">
          <table className="dp1-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Demand Level</th>
                <th>Policy Strategy</th>
                <th>Sample N</th>
                <th>Mean Wait (s)</th>
                <th>p95 Wait (s)</th>
                <th>Max Queue (m)</th>
                <th>Throughput</th>
                <th>Directional Gap</th>
                <th>Completion Rate</th>
              </tr>
            </thead>
            <tbody>
              {results.aggregate.map((row, i) => (
                <tr key={i}>
                  <td className="font-mono text-xs font-semibold text-white">{row.pattern || row.scenario}</td>
                  <td className="font-mono text-xs">{row.demand_level || row.level}</td>
                  <td className="font-mono text-xs font-bold text-blue-400">{row.policy}</td>
                  <td className="font-mono text-xs">{row.n_runs || row.n || 1}</td>
                  <td className="font-mono text-xs font-bold text-emerald-400">
                    {row.mean_wait_s ? `${row.mean_wait_s.toFixed(1)}s` : row.avg_wait_s ? `${row.avg_wait_s.toFixed(1)}s` : '—'}
                  </td>
                  <td className="font-mono text-xs text-slate-300">
                    {row.mean_p95_wait_s ? `${row.mean_p95_wait_s.toFixed(1)}s` : row.p95_wait_s ? `${row.p95_wait_s.toFixed(1)}s` : '—'}
                  </td>
                  <td className="font-mono text-xs text-slate-300">{row.max_queue_m ? `${row.max_queue_m.toFixed(1)}m` : '—'}</td>
                  <td className="font-mono text-xs text-slate-300">{row.mean_throughput || row.throughput_veh_per_h || '—'} veh/h</td>
                  <td className="font-mono text-xs text-cyan-300">{row.mean_disparity_s ? `${row.mean_disparity_s.toFixed(1)}s` : row.directional_wait_disparity_s ? `${row.directional_wait_disparity_s.toFixed(1)}s` : '—'}</td>
                  <td className="font-mono text-xs text-emerald-400 font-bold">{row.completion_rate ? `${(row.completion_rate * 100).toFixed(0)}%` : '100%'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
