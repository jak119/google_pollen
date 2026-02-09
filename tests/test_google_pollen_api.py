"""Test the Google Pollen API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.google_pollen.google_pollen_api import (
    GooglePollenApi,
    GooglePollenApiError,
    PollenCurrentConditionsData,
)


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    return session


async def test_api_get_current_conditions_success(mock_session):
    """Test successful API call."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "index": {
                "pollen": {
                    "value": 3,
                    "category": "High",
                }
            },
            "types": {
                "tree": {"value": 4, "category": "Very High"},
                "grass": {"value": 2, "category": "Moderate"},
                "weed": {"value": 1, "category": "Low"},
            },
        }
    )

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert isinstance(result, PollenCurrentConditionsData)
    assert result.index == 3
    assert result.category == "High"
    assert "tree" in result.types
    assert result.types["tree"]["value"] == 4


async def test_api_with_referrer(mock_session):
    """Test API call with referrer header."""
    api = GooglePollenApi(mock_session, "test_api_key", referrer="https://example.com")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"index": {}, "types": {}})

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    await api.async_get_current_conditions(37.7749, -122.4194)

    # Verify referrer header was passed
    call_kwargs = mock_session.get.call_args[1]
    assert call_kwargs["headers"]["Referer"] == "https://example.com"


async def test_api_http_error(mock_session):
    """Test API HTTP error."""
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
    """Test API timeout."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_session.get = MagicMock(side_effect=aiohttp.ServerTimeoutError("Timeout"))

    with pytest.raises(GooglePollenApiError):
        await api.async_get_current_conditions(37.7749, -122.4194)


async def test_api_defensive_parsing_no_types(mock_session):
    """Test defensive parsing when types are missing."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "index": {"pollen": {"value": 2}},
            # No types field
        }
    )

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert result.index == 2
    assert result.types == {}


async def test_api_defensive_parsing_minimal(mock_session):
    """Test defensive parsing with minimal data."""
    api = GooglePollenApi(mock_session, "test_api_key")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={})

    mock_session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    result = await api.async_get_current_conditions(37.7749, -122.4194)

    assert result.index is None
    assert result.category is None
    assert result.types == {}
