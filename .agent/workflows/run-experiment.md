---
description: Run the full fixed-vs-adaptive comparison and summarise the real results
---
1. Run `python -m dp1.cli compare --seeds 5 --jobs 4`.
2. Open `results/improvement.csv` and `results/aggregate.csv`.
3. Summarise per scenario: avg waiting time, avg queue, throughput, % change. Use only the real numbers.
4. State plainly any scenario where adaptive is worse than fixed.
5. Mention the plot files written to `results/`.
