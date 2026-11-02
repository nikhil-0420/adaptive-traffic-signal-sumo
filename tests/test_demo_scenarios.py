import pytest
from dp1.demo_scenarios import run_curated_demo

def test_demo_asymmetric_extensions_and_gapouts(tmp_path):
    """Assert curated heavy demo scenario triggers real extension decisions."""
    res = run_curated_demo("demo_asymmetric", policy="hybrid_queue_adaptive", seed=121, out_dir=tmp_path / "asym")
    print(f"\n[DEMO REAL COUNTS - Asymmetric] Extensions: {res['extensions']}, Gap-Outs: {res['gap_outs']}, Holds: {res['holds']}")
    assert res["extensions"] >= 1, f"Expected at least 1 extension, got {res['extensions']}"
    assert res["safety_violations"] == 0

def test_demo_ambulance_preemption_event(tmp_path):
    """Assert curated ambulance demo scenario triggers real preemption event."""
    res = run_curated_demo("demo_ambulance", policy="adaptive", seed=121, out_dir=tmp_path / "amb")
    print(f"\n[DEMO REAL COUNTS - Ambulance] Preemptions: {res['preemptions']}, Extensions: {res['extensions']}")
    assert res["preemptions"] >= 1, f"Expected at least 1 preemption, got {res['preemptions']}"
    assert res["safety_violations"] == 0
