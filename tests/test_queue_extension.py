"""Unit and integration tests for Bounded Queue-Extension controller (Upgrade 1)."""
import pandas as pd
import pytest

from dp1 import config as C
from dp1.controllers.queue_extension import QueueExtensionController
from dp1.network import build_network, NET_FILE
from dp1.runner import run_simulation
from dp1.signal_states import SignalStates


@pytest.fixture(scope="session", autouse=True)
def net():
    return build_network()


def test_queue_extension_unit_decide_green():
    """Verify initial green sizing and bounds."""
    states = SignalStates(NET_FILE)
    ctrl = QueueExtensionController(states)

    # Empty queue -> minimum green
    queues_empty = {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}
    g0 = ctrl.decide_green("NS", queues_empty, t=0.0)
    assert g0 == C.QUEUE_EXTENSION.min_green_s

    # Small queue -> between min_green_s and initial_green_s
    queues_small = {"N": 20.0, "S": 10.0, "E": 0.0, "W": 0.0}
    g1 = ctrl.decide_green("NS", queues_small, t=10.0)
    assert C.QUEUE_EXTENSION.min_green_s <= g1 <= C.QUEUE_EXTENSION.initial_green_s


def test_queue_extension_unit_extension_and_bounds():
    """Verify dynamic extension step and max green cutoff."""
    states = SignalStates(NET_FILE)
    ctrl = QueueExtensionController(states)

    queues = {"N": 25.0, "S": 20.0, "E": 0.0, "W": 0.0}
    ctrl.target_green = 15.0
    ctrl.red_start_times["EW"] = 0.0

    # Before reaching target green, does not end
    assert not ctrl.green_should_end("NS", elapsed=14.0, queues=queues, t=14.0)

    # At target green with active queue > threshold and no competing traffic -> extends green
    assert not ctrl.green_should_end("NS", elapsed=15.0, queues=queues, t=15.0)
    assert ctrl.target_green == 15.0 + C.QUEUE_EXTENSION.extend_step_s

    # When reaching max_green_s, forces termination
    assert ctrl.green_should_end("NS", elapsed=C.QUEUE_EXTENSION.max_green_s, queues=queues, t=60.0)


def test_queue_extension_unit_anti_monopoly_fairness():
    """Verify anti-monopoly cutoff when competing approach waits too long or accumulates backlog."""
    states = SignalStates(NET_FILE)
    ctrl = QueueExtensionController(states)

    # Competing axis red wait exceeded
    ctrl.target_green = 20.0
    ctrl.red_start_times["EW"] = 0.0
    queues_competing = {"N": 30.0, "S": 30.0, "E": 10.0, "W": 5.0}

    # At t = 40s (competing red wait 40s > max_competing_wait_s 35s) -> should end green
    assert ctrl.green_should_end("NS", elapsed=15.0, queues=queues_competing, t=40.0)


def test_queue_extension_unit_gap_out():
    """Verify gap-out terminates green when active queue empties while competing traffic waits."""
    states = SignalStates(NET_FILE)
    ctrl = QueueExtensionController(states)

    ctrl.target_green = 30.0
    ctrl.red_start_times["EW"] = 0.0
    queues_gap = {"N": 0.0, "S": 0.0, "E": 15.0, "W": 10.0}

    # First empty detection at elapsed 12.0s
    assert not ctrl.green_should_end("NS", elapsed=12.0, queues=queues_gap, t=12.0)
    assert ctrl._empty_since == 12.0

    # Before gap_out_s elapsed -> False
    assert not ctrl.green_should_end("NS", elapsed=13.0, queues=queues_gap, t=13.0)

    # After gap_out_s elapsed -> True
    assert ctrl.green_should_end("NS", elapsed=16.0, queues=queues_gap, t=16.0)


def test_queue_extension_simulation_integration(tmp_path):
    """Run full SUMO simulation with queue_extension and verify invariants and behavior."""
    out_dir = tmp_path / "sim_qext"
    res = run_simulation("imbalanced_ns", "queue_extension", seed=1, out_dir=out_dir)

    assert res["policy"] == "queue_extension"
    assert res["completion_rate"] > 0.90
    assert res["avg_wait_s"] < 60.0  # Competitive queue delay

    ts = pd.read_csv(out_dir / "timeseries.csv")
    dec = pd.read_csv(out_dir / "decisions.csv")

    # Safety invariant: strictly GREEN -> YELLOW -> ALL_RED -> GREEN
    seq = ts.loc[ts.phase.ne(ts.phase.shift()), "phase"].tolist()
    for prev, nxt in zip(seq, seq[1:]):
        assert (prev, nxt) in {("GREEN", "YELLOW"), ("YELLOW", "ALL_RED"), ("ALL_RED", "GREEN")}, (prev, nxt)

    # Durations of clearance phases
    run_id = ts.phase.ne(ts.phase.shift()).cumsum()
    lens = ts.groupby(run_id).agg(ph=("phase", "first"), n=("t", "size"))
    inner = lens.iloc[1:-1]
    assert (inner[inner.ph == "YELLOW"].n == C.TIMING.yellow_s).all()
    assert (inner[inner.ph == "ALL_RED"].n == C.TIMING.all_red_s).all()

    # Green bounds
    actual_greens = dec.get("actual_green_s", dec["green_s"])
    assert actual_greens.min() >= C.QUEUE_EXTENSION.min_green_s
    assert actual_greens.max() <= C.QUEUE_EXTENSION.max_green_s

    # Imbalanced scenario: heavy NS approach should receive more green than EW
    mean_green = dec.groupby("axis").green_s.mean()
    assert mean_green["NS"] > mean_green["EW"]
