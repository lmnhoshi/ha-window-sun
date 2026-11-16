"""Constants for Window Sun."""

DOMAIN = "window_sun"

CONF_AZIMUTH = "azimuth"
CONF_FLOOR = "floor"
CONF_GROUND_FLOOR = "ground_floor"

# The ground floor is called 0 in most of Europe and 1 in North America.
GROUND_FLOOR_OPTIONS = ["0", "1"]
DEFAULT_GROUND_FLOOR = "0"

CONF_MIN_ANGLE = "min_angle"
CONF_MAX_ANGLE = "max_angle"

# The sun counts as hitting the window while its angle from the wall plane is
# between these. Measured looking out: 0° along the wall to the left, 90°
# straight ahead, 180° along the wall to the right.
DEFAULT_MIN_ANGLE = 1.0
DEFAULT_MAX_ANGLE = 179.0

COMPASS_POINTS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def compass_point(azimuth: float) -> str:
    """Return the 16-point compass label for an azimuth in degrees."""
    return COMPASS_POINTS[round(azimuth % 360 / 22.5) % 16]
