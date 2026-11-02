"""Tests for Phase 9 reference baselines:
1. webster_measured
2. webster_recalc
3. fixed_matched_cycle
4. sumo_actuated
5. webster_oracle

Safety invariants:
- No conflicting greens
- Yellow (3s) and all-red (2s) always respected
- Plans applied strictly at legal cycle boundaries
- Seed determinism for measured flow variants
"""
import json
import pandas as pd
import pytest

from dp1 import config as C
from dp1.controllers import POLICIES
from dp1.runner import run_simulation
from dp1.site_network import build_network as build_site_net
from dp1.controllers.webster_utils import compute_webster_plan


@pytest.fixture(scope="session", autouse=True)
def prepare_networks():
    build_site_net("marathahalli")


def test_baseline_policies_registered():
    expected = ["webster_measured", "webster_recalc", "fixed_matched_cycle", "sumo_actuated", "webster_oracle"]
    for p in expected:
        assert p in POLICIES, f"Policy {p} not registered in POLICIES"
        assert p in C.ALL_POLICIES, f"Policy {p} not in C.ALL_POLICIES"
        assert p in C.BASELINE_POLICIES or p == "webster_oracle"


def test_webster_utils_canonical_formula():
    flows = {"N": 500.0, "S": 600.0, "E": 300.0, "W": 400.0}
    plan = compute_webster_plan(flows, lanes=2)
    # Sat flow = 3600 vph
    # y_ns = 600 / 3600 = 1/6
    # y_ew = 400 / 3600 = 1/9
    # Y = 1/6 + 1/9 = 5/18 (~0.2778)
    # L = 10.0
    # c_opt = (1.5 * 10 + 5) / (1 - 5/18) = 20 / (13/18) = 360 / 13 = 27.69 -> clamped to min_cycle_s = 40.0
    # total_green = 40 - 10 = 30.0
    # g_ns = 30.0 * (1/6) / (5/18) = 30.0 * 3/5 = 18.0 s
    # g_ew = 30.0 * (1/9) / (5/18) = 30.0 * 2/5 = 12.0 s
    assert plan.green_ns_s == 18.0
    assert plan.green_ew_s == 12.0
    assert plan.green_ns_s + plan.green_ew_s + 10.0 == 40.0


def test_fixed_matched_cycle_structure():
    ctl = POLICIES["fixed_matched_cycle"](
        states=None,
        scenario="ramp_peak",
        demand_level="medium",
        network="marathahalli"
    )
    # Cycle length should match Webster cycle length
    from dp1.site_scenarios import site_webster_plan
    w_plan = site_webster_plan("ramp_peak", demand_level="medium")
    w_cycle = w_plan.green_ns_s + w_plan.green_ew_s + 10.0
    assert round(ctl.webster_cycle_s, 1) == round(w_cycle, 1)
    # Green split ratio should match BTP 105:95 on Marathahalli (52.5% EW : 47.5% NS)
    g_total = w_cycle - 10.0
    expected_ew = max(10.0, round(0.525 * g_total, 1))
    expected_ns = max(10.0, round(g_total - expected_ew, 1))
    assert ctl.plan.green_ew_s == expected_ew
    assert ctl.plan.green_ns_s == expected_ns
    assert ctl.plan.green_ns_s + ctl.plan.green_ew_s + 10.0 == pytest.approx(w_cycle, abs=0.2)


@pytest.mark.parametrize("policy", ["webster_measured", "webster_recalc", "fixed_matched_cycle", "sumo_actuated"])
def test_baselines_safety_and_clearance(policy, tmp_path):
    out = tmp_path / f"run_{policy}"
    run_simulation(
        scenario="ramp_peak",
        policy=policy,
        seed=101,
        network="marathahalli",
        demand_level="medium",
        max_sim_time_s=650,  # runs past 300s warm-up and 600s recalculation
        out_dir=out,
    )
    ts = pd.read_csv(out / "timeseries.csv")
    dec = pd.read_csv(out / "decisions.csv")

    assert not ts.empty
    assert not dec.empty

    # Safety: phase sequence must always be GREEN -> YELLOW -> ALL_RED -> GREEN
    phase_changes = ts.loc[ts.phase.ne(ts.phase.shift()), "phase"].tolist()
    for prev, nxt in zip(phase_changes, phase_changes[1:]):
        assert (prev, nxt) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, f"Illegal transition {prev} -> {nxt}"

    # Clearance durations: yellow == 3s, all-red == 2s
    run_groups = ts.phase.ne(ts.phase.shift()).cumsum()
    durations = ts.groupby(run_groups).agg(ph=("phase", "first"), n=("t", "size"))
    inner = durations.iloc[1:-1]
    assert (inner[inner.ph == "YELLOW"].n == C.TIMING.yellow_s).all()
    assert (inner[inner.ph == "ALL_RED"].n == C.TIMING.all_red_s).all()


def test_plans_applied_only_at_legal_boundaries(tmp_path):
    out = tmp_path / "run_boundary"
    run_simulation(
        scenario="ramp_peak",
        policy="webster_measured",
        seed=101,
        network="marathahalli",
        demand_level="medium",
        max_sim_time_s=600,
        out_dir=out,
    )
    plan_log_path = out / "plan_log.json"
    assert plan_log_path.exists(), "plan_log.json was not emitted"
    with open(plan_log_path, "r", encoding="utf-8") as f:
        plan_log = json.load(f)

    # Initial warm-up plan and measured plan
    assert len(plan_log) >= 2
    warmup_rec = plan_log[0]
    measured_rec = plan_log[1]
    assert warmup_rec["source"] == "btp_warmup"
    assert measured_rec["source"] == "webster_measured"
    assert measured_rec["t_applied_s"] >= 300.0

    # Verify boundary: t_applied_s must coincide with a transition to NS GREEN
    dec = pd.read_csv(out / "decisions.csv")
    applied_t = measured_rec["t_applied_s"]
    ns_starts = dec[dec.axis == "NS"]["t"].tolist()
    assert applied_t in ns_starts, f"Plan applied at t={applied_t}, not at NS cycle boundary {ns_starts}"


def test_seed_determinism_measured_variants(tmp_path):
    out1 = tmp_path / "run_det1"
    out2 = tmp_path / "run_det2"
    run_simulation("ramp_peak", "webster_measured", seed=101, network="marathahalli", demand_level="medium", max_sim_time_s=400, out_dir=out1)
    run_simulation("ramp_peak", "webster_measured", seed=101, network="marathahalli", demand_level="medium", max_sim_time_s=400, out_dir=out2)

    with open(out1 / "plan_log.json", "r") as f1, open(out2 / "plan_log.json", "r") as f2:
        p1 = json.load(f1)
        p2 = json.load(f2)
    assert p1 == p2, "plan_log not deterministic across identical seeds"

    dec1 = pd.read_csv(out1 / "decisions.csv")
    dec2 = pd.read_csv(out2 / "decisions.csv")
    pd.testing.assert_frame_equal(dec1, dec2)
