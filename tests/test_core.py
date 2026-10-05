"""Quality gate. Run with:  pytest -q   (takes ~30 s). Every change must keep these green."""
import pandas as pd
import pytest

from dp1 import config as C
from dp1.network import build_network, NET_FILE
from dp1.runner import run_simulation
from dp1.signal_states import SignalStates


@pytest.fixture(scope="session", autouse=True)
def net():
    return build_network()


def _run(scenario, policy, tmp_path_factory):
    out = tmp_path_factory.mktemp(f"{scenario}_{policy}")
    m = run_simulation(scenario, policy, seed=1, out_dir=out)
    return m, pd.read_csv(out / "timeseries.csv"), pd.read_csv(out / "decisions.csv")


@pytest.fixture(scope="session")
def adaptive(tmp_path_factory):
    return _run("imbalanced_ns", "adaptive", tmp_path_factory)


@pytest.fixture(scope="session")
def fixed(tmp_path_factory):
    return _run("imbalanced_ns", "fixed", tmp_path_factory)


def test_signal_states_never_green_on_both_axes():
    s = SignalStates(NET_FILE)
    ns, ew = s.green("NS"), s.green("EW")
    assert all(not (a in "Gg" and b in "Gg") for a, b in zip(ns, ew))
    assert set(s.all_red()) == {"r"}


@pytest.mark.parametrize("which", ["adaptive", "fixed"])
def test_every_switch_goes_yellow_then_all_red(which, adaptive, fixed):
    mapping = {"adaptive": adaptive, "fixed": fixed}
    _, ts, _ = mapping[which]
    seq = ts.loc[ts.phase.ne(ts.phase.shift()), "phase"].tolist()
    for prev, nxt in zip(seq, seq[1:]):
        assert (prev, nxt) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, (prev, nxt)


@pytest.mark.parametrize("which", ["adaptive", "fixed"])
def test_yellow_and_all_red_durations(which, adaptive, fixed):
    mapping = {"adaptive": adaptive, "fixed": fixed}
    _, ts, _ = mapping[which]
    run_id = ts.phase.ne(ts.phase.shift()).cumsum()
    lens = ts.groupby(run_id).agg(ph=("phase", "first"), n=("t", "size"))
    inner = lens.iloc[1:-1]  # ignore possibly truncated first/last run
    assert (inner[inner.ph == "YELLOW"].n == C.TIMING.yellow_s).all()
    assert (inner[inner.ph == "ALL_RED"].n == C.TIMING.all_red_s).all()


def test_adaptive_green_within_limits(adaptive):
    _, _, dec = adaptive
    assert dec.green_s.min() >= C.ADAPTIVE.min_green_s
    assert dec.green_s.max() <= C.ADAPTIVE.max_green_s


def test_fixed_green_is_constant(fixed):
    _, _, dec = fixed
    assert set(dec[dec.axis == "NS"].green_s.round(0)) == {105}
    assert set(dec[dec.axis == "EW"].green_s.round(0)) == {95}


def test_heavy_axis_gets_more_green(adaptive):
    """imbalanced_ns: NS carries 3.5x the traffic of EW, so NS must get longer greens."""
    _, _, dec = adaptive
    mean = dec.groupby("axis").green_s.mean()
    assert mean["NS"] > mean["EW"] * 1.3


def test_queue_readings_are_physical(adaptive):
    _, ts, _ = adaptive
    for a in C.APPROACHES:
        assert ts[f"q_{a}"].between(0, C.NET.detector_length_m + 1).all()


def test_all_vehicles_complete(adaptive, fixed):
    for m, _, _ in (adaptive, fixed):
        assert m["completion_rate"] == 1.0


def test_adaptive_beats_fixed_on_imbalanced_demand(adaptive, fixed):
    assert adaptive[0]["avg_wait_s"] < fixed[0]["avg_wait_s"]


def test_balanced_fixed_symmetry(tmp_path_factory):
    means = {f"q_{a}": [] for a in C.APPROACHES}
    for seed in range(1, 5):
        out = tmp_path_factory.mktemp(f"balanced_fixed_s{seed}")
        run_simulation("balanced", "fixed", seed=seed, out_dir=out)
        ts = pd.read_csv(out / "timeseries.csv")
        for a in C.APPROACHES:
            means[f"q_{a}"].append(ts[f"q_{a}"].mean())
    avg = [sum(v) / len(v) for v in means.values()]
    assert max(avg) / min(avg) < 2.0
