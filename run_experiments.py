#!/usr/bin/env python3
"""
run_experiments.py — Headless experiment runner for thesis results.

Each scenario runs in a fresh subprocess to guarantee clean module state.
Logs per-tick metrics to CSV files in the output directory.
Use generate_figures.py afterwards to produce publication-quality plots.

Usage:
    python3 run_experiments.py                  # run all scenarios
    python3 run_experiments.py --scenario baseline high_wind
    python3 run_experiments.py --max-ticks 3000  # cap each run
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np


# ── Scenario definitions ─────────────────────────────────────────────────────

SCENARIOS = {
    "baseline": {
        "description": "Default configuration (100 drones, 5 m/s wind)",
        "overrides": {},
    },
    "high_wind": {
        "description": "High wind scenario (10 m/s, SE direction)",
        "overrides": {
            "WIND_BASE_SPEED": 10.0,
            "WIND_BASE_DIR": float(np.radians(135)),
        },
    },
    "drones_25": {
        "description": "Reduced fleet: 25 drones",
        "overrides": {"NUM_DRONES": 25},
    },
    "drones_50": {
        "description": "Reduced fleet: 50 drones",
        "overrides": {"NUM_DRONES": 50},
    },
    "drones_150": {
        "description": "Enlarged fleet: 150 drones",
        "overrides": {"NUM_DRONES": 150},
    },
    "no_drones": {
        "description": "No drone intervention (uncontrolled fire)",
        "overrides": {"NUM_DRONES": 0},
    },
    "high_wind_150": {
        "description": "High wind (10 m/s) with 150 drones",
        "overrides": {
            "WIND_BASE_SPEED": 10.0,
            "WIND_BASE_DIR": float(np.radians(135)),
            "NUM_DRONES": 150,
        },
    },
}


def write_summary_table(summaries: list[dict], output_dir: Path):
    """Write a summary CSV comparing all scenarios."""
    path = output_dir / "summary_table.csv"
    fields = list(summaries[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in summaries:
            writer.writerow(s)

    print(f"\n{'='*80}")
    print("  EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    header = (f"{'Scenario':<18} {'Drones':>6} {'Wind':>5} {'Ticks':>6} "
              f"{'SimTime':>8} {'PkBurn':>7} {'PkEmber':>7} "
              f"{'Burned':>7} {'Done':>5}")
    print(header)
    print("-" * 80)
    for s in summaries:
        row = (f"{s['scenario']:<18} {s['num_drones']:>6} "
               f"{s['wind_speed']:>5.1f} {s['total_ticks']:>6} "
               f"{s['sim_time_s']:>7.1f}s {s['peak_burning']:>7} "
               f"{s['peak_ember']:>7} {s['total_burned']:>7} "
               f"{'Yes' if s['mission_complete'] else 'No':>5}")
        print(row)
    print(f"{'='*80}")
    print(f"Summary CSV: {path}")


def main():
    parser = argparse.ArgumentParser(description="Run thesis experiment scenarios")
    parser.add_argument("--scenario", nargs="+", default=None,
                        help="Specific scenarios to run (default: all)")
    parser.add_argument("--max-ticks", type=int, default=5000,
                        help="Maximum ticks per scenario (default: 5000)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Output directory for CSVs and figures")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    scenarios_to_run = args.scenario or list(SCENARIOS.keys())

    for s in scenarios_to_run:
        if s not in SCENARIOS:
            print(f"ERROR: Unknown scenario '{s}'. "
                  f"Available: {', '.join(SCENARIOS.keys())}")
            sys.exit(1)

    print(f"Will run {len(scenarios_to_run)} scenario(s): "
          f"{', '.join(scenarios_to_run)}")
    print(f"Max ticks per scenario: {args.max_ticks}")
    print(f"Output directory: {output_dir}")

    summaries = []
    for name in scenarios_to_run:
        scenario = SCENARIOS[name]
        print(f"\n{'='*60}")
        print(f"  Scenario: {name}")
        print(f"  {scenario['description']}")
        print(f"{'='*60}")

        # Launch each scenario as a fresh subprocess
        overrides_json = json.dumps(scenario["overrides"])
        result = subprocess.run(
            [sys.executable, "_run_single_scenario.py",
             "--name", name,
             "--description", scenario["description"],
             "--overrides", overrides_json,
             "--max-ticks", str(args.max_ticks),
             "--seed", str(args.seed),
             "--output-dir", str(output_dir)],
            capture_output=False,
        )

        if result.returncode != 0:
            print(f"  [ERROR] Scenario {name} failed (exit code {result.returncode})")
            continue

        # Read back the summary JSON written by the subprocess
        summary_path = output_dir / f"{name}_summary.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)
            summaries.append(summary)
        else:
            print(f"  [WARNING] No summary file for {name}")

    if summaries:
        write_summary_table(summaries, output_dir)


if __name__ == "__main__":
    main()
