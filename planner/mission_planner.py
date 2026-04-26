"""
MissionPlanner: top-level fire suppression goal management and metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import config
from environment.grid import TerrainGrid
from coordination.task_allocator import Target
from planner.target_prioritizer import build_targets


@dataclass
class SimMetrics:
    tick: int = 0
    sim_time: float = 0.0
    cells_burned: int = 0
    cells_suppressed: int = 0
    cells_currently_burning: int = 0
    embers_detected: int = 0
    drones_emitting: int = 0
    drones_returning: int = 0


class MissionPlanner:
    def __init__(self):
        self._active_targets: list[Target] = []
        self.metrics = SimMetrics()
        self._suppressed_prev = 0

    def get_priority_targets(
        self,
        grid: TerrainGrid,
        wind_field: np.ndarray,
        firefighter_positions: list[tuple[float, float]],
        n: int = 100,
    ) -> list[Target]:
        """Build and return the top-N prioritised target list."""
        self._active_targets = build_targets(grid, wind_field, firefighter_positions, max_targets=n)
        return self._active_targets

    def update_metrics(
        self,
        tick: int,
        dt: float,
        grid: TerrainGrid,
        drone_states: list,  # list[DroneMessage]
    ) -> SimMetrics:
        from agents.drone import DroneState

        m = self.metrics
        m.tick = tick
        m.sim_time += dt

        state_arr = grid.cell_state
        m.cells_burned = int(np.sum(state_arr == config.STATE_BURNED))
        m.cells_currently_burning = int(np.sum(state_arr == config.STATE_BURNING))
        m.embers_detected = int(np.sum(state_arr == config.STATE_EMBER))

        m.drones_emitting = sum(
            1 for d in drone_states if d.state == DroneState.EMITTING
        )
        m.drones_returning = sum(
            1 for d in drone_states if d.state in (DroneState.RETURNING, DroneState.CHARGING)
        )

        return m

    @property
    def active_targets(self) -> list[Target]:
        return self._active_targets

    def is_mission_complete(self, grid: TerrainGrid) -> bool:
        """Mission ends when no burning or ember cells remain."""
        return (
            len(grid.get_burning_cells()) == 0
            and len(grid.get_ember_cells()) == 0
        )
