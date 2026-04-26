#!/usr/bin/env python3
"""
main.py — CLI entry point for the Wildfire Drone Swarm simulation.

Usage examples:
    python main.py
    python main.py --headless --ticks 5000
    python main.py --wind-speed 8 --wind-dir 45 --seed 7
    python main.py --fire-start 80,90 95,100 110,85
"""

import argparse
import sys
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Wildfire Drone Swarm — Acoustic Fire Suppression Simulation"
    )
    p.add_argument("--headless", action="store_true",
                   help="Run without visualisation (faster, for benchmarking)")
    p.add_argument("--ticks", type=int, default=None,
                   help="Maximum number of simulation ticks (default: run until mission complete)")
    p.add_argument("--realtime", action="store_true",
                   help="Throttle simulation to real time (DT per tick)")
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed for reproducibility (default: 42)")
    p.add_argument("--wind-speed", type=float, default=None,
                   help="Override base wind speed in m/s")
    p.add_argument("--wind-dir", type=float, default=None,
                   help="Override base wind direction in degrees (0=east, 90=north)")
    p.add_argument("--fire-start", nargs="+", default=None,
                   help="Starting fire cells as col,row pairs (e.g. 100,100 105,98)")
    p.add_argument("--drones", type=int, default=None,
                   help="Override number of drones")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Apply CLI overrides to config before importing simulation
    import config

    if args.wind_speed is not None:
        config.WIND_BASE_SPEED = args.wind_speed
    if args.wind_dir is not None:
        config.WIND_BASE_DIR = np.radians(args.wind_dir)
    if args.drones is not None:
        config.NUM_DRONES = args.drones

    fire_starts = None
    if args.fire_start:
        fire_starts = []
        for token in args.fire_start:
            try:
                col, row = map(int, token.split(","))
                fire_starts.append((col, row))
            except ValueError:
                print(f"ERROR: invalid fire-start cell '{token}'. Use col,row format.", file=sys.stderr)
                sys.exit(1)

    print("=" * 60)
    print("  Wildfire Drone Swarm — Acoustic Suppression Simulation")
    print("=" * 60)
    print(f"  Drones:      {config.NUM_DRONES}")
    print(f"  Grid:        {config.GRID_WIDTH}×{config.GRID_HEIGHT} cells "
          f"({config.GRID_WIDTH * config.CELL_SIZE:.0f}×{config.GRID_HEIGHT * config.CELL_SIZE:.0f}m)")
    print(f"  Wind:        {config.WIND_BASE_SPEED:.1f} m/s "
          f"@ {np.degrees(config.WIND_BASE_DIR):.0f}°")
    print(f"  Seed:        {args.seed}")
    print(f"  Visualise:   {not args.headless}")
    print("=" * 60)

    from simulation import Simulation
    sim = Simulation(
        visualize=not args.headless,
        seed=args.seed,
        fire_start_cells=fire_starts,
    )

    sim.run(max_ticks=args.ticks, realtime=args.realtime)

    m = sim.planner.metrics
    print("\n=== Final Metrics ===")
    print(f"  Simulation time:  {m.sim_time:.1f}s")
    print(f"  Cells burned:     {m.cells_burned}")
    print(f"  Still burning:    {m.cells_currently_burning}")


if __name__ == "__main__":
    main()
