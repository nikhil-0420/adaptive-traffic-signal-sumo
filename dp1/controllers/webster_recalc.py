"""Recalculated Webster baseline traffic signal controller.

Re-solves Webster's optimal cycle and splits every N minutes (default 300 s / 5 min)
from a sliding window of measured approach flows (default W = 300 s / 5 min).
New plans are applied strictly at a legal cycle boundary (start of NS GREEN after
completing EW clearance).
"""
from typing import Dict, List, Set, Tuple, Optional
import traci

from .base import PhaseMachineController
from .webster_utils import compute_webster_plan, format_plan_record
from .. import config as C
from ..signal_states import MARATHAHALLI_APPROACH_EDGES


class WebsterRecalcController(PhaseMachineController):
    """Webster controller re-solved periodically from a sliding window of measured flows."""
    name = "webster_recalc"

    def __init__(
        self,
        states,
        network: str = "synthetic",
        cfg: Optional[C.WebsterRecalcConfig] = None,
        timing: Optional[C.SignalTiming] = None,
        **kw,
    ):
        super().__init__(states, timing=timing or C.TIMING, **kw)
        self.network = network.lower().strip()
        self.cfg = cfg or C.WEBSTER_RECALC
        self.recalc_interval_s = float(self.cfg.recalc_interval_s)
        self.window_s = float(self.cfg.window_s)
        self.next_recalc_t = self.recalc_interval_s

        if self.network == "marathahalli":
            self.current_plan = C.FIXED_MARATHAHALLI
            self.edges = dict(MARATHAHALLI_APPROACH_EDGES)
        else:
            self.current_plan = C.FIXED
            self.edges = {a: f"{a}_in" for a in C.APPROACHES}

        self.pending_plan: Optional[C.FixedTimeConfig] = None
        self.last_solved_flows: Optional[Dict[str, float]] = None

        # Arrival tracking: approach -> list of (veh_id, arrival_t)
        self.arrivals: Dict[str, List[Tuple[str, float]]] = {a: [] for a in C.APPROACHES}
        self._active_on_edge: Dict[str, Set[str]] = {a: set() for a in C.APPROACHES}

        # Plan audit trail
        self.plan_log: List[Dict] = []
        self._log_plan(0.0, self.current_plan, "btp_warmup")

    def _log_plan(self, t: float, plan: C.FixedTimeConfig, source: str, extra: Optional[Dict] = None):
        rec = format_plan_record(
            t_applied_s=t,
            plan=plan,
            timing=self.timing,
            source=source,
            cycle_index=self.cycle,
            extra=extra,
        )
        self.plan_log.append(rec)

    def _track_arrivals(self, t: float):
        """Record arrival times of newly appearing vehicles on approach legs."""
        try:
            for a, edge_id in self.edges.items():
                cur_vehs = set(traci.edge.getLastStepVehicleIDs(edge_id))
                new_vehs = cur_vehs - self._active_on_edge[a]
                for vid in new_vehs:
                    self.arrivals[a].append((vid, t))
                self._active_on_edge[a] = cur_vehs
        except (traci.exceptions.FatalTraCIError, traci.exceptions.TraCIException):
            pass

    def decide_green(self, axis: str, queues, t: float) -> float:
        """Establish target green duration from currently active plan."""
        return self.current_plan.green_ns_s if axis == "NS" else self.current_plan.green_ew_s

    def _enter_green(self, axis: str, t: float, queues):
        """Cycle boundary hook: apply pending plan when starting a new cycle on NS."""
        if axis == "NS" and self.pending_plan is not None:
            self.current_plan = self.pending_plan
            self.pending_plan = None
            extra = {"measured_flows_vph": {a: round(f, 1) for a, f in (self.last_solved_flows or {}).items()}}
            self._log_plan(t, self.current_plan, "webster_recalc", extra=extra)

        super()._enter_green(axis, t, queues)

    def step(self, t: float, queues, action=None):
        """Advance controller and re-solve Webster at periodic intervals."""
        self._track_arrivals(t)

        while t >= self.next_recalc_t:
            t_end = self.next_recalc_t
            t_start = max(0.0, t_end - self.window_s)
            dt = t_end - t_start

            flows: Dict[str, float] = {}
            for a in C.APPROACHES:
                count = sum(1 for _, arr_t in self.arrivals[a] if t_start <= arr_t <= t_end)
                flows[a] = count * (3600.0 / max(1.0, dt))

            self.last_solved_flows = flows
            self.pending_plan = compute_webster_plan(
                flows_vph=flows,
                timing=self.timing,
                cfg=C.WEBSTER,
                lanes=C.NET.lanes,
                min_green_s=float(self.cfg.min_green_s),
            )
            self.next_recalc_t += self.recalc_interval_s

        super().step(t, queues, action=action)
