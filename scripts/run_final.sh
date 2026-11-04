#!/usr/bin/env bash
# DP1: Final Experiment Matrix Quality-Gated Execution Script
# Refuses to run unless working tree is clean and HEAD equals the frozen tag 'dp1-final-frozen'.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate Python virtual environment if present
if [ -d ".venv" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    fi
fi

python -u scripts/run_final.py "$@"
