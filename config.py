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
DRONE_MASS          = 5.0    # kg
DRONE_MAX_THRUST    = 80.0   # N (1.6× hover thrust)
DRONE_CD            = 0.4    # drag coefficient
DRONE_FRONTAL_AREA  = 0.05   # m²
DRONE_MAX_SPEED     = 15.0   # m/s horizontal
DRONE_MAX_VSPEED    = 5.0    # m/s vertical
DRONE_CRUISE_ALT    = 15.0   # m AGL operating altitude
DRONE_MAX_WIND      = 12.0   # m/s; above this drone returns to base
AIR_DENSITY         = 1.225  # kg/m³ at sea level

# PID gains (position control)
PID_KP = 2.0
PID_KI = 0.1
PID_KD = 0.5
WIND_FF_GAIN = 0.8           # feedforward wind compensation gain

# Battery
BATTERY_CAPACITY_WH  = 1500.0  # Wh (large UAV)
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

# Sensors
THERMAL_FOV_DEG   = 90.0   # half-angle field of view
THERMAL_RANGE     = 30.0   # m
THERMAL_NOISE_STD = 0.02   # intensity noise std
PROX_RANGE        = 10.0   # m proximity sensor range
ANEM_NOISE_STD    = 0.3    # m/s wind measurement noise

# ── Swarm coordination ─────────────────────────────────────────────────────────
MIN_DRONE_SEPARATION = 5.0   # m minimum inter-drone distance
SAFE_FIRE_DISTANCE   = 10.0  # m minimum drone distance from fire edge
MAX_FIRE_DISTANCE    = 20.0  # m maximum effective range from target fire cell
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
