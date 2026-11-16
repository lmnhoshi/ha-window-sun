"""Constants for Window Sun."""

DOMAIN = "window_sun"

CONF_AZIMUTH = "azimuth"
CONF_FLOOR = "floor"
CONF_GROUND_FLOOR = "ground_floor"

# The ground floor is called 0 in most of Europe and 1 in North America.
GROUND_FLOOR_OPTIONS = ["0", "1"]
DEFAULT_GROUND_FLOOR = "0"

# The sun counts as hitting the window while it is between 1° and 179° from the
# wall plane, i.e. at most 89° away from the direction the window faces.
EDGE_MARGIN = 1.0

COMPASS_POINTS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def compass_point(azimuth: float) -> str:
    """Return the 16-point compass label for an azimuth in degrees."""
    return COMPASS_POINTS[round(azimuth % 360 / 22.5) % 16]
