"""Test the Google Pollen config flow."""

import asyncio
from types import MappingProxyType
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigSubentry
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
    second_subentry = ConfigSubentry(
        data=MappingProxyType({CONF_LATITUDE: 40.0, CONF_LONGITUDE: -74.0}),
        subentry_type="location",
        title="Second location",
        unique_id=None,
        subentry_id="second_location",
    )
    entry.subentries[second_subentry.subentry_id] = second_subentry
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

    with (
        patch(
            "custom_components.google_pollen.config_flow.GooglePollenApi",
            return_value=mock_google_pollen_api,
        ) as api_class,
        patch(
            "custom_components.google_pollen.GooglePollenApi",
            return_value=mock_google_pollen_api,
        ) as setup_api_class,
    ):
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
    assert setup_api_class.call_args.args[1] == "new_key"
    mock_google_pollen_api.async_get_current_conditions.assert_any_await(
        lat=mock_subentry_data[CONF_LATITUDE], lon=mock_subentry_data[CONF_LONGITUDE]
    )
    assert entry.subentries[subentry_id] == subentry
    assert entry.subentries[second_subentry.subentry_id] == second_subentry
    assert entry.runtime_data.subentries_runtime_data[subentry_id].data is not None
    assert entry.runtime_data.subentries_runtime_data[second_subentry.subentry_id].data
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


@pytest.mark.parametrize("simultaneous_release", [False, True])
@pytest.mark.parametrize(
    ("first_source", "second_source"),
    [
        (config_entries.SOURCE_REAUTH, config_entries.SOURCE_REAUTH),
        (config_entries.SOURCE_USER, config_entries.SOURCE_REAUTH),
        (config_entries.SOURCE_REAUTH, config_entries.SOURCE_USER),
        (config_entries.SOURCE_USER, config_entries.SOURCE_USER),
    ],
)
async def test_concurrent_flows_reject_duplicate_key(
    hass: HomeAssistant,
    mock_google_pollen_api,
    first_source: str,
    second_source: str,
    simultaneous_release: bool,
) -> None:
    """Only one overlapping flow can claim a validated API key."""
    sources = (first_source, second_source)
    flows = []
    entries = []
    for index, source in enumerate(sources):
        context = {"source": source}
        if source == config_entries.SOURCE_REAUTH:
            entry = MockConfigEntry(
                domain=DOMAIN, data={CONF_API_KEY: f"old_key_{index}"}
            )
            entry.add_to_hass(hass)
            entries.append(entry)
            context["entry_id"] = entry.entry_id
        flows.append(await hass.config_entries.flow.async_init(DOMAIN, context=context))

    started = [asyncio.Event(), asyncio.Event()]
    release = [asyncio.Event(), asyncio.Event()]
    call_count = 0

    async def validate(**kwargs: float) -> None:
        nonlocal call_count
        index = call_count
        call_count += 1
        started[index].set()
        await release[index].wait()

    mock_google_pollen_api.async_get_current_conditions.side_effect = validate
    inputs = [
        {CONF_API_KEY: "shared_key"}
        if source == config_entries.SOURCE_REAUTH
        else {
            CONF_API_KEY: "shared_key",
            CONF_NAME: f"Location {index}",
            CONF_LOCATION: {CONF_LATITUDE: 10.0 + index, CONF_LONGITUDE: 20.0},
        }
        for index, source in enumerate(sources)
    ]

    with (
        patch(
            "custom_components.google_pollen.config_flow.GooglePollenApi",
            return_value=mock_google_pollen_api,
        ),
        patch("custom_components.google_pollen.async_setup_entry", return_value=True),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        first = asyncio.create_task(
            hass.config_entries.flow.async_configure(flows[0]["flow_id"], inputs[0])
        )
        await asyncio.wait_for(started[0].wait(), timeout=5)
        second = asyncio.create_task(
            hass.config_entries.flow.async_configure(flows[1]["flow_id"], inputs[1])
        )
        await asyncio.wait_for(started[1].wait(), timeout=5)
        release[0].set()
        if simultaneous_release:
            release[1].set()
        first_result = await first
        release[1].set()
        second_result = await second
        await hass.async_block_till_done()

    if first_source == config_entries.SOURCE_REAUTH:
        assert first_result["reason"] == "reauth_successful"
    else:
        assert first_result["type"] is FlowResultType.CREATE_ENTRY
    if second_source == config_entries.SOURCE_REAUTH:
        assert second_result["type"] is FlowResultType.FORM
        assert second_result["errors"] == {"base": "already_configured"}
        assert entries[-1].data[CONF_API_KEY] == "old_key_1"
    else:
        assert second_result["type"] is FlowResultType.ABORT
        assert second_result["reason"] == "already_configured"
    assert (
        sum(
            entry.data.get(CONF_API_KEY) == "shared_key"
            for entry in hass.config_entries.async_entries(DOMAIN)
        )
        == 1
    )
