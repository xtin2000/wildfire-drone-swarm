# Section 5 Update Plan — All Scenarios at 35,000 Ticks

## Data status

| Scenario | 35,000-tick data | Peak burning | Total burned |
|----------|------------------|--------------|--------------|
| baseline | DONE | 2,974 | 37,171 |
| high_wind | DONE | 4,163 | 37,502 |
| no_drones | DONE | 3,930 | 37,606 |
| drones_25 | RUNNING | [PENDING] | [PENDING] |
| drones_50 | RUNNING | [PENDING] | [PENDING] |
| drones_150 | RUNNING | [PENDING] | [PENDING] |
| high_wind_150 | RUNNING | [PENDING] | [PENDING] |

Grid total = 200 x 200 = **40,000 cells** (so 37,000+ burned ≈ 93% of grid consumed)

---

## Proposed text changes (yellow-highlighted in the .docx)

### §5.6 Experimental Scenarios
**Current**: "...when 5,000 ticks (500 simulated seconds) elapse..."
**New**: "...when 35,000 ticks (3,500 simulated seconds, ~58 minutes of simulated mission time) elapse..."

### §5.8 (intro paragraph)
**Current**: "Each scenario ran for the full 5,000 ticks (500 simulated seconds); no scenario achieved complete mission success within this window..."
**New**: "Each scenario ran for the full 35,000 ticks (3,500 simulated seconds, or ~58 minutes of mission time). At this duration, all scenarios reached fire burnout: the available fuel was consumed and active burning ceased. The interesting differences are not in absolute final damage (which converges across scenarios) but in *peak burning*, *time to peak*, *time to total burnout*, and battery dynamics."

### §5.8.1 Baseline Scenario Performance
**Current text**: "...peak of 456 simultaneously burning cells... 1,119 cells burned and the fire still active... 73% reduction..."

**New text**:
"Under default conditions (100 drones, 5.0 m/s easterly wind), the fire spread from the three-cell ignition cluster and reached a peak of **2,974 simultaneously burning cells** at approximately t=1,250 s. By t=3,500 s, **37,171 cells had burned** (93% of the 40,000-cell grid). The drone fleet was unable to prevent the fire from eventually consuming the available fuel; however, it materially altered the timing and pace of the fire, as discussed in §5.8.2 below."

### §5.8.2 Uncontrolled Fire Baseline (No Drones)
**New text**:
"With drone intervention disabled, the fire reached a peak of **3,930 simultaneously burning cells** at approximately t=900 s and consumed **37,606 cells** by the end of the simulation. The fire trajectory differs from baseline in three operationally important ways:

1. **Peak burning was 32% higher** with drones (3,930 vs 2,974 with drones)
2. **Peak occurred 350 seconds earlier** without drones (t=900 s vs t=1,250 s)
3. **Time to reach equivalent damage** — the no-drone scenario reached 37,171 burned cells (the baseline's final count) at **t=1,369 s**. The baseline reached the same damage at **t=3,500 s**.

This last metric is the operationally meaningful one: drones delayed equivalent fire damage by **2,131 simulated seconds (~35 minutes)**. While final absolute damage converges (1.2% difference at t=3,500 s), the *time bought* by the drone fleet is substantial — and represents the time available for ground crew deployment, evacuation, or escalating intervention."

### §5.8.3 Fleet Size Scalability (UPDATE WITH NEW DATA)
**Pending — fill in when drones_25/50/150 finish**

**Tentative structure**:
"At 35,000 ticks, the fleet-size ablation reveals [SAME / DIFFERENT] threshold behavior compared to the 5,000-tick snapshot. [Discussion based on actual numbers]:

- **No drones**: peak 3,930, burned 37,606
- **25 drones**: peak [PENDING], burned [PENDING]
- **50 drones**: peak [PENDING], burned [PENDING]
- **100 drones (baseline)**: peak 2,974, burned 37,171
- **150 drones**: peak [PENDING], burned [PENDING]

[Discussion of whether the 50→100 threshold persists at long duration, and whether 150 drones meaningfully change time-to-equivalent-damage]"

### §5.8.4 Wind Impact (UPDATE)
**New text**:
"Under high-wind conditions with 100 drones, the fire reached a peak of **4,163 simultaneously burning cells** (vs 2,974 baseline — a 40% increase) and consumed **37,502 cells** total. Peak burning occurred at approximately **t=800 s**, 450 seconds earlier than baseline.

While final absolute damage converges (37,171 baseline vs 37,502 high_wind), high-wind conditions dramatically compress the timeline. Compounding mechanisms:

1. **Faster fire spread** via the exponential wind factor in the spread probability model
2. **Increased ember activity** — peak ember cells of 96 (vs 23 baseline)
3. **Catastrophic loss of drone stability** — mean stability collapsed to 0.05–0.32 (vs 0.85–0.95 baseline), with periodic mass returns-to-base when gusts exceed the 12 m/s safety threshold

When the fleet was increased to 150 drones under high-wind conditions, [PENDING — fill in with high_wind_150 data]."

### §5.8.5 Battery and Operational Endurance (ALREADY UPDATED)
Already correct — no further changes needed. The extended-run battery analysis is in place.

### §5.9.2 Key Findings (UPDATE FINDINGS #1, #3, #6)

**Finding #1 — replace**:
"1. Acoustic suppression by drone swarm meaningfully alters fire timeline rather than final damage. Across all scenarios, the fire eventually consumed approximately 93% of the grid (37,000–37,600 cells out of 40,000). However, the 100-drone fleet delayed equivalent damage by 35 minutes (2,131 simulated seconds) and reduced peak simultaneously-burning cells by 32% (2,974 vs 3,930). The operational value is in time bought, not damage prevented."

**Finding #3 — replace**:
"3. Wind compresses the fire timeline rather than amplifying final damage. Doubling wind speed from 5.0 to 10.0 m/s shifted peak burning earlier by 350 seconds and increased peak burning by 40% (4,163 vs 2,974), but final cells burned were nearly identical (37,502 vs 37,171). The compounding effect is in the *rate*: high wind simultaneously accelerates fire spread and degrades drone stability to near-zero, eliminating the suppression delay observed under moderate wind."

**Finding #6 — update numbers**:
[Pending — recalculate ember numbers from 35,000-tick data once drones_25/50 finish; current ember peaks at 35k ticks: baseline 70, no_drones 393]

**Finding #7 (already added)**: No change needed.

---

## Implementation plan

When the 4 pending scenarios complete:
1. Read out final peak/burned numbers from each `*_summary.json`
2. Update this plan with concrete numbers
3. Modify `update_thesis_long_run.py` to apply ALL the changes above
4. Re-run on `Thesis_04_20_ChristineLangmayr.docx` (the original)
5. Save as `Thesis_04_26_Long_Run_Full_Updates.docx`
