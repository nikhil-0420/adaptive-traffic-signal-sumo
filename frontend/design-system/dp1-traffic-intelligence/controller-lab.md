# Controller Lab & Policy Comparison — Design Guidelines

## Purpose
Direct side-by-side scientific comparison of traffic signal control algorithms (`fixed`, `fixed_webster`, `adaptive`, `pressure`, `rl_dqn`).

## Key Visualizations & Interactions
1. **Interactive Scenario & Demand Selector:**
   - Filter by scenario: `balanced`, `imbalanced_ns`, `imbalanced_ew`, `surge_north`.
   - Filter by demand level: `low (0.7x)`, `medium (1.0x)`, `heavy (1.3x)`.
   - Filter by seed range: Train seeds (1..5) vs Held-out seeds (11..15).
2. **Policy Performance Bar & Error Chart (Recharts):**
   - Grouped bars showing Average Wait Time (s) per policy with standard deviation error bars.
   - Distinct policy colors:
     - Fixed (Baseline): Slate `#64748B`
     - Webster: Amber `#F59E0B`
     - Adaptive Queue: Emerald `#10B981`
     - Pressure: Cyan `#06B6D4`
     - RL DQN: Violet `#8B5CF6`
3. **Paired Comparison Delta Matrix:**
   - Evaluates each candidate policy against Fixed baseline for identical seeds.
   - Shows Mean Delta (s), 95% Confidence Interval, and Wilcoxon/t-test significance.
4. **Directional Service Disparity:**
   - Visualizing NS vs EW wait time gap.
   - Contextual callout: Note that lower disparity means more balanced service between axes, but must be evaluated in conjunction with total throughput.
