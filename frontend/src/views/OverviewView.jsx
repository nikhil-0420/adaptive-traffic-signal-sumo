import React from 'react';
import { useApp } from '../context/AppContext';
import { useResults } from '../context/useResults';
import { ResultsStrip } from '../components/ResultsStrip';
import { IconArrowRight, IconArrowUpRight, IconLiveSim, IconJunction, IconOperations, IconCompare } from '../components/icons';

export function OverviewView() {
  const { setCurrentView } = useApp();
  const { siteHeadline, syntheticHeadline, getComparisonTable } = useResults();

  const comparisonRows = getComparisonTable('imbalanced_orr', 'medium');

  const headlineKpis = [
    {
      label: 'Delay Reduction (Hybrid vs Fixed)',
      value: siteHeadline.deltaPercent,
      unit: '% change',
      isDelta: true,
      deltaPercent: siteHeadline.deltaPercent,
      subtext: 'vs 47.6 s fixed baseline'
    },
    {
      label: 'Average Vehicle Delay',
      value: siteHeadline.hybridWaitS,
      unit: 's/veh',
      subtext: 'Fixed: 47.6 s · Hybrid: 42.9 s'
    },
    {
      label: 'Directional Wait Disparity',
      value: siteHeadline.directionalDisparityS,
      unit: 's',
      subtext: 'ORR vs Varthur corridor'
    },
    {
      label: 'Maximum Approach Queue',
      value: siteHeadline.maxQueueCapped ? '150' : `${siteHeadline.maxQueueM}`,
      unit: 'm',
      subtext: 'Sensor length capped at 150m'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Page Header: Noun Title (24px) + One-sentence question */}
      <div className="border-b border-hairline pb-4">
        <h1 className="text-2xl font-bold text-ink tracking-tight">
          Overview
        </h1>
        <p className="text-sm text-ink-secondary mt-1 max-w-3xl">
          How effectively does queue-adaptive signal control reduce vehicle delay and queue accumulation at the Marathahalli Bridge junction compared to fixed-time operations?
        </p>
      </div>

      {/* Headline Results Strip (Double-Bezel #1) */}
      <ResultsStrip
        title="Headline Outcome: Marathahalli Real-Road Corridor"
        basis={siteHeadline.basis}
        items={headlineKpis}
      />

      {/* Primary Hero Section: Split Layout (Plain copy on left, Interactive Poster on right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left: Plain, specific copy & CTA buttons */}
        <div className="lg:col-span-7 flex flex-col justify-between dp1-panel p-6 bg-panel">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-inset border border-hairline text-xs font-mono text-ink-secondary">
              <span>B.Tech AI & Data Science</span>
              <span>•</span>
              <span>Alliance University</span>
            </div>

            <h2 className="text-xl font-bold text-ink tracking-tight">
              Sensor-guided adaptive control for complex grade-separated junctions
            </h2>

            <p className="text-sm text-ink-secondary leading-relaxed">
              This system evaluates real-time queue-length adaptive control at Bengaluru’s Marathahalli Bridge junction using microscopic SUMO simulation with TraCI. By dynamically extending green phases when queue demand is present and terminating phases early on gap-out, the hybrid controller reduces stopping delay while preserving strict clearance safety invariants and cross-street fairness.
            </p>

            <div className="bg-inset p-3.5 rounded border border-hairline text-xs space-y-1.5 font-mono text-ink-secondary">
              <div className="font-semibold text-ink">Authoritative Validation Summary:</div>
              <div>• <strong>Site Model:</strong> -9.9% delay reduction on Marathahalli real-road corridor ({siteHeadline.basis}).</div>
              <div>• <strong>Held-Out Benchmark:</strong> -64.9% delay reduction on synthetic imbalanced flow ({syntheticHeadline.basis}).</div>
            </div>
          </div>

          {/* Reduced action buttons: One primary button-in-button, one text link */}
          <div className="flex flex-wrap items-center gap-4 pt-6 mt-6 border-t border-hairline">
            <button
              type="button"
              onClick={() => setCurrentView('live-simulation')}
              className="dp1-btn-primary"
            >
              <span>Launch live simulation</span>
              <span className="btn-icon-nest">
                <IconArrowRight size={13} />
              </span>
            </button>

            <button
              type="button"
              onClick={() => setCurrentView('junction')}
              className="text-xs font-medium text-ink-secondary hover:text-ink flex items-center gap-1.5 transition-colors"
            >
              <span>Inspect physical site model</span>
              <IconArrowUpRight size={13} />
            </button>
          </div>
        </div>

        {/* Right: Static Poster Frame of Junction Twin linking to Live Simulation */}
        <div
          onClick={() => setCurrentView('live-simulation')}
          className="lg:col-span-5 dp1-panel p-5 bg-panel flex flex-col justify-between cursor-pointer group hover:border-ink-secondary transition-colors"
        >
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-ink-secondary mb-3">
              <span className="font-semibold text-ink">Marathahalli Bridge Digital Twin</span>
              <span className="group-hover:text-petrol flex items-center gap-1">
                Open in Live Mode <IconArrowRight size={12} />
              </span>
            </div>

            {/* Poster Canvas Schematic Preview */}
            <div className="relative w-full h-44 bg-ground rounded border border-hairline overflow-hidden flex items-center justify-center">
              <div className="absolute inset-0 flex items-center justify-center opacity-60">
                <svg width="240" height="150" viewBox="0 0 240 150" fill="none" className="text-hairline">
                  <path d="M20 75h200" stroke="#8C8F8A" strokeWidth="18" />
                  <path d="M120 15v120" stroke="#8C8F8A" strokeWidth="24" />
                  <rect x="100" y="55" width="40" height="40" fill="#EFEDE6" stroke="#5C5F5A" strokeWidth="1.5" />
                  <circle cx="120" cy="75" r="5" fill="#2F7D4F" />
                </svg>
              </div>

              <div className="relative z-10 text-center space-y-1">
                <span className="inline-block px-2.5 py-1 rounded-full bg-panel border border-hairline text-xs font-mono text-ink shadow-xs">
                  Click to launch interactive simulation
                </span>
                <div className="text-[11px] text-ink-secondary font-mono">
                  3-Tier Grade Separation: Flyover · Surface · Underpass
                </div>
              </div>
            </div>
          </div>

          <div className="text-[11px] font-mono text-ink-secondary pt-3 mt-3 border-t border-hairline flex items-center justify-between">
            <span>Outer Ring Road & Varthur Rd</span>
            <span>Real TraCI Telemetry</span>
          </div>
        </div>
      </div>

      {/* How to Read This Dashboard — Mirrors the Sidebar Groups */}
      <div className="dp1-panel p-6 bg-panel">
        <h3 className="text-xs font-semibold text-ink uppercase tracking-wider mb-4">
          How to Read This Operational Dashboard
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-ink-secondary leading-relaxed">
          <div className="space-y-1.5 p-3.5 rounded bg-inset border border-hairline">
            <div className="flex items-center gap-2 text-ink font-semibold">
              <IconJunction size={14} className="text-petrol" />
              <span>1. Understand (System Baseline)</span>
            </div>
            <p>
              Examine the physical 3-tier grade-separation geometry of Marathahalli Bridge in <strong>Junction</strong>, including the elevated flyover, mainline underpass, and surface conflict node with its 8 induction loop detectors.
            </p>
          </div>

          <div className="space-y-1.5 p-3.5 rounded bg-inset border border-hairline">
            <div className="flex items-center gap-2 text-ink font-semibold">
              <IconOperations size={14} className="text-petrol" />
              <span>2. Operate (Controller Logic & Live Runs)</span>
            </div>
            <p>
              Review the decision pipeline and priority order in <strong>Operations</strong>, or run a live simulation in <strong>Live simulation</strong> with real-time decision explanations and green-time extension telemetry.
            </p>
          </div>

          <div className="space-y-1.5 p-3.5 rounded bg-inset border border-hairline">
            <div className="flex items-center gap-2 text-ink font-semibold">
              <IconCompare size={14} className="text-petrol" />
              <span>3. Evaluate (Benchmark & Evidence)</span>
            </div>
            <p>
              Inspect all 7 control policies across held-out seeds in <strong>Controller comparison</strong>, and trace every simulation run, raw data file, and paired delta in the <strong>Evidence</strong> archive.
            </p>
          </div>
        </div>
      </div>

      {/* Multi-Policy Benchmark Comparison Table (Derived from Data Layer) */}
      <div className="dp1-panel p-6 bg-panel space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-ink">
              Controller Policy Benchmark Table
            </h3>
            <p className="text-xs text-ink-secondary mt-0.5">
              Performance across {comparisonRows.length} evaluated signal policies on Marathahalli Bridge (Medium demand, seeds 121–130).
            </p>
          </div>
          <button
            type="button"
            onClick={() => setCurrentView('controller-comparison')}
            className="text-xs font-mono text-petrol hover:underline inline-flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Full Controller Comparison</span>
            <IconArrowRight size={12} />
          </button>
        </div>

        <div className="overflow-x-auto border border-hairline rounded">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-inset border-b border-hairline text-ink-secondary font-mono text-[11px]">
                <th className="py-2.5 px-3">Policy</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3 text-right">Avg Delay</th>
                <th className="py-2.5 px-3 text-right">95% CI</th>
                <th className="py-2.5 px-3 text-right">vs Fixed Baseline</th>
                <th className="py-2.5 px-3 text-right">Directional Disparity</th>
                <th className="py-2.5 px-3 text-right">Throughput</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {comparisonRows.map((row) => {
                const isHybrid = row.meta.isHybrid;
                const isBaseline = row.meta.isBaseline;
                const delta = row.deltaPercent;

                return (
                  <tr
                    key={row.policy}
                    className={isHybrid ? 'bg-petrol-subtle/40 font-medium' : 'hover:bg-inset/50'}
                  >
                    <td className="py-2.5 px-3 text-ink font-semibold flex items-center gap-2">
                      {isHybrid && <span className="w-2 h-2 rounded-full bg-petrol shrink-0" />}
                      <span>{row.meta.label}</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-ink-secondary">
                      {isBaseline ? 'Baseline' : (isHybrid ? 'Hybrid (Fused)' : 'Single-Model')}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-ink">
                      {row.avgWaitS.toFixed(1)} s
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-ink-secondary">
                      [{row.ciLowerS.toFixed(1)} s, {row.ciUpperS.toFixed(1)} s]
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">
                      {isBaseline ? (
                        <span className="text-ink-secondary">—</span>
                      ) : (
                        <span
                          className={delta < 0 ? 'text-signal-green font-bold' : 'text-signal-red font-bold'}
                        >
                          {delta > 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-ink-secondary">
                      {row.directionalDisparityS != null ? `${row.directionalDisparityS.toFixed(1)} s` : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-ink-secondary">
                      {row.throughputVph ? `${Math.round(row.throughputVph)} vph` : '—'}
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
export default OverviewView;
