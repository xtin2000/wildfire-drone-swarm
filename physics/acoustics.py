"""
Acoustic suppression physics.

Key reference: DARPA / AFRL 2012 acoustic flame suppression experiments.
Frequencies 30–60 Hz disrupt the combustion boundary layer.
"""

import numpy as np
import config

_P_REF = 1e-12  # W (reference acoustic power)


def sound_power_level(acoustic_power_w: float) -> float:
    """Sound Power Level in dB re 1 pW."""
    return 10.0 * np.log10(acoustic_power_w / _P_REF)


def directivity_index(angle_rad: float, q: float = config.SOUND_DIRECTIVITY_Q) -> float:
    """
    Directivity index (dB) for a cardioid-like pattern.
    angle_rad: angle from beam axis.
    """
    cos_term = np.cos(angle_rad / 2.0) ** 2
    di_linear = q * cos_term + 1e-9  # avoid log(0)
    return 10.0 * np.log10(di_linear)


def spl_at(
    acoustic_power_w: float,
    distance_m: float,
    angle_rad: float,
    q: float = config.SOUND_DIRECTIVITY_Q,
) -> float:
    """
    Sound Pressure Level in dB at given distance and off-axis angle.
    Uses free-field inverse-square law with directivity.
    """
    if distance_m < 0.1:
        distance_m = 0.1
    swl = sound_power_level(acoustic_power_w)
    di = directivity_index(angle_rad, q)
    return swl + di - 20.0 * np.log10(distance_m) - 11.0


def wind_deflection_factor(spl: float, wind_opposing_speed: float) -> float:
    """
    Reduce effective SPL due to wind refraction (upwind attenuation).
    wind_opposing_speed: component of wind opposing sound propagation (m/s).
    Returns a factor in [0.5, 1.0] applied as additive dB correction.
    """
    # Sound refracts upward against wind; ground-level SPL decreases ~15% at 10 m/s
    factor = max(0.5, 1.0 - 0.015 * max(0.0, wind_opposing_speed))
    return factor


def effective_spl(
    acoustic_power_w: float,
    distance_m: float,
    angle_rad: float,
    wind_opposing_speed: float = 0.0,
) -> float:
    """SPL after accounting for distance, directivity, and wind refraction."""
    raw = spl_at(acoustic_power_w, distance_m, angle_rad)
    wdf = wind_deflection_factor(raw, wind_opposing_speed)
    return raw + 20.0 * np.log10(wdf)


def suppression_effectiveness(spl: float) -> float:
    """
    Normalised suppression effectiveness eta in [0, 1].
    0 below threshold (110 dB), linearly rising to 1 at saturation (130 dB).
    """
    lo = config.SOUND_SPL_THRESHOLD
    hi = config.SOUND_SPL_SATURATION
    return float(np.clip((spl - lo) / (hi - lo), 0.0, 1.0))


def suppression_energy(spl: float, dt: float, burn_intensity: float = 1.0) -> float:
    """
    Suppression energy deposited on a target cell in one tick.
    Scaled down for nascent/low-intensity fires (easier to extinguish).
    Returns J-equivalent value to accumulate against suppression_applied.
    """
    eta = suppression_effectiveness(spl)
    # Effective energy: higher eta → more energy; intensity scaling handled by threshold
    return eta * config.FIRE_SUPPRESSION_THRESHOLD_BASE * dt


def combined_spl(spls: list[float]) -> float:
    """
    Incoherent summation of SPLs from multiple drones targeting same cell.
    10 * log10(sum(10^(SPL_i/10)))
    """
    if not spls:
        return -np.inf
    return 10.0 * np.log10(sum(10.0 ** (s / 10.0) for s in spls))
