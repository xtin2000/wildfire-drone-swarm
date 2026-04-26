"""Tests for Hungarian task allocation."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from coordination.task_allocator import AuctionTaskAllocator, Target
from agents.drone import DroneState, DroneMessage


def _make_msg(drone_id: int, x: float, y: float) -> DroneMessage:
    return DroneMessage(
        drone_id=drone_id,
        position=np.array([x, y, 15.0]),
        velocity=np.zeros(3),
        state=DroneState.IDLE,
        battery_fraction=0.8,
        task_id=None,
        stability=1.0,
    )


def _make_target(task_id: int, x: float, y: float, urgency: float = 1.0) -> Target:
    return Target(task_id=task_id, cell=(int(x // 2), int(y // 2)),
                  urgency=urgency, world_pos=np.array([x, y]))


def test_unique_assignments():
    """Each drone should get a unique target (no double-assignment)."""
    alloc = AuctionTaskAllocator()
    drones = [_make_msg(i, i * 5.0, 10.0) for i in range(5)]
    targets = [_make_target(j, j * 8.0 + 20.0, 50.0) for j in range(5)]

    result = alloc.allocate(targets, drones)
    assigned_tasks = [v.task_id for v in result.values() if v is not None]
    assert len(assigned_tasks) == len(set(assigned_tasks)), "Duplicate task assignments!"


def test_ember_preferred():
    """High-urgency (ember) targets should be assigned over low-urgency ones."""
    alloc = AuctionTaskAllocator()
    drone = [_make_msg(0, 100.0, 100.0)]
    targets = [
        _make_target(1, 120.0, 100.0, urgency=1.0),   # low urgency
        _make_target(2, 125.0, 100.0, urgency=10.0),  # ember
    ]
    result = alloc.allocate(targets, drone)
    assigned = result[0]
    assert assigned is not None
    assert assigned.task_id == 2, f"Expected ember (task 2) assigned, got task {assigned.task_id}"
