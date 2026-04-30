"""
EmberModel: ballistic ember trajectories with wind drift and secondary ignition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import config
from environment.grid import TerrainGrid
from physics.aerodynamics import (
    rotor_wash_velocity,
    rotor_wash_footprint_radius,
    rotor_wash_radial_factor,
)


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

    def step(
        self,
        dt: float,
        wind_field: np.ndarray,
        drone_positions: np.ndarray | None = None,
        drone_states: list | None = None,
    ) -> None:
        """Advance all embers and handle landings/new lofting.

        If drone_positions and drone_states are provided and rotor wash is
        enabled, airborne embers below hovering/emitting drones receive an
        additional downward acceleration.
        """
        self._loft_new(wind_field)
        self._advance(dt, wind_field, drone_positions, drone_states)
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

    def _advance(
        self,
        dt: float,
        wind_field: np.ndarray,
        drone_positions: np.ndarray | None,
        drone_states: list | None,
    ) -> None:
        """Euler integration with wind drag, gravity, and rotor downwash."""
        # Pre-filter drones that can produce rotor wash (hovering/emitting)
        wash_drones = self._collect_wash_drones(drone_positions, drone_states)

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

            # Rotor downwash from any drone hovering above this ember
            if wash_drones is not None:
                az -= self._rotor_downwash_accel(e, wash_drones)

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

    def _collect_wash_drones(self, positions, states):
        """Return list of (x, y, z) positions for drones currently producing rotor wash."""
        if not config.ROTOR_WASH_ENABLED or positions is None or states is None:
            return None
        if not config.ROTOR_WASH_EMBER_DRAG_ENABLED:
            return None  # ember-drag isolation ablation: ground suppression still applies
        # Avoid circular import: refer to state by name
        active_state_names = {"HOVERING", "EMITTING"}
        wash = []
        for pos, st in zip(positions, states):
            if st.name in active_state_names:
                wash.append(pos)
        return wash if wash else None

    @staticmethod
    def _rotor_downwash_accel(ember: "Ember", wash_drones: list) -> float:
        """Total downward acceleration on an ember from all rotor wash columns above it."""
        accel = 0.0
        for drone_pos in wash_drones:
            altitude_above = float(drone_pos[2]) - ember.z
            if altitude_above <= 0:
                continue  # drone is below or at ember height; no downwash here
            lateral = float(np.hypot(
                drone_pos[0] - ember.x,
                drone_pos[1] - ember.y,
            ))
            radius = rotor_wash_footprint_radius(altitude_above)
            if lateral >= radius:
                continue
            radial = rotor_wash_radial_factor(lateral, altitude_above)
            v_wash = rotor_wash_velocity(altitude_above)
            # Acceleration scales with wash velocity and radial position
            strength = v_wash / max(1.0, rotor_wash_velocity(0.1))
            accel += config.ROTOR_WASH_EMBER_DRAG * strength * radial
        return accel

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
