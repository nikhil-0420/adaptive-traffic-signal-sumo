"""Unit tests for scripts/export_network3d.py and frontend/public/network3d.json.

Phase 3 validation test suite ensuring:
- 3D network geometry completeness (lanes, junctions, connections, detectors, flyover)
- Provenance integrity (elevation_source = 'modelled_config')
- Safety and mapping consistency against Starting Prompt
- Geometric invariants (continuity, ramp z-monotonicity, crossings, file size < 3MB)
"""

import json
from pathlib import Path
import pytest

from scripts.export_network3d import (
    DEFAULT_NET_FILE,
    DEFAULT_DET_FILE,
    DEFAULT_TLL_FILE,
    DEFAULT_OUTPUT_FILE,
    export_network3d,
    rdp_simplify_3d,
    validate_polyline_continuity,
    validate_ramp_monotonicity,
    count_lane_crossings,
    verify_starting_prompt_mapping,
)


@pytest.fixture(scope="module")
def network_data():
    """Ensure network3d.json is generated and return parsed JSON."""
    if not DEFAULT_OUTPUT_FILE.exists():
        export_network3d(
            net_file=DEFAULT_NET_FILE,
            det_file=DEFAULT_DET_FILE,
            tll_file=DEFAULT_TLL_FILE,
            output_file=DEFAULT_OUTPUT_FILE,
            tolerance=0.0,
            verbose=False,
        )
    with open(DEFAULT_OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists_and_size_under_3mb(network_data):
    """Output file must exist and be well under 3 MB."""
    assert DEFAULT_OUTPUT_FILE.exists()
    size_bytes = DEFAULT_OUTPUT_FILE.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    assert size_mb < 3.0, f"File size {size_mb:.2f} MB exceeds 3.0 MB target"
    assert size_bytes > 50_000, "File size too small; geometry likely missing"


def test_provenance_block(network_data):
    """Provenance block must state source files, SUMO version, commit, and modelled_config elevation."""
    prov = network_data.get("provenance")
    assert prov is not None, "Missing provenance block"
    assert prov["elevation_source"] == "modelled_config", (
        f"elevation_source must be 'modelled_config', got '{prov['elevation_source']}'"
    )
    assert "never survey data" in prov["elevation_disclaimer"]
    assert "marathahalli.net.xml" in prov["source_net_file"]
    assert "detectors.add.xml" in prov["source_detector_file"]
    assert "marathahalli.tll.xml" in prov["source_tllogic_file"]
    assert prov["sumo_version"] != ""
    assert prov["git_commit"] != ""
    assert prov["polyline_simplification"]["tolerance_m"] == 0.0


def test_bounds_and_coordinate_transform(network_data):
    """Bounds and coordinate transform must define 1 unit = 1 metre and valid 4x4 matrix."""
    bounds = network_data.get("bounds")
    assert bounds is not None
    assert bounds["bbox_sumo"]["min"] == [0.0, 0.0, 0.0]
    assert bounds["bbox_sumo"]["max"] == [700.0, 700.0, 7.0]
    assert bounds["center"] == [350.0, 350.0, 3.5]
    assert bounds["controlled_junction"]["id"] == "marathahalli_tls"
    assert bounds["controlled_junction"]["coord"] == [350.0, 332.0, 0.0]

    transform = network_data.get("coordinate_transform")
    assert transform is not None
    assert transform["scale"] == 1.0
    assert transform["unit"] == "metre"
    assert transform["sumo_offset"] == [350.0, 350.0, 0.0]
    assert len(transform["matrix_sumo_to_threejs_y_up"]) == 16
    assert len(transform["matrix_sumo_to_scene_z_up"]) == 16


def test_lanes_structure_and_polyline_3d(network_data):
    """Lanes must contain required attributes and 3D polylines."""
    lanes = network_data.get("lanes")
    assert isinstance(lanes, list)
    assert len(lanes) >= 160, f"Expected >= 160 lanes (normal + internal), got {len(lanes)}"

    for lane in lanes:
        assert "id" in lane
        assert "edge_id" in lane
        assert "polyline" in lane
        assert "width" in lane
        assert lane["width"] > 0
        assert "allowed_vehicle_classes" in lane
        assert isinstance(lane["allowed_vehicle_classes"], list)
        assert len(lane["allowed_vehicle_classes"]) > 0
        assert "speed_limit" in lane
        assert lane["speed_limit"] > 0
        assert "length" in lane
        assert lane["length"] > 0

        # Check 3D points
        pts = lane["polyline"]
        assert len(pts) >= 2, f"Lane {lane['id']} must have >= 2 points"
        for p in pts:
            assert len(p) == 3, f"Point in lane {lane['id']} must have 3 coordinates [x, y, z]"
            assert all(isinstance(c, (int, float)) for c in p)


def test_junctions_structure_and_z_polygon(network_data):
    """Junctions must contain id, type, coord, and 3D shape polygon."""
    junctions = network_data.get("junctions")
    assert isinstance(junctions, list)
    assert len(junctions) == 16, f"Expected 16 junctions, got {len(junctions)}"

    junc_by_id = {j["id"]: j for j in junctions}
    assert "marathahalli_tls" in junc_by_id
    assert "node_bridge_w" in junc_by_id
    assert "node_bridge_mid" in junc_by_id
    assert "node_bridge_e" in junc_by_id

    # Verify bridge node elevations
    assert junc_by_id["node_bridge_w"]["coord"][2] == 6.5
    assert junc_by_id["node_bridge_mid"]["coord"][2] == 7.0
    assert junc_by_id["node_bridge_e"]["coord"][2] == 6.5

    for j in junctions:
        assert "id" in j
        assert "type" in j
        assert "coord" in j and len(j["coord"]) == 3
        assert "shape" in j
        assert len(j["shape"]) >= 3, f"Junction {j['id']} shape must have >= 3 points"
        for p in j["shape"]:
            assert len(p) == 3


def test_connections_at_marathahalli_tls(network_data):
    """Verify all 16 controlled connections at marathahalli_tls against prompt specification."""
    conns = network_data.get("connections")
    assert isinstance(conns, list)
    assert len(conns) == 16, f"Expected exactly 16 controlled connections, got {len(conns)}"

    link_indices = [c["link_index"] for c in conns]
    assert link_indices == list(range(16)), "Link indices must be contiguous 0 to 15"

    for c in conns:
        assert c["link_index"] in range(16)
        assert c["approach"] in ("N", "E", "S", "W")
        assert c["phase_group"] in ("NS", "EW")
        assert "from_edge" in c
        assert "to_edge" in c
        assert "direction" in c
        assert "tls_phases" in c

    # Link 0-3: North (leg_orr_n_in) -> NS
    for idx in range(0, 4):
        assert conns[idx]["approach"] == "N"
        assert conns[idx]["from_edge"] == "leg_orr_n_in"
        assert conns[idx]["phase_group"] == "NS"
        assert conns[idx]["tls_phases"]["3"].upper() == "G"  # NS Green in Phase 3
        assert conns[idx]["tls_phases"]["0"].lower() == "r"  # Red in Phase 0

    # Link 4-7: East (leg_wf_in) -> EW
    for idx in range(4, 8):
        assert conns[idx]["approach"] == "E"
        assert conns[idx]["from_edge"] == "leg_wf_in"
        assert conns[idx]["phase_group"] == "EW"
        assert conns[idx]["tls_phases"]["0"].upper() == "G"  # EW Green in Phase 0
        assert conns[idx]["tls_phases"]["3"].lower() == "r"  # Red in Phase 3

    # Link 8-11: South (leg_orr_s_in) -> NS
    for idx in range(8, 12):
        assert conns[idx]["approach"] == "S"
        assert conns[idx]["from_edge"] == "leg_orr_s_in"
        assert conns[idx]["phase_group"] == "NS"
        assert conns[idx]["tls_phases"]["3"].upper() == "G"  # NS Green in Phase 3
        assert conns[idx]["tls_phases"]["0"].lower() == "r"  # Red in Phase 0

    # Link 12-15: West (leg_hal_in) -> EW
    for idx in range(12, 16):
        assert conns[idx]["approach"] == "W"
        assert conns[idx]["from_edge"] == "leg_hal_in"
        assert conns[idx]["phase_group"] == "EW"
        assert conns[idx]["tls_phases"]["0"].upper() == "G"  # EW Green in Phase 0
        assert conns[idx]["tls_phases"]["3"].lower() == "r"  # Red in Phase 3


def test_detectors_e2_structure(network_data):
    """Verify the 8 E2 lane-area detectors, approaches, positions, and 3D spans."""
    dets = network_data.get("detectors")
    assert isinstance(dets, list)
    assert len(dets) == 8, f"Expected 8 E2 detectors, got {len(dets)}"

    det_by_id = {d["id"]: d for d in dets}
    expected_dets = ["det_hal_0", "det_hal_1", "det_wf_0", "det_wf_1", "det_orr_s_0", "det_orr_s_1", "det_orr_n_0", "det_orr_n_1"]
    for ed in expected_dets:
        assert ed in det_by_id

    # Check each detector pos and length
    for d in dets:
        assert d["pos"] == -25.0
        assert d["endPos"] == -0.1
        assert d["length_m"] == 24.9
        assert d["approach"] in ("N", "E", "S", "W")
        assert len(d["polyline"]) == 2
        for p in d["polyline"]:
            assert len(p) == 3


def test_flyover_bypass_classification(network_data):
    """Verify classification of elevated deck edges, ramps with gradients, mainline, and slip roads."""
    fb = network_data.get("flyover_bypass")
    assert fb is not None

    elevated = fb.get("elevated_edges", [])
    assert len(elevated) == 4, f"Expected 4 flyover deck edges, got {len(elevated)}"
    for e in elevated:
        assert 6.0 <= e["deck_height_m"] <= 7.0
        assert e["category"] == "flyover_deck"

    ramps = fb.get("ramp_edges", [])
    assert len(ramps) == 12, f"Expected 12 ramp edges, got {len(ramps)}"
    flyover_ramps = [r for r in ramps if r["category"] == "flyover_ramp"]
    assert len(flyover_ramps) == 4
    for r in flyover_ramps:
        assert abs(r["gradient_pct"]) > 5.0  # ~7.8% to 9.0%

    mainline = fb.get("mainline_edges", [])
    assert len(mainline) == 2
    for m in mainline:
        assert m["id"] in ("orr_mainline_nb", "orr_mainline_sb")

    slip_roads = fb.get("slip_roads", [])
    assert len(slip_roads) == 4


def test_validation_block_invariants(network_data):
    """Validation block must report 0 gaps, monotone ramps, and zero Starting Prompt mismatches."""
    val = network_data.get("validation")
    assert val is not None

    # Continuity
    cont = val["polyline_continuity"]
    assert cont["status"] == "PASS"
    assert cont["max_gap_m"] < 0.005
    assert cont["gaps_above_5mm"] == 0

    # Monotonicity
    ramp = val["ramp_z_monotonicity"]
    assert ramp["status"] == "PASS"
    assert ramp["all_monotone"] is True

    # Crossings
    cross = val["lane_crossings"]
    assert cross["normal_edges_same_z_count"] == 0
    assert cross["normal_edges_diff_z_count"] == 41

    # Starting prompt mapping
    mapping = val["starting_prompt_mapping"]
    assert mapping["status"] == "PASS"
    assert mapping["mismatch_count"] == 0
    assert len(mapping["mismatches"]) == 0

    # File size
    fs = val["file_size"]
    assert fs["status"] == "PASS"
    assert fs["megabytes"] < 3.0


def test_rdp_simplify_3d():
    """Verify Ramer-Douglas-Peucker 3D algorithm preserves endpoints and reduces collinear points."""
    # Collinear points in 3D
    pts = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (2.0, 2.0, 2.0), (3.0, 3.0, 3.0)]
    simplified = rdp_simplify_3d(pts, tolerance=0.1)
    assert len(simplified) == 2
    assert simplified[0] == (0.0, 0.0, 0.0)
    assert simplified[-1] == (3.0, 3.0, 3.0)

    # Lossless with tolerance=0
    assert rdp_simplify_3d(pts, tolerance=0.0) == pts
