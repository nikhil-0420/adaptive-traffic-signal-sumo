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
    const candidates = [runId];
    if (runId.includes('_medium_')) {
      candidates.push(runId.replace('_medium_', '_'));
    } else {
      const parts = runId.split('_');
      if (parts.length >= 3) {
        const idx = parts.findIndex((p) => ['adaptive', 'fixed', 'pressure', 'rl'].includes(p));
        if (idx > 0) {
          const c = [...parts];
          c.splice(idx, 0, 'medium');
          candidates.push(c.join('_'));
        }
      }
    }

    for (const cid of candidates) {
      if (this.mode === 'api') {
        try {
          const url = this.baseUrl ? `${this.baseUrl}/api/runs/${cid}/replay` : `/api/runs/${cid}/replay`;
          const res = await this._fetchWithTimeout(url, {}, 5000);
          if (res.ok) return await res.json();
        } catch (e) {}
      }
      try {
        const res = await this._fetchWithTimeout(`/demo-data/runs/${cid}/replay.json`, {}, 5000);
        if (res.ok) return await res.json();
      } catch (e) {}
    }
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

  async getReplay(runId) {
    if (!runId) return null;
    // 1. If in API mode, query the live backend endpoint
    if (this.mode === 'api') {
      try {
        const url = this.baseUrl ? `${this.baseUrl}/api/runs/${runId}/replay` : `/api/runs/${runId}/replay`;
        const res = await this._fetchWithTimeout(url, {}, 5000);
        if (res.ok) {
          return await res.json();
        }
      } catch (e) {
        console.warn(`API getReplay failed for ${runId}, falling back to static snapshot:`, e);
      }
    }

    // 2. Static snapshot / demo-data fallback
    try {
      const snapRes = await this._fetchWithTimeout(`/demo-data/runs/${runId}/replay.json`, {}, 4000);
      if (snapRes.ok) {
        return await snapRes.json();
      }
      // Check alternative naming (e.g. without or with _medium_)
      const altRunId = runId.includes('_medium_')
        ? runId.replace('_medium_', '_')
        : runId.replace('_adaptive_', '_medium_adaptive_')
               .replace('_fixed_', '_medium_fixed_')
               .replace('_queue_extension_', '_medium_queue_extension_');
      const snapResAlt = await this._fetchWithTimeout(`/demo-data/runs/${altRunId}/replay.json`, {}, 4000);
      if (snapResAlt.ok) {
        return await snapResAlt.json();
      }
    } catch (e) {
      console.warn(`Static getReplay failed for ${runId}:`, e);
    }

    return null;
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
