"""Geometric and angular math primitives shared across modules."""

import numpy as np


def wrap_angle(a: float) -> float:
    """Wrap an angle in radians to the range (-pi, pi]."""
    return float((a + np.pi) % (2 * np.pi) - np.pi)
