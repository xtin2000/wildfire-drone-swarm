# Sensitivity Test Plan — Combined-Mechanism Robustness

Drafted overnight 2026-04-26. Runs once `combined_high_wind` completes.

## Goal

The headline finding — *combined mechanism contains the fire in ~17 min, neither alone does* — comes from a single seed (42), a single fire-size, and a single rotor-wash strength setting. Reviewers will ask whether this is robust. These four sensitivity probes address the most plausible robustness questions before the thesis defense.

## Test 1 — Rotor wash strength sweep

**Question**: Does containment depend on the specific rotor-wash suppression rate values? At what point does the mechanism stop working?

**Knobs to vary** (`config.py`):
- `ROTOR_WASH_EMBER_RATE` (currently 50.0 J/s) → sweep 0.5×, 1×, 2× = {25, 50, 100}
- Hold `ROTOR_WASH_BURNING_RATE` at 5.0 J/s
- Hold `ROTOR_WASH_EMBER_DRAG` at 1.5 m/s²

**Scenarios to add** to `SCENARIOS` dict in `run_experiments.py`:

```python
"combined_wash_half": {
    "description": "Combined mechanisms, rotor wash ember rate halved (25 J/s)",
    "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True,
                  "ROTOR_WASH_EMBER_RATE": 25.0},
},
"combined_wash_double": {
    "description": "Combined mechanisms, rotor wash ember rate doubled (100 J/s)",
    "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True,
                  "ROTOR_WASH_EMBER_RATE": 100.0},
},
```

(Baseline `combined_baseline` is the 1× point — already done.)

## Test 2 — Initial fire size sweep

**Question**: Does the result hold if the initial fire is larger, or is the swarm only winning because it catches a small ignition early?

**Approach**: The current sim ignites a 3-cell cluster. Add scenarios that ignite a 9-cell and 25-cell cluster. **Need to check `simulation.py` and `environment/fire_model.py`** for the ignition init code — currently appears to be hard-coded; may need a config knob like `INITIAL_FIRE_RADIUS` that the scenario overrides.

**Tentative scenarios**:
```python
"combined_fire_medium": {
    "description": "Combined, 9-cell ignition cluster (3× larger start)",
    "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True,
                  "INITIAL_FIRE_CELLS": 9},
},
"combined_fire_large": {
    "description": "Combined, 25-cell ignition cluster (~8× larger start)",
    "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True,
                  "INITIAL_FIRE_CELLS": 25},
},
```

**Caveat**: This requires a small code change to make ignition size configurable. Defer execution until I can read `_run_single_scenario.py` and understand the ignition path. **Do NOT modify code while the running experiment is in progress** — wait for PID 50105 to finish first.

## Test 3 — Seed reproducibility (N=5)

**Question**: How tight is the spread? A single-seed result is anecdotal; 5 seeds give a coefficient of variation that's defensible.

**Approach**: Re-run `combined_baseline` at seeds {42, 43, 44, 45, 46}. Already supported by `--seed` flag; `_run_single_scenario.py` uses it.

**Execution**:
```bash
for seed in 42 43 44 45 46; do
  python3 run_experiments.py --scenario combined_baseline \
    --max-ticks 35000 --seed "$seed" \
    --output-dir results_v2/seed_$seed
done
```

(Seed 42 is already done — copy from `results_v2/combined_baseline_*` to `results_v2/seed_42/` to keep the layout consistent.)

**Metrics to extract**: time-to-containment (sim seconds), peak burning, peak embers, total burned. Compute mean ± std.

## Test 4 — Ember-fix isolation

**Question**: How much of the combined-mechanism win comes from the *new ember-downwash interaction* (the diff in `environment/ember_model.py` that lets rotor wash drag airborne embers down) vs. the *baseline rotor-wash effect on ground cells*?

**Approach**: Add a config toggle `ROTOR_WASH_EMBER_DRAG_ENABLED` (default `True`); when `False`, skip the `_rotor_downwash_accel` term in `EmberModel._advance`. Then run `combined_baseline` with this disabled.

**Required code change** (deferred until current run finishes):
1. Add `ROTOR_WASH_EMBER_DRAG_ENABLED = True` to `config.py`
2. In `environment/ember_model.py:_collect_wash_drones`, return `None` early if `not config.ROTOR_WASH_EMBER_DRAG_ENABLED`
3. Add scenario:
```python
"combined_no_ember_drag": {
    "description": "Combined mechanisms, but no rotor-downwash drag on airborne embers",
    "overrides": {"ROTOR_WASH_ENABLED": True, "ACOUSTIC_ENABLED": True,
                  "ROTOR_WASH_EMBER_DRAG_ENABLED": False},
},
```

If this scenario *still contains* the fire, the airborne-ember drag term isn't load-bearing and the headline is robust. If it *fails*, the airborne-ember term is the load-bearing piece — which is interesting but means we should reframe the thesis claim around that specific mechanism.

## Execution order (when ready)

1. Test 3 (seed reproducibility) — fewest unknowns, just re-runs with --seed. **Run first**.
2. Test 1 (rotor wash strength) — add 2 SCENARIOS entries, no other code change.
3. Test 4 (ember-fix isolation) — needs config toggle + 1 line in ember_model.py.
4. Test 2 (initial fire size) — needs ignition path investigation; lowest priority overnight.

Total run-time budget: each combined_baseline takes ~1,000 sim seconds (~17 min real-time wall-clock if early-terminating). 5 seeds + 2 wash-strength + 1 ember-isolation = 8 runs. Worst case ~2-3 hours total if all early-terminate.
