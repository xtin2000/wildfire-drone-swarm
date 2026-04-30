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
    # ── Acoustic + rotor wash (realistic full-physics drone) ─────────────────
    "combined_baseline": {
        "description": "100 drones, both rotor wash and acoustic (5 m/s wind)",
        "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True},
    },
    "combined_high_wind": {
        "description": "100 drones, both mechanisms, 10 m/s wind",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
            "WIND_BASE_SPEED": 10.0,
            "WIND_BASE_DIR": float(np.radians(135)),
        },
    },
    # ── Rotor wash only (drones hover but don't emit acoustic) ───────────────
    "rotor_only_baseline": {
        "description": "100 drones, rotor wash only, no acoustic (5 m/s wind)",
        "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": False},
    },
    "rotor_only_high_wind": {
        "description": "100 drones, rotor wash only, 10 m/s wind",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": False,
            "WIND_BASE_SPEED": 10.0,
            "WIND_BASE_DIR": float(np.radians(135)),
        },
    },
    # ── Control: no drones at all ────────────────────────────────────────────
    "no_drones": {
        "description": "No drone intervention (uncontrolled fire)",
        "overrides": {"NUM_DRONES": 0},
    },
    # ── Fleet-size ablation (combined physics) ───────────────────────────────
    "combined_drones_25": {
        "description": "25 drones, both mechanisms",
        "overrides": {
            "NUM_DRONES": 25,
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
        },
    },
    "combined_drones_50": {
        "description": "50 drones, both mechanisms",
        "overrides": {
            "NUM_DRONES": 50,
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
        },
    },
    "combined_drones_150": {
        "description": "150 drones, both mechanisms",
        "overrides": {
            "NUM_DRONES": 150,
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
        },
    },
    # ── Sensitivity: rotor wash strength sweep ───────────────────────────────
    "combined_wash_half": {
        "description": "Combined mechanisms, rotor wash ember rate halved (25 J/s)",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
            "ROTOR_WASH_EMBER_RATE": 25.0,
        },
    },
    "combined_wash_double": {
        "description": "Combined mechanisms, rotor wash ember rate doubled (100 J/s)",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
            "ROTOR_WASH_EMBER_RATE": 100.0,
        },
    },
    # ── 2×2 factorial: drones × firefighters (under Option B firefighter physics) ──
    "pure_fire": {
        "description": "No drones, no firefighters — pure fire dynamics baseline",
        "overrides": {"NUM_DRONES": 0, "NUM_FIREFIGHTERS": 0},
    },
    "drones_only": {
        "description": "100 drones (combined mechanisms), no firefighters",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
            "NUM_FIREFIGHTERS": 0,
        },
    },
    "combined_no_ember_drag": {
        "description": "Combined mechanisms but rotor wash does NOT drag airborne embers down",
        "overrides": {
            "ROTOR_WASH_ENABLED": True,
            "ACOUSTIC_ENABLED": True,
            "ROTOR_WASH_EMBER_DRAG_ENABLED": False,
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
