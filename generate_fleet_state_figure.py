#!/usr/bin/env python3
"""Generate a drone-fleet-state-distribution figure for combined_baseline (seed 42)."""

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


def main() -> None:
    path = RESULTS / "combined_baseline_ticks.csv"
    d = load_ticks(path)
    t_min = np.array(d["sim_time"]) / 60

    state_keys = [
        ("drones_idle", "Idle", "#7f7f7f"),
        ("drones_transit", "Transit", "#1f77b4"),
        ("drones_hovering", "Hovering", "#9467bd"),
        ("drones_emitting", "Emitting", "#2ca02c"),
        ("drones_returning", "Returning", "#ff7f0e"),
        ("drones_charging", "Charging", "#d62728"),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)

    # Top panel — stacked area showing drone state distribution over time
    state_data = [np.array(d[k]) for k, _, _ in state_keys]
    labels = [label for _, label, _ in state_keys]
    colors = [c for _, _, c in state_keys]
    ax1.stackplot(t_min, *state_data, labels=labels, colors=colors, alpha=0.85)
    ax1.set_ylabel("Drone count (stacked)")
    ax1.set_ylim(0, 105)
    ax1.set_title(
        "Drone fleet state distribution over time — combined_baseline (seed 42, 5 m/s wind)"
    )
    ax1.legend(loc="lower right", ncol=3, fontsize=9)
    ax1.grid(alpha=0.3)

    # Bottom panel — battery and stability
    ax2.plot(t_min, np.array(d["mean_battery"]) * 100, label="Mean battery (%)",
             color="purple", linewidth=1.6)
    ax2.plot(t_min, np.array(d["min_battery"]) * 100, label="Min battery (%)",
             color="purple", linewidth=1.0, linestyle="--", alpha=0.7)
    ax2.plot(t_min, np.array(d["mean_stability"]) * 100, label="Mean stability × 100",
             color="teal", linewidth=1.0, alpha=0.7)
    ax2.set_ylabel("Battery / Stability")
    ax2.set_xlabel("Simulated time (minutes)")
    ax2.set_ylim(0, 105)
    ax2.set_title("Mean fleet battery and stability over the same run")
    ax2.legend(loc="lower left", fontsize=9)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    out = FIG_DIR / "fig_fleet_state.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
