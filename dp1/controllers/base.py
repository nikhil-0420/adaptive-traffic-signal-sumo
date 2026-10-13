"""Phase state machine shared by every controller.

    GREEN(axis)  ->  YELLOW(axis)  ->  ALL_RED  ->  GREEN(other axis)  -> ...

Safety invariant (tested):
- A green never follows a green directly.
- Every switch passes through yellow (3 s) and all-red (2 s).
- Both axes are never green simultaneously.

Action seam semantics (for external / RL / emergency controllers):
- Two discrete actions: HOLD (0) and REQUEST_SWITCH (1).
- Actions are evaluated on simulation steps during GREEN.
- Outside GREEN (during YELLOW or ALL_RED), actions are completely ignored.
- Minimum green cannot be violated: if elapsed < min_green, REQUEST_SWITCH is ignored.
- Maximum green forces switch: if elapsed >= max_green, switch is forced even on HOLD.
- Accepted switches always initiate the standard clearance chain (YELLOW -> ALL_RED -> next GREEN).
- Legacy controllers remain unchanged with external actions off by default (action=None).
"""
from enum import IntEnum
import traci
from .. import config as C


class ControllerAction(IntEnum):
    """Discrete actions accepted by the controller action seam during GREEN.

    HOLD (0):
        Request to continue the current green phase.
        Ignored outside GREEN.
        Overridden by max_green: if elapsed >= max_green, a switch is forced.

    REQUEST_SWITCH (1):
        Request to terminate the current green phase and switch to the other axis.
        Ignored outside GREEN.
        Guarded by min_green: if elapsed < min_green, the request is rejected/ignored.
        Once accepted, the controller transitions GREEN -> YELLOW -> ALL_RED -> GREEN(other axis).
    """
    HOLD = 0
    REQUEST_SWITCH = 1


class PhaseMachineController:
    name = "base"

    def __init__(self, states, tls_id=C.TLS_ID, timing=C.TIMING,
                 min_green_s=None, max_green_s=None,
                 emergency_priority: bool = False,
                 emergency_cfg=None, **_kw):
        self.states = states
        self.tls = tls_id
        self.timing = timing
        self.min_green_s = min_green_s
        self.max_green_s = max_green_s
        self.emergency_priority = emergency_priority
        self.emergency_cfg = emergency_cfg or (C.EMERGENCY if emergency_priority else None)
        if self.emergency_priority:
            from ..emergency import EmergencyPriorityCoordinator
            self.emergency_coordinator = EmergencyPriorityCoordinator(em_cfg=self.emergency_cfg)
        else:
            self.emergency_coordinator = None

        self.axis = "NS"
        self.phase = "GREEN"           # GREEN | YELLOW | ALL_RED
        self.phase_start = 0.0
        self.target_green = 0.0
        self.cycle = 0
        self.decisions = []            # one dict per green decision (for the demo / report)

    # ---- bounds resolution ----------------------------------------------------
    def get_min_green_s(self) -> float:
        """Effective minimum green duration for action seam evaluation."""
        if self.min_green_s is not None:
            return float(self.min_green_s)
        if hasattr(self, "cfg") and hasattr(self.cfg, "min_green_s"):
            return float(self.cfg.min_green_s)
        return float(C.ACTION.min_green_s)

    def get_max_green_s(self) -> float:
        """Effective maximum green duration for action seam evaluation."""
        if self.max_green_s is not None:
            return float(self.max_green_s)
        if hasattr(self, "cfg") and hasattr(self.cfg, "max_green_s"):
            return float(self.cfg.max_green_s)
        base_max = float(C.ACTION.max_green_s)
        if hasattr(self, "target_green") and self.target_green > base_max:
            return float(self.target_green)
        return base_max

    # ---- hooks for subclasses -------------------------------------------------
    def decide_green(self, axis, queues, t):
        """Establish target green duration upon entering GREEN."""
        raise NotImplementedError

    def green_should_end(self, axis, elapsed, queues, t):
        """Legacy decision hook for whether GREEN should end at this timestep."""
        return elapsed >= self.target_green

    def decide_action(self, axis, elapsed, queues, t):
        """Optional hook for subclasses (e.g. RL policy) to produce a per-step action.

        Returns ControllerAction.HOLD (0), ControllerAction.REQUEST_SWITCH (1), or None.
        Default is None (delegates to legacy green_should_end).
        """
        return None

    # ---- machine --------------------------------------------------------------
    def start(self, t, queues):
        self._enter_green("NS", t, queues)

    def _enter_green(self, axis, t, queues):
        self.axis, self.phase, self.phase_start = axis, "GREEN", t
        self.target_green = self.decide_green(axis, queues, t)
        self.cycle += 1
        rec = {
            "t": round(t, 1), "cycle": self.cycle, "axis": axis,
            "green_s": round(self.target_green, 1),
            "actual_green_s": round(self.target_green, 1),
            **{f"q_{a}_m": round(queues[a], 1) for a in C.APPROACHES},
        }
        if self.emergency_priority and self.emergency_coordinator:
            rec["emergency_status"] = self.emergency_coordinator.last_status
        self.decisions.append(rec)

    def _evaluate_green_switch(self, elapsed, queues, t, action=None):
        """Evaluate if GREEN should end, enforcing action seam semantics and bounds.

        Action semantics:
        - If action is None, query subclass decide_action().
        - If an action is specified (externally or from decide_action):
            - If elapsed >= max_green: forces switch (returns True).
            - If action is REQUEST_SWITCH: returns True if elapsed >= min_green else False.
            - If action is HOLD: returns False (unless elapsed >= max_green above).
        - If emergency priority is enabled and coordinator returns an override action, apply it.
        - If action is still None: falls back to legacy green_should_end().
        """
        if action is None:
            action = self.decide_action(self.axis, elapsed, queues, t)

        policy_wants_switch = False
        act = None
        if action is not None:
            if action in (ControllerAction.REQUEST_SWITCH, 1, "REQUEST_SWITCH"):
                act = ControllerAction.REQUEST_SWITCH
                policy_wants_switch = True
            elif action in (ControllerAction.HOLD, 0, "HOLD"):
                act = ControllerAction.HOLD
                policy_wants_switch = False
            else:
                raise ValueError(
                    f"Invalid action {action!r}: expected ControllerAction.HOLD (0) "
                    f"or ControllerAction.REQUEST_SWITCH (1)"
                )
        else:
            policy_wants_switch = self.green_should_end(self.axis, elapsed, queues, t)

        # Emergency priority override check
        if self.emergency_priority and self.emergency_coordinator:
            em_action, _ = self.emergency_coordinator.evaluate(
                self.axis, self.phase, elapsed, t, policy_wants_switch
            )
            if em_action is not None:
                act = em_action

        min_g = self.get_min_green_s()
        base_max_g = self.get_max_green_s()
        if self.emergency_priority and self.emergency_cfg:
            max_allowed = base_max_g + self.emergency_cfg.max_extension_s
        else:
            max_allowed = base_max_g

        if act is not None:
            # Maximum green bounds force switch regardless of action
            if elapsed >= max_allowed:
                return True

            # REQUEST_SWITCH accepted only after minimum green
            if act == ControllerAction.REQUEST_SWITCH:
                return elapsed >= min_g

            # HOLD requested and within max_allowed bound
            return False

        # Legacy decision logic for existing policies
        return policy_wants_switch

    def step(self, t, queues, action=None):
        """Advance the controller by one simulation step.

        Args:
            t: current simulation time in seconds.
            queues: dict of approach queue lengths in metres.
            action: optional external action (HOLD=0, REQUEST_SWITCH=1).
                    Ignored outside GREEN. If None, uses controller policy.
        """
        elapsed = t - self.phase_start
        if self.phase == "GREEN":
            if self._evaluate_green_switch(elapsed, queues, t, action=action):
                if self.decisions:
                    self.decisions[-1]["actual_green_s"] = round(elapsed, 1)
                    if self.emergency_priority and self.emergency_coordinator:
                        self.decisions[-1]["emergency_status"] = self.emergency_coordinator.last_status
                self.phase, self.phase_start = "YELLOW", t
        elif self.phase == "YELLOW":
            # Action ignored outside GREEN; clearance timing cannot be bypassed
            if elapsed >= self.timing.yellow_s:
                self.phase, self.phase_start = "ALL_RED", t
        elif self.phase == "ALL_RED":
            # Action ignored outside GREEN; clearance timing cannot be bypassed
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
        try:
            if traci.trafficlight.getRedYellowGreenState(self.tls) != want:
                traci.trafficlight.setRedYellowGreenState(self.tls, want)
        except (traci.exceptions.FatalTraCIError, traci.exceptions.TraCIException):
            pass
