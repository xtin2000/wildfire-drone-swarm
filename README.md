# Wildfire Drone Swarm

Multi-agent simulation framework for evaluating coordinated UAV-swarm strategies against wildfires. Models a swarm of 100 drones using both directional acoustic emission and rotor-wash aerodynamics, deployed alongside 10 ground firefighters against a probabilistic cellular-automaton fire on a 200×200 cell grid.

This is the open-source release accompanying a Master's thesis on the technical feasibility of coordinated drone-based wildfire suppression.

## What it models

Six concurrent physical processes integrated under a single time-stepped loop at 10 Hz:

- **Fire spread**: 8-neighbour cellular automaton with Rothermel-inspired wind factor and stochastic ignition probability
- **Wind**: Ornstein-Uhlenbeck stochastic process with Gaussian spatial smoothing
- **Embers**: Lagrangian particle physics (lofting, ballistic flight, landing ignition) — the spotting mechanism
- **Drone flight**: 3-axis PID with anti-windup and wind feedforward; 6-state FSM per drone (IDLE → TRANSIT → HOVERING → EMITTING → RETURNING → CHARGING)
- **Acoustic suppression**: SPL-threshold model with directional emitter physics (200 W, 40 Hz, cardioid)
- **Rotor-wash aerodynamics**: actuator-disk theory with linear wake decay; effective on ember-state cells and airborne ember particles

The grid is 400 m × 400 m at 2 m per cell. Simulations are deterministic for any given random seed.

## Multi-agent architecture

Two autonomous agent populations:

- **100 drone agents** with private state machines, sensors, batteries, and flight controllers
- **10 firefighter agents** that walk toward the nearest active fire

Coordination is hybrid. State machines, flight control, sensing, and return-to-base decisions are decentralised at each agent. Task allocation (Hungarian algorithm via `scipy.optimize.linear_sum_assignment`) and collision avoidance (KDTree-accelerated, ORCA-inspired reciprocal velocity-obstacle) run centrally at each 2-second coordination cycle.

## Quick start

```bash
pip install -r requirements.txt

# Visualised run with default scenario
python3 main.py

# Headless run capped at 5000 ticks
python3 main.py --headless --ticks 5000

# Override scenario parameters
python3 main.py --wind-speed 8 --wind-dir 45 --drones 50 --seed 7

# Custom ignition points
python3 main.py --fire-start 80,90 95,100 110,85
```

## Reproducing the thesis experiments

Headless batch experiments run named scenarios that apply config overrides:

```bash
# Single scenario at the 35,000-tick long-run window
python3 run_experiments.py --scenario combined_baseline \
                           --max-ticks 35000 --seed 42 \
                           --output-dir results_v2/

# Multiple scenarios in sequence
python3 run_experiments.py \
    --scenario combined_baseline rotor_only_baseline no_drones \
    --max-ticks 35000

# Pre-built batch scripts for the experimental sets in the thesis
bash run_heavy_lift_seeds_batch.sh    # N=5 seed reproducibility, final config
bash run_sensitivity_batch.sh         # rotor-wash strength + seed sweep
bash run_option_b_batch.sh            # 2×2 factorial under Option B firefighters
```

Each scenario produces a per-tick CSV of fleet metrics and a summary JSON.

Named scenarios available in `run_experiments.py`:

| Scenario | Description |
|---|---|
| `combined_baseline` | 100 drones, both mechanisms, 5 m/s wind |
| `combined_high_wind` | 100 drones, both mechanisms, 10 m/s wind |
| `rotor_only_baseline` | 100 drones, rotor wash only, 5 m/s |
| `rotor_only_high_wind` | 100 drones, rotor wash only, 10 m/s |
| `no_drones` | 0 drones, 10 firefighters (counterfactual) |
| `pure_fire` | 0 drones, 0 firefighters |
| `drones_only` | 100 drones, 0 firefighters |
| `combined_drones_{25,50,150}` | fleet-size variants of combined |
| `combined_wash_{half,double}` | rotor-wash strength sensitivity |
| `combined_no_ember_drag` | airborne-ember-drag ablation |

## Project layout

```
agents/         drone, battery, sensors, sound emitter, flight controller
coordination/   task allocator, swarm coordinator, collision avoidance
environment/    grid, fire model, wind model, ember model, firefighters
physics/        acoustics, aerodynamics, flight dynamics, geometry
planner/        mission planner, target prioritization
visualization/  matplotlib live renderer
tests/          pytest unit tests

config.py                 tunable simulation constants
simulation.py             top-level simulation orchestrator
main.py                   visualised CLI entry point
run_experiments.py        headless batch runner with named scenarios
_run_single_scenario.py   subprocess wrapper for clean module state
```

The `update_thesis_*.py` scripts and `generate_*_figures.py` files in the repository root were used to produce the accompanying thesis; they are not part of the simulation framework.

## Tests

```bash
python3 -m pytest tests/ -q
```

Covers the fire-spread cellular automaton, acoustic SPL formulas, PID controller, and Hungarian task allocator.

## License

MIT — see [LICENSE](LICENSE).
