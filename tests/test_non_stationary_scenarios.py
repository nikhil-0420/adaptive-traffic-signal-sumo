"""Tests for Phase 8: Non-Stationary Demand Scenarios (Frozen Configuration).

Verifies:
1. Determinism: Regenerating routes with the same seed produces byte-identical files and identical SHA-256 hashes.
2. Manifest Integrity: Cryptographic SHA-256 manifest recorded with vehicle origins and routes.
3. Webster Computation: Valid cycle and green splits computed across all non-stationary patterns.
4. Lane Closure Dynamics: Lane ramp_orr_n_in_0 closure window is valid and verified in SUMO.
5. Smoke Test: fixed_webster and hybrid_queue_adaptive on seed 101 across all 3 scenarios:
   - Identical route hashes for both policies.
   - 100% completion rate (0 unfinished vehicles).
   - Strict signal safety invariants (GREEN -> YELLOW -> ALL_RED -> GREEN).
   - No NaN in metrics.
"""

import hashlib
import json
from pathlib import Path
import pytest
import sumolib

from dp1 import config as C
from dp1.site_scenarios import build_site_routes, site_webster_plan, get_site_scenarios
from dp1.runner import run_simulation
from dp1.site_network import MARATHAHALLI_NET_FILE


NON_STATIONARY_SCENARIOS = ("ramp_peak", "surge_shift", "lane_closure")
TEST_LEVELS = ("medium", "heavy")


def test_non_stationary_scenarios_registered_in_config():
    """Verify all 3 non-stationary scenarios are defined in central config and get_site_scenarios."""
    for sc in NON_STATIONARY_SCENARIOS:
        assert sc in C.SITE_DEMAND_PATTERNS
        assert sc in C.SITE_PATTERNS_NON_STATIONARY

    # Verify existing stationary patterns remain untouched
    for st in ("balanced", "imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
        assert st in C.SITE_DEMAND_PATTERNS_STATIONARY
        assert st in C.SITE_DEMAND_PATTERNS

    scens_med = get_site_scenarios("medium")
    for sc in NON_STATIONARY_SCENARIOS:
        assert sc in scens_med
        for app in ("W", "E", "N", "S"):
            assert app in scens_med[sc]
            assert len(scens_med[sc][app]) > 0


@pytest.mark.parametrize("scenario", NON_STATIONARY_SCENARIOS)
@pytest.mark.parametrize("level", TEST_LEVELS)
def test_route_generation_determinism_and_byte_identity(scenario, level, tmp_path):
    """Regenerating routes with identical (scenario, level, seed) produces byte-identical XML and manifests."""
    seed = 101
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    route_path1, n1 = build_site_routes(scenario=scenario, seed=seed, out_dir=dir1, demand_level=level)
    route_path2, n2 = build_site_routes(scenario=scenario, seed=seed, out_dir=dir2, demand_level=level)

    assert n1 == n2
    assert n1 > 0

    content1 = route_path1.read_bytes()
    content2 = route_path2.read_bytes()
    assert content1 == content2, f"Route files for {scenario}_{level}_s{seed} are not byte-identical!"

    hash1 = hashlib.sha256(content1).hexdigest()
    hash2 = hashlib.sha256(content2).hexdigest()
    assert hash1 == hash2

    # Manifest checks
    man1_path = route_path1.with_name(f"{route_path1.name}.manifest.json")
    man2_path = route_path2.with_name(f"{route_path2.name}.manifest.json")
    assert man1_path.exists() and man2_path.exists()

    man1 = json.loads(man1_path.read_text(encoding="utf-8"))
    man2 = json.loads(man2_path.read_text(encoding="utf-8"))
    assert man1["route_hash"] == hash1
    assert man2["route_hash"] == hash2
    assert man1["total_vehicles"] == n1
    assert man1["vehicles"] == man2["vehicles"]

    # Different seed must produce different hash
    dir3 = tmp_path / "run3"
    route_path3, _ = build_site_routes(scenario=scenario, seed=102, out_dir=dir3, demand_level=level)
    content3 = route_path3.read_bytes()
    assert content3 != content1


@pytest.mark.parametrize("scenario", NON_STATIONARY_SCENARIOS)
@pytest.mark.parametrize("level", TEST_LEVELS)
def test_webster_plan_computes_valid_timings(scenario, level):
    """Webster plan successfully computes positive, bounded green times for each new scenario."""
    plan = site_webster_plan(scenario, demand_level=level)
    assert plan.green_ns_s >= 10.0
    assert plan.green_ew_s >= 10.0
    total_cycle = plan.green_ns_s + plan.green_ew_s + 2.0 * (C.TIMING.yellow_s + C.TIMING.all_red_s)
    assert C.WEBSTER.min_cycle_s <= total_cycle <= C.WEBSTER.max_cycle_s + 1.0


def test_lane_closure_configuration_invariants():
    """Verify lane closure target exists in Marathahalli network and has valid temporal window."""
    cfg = C.LANE_CLOSURE
    assert cfg.lane_id == "ramp_orr_n_in_0"
    assert 0.0 <= cfg.start_s < cfg.end_s <= cfg.horizon_s
    assert (cfg.end_s - cfg.start_s) == 600.0  # 10 minute closure window

    # Check lane exists in network
    net = sumolib.net.readNet(str(MARATHAHALLI_NET_FILE))
    lane = net.getLane(cfg.lane_id)
    assert lane is not None
    assert lane.getEdge().getID() == "ramp_orr_n_in"


@pytest.mark.parametrize("scenario", NON_STATIONARY_SCENARIOS)
def test_smoke_simulation_fixed_and_hybrid_seed_101(scenario, tmp_path):
    """Smoke test: fixed_webster and hybrid on seed 101 (medium level):
    - Identical route hashes
    - Full completion (0 unfinished)
    - Valid phase transitions (GREEN -> YELLOW -> ALL_RED -> GREEN)
    - No NaN in metrics
    """
    out_webster = tmp_path / f"webster_{scenario}"
    out_hybrid = tmp_path / f"hybrid_{scenario}"

    m_webster = run_simulation(
        scenario=scenario,
        policy="fixed_webster",
        seed=101,
        demand_level="medium",
        out_dir=out_webster,
        network="marathahalli",
    )

    m_hybrid = run_simulation(
        scenario=scenario,
        policy="hybrid_queue_adaptive",
        seed=101,
        demand_level="medium",
        out_dir=out_hybrid,
        network="marathahalli",
    )

    # 1. Identical route hashes
    assert m_webster["route_hash"] == m_hybrid["route_hash"]
    assert len(m_webster["route_hash"]) == 64

    # 2. Vehicle completion
    assert m_webster["vehicles_total"] == m_hybrid["vehicles_total"]
    assert m_webster["vehicles_total"] > 0
    assert m_webster["completion_rate"] == 1.0
    assert m_hybrid["completion_rate"] == 1.0
    assert m_webster["vehicles_unfinished"] == 0
    assert m_hybrid["vehicles_unfinished"] == 0

    # 3. No NaN
    for m in (m_webster, m_hybrid):
        assert not any(
            v is None or (isinstance(v, float) and v != v)  # NaN check
            for k, v in m.items()
            if k in ("avg_wait_s", "p95_wait_s", "avg_queue_m", "max_queue_m", "completion_rate")
        )

    # 4. Strict safety sequence in timeseries
    import pandas as pd
    for out_d in (out_webster, out_hybrid):
        ts = pd.read_csv(out_d / "timeseries.csv")
        seq = ts.loc[ts.phase.ne(ts.phase.shift()), "phase"].tolist()
        for prev, nxt in zip(seq, seq[1:]):
            assert (prev, nxt) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, (prev, nxt)
