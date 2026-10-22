"""Site network manager and loader for DP1.

Supports dual network topologies:
1. 'synthetic': 4-way isolated crossroad (Upgrade 1 default, preserved for regression checks).
2. 'marathahalli': Source-grounded Marathahalli Bridge junction (OpenCity + BTP timings,
   grade-separated flyover + ORR mainline + surface signal-controlled junction).

Safety invariant:
Controllers decide green durations; state machine enforces
GREEN -> YELLOW -> ALL_RED -> GREEN clearance transitions.
"""

from pathlib import Path
from typing import Dict, Any

from . import config as C
from .network import build_network as build_synthetic_net, NET_FILE as SYNTHETIC_NET_FILE, DET_FILE as SYNTHETIC_DET_FILE

MARATHAHALLI_DIR = C.ROOT / "network" / "marathahalli"
MARATHAHALLI_DIST = MARATHAHALLI_DIR / "dist"
MARATHAHALLI_BUILD = MARATHAHALLI_DIR / "build"
MARATHAHALLI_NET_FILE = MARATHAHALLI_DIST / "marathahalli.net.xml"
MARATHAHALLI_DET_FILE = MARATHAHALLI_BUILD / "detectors.add.xml"
MARATHAHALLI_SUMOCFG_FILE = MARATHAHALLI_DIST / "marathahalli.sumocfg"

SUPPORTED_NETWORKS = ("synthetic", "marathahalli")

# Metadata schema for experiment manifests
NETWORK_METADATA: Dict[str, Dict[str, Any]] = {
    "synthetic": {
        "network_name": "synthetic",
        "network_model_version": "1.0.0",
        "source_snapshot_id": "synthetic_4way_cross",
        "signal_plan_id": "btp_timing_structure_synthetic",
        "tls_id": C.TLS_ID,
        "assumption_status": {
            "geometry": "synthetic_idealized",
            "detector_coverage": "simulated_e2_150m",
            "timing_structure": "btp_105_95_adapted"
        }
    },
    "marathahalli": {
        "network_name": "marathahalli",
        "network_model_version": "1.0.0",
        "source_snapshot_id": "opencity_bbmp_20261014",
        "signal_plan_id": "btp_airport_ps_marathahalli_v1",
        "tls_id": "marathahalli_tls",
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
}


def get_network_paths(network_name: str = "synthetic") -> Dict[str, Path]:
    """Return dictionary of paths for the requested network."""
    name = network_name.lower().strip()
    if name == "synthetic":
        return {
            "net_file": SYNTHETIC_NET_FILE,
            "det_file": SYNTHETIC_DET_FILE,
            "sumocfg_file": C.SUMO_DIR / "junction.sumocfg",
            "network_name": "synthetic"
        }
    elif name == "marathahalli":
        return {
            "net_file": MARATHAHALLI_NET_FILE,
            "det_file": MARATHAHALLI_DET_FILE,
            "sumocfg_file": MARATHAHALLI_SUMOCFG_FILE,
            "network_name": "marathahalli"
        }
    else:
        raise ValueError(f"Unknown network '{network_name}'. Supported networks: {SUPPORTED_NETWORKS}")


def get_network_metadata(network_name: str = "synthetic") -> Dict[str, Any]:
    """Return metadata dict for the requested network."""
    name = network_name.lower().strip()
    if name not in NETWORK_METADATA:
        raise ValueError(f"Unknown network '{network_name}'. Supported networks: {SUPPORTED_NETWORKS}")
    return dict(NETWORK_METADATA[name])


def build_network(network_name: str = "synthetic") -> Path:
    """Build the requested network if not already present or force build."""
    name = network_name.lower().strip()
    if name == "synthetic":
        return build_synthetic_net()
    elif name == "marathahalli":
        from network.marathahalli.build_network import build_marathahalli_net
        return build_marathahalli_net(verbose=False)
    else:
        raise ValueError(f"Unknown network '{network_name}'. Supported networks: {SUPPORTED_NETWORKS}")
