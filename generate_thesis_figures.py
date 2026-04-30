#!/usr/bin/env python3
"""Generate the figures referenced in thesis_section5_v3_redraft.md from results_v2."""

from __future__ import annotations
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
RESULTS = ROOT / "results_v2"
FIG_DIR = RESULTS / "figures"
FIG_DIR.mkdir(exist_ok=True)


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text())


def load_ticks(path: Path) -> dict[str, list[float]]:
    cols: dict[str, list[float]] = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                cols.setdefault(k, []).append(float(v))
    return cols


def fig_2x2_factorial() -> Path:
    """Bar chart: drones × firefighters factorial (all under Option B physics)."""
    cells = {
        ("No drones", "No firefighters"): RESULTS / "option_b" / "pure_fire_summary.json",
        ("No drones", "10 firefighters"): RESULTS / "option_b" / "no_drones_summary.json",
        ("100 drones", "No firefighters"): RESULTS / "option_b" / "drones_only_summary.json",
        ("100 drones", "10 firefighters"): RESULTS / "combined_baseline_summary.json",
    }
    pcts = {label: 100 * load_summary(p)["total_burned"] / 40000 for label, p in cells.items()}

    drones = ["No drones", "100 drones"]
    firefighters = ["No firefighters", "10 firefighters"]
    matrix = np.array([[pcts[(d, f)] for f in firefighters] for d in drones])

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(drones))
    width = 0.35
    ax.bar(x - width / 2, matrix[:, 0], width, label=firefighters[0], color="#d62728")
    ax.bar(x + width / 2, matrix[:, 1], width, label=firefighters[1], color="#2ca02c")
    for i, d in enumerate(drones):
        for j, f in enumerate(firefighters):
            v = matrix[i, j]
            x_pos = x[i] + (j - 0.5) * width
            ax.text(x_pos, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(drones)
    ax.set_ylabel("% of grid burned (after 35,000 ticks or mission complete)")
    ax.set_ylim(0, 110)
    ax.set_title("Containment factorial — drones × firefighters (5 m/s wind, seed 42)\nOption B firefighter physics")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    out = FIG_DIR / "fig_2x2_factorial.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_seed_reproducibility() -> Path:
    """N=5 seeds for combined_baseline showing bimodal outcome."""
    seed_data: list[tuple[int, dict]] = []
    seed_42 = load_summary(RESULTS / "combined_baseline_summary.json")
    seed_data.append((42, seed_42))
    for seed in [43, 44, 45, 46]:
        p = RESULTS / "sensitivity" / f"seed_{seed}" / "combined_baseline_summary.json"
        if p.exists():
            seed_data.append((seed, load_summary(p)))

    seeds = [s for s, _ in seed_data]
    pcts = [100 * d["total_burned"] / 40000 for _, d in seed_data]
    sim_times = [d["sim_time_s"] / 60 for _, d in seed_data]
    contained = [p < 10 for p in pcts]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    colors = ["#2ca02c" if c else "#d62728" for c in contained]
    bars = ax1.bar([str(s) for s in seeds], pcts, color=colors)
    ax1.set_ylabel("% of grid burned")
    ax1.set_xlabel("Random seed")
    ax1.set_title("Seed reproducibility — combined_baseline (5 m/s wind, 100 drones, 10 firefighters)")
    ax1.set_ylim(0, 110)
    ax1.axhline(10, color="black", linestyle="--", alpha=0.4, label="containment threshold (10%)")
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", alpha=0.3)
    for bar, pct in zip(bars, pcts):
        ax1.text(bar.get_x() + bar.get_width() / 2, pct + 2, f"{pct:.1f}%", ha="center", fontsize=10)

    bars2 = ax2.bar([str(s) for s in seeds], sim_times, color=colors)
    ax2.set_ylabel("Simulated minutes to mission_complete")
    ax2.set_xlabel("Random seed")
    ax2.set_title("Time to mission_complete (sim minutes)\nGreen = real containment, Red = fuel exhaustion")
    ax2.grid(axis="y", alpha=0.3)
    for bar, t in zip(bars2, sim_times):
        ax2.text(bar.get_x() + bar.get_width() / 2, t + 0.8, f"{t:.1f} min", ha="center", fontsize=10)

    plt.tight_layout()
    out = FIG_DIR / "fig_seed_reproducibility.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_timeline_overlay() -> Path:
    """Burning cells vs sim time, comparing all major scenarios."""
    runs = [
        ("pure_fire", RESULTS / "option_b" / "pure_fire_ticks.csv", "#7f7f7f", "-"),
        ("no_drones (Option B)", RESULTS / "option_b" / "no_drones_ticks.csv", "#9467bd", "-"),
        ("rotor_only_baseline (Option B)", RESULTS / "option_b" / "rotor_only_baseline_ticks.csv", "#ff7f0e", "-"),
        ("drones_only", RESULTS / "option_b" / "drones_only_ticks.csv", "#1f77b4", "--"),
        ("combined_baseline (seed 42)", RESULTS / "combined_baseline_ticks.csv", "#2ca02c", "-"),
    ]

    fig, ax = plt.subplots(figsize=(11, 6))
    for label, path, color, ls in runs:
        if not path.exists():
            continue
        d = load_ticks(path)
        ax.plot(np.array(d["sim_time"]) / 60, d["cells_burning"], label=label, color=color, linestyle=ls, linewidth=1.6)

    ax.set_xlabel("Simulated time (minutes)")
    ax.set_ylabel("Cells burning (snapshot)")
    ax.set_title("Burning-cell trajectory across scenarios — 5 m/s wind, seed 42")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 60)
    plt.tight_layout()
    out = FIG_DIR / "fig_timeline_overlay.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_wash_sweep() -> Path:
    """Rotor wash strength sensitivity sweep."""
    runs = {
        "wash_half (25 J/s)": RESULTS / "sensitivity" / "wash" / "combined_wash_half_ticks.csv",
        "baseline (50 J/s)": RESULTS / "combined_baseline_ticks.csv",
        "wash_double (100 J/s)": RESULTS / "sensitivity" / "wash" / "combined_wash_double_ticks.csv",
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharex=True)
    colors = {"wash_half (25 J/s)": "#1f77b4", "baseline (50 J/s)": "#2ca02c", "wash_double (100 J/s)": "#d62728"}
    for label, path in runs.items():
        if not path.exists():
            continue
        d = load_ticks(path)
        t_min = np.array(d["sim_time"]) / 60
        ax1.plot(t_min, d["cells_burning"], label=label, color=colors[label], linewidth=1.5)
        ax2.plot(t_min, d["cells_burned"], label=label, color=colors[label], linewidth=1.5)

    ax1.set_xlabel("Simulated time (minutes)")
    ax1.set_ylabel("Cells burning (snapshot)")
    ax1.set_title("Burning cells over time — rotor wash strength sweep")
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)

    ax2.set_xlabel("Simulated time (minutes)")
    ax2.set_ylabel("Cells burned (cumulative)")
    ax2.set_title("Cumulative burned — rotor wash strength sweep")
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    out = FIG_DIR / "fig_wash_sweep.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig_high_wind_collapse() -> Path:
    """Show that rotor_only and combined produce identical curves at high wind."""
    runs = {
        "rotor_only_baseline (5 m/s)": (RESULTS / "rotor_only_baseline_ticks.csv", "#1f77b4", "-"),
        "combined_baseline (5 m/s)": (RESULTS / "combined_baseline_ticks.csv", "#2ca02c", "-"),
        "rotor_only_high_wind (10 m/s)": (RESULTS / "rotor_only_high_wind_ticks.csv", "#1f77b4", "--"),
        "combined_high_wind (10 m/s)": (RESULTS / "combined_high_wind_ticks.csv", "#2ca02c", "--"),
    }

    fig, ax = plt.subplots(figsize=(11, 6))
    for label, (path, color, ls) in runs.items():
        if not path.exists():
            continue
        d = load_ticks(path)
        t_min = np.array(d["sim_time"]) / 60
        ax.plot(t_min, d["cells_burned"], label=label, color=color, linestyle=ls, linewidth=1.6)

    ax.set_xlabel("Simulated time (minutes)")
    ax.set_ylabel("Cells burned (cumulative)")
    ax.set_title("High wind collapses both mechanisms to identical outcomes\nDashed = 10 m/s wind, Solid = 5 m/s wind")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 60)
    plt.tight_layout()
    out = FIG_DIR / "fig_high_wind_collapse.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    figures = [
        ("2x2 factorial", fig_2x2_factorial),
        ("seed reproducibility", fig_seed_reproducibility),
        ("timeline overlay", fig_timeline_overlay),
        ("wash sensitivity sweep", fig_wash_sweep),
        ("high wind collapse", fig_high_wind_collapse),
    ]
    for name, fn in figures:
        out = fn()
        print(f"  {name}: {out}")


if __name__ == "__main__":
    main()
