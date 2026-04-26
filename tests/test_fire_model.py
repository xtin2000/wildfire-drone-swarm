"""Tests for fire spread and suppression."""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from environment.grid import TerrainGrid
from environment.wind_model import WindModel
from environment.fire_model import FireSpreadModel


def test_fire_spreads():
    """A burning cell should spread to neighbours over time."""
    grid = TerrainGrid(seed=0)
    wind = WindModel(seed=0)
    fire = FireSpreadModel(grid, wind, seed=0)

    # Ignite centre
    grid.ignite(100, 100)
    initial = len(grid.get_burning_cells())
    assert initial == 1

    # Run 500 ticks (50 sim-seconds)
    for _ in range(500):
        fire.step(config.DT)

    final = len(grid.get_burning_cells())
    assert final > initial, f"Fire did not spread: still {final} cells"


def test_fire_suppressed():
    """Enough suppression energy should extinguish a cell."""
    grid = TerrainGrid(seed=1)
    wind = WindModel(seed=1)
    fire = FireSpreadModel(grid, wind, seed=1)

    grid.ignite(50, 50)
    grid.burn_intensity[50, 50] = 0.5

    # Dump more than the threshold worth of energy
    threshold = config.FIRE_SUPPRESSION_THRESHOLD_BASE * 0.5
    grid.apply_suppression(50, 50, threshold + 1.0)
    fire.step(config.DT)

    assert grid.cell_state[50, 50] == config.STATE_BURNED, "Cell should be extinguished"


def test_wind_influences_spread_direction():
    """Fire should spread faster in wind direction than against it."""
    # Strong eastward wind
    config.WIND_BASE_SPEED = 8.0
    config.WIND_BASE_DIR = 0.0  # east

    grid = TerrainGrid(seed=2)
    wind = WindModel(seed=2)
    fire = FireSpreadModel(grid, wind, seed=2)

    grid.ignite(100, 100)

    for _ in range(200):
        wind.step(config.DT)
        fire.step(config.DT)

    # Count burning cells east vs west of start
    east_count = sum(1 for col, row in grid.get_burning_cells() if col > 100)
    west_count = sum(1 for col, row in grid.get_burning_cells() if col < 100)

    assert east_count >= west_count, (
        f"Expected more eastward spread, got east={east_count} west={west_count}"
    )

    # Restore defaults
    config.WIND_BASE_SPEED = 5.0
