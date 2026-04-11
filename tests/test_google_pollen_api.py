"""Test the Google Pollen API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.google_pollen.google_pollen_api import (
    GooglePollenApi,
    GooglePollenApiError,
    PollenCurrentConditionsData,
)

# Real Google Pollen API v1 response shape used across tests
REAL_API_RESPONSE = {
    "regionCode": "US",
    "dailyInfo": [
        {
            "date": {"year": 2024, "month": 4, "day": 1},
            "pollenTypeInfo": [
                {
                    "code": "GRASS",
                    "displayName": "Grass",
                    "inSeason": True,
                    "indexInfo": {
                        "code": "UPI",
                        "value": 2,
                        "category": "Low",
                    },
                },
                {
                    "code": "TREE",
                    "displayName": "Tree",
                    "inSeason": True,
                    "indexInfo": {
                        "code": "UPI",
                        "value": 4,
                        "category": "Very High",
                    },
                },
                {
                    "code": "WEED",
                    "displayName": "Weed",
                    "inSeason": False,
                    "indexInfo": {
                        "code": "UPI",
                        "value": 1,
                        "category": "Low",
                    },
                },
            ],
        }
    ],
}


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    return session


def _setup_mock_session(mock_session, response_data):
    """Configure mock session to return the given response data."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=response_data)

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_response


async def test_api_get_current_conditions_success(mock_session):
    """Test successful API call with real response shape."""
    api = GooglePollenApi(mock_session, "test_api_key")
    _setup_mock_session(mock_session, REAL_API_RESPONSE)

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert isinstance(result, PollenCurrentConditionsData)
    # Overall index is the max value across in-season types (tree=4, grass=2; weed not in season)
    assert result.index == 4
    assert result.category == "Very High"
    assert "tree" in result.types
    assert result.types["tree"]["value"] == 4
    assert "grass" in result.types
    assert result.types["grass"]["value"] == 2
    assert "weed" in result.types
    assert result.types["weed"]["value"] == 1


async def test_api_with_referrer(mock_session):
    """Test API call includes Referer header when referrer is configured."""
    api = GooglePollenApi(mock_session, "test_api_key", referrer="https://example.com")
    _setup_mock_session(mock_session, REAL_API_RESPONSE)

    await api.async_get_current_conditions(37.7749, -122.4194)

    call_kwargs = mock_session.get.call_args[1]
    assert call_kwargs["headers"]["Referer"] == "https://example.com"


async def test_api_url_params(mock_session):
    """Test that location is sent as separate lat/lon params, not a combined string."""
    api = GooglePollenApi(mock_session, "test_api_key")
    _setup_mock_session(mock_session, REAL_API_RESPONSE)

    await api.async_get_current_conditions(37.7749, -122.4194)

    call_kwargs = mock_session.get.call_args[1]
    params = call_kwargs["params"]
    assert params["location.latitude"] == 37.7749
    assert params["location.longitude"] == -122.4194
    assert "location" not in params


async def test_api_http_error(mock_session):
    """Test API HTTP error raises GooglePollenApiError."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_response = MagicMock()
    mock_response.status = 403
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=403,
            message="Forbidden",
        )
    )

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(GooglePollenApiError):
        await api.async_get_current_conditions(37.7749, -122.4194)


async def test_api_timeout(mock_session):
    """Test API timeout raises GooglePollenApiError."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_session.get = MagicMock(side_effect=aiohttp.ServerTimeoutError("Timeout"))

    with pytest.raises(GooglePollenApiError):
        await api.async_get_current_conditions(37.7749, -122.4194)


async def test_api_out_of_season_excluded_from_overall(mock_session):
    """Test that out-of-season types don't contribute to the overall index."""
    api = GooglePollenApi(mock_session, "test_api_key")
    response = {
        "dailyInfo": [
            {
                "pollenTypeInfo": [
                    {
                        "code": "TREE",
                        "inSeason": False,
                        "indexInfo": {"value": 5, "category": "Very High"},
                    },
                    {
                        "code": "GRASS",
                        "inSeason": True,
                        "indexInfo": {"value": 1, "category": "Low"},
                    },
                ]
            }
        ]
    }
    _setup_mock_session(mock_session, response)

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    # Tree is out of season so grass (1) wins, not tree (5)
    assert result.index == 1
    assert result.category == "Low"


async def test_api_empty_response(mock_session):
    """Test parsing when the API returns an empty object."""
    api = GooglePollenApi(mock_session, "test_api_key")
    _setup_mock_session(mock_session, {})

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert result.index is None
    assert result.category is None
    assert result.types == {}
