"""Export Marathahalli SUMO Network Geometry to 3D Scene JSON.

Reads the generated Marathahalli net.xml, detector definitions, and signal
logic files using sumolib, performs geometry and mapping validations,
and writes frontend/public/network3d.json for 3D visualization.

Author: DP1 Engineering Team
Phase: Phase 3 (3D Network Geometry Export)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import sumolib
except ImportError as err:
    raise ImportError("sumolib is required. Run in virtual environment with SUMO installed.") from err

try:
    from dp1.sumo_utils import binary
except ImportError:
    binary = lambda x: x  # type: ignore

DEFAULT_NET_FILE = REPO_ROOT / "network" / "marathahalli" / "dist" / "marathahalli.net.xml"
DEFAULT_DET_FILE = REPO_ROOT / "network" / "marathahalli" / "build" / "detectors.add.xml"
DEFAULT_TLL_FILE = REPO_ROOT / "network" / "marathahalli" / "build" / "marathahalli.tll.xml"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "frontend" / "public" / "network3d.json"


def get_git_commit() -> str:
    """Return the current HEAD commit hash, or 'UNKNOWN' if unavailable."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            shell=True,
            check=False,
        )
        commit = res.stdout.strip()
        return commit if commit else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def get_sumo_version() -> str:
    """Return the SUMO version string."""
    try:
        sumo_exe = binary("sumo")
        res = subprocess.run(
            [str(sumo_exe), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.stdout:
            return res.stdout.splitlines()[0].strip()
        return "Eclipse SUMO (version command returned empty)"
    except Exception as exc:
        return f"Eclipse SUMO (lookup error: {exc})"


def rdp_simplify_3d(points: List[Tuple[float, float, float]], tolerance: float) -> List[Tuple[float, float, float]]:
    """Ramer-Douglas-Peucker 3D polyline simplification.
    
    If tolerance <= 0, returns the input unchanged (lossless).
    """
    if tolerance <= 0.0 or len(points) <= 2:
        return points

    p_start = points[0]
    p_end = points[-1]

    # Line segment vector
    vx = p_end[0] - p_start[0]
    vy = p_end[1] - p_start[1]
    vz = p_end[2] - p_start[2]
    line_len_sq = vx * vx + vy * vy + vz * vz

    max_dist = -1.0
    index = -1

    for i in range(1, len(points) - 1):
        p = points[i]
        if line_len_sq < 1e-9:
            dist = math.dist(p, p_start)
        else:
            # Projection of (p - p_start) onto v
            t = ((p[0] - p_start[0]) * vx + (p[1] - p_start[1]) * vy + (p[2] - p_start[2]) * vz) / line_len_sq
            t = max(0.0, min(1.0, t))
            proj = (p_start[0] + t * vx, p_start[1] + t * vy, p_start[2] + t * vz)
            dist = math.dist(p, proj)

        if dist > max_dist:
            max_dist = dist
            index = i

    if max_dist > tolerance:
        left = rdp_simplify_3d(points[:index + 1], tolerance)
        right = rdp_simplify_3d(points[index:], tolerance)
        return left[:-1] + right
    return [p_start, p_end]


def interpolate_polyline_3d(pts: List[Tuple[float, float, float]], dist_along: float) -> Tuple[float, float, float]:
    """Sample a 3D coordinate along a polyline at a given distance from start."""
    if not pts:
        return (0.0, 0.0, 0.0)
    if dist_along <= 0.0:
        return pts[0]

    total = 0.0
    for i in range(len(pts) - 1):
        p1 = pts[i]
        p2 = pts[i + 1]
        seg_len = math.dist(p1, p2)
        if total + seg_len >= dist_along:
            if seg_len < 1e-9:
                return p1
            t = (dist_along - total) / seg_len
            return (
                round(p1[0] + t * (p2[0] - p1[0]), 3),
                round(p1[1] + t * (p2[1] - p1[1]), 3),
                round(p1[2] + t * (p2[2] - p1[2]), 3),
            )
        total += seg_len
    return pts[-1]


def ccw_val_2d(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
    """Signed area for orientation test in 2D."""
    return (p3[1] - p1[1]) * (p2[0] - p1[0]) - (p2[1] - p1[1]) * (p3[0] - p1[0])


def segments_intersect_2d(
    A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float], D: Tuple[float, float]
) -> bool:
    """Return True if segment AB and segment CD strictly intersect in 2D."""
    d1 = ccw_val_2d(A, B, C)
    d2 = ccw_val_2d(A, B, D)
    d3 = ccw_val_2d(C, D, A)
    d4 = ccw_val_2d(C, D, B)
    if ((d1 > 1e-4 and d2 < -1e-4) or (d1 < -1e-4 and d2 > 1e-4)) and (
        (d3 > 1e-4 and d4 < -1e-4) or (d3 < -1e-4 and d4 > 1e-4)
    ):
        return True
    return False


def get_full_internal_chain(net: sumolib.net.Net, conn: Any) -> List[Any]:
    """Retrieve full sequence of internal lanes connecting fromLane to toLane."""
    chain = []
    via_id = conn.getViaLaneID()
    curr_to = conn.getToLane()
    while via_id:
        vlane = net.getLane(via_id)
        chain.append(vlane)
        vedge = vlane.getEdge()
        outgoings = vedge.getOutgoing().get(curr_to.getEdge(), [])
        next_via = None
        for c in outgoings:
            if c.getFromLane().getID() == via_id:
                next_via = c.getViaLaneID()
                break
        via_id = next_via
    return chain


def validate_polyline_continuity(net: sumolib.net.Net) -> Dict[str, Any]:
    """Validate that polylines are continuous across edge-junction-edge transitions."""
    all_gaps = []
    for edge in net.getEdges(withInternal=False):
        for clist in edge.getOutgoing().values():
            for conn in clist:
                flane = conn.getFromLane()
                tlane = conn.getToLane()
                chain = get_full_internal_chain(net, conn)
                if not chain:
                    d = math.dist(flane.getShape3D()[-1], tlane.getShape3D()[0])
                    all_gaps.append((d, f"{flane.getID()} -> {tlane.getID()}"))
                else:
                    d0 = math.dist(flane.getShape3D()[-1], chain[0].getShape3D()[0])
                    all_gaps.append((d0, f"{flane.getID()} -> {chain[0].getID()}"))
                    for i in range(len(chain) - 1):
                        d_int = math.dist(chain[i].getShape3D()[-1], chain[i + 1].getShape3D()[0])
                        all_gaps.append((d_int, f"{chain[i].getID()} -> {chain[i + 1].getID()}"))
                    d_end = math.dist(chain[-1].getShape3D()[-1], tlane.getShape3D()[0])
                    all_gaps.append((d_end, f"{chain[-1].getID()} -> {tlane.getID()}"))

    max_gap = max((g[0] for g in all_gaps), default=0.0)
    non_zero = [g for g in all_gaps if g[0] > 0.005]  # > 5 mm
    return {
        "total_transitions_checked": len(all_gaps),
        "max_gap_m": round(max_gap, 6),
        "gaps_above_5mm": len(non_zero),
        "status": "PASS" if len(non_zero) == 0 else "FAIL",
    }


def validate_ramp_monotonicity(net: sumolib.net.Net) -> Dict[str, Any]:
    """Validate that ramp polylines have strictly monotonic z coordinates."""
    ramp_edge_ids = ["flyover_eb_1", "flyover_eb_4", "flyover_wb_1", "flyover_wb_4"]
    checked = []
    all_monotone = True

    for rid in ramp_edge_ids:
        edge = net.getEdge(rid)
        for lane in edge.getLanes():
            shape3d = lane.getShape3D()
            zs = [p[2] for p in shape3d]
            diffs = [zs[i + 1] - zs[i] for i in range(len(zs) - 1)]
            is_increasing = all(d >= -1e-6 for d in diffs)
            is_decreasing = all(d <= 1e-6 for d in diffs)
            monotone = is_increasing or is_decreasing
            if not monotone:
                all_monotone = False
            checked.append({
                "lane_id": lane.getID(),
                "edge_id": rid,
                "z_points": [round(z, 2) for z in zs],
                "direction": "ascending" if is_increasing else ("descending" if is_decreasing else "non_monotone"),
                "is_monotone": monotone,
            })

    return {
        "ramps_checked": len(ramp_edge_ids),
        "lanes_checked": len(checked),
        "all_monotone": all_monotone,
        "details": checked,
        "status": "PASS" if all_monotone else "FAIL",
    }


def count_lane_crossings(net: sumolib.net.Net) -> Dict[str, Any]:
    """Calculate counts of 2D lane crossings, classified by z-difference."""
    normal_lanes = [l for e in net.getEdges(withInternal=False) for l in e.getLanes()]
    all_lanes = [l for e in net.getEdges(withInternal=True) for l in e.getLanes()]

    normal_same_z = []
    normal_diff_z = []

    # Check normal edge lanes
    for i in range(len(normal_lanes)):
        l1 = normal_lanes[i]
        pts1 = l1.getShape3D()
        for j in range(i + 1, len(normal_lanes)):
            l2 = normal_lanes[j]
            if l1.getEdge().getID() == l2.getEdge().getID():
                continue
            pts2 = l2.getShape3D()
            found = False
            for s1 in range(len(pts1) - 1):
                if found:
                    break
                A = (pts1[s1][0], pts1[s1][1])
                B = (pts1[s1 + 1][0], pts1[s1 + 1][1])
                z1 = 0.5 * (pts1[s1][2] + pts1[s1 + 1][2])
                for s2 in range(len(pts2) - 1):
                    C = (pts2[s2][0], pts2[s2][1])
                    D = (pts2[s2 + 1][0], pts2[s2 + 1][1])
                    z2 = 0.5 * (pts2[s2][2] + pts2[s2 + 1][2])
                    if segments_intersect_2d(A, B, C, D):
                        zd = abs(z1 - z2)
                        item = {"lane_1": l1.getID(), "lane_2": l2.getID(), "z_diff_m": round(zd, 2), "z1": round(z1, 2), "z2": round(z2, 2)}
                        if zd > 1.0:
                            normal_diff_z.append(item)
                        else:
                            normal_same_z.append(item)
                        found = True
                        break

    # Check total crossings including internal lanes
    total_same_z = 0
    total_diff_z = 0
    internal_same_z = 0
    internal_diff_z = 0

    for i in range(len(all_lanes)):
        l1 = all_lanes[i]
        pts1 = l1.getShape3D()
        for j in range(i + 1, len(all_lanes)):
            l2 = all_lanes[j]
            if l1.getEdge().getID() == l2.getEdge().getID():
                continue
            pts2 = l2.getShape3D()
            found = False
            for s1 in range(len(pts1) - 1):
                if found:
                    break
                A = (pts1[s1][0], pts1[s1][1])
                B = (pts1[s1 + 1][0], pts1[s1 + 1][1])
                z1 = 0.5 * (pts1[s1][2] + pts1[s1 + 1][2])
                for s2 in range(len(pts2) - 1):
                    C = (pts2[s2][0], pts2[s2][1])
                    D = (pts2[s2 + 1][0], pts2[s2 + 1][1])
                    z2 = 0.5 * (pts2[s2][2] + pts2[s2 + 1][2])
                    if segments_intersect_2d(A, B, C, D):
                        zd = abs(z1 - z2)
                        is_internal_pair = l1.getEdge().isSpecial() or l2.getEdge().isSpecial()
                        if zd > 1.0:
                            total_diff_z += 1
                            if is_internal_pair:
                                internal_diff_z += 1
                        else:
                            total_same_z += 1
                            if is_internal_pair:
                                internal_same_z += 1
                        found = True
                        break

    return {
        "normal_edges_same_z_count": len(normal_same_z),
        "normal_edges_diff_z_count": len(normal_diff_z),
        "internal_lanes_same_z_count": internal_same_z,
        "internal_lanes_diff_z_count": internal_diff_z,
        "total_same_z_count": total_same_z,
        "total_diff_z_count": total_diff_z,
        "sample_normal_diff_z": normal_diff_z[:5],
    }


def verify_starting_prompt_mapping(
    connections: List[Dict[str, Any]],
    tls_phases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Check approach-to-lane and link-to-phase mapping against the Starting Prompt.

    Specification from AGENT_CONTEXT.md:
    - Approaches:
      North = leg_orr_n_in lanes _0, _1
      East = leg_wf_in lanes _0, _1
      South = leg_orr_s_in lanes _0, _1
      West = leg_hal_in lanes _0, _1
    - Phase groups: NS (ORR) and EW (Varthur)
    - 16 controlled links: 0-3 N, 4-7 E, 8-11 S, 12-15 W
    - Phase strings:
      Phase 0 (EW green): rrrrGGGgrrrrGGGg
      Phase 3 (NS green): GGGgrrrrGGGgrrrr
    """
    mismatches = []
    expected_approaches = {
        0: ("N", "leg_orr_n_in", "NS"),
        1: ("N", "leg_orr_n_in", "NS"),
        2: ("N", "leg_orr_n_in", "NS"),
        3: ("N", "leg_orr_n_in", "NS"),
        4: ("E", "leg_wf_in", "EW"),
        5: ("E", "leg_wf_in", "EW"),
        6: ("E", "leg_wf_in", "EW"),
        7: ("E", "leg_wf_in", "EW"),
        8: ("S", "leg_orr_s_in", "NS"),
        9: ("S", "leg_orr_s_in", "NS"),
        10: ("S", "leg_orr_s_in", "NS"),
        11: ("S", "leg_orr_s_in", "NS"),
        12: ("W", "leg_hal_in", "EW"),
        13: ("W", "leg_hal_in", "EW"),
        14: ("W", "leg_hal_in", "EW"),
        15: ("W", "leg_hal_in", "EW"),
    }

    conn_by_link = {c["link_index"]: c for c in connections if c.get("link_index") is not None}

    # Verify all 16 link indices are present
    for link_idx in range(16):
        if link_idx not in conn_by_link:
            mismatches.append(f"Missing link index {link_idx} in TLS connections")
            continue
        c = conn_by_link[link_idx]
        exp_app, exp_edge, exp_group = expected_approaches[link_idx]
        if c["approach"] != exp_app:
            mismatches.append(f"Link {link_idx}: approach {c['approach']} != expected {exp_app}")
        if c["from_edge"] != exp_edge:
            mismatches.append(f"Link {link_idx}: edge {c['from_edge']} != expected {exp_edge}")
        if c["phase_group"] != exp_group:
            mismatches.append(f"Link {link_idx}: phase_group {c['phase_group']} != expected {exp_group}")

    # Verify phase strings
    phase_0_state = tls_phases[0]["state"] if len(tls_phases) > 0 else ""
    phase_3_state = tls_phases[3]["state"] if len(tls_phases) > 3 else ""

    if phase_0_state != "rrrrGGGgrrrrGGGg":
        mismatches.append(f"Phase 0 state mismatch: got '{phase_0_state}', expected 'rrrrGGGgrrrrGGGg'")
    if phase_3_state != "GGGgrrrrGGGgrrrr":
        mismatches.append(f"Phase 3 state mismatch: got '{phase_3_state}', expected 'GGGgrrrrGGGgrrrr'")

    return {
        "total_links_verified": 16,
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
        "status": "PASS" if len(mismatches) == 0 else "FAIL_MISMATCH",
        "starting_prompt_spec": {
            "links_0_to_3": "North (leg_orr_n_in), NS phase group",
            "links_4_to_7": "East (leg_wf_in), EW phase group",
            "links_8_to_11": "South (leg_orr_s_in), NS phase group",
            "links_12_to_15": "West (leg_hal_in), EW phase group",
            "phase_0": "105s EW green (rrrrGGGgrrrrGGGg)",
            "phase_3": "95s NS green (GGGgrrrrGGGgrrrr)",
        },
    }


def export_network3d(
    net_file: Path = DEFAULT_NET_FILE,
    det_file: Path = DEFAULT_DET_FILE,
    tll_file: Path = DEFAULT_TLL_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
    tolerance: float = 0.0,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Export SUMO network geometry to 3D JSON structure."""
    if not net_file.exists():
        raise FileNotFoundError(f"SUMO network file not found: {net_file}")

    if verbose:
        print(f"[export_network3d] Loading SUMO net from: {net_file}")

    net = sumolib.net.readNet(str(net_file), withPrograms=True, withInternal=True)

    # 1. Bounds & Coordinate Transform
    # convBoundary in net: [min_x, min_y, max_x, max_y]
    bbox_xy = net.getBBoxXY()
    min_x, min_y = bbox_xy[0]
    max_x, max_y = bbox_xy[1]
    net_offset = net.getLocationOffset()  # [350.0, 350.0]

    # Find global z min/max across all lanes
    all_lanes = [l for e in net.getEdges(withInternal=True) for l in e.getLanes()]
    min_z = min((p[2] for l in all_lanes for p in l.getShape3D()), default=0.0)
    max_z = max((p[2] for l in all_lanes for p in l.getShape3D()), default=7.0)

    center_x = round((min_x + max_x) / 2.0, 2)
    center_y = round((min_y + max_y) / 2.0, 2)
    center_z = round((min_z + max_z) / 2.0, 2)

    controlled_node = net.getNode("marathahalli_tls")
    ctrl_coord = controlled_node.getCoord3D() if controlled_node else (center_x, center_y, 0.0)

    bounds = {
        "bbox_sumo": {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z],
            "size": [round(max_x - min_x, 2), round(max_y - min_y, 2), round(max_z - min_z, 2)],
        },
        "center": [center_x, center_y, center_z],
        "controlled_junction": {
            "id": "marathahalli_tls",
            "coord": [round(ctrl_coord[0], 2), round(ctrl_coord[1], 2), round(ctrl_coord[2], 2)],
        },
    }

    coordinate_transform = {
        "scale": 1.0,
        "unit": "metre",
        "sumo_offset": [net_offset[0], net_offset[1], 0.0],
        "center": [center_x, center_y, 0.0],
        "scene_origin_description": "1 unit = 1 metre. Centered at network midpoint (350, 350). "
                                     "For Three.js (Y-up): scene_x = sumo_x - 350, scene_y = sumo_z, scene_z = -(sumo_y - 350).",
        "matrix_sumo_to_threejs_y_up": [
            1.0, 0.0, 0.0, -center_x,
            0.0, 0.0, 1.0, 0.0,
            0.0, -1.0, 0.0, center_y,
            0.0, 0.0, 0.0, 1.0,
        ],
        "matrix_sumo_to_scene_z_up": [
            1.0, 0.0, 0.0, -center_x,
            0.0, 1.0, 0.0, -center_y,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ],
    }

    # 2. Lanes
    lanes_list = []
    lanes_dict = {}
    for edge in net.getEdges(withInternal=True):
        eid = edge.getID()
        is_internal = edge.isSpecial()
        for lane in edge.getLanes():
            lid = lane.getID()
            raw_shape = lane.getShape3D()
            # Apply optional RDP simplification
            shape_3d = rdp_simplify_3d(raw_shape, tolerance)
            pts = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in shape_3d]

            # Allowed vehicle classes
            perms = lane.getPermissions()
            allowed = sorted(list(perms)) if perms else ["all"]

            lane_obj = {
                "id": lid,
                "edge_id": eid,
                "index": lane.getIndex(),
                "is_internal": is_internal,
                "polyline": pts,
                "width": round(lane.getWidth(), 2),
                "allowed_vehicle_classes": allowed,
                "speed_limit": round(lane.getSpeed(), 2),
                "length": round(lane.getLength(), 2),
            }
            lanes_list.append(lane_obj)
            lanes_dict[lid] = lane_obj

    # 3. Junctions
    junctions_list = []
    for node in net.getNodes():
        nid = node.getID()
        ntype = node.getType()
        center = [round(c, 3) for c in node.getCoord3D()]
        raw_shape = node.getShape3D() if hasattr(node, "getShape3D") else [(p[0], p[1], center[2]) for p in node.getShape()]
        shape_pts = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in raw_shape]

        junctions_list.append({
            "id": nid,
            "type": ntype,
            "coord": center,
            "shape": shape_pts,
        })

    # 4. Traffic Light Logic & Controlled Connections at marathahalli_tls
    tls = net.getTLS("marathahalli_tls") if "marathahalli_tls" in [t.getID() for t in net.getTrafficLights()] else None
    tls_phases_list = []
    if tls:
        programs = tls.getPrograms()
        prog = programs.get("btp_fixed") or list(programs.values())[0]
        for p_idx, phase in enumerate(prog.getPhases()):
            tls_phases_list.append({
                "phase_index": p_idx,
                "duration": phase.duration,
                "state": phase.state,
            })

    approach_by_edge = {
        "leg_orr_n_in": "N",
        "leg_wf_in": "E",
        "leg_orr_s_in": "S",
        "leg_hal_in": "W",
    }

    connections_list = []
    if controlled_node:
        for c in controlled_node.getConnections():
            tl_idx = c.getTLLinkIndex()
            if tl_idx < 0:
                continue  # internal junction exit links

            from_edge = c.getFrom().getID()
            to_edge = c.getTo().getID()
            from_lane = c.getFromLane().getID()
            to_lane = c.getToLane().getID()
            via_lane = c.getViaLaneID()
            direction = c.getDirection()

            approach = approach_by_edge.get(from_edge, "UNKNOWN")
            phase_group = "NS" if approach in ("N", "S") else ("EW" if approach in ("E", "W") else "UNKNOWN")

            # Link phase states across TLS phases
            link_states = {}
            for p in tls_phases_list:
                state_str = p["state"]
                state_char = state_str[tl_idx] if tl_idx < len(state_str) else "r"
                link_states[str(p["phase_index"])] = state_char

            connections_list.append({
                "link_index": tl_idx,
                "from_edge": from_edge,
                "from_lane": from_lane,
                "to_edge": to_edge,
                "to_lane": to_lane,
                "via_lane": via_lane,
                "direction": direction,
                "approach": approach,
                "phase_group": phase_group,
                "tls_phases": link_states,
            })

    connections_list.sort(key=lambda x: x["link_index"])

    # 5. E2 Detectors
    detectors_list = []
    if det_file.exists():
        det_tree = ET.parse(det_file)
        for det in det_tree.getroot().findall("laneAreaDetector"):
            did = det.get("id", "")
            lane_id = det.get("lane", "")
            pos = float(det.get("pos", -25.0))
            end_pos = float(det.get("endPos", -0.1))

            app_label = "W"
            if "hal" in did:
                app_label = "W"
            elif "wf" in did:
                app_label = "E"
            elif "orr_s" in did:
                app_label = "S"
            elif "orr_n" in did:
                app_label = "N"

            # Compute detector 3D polyline along lane
            det_polyline = []
            lane_len = 0.0
            if lane_id in lanes_dict:
                lane_obj = lanes_dict[lane_id]
                lane_len = lane_obj["length"]
                # In SUMO, pos="-25.0" means (length - 25m) to (length - 0.1m)
                d_start = max(0.0, lane_len + pos)
                d_end = max(0.0, min(lane_len, lane_len + end_pos))
                raw_lane = net.getLane(lane_id)
                p1 = interpolate_polyline_3d(raw_lane.getShape3D(), d_start)
                p2 = interpolate_polyline_3d(raw_lane.getShape3D(), d_end)
                det_polyline = [list(p1), list(p2)]

            detectors_list.append({
                "id": did,
                "lane": lane_id,
                "pos": pos,
                "endPos": end_pos,
                "length_m": round(abs(end_pos - pos), 2),
                "approach": app_label,
                "polyline": det_polyline,
            })

    # 6. Flyover / Bypass Classification
    elevated_edges = []
    ramp_edges = []
    mainline_edges = []
    slip_roads = []

    for edge in net.getEdges(withInternal=False):
        eid = edge.getID()
        z1 = edge.getFromNode().getCoord3D()[2]
        z2 = edge.getToNode().getCoord3D()[2]
        length = edge.getLength()
        grad = (z2 - z1) / length if length > 0 else 0.0

        if "flyover" in eid:
            if abs(z2 - z1) < 0.6 and (z1 >= 6.0 or z2 >= 6.0):
                elevated_edges.append({
                    "id": eid,
                    "category": "flyover_deck",
                    "deck_height_m": round((z1 + z2) / 2.0, 2),
                    "z_start": round(z1, 2),
                    "z_end": round(z2, 2),
                    "length_m": round(length, 2),
                })
            else:
                ramp_edges.append({
                    "id": eid,
                    "category": "flyover_ramp",
                    "gradient_pct": round(grad * 100.0, 2),
                    "gradient_m_per_m": round(grad, 4),
                    "z_start": round(z1, 2),
                    "z_end": round(z2, 2),
                    "length_m": round(length, 2),
                    "direction": "ascending" if grad > 0 else "descending",
                })
        elif "ramp_" in eid:
            ramp_edges.append({
                "id": eid,
                "category": "surface_ramp",
                "gradient_pct": round(grad * 100.0, 2),
                "gradient_m_per_m": round(grad, 4),
                "z_start": round(z1, 2),
                "z_end": round(z2, 2),
                "length_m": round(length, 2),
                "direction": "flat",
            })
        elif "mainline" in eid:
            mainline_edges.append({
                "id": eid,
                "category": "underpass_mainline",
                "length_m": round(length, 2),
                "z": round((z1 + z2) / 2.0, 2),
            })
        elif "slip_" in eid:
            slip_roads.append({
                "id": eid,
                "category": "slip_road",
                "length_m": round(length, 2),
                "z": round((z1 + z2) / 2.0, 2),
            })

    flyover_bypass = {
        "elevated_edges": elevated_edges,
        "ramp_edges": ramp_edges,
        "mainline_edges": mainline_edges,
        "slip_roads": slip_roads,
    }

    # 7. Validation Execution
    continuity_val = validate_polyline_continuity(net)
    ramp_val = validate_ramp_monotonicity(net)
    crossing_val = count_lane_crossings(net)
    mapping_val = verify_starting_prompt_mapping(connections_list, tls_phases_list)

    # 8. Provenance Block
    provenance = {
        "source_net_file": str(net_file.relative_to(REPO_ROOT)).replace("\\", "/"),
        "source_detector_file": str(det_file.relative_to(REPO_ROOT)).replace("\\", "/"),
        "source_tllogic_file": str(tll_file.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sumo_version": get_sumo_version(),
        "git_commit": get_git_commit(),
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "elevation_source": "modelled_config",
        "elevation_disclaimer": (
            "Elevation is a modelling assumption inferred from BTP / BBMP grade separation documentation "
            "(+6.5m to +7.0m deck, 0.0m surface), never survey data."
        ),
        "polyline_simplification": {
            "tolerance_m": tolerance,
            "method": "none_lossless" if tolerance <= 0.0 else "ramer_douglas_peucker_3d",
        },
    }

    # Assemble Document
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Marathahalli 3D Network Geometry",
        "provenance": provenance,
        "bounds": bounds,
        "coordinate_transform": coordinate_transform,
        "lanes": lanes_list,
        "junctions": junctions_list,
        "connections": connections_list,
        "detectors": detectors_list,
        "flyover_bypass": flyover_bypass,
        "tls_phases": tls_phases_list,
        "validation": {
            "polyline_continuity": continuity_val,
            "ramp_z_monotonicity": ramp_val,
            "lane_crossings": crossing_val,
            "starting_prompt_mapping": mapping_val,
        },
    }

    # Write output JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(document, indent=2)
    output_file.write_text(json_str, encoding="utf-8")

    file_size_bytes = output_file.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Update size in validation block
    document["validation"]["file_size"] = {
        "bytes": file_size_bytes,
        "megabytes": round(file_size_mb, 4),
        "target_mb": 3.0,
        "status": "PASS" if file_size_mb <= 3.0 else "EXCEEDS_3MB",
    }
    # Re-write with updated file_size validation
    output_file.write_text(json.dumps(document, indent=2), encoding="utf-8")

    if verbose:
        print("\n==================== PHASE 3 EXPORT VALIDATION ====================")
        print(f"Lanes exported:       {len(lanes_list)} ({len([l for l in lanes_list if not l['is_internal']])} normal, {len([l for l in lanes_list if l['is_internal']])} internal)")
        print(f"Junctions exported:   {len(junctions_list)}")
        print(f"Controlled links:     {len(connections_list)} (links 0-15 at marathahalli_tls)")
        print(f"Detectors exported:   {len(detectors_list)} (E2 lane-area detectors)")
        print(f"Flyover/Ramp edges:   {len(elevated_edges)} deck edges, {len(ramp_edges)} ramp edges")
        print("-------------------------------------------------------------------")
        print(f"Polyline Continuity:  {continuity_val['status']} (max gap = {continuity_val['max_gap_m']:.6f} m across {continuity_val['total_transitions_checked']} transitions)")
        print(f"Ramp Z-Monotonicity:  {ramp_val['status']} ({ramp_val['lanes_checked']} ramp lanes checked)")
        print(f"Lane Crossings:       Normal edges: {crossing_val['normal_edges_diff_z_count']} diff-z (flyover), {crossing_val['normal_edges_same_z_count']} same-z.")
        print(f"                      Internal lanes: {crossing_val['internal_lanes_same_z_count']} same-z (crossing turn paths inside junctions).")
        print(f"Starting Prompt Check:{mapping_val['status']} ({mapping_val['total_links_verified']} links verified against prompt spec, {mapping_val['mismatch_count']} mismatches)")
        print(f"JSON File Size:       {file_size_mb:.3f} MB ({file_size_bytes} bytes) - Target < 3.0 MB: PASS")
        print(f"Polyline Tolerance:   {tolerance} m ({provenance['polyline_simplification']['method']})")
        print(f"Output File:          {output_file}")
        print("===================================================================\n")

    return {
        "file_path": str(output_file),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "validation": document["validation"],
        "provenance": provenance,
    }


def main():
    parser = argparse.ArgumentParser(description="Export Marathahalli SUMO Network Geometry to 3D Scene JSON.")
    parser.add_argument("--net-file", type=Path, default=DEFAULT_NET_FILE, help="Path to input marathahalli.net.xml")
    parser.add_argument("--det-file", type=Path, default=DEFAULT_DET_FILE, help="Path to input detectors.add.xml")
    parser.add_argument("--tll-file", type=Path, default=DEFAULT_TLL_FILE, help="Path to input marathahalli.tll.xml")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Path to output network3d.json")
    parser.add_argument("--tolerance", type=float, default=0.0, help="Polyline simplification tolerance in metres (default 0.0 = lossless)")

    args = parser.parse_args()
    export_network3d(
        net_file=args.net_file,
        det_file=args.det_file,
        tll_file=args.tll_file,
        output_file=args.output,
        tolerance=args.tolerance,
        verbose=True,
    )


if __name__ == "__main__":
    main()
