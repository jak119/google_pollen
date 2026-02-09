"""Common fixtures for Google Pollen tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.google_pollen.const import CONF_REFERRER
from custom_components.google_pollen.google_pollen_api import (
    PollenCurrentConditionsData,
)


# This fixture enables loading custom integrations in all tests
# Remove to enable selective removal of this fixture to test
# standard behavior.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


def create_mock_entry_with_subentry(
    hass: HomeAssistant,
    entry_data: dict,
    subentry_data: dict,
    subentry_title: str = "Test Location",
    subentry_id: str = "test_subentry_id",
) -> tuple[MockConfigEntry, str]:
    """Create a mock config entry with a subentry."""
    from types import MappingProxyType

    from homeassistant.config_entries import ConfigSubentry

    from custom_components.google_pollen.const import DOMAIN

    # Create main config entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=entry_data,
        entry_id="test_entry_id",
        unique_id=entry_data.get(CONF_API_KEY),
    )

    # Create a real ConfigSubentry
    subentry = ConfigSubentry(
        data=MappingProxyType(subentry_data),
        subentry_type="location",
        title=subentry_title,
        unique_id=None,
        subentry_id=subentry_id,
    )

    # Mock the subentries using a simple dict
    subentries_dict = {subentry_id: subentry}

    # Override subentries attribute with a simple dict
    type(config_entry).subentries = MagicMock(return_value=subentries_dict)
    config_entry.subentries = subentries_dict

    config_entry.add_to_hass(hass)

    return config_entry, subentry_id


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.google_pollen.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_google_pollen_api():
    """Mock the GooglePollenApi client instance."""
    mock_api = MagicMock()
    mock_api.async_get_current_conditions = AsyncMock(
        return_value=PollenCurrentConditionsData(
            index=3,
            category="High",
            types={
                "tree": {"value": 4, "category": "Very High"},
                "grass": {"value": 2, "category": "Moderate"},
                "weed": {"value": 1, "category": "Low"},
            },
        )
    )
    return mock_api


@pytest.fixture
def mock_google_pollen_api_class(mock_google_pollen_api):
    """Patch GooglePollenApi class to return mock instance."""
    with patch(
        "custom_components.google_pollen.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        yield mock_google_pollen_api


@pytest.fixture
def mock_config_entry_data():
    """Return mock config entry data."""
    return {
        CONF_API_KEY: "test_api_key_123",
        CONF_REFERRER: "https://example.com",
    }


@pytest.fixture
def mock_subentry_data():
    """Return mock subentry data."""
    return {
        CONF_LATITUDE: 37.7749,
        CONF_LONGITUDE: -122.4194,
    }
