/**
 * Network3DScene.jsx - 3D Road Topology Scene using Three.js & @react-three/fiber
 *
 * Implements Phase 4:
 * - Full 3D road ribbons with width and elevation (surface, flyover deck, underpass mainline)
 * - Crisp lane markings (solid edges, dashed lane dividers, stop lines)
 * - Flyover deck with thickness, barriers, and support pillars with clearance reporting
 * - Ground plane with subtle 10m/50m coordinate grid
 * - Area labels marked "(approximate)"
 * - See-through flyover deck opacity toggle (35% alpha)
 * - Explode 3-Tier View in 3D with vertical tier separation and floating badges
 * - Soft hemisphere light + directional light (shadow-free, legible in dark and light themes)
 * - Performance: merged static geometry, dpr capped at 2, frameloop="demand"
 * - Footer disclaimer: "Modelled elevation; synthetic demand. Never present geometry as surveyed."
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import { compileNetwork3DGeometries, CAMERA_PRESETS } from '../utils/network3dGeometry';

export { CAMERA_PRESETS };

/** Controller component for animated / instant camera preset transitions */
function CameraRig({ preset, onResetComplete }) {
  const { camera } = useThree();
  const controlsRef = useRef();

  useEffect(() => {
    if (!preset) return;
    camera.position.set(...preset.position);
    camera.lookAt(...preset.target);
    if (controlsRef.current) {
      controlsRef.current.target.set(...preset.target);
      controlsRef.current.update();
    }
    if (onResetComplete) onResetComplete();
  }, [preset, camera, onResetComplete]);

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      minDistance={15}
      maxDistance={650}
      maxPolarAngle={Math.PI / 2 - 0.05}
    />
  );
}

/** 3D Meshes group containing road network layers */
function RoadNetworkMeshes({
  geometries,
  isDark = true,
  seeThroughFlyover = false,
  isExploded = false,
  showPillars = true,
  showLabels = true,
}) {
  const { invalidate } = useThree();

  // Invalidate on prop changes so frameloop="demand" re-renders
  useEffect(() => {
    invalidate();
  }, [isDark, seeThroughFlyover, isExploded, showPillars, showLabels, invalidate]);

  // Explode offsets
  const flyoverYOffset = isExploded ? 25.0 : 0.0;
  const underpassYOffset = isExploded ? -18.0 : 0.0;
  const surfaceYOffset = 0.0;

  // Theme palettes
  const colors = useMemo(() => {
    if (isDark) {
      return {
        surfaceRoad: '#1E252B',
        flyoverRoad: '#3E4C59',
        underpassRoad: '#12181C',
        junction: '#1A2126',
        edgeLine: '#F8FAFC',
        dashLine: '#E2E8F0',
        stopLine: '#FFFFFF',
        barriers: '#64748B',
        deckSlab: '#2A343D',
        pillars: '#94A3B8',
        ground: '#0B0F13',
        gridMajor: '#26333D',
        gridMinor: '#141D22',
      };
    }
    return {
      surfaceRoad: '#334155',
      flyoverRoad: '#475569',
      underpassRoad: '#1E293B',
      junction: '#2D3748',
      edgeLine: '#FFFFFF',
      dashLine: '#F1F5F9',
      stopLine: '#FFFFFF',
      barriers: '#64748B',
      deckSlab: '#3B4856',
      pillars: '#94A3B8',
      ground: '#F1F5F9',
      gridMajor: '#CBD5E1',
      gridMinor: '#E2E8F0',
    };
  }, [isDark]);

  const flyoverOpacity = seeThroughFlyover ? 0.35 : 1.0;
  const flyoverTransparent = seeThroughFlyover;

  return (
    <group>
      {/* 1. Ground Plane with subtle grid */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
        <planeGeometry args={[750, 750]} />
        <meshBasicMaterial color={colors.ground} />
      </mesh>
      <gridHelper
        args={[700, 70, colors.gridMajor, colors.gridMinor]}
        position={[0, -0.03, 0]}
      />

      {/* 2. Underpass Mainline Group (shifts down when exploded) */}
      <group position={[0, underpassYOffset, 0]}>
        {geometries.underpassRoads && (
          <mesh geometry={geometries.underpassRoads}>
            <meshStandardMaterial
              color={colors.underpassRoad}
              roughness={0.85}
              metalness={0.1}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, -2.0, 60]} center distanceFactor={120}>
            <div className="px-2.5 py-1 rounded bg-[#0A0E12]/90 border border-blue-500/50 text-blue-400 text-xs font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
              UNDERPASS MAINLINE (-4m)
            </div>
          </Html>
        )}
      </group>

      {/* 3. Surface Roads & Junctions Group */}
      <group position={[0, surfaceYOffset, 0]}>
        {geometries.surfaceRoads && (
          <mesh geometry={geometries.surfaceRoads}>
            <meshStandardMaterial
              color={colors.surfaceRoad}
              roughness={0.8}
              metalness={0.1}
            />
          </mesh>
        )}
        {geometries.junctions && (
          <mesh geometry={geometries.junctions}>
            <meshStandardMaterial
              color={colors.junction}
              roughness={0.8}
              metalness={0.1}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, 1.0, 75]} center distanceFactor={120}>
            <div className="px-2.5 py-1 rounded bg-[#0A0E12]/90 border border-amber-500/50 text-[#FFB020] text-xs font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
              SURFACE LEVEL TIER (0m)
            </div>
          </Html>
        )}
      </group>

      {/* 4. Flyover Deck & Elevated Ramps Group (shifts up when exploded) */}
      <group position={[0, flyoverYOffset, 0]}>
        {geometries.flyoverRoads && (
          <mesh geometry={geometries.flyoverRoads}>
            <meshStandardMaterial
              color={colors.flyoverRoad}
              roughness={0.7}
              metalness={0.15}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
            />
          </mesh>
        )}
        {geometries.deckThickness && (
          <mesh geometry={geometries.deckThickness}>
            <meshStandardMaterial
              color={colors.deckSlab}
              roughness={0.9}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
            />
          </mesh>
        )}
        {geometries.barriers && (
          <mesh geometry={geometries.barriers}>
            <meshStandardMaterial
              color={colors.barriers}
              roughness={0.7}
              metalness={0.2}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, 8.5, 40]} center distanceFactor={120}>
            <div className="px-2.5 py-1 rounded bg-[#0A0E12]/90 border border-purple-500/50 text-purple-300 text-xs font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
              ELEVATED FLYOVER TIER (+7m)
            </div>
          </Html>
        )}
      </group>

      {/* 5. Lane Markings (elevated slightly above pavement) */}
      <group position={[0, isExploded ? surfaceYOffset : 0, 0]}>
        {geometries.markings && (
          <mesh geometry={geometries.markings}>
            <meshBasicMaterial color={colors.edgeLine} />
          </mesh>
        )}
      </group>

      {/* 6. Support Pillars (Ground to underside of flyover deck) */}
      {showPillars && geometries.pillars && (
        <group position={[0, 0, 0]}>
          <mesh geometry={geometries.pillars}>
            <meshStandardMaterial
              color={colors.pillars}
              roughness={0.8}
              metalness={0.15}
              transparent={flyoverTransparent}
              opacity={seeThroughFlyover ? 0.45 : 1.0}
            />
          </mesh>
        </group>
      )}

      {/* 7. Area Location Labels marked "(approximate)" */}
      {showLabels && (
        <group>
          {/* Marathahalli Bridge Center Overpass */}
          <Html position={[0, flyoverYOffset + 8.5, 0]} center distanceFactor={130}>
            <div className="px-2 py-0.5 rounded bg-black/80 border border-amber-500/40 text-amber-300 text-[11px] font-sans font-medium tracking-tight shadow backdrop-blur-sm pointer-events-none select-none whitespace-nowrap">
              Marathahalli Bridge Overpass <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          {/* Varthur Road Arterial East */}
          <Html position={[110, 2.0, 15]} center distanceFactor={140}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Varthur Road (To Whitefield) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          {/* Varthur Road Arterial West */}
          <Html position={[-110, 2.0, 15]} center distanceFactor={140}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              HAL Old Airport Road <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          {/* Outer Ring Road (ORR) North */}
          <Html position={[15, 2.0, -110]} center distanceFactor={140}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Outer Ring Road (To KR Puram) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          {/* Outer Ring Road (ORR) South */}
          <Html position={[15, 2.0, 110]} center distanceFactor={140}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Outer Ring Road (To Bellandur) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          {/* Controlled Surface Junction Node */}
          <Html position={[0, 1.8, 18]} center distanceFactor={120}>
            <div className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-[10px] font-mono font-semibold pointer-events-none select-none whitespace-nowrap flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              marathahalli_tls (Surface Signal)
            </div>
          </Html>
        </group>
      )}
    </group>
  );
}

/**
 * Main Network3DScene Component
 */
export default function Network3DScene({
  isDark = true,
  seeThroughFlyover = true,
  isExploded = false,
  onExplodeToggle = null,
  onSeeThroughToggle = null,
  showControls = true,
  className = '',
}) {
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [activePreset, setActivePreset] = useState(CAMERA_PRESETS.isoSW);
  const [showPillars, setShowPillars] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showPillarReport, setShowPillarReport] = useState(false);

  // Load network3d.json
  useEffect(() => {
    let isMounted = true;
    fetch('/network3d.json')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load /network3d.json`);
        return res.json();
      })
      .then((data) => {
        if (isMounted) {
          setNetworkData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('[Network3DScene] Error loading network3d.json:', err);
          setLoadError(err.message);
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Compile geometries once data is loaded
  const geometries = useMemo(() => {
    if (!networkData) return null;
    return compileNetwork3DGeometries(networkData);
  }, [networkData]);

  if (loading) {
    return (
      <div className="w-full h-full min-h-[480px] flex flex-col items-center justify-center bg-[#0C1316] text-[#AEB8BA] font-mono">
        <div className="w-8 h-8 border-2 border-[#FFB020] border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-sm">Loading 3D Road Geometry from network3d.json...</span>
      </div>
    );
  }

  if (loadError || !geometries) {
    return (
      <div className="w-full h-full min-h-[480px] flex flex-col items-center justify-center bg-[#0C1316] text-rose-400 font-mono p-6">
        <div className="text-base font-bold mb-1">Failed to load 3D Scene</div>
        <div className="text-xs text-slate-400 mb-4">{loadError || 'Geometry compilation failed'}</div>
        <div className="text-xs text-[#AEB8BA]">
          Confirm that <code>frontend/public/network3d.json</code> was generated by <code>scripts/export_network3d.py</code>.
        </div>
      </div>
    );
  }

  const { pillarAudit } = geometries;

  return (
    <div className={`relative w-full h-full select-none overflow-hidden ${className}`}>
      {/* 3D Canvas */}
      <Canvas
        frameloop="demand"
        dpr={Math.min(typeof window !== 'undefined' ? window.devicePixelRatio : 1, 2)}
        camera={{ position: activePreset.position, fov: 45, near: 0.5, far: 2000 }}
        gl={{
          antialias: true,
          powerPreference: 'high-performance',
          alpha: false,
          preserveDrawingBuffer: true,
        }}
        onCreated={({ gl }) => {
          gl.setClearColor(isDark ? '#0B0F13' : '#F1F5F9', 1);
        }}
      >
        {/* Lighting: Soft hemisphere light + single directional light (no heavy shadows) */}
        <hemisphereLight
          skyColor={isDark ? '#E2E8F0' : '#FFFFFF'}
          groundColor={isDark ? '#1E293B' : '#CBD5E1'}
          intensity={isDark ? 0.75 : 0.85}
        />
        <directionalLight
          position={[100, 150, 80]}
          intensity={isDark ? 0.9 : 0.95}
          castShadow={false}
        />
        <ambientLight intensity={isDark ? 0.25 : 0.35} />

        {/* Camera Controller */}
        <CameraRig preset={activePreset} />

        {/* Merged Road Network Meshes */}
        <RoadNetworkMeshes
          geometries={geometries}
          isDark={isDark}
          seeThroughFlyover={seeThroughFlyover}
          isExploded={isExploded}
          showPillars={showPillars}
          showLabels={showLabels}
        />
      </Canvas>

      {/* 3D Overlay Toolbar (Top-Right Camera Presets) */}
      {showControls && (
        <div className="absolute top-3 right-3 flex items-center gap-1.5 z-20">
          <div className="flex items-center bg-[#0C1316]/90 border border-white/15 rounded-full p-0.5 shadow-lg backdrop-blur-md">
            {Object.entries(CAMERA_PRESETS).map(([key, preset]) => (
              <button
                key={key}
                type="button"
                onClick={() => setActivePreset(preset)}
                className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                  activePreset.name === preset.name
                    ? 'bg-[#1A2327] text-[#FFB020] border border-[#FFB020]/30'
                    : 'text-[#AEB8BA] hover:text-white'
                }`}
              >
                {preset.name}
              </button>
            ))}
          </div>

          {/* Pillars Audit Button */}
          <button
            type="button"
            onClick={() => setShowPillarReport((prev) => !prev)}
            className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-all shadow-md backdrop-blur-md flex items-center gap-1 ${
              showPillarReport
                ? 'bg-[#FFB020]/20 text-[#FFB020] border border-[#FFB020]/50'
                : 'bg-[#0C1316]/90 text-[#AEB8BA] hover:bg-[#1A2327] border border-white/15'
            }`}
            title="Inspect Bridge Support Pillars Surface Clearance Audit"
          >
            <span>Pillars Audit</span>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          </button>
        </div>
      )}

      {/* Bottom Floating Footer / Tooltip Bar */}
      <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none z-20">
        {/* Left: Elevation & Provenance Tooltip */}
        <div className="pointer-events-auto flex items-center gap-2 bg-[#0C1316]/90 border border-white/15 rounded-lg px-3 py-1.5 shadow-lg backdrop-blur-md text-xs font-mono">
          <span className="text-[#FFB020] font-bold">3D SCENE</span>
          <span className="text-white/20">|</span>
          <span className="text-[#AEB8BA] text-[11px]">
            Modelled elevation (+7m deck / 0m surface / -4m underpass); synthetic demand.
          </span>
          <span className="text-[10px] text-amber-300/80 italic hidden md:inline">
            (Never present geometry as surveyed)
          </span>
        </div>

        {/* Right: Quick Toggles (See-Through, Explode, Labels) */}
        <div className="pointer-events-auto flex items-center gap-1.5 bg-[#0C1316]/90 border border-white/15 rounded-full p-1 shadow-lg backdrop-blur-md">
          {onSeeThroughToggle && (
            <button
              type="button"
              onClick={onSeeThroughToggle}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                seeThroughFlyover
                  ? 'bg-[#FFB020]/20 text-[#FFB020] border border-[#FFB020]/50'
                  : 'text-[#AEB8BA] hover:text-white'
              }`}
              title="Toggle Flyover Deck Opacity (35% alpha)"
            >
              See-Through Deck
            </button>
          )}

          {onExplodeToggle && (
            <button
              type="button"
              onClick={onExplodeToggle}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                isExploded
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50'
                  : 'text-[#AEB8BA] hover:text-white'
              }`}
              title="Separate layers vertically"
            >
              {isExploded ? 'Collapse Tiers' : 'Explode Tiers'}
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowLabels((prev) => !prev)}
            className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
              showLabels ? 'text-[#FFB020]' : 'text-[#AEB8BA] opacity-60'
            }`}
          >
            Labels
          </button>
        </div>
      </div>

      {/* Pillar Surface Lane Intersection Modal / Inspector */}
      {showPillarReport && (
        <div className="absolute top-14 right-3 w-96 max-w-[calc(100vw-24px)] bg-[#0C1316]/95 border border-amber-500/30 rounded-xl p-4 shadow-2xl backdrop-blur-xl z-30 text-xs font-mono">
          <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-3">
            <span className="font-bold text-amber-300 flex items-center gap-1.5">
              <span>Bridge Pier Surface Lane Audit</span>
            </span>
            <button
              type="button"
              onClick={() => setShowPillarReport(false)}
              className="text-slate-400 hover:text-white text-sm px-1.5 py-0.5 rounded"
            >
              ✕
            </button>
          </div>

          <p className="text-[11px] text-slate-300 mb-2 leading-relaxed">
            Evaluates regular spacing candidate piers against all surface lane polylines.
          </p>

          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="p-2 rounded bg-emerald-950/40 border border-emerald-500/30">
              <div className="text-[10px] text-slate-400">Clear Piers (Rendered)</div>
              <div className="text-lg font-bold text-emerald-400">{pillarAudit.clearPillars.length}</div>
              <div className="text-[9px] text-emerald-400/80">Clearance &gt; 10m from lanes</div>
            </div>
            <div className="p-2 rounded bg-rose-950/40 border border-rose-500/30">
              <div className="text-[10px] text-slate-400">Intersecting Grid Piers</div>
              <div className="text-lg font-bold text-rose-400">{pillarAudit.intersectingPillars.length}</div>
              <div className="text-[9px] text-rose-400/80">Conflicts with surface lanes</div>
            </div>
          </div>

          <div className="text-[11px] font-bold text-slate-200 mb-1">Intersecting Grid Locations:</div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {pillarAudit.intersectingPillars.map((p, idx) => (
              <div key={idx} className="p-2 rounded bg-black/40 border border-rose-500/20 text-[10px]">
                <div className="flex justify-between text-rose-300 font-semibold mb-0.5">
                  <span>Station X = {p.threeX}m (Z = 0m)</span>
                  <span>Deck {p.deckElevation}m</span>
                </div>
                <div className="text-slate-400">
                  Collides with {p.conflicts.length} surface lane(s):
                </div>
                <ul className="list-disc list-inside text-rose-200/90 pl-1 mt-0.5 space-y-0.5">
                  {p.conflicts.map((c, cIdx) => (
                    <li key={cIdx}>
                      <code>{c.laneId}</code> (penetration: {c.penetrationM}m)
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-3 pt-2 border-t border-white/10 text-[10px] text-slate-400 leading-tight">
            * Civil Engineering Rationale: The central 30m overpass spans directly over the ORR mainline and surface legs. Only clear portal piers are erected in the rendered scene.
          </div>
        </div>
      )}
    </div>
  );
}
