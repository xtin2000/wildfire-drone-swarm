"""
FireSpreadModel: probabilistic cellular automaton fire spread.

Uses a Rothermel-inspired wind factor for directional spread probability.
All spreading logic is vectorised with NumPy — no Python loops over cells.
"""

import numpy as np
import config
from environment.grid import TerrainGrid
from environment.wind_model import WindModel


# 8-neighbourhood: (dcol, drow, unit_direction_vector)
_NEIGHBORS = np.array([
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),           (1,  0),
    (-1,  1), (0,  1), (1,  1),
], dtype=np.int32)  # shape (8, 2): [dcol, drow]

# Unit vectors from source to neighbour (same order as _NEIGHBORS)
_NEIGHBOR_DIRS = np.array([
    [-1, -1], [0, -1], [1, -1],
    [-1,  0],          [1,  0],
    [-1,  1], [0,  1], [1,  1],
], dtype=np.float32)
_NEIGHBOR_DIRS /= np.linalg.norm(_NEIGHBOR_DIRS, axis=1, keepdims=True)  # normalise


class FireSpreadModel:
    def __init__(self, grid: TerrainGrid, wind_model: WindModel, seed: int = 1):
        self.grid = grid
        self.wind = wind_model
        self._rng = np.random.default_rng(seed)

        H, W = config.GRID_HEIGHT, config.GRID_WIDTH
        # Time-to-ignite countdown: NaN = not queued; >=0 = burning countdown
        self._ignition_timer: np.ndarray = np.full((H, W), np.nan, dtype=np.float32)

    # ── public ────────────────────────────────────────────────────────────────

    def step(self, dt: float) -> None:
        # Check suppression first (against current intensity before any growth)
        self._apply_suppression()
        self._grow_flames(dt)
        self._spread(dt)
        self._age_burned_cells(dt)

    # ── private ───────────────────────────────────────────────────────────────

    def _grow_flames(self, dt: float) -> None:
        """Ramp up burn intensity on burning cells over time."""
        burning = self.grid.burning_mask()
        # Intensity grows logistically toward 1
        bi = self.grid.burn_intensity
        bi[burning] += 0.3 * dt * (1.0 - bi[burning])
        bi[burning] = np.clip(bi[burning], 0.0, 1.0)
        self.grid.burn_time[burning] += dt

    def _spread(self, dt: float) -> None:
        """Vectorised spread from burning cells to 8-neighbours."""
        grid = self.grid
        H, W = config.GRID_HEIGHT, config.GRID_WIDTH
        burning_mask = grid.burning_mask()

        if not np.any(burning_mask):
            return

        # Mean wind field (reused for all neighbours)
        wf = self.wind.field  # (H, W, 2)

        # Process each neighbour direction
        for k, (dcol, drow) in enumerate(_NEIGHBORS):
            direction = _NEIGHBOR_DIRS[k]  # (2,) unit vector: [dx, dy] toward neighbour

            # Roll the burning mask to get "which source cells can spread to neighbour k"
            # Burning source is at (col, row); neighbour is at (col+dcol, row+drow)
            # To find sources for each cell, shift in OPPOSITE direction
            src_mask = np.roll(np.roll(burning_mask, -drow, axis=0), -dcol, axis=1)

            # Wind factor: exp(k_w * dot(wind_at_source, direction_to_neighbour))
            #   direction = (dcol, drow) normalised
            dot = wf[:, :, 0] * direction[0] + wf[:, :, 1] * direction[1]
            wind_factor = np.exp(config.FIRE_K_WIND * dot)

            # Fuel factor at the target cell
            dry_factor = grid.fuel_load * (1.0 - np.clip(grid.moisture / config.MOISTURE_EXTINCTION, 0, 1))

            # Spread probability per tick
            p_spread = config.FIRE_P_BASE * wind_factor * dry_factor

            # Draw: only unburned+dry cells can ignite
            can_ignite = (grid.cell_state == config.STATE_UNBURNED) & (grid.moisture < config.MOISTURE_EXTINCTION)
            roll = self._rng.random((H, W), dtype=np.float32)
            new_ignitions = src_mask & can_ignite & (roll < p_spread)

            # Ignite new cells (use grid method for proper initialisation)
            rows, cols = np.where(new_ignitions)
            for r, c in zip(rows, cols):
                grid.ignite(int(c), int(r))

    def _apply_suppression(self) -> None:
        """Check accumulated suppression energy and extinguish qualifying cells.

        Operates on both BURNING cells (full flames) and EMBER cells (small,
        nascent ignitions). Embers are easier to extinguish: their effective
        threshold uses a floor on intensity since real intensity is ~0.1.
        """
        grid = self.grid
        burning = grid.burning_mask()
        ember = grid.cell_state == config.STATE_EMBER

        # Threshold for burning cells: scales with intensity (harder to kill hotter fire).
        # Threshold for ember cells: small floor so embers can be extinguished cleanly
        # by even modest suppression energy (consistent with §4.13 — embers are easy
        # to disrupt with rotor wash or acoustic forcing).
        threshold = config.FIRE_SUPPRESSION_THRESHOLD_BASE * grid.burn_intensity
        # Use intensity floor of 0.2 for embers (so threshold is at least 6 J at
        # FIRE_SUPPRESSION_THRESHOLD_BASE=30) — easier than full burning cells
        ember_threshold_floor = config.FIRE_SUPPRESSION_THRESHOLD_BASE * 0.2
        threshold_eff = np.where(ember, ember_threshold_floor, threshold)

        suppressible = burning | ember

        # Cells with enough accumulated energy get extinguished
        to_extinguish = suppressible & (grid.suppression_applied >= threshold_eff)
        rows, cols = np.where(to_extinguish)
        for r, c in zip(rows, cols):
            grid.extinguish(int(c), int(r))

        # Partial intensity reduction on burning cells that received some energy
        # but not enough to extinguish (cooling effect of sustained forcing)
        partial = burning & (grid.suppression_applied > 0) & ~to_extinguish
        with np.errstate(divide="ignore", invalid="ignore"):
            reduction = np.where(
                threshold > 0,
                grid.suppression_applied / np.maximum(threshold, 1e-9),
                0.0,
            ).clip(0, 0.3)
        grid.burn_intensity[partial] -= reduction[partial]

    def _age_burned_cells(self, dt: float) -> None:
        """Cells that have burned long enough transition to BURNED (ash)."""
        long_burning = (
            self.grid.cell_state == config.STATE_BURNING
        ) & (self.grid.burn_time >= config.FIRE_BURN_TIME)
        rows, cols = np.where(long_burning)
        for r, c in zip(rows, cols):
            self.grid.extinguish(int(c), int(r))
