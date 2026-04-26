"""
WindModel: Ornstein-Uhlenbeck stochastic wind with spatial coherence.

The wind field is a (H, W, 2) float32 array of (vx, vy) vectors in m/s.
It is updated every WIND_UPDATE_INTERVAL ticks to save CPU.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
import config


class WindModel:
    def __init__(self, seed: int = 0):
        self._rng = np.random.default_rng(seed)
        H, W = config.GRID_HEIGHT, config.GRID_WIDTH

        # Initialise at base wind
        bx = config.WIND_BASE_SPEED * np.cos(config.WIND_BASE_DIR)
        by = config.WIND_BASE_SPEED * np.sin(config.WIND_BASE_DIR)
        self._field = np.stack([
            np.full((H, W), bx, dtype=np.float32),
            np.full((H, W), by, dtype=np.float32),
        ], axis=-1)  # shape (H, W, 2)

        # Scalar OU state for the bulk wind vector (drives the field mean)
        self._bulk_vx = float(bx)
        self._bulk_vy = float(by)

    # ── public API ────────────────────────────────────────────────────────────

    def step(self, dt: float) -> None:
        """Advance OU process and recompute spatially-coherent field."""
        mu_x = config.WIND_BASE_SPEED * np.cos(config.WIND_BASE_DIR)
        mu_y = config.WIND_BASE_SPEED * np.sin(config.WIND_BASE_DIR)
        theta = config.WIND_THETA
        sigma = config.WIND_GUST_SIGMA

        # OU update for bulk wind
        noise_x, noise_y = self._rng.normal(0, 1, 2)
        self._bulk_vx += theta * (mu_x - self._bulk_vx) * dt + sigma * np.sqrt(dt) * noise_x
        self._bulk_vy += theta * (mu_y - self._bulk_vy) * dt + sigma * np.sqrt(dt) * noise_y

        # Soft-cap: keep bulk speed within 1.5× the base speed
        cap = config.WIND_BASE_SPEED * 1.5 + 1.0
        bulk_speed = np.hypot(self._bulk_vx, self._bulk_vy)
        if bulk_speed > cap:
            factor = cap / bulk_speed
            self._bulk_vx *= factor
            self._bulk_vy *= factor

        # Spatially-varying perturbations
        H, W = config.GRID_HEIGHT, config.GRID_WIDTH
        noise_field_x = self._rng.normal(0, sigma * 0.4, (H, W)).astype(np.float32)
        noise_field_y = self._rng.normal(0, sigma * 0.4, (H, W)).astype(np.float32)

        # Smooth for spatial coherence
        sx = gaussian_filter(noise_field_x, sigma=config.WIND_SPATIAL_SIGMA)
        sy = gaussian_filter(noise_field_y, sigma=config.WIND_SPATIAL_SIGMA)

        self._field[:, :, 0] = self._bulk_vx + sx
        self._field[:, :, 1] = self._bulk_vy + sy

    def get_wind_at(self, col: int, row: int) -> np.ndarray:
        """Return (vx, vy) wind vector at a cell, clipped to grid bounds."""
        col = int(np.clip(col, 0, config.GRID_WIDTH - 1))
        row = int(np.clip(row, 0, config.GRID_HEIGHT - 1))
        return self._field[row, col]

    def get_wind_at_world(self, x: float, y: float) -> np.ndarray:
        col = int(x / config.CELL_SIZE)
        row = int(y / config.CELL_SIZE)
        return self.get_wind_at(col, row)

    @property
    def field(self) -> np.ndarray:
        """Full (H, W, 2) wind field — treat as read-only."""
        return self._field

    @property
    def bulk_speed(self) -> float:
        return float(np.hypot(self._bulk_vx, self._bulk_vy))

    @property
    def bulk_direction(self) -> float:
        """Radians, meteorological from."""
        return float(np.arctan2(self._bulk_vy, self._bulk_vx))
