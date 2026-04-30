#!/usr/bin/env bash
# Sensitivity test batch — runs overnight after the long-run experiments complete.
# Outputs go to results_v2/sensitivity/ to keep the headline data isolated.

set -e
cd "$(dirname "$0")"

OUT_BASE=results_v2/sensitivity
mkdir -p "$OUT_BASE"

LOG="$OUT_BASE/batch.log"
echo "=== Sensitivity batch started $(date) ===" | tee -a "$LOG"

# ── Test 3: seed reproducibility (combined_baseline at seeds 43, 44, 45, 46) ──
for seed in 43 44 45 46; do
    DIR="$OUT_BASE/seed_$seed"
    if [ -f "$DIR/combined_baseline_summary.json" ]; then
        echo "[skip] seed=$seed already has summary" | tee -a "$LOG"
        continue
    fi
    mkdir -p "$DIR"
    echo "--- combined_baseline seed=$seed ---" | tee -a "$LOG"
    python3 run_experiments.py --scenario combined_baseline \
        --max-ticks 35000 --seed "$seed" \
        --output-dir "$DIR" 2>&1 | tee -a "$LOG"
done

# ── Test 1: rotor wash strength sweep ──
for scenario in combined_wash_half combined_wash_double; do
    DIR="$OUT_BASE/wash"
    if [ -f "$DIR/${scenario}_summary.json" ]; then
        echo "[skip] $scenario already has summary" | tee -a "$LOG"
        continue
    fi
    mkdir -p "$DIR"
    echo "--- $scenario seed=42 ---" | tee -a "$LOG"
    python3 run_experiments.py --scenario "$scenario" \
        --max-ticks 35000 --seed 42 \
        --output-dir "$DIR" 2>&1 | tee -a "$LOG"
done

echo "=== Sensitivity batch finished $(date) ===" | tee -a "$LOG"
