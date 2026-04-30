"""Rotor-wash aerodynamics for multirotor drones.

Models the downward airflow column produced by a hovering drone's propellers.
Used to (a) deflect airborne embers downward and (b) disrupt small flames and
ember-state cells directly below the drone.

Physical basis: actuator disk theory. The induced velocity at the rotor disk
of a hovering rotor producing thrust T over area A in air of density rho is
v_disk = sqrt(T / (2 * rho * A)). Below the disk, the wake contracts
slightly, then expands and decays with distance as it entrains ambient air.
This module uses a linear decay approximation suitable for the 0-15 m altitude
regime relevant to fire suppression.
"""

import math

import config


def rotor_wash_velocity(altitude: float) -> float:
    """Downward airflow velocity (m/s) from a hovering drone, at the given altitude below it.

    Uses actuator disk theory for the disk velocity, then applies a linear
    decay to model wake expansion and ambient air entrainment.
    """
    if altitude <= 0:
        return 0.0
    thrust_n = config.DRONE_MASS * 9.81
    v_disk = math.sqrt(thrust_n / (2 * config.AIR_DENSITY * config.ROTOR_TOTAL_AREA))
    decay = 1.0 / (1.0 + altitude / config.ROTOR_WASH_DECAY_LENGTH)
    return v_disk * decay


def rotor_wash_footprint_radius(altitude: float) -> float:
    """Lateral radius (m) of the rotor wash footprint at the given altitude below the drone."""
    return config.ROTOR_WASH_FOOTPRINT_BASE + altitude * config.ROTOR_WASH_SPREAD_RATE


def rotor_wash_radial_factor(lateral_distance: float, altitude: float) -> float:
    """Radial intensity factor in [0, 1] at a lateral offset from the drone's vertical axis.

    Returns 1.0 directly under the drone, smoothly falling to 0 at the footprint edge.
    """
    radius = rotor_wash_footprint_radius(altitude)
    if lateral_distance >= radius:
        return 0.0
    return (1.0 - lateral_distance / radius) ** 2
