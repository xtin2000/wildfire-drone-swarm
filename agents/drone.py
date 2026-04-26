"""
DroneAgent: the central per-drone agent with state machine.

States: IDLE → TRANSIT → HOVERING → EMITTING → RETURNING → CHARGING
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
import numpy as np

import config
from agents.battery import BatteryModel
from agents.flight_controller import FlightController
from agents.sound_emitter import SoundEmitter
from agents.sensors import SensorSuite, SensorReading
from physics.flight_dynamics import stability_factor
from environment.grid import TerrainGrid


class DroneState(Enum):
    IDLE      = auto()
    TRANSIT   = auto()
    HOVERING  = auto()
    EMITTING  = auto()
    RETURNING = auto()
    CHARGING  = auto()


@dataclass
class Task:
    """A fire-suppression task assigned by the coordinator."""
    task_id: int
    target_cell: tuple[int, int]   # (col, row)
    urgency: float = 1.0


@dataclass
class DroneMessage:
    """State broadcast for coordinator consumption."""
    drone_id: int
    position: np.ndarray
    velocity: np.ndarray
    state: DroneState
    battery_fraction: float
    task_id: int | None
    stability: float


class DroneAgent:
    def __init__(self, drone_id: int, seed_offset: int = 0):
        self.id = drone_id
        self.state = DroneState.IDLE

        # Spawn near base with slight jitter
        rng = np.random.default_rng(drone_id + seed_offset)
        bx, by, bz = config.BASE_POSITION
        self.position = np.array([
            bx + rng.uniform(-5, 5),
            by + rng.uniform(-5, 5),
            0.0,
        ], dtype=np.float64)
        self.velocity = np.zeros(3)
        self.heading = 0.0  # radians (yaw)

        self.task: Task | None = None
        self._target_pos: np.ndarray = np.array(config.BASE_POSITION, dtype=np.float64)

        self.battery = BatteryModel()
        self.controller = FlightController()
        self.emitter = SoundEmitter()
        self.sensors = SensorSuite(np.random.default_rng(drone_id * 1000 + seed_offset))

        self._last_sensor_reading: SensorReading | None = None
        self._hover_timer = 0.0   # seconds spent hovering at target
        self._stability = 1.0

    # ── public API ────────────────────────────────────────────────────────────

    def assign_task(self, task: Task | None) -> None:
        """Called by coordinator to assign or clear a task."""
        if task is None:
            self.task = None
            if self.state in (DroneState.EMITTING, DroneState.HOVERING, DroneState.TRANSIT):
                self.state = DroneState.IDLE
                self.emitter.stop()
        else:
            if self.task is None or self.task.task_id != task.task_id:
                # Don't interrupt a drone that is actively emitting on a
                # burning cell — let it finish suppression before reassigning.
                if self.state == DroneState.EMITTING:
                    return
                self.task = task
                if self.state not in (DroneState.RETURNING, DroneState.CHARGING):
                    self.state = DroneState.TRANSIT
                    self.emitter.stop()
                    self.controller.reset()

    def sense(self, env_snapshot, other_drones: dict[int, np.ndarray]) -> SensorReading:
        reading = self.sensors.sense(
            self.id, self.position, self.heading, env_snapshot, other_drones
        )
        self._last_sensor_reading = reading
        return reading

    def step(self, dt: float, env_snapshot, coordinator_velocity_hint: np.ndarray | None = None) -> None:
        """Advance drone by one tick."""
        wind = self._last_sensor_reading.wind if self._last_sensor_reading else np.zeros(2)
        wind3 = np.array([wind[0], wind[1], 0.0])
        wind_speed = float(np.linalg.norm(wind))
        self._stability = stability_factor(wind_speed)

        # Emergency return: wind too strong
        if wind_speed > config.DRONE_MAX_WIND and self.state not in (
            DroneState.RETURNING, DroneState.CHARGING
        ):
            self._start_return()

        # Battery low: return to base
        if self.battery.is_low and self.state not in (DroneState.RETURNING, DroneState.CHARGING):
            self._start_return()

        self._run_state_machine(dt, wind_speed, env_snapshot)
        self._move(dt, wind3)
        self.battery.consume(float(np.linalg.norm(self.velocity)), self.emitter.is_active, dt)

    def deliver_suppression(self, grid: TerrainGrid) -> None:
        """Called after step() to deposit energy into the grid."""
        if not self.emitter.is_active or self.task is None:
            return
        wind = self._last_sensor_reading.wind if self._last_sensor_reading else np.zeros(2)
        target_world = self._task_world_pos()
        energy = self.emitter.compute_delivered_energy(
            self.position, self.heading, wind, self._stability, config.DT
        )
        col, row = self.task.target_cell
        grid.apply_suppression(col, row, energy)

    def broadcast_state(self) -> DroneMessage:
        return DroneMessage(
            drone_id=self.id,
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            state=self.state,
            battery_fraction=self.battery.fraction,
            task_id=self.task.task_id if self.task else None,
            stability=self._stability,
        )

    def is_emitting(self) -> bool:
        return self.emitter.is_active

    # ── state machine ─────────────────────────────────────────────────────────

    def _run_state_machine(self, dt: float, wind_speed: float, env_snapshot) -> None:
        state = self.state

        if state == DroneState.IDLE:
            self._target_pos = np.array(config.BASE_POSITION, dtype=float)
            self._target_pos[2] = config.DRONE_CRUISE_ALT * 0.3

        elif state == DroneState.TRANSIT:
            if self.task is None:
                self.state = DroneState.IDLE
                return
            self._target_pos = self._safe_hover_pos()
            dist = np.linalg.norm(self.position - self._target_pos)
            if dist < 3.0:
                self.state = DroneState.HOVERING
                self._hover_timer = 0.0

        elif state == DroneState.HOVERING:
            self._target_pos = self._safe_hover_pos()
            self._hover_timer += dt
            if self._hover_timer > 1.0:  # 1 second stabilisation
                self.state = DroneState.EMITTING
                tw = self._task_world_pos()
                self.emitter.start(tw)

        elif state == DroneState.EMITTING:
            if self.task is None:
                self.emitter.stop()
                self.state = DroneState.IDLE
                return
            # Check if target cell is still burning/ember — stop if extinguished
            col, row = self.task.target_cell
            cell = env_snapshot.cell_state[row, col]
            if cell not in (config.STATE_BURNING, config.STATE_EMBER):
                self.emitter.stop()
                self.task = None
                self.state = DroneState.IDLE
                return
            self._target_pos = self._safe_hover_pos()
            self.emitter.update_target(self._task_world_pos())
            # Update heading toward target
            diff = self._task_world_pos() - self.position
            if np.linalg.norm(diff[:2]) > 0.1:
                self.heading = float(np.arctan2(diff[1], diff[0]))

        elif state == DroneState.RETURNING:
            base = np.array(config.BASE_POSITION, dtype=float)
            self._target_pos = base
            dist = np.linalg.norm(self.position[:2] - base[:2])
            if dist < 3.0:
                self.state = DroneState.CHARGING
                self.position[2] = 0.0

        elif state == DroneState.CHARGING:
            self.battery.charge(dt)
            if self.battery.is_full:
                self.state = DroneState.IDLE

    def _move(self, dt: float, wind3: np.ndarray) -> None:
        """Integrate position using PID-commanded velocity."""
        if self.state == DroneState.CHARGING:
            self.velocity = np.zeros(3)
            return

        cmd_vel = self.controller.compute(
            self._target_pos, self.position, self.velocity, wind3, dt
        )
        self.velocity = cmd_vel
        self.position += self.velocity * dt

        # Clamp to ground and grid bounds
        self.position[2] = max(0.0, self.position[2])
        self.position[0] = np.clip(self.position[0], 0, config.GRID_WIDTH * config.CELL_SIZE)
        self.position[1] = np.clip(self.position[1], 0, config.GRID_HEIGHT * config.CELL_SIZE)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _task_world_pos(self) -> np.ndarray:
        """World coords of target cell centre."""
        if self.task is None:
            return np.array(config.BASE_POSITION, dtype=float)
        col, row = self.task.target_cell
        from environment.grid import TerrainGrid
        x, y = TerrainGrid.cell_to_world(col, row)
        return np.array([x, y, 0.0])

    def _safe_hover_pos(self) -> np.ndarray:
        """
        Hover position: cruise altitude, clamped to safe distance range from fire.
        """
        tw = self._task_world_pos()
        diff = tw[:2] - self.position[:2]
        dist = np.linalg.norm(diff)

        # Target distance from fire: midpoint of safe range
        target_dist = (config.SAFE_FIRE_DISTANCE + config.MAX_FIRE_DISTANCE) / 2.0
        if dist > 1e-3:
            hover_xy = tw[:2] - (diff / dist) * target_dist
        else:
            hover_xy = self.position[:2]

        return np.array([hover_xy[0], hover_xy[1], config.DRONE_CRUISE_ALT])

    def _start_return(self) -> None:
        self.emitter.stop()
        self.state = DroneState.RETURNING
        self.controller.reset()
