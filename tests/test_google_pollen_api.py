"""Test the Google Pollen API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.google_pollen.google_pollen_api import (
    GooglePollenApi,
    GooglePollenApiError,
    GooglePollenAuthError,
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
    mock_response.json = AsyncMock(return_value={})
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


@pytest.mark.parametrize(
    ("status", "reason", "auth_error"),
    [
        (401, None, True),
        (400, "API_KEY_INVALID", True),
        (403, "API_KEY_SERVICE_BLOCKED", True),
        (403, "API_KEY_HTTP_REFERRER_BLOCKED", True),
        (403, "RATE_LIMIT_EXCEEDED", False),
        (403, "SERVICE_DISABLED", False),
        (400, "INVALID_ARGUMENT", False),
        (429, "RATE_LIMIT_EXCEEDED", False),
        (500, None, False),
    ],
)
async def test_api_error_classification(mock_session, status, reason, auth_error):
    """Only credential errors require reauthentication."""
    api = GooglePollenApi(mock_session, "secret_key")
    response = _setup_mock_session(
        mock_session, {"error": {"details": [{"reason": reason}]}}
    )
    response.status = status
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=status
    )

    with pytest.raises(GooglePollenApiError) as raised:
        await api.async_get_current_conditions(37.7749, -122.4194)

    assert isinstance(raised.value, GooglePollenAuthError) is auth_error
    assert "secret_key" not in str(raised.value)


async def test_api_invalid_error_body(mock_session):
    """An unreadable error response is not mistaken for an invalid key."""
    api = GooglePollenApi(mock_session, "secret_key")
    response = _setup_mock_session(mock_session, {})
    response.status = 403
    response.json.side_effect = ValueError("Invalid JSON")
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=403
    )
    with pytest.raises(GooglePollenApiError) as raised:
        await api.async_get_current_conditions(37.7749, -122.4194)
    assert not isinstance(raised.value, GooglePollenAuthError)


async def test_api_timeout(mock_session):
    """Test API timeout raises GooglePollenApiError."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_session.get = MagicMock(side_effect=aiohttp.ServerTimeoutError("Timeout"))

    with pytest.raises(GooglePollenApiError):
        await api.async_get_current_conditions(37.7749, -122.4194)


async def test_api_includes_out_of_season_types(mock_session):
    """Test that out-of-season pollen type data is included."""
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

    assert result.types["tree"]["value"] == 5
    assert result.types["grass"]["value"] == 1


async def test_api_empty_response(mock_session):
    """Test parsing when the API returns an empty object."""
    api = GooglePollenApi(mock_session, "test_api_key")
    _setup_mock_session(mock_session, {})

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert result.types == {}
