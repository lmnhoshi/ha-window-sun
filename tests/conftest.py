import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


@pytest.fixture
async def bordeaux(hass):
    """Home in Bordeaux, Paris time."""
    await hass.config.async_update(
        latitude=44.84, longitude=-0.58, elevation=20, time_zone="Europe/Paris"
    )
