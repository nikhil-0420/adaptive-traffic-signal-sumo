"""Comprehensive tests for the research-grade evaluation matrix and statistical pipeline."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from dp1 import config as C
from dp1.scenarios import build_routes, load_route_manifest
from dp1.metrics import summarise_run
from dp1.research.matrix import (
    CellStatus,
    MatrixCell,
    build_research_matrix,
    format_matrix_preview,
)
from dp1.research.stats import (
    bootstrap_percentile_ci,
    compute_aggregates,
    compute_fairness_by_approach,
    compute_fairness_by_direction,
    compute_paired_deltas,
)
from dp1.research.orchestrator import _worker_execute_cell


def test_demand_levels_and_scenarios_multipliers():
    """Verify low/medium/heavy multipliers and backwards-compatible defaults."""
    assert C.DEMAND_LEVELS["low"] == 0.70
    assert C.DEMAND_LEVELS["medium"] == 1.00
    assert C.DEMAND_LEVELS["heavy"] == 1.30
    assert C.DEFAULT_DEMAND_LEVEL == "medium"

    scen_def = C.scenarios()
    scen_med = C.scenarios(demand_level="medium")
    scen_low = C.scenarios(demand_level="low")
    scen_hvy = C.scenarios(demand_level="heavy")

    # Medium is byte-identical to legacy default
    for pat in C.scenarios():
        for a in C.APPROACHES:
            assert scen_def[pat][a] == scen_med[pat][a]

    # Flow rates scale proportionally
    vph_med = scen_med["balanced"]["N"][0][2]
    vph_low = scen_low["balanced"]["N"][0][2]
    vph_hvy = scen_hvy["balanced"]["N"][0][2]

    assert pytest.approx(vph_low / vph_med, abs=1e-5) == 0.70
    assert pytest.approx(vph_hvy / vph_med, abs=1e-5) == 1.30

    with pytest.raises(ValueError):
        C.scenarios(demand_level="ultra")


def test_webster_plan_scaled_with_demand_levels():
    """Verify Webster calculates from the selected scaled profile."""
    plan_med = C.webster_plan("imbalanced_ns", demand_level="medium")
    plan_def = C.webster_plan("imbalanced_ns")
    assert plan_med.green_ns_s == plan_def.green_ns_s
    assert plan_med.green_ew_s == plan_def.green_ew_s

    plan_low = C.webster_plan("imbalanced_ns", demand_level="low")
    plan_hvy = C.webster_plan("imbalanced_ns", demand_level="heavy")

    # Heavy demand requires larger or equal cycle / green
    cycle_low = plan_low.green_ns_s + plan_low.green_ew_s + 2 * (C.TIMING.yellow_s + C.TIMING.all_red_s)
    cycle_hvy = plan_hvy.green_ns_s + plan_hvy.green_ew_s + 2 * (C.TIMING.yellow_s + C.TIMING.all_red_s)
    assert cycle_hvy >= cycle_low


def test_route_generation_and_hash_pairing(tmp_path):
    """Verify route generation is deterministic, hash-paired, and writes companion manifest."""
    p1, n1 = build_routes("balanced", seed=21, out_dir=tmp_path / "run1", demand_level="medium")
    p2, n2 = build_routes("balanced", seed=21, out_dir=tmp_path / "run2", demand_level="medium")
    assert n1 == n2

    m1 = load_route_manifest(p1)
    m2 = load_route_manifest(p2)
    assert m1["route_hash"] == m2["route_hash"]
    assert len(m1["vehicle_origins"]) == n1
    assert m1["demand_level"] == "medium"

    # Changing demand level changes route content and vehicle count
    p_low, n_low = build_routes("balanced", seed=21, out_dir=tmp_path / "run_low", demand_level="low")
    m_low = load_route_manifest(p_low)
    assert n_low < n1
    assert m_low["route_hash"] != m1["route_hash"]


def test_research_matrix_dimensions_and_presets():
    """Verify full matrix contains exactly 720 cells and dry-run preview works."""
    full_matrix = build_research_matrix("exp_full_test", preset="full")
    assert full_matrix.total_cells == 720
    assert len(full_matrix.patterns) == 4
    assert len(full_matrix.levels) == 3
    assert len(full_matrix.policies) == 6
    assert len(full_matrix.seeds) == 10

    smoke_matrix = build_research_matrix("exp_smoke_test", preset="smoke")
    assert smoke_matrix.total_cells == 3

    preview = format_matrix_preview(full_matrix)
    assert "Total Matrix Cells: 720" in preview
    assert "cell_balanced_low_fixed_s21" in preview


def test_bootstrap_percentile_ci_deterministic():
    """Verify deterministic paired-bootstrap percentile confidence intervals."""
    data = np.array([-10.0, -12.0, -8.0, -15.0, -9.0, -11.0, -14.0, -10.0])
    mean1, lo1, hi1 = bootstrap_percentile_ci(data, n_resamples=1000, random_seed=42)
    mean2, lo2, hi2 = bootstrap_percentile_ci(data, n_resamples=1000, random_seed=42)

    assert mean1 == mean2
    assert lo1 == lo2
    assert hi1 == hi2
    assert lo1 <= mean1 <= hi1

    # Empty data
    empty_mean, empty_lo, empty_hi = bootstrap_percentile_ci(np.array([]))
    assert np.isnan(empty_mean)


def test_stats_paired_deltas_and_fairness():
    """Verify paired candidate - fixed deltas and directional fairness summaries."""
    rows = [
        # Seed 21: fixed vs adaptive
        {"pattern": "imbalanced_ns", "demand_level": "medium", "policy": "fixed", "seed": 21,
         "avg_wait_s": 100.0, "avg_time_loss_s": 120.0, "avg_queue_m": 50.0, "throughput_veh_per_h": 2000.0,
         "avg_wait_NS_s": 120.0, "avg_wait_EW_s": 40.0, "directional_wait_disparity_s": 80.0, "approach_wait_gap_s": 90.0,
         "n_completed_N": 500, "avg_wait_N_s": 125.0, "p95_wait_N_s": 200.0, "avg_queue_N_m": 40.0, "max_queue_N_m": 120.0,
         "n_completed_S": 500, "avg_wait_S_s": 115.0, "p95_wait_S_s": 190.0, "avg_queue_S_m": 40.0, "max_queue_S_m": 110.0,
         "n_completed_E": 150, "avg_wait_E_s": 42.0, "p95_wait_E_s": 80.0, "avg_queue_E_m": 10.0, "max_queue_E_m": 30.0,
         "n_completed_W": 150, "avg_wait_W_s": 38.0, "p95_wait_W_s": 75.0, "avg_queue_W_m": 10.0, "max_queue_W_m": 30.0},
        {"pattern": "imbalanced_ns", "demand_level": "medium", "policy": "adaptive", "seed": 21,
         "avg_wait_s": 40.0, "avg_time_loss_s": 50.0, "avg_queue_m": 35.0, "throughput_veh_per_h": 2400.0,
         "avg_wait_NS_s": 42.0, "avg_wait_EW_s": 35.0, "directional_wait_disparity_s": 7.0, "approach_wait_gap_s": 10.0,
         "n_completed_N": 500, "avg_wait_N_s": 43.0, "p95_wait_N_s": 90.0, "avg_queue_N_m": 25.0, "max_queue_N_m": 70.0,
         "n_completed_S": 500, "avg_wait_S_s": 41.0, "p95_wait_S_s": 85.0, "avg_queue_S_m": 25.0, "max_queue_S_m": 65.0,
         "n_completed_E": 150, "avg_wait_E_s": 36.0, "p95_wait_E_s": 70.0, "avg_queue_E_m": 10.0, "max_queue_E_m": 25.0,
         "n_completed_W": 150, "avg_wait_W_s": 34.0, "p95_wait_W_s": 65.0, "avg_queue_W_m": 10.0, "max_queue_W_m": 25.0},
    ]
    df = pd.DataFrame(rows)
    deltas = compute_paired_deltas(df, reference_policy="fixed")
    assert not deltas.empty
    row_delta = deltas.iloc[0]
    # Candidate (40) - Fixed (100) = -60
    assert row_delta["delta_wait_mean_s"] == -60.0
    assert row_delta["delta_time_loss_mean_s"] == -70.0
    assert row_delta["delta_queue_mean_m"] == -15.0

    fairness_dir = compute_fairness_by_direction(df)
    assert not fairness_dir.empty
    assert "directional_wait_disparity_s_mean" in fairness_dir.columns

    fairness_app = compute_fairness_by_approach(df)
    assert len(fairness_app) == 8  # 2 policies x 4 approaches


def test_blocked_cell_when_model_missing(tmp_path):
    """Verify cells requesting rl_dqn are cleanly marked BLOCKED if model is absent."""
    cell = MatrixCell(
        cell_id="cell_test_blocked",
        pattern="imbalanced_ns",
        demand_level="medium",
        policy="rl_dqn",
        seed=21,
    )
    nonexistent_model = str(tmp_path / "nonexistent_model.zip")
    updated_cell, row, err = _worker_execute_cell((cell.to_dict(), str(tmp_path), nonexistent_model))

    assert updated_cell.status == CellStatus.BLOCKED.value
    assert "Model checkpoint not found" in updated_cell.error_message
    assert row is None
