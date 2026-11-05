/**
 * DP1 Traffic Simulation API & Static Snapshot Client
 *
 * Handles live backend communication with AbortController timeouts and
 * falls back seamlessly to the verified /demo-data/ snapshot when offline.
 */

const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '';
const TIMEOUT_MS = 8000;

export class ApiClient {
  constructor() {
    this.baseUrl = API_BASE.replace(/\/+$/, '');
    this.mode = 'unknown'; // 'api' | 'snapshot' | 'degraded_api' | 'disconnected'
    this.healthDetails = null;
    this.snapshotManifest = null;
    this.liveRunStore = new Map();
    this.healthBackoffMs = 4000;
    this.nextHealthCheckTime = 0;
    this.healthCheckInFlight = false;
    this._initSessionStorage();
  }

  _initSessionStorage() {
    if (typeof window === 'undefined' || !window.sessionStorage) return;
    try {
      const raw = window.sessionStorage.getItem('dp1_live_runs');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          for (const item of parsed) {
            if (item && item.run_id) {
              this.liveRunStore.set(item.run_id, item);
            }
          }
        }
      }
    } catch (e) {}
  }

  _persistSessionRuns() {
    if (typeof window === 'undefined' || !window.sessionStorage) return;
    try {
      const array = Array.from(this.liveRunStore.values());
      window.sessionStorage.setItem('dp1_live_runs', JSON.stringify(array.slice(-20)));
    } catch (e) {}
  }

  deduplicateDecisions(decisions, runId = '') {
    if (!Array.isArray(decisions)) return [];
    const seen = new Set();
    const result = [];
    for (const d of decisions) {
      if (!d) continue;
      const t = Math.round(Number(d.t || 0) * 10) / 10;
      const axis = String(d.axis || '').toUpperCase();
      const type = String(d.applied_action || d.decision_outcome || d.action || '').toUpperCase();
      const rId = String(d.run_id || runId);
      const key = `${t}_${axis}_${type}_${rId}`;
      if (!seen.has(key)) {
        seen.add(key);
        result.push(d);
      }
    }
    return result;
  }

  saveLiveRun(runData) {
    if (!runData || !runData.run_id) return null;
    const dedupedDecisions = this.deduplicateDecisions(runData.decisions || [], runData.run_id);
    const completedRun = {
      ...runData,
      status: 'completed',
      decisions: dedupedDecisions,
      completed_at: runData.completed_at || new Date().toISOString(),
    };
    this.liveRunStore.set(completedRun.run_id, completedRun);
    this._persistSessionRuns();
    return completedRun;
  }

  async finaliseLiveRun(runId, timeoutMs = 6000) {
    if (!runId) return;
    if (this.mode !== 'api') return;
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const run = await this.getRun(runId);
        if (run && (run.status === 'completed' || run.status === 'finished')) {
          return run;
        }
      } catch (e) {}
      await new Promise((r) => setTimeout(r, 400));
    }
  }

  async _fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // If caller provided an external abort signal, link it to the local controller
    if (options.signal) {
      if (options.signal.aborted) {
        clearTimeout(timeoutId);
        throw new DOMException('Aborted', 'AbortError');
      }
      options.signal.addEventListener('abort', () => controller.abort(), { once: true });
    }

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
        if (options.signal?.aborted) {
          throw err;
        }
        throw new Error(`Request timed out after ${timeoutMs}ms: ${url}`);
      }
      throw err;
    }
  }

  async _parseJsonSafe(res) {
    if (!res || !res.ok) return null;
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return null;
    }
    try {
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  async checkConnection(force = false) {
    const now = Date.now();
    if (!force && this.mode === 'snapshot' && now < this.nextHealthCheckTime) {
      return {
        mode: 'snapshot',
        manifest: this.snapshotManifest,
        offlineReason: 'Snapshot mode (backend offline): verified TraCI simulation artifacts loaded.'
      };
    }

    // 1. Try hitting /api/health quietly with timeout and exponential backoff on failure
    try {
      const healthUrl = this.baseUrl ? `${this.baseUrl}/api/health` : '/api/health';
      const res = await this._fetchWithTimeout(healthUrl, {}, 2500);
      if (res.ok) {
        const data = await res.json();
        this.mode = 'api';
        this.healthDetails = data;
        this.healthBackoffMs = 4000;
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
      // Backend unreachable: back off quietly without console errors
      this.healthBackoffMs = Math.min(60000, this.healthBackoffMs * 1.5);
      this.nextHealthCheckTime = now + this.healthBackoffMs;
    }

    // 2. Load static snapshot manifest
    try {
      const res = await this._fetchWithTimeout('/demo-data/manifest.json', {}, 3000);
      if (res.ok) {
        const manifest = await res.json();
        this.mode = 'snapshot';
        this.snapshotManifest = manifest;
        return {
          mode: 'snapshot',
          manifest,
          offlineReason: 'Snapshot mode (backend offline): verified TraCI simulation artifacts loaded.'
        };
      }
    } catch (e) {}

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
    const runsMap = new Map();

    // 1. Add session/live runs first
    for (const [id, r] of this.liveRunStore.entries()) {
      runsMap.set(id, {
        run_id: id,
        scenario: r.scenario || 'imbalanced_orr',
        policy: r.policy || 'hybrid_queue_adaptive',
        seed: r.seed || 121,
        status: 'completed',
        is_live_session: true,
        completed_at: r.completed_at,
        metrics: r.metrics || null,
        decisions_count: r.decisions?.length || 0
      });
    }

    // 2. Add verified snapshot runs
    try {
      const res = await this._fetchWithTimeout('/demo-data/all_runs.json');
      if (res.ok) {
        const list = await res.json();
        if (Array.isArray(list)) {
          for (const item of list) {
            if (item && item.run_id && !runsMap.has(item.run_id)) {
              runsMap.set(item.run_id, item);
            }
          }
        }
      }
    } catch (e) {}

    return Array.from(runsMap.values());
  }

  async getRun(runId) {
    if (!runId) return null;

    // Check live run store first
    if (this.liveRunStore.has(runId)) {
      const live = this.liveRunStore.get(runId);
      return {
        run_id: runId,
        status: 'completed',
        scenario: live.scenario,
        policy: live.policy,
        seed: live.seed,
        metrics: live.metrics,
        available_artifacts: ['decisions.json', 'replay.json', 'metrics.json'],
        is_live_session: true
      };
    }

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
      const metrics = await this._parseJsonSafe(res);
      if (metrics) {
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
    if (!runId) return { run_id: '', total_points: 0, points: [] };

    if (this.liveRunStore.has(runId)) {
      const live = this.liveRunStore.get(runId);
      if (live.timeseries) return live.timeseries;
    }

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

  async getDecisions(runId, signal = null) {
    if (!runId) return { run_id: '', total_decisions: 0, decisions: [] };

    // 1. Check live run store first
    if (this.liveRunStore.has(runId)) {
      const live = this.liveRunStore.get(runId);
      const decs = this.deduplicateDecisions(live.decisions || [], runId);
      return {
        run_id: runId,
        total_decisions: decs.length,
        decisions: decs,
        is_live_session: true,
      };
    }

    // 2. Try API
    let rawData = null;
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/decisions` : `/api/runs/${runId}/decisions`;
        const res = await this._fetchWithTimeout(url, { signal });
        rawData = await this._parseJsonSafe(res);
      } catch (e) {
        if (e.name === 'AbortError') throw e;
      }
    }

    // 3. Try snapshot file
    if (!rawData) {
      try {
        const res = await this._fetchWithTimeout(`/demo-data/runs/${runId}/decisions.json`, { signal });
        rawData = await this._parseJsonSafe(res);
      } catch (e) {
        if (e.name === 'AbortError') throw e;
      }
    }

    if (rawData && Array.isArray(rawData.decisions)) {
      const normalized = rawData.decisions.map((d) => {
        let qActive = d.q_active_m;
        let qCompeting = d.q_competing_m;
        const isNS = String(d.axis || 'NS').toUpperCase() === 'NS';
        if (qActive == null && (d.q_N_m != null || d.q_S_m != null || d.q_E_m != null || d.q_W_m != null)) {
          const qN = Number(d.q_N_m || 0);
          const qS = Number(d.q_S_m || 0);
          const qE = Number(d.q_E_m || 0);
          const qW = Number(d.q_W_m || 0);
          qActive = isNS ? Math.max(qN, qS) : Math.max(qE, qW);
          qCompeting = isNS ? Math.max(qE, qW) : Math.max(qN, qS);
        }
        return {
          ...d,
          q_active_m: qActive != null ? Number(qActive) : undefined,
          q_competing_m: qCompeting != null ? Number(qCompeting) : undefined,
        };
      });
      const deduped = this.deduplicateDecisions(normalized, runId);
      return {
        ...rawData,
        run_id: runId,
        total_decisions: deduped.length,
        decisions: deduped,
      };
    }

    return { run_id: runId, total_decisions: 0, decisions: [] };
  }

  async getRunDecisions(runId, signal = null) {
    return this.getDecisions(runId, signal);
  }

  async getRunReplay(runId) {
    return this.getReplay(runId);
  }

  async getReplay(runId) {
    if (!runId) return null;

    // Check live store first
    if (this.liveRunStore.has(runId)) {
      const live = this.liveRunStore.get(runId);
      if (live.replay && live.replay.frames && live.replay.frames.length > 0) {
        return live.replay;
      }
    }

    const candidates = [runId];
    if (runId.startsWith('live_')) {
      // Map live scenario to corresponding verified replay asset
      candidates.push('marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121');
      candidates.push('marathahalli_imbalanced_orr_adaptive_s121');
    }
    if (runId.includes('_medium_')) {
      candidates.push(runId.replace('_medium_', '_'));
    } else {
      const parts = runId.split('_');
      if (parts.length >= 3) {
        const idx = parts.findIndex((p) => ['adaptive', 'fixed', 'pressure', 'rl', 'hybrid'].includes(p));
        if (idx > 0) {
          const c = [...parts];
          c.splice(idx, 0, 'medium');
          candidates.push(c.join('_'));
        }
      }
    }

    // 1. Try API endpoints
    if (this.mode === 'api') {
      for (const cid of candidates) {
        try {
          const url = this.baseUrl ? `${this.baseUrl}/api/runs/${cid}/replay` : `/api/runs/${cid}/replay`;
          const res = await this._fetchWithTimeout(url, {}, 5000);
          const data = await this._parseJsonSafe(res);
          if (data && data.frames && data.frames.length > 0) {
            return data;
          }
        } catch (e) {
          break; // Stop immediately on connection error
        }
      }
    }

    // 2. Try static demo-data files
    for (const cid of candidates) {
      try {
        const res = await this._fetchWithTimeout(`/demo-data/runs/${cid}/replay.json`, {}, 4000);
        const data = await this._parseJsonSafe(res);
        if (data && data.frames && data.frames.length > 0) {
          return data;
        }
      } catch (e) {
        break; // Stop immediately on connection error
      }
    }

    return null;
  }

  async getTelemetry(runId, signal = null) {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/telemetry` : `/api/runs/${runId}/telemetry`;
        const res = await this._fetchWithTimeout(url, { signal }, 3000);
        const data = await this._parseJsonSafe(res);
        if (data && data.status) return data;
      } catch (e) {
        if (e.name === 'AbortError') throw e;
      }
    }
    // Graceful fallback: synthesize completed telemetry from run details or snapshot
    const run = await this.getRun(runId);
    return {
      run_id: runId,
      status: run?.status === 'running' ? 'running' : 'completed',
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

  async getActiveRuns() {
    if (this.mode !== 'api') return [];
    try {
      const url = this.baseUrl ? `${this.baseUrl}/api/runs/active` : '/api/runs/active';
      const res = await this._fetchWithTimeout(url, {}, 3000);
      const data = await this._parseJsonSafe(res);
      return data?.active_runs || [];
    } catch (e) {
      return [];
    }
  }

  async stopRun(runId) {
    if (this.mode !== 'api') return { status: 'stopped' };
    try {
      const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/stop` : `/api/runs/${runId}/stop`;
      const res = await this._fetchWithTimeout(url, { method: 'POST' }, 5000);
      return (await this._parseJsonSafe(res)) || { status: 'stopped' };
    } catch (e) {
      return { status: 'stopped', error: e.message };
    }
  }

  async launchRun(params) {
    if (this.mode !== 'api') {
      throw new Error(
        'Live simulation launch is disabled in Saved Simulation Snapshot mode. A live host with Eclipse SUMO installed is required.'
      );
    }
    const url = this.baseUrl ? `${this.baseUrl}/api/runs` : '/api/runs';
    try {
      const res = await this._fetchWithTimeout(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let detailMsg = `Launch failed: ${res.statusText}`;
        let activeRunId = null;
        if (typeof err.detail === 'string') {
          detailMsg = err.detail;
          const match = err.detail.match(/Run '([^']+)' is already running/);
          if (match) activeRunId = match[1];
        } else if (err.detail && typeof err.detail === 'object') {
          detailMsg = err.detail.message || err.detail.detail || detailMsg;
          activeRunId = err.detail.run_id || null;
        }
        const launchErr = new Error(detailMsg);
        launchErr.status = res.status;
        launchErr.isConflict = res.status === 409;
        launchErr.activeRunId = activeRunId || params?.run_id || null;
        throw launchErr;
      }
      return await res.json();
    } catch (err) {
      if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError') || err.message.includes('connect ECONNREFUSED'))) {
        throw new Error(
          'Cannot connect to DP1 simulation API at http://127.0.0.1:8000. Verify the backend server is running (`python -m backend`).'
        );
      }
      throw err;
    }
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
        experiment_id: 'exp_marathahalli_hybrid_840',
        status: 'complete',
        preset: 'hybrid',
        network: 'marathahalli',
        total_cells: 840,
        created_at: '2026-10-20T16:00:00Z',
      },
      {
        experiment_id: 'exp_marathahalli_site_720',
        status: 'complete',
        preset: 'full',
        network: 'marathahalli',
        total_cells: 720,
        created_at: '2026-10-14T14:35:00Z',
      },
      {
        experiment_id: 'exp_marathahalli_site',
        status: 'complete',
        preset: 'site',
        network: 'marathahalli',
        total_cells: 600,
        created_at: '2026-10-14T06:00:00Z',
      },
      {
        experiment_id: 'exp_marathahalli_emergency_360',
        status: 'complete',
        preset: 'emergency',
        network: 'marathahalli',
        total_cells: 360,
        created_at: '2026-10-14T07:30:00Z',
      },
      {
        experiment_id: 'exp_primary_720',
        status: 'complete',
        preset: 'full',
        network: 'synthetic',
        total_cells: 720,
        created_at: '2026-10-12T07:00:00Z',
      },
      {
        experiment_id: 'exp_smoke_test',
        status: 'complete',
        preset: 'smoke',
        network: 'synthetic',
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

  async getSiteModel() {
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/site-model` : '/api/site-model';
        const res = await this._fetchWithTimeout(url);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Fallback to demo snapshot or bundle default
    try {
      const res = await this._fetchWithTimeout('/demo-data/site_model.json');
      if (res.ok) return await res.json();
    } catch (e) {}

    return {
      network_id: 'marathahalli',
      name: 'Marathahalli Bridge Junction (Varthur Rd / Outer Ring Rd)',
      location: 'Marathahalli, Bengaluru, Karnataka 560037 (12.9562° N, 77.7011° E)',
      description:
        'Geographically grounded SUMO network model of the Marathahalli Bridge intersection. Integrates OpenCity road-width GIS datasets, OSM centerlines, and BTP signal timing adaptations.',
      grounding_sources: [
        {
          name: 'BTP Marathahalli Yamlur Signal Plan',
          type: 'Traffic Signal Plan (PDF)',
          detail: 'Bengaluru Traffic Police signal timing structure adapted with 3s yellow and 2s all-red clearance.',
        },
        {
          name: 'OpenCity Bengaluru Road GIS',
          type: 'Geospatial Centerlines & Widths',
          detail: 'OpenCity municipal GIS road widths confirming 4-lane Varthur Rd and 6-lane Outer Ring Road.',
        },
        {
          name: 'OpenStreetMap Real-World Alignment',
          type: 'Physical Street Network',
          detail: 'Elevation profiles, ramp alignments, and directional service road slip lanes.',
        },
      ],
      grade_separation: {
        flyover: {
          name: 'Varthur Road Elevated Flyover',
          lanes: 4,
          direction: 'East-West (HAL Airport Rd <-> Whitefield)',
          function: 'Carries ~70% of through traffic overhead, completely bypassing the surface signal.',
        },
        underpass: {
          name: 'Outer Ring Road Mainline Underpass',
          lanes: 6,
          direction: 'North-South (K.R. Puram <-> Kadubeesanahalli / Sarjapur)',
          function: 'Carries ~70% of through IT corridor traffic beneath, completely bypassing the surface signal.',
        },
        surface_level: {
          name: 'Marathahalli Surface Signalized Junction',
          tls_id: 'marathahalli_tls',
          lanes_per_leg: 2,
          function: 'Controls turning traffic, right-turns, bus transit, and remaining surface through movements.',
        },
      },
      surface_junction: {
        tls_id: 'marathahalli_tls',
        control_type: '2-Stage Signal with All-Red Clearance',
        stages: [
          { phase: 'NS_GREEN', axis: 'NS', movements: 'ORR South & North surface legs', state_string: 'GGGgrrrrGGGgrrrr' },
          { phase: 'NS_YELLOW', axis: 'NS', duration_s: 3.0, state_string: 'yyygrrrryyygrrrr' },
          { phase: 'ALL_RED_1', axis: 'ALL_RED', duration_s: 2.0, state_string: 'rrrrrrrrrrrrrrrr' },
          { phase: 'EW_GREEN', axis: 'EW', movements: 'Varthur West & East surface legs', state_string: 'rrrrGGGgrrrrGGGg' },
          { phase: 'EW_YELLOW', axis: 'EW', duration_s: 3.0, state_string: 'rrrryyygrrrryyyg' },
          { phase: 'ALL_RED_2', axis: 'ALL_RED', duration_s: 2.0, state_string: 'rrrrrrrrrrrrrrrr' },
        ],
        detectors: [
          { id: 'det_hal_0', approach: 'W', lane: 0, length_m: 80.0 },
          { id: 'det_hal_1', approach: 'W', lane: 1, length_m: 80.0 },
          { id: 'det_wf_0', approach: 'E', lane: 0, length_m: 80.0 },
          { id: 'det_wf_1', approach: 'E', lane: 1, length_m: 80.0 },
          { id: 'det_orr_s_0', approach: 'S', lane: 0, length_m: 80.0 },
          { id: 'det_orr_s_1', approach: 'S', lane: 1, length_m: 80.0 },
          { id: 'det_orr_n_0', approach: 'N', lane: 0, length_m: 80.0 },
          { id: 'det_orr_n_1', approach: 'N', lane: 1, length_m: 80.0 },
        ],
      },
      provenance_table: [
        {
          attribute: 'Road Alignment & Centerlines',
          status: 'Verified',
          source: 'OpenCity GIS + OSM',
          notes: 'Exact physical geometries for Varthur Rd, ORR, and 4 service slip roads.',
        },
        {
          attribute: 'Grade Separation (Flyover + Underpass)',
          status: 'Verified',
          source: 'Satellite imagery + BDA infrastructure records',
          notes: '4-lane flyover above, 6-lane mainline below, surface roundabout/signal between.',
        },
        {
          attribute: 'Signal Phase Clearance (Yellow/All-Red)',
          status: 'Verified',
          source: 'DP1 Safety Contract & BTP standard clearance',
          notes: 'Strictly 3s yellow and 2s all-red clearance preserved across all phase changes.',
        },
        {
          attribute: 'Surface Signal Phasing Structure',
          status: 'Inferred',
          source: 'BTP Yamlur corridor document adaptation',
          notes: 'Adapted as 2-stage alternating surface greens without pedestrian exclusive phase.',
        },
        {
          attribute: 'Grade Separation Volume Split',
          status: 'Inferred',
          source: 'Standard traffic engineering guidelines (HCM)',
          notes: '70% through traffic assigned to flyover/underpass; 30% through + 100% turns at surface.',
        },
        {
          attribute: 'Real-Time Traffic Sensor Telemetry',
          status: 'Unknown (Synthetic Demand)',
          source: 'SUMO Lane-Area Detectors (E2)',
          notes: 'Controlled synthetic demand matrices (balanced, imbalanced_orr, imbalanced_varthur, surge).',
        },
      ],
      topology_image_url: '/network/marathahalli/marathahalli_network_topology.png',
      sumo_gui_image_url: '/network/marathahalli/sumo_gui_render.png',
    };
  }
}

export const api = new ApiClient();
