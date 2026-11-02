/**
 * Network3D Geometry Builder for Three.js / @react-three/fiber
 *
 * Converts SUMO network3d.json payload into optimized, merged Three.js geometries:
 * - Road ribbons (surface, flyover deck, underpass mainline)
 * - Lane markings (solid edge lines, dashed lane dividers, stop lines)
 * - Junction surface polygons
 * - Flyover deck thickness, fascia, and concrete crash barriers
 * - Bridge support pillars with geometric surface-lane clearance auditing
 *
 * Coordinate Convention (1 unit = 1 metre):
 * - Three.js X = sumo_x - 350.0  (East is +X, West is -X)
 * - Three.js Y = sumo_z          (Up is +Y)
 * - Three.js Z = 350.0 - sumo_y  (North is -Z, South is +Z)
 */

import * as THREE from 'three';
import * as BufferGeometryUtils from 'three/examples/jsm/utils/BufferGeometryUtils.js';

export const SUMO_OFFSET_X = 350.0;
export const SUMO_OFFSET_Y = 350.0;

// Camera Presets for Quick Navigation (Phase 6 presets + backward-compatible keys)
export const CAMERA_PRESETS = {
  topDown: { position: [0, 160, 0.01], target: [0, 0, 0], name: 'Top-Down' },
  iso: { position: [75, 65, 85], target: [0, 2, 0], name: 'Iso' },
  junctionCloseUp: { position: [25, 18, 25], target: [0, 1.5, 0], name: 'Junction close-up' },
  flyoverSide: { position: [-70, 15, 0], target: [0, 6.8, 0], name: 'Flyover side view' },
  approachN: { position: [0, 15, -45], target: [0, 2, -18], name: 'Approach N' },
  approachS: { position: [0, 15, 45], target: [0, 2, 18], name: 'Approach S' },
  approachE: { position: [45, 15, 0], target: [22, 2, 0], name: 'Approach E' },
  approachW: { position: [-45, 15, 0], target: [-22, 2, 0], name: 'Approach W' },
  fitJunction: { position: [50, 45, 60], target: [0, 2, 0], name: 'Fit to junction' },
  // Backwards-compatible aliases
  isoSW: { position: [75, 65, 85], target: [0, 2, 0], name: 'Iso SW' },
  isoNE: { position: [-75, 65, -85], target: [0, 2, 0], name: 'Iso NE' },
  flyoverEye: { position: [-60, 12, 10], target: [0, 7, 0], name: 'Flyover Eye-Level' },
};

/** Check whether WebGL is supported in the browser / client environment */
export function isWebGLAvailable() {
  if (typeof window === 'undefined') return true;
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
}

/** Convert SUMO (x, y, z) to Three.js (X, Y, Z) */
export function sumoToThree(x, y, z) {
  return [x - SUMO_OFFSET_X, z || 0.0, SUMO_OFFSET_Y - y];
}

/** Convert Three.js (X, Y, Z) to SUMO (x, y, z) */
export function threeToSumo(X, Y, Z) {
  return [X + SUMO_OFFSET_X, SUMO_OFFSET_Y - Z, Y];
}

/**
 * 2D distance from point (px, py) to line segment (x1, y1) -> (x2, y2).
 */
export function pointToSegmentDist2D(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
  t = Math.max(0.0, Math.min(1.0, t));
  const cx = x1 + t * dx;
  const cy = y1 + t * dy;
  return Math.hypot(px - cx, py - cy);
}

/**
 * Generate a 3D road ribbon BufferGeometry from a 3D polyline and width.
 */
export function buildRibbonGeometry(polyline3d, width = 3.2, yOffset = 0.0) {
  if (!polyline3d || polyline3d.length < 2) return null;

  // Convert polyline to Three.js coordinates
  const pts = polyline3d.map((p) => {
    const t = sumoToThree(p[0], p[1], p[2]);
    return [t[0], t[1] + yOffset, t[2]];
  });

  const numPts = pts.length;
  const positions = [];
  const normals = [];
  const uvs = [];
  const indices = [];

  let cumDist = 0.0;
  const halfW = width / 2.0;

  for (let i = 0; i < numPts; i++) {
    const curr = pts[i];
    let tx, tz;

    if (i === 0) {
      tx = pts[1][0] - curr[0];
      tz = pts[1][2] - curr[2];
    } else if (i === numPts - 1) {
      tx = curr[0] - pts[i - 1][0];
      tz = curr[2] - pts[i - 1][2];
    } else {
      tx = pts[i + 1][0] - pts[i - 1][0];
      tz = pts[i + 1][2] - pts[i - 1][2];
    }

    const len = Math.hypot(tx, tz) || 1.0;
    const nx = -tz / len;
    const nz = tx / len;

    if (i > 0) {
      cumDist += Math.hypot(curr[0] - pts[i - 1][0], curr[2] - pts[i - 1][2]);
    }

    // Left vertex
    positions.push(curr[0] + nx * halfW, curr[1], curr[2] + nz * halfW);
    normals.push(0, 1, 0);
    uvs.push(0, cumDist);

    // Right vertex
    positions.push(curr[0] - nx * halfW, curr[1], curr[2] - nz * halfW);
    normals.push(0, 1, 0);
    uvs.push(1, cumDist);

    if (i < numPts - 1) {
      const v0 = i * 2;
      const v1 = i * 2 + 1;
      const v2 = (i + 1) * 2;
      const v3 = (i + 1) * 2 + 1;
      indices.push(v0, v1, v2);
      indices.push(v1, v3, v2);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geom.setIndex(indices);
  return geom;
}

/**
 * Generate dashed line segments along a lane polyline.
 */
export function buildDashedLineGeometry(polyline3d, dashLength = 3.0, gapLength = 3.0, lineWidth = 0.14, yOffset = 0.015) {
  if (!polyline3d || polyline3d.length < 2) return null;

  const pts = polyline3d.map((p) => {
    const t = sumoToThree(p[0], p[1], p[2]);
    return [t[0], t[1] + yOffset, t[2]];
  });

  const segmentGeoms = [];
  const halfW = lineWidth / 2.0;

  let totalDist = 0.0;
  for (let i = 0; i < pts.length - 1; i++) {
    totalDist += Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][2] - pts[i][2]);
  }

  if (totalDist < 1.0) return null;

  // Walk in dash + gap steps
  let d = 0.0;
  let isDash = true;

  function samplePoint(targetD) {
    let acc = 0.0;
    for (let i = 0; i < pts.length - 1; i++) {
      const segLen = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][2] - pts[i][2]);
      if (acc + segLen >= targetD) {
        const frac = segLen > 0 ? (targetD - acc) / segLen : 0;
        return [
          pts[i][0] + frac * (pts[i + 1][0] - pts[i][0]),
          pts[i][1] + frac * (pts[i + 1][1] - pts[i][1]),
          pts[i][2] + frac * (pts[i + 1][2] - pts[i][2]),
        ];
      }
      acc += segLen;
    }
    return pts[pts.length - 1];
  }

  while (d < totalDist) {
    const step = isDash ? dashLength : gapLength;
    const nextD = Math.min(totalDist, d + step);

    if (isDash && nextD > d + 0.3) {
      const p1 = samplePoint(d);
      const p2 = samplePoint(nextD);
      const tx = p2[0] - p1[0];
      const tz = p2[2] - p1[2];
      const len = Math.hypot(tx, tz) || 1.0;
      const nx = -tz / len;
      const nz = tx / len;

      const pos = [
        p1[0] + nx * halfW, p1[1], p1[2] + nz * halfW,
        p1[0] - nx * halfW, p1[1], p1[2] - nz * halfW,
        p2[0] + nx * halfW, p2[1], p2[2] + nz * halfW,
        p2[0] - nx * halfW, p2[1], p2[2] - nz * halfW,
      ];
      const norm = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0];
      const uvs = [0, 0, 1, 0, 0, 1, 1, 1];
      const idx = [0, 1, 2, 1, 3, 2];

      const dashGeom = new THREE.BufferGeometry();
      dashGeom.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      dashGeom.setAttribute('normal', new THREE.Float32BufferAttribute(norm, 3));
      dashGeom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
      dashGeom.setIndex(idx);
      segmentGeoms.push(dashGeom);
    }

    d = nextD;
    isDash = !isDash;
  }

  if (segmentGeoms.length === 0) return null;
  return BufferGeometryUtils.mergeGeometries(segmentGeoms, false);
}

/**
 * Generate solid outer edge line ribbon.
 */
export function buildEdgeLineGeometry(polyline3d, laneWidth = 3.2, side = 'both', lineWidth = 0.15, yOffset = 0.015) {
  if (!polyline3d || polyline3d.length < 2) return null;

  const pts = polyline3d.map((p) => {
    const t = sumoToThree(p[0], p[1], p[2]);
    return [t[0], t[1] + yOffset, t[2]];
  });

  const geoms = [];
  const sidesToBuild = side === 'both' ? ['left', 'right'] : [side];

  for (const s of sidesToBuild) {
    const sign = s === 'left' ? 1.0 : -1.0;
    const offsetDist = (laneWidth / 2.0 - lineWidth / 2.0) * sign;
    const halfW = lineWidth / 2.0;

    const positions = [];
    const normals = [];
    const uvs = [];
    const indices = [];

    for (let i = 0; i < pts.length; i++) {
      const curr = pts[i];
      let tx, tz;
      if (i === 0) {
        tx = pts[1][0] - curr[0];
        tz = pts[1][2] - curr[2];
      } else if (i === pts.length - 1) {
        tx = curr[0] - pts[i - 1][0];
        tz = curr[2] - pts[i - 1][2];
      } else {
        tx = pts[i + 1][0] - pts[i - 1][0];
        tz = pts[i + 1][2] - pts[i - 1][2];
      }
      const len = Math.hypot(tx, tz) || 1.0;
      const nx = -tz / len;
      const nz = tx / len;

      const cx = curr[0] + nx * offsetDist;
      const cz = curr[2] + nz * offsetDist;

      positions.push(cx + nx * halfW, curr[1], cz + nz * halfW);
      positions.push(cx - nx * halfW, curr[1], cz - nz * halfW);
      normals.push(0, 1, 0, 0, 1, 0);
      uvs.push(0, i, 1, i);

      if (i < pts.length - 1) {
        const v0 = i * 2;
        const v1 = i * 2 + 1;
        const v2 = (i + 1) * 2;
        const v3 = (i + 1) * 2 + 1;
        indices.push(v0, v1, v2);
        indices.push(v1, v3, v2);
      }
    }

    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    g.setIndex(indices);
    geoms.push(g);
  }

  return geoms.length > 0 ? BufferGeometryUtils.mergeGeometries(geoms, false) : null;
}

/**
 * Generate a stop line bar perpendicular to lane direction at the stop line position.
 */
export function buildStopLineGeometry(lanePolyline3d, width = 3.2, barThickness = 0.4, yOffset = 0.02) {
  if (!lanePolyline3d || lanePolyline3d.length < 2) return null;
  const pLast = lanePolyline3d[lanePolyline3d.length - 1];
  const pPrev = lanePolyline3d[lanePolyline3d.length - 2];

  const tLast = sumoToThree(pLast[0], pLast[1], pLast[2]);
  const tPrev = sumoToThree(pPrev[0], pPrev[1], pPrev[2]);

  const tx = tLast[0] - tPrev[0];
  const tz = tLast[2] - tPrev[2];
  const len = Math.hypot(tx, tz) || 1.0;
  const nx = -tz / len;
  const nz = tx / len;
  const fx = tx / len;
  const fz = tz / len;

  const halfW = width / 2.0;
  const y = tLast[1] + yOffset;

  // 4 corners of stop rectangle
  const cx = tLast[0];
  const cz = tLast[2];

  const p1 = [cx - fx * barThickness + nx * halfW, y, cz - fz * barThickness + nz * halfW];
  const p2 = [cx - fx * barThickness - nx * halfW, y, cz - fz * barThickness - nz * halfW];
  const p3 = [cx + nx * halfW, y, cz + nz * halfW];
  const p4 = [cx - nx * halfW, y, cz - nz * halfW];

  const positions = [
    p1[0], p1[1], p1[2],
    p2[0], p2[1], p2[2],
    p3[0], p3[1], p3[2],
    p4[0], p4[1], p4[2],
  ];
  const normals = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0];
  const uvs = [0, 0, 1, 0, 0, 1, 1, 1];
  const indices = [0, 1, 2, 1, 3, 2];

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geom.setIndex(indices);
  return geom;
}

/**
 * Generate extruded junction surface geometry from a 2D/3D polygon.
 */
export function buildJunctionGeometry(shapePolygon, junctionZ = 0.0, yOffset = 0.0) {
  if (!shapePolygon || shapePolygon.length < 3) return null;

  // Convert to Three.js coordinates
  const threePts = shapePolygon.map((p) => {
    const t = sumoToThree(p[0], p[1], p[2] !== undefined ? p[2] : junctionZ);
    return [t[0], t[1] + yOffset, t[2]];
  });

  // Triangulate 2D footprint (X, Z)
  const flat2D = [];
  const coords2D = [];
  for (const pt of threePts) {
    coords2D.push(new THREE.Vector2(pt[0], pt[2]));
    flat2D.push(pt[0], pt[2]);
  }

  const triangles = THREE.ShapeUtils.triangulateShape(coords2D, []);
  if (!triangles || triangles.length === 0) return null;

  const positions = [];
  const normals = [];
  const uvs = [];
  const indices = [];

  for (let i = 0; i < threePts.length; i++) {
    positions.push(threePts[i][0], threePts[i][1], threePts[i][2]);
    normals.push(0, 1, 0);
    uvs.push(threePts[i][0] / 100.0, threePts[i][2] / 100.0);
  }

  for (const tri of triangles) {
    indices.push(tri[0], tri[1], tri[2]);
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geom.setIndex(indices);
  return geom;
}

/**
 * Generate concrete parapet barrier geometry along the outer edge of an elevated corridor.
 */
export function buildParapetBarrierGeometry(polyline3d, outerOffset = 3.2, barrierHeight = 0.8, barrierThick = 0.3) {
  if (!polyline3d || polyline3d.length < 2) return null;

  const pts = polyline3d.map((p) => sumoToThree(p[0], p[1], p[2]));
  const positions = [];
  const normals = [];
  const indices = [];

  const halfT = barrierThick / 2.0;

  for (let i = 0; i < pts.length; i++) {
    const curr = pts[i];
    let tx, tz;
    if (i === 0) {
      tx = pts[1][0] - curr[0];
      tz = pts[1][2] - curr[2];
    } else if (i === pts.length - 1) {
      tx = curr[0] - pts[i - 1][0];
      tz = curr[2] - pts[i - 1][2];
    } else {
      tx = pts[i + 1][0] - pts[i - 1][0];
      tz = pts[i + 1][2] - pts[i - 1][2];
    }
    const len = Math.hypot(tx, tz) || 1.0;
    const nx = -tz / len;
    const nz = tx / len;

    const cx = curr[0] + nx * outerOffset;
    const cz = curr[2] + nz * outerOffset;
    const baseY = curr[1];
    const topY = curr[1] + barrierHeight;

    // 4 profile vertices at this station: inner-bottom, inner-top, outer-top, outer-bottom
    const ib = [cx - nx * halfT, baseY, cz - nz * halfT];
    const it = [cx - nx * halfT, topY, cz - nz * halfT];
    const ot = [cx + nx * halfT, topY, cz + nz * halfT];
    const ob = [cx + nx * halfT, baseY, cz + nz * halfT];

    positions.push(...ib, ...it, ...ot, ...ob);
    normals.push(0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0);

    if (i < pts.length - 1) {
      const b0 = i * 4;
      const b1 = (i + 1) * 4;
      // Top face
      indices.push(b0 + 1, b1 + 1, b0 + 2);
      indices.push(b1 + 1, b1 + 2, b0 + 2);
      // Outer face
      indices.push(b0 + 2, b1 + 2, b0 + 3);
      indices.push(b1 + 2, b1 + 3, b0 + 3);
      // Inner face
      indices.push(b0 + 0, b1 + 0, b0 + 1);
      indices.push(b1 + 0, b1 + 1, b0 + 1);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geom.setIndex(indices);
  return geom;
}

/**
 * Generate 3D flyover deck thickness (underside slab and side fascia).
 */
export function buildDeckThicknessGeometry(polyline3d, deckWidth = 6.8, slabThickness = 0.6) {
  if (!polyline3d || polyline3d.length < 2) return null;

  const pts = polyline3d.map((p) => sumoToThree(p[0], p[1], p[2]));
  const positions = [];
  const normals = [];
  const indices = [];

  const halfW = deckWidth / 2.0;

  for (let i = 0; i < pts.length; i++) {
    const curr = pts[i];
    let tx, tz;
    if (i === 0) {
      tx = pts[1][0] - curr[0];
      tz = pts[1][2] - curr[2];
    } else if (i === pts.length - 1) {
      tx = curr[0] - pts[i - 1][0];
      tz = curr[2] - pts[i - 1][2];
    } else {
      tx = pts[i + 1][0] - pts[i - 1][0];
      tz = pts[i + 1][2] - pts[i - 1][2];
    }
    const len = Math.hypot(tx, tz) || 1.0;
    const nx = -tz / len;
    const nz = tx / len;

    const topY = curr[1];
    const btmY = curr[1] - slabThickness;

    // Left-top, left-bottom, right-top, right-bottom
    const lt = [curr[0] + nx * halfW, topY, curr[2] + nz * halfW];
    const lb = [curr[0] + nx * halfW, btmY, curr[2] + nz * halfW];
    const rt = [curr[0] - nx * halfW, topY, curr[2] - nz * halfW];
    const rb = [curr[0] - nx * halfW, btmY, curr[2] - nz * halfW];

    positions.push(...lt, ...lb, ...rt, ...rb);
    normals.push(0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0);

    if (i < pts.length - 1) {
      const b0 = i * 4;
      const b1 = (i + 1) * 4;
      // Underside face (lb -> rb)
      indices.push(b0 + 1, b0 + 3, b1 + 1);
      indices.push(b1 + 1, b0 + 3, b1 + 3);
      // Left fascia (lt -> lb)
      indices.push(b0 + 0, b1 + 0, b0 + 1);
      indices.push(b1 + 0, b1 + 1, b0 + 1);
      // Right fascia (rt -> rb)
      indices.push(b0 + 2, b0 + 3, b1 + 2);
      indices.push(b1 + 2, b0 + 3, b1 + 3);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geom.setIndex(indices);
  return geom;
}

/**
 * Geometric audit of candidate bridge piers against surface road lanes.
 *
 * Checks regular candidate pillar positions along the flyover corridor against
 * all surface lanes in network3d.json and reports any intersecting pillars.
 */
export function auditBridgePillars(networkData, candidatePillarSpacing = 25.0) {
  if (!networkData || !networkData.lanes) {
    return { pillars: [], intersectingPillars: [], clearPillars: [], totalChecked: 0 };
  }

  // Find surface lanes (z < 1.0)
  const surfaceLanes = networkData.lanes.filter((l) => {
    return l.polyline && Math.max(...l.polyline.map((p) => p[2])) < 1.0;
  });

  const pillarRadius = 0.9; // 1.8m diameter concrete pier

  // Flyover span spans Three.js X from -75 to +75 (SUMO x=275 to 425) where z >= 4.0m
  // We evaluate a regular grid of candidates at spacing, e.g. every 25m: -65, -45, -25, -5, 0, 5, 25, 45, 65
  const candidateXs = [-65, -45, -25, -5, 0, 5, 25, 45, 65];

  const auditedPillars = [];
  const intersectingPillars = [];
  const clearPillars = [];

  for (const cx of candidateXs) {
    // Flyover center is at Z_three = 0 (SUMO y = 350.0)
    const px = cx;
    const pz = 0.0;
    const sumoX = px + SUMO_OFFSET_X;
    const sumoY = SUMO_OFFSET_Y - pz;

    // Approximate deck elevation at this X
    // Flyover deck is at z=6.5m at |X|=75, rising to z=7.0m at X=0
    const frac = 1.0 - Math.min(1.0, Math.abs(cx) / 75.0);
    const deckElevation = 6.5 + frac * 0.5;

    let minClearance = 9999.0;
    let closestLane = null;
    const conflicts = [];

    for (const lane of surfaceLanes) {
      const halfW = (lane.width || 3.2) / 2.0;
      const pts = lane.polyline;
      for (let i = 0; i < pts.length - 1; i++) {
        const dSeg = pointToSegmentDist2D(sumoX, sumoY, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]);
        const clearance = dSeg - halfW - pillarRadius;
        if (dSeg < minClearance) {
          minClearance = dSeg;
          closestLane = lane.id;
        }
        if (clearance < 0.0) {
          conflicts.push({
            laneId: lane.id,
            penetrationM: Math.round(Math.abs(clearance) * 100) / 100,
          });
        }
      }
    }

    const isIntersecting = conflicts.length > 0;
    const pillarRecord = {
      threeX: cx,
      threeZ: pz,
      threeYBase: 0.0,
      threeYTop: deckElevation - 0.6,
      sumoX,
      sumoY,
      deckElevation: Math.round(deckElevation * 100) / 100,
      minDistanceM: Math.round(minClearance * 100) / 100,
      closestLane,
      status: isIntersecting ? 'INTERSECTING' : 'CLEAR',
      conflicts,
    };

    auditedPillars.push(pillarRecord);
    if (isIntersecting) {
      intersectingPillars.push(pillarRecord);
    } else {
      clearPillars.push(pillarRecord);
    }
  }

  return {
    pillars: auditedPillars,
    intersectingPillars,
    clearPillars,
    totalChecked: auditedPillars.length,
  };
}

/**
 * Build 3D mesh cylinder geometry for support piers.
 */
export function buildPillarsGeometry(pillarsList) {
  if (!pillarsList || pillarsList.length === 0) return null;
  const geoms = [];
  const radius = 0.85;

  for (const p of pillarsList) {
    const height = Math.max(1.0, p.threeYTop - p.threeYBase);
    const cyl = new THREE.CylinderGeometry(radius, radius, height, 16);
    cyl.translate(p.threeX, p.threeYBase + height / 2.0, p.threeZ);
    geoms.push(cyl);
  }

  return geoms.length > 0 ? BufferGeometryUtils.mergeGeometries(geoms, false) : null;
}

/**
 * Main Assembler: Process network3d.json into complete category-merged 3D geometry objects.
 */
export function compileNetwork3DGeometries(networkData) {
  if (!networkData) return null;

  const surfaceLanes = [];
  const flyoverLanes = [];
  const underpassLanes = [];

  for (const lane of networkData.lanes || []) {
    const eid = lane.edge_id || '';
    if (eid.startsWith('flyover')) {
      flyoverLanes.push(lane);
    } else if (eid.startsWith('orr_mainline')) {
      underpassLanes.push(lane);
    } else {
      surfaceLanes.push(lane);
    }
  }

  // 1. Road Ribbons
  const surfaceRoadGeoms = [];
  const flyoverRoadGeoms = [];
  const underpassRoadGeoms = [];

  // Markings
  const edgeLineGeoms = [];
  const dashedLineGeoms = [];
  const stopLineGeoms = [];

  for (const l of surfaceLanes) {
    const rg = buildRibbonGeometry(l.polyline, l.width);
    if (rg) surfaceRoadGeoms.push(rg);

    // Edge lines for normal lanes
    if (!l.is_internal) {
      const eg = buildEdgeLineGeometry(l.polyline, l.width, 'both');
      if (eg) edgeLineGeoms.push(eg);

      // Center dash for right lane (index 1)
      if (l.index === 1) {
        const dg = buildDashedLineGeometry(l.polyline);
        if (dg) dashedLineGeoms.push(dg);
      }
    }
  }

  for (const l of flyoverLanes) {
    const rg = buildRibbonGeometry(l.polyline, l.width);
    if (rg) flyoverRoadGeoms.push(rg);

    if (!l.is_internal) {
      const eg = buildEdgeLineGeometry(l.polyline, l.width, 'both');
      if (eg) edgeLineGeoms.push(eg);
      if (l.index === 1) {
        const dg = buildDashedLineGeometry(l.polyline);
        if (dg) dashedLineGeoms.push(dg);
      }
    }
  }

  for (const l of underpassLanes) {
    const rg = buildRibbonGeometry(l.polyline, l.width);
    if (rg) underpassRoadGeoms.push(rg);

    if (!l.is_internal) {
      const eg = buildEdgeLineGeometry(l.polyline, l.width, 'both');
      if (eg) edgeLineGeoms.push(eg);
      if (l.index === 1) {
        const dg = buildDashedLineGeometry(l.polyline);
        if (dg) dashedLineGeoms.push(dg);
      }
    }
  }

  // Stop lines at marathahalli_tls approach legs
  const approachLanes = ['leg_orr_n_in_0', 'leg_orr_n_in_1', 'leg_wf_in_0', 'leg_wf_in_1', 'leg_orr_s_in_0', 'leg_orr_s_in_1', 'leg_hal_in_0', 'leg_hal_in_1'];
  for (const aid of approachLanes) {
    const l = (networkData.lanes || []).find((x) => x.id === aid);
    if (l) {
      const slg = buildStopLineGeometry(l.polyline, l.width);
      if (slg) stopLineGeoms.push(slg);
    }
  }

  // 2. Junction Surfaces
  const junctionGeoms = [];
  for (const j of networkData.junctions || []) {
    const jg = buildJunctionGeometry(j.shape, j.coord ? j.coord[2] : 0.0);
    if (jg) junctionGeoms.push(jg);
  }

  // 3. Flyover Thickness and Parapet Barriers
  const deckThicknessGeoms = [];
  const barrierGeoms = [];

  // Eastbound outer corridor
  const ebDeckLanes = flyoverLanes.filter((l) => l.edge_id === 'flyover_eb_2' || l.edge_id === 'flyover_eb_3');
  if (ebDeckLanes.length > 0) {
    const dtg = buildDeckThicknessGeometry(ebDeckLanes[0].polyline, 6.8, 0.6);
    if (dtg) deckThicknessGeoms.push(dtg);
    const bg1 = buildParapetBarrierGeometry(ebDeckLanes[0].polyline, 3.4, 0.8, 0.3);
    if (bg1) barrierGeoms.push(bg1);
  }

  // Westbound outer corridor
  const wbDeckLanes = flyoverLanes.filter((l) => l.edge_id === 'flyover_wb_2' || l.edge_id === 'flyover_wb_3');
  if (wbDeckLanes.length > 0) {
    const dtg = buildDeckThicknessGeometry(wbDeckLanes[0].polyline, 6.8, 0.6);
    if (dtg) deckThicknessGeoms.push(dtg);
    const bg2 = buildParapetBarrierGeometry(wbDeckLanes[0].polyline, -3.4, 0.8, 0.3);
    if (bg2) barrierGeoms.push(bg2);
  }

  // 4. Audit & Build Pillars
  const pillarAudit = auditBridgePillars(networkData);
  // We place piers at all valid clear candidate stations
  const clearPillarsGeom = buildPillarsGeometry(pillarAudit.clearPillars);

  // Merge static categories into few unified geometries
  const mergedSurfaceRoads = surfaceRoadGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(surfaceRoadGeoms, false) : null;
  const mergedFlyoverRoads = flyoverRoadGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(flyoverRoadGeoms, false) : null;
  const mergedUnderpassRoads = underpassRoadGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(underpassRoadGeoms, false) : null;

  const allMarkings = [...edgeLineGeoms, ...dashedLineGeoms, ...stopLineGeoms];
  const mergedMarkings = allMarkings.length > 0 ? BufferGeometryUtils.mergeGeometries(allMarkings, false) : null;
  const mergedJunctions = junctionGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(junctionGeoms, false) : null;
  const mergedDeckThickness = deckThicknessGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(deckThicknessGeoms, false) : null;
  const mergedBarriers = barrierGeoms.length > 0 ? BufferGeometryUtils.mergeGeometries(barrierGeoms, false) : null;

  return {
    surfaceRoads: mergedSurfaceRoads,
    flyoverRoads: mergedFlyoverRoads,
    underpassRoads: mergedUnderpassRoads,
    markings: mergedMarkings,
    junctions: mergedJunctions,
    deckThickness: mergedDeckThickness,
    barriers: mergedBarriers,
    pillars: clearPillarsGeom,
    pillarAudit,
  };
}
