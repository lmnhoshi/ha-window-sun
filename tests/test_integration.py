"""Config flow, entities, and the switch from today to tomorrow."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.window_sun.const import DOMAIN

TZ = ZoneInfo("Europe/Paris")
OPTIONS = {"azimuth": 90.0, "floor": 2, "ground_floor": "0"}


async def _setup(hass, options=OPTIONS, title="Kitchen") -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title=title, data={}, options=options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow(hass: HomeAssistant, bordeaux) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Living room", "azimuth": 1, "floor": 1, "ground_floor": "1"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living room"
    assert result["options"] == {"azimuth": 1.0, "floor": 1, "ground_floor": "1"}
    await hass.async_block_till_done()
    attrs = hass.states.get("sensor.living_room_sun_hours").attributes
    assert attrs["storeys_above_ground"] == 0 and attrs["facing"] == "N"


async def test_options_flow_changes_orientation(hass, bordeaux, freezer) -> None:
    freezer.move_to(datetime(2026, 11, 16, 7, 0, tzinfo=TZ))
    entry = await _setup(hass)
    east = float(hass.states.get("sensor.kitchen_sun_hours").state)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"azimuth": 0, "floor": 2, "ground_floor": "0"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert east > 4
    assert hass.states.get("sensor.kitchen_sun_hours").state == "0.0"


async def test_today_then_tomorrow(
    hass: HomeAssistant, bordeaux, freezer: FrozenDateTimeFactory
) -> None:
    """East window: today's values until the sun leaves, then tomorrow's."""
    freezer.move_to(datetime(2026, 11, 16, 10, 0, tzinfo=TZ))
    await _setup(hass)

    assert hass.states.get("sensor.kitchen_sun_day").state == "today"
    assert hass.states.get("binary_sensor.kitchen_sun_on_window").state == "on"
    hours = hass.states.get("sensor.kitchen_sun_hours")
    assert 4.3 < float(hours.state) < 5.0
    assert hours.attributes["date"] == "2026-11-16"
    assert len(hours.attributes["periods"]) == 1
    end = datetime.fromisoformat(hass.states.get("sensor.kitchen_sun_end").state)
    assert end.astimezone(TZ).hour == 12

    # Two seconds after the sun leaves the window, tomorrow is shown.
    freezer.move_to(end + timedelta(seconds=2))
    async_fire_time_changed(hass, end + timedelta(seconds=2))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.kitchen_sun_day").state == "tomorrow"
    assert hass.states.get("binary_sensor.kitchen_sun_on_window").state == "off"
    hours = hass.states.get("sensor.kitchen_sun_hours")
    assert hours.attributes["date"] == "2026-11-17"
    start = datetime.fromisoformat(hass.states.get("sensor.kitchen_sun_start").state)
    assert start.astimezone(TZ).date().isoformat() == "2026-11-17"

    # After midnight the shown day becomes "today" again, same date.
    midnight = datetime(2026, 11, 17, 0, 0, 1, tzinfo=TZ)
    freezer.move_to(midnight + timedelta(seconds=1))
    async_fire_time_changed(hass, midnight + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.kitchen_sun_day").state == "today"
    assert hass.states.get("sensor.kitchen_sun_hours").attributes["date"] == "2026-11-17"


async def test_window_without_sun_today_shows_tomorrow(hass, bordeaux, freezer) -> None:
    freezer.move_to(datetime(2026, 11, 16, 9, 0, tzinfo=TZ))
    await _setup(hass, {"azimuth": 0.0, "floor": 0, "ground_floor": "0"}, "North")
    assert hass.states.get("sensor.north_sun_day").state == "tomorrow"
    assert hass.states.get("sensor.north_sun_hours").state == "0.0"
    assert hass.states.get("sensor.north_sun_start").state == "unknown"


@pytest.mark.parametrize("floor,ground,above", [(3, "0", 3), (3, "1", 2), (-1, "0", -1)])
async def test_floor_conventions(hass, bordeaux, floor, ground, above) -> None:
    await _setup(hass, {"azimuth": 180.0, "floor": floor, "ground_floor": ground}, "W")
    assert hass.states.get("sensor.w_sun_hours").attributes["storeys_above_ground"] == above


async def test_unload(hass, bordeaux) -> None:
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
