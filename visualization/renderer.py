"""
SimRenderer: Matplotlib-based real-time animated visualisation.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import config


@dataclass
class RenderSnapshot:
    cell_state: np.ndarray       # (H, W) uint8
    burn_intensity: np.ndarray   # (H, W) float32
    wind_field: np.ndarray       # (H, W, 2)
    drone_positions: np.ndarray  # (N, 3)
    drone_headings: np.ndarray   # (N,) radians
    drone_states: list           # list[DroneState]
    drone_batteries: np.ndarray  # (N,)
    emitting_mask: np.ndarray    # (N,) bool
    firefighter_positions: list  # list[(x,y)]
    metrics: object              # SimMetrics


class SimRenderer:
    def __init__(self):
        matplotlib.rcParams["toolbar"] = "None"
        W = config.GRID_WIDTH * config.CELL_SIZE
        H_world = config.GRID_HEIGHT * config.CELL_SIZE

        self.fig = plt.figure(
            figsize=(config.WINDOW_WIDTH / config.FIG_DPI,
                     config.WINDOW_HEIGHT / config.FIG_DPI),
            dpi=config.FIG_DPI,
        )
        self.fig.patch.set_facecolor("#1a1a2e")

        # Layout: main map (left) + status panel (right)
        gs = self.fig.add_gridspec(2, 2, width_ratios=[3, 1], hspace=0.3, wspace=0.25)
        self.ax_main   = self.fig.add_subplot(gs[:, 0])
        self.ax_info   = self.fig.add_subplot(gs[0, 1])
        self.ax_bat    = self.fig.add_subplot(gs[1, 1])

        for ax in [self.ax_main, self.ax_info, self.ax_bat]:
            ax.set_facecolor("#16213e")

        self.ax_main.set_title("Wildfire Drone Swarm — Acoustic Suppression",
                               color="white", fontsize=10)
        self.ax_main.set_xlim(0, W)
        self.ax_main.set_ylim(0, H_world)
        self.ax_main.set_aspect("equal")
        self.ax_main.tick_params(colors="gray")

        # Fire heatmap
        self._fire_im = self.ax_main.imshow(
            np.zeros((config.GRID_HEIGHT, config.GRID_WIDTH, 4), dtype=np.float32),
            origin="lower",
            extent=[0, W, 0, H_world],
            interpolation="nearest",
            zorder=1,
        )

        # Wind quiver (downsampled)
        ds = config.QUIVER_DOWNSAMPLE
        xs = np.arange(ds // 2, config.GRID_WIDTH, ds) * config.CELL_SIZE
        ys = np.arange(ds // 2, config.GRID_HEIGHT, ds) * config.CELL_SIZE
        self._Xq, self._Yq = np.meshgrid(xs, ys)
        self._wind_q = self.ax_main.quiver(
            self._Xq, self._Yq,
            np.zeros_like(self._Xq), np.zeros_like(self._Yq),
            color="cyan", alpha=0.4, scale=50, zorder=2, width=0.002,
        )

        # Drone scatter
        self._drone_sc = self.ax_main.scatter(
            [], [], c="lime", s=12, zorder=5, label="Drone"
        )
        # Emitting drones
        self._emit_sc = self.ax_main.scatter(
            [], [], c="yellow", s=30, marker="*", zorder=6, label="Emitting"
        )
        # Firefighters
        self._ff_sc = self.ax_main.scatter(
            [], [], c="deepskyblue", s=50, marker="^", zorder=7, label="Firefighter"
        )

        self.ax_main.legend(loc="upper right", fontsize=7, facecolor="#1a1a2e",
                            labelcolor="white", framealpha=0.7)

        # Info panel
        self.ax_info.set_title("Metrics", color="white", fontsize=9)
        self.ax_info.axis("off")
        self._info_text = self.ax_info.text(
            0.05, 0.95, "", transform=self.ax_info.transAxes,
            va="top", color="white", fontsize=8, fontfamily="monospace",
        )

        # Battery bar chart
        self.ax_bat.set_title("Battery (sample 20)", color="white", fontsize=9)
        self.ax_bat.set_xlim(0, 1)
        self.ax_bat.set_ylim(-0.5, 19.5)
        self.ax_bat.tick_params(colors="gray", labelsize=6)
        self.ax_bat.set_xlabel("Charge", color="gray", fontsize=7)
        self._bat_bars = self.ax_bat.barh(
            range(20), [1.0] * 20, color="green", height=0.7
        )

        plt.tight_layout()

    def update(self, snap: RenderSnapshot) -> None:
        self._draw_fire(snap)
        self._draw_wind(snap)
        self._draw_drones(snap)
        self._draw_firefighters(snap)
        self._draw_info(snap)
        self._draw_batteries(snap)
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    # ── drawing helpers ───────────────────────────────────────────────────────

    def _draw_fire(self, snap: RenderSnapshot) -> None:
        """Render fire state as RGBA overlay."""
        H, W = config.GRID_HEIGHT, config.GRID_WIDTH
        rgba = np.zeros((H, W, 4), dtype=np.float32)

        burning = snap.cell_state == config.STATE_BURNING
        ember   = snap.cell_state == config.STATE_EMBER
        burned  = snap.cell_state == config.STATE_BURNED

        # Burning: orange-red based on intensity
        bi = snap.burn_intensity
        rgba[burning, 0] = 1.0
        rgba[burning, 1] = 0.3 * (1.0 - bi[burning])
        rgba[burning, 2] = 0.0
        rgba[burning, 3] = 0.8

        # Embers: bright yellow, low intensity
        rgba[ember, 0] = 1.0
        rgba[ember, 1] = 1.0
        rgba[ember, 2] = 0.0
        rgba[ember, 3] = 0.6

        # Burned: dark gray
        rgba[burned, 0] = 0.3
        rgba[burned, 1] = 0.3
        rgba[burned, 2] = 0.3
        rgba[burned, 3] = 0.5

        self._fire_im.set_data(rgba)

    def _draw_wind(self, snap: RenderSnapshot) -> None:
        ds = config.QUIVER_DOWNSAMPLE
        wf = snap.wind_field
        u = wf[::ds, ::ds, 0]
        v = wf[::ds, ::ds, 1]
        self._wind_q.set_UVC(u, v)

    def _draw_drones(self, snap: RenderSnapshot) -> None:
        pos = snap.drone_positions
        emitting = snap.emitting_mask

        all_xy = pos[:, :2]
        emit_xy = pos[emitting, :2]

        self._drone_sc.set_offsets(all_xy)
        self._emit_sc.set_offsets(emit_xy if len(emit_xy) > 0 else np.empty((0, 2)))

    def _draw_firefighters(self, snap: RenderSnapshot) -> None:
        if snap.firefighter_positions:
            ff_xy = np.array(snap.firefighter_positions)
            self._ff_sc.set_offsets(ff_xy)
        else:
            self._ff_sc.set_offsets(np.empty((0, 2)))

    def _draw_info(self, snap: RenderSnapshot) -> None:
        m = snap.metrics
        from agents.drone import DroneState
        txt = (
            f"Time:      {m.sim_time:6.1f}s\n"
            f"Burning:   {m.cells_currently_burning:4d} cells\n"
            f"Embers:    {m.embers_detected:4d} cells\n"
            f"Burned:    {m.cells_burned:4d} cells\n"
            f"Emitting:  {m.drones_emitting:4d} drones\n"
            f"Returning: {m.drones_returning:4d} drones\n"
        )
        self._info_text.set_text(txt)

    def _draw_batteries(self, snap: RenderSnapshot) -> None:
        sample = snap.drone_batteries[:20]
        for i, (bar, val) in enumerate(zip(self._bat_bars, sample)):
            bar.set_width(float(val))
            color = "green" if val > 0.5 else ("orange" if val > 0.2 else "red")
            bar.set_color(color)

    def show(self) -> None:
        plt.show(block=False)
        plt.pause(0.001)

    def close(self) -> None:
        plt.close(self.fig)
