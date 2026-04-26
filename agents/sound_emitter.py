"""
SoundEmitter: subwoofer acoustic suppression model for a single drone.
"""

import numpy as np
import config
from physics import acoustics
from physics.geometry import wrap_angle


class SoundEmitter:
    def __init__(self):
        self.is_active = False
        self._target_pos: np.ndarray | None = None  # world coords (3,)

    def start(self, target_pos: np.ndarray) -> None:
        self.is_active = True
        self._target_pos = target_pos.copy()

    def stop(self) -> None:
        self.is_active = False
        self._target_pos = None

    def update_target(self, target_pos: np.ndarray) -> None:
        if self.is_active:
            self._target_pos = target_pos.copy()

    def compute_delivered_energy(
        self,
        drone_pos: np.ndarray,   # (3,)
        drone_heading: float,    # radians (yaw, CCW from +x)
        wind_vec: np.ndarray,    # (2,) at drone position
        stability: float,        # 0–1 from flight_dynamics.stability_factor
        dt: float,
    ) -> float:
        """
        Return suppression energy (J-equivalent) delivered to target this tick.
        Returns 0 if not active, out of range, or misaligned.
        """
        if not self.is_active or self._target_pos is None:
            return 0.0

        diff = self._target_pos - drone_pos
        distance = float(np.linalg.norm(diff))

        if distance < 0.1 or distance > config.SOUND_MAX_RANGE * 1.5:
            return 0.0

        # Angle between drone heading and direction-to-target
        target_angle = float(np.arctan2(diff[1], diff[0]))
        angle_error = abs(wrap_angle(target_angle - drone_heading))

        beam_half = np.radians(config.SOUND_BEAM_ANGLE_DEG)
        if angle_error > beam_half:
            # Outside beam — small spillover still possible
            off_axis = angle_error
        else:
            off_axis = angle_error

        # Wind opposing component (sound propagation direction)
        prop_dir = diff[:2] / (np.linalg.norm(diff[:2]) + 1e-9)
        wind_opp = float(-np.dot(wind_vec, prop_dir))  # positive = headwind for sound

        # Effective acoustic power reduced by drone instability
        power = config.SOUND_POWER_W * stability

        spl = acoustics.effective_spl(power, distance, off_axis, max(0.0, wind_opp))
        energy = acoustics.suppression_energy(spl, dt)
        return energy

    @property
    def target_pos(self) -> np.ndarray | None:
        return self._target_pos
