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
import * as BufferGeometryUtils from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { sumoToThree } from './network3dGeometry.js';

// Base physical dimensions in metres [width, height, length]
export const VEHICLE_BASE_DIMENSIONS = {
  car: { width: 1.85, height: 1.45, length: 4.60, wheelRadius: 0.32 },
  bus: { width: 2.55, height: 3.10, length: 11.80, wheelRadius: 0.50 },
  truck: { width: 2.45, height: 2.90, length: 8.50, wheelRadius: 0.48 },
  two_wheeler: { width: 0.85, height: 1.25, length: 2.10, wheelRadius: 0.28 },
  ambulance: { width: 2.10, height: 2.30, length: 5.80, wheelRadius: 0.38 },
};

/** Helper to construct low-poly car geometry */
function buildCarGeometry() {
  const parts = [];

  // 1. Lower Chassis
  const chassis = new THREE.BoxGeometry(1.85, 0.55, 4.40);
  chassis.translate(0, 0.35, 0);
  parts.push(chassis);

  // 2. Cabin / Greenhouse
  const cabin = new THREE.BoxGeometry(1.50, 0.58, 2.10);
  cabin.translate(0, 0.88, -0.20);
  parts.push(cabin);

  // 3. Front Windshield Slope
  const frontWindshield = new THREE.BoxGeometry(1.48, 0.45, 0.65);
  frontWindshield.rotateX(0.42);
  frontWindshield.translate(0, 0.70, 0.95);
  parts.push(frontWindshield);

  // 4. Rear Window Slope
  const rearWindow = new THREE.BoxGeometry(1.48, 0.45, 0.65);
  rearWindow.rotateX(-0.42);
  rearWindow.translate(0, 0.70, -1.35);
  parts.push(rearWindow);

  // 5. 4 Wheels (black side boxes)
  const wheelPositions = [
    [0.92, 0.28, 1.25],
    [-0.92, 0.28, 1.25],
    [0.92, 0.28, -1.25],
    [-0.92, 0.28, -1.25],
  ];
  for (const [wx, wy, wz] of wheelPositions) {
    const wheel = new THREE.BoxGeometry(0.24, 0.56, 0.56);
    wheel.translate(wx, wy, wz);
    parts.push(wheel);
  }

  // 6. Front Headlights & Rear Taillights
  const headlightL = new THREE.BoxGeometry(0.35, 0.16, 0.12);
  headlightL.translate(0.65, 0.45, 2.22);
  const headlightR = new THREE.BoxGeometry(0.35, 0.16, 0.12);
  headlightR.translate(-0.65, 0.45, 2.22);
  const taillightL = new THREE.BoxGeometry(0.35, 0.16, 0.12);
  taillightL.translate(0.65, 0.45, -2.22);
  const taillightR = new THREE.BoxGeometry(0.35, 0.16, 0.12);
  taillightR.translate(-0.65, 0.45, -2.22);
  parts.push(headlightL, headlightR, taillightL, taillightR);

  // 7. Roof Directional Indicator
  const arrow = new THREE.BoxGeometry(0.25, 0.08, 0.65);
  arrow.translate(0, 1.20, 0.10);
  parts.push(arrow);

  return BufferGeometryUtils.mergeGeometries(parts, false);
}

/** Helper to construct low-poly truck geometry */
function buildTruckGeometry() {
  const parts = [];

  // 1. Front Cab
  const cab = new THREE.BoxGeometry(2.40, 1.75, 2.20);
  cab.translate(0, 1.15, 2.30);
  parts.push(cab);

  // 2. Cab Windshield
  const windshield = new THREE.BoxGeometry(2.20, 0.70, 0.25);
  windshield.translate(0, 1.55, 3.35);
  parts.push(windshield);

  // 3. Rear Cargo Container
  const container = new THREE.BoxGeometry(2.45, 2.45, 5.60);
  container.translate(0, 1.55, -1.30);
  parts.push(container);

  // 4. Lower Steel Rail
  const rail = new THREE.BoxGeometry(1.70, 0.35, 7.80);
  rail.translate(0, 0.35, 0);
  parts.push(rail);

  // 5. 6 Wheels
  const wheelPositions = [
    [1.22, 0.36, 2.40],
    [-1.22, 0.36, 2.40],
    [1.22, 0.36, -1.40],
    [-1.22, 0.36, -1.40],
    [1.22, 0.36, -2.90],
    [-1.22, 0.36, -2.90],
  ];
  for (const [wx, wy, wz] of wheelPositions) {
    const wheel = new THREE.BoxGeometry(0.28, 0.70, 0.70);
    wheel.translate(wx, wy, wz);
    parts.push(wheel);
  }

  // 6. Lights
  const headlightL = new THREE.BoxGeometry(0.40, 0.20, 0.12);
  headlightL.translate(0.85, 0.50, 3.42);
  const headlightR = new THREE.BoxGeometry(0.40, 0.20, 0.12);
  headlightR.translate(-0.85, 0.50, 3.42);
  const taillightL = new THREE.BoxGeometry(0.40, 0.20, 0.12);
  taillightL.translate(0.85, 0.50, -4.12);
  const taillightR = new THREE.BoxGeometry(0.40, 0.20, 0.12);
  taillightR.translate(-0.85, 0.50, -4.12);
  parts.push(headlightL, headlightR, taillightL, taillightR);

  return BufferGeometryUtils.mergeGeometries(parts, false);
}

/** Helper to construct low-poly transit bus geometry */
function buildBusGeometry() {
  const parts = [];

  // 1. Long Coach Body
  const body = new THREE.BoxGeometry(2.55, 2.65, 11.40);
  body.translate(0, 1.50, 0);
  parts.push(body);

  // 2. Panoramic Front Windshield
  const windshield = new THREE.BoxGeometry(2.40, 1.10, 0.25);
  windshield.translate(0, 1.80, 5.65);
  parts.push(windshield);

  // 3. Side Window Strips (recessed black ribbons)
  const windowStrip = new THREE.BoxGeometry(2.58, 0.75, 9.40);
  windowStrip.translate(0, 1.95, -0.40);
  parts.push(windowStrip);

  // 4. Roof AC Pod
  const acPod = new THREE.BoxGeometry(1.60, 0.32, 2.80);
  acPod.translate(0, 2.95, -1.50);
  parts.push(acPod);

  // 5. 6 Wheels
  const wheelPositions = [
    [1.28, 0.40, 4.00],
    [-1.28, 0.40, 4.00],
    [1.28, 0.40, -3.20],
    [-1.28, 0.40, -3.20],
    [1.28, 0.40, -4.80],
    [-1.28, 0.40, -4.80],
  ];
  for (const [wx, wy, wz] of wheelPositions) {
    const wheel = new THREE.BoxGeometry(0.28, 0.78, 0.78);
    wheel.translate(wx, wy, wz);
    parts.push(wheel);
  }

  // 6. Lights
  const headlightL = new THREE.BoxGeometry(0.42, 0.22, 0.12);
  headlightL.translate(0.90, 0.55, 5.72);
  const headlightR = new THREE.BoxGeometry(0.42, 0.22, 0.12);
  headlightR.translate(-0.90, 0.55, 5.72);
  const taillightL = new THREE.BoxGeometry(0.42, 0.22, 0.12);
  taillightL.translate(0.90, 0.55, -5.72);
  const taillightR = new THREE.BoxGeometry(0.42, 0.22, 0.12);
  taillightR.translate(-0.90, 0.55, -5.72);
  parts.push(headlightL, headlightR, taillightL, taillightR);

  return BufferGeometryUtils.mergeGeometries(parts, false);
}

/** Helper to construct low-poly ambulance geometry */
function buildAmbulanceGeometry() {
  const parts = [];

  // 1. Box Body
  const body = new THREE.BoxGeometry(2.15, 2.15, 5.60);
  body.translate(0, 1.30, 0);
  parts.push(body);

  // 2. Windshield
  const windshield = new THREE.BoxGeometry(1.95, 0.65, 0.25);
  windshield.translate(0, 1.60, 2.75);
  parts.push(windshield);

  // 3. Roof Siren Lightbar
  const sirenBar = new THREE.BoxGeometry(1.60, 0.20, 0.35);
  sirenBar.translate(0, 2.45, 1.20);
  const strobeL = new THREE.BoxGeometry(0.35, 0.26, 0.32);
  strobeL.translate(0.60, 2.58, 1.20);
  const strobeR = new THREE.BoxGeometry(0.35, 0.26, 0.32);
  strobeR.translate(-0.60, 2.58, 1.20);
  parts.push(sirenBar, strobeL, strobeR);

  // 4. Roof Medical Cross
  const crossH = new THREE.BoxGeometry(0.90, 0.08, 0.28);
  crossH.translate(0, 2.42, -0.60);
  const crossV = new THREE.BoxGeometry(0.28, 0.08, 0.90);
  crossV.translate(0, 2.42, -0.60);
  parts.push(crossH, crossV);

  // 5. 4 Wheels
  const wheelPositions = [
    [1.08, 0.32, 1.60],
    [-1.08, 0.32, 1.60],
    [1.08, 0.32, -1.60],
    [-1.08, 0.32, -1.60],
  ];
  for (const [wx, wy, wz] of wheelPositions) {
    const wheel = new THREE.BoxGeometry(0.26, 0.62, 0.62);
    wheel.translate(wx, wy, wz);
    parts.push(wheel);
  }

  // 6. Lights
  const headlightL = new THREE.BoxGeometry(0.35, 0.18, 0.12);
  headlightL.translate(0.75, 0.50, 2.82);
  const headlightR = new THREE.BoxGeometry(0.35, 0.18, 0.12);
  headlightR.translate(-0.75, 0.50, 2.82);
  const taillightL = new THREE.BoxGeometry(0.35, 0.18, 0.12);
  taillightL.translate(0.75, 0.50, -2.82);
  const taillightR = new THREE.BoxGeometry(0.35, 0.18, 0.12);
  taillightR.translate(-0.75, 0.50, -2.82);
  parts.push(headlightL, headlightR, taillightL, taillightR);

  return BufferGeometryUtils.mergeGeometries(parts, false);
}

/** Helper to construct low-poly motorcycle / two-wheeler geometry */
function buildTwoWheelerGeometry() {
  const parts = [];

  // 1. Chassis Frame
  const frame = new THREE.BoxGeometry(0.45, 0.55, 1.80);
  frame.translate(0, 0.48, 0);
  parts.push(frame);

  // 2. Handlebar & Fork
  const handlebar = new THREE.BoxGeometry(0.85, 0.10, 0.10);
  handlebar.translate(0, 0.95, 0.55);
  const fork = new THREE.BoxGeometry(0.20, 0.60, 0.20);
  fork.translate(0, 0.65, 0.65);
  parts.push(handlebar, fork);

  // 3. Stylized Rider (torso and helmet)
  const torso = new THREE.BoxGeometry(0.45, 0.55, 0.35);
  torso.translate(0, 1.05, -0.15);
  const helmet = new THREE.BoxGeometry(0.32, 0.32, 0.32);
  helmet.translate(0, 1.45, -0.15);
  parts.push(torso, helmet);

  // 4. Wheels
  const frontWheel = new THREE.BoxGeometry(0.16, 0.54, 0.54);
  frontWheel.translate(0, 0.28, 0.75);
  const rearWheel = new THREE.BoxGeometry(0.16, 0.54, 0.54);
  rearWheel.translate(0, 0.28, -0.75);
  parts.push(frontWheel, rearWheel);

  // 5. Headlight & Taillight
  const headlight = new THREE.BoxGeometry(0.20, 0.14, 0.10);
  headlight.translate(0, 0.75, 0.82);
  const taillight = new THREE.BoxGeometry(0.20, 0.14, 0.10);
  taillight.translate(0, 0.70, -0.85);
  parts.push(headlight, taillight);

  return BufferGeometryUtils.mergeGeometries(parts, false);
}

/** Create optimized low-poly vehicle compound geometry with chassis, cabin, wheels, and lights */
export function createLowPolyVehicleGeometry(type) {
  try {
    switch (type) {
      case 'bus':
        return buildBusGeometry();
      case 'truck':
        return buildTruckGeometry();
      case 'ambulance':
        return buildAmbulanceGeometry();
      case 'two_wheeler':
        return buildTwoWheelerGeometry();
      case 'car':
      default:
        return buildCarGeometry();
    }
  } catch (err) {
    // Graceful fallback to basic box if merge fails
    const dims = VEHICLE_BASE_DIMENSIONS[type] || VEHICLE_BASE_DIMENSIONS.car;
    const geom = new THREE.BoxGeometry(dims.width, dims.height, dims.length);
    geom.translate(0, dims.height / 2, 0);
    return geom;
  }
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

/** High-contrast vehicle color lookup matching 2.5D palette */
export function getVehicleColor(v, isDark = true, colorblindSafe = false) {
  const type = classifyVehicleType(v);
  if (type === 'ambulance') {
    return {
      body: new THREE.Color('#FFFFFF'), // Pure white ambulance
      glow: '#EF4444',
      beacon: '#EF4444',
    };
  }

  const isQueued = (v.s !== undefined && v.s < 0.2) || (v.w !== undefined && v.w > 1.0) || v.is_queued;
  if (isQueued) {
    // Queued / stopped vehicle: distinct warm amber matching 2.5D #F59E0B
    return {
      body: new THREE.Color('#F59E0B'),
      glow: '#F59E0B',
      beacon: null,
    };
  }

  // Moving vehicles: exact color hierarchy matching 2.5D view
  let hex = '#38BDF8'; // Car = Sky Blue
  if (type === 'bus') hex = '#00E5FF'; // Bus = Cyan
  else if (type === 'truck') hex = '#7DD3FC'; // Truck = Light Steel Blue
  else if (type === 'two_wheeler') hex = '#2DD4BF'; // Two-wheeler = Teal

  return {
    body: new THREE.Color(hex),
    glow: hex,
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
    const isFlyover = (v.z || 0.0) >= 5.0 || (v.lane && v.lane.includes('flyover'));
    const isUnderpass = (v.z || 0.0) < -1.0 || (v.lane && v.lane.includes('orr_mainline'));
    let baseZ = v.z || 0.0;
    if (isUnderpass && (!v.z || v.z >= 0.0)) {
      baseZ = -3.8;
    }
    const [tx, rawTy, tz] = sumoToThree(v.x, v.y, baseZ);
    let effectiveYOffset = 0.0;
    if (isFlyover) effectiveYOffset = tierYOffset;
    if (isUnderpass) effectiveYOffset = -tierYOffset;

    dummyPosition.set(tx, rawTy + effectiveYOffset, tz);

    // Convert SUMO angle (0 deg = North/-Z, 90 deg = East/+X) to Three.js Euler
    // Vehicle model length is along Z, so heading angle rotY = -deg2rad(a) + PI
    const rotY = (-((v.a || 0.0) * Math.PI)) / 180.0 + Math.PI;
    dummyQuaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rotY);

    // Scaling: clamp scale so vehicles don't overlap neighboring lanes (default ~1.35x when 2x passed)
    const effectiveScale = vehicleScale <= 1.05 ? 1.0 : (vehicleScale >= 2.8 ? 1.75 : 1.35);
    dummyScale.set(effectiveScale, effectiveScale, effectiveScale);

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
