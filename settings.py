REFERENCE_FPS = 60
MAX_DELTA_TIME = 0.05
DISPLAY_FPS_CAP = 120

PIPE_WIDTH_FRACTION = 1 / 10
PIPE_SPACING_FRACTION = 0.5
PIPE_GAP_FRACTION = 0.25
PIPE_MIN_TOP_FRACTION = 0.2
PIPE_MAX_BOTTOM_FRACTION = 0.8
BIRD_HEIGHT_FRACTION = 1 / 15
SPAWN_INTERVAL_START_FRAMES = 68
SPAWN_INTERVAL_MIN_FRAMES = 32
SPAWN_INTERVAL_STAGE_SCALE = 8 / 9
WORLD_SPEED_MULTIPLIER = 1.0
GRACE_PERIOD_SECONDS = 2.5

STAGE_DURATION_SECONDS = 10.0

GROUND_HEIGHT_FRACTION = 0.09

PARALLAX_SPEEDS = {
    "celestial": 0.03,
    "clouds_far": 0.08,
    "clouds_near": 0.14,
    "mountains_far": 0.16,
    "mountains_near": 0.24,
    "hills": 0.36,
    "trees": 0.55,
    "bushes": 0.72,
    "foreground": 1.0,
}

CLOUD_COUNT_FAR = 5
CLOUD_COUNT_NEAR = 4
CLOUD_WIND_SPEED = 7.0
CLOUD_ALTITUDE_RANGE = (0.05, 0.40)
CLOUD_SCALE_RANGE_FAR = (0.5, 0.9)
CLOUD_SCALE_RANGE_NEAR = (0.9, 1.6)

STAR_COUNT = 150
TWINKLE_STAR_COUNT = 16

SUN_X_FRACTION = 0.78
MOON_X_FRACTION = 0.68
MOON_Y_FRACTION = 0.16

ATMOSPHERE_PHASE_STEP = 0.1
ATMOSPHERE_GROUND_STEP = 0.2
MAX_PHASE = 7.0

SHAKE_MAX_OFFSET = 16.0
SHAKE_TRAUMA_DECAY = 1.7
SHAKE_FREQUENCY = 26.0

SCORE_PULSE_DURATION = 0.45
SCORE_FONT_FRACTION = 0.088
STAGE_BANNER_DURATION = 1.7

PARTICLE_MAX_COUNT = 260
PARTICLE_PIPE_PASS_COUNT = 10
PARTICLE_COLLISION_COUNT = 20
PARTICLE_CONFETTI_COUNT = 26
PARTICLE_STAGE_MOTE_COUNT = 14

PALETTES = [
    {
        "phase": 0.0,
        "sky_top": (72, 164, 224),
        "sky_bottom": (188, 226, 238),
        "horizon_glow": (255, 244, 214, 110),
        "haze_color": (210, 232, 240),
        "haze_alpha": 70,
        "sun_color": (255, 246, 214),
        "sun_glow_alpha": 200,
        "sun_y_fraction": 0.24,
        "moon_alpha": 0,
        "star_alpha": 0,
        "cloud_color": (255, 255, 255, 215),
        "mountains_far": (142, 178, 204),
        "mountains_near": (112, 148, 176),
        "snow_color": (245, 250, 255, 200),
        "hills": (98, 168, 104),
        "trees": (44, 116, 70),
        "bushes": (36, 102, 60),
        "grass_top": (128, 196, 96),
        "grass_body": (74, 148, 72),
        "soil_color": (118, 84, 60),
        "soil_speckle": (86, 60, 42),
        "grade_color": (0, 0, 0, 0),
        "vignette_alpha": 70,
    },
    {
        "phase": 2.0,
        "sky_top": (96, 150, 208),
        "sky_bottom": (252, 206, 142),
        "horizon_glow": (255, 214, 150, 150),
        "haze_color": (246, 214, 166),
        "haze_alpha": 84,
        "sun_color": (255, 214, 140),
        "sun_glow_alpha": 225,
        "sun_y_fraction": 0.40,
        "moon_alpha": 0,
        "star_alpha": 0,
        "cloud_color": (255, 226, 186, 205),
        "mountains_far": (172, 138, 150),
        "mountains_near": (136, 106, 124),
        "snow_color": (255, 238, 220, 190),
        "hills": (134, 152, 88),
        "trees": (58, 102, 60),
        "bushes": (48, 90, 54),
        "grass_top": (156, 182, 92),
        "grass_body": (96, 132, 66),
        "soil_color": (120, 82, 58),
        "soil_speckle": (88, 60, 44),
        "grade_color": (255, 176, 88, 16),
        "vignette_alpha": 74,
    },
    {
        "phase": 4.0,
        "sky_top": (66, 60, 126),
        "sky_bottom": (244, 132, 92),
        "horizon_glow": (255, 150, 90, 170),
        "haze_color": (238, 150, 120),
        "haze_alpha": 96,
        "sun_color": (255, 150, 96),
        "sun_glow_alpha": 235,
        "sun_y_fraction": 0.58,
        "moon_alpha": 40,
        "star_alpha": 30,
        "cloud_color": (232, 150, 130, 190),
        "mountains_far": (120, 84, 120),
        "mountains_near": (86, 60, 96),
        "snow_color": (255, 210, 190, 150),
        "hills": (84, 96, 72),
        "trees": (40, 72, 54),
        "bushes": (34, 62, 48),
        "grass_top": (110, 130, 72),
        "grass_body": (66, 96, 56),
        "soil_color": (96, 68, 52),
        "soil_speckle": (70, 48, 38),
        "grade_color": (255, 110, 70, 24),
        "vignette_alpha": 84,
    },
    {
        "phase": 5.5,
        "sky_top": (30, 32, 72),
        "sky_bottom": (150, 84, 110),
        "horizon_glow": (200, 120, 140, 120),
        "haze_color": (150, 110, 140),
        "haze_alpha": 80,
        "sun_color": (255, 170, 120),
        "sun_glow_alpha": 120,
        "sun_y_fraction": 0.70,
        "moon_alpha": 160,
        "star_alpha": 120,
        "cloud_color": (120, 100, 140, 150),
        "mountains_far": (66, 58, 96),
        "mountains_near": (46, 42, 74),
        "snow_color": (200, 200, 230, 110),
        "hills": (48, 64, 60),
        "trees": (26, 46, 42),
        "bushes": (22, 40, 38),
        "grass_top": (70, 96, 64),
        "grass_body": (44, 68, 46),
        "soil_color": (66, 50, 42),
        "soil_speckle": (48, 36, 32),
        "grade_color": (70, 60, 140, 26),
        "vignette_alpha": 92,
    },
    {
        "phase": 7.0,
        "sky_top": (8, 10, 30),
        "sky_bottom": (30, 42, 74),
        "horizon_glow": (140, 160, 220, 70),
        "haze_color": (70, 86, 130),
        "haze_alpha": 56,
        "sun_color": (200, 210, 255),
        "sun_glow_alpha": 0,
        "sun_y_fraction": 0.95,
        "moon_alpha": 235,
        "star_alpha": 235,
        "cloud_color": (66, 78, 112, 120),
        "mountains_far": (34, 40, 68),
        "mountains_near": (24, 30, 52),
        "snow_color": (170, 185, 225, 90),
        "hills": (26, 44, 44),
        "trees": (14, 30, 30),
        "bushes": (12, 26, 26),
        "grass_top": (40, 72, 52),
        "grass_body": (26, 48, 38),
        "soil_color": (40, 32, 30),
        "soil_speckle": (28, 22, 20),
        "grade_color": (14, 20, 60, 32),
        "vignette_alpha": 100,
    },
]
