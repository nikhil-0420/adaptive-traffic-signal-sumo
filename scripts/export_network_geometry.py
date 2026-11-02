"""Export Marathahalli SUMO Network Geometry to compact JSON for Phasora Twin Engine.

Builds road visuals directly from the SUMO net source of truth:
- Lane shapes and widths
- Junction polygons and stop-line positions
- Link-to-TLS-index mapping
- E2 lane-area detector zones (25m approach strips)
- 3-tier classification: flyover (+7m), surface (0m), underpass (-4m)
"""

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NET_FILE = REPO_ROOT / "network" / "marathahalli" / "dist" / "marathahalli.net.xml"
DET_FILE = REPO_ROOT / "network" / "marathahalli" / "build" / "detectors.add.xml"
OUTPUT_FILE = REPO_ROOT / "frontend" / "src" / "data" / "marathahalli_geometry.json"

FLYOVER_EDGES = {
    "flyover_eb_1", "flyover_eb_2", "flyover_eb_3", "flyover_eb_4",
    "flyover_wb_1", "flyover_wb_2", "flyover_wb_3", "flyover_wb_4"
}
FLYOVER_JUNCTIONS = {"node_bridge_w", "node_bridge_mid", "node_bridge_e"}

UNDERPASS_EDGES = {"orr_mainline_nb", "orr_mainline_sb"}
UNDERPASS_JUNCTIONS = set()


def get_tier_and_z(edge_id: str, junction_id: str = ""):
    if edge_id in FLYOVER_EDGES or junction_id in FLYOVER_JUNCTIONS:
        return "flyover", 7.0
    if edge_id in UNDERPASS_EDGES or junction_id in UNDERPASS_JUNCTIONS:
        return "underpass", -4.0
    return "surface", 0.0


def parse_shape(shape_str: str):
    if not shape_str or not shape_str.strip():
        return []
    coords = []
    for pair in shape_str.strip().split(" "):
        parts = pair.split(",")
        if len(parts) >= 2:
            coords.append([round(float(parts[0]), 2), round(float(parts[1]), 2)])
    return coords


def main():
    print(f"Reading SUMO net from {NET_FILE}...")
    tree = ET.parse(NET_FILE)
    root = tree.getroot()

    loc_el = root.find("location")
    net_offset = [350.0, 350.0]
    conv_boundary = [0.0, 0.0, 700.0, 700.0]
    if loc_el is not None:
        if "netOffset" in loc_el.attrib:
            net_offset = [float(x) for x in loc_el.attrib["netOffset"].split(",")]
        if "convBoundary" in loc_el.attrib:
            conv_boundary = [float(x) for x in loc_el.attrib["convBoundary"].split(",")]

    lanes_dict = {}
    edges_list = []
    
    # Track internal lane tier based on junction
    junction_tiers = {}
    junctions_list = []
    for junc in root.findall("junction"):
        jid = junc.get("id", "")
        jtype = junc.get("type", "")
        if jtype == "internal":
            continue
        shape = parse_shape(junc.get("shape", ""))
        x = round(float(junc.get("x", 0)), 2)
        y = round(float(junc.get("y", 0)), 2)
        tier, z = get_tier_and_z("", jid)
        junction_tiers[jid] = tier
        junctions_list.append({
            "id": jid,
            "type": jtype,
            "x": x,
            "y": y,
            "z": z,
            "tier": tier,
            "shape": shape
        })

    # Parse edges and lanes
    for edge in root.findall("edge"):
        eid = edge.get("id", "")
        is_internal = edge.get("function") == "internal"
        
        # Check tier
        tier, z = "surface", 0.0
        if is_internal:
            # Look at junction id or name
            for jid in FLYOVER_JUNCTIONS:
                if f":{jid}" in eid:
                    tier, z = "flyover", 7.0
                    break
        else:
            tier, z = get_tier_and_z(eid)

        edge_lanes = []
        for lane in edge.findall("lane"):
            lid = lane.get("id", "")
            index = int(lane.get("index", 0))
            speed = round(float(lane.get("speed", 13.89)), 2)
            length = round(float(lane.get("length", 0)), 2)
            width = round(float(lane.get("width", 3.2)), 2)
            shape = parse_shape(lane.get("shape", ""))

            lane_data = {
                "id": lid,
                "edge_id": eid,
                "index": index,
                "tier": tier,
                "z": z,
                "speed": speed,
                "length": length,
                "width": width,
                "is_internal": is_internal,
                "shape": shape
            }
            lanes_dict[lid] = lane_data
            edge_lanes.append(lane_data)

        edges_list.append({
            "id": eid,
            "is_internal": is_internal,
            "tier": tier,
            "z": z,
            "lanes": edge_lanes
        })

    # Detectors parsing
    detectors = []
    if DET_FILE.exists():
        det_tree = ET.parse(DET_FILE)
        for d in det_tree.getroot().findall("laneAreaDetector"):
            did = d.get("id", "")
            lane_id = d.get("lane", "")
            pos = float(d.get("pos", -25.0))
            end_pos = float(d.get("endPos", -0.1))

            approach = "W"
            if "hal" in did:
                approach = "W"
            elif "wf" in did:
                approach = "E"
            elif "orr_s" in did:
                approach = "S"
            elif "orr_n" in did:
                approach = "N"

            # Compute detector polygon strip along the lane shape
            det_shape = []
            if lane_id in lanes_dict:
                lane_pts = lanes_dict[lane_id]["shape"]
                lane_len = lanes_dict[lane_id]["length"]
                # pos is negative from end of lane (e.g. -25m to -0.1m)
                # In SUMO pos="-25.0" means from (lane_len - 25m) to (lane_len - 0.1m)
                start_m = max(0.0, lane_len + pos)
                end_m = max(0.0, lane_len + end_pos)
                
                # Sample 2 points along lane polyline
                # For simplicity, calculate start and end points
                if len(lane_pts) >= 2:
                    p_start = lane_pts[0]
                    p_end = lane_pts[-1]
                    dx = p_end[0] - p_start[0]
                    dy = p_end[1] - p_start[1]
                    d_total = math.hypot(dx, dy)
                    if d_total > 0:
                        t1 = max(0.0, min(1.0, start_m / lane_len))
                        t2 = max(0.0, min(1.0, end_m / lane_len))
                        det_shape = [
                            [round(p_start[0] + dx * t1, 2), round(p_start[1] + dy * t1, 2)],
                            [round(p_start[0] + dx * t2, 2), round(p_start[1] + dy * t2, 2)]
                        ]

            detectors.append({
                "id": did,
                "lane": lane_id,
                "approach": approach,
                "pos_m": pos,
                "end_pos_m": end_pos,
                "shape": det_shape
            })

    # Parse TLS connections and stop lines for marathahalli_tls
    tls_connections = []
    stop_lines = []
    approach_legs = {
        "leg_hal_in": {"approach": "W", "name": "HAL West Approach"},
        "leg_wf_in": {"approach": "E", "name": "Whitefield East Approach"},
        "leg_orr_s_in": {"approach": "S", "name": "ORR South Approach"},
        "leg_orr_n_in": {"approach": "N", "name": "ORR North Approach"}
    }

    seen_stop_lanes = set()
    for conn in root.findall("connection"):
        tl = conn.get("tl", "")
        if tl == "marathahalli_tls":
            link_idx = int(conn.get("linkIndex", -1))
            from_edge = conn.get("from", "")
            from_lane = f"{from_edge}_{conn.get('fromLane', 0)}"
            to_edge = conn.get("to", "")
            to_lane = f"{to_edge}_{conn.get('toLane', 0)}"
            via_lane = conn.get("via", "")
            direction = conn.get("dir", "")
            state = conn.get("state", "")

            tls_connections.append({
                "link_index": link_idx,
                "from_edge": from_edge,
                "from_lane": from_lane,
                "to_edge": to_edge,
                "to_lane": to_lane,
                "via_lane": via_lane,
                "dir": direction,
                "state": state
            })

            # Check stop line
            if from_edge in approach_legs and from_lane not in seen_stop_lanes:
                seen_stop_lanes.add(from_lane)
                if from_lane in lanes_dict:
                    pts = lanes_dict[from_lane]["shape"]
                    if len(pts) >= 2:
                        p_last = pts[-1]
                        p_prev = pts[-2]
                        # Calculate perpendicular line across lane for stop line
                        dx = p_last[0] - p_prev[0]
                        dy = p_last[1] - p_prev[1]
                        dist = math.hypot(dx, dy)
                        if dist > 0:
                            nx = -dy / dist
                            ny = dx / dist
                            half_w = lanes_dict[from_lane]["width"] / 2.0
                            stop_lines.append({
                                "lane_id": from_lane,
                                "approach": approach_legs[from_edge]["approach"],
                                "link_index": link_idx,
                                "p1": [round(p_last[0] - nx * half_w, 2), round(p_last[1] - ny * half_w, 2)],
                                "p2": [round(p_last[0] + nx * half_w, 2), round(p_last[1] + ny * half_w, 2)],
                                "center": p_last,
                                "heading_deg": round((math.atan2(dx, dy) * 180 / math.pi) % 360, 1)
                            })

    # Sort stop lines by approach and link index
    stop_lines.sort(key=lambda s: (s["approach"], s["link_index"]))

    output_data = {
        "metadata": {
            "name": "marathahalli",
            "version": "1.0.0",
            "netOffset": net_offset,
            "convBoundary": conv_boundary,
            "center": [350.0, 350.0],
            "tls_id": "marathahalli_tls"
        },
        "junctions": junctions_list,
        "lanes": list(lanes_dict.values()),
        "detectors": detectors,
        "stop_lines": stop_lines,
        "tls_connections": tls_connections
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output_data, separators=(',', ':')), encoding="utf-8")
    print(f"Exported {len(lanes_dict)} lanes, {len(junctions_list)} junctions, {len(detectors)} detectors, {len(stop_lines)} stop lines to {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
