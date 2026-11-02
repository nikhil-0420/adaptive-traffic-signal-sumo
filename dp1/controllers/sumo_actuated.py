"""SUMO built-in actuated traffic signal controller.

Uses SUMO's native 'actuated' traffic light logic (type='actuated') with
detectors, adhering to the same safety state machine, clearance intervals
(3s yellow, 2s all-red), and phase definitions.

Parameters & Provenance:
- minDur: 10.0 s (minimum green duration before gap-out can terminate phase).
  Source: Project-wide minimum green safety constraint (C.ACTION.min_green_s / C.ADAPTIVE.min_green_s).
- maxDur: 60.0 s (hard maximum green duration before forced switch).
  Source: Project-wide maximum green constraint (C.ACTION.max_green_s / C.ADAPTIVE.max_green_s).
- max-gap: 3.0 s (maximum time gap between detector vehicle passages to keep extending green).
  Source: Eclipse SUMO documentation default for actuated controllers
  (https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#actuated_traffic_lights).
- detector-gap: 3.0 s (time threshold between detector activation and green extension).
  Source: Eclipse SUMO v1.21.0 default parameter.
- yellow clearance: 3.0 s (matches C.TIMING.yellow_s across all policies).
- all-red clearance: 2.0 s (matches C.TIMING.all_red_s across all policies).
"""
from pathlib import Path
from typing import Optional, Dict
import traci

from .base import PhaseMachineController
from .. import config as C


def get_actuated_additional_file(
    network: str,
    tls_id: str,
    states,
    cfg: Optional[C.SumoActuatedConfig] = None,
    timing: Optional[C.SignalTiming] = None,
    out_dir: Optional[Path] = None,
) -> Path:
    """Generate or retrieve the SUMO actuated tlLogic additional XML file."""
    cfg = cfg or C.SUMO_ACTUATED
    timing = timing or C.TIMING
    target_dir = out_dir or (C.SUMO_DIR / "actuated")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{network}_{tls_id}_actuated.add.xml"

    ns_green = states.green("NS")
    ns_yellow = states.yellow("NS")
    all_red = states.all_red()
    ew_green = states.green("EW")
    ew_yellow = states.yellow("EW")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n'
        f'    <tlLogic id="{tls_id}" type="actuated" programID="sumo_actuated" offset="0">\n'
        f'        <param key="max-gap" value="{cfg.max_gap_s:.1f}"/>\n'
        f'        <param key="detector-gap" value="{cfg.detector_gap_s:.1f}"/>\n'
        f'        <phase duration="{cfg.max_green_s:.0f}" minDur="{cfg.min_green_s:.0f}" maxDur="{cfg.max_green_s:.0f}" state="{ns_green}"/>\n'
        f'        <phase duration="{timing.yellow_s:.0f}" minDur="{timing.yellow_s:.0f}" maxDur="{timing.yellow_s:.0f}" state="{ns_yellow}"/>\n'
        f'        <phase duration="{timing.all_red_s:.0f}" minDur="{timing.all_red_s:.0f}" maxDur="{timing.all_red_s:.0f}" state="{all_red}"/>\n'
        f'        <phase duration="{cfg.max_green_s:.0f}" minDur="{cfg.min_green_s:.0f}" maxDur="{cfg.max_green_s:.0f}" state="{ew_green}"/>\n'
        f'        <phase duration="{timing.yellow_s:.0f}" minDur="{timing.yellow_s:.0f}" maxDur="{timing.yellow_s:.0f}" state="{ew_yellow}"/>\n'
        f'        <phase duration="{timing.all_red_s:.0f}" minDur="{timing.all_red_s:.0f}" maxDur="{timing.all_red_s:.0f}" state="{all_red}"/>\n'
        '    </tlLogic>\n'
        '</additional>\n'
    )
    target_file.write_text(xml, encoding="utf-8")
    return target_file


class SumoActuatedController(PhaseMachineController):
    """SUMO native actuated controller wrapped in the shared safety state machine."""
    name = "sumo_actuated"

    def __init__(
        self,
        states,
        tls_id: str = C.TLS_ID,
        cfg: Optional[C.SumoActuatedConfig] = None,
        timing: Optional[C.SignalTiming] = None,
        network: str = "synthetic",
        **kw,
    ):
        super().__init__(states, tls_id=tls_id, timing=timing or C.TIMING, **kw)
        self.cfg = cfg or C.SUMO_ACTUATED
        self.network = network.lower().strip()
        self._traci_active = False
        self._gap_out_since: Optional[float] = None

    def start(self, t: float, queues):
        """Initialize controller and switch SUMO to native actuated program."""
        try:
            traci.trafficlight.setProgram(self.tls, "sumo_actuated")
            self._traci_active = True
        except (traci.exceptions.FatalTraCIError, traci.exceptions.TraCIException, Exception):
            self._traci_active = False

        self._enter_green("NS", t, queues)

    def decide_green(self, axis: str, queues, t: float) -> float:
        """Baseline initial target green duration (defaults to max_green_s)."""
        return float(self.cfg.max_green_s)

    def green_should_end(self, axis: str, elapsed: float, queues, t: float) -> bool:
        """Standalone fallback decision logic (mimics SUMO gap-out if TraCI is absent)."""
        if elapsed < self.cfg.min_green_s:
            return False
        if elapsed >= self.cfg.max_green_s:
            return True
        own_q = max(queues[a] for a in C.AXES[axis])
        other_q = max(queues[a] for a in C.AXES[C.OTHER_AXIS[axis]])
        if own_q <= 0.0 and other_q > 0.0:
            if self._gap_out_since is None:
                self._gap_out_since = t
            if t - self._gap_out_since >= self.cfg.max_gap_s:
                return True
        else:
            self._gap_out_since = None
        return False

    def step(self, t: float, queues, action=None):
        """Observe SUMO's native state transitions and keep telemetry/decisions synchronized."""
        if not self._traci_active:
            # TraCI inactive fallback (e.g. pure unit test)
            super().step(t, queues, action=action)
            return

        try:
            tl_state = traci.trafficlight.getRedYellowGreenState(self.tls)
        except Exception:
            super().step(t, queues, action=action)
            return

        # Determine current state from SUMO TLS string
        if tl_state == self.states.green("NS"):
            curr_axis, curr_phase = "NS", "GREEN"
        elif tl_state == self.states.yellow("NS"):
            curr_axis, curr_phase = "NS", "YELLOW"
        elif tl_state == self.states.green("EW"):
            curr_axis, curr_phase = "EW", "GREEN"
        elif tl_state == self.states.yellow("EW"):
            curr_axis, curr_phase = "EW", "YELLOW"
        else:
            curr_axis, curr_phase = self.axis, "ALL_RED"

        # Detect transition
        if curr_phase != self.phase:
            if self.phase == "GREEN" and self.decisions:
                actual_g = max(0.0, round(t - self.phase_start, 1))
                self.decisions[-1]["actual_green_s"] = actual_g
                if actual_g >= self.cfg.max_green_s:
                    self.decisions[-1]["switch_reason"] = "MAX_GREEN_EXPIRED"
                else:
                    self.decisions[-1]["switch_reason"] = "GAP_OUT"

            if curr_phase == "GREEN":
                self.axis = curr_axis
                self.phase = "GREEN"
                self.phase_start = t
                self.cycle += 1
                rec = {
                    "t": round(t, 1),
                    "cycle": self.cycle,
                    "axis": self.axis,
                    "green_s": float(self.cfg.max_green_s),
                    "actual_green_s": float(self.cfg.max_green_s),
                    **{f"q_{a}_m": round(queues[a], 1) for a in C.APPROACHES},
                }
                self.decisions.append(rec)
            else:
                self.phase = curr_phase
                self.phase_start = t
        else:
            # Phase is continuing
            if self.phase == "GREEN" and self.decisions:
                self.decisions[-1]["actual_green_s"] = max(0.0, round(t - self.phase_start, 1))

    def apply(self):
        """In actuated mode, SUMO natively manages state transitions."""
        if not self._traci_active:
            super().apply()
