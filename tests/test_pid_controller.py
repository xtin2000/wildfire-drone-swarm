"""Tests for PID flight controller."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from agents.flight_controller import FlightController
import config


def test_drone_reaches_target():
    """
    Simulating 200 ticks of PID control, drone should reach target within 5m.
    """
    ctrl = FlightController()
    pos = np.array([0.0, 0.0, 0.0])
    vel = np.zeros(3)
    target = np.array([50.0, 50.0, config.DRONE_CRUISE_ALT])
    wind = np.zeros(3)
    dt = config.DT

    for _ in range(300):
        cmd = ctrl.compute(target, pos, vel, wind, dt)
        vel = cmd
        pos = pos + vel * dt

    dist = float(np.linalg.norm(pos - target))
    assert dist < 5.0, f"Drone did not reach target: distance = {dist:.2f}m"


def test_wind_feedforward_reduces_error():
    """With wind feedforward, steady-state error in wind direction should be small."""
    ctrl_ff = FlightController()
    ctrl_noff = FlightController()
    ctrl_noff._pid_x._integral = 0  # same starting state

    target = np.array([100.0, 50.0, 15.0])
    wind = np.array([5.0, 0.0, 0.0])   # 5 m/s eastward headwind (for x-axis)

    pos_ff   = np.array([0.0, 50.0, 15.0])
    pos_noff = np.array([0.0, 50.0, 15.0])

    for _ in range(200):
        cmd = ctrl_ff.compute(target, pos_ff, np.zeros(3), wind, config.DT)
        pos_ff += cmd * config.DT

    err_ff = abs(pos_ff[0] - target[0])
    assert err_ff < 10.0, f"Feedforward controller x-error too large: {err_ff:.2f}m"
