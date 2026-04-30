#!/usr/bin/env python3
"""Generate three additional thesis figures:
  - fig_battery_depletion.png   — mean/min battery over time, contained vs uncontained
  - fig_suppression_pressure.png — active drones per active fire cell over time
  - fig_active_fire.png         — burning + ember cells (total active fire) over time
"""

from __future__ import annotations
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
RESULTS = ROOT / "results_v2"
FIG_DIR = RESULTS / "figures"


def load_ticks(path: Path) -> dict[str, list[float]]:
    cols: dict[str, list[float]] = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                cols.setdefault(k, []).append(float(v))
    return cols


def fig_battery() -> Path:
    """Battery depletion: contained vs uncontained scenario."""
    runs = [
        ("combined_baseline (contained)", RESULTS / "combined_baseline_ticks.csv", "#2ca02c"),
        ("rotor_only_baseline (uncontained)", RESULTS / "rotor_only_baseline_ticks.csv", "#1f77b4"),
        ("combined_high_wind (high-wind, RTB-dominated)", RESULTS / "combined_high_wind_ticks.csv", "#d62728"),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for label, path, color in runs:
        if not path.exists():
            continue
        d = load_ticks(path)
        t_min = np.array(d["sim_time"]) / 60
        ax.plot(t_min, np.array(d["mean_battery"]) * 100, label=f"{label} — mean", color=color, linewidth=1.6)
        ax.plot(t_min, np.array(d["min_battery"]) * 100, color=color, linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axhline(20, color="black", linestyle=":", alpha=0.5, label="RTB threshold (20%)")
    ax.set_xlabel("Simulated time (minutes)")
    ax.set_ylabel("Battery (%)")
    ax.set_title("Drone fleet battery depletion over time — contained vs uncontained scenarios\nSolid = mean across fleet; dashed = minimum")
    ax.set_ylim(0, 105)
    ax.set_xlim(0, 60)
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = FIG_DIR / "fig_battery_depletion.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_suppression_pressure() -> Path:
    """Suppression pressure: (emitting + hovering drones) / (active fire cells)."""
    runs = [
        ("combined_baseline (contains)", RESULTS / "combined_baseline_ticks.csv", "#2ca02c"),
        ("rotor_only_baseline", RESULTS / "rotor_only_baseline_ticks.csv", "#1f77b4"),
        ("drones_only (no firefighters)", RESULTS / "option_b" / "drones_only_ticks.csv", "#ff7f0e"),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for label, path, color in runs:
        if not path.exists():
            continue
        d = load_ticks(path)
        t_min = np.array(d["sim_time"]) / 60
        active_drones = np.array(d["drones_emitting"]) + np.array(d["drones_hovering"])
        active_fire = np.array(d["cells_burning"]) + np.array(d["cells_ember"])
        active_fire_safe = np.maximum(active_fire, 1.0)
        pressure = active_drones / active_fire_safe
        ax.plot(t_min, pressure, label=label, color=color, linewidth=1.5)
    ax.axhline(1.0, color="black", linestyle=":", alpha=0.5, label="parity (1 active drone per active fire cell)")
    ax.set_xlabel("Simulated time (minutes)")
    ax.set_ylabel("Active drones per active fire cell")
    ax.set_title("Suppression pressure: ratio of active drones (emitting + hovering) to active fire cells (burning + ember)")
    ax.set_yscale("log")
    ax.set_ylim(0.001, 200)
    ax.set_xlim(0, 60)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3, which="both")
    plt.tight_layout()
    out = FIG_DIR / "fig_suppression_pressure.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_active_fire() -> Path:
    """Total active fire (burning + ember) over time across major scenarios."""
    runs = [
        ("pure_fire (no intervention)", RESULTS / "option_b" / "pure_fire_ticks.csv", "#7f7f7f", "-"),
        ("no_drones (firefighters only)", RESULTS / "option_b" / "no_drones_ticks.csv", "#9467bd", "-"),
        ("rotor_only_baseline", RESULTS / "rotor_only_baseline_ticks.csv", "#1f77b4", "-"),
        ("drones_only (no firefighters)", RESULTS / "option_b" / "drones_only_ticks.csv", "#ff7f0e", "-"),
        ("combined_baseline (contained)", RESULTS / "combined_baseline_ticks.csv", "#2ca02c", "-"),
        ("combined_high_wind (10 m/s)", RESULTS / "combined_high_wind_ticks.csv", "#d62728", "--"),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for label, path, color, ls in runs:
        if not path.exists():
            continue
        d = load_ticks(path)
        t_min = np.array(d["sim_time"]) / 60
        active = np.array(d["cells_burning"]) + np.array(d["cells_ember"])
        ax.plot(t_min, active, label=label, color=color, linestyle=ls, linewidth=1.5)
    ax.set_xlabel("Simulated time (minutes)")
    ax.set_ylabel("Active fire cells (burning + ember)")
    ax.set_title("Total active fire over time across scenarios — 5 m/s wind unless noted")
    ax.set_xlim(0, 60)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = FIG_DIR / "fig_active_fire.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    for name, fn in [("battery", fig_battery), ("suppression_pressure", fig_suppression_pressure), ("active_fire", fig_active_fire)]:
        out = fn()
        print(f"  {name}: {out}")


if __name__ == "__main__":
    main()
