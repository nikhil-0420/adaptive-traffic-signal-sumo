---
description: Verify the project works end to end (setup, tests, demo)
---
1. Check `sumo --version` works inside the active venv; if not, run `pip install -r requirements.txt`.
2. Run `python -m dp1.cli build`.
3. Run `pytest -q` and report the pass count.
4. Run `python -m dp1.cli demo` and report both lines of output.
5. Report any failure with the full error text. Do not change code to hide a failure.
