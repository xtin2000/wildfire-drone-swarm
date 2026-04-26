"""
AuctionTaskAllocator: Hungarian-algorithm-based task assignment.

Drones bid on fire targets; optimal assignment minimises cost (maximises score).
Hysteresis prevents thrashing when scores change by small amounts.
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment
from dataclasses import dataclass
import config


@dataclass
class Target:
    task_id: int
    cell: tuple[int, int]   # (col, row)
    urgency: float
    world_pos: np.ndarray   # (2,) x, y


class AuctionTaskAllocator:
    def __init__(self):
        # drone_id -> task_id
        self._assignments: dict[int, int | None] = {}
        # drone_id -> last assignment score
        self._scores: dict[int, float] = {}

    def allocate(
        self,
        targets: list[Target],
        drone_msgs: list,  # list[DroneMessage]
    ) -> dict[int, Target | None]:
        """
        Return mapping drone_id -> Target (or None if no task).
        """
        if not targets or not drone_msgs:
            return {msg.drone_id: None for msg in drone_msgs}

        # Only consider drones that are available (not RETURNING or CHARGING)
        from agents.drone import DroneState
        available = [
            m for m in drone_msgs
            if m.state not in (DroneState.RETURNING, DroneState.CHARGING)
        ]
        if not available:
            return {msg.drone_id: None for msg in drone_msgs}

        n_drones = len(available)
        n_targets = len(targets)

        # Build cost matrix (we minimise cost = -score)
        cost = np.zeros((n_drones, n_targets), dtype=np.float64)
        for i, msg in enumerate(available):
            for j, tgt in enumerate(targets):
                cost[i, j] = -self._score(msg, tgt)

        # Solve assignment
        row_ind, col_ind = linear_sum_assignment(cost)

        # Build result dict — start with None for all drones
        result: dict[int, Target | None] = {msg.drone_id: None for msg in drone_msgs}

        for ri, ci in zip(row_ind, col_ind):
            msg = available[ri]
            tgt = targets[ci]
            new_score = -cost[ri, ci]
            old_score = self._scores.get(msg.drone_id, -1e9)
            old_task = self._assignments.get(msg.drone_id)

            # Apply hysteresis: only reassign if meaningfully better
            if old_task != tgt.task_id and new_score < old_score + config.TASK_REALLOC_HYSTERESIS:
                # Keep old assignment if target still exists
                old_tgt = next((t for t in targets if t.task_id == old_task), None)
                if old_tgt is not None:
                    result[msg.drone_id] = old_tgt
                    continue

            result[msg.drone_id] = tgt
            self._assignments[msg.drone_id] = tgt.task_id
            self._scores[msg.drone_id] = new_score

        return result

    def _score(self, msg, tgt: Target) -> float:
        """
        Higher is better.
        w1: proximity, w2: urgency, w3: battery, w4: stability
        """
        drone_xy = msg.position[:2]
        dist = float(np.linalg.norm(drone_xy - tgt.world_pos))
        dist = max(dist, 1.0)  # avoid division by zero

        w1 = 1.0 / dist * 20.0
        w2 = tgt.urgency * 5.0
        w3 = msg.battery_fraction * 3.0
        w4 = msg.stability * 2.0

        return w1 + w2 + w3 + w4
