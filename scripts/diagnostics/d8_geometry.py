"""Diagnostic D8: Inbound Edge Geometry and Maximum Detector Capacity.

For each inbound approach edge to marathahalli_tls:
- Lane count
- Edge length
- Lane length
- Current detector pos / endPos
- Maximum physically available detector length without crossing upstream junctions or network boundary.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sumolib

DEFAULT_NET = Path("network/marathahalli/dist/marathahalli.net.xml")
DEFAULT_DET = Path("network/marathahalli/build/detectors.add.xml")

INBOUND_EDGES = {
    "N": "leg_orr_n_in",
    "S": "leg_orr_s_in",
    "E": "leg_wf_in",
    "W": "leg_hal_in",
}


def analyze_geometry(net_path: Path) -> list[dict]:
    net = sumolib.net.readNet(str(net_path))
    records = []

    for app, edge_id in INBOUND_EDGES.items():
        edge = net.getEdge(edge_id)
        lanes = edge.getLanes()
        edge_len = edge.getLength()
        from_node = edge.getFromNode()
        to_node = edge.getToNode()

        # Detector occupies pos="-25.0" to endPos="-0.1", meaning 24.9m length
        # Physical maximum on this edge is edge_len minus safety stopline buffer (0.1m)
        max_phys_len = round(edge_len - 0.1, 2)

        records.append({
            "approach": app,
            "edge_id": edge_id,
            "lane_count": len(lanes),
            "edge_length_m": round(edge_len, 2),
            "lane_length_m": round(lanes[0].getLength(), 2),
            "lane_width_m": round(lanes[0].getWidth(), 2),
            "current_detector_pos": "-25.0",
            "current_detector_endPos": "-0.1",
            "current_detector_span_m": 24.9,
            "from_node": from_node.getID(),
            "to_node": to_node.getID(),
            "max_phys_detector_length_m": max_phys_len,
            "physical_headroom_m": round(max_phys_len - 24.9, 2),
        })

    return records


def main():
    parser = argparse.ArgumentParser(description="Analyze inbound geometry and detector limits.")
    parser.add_argument("--net-file", type=str, default=str(DEFAULT_NET), help="Path to net.xml")
    args = parser.parse_args()

    records = analyze_geometry(Path(args.net_file))
    import pandas as pd
    df = pd.DataFrame(records)

    print("=" * 80)
    print("D8: INBOUND EDGE GEOMETRY & PHYSICAL DETECTOR EXTENSION LIMITS")
    print("=" * 80)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
