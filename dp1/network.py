"""Generate a clean 4-way signalised junction + lane-area (E2) queue detectors.

This synthetic junction is the Monday-demo network. The same code path accepts a real
OSM-derived net later (see docs/BUILD_PLAN.md, phase 6).
"""
from pathlib import Path
from . import config as C
from .sumo_utils import binary, run

NET_FILE = C.SUMO_DIR / "junction.net.xml"
DET_FILE = C.SUMO_DIR / "detectors.add.xml"


def build_network(net=C.NET) -> Path:
    C.SUMO_DIR.mkdir(parents=True, exist_ok=True)
    L = net.approach_length_m
    nodes = C.SUMO_DIR / "junction.nod.xml"
    edges = C.SUMO_DIR / "junction.edg.xml"
    pos = {"N": (0, L), "S": (0, -L), "E": (L, 0), "W": (-L, 0)}

    nodes.write_text(
        '<nodes>\n'
        f'  <node id="{C.TLS_ID}" x="0" y="0" type="traffic_light"/>\n'
        + "".join(f'  <node id="{a}" x="{x}" y="{y}" type="priority"/>\n' for a, (x, y) in pos.items())
        + '</nodes>\n'
    )
    edges.write_text(
        '<edges>\n'
        + "".join(
            f'  <edge id="{a}_in" from="{a}" to="{C.TLS_ID}" numLanes="{net.lanes}" speed="{net.speed_mps}"/>\n'
            f'  <edge id="{a}_out" from="{C.TLS_ID}" to="{a}" numLanes="{net.lanes}" speed="{net.speed_mps}"/>\n'
            for a in C.APPROACHES)
        + '</edges>\n'
    )
    run([binary("netconvert"), "--node-files", str(nodes), "--edge-files", str(edges),
         "--output-file", str(NET_FILE), "--no-turnarounds", "true",
         "--tls.default-type", "static", "--no-warnings", "true"])

    DET_FILE.write_text(
        '<additional>\n'
        + "".join(
            f'  <laneAreaDetector id="det_{a}_{i}" lane="{a}_in_{i}" pos="-{net.detector_length_m}" '
            f'endPos="-0.1" period="1" file="detector_out.xml"/>\n'
            for a in C.APPROACHES
            for i in range(net.lanes))
        + '</additional>\n'
    )
    return NET_FILE
