import React from 'react';
import { IsometricIntersection } from './IsometricIntersection';

/**
 * JunctionTwin
 * 
 * Renders the original, verified 2.5D Isometric road simulation (IsometricIntersection)
 * that models the 1:1 SUMO TraCI Marathahalli Bridge junction geometry.
 */
export function JunctionTwin({
  mode = 'ambient', // 'ambient' | 'live' | 'replay' | 'overview'
  runId = 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121',
  liveTelemetry = null,
  currentTime = null,
  onSeek = null,
  onFrameUpdate = null,
  className = '',
  height = 460,
  network = 'marathahalli',
  isExploded = false,
  onExplodeToggle = null,
  soloTier = null,
  onSoloTierChange = null,
  initialViewMode = 'isometric',
  showControls = true,
}) {
  const isLive = mode === 'live';
  const effectiveRunId = runId || 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121';

  return (
    <div className={`double-bezel-outer ${className}`}>
      <div className="double-bezel-inner bg-panel overflow-hidden rounded-xl border border-hairline shadow-sm">
        <IsometricIntersection
          runId={effectiveRunId}
          network={network}
          liveTelemetry={liveTelemetry}
          isLiveMode={isLive}
          currentTime={currentTime}
          onSeek={onSeek}
          onFrameUpdate={onFrameUpdate}
          height={height}
          isExploded={isExploded}
          onExplodeToggle={onExplodeToggle}
          soloTier={soloTier}
          onSoloTierChange={onSoloTierChange}
          initialViewMode={initialViewMode}
          showControls={showControls}
          modeLabel={
            mode === 'live'
              ? 'Live simulation view'
              : mode === 'replay'
              ? 'Replay'
              : 'Snapshot'
          }
          className="w-full"
        />
      </div>
    </div>
  );
}

export default JunctionTwin;
