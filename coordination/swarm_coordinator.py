"""
SwarmCoordinator: runs every COORD_INTERVAL ticks.

Integrates task allocation, conflict avoidance, and message dispatch.
"""

from __future__ import annotations
import numpy as np
import config
from coordination.task_allocator import AuctionTaskAllocator, Target
from coordination.conflict_avoider import ConflictAvoider
from agents.drone import DroneAgent, Task


class SwarmCoordinator:
    def __init__(self, drones: list[DroneAgent]):
        self.drones = drones
        self._allocator = AuctionTaskAllocator()
        self._avoider = ConflictAvoider()
        # Pending velocity adjustments broadcast to each drone
        self._velocity_hints: dict[int, np.ndarray] = {}

    def step(
        self,
        tick: int,
        targets: list[Target],
        firefighter_positions: list[tuple[float, float]],
    ) -> None:
        """Run coordination cycle."""
        # Collect drone state broadcasts
        msgs = [d.broadcast_state() for d in self.drones]

        # Task allocation
        assignments = self._allocator.allocate(targets, msgs)

        # Push tasks to drones
        for drone in self.drones:
            tgt = assignments.get(drone.id)
            if tgt is not None:
                drone.assign_task(Task(
                    task_id=tgt.task_id,
                    target_cell=tgt.cell,
                    urgency=tgt.urgency,
                ))
            else:
                # Don't clear tasks for drones mid-emitting unless explicitly None
                pass

        # Collision avoidance
        positions = np.array([d.position for d in self.drones])
        velocities = np.array([d.velocity for d in self.drones])

        adj = self._avoider.compute_adjustments(positions, velocities)

        if firefighter_positions:
            adj += self._avoider.check_firefighter_exclusion(positions, firefighter_positions)

        # Store hints (applied as additive velocity offsets in drone.step next tick)
        self._velocity_hints = {
            d.id: adj[i] for i, d in enumerate(self.drones)
        }

    def get_velocity_hint(self, drone_id: int) -> np.ndarray:
        return self._velocity_hints.get(drone_id, np.zeros(3))
