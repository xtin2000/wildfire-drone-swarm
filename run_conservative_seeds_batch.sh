#!/usr/bin/env bash
# Re-run combined_baseline at seeds 43-46 under the conservative + tight-geometry
# configuration (ROTOR_WASH_EMBER_RATE=10, ROTOR_WASH_BURNING_RATE=0,
# SAFE_FIRE_DISTANCE=5, MAX_FIRE_DISTANCE=10). Seed 42 is already done in
# results_v2/option_b/conservative/.

set -e
cd "$(dirname "$0")"

OUT_BASE=results_v2/option_b/conservative_seeds
mkdir -p "$OUT_BASE"

LOG="$OUT_BASE/batch.log"
echo "=== Conservative-config seed batch started $(date) ===" | tee -a "$LOG"

for seed in 43 44 45 46; do
    DIR="$OUT_BASE/seed_$seed"
    if [ -f "$DIR/combined_baseline_summary.json" ]; then
        echo "[skip] seed=$seed already has summary" | tee -a "$LOG"
        continue
    fi
    mkdir -p "$DIR"
    echo "--- combined_baseline (conservative + tight) seed=$seed ---" | tee -a "$LOG"
    python3 run_experiments.py --scenario combined_baseline \
        --max-ticks 35000 --seed "$seed" \
        --output-dir "$DIR" 2>&1 | tee -a "$LOG"
done

echo "=== Conservative-config seed batch finished $(date) ===" | tee -a "$LOG"
