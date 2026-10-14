"""Research evaluation matrix definitions, cell models, and plan previews."""
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from .. import config as C


class CellStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class MatrixCell:
    """One evaluation run unit within the research matrix."""
    cell_id: str
    pattern: str
    demand_level: str
    policy: str
    seed: int
    network: str = "synthetic"
    status: str = CellStatus.PENDING.value
    runtime_s: float = 0.0
    route_hash: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResearchMatrix:
    """Container for the full research plan and its constituent cells."""
    experiment_id: str
    patterns: Tuple[str, ...]
    levels: Tuple[str, ...]
    policies: Tuple[str, ...]
    seeds: Tuple[int, ...]
    cells: List[MatrixCell]
    preset: str = "full"
    network: str = "synthetic"

    @property
    def total_cells(self) -> int:
        return len(self.cells)

    def status_counts(self) -> dict:
        counts = {s.value: 0 for s in CellStatus}
        for c in self.cells:
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts


SITE_PATTERNS = ("balanced", "imbalanced_orr", "imbalanced_varthur", "surge_orr_north")
SITE_POLICIES_LEGACY = ("fixed", "fixed_webster", "adaptive", "pressure", "rl_dqn")
SITE_POLICIES = ("fixed", "fixed_webster", "adaptive", "pressure", "queue_extension", "rl_dqn")
SITE_RESEARCH_SEEDS = tuple(range(121, 131))  # (121..130)


def build_research_matrix(
    experiment_id: str,
    patterns: Optional[Tuple[str, ...]] = None,
    levels: Optional[Tuple[str, ...]] = None,
    policies: Optional[Tuple[str, ...]] = None,
    seeds: Optional[Tuple[int, ...]] = None,
    preset: str = "full",
    network: str = "synthetic",
) -> ResearchMatrix:
    """Build the planned research evaluation matrix.

    Presets:
        'smoke': tiny deterministic sanity test.
        'full': canonical research matrix (720 runs for synthetic, 720 runs for marathahalli site; 600 for legacy exp_marathahalli_site).
        'custom': user-selected combination of factors.
    """
    if network == "marathahalli":
        default_pats = SITE_PATTERNS
        default_pols = SITE_POLICIES_LEGACY if experiment_id == "exp_marathahalli_site" else SITE_POLICIES
        default_sds = SITE_RESEARCH_SEEDS
        smoke_pats = ("imbalanced_orr",)
        smoke_lvls = ("low",)
        smoke_pols = ("fixed", "adaptive", "rl_dqn")
        smoke_sds = (121,)
    else:
        default_pats = C.RESEARCH.patterns
        default_pols = C.RESEARCH.policies
        default_sds = C.RESEARCH.seeds
        smoke_pats = ("imbalanced_ns",)
        smoke_lvls = ("medium",)
        smoke_pols = ("fixed", "adaptive", "pressure")
        smoke_sds = (21,)

    if preset == "smoke":
        pats = smoke_pats
        lvls = smoke_lvls
        pols = smoke_pols
        sds = smoke_sds
    elif preset == "full":
        pats = patterns or default_pats
        lvls = levels or C.RESEARCH.levels
        pols = policies or default_pols
        sds = seeds or default_sds
    else:  # custom
        pats = patterns or default_pats
        lvls = levels or C.RESEARCH.levels
        pols = policies or default_pols
        sds = seeds or default_sds

    cells: List[MatrixCell] = []
    for pat in pats:
        for lvl in lvls:
            for pol in pols:
                for sd in sds:
                    net_prefix = f"cell_{network}" if network != "synthetic" else "cell"
                    c_id = f"{net_prefix}_{pat}_{lvl}_{pol}_s{sd}"
                    cells.append(MatrixCell(
                        cell_id=c_id,
                        pattern=pat,
                        demand_level=lvl,
                        policy=pol,
                        seed=sd,
                        network=network,
                    ))

    return ResearchMatrix(
        experiment_id=experiment_id,
        patterns=pats,
        levels=lvls,
        policies=pols,
        seeds=sds,
        cells=cells,
        preset=preset,
        network=network,
    )


def format_matrix_preview(matrix: ResearchMatrix) -> str:
    """Render a clear, human-readable summary table of the planned matrix."""
    lines = [
        "=" * 80,
        f"DP1 RESEARCH EVALUATION MATRIX PLAN -- Experiment ID: {matrix.experiment_id}",
        "=" * 80,
        f"Preset:             {matrix.preset}",
        f"Patterns ({len(matrix.patterns)}):       {', '.join(matrix.patterns)}",
        f"Demand Levels ({len(matrix.levels)}):  {', '.join(f'{l} (x{C.DEMAND_LEVELS[l]:.2f})' for l in matrix.levels)}",
        f"Policies ({len(matrix.policies)}):       {', '.join(matrix.policies)}",
        f"Seeds ({len(matrix.seeds)}):          {matrix.seeds[0]}..{matrix.seeds[-1]} (n={len(matrix.seeds)})",
        f"Total Matrix Cells: {matrix.total_cells}",
        "-" * 80,
        f"{'Index':>5} | {'Cell ID':<35} | {'Pattern':<14} | {'Level':<7} | {'Policy':<14} | {'Seed':>4}",
        "-" * 80,
    ]
    # Show first 15 and last 5 if large
    display_cells = matrix.cells if len(matrix.cells) <= 20 else matrix.cells[:12] + [None] + matrix.cells[-3:]
    for idx, c in enumerate(display_cells):
        if c is None:
            lines.append(f"{'...':>5} | {'...':<35} | {'...':<14} | {'...':<7} | {'...':<14} | {'...':>4}")
            continue
        actual_idx = matrix.cells.index(c) + 1
        lines.append(
            f"{actual_idx:>5} | {c.cell_id:<35} | {c.pattern:<14} | {c.demand_level:<7} | {c.policy:<14} | {c.seed:>4}"
        )
    lines.append("=" * 80)
    return "\n".join(lines)
