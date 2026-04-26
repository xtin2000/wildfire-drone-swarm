"""
TargetPrioritizer: scores fire/ember cells for mission prioritisation.

Higher score = more urgent to suppress.
"""

from __future__ import annotations
from itertools import count

import numpy as np

import config
from environment.grid import TerrainGrid
from coordination.task_allocator import Target


_task_id_counter = count(1)


def _next_task_id() -> int:
    return next(_task_id_counter)


def build_targets(
    grid: TerrainGrid,
    wind_field: np.ndarray,
    firefighter_positions: list[tuple[float, float]],
    max_targets: int = 200,
) -> list[Target]:
    """
    Build a prioritised list of targets from the current grid state.
    Only returns up to max_targets most urgent targets.
    """
    cells = grid.get_ember_cells() + grid.get_burning_cells()
    if not cells:
        return []

    scored: list[tuple[float, tuple[int, int]]] = []

    for col, row in cells:
        score = _score_cell(col, row, grid, wind_field, firefighter_positions)
        scored.append((score, (col, row)))

    # Sort descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    scored = scored[:max_targets]

    targets = []
    for urgency, (col, row) in scored:
        wx, wy = grid.cell_to_world(col, row)
        targets.append(Target(
            task_id=_next_task_id(),
            cell=(col, row),
            urgency=urgency,
            world_pos=np.array([wx, wy]),
        ))
    return targets


def _score_cell(
    col: int,
    row: int,
    grid: TerrainGrid,
    wind_field: np.ndarray,
    ff_positions: list[tuple[float, float]],
) -> float:
    state = grid.cell_state[row, col]
    intensity = float(grid.burn_intensity[row, col])

    # Base: embers are top priority (small and suppressible)
    is_ember = (state == config.STATE_EMBER)
    score = 10.0 * is_ember

    # Nascent fires (low intensity) are easier and more important to kill early
    score += 5.0 * (1.0 - intensity) if not is_ember else 0.0

    # Expansion pressure: count burning neighbours (fires about to spread)
    n_burning_neighbors = _count_burning_neighbors(col, row, grid)
    score += 2.0 * n_burning_neighbors

    # Proximity to firefighters (threat to personnel)
    min_ff_dist = _min_firefighter_dist(col, row, grid, ff_positions)
    if min_ff_dist > 0:
        score += 3.0 / min_ff_dist

    # Wind-aligned cells spread faster → higher priority
    wind = wind_field[row, col]
    wind_speed = float(np.linalg.norm(wind))
    score += 0.5 * wind_speed

    return score


def _count_burning_neighbors(col: int, row: int, grid: TerrainGrid) -> int:
    count = 0
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            c2, r2 = col + dc, row + dr
            if grid.in_bounds(c2, r2) and grid.cell_state[r2, c2] == config.STATE_BURNING:
                count += 1
    return count


def _min_firefighter_dist(
    col: int,
    row: int,
    grid: TerrainGrid,
    ff_positions: list[tuple[float, float]],
) -> float:
    if not ff_positions:
        return float("inf")
    wx, wy = grid.cell_to_world(col, row)
    return min(np.hypot(fx - wx, fy - wy) for fx, fy in ff_positions)
