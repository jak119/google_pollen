"""Test the Google Pollen coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.google_pollen.const import DOMAIN
from custom_components.google_pollen.coordinator import GooglePollenUpdateCoordinator
from custom_components.google_pollen.google_pollen_api import (
    GooglePollenApiError,
    PollenCurrentConditionsData,
)

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test successful data update."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, subentry_id = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    coordinator = GooglePollenUpdateCoordinator(
        hass, config_entry, subentry_id, mock_google_pollen_api
    )

    await coordinator.async_refresh()

    assert coordinator.data is not None
    assert coordinator.data.index == 3
    assert coordinator.data.category == "High"
    assert "tree" in coordinator.data.types
    assert coordinator.data.types["tree"]["value"] == 4


async def test_coordinator_update_failed(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test failed data update."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, subentry_id = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    mock_google_pollen_api.async_get_current_conditions.side_effect = (
        GooglePollenApiError("API Error")
    )

    coordinator = GooglePollenUpdateCoordinator(
        hass, config_entry, subentry_id, mock_google_pollen_api
    )

    with pytest.raises(UpdateFailed):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        if coordinator.last_exception:
            raise coordinator.last_exception


async def test_coordinator_interval_update(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test coordinator can be refreshed multiple times."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, subentry_id = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    coordinator = GooglePollenUpdateCoordinator(
        hass, config_entry, subentry_id, mock_google_pollen_api
    )

    # First refresh
    await coordinator.async_refresh()
    assert mock_google_pollen_api.async_get_current_conditions.call_count == 1

    # Manual second refresh (not testing time-based triggers)
    await coordinator.async_refresh()
    assert mock_google_pollen_api.async_get_current_conditions.call_count == 2
