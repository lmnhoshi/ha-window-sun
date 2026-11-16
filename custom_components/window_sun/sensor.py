"""Sensors: sun hours, first and last sun, and which day they describe."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WindowSunConfigEntry, WindowSunData
from .entity import WindowSunEntity


def _hours(data: WindowSunData) -> float:
    return round(data.duration.total_seconds() / 3600, 2)


def _day(data: WindowSunData) -> str:
    return "today" if data.is_today else "tomorrow"


@dataclass(frozen=True, kw_only=True)
class WindowSunSensorDescription(SensorEntityDescription):
    value: Callable[[WindowSunData], Any]


SENSORS = (
    WindowSunSensorDescription(
        key="sun_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
        value=_hours,
    ),
    WindowSunSensorDescription(
        key="sun_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value=lambda data: data.first,
    ),
    WindowSunSensorDescription(
        key="sun_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value=lambda data: data.last,
    ),
    WindowSunSensorDescription(
        key="day",
        device_class=SensorDeviceClass.ENUM,
        options=["today", "tomorrow"],
        value=_day,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WindowSunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors of one window."""
    async_add_entities(
        WindowSunSensor(entry.runtime_data, description) for description in SENSORS
    )


def _iso(moment: datetime) -> str:
    return moment.isoformat()


class WindowSunSensor(WindowSunEntity, SensorEntity):
    """One value of the shown day."""

    entity_description: WindowSunSensorDescription

    def __init__(self, coordinator, description: WindowSunSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "sun_hours":
            return None
        data = self.coordinator.data
        return {
            "day": _day(data),
            "date": data.day.isoformat(),
            "periods": [
                {"start": _iso(start), "end": _iso(end)}
                for start, end in data.intervals
            ],
            **self.window_attributes,
        }
