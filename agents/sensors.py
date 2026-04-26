"""
SensorSuite: thermal camera, anemometer, proximity sensor (all noisy).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import config
from physics.geometry import wrap_angle


@dataclass
class SensorReading:
    """Aggregated sensor output for one tick."""
    # Thermal: list of (col, row, intensity) for detected burning cells
    detected_fires: list[tuple[int, int, float]] = field(default_factory=list)
    # Local wind vector (vx, vy) with noise
    wind: np.ndarray = field(default_factory=lambda: np.zeros(2))
    # IDs of nearby drones (within proximity range)
    nearby_drone_ids: list[int] = field(default_factory=list)
    # Nearby drone positions: drone_id -> np.ndarray(3,)
    nearby_drone_positions: dict[int, np.ndarray] = field(default_factory=dict)


class SensorSuite:
    def __init__(self, rng: np.random.Generator):
        self._rng = rng

    def sense(
        self,
        drone_id: int,
        drone_pos: np.ndarray,       # (3,) world coords
        drone_heading: float,        # radians
        env_snapshot: "EnvSnapshot",
        other_drones: dict[int, np.ndarray],  # id -> pos (3,)
    ) -> SensorReading:
        reading = SensorReading()
        reading.detected_fires = self._thermal(drone_pos, drone_heading, env_snapshot)
        reading.wind = self._anemometer(drone_pos, env_snapshot)
        nearby_ids, nearby_pos = self._proximity(drone_id, drone_pos, other_drones)
        reading.nearby_drone_ids = nearby_ids
        reading.nearby_drone_positions = nearby_pos
        return reading

    # ── sub-sensors ───────────────────────────────────────────────────────────

    def _thermal(
        self,
        pos: np.ndarray,
        heading: float,
        snap: "EnvSnapshot",
    ) -> list[tuple[int, int, float]]:
        """Detect burning/ember cells within FOV cone."""
        fov_half = np.radians(config.THERMAL_FOV_DEG)
        max_r = config.THERMAL_RANGE / config.CELL_SIZE  # in cells

        col0 = int(pos[0] / config.CELL_SIZE)
        row0 = int(pos[1] / config.CELL_SIZE)
        r_int = int(max_r) + 1

        detected = []
        for dc in range(-r_int, r_int + 1):
            for dr in range(-r_int, r_int + 1):
                col = col0 + dc
                row = row0 + dr
                if not (0 <= col < config.GRID_WIDTH and 0 <= row < config.GRID_HEIGHT):
                    continue
                dist_cells = np.hypot(dc, dr)
                if dist_cells > max_r:
                    continue
                state = snap.cell_state[row, col]
                if state not in (config.STATE_BURNING, config.STATE_EMBER):
                    continue
                # Check FOV angle
                angle_to = np.arctan2(dr, dc)
                angle_diff = abs(wrap_angle(angle_to - heading))
                if angle_diff > fov_half:
                    continue
                intensity = float(snap.burn_intensity[row, col])
                intensity += self._rng.normal(0, config.THERMAL_NOISE_STD)
                intensity = float(np.clip(intensity, 0.0, 1.0))
                detected.append((col, row, intensity))
        return detected

    def _anemometer(self, pos: np.ndarray, snap: "EnvSnapshot") -> np.ndarray:
        col = int(np.clip(pos[0] / config.CELL_SIZE, 0, config.GRID_WIDTH - 1))
        row = int(np.clip(pos[1] / config.CELL_SIZE, 0, config.GRID_HEIGHT - 1))
        true_wind = snap.wind_field[row, col].copy()
        noise = self._rng.normal(0, config.ANEM_NOISE_STD, 2).astype(np.float32)
        return true_wind + noise

    def _proximity(
        self,
        my_id: int,
        pos: np.ndarray,
        others: dict[int, np.ndarray],
    ) -> tuple[list[int], dict[int, np.ndarray]]:
        ids = []
        positions = {}
        for oid, opos in others.items():
            if oid == my_id:
                continue
            if np.linalg.norm(opos - pos) <= config.PROX_RANGE:
                ids.append(oid)
                positions[oid] = opos
        return ids, positions
