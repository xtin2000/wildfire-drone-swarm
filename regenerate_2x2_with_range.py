#!/usr/bin/env python3
"""Regenerate the 2x2 factorial figure with a min/max range bar on the combined cell.

The combined cell aggregates over the 5 random-seed trials of combined_baseline:
seeds 42, 43, 44, 45, 46. The bar height is set to the median; a thin vertical
line spans the observed min and max to communicate the bimodal outcome
(3 contained / 2 fuel-exhausted).
"""

from __future__ import annotations
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


def burn_pct(summary_path: Path) -> float:
    s = json.loads(summary_path.read_text())
    return 100 * s["total_burned"] / 40000


def main() -> None:
    pure_pct = burn_pct(RESULTS / "option_b" / "pure_fire_summary.json")
    no_drones_pct = burn_pct(RESULTS / "option_b" / "no_drones_summary.json")
    drones_only_pct = burn_pct(RESULTS / "option_b" / "drones_only_summary.json")

    # Combined-cell variance: aggregate over seeds 42-46
    combined_paths = [
        RESULTS / "combined_baseline_summary.json",  # seed 42
        RESULTS / "sensitivity" / "seed_43" / "combined_baseline_summary.json",
        RESULTS / "sensitivity" / "seed_44" / "combined_baseline_summary.json",
        RESULTS / "sensitivity" / "seed_45" / "combined_baseline_summary.json",
        RESULTS / "sensitivity" / "seed_46" / "combined_baseline_summary.json",
    ]
    combined_pcts = [burn_pct(p) for p in combined_paths]
    combined_median = float(np.median(combined_pcts))
    combined_min = min(combined_pcts)
    combined_max = max(combined_pcts)
    n_contained = sum(1 for v in combined_pcts if v < 10.0)

    print(f"Combined-cell seed values: {[f'{v:.2f}' for v in combined_pcts]}")
    print(f"  median: {combined_median:.2f}, min: {combined_min:.2f}, max: {combined_max:.2f}")
    print(f"  contained ({n_contained}/{len(combined_pcts)})")

    drones = ["No drones", "100 drones"]
    firefighters = ["No firefighters", "10 firefighters"]
    matrix = np.array(
        [
            [pure_pct, no_drones_pct],
            [drones_only_pct, combined_median],
        ]
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(drones))
    width = 0.35

    ax.bar(x - width / 2, matrix[:, 0], width, label=firefighters[0], color="#d62728")
    ax.bar(x + width / 2, matrix[:, 1], width, label=firefighters[1], color="#2ca02c")

    # Min/max range marker on the combined cell only (100 drones, 10 firefighters)
    cx = x[1] + width / 2  # combined cell x position
    ax.plot(
        [cx, cx], [combined_min, combined_max],
        color="black", linewidth=1.5, zorder=10,
    )
    cap_w = width * 0.15
    ax.plot([cx - cap_w, cx + cap_w], [combined_min, combined_min],
            color="black", linewidth=1.5, zorder=10)
    ax.plot([cx - cap_w, cx + cap_w], [combined_max, combined_max],
            color="black", linewidth=1.5, zorder=10)
    ax.annotate(
        f"N=5 seeds\n{n_contained} of {len(combined_pcts)} contained\nrange {combined_min:.1f}–{combined_max:.1f}%",
        xy=(cx, combined_max),
        xytext=(cx + 0.15, combined_max + 8),
        fontsize=8.5,
        ha="left",
        va="top",
    )

    # Numeric labels on the bars
    for i, d in enumerate(drones):
        for j, f in enumerate(firefighters):
            v = matrix[i, j]
            xpos = x[i] + (j - 0.5) * width
            label = f"{v:.1f}%"
            if i == 1 and j == 1:
                label = f"median {v:.1f}%"
            ax.text(xpos, v + 1.5, label, ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(drones)
    ax.set_ylabel("% of grid burned (after 35,000 ticks or mission complete)")
    ax.set_ylim(0, 115)
    ax.set_title(
        "Containment factorial — drones × firefighters (5 m/s wind)\nOption B firefighter physics"
    )
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    out = FIG_DIR / "fig_2x2_factorial.png"
    plt.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
