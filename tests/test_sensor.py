"""Test the Google Pollen sensor platform."""

from unittest.mock import patch

import pytest

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_API_KEY, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.google_pollen.const import DOMAIN

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_sensor_setup(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test sensor platform setup."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that sensors were created
    entity_registry = er.async_get(hass)

    # Get all entities for the integration
    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    assert len(entities) == 5  # pollen_index, pollen_category, tree, grass, weed

    # Get entity IDs
    entity_ids = [entity.entity_id for entity in entities]

    # Verify sensors exist and have correct values
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is not None
        if "pollen_index" in entity_id:
            assert state.state == "3"
        elif "pollen_category" in entity_id:
            assert state.state == "High"
        elif "tree_pollen" in entity_id:
            assert state.state == "4"
        elif "grass_pollen" in entity_id:
            assert state.state == "2"
        elif "weed_pollen" in entity_id:
            assert state.state == "1"


async def test_sensor_missing_data(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test sensors handle missing data gracefully."""
    from custom_components.google_pollen.google_pollen_api import (
        PollenCurrentConditionsData,
    )
    from tests.conftest import create_mock_entry_with_subentry

    # Mock API with minimal data - need to modify the class-level mock
    mock_google_pollen_api_class.async_get_current_conditions.return_value = (
        PollenCurrentConditionsData(
            index=None,
            category=None,
            types={},
        )
    )

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that only basic sensors were created (no type-specific ones)
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    # Only pollen_index and pollen_category should exist
    assert len(entities) == 2

    # Check that sensors have unknown state
    for entity in entities:
        state = hass.states.get(entity.entity_id)
        assert state is not None
        if "pollen_index" in entity.entity_id or "pollen_category" in entity.entity_id:
            assert state.state == STATE_UNKNOWN


async def test_sensor_attributes(
    hass: HomeAssistant,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test sensor attributes."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Get any sensor and check attributes
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    assert len(entities) > 0

    # Check attribution on first entity
    state = hass.states.get(entities[0].entity_id)
    assert state is not None
    assert state.attributes.get("attribution") == "Data provided by Google Pollen"
