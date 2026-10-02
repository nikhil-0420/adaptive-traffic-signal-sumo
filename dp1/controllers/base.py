"""Phase state machine shared by every controller.

    GREEN(axis)  ->  YELLOW(axis)  ->  ALL_RED  ->  GREEN(other axis)  -> ...

Safety invariant (tested): a green never follows a green directly; every switch passes
through yellow and all-red. Subclasses only decide HOW LONG a green lasts.
"""
import traci
from .. import config as C


class PhaseMachineController:
    name = "base"

    def __init__(self, states, tls_id=C.TLS_ID, timing=C.TIMING, **_kw):
        self.states = states
        self.tls = tls_id
        self.timing = timing
        self.axis = "NS"
        self.phase = "GREEN"           # GREEN | YELLOW | ALL_RED
        self.phase_start = 0.0
        self.target_green = 0.0
        self.cycle = 0
        self.decisions = []            # one dict per green decision (for the demo / report)

    # ---- hooks for subclasses -------------------------------------------------
    def decide_green(self, axis, queues, t):
        raise NotImplementedError

    def green_should_end(self, axis, elapsed, queues, t):
        return elapsed >= self.target_green

    # ---- machine --------------------------------------------------------------
    def start(self, t, queues):
        self._enter_green("NS", t, queues)

    def _enter_green(self, axis, t, queues):
        self.axis, self.phase, self.phase_start = axis, "GREEN", t
        self.target_green = self.decide_green(axis, queues, t)
        self.cycle += 1
        self.decisions.append({
            "t": round(t, 1), "cycle": self.cycle, "axis": axis,
            "green_s": round(self.target_green, 1),
            **{f"q_{a}_m": round(queues[a], 1) for a in C.APPROACHES},
        })

    def step(self, t, queues):
        elapsed = t - self.phase_start
        if self.phase == "GREEN":
            if self.green_should_end(self.axis, elapsed, queues, t):
                self.phase, self.phase_start = "YELLOW", t
        elif self.phase == "YELLOW":
            if elapsed >= self.timing.yellow_s:
                self.phase, self.phase_start = "ALL_RED", t
        elif self.phase == "ALL_RED":
            if elapsed >= self.timing.all_red_s:
                self._enter_green(C.OTHER_AXIS[self.axis], t, queues)
        self.apply()

    def desired_state(self):
        if self.phase == "GREEN":
            return self.states.green(self.axis)
        if self.phase == "YELLOW":
            return self.states.yellow(self.axis)
        return self.states.all_red()

    def apply(self):
        want = self.desired_state()
        if traci.trafficlight.getRedYellowGreenState(self.tls) != want:
            traci.trafficlight.setRedYellowGreenState(self.tls, want)
