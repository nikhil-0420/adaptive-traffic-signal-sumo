/**
 * vehicle3dMesh.js - Low-Poly 3D Vehicle Geometries & InstancedMesh Management
 *
 * Implements Phase 5:
 * - 5 low-poly vehicle models: car, bus, truck, two-wheeler (motorcycle/auto), ambulance
 * - High-contrast color mapping (moving = cool blue, queued/stopped = warm orange/amber, ambulance = white/red)
 * - One-tick buffer interpolation (no extrapolation, clamped at alpha = 1.0)
 * - Exaggeration control (1x, 2x default, 3x)
 * - Physical elevation: sitting on road surface (0m) or flyover deck (+6.8m)
 */

import * as THREE from 'three';
import { sumoToThree } from './network3dGeometry.js';

// Base physical dimensions in metres [width, height, length]
export const VEHICLE_BASE_DIMENSIONS = {
  car: { width: 1.85, height: 1.45, length: 4.60, wheelRadius: 0.32 },
  bus: { width: 2.55, height: 3.10, length: 11.80, wheelRadius: 0.50 },
  truck: { width: 2.45, height: 2.90, length: 8.50, wheelRadius: 0.48 },
  two_wheeler: { width: 0.85, height: 1.25, length: 2.10, wheelRadius: 0.28 },
  ambulance: { width: 2.10, height: 2.30, length: 5.80, wheelRadius: 0.38 },
};

/** Create optimized low-poly BoxGeometry with chassis and cabin */
export function createLowPolyVehicleGeometry(type) {
  const dims = VEHICLE_BASE_DIMENSIONS[type] || VEHICLE_BASE_DIMENSIONS.car;
  const geom = new THREE.BoxGeometry(dims.width, dims.height, dims.length);
  // Shift pivot so bottom sits at Y = 0
  geom.translate(0, dims.height / 2, 0);
  return geom;
}

/** Determine vehicle category from telemetry object */
export function classifyVehicleType(v) {
  if (v.em || v.is_emergency || v.type === 'emergency' || v.type === 'ambulance' || (v.id && v.id.includes('ambulance'))) {
    return 'ambulance';
  }
  const rawType = (v.type || '').toLowerCase();
  if (rawType.includes('bus')) return 'bus';
  if (rawType.includes('truck')) return 'truck';
  if (rawType.includes('motorcycle') || rawType.includes('bike') || rawType.includes('auto') || rawType.includes('two_wheeler')) {
    return 'two_wheeler';
  }
  if (rawType.includes('car')) return 'car';

  // Deterministic fallback from vehicle id hash
  let hash = 0;
  const idStr = String(v.id || '');
  for (let i = 0; i < idStr.length; i++) {
    hash = (hash * 31 + idStr.charCodeAt(i)) | 0;
  }
  const mod = Math.abs(hash) % 100;
  if (mod < 60) return 'car';
  if (mod < 78) return 'two_wheeler';
  if (mod < 90) return 'bus';
  return 'truck';
}

/** High-contrast vehicle color lookup (with optional colorblind-safe palette) */
export function getVehicleColor(v, isDark = true, colorblindSafe = false) {
  const isAmbulance = classifyVehicleType(v) === 'ambulance';
  if (isAmbulance) {
    return {
      body: new THREE.Color(colorblindSafe ? '#dc2626' : '#f43f5e'), // Bright emergency red/rose
      glow: colorblindSafe ? '#b91c1c' : '#ef4444',
      beacon: '#ffffff',
    };
  }

  const isQueued = (v.s !== undefined && v.s < 0.2) || (v.w !== undefined && v.w > 1.0) || v.is_queued;
  if (isQueued) {
    // Queued / stopped vehicle: distinct warm orange/amber
    return {
      body: new THREE.Color(colorblindSafe ? '#f59e0b' : (isDark ? '#f97316' : '#ea580c')),
      glow: '#f59e0b',
      beacon: null,
    };
  }

  // Moving vehicle: high-contrast cool cyan / sky blue
  return {
    body: new THREE.Color(colorblindSafe ? '#0284c7' : (isDark ? '#38bdf8' : '#0284c7')),
    glow: colorblindSafe ? '#0284c7' : '#38bdf8',
    beacon: null,
  };
}

/** Interpolate angle along shortest circular arc */
export function interpolateAngleDegrees(a1, a2, alpha) {
  let diff = (a2 - a1) % 360;
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;
  return a1 + diff * alpha;
}

/**
 * Interpolate a vehicle state between two frames.
 * Clamps alpha to [0, 1] to strictly enforce NO extrapolation.
 */
export function interpolateVehicle(vPrev, vCurr, alpha = 1.0) {
  const t = Math.max(0.0, Math.min(1.0, alpha));
  if (!vPrev) return vCurr;
  if (!vCurr) return vPrev;

  const x = vPrev.x + (vCurr.x - vPrev.x) * t;
  const y = vPrev.y + (vCurr.y - vPrev.y) * t;
  const z = (vPrev.z || 0.0) + ((vCurr.z || 0.0) - (vPrev.z || 0.0)) * t;
  const a = interpolateAngleDegrees(vPrev.a || 0, vCurr.a || 0, t);
  const s = (vPrev.s || 0.0) + ((vCurr.s || 0.0) - (vPrev.s || 0.0)) * t;

  return {
    ...vCurr,
    x,
    y,
    z,
    a,
    s,
  };
}

const dummyMatrix = new THREE.Matrix4();
const dummyPosition = new THREE.Vector3();
const dummyQuaternion = new THREE.Quaternion();
const dummyScale = new THREE.Vector3();
const dummyColor = new THREE.Color();

/**
 * Update an InstancedMesh with current interpolated vehicle instances.
 * Sets position, heading rotation, elevation (z), exaggeration scale, and colors.
 */
export function updateVehicleInstancedMesh(
  instancedMesh,
  vehicles,
  vehicleScale = 2.0,
  isDark = true,
  tierYOffset = 0.0,
  colorblindSafe = false
) {
  if (!instancedMesh) return;

  const count = vehicles.length;
  instancedMesh.count = count;

  for (let i = 0; i < count; i++) {
    const v = vehicles[i];
    const [tx, ty, tz] = sumoToThree(v.x, v.y, v.z || 0.0);

    // Apply tier vertical explode offset if applicable
    const isFlyover = (v.z || 0.0) >= 5.0;
    const isUnderpass = (v.z || 0.0) < -1.0;
    let effectiveYOffset = 0.0;
    if (isFlyover) effectiveYOffset = tierYOffset;
    if (isUnderpass) effectiveYOffset = -tierYOffset;

    dummyPosition.set(tx, ty + effectiveYOffset, tz);

    // Convert SUMO angle (0 deg = North/-Z, 90 deg = East/+X) to Three.js Euler
    // Vehicle model length is along Z, so heading angle rotY = -deg2rad(a) + PI
    const rotY = (-((v.a || 0.0) * Math.PI)) / 180.0 + Math.PI;
    dummyQuaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rotY);

    // Scaling: multiply base dimensions by exaggeration factor (default 2x)
    dummyScale.set(vehicleScale, vehicleScale, vehicleScale);

    dummyMatrix.compose(dummyPosition, dummyQuaternion, dummyScale);
    instancedMesh.setMatrixAt(i, dummyMatrix);

    // Set instance color
    const c = getVehicleColor(v, isDark, colorblindSafe);
    instancedMesh.setColorAt(i, c.body);
  }

  instancedMesh.instanceMatrix.needsUpdate = true;
  if (instancedMesh.instanceColor) {
    instancedMesh.instanceColor.needsUpdate = true;
  }
}
