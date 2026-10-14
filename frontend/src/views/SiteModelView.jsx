import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
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
  Minimize2
} from 'lucide-react';

export function SiteModelView() {
  const { setCurrentView } = useApp();
  const [siteData, setSiteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('topology'); // 'topology' | 'grade_separation' | 'signal_plan' | 'provenance'
  const [selectedMovement, setSelectedMovement] = useState('all');
  const [zoomedImage, setZoomedImage] = useState(null);

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

      {/* Tab 1: Topology & SUMO GUI Render */}
      {activeTab === 'topology' && (
        <div className="space-y-6">
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
