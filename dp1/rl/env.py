"""Gymnasium environment wrapping SUMO traffic junction simulation.

Each environment step represents one SUMO simulation second (step_s = 1.0).
Action space: Discrete(2) where:
    0 = HOLD (request to continue the current green phase)
    1 = REQUEST_SWITCH (request to end green phase and transition to the other axis)

Signal safety transitions (GREEN -> YELLOW -> ALL_RED -> GREEN) and green time
bounds (min_green_s = 10s, max_green_s = 60s) are strictly enforced by
PhaseMachineController.
"""
from pathlib import Path
import random
import time
from typing import Any, Dict, Optional, Tuple

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    _GYM_AVAILABLE = True
except ImportError:
    gym = None
    spaces = None
    _GYM_AVAILABLE = False

import traci

from .. import config as C
from ..controllers.base import PhaseMachineController, ControllerAction
from ..network import NET_FILE, DET_FILE, build_network
from ..scenarios import build_routes
from ..signal_states import SignalStates
from ..sumo_utils import binary
from .obs import build_observation, OBS_DIM


class RLPhaseController(PhaseMachineController):
    """Minimal phase machine controller for RL environment.

    Defines nominal target green as max_green_s; actual phase switching
    is governed by agent actions via the action seam and bounded by min/max green.
    """
    name = "rl_phase_env"

    def decide_green(self, axis: str, queues: dict, t: float) -> float:
        return self.get_max_green_s()


def _read_detector_queues() -> Dict[str, float]:
    """Read queue length in metres per approach from SUMO lane-area detectors."""
    return {
        a: max(traci.lanearea.getJamLengthMeters(f"det_{a}_{i}") for i in range(C.NET.lanes))
        for a in C.APPROACHES
    }


class SumoIntersectionEnv(gym.Env if _GYM_AVAILABLE else object):
    """Gymnasium environment for adaptive traffic signal control on DP1 junction."""

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        scenario: str = "imbalanced_ns",
        seed: int = 1,
        cfg: C.RLConfig = C.RL,
        gui: bool = False,
        out_dir: Optional[Path] = None,
        rotate_seeds: bool = False,
        scenarios: Optional[tuple] = None,
    ):
        if not _GYM_AVAILABLE:
            raise ImportError(
                "Gymnasium is required for SumoIntersectionEnv. "
                "Install requirements-rl.txt: pip install -r requirements-rl.txt"
            )

        super().__init__()
        self.scenario = scenario
        self.scenarios = scenarios or (("imbalanced_ns", "imbalanced_ew", "balanced", "surge_north") if scenario == "all" else None)
        self.seed = seed
        self.cfg = cfg
        self.gui = gui
        self.out_dir = Path(out_dir) if out_dir else None
        self.rotate_seeds = rotate_seeds
        self._episode_count = 0

        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )

        self.ctl: Optional[RLPhaseController] = None
        self.states: Optional[SignalStates] = None
        self.t: float = 0.0
        self.queues: Dict[str, float] = {a: 0.0 for a in C.APPROACHES}
        self.n_vehicles: int = 0
        self._traci_running: bool = False

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the simulation environment for a new episode."""
        if seed is not None:
            self.seed = seed
        elif self.rotate_seeds and hasattr(self.cfg, "train_seeds") and self.cfg.train_seeds:
            self.seed = self.cfg.train_seeds[self._episode_count % len(self.cfg.train_seeds)]

        if self.scenarios:
            self.scenario = self.scenarios[self._episode_count % len(self.scenarios)]

        self._episode_count += 1
        self.close()

        if not NET_FILE.exists():
            build_network()

        # Build routes for this episode
        run_out = self.out_dir or (C.RESULTS_DIR / "rl_runs" / f"{self.scenario}_s{self.seed}")
        run_out.mkdir(parents=True, exist_ok=True)
        routes, self.n_vehicles = build_routes(self.scenario, self.seed, out_dir=run_out)

        cmd = [
            binary("sumo-gui" if self.gui else "sumo"),
            "-n", str(NET_FILE),
            "-r", str(routes),
            "-a", str(DET_FILE),
            "--seed", str(self.seed),
            "--step-length", str(C.SIM.step_s),
            "--time-to-teleport", "-1",
            "--no-step-log", "true",
            "--no-warnings", "true",
            "--waiting-time-memory", "3600",
        ]
        if self.out_dir is not None:
            cmd.extend(["--tripinfo-output", str(run_out / "tripinfo.xml")])
        if self.gui:
            cmd += ["--start", "true", "--delay", "100"]

        # Retry starting TraCI in case of port contention
        started = False
        last_exc = None
        for attempt in range(5):
            try:
                traci.start(cmd, label=f"rl_env_{self.scenario}_{self.seed}_{random.randint(1000, 99999)}")
                self._traci_running = True
                started = True
                break
            except Exception as exc:
                last_exc = exc
                try:
                    traci.close()
                except Exception:
                    pass
                time.sleep(random.uniform(0.2, 0.8))

        if not started:
            raise RuntimeError(f"Failed to start SUMO for RL env: {last_exc}") from last_exc

        self.states = SignalStates(NET_FILE)
        self.ctl = RLPhaseController(
            self.states,
            min_green_s=self.cfg.min_green_s,
            max_green_s=self.cfg.max_green_s,
        )

        self.t = 0.0
        self.queues = _read_detector_queues()
        self.ctl.start(self.t, self.queues)
        self.ctl.apply()

        obs = build_observation(
            queues=self.queues,
            axis=self.ctl.axis,
            phase=self.ctl.phase,
            elapsed_green_s=0.0,
            t_s=self.t,
            max_detector_m=self.cfg.max_detector_m,
            max_green_s=self.cfg.max_green_s,
            demand_duration_s=float(C.SIM.demand_duration_s),
        )

        info = {
            "t": self.t,
            "cycle": self.ctl.cycle,
            "phase": self.ctl.phase,
            "axis": self.ctl.axis,
            "queues": dict(self.queues),
        }
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one simulation second with the given discrete action."""
        if not self._traci_running or self.ctl is None:
            raise RuntimeError("Environment step called before reset or after close.")

        if action not in (0, 1):
            raise ValueError(f"Invalid action {action!r}: expected 0 (HOLD) or 1 (REQUEST_SWITCH)")

        prev_phase = self.ctl.phase

        # Step controller with external action
        self.ctl.step(self.t, self.queues, action=action)

        # Advance SUMO simulation by one second
        traci.simulationStep()
        self.t = float(traci.simulation.getTime())
        self.queues = _read_detector_queues()

        # Check if an accepted switch from GREEN to YELLOW occurred
        switched = (prev_phase == "GREEN" and self.ctl.phase == "YELLOW")

        # Elapsed green time
        elapsed_green = (self.t - self.ctl.phase_start) if self.ctl.phase == "GREEN" else 0.0

        # Build next observation
        obs = build_observation(
            queues=self.queues,
            axis=self.ctl.axis,
            phase=self.ctl.phase,
            elapsed_green_s=elapsed_green,
            t_s=self.t,
            max_detector_m=self.cfg.max_detector_m,
            max_green_s=self.cfg.max_green_s,
            demand_duration_s=float(C.SIM.demand_duration_s),
        )

        # Transparent normalized per-second reward across all approaches
        total_queue_m = sum(self.queues.values())
        norm_q = total_queue_m / (4.0 * self.cfg.max_detector_m)  # [0.0, 1.0]
        queue_penalty = self.cfg.queue_weight * norm_q
        switch_penalty = self.cfg.switch_penalty if switched else 0.0
        reward = float(-(queue_penalty + switch_penalty))

        # Termination: demand window finished and junction clear
        terminated = False
        truncated = False
        if self.t >= C.SIM.demand_duration_s:
            if traci.simulation.getMinExpectedNumber() == 0:
                terminated = True

        if self.t >= C.SIM.max_sim_time_s:
            truncated = True

        info = {
            "t": self.t,
            "cycle": self.ctl.cycle,
            "phase": self.ctl.phase,
            "axis": self.ctl.axis,
            "queues": dict(self.queues),
            "total_queue_m": round(total_queue_m, 2),
            "switched": switched,
            "reward_components": {
                "queue_penalty": round(queue_penalty, 4),
                "switch_penalty": round(switch_penalty, 4),
            },
        }

        if terminated or truncated:
            self.close()

        return obs, reward, terminated, truncated, info

    def close(self):
        """Cleanly close TraCI and terminate the SUMO process."""
        if self._traci_running:
            try:
                traci.close()
            except Exception:
                pass
            self._traci_running = False
