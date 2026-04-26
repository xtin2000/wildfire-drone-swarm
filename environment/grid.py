"""
TerrainGrid: core 2D data store for the simulation.

All arrays are NumPy, indexed as [row, col] = [y, x] for consistency with
standard image convention.  Consumers should use (x, y) coordinate tuples
and call helpers to convert.
"""

import numpy as np
import config


class TerrainGrid:
    """Owns all per-cell state arrays for the terrain."""

    def __init__(self, seed: int = 42):
        rng = np.random.default_rng(seed)
        H, W = config.GRID_HEIGHT, config.GRID_WIDTH

        # Cell state (uint8 enum: UNBURNED/BURNING/EMBER/BURNED/WET)
        self.cell_state: np.ndarray = np.full((H, W), config.STATE_UNBURNED, dtype=np.uint8)

        # Fuel load kg/m² — slight spatial variation
        base = config.DEFAULT_FUEL_LOAD
        self.fuel_load: np.ndarray = (
            base + rng.normal(0, 0.05, (H, W))
        ).clip(0.1, 1.5).astype(np.float32)

        # Fuel moisture 0–1
        self.moisture: np.ndarray = np.full((H, W), config.DEFAULT_MOISTURE, dtype=np.float32)

        # Burn intensity 0–1 for currently burning cells
        self.burn_intensity: np.ndarray = np.zeros((H, W), dtype=np.float32)

        # Accumulated sound suppression energy (J-equivalent) per cell.
        # Energy accumulates across ticks under sustained acoustic forcing
        # and decays when forcing stops.
        self.suppression_applied: np.ndarray = np.zeros((H, W), dtype=np.float32)
        # Per-tick energy tracker (used to detect which cells received energy)
        self._suppression_this_tick: np.ndarray = np.zeros((H, W), dtype=np.float32)

        # Time a cell has been burning (seconds)
        self.burn_time: np.ndarray = np.zeros((H, W), dtype=np.float32)

    # ── coordinate helpers ────────────────────────────────────────────────────

    @staticmethod
    def world_to_cell(x: float, y: float) -> tuple[int, int]:
        """Convert world coordinates (m) to (col, row) cell indices."""
        col = int(x / config.CELL_SIZE)
        row = int(y / config.CELL_SIZE)
        return col, row

    @staticmethod
    def cell_to_world(col: int, row: int) -> tuple[float, float]:
        """Return the world-space centre of a cell in metres."""
        x = (col + 0.5) * config.CELL_SIZE
        y = (row + 0.5) * config.CELL_SIZE
        return x, y

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < config.GRID_WIDTH and 0 <= row < config.GRID_HEIGHT

    # ── state mutators ────────────────────────────────────────────────────────

    def ignite(self, col: int, row: int) -> None:
        if self.in_bounds(col, row) and self.cell_state[row, col] == config.STATE_UNBURNED:
            self.cell_state[row, col] = config.STATE_BURNING
            self.burn_intensity[row, col] = 0.3  # nascent flame
            self.burn_time[row, col] = 0.0

    def extinguish(self, col: int, row: int) -> None:
        if self.in_bounds(col, row):
            self.cell_state[row, col] = config.STATE_BURNED
            self.burn_intensity[row, col] = 0.0
            self.suppression_applied[row, col] = 0.0
            self._suppression_this_tick[row, col] = 0.0

    def apply_suppression(self, col: int, row: int, energy: float) -> None:
        """Accumulate suppression energy on a cell."""
        if self.in_bounds(col, row):
            self.suppression_applied[row, col] += energy
            self._suppression_this_tick[row, col] += energy

    def wet_cell(self, col: int, row: int) -> None:
        """Water spray from firefighters fully saturates moisture."""
        if self.in_bounds(col, row):
            self.moisture[row, col] = 1.0
            if self.cell_state[row, col] == config.STATE_UNBURNED:
                self.cell_state[row, col] = config.STATE_WET

    def reset_suppression(self) -> None:
        """Decay suppression on cells that received no new energy this tick.

        Cells receiving active acoustic forcing accumulate energy across ticks.
        Cells NOT receiving energy this tick lose accumulated energy (heat
        re-establishes once acoustic forcing stops).
        """
        # Track which cells received energy this tick
        received = self._suppression_this_tick > 0
        # Cells that didn't receive energy: rapid decay (fire re-intensifies)
        self.suppression_applied[~received] *= 0.5
        # Reset the per-tick tracker
        self._suppression_this_tick[:] = 0.0

    # ── queries ───────────────────────────────────────────────────────────────

    def get_burning_cells(self) -> list[tuple[int, int]]:
        """Return list of (col, row) for all burning cells."""
        rows, cols = np.where(self.cell_state == config.STATE_BURNING)
        return list(zip(cols.tolist(), rows.tolist()))

    def get_ember_cells(self) -> list[tuple[int, int]]:
        rows, cols = np.where(self.cell_state == config.STATE_EMBER)
        return list(zip(cols.tolist(), rows.tolist()))

    def burning_mask(self) -> np.ndarray:
        return self.cell_state == config.STATE_BURNING

    def suppressible_mask(self) -> np.ndarray:
        """Cells that are either BURNING or EMBER (targetable by sound)."""
        return (self.cell_state == config.STATE_BURNING) | (self.cell_state == config.STATE_EMBER)
