"""Test the Google Pollen config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.google_pollen.const import (
    CONF_REFERRER,
    DOMAIN,
    SECTION_API_KEY_OPTIONS,
)
from custom_components.google_pollen.google_pollen_api import (
    GooglePollenApiError,
    GooglePollenAuthError,
)


async def test_form(hass: HomeAssistant, mock_google_pollen_api) -> None:
    """Test the initial config flow form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "test_api_key",
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: 37.7749,
                    CONF_LONGITUDE: -122.4194,
                },
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Google Pollen"
    assert result2["data"] == {
        CONF_API_KEY: "test_api_key",
        CONF_REFERRER: None,
    }
    # Verify subentry was created
    assert len(result2["subentries"]) == 1
    assert result2["subentries"][0]["title"] == "Test Location"


async def test_form_with_referrer(hass: HomeAssistant, mock_google_pollen_api) -> None:
    """Test config flow with optional referrer."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "test_api_key",
                SECTION_API_KEY_OPTIONS: {CONF_REFERRER: "https://example.com"},
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: 37.7749,
                    CONF_LONGITUDE: -122.4194,
                },
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_REFERRER] == "https://example.com"


async def test_form_cannot_connect(hass: HomeAssistant, mock_google_pollen_api) -> None:
    """Test error when cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_google_pollen_api.async_get_current_conditions.side_effect = (
        GooglePollenApiError("Connection failed")
    )

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "test_api_key",
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: 37.7749,
                    CONF_LONGITUDE: -122.4194,
                },
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(hass: HomeAssistant, mock_google_pollen_api) -> None:
    """Test unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_google_pollen_api.async_get_current_conditions.side_effect = Exception(
        "Unexpected error"
    )

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "test_api_key",
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: 37.7749,
                    CONF_LONGITUDE: -122.4194,
                },
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_already_configured(
    hass: HomeAssistant, mock_google_pollen_api
) -> None:
    """Test duplicate API key aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test_api_key"},
        unique_id="test_api_key",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "test_api_key",
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: 37.7749,
                    CONF_LONGITUDE: -122.4194,
                },
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_location_already_configured(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test location already configured."""
    from tests.conftest import create_mock_entry_with_subentry

    # Set up existing entry with subentry
    create_mock_entry_with_subentry(
        hass,
        mock_config_entry_data,
        mock_subentry_data,
        subentry_title="Existing Location",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "different_api_key",
                CONF_NAME: "Test Location",
                CONF_LOCATION: {
                    CONF_LATITUDE: mock_subentry_data[CONF_LATITUDE],
                    CONF_LONGITUDE: mock_subentry_data[CONF_LONGITUDE],
                },
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_reauth_recovers_existing_entry(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_google_pollen_api_class,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Reauthentication preserves locations and sensors and reloads with the new key."""
    from tests.conftest import create_mock_entry_with_subentry

    entry, subentry_id = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    before = {
        (entity.entity_id, entity.unique_id)
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
    }
    assert before
    subentry = entry.subentries[subentry_id]
    mock_google_pollen_api.async_get_current_conditions.side_effect = (
        GooglePollenAuthError("Invalid key")
    )
    await entry.runtime_data.subentries_runtime_data[subentry_id].async_refresh()
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == config_entries.SOURCE_REAUTH
    flow_id = flows[0]["flow_id"]

    with patch(
        "custom_components.google_pollen.config_flow.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ) as api_class:
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_API_KEY: "bad_key"}
        )
        assert result["errors"] == {"base": "invalid_auth"}
        assert entry.data == mock_config_entry_data

        mock_google_pollen_api.async_get_current_conditions.side_effect = (
            GooglePollenApiError("Temporary failure")
        )
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_API_KEY: "new_key"}
        )
        assert result["errors"] == {"base": "cannot_connect"}
        assert entry.data == mock_config_entry_data

        mock_google_pollen_api.async_get_current_conditions.side_effect = None
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_API_KEY: "new_key"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {**mock_config_entry_data, CONF_API_KEY: "new_key"}
    assert (
        api_class.call_args.kwargs["referrer"] == mock_config_entry_data[CONF_REFERRER]
    )
    mock_google_pollen_api.async_get_current_conditions.assert_any_await(
        lat=mock_subentry_data[CONF_LATITUDE], lon=mock_subentry_data[CONF_LONGITUDE]
    )
    assert entry.subentries[subentry_id] == subentry
    assert entry.runtime_data.subentries_runtime_data[subentry_id].data is not None
    assert {
        (entity.entity_id, entity.unique_id)
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
    } == before


async def test_reauth_rejects_duplicate_key(
    hass: HomeAssistant, mock_config_entry_data, mock_subentry_data
) -> None:
    """A replacement key cannot already belong to another entry."""
    from tests.conftest import create_mock_entry_with_subentry

    entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )
    MockConfigEntry(domain=DOMAIN, data={CONF_API_KEY: "other_key"}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "other_key"}
    )
    assert result["errors"] == {"base": "already_configured"}
    assert entry.data == mock_config_entry_data
