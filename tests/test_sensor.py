"""Test the Google Pollen sensor platform."""



from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


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
    # 3 pollen types × 5 sensors each = 15 total
    assert len(entities) == 15

    # Get entity IDs
    entity_ids = [entity.entity_id for entity in entities]

    # Verify sensors exist and have correct values (enabled sensors only have states)
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            # Disabled-by-default sensors won't have a state
            continue
        if "tree_pollen_index" in entity_id:
            assert state.state == "4"
        elif "grass_pollen_index" in entity_id:
            assert state.state == "2"
        elif "weed_pollen_index" in entity_id:
            assert state.state == "1"
        elif "tree_pollen_category" in entity_id:
            assert state.state == "Very high"
        elif "grass_pollen_category" in entity_id:
            assert state.state == "Moderate"
        elif "weed_pollen_category" in entity_id:
            assert state.state == "Low"


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
            types={},
        )
    )

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that no sensors were created without type-specific data
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    assert not entities


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

    # Check attribution on first enabled entity
    enabled_entities = [e for e in entities if not e.disabled]
    assert len(enabled_entities) > 0
    state = hass.states.get(enabled_entities[0].entity_id)
    assert state is not None
    assert state.attributes.get("attribution") == "Data provided by Google Pollen"
