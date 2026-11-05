"""Canonical Webster formula implementation and plan formatting utilities.

Safety and integrity invariant:
Uses the exact same Webster formula as existing fixed_webster / site_webster_plan:
- Saturation flow: sat_flow_per_lane_vph * lanes (default 1800 vph/lane * 2 = 3600 vph)
- Lost time L: 2 * (yellow_s + all_red_s) = 10.0 s
- Optimal cycle: c_opt = (1.5 * L + 5.0) / (1.0 - Y) if Y < 1.0 else max_cycle_s
- Cycle bounds: [min_cycle_s, max_cycle_s] = [40.0, 120.0]
- Minimum green bound: min_green_s = 10.0 s per axis
"""
from typing import Dict, Any, Optional
from .. import config as C


def compute_webster_plan(
    flows_vph: Dict[str, float],
    timing: Optional[C.SignalTiming] = None,
    cfg: Optional[C.WebsterConfig] = None,
    lanes: int = 2,
    min_green_s: float = 10.0,
) -> C.FixedTimeConfig:
    """Compute Webster's optimal cycle and splits from approach arrival flows (vph)."""
    timing = timing or C.TIMING
    cfg = cfg or C.WEBSTER
    sat_flow = cfg.sat_flow_per_lane_vph * lanes

    q_n = float(flows_vph.get("N", 0.0))
    q_s = float(flows_vph.get("S", 0.0))
    q_e = float(flows_vph.get("E", 0.0))
    q_w = float(flows_vph.get("W", 0.0))

    y_ns = max(q_n, q_s) / sat_flow
    y_ew = max(q_w, q_e) / sat_flow
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

    g_ns = max(min_green_s, g_ns)
    g_ew = max(min_green_s, g_ew)

    return C.FixedTimeConfig(green_ns_s=round(g_ns, 1), green_ew_s=round(g_ew, 1))


def format_plan_record(
    t_applied_s: float,
    plan: C.FixedTimeConfig,
    timing: C.SignalTiming,
    source: str,
    cycle_index: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format structured plan metadata for execution logs (plan_log.json)."""
    rec = {
        "t_applied_s": round(float(t_applied_s), 1),
        "cycle_index": int(cycle_index),
        "cycle_s": round(float(plan.green_ns_s + plan.green_ew_s + 2.0 * (timing.yellow_s + timing.all_red_s)), 1),
        "green_ns_s": round(float(plan.green_ns_s), 1),
        "green_ew_s": round(float(plan.green_ew_s), 1),
        "yellow_s": round(float(timing.yellow_s), 1),
        "all_red_s": round(float(timing.all_red_s), 1),
        "split_ns_pct": round(float(plan.green_ns_s / max(1e-3, (plan.green_ns_s + plan.green_ew_s)) * 100.0), 1),
        "split_ew_pct": round(float(plan.green_ew_s / max(1e-3, (plan.green_ns_s + plan.green_ew_s)) * 100.0), 1),
        "source": str(source),
    }
    if extra:
        rec.update(extra)
    return rec
