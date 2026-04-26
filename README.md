# Wildfire Drone Swarm — Acoustic Suppression Simulation

A multi-agent simulation evaluating coordinated UAV acoustic fire suppression under realistic wildfire conditions. This is the computational companion to a Master's thesis on the technical feasibility of drone-mounted subwoofer systems for wildfire suppression.

## What it models

- **Fire dynamics**: probabilistic cellular automaton with Rothermel-derived spread, ember transport, and burnout
- **Wind**: Ornstein-Uhlenbeck stochastic process with Gaussian spatial coherence
- **Drones**: 100-drone swarm with PID flight control, battery dynamics, directional acoustic emitters
- **Coordination**: Hungarian-algorithm task allocation, velocity-obstacle collision avoidance
- **Ground crew**: 10 firefighters applying water on the nearest fire

A 200x200 cell grid (400m x 400m at 2m/cell) advances at 10 Hz.

## Quick start

```bash
pip install -r requirements.txt

# Run the live simulation with visualization
python3 main.py

# Run a single headless scenario for benchmarking
python3 main.py --headless --ticks 5000

# Override scenario parameters
python3 main.py --wind-speed 8 --wind-dir 45 --drones 50
```

## Reproducing the thesis results

```bash
# Run all 7 experimental scenarios (~3 hours total wall time)
python3 run_experiments.py --max-ticks 5000

# Generate publication-quality figures from the per-tick CSVs
python3 generate_figures.py --format png
```

Figures land in `results/figures/`, including a LaTeX-ready summary table.

## Project layout

```
agents/         drone agent, battery, sensors, sound emitter, flight control
coordination/   task allocator, swarm coordinator, collision avoidance
environment/    grid, fire model, wind model, ember model, firefighters
physics/        acoustics, flight dynamics, geometry helpers
planner/        mission planner, target prioritization
visualization/  live matplotlib renderer
tests/          pytest unit tests
config.py       all tunable simulation constants
simulation.py   top-level orchestrator
main.py         CLI entry point
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).
