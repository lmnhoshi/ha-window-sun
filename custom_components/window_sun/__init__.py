"""Window Sun: potential hours of direct sun on each window, without obstacles."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import WindowSunConfigEntry, WindowSunCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: WindowSunConfigEntry) -> bool:
    """Set up one window."""
    coordinator = WindowSunCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WindowSunConfigEntry) -> bool:
    """Remove one window."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
