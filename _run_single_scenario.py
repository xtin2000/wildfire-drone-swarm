#!/usr/bin/env python3
"""
_run_single_scenario.py — Runs one experiment scenario in a fresh process.

Called by run_experiments.py via subprocess. This guarantees that config
and all simulation modules start from a clean state for each scenario.
"""

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--overrides", required=True, help="JSON dict of config overrides")
    parser.add_argument("--max-ticks", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    overrides = json.loads(args.overrides)

    # Apply config overrides BEFORE importing simulation
    for key, value in overrides.items():
        setattr(config, key, value)

    num_drones = config.NUM_DRONES

    from simulation import Simulation
    from agents.drone import DroneState

    sim = Simulation(visualize=False, seed=args.seed)

    csv_path = output_dir / f"{args.name}_ticks.csv"
    fieldnames = [
        "tick", "sim_time",
        "cells_burning", "cells_ember", "cells_burned", "cells_wet",
        "total_fire_cells",
        "drones_emitting", "drones_returning", "drones_transit",
        "drones_idle", "drones_hovering", "drones_charging",
        "mean_battery", "min_battery",
        "mean_stability",
    ]

    wall_start = time.perf_counter()
    tick_data = []

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        while True:
            if sim.tick >= args.max_ticks:
                print(f"  [STOP] Max ticks ({args.max_ticks}) reached.")
                break
            if sim.planner.is_mission_complete(sim.grid) and sim.tick > 10:
                print(f"  [DONE] Mission complete at tick {sim.tick} "
                      f"(sim_time={sim.sim_time:.1f}s)")
                break

            sim.step()

            state_arr = sim.grid.cell_state
            burning = int(np.sum(state_arr == config.STATE_BURNING))
            ember = int(np.sum(state_arr == config.STATE_EMBER))
            burned = int(np.sum(state_arr == config.STATE_BURNED))
            wet = int(np.sum(state_arr == config.STATE_WET))

            drone_states = [d.state for d in sim.drones]
            batteries = [d.battery.fraction for d in sim.drones] if sim.drones else []
            stabilities = [d._stability for d in sim.drones] if sim.drones else []

            row = {
                "tick": sim.tick,
                "sim_time": round(sim.sim_time, 3),
                "cells_burning": burning,
                "cells_ember": ember,
                "cells_burned": burned,
                "cells_wet": wet,
                "total_fire_cells": burning + ember,
                "drones_emitting": sum(1 for s in drone_states if s == DroneState.EMITTING),
                "drones_returning": sum(1 for s in drone_states if s == DroneState.RETURNING),
                "drones_transit": sum(1 for s in drone_states if s == DroneState.TRANSIT),
                "drones_idle": sum(1 for s in drone_states if s == DroneState.IDLE),
                "drones_hovering": sum(1 for s in drone_states if s == DroneState.HOVERING),
                "drones_charging": sum(1 for s in drone_states if s == DroneState.CHARGING),
                "mean_battery": round(np.mean(batteries), 4) if batteries else 0,
                "min_battery": round(np.min(batteries), 4) if batteries else 0,
                "mean_stability": round(np.mean(stabilities), 4) if stabilities else 0,
            }
            writer.writerow(row)
            tick_data.append(row)

            if sim.tick % 500 == 0:
                wall = time.perf_counter() - wall_start
                print(f"  tick={sim.tick:5d} | burning={burning:4d} "
                      f"| ember={ember:3d} | burned={burned:4d} "
                      f"| emitting={row['drones_emitting']:3d} "
                      f"| wall={wall:.1f}s")

    wall_total = time.perf_counter() - wall_start

    summary = {
        "scenario": args.name,
        "description": args.description,
        "num_drones": num_drones,
        "wind_speed": config.WIND_BASE_SPEED,
        "total_ticks": sim.tick,
        "sim_time_s": round(sim.sim_time, 1),
        "wall_time_s": round(wall_total, 1),
        "mission_complete": sim.planner.is_mission_complete(sim.grid),
        "peak_burning": max(r["cells_burning"] for r in tick_data) if tick_data else 0,
        "peak_ember": max(r["cells_ember"] for r in tick_data) if tick_data else 0,
        "total_burned": tick_data[-1]["cells_burned"] if tick_data else 0,
        "total_wet": tick_data[-1]["cells_wet"] if tick_data else 0,
        "final_burning": tick_data[-1]["cells_burning"] if tick_data else 0,
        "csv_path": str(csv_path),
    }

    # Write summary JSON for parent process
    summary_path = output_dir / f"{args.name}_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Wall time: {wall_total:.1f}s")
    print(f"  Peak burning: {summary['peak_burning']} cells")
    print(f"  Total burned: {summary['total_burned']} cells")
    print(f"  CSV saved to: {csv_path}")


if __name__ == "__main__":
    main()
