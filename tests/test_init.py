"""Test the Google Pollen integration init."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from custom_components.google_pollen.const import DOMAIN

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_entry(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test successful setup of config entry."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, subentry_id = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Verify coordinator was created and has data
    assert config_entry.runtime_data is not None
    assert config_entry.runtime_data.api is not None
    assert subentry_id in config_entry.runtime_data.subentries_runtime_data


async def test_setup_entry_no_subentries(
    hass: HomeAssistant, mock_google_pollen_api_class, mock_config_entry_data
) -> None:
    """Test setup with no subentries."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_entry_data,
        entry_id="test_entry_id",
        unique_id=mock_config_entry_data[CONF_API_KEY],
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED


async def test_unload_entry(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test unloading a config entry."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_update_options(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test updating options triggers reload."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Trigger options update
    hass.config_entries.async_update_entry(config_entry, options={"test": "value"})
    await hass.async_block_till_done()

    # Entry should still be loaded
    assert config_entry.state is ConfigEntryState.LOADED
