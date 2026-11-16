"""Works out which day to show and when to recalculate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging

from astral import Observer

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AZIMUTH,
    CONF_MAX_ANGLE,
    CONF_MIN_ANGLE,
    DEFAULT_MAX_ANGLE,
    DEFAULT_MIN_ANGLE,
    DOMAIN,
)
from .solar import Interval, day_bounds, sun_intervals, total

_LOGGER = logging.getLogger(__name__)

type WindowSunConfigEntry = ConfigEntry[WindowSunCoordinator]


@dataclass(frozen=True)
class WindowSunData:
    """What the entities show."""

    day: date
    is_today: bool
    intervals: list[Interval]
    duration: timedelta
    in_sun: bool

    @property
    def first(self) -> datetime | None:
        return self.intervals[0][0] if self.intervals else None

    @property
    def last(self) -> datetime | None:
        return self.intervals[-1][1] if self.intervals else None


def choose_day(
    now: datetime, today: list[Interval], tomorrow: list[Interval]
) -> tuple[bool, list[Interval]]:
    """Show today until its last sun has gone, then tomorrow.

    A day without any sun on the window counts as already finished.
    """
    if today and now < today[-1][1]:
        return True, today
    return False, tomorrow


def next_change(now: datetime, intervals: list[Interval], midnight: datetime) -> datetime:
    """The next moment the shown values can change: an edge or midnight."""
    edges = [edge for interval in intervals for edge in interval if edge > now]
    return min([*edges, midnight])


class WindowSunCoordinator(DataUpdateCoordinator[WindowSunData]):
    """Calculates one window, and recalculates exactly when something changes."""

    config_entry: WindowSunConfigEntry

    def __init__(self, hass: HomeAssistant, entry: WindowSunConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=f"{DOMAIN} {entry.title}"
        )
        self._unsub_timer: CALLBACK_TYPE | None = None
        entry.async_on_unload(self._cancel_timer)
        # The home location can be edited in Settings → System → General.
        entry.async_on_unload(
            hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, self._config_updated)
        )

    @property
    def azimuth(self) -> float:
        return float(self.config_entry.options[CONF_AZIMUTH])

    @property
    def angle_range(self) -> tuple[float, float]:
        """Allowed sun angles from the wall; entries made by 0.1.0 have none."""
        options = self.config_entry.options
        return (
            float(options.get(CONF_MIN_ANGLE, DEFAULT_MIN_ANGLE)),
            float(options.get(CONF_MAX_ANGLE, DEFAULT_MAX_ANGLE)),
        )

    @callback
    def _config_updated(self, _event: Event) -> None:
        self.hass.async_create_task(self.async_refresh())

    @callback
    def _cancel_timer(self) -> None:
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    def _calculate(self, now: datetime) -> tuple[WindowSunData, datetime]:
        config = self.hass.config
        observer = Observer(config.latitude, config.longitude, config.elevation or 0)
        tz = dt_util.get_default_time_zone()
        local_now = now.astimezone(tz)
        today = local_now.date()
        tomorrow = today + timedelta(days=1)

        angles = self.angle_range
        today_iv = sun_intervals(observer, today, tz, self.azimuth, *angles)
        tomorrow_iv = sun_intervals(observer, tomorrow, tz, self.azimuth, *angles)
        is_today, shown = choose_day(now, today_iv, tomorrow_iv)
        in_sun = any(start <= now < end for start, end in today_iv)
        data = WindowSunData(
            day=today if is_today else tomorrow,
            is_today=is_today,
            intervals=shown,
            duration=total(shown),
            in_sun=in_sun,
        )
        midnight = day_bounds(today, tz)[1]
        return data, next_change(now, today_iv, midnight)

    async def _async_update_data(self) -> WindowSunData:
        now = dt_util.utcnow()
        data, when = await self.hass.async_add_executor_job(self._calculate, now)
        self._cancel_timer()
        # One second late, so the edge itself is already in the past.
        self._unsub_timer = async_track_point_in_utc_time(
            self.hass, self._timer_fired, when + timedelta(seconds=1)
        )
        return data

    @callback
    def _timer_fired(self, _now: datetime) -> None:
        self._unsub_timer = None
        self.hass.async_create_task(self.async_refresh())
