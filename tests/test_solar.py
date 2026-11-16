"""Geometry checks against known sun behaviour in Bordeaux."""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import sun
import pytest

from custom_components.window_sun.const import compass_point
from custom_components.window_sun.solar import (
    facing_offset,
    sun_intervals,
    total,
    wall_angle,
)

OBS = Observer(44.84, -0.58, 0)
TZ = ZoneInfo("Europe/Paris")
WINTER = date(2026, 12, 21)
SUMMER = date(2026, 6, 21)


def test_facing_offset_wraps():
    assert facing_offset(10, 350) == 20
    assert facing_offset(350, 10) == 20
    assert facing_offset(180, 0) == 180


def test_compass_point():
    assert [compass_point(a) for a in (0, 90, 135, 200, 359)] == [
        "N", "E", "SE", "SSW", "N",
    ]


def test_south_window_in_winter_gets_sunrise_to_sunset():
    (start, end), = sun_intervals(OBS, WINTER, TZ, 180)
    ref = sun(OBS, WINTER, tzinfo=TZ)
    assert abs(start - ref["sunrise"]) < timedelta(minutes=1)
    assert abs(end - ref["sunset"]) < timedelta(minutes=1)


def test_north_window_dark_in_winter_twice_lit_in_summer():
    assert sun_intervals(OBS, WINTER, TZ, 0) == []
    morning, evening = sun_intervals(OBS, SUMMER, TZ, 0)
    assert morning[0].hour == 6 and evening[1].hour == 21


@pytest.mark.parametrize("day", [WINTER, SUMMER, date(2026, 3, 29)])
def test_opposite_windows_share_the_day(day):
    """East + west ≈ the whole day, minus the two 1° edges."""
    ref = sun(OBS, day, tzinfo=TZ)
    both = total(sun_intervals(OBS, day, TZ, 90)) + total(
        sun_intervals(OBS, day, TZ, 270)
    )
    gap = ref["sunset"] - ref["sunrise"] - both
    assert timedelta(0) < gap < timedelta(minutes=15)


def test_dst_day_times_are_local():
    """Clocks go forward on 29 March; a south window gets sun ~08:26 local.

    The sun rises at azimuth 84° and sets at 276°, so a south window (sun
    within 91°–269°) starts after sunrise and ends before sunset.
    """
    day = date(2026, 3, 29)
    (start, end), = sun_intervals(OBS, day, TZ, 180)
    ref = sun(OBS, day, tzinfo=TZ)
    assert start.tzinfo is TZ and (start.hour, start.minute // 10) == (8, 2)
    assert ref["sunrise"] < start < ref["sunrise"] + timedelta(hours=1)
    assert ref["sunset"] - timedelta(hours=1) < end < ref["sunset"]


def test_wall_angle_scale():
    """Looking out of a south window: east is on the left, west on the right."""
    assert wall_angle(90, 180) == 0
    assert wall_angle(180, 180) == 90
    assert wall_angle(270, 180) == 180
    assert not 0 <= wall_angle(0, 180) <= 180
    assert wall_angle(10, 350) == 110


def test_default_range_is_the_1_to_179_rule():
    """0°–180° gives an east window a little more sun than 1°–179°."""
    strict = total(sun_intervals(OBS, SUMMER, TZ, 90))
    loose = total(sun_intervals(OBS, SUMMER, TZ, 90, 0, 180))
    assert timedelta(0) < loose - strict < timedelta(minutes=10)


def test_narrow_range_cuts_one_side():
    """South window in winter, right side blocked from 135°: sun ends earlier."""
    (start, end), = sun_intervals(OBS, WINTER, TZ, 180)
    (cut_start, cut_end), = sun_intervals(OBS, WINTER, TZ, 180, 1, 135)
    assert cut_start == start
    # Sun at azimuth 180 + 45 = 225°: about 16:20 in December, before sunset.
    assert cut_end.hour == 16 and cut_end < end
