---
description: Tune adaptive-controller parameters on train seeds, evaluate on held-out seeds
---
1. Use `dp1/tune.py` (create it if missing). Search space lives in `dp1/config.py`: k_s_per_m, min_green_s, max_green_s, gap_out_s.
2. Optimise mean waiting time over scenarios on TRAIN seeds 1-5 only.
3. Evaluate the best settings and the defaults on HELD-OUT seeds 11-15.
4. Write `results/tuning.csv` and a short `results/tuning.md` with train vs held-out numbers.
5. Never report train-seed numbers as the result.
