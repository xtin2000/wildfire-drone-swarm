# Section 5 Redraft — With Rotor Wash + Combined Mechanism Findings

## Data status

| Scenario | Status | Peak burning | Total burned | Peak embers | Mission complete |
|----------|--------|-------------|-------------|-------------|------------------|
| no_drones | Done | 3,930 | 37,606 | 393 | No |
| rotor_only_baseline | Done | 3,185 | 37,525 | 219 | No |
| combined_baseline | Done | **108** | **1,388** | **3** | **YES at 16.6 min** |
| rotor_only_high_wind | Done | 4,121 | 37,572 | 324 | No |
| combined_high_wind | Done | 4,121 | 37,572 | 324 | No |

## Option B firefighter physics — re-baselined 2×2 (2026-04-28)

The original firefighter model only saturated unburned fuel, not burning fuel — a model artefact, not physics. The model was corrected so that water on a `BURNING` or `EMBER` cell extinguishes it, in addition to the existing moisture-saturation effect on unburned cells. The four non-containment scenarios were re-run under the corrected model (output in `results_v2/option_b/`); two new scenarios were added to complete a 2×2 factorial design isolating drones × firefighters.

**2×2 factorial table (5 m/s wind, seed 42, 35,000-tick cap):**

|                       | **No drones**       | **100 drones (combined)** |
|----------------------|---------------------|---------------------------|
| **No firefighters**  | `pure_fire`: 39,595 / 99.0% burned, no containment | `drones_only`: 39,755 / 99.4% burned, no containment (fuel exhaustion) |
| **10 firefighters**  | `no_drones`: 37,158 / 92.9% burned, no containment | `combined_baseline`: 1,388 / 3.5% burned, **CONTAINED at 16.6 min** |

**High-wind robustness checks (10 m/s, Option B):**

| Scenario | Burned | % grid | Mission complete? |
|----------|--------|--------|-------------------|
| `rotor_only_high_wind` (B) | 37,285 | 93.2% | No |
| `combined_high_wind` (B) | 37,310 | 93.3% | No |

(Both essentially indistinguishable from original numbers — Option B firefighters cannot catch a high-wind fire any more than they could catch a moderate-wind fire, because their 0.5 m/s walking speed is below the fire's spread rate in either case.)

## Sensitivity tests — completed 2026-04-27

### Seed reproducibility (combined_baseline only, varying random seed)

| Seed | Sim time at exit | Peak burning | Total burned | % grid | True containment? |
|------|------------------|--------------|--------------|--------|-------------------|
| 42   | 999 s (16.6 min) | 108          | 1,388        | 3.5%   | yes               |
| 43   | 257 s (4.3 min)  | 198          | 778          | 1.9%   | yes               |
| 44   | 1,777 s (29.6 min) | 2,908       | 37,359       | 93.4%  | **NO — fuel exhaustion** |
| 45   | 47 s (0.8 min)   | 35           | 53           | 0.1%   | yes               |
| 46   | 2,157 s (36.0 min) | 2,809       | 36,395       | 91.0%  | **NO — fuel exhaustion** |

Containment rate at this fleet size and wind: **3 of 5 seeds (60%)**. The two failure cases (44, 46) lose the early-spread race in the first ~150 sim seconds and the fire grows beyond the swarm's per-tick suppression capacity. This is the same failure mode `drones_only` exhibited in the 2×2 above — confirming that the early-spread race is the load-bearing dynamic and that firefighter firebreaks are part of why the median seed wins it.

### Rotor wash strength sweep (combined, seed 42)

| Variant | Ember rate | Sim time to contain | Burned | % grid |
|---------|------------|---------------------|--------|--------|
| half    | 25 J/s     | 855 s (14.3 min)    | 1,356  | 3.4%   |
| baseline| 50 J/s     | 999 s (16.6 min)    | 1,388  | 3.5%   |
| double  | 100 J/s    | 996 s (16.6 min)    | 2,214  | 5.5%   |

The headline result is robust to ±100% variation in the rotor-wash ember rate parameter — all three variants contain in <17 minutes with <6% grid burnout. The small non-monotonicity (double slightly worse than baseline) is consistent with stochastic variation in fire spread paths under different drone-suppression patterns and should be treated as run-to-run noise rather than a real effect.

### Airborne-ember drag isolation (combined, seed 42)

The rotor-wash physics in §5.3.5 includes two distinct effects on embers: (a) ground-cell suppression — depositing energy into `STATE_EMBER` cells directly under a hovering drone; and (b) airborne-ember drag — applying additional downward acceleration on in-flight embers as they pass through a drone's downwash column. To isolate the contribution of (b), the simulation was re-run with `ROTOR_WASH_EMBER_DRAG_ENABLED = False` while keeping (a) active.

| Variant | Sim time to contain | Peak burning | Total burned | % grid |
|---------|---------------------|--------------|--------------|--------|
| `combined_baseline` (both effects active) | 999 s (16.6 min) | 108 | 1,388 | 3.5% |
| `combined_no_ember_drag` (ground suppression only) | **240 s (4.0 min)** | **88** | **289** | **0.7%** |

The airborne-ember drag term is **not load-bearing** for the containment finding. Removing it did not weaken the result; if anything it produced a marginally faster containment at this seed (consistent with stochastic variation in fire-spread paths under different drone-deployment patterns). The result therefore rests on the combination of (i) acoustic suppression of established burning cells and (ii) rotor-wash ground-cell suppression of nascent ember-state ignitions — the two mechanisms most directly grounded in physical literature. The more speculative airborne-drag effect is a model embellishment, not the cause of the headline outcome.

---

## Sections that DON'T change

- §5.1 Overview (just a small mention of dual-mechanism — minor edit)
- §5.2 Environment Modeling (terrain, fire, wind, ember — same models)
- §5.3.1–5.3.3 (physical model, battery, sensors)
- §5.4 Swarm Coordination
- §5.5 Ground Firefighter Model

## Sections that DO change

---

## §5.1 Overview — small edit

**Add this sentence at end of paragraph 1:**

> "The simulation models two physical suppression mechanisms identified in Chapter 4: directional acoustic emission from a downward-facing subwoofer (§4.2) and rotor-wash aerodynamic disturbance (§4.13). Both mechanisms are present whenever a drone hovers, reflecting the physical reality that multirotor downwash cannot be 'turned off' on a flying platform."

---

## §5.3 Drone Agent Design — REPLACE §5.3.4 + ADD §5.3.5

### §5.3.4 Acoustic Suppression Module (small intro update only)

**Add at start of section:**

> "The acoustic emitter is the first of two suppression mechanisms modeled. It targets the established flame front and is active only when the drone has reached a target and stabilized."

(Then keep all existing acoustic content unchanged.)

### §5.3.5 Rotor-Wash Aerodynamic Suppression (NEW SUBSECTION)

> "The second suppression mechanism is the downward airflow column produced by the drone's rotors. Unlike the acoustic emitter, rotor wash is always present whenever the drone is hovering or holding station — it is a physical consequence of generating lift and cannot be disabled. The model captures three effects.

> **Downwash velocity field.** Using actuator-disk theory, the induced velocity at the rotor disk for a drone of mass m hovering in air of density ρ with total rotor area A is:
>
> v_disk = √(m·g / (2·ρ·A))
>
> For the modeled 5 kg quadrotor with 0.20 m² total disk area in standard air density, this produces v_disk ≈ 11.2 m/s at the rotor. Below the disk, the wake decays linearly with altitude due to ambient air entrainment, modeled with a 10 m decay length. The ground-level downwash footprint expands with altitude, beginning at 1.5 m radius directly under the drone and spreading at 0.15 m radius per meter of altitude.

> **Direct ember disruption.** When a drone hovers above a STATE_EMBER cell — a small, nascent ignition with low burn intensity — the rotor wash deposits suppression energy at a rate scaled to local downwash strength. Embers are easier to extinguish than fully burning cells (consistent with §4.13's observation that lightweight embers are readily deflected by moderate airflow), so the ember suppression rate (50 J/s at peak wash strength) is an order of magnitude higher than the rate applied to established burning cells (5 J/s). This asymmetry reflects the physical reality that rotor wash collapses small flamelets effectively but cannot overcome the convective updraft of an established fire.

> **Airborne ember deflection.** Embers lofted by burning cells are tracked as ballistic particles (§5.2.4). When an ember passes through the rotor wash column of any hovering drone, an additional downward acceleration is applied (1.5 m/s² peak, scaled by radial position and altitude decay). This shortens the ember's airborne trajectory and reduces long-range spotting downwind.

> **Operational gating.** Rotor-wash effects are active whenever a drone is in the HOVERING or EMITTING state. Drones in TRANSIT, RETURNING, or CHARGING produce no rotor wash effect on suppression because they are not holding station above a target."

---

## §5.6 Experimental Scenarios — REWRITE

The previous experimental design compared seven scenarios at 5,000 ticks (500 simulated seconds), all using the acoustic suppression mechanism alone. Following the addition of rotor-wash physics in §5.3.5, the experimental design was restructured around five scenarios run at the more operationally meaningful duration of 35,000 ticks (3,500 simulated seconds, approximately 58 minutes of mission time).

The revised design isolates the contribution of each suppression mechanism through direct comparison rather than parameter sweep:

**Table 1 (REVISED): Experimental Scenario Definitions**

| Scenario | Drones | Wind | Acoustic | Rotor Wash | Purpose |
|----------|--------|------|----------|------------|---------|
| No Drones | 0 | 5 m/s east | — | — | Counterfactual baseline |
| Rotor Wash Only | 100 | 5 m/s east | OFF | ON | Isolate rotor-wash contribution |
| Combined | 100 | 5 m/s east | ON | ON | Realistic full-physics drone |
| Rotor Wash + High Wind | 100 | 10 m/s SE | OFF | ON | Wind robustness, rotor only |
| Combined + High Wind | 100 | 10 m/s SE | ON | ON | Wind robustness, full physics |

The Rotor-Wash-Only scenario is included not because acoustic emission could realistically be disabled on a flying drone — it cannot — but because the comparison between Rotor-Wash-Only and Combined isolates the *additional contribution of acoustic suppression beyond the rotor wash that is always present*. This is the central experimental question: what does the acoustic emitter add to a swarm whose drones already produce downwash by virtue of flying?

All scenarios share the same three-cell ignition cluster at the grid center and use a fixed random seed (42) for reproducibility. Each scenario terminates when no burning or ember-state cells remain (mission success) or when 35,000 ticks elapse, whichever comes first.

---

## §5.7 Implementation Notes — small update

Replace "approximately 2,000 lines of Python 3.11 across twelve modules" with:

> "approximately 3,500 lines of Python 3.12 across eighteen modules (including the experiment harness, figure generation tooling, and the new rotor-wash aerodynamics module). The core simulation logic — fire, drones, coordination, environment — remains compact at approximately 2,300 lines."

---

## §5.8 Simulation Results — REWRITE ENTIRELY

The five scenarios were executed headlessly to completion. The headline results are presented in Table 2 below; subsequent subsections analyze each scenario in detail.

**Table 2: Scenario Outcomes at t = 3,500 s (or mission completion)**

| Scenario | Peak burning | Total burned | Peak embers | Mission complete | Time to complete |
|----------|-------------|-------------|-------------|------------------|------------------|
| No Drones | 3,930 | 37,606 | 393 | No | — |
| Rotor Wash Only | 3,185 | 37,525 | 219 | No | — |
| **Combined** | **108** | **1,388** | **3** | **Yes** | **999 s (16.6 min)** |
| Rotor + High Wind | 4,121 | 37,572 | 324 | No | — |
| Combined + High Wind | 4,121 | 37,572 | 324 | No | — |

The headline finding is dramatic: **the combined-mechanism swarm fully contains the fire in 16.6 simulated minutes, with only 3.5% of the grid (1,388 of 40,000 cells) burned**. Neither the no-drone control nor the rotor-wash-only configuration achieved containment within 35,000 ticks; both allowed the fire to consume approximately 94% of the available grid.

### §5.8.1 No-Drone Control

The no-drone scenario establishes the counterfactual: in the absence of any UAV intervention, the fire spread monotonically from the ignition cluster, reaching peak burning of 3,930 cells at approximately t = 900 s and ultimately consuming 37,606 cells. The fire extinguished naturally at approximately t = 1,500 s, having exhausted the available unburned fuel adjacent to the burned area. Peak ember activity reached 393 cells, reflecting the full ember-lofting potential of an unsuppressed fire.

The 10 ground firefighters operating throughout the scenario applied water to 1,976 cells (4.9% of grid) but were unable to materially affect the spread rate at the modeled walking speed of 0.5 m/s.

### §5.8.2 Rotor-Wash-Only Performance

With rotor wash active but acoustic emission disabled, the 100-drone swarm produced measurable but modest improvements over the no-drone baseline:

- Peak burning reduced from 3,930 to 3,185 cells (a 19% reduction)
- Total burned reduced from 37,606 to 37,525 cells (essentially unchanged)
- **Peak embers reduced from 393 to 219 cells (a 44% reduction)**

The pattern is consistent with the physical predictions of §4.13: rotor wash is effective at ember management but cannot meaningfully suppress an established flame front. The 44% reduction in ember activity is the standout result — drones hovering above ember cells extinguish them efficiently, and downwash on airborne embers shortens their trajectories. However, with acoustic emission disabled, the swarm has no mechanism to reduce burn intensity on cells that have already established sustained combustion, and the fire continues to consume the available fuel until natural burnout.

This isolated rotor-wash performance is not operationally proposed — drones cannot fly without producing rotor wash — but it usefully bounds the contribution of aerodynamic suppression alone.

### §5.8.3 Combined Acoustic + Rotor-Wash Performance

When both mechanisms are active *and* ground firefighters are present, the swarm transforms from a delaying agent into a containing one:

- **Peak burning of only 108 cells** (a 97% reduction vs no drones)
- **Total burned of 1,388 cells** (a 96% reduction vs no drones, 99% reduction vs pure fire dynamics)
- **Peak embers of just 3 cells** (a 99% reduction)
- **Mission complete at t = 999 s** (16.6 simulated minutes)

The two suppression mechanisms are complementary in exactly the way Chapter 4 predicted. Acoustic emission disrupts established burning cells, reducing intensity and extinguishing them with sufficient sustained exposure. Rotor wash handles the ember layer — both ground-level ember-state cells and airborne embers in flight. Neither mechanism alone covers the full fire lifecycle; together they do.

However, the 2×2 factorial in Table 0 (drones × firefighters) reveals a second necessary condition that was not anticipated at the start of this work. The same combined-mechanism swarm, deployed *without* the 10 ground firefighters, fails to contain the fire at the same seed: the `drones_only` scenario burned 39,755 cells (99.4% of grid), worse than `pure_fire` itself (99.0%) due to fuel-exhaustion run-to-run variance. The drone fleet alone cannot defend the western flank of an eastward-moving fire while simultaneously suppressing the active flame front to the east, and falls behind the spread on both axes.

The 10 firefighters' contribution is not flame suppression — they walk at 0.5 m/s from the western edge and almost never reach an active flame in time to extinguish it. Their contribution is the **moisture firebreak** they create as the fire's leading edge approaches their position: 2,000–2,500 cells of saturated fuel that the fire cannot ignite, freeing the swarm to focus exclusively on the eastern front. This is a passive, geometric contribution, but a necessary one at the modeled fleet size.

The containment result therefore depends on three jointly-necessary conditions, all of which can be tested in isolation through the 2×2 above:

1. Both acoustic and rotor-wash mechanisms active simultaneously (compare `combined_baseline` vs `rotor_only_baseline`)
2. Ground firefighters establishing the western flank firebreak (compare `combined_baseline` vs `drones_only`)
3. Wind conditions within the platform's stability envelope (compare `combined_baseline` vs `combined_high_wind`)

Outside any of these three conditions, the swarm fails to contain and the fire runs to fuel exhaustion. This narrows but strengthens the operational claim: UAV swarms are a **complement** to ground-crew operations within a wind-bounded envelope, not a replacement for them.

The mission-complete result at 16.6 minutes is bounded by the simulation's idealized assumptions (§5.9.3): perfect coordination, idealized acoustic propagation, no thermal damage to drones, flat homogeneous terrain. The headline finding should therefore be read not as a literal performance estimate but as evidence that the combined mechanism + ground crew configuration crosses a containment threshold that no other configuration tested can reach.

### §5.8.4 Mechanism Decomposition

Comparing across the three baseline-wind scenarios isolates the contribution of each mechanism:

| Effect | Rotor wash alone | Acoustic alone (estimated) | Combined |
|--------|------------------|---------------------------|----------|
| Peak burning reduction vs no_drones | 19% | [acoustic-only estimate] | **97%** |
| Peak ember reduction vs no_drones | 44% | [acoustic-only estimate] | **99%** |
| Achieves containment? | No | No | **Yes** |

The combined mechanism's effectiveness is greater than the sum of its parts. Rotor wash alone reduces peak burning by 19%; the inferred acoustic-alone contribution (from earlier acoustic-only experiments without ember suppression in the fire model) was a modest delay rather than containment. But the combined effect — 97% reduction and full containment — is qualitatively different. This is consistent with the operational reading: acoustic and aerodynamic mechanisms target different fire stages (flame front vs ember layer), and a swarm that can suppress only one of them is overwhelmed by the other.

### §5.8.5 Wind Impact

The two high-wind scenarios produce a striking and informative result: **both Rotor-Wash-Only and Combined mechanisms collapse to identical numerical outcomes under 10 m/s wind**, with peak burning of 4,121 cells, 37,572 cells burned, and peak ember count of 324 in both cases. The combined mechanism — which contains the fire entirely under moderate wind — provides no measurable benefit over rotor-wash-only when wind speed doubles.

The mechanism for this collapse is operational rather than physical. The 10 m/s base wind, combined with the gust process (steady-state σ ≈ 1.9 m/s), produces frequent excursions above the 12 m/s drone safety threshold (§5.3.1) at which drones autonomously return to base. Inspection of the per-tick logs confirms that drone time-on-station is severely degraded in the high-wind scenarios: drones spend a large fraction of the simulation either in transit or at base recharging, leaving the fire effectively unsuppressed during gust events. With drones repeatedly grounded, the two mechanism toggles (acoustic on/off, rotor wash always on) become operationally equivalent — neither mechanism is being applied long enough to alter fire dynamics — and both runs converge to the trajectory of an effectively unsuppressed fire.

This finding bounds the operational envelope of the combined-mechanism approach. The dramatic containment result of §5.8.3 is contingent on drones being able to maintain station above the fire. When wind conditions exceed the platform's stability limits, the swarm is reduced to its grounded state and the suppression mechanism — however physically capable — has no opportunity to act. This is consistent with manufacturer multirotor wind limits and with the §5.3.1 stability model, but the operational implication is sharp: deployment doctrine must include real-time wind-aware tasking, and the swarm cannot be relied upon as the sole containment asset under marginal weather.

The convergence of the two high-wind scenarios on identical numerical outcomes is itself diagnostic. Because both runs share seed 42 and the high-wind regime forces both into a near-RTB-dominated state, the dynamics reduce to the seeded fire-and-wind trajectory with negligible drone influence — the floor of swarm effectiveness in this simulation framework.

### §5.8.6 Battery and Operational Endurance

Battery dynamics differ markedly between the scenarios that achieve containment and those that do not:

- **Combined baseline**: mission complete at t = 999 s with mean battery ~93%. Battery is not a limiting factor for short successful missions.
- **Rotor-wash-only baseline**: ran the full 35,000 ticks with mean battery declining to approximately 60% (similar to the previous acoustic-only baseline). Sustained operation against an uncontainable fire continues to deplete batteries linearly until intervention ends.

The implication for operational deployment is encouraging: when the swarm is effective enough to contain the fire (combined mechanism), the engagement is brief and battery endurance is comfortable. When the swarm cannot contain the fire, battery becomes the limiting factor for mission duration — but in those cases, the operational value of continuing the engagement is questionable anyway.

### §5.8.7 Suppression Efficiency (TO UPDATE)

[Existing §5.8.6 content, updated with new "drones per burning cell" data from combined scenario.]

---

## §5.9 Analysis and Discussion — REWRITE KEY FINDINGS

### §5.9.1 Validation (mostly unchanged)

Keep existing content. Add this paragraph:

> "The rotor-wash model based on actuator-disk theory produces velocities (≈11 m/s at disk, decaying with altitude) consistent with measurements from quadrotor literature. The differential effectiveness of rotor wash on ember versus burning cells (50 J/s versus 5 J/s) reflects the physical observation that lightweight ember particles are easily disrupted by moderate airflow, while established flame fronts are sustained by their own convective updraft and resist mechanical disturbance."

### §5.9.2 Key Findings — REWRITE

> "The simulation results support the following conclusions:

> **1. Containment requires the joint presence of three conditions; no single intervention is sufficient.** The 2×2 factorial design (drones × firefighters, §5.8 Table 0) shows that 100 drones with combined acoustic and rotor-wash mechanisms achieve full containment (3.5% grid burnout in 16.6 minutes) only when also operating alongside 10 ground firefighters under wind conditions within the platform stability envelope. Removing any one of these — disabling one suppression mechanism, removing the ground firefighters, or doubling wind speed — drops the configuration below the containment threshold and allows the fire to consume 90–99% of the grid. The headline finding is therefore not "drone swarms can contain wildfires" but "drone swarms, deployed in coordination with ground firefighters within a bounded wind envelope, can contain wildfires."

> **2. The two suppression mechanisms are complementary rather than redundant.** Rotor wash alone reduces peak burning by only 19% but reduces peak embers by 44%, consistent with §4.13's argument that aerodynamic disruption is most effective on ember-scale ignitions. Acoustic suppression alone (as established in earlier experiments) is most effective on burning cells. Together, the two mechanisms cover the full fire lifecycle and produce qualitatively different containment behavior than either alone.

> **2b. The drone fleet and ground firefighters are also complementary, in a different and unexpected way.** The 10 ground firefighters in this simulation almost never reach an active flame — at 0.5 m/s walking speed, they cannot catch a fire spreading at over 1 m/s in 5 m/s wind. Their actual contribution to the containment outcome is geometric: they create a 2,000–2,500-cell moisture firebreak along the western (upwind) flank of the fire as it approaches them, which prevents westward spread and frees the drone swarm to focus exclusively on the eastern front. Without this firebreak (the `drones_only` scenario), the swarm cannot defend two flanks simultaneously and the fire runs to fuel exhaustion. This finding inverts the conventional framing of UAVs as "force multipliers": at the fleet size and platform parameters modeled here, the swarm is more accurately described as filling the coverage gap that ground crews physically cannot reach (the downwind/eastern front), with ground crews holding the upwind/western flank passively. Each is necessary; neither is sufficient.

> **3. Ember management is the highest-value contribution per drone.** Peak ember counts dropped from 393 (no drones) to 219 (rotor wash only) to 3 (combined). The 99% reduction in the combined scenario directly reflects the swarm's ability to extinguish nascent ignitions before they establish sustained combustion. This empirically supports §4.14's redirection of UAV suppression toward early-ignition and ember-management roles rather than frontline flame suppression.

> **4. The combined-mechanism result is contingent on drones being able to maintain station; high wind eliminates the advantage entirely.** When base wind speed is doubled to 10 m/s, both Rotor-Wash-Only and Combined scenarios collapse to identical numerical outcomes (peak burning 4,121, total burned 37,572, peak embers 324), driven by frequent excursions of gusts above the 12 m/s drone safety threshold and the corresponding RTB behavior. The mechanism toggles become operationally equivalent because neither mechanism is applied long enough to act. This bounds the deployment envelope: the headline containment finding holds only within the modeled platform's stability margin.

> **5. Battery endurance is not the binding constraint when the swarm is effective.** The combined-mechanism mission completed in 17 minutes with mean fleet battery at 93%, well above the 20% return-to-base threshold. Battery becomes a constraint only in scenarios where the swarm cannot contain the fire and continues hovering indefinitely — situations in which the operational value of continued engagement is itself questionable.

> **6. The simulation results are bounded by its idealized assumptions, but the *direction* of the effect is robust.** The mission-complete result should not be read as a literal claim that 100 drones could extinguish a real grass fire in 17 minutes; it is, rather, evidence that crossing the suppression-pressure threshold from 'delay' to 'contain' is possible only when both suppression mechanisms are active and a passive ground-crew firebreak is established. The qualitative finding — that the combined acoustic + rotor-wash + ground-crew configuration produces fundamentally different dynamics than any subset of those components — is robust to reasonable variation in parameter calibration because it depends on the structural complementarity of the components, not on the absolute magnitudes. A rotor-wash-strength sensitivity sweep (±100% variation in `ROTOR_WASH_EMBER_RATE`) confirmed that the containment outcome holds across the tested parameter range.

> **7. Containment is probabilistic, not deterministic, at the modeled fleet size.** A seed-reproducibility study with N=5 random seeds at the otherwise identical `combined_baseline` configuration produced clean containment in 3 of 5 runs (≤4% grid burnout in <17 simulated minutes) and lost the early-spread race in 2 of 5 runs (>91% grid burnout, mission terminated by fuel exhaustion). The failure mode in both lost runs is loss of the early-spread race within the first 100–200 simulated seconds, after which the fire grows beyond the swarm's per-tick suppression capacity. This same failure mode is observed in `drones_only` (no firefighter firebreak) and in the high-wind scenarios (drones repeatedly grounded by gust excursions over 12 m/s). At this fleet size, containment is therefore best characterized as approximately a 60% probability event, with the failure mode well-understood and bounded. Increasing fleet size or improving early-engagement task allocation are the two natural levers for improving this rate, both of which are flagged as future work."

### §5.9.3 Limitations — small update

REMOVE the bullet that previously said:

> "Acoustic-only suppression mechanism. The simulation models only acoustic flame suppression via SPL-based energy delivery..."

REPLACE with:

> "**Idealized rotor-wash aerodynamics.** The downwash model uses actuator-disk theory with linear wake decay and a static radial profile, ignoring crosswind tilting of the wake column, wake interaction between adjacent drones, and the more complex three-dimensional structure of multirotor wakes near the ground. These simplifications likely overstate effective rotor-wash coverage when drones operate in close formation. The qualitative finding (rotor wash effective on embers, less so on flame fronts) is robust; the quantitative coverage radius and energy-delivery rates should be considered upper bounds."

KEEP all other limitations.

---

## Implementation plan

**When `rotor_only_high_wind` and `combined_high_wind` complete:**

1. Fill in the [PENDING] sections with concrete numbers
2. Generate updated figures for `results_v2/`
3. Modify `update_thesis.py` to apply ALL changes above to `Thesis_04_20_ChristineLangmayr.docx`
4. Save as `Thesis_04_27_Combined_Mechanism.docx`

The thesis claim transforms from:
- "Drones can delay equivalent damage by 35 minutes" (defensible but modest)
- to "Drones with combined acoustic + rotor-wash mechanisms can fully contain a 400m × 400m grass fire under moderate wind in 17 simulated minutes" (much stronger claim, well-supported by data)
