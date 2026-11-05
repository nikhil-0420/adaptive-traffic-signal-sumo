"""Measured Webster baseline traffic signal controller.

Runs the BTP-adapted fixed plan during an initial warm-up window (300 s),
measures approach vehicle arrivals, solves for Webster's optimal cycle and
split, and applies the new plan strictly at the next legal cycle boundary.
Once applied, the plan remains fixed for the remainder of the run.
"""
from typing import Dict, List, Set, Tuple, Optional
import traci

from .base import PhaseMachineController
from .webster_utils import compute_webster_plan, format_plan_record
from .. import config as C
from ..signal_states import MARATHAHALLI_APPROACH_EDGES


class WebsterMeasuredController(PhaseMachineController):
    """Webster fixed controller with parameters derived from warm-up measured flows."""
    name = "webster_measured"

    def __init__(
        self,
        states,
        network: str = "synthetic",
        cfg: Optional[C.WebsterMeasuredConfig] = None,
        timing: Optional[C.SignalTiming] = None,
        **kw,
    ):
        super().__init__(states, timing=timing or C.TIMING, **kw)
        self.network = network.lower().strip()
        self.cfg = cfg or C.WEBSTER_MEASURED
        self.warmup_s = float(self.cfg.warmup_s)

        # Baseline warm-up plan: BTP-adapted fixed timing
        if self.network == "marathahalli":
            self.warmup_plan = C.FIXED_MARATHAHALLI
            self.edges = dict(MARATHAHALLI_APPROACH_EDGES)
        else:
            self.warmup_plan = C.FIXED
            self.edges = {a: f"{a}_in" for a in C.APPROACHES}

        self.current_plan = self.warmup_plan
        self.pending_plan: Optional[C.FixedTimeConfig] = None
        self.plan_solved: bool = False
        self.plan_applied: bool = False
        self.measured_flows: Optional[Dict[str, float]] = None

        # Arrival tracking: approach -> list of (veh_id, arrival_t)
        self.arrivals: Dict[str, List[Tuple[str, float]]] = {a: [] for a in C.APPROACHES}
        self._active_on_edge: Dict[str, Set[str]] = {a: set() for a in C.APPROACHES}

        # Plan audit trail for verification and reporting
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
        if axis == "NS" and self.pending_plan is not None and not self.plan_applied:
            self.current_plan = self.pending_plan
            self.pending_plan = None
            self.plan_applied = True
            extra = {"measured_flows_vph": {a: round(f, 1) for a, f in (self.measured_flows or {}).items()}}
            self._log_plan(t, self.current_plan, "webster_measured", extra=extra)

        super()._enter_green(axis, t, queues)

    def step(self, t: float, queues, action=None):
        """Simulation step hook with arrival recording and warm-up solver."""
        self._track_arrivals(t)

        # At warm-up expiration, compute Webster plan once from measured flows
        if t >= self.warmup_s and not self.plan_solved:
            dt = self.warmup_s
            flows: Dict[str, float] = {}
            for a in C.APPROACHES:
                # Count arrivals within warm-up window [0, warmup_s]
                count = sum(1 for _, arr_t in self.arrivals[a] if 0.0 <= arr_t <= self.warmup_s)
                flows[a] = count * (3600.0 / max(1.0, dt))

            self.measured_flows = flows
            self.pending_plan = compute_webster_plan(
                flows_vph=flows,
                timing=self.timing,
                cfg=C.WEBSTER,
                lanes=C.NET.lanes,
                min_green_s=float(self.cfg.min_green_s),
            )
            self.plan_solved = True

        super().step(t, queues, action=action)
