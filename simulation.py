"""
Simulation: top-level orchestrator tying all components together.
"""

from __future__ import annotations
from dataclasses import dataclass
import time

import numpy as np

import config

from environment.grid import TerrainGrid
from environment.fire_model import FireSpreadModel
from environment.wind_model import WindModel
from environment.ember_model import EmberModel
from environment.firefighter import FirefighterZone
from agents.drone import DroneAgent
from coordination.swarm_coordinator import SwarmCoordinator
from planner.mission_planner import MissionPlanner


@dataclass
class EnvSnapshot:
    """Lightweight read-only view passed to agents each tick."""
    cell_state: np.ndarray
    burn_intensity: np.ndarray
    wind_field: np.ndarray
    firefighter_exclusions: list  # list[(x,y,radius)]


class Simulation:
    def __init__(
        self,
        visualize: bool = True,
        seed: int = 42,
        fire_start_cells: list[tuple[int, int]] | None = None,
    ):
        self.visualize = visualize
        self._seed = seed

        # ── environment ───────────────────────────────────────────────────────
        self.grid = TerrainGrid(seed=seed)
        self.wind = WindModel(seed=seed)
        self.fire = FireSpreadModel(self.grid, self.wind, seed=seed + 1)
        self.embers = EmberModel(self.grid, seed=seed + 2)
        self.firefighters = FirefighterZone(seed=seed + 3)

        # Ignite starting fire
        starts = fire_start_cells or [(100, 100), (105, 98), (98, 103)]
        for col, row in starts:
            self.grid.ignite(col, row)
            # Give initial cells some intensity
            self.grid.burn_intensity[row, col] = 0.8

        # ── agents ────────────────────────────────────────────────────────────
        self.drones: list[DroneAgent] = [
            DroneAgent(i, seed_offset=seed) for i in range(config.NUM_DRONES)
        ]

        # ── coordination / planning ───────────────────────────────────────────
        self.coordinator = SwarmCoordinator(self.drones)
        self.planner = MissionPlanner()

        # ── visualization ─────────────────────────────────────────────────────
        self.renderer = None
        if visualize:
            from visualization.renderer import SimRenderer, RenderSnapshot
            self.renderer = SimRenderer()
            self._RenderSnapshot = RenderSnapshot
            self.renderer.show()

        self.tick = 0
        self.sim_time = 0.0
        self._wall_start = time.perf_counter()

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self, max_ticks: int | None = None, realtime: bool = False) -> None:
        """Run the simulation loop."""
        while True:
            if max_ticks is not None and self.tick >= max_ticks:
                break
            if self.planner.is_mission_complete(self.grid):
                print(f"[SIM] Mission complete at t={self.sim_time:.1f}s (tick {self.tick})")
                break

            t0 = time.perf_counter()
            self.step()

            if realtime:
                elapsed = time.perf_counter() - t0
                sleep_time = config.DT - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        if self.renderer:
            import matplotlib.pyplot as plt
            plt.show(block=True)

    def step(self) -> None:
        dt = config.DT

        # ── Phase 1: wind update ──────────────────────────────────────────────
        if self.tick % config.WIND_UPDATE_INTERVAL == 0:
            self.wind.step(dt * config.WIND_UPDATE_INTERVAL)

        # ── Phase 2: build environment snapshot ───────────────────────────────
        snap = EnvSnapshot(
            cell_state=self.grid.cell_state,
            burn_intensity=self.grid.burn_intensity,
            wind_field=self.wind.field,
            firefighter_exclusions=self.firefighters.exclusion_zones,
        )

        # ── Phase 3: sense ────────────────────────────────────────────────────
        other_positions = {d.id: d.position for d in self.drones}
        for drone in self.drones:
            drone.sense(snap, other_positions)

        # ── Phase 4: coordinate (every COORD_INTERVAL ticks) ─────────────────
        if self.tick % config.COORD_INTERVAL == 0:
            targets = self.planner.get_priority_targets(
                self.grid, self.wind.field,
                self.firefighters.positions,
                n=config.NUM_DRONES,
            )
            self.coordinator.step(
                self.tick, targets, self.firefighters.positions
            )

        # ── Phase 5: drone act + suppression delivery ─────────────────────────
        for drone in self.drones:
            drone.step(dt, snap)
            drone.deliver_suppression(self.grid)
            drone.deliver_rotor_wash(self.grid)

        # ── Phase 6: fire model consumes suppression, then reset ──────────────
        self.fire.step(dt)
        self.grid.reset_suppression()  # clear accumulator after fire model used it
        drone_positions = np.array([d.position for d in self.drones]) if self.drones else None
        drone_states = [d.state for d in self.drones] if self.drones else None
        self.embers.step(dt, self.wind.field, drone_positions, drone_states)
        self.firefighters.step(dt, self.grid)

        # ── Phase 7: planner metrics ──────────────────────────────────────────
        msgs = [d.broadcast_state() for d in self.drones]
        self.planner.update_metrics(self.tick, dt, self.grid, msgs)

        # ── Phase 8: render ───────────────────────────────────────────────────
        if self.renderer and self.tick % config.RENDER_INTERVAL == 0:
            snap_r = self._build_render_snapshot(msgs)
            self.renderer.update(snap_r)

        self.tick += 1
        self.sim_time += dt

        # Progress log every 100 ticks
        if self.tick % 100 == 0:
            m = self.planner.metrics
            wall = time.perf_counter() - self._wall_start
            print(
                f"t={self.sim_time:6.1f}s | burning={m.cells_currently_burning:4d} "
                f"| embers={m.embers_detected:3d} | emitting={m.drones_emitting:3d} "
                f"| returning={m.drones_returning:3d} | wall={wall:.1f}s"
            )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_render_snapshot(self, msgs: list):
        from visualization.renderer import RenderSnapshot
        from agents.drone import DroneState
        positions = np.array([d.position for d in self.drones])
        headings  = np.array([d.heading  for d in self.drones])
        states    = [d.state for d in self.drones]
        batteries = np.array([d.battery.fraction for d in self.drones])
        emitting  = np.array([d.is_emitting() for d in self.drones])

        return RenderSnapshot(
            cell_state=self.grid.cell_state.copy(),
            burn_intensity=self.grid.burn_intensity.copy(),
            wind_field=self.wind.field.copy(),
            drone_positions=positions,
            drone_headings=headings,
            drone_states=states,
            drone_batteries=batteries,
            emitting_mask=emitting,
            firefighter_positions=self.firefighters.positions,
            metrics=self.planner.metrics,
        )
