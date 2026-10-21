"""Process manager for launching and tracking SUMO simulation subprocesses safely."""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import REPO_ROOT, RESEARCH_DIR, RUNS_DIR


class ProcessInfo:
    def __init__(
        self,
        item_id: str,
        item_type: str,  # "run" or "experiment"
        proc: subprocess.Popen,
        log_path: Path,
        started_at: float,
    ):
        self.item_id = item_id
        self.item_type = item_type
        self.proc = proc
        self.log_path = log_path
        self.started_at = started_at
        self.finished_at: Optional[float] = None
        self.exit_code: Optional[int] = None
        self.cancelled: bool = False

    def poll_status(self) -> str:
        """Return 'running', 'completed', 'failed', or 'cancelled'."""
        if self.proc.poll() is None:
            # Process is still running according to python handle
            return "running"

        if self.finished_at is None:
            self.finished_at = time.time()
            self.exit_code = self.proc.returncode

        if self.cancelled:
            return "cancelled"
        if self.exit_code == 0:
            return "completed"
        return "failed"


class ProcessManager:
    """Thread-safe manager for simulation subprocesses."""

    def __init__(self):
        self._lock = threading.Lock()
        self._processes: Dict[str, ProcessInfo] = {}

    def is_running(self, item_id: str) -> bool:
        with self._lock:
            info = self._processes.get(item_id)
            if not info:
                return False
            status = info.poll_status()
            if status != "running":
                return False

            # Check for stale telemetry if process has been active > 10s
            run_dir = RUNS_DIR / item_id
            telem_file = run_dir / "telemetry.json"
            if telem_file.exists():
                try:
                    with open(telem_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    updated_at = float(data.get("updated_at", 0))
                    if (time.time() - info.started_at > 10.0) and (time.time() - updated_at > 15.0):
                        # Process stalled: terminate safely and release lock
                        try:
                            info.proc.terminate()
                            info.proc.wait(timeout=2.0)
                        except Exception:
                            try:
                                info.proc.kill()
                            except Exception:
                                pass
                        info.finished_at = time.time()
                        info.exit_code = -1
                        data["status"] = "failed"
                        data["error"] = "Simulation process stalled; telemetry ceased advancing."
                        with open(telem_file, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                        return False
                except Exception:
                    pass
            return True

    def clean_stale_processes(self, stale_threshold_s: float = 15.0) -> int:
        """Scan active runs and recover any stalled or dead child processes."""
        cleaned = 0
        with self._lock:
            for item_id, info in list(self._processes.items()):
                if info.poll_status() == "running":
                    run_dir = RUNS_DIR / item_id
                    telem_file = run_dir / "telemetry.json"
                    if telem_file.exists():
                        try:
                            with open(telem_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            updated_at = float(data.get("updated_at", 0))
                            if (time.time() - info.started_at > 10.0) and (time.time() - updated_at > stale_threshold_s):
                                try:
                                    info.proc.terminate()
                                    info.proc.wait(timeout=2.0)
                                except Exception:
                                    try:
                                        info.proc.kill()
                                    except Exception:
                                        pass
                                info.finished_at = time.time()
                                info.exit_code = -1
                                data["status"] = "failed"
                                data["error"] = "Simulation process stalled; telemetry ceased advancing."
                                with open(telem_file, "w", encoding="utf-8") as f:
                                    json.dump(data, f)
                                cleaned += 1
                        except Exception:
                            pass
        return cleaned

    def count_active(self, item_type: Optional[str] = None) -> int:
        with self._lock:
            count = 0
            for info in self._processes.values():
                if info.poll_status() == "running":
                    if item_type is None or info.item_type == item_type:
                        count += 1
            return count

    def get_info(self, item_id: str) -> Optional[ProcessInfo]:
        with self._lock:
            info = self._processes.get(item_id)
            if info:
                info.poll_status()  # update internal state if exited
            return info

    def launch_run(
        self,
        run_id: str,
        scenario: str,
        policy: str,
        seed: int,
        demand_level: str = "medium",
        emergency_event: bool = False,
        emergency_priority: bool = False,
        emergency_approach: str = "N",
        emergency_depart: float = 300.0,
        model_path: Optional[str] = None,
        gui: bool = False,
        network: str = "synthetic",
    ) -> Tuple[bool, str]:
        """Launch a single simulation run via `sys.executable -m dp1.cli run ...`."""
        with self._lock:
            info = self._processes.get(run_id)
            if info and info.poll_status() == "running":
                return False, f"Run '{run_id}' is already running with PID {info.proc.pid}."

            run_dir = RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            log_path = run_dir / "process.log"

            cmd = [
                sys.executable,
                "-u",
                "-m", "dp1.cli", "run",
                "--scenario", scenario,
                "--policy", policy,
                "--seed", str(seed),
                "--demand-level", demand_level,
                "--network", network,
                "--record-vehicles",
            ]
            if gui:
                cmd.append("--gui")
            if model_path:
                cmd.extend(["--model-path", str(model_path)])
            if emergency_event:
                cmd.append("--emergency-event")
                cmd.extend(["--emergency-approach", emergency_approach])
                cmd.extend(["--emergency-depart", str(emergency_depart)])
                if emergency_priority:
                    cmd.append("--emergency-priority")

            try:
                log_file = open(log_path, "w", encoding="utf-8")
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_ROOT),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    shell=False,
                )
                self._processes[run_id] = ProcessInfo(
                    item_id=run_id,
                    item_type="run",
                    proc=proc,
                    log_path=log_path,
                    started_at=time.time(),
                )
                return True, f"Run '{run_id}' started with PID {proc.pid}."
            except Exception as e:
                return False, f"Failed to spawn run process: {e}"

    def launch_experiment(
        self,
        experiment_id: str,
        preset: str = "smoke",
        patterns: Optional[List[str]] = None,
        levels: Optional[List[str]] = None,
        policies: Optional[List[str]] = None,
        seeds: Optional[List[int]] = None,
        limit: Optional[int] = None,
        jobs: int = 1,
        emergency_matrix: bool = False,
        model_path: Optional[str] = None,
        network: str = "synthetic",
    ) -> Tuple[bool, str]:
        """Launch research matrix evaluation via `sys.executable -m dp1.cli evaluate-research ...`."""
        with self._lock:
            info = self._processes.get(experiment_id)
            if info and info.poll_status() == "running":
                return False, f"Experiment '{experiment_id}' is already running with PID {info.proc.pid}."

            exp_dir = RESEARCH_DIR / experiment_id
            exp_dir.mkdir(parents=True, exist_ok=True)
            log_path = exp_dir / "process.log"

            cmd = [
                sys.executable,
                "-u",
                "-m", "dp1.cli", "evaluate-research",
                "--preset", preset,
                "--experiment-id", experiment_id,
                "--jobs", str(jobs),
                "--network", network,
            ]
            if limit is not None:
                cmd.extend(["--limit", str(limit)])
            if patterns:
                cmd.append("--patterns")
                cmd.extend(patterns)
            if levels:
                cmd.append("--levels")
                cmd.extend(levels)
            if policies:
                cmd.append("--policies")
                cmd.extend(policies)
            if seeds:
                cmd.append("--seeds")
                cmd.extend([str(s) for s in seeds])
            if emergency_matrix:
                cmd.append("--emergency-matrix")
            if model_path:
                cmd.extend(["--model-path", str(model_path)])

            try:
                log_file = open(log_path, "w", encoding="utf-8")
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_ROOT),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    shell=False,
                )
                self._processes[experiment_id] = ProcessInfo(
                    item_id=experiment_id,
                    item_type="experiment",
                    proc=proc,
                    log_path=log_path,
                    started_at=time.time(),
                )
                return True, f"Experiment '{experiment_id}' started with PID {proc.pid}."
            except Exception as e:
                return False, f"Failed to spawn experiment process: {e}"

    def cancel(self, item_id: str) -> Tuple[bool, str]:
        """Safely terminate child process."""
        with self._lock:
            info = self._processes.get(item_id)
            if not info:
                return False, f"No active process found for '{item_id}'."
            if info.poll_status() != "running":
                return False, f"Process '{item_id}' is already {info.poll_status()}."

            info.cancelled = True
            try:
                info.proc.terminate()
                try:
                    info.proc.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    info.proc.kill()
                    info.proc.wait(timeout=2.0)
                info.finished_at = time.time()
                info.exit_code = info.proc.returncode
                return True, f"Process '{item_id}' was cancelled."
            except Exception as e:
                return False, f"Error cancelling process '{item_id}': {e}"


# Singleton instance
process_manager = ProcessManager()
