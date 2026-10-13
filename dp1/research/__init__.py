"""Research Evaluation Pipeline package for DP1."""
from .matrix import (
    ResearchMatrix,
    MatrixCell,
    CellStatus,
    build_research_matrix,
)
from .stats import (
    compute_aggregates,
    compute_paired_deltas,
    compute_fairness_by_approach,
    compute_fairness_by_direction,
)
from .plots import generate_research_plots
from .report_gen import generate_research_report
from .orchestrator import run_research_experiment

__all__ = [
    "ResearchMatrix",
    "MatrixCell",
    "CellStatus",
    "build_research_matrix",
    "compute_aggregates",
    "compute_paired_deltas",
    "compute_fairness_by_approach",
    "compute_fairness_by_direction",
    "generate_research_plots",
    "generate_research_report",
    "run_research_experiment",
]
