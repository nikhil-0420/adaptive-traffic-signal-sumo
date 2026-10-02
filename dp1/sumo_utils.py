"""Locate SUMO binaries whether SUMO came from pip (eclipse-sumo) or a system install."""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _pip_sumo_home():
    try:
        import sumo  # provided by the eclipse-sumo wheel
        return sumo.SUMO_HOME
    except Exception:
        return None


def binary(name: str) -> str:
    """Return a runnable path for sumo / sumo-gui / netconvert / netgenerate."""
    exe = name + (".exe" if os.name == "nt" else "")
    # 1) next to the active python (venv Scripts/bin)
    cand = Path(sys.executable).parent / exe
    if cand.exists():
        return str(cand)
    # 2) on PATH
    found = shutil.which(name)
    if found:
        return found
    # 3) SUMO_HOME / pip SUMO_HOME
    for home in (os.environ.get("SUMO_HOME"), _pip_sumo_home()):
        if home:
            cand = Path(home) / "bin" / exe
            if cand.exists():
                return str(cand)
    raise FileNotFoundError(
        f"Cannot find '{name}'. Run: pip install -r requirements.txt (installs SUMO), "
        "or install SUMO and set SUMO_HOME."
    )


def run(cmd, **kw):
    res = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd))}\n{res.stdout}\n{res.stderr}")
    return res
