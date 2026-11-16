"""Pure sun-on-window geometry, independent of Home Assistant.

A window facing azimuth A (degrees clockwise from north) is in the sun when
  * the sun is up, using the same definition as the Sun integration's
    sunrise and sunset (geometric elevation above -0.833°: the top of the
    disc, with standard atmospheric refraction), and
  * the sun is in front of the wall: its azimuth is at most 90° - margin away
    from A. With the default 1° margin this is "between 1° and 179° from the
    wall plane".

There are no obstacles: neighbouring buildings, trees, balconies and window
reveals are ignored, so the result is the potential (maximum) sun time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta, tzinfo

from astral import Observer
from astral.sun import azimuth as sun_azimuth, elevation as sun_elevation

from .const import EDGE_MARGIN

SUNRISE_ELEVATION = -0.833

Interval = tuple[datetime, datetime]

SAMPLE_STEP = timedelta(minutes=2)
PRECISION = timedelta(seconds=1)


def facing_offset(sun_az: float, window_az: float) -> float:
    """Angle between the sun's azimuth and the window's facing, 0..180°."""
    return abs((sun_az - window_az + 180.0) % 360.0 - 180.0)


def sun_on_window(
    observer: Observer, when: datetime, window_az: float, margin: float = EDGE_MARGIN
) -> bool:
    """Return True if the sun hits the window at this instant."""
    if sun_elevation(observer, when, with_refraction=False) <= SUNRISE_ELEVATION:
        return False
    return facing_offset(sun_azimuth(observer, when), window_az) <= 90.0 - margin


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
    margin: float = EDGE_MARGIN,
) -> list[Interval]:
    """Return the periods of a local day when the sun hits the window.

    A window can get two periods, for example a north-facing one in summer
    (early morning and late evening).
    """

    def lit(when: datetime) -> bool:
        return sun_on_window(observer, when, window_az, margin)

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
