"""Tests for acoustic suppression physics."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from physics.acoustics import spl_at, suppression_effectiveness, combined_spl
import config


def test_spl_at_5m():
    """200W subwoofer should produce >110 dB at 5m on-axis."""
    spl = spl_at(config.SOUND_POWER_W, 5.0, 0.0)
    assert spl > 110.0, f"Expected SPL > 110 dB at 5m, got {spl:.1f}"


def test_spl_below_threshold_at_far_range():
    """SPL should fall below threshold at long range."""
    spl = spl_at(config.SOUND_POWER_W, 30.0, 0.0)
    assert spl < config.SOUND_SPL_THRESHOLD, f"Expected SPL < {config.SOUND_SPL_THRESHOLD} at 30m, got {spl:.1f}"


def test_effectiveness_zero_below_threshold():
    eta = suppression_effectiveness(config.SOUND_SPL_THRESHOLD - 1)
    assert eta == 0.0


def test_effectiveness_one_above_saturation():
    eta = suppression_effectiveness(config.SOUND_SPL_SATURATION + 5)
    assert eta == 1.0


def test_combined_spl_two_equal_sources():
    """Two equal SPL sources should add ~3 dB."""
    s = 120.0
    combined = combined_spl([s, s])
    assert abs(combined - (s + 3.01)) < 0.1, f"Expected {s+3.01:.2f}, got {combined:.2f}"
