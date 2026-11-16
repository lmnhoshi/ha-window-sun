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
    CONF_MAX_ANGLE,
    CONF_MIN_ANGLE,
    DEFAULT_GROUND_FLOOR,
    DEFAULT_MAX_ANGLE,
    DEFAULT_MIN_ANGLE,
    DOMAIN,
    GROUND_FLOOR_OPTIONS,
)


def _angle() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=180,
            step=0.1,
            unit_of_measurement="°",
            mode=selector.NumberSelectorMode.BOX,
        )
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
    vol.Required(CONF_MIN_ANGLE, default=DEFAULT_MIN_ANGLE): _angle(),
    vol.Required(CONF_MAX_ANGLE, default=DEFAULT_MAX_ANGLE): _angle(),
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


def _errors(user_input: dict[str, Any]) -> dict[str, str]:
    if float(user_input[CONF_MIN_ANGLE]) >= float(user_input[CONF_MAX_ANGLE]):
        return {CONF_MAX_ANGLE: "angle_order"}
    return {}


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_AZIMUTH: float(user_input[CONF_AZIMUTH]) % 360,
        CONF_MIN_ANGLE: float(user_input[CONF_MIN_ANGLE]),
        CONF_MAX_ANGLE: float(user_input[CONF_MAX_ANGLE]),
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
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (errors := _errors(user_input)):
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip() or "Window",
                    data={},
                    options=_clean(user_input),
                )
        schema = self.add_suggested_values_to_schema(
            vol.Schema({vol.Required(CONF_NAME, default="Window"): str, **WINDOW_FIELDS}),
            user_input,
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class WindowSunOptionsFlow(OptionsFlowWithReload):
    """Change the orientation or the floor."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (errors := _errors(user_input)):
                return self.async_create_entry(data=_clean(user_input))
        current = {
            CONF_MIN_ANGLE: DEFAULT_MIN_ANGLE,
            CONF_MAX_ANGLE: DEFAULT_MAX_ANGLE,
            **self.config_entry.options,
        }
        schema = self.add_suggested_values_to_schema(
            vol.Schema(WINDOW_FIELDS), user_input or current
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
