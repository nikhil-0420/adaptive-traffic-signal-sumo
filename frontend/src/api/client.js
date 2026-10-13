/**
 * DP1 Traffic Simulation API & Static Snapshot Client
 *
 * Handles live backend communication with AbortController timeouts and
 * falls back seamlessly to the verified /demo-data/ snapshot when offline.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const TIMEOUT_MS = 8000;

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE.replace(/\/+$/, '');
    this.mode = 'unknown'; // 'api' | 'snapshot'
    this.healthDetails = null;
    this.snapshotManifest = null;
  }

  async _fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error(`Request timed out after ${timeoutMs}ms: ${url}`);
      }
      throw err;
    }
  }

  async checkConnection() {
    // 1. Try hitting /api/health if base URL or proxy is present
    try {
      const healthUrl = this.baseUrl ? `${this.baseUrl}/api/health` : '/api/health';
      const res = await this._fetchWithTimeout(healthUrl, {}, 3000);
      if (res.ok) {
        const data = await res.json();
        this.mode = 'api';
        this.healthDetails = data;
        return { mode: 'api', data };
      }
      if (res.status === 503) {
        // SUMO unavailable on live host
        const data = await res.json();
        this.mode = 'degraded_api';
        this.healthDetails = data;
        return { mode: 'degraded_api', data };
      }
    } catch (e) {
      // API host unreachable -> switch to verified snapshot
    }

    // 2. Load static snapshot manifest
    try {
      const res = await this._fetchWithTimeout('/demo-data/manifest.json', {}, 3000);
      if (res.ok) {
        const manifest = await res.json();
        this.mode = 'snapshot';
        this.snapshotManifest = manifest;
        return { mode: 'snapshot', manifest };
      }
    } catch (e) {
      // Snapshot also missing
    }

    this.mode = 'disconnected';
    return { mode: 'disconnected' };
  }

  async getSummary() {
    if (this.mode === 'api') {
      const url = this.baseUrl ? `${this.baseUrl}/api/summary` : '/api/summary';
      const res = await this._fetchWithTimeout(url);
      if (res.ok) return await res.json();
    }
    // Fallback to demo snapshot
    const res = await this._fetchWithTimeout('/demo-data/summary.json');
    return await res.json();
  }

  async getAllRuns() {
    // Read from snapshot all_runs.json
    try {
      const res = await this._fetchWithTimeout('/demo-data/all_runs.json');
      if (res.ok) return await res.json();
    } catch (e) {
      return [];
    }
    return [];
  }

  async getRun(runId) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}` : `/api/runs/${runId}`;
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot run
    try {
      const res = await this._fetchWithTimeout(`/demo-data/runs/${runId}/metrics.json`);
      if (res.ok) {
        const metrics = await res.json();
        return {
          run_id: runId,
          status: 'completed',
          metrics,
          available_artifacts: ['timeseries.json', 'decisions.json', 'metrics.json'],
        };
      }
    } catch (e) {}
    return { run_id: runId, status: 'unknown', metrics: null, available_artifacts: [] };
  }

  async getTimeseries(runId, step = 1) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl
          ? `${this.baseUrl}/api/runs/${runId}/timeseries?step=${step}`
          : `/api/runs/${runId}/timeseries?step=${step}`;
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot
    try {
      const res = await this._fetchWithTimeout(`/demo-data/runs/${runId}/timeseries.json`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return { run_id: runId, total_points: 0, points: [] };
  }

  async getDecisions(runId) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/decisions` : `/api/runs/${runId}/decisions`;
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    return { run_id: runId, total_decisions: 0, decisions: [] };
  }

  async getReplay(runId) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/replay` : `/api/runs/${runId}/replay`;
        const res = await this._fetchWithTimeout(url, {}, 5000);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot demo-data
    try {
      const res = await this._fetchWithTimeout(`/demo-data/runs/${runId}/replay.json`, {}, 5000);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  }

  async getTelemetry(runId) {
    if (this.mode === 'api') {
      const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/telemetry` : `/api/runs/${runId}/telemetry`;
      const res = await this._fetchWithTimeout(url, {}, 3000);
      if (res.ok) return await res.json();
      throw new Error(`Telemetry error: ${res.statusText}`);
    }
    // In snapshot mode, synthesize completed telemetry from metrics
    const run = await this.getRun(runId);
    return {
      run_id: runId,
      status: 'completed',
      sim_time_s: run?.metrics?.sim_end_s || 2000.0,
      phase: 'GREEN',
      axis: 'NS',
      queues_m: { N: 0, S: 0, E: 0, W: 0 },
      traffic_light_state: 'GGggrrrrGGggrrrr',
      updated_at: Date.now() / 1000,
      is_stale: true,
      emergency_approaching: false,
      emergency_dist_m: null,
    };
  }

  async launchRun(params) {
    if (this.mode !== 'api') {
      throw new Error(
        'Live simulation launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO installed is required.'
      );
    }
    const url = this.baseUrl ? `${this.baseUrl}/api/runs` : '/api/runs';
    const res = await this._fetchWithTimeout(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Launch failed: ${res.statusText}`);
    }
    return await res.json();
  }

  async getExperiments() {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/experiments` : '/api/experiments';
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot experiment
    return [
      {
        experiment_id: 'exp_smoke_test',
        status: 'complete',
        preset: 'smoke',
        total_cells: 3,
        created_at: '2026-10-12T06:49:49Z',
      },
    ];
  }

  async getExperimentStatus(expId) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/experiments/${expId}/status` : `/api/experiments/${expId}/status`;
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot
    return {
      experiment_id: expId,
      status: 'complete',
      total_cells: 3,
      pending: 0,
      running: 0,
      complete: 3,
      failed: 0,
      blocked: 0,
      skipped: 0,
    };
  }

  async getExperimentResults(expId) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/experiments/${expId}/results` : `/api/experiments/${expId}/results`;
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to snapshot
    try {
      const [aggRes, rawRes] = await Promise.all([
        this._fetchWithTimeout(`/demo-data/experiments/${expId}/aggregate.json`),
        this._fetchWithTimeout(`/demo-data/experiments/${expId}/raw_runs.json`),
      ]);
      const aggregate = aggRes.ok ? await aggRes.json() : [];
      const raw_runs = rawRes.ok ? await rawRes.json() : [];
      return { experiment_id: expId, aggregate, raw_runs };
    } catch (e) {
      return { experiment_id: expId, aggregate: [], raw_runs: [] };
    }
  }

  async getExperimentArtifactContent(expId, artifactName) {
    if (this.mode === 'api') {
      const url = this.baseUrl
        ? `${this.baseUrl}/api/experiments/${expId}/artifacts/${artifactName}`
        : `/api/experiments/${expId}/artifacts/${artifactName}`;
      const res = await this._fetchWithTimeout(url);
      if (res.ok) return await res.text();
    }
    // Fallback
    const res = await this._fetchWithTimeout(`/demo-data/experiments/${expId}/${artifactName}`);
    if (res.ok) return await res.text();
    throw new Error(`Artifact ${artifactName} not available.`);
  }

  async launchExperiment(params) {
    if (this.mode !== 'api') {
      throw new Error(
        'Research matrix launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO is required.'
      );
    }
    const url = this.baseUrl ? `${this.baseUrl}/api/experiments` : '/api/experiments';
    const res = await this._fetchWithTimeout(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Experiment launch failed: ${res.statusText}`);
    }
    return await res.json();
  }

  async cancelExperiment(expId) {
    if (this.mode !== 'api') {
      throw new Error('Cancel is only supported in live API mode.');
    }
    const url = this.baseUrl ? `${this.baseUrl}/api/experiments/${expId}/cancel` : `/api/experiments/${expId}/cancel`;
    const res = await this._fetchWithTimeout(url, { method: 'POST' });
    if (!res.ok) throw new Error('Cancellation failed.');
    return await res.json();
  }
}

export const api = new ApiClient();
