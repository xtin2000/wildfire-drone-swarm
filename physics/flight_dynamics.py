"""
Point-mass drone flight dynamics (simplified quadrotor).
"""

import numpy as np
import config

G = 9.81  # m/s²


def drag_force(velocity: np.ndarray) -> np.ndarray:
    """Aerodynamic drag vector opposing motion (N)."""
    speed = np.linalg.norm(velocity)
    if speed < 1e-6:
        return np.zeros(3)
    return -0.5 * config.AIR_DENSITY * config.DRONE_CD * config.DRONE_FRONTAL_AREA * speed ** 2 * (velocity / speed)


def wind_force(wind_velocity: np.ndarray, drone_velocity: np.ndarray) -> np.ndarray:
    """Wind-induced force on drone (simplified linear drag model)."""
    rel = wind_velocity - drone_velocity
    speed = np.linalg.norm(rel)
    if speed < 1e-6:
        return np.zeros(3)
    # Use drone drag coefficient to model wind loading
    return 0.5 * config.AIR_DENSITY * config.DRONE_CD * config.DRONE_FRONTAL_AREA * speed ** 2 * (rel / speed)


def stability_factor(wind_speed: float) -> float:
    """
    Drone stability degrades quadratically with wind speed.
    Returns 0 at max_wind, 1 in calm conditions.
    """
    ratio = wind_speed / config.DRONE_MAX_WIND
    return float(max(0.0, 1.0 - ratio ** 2))


def hover_power(mass: float = config.DRONE_MASS) -> float:
    """Approximate hover power (W) using actuator disk theory."""
    return config.BATTERY_P_HOVER  # pre-calibrated constant from config


def transit_power(speed: float) -> float:
    """Power required for horizontal transit at given speed (W)."""
    # Cube law for propulsion power with a floor at hover
    return config.BATTERY_P_HOVER * (1.0 + (speed / config.DRONE_MAX_SPEED) ** 3)
