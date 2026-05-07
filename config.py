"""
All tunable simulation constants in one place.
"""

# ── Simulation timing ──────────────────────────────────────────────────────────
DT = 0.1                  # seconds per tick (10 Hz)
COORD_INTERVAL = 20       # ticks between swarm coordination runs (2 sim-seconds)
RENDER_INTERVAL = 5       # ticks between render frames (0.5 sim-seconds)
WIND_UPDATE_INTERVAL = 10 # ticks between wind field recomputes (1 sim-second)

# ── Terrain / Grid ─────────────────────────────────────────────────────────────
GRID_WIDTH = 200          # cells
GRID_HEIGHT = 200         # cells
CELL_SIZE = 2.0           # meters per cell side → 400m × 400m area

# Cell state enum values (stored as uint8)
STATE_UNBURNED = 0
STATE_BURNING  = 1
STATE_EMBER    = 2
STATE_BURNED   = 3
STATE_WET      = 4

# Fuel (grass) defaults
DEFAULT_FUEL_LOAD = 0.8        # kg/m² dry biomass
DEFAULT_MOISTURE  = 0.15       # 0–1; >0.30 = extinction moisture
MOISTURE_EXTINCTION = 0.30

# ── Fire model ─────────────────────────────────────────────────────────────────
# Rothermel grass fuel constants
FIRE_R0          = 0.5 / 60.0  # base rate of spread in m/s (0.5 m/min → 0.00833 m/s)
FIRE_WIND_C      = 0.165        # wind factor coefficient
FIRE_WIND_B      = 0.69         # wind factor exponent
FIRE_K_WIND      = 0.08         # exponential wind factor for CA spread probability
FIRE_P_BASE      = 0.004        # base ignition probability per tick (per neighbor)
FIRE_BURN_TIME   = 60.0         # seconds a cell burns before transitioning to BURNED
FIRE_SUPPRESSION_THRESHOLD_BASE = 30.0   # J equivalent to extinguish a cell at intensity=1.0

# ── Wind model ─────────────────────────────────────────────────────────────────
WIND_BASE_SPEED     = 5.0    # m/s mean wind speed
WIND_BASE_DIR       = 0.0    # radians (east)
WIND_GUST_SIGMA     = 0.6    # m/s volatility (OU process); steady-state std ≈ 1.9 m/s
WIND_THETA          = 0.1    # mean-reversion rate
WIND_SPATIAL_SIGMA  = 15.0   # cells; Gaussian smoothing kernel std for spatial coherence

# ── Ember model ────────────────────────────────────────────────────────────────
EMBER_LOFT_PROB       = 0.0005  # probability per burning cell per tick of lofting an ember
EMBER_IGNITE_P_BASE   = 0.35    # base landing ignition probability (scaled by dryness)
EMBER_DRAG_COEFF      = 0.3     # aerodynamic drag coefficient for ember ballistics
EMBER_V0_Z_SCALE      = 4.0     # m/s updraft scale factor (× burn_intensity)
EMBER_MAX_AGE         = 20.0    # seconds; embers burn out after this

# ── Drones ─────────────────────────────────────────────────────────────────────
NUM_DRONES = 100

# Physical specs
DRONE_MASS          = 8.0    # kg (heavy-lift heat-hardened class — Matrice-350-equivalent
                              # airframe + ~3 kg of ceramic-coated panels, aerogel battery
                              # insulation, sealed/smoke-filtered motor housings, encapsulated
                              # avionics, raised from 5 kg in the original configuration)
DRONE_MAX_THRUST    = 130.0  # N (≈1.65× hover thrust, scaled with mass)
DRONE_CD            = 0.4    # drag coefficient
DRONE_FRONTAL_AREA  = 0.08   # m² (larger body cross-section)
DRONE_MAX_SPEED     = 15.0   # m/s horizontal
DRONE_MAX_VSPEED    = 5.0    # m/s vertical
DRONE_CRUISE_ALT    = 5.0    # m AGL operating altitude (lowered from 15 m so rotor wash
                              # actually exceeds ambient wind at the target cell, and so 3D
                              # distance to target stays inside the SPL-effective regime)
DRONE_MAX_WIND      = 15.0   # m/s; above this drone returns to base (raised from 12 m/s with
                              # the larger platform's higher stability margin)
AIR_DENSITY         = 1.225  # kg/m³ at sea level

# PID gains (position control)
PID_KP = 2.0
PID_KI = 0.1
PID_KD = 0.5
WIND_FF_GAIN = 0.8           # feedforward wind compensation gain

# Battery
BATTERY_CAPACITY_WH  = 2000.0  # Wh (large UAV with thermal-management overhead)
BATTERY_P_HOVER      = 350.0   # W
BATTERY_P_SENSORS    = 10.0    # W
BATTERY_LOW_THRESH   = 0.20    # fraction; triggers return-to-base
BATTERY_FULL_THRESH  = 0.90    # fraction; drone re-enters mission

# Sound emitter
SOUND_FREQ_HZ        = 40.0    # Hz (30–80 Hz effective range)
SOUND_POWER_W        = 200.0   # W acoustic output
SOUND_EFFICIENCY     = 0.80    # electrical→acoustic efficiency
SOUND_BEAM_ANGLE_DEG = 45.0    # half-angle of directional cone
SOUND_DIRECTIVITY_Q  = 4.0     # Q factor (cardioid ≈ 4)
SOUND_SPL_THRESHOLD  = 110.0   # dB; minimum for any suppression
SOUND_SPL_SATURATION = 130.0   # dB; maximum effectiveness
SOUND_MAX_RANGE      = 15.0    # m; beyond this SPL < threshold

# ── Rotor wash (multirotor downwash aerodynamics) ──────────────────────────────
# Always physically present when drones hover; modeled as actuator-disk theory
# with linear wake decay. See physics/aerodynamics.py.
ROTOR_TOTAL_AREA          = 0.30    # m² combined disk area (larger rotors give a thrust margin
                                     # for fire-induced thermal-plume turbulence and support the
                                     # heavier 8 kg airframe; raised from 0.20 m²)
ROTOR_WASH_DECAY_LENGTH   = 10.0    # m altitude scale for wake velocity decay
ROTOR_WASH_FOOTPRINT_BASE = 1.5     # m base footprint radius at the drone
ROTOR_WASH_SPREAD_RATE    = 0.15    # m radius gain per m of altitude
ROTOR_WASH_EMBER_RATE     = 10.0    # J/s suppression rate on STATE_EMBER cells (reduced from
                                     # 50 to 10 — the original value was a calibration choice,
                                     # not a measured rate. 10 J/s extinguishes a 6 J ember cell
                                     # in 0.6 s, consistent with the qualitative observation
                                     # that small flamelets can be disrupted by modest airflow
                                     # but conservative compared to a near-instant kill rate.)
ROTOR_WASH_BURNING_RATE   = 0.0     # J/s suppression rate on STATE_BURNING cells (reduced
                                     # from 5 to 0 — published literature does not support
                                     # small-drone rotor wash disrupting an established flame
                                     # front; established fires sustain themselves through
                                     # their own convective updraft and resist 4 m/s downwash.
                                     # Setting to zero is the conservative literature-honest
                                     # choice.)
ROTOR_WASH_EMBER_DRAG     = 1.5     # m/s² downward acceleration applied to airborne embers in column

# ── Mechanism toggles (for ablation studies) ───────────────────────────────────
ROTOR_WASH_ENABLED = True   # If False, drones produce no downwash effect
ACOUSTIC_ENABLED   = True   # If False, drones do not emit acoustic energy
ROTOR_WASH_EMBER_DRAG_ENABLED = True  # If False, rotor wash does not drag airborne embers down (isolates the
                                       # ground-cell suppression contribution from the airborne-ember
                                       # contribution).

# Sensors
THERMAL_FOV_DEG   = 90.0   # half-angle field of view
THERMAL_RANGE     = 30.0   # m
THERMAL_NOISE_STD = 0.02   # intensity noise std
PROX_RANGE        = 10.0   # m proximity sensor range
ANEM_NOISE_STD    = 0.3    # m/s wind measurement noise

# ── Swarm coordination ─────────────────────────────────────────────────────────
MIN_DRONE_SEPARATION = 5.0   # m minimum inter-drone distance
SAFE_FIRE_DISTANCE   = 2.0   # m minimum drone distance from fire edge (tightened to literature-
                              # validated regime; assumes the heat-hardened platform class above
                              # can survive sustained close-range thermal exposure — see §5.9.3
                              # for the operating-time-budget caveat)
MAX_FIRE_DISTANCE    = 5.0   # m maximum effective range from target fire cell (tightened to
                              # the regime where on-axis SPL is well above the 110 dB threshold
                              # and rotor-wash velocity at the ground exceeds ambient wind)
TASK_REALLOC_HYSTERESIS = 0.1 # minimum score improvement to trigger reassignment
VO_TIME_HORIZON      = 3.0   # seconds for velocity obstacle lookahead

# ── Firefighters ──────────────────────────────────────────────────────────────
NUM_FIREFIGHTERS       = 10
FIREFIGHTER_EXCL_RADIUS = 15.0  # m drone no-fly zone around each firefighter
FIREFIGHTER_WATER_RADIUS = 5.0  # m water spray effective radius
FIREFIGHTER_SPEED        = 0.5  # m/s (slow deliberate movement)

# ── Base station ───────────────────────────────────────────────────────────────
BASE_POSITION = (10.0, 10.0, 0.0)  # (x, y, z) meters; bottom-left corner area
BASE_CHARGE_RATE = 0.02             # fraction of capacity per second when charging

# ── Visualization ──────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1400   # pixels
WINDOW_HEIGHT = 800    # pixels
FIG_DPI = 100
COLORMAP_FIRE = "hot"
QUIVER_DOWNSAMPLE = 10  # show wind every Nth cell
