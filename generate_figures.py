#!/usr/bin/env python3
"""
generate_figures.py — Produce publication-quality figures from experiment CSVs.

Reads the per-tick CSV files produced by run_experiments.py and generates:
  1. Fire progression curves (burning cells over time)
  2. Drone fleet state breakdown over time
  3. Battery depletion curves
  4. Drone count scalability comparison
  5. Wind impact comparison
  6. Summary bar chart (total area burned)
  7. Ember detection and response timeline

Usage:
    python3 generate_figures.py                     # default results/ dir
    python3 generate_figures.py --results-dir results --format pdf
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for headless generation
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv


# ── Style ─────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def load_csv(path: Path) -> dict[str, np.ndarray]:
    """Load a tick CSV into a dict of numpy arrays."""
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return {}
    return {key: np.array([float(r[key]) for r in rows]) for key in rows[0]}


def load_summary(path: Path) -> list[dict]:
    """Load summary_table.csv."""
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)


# ── Figure generators ─────────────────────────────────────────────────────────

def fig_fire_progression(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 1: Burning + ember cells over simulation time for each scenario."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    for name, data in datasets.items():
        t = data["sim_time"]
        ax1.plot(t, data["cells_burning"], label=name, linewidth=1.5)
        ax2.plot(t, data["cells_ember"], label=name, linewidth=1.5)

    ax1.set_xlabel("Simulation time (s)")
    ax1.set_ylabel("Cells actively burning")
    ax1.set_title("(a) Active Fire Spread")
    ax1.legend(fontsize=8)

    ax2.set_xlabel("Simulation time (s)")
    ax2.set_ylabel("Ember cells detected")
    ax2.set_title("(b) Ember Activity")
    ax2.legend(fontsize=8)

    fig.suptitle("Fire Progression Across Scenarios", fontsize=14, y=1.02)
    plt.tight_layout()
    path = fig_dir / f"fig_fire_progression.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_total_fire(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 2: Total fire cells (burning + ember) — the key suppression metric."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for name, data in datasets.items():
        t = data["sim_time"]
        total = data["cells_burning"] + data["cells_ember"]
        ax.plot(t, total, label=name, linewidth=1.5)

    ax.set_xlabel("Simulation time (s)")
    ax.set_ylabel("Total active fire cells (burning + ember)")
    ax.set_title("Fire Containment: Total Active Fire Over Time")
    ax.legend()
    plt.tight_layout()
    path = fig_dir / f"fig_total_fire.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_drone_states(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 3: Stacked area chart of drone fleet state for baseline scenario."""
    for scenario_name in ["baseline", "high_wind"]:
        if scenario_name not in datasets:
            continue
        data = datasets[scenario_name]
        t = data["sim_time"]

        fig, ax = plt.subplots(figsize=(9, 5))
        states = ["drones_idle", "drones_transit", "drones_hovering",
                  "drones_emitting", "drones_returning", "drones_charging"]
        labels = ["Idle", "Transit", "Hovering", "Emitting", "Returning", "Charging"]
        colors = ["#cccccc", "#4dabf7", "#ffd43b", "#ff6b6b", "#69db7c", "#da77f2"]

        stack = np.array([data[s] for s in states])
        ax.stackplot(t, stack, labels=labels, colors=colors, alpha=0.85)

        ax.set_xlabel("Simulation time (s)")
        ax.set_ylabel("Number of drones")
        ax.set_title(f"Drone Fleet State Distribution ({scenario_name})")
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        path = fig_dir / f"fig_drone_states_{scenario_name}.{fmt}"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")


def fig_battery(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 4: Mean and min battery over time."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for name, data in datasets.items():
        if "mean_battery" not in data:
            continue
        t = data["sim_time"]
        ax.plot(t, data["mean_battery"] * 100, label=f"{name} (mean)",
                linewidth=1.5)
        ax.plot(t, data["min_battery"] * 100, label=f"{name} (min)",
                linewidth=1.0, linestyle="--", alpha=0.7)

    ax.axhline(y=20, color="red", linestyle=":", linewidth=1, label="RTB threshold (20%)")
    ax.set_xlabel("Simulation time (s)")
    ax.set_ylabel("Battery level (%)")
    ax.set_title("Drone Battery Depletion Over Time")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 105)
    plt.tight_layout()
    path = fig_dir / f"fig_battery.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_scalability(summary: list[dict], fig_dir: Path, fmt: str):
    """Fig 5: Bar chart — drone count vs total area burned & mission time."""
    # Filter to drone-count scenarios
    scale_scenarios = ["no_drones", "drones_25", "drones_50",
                       "baseline", "drones_150"]
    rows = [s for s in summary if s["scenario"] in scale_scenarios]
    rows.sort(key=lambda r: int(r["num_drones"]))

    if len(rows) < 2:
        print("  [SKIP] fig_scalability: not enough drone-count scenarios")
        return

    drone_counts = [int(r["num_drones"]) for r in rows]
    burned = [int(r["total_burned"]) for r in rows]
    peak_burning = [int(r["peak_burning"]) for r in rows]

    x = np.arange(len(drone_counts))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8, 5))
    bars1 = ax1.bar(x - width/2, burned, width, label="Total cells burned",
                    color="#ff6b6b", alpha=0.85)
    bars2 = ax1.bar(x + width/2, peak_burning, width, label="Peak burning cells",
                    color="#ffa94d", alpha=0.85)

    ax1.set_xlabel("Number of drones")
    ax1.set_ylabel("Cell count")
    ax1.set_title("Swarm Scalability: Drone Count vs Fire Damage")
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(d) for d in drone_counts])
    ax1.legend()

    # Add value labels on bars
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points",
                     ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax1.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points",
                     ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    path = fig_dir / f"fig_scalability.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_wind_comparison(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 6: Side-by-side comparison of baseline vs high wind."""
    pairs = [("baseline", "high_wind")]
    for a, b in pairs:
        if a not in datasets or b not in datasets:
            continue

        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

        for name, ls in [(a, "-"), (b, "--")]:
            data = datasets[name]
            t = data["sim_time"]
            axes[0].plot(t, data["cells_burning"], label=name, linestyle=ls, linewidth=1.5)
            axes[1].plot(t, data["cells_ember"], label=name, linestyle=ls, linewidth=1.5)
            axes[2].plot(t, data["cells_burned"], label=name, linestyle=ls, linewidth=1.5)

        axes[0].set_title("(a) Burning Cells")
        axes[1].set_title("(b) Ember Cells")
        axes[2].set_title("(c) Cumulative Burned")
        for ax in axes:
            ax.set_xlabel("Simulation time (s)")
            ax.legend(fontsize=9)
        axes[0].set_ylabel("Cell count")

        fig.suptitle("Wind Impact: Baseline (5 m/s) vs High Wind (10 m/s)",
                     fontsize=14, y=1.02)
        plt.tight_layout()
        path = fig_dir / f"fig_wind_comparison.{fmt}"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")


def fig_suppression_efficiency(datasets: dict, fig_dir: Path, fmt: str):
    """Fig 7: Ratio of emitting drones to burning cells — suppression pressure."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for name, data in datasets.items():
        if data["cells_burning"].max() == 0:
            continue
        t = data["sim_time"]
        # Avoid division by zero
        burning = np.maximum(data["cells_burning"], 1)
        ratio = data["drones_emitting"] / burning
        # Smooth with rolling average
        window = min(50, len(ratio) // 4) if len(ratio) > 10 else 1
        if window > 1:
            kernel = np.ones(window) / window
            ratio_smooth = np.convolve(ratio, kernel, mode="same")
        else:
            ratio_smooth = ratio
        ax.plot(t, ratio_smooth, label=name, linewidth=1.5)

    ax.set_xlabel("Simulation time (s)")
    ax.set_ylabel("Emitting drones per burning cell")
    ax.set_title("Suppression Pressure: Active Drones per Fire Cell")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = fig_dir / f"fig_suppression_efficiency.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_summary_bars(summary: list[dict], fig_dir: Path, fmt: str):
    """Fig 8: Horizontal bar chart comparing all scenarios on key metrics."""
    names = [s["scenario"] for s in summary]
    burned = [int(s["total_burned"]) for s in summary]
    peak = [int(s["peak_burning"]) for s in summary]
    sim_time = [float(s["sim_time_s"]) for s in summary]
    complete = [str(s["mission_complete"]).lower() == "true" for s in summary]

    fig, axes = plt.subplots(1, 3, figsize=(14, max(4, len(names) * 0.6)))

    y = np.arange(len(names))
    colors = ["#69db7c" if c else "#ff6b6b" for c in complete]

    axes[0].barh(y, burned, color=colors, alpha=0.85)
    axes[0].set_title("Total Cells Burned")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(names)

    axes[1].barh(y, peak, color="#ffa94d", alpha=0.85)
    axes[1].set_title("Peak Burning Cells")
    axes[1].set_yticks(y)
    axes[1].set_yticklabels([])

    axes[2].barh(y, sim_time, color="#4dabf7", alpha=0.85)
    axes[2].set_title("Simulation Time (s)")
    axes[2].set_yticks(y)
    axes[2].set_yticklabels([])

    fig.suptitle("Scenario Comparison Summary", fontsize=14, y=1.02)
    plt.tight_layout()
    path = fig_dir / f"fig_summary_bars.{fmt}"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ── LaTeX table generator ────────────────────────────────────────────────────

def generate_latex_table(summary: list[dict], fig_dir: Path):
    """Generate a LaTeX-formatted results table."""
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{Simulation results across experimental scenarios.}")
    lines.append(r"\label{tab:sim-results}")
    lines.append(r"\begin{tabular}{lrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Scenario & Drones & Wind & Sim Time & Peak & Peak & Total & Mission \\")
    lines.append(r"         &        & (m/s) & (s) & Burning & Embers & Burned & Complete \\")
    lines.append(r"\midrule")

    for s in summary:
        complete = "Yes" if str(s["mission_complete"]).lower() == "true" else "No"
        line = (f"{s['scenario'].replace('_', r'\\_')} & "
                f"{s['num_drones']} & "
                f"{float(s['wind_speed']):.1f} & "
                f"{float(s['sim_time_s']):.1f} & "
                f"{s['peak_burning']} & "
                f"{s['peak_ember']} & "
                f"{s['total_burned']} & "
                f"{complete} \\\\")
        lines.append(line)

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    path = fig_dir / "table_results.tex"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Saved LaTeX table: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate thesis figures from experiment data")
    parser.add_argument("--results-dir", type=str, default="results",
                        help="Directory containing CSV results")
    parser.add_argument("--format", type=str, default="png",
                        choices=["png", "pdf", "svg", "eps"],
                        help="Output figure format (default: png)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    fig_dir = results_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    # Load all scenario CSVs
    datasets = {}
    for csv_path in sorted(results_dir.glob("*_ticks.csv")):
        name = csv_path.stem.replace("_ticks", "")
        data = load_csv(csv_path)
        if data:
            datasets[name] = data
            print(f"Loaded {name}: {len(data['tick'])} ticks")

    if not datasets:
        print(f"ERROR: No CSV files found in {results_dir}/")
        print("Run run_experiments.py first.")
        return

    # Load summary
    summary_path = results_dir / "summary_table.csv"
    summary = load_summary(summary_path) if summary_path.exists() else []

    fmt = args.format
    print(f"\nGenerating figures ({fmt} format) in {fig_dir}/\n")

    fig_fire_progression(datasets, fig_dir, fmt)
    fig_total_fire(datasets, fig_dir, fmt)
    fig_drone_states(datasets, fig_dir, fmt)
    fig_battery(datasets, fig_dir, fmt)
    fig_wind_comparison(datasets, fig_dir, fmt)
    fig_suppression_efficiency(datasets, fig_dir, fmt)

    if summary:
        fig_scalability(summary, fig_dir, fmt)
        fig_summary_bars(summary, fig_dir, fmt)
        generate_latex_table(summary, fig_dir)

    print(f"\nDone! All figures saved to {fig_dir}/")
    print(f"Total figures generated: {len(list(fig_dir.glob(f'*.{fmt}')))}")


if __name__ == "__main__":
    main()
