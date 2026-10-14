"""Reproducible builder for the Marathahalli Bridge site network.

Grounded in OpenCity geospatial datasets and Bengaluru Traffic Police (BTP)
signal timing data (Airport Police Station - Marathalli Bridge Junction).
Models grade-separated Varthur Road flyover over the Outer Ring Road (ORR),
surface connector ramps, slip turns, and the single verified surface traffic-signal
controlled node (marathahalli_tls).

Author: DP1 Engineering Team
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add repo root to sys.path so dp1 modules can be imported
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dp1.sumo_utils import binary, run

NETWORK_DIR = Path(__file__).resolve().parent
BUILD_DIR = NETWORK_DIR / "build"
DIST_DIR = NETWORK_DIR / "dist"
SOURCE_DIR = NETWORK_DIR / "source"

NODES_FILE = BUILD_DIR / "marathahalli.nod.xml"
EDGES_FILE = BUILD_DIR / "marathahalli.edg.xml"
CONNS_FILE = BUILD_DIR / "marathahalli.con.xml"
TLL_FILE = BUILD_DIR / "marathahalli.tll.xml"
DET_FILE = BUILD_DIR / "detectors.add.xml"
NET_FILE = DIST_DIR / "marathahalli.net.xml"
SUMOCFG_FILE = DIST_DIR / "marathahalli.sumocfg"

# Model metadata
NETWORK_METADATA = {
    "network_name": "marathahalli",
    "network_model_version": "1.0.0",
    "source_snapshot_id": "opencity_bbmp_20261014",
    "signal_plan_id": "btp_airport_ps_marathahalli_v1",
    "assumption_status": {
        "flyover_grade_separation": "verified",
        "arterial_alignment_orr_varthur": "verified",
        "surface_signal_controlled_node": "verified",
        "signal_phase_durations_btp": "verified",
        "lane_counts_from_road_width": "inferred",
        "slip_road_radii": "inferred",
        "traffic_volume_counts": "unknown_synthetic_demand"
    }
}


def generate_nodes():
    """Generate node definitions with explicit coordinates and elevation."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<nodes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/nodes_file.xsd">
    <!-- Network Boundaries (Arterial entries/exits) -->
    <node id="node_hal_w" x="-350.0" y="0.0" z="0.0" type="priority"/>
    <node id="node_wf_e" x="350.0" y="0.0" z="0.0" type="priority"/>
    <node id="node_orr_n" x="0.0" y="350.0" z="0.0" type="priority"/>
    <node id="node_orr_s" x="0.0" y="-350.0" z="0.0" type="priority"/>

    <!-- Grade Separation: Ramp Split & Merge Nodes -->
    <node id="node_hal_split" x="-180.0" y="0.0" z="0.0" type="priority"/>
    <node id="node_wf_split" x="180.0" y="0.0" z="0.0" type="priority"/>
    <node id="node_orr_n_split" x="0.0" y="180.0" z="0.0" type="priority"/>
    <node id="node_orr_s_split" x="0.0" y="-180.0" z="0.0" type="priority"/>

    <!-- Elevated Flyover Bridge Overpass (Z = 6.5m to 7.0m above ORR) -->
    <node id="node_bridge_w" x="-75.0" y="0.0" z="6.5" type="priority"/>
    <node id="node_bridge_mid" x="0.0" y="0.0" z="7.0" type="priority"/>
    <node id="node_bridge_e" x="75.0" y="0.0" z="6.5" type="priority"/>

    <!-- Surface Level Junction Approaches (Z = 0.0m) -->
    <node id="node_junc_w" x="-45.0" y="-18.0" z="0.0" type="priority"/>
    <node id="node_junc_e" x="45.0" y="-18.0" z="0.0" type="priority"/>
    <node id="node_junc_n" x="0.0" y="25.0" z="0.0" type="priority"/>
    <node id="node_junc_s" x="0.0" y="-60.0" z="0.0" type="priority"/>

    <!-- Verified Signal-Controlled Surface Junction -->
    <node id="marathahalli_tls" x="0.0" y="-18.0" z="0.0" type="traffic_light"/>
</nodes>
"""
    NODES_FILE.write_text(xml, encoding="utf-8")


def generate_edges():
    """Generate edge definitions including elevated flyover, mainline, and surface legs."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<edges xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/edges_file.xsd">
    <!-- Outer HAL Arterial (Dual Carriageway, 2 lanes each direction, 60 km/h) -->
    <edge id="hal_in" from="node_hal_w" to="node_hal_split" numLanes="2" speed="16.67"/>
    <edge id="hal_out" from="node_hal_split" to="node_hal_w" numLanes="2" speed="16.67"/>

    <!-- Outer Whitefield Arterial (Dual Carriageway, 2 lanes each direction, 60 km/h) -->
    <edge id="wf_in" from="node_wf_e" to="node_wf_split" numLanes="2" speed="16.67"/>
    <edge id="wf_out" from="node_wf_split" to="node_wf_e" numLanes="2" speed="16.67"/>

    <!-- Outer ORR North Arterial (KR Puram, Dual Carriageway, 2 lanes, 60 km/h) -->
    <edge id="orr_n_in" from="node_orr_n" to="node_orr_n_split" numLanes="2" speed="16.67"/>
    <edge id="orr_n_out" from="node_orr_n_split" to="node_orr_n" numLanes="2" speed="16.67"/>

    <!-- Outer ORR South Arterial (Kadubeesanahalli, Dual Carriageway, 2 lanes, 60 km/h) -->
    <edge id="orr_s_in" from="node_orr_s" to="node_orr_s_split" numLanes="2" speed="16.67"/>
    <edge id="orr_s_out" from="node_orr_s_split" to="node_orr_s" numLanes="2" speed="16.67"/>

    <!-- GRADE-SEPARATED MARATHAHALLI FLYOVER (Elevated overpass, continuous flow, 60 km/h) -->
    <!-- Eastbound Flyover: HAL -> Whitefield -->
    <edge id="flyover_eb_1" from="node_hal_split" to="node_bridge_w" numLanes="2" speed="16.67"/>
    <edge id="flyover_eb_2" from="node_bridge_w" to="node_bridge_mid" numLanes="2" speed="16.67"/>
    <edge id="flyover_eb_3" from="node_bridge_mid" to="node_bridge_e" numLanes="2" speed="16.67"/>
    <edge id="flyover_eb_4" from="node_bridge_e" to="node_wf_split" numLanes="2" speed="16.67"/>

    <!-- Westbound Flyover: Whitefield -> HAL -->
    <edge id="flyover_wb_1" from="node_wf_split" to="node_bridge_e" numLanes="2" speed="16.67"/>
    <edge id="flyover_wb_2" from="node_bridge_e" to="node_bridge_mid" numLanes="2" speed="16.67"/>
    <edge id="flyover_wb_3" from="node_bridge_mid" to="node_bridge_w" numLanes="2" speed="16.67"/>
    <edge id="flyover_wb_4" from="node_bridge_w" to="node_hal_split" numLanes="2" speed="16.67"/>

    <!-- GRADE-SEPARATED ORR MAINLINE (Underpass / Through flow under bridge, 60 km/h) -->
    <edge id="orr_mainline_nb" from="node_orr_s_split" to="node_orr_n_split" numLanes="2" speed="16.67"/>
    <edge id="orr_mainline_sb" from="node_orr_n_split" to="node_orr_s_split" numLanes="2" speed="16.67"/>

    <!-- SURFACE RAMPS & CONNECTORS (To/From Surface Junction, 40 km/h) -->
    <!-- From HAL to Surface Junction -->
    <edge id="ramp_hal_in" from="node_hal_split" to="node_junc_w" numLanes="2" speed="11.11"/>
    <!-- From Surface Junction to HAL -->
    <edge id="ramp_hal_out" from="node_junc_w" to="node_hal_split" numLanes="2" speed="11.11"/>

    <!-- From Whitefield to Surface Junction -->
    <edge id="ramp_wf_in" from="node_wf_split" to="node_junc_e" numLanes="2" speed="11.11"/>
    <!-- From Surface Junction to Whitefield -->
    <edge id="ramp_wf_out" from="node_junc_e" to="node_wf_split" numLanes="2" speed="11.11"/>

    <!-- From ORR North to Surface Junction -->
    <edge id="ramp_orr_n_in" from="node_orr_n_split" to="node_junc_n" numLanes="2" speed="11.11"/>
    <!-- From Surface Junction to ORR North -->
    <edge id="ramp_orr_n_out" from="node_junc_n" to="node_orr_n_split" numLanes="2" speed="11.11"/>

    <!-- From ORR South to Surface Junction -->
    <edge id="ramp_orr_s_in" from="node_orr_s_split" to="node_junc_s" numLanes="2" speed="11.11"/>
    <!-- From Surface Junction to ORR South -->
    <edge id="ramp_orr_s_out" from="node_junc_s" to="node_orr_s_split" numLanes="2" speed="11.11"/>

    <!-- SURFACE CROSSROADS LEGS AT SIGNAL-CONTROLLED NODE (marathahalli_tls) -->
    <edge id="leg_hal_in" from="node_junc_w" to="marathahalli_tls" numLanes="2" speed="11.11"/>
    <edge id="leg_hal_out" from="marathahalli_tls" to="node_junc_w" numLanes="2" speed="11.11"/>

    <edge id="leg_wf_in" from="node_junc_e" to="marathahalli_tls" numLanes="2" speed="11.11"/>
    <edge id="leg_wf_out" from="marathahalli_tls" to="node_junc_e" numLanes="2" speed="11.11"/>

    <edge id="leg_orr_s_in" from="node_junc_s" to="marathahalli_tls" numLanes="2" speed="11.11"/>
    <edge id="leg_orr_s_out" from="marathahalli_tls" to="node_junc_s" numLanes="2" speed="11.11"/>

    <edge id="leg_orr_n_in" from="node_junc_n" to="marathahalli_tls" numLanes="2" speed="11.11"/>
    <edge id="leg_orr_n_out" from="marathahalli_tls" to="node_junc_n" numLanes="2" speed="11.11"/>

    <!-- CHANNELIZED FREE-FLOW LEFT TURN SLIP ROADS (40 km/h) -->
    <!-- West (HAL) -> North (KR Puram) -->
    <edge id="slip_hal_to_orr_n" from="node_hal_split" to="node_orr_n_split" numLanes="1" speed="11.11"
          shape="-180.0,0.0 -120.0,30.0 -30.0,120.0 0.0,180.0"/>
    <!-- North (KR Puram) -> East (Whitefield) -->
    <edge id="slip_orr_n_to_wf" from="node_orr_n_split" to="node_wf_split" numLanes="1" speed="11.11"
          shape="0.0,180.0 30.0,120.0 120.0,30.0 180.0,0.0"/>
    <!-- East (Whitefield) -> South (Kadubeesanahalli) -->
    <edge id="slip_wf_to_orr_s" from="node_wf_split" to="node_orr_s_split" numLanes="1" speed="11.11"
          shape="180.0,0.0 120.0,-30.0 30.0,-120.0 0.0,-180.0"/>
    <!-- South (Kadubeesanahalli) -> West (HAL) -->
    <edge id="slip_orr_s_to_hal" from="node_orr_s_split" to="node_hal_split" numLanes="1" speed="11.11"
          shape="0.0,-180.0 -30.0,-120.0 -120.0,-30.0 -180.0,0.0"/>
</edges>
"""
    EDGES_FILE.write_text(xml, encoding="utf-8")


def generate_connections():
    """Generate connection permissions ensuring legal turns and grade separation."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<connections xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/connections_file.xsd">
    <!-- HAL Split Node Connections -->
    <connection from="hal_in" to="flyover_eb_1" fromLane="0" toLane="0"/>
    <connection from="hal_in" to="flyover_eb_1" fromLane="1" toLane="1"/>
    <connection from="hal_in" to="ramp_hal_in" fromLane="0" toLane="0"/>
    <connection from="hal_in" to="ramp_hal_in" fromLane="1" toLane="1"/>
    <connection from="hal_in" to="slip_hal_to_orr_n" fromLane="0" toLane="0"/>

    <connection from="flyover_wb_4" to="hal_out" fromLane="0" toLane="0"/>
    <connection from="flyover_wb_4" to="hal_out" fromLane="1" toLane="1"/>
    <connection from="ramp_hal_out" to="hal_out" fromLane="0" toLane="0"/>
    <connection from="ramp_hal_out" to="hal_out" fromLane="1" toLane="1"/>
    <connection from="slip_orr_s_to_hal" to="hal_out" fromLane="0" toLane="0"/>

    <!-- Whitefield Split Node Connections -->
    <connection from="wf_in" to="flyover_wb_1" fromLane="0" toLane="0"/>
    <connection from="wf_in" to="flyover_wb_1" fromLane="1" toLane="1"/>
    <connection from="wf_in" to="ramp_wf_in" fromLane="0" toLane="0"/>
    <connection from="wf_in" to="ramp_wf_in" fromLane="1" toLane="1"/>
    <connection from="wf_in" to="slip_wf_to_orr_s" fromLane="0" toLane="0"/>

    <connection from="flyover_eb_4" to="wf_out" fromLane="0" toLane="0"/>
    <connection from="flyover_eb_4" to="wf_out" fromLane="1" toLane="1"/>
    <connection from="ramp_wf_out" to="wf_out" fromLane="0" toLane="0"/>
    <connection from="ramp_wf_out" to="wf_out" fromLane="1" toLane="1"/>
    <connection from="slip_orr_n_to_wf" to="wf_out" fromLane="0" toLane="0"/>

    <!-- ORR North Split Node Connections -->
    <connection from="orr_n_in" to="orr_mainline_sb" fromLane="0" toLane="0"/>
    <connection from="orr_n_in" to="orr_mainline_sb" fromLane="1" toLane="1"/>
    <connection from="orr_n_in" to="ramp_orr_n_in" fromLane="0" toLane="0"/>
    <connection from="orr_n_in" to="ramp_orr_n_in" fromLane="1" toLane="1"/>
    <connection from="orr_n_in" to="slip_orr_n_to_wf" fromLane="0" toLane="0"/>

    <connection from="orr_mainline_nb" to="orr_n_out" fromLane="0" toLane="0"/>
    <connection from="orr_mainline_nb" to="orr_n_out" fromLane="1" toLane="1"/>
    <connection from="ramp_orr_n_out" to="orr_n_out" fromLane="0" toLane="0"/>
    <connection from="ramp_orr_n_out" to="orr_n_out" fromLane="1" toLane="1"/>
    <connection from="slip_hal_to_orr_n" to="orr_n_out" fromLane="0" toLane="0"/>

    <!-- ORR South Split Node Connections -->
    <connection from="orr_s_in" to="orr_mainline_nb" fromLane="0" toLane="0"/>
    <connection from="orr_s_in" to="orr_mainline_nb" fromLane="1" toLane="1"/>
    <connection from="orr_s_in" to="ramp_orr_s_in" fromLane="0" toLane="0"/>
    <connection from="orr_s_in" to="ramp_orr_s_in" fromLane="1" toLane="1"/>
    <connection from="orr_s_in" to="slip_orr_s_to_hal" fromLane="0" toLane="0"/>

    <connection from="orr_mainline_sb" to="orr_s_out" fromLane="0" toLane="0"/>
    <connection from="orr_mainline_sb" to="orr_s_out" fromLane="1" toLane="1"/>
    <connection from="ramp_orr_s_out" to="orr_s_out" fromLane="0" toLane="0"/>
    <connection from="ramp_orr_s_out" to="orr_s_out" fromLane="1" toLane="1"/>
    <connection from="slip_wf_to_orr_s" to="orr_s_out" fromLane="0" toLane="0"/>

    <!-- Surface Crossroads Leg Connections (to/from ramps) -->
    <connection from="ramp_hal_in" to="leg_hal_in" fromLane="0" toLane="0"/>
    <connection from="ramp_hal_in" to="leg_hal_in" fromLane="1" toLane="1"/>
    <connection from="leg_hal_out" to="ramp_hal_out" fromLane="0" toLane="0"/>
    <connection from="leg_hal_out" to="ramp_hal_out" fromLane="1" toLane="1"/>

    <connection from="ramp_wf_in" to="leg_wf_in" fromLane="0" toLane="0"/>
    <connection from="ramp_wf_in" to="leg_wf_in" fromLane="1" toLane="1"/>
    <connection from="leg_wf_out" to="ramp_wf_out" fromLane="0" toLane="0"/>
    <connection from="leg_wf_out" to="ramp_wf_out" fromLane="1" toLane="1"/>

    <connection from="ramp_orr_s_in" to="leg_orr_s_in" fromLane="0" toLane="0"/>
    <connection from="ramp_orr_s_in" to="leg_orr_s_in" fromLane="1" toLane="1"/>
    <connection from="leg_orr_s_out" to="ramp_orr_s_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_s_out" to="ramp_orr_s_out" fromLane="1" toLane="1"/>

    <connection from="ramp_orr_n_in" to="leg_orr_n_in" fromLane="0" toLane="0"/>
    <connection from="ramp_orr_n_in" to="leg_orr_n_in" fromLane="1" toLane="1"/>
    <connection from="leg_orr_n_out" to="ramp_orr_n_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_n_out" to="ramp_orr_n_out" fromLane="1" toLane="1"/>

    <!-- SIGNAL-CONTROLLED NODE (marathahalli_tls) INTERNAL TURNS -->
    <!-- Leg HAL In: Straight to WF, Right to ORR South, Left to ORR North -->
    <connection from="leg_hal_in" to="leg_wf_out" fromLane="0" toLane="0"/>
    <connection from="leg_hal_in" to="leg_wf_out" fromLane="1" toLane="1"/>
    <connection from="leg_hal_in" to="leg_orr_s_out" fromLane="0" toLane="0"/>
    <connection from="leg_hal_in" to="leg_orr_n_out" fromLane="1" toLane="1"/>

    <!-- Leg WF In: Straight to HAL, Right to ORR North, Left to ORR South -->
    <connection from="leg_wf_in" to="leg_hal_out" fromLane="0" toLane="0"/>
    <connection from="leg_wf_in" to="leg_hal_out" fromLane="1" toLane="1"/>
    <connection from="leg_wf_in" to="leg_orr_n_out" fromLane="0" toLane="0"/>
    <connection from="leg_wf_in" to="leg_orr_s_out" fromLane="1" toLane="1"/>

    <!-- Leg ORR South In: Straight to ORR North, Right to WF, Left to HAL -->
    <connection from="leg_orr_s_in" to="leg_orr_n_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_s_in" to="leg_orr_n_out" fromLane="1" toLane="1"/>
    <connection from="leg_orr_s_in" to="leg_wf_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_s_in" to="leg_hal_out" fromLane="1" toLane="1"/>

    <!-- Leg ORR North In: Straight to ORR South, Right to HAL, Left to WF -->
    <connection from="leg_orr_n_in" to="leg_orr_s_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_n_in" to="leg_orr_s_out" fromLane="1" toLane="1"/>
    <connection from="leg_orr_n_in" to="leg_hal_out" fromLane="0" toLane="0"/>
    <connection from="leg_orr_n_in" to="leg_wf_out" fromLane="1" toLane="1"/>
</connections>
"""
    CONNS_FILE.write_text(xml, encoding="utf-8")


def generate_traffic_light_logic():
    """Generate BTP-grounded signal program with yellow/all-red clearances.

    Adheres strictly to the safety invariant:
    GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN (other axis).
    Duration baseline: BTP Weekday Morning Peak (105s EW / 95s NS vehicle greens).
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<tlLogics xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/tllogic_file.xsd">
    <tlLogic id="marathahalli_tls" type="static" programID="btp_fixed" offset="0">
        <!-- Phase 0: North-South (ORR: Kadubeesanahalli <-> KR Puram) Green (105s) -->
        <phase duration="105" state="GGGgrrrrGGGgrrrr"/>
        <!-- Phase 1: North-South Yellow Clearance (3s) -->
        <phase duration="3"   state="yyyyrrrryyyyrrrr"/>
        <!-- Phase 2: All-Red Clearance (2s) -->
        <phase duration="2"   state="rrrrrrrrrrrrrrrr"/>
        <!-- Phase 3: East-West (Varthur Rd: HAL <-> Whitefield) Green (95s) -->
        <phase duration="95"  state="rrrrGGGgrrrrGGGg"/>
        <!-- Phase 4: East-West Yellow Clearance (3s) -->
        <phase duration="3"   state="rrrryyyyrrrryyyy"/>
        <!-- Phase 5: All-Red Clearance (2s) -->
        <phase duration="2"   state="rrrrrrrrrrrrrrrr"/>
    </tlLogic>
</tlLogics>
"""
    TLL_FILE.write_text(xml, encoding="utf-8")


def generate_detectors():
    """Generate simulated lane-area (E2) detectors on the 4 surface approaches."""
    # Each surface approach leg has 2 lanes (approx 31m-34m long).
    # We place 25m detectors on each lane approaching the stop line.
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Surface Approach Detectors for Queue Length Measurement -->
    <!-- HAL West approach to surface junction -->
    <laneAreaDetector id="det_hal_0" lane="leg_hal_in_0" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>
    <laneAreaDetector id="det_hal_1" lane="leg_hal_in_1" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>

    <!-- Whitefield East approach to surface junction -->
    <laneAreaDetector id="det_wf_0" lane="leg_wf_in_0" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>
    <laneAreaDetector id="det_wf_1" lane="leg_wf_in_1" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>

    <!-- ORR South approach (Kadubeesanahalli) to surface junction -->
    <laneAreaDetector id="det_orr_s_0" lane="leg_orr_s_in_0" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>
    <laneAreaDetector id="det_orr_s_1" lane="leg_orr_s_in_1" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>

    <!-- ORR North approach (KR Puram) to surface junction -->
    <laneAreaDetector id="det_orr_n_0" lane="leg_orr_n_in_0" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>
    <laneAreaDetector id="det_orr_n_1" lane="leg_orr_n_in_1" pos="-25.0" endPos="-0.1" period="1" file="detector_out.xml"/>
</additional>
"""
    DET_FILE.write_text(xml, encoding="utf-8")


def generate_sumocfg():
    """Generate a clean SUMO configuration file for the Marathahalli network."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="marathahalli.net.xml"/>
        <additional-files value="../build/detectors.add.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="1.0"/>
    </time>
    <processing>
        <time-to-teleport value="-1"/>
        <waiting-time-memory value="1000"/>
    </processing>
    <report>
        <no-step-log value="true"/>
        <no-warnings value="true"/>
    </report>
</configuration>
"""
    SUMOCFG_FILE.write_text(xml, encoding="utf-8")


def build_marathahalli_net(verbose: bool = True) -> Path:
    """Build the complete Marathahalli SUMO network using netconvert."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("[Marathahalli] Writing node, edge, connection, detector definitions...")

    generate_nodes()
    generate_edges()
    generate_connections()
    generate_traffic_light_logic()
    generate_detectors()
    generate_sumocfg()

    cmd = [
        binary("netconvert"),
        "--node-files", str(NODES_FILE),
        "--edge-files", str(EDGES_FILE),
        "--connection-files", str(CONNS_FILE),
        "--tllogic-files", str(TLL_FILE),
        "--output-file", str(NET_FILE),
        "--no-turnarounds", "true",
        "--tls.default-type", "static",
        "--no-warnings", "true",
        "--geometry.avoid-overlap", "true"
    ]

    if verbose:
        print(f"[Marathahalli] Compiling network via netconvert: {' '.join(cmd)}")

    run(cmd)

    if not NET_FILE.exists():
        raise RuntimeError(f"netconvert failed to generate {NET_FILE}")

    if verbose:
        print(f"[Marathahalli] Successfully compiled network: {NET_FILE} ({NET_FILE.stat().st_size} bytes)")

    return NET_FILE


if __name__ == "__main__":
    build_marathahalli_net(verbose=True)
