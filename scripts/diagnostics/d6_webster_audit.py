"""Diagnostic D6: Fixed Webster Controller Input and Formulation Audit.

D6: Webster inputs: read fixed_webster.py and site_scenarios.py.
    Where do its flow inputs come from: true scenario rates, a measured warm-up, or hard-coded values?
    Quote the code. Does it have information a live adaptive controller lacks?
    How are cycle length and green splits computed?
"""

from __future__ import annotations

import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import inspect
from dp1.controllers.fixed_webster import FixedWebsterController
from dp1 import site_scenarios
from dp1 import config as C


CODE_QUOTES = """
=== CODE QUOTE 1: dp1/controllers/fixed_webster.py (Lines 10-25) ===
class FixedWebsterController(PhaseMachineController):
    def __init__(self, states, scenario="balanced", plan=None, demand_level=C.DEFAULT_DEMAND_LEVEL, network="synthetic", **kw):
        super().__init__(states, **kw)
        self.scenario = scenario
        self.demand_level = demand_level
        self.network = network
        if plan is not None:
            self.plan = plan
        elif network == "marathahalli" or scenario in ("imbalanced_orr", "imbalanced_varthur", "surge_orr_north"):
            from ..site_scenarios import site_webster_plan
            self.plan = site_webster_plan(scenario, demand_level=demand_level)
        else:
            self.plan = C.webster_plan(scenario, demand_level=demand_level)

    def decide_green(self, axis, queues, t):
        return self.plan.green_ns_s if axis == "NS" else self.plan.green_ew_s

=== CODE QUOTE 2: dp1/site_scenarios.py (Lines 257-306) ===
def site_webster_plan(
    scenario: str,
    timing: Optional[C.SignalTiming] = None,
    cfg: Optional[C.WebsterConfig] = None,
    demand_level: str = C.DEFAULT_DEMAND_LEVEL,
) -> C.FixedTimeConfig:
    scens = get_site_scenarios(demand_level=demand_level)
    if scenario not in scens:
        raise KeyError(f"Unknown site scenario: {scenario}")
    prof = scens[scenario]
    timing = timing or C.TIMING
    cfg = cfg or C.WEBSTER
    duration = float(C.SIM.demand_duration_s)

    avg_flows = {}
    for a in SITE_APPROACHES:
        segments = prof[a]
        total_veh = sum((t1 - t0) * (vph / 3600.0) for t0, t1, vph in segments)
        avg_flows[a] = total_veh * (3600.0 / duration)

    # 2 lanes per surface approach leg
    sat_flow = cfg.sat_flow_per_lane_vph * 2
    # In site demand, through traffic uses 30% surface, right turns use 15% surface
    # Approach traffic arriving at surface signal is approx 35% of total approach flow
    surface_factor = 0.35
    y_ns = (max(avg_flows["N"], avg_flows["S"]) * surface_factor) / sat_flow
    y_ew = (max(avg_flows["W"], avg_flows["E"]) * surface_factor) / sat_flow

    Y = y_ns + y_ew
    L = 2.0 * (timing.yellow_s + timing.all_red_s)
    if Y >= 1.0:
        c_opt = cfg.max_cycle_s
    else:
        c_opt = (1.5 * L + 5.0) / (1.0 - Y)
    cycle = max(cfg.min_cycle_s, min(cfg.max_cycle_s, c_opt))

    total_green = max(0.0, cycle - L)
    if Y > 0:
        g_ns = total_green * (y_ns / Y)
        g_ew = total_green * (y_ew / Y)
    else:
        g_ns = total_green / 2.0
        g_ew = total_green / 2.0

    min_g = 10.0
    g_ns = max(min_g, g_ns)
    g_ew = max(min_g, g_ew)

    return C.FixedTimeConfig(green_ns_s=round(g_ns, 1), green_ew_s=round(g_ew, 1))
"""


def compute_all_webster_plans() -> dict:
    plans = {}
    for sc in ["balanced", "imbalanced_orr", "imbalanced_varthur", "surge_orr_north"]:
        plans[sc] = {}
        for lvl in ["low", "medium", "heavy"]:
            p = site_scenarios.site_webster_plan(sc, demand_level=lvl)
            plans[sc][lvl] = {
                "green_ns_s": p.green_ns_s,
                "green_ew_s": p.green_ew_s,
                "cycle_s": round(p.green_ns_s + p.green_ew_s + 2.0 * (C.TIMING.yellow_s + C.TIMING.all_red_s), 1),
            }
    return plans


def main():
    print(CODE_QUOTES)
    print("\n" + "=" * 80)
    print("WEBSTER COMPUTED PLANS BY PATTERN AND DEMAND LEVEL (Marathahalli Site)")
    print("=" * 80)
    plans = compute_all_webster_plans()
    for sc, lvls in plans.items():
        print(f"\nScenario: {sc}")
        for lvl, d in lvls.items():
            print(f"  {lvl:>6}: NS green = {d['green_ns_s']:>4.1f}s | EW green = {d['green_ew_s']:>4.1f}s | Cycle = {d['cycle_s']:>5.1f}s")

    print("\n" + "=" * 80)
    print("D6 FINDINGS SUMMARY:")
    print("1. Flow inputs origin: TRUE SCENARIO RATES directly read from site_scenarios.SITE_DEMAND_PATTERNS.")
    print("   They are NOT measured from warm-up, and NOT estimated in real time.")
    print("2. Oracle information: YES! Fixed Webster is endowed with exact global knowledge of the entire")
    print("   1800s demand profile, the exact split between flyover and surface (surface_factor=0.35),")
    print("   and the exact demand multiplier (0.70x, 1.00x, 1.30x) at initialization time.")
    print("   The live adaptive controller only has local 24.9m detector readings and has NO prior oracle")
    print("   knowledge of scenario name, arrival rate, or future surge timing.")
    print("=" * 80)


if __name__ == "__main__":
    main()
