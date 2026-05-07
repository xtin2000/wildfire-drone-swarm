#!/usr/bin/env bash
# Run combined_baseline at seeds 42-46 under the heavy-lift heat-hardened
# platform configuration: DRONE_MASS=8, ROTOR_TOTAL_AREA=0.30,
# DRONE_MAX_THRUST=130, DRONE_CRUISE_ALT=5, SAFE_FIRE_DISTANCE=2,
# MAX_FIRE_DISTANCE=5. Conservative rotor-wash rates (10 J/s ember, 0 J/s
# burning) carried over from the previous configuration.

set -e
cd "$(dirname "$0")"

OUT_BASE=results_v2/option_b/heavy_lift
mkdir -p "$OUT_BASE"

LOG="$OUT_BASE/batch.log"
echo "=== Heavy-lift heat-hardened seed batch started $(date) ===" | tee -a "$LOG"

for seed in 42 43 44 45 46; do
    DIR="$OUT_BASE/seed_$seed"
    if [ -f "$DIR/combined_baseline_summary.json" ]; then
        echo "[skip] seed=$seed already has summary" | tee -a "$LOG"
        continue
    fi
    mkdir -p "$DIR"
    echo "--- combined_baseline (heavy-lift) seed=$seed ---" | tee -a "$LOG"
    python3 run_experiments.py --scenario combined_baseline \
        --max-ticks 35000 --seed "$seed" \
        --output-dir "$DIR" 2>&1 | tee -a "$LOG"
done

echo "=== Heavy-lift heat-hardened seed batch finished $(date) ===" | tee -a "$LOG"
