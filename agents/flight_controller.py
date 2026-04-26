"""
FlightController: PID position control with wind feedforward.
"""

import numpy as np
import config
from physics.flight_dynamics import stability_factor


class PIDAxis:
    """Single-axis discrete PID with anti-windup."""

    def __init__(self, kp: float, ki: float, kd: float, output_limit: float = 15.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self._integral = 0.0
        self._prev_error = 0.0

    def step(self, error: float, dt: float) -> float:
        self._integral += error * dt
        derivative = (error - self._prev_error) / dt if dt > 0 else 0.0
        self._prev_error = error

        out = self.kp * error + self.ki * self._integral + self.kd * derivative

        # Anti-windup: clamp integral if output saturates
        if abs(out) > self.output_limit:
            self._integral -= error * dt
            out = np.clip(out, -self.output_limit, self.output_limit)

        return float(out)

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = 0.0


class FlightController:
    def __init__(self):
        kp, ki, kd = config.PID_KP, config.PID_KI, config.PID_KD
        self._pid_x = PIDAxis(kp, ki, kd, config.DRONE_MAX_SPEED)
        self._pid_y = PIDAxis(kp, ki, kd, config.DRONE_MAX_SPEED)
        self._pid_z = PIDAxis(kp, ki, kd, config.DRONE_MAX_VSPEED)

    def compute(
        self,
        target_pos: np.ndarray,   # (3,) world coordinates
        current_pos: np.ndarray,  # (3,)
        current_vel: np.ndarray,  # (3,)
        wind_vec: np.ndarray,     # (2,) or (3,) wind at drone location
        dt: float,
    ) -> np.ndarray:
        """Return commanded velocity vector (3,) in m/s."""
        error = target_pos - current_pos

        # Wind feedforward: proactively lean into wind
        ff = np.zeros(3)
        ff[0] = config.WIND_FF_GAIN * wind_vec[0]
        ff[1] = config.WIND_FF_GAIN * wind_vec[1]

        cmd_x = self._pid_x.step(error[0], dt) + ff[0]
        cmd_y = self._pid_y.step(error[1], dt) + ff[1]
        cmd_z = self._pid_z.step(error[2], dt)

        cmd = np.array([cmd_x, cmd_y, cmd_z])

        # Degrade max speed in strong winds
        w_speed = float(np.linalg.norm(wind_vec[:2]))
        sf = stability_factor(w_speed)
        max_h = config.DRONE_MAX_SPEED * max(sf, 0.3)  # minimum 30% capability
        h_speed = np.linalg.norm(cmd[:2])
        if h_speed > max_h:
            cmd[:2] *= max_h / h_speed
        cmd[2] = np.clip(cmd[2], -config.DRONE_MAX_VSPEED, config.DRONE_MAX_VSPEED)

        return cmd

    def reset(self) -> None:
        self._pid_x.reset()
        self._pid_y.reset()
        self._pid_z.reset()
