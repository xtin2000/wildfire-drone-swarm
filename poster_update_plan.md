# Poster Update Plan — New Combined-Mechanism Findings

## Summary of changes needed

The current poster is built around acoustic-only, 5,000-tick data. The new findings (combined acoustic + rotor wash, 35,000-tick mission-complete result) are dramatically stronger and require updating most numerical claims and one structural section.

**Headline shift:**
- Before: "cuts ember activity by two-thirds and total fire damage by nearly three-quarters"
- After: "**eliminates 99% of airborne embers and fully contains the fire in 17 minutes**"

---

## Section-by-section updates

### HEADLINE (top of poster)

**Title** — keep as-is: *"Drone swarms against embers."*

**Subtitle** — REPLACE with:

> "A coordinated 100-UAV swarm equipped with both acoustic emission and rotor-wash aerodynamics fully contains a 400 m × 400 m grass fire in 17 simulated minutes — eliminating 99% of airborne embers and reducing total fire damage by 96%. Neither mechanism alone achieves containment; their combination is essential."

---

### SECTION 1: FLEET SIZE → REPLACE with MECHANISM COMPARISON

The existing fleet-size analysis (25/50/100/150 drones) was conducted with acoustic-only physics that we now know is incomplete. The new headline finding is the *mechanism comparison*, which is more compelling.

**New title:** "Why both mechanisms matter."

**New subtitle:** "Outcomes for a 100-drone swarm over a 35,000-tick (~58 simulated minutes) experiment on a 400 m × 400 m grass-fueled landscape with 5 m/s wind. Each drone contributes both directional acoustic emission and rotor downwash that is always present when hovering."

**New 4-box structure:**

| Box 1: NO DRONES | Box 2: ROTOR WASH ONLY | Box 3: COMBINED | Box 4: KEY INSIGHT |
|------------------|------------------------|-----------------|-------------------|
| **Uncontrolled fire** | **Modest improvement** | **Full containment** | **Mechanisms complement** |
| Peak burning: 3,930 | Peak burning: 3,185 | **Peak burning: 108** | Acoustic targets burning cells; |
| Total burned: 37,606 | Total burned: 37,525 | **Total burned: 1,388** | rotor wash targets embers. |
| Peak embers: 393 | Peak embers: 219 (-44%) | **Peak embers: 3 (-99%)** | Together they cover the full |
| Fire consumes 94% of grid | Fire still consumes 94% | **Mission complete in 17 min** | fire lifecycle. |

---

### SECTION 2: WIND OPERATING ENVELOPE → UPDATE NUMBERS

**Title:** keep — *"Where the swarm can fly."*
**Subtitle:** keep

**Wind band chart:** keep visual (0-5 / 5-8 / 8-12 / >12 m/s)

**Bullet text — REPLACE:**

OLD:
> "5 m/s baseline — 73% damage reduction with 100 drones; ember activity reduced from 70 to 23 peak cells."

NEW:
> "5 m/s baseline — 100 drones with combined mechanisms achieve full containment in 17 minutes (96% damage reduction)."

OLD:
> "10 m/s stress test — Wind doubles, damage rises sixfold. Fleet scaling to 150 cannot compensate."

NEW (PENDING — fill in once high_wind scenarios complete):
> "10 m/s stress test — [combined_high_wind result]. Wind compresses the operating envelope and [containment achieved / containment fails] under stress conditions."

OLD:
> "12 m/s safety cutoff — Drones autonomously return to base, consistent with manufacturer multirotor limits."

NEW: keep (no change needed)

OLD:
> "Wind feedforward control — PID + wind feedforward (gain 0.8) preserves emitter pointing accuracy in turbulence."

NEW: keep (no change needed)

---

### SECTION 3: DRONE CAPABILITIES → ADD ROTOR WASH SPECS

The current section is fine but should add rotor-wash specs to reflect the new physics. **Add two rows** to the spec table:

| Existing rows | (keep all) |
| Rotor wash | 11 m/s downwash @ disk |
| Wash footprint | 1.5–4 m radius @ 15 m altitude |

The drone illustration could optionally add a stylized downward airflow column to visualize rotor wash.

---

### "WORKING ENVELOPE" CALLOUT (right-side panel over hero image)

**Headline:** REPLACE *"Coordinated swarms work, at the right scale, in the right wind."*

NEW: "**Combined mechanisms make containment possible.**"

**Body text — REPLACE:**

OLD:
> "Below 100 drones, partial coverage worsens outcomes. Above 100, additional units add nothing. Above 12 m/s wind, drones must return to base. The operating window is narrow but real, and within it, the swarm is highly effective at suppressing the airborne embers responsible for most wildland-urban interface structure loss."

NEW:
> "Acoustic suppression alone cannot contain a wildfire — it only delays it. Rotor wash alone reduces ember activity but cannot suppress flame fronts. The combination of both mechanisms — both physically present on every multirotor drone — crosses a containment threshold neither can cross alone. Within the operating envelope (≤12 m/s wind, ≥100-drone fleet density), a coordinated swarm fully contains the modeled fire in 17 simulated minutes."

---

### SECTION 4: HUMAN + DRONE COORDINATION → MINOR UPDATES

The structure is fine. The AERIAL column already mentions rotor-wash deflection.

**Suggested updates to the AERIAL · DRONE SWARM column bullets:**

CURRENT:
- 40 Hz acoustic disruption of small flame kernels
- Rotor-wash deflection of lightweight embers
- Greedy task allocation every 2 s; VO collision avoidance
- Operates 30–300 m downwind of fireline

NEW:
- 40 Hz acoustic disruption of established burning cells
- Rotor-wash extinguishment of nascent ember-state ignitions
- Aerodynamic deflection of airborne embers in flight
- Greedy task allocation every 2 s; VO collision avoidance

---

## What I cannot directly do

I can't edit your PDF poster directly because I don't have the source design file. To apply these changes, you'll need to:

1. Open the poster in whatever tool you originally used (looks like Figma, Adobe InDesign/Illustrator, or similar)
2. Apply the text changes section-by-section per this plan
3. Optionally update the hero image / drone illustration to show downwash columns
4. Re-export to PDF

If you have the source file (e.g., `.fig`, `.ai`, `.indd`), share its location and I can document precise text changes by element.

Alternatively: if you'd like me to **build a fresh poster from scratch** in HTML/CSS or a print-ready format, I can do that — but the design is so well-crafted that I'd recommend keeping your original layout and just swapping the text/numbers.

---

## Pending data

The high_wind scenarios are still running. Once they complete:
- Section 2 (Wind Operating Envelope) bullet about high wind
- Working Envelope callout claim about "≤12 m/s wind" envelope (depends on whether combined still contains under 10 m/s wind)

I'll update this plan with concrete high-wind numbers once those scenarios finish.
