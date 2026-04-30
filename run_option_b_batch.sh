#!/usr/bin/env bash
# Option B re-runs: firefighter water extinguishes burning/ember cells.
# Re-runs only the four non-containment scenarios where firefighters can
# materially affect outcomes; combined_baseline scenarios are unchanged
# because drones contain the fire before firefighters arrive.

set -e
cd "$(dirname "$0")"

OUT_BASE=results_v2/option_b
mkdir -p "$OUT_BASE"

LOG="$OUT_BASE/batch.log"
echo "=== Option B batch started $(date) ===" | tee -a "$LOG"

for scenario in pure_fire drones_only no_drones rotor_only_baseline rotor_only_high_wind combined_high_wind; do
    if [ -f "$OUT_BASE/${scenario}_summary.json" ]; then
        echo "[skip] $scenario already has summary" | tee -a "$LOG"
        continue
    fi
    echo "--- $scenario seed=42 ---" | tee -a "$LOG"
    python3 run_experiments.py --scenario "$scenario" \
        --max-ticks 35000 --seed 42 \
        --output-dir "$OUT_BASE" 2>&1 | tee -a "$LOG"
done

echo "=== Option B batch finished $(date) ===" | tee -a "$LOG"
