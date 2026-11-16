"""Binary sensor: is the sun on the window right now."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WindowSunConfigEntry
from .entity import WindowSunEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WindowSunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the binary sensor of one window."""
    async_add_entities([WindowSunNow(entry.runtime_data, "in_sun")])


class WindowSunNow(WindowSunEntity, BinarySensorEntity):
    """On while the sun hits the window (geometrically, ignoring obstacles)."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.in_sun
