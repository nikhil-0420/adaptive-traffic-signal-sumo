---
trigger: always_on
description: Where things live and how to change them
---
- Numbers live in `dp1/config.py` only. Controllers decide green duration only; the state machine is `controllers/base.py`.
- Use `SignalStates` for light strings; never hard-code SUMO phase indices.
- Do not edit generated files in `sumo/` or `results/`. Regenerate with the CLI.
- Finish each task by reporting: files changed, commands run, real numbers, open risks.
