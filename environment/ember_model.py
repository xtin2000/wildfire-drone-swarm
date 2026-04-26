"""
EmberModel: ballistic ember trajectories with wind drift and secondary ignition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import config
from environment.grid import TerrainGrid


@dataclass
class Ember:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    intensity: float
    age: float = 0.0

    @property
    def pos(self) -> tuple[float, float]:
        return self.x, self.y


G = 9.81  # m/s²


class EmberModel:
    def __init__(self, grid: TerrainGrid, seed: int = 2):
        self.grid = grid
        self._rng = np.random.default_rng(seed)
        self._embers: list[Ember] = []

    def step(self, dt: float, wind_field: np.ndarray) -> None:
        """Advance all embers and handle landings/new lofting."""
        self._loft_new(wind_field)
        self._advance(dt, wind_field)
        self._check_landings()

    # ── public queries ────────────────────────────────────────────────────────

    @property
    def active_embers(self) -> list[Ember]:
        return self._embers

    # ── private ───────────────────────────────────────────────────────────────

    def _loft_new(self, wind_field: np.ndarray) -> None:
        """Probabilistically loft embers from intense burning cells."""
        burning_cells = self.grid.get_burning_cells()
        for col, row in burning_cells:
            if self._rng.random() > config.EMBER_LOFT_PROB:
                continue
            intensity = float(self.grid.burn_intensity[row, col])
            if intensity < 0.5:
                continue  # only intense fire lofts embers

            wx, wy = self.grid.cell_to_world(col, row)
            wind = wind_field[row, col]
            vz0 = config.EMBER_V0_Z_SCALE * intensity * self._rng.uniform(0.8, 1.2)
            # Initial horizontal velocity: some wind-following randomness
            vx0 = wind[0] * self._rng.uniform(0.3, 0.7)
            vy0 = wind[1] * self._rng.uniform(0.3, 0.7)

            self._embers.append(Ember(
                x=wx, y=wy, z=2.0,
                vx=vx0, vy=vy0, vz=vz0,
                intensity=intensity,
            ))

    def _advance(self, dt: float, wind_field: np.ndarray) -> None:
        """Euler integration with wind drag and gravity."""
        alive = []
        for e in self._embers:
            e.age += dt
            if e.age > config.EMBER_MAX_AGE:
                continue

            # Wind at current cell
            col = int(np.clip(e.x / config.CELL_SIZE, 0, config.GRID_WIDTH - 1))
            row = int(np.clip(e.y / config.CELL_SIZE, 0, config.GRID_HEIGHT - 1))
            wind = wind_field[row, col]

            # Drag toward wind velocity
            ax = (wind[0] - e.vx) * config.EMBER_DRAG_COEFF
            ay = (wind[1] - e.vy) * config.EMBER_DRAG_COEFF
            az = -G + (-e.vz) * config.EMBER_DRAG_COEFF * 0.5  # gravity + drag

            e.vx += ax * dt
            e.vy += ay * dt
            e.vz += az * dt
            e.x += e.vx * dt
            e.y += e.vy * dt
            e.z += e.vz * dt

            if e.z <= 0.0:
                e.z = 0.0
                self._handle_landing(e)
                continue  # consumed on landing

            # Remove if out of bounds
            if not (0 <= e.x <= config.GRID_WIDTH * config.CELL_SIZE and
                    0 <= e.y <= config.GRID_HEIGHT * config.CELL_SIZE):
                continue

            alive.append(e)

        self._embers = alive

    def _handle_landing(self, e: Ember) -> None:
        """Probabilistic ignition at ember landing site."""
        col = int(np.clip(e.x / config.CELL_SIZE, 0, config.GRID_WIDTH - 1))
        row = int(np.clip(e.y / config.CELL_SIZE, 0, config.GRID_HEIGHT - 1))

        if self.grid.cell_state[row, col] != config.STATE_UNBURNED:
            return
        moisture = float(self.grid.moisture[row, col])
        p_ignite = config.EMBER_IGNITE_P_BASE * e.intensity * (1.0 - moisture)
        if self._rng.random() < p_ignite:
            self.grid.ignite(col, row)
            # Mark as ember cell (small/nascent)
            self.grid.cell_state[row, col] = config.STATE_EMBER
            self.grid.burn_intensity[row, col] = 0.1

    def _check_landings(self) -> None:
        """Upgrade ember cells that have grown to full burning."""
        ember_cells = self.grid.get_ember_cells()
        for col, row in ember_cells:
            intensity = self.grid.burn_intensity[row, col]
            if intensity > 0.35:
                self.grid.cell_state[row, col] = config.STATE_BURNING
