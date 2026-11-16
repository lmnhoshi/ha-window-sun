"""Add a window: name, compass orientation and floor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AZIMUTH,
    CONF_FLOOR,
    CONF_GROUND_FLOOR,
    DEFAULT_GROUND_FLOOR,
    DOMAIN,
    GROUND_FLOOR_OPTIONS,
)

WINDOW_FIELDS = {
    vol.Required(CONF_AZIMUTH): selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=359.9,
            step=0.1,
            unit_of_measurement="°",
            mode=selector.NumberSelectorMode.BOX,
        )
    ),
    vol.Required(CONF_FLOOR, default=0): selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=-5, max=200, step=1, mode=selector.NumberSelectorMode.BOX
        )
    ),
    vol.Required(CONF_GROUND_FLOOR, default=DEFAULT_GROUND_FLOOR): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=GROUND_FLOOR_OPTIONS,
            translation_key=CONF_GROUND_FLOOR,
            mode=selector.SelectSelectorMode.LIST,
        )
    ),
}


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_AZIMUTH: float(user_input[CONF_AZIMUTH]) % 360,
        CONF_FLOOR: int(user_input[CONF_FLOOR]),
        CONF_GROUND_FLOOR: user_input[CONF_GROUND_FLOOR],
    }


class WindowSunConfigFlow(ConfigFlow, domain=DOMAIN):
    """One config entry per window."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WindowSunOptionsFlow:
        return WindowSunOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME].strip() or "Window",
                data={},
                options=_clean(user_input),
            )
        schema = vol.Schema(
            {vol.Required(CONF_NAME, default="Window"): str, **WINDOW_FIELDS}
        )
        return self.async_show_form(step_id="user", data_schema=schema)


class WindowSunOptionsFlow(OptionsFlowWithReload):
    """Change the orientation or the floor."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        schema = self.add_suggested_values_to_schema(
            vol.Schema(WINDOW_FIELDS), self.config_entry.options
        )
        return self.async_show_form(step_id="init", data_schema=schema)
