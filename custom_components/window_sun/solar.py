"""Pure sun-on-window geometry, independent of Home Assistant.

A window facing azimuth A (degrees clockwise from north) is in the sun when
  * the sun is up, using the same definition as the Sun integration's
    sunrise and sunset (geometric elevation above -0.833°: the top of the
    disc, with standard atmospheric refraction), and
  * the sun is in front of the wall, within the window's angle range: its
    angle from the wall plane, looking out, is between min_angle and
    max_angle (0° = along the wall to the left, 90° = straight ahead,
    180° = along the wall to the right). The default 1°–179° leaves out the
    sun skimming along the façade.

There are no obstacles: neighbouring buildings, trees, balconies and window
reveals are ignored, so the result is the potential (maximum) sun time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta, tzinfo

from astral import Observer
from astral.sun import azimuth as sun_azimuth, elevation as sun_elevation

from .const import DEFAULT_MAX_ANGLE, DEFAULT_MIN_ANGLE

SUNRISE_ELEVATION = -0.833

Interval = tuple[datetime, datetime]

SAMPLE_STEP = timedelta(minutes=2)
PRECISION = timedelta(seconds=1)


def facing_offset(sun_az: float, window_az: float) -> float:
    """Angle between the sun's azimuth and the window's facing, 0..180°."""
    return abs((sun_az - window_az + 180.0) % 360.0 - 180.0)


def wall_angle(sun_az: float, window_az: float) -> float:
    """Sun's angle from the wall plane, looking out: 0 left, 90 ahead, 180 right.

    Behind the wall the result is outside 0..180 (negative or above 180).
    """
    return (sun_az - window_az + 180.0) % 360.0 - 90.0


def sun_on_window(
    observer: Observer,
    when: datetime,
    window_az: float,
    min_angle: float = DEFAULT_MIN_ANGLE,
    max_angle: float = DEFAULT_MAX_ANGLE,
) -> bool:
    """Return True if the sun hits the window at this instant."""
    if sun_elevation(observer, when, with_refraction=False) <= SUNRISE_ELEVATION:
        return False
    return min_angle <= wall_angle(sun_azimuth(observer, when), window_az) <= max_angle


def _edge(lit: Callable[[datetime], bool], low: datetime, high: datetime) -> datetime:
    """Bisect the instant where lit() changes between low and high."""
    state = lit(low)
    while high - low > PRECISION:
        middle = low + (high - low) / 2
        if lit(middle) == state:
            low = middle
        else:
            high = middle
    return high.replace(microsecond=0)


def day_bounds(day: date, tz: tzinfo) -> tuple[datetime, datetime]:
    """Local midnight to the next local midnight (23 or 25 h on DST days)."""
    start = datetime.combine(day, time.min, tz)
    end = datetime.combine(day + timedelta(days=1), time.min, tz)
    return start, end


def sun_intervals(
    observer: Observer,
    day: date,
    tz: tzinfo,
    window_az: float,
    min_angle: float = DEFAULT_MIN_ANGLE,
    max_angle: float = DEFAULT_MAX_ANGLE,
) -> list[Interval]:
    """Return the periods of a local day when the sun hits the window.

    A window can get two periods, for example a north-facing one in summer
    (early morning and late evening).
    """

    def lit(when: datetime) -> bool:
        return sun_on_window(observer, when, window_az, min_angle, max_angle)

    start, end = day_bounds(day, tz)
    intervals: list[Interval] = []
    opened: datetime | None = start if lit(start) else None
    previous, previous_lit = start, opened is not None
    when = start
    while when < end:
        when = min(when + SAMPLE_STEP, end)
        now_lit = lit(when)
        if now_lit != previous_lit:
            edge = _edge(lit, previous, when)
            if now_lit:
                opened = edge
            else:
                intervals.append((opened, edge))
                opened = None
        previous, previous_lit = when, now_lit
    if opened is not None:
        intervals.append((opened, end))
    return intervals


def total(intervals: list[Interval]) -> timedelta:
    """Sum of the interval lengths."""
    return sum((end - start for start, end in intervals), timedelta())
