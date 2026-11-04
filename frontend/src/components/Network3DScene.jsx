/**
 * Network3DScene.jsx - 3D Road Topology, Vehicles, Signals & Queues Scene
 *
 * Implements Phase 4 & Phase 5:
 * - Full 3D road ribbons with width and elevation (surface, flyover deck, underpass mainline)
 * - Crisp lane markings (solid edges, dashed lane dividers, stop lines)
 * - Flyover deck with thickness, barriers, and support pillars with clearance reporting
 * - Low-Poly Vehicles using InstancedMesh (car, bus, truck, two_wheeler, ambulance)
 * - One-tick buffer interpolation (no extrapolation, clamped at alpha = 1.0)
 * - Vehicle exaggeration control (1x true scale, 2x default, 3x max)
 * - High-contrast color scheme (moving = cool blue, queued = warm orange, ambulance = rose/white)
 * - Flyover vehicles sit on the elevated deck (+6.8m)
 * - 3D Signal heads at stop lines derived from actual SUMO signal state strings (never client timers)
 * - Distinct yellow and all-red clearance signals
 * - Countdown only if target green provided; otherwise elapsed time
 * - 3D Translucent Queue Bars over the 24.9m detector spans
 * - Queue sensor statuses: CONFIRMED_ZERO, MEASURING, SATURATED warning, OFFLINE (never zero)
 * - Decision callout displaying logged reason with separate requested vs applied increments
 * - Dynamic mode labelling: "Live simulation" vs "Replay" vs "Snapshot"
 * - Soft hemisphere light + directional light (shadow-free, dark and light theme palettes)
 * - Performance: merged static geometry (8 meshes), dpr capped at 2, frameloop="demand"
 * - Footer disclaimer: "Modelled elevation; synthetic demand. Never present geometry as surveyed."
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import { compileNetwork3DGeometries, CAMERA_PRESETS, sumoToThree } from '../utils/network3dGeometry.js';
import {
  createLowPolyVehicleGeometry,
  classifyVehicleType,
  interpolateVehicle,
  updateVehicleInstancedMesh,
} from '../utils/vehicle3dMesh.js';
import {
  SIGNAL_APPROACH_CONFIG,
  decodeSignalStateString,
  computeSignalTimer,
  getApproachQueueDisplay,
} from '../utils/signalAndQueue3d.js';

export { CAMERA_PRESETS };

/** Controller component for animated / instant camera preset transitions */
function CameraRig({ preset, onResetComplete, vehicles = [] }) {
  const { camera } = useThree();
  const controlsRef = useRef();

  useEffect(() => {
    if (!preset) return;

    if (preset.name === 'Fit to junction' || preset.name === 'Fit') {
      // Dynamic framing: adapt to active vehicles and junction area
      let minX = -45, maxX = 45, minZ = -15, maxZ = 50;
      if (vehicles && vehicles.length > 0) {
        for (const v of vehicles) {
          if (v && typeof v.x === 'number' && typeof v.y === 'number') {
            const [vx, , vz] = sumoToThree(v.x, v.y, v.z || 0.0);
            minX = Math.min(minX, vx);
            maxX = Math.max(maxX, vx);
            minZ = Math.min(minZ, vz);
            maxZ = Math.max(maxZ, vz);
          }
        }
      }
      const cx = (minX + maxX) / 2;
      const cz = (minZ + maxZ) / 2;
      const span = Math.max(maxX - minX, maxZ - minZ, 90);
      const dist = Math.max(85, span * 0.95);

      const posX = cx + dist * 0.65;
      const posY = dist * 0.55;
      const posZ = cz + dist * 0.75;

      camera.position.set(posX, posY, posZ);
      camera.lookAt(cx, 2, cz);
      if (controlsRef.current) {
        controlsRef.current.target.set(cx, 2, cz);
        controlsRef.current.update();
      }
    } else {
      camera.position.set(...preset.position);
      camera.lookAt(...preset.target);
      if (controlsRef.current) {
        controlsRef.current.target.set(...preset.target);
        controlsRef.current.update();
      }
    }
    if (onResetComplete) onResetComplete();
  }, [preset, camera, vehicles, onResetComplete]);

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      minDistance={10}
      maxDistance={800}
      maxPolarAngle={Math.PI / 2 - 0.02}
    />
  );
}

/** 3D Meshes group containing static road network layers */
function RoadNetworkMeshes({
  geometries,
  isDark = true,
  seeThroughFlyover = false,
  isExploded = false,
  showPillars = true,
  showLabels = true,
  wireframe = false,
}) {
  const { invalidate } = useThree();

  useEffect(() => {
    invalidate();
  }, [geometries, isDark, seeThroughFlyover, isExploded, showPillars, showLabels, wireframe, invalidate]);

  const flyoverYOffset = isExploded ? 25.0 : 0.0;
  const underpassYOffset = isExploded ? -18.0 : 0.0;
  const surfaceYOffset = 0.0;

  const colors = useMemo(() => {
    if (isDark) {
      return {
        background: '#0D1417',
        surfaceRoad: '#2D3C49',
        flyoverRoad: '#3E5162',
        underpassRoad: '#1F2932',
        junction: '#334453',
        edgeLine: '#FFFFFF',
        dashLine: '#FFFFFF',
        stopLine: '#FFFFFF',
        barriers: '#647585',
        deckSlab: '#4A5B6B',
        pillars: '#7D90A1',
        ground: '#080C0E',
        gridMajor: '#172228',
        gridMinor: '#0F161A',
        roadEmissive: '#101921',
      };
    }
    // High-contrast refined light theme matching 2.5D palette
    return {
      background: '#F1ECE1',
      surfaceRoad: '#344555',
      flyoverRoad: '#46586A',
      underpassRoad: '#222F3B',
      junction: '#3C4E5E',
      edgeLine: '#FFFFFF',
      dashLine: '#FFFFFF',
      stopLine: '#FFFFFF',
      barriers: '#7A8C9C',
      deckSlab: '#5A6C7C',
      pillars: '#64748B',
      ground: '#E5DFD2',
      gridMajor: '#D4CBB8',
      gridMinor: '#E2D9C8',
      roadEmissive: '#0C141B',
    };
  }, [isDark]);

  const flyoverOpacity = seeThroughFlyover ? 0.55 : 1.0;
  const flyoverTransparent = seeThroughFlyover;

  return (
    <group>
      {/* 1. Ground Plane with subtle grid */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.25, 0]} receiveShadow>
        <planeGeometry args={[1200, 1200]} />
        <meshBasicMaterial color={colors.ground} depthWrite={true} />
      </mesh>
      <gridHelper
        args={[800, 80, colors.gridMajor, colors.gridMinor]}
        position={[0, -0.22, 0]}
      />

      {/* 2. Underpass Mainline Group */}
      <group position={[0, underpassYOffset, 0]}>
        {geometries.underpassRoads && (
          <mesh geometry={geometries.underpassRoads}>
            <meshStandardMaterial
              color={colors.underpassRoad}
              emissive={colors.roadEmissive}
              emissiveIntensity={0.3}
              side={THREE.DoubleSide}
              roughness={0.7}
              metalness={0.05}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, -2.0, 60]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-[#0A0E12]/90 border border-blue-500/50 text-blue-400 text-[10px] font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
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
              emissive={colors.roadEmissive}
              emissiveIntensity={0.35}
              side={THREE.DoubleSide}
              roughness={0.65}
              metalness={0.05}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {geometries.junctions && (
          <mesh geometry={geometries.junctions}>
            <meshStandardMaterial
              color={colors.junction}
              emissive={colors.roadEmissive}
              emissiveIntensity={0.35}
              side={THREE.DoubleSide}
              roughness={0.65}
              metalness={0.05}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, 1.0, 75]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-[#0A0E12]/90 border border-amber-500/50 text-[#FFB020] text-[10px] font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
              SURFACE LEVEL TIER (0m)
            </div>
          </Html>
        )}
      </group>

      {/* 4. Flyover Deck & Elevated Ramps Group */}
      <group position={[0, flyoverYOffset, 0]}>
        {geometries.flyoverRoads && (
          <mesh geometry={geometries.flyoverRoads}>
            <meshStandardMaterial
              color={colors.flyoverRoad}
              emissive={colors.roadEmissive}
              emissiveIntensity={0.4}
              side={THREE.DoubleSide}
              roughness={0.6}
              metalness={0.08}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {geometries.deckThickness && (
          <mesh geometry={geometries.deckThickness}>
            <meshStandardMaterial
              color={colors.deckSlab}
              side={THREE.DoubleSide}
              roughness={0.9}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {geometries.barriers && (
          <mesh geometry={geometries.barriers}>
            <meshStandardMaterial
              color={colors.barriers}
              side={THREE.DoubleSide}
              roughness={0.7}
              metalness={0.2}
              transparent={flyoverTransparent}
              opacity={flyoverOpacity}
              depthWrite={!seeThroughFlyover}
              wireframe={wireframe}
            />
          </mesh>
        )}
        {isExploded && (
          <Html position={[0, 8.5, 40]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-[#0A0E12]/90 border border-purple-500/50 text-purple-300 text-[10px] font-mono font-bold tracking-wide shadow-lg pointer-events-none select-none backdrop-blur-sm whitespace-nowrap">
              ELEVATED FLYOVER TIER (+7m)
            </div>
          </Html>
        )}
      </group>

      {/* 5. Lane Markings */}
      <group position={[0, isExploded ? surfaceYOffset : 0, 0]}>
        {geometries.markings && (
          <mesh geometry={geometries.markings}>
            <meshBasicMaterial
              color="#FFFFFF"
              side={THREE.DoubleSide}
              polygonOffset
              polygonOffsetFactor={-4}
              polygonOffsetUnits={-4}
              wireframe={wireframe}
            />
          </mesh>
        )}
      </group>

      {/* 6. Support Pillars */}
      {showPillars && geometries.pillars && (
        <group position={[0, 0, 0]}>
          <mesh geometry={geometries.pillars}>
            <meshStandardMaterial
              color={colors.pillars}
              roughness={0.8}
              metalness={0.15}
              transparent={flyoverTransparent}
              opacity={seeThroughFlyover ? 0.45 : 1.0}
              wireframe={wireframe}
            />
          </mesh>
        </group>
      )}

      {/* 7. Area Location Labels marked "(approximate)" */}
      {showLabels && (
        <group>
          <Html position={[0, flyoverYOffset + 8.5, 0]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-black/80 border border-amber-500/40 text-amber-300 text-[10px] font-sans font-medium tracking-tight shadow backdrop-blur-sm pointer-events-none select-none whitespace-nowrap">
              Marathahalli Bridge Overpass <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          <Html position={[140, 2.0, 18]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Varthur Road (To Whitefield) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          <Html position={[-140, 2.0, 18]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              HAL Old Airport Road <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          <Html position={[0, 2.0, -140]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Outer Ring Road (To KR Puram) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          <Html position={[0, 2.0, 160]} center distanceFactor={80}>
            <div className="px-2 py-0.5 rounded bg-black/75 border border-white/20 text-slate-200 text-[10px] font-sans font-medium pointer-events-none select-none whitespace-nowrap">
              Outer Ring Road (To Bellandur) <span className="text-[9px] opacity-75">(approximate)</span>
            </div>
          </Html>

          <Html position={[0, 6.5, 18]} center distanceFactor={70}>
            <div className="px-2 py-0.5 rounded bg-emerald-950/85 border border-emerald-500/50 text-emerald-300 text-[9px] font-mono font-semibold pointer-events-none select-none whitespace-nowrap flex items-center gap-1 shadow-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              marathahalli_tls (Surface Signal)
            </div>
          </Html>
        </group>
      )}
    </group>
  );
}

/** 3D Vehicles Layer using InstancedMesh for 5 types */
function Vehicles3DLayer({
  vehicles = [],
  prevVehicles = [],
  interpolationAlpha = 1.0,
  vehicleScale = 2.0,
  isDark = true,
  isExploded = false,
}) {
  const { invalidate } = useThree();
  const carMeshRef = useRef();
  const busMeshRef = useRef();
  const truckMeshRef = useRef();
  const twoWheelerMeshRef = useRef();
  const ambulanceMeshRef = useRef();

  const vehicleGeoms = useMemo(
    () => ({
      car: createLowPolyVehicleGeometry('car'),
      bus: createLowPolyVehicleGeometry('bus'),
      truck: createLowPolyVehicleGeometry('truck'),
      two_wheeler: createLowPolyVehicleGeometry('two_wheeler'),
      ambulance: createLowPolyVehicleGeometry('ambulance'),
    }),
    []
  );

  const prevMap = useMemo(() => {
    const m = new Map();
    for (const v of prevVehicles) {
      if (v && v.id) m.set(v.id, v);
    }
    return m;
  }, [prevVehicles]);

  useEffect(() => {
    const buckets = {
      car: [],
      bus: [],
      truck: [],
      two_wheeler: [],
      ambulance: [],
    };

    for (const v of vehicles) {
      if (!v) continue;
      const prevV = prevMap.get(v.id);
      const interpolated = prevV ? interpolateVehicle(prevV, v, interpolationAlpha) : v;
      const type = classifyVehicleType(interpolated);
      if (buckets[type]) {
        buckets[type].push(interpolated);
      } else {
        buckets.car.push(interpolated);
      }
    }

    const tierY = isExploded ? 25.0 : 0.0;
    updateVehicleInstancedMesh(carMeshRef.current, buckets.car, vehicleScale, isDark, tierY);
    updateVehicleInstancedMesh(busMeshRef.current, buckets.bus, vehicleScale, isDark, tierY);
    updateVehicleInstancedMesh(truckMeshRef.current, buckets.truck, vehicleScale, isDark, tierY);
    updateVehicleInstancedMesh(twoWheelerMeshRef.current, buckets.two_wheeler, vehicleScale, isDark, tierY);
    updateVehicleInstancedMesh(ambulanceMeshRef.current, buckets.ambulance, vehicleScale, isDark, tierY);

    invalidate();
  }, [vehicles, prevMap, interpolationAlpha, vehicleScale, isDark, isExploded, invalidate]);

  return (
    <group>
      <instancedMesh ref={carMeshRef} args={[vehicleGeoms.car, null, 600]}>
        <meshStandardMaterial roughness={0.3} metalness={0.15} />
      </instancedMesh>
      <instancedMesh ref={busMeshRef} args={[vehicleGeoms.bus, null, 200]}>
        <meshStandardMaterial roughness={0.3} metalness={0.15} />
      </instancedMesh>
      <instancedMesh ref={truckMeshRef} args={[vehicleGeoms.truck, null, 200]}>
        <meshStandardMaterial roughness={0.35} metalness={0.15} />
      </instancedMesh>
      <instancedMesh ref={twoWheelerMeshRef} args={[vehicleGeoms.two_wheeler, null, 400]}>
        <meshStandardMaterial roughness={0.3} metalness={0.1} />
      </instancedMesh>
      <instancedMesh ref={ambulanceMeshRef} args={[vehicleGeoms.ambulance, null, 50]}>
        <meshStandardMaterial roughness={0.2} metalness={0.25} emissive="#ef4444" emissiveIntensity={0.35} />
      </instancedMesh>
    </group>
  );
}

/** 3D Traffic Signals Layer */
function TrafficSignals3DLayer({
  trafficLightState = 'rrrrGGGgrrrrGGGg',
  adaptiveDecision = null,
  activePhase = 'GREEN',
  simTime = 0,
  showLabels = true,
}) {
  const decoded = useMemo(() => decodeSignalStateString(trafficLightState), [trafficLightState]);
  const timer = useMemo(
    () => computeSignalTimer(adaptiveDecision, activePhase, simTime),
    [adaptiveDecision, activePhase, simTime]
  );

  return (
    <group>
      {Object.entries(SIGNAL_APPROACH_CONFIG).map(([appKey, cfg]) => {
        const appState = decoded.approaches[appKey] || { colorName: 'RED', hex: '#ef4444' };
        const isGreen = appState.colorName === 'GREEN';
        const isYellow = appState.colorName === 'YELLOW';
        const isRed = appState.colorName === 'RED' || appState.colorName === 'ALL_RED';
        const isAllRed = decoded.isAllRed;

        const [px, , pz] = cfg.signalHeadPos;

        return (
          <group key={appKey} position={[px, 0, pz]} rotation={[0, cfg.rotationY, 0]}>
            {/* Pole */}
            <mesh position={[0, 2.25, 0]}>
              <cylinderGeometry args={[0.08, 0.1, 4.5, 12]} />
              <meshStandardMaterial color="#334155" metalness={0.6} roughness={0.3} />
            </mesh>

            {/* Signal Head Housing */}
            <group position={[0, 4.2, 0.2]}>
              <mesh>
                <boxGeometry args={[0.6, 1.5, 0.35]} />
                <meshStandardMaterial color="#0f172a" roughness={0.6} metalness={0.2} />
              </mesh>

              {/* Red Bulb */}
              <mesh position={[0, 0.45, 0.18]}>
                <sphereGeometry args={[0.16, 16, 16]} />
                <meshStandardMaterial
                  color={isRed ? (isAllRed ? '#dc2626' : '#D6453D') : '#3f1414'}
                  emissive={isRed ? '#D6453D' : '#000000'}
                  emissiveIntensity={isRed ? 3.0 : 0.05}
                  roughness={0.2}
                />
              </mesh>

              {/* Yellow Bulb */}
              <mesh position={[0, 0.0, 0.18]}>
                <sphereGeometry args={[0.16, 16, 16]} />
                <meshStandardMaterial
                  color={isYellow ? '#F2C230' : '#3a2e0a'}
                  emissive={isYellow ? '#F2C230' : '#000000'}
                  emissiveIntensity={isYellow ? 3.0 : 0.05}
                  roughness={0.2}
                />
              </mesh>

              {/* Green Bulb */}
              <mesh position={[0, -0.45, 0.18]}>
                <sphereGeometry args={[0.16, 16, 16]} />
                <meshStandardMaterial
                  color={isGreen ? '#2FA866' : '#0a2e14'}
                  emissive={isGreen ? '#2FA866' : '#000000'}
                  emissiveIntensity={isGreen ? 3.0 : 0.05}
                  roughness={0.2}
                />
              </mesh>

              {/* Floating Head Tag */}
              {showLabels && (
                <Html position={[0, 1.1, 0]} center distanceFactor={50} occlude>
                  <div
                    className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold shadow backdrop-blur-md whitespace-nowrap flex items-center gap-1 ${
                      isGreen
                        ? 'bg-emerald-950/90 text-emerald-300 border border-emerald-500/60'
                        : isYellow
                        ? 'bg-amber-950/90 text-amber-300 border border-amber-500/60'
                        : 'bg-rose-950/90 text-rose-300 border border-rose-500/60'
                    }`}
                  >
                    <span>{appKey}</span>
                    <span className="opacity-40">|</span>
                    <span className="font-extrabold">{timer.text}</span>
                    {isAllRed && <span className="text-red-400 font-extrabold">[ALL-RED]</span>}
                  </div>
                </Html>
              )}
            </group>
          </group>
        );
      })}
    </group>
  );
}

/** 3D Translucent Queue Bars Layer */
function QueueBars3DLayer({ approachQueues = null, queues_m = {}, gtExtQueues = {}, detFull = {}, wireframe = false, showLabels = true }) {
  return (
    <group>
      {Object.entries(SIGNAL_APPROACH_CONFIG).map(([appKey, cfg]) => {
        const display = getApproachQueueDisplay(appKey, approachQueues, queues_m);
        const { renderQueueM, queue_m, vehCount, style, isOffline, isSaturated } = display;
        const extQueue = gtExtQueues ? (gtExtQueues[appKey] ?? gtExtQueues[`gt_ext_q_${appKey}`]) : null;
        const isDetFull = detFull ? (detFull[appKey] ?? detFull[`det_full_${appKey}`] ?? queue_m >= 23.8) : (queue_m >= 23.8);

        const halfLen = Math.max(0.5, renderQueueM) / 2;
        let posX = cfg.stopLinePos[0];
        let posZ = cfg.stopLinePos[2];
        let barWidth = cfg.width;
        let barLength = Math.max(0.5, renderQueueM);

        if (cfg.axisDir[2] !== 0) {
          posZ = cfg.stopLinePos[2] - cfg.axisDir[2] * halfLen;
        } else {
          posX = cfg.stopLinePos[0] - cfg.axisDir[0] * halfLen;
          const tmp = barWidth;
          barWidth = barLength;
          barLength = tmp;
        }

        const labelPos = [
          cfg.stopLinePos[0] - cfg.axisDir[0] * 12.0,
          2.0,
          cfg.stopLinePos[2] - cfg.axisDir[2] * 12.0,
        ];

        return (
          <group key={appKey}>
            {/* Translucent 3D Volume Bar */}
            <mesh position={[posX, 0.4, posZ]}>
              <boxGeometry args={[barWidth, 0.8, barLength]} />
              <meshStandardMaterial
                color={style.color}
                transparent
                opacity={style.fillOpacity}
                roughness={0.3}
                metalness={0.1}
                wireframe={isOffline || wireframe}
                depthWrite={false}
              />
            </mesh>

            {/* Approach Metric Floating Label: only when queue active or warning/offline */}
            {showLabels && (queue_m > 0.5 || (typeof extQueue === 'number' && extQueue > 0.5) || isSaturated || isDetFull || isOffline) && (
              <Html position={labelPos} center distanceFactor={55} occlude>
                <div
                  className={`px-2 py-0.5 rounded shadow backdrop-blur-md text-[10px] font-mono pointer-events-none select-none border whitespace-nowrap ${
                    isOffline
                      ? 'bg-slate-900/90 text-slate-300 border-slate-500/60'
                      : isSaturated || isDetFull
                      ? 'bg-amber-950/95 text-amber-300 border-amber-500/80 animate-pulse'
                      : 'bg-black/85 text-white border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold">
                    <span>
                      {appKey}: {queue_m.toFixed(1)}m
                    </span>
                    {typeof extQueue === 'number' && (
                      <span className="text-amber-300 font-semibold">
                        | GT: {extQueue.toFixed(1)}m
                      </span>
                    )}
                    <span className="opacity-40">|</span>
                    <span className="text-slate-300">{vehCount} vehs</span>
                  </div>
                </div>
              </Html>
            )}
          </group>
        );
      })}
    </group>
  );
}

/** 3D Decision Event Callout floating above marathahalli_tls */
function DecisionCallout3D({ decision, showLabels = true }) {
  if (!decision || !showLabels) return null;

  return (
    <Html position={[0, 14.0, 18.0]} center distanceFactor={75}>
      <div className="px-3 py-2 rounded-xl bg-[#0C1316]/95 border border-amber-500/60 shadow-2xl backdrop-blur-xl text-xs font-mono max-w-sm pointer-events-none select-none text-slate-200">
        <div className="flex items-center justify-between gap-3 pb-1 border-b border-white/15 mb-1.5">
          <span className="font-bold text-amber-300 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>
              {decision.axis || 'SIGNAL'}: {decision.action || decision.decision_outcome || 'DECISION'}
            </span>
          </span>
          <span className="text-[10px] text-slate-400">t={decision.t ?? 0}s</span>
        </div>

        <p className="text-[11px] text-slate-200 mb-2 leading-tight">
          {decision.reason || 'Phase extension evaluated'}
        </p>

        {/* Separated Requested vs Applied Increments */}
        <div className="flex items-center gap-2 pt-1 border-t border-white/10 text-[10px]">
          <span className="px-1.5 py-0.5 rounded bg-blue-950/80 border border-blue-500/40 text-blue-300">
            Req: +{decision.delta_g_req_s ?? 0}s
          </span>
          <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 font-bold">
            App: +{decision.delta_g_app_s ?? 0}s
          </span>
          {decision.target_green_s !== undefined && (
            <span className="text-slate-400 ml-auto">Target: {decision.target_green_s}s</span>
          )}
        </div>
      </div>
    </Html>
  );
}

function DebugSceneHelper({ enabled }) {
  if (!enabled) return null;
  return (
    <group>
      <axesHelper args={[35]} />
      <gridHelper args={[300, 30, '#f59e0b', '#334155']} position={[0, 0.05, 0]} />
    </group>
  );
}

function WebGLEventHandler({ onContextLost }) {
  const { gl } = useThree();
  useEffect(() => {
    const handleLost = (e) => {
      e.preventDefault();
      console.warn('[Network3DScene] WebGL context lost!');
      if (onContextLost) onContextLost(e);
    };
    const el = gl.domElement;
    el.addEventListener('webglcontextlost', handleLost, false);
    return () => el.removeEventListener('webglcontextlost', handleLost);
  }, [gl, onContextLost]);
  return null;
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
  showLabels: propShowLabels = null,
  className = '',
  // Phase 5 additions:
  activeFrame = null,
  prevFrame = null,
  interpolationAlpha = 1.0,
  vehicleScale = 2.0,
  onVehicleScaleChange = null,
  trafficLightState = 'rrrrGGGgrrrrGGGg',
  activePhase = 'GREEN',
  approachQueues = null,
  queues_m = {},
  gtExtQueues = {},
  detFull = {},
  adaptiveDecision = null,
  simTime = 0,
  isLiveMode = false,
  runId = null,
  modeLabel = null,
  activePreset: propActivePreset = null,
  onPresetChange = null,
  onContextLost = null,
}) {
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [internalPreset, setInternalPreset] = useState(CAMERA_PRESETS.iso || CAMERA_PRESETS.isoSW);
  const activePreset = propActivePreset || internalPreset;

  const setActivePreset = useCallback(
    (preset) => {
      setInternalPreset(preset);
      if (onPresetChange) onPresetChange(preset);
    },
    [onPresetChange]
  );

  const [showPillars, setShowPillars] = useState(true);
  const [internalShowLabels, setInternalShowLabels] = useState(true);
  const showLabels = propShowLabels !== null ? propShowLabels : internalShowLabels;
  const setShowLabels = setInternalShowLabels;
  const [showPillarReport, setShowPillarReport] = useState(false);

  // Debug overlay & wireframe toggles (Keyboard 'd' and 'w')
  const [debugMode, setDebugMode] = useState(false);
  const [wireframeMode, setWireframeMode] = useState(false);
  const [fps, setFps] = useState(60);
  const frameTimesRef = useRef([]);

  useEffect(() => {
    let animId;
    let lastTime = performance.now();
    const tick = (now) => {
      const dt = now - lastTime;
      lastTime = now;
      if (dt > 0) {
        frameTimesRef.current.push(1000 / dt);
        if (frameTimesRef.current.length > 30) frameTimesRef.current.shift();
        const avg = Math.round(
          frameTimesRef.current.reduce((a, b) => a + b, 0) / frameTimesRef.current.length
        );
        setFps(avg);
      }
      animId = requestAnimationFrame(tick);
    };
    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'd' || e.key === 'D') {
        setDebugMode((prev) => !prev);
      } else if (e.key === 'w' || e.key === 'W') {
        setWireframeMode((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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

  const geometries = useMemo(() => {
    if (!networkData) return null;
    return compileNetwork3DGeometries(networkData);
  }, [networkData]);

  // Derived labelling: "Live simulation" vs "Replay" vs "Snapshot"
  const resolvedLabel = useMemo(() => {
    if (modeLabel) return modeLabel;
    if (isLiveMode) return 'Live simulation';
    if (runId) return 'Replay';
    return 'Snapshot';
  }, [modeLabel, isLiveMode, runId]);

  const currentVehicles = activeFrame?.vehicles || [];
  const previousVehicles = prevFrame?.vehicles || [];

  const vehicleCounts = useMemo(() => {
    const counts = { car: 0, bus: 0, truck: 0, two_wheeler: 0, ambulance: 0 };
    for (const v of currentVehicles) {
      const t = classifyVehicleType(v);
      if (counts[t] !== undefined) counts[t]++;
      else counts.car++;
    }
    return counts;
  }, [currentVehicles]);

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
        <div className="text-xs text-[#AEB8BA]">{loadError || 'Missing geometry compilation.'}</div>
      </div>
    );
  }

  const { pillarAudit } = geometries;

  return (
    <div className={`relative w-full h-full overflow-hidden select-none ${className}`}>
      {/* Three.js R3F Canvas */}
      <Canvas
        frameloop="always"
        dpr={Math.min(typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1, 2)}
        camera={{ position: activePreset.position, fov: 45, near: 1.0, far: 5000.0 }}
        className="w-full h-full"
      >
        <color attach="background" args={[isDark ? '#0D1417' : '#F1ECE1']} />

        {/* Crisp balanced tactical lighting */}
        <ambientLight intensity={1.5} color="#FFFFFF" />
        <hemisphereLight
          skyColor={isDark ? '#7DD3FC' : '#FFFFFF'}
          groundColor={isDark ? '#0F172A' : '#CBD5E1'}
          intensity={0.8}
        />
        <directionalLight position={[70, 140, 60]} intensity={1.8} color="#FFFFFF" castShadow={false} />
        <directionalLight position={[-70, 90, -50]} intensity={1.0} color="#94A3B8" castShadow={false} />

        {/* WebGL Event Handler */}
        <WebGLEventHandler onContextLost={onContextLost} />

        {/* Interactive Camera Controller */}
        <CameraRig preset={activePreset} vehicles={currentVehicles} />

        {/* Debug Grid & Axes Helper */}
        <DebugSceneHelper enabled={debugMode} />

        {/* 1. Road ribbons, markings, deck slab and support pillars */}
        <RoadNetworkMeshes
          geometries={geometries}
          isDark={isDark}
          seeThroughFlyover={seeThroughFlyover}
          isExploded={isExploded}
          showPillars={showPillars}
          showLabels={showLabels}
          wireframe={wireframeMode}
        />

        {/* 2. Phase 5 Vehicles Layer (InstancedMesh) */}
        <Vehicles3DLayer
          vehicles={currentVehicles}
          prevVehicles={previousVehicles}
          interpolationAlpha={interpolationAlpha}
          vehicleScale={vehicleScale}
          isDark={isDark}
          isExploded={isExploded}
        />

        {/* 3. Phase 5 Traffic Signals Layer */}
        <TrafficSignals3DLayer
          trafficLightState={trafficLightState}
          adaptiveDecision={adaptiveDecision}
          activePhase={activePhase}
          simTime={simTime}
          showLabels={showLabels}
        />

        {/* 4. Phase 5 Queue Bars Layer */}
        <QueueBars3DLayer
          approachQueues={approachQueues}
          queues_m={queues_m}
          gtExtQueues={gtExtQueues}
          detFull={detFull}
          wireframe={wireframeMode}
          showLabels={showLabels}
        />

        {/* 5. Phase 5 Decision Event Callout */}
        <DecisionCallout3D decision={adaptiveDecision} showLabels={showLabels} />
      </Canvas>

      {/* Real-Time Debug HUD Overlay (Keyboard 'd' to toggle, 'w' for wireframe) */}
      {debugMode && (
        <div className="absolute top-16 left-3 bg-[#0C1316]/95 border border-amber-500/60 rounded-xl p-3 shadow-2xl backdrop-blur-xl z-30 text-xs font-mono max-w-xs text-slate-200 pointer-events-auto">
          <div className="flex items-center justify-between pb-1.5 border-b border-white/10 mb-2">
            <span className="font-bold text-amber-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>3D Engine Debug HUD</span>
            </span>
            <button
              type="button"
              onClick={() => setDebugMode(false)}
              className="text-slate-400 hover:text-white px-1 text-xs"
            >
              ✕
            </button>
          </div>

          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-400">FPS:</span>
              <span className="font-bold text-emerald-400">{fps}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Static Meshes:</span>
              <span className="font-bold text-cyan-300">8 merged layers</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Active Vehicles:</span>
              <span className="font-bold text-white">{currentVehicles.length}</span>
            </div>
            <div className="pl-2 border-l border-white/10 text-[10px] space-y-0.5 text-slate-300">
              <div>Cars: {vehicleCounts.car || 0}</div>
              <div>Buses: {vehicleCounts.bus || 0}</div>
              <div>Trucks: {vehicleCounts.truck || 0}</div>
              <div>Two-Wheelers: {vehicleCounts.two_wheeler || 0}</div>
              <div>Ambulances: {vehicleCounts.ambulance || 0}</div>
            </div>
            <div className="pt-1.5 border-t border-white/10 flex items-center justify-between">
              <span className="text-slate-400">Wireframe (w):</span>
              <button
                type="button"
                onClick={() => setWireframeMode((w) => !w)}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  wireframeMode ? 'bg-amber-500 text-black' : 'bg-white/10 text-slate-300 hover:text-white'
                }`}
              >
                {wireframeMode ? 'ON' : 'OFF'}
              </button>
            </div>
            <div className="text-[10px] text-slate-400 italic pt-1">
              Press 'd' to hide HUD, 'w' to toggle wireframe.
            </div>
          </div>
        </div>
      )}

      {/* Top Floating Control Bar */}
      {showControls && (
        <div className="absolute top-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none z-20">
          {/* Left: Mode Pill & Camera Angle Selectors */}
          <div className="pointer-events-auto flex items-center gap-2 bg-[#0C1316]/90 border border-white/15 rounded-full p-1.5 shadow-xl backdrop-blur-md">
            {/* Mode Indicator */}
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/50 text-xs font-mono font-bold tracking-wide">
              <span
                className={`w-2 h-2 rounded-full ${
                  resolvedLabel.includes('Live')
                    ? 'bg-emerald-400 animate-pulse'
                    : resolvedLabel.includes('Replay')
                    ? 'bg-blue-400'
                    : 'bg-slate-400'
                }`}
              />
              <span
                className={
                  resolvedLabel.includes('Live')
                    ? 'text-emerald-300'
                    : resolvedLabel.includes('Replay')
                    ? 'text-blue-300'
                    : 'text-slate-300'
                }
              >
                {resolvedLabel}
              </span>
            </div>

            <div className="h-4 w-px bg-white/20" />

            {/* Camera Presets */}
            <div className="flex items-center gap-1">
              {Object.entries(CAMERA_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setActivePreset(preset)}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono font-medium transition-all ${
                    activePreset.name === preset.name
                      ? 'bg-[#FFB020] text-black font-bold shadow-md'
                      : 'text-[#AEB8BA] hover:text-white hover:bg-white/10'
                  }`}
                  title={`Switch to ${preset.name} camera perspective`}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Right: Exaggeration & Pillar Audit Badge */}
          <div className="pointer-events-auto flex items-center gap-2">
            {/* Vehicle Exaggeration Scale */}
            <div className="flex items-center gap-1 bg-[#0C1316]/90 border border-white/15 rounded-full p-1 shadow-lg backdrop-blur-md">
              <span className="text-[10px] font-mono text-slate-400 px-2">SCALE:</span>
              {[1.0, 2.0, 3.0].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => onVehicleScaleChange && onVehicleScaleChange(s)}
                  className={`px-2 py-0.5 rounded-full text-[11px] font-mono font-bold transition-colors ${
                    Math.abs(vehicleScale - s) < 0.1
                      ? 'bg-[#FFB020] text-black'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>

            {pillarAudit && (
              <button
                type="button"
                onClick={() => setShowPillarReport((prev) => !prev)}
                className={`px-3 py-1.5 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5 shadow-lg backdrop-blur-md transition-colors ${
                  showPillarReport
                    ? 'bg-amber-500 text-black font-bold'
                    : 'bg-[#0C1316]/90 text-amber-300 border border-amber-500/40 hover:bg-amber-500/20'
                }`}
              >
                <span>Pillars: {pillarAudit.clearPillars.length} Clear</span>
                <span className="text-[10px] text-rose-400 font-bold">
                  ({pillarAudit.intersectingPillars.length} Conflicts)
                </span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Bottom Floating Footer / Tooltip Bar (suppressed when embedded in IsometricIntersection) */}
      {showControls && (
        <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none z-20">
          {/* Left: Elevation & Provenance Tooltip */}
          <div className="pointer-events-auto flex items-center gap-2 bg-[#0C1316]/90 border border-white/15 rounded-lg px-3 py-1.5 shadow-lg backdrop-blur-md text-xs font-mono">
            <span className="text-[#FFB020] font-bold">3D TWIN</span>
            <span className="text-white/20">|</span>
            <span className="text-[#AEB8BA] text-[11px]">
              Synthetic demand, modelled geometry, SUMO simulation.
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
      )}

      {/* Pillar Surface Lane Intersection Modal */}
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
                  <span>
                    Station X = {p.threeX}m (Z = 0m)
                  </span>
                  <span>Deck {p.deckElevation}m</span>
                </div>
                <div className="text-slate-400">Collides with {p.conflicts.length} surface lane(s):</div>
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
