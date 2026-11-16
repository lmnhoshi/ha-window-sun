"""Shared entity base: one device per window."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_FLOOR, CONF_GROUND_FLOOR, DOMAIN, compass_point
from .coordinator import WindowSunCoordinator


def storeys_above_ground(options: dict) -> int:
    """Floor number converted to storeys above the ground floor."""
    return int(options[CONF_FLOOR]) - int(options[CONF_GROUND_FLOOR])


class WindowSunEntity(CoordinatorEntity[WindowSunCoordinator]):
    """An entity of one window."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: WindowSunCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        options = entry.options
        azimuth = coordinator.azimuth
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Window Sun",
            model=f"Facing {azimuth:g}° {compass_point(azimuth)}",
            model_id=f"Floor {int(options[CONF_FLOOR])}",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def window_attributes(self) -> dict:
        options = self.coordinator.config_entry.options
        azimuth = self.coordinator.azimuth
        return {
            "azimuth": azimuth,
            "facing": compass_point(azimuth),
            "floor": int(options[CONF_FLOOR]),
            "ground_floor_number": int(options[CONF_GROUND_FLOOR]),
            "storeys_above_ground": storeys_above_ground(options),
        }
