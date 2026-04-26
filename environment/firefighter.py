"""
FirefighterZone: firefighter agents with water spray and exclusion zones.
"""

from __future__ import annotations
import numpy as np
import config
from environment.grid import TerrainGrid


class FirefighterZone:
    def __init__(self, positions: list[tuple[float, float]] | None = None, seed: int = 3):
        self._rng = np.random.default_rng(seed)
        n = config.NUM_FIREFIGHTERS

        if positions:
            self._positions = [np.array([x, y], dtype=np.float64) for x, y in positions]
        else:
            # Default: spread along one edge of the grid (western flank)
            W = config.GRID_WIDTH * config.CELL_SIZE
            H = config.GRID_HEIGHT * config.CELL_SIZE
            self._positions = [
                np.array([
                    self._rng.uniform(0.1 * W, 0.3 * W),
                    self._rng.uniform(0.1 * H, 0.9 * H),
                ], dtype=np.float64)
                for _ in range(n)
            ]

        # Each firefighter has a movement goal (they drift toward active fire)
        self._goals: list[np.ndarray] = [p.copy() for p in self._positions]

    def step(self, dt: float, grid: TerrainGrid) -> None:
        """Move firefighters toward fire and apply water spray."""
        burning = grid.get_burning_cells()
        for i, pos in enumerate(self._positions):
            # Update goal: move toward nearest burning cell
            if burning:
                nearest = min(
                    burning,
                    key=lambda c: np.hypot(
                        c[0] * config.CELL_SIZE - pos[0],
                        c[1] * config.CELL_SIZE - pos[1],
                    )
                )
                nx, ny = grid.cell_to_world(nearest[0], nearest[1])
                self._goals[i] = np.array([nx, ny]) + self._rng.normal(0, 5, 2)

            # Move toward goal
            goal = self._goals[i]
            diff = goal - pos
            dist = np.linalg.norm(diff)
            if dist > config.FIREFIGHTER_WATER_RADIUS:
                pos += diff / dist * config.FIREFIGHTER_SPEED * dt
            self._positions[i] = pos

            # Apply water spray to nearby cells
            col0 = int(pos[0] / config.CELL_SIZE)
            row0 = int(pos[1] / config.CELL_SIZE)
            r_cells = int(config.FIREFIGHTER_WATER_RADIUS / config.CELL_SIZE) + 1
            for dc in range(-r_cells, r_cells + 1):
                for dr in range(-r_cells, r_cells + 1):
                    col = col0 + dc
                    row = row0 + dr
                    if not grid.in_bounds(col, row):
                        continue
                    wx, wy = grid.cell_to_world(col, row)
                    if np.hypot(wx - pos[0], wy - pos[1]) <= config.FIREFIGHTER_WATER_RADIUS:
                        grid.wet_cell(col, row)

    @property
    def positions(self) -> list[tuple[float, float]]:
        """World-space (x, y) positions."""
        return [(float(p[0]), float(p[1])) for p in self._positions]

    @property
    def exclusion_zones(self) -> list[tuple[float, float, float]]:
        """List of (cx, cy, radius) exclusion circles."""
        return [(float(p[0]), float(p[1]), config.FIREFIGHTER_EXCL_RADIUS)
                for p in self._positions]
