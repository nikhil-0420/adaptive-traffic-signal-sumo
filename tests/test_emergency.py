"""Comprehensive unit, regression, and integration tests for Emergency Priority (Phase P4).

Verifies:
1. Deterministic route pairing: identical background vehicles between emergency off and on.
2. Disabled-feature regression: non-emergency runs unchanged and backward compatible.
3. Accurate geometry detection: ambulance detected strictly on incoming approaches within detection distance.
4. Preemption safety: minimum green (10s) strictly respected before switching competing axis.
5. Extension cap: maximum green extension (30s) prevents indefinite hold on emergency axis.
6. Clearance safety: transitions strictly pass through YELLOW (3s) and ALL_RED (2s); no simultaneous greens.
7. Metric extraction: completed, incomplete, and disabled cases parsed from actual/mock tripinfo.
8. End-to-end SUMO pairing: priority-off vs priority-on runs execute cleanly.
"""
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from dp1 import config as C
from dp1.controllers.base import ControllerAction, PhaseMachineController
from dp1.emergency import EmergencyPriorityCoordinator, detect_approaching_emergency
from dp1.metrics import summarise_run
from dp1.runner import run_simulation
from dp1.scenarios import build_routes, load_route_manifest


class DummyStates:
    def green(self, axis):
        return "GGGG" if axis == "NS" else "gggg"

    def yellow(self, axis):
        return "yyyy"

    def all_red(self):
        return "rrrr"


class MockPhaseController(PhaseMachineController):
    name = "mock_phase"

    def __init__(self, states=None, min_green_s=10.0, max_green_s=60.0, **kw):
        super().__init__(states or DummyStates(), min_green_s=min_green_s, max_green_s=max_green_s, **kw)

    def decide_green(self, axis, queues, t):
        return float(self.max_green_s)


@pytest.fixture
def empty_queues():
    return {a: 0.0 for a in C.APPROACHES}



def test_deterministic_route_pairing():
    """Background vehicles must be 100% identical between emergency-event off and on."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        route_off, n_off = build_routes("imbalanced_ns", seed=42, out_dir=tmp_path, emergency_event=False)
        route_on, n_on = build_routes("imbalanced_ns", seed=42, out_dir=tmp_path, emergency_event=True)

        manifest_off = load_route_manifest(route_off)
        manifest_on = load_route_manifest(route_on)

        # Emergency run has exactly 1 more vehicle (the ambulance)
        assert n_on == n_off + 1
        assert manifest_off["emergency_event"] is False
        assert manifest_on["emergency_event"] is True
        assert manifest_on["emergency_vehicle_id"] == "ambulance"

        # Background vehicles must match exactly in ID, depart time, and route
        bg_off = {v["id"]: (v["depart"], v["origin"], v["destination"]) for v in manifest_off["vehicles"]}
        bg_on = {v["id"]: (v["depart"], v["origin"], v["destination"]) for v in manifest_on["vehicles"] if not v["emergency"]}
        assert bg_off == bg_on

        # Re-generating with emergency_event=True produces byte-identical XML
        route_on_2, _ = build_routes("imbalanced_ns", seed=42, out_dir=tmp_path / "sub", emergency_event=True)
        assert route_on.read_text(encoding="utf-8") == route_on_2.read_text(encoding="utf-8")


def test_detection_geometry_filtering():
    """Ambulance detected only on incoming edges within detection distance."""
    em_cfg = C.EmergencyConfig(vehicle_id="ambulance", detection_dist_m=100.0)

    # 1. Vehicle not active in simulation
    with patch("traci.vehicle.getIDList", return_value=["v0", "v1"]):
        assert detect_approaching_emergency(em_cfg=em_cfg) is None

    # 2. Vehicle on outgoing edge (already crossed intersection)
    with patch("traci.vehicle.getIDList", return_value=["ambulance"]), \
         patch("traci.vehicle.getRoadID", return_value="S_out"):
        assert detect_approaching_emergency(em_cfg=em_cfg) is None

    # 3. Vehicle on internal junction lane (currently crossing)
    with patch("traci.vehicle.getIDList", return_value=["ambulance"]), \
         patch("traci.vehicle.getRoadID", return_value=":J0_1"):
        assert detect_approaching_emergency(em_cfg=em_cfg) is None

    # 4. Vehicle on incoming edge, but too far (> 100m)
    with patch("traci.vehicle.getIDList", return_value=["ambulance"]), \
         patch("traci.vehicle.getRoadID", return_value="N_in"), \
         patch("traci.vehicle.getLaneID", return_value="N_in_0"), \
         patch("traci.vehicle.getLanePosition", return_value=150.0), \
         patch("traci.lane.getLength", return_value=300.0):
        # dist = 300 - 150 = 150m > 100m
        assert detect_approaching_emergency(em_cfg=em_cfg) is None

    # 5. Vehicle on incoming edge, approaching within detection distance (<= 100m)
    with patch("traci.vehicle.getIDList", return_value=["ambulance"]), \
         patch("traci.vehicle.getRoadID", return_value="N_in"), \
         patch("traci.vehicle.getLaneID", return_value="N_in_0"), \
         patch("traci.vehicle.getLanePosition", return_value=240.0), \
         patch("traci.lane.getLength", return_value=300.0):
        # dist = 300 - 240 = 60m <= 100m
        res = detect_approaching_emergency(em_cfg=em_cfg)
        assert res is not None
        app, axis, dist = res
        assert app == "N"
        assert axis == "NS"
        assert dist == 60.0


def test_preemption_respects_minimum_green(empty_queues):
    """Emergency preemption on competing axis cannot switch before min_green_s."""
    em_cfg = C.EmergencyConfig(approach="N", min_green_s=10.0, detection_dist_m=100.0)
    ctl = MockPhaseController(
        DummyStates(),
        min_green_s=10.0,
        max_green_s=60.0,
        emergency_priority=True,
        emergency_cfg=em_cfg,
    )
    ctl.start(0.0, empty_queues)
    # Start on EW green
    ctl._enter_green("EW", 0.0, empty_queues)
    ctl.target_green = 50.0

    # Mock ambulance approaching on N (NS axis)
    with patch("dp1.emergency.detect_approaching_emergency", return_value=("N", "NS", 50.0)):
        # At elapsed = 5s < min_green (10s), preemption cannot switch
        for t in range(1, 10):
            ctl.step(float(t), empty_queues)
            assert ctl.phase == "GREEN", f"Premature preemption at t={t}"
            assert ctl.axis == "EW"

        # At elapsed = 10s >= min_green (10s), preemption triggers switch to YELLOW
        ctl.step(10.0, empty_queues)
        assert ctl.phase == "YELLOW"
        assert ctl.decisions[-1]["actual_green_s"] == 10.0

        # Enforces full clearance: 3s yellow then 2s all-red before NS gets green
        ctl.step(11.0, empty_queues)
        assert ctl.phase == "YELLOW"
        ctl.step(12.0, empty_queues)
        assert ctl.phase == "YELLOW"
        ctl.step(13.0, empty_queues)
        assert ctl.phase == "ALL_RED"
        ctl.step(14.0, empty_queues)
        assert ctl.phase == "ALL_RED"
        ctl.step(15.0, empty_queues)
        assert ctl.phase == "GREEN"
        assert ctl.axis == "NS"


def test_emergency_extension_bounded_by_max_extension(empty_queues):
    """Emergency green extension cannot exceed max_extension_s and starve competing axis."""
    em_cfg = C.EmergencyConfig(approach="N", max_extension_s=30.0, detection_dist_m=100.0)
    ctl = MockPhaseController(
        DummyStates(),
        min_green_s=10.0,
        max_green_s=40.0,
        emergency_priority=True,
        emergency_cfg=em_cfg,
    )
    ctl.start(0.0, empty_queues)
    ctl._enter_green("NS", 0.0, empty_queues)
    ctl.target_green = 40.0

    # Mock ambulance approaching on N (NS axis)
    with patch("dp1.emergency.detect_approaching_emergency", return_value=("N", "NS", 30.0)):
        # Normal green runs up to target 40s
        for t in range(1, 40):
            ctl.step(float(t), empty_queues)
            assert ctl.phase == "GREEN"

        # At t=40, policy wants to end green, but ambulance extends it
        ctl.step(40.0, empty_queues)
        assert ctl.phase == "GREEN"

        # Extension continues up to t=69 (ext=29s < max_ext=30s)
        for t in range(41, 70):
            ctl.step(float(t), empty_queues)
            assert ctl.phase == "GREEN", f"Premature extension termination at t={t}"

        # At t=70 (ext=30s >= max_ext=30s), extension cap forces transition to YELLOW
        ctl.step(70.0, empty_queues)
        assert ctl.phase == "YELLOW"


def test_clearance_safety_invariants_under_preemption(empty_queues):
    """Safety invariants hold: GREEN -> YELLOW (3s) -> ALL_RED (2s) -> GREEN(other)."""
    em_cfg = C.EmergencyConfig(approach="N", min_green_s=10.0, max_extension_s=30.0)
    ctl = MockPhaseController(
        DummyStates(),
        min_green_s=10.0,
        max_green_s=60.0,
        emergency_priority=True,
        emergency_cfg=em_cfg,
    )
    ctl.start(0.0, empty_queues)

    # Alternate ambulance detection between N and E
    detections = [("N", "NS", 40.0)] * 30 + [("E", "EW", 40.0)] * 30 + [None] * 40
    history = []

    for t in range(1, 300):
        det = detections[t % len(detections)]
        with patch("dp1.emergency.detect_approaching_emergency", return_value=det):
            ctl.step(float(t), empty_queues)
            history.append((float(t), ctl.phase, ctl.axis))

    # Check state transitions
    for (t0, p0, a0), (t1, p1, a1) in zip(history, history[1:]):
        if (p0, a0) != (p1, a1):
            assert (p0, p1) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, (
                f"Illegal transition at t={t1}: {p0} -> {p1}"
            )
            if p0 == "ALL_RED" and p1 == "GREEN":
                assert a0 != a1, f"Axis did not toggle after clearance at t={t1}"


def test_metrics_emergency_completed_and_incomplete(tmp_path):
    """summarise_run extracts emergency metrics accurately for completed, incomplete, and off runs."""
    # 1. Completed emergency vehicle
    xml_completed = """<tripinfos>
        <tripinfo id="v0" waitingTime="12.0" timeLoss="18.5" duration="45.0" arrival="45.0" depart="0.0"/>
        <tripinfo id="v1" waitingTime="8.0" timeLoss="10.0" duration="30.0" arrival="35.0" depart="5.0"/>
        <tripinfo id="ambulance" waitingTime="2.0" timeLoss="4.5" duration="22.0" arrival="322.0" depart="300.0"/>
    </tripinfos>"""
    f_comp = tmp_path / "tripinfo_comp.xml"
    f_comp.write_text(xml_completed, encoding="utf-8")

    m_comp = summarise_run(
        f_comp, [], 3, 0,
        emergency_event=True, emergency_priority=True,
    )
    assert m_comp["emergency_event"] is True
    assert m_comp["emergency_priority"] is True
    assert m_comp["emergency_completed"] is True
    assert m_comp["emergency_wait_s"] == 2.0
    assert m_comp["emergency_time_loss_s"] == 4.5
    assert m_comp["emergency_trip_s"] == 22.0
    assert m_comp["emergency_arrival_s"] == 322.0
    # Background average excludes ambulance: mean(12.0, 8.0) = 10.0
    assert m_comp["non_emergency_avg_wait_s"] == 10.0

    # 2. Incomplete emergency vehicle (did not finish before simulation ended)
    xml_incomplete = """<tripinfos>
        <tripinfo id="v0" waitingTime="12.0" timeLoss="18.5" duration="45.0" arrival="45.0" depart="0.0"/>
    </tripinfos>"""
    f_incomp = tmp_path / "tripinfo_incomp.xml"
    f_incomp.write_text(xml_incomplete, encoding="utf-8")

    m_incomp = summarise_run(
        f_incomp, [], 3, 2,
        emergency_event=True, emergency_priority=False,
    )
    assert m_incomp["emergency_event"] is True
    assert m_incomp["emergency_priority"] is False
    assert m_incomp["emergency_completed"] is False
    assert m_incomp["emergency_wait_s"] is None
    assert m_incomp["emergency_time_loss_s"] is None
    assert m_incomp["emergency_trip_s"] is None

    # 3. Emergency feature disabled
    m_disabled = summarise_run(
        f_comp, [], 3, 0,
        emergency_event=False, emergency_priority=False,
    )
    assert m_disabled["emergency_event"] is False
    assert m_disabled["emergency_priority"] is False
    assert m_disabled["emergency_completed"] is None
    assert m_disabled["emergency_wait_s"] is None


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_full_sumo_paired_emergency_simulation(tmp_path):
    """Integration test running actual SUMO with emergency-event off vs on."""
    # Priority OFF run
    m_off = run_simulation(
        "imbalanced_ns", "fixed", seed=1,
        out_dir=tmp_path / "em_off",
        emergency_event=True, emergency_priority=False,
    )
    assert m_off["emergency_event"] is True
    assert m_off["emergency_priority"] is False
    assert m_off["emergency_completed"] is True
    assert isinstance(m_off["emergency_trip_s"], float)

    # Priority ON run (same scenario, seed, and route)
    m_on = run_simulation(
        "imbalanced_ns", "fixed", seed=1,
        out_dir=tmp_path / "em_on",
        emergency_event=True, emergency_priority=True,
    )
    assert m_on["emergency_event"] is True
    assert m_on["emergency_priority"] is True
    assert m_on["emergency_completed"] is True
    assert isinstance(m_on["emergency_trip_s"], float)

    # Verify input route hashes are identical between off and on runs
    manifest_off = load_route_manifest(tmp_path / "em_off" / "routes_imbalanced_ns_em_s1.rou.xml")
    manifest_on = load_route_manifest(tmp_path / "em_on" / "routes_imbalanced_ns_em_s1.rou.xml")
    assert manifest_off["route_hash"] == manifest_on["route_hash"]
