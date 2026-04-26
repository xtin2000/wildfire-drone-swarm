"""
BatteryModel: energy accounting for a drone.
"""

import config
from physics.flight_dynamics import transit_power


class BatteryModel:
    def __init__(self):
        self.charge_wh = config.BATTERY_CAPACITY_WH  # start full

    @property
    def fraction(self) -> float:
        return self.charge_wh / config.BATTERY_CAPACITY_WH

    @property
    def is_low(self) -> bool:
        return self.fraction < config.BATTERY_LOW_THRESH

    @property
    def is_full(self) -> bool:
        return self.fraction >= config.BATTERY_FULL_THRESH

    def consume(self, speed: float, is_emitting: bool, dt: float) -> None:
        """Deduct energy used in one tick."""
        p_flight = transit_power(speed)
        p_sound = (config.SOUND_POWER_W / config.SOUND_EFFICIENCY) if is_emitting else 0.0
        p_total = p_flight + p_sound + config.BATTERY_P_SENSORS
        self.charge_wh -= p_total * (dt / 3600.0)
        self.charge_wh = max(0.0, self.charge_wh)

    def charge(self, dt: float) -> None:
        """Recharge at base station."""
        self.charge_wh += config.BASE_CHARGE_RATE * config.BATTERY_CAPACITY_WH * dt
        self.charge_wh = min(self.charge_wh, config.BATTERY_CAPACITY_WH)
