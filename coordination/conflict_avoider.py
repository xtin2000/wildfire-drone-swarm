"""
ConflictAvoider: velocity obstacle (ORCA-inspired) collision avoidance.

Uses scipy.spatial.KDTree for efficient proximity queries.
Each drone pair shares responsibility 50/50.
"""

from __future__ import annotations
import numpy as np
from scipy.spatial import KDTree
import config


class ConflictAvoider:
    """Produces velocity adjustments to keep drones separated."""

    def __init__(self):
        self.min_sep = config.MIN_DRONE_SEPARATION
        self.time_horizon = config.VO_TIME_HORIZON

    def compute_adjustments(
        self,
        positions: np.ndarray,    # (N, 3) world coords
        velocities: np.ndarray,   # (N, 3)
    ) -> np.ndarray:
        """
        Return velocity adjustments (N, 3) to add to commanded velocities.
        Uses a simplified VO: if drones are on collision course within time_horizon,
        apply a repulsion impulse perpendicular to the relative position.
        """
        N = len(positions)
        adjustments = np.zeros((N, 3))
        if N < 2:
            return adjustments

        xy_pos = positions[:, :2]
        tree = KDTree(xy_pos)

        # Query pairs within detection range
        pairs = tree.query_pairs(self.min_sep * 4.0)

        for i, j in pairs:
            p_rel = positions[j] - positions[i]
            dist = float(np.linalg.norm(p_rel[:2]))

            if dist < 1e-6:
                # Exact overlap — push apart randomly
                angle = np.random.uniform(0, 2 * np.pi)
                push = np.array([np.cos(angle), np.sin(angle), 0.0]) * 1.0
                adjustments[i] -= push * 0.5
                adjustments[j] += push * 0.5
                continue

            v_rel = velocities[j] - velocities[i]

            # Time to closest approach
            t_ca = -float(np.dot(p_rel[:2], v_rel[:2])) / (np.dot(v_rel[:2], v_rel[:2]) + 1e-9)
            t_ca = np.clip(t_ca, 0, self.time_horizon)

            # Predicted closest distance
            closest_pos = p_rel[:2] + v_rel[:2] * t_ca
            closest_dist = float(np.linalg.norm(closest_pos))

            if closest_dist >= self.min_sep:
                continue  # No collision predicted

            # Avoidance: push drones apart along relative position vector
            repulsion_dir = p_rel[:2] / (dist + 1e-9)
            # Strength inversely proportional to distance
            strength = (self.min_sep - closest_dist) / self.min_sep * 2.0

            avoidance = np.array([
                -repulsion_dir[0] * strength,
                -repulsion_dir[1] * strength,
                0.0,
            ])
            # 50/50 responsibility
            adjustments[i] += avoidance * 0.5
            adjustments[j] -= avoidance * 0.5

        return adjustments

    def check_firefighter_exclusion(
        self,
        positions: np.ndarray,           # (N, 3)
        firefighter_positions: list,     # list of (x, y) world coords
    ) -> np.ndarray:
        """Return repulsion adjustments to push drones away from firefighters."""
        N = len(positions)
        adjustments = np.zeros((N, 3))
        excl_r = config.FIREFIGHTER_EXCL_RADIUS

        for fx, fy in firefighter_positions:
            ff_pos = np.array([fx, fy])
            for i in range(N):
                diff = positions[i, :2] - ff_pos
                dist = float(np.linalg.norm(diff))
                if dist < excl_r and dist > 1e-6:
                    push_dir = diff / dist
                    strength = (excl_r - dist) / excl_r * 3.0
                    adjustments[i, 0] += push_dir[0] * strength
                    adjustments[i, 1] += push_dir[1] * strength

        return adjustments
