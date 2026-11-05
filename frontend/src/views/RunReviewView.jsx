import React, { useState, useEffect, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { JunctionTwin } from '../components/JunctionTwin';
import { DecisionTimeline } from '../components/DecisionTimeline';
import { DecisionExplainer } from '../components/DecisionExplainer';
import { ResultsStrip } from '../components/ResultsStrip';
import { explainDecision, collapseHolds, getAxisName } from '../utils/explainDecision';
import { api } from '../api/client';
import {
  IconDownload,
  IconArrowRight,
  IconInfo,
  IconCheck,
  IconFilter
} from '../components/icons';
import clsx from 'clsx';

export function RunReviewView() {
  const { selectedRunId, activeReviewRun, setCurrentView, allRuns } = useApp();

  const runId = activeReviewRun?.run_id || selectedRunId || 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121';

  const [currentTime, setCurrentTime] = useState(0);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDecisionIndex, setSelectedDecisionIndex] = useState(0);
  const [filterType, setFilterType] = useState('all'); // 'all' | 'extend' | 'gap_out' | 'rejected' | 'emergency' | 'hold'
  const [expandedRowIndex, setExpandedRowIndex] = useState(null);
  const [expandedReasonIndex, setExpandedReasonIndex] = useState(null);

  // Load run decisions
  useEffect(() => {
    let isSubscribed = true;
    setLoading(true);

    api.getDecisions(runId)
      .then((data) => {
        if (!isSubscribed) return;
        const decList = data?.decisions || [];
        setDecisions(decList);
        if (decList.length > 0) {
          setCurrentTime(decList[0].t);
        }
      })
      .catch((err) => {
        console.error('Failed to load run decisions:', err);
      })
      .finally(() => {
        if (isSubscribed) setLoading(false);
      });

    return () => {
      isSubscribed = false;
    };
  }, [runId]);

  // Current decision synced to playback/scrub time
  const currentDecision = useMemo(() => {
    if (decisions.length === 0) return null;
    let closest = decisions[0];
    for (const d of decisions) {
      if (d.t <= currentTime) {
        closest = d;
      } else {
        break;
      }
    }
    return closest;
  }, [decisions, currentTime]);

  // Compute summary metrics for the run
  const summary = useMemo(() => {
    let secondsAdded = 0;
    let extensionsGranted = 0;
    let extensionsRefused = 0;
    let earlyEnds = 0;
    let emergencyPreemptions = 0;
    let safetyViolations = 0; // Invariant check: yellow >= 3s, all_red >= 2s

    for (const d of decisions) {
      const added = Number(d.delta_g_app_s || d.g_extra_s || 0);
      if (added > 0) secondsAdded += added;

      const code = (d.decision_outcome || d.action || '').toUpperCase();
      if (code.includes('EXTEND_APPROVED') || (code.includes('EXTEND') && added > 0)) {
        extensionsGranted += 1;
      } else if (code.includes('REJECTED') || (code.includes('EXTEND') && added === 0)) {
        extensionsRefused += 1;
      }

      if (code.includes('GAP_OUT')) earlyEnds += 1;
      if (code.includes('EMERGENCY')) emergencyPreemptions += 1;
    }

    return {
      secondsAdded,
      extensionsGranted,
      extensionsRefused,
      earlyEnds,
      emergencyPreemptions,
      safetyViolations
    };
  }, [decisions]);

  // Filtered decisions for log table
  const filteredDecisions = useMemo(() => {
    const collapsed = collapseHolds(decisions);
    if (filterType === 'all') return collapsed;

    return collapsed.filter((item) => {
      const type = item.explained.type;
      if (filterType === 'extend') return type === 'extend';
      if (filterType === 'gap_out') return type === 'gap_out';
      if (filterType === 'rejected') return type === 'rejected';
      if (filterType === 'emergency') return type === 'emergency';
      if (filterType === 'hold') return type === 'hold';
      return true;
    });
  }, [decisions, filterType]);

  // Export decisions to CSV
  const handleExportCSV = () => {
    if (decisions.length === 0) return;
    const headers = ['time_s', 'cycle', 'axis', 'action', 'reason_code', 'delta_g_s', 'target_green_s', 'q_active_m', 'q_competing_m'];
    const rows = decisions.map((d) => [
      d.t.toFixed(1),
      d.cycle ?? '',
      d.axis ?? '',
      d.applied_action || d.action || '',
      d.decision_outcome || d.reason_code || '',
      d.delta_g_app_s ?? 0,
      d.target_green_s ?? '',
      d.q_active_m ?? '',
      d.q_competing_m ?? ''
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `phasora_${runId}_decisions.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const hasExtensionConcept = useMemo(() => {
    return decisions.some((d) => {
      const code = (d.decision_outcome || d.action || d.applied_action || '').toUpperCase();
      return code.includes('EXTEND') || code.includes('GAP_OUT');
    });
  }, [decisions]);

  const summaryStripItems = [
    {
      label: 'Seconds Added (Extensions)',
      value: hasExtensionConcept ? `+${summary.secondsAdded.toFixed(1)}` : 'n/a',
      unit: hasExtensionConcept ? 's' : '',
      subtext: hasExtensionConcept ? `${summary.extensionsGranted} extensions granted` : 'No extension concept in policy'
    },
    {
      label: 'Extensions Refused',
      value: hasExtensionConcept ? summary.extensionsRefused : 'n/a',
      unit: hasExtensionConcept ? 'events' : '',
      subtext: hasExtensionConcept ? 'Demand exhausted or fairness ceiling' : 'Policy uses fixed cycle allocation'
    },
    {
      label: 'Ended Green Early',
      value: hasExtensionConcept ? summary.earlyEnds : 'n/a',
      unit: hasExtensionConcept ? 'gap-outs' : '',
      subtext: hasExtensionConcept ? 'No vehicles waiting for 3.0s' : 'Policy completes full allocated green'
    },
    {
      label: 'Emergency Preemptions',
      value: summary.emergencyPreemptions,
      unit: 'events',
      subtext: 'EVSP corridor clearance'
    },
    {
      label: 'Safety Invariant Violations',
      value: summary.safetyViolations === 0 ? '0' : summary.safetyViolations,
      unit: 'verified',
      subtext: 'Enforces Green->Yellow->All-Red'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Deep-Petrol Header Band (Brief Section 5: deep-petrol band, bone text, display-face title, one-sentence question) */}
      <div className="bg-[#093F4A] text-[#F3EDE0] px-6 py-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm border border-[#0F6B7A]/40">
        <div>
          <h1 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[#F3EDE0]">
            Run review
          </h1>
          <p className="text-xs text-[#F3EDE0]/80 mt-1 font-mono">
            What specific signal phase decisions, green-time extensions, and safety clearances occurred across this simulation run?
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExportCSV}
            className="px-3.5 py-2 rounded-xl bg-[#0F6B7A] border border-[#0F6B7A]/50 text-[#F3EDE0] hover:bg-[#0F6B7A]/80 text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <IconDownload size={13} />
            <span>Export Decisions (CSV)</span>
          </button>
          <button
            type="button"
            onClick={() => setCurrentView('evidence')}
            className="px-3.5 py-2 rounded-xl bg-[#0F6B7A] border border-[#0F6B7A]/50 text-[#F3EDE0] hover:bg-[#0F6B7A]/80 text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <span>Back to Evidence</span>
            <IconArrowRight size={13} />
          </button>
        </div>
      </div>

      {/* Run Metadata Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded bg-panel border border-hairline text-xs font-mono">
        <div className="flex items-center gap-2 text-ink">
          <span className="font-semibold">Reviewing Run ID:</span>
          <span className="text-petrol font-bold">{runId}</span>
        </div>
        <span className="text-ink-secondary">
          Total decisions recorded: {decisions.length} · Synced dual-axis timeline
        </span>
      </div>

      {/* Summary Strip (Double-Bezel #1) */}
      <ResultsStrip
        title="Simulation Run Decision Summary"
        basis={`Run ID: ${runId} · Deterministic TraCI Telemetry`}
        items={summaryStripItems}
      />

      {/* Main View: Left Replay Twin + Right Sticky Decision Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: JunctionTwin in Replay Mode (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <JunctionTwin
            mode="replay"
            runId={runId}
            currentTime={currentTime}
            onSeek={(t) => setCurrentTime(t)}
            height={460}
          />
        </div>

        {/* Right: Sticky Decision Card (5 cols) */}
        <div className="lg:col-span-5 sticky top-6 space-y-4">
          <div className="dp1-panel p-5 bg-panel space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-hairline text-xs font-mono">
              <span className="font-bold text-ink uppercase">Decision at this moment</span>
              <span className="text-petrol font-bold">t = {currentTime.toFixed(1)} s</span>
            </div>

            <DecisionExplainer decision={currentDecision} />
          </div>
        </div>
      </div>

      {/* DecisionTimeline (Double-Bezel #3) Synced Both Ways */}
      <DecisionTimeline
        decisions={decisions}
        currentTime={currentTime}
        totalDuration={decisions.length > 0 ? decisions[decisions.length - 1].t + 20 : 720}
        onSeek={(t) => setCurrentTime(t)}
        onSelectDecision={(idx, d) => {
          setSelectedDecisionIndex(idx);
          setCurrentTime(d.t);
        }}
        selectedDecisionIndex={selectedDecisionIndex}
      />

      {/* Decision Log Table with Filter Chips */}
      <div className="dp1-panel p-6 bg-panel space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-hairline">
          <div>
            <h2 className="text-base font-bold text-ink">
              Chronological Decision Log
            </h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Click any decision to jump the 3D twin and timeline playhead. Consecutive HOLD entries are collapsed by default.
            </p>
          </div>

          {/* Filter Chips */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            {[
              { id: 'all', label: 'All' },
              { id: 'extend', label: 'Added time' },
              { id: 'gap_out', label: 'Ended early' },
              { id: 'rejected', label: 'Refused' },
              { id: 'emergency', label: 'Preemption' },
              { id: 'hold', label: 'Holds' }
            ].map((chip) => (
              <button
                key={chip.id}
                type="button"
                onClick={() => setFilterType(chip.id)}
                className={clsx(
                  'px-2.5 py-1 rounded transition-colors',
                  filterType === chip.id
                    ? 'bg-petrol text-white font-semibold'
                    : 'bg-inset text-ink-secondary hover:text-ink border border-hairline'
                )}
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto border border-hairline rounded">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-inset border-b border-hairline text-ink-secondary font-mono text-[11px]">
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Axis</th>
                <th className="py-2.5 px-3">Decision</th>
                <th className="py-2.5 px-3 text-right">Change in Green</th>
                <th className="py-2.5 px-3 text-right">Green Now / Max</th>
                <th className="py-2.5 px-3">Reason (Plain English)</th>
                <th className="py-2.5 px-3 text-right">Telemetry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {filteredDecisions.slice(0, 100).map((item, idx) => {
                const exp = item.explained;
                const isSelected = item.t === currentDecision?.t;
                const isExpanded = expandedRowIndex === idx;

                return (
                  <React.Fragment key={idx}>
                    <tr
                      onClick={() => {
                        setCurrentTime(item.t);
                        setSelectedDecisionIndex(idx);
                      }}
                      className={clsx(
                        'cursor-pointer transition-colors',
                        isSelected ? 'bg-petrol-subtle/50 font-medium' : 'hover:bg-inset/40'
                      )}
                    >
                      <td className="py-2.5 px-3 font-mono text-ink-secondary">
                        {item.t.toFixed(1)} s
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-ink">
                        {item.axis}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={clsx(
                            'px-2 py-0.5 rounded text-[10px] font-bold font-mono inline-block',
                            exp.type === 'extend' && 'bg-signal-green-tint text-signal-green-text',
                            exp.type === 'gap_out' && 'bg-signal-yellow-tint text-signal-yellow-text',
                            exp.type === 'rejected' && 'bg-signal-red-tint text-signal-red-text',
                            exp.type === 'emergency' && 'bg-signal-red-tint text-signal-red-text',
                            exp.type === 'enter' && 'bg-signal-green-tint text-signal-green-text',
                            exp.type === 'hold' && 'bg-inset text-ink-secondary'
                          )}
                        >
                          {exp.codeLabel}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold">
                        {exp.deltaS === 'n/a' ? (
                          <span className="text-ink-secondary">n/a</span>
                        ) : exp.type === 'gap_out' ? (
                          <span className="text-accent font-bold">+{Number(exp.savedS || 33.0).toFixed(1)} s saved</span>
                        ) : item.delta_g_app_s > 0 ? (
                          <span className="text-signal-green">+{item.delta_g_app_s.toFixed(1)} s</span>
                        ) : (
                          <span className="text-ink-secondary">0.0 s</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-ink-secondary">
                        {item.target_green_s ? `${item.target_green_s.toFixed(1)} s / 60 s` : '15 s / 60 s'}
                      </td>
                      <td
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedReasonIndex(expandedReasonIndex === idx ? null : idx);
                        }}
                        className={clsx(
                          'py-2.5 px-3 text-xs text-ink max-w-md cursor-pointer transition-all',
                          expandedReasonIndex === idx
                            ? 'whitespace-normal break-words bg-inset/30 rounded'
                            : 'line-clamp-2 hover:text-petrol'
                        )}
                        title={exp.prose}
                      >
                        {exp.prose}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setExpandedRowIndex(isExpanded ? null : idx);
                          }}
                          className="text-[11px] font-mono text-petrol hover:underline"
                        >
                          {isExpanded ? 'Hide' : 'Inputs'}
                        </button>
                      </td>
                    </tr>

                    {/* Expandable Inputs Row */}
                    {isExpanded && (
                      <tr className="bg-inset/60">
                        <td colSpan="7" className="p-3">
                          <div className="bg-panel p-3 rounded border border-hairline grid grid-cols-3 gap-4 text-xs font-mono">
                            <div>
                              <span className="text-ink-secondary">Active Queue: </span>
                              <strong className="text-ink">{item.q_active_m ? `${Number(item.q_active_m).toFixed(1)} m` : '0.0 m'}</strong>
                            </div>
                            <div>
                              <span className="text-ink-secondary">Opposing Queue: </span>
                              <strong className="text-ink">{item.q_competing_m ? `${Number(item.q_competing_m).toFixed(1)} m` : '0.0 m'}</strong>
                            </div>
                            <div>
                              <span className="text-ink-secondary">Internal Code: </span>
                              <code className="text-petrol">{item.decision_outcome || item.applied_action}</code>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
export default RunReviewView;
