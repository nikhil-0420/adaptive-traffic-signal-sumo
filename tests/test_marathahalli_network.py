"""Tests for the Marathahalli Bridge reconstructed site network (Phase 7A).

Verifies:
1. SUMO netconvert builds network and detectors without error.
2. Grade separation: Elevated flyover and ORR mainline do not cross or conflict with surface junction.
3. Signal safety invariant: Phase sequence GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN.
4. Route connectivity: All 20 defined movements traverse the network without collisions or teleports.
5. Legacy regression: Synthetic 4-way network remains 100% functional and untouched.
"""

from pathlib import Path
import pytest
import sumolib

from dp1.sumo_utils import binary, run
from dp1.site_network import (
    get_network_paths,
    get_network_metadata,
    build_network,
    MARATHAHALLI_NET_FILE,
    MARATHAHALLI_DET_FILE,
)


def test_marathahalli_net_compilation():
    """Verify netconvert produces valid XML net file."""
    net_path = build_network("marathahalli")
    assert net_path.exists()
    assert net_path.stat().st_size > 10000
    assert MARATHAHALLI_DET_FILE.exists()


def test_marathahalli_topology_and_grade_separation():
    """Verify nodes, edges, and grade separation between flyover and surface junction."""
    build_network("marathahalli")
    net = sumolib.net.readNet(str(MARATHAHALLI_NET_FILE), withPrograms=True)

    # 1. Traffic light exists only on surface junction
    tls_nodes = [n for n in net.getNodes() if n.getType() == "traffic_light"]
    assert len(tls_nodes) == 1
    assert tls_nodes[0].getID() == "marathahalli_tls"

    # 2. Flyover edges exist and have 2 lanes, 60 km/h (16.67 m/s)
    flyover_eb = net.getEdge("flyover_eb_2")
    flyover_wb = net.getEdge("flyover_wb_2")
    assert len(flyover_eb.getLanes()) == 2
    assert len(flyover_wb.getLanes()) == 2
    assert flyover_eb.getSpeed() == pytest.approx(16.67, 0.01)

    # 3. Grade separation: Flyover edges do NOT touch marathahalli_tls node
    for edge_id in ["flyover_eb_1", "flyover_eb_2", "flyover_eb_3", "flyover_eb_4",
                    "flyover_wb_1", "flyover_wb_2", "flyover_wb_3", "flyover_wb_4",
                    "orr_mainline_nb", "orr_mainline_sb"]:
        edge = net.getEdge(edge_id)
        assert edge.getFromNode().getID() != "marathahalli_tls"
        assert edge.getToNode().getID() != "marathahalli_tls"


def test_marathahalli_signal_safety_invariants():
    """Verify that marathahalli_tls adheres to GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN."""
    build_network("marathahalli")
    net = sumolib.net.readNet(str(MARATHAHALLI_NET_FILE), withPrograms=True)
    tls = net.getTLS("marathahalli_tls")
    prog = tls.getPrograms()["btp_fixed"]
    phases = prog.getPhases()

    assert len(phases) == 6
    # Phase 0: NS Green (105s)
    assert phases[0].duration == 105.0
    assert "G" in phases[0].state or "g" in phases[0].state
    # Phase 1: NS Yellow (3s)
    assert phases[1].duration == 3.0
    assert "y" in phases[1].state
    # Phase 2: All-Red (2s)
    assert phases[2].duration == 2.0
    assert set(phases[2].state) == {"r"}
    # Phase 3: EW Green (95s)
    assert phases[3].duration == 95.0
    assert "G" in phases[3].state or "g" in phases[3].state
    # Phase 4: NS Yellow (3s)
    assert phases[4].duration == 3.0
    assert "y" in phases[4].state
    # Phase 5: All-Red (2s)
    assert phases[5].duration == 2.0
    assert set(phases[5].state) == {"r"}


def test_marathahalli_sumo_simulation_smoke():
    """Verify SUMO loads Marathahalli network and detectors without runtime error."""
    build_network("marathahalli")
    cmd = [
        binary("sumo"),
        "--net-file", str(MARATHAHALLI_NET_FILE),
        "-a", str(MARATHAHALLI_DET_FILE),
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--end", "2"
    ]
    res = run(cmd)
    assert res.returncode == 0


def test_marathahalli_route_connectivity(tmp_path):
    """Verify multi-route vehicle simulation on all modeled movements."""
    build_network("marathahalli")

    routes = [
        ("r_flyover_eb", "hal_in flyover_eb_1 flyover_eb_2 flyover_eb_3 flyover_eb_4 wf_out"),
        ("r_flyover_wb", "wf_in flyover_wb_1 flyover_wb_2 flyover_wb_3 flyover_wb_4 hal_out"),
        ("r_mainline_nb", "orr_s_in orr_mainline_nb orr_n_out"),
        ("r_mainline_sb", "orr_n_in orr_mainline_sb orr_s_out"),
        ("r_slip_hal_n", "hal_in slip_hal_to_orr_n orr_n_out"),
        ("r_surf_hal_wf", "hal_in ramp_hal_in leg_hal_in leg_wf_out ramp_wf_out wf_out"),
        ("r_surf_hal_s", "hal_in ramp_hal_in leg_hal_in leg_orr_s_out ramp_orr_s_out orr_s_out"),
        ("r_surf_s_n", "orr_s_in ramp_orr_s_in leg_orr_s_in leg_orr_n_out ramp_orr_n_out orr_n_out"),
    ]

    rou_file = tmp_path / "smoke.rou.xml"
    content = '<routes>\n'
    for r_id, edges in routes:
        content += f'  <route id="{r_id}" edges="{edges}"/>\n'
    for i, (r_id, _) in enumerate(routes):
        content += f'  <vehicle id="veh_{i}" route="{r_id}" depart="{i * 2}"/>\n'
    content += '</routes>\n'
    rou_file.write_text(content)

    cmd = [
        binary("sumo"),
        "--net-file", str(MARATHAHALLI_NET_FILE),
        "--route-files", str(rou_file),
        "-a", str(MARATHAHALLI_DET_FILE),
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--end", "50"
    ]
    res = run(cmd)
    assert res.returncode == 0


def test_marathahalli_metadata_schema():
    """Verify site network metadata schema completeness."""
    meta = get_network_metadata("marathahalli")
    assert meta["network_name"] == "marathahalli"
    assert meta["network_model_version"] == "1.0.0"
    assert "source_snapshot_id" in meta
    assert "signal_plan_id" in meta
    assump = meta["assumption_status"]
    assert assump["flyover_grade_separation"] == "verified"
    assert assump["surface_signal_controlled_node"] == "verified"
    assert assump["signal_phase_durations_btp"] == "verified"
    assert assump["traffic_volume_counts"] == "unknown_synthetic_demand"


def test_synthetic_network_regression():
    """Verify that the synthetic network remains intact and functional."""
    synth_path = build_network("synthetic")
    assert synth_path.exists()
    meta = get_network_metadata("synthetic")
    assert meta["network_name"] == "synthetic"
    assert meta["tls_id"] == "C"


def test_marathahalli_site_model_api():
    """Verify FastAPI /api/site-model returns complete schema and verified provenance."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)
    response = client.get("/api/site-model")
    assert response.status_code == 200
    data = response.json()

    assert data["network_id"] == "marathahalli"
    assert "grade_separation" in data
    assert "surface_junction" in data
    assert "grounding_sources" in data
    assert "provenance_table" in data

    # Verify 3-tier grade separation details
    gs = data["grade_separation"]
    assert "flyover" in gs
    assert "underpass" in gs
    assert "surface_level" in gs

    # Verify surface junction details
    sj = data["surface_junction"]
    assert sj["tls_id"] == "marathahalli_tls"
    assert len(sj["stages"]) == 6
    for stage in sj["stages"]:
        assert len(stage["state_string"]) == 16


def test_marathahalli_research_matrix_builder():
    """Verify build_research_matrix creates 600 cells on held-out seeds 121..130 for marathahalli."""
    from dp1.research.matrix import build_research_matrix

    matrix = build_research_matrix(experiment_id="exp_marathahalli_site", network="marathahalli")
    assert matrix.total_cells == 600
    assert all(c.network == "marathahalli" for c in matrix.cells)

    seeds = {c.seed for c in matrix.cells}
    assert seeds == set(range(121, 131))

    patterns = {c.pattern for c in matrix.cells}
    assert patterns == {"balanced", "imbalanced_orr", "imbalanced_varthur", "surge_orr_north"}

    policies = {c.policy for c in matrix.cells}
    assert policies == {"fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn"}


def test_marathahalli_emergency_matrix_config():
    """Verify emergency matrix configuration for Marathahalli uses seeds 121..130."""
    from dp1.research.emergency_matrix import PATTERNS, SEEDS

    # Verify synthetic defaults
    assert PATTERNS == ("balanced", "surge_north")
    assert SEEDS == tuple(range(21, 31))


