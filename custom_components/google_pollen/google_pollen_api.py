"""
Minimal async client and model for Google's Pollen API.

This is a lightweight client for the Google Pollen v1 forecast API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp


class GooglePollenApiError(Exception):
    """Generic error from Google Pollen client."""


class GooglePollenAuthError(GooglePollenApiError):
    """The API key is invalid or not authorized."""


@dataclass
class PollenCurrentConditionsData:
    """Parsed pollen data model."""

    types: dict[str, dict[str, Any]]


def _color_to_hex(color: dict[str, Any] | None) -> str | None:
    """Convert a Google Pollen Color object (0–1 floats) to a #rrggbb hex string."""
    if not color:
        return None
    r = round(color.get("red", 0) * 255)
    g = round(color.get("green", 0) * 255)
    b = round(color.get("blue", 0) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


class GooglePollenApi:
    """
    Simple client for Google Pollen API.

    The client expects an aiohttp session and an API key. It makes a single
    GET request to the v1 forecast endpoint and returns a parsed data model.
    """

    BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"

    def __init__(
        self, session: aiohttp.ClientSession, api_key: str, referrer: str | None = None
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._api_key = api_key
        self._referrer = referrer

    async def async_get_current_conditions(
        self, lat: float, lon: float
    ) -> PollenCurrentConditionsData:
        """
        Fetch current pollen conditions for the given coordinates.

        Parses the first day of the v1 forecast response and extracts values
        for tree, grass, and weed pollen.
        """
        params: dict[str, str | float | int] = {
            "key": self._api_key,
            "location.latitude": lat,
            "location.longitude": lon,
            "days": 1,
        }
        headers = {}
        if self._referrer:
            headers["Referer"] = self._referrer

        try:
            async with self._session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 401:
                    raise GooglePollenAuthError("API key is not authorized")
                if resp.status in (400, 403):
                    try:
                        error_data = await resp.json()
                    except (aiohttp.ContentTypeError, ValueError):
                        error_data = {}
                    if isinstance(error_data, dict):
                        error = error_data.get("error")
                        if isinstance(error, dict) and isinstance(
                            error.get("details"), list
                        ):
                            for detail in error["details"]:
                                if isinstance(detail, dict) and detail.get(
                                    "reason"
                                ) in {
                                    "API_KEY_INVALID",
                                    "API_KEY_EXPIRED",
                                    "API_KEY_DELETED",
                                    "API_KEY_SERVICE_BLOCKED",
                                    "API_KEY_HTTP_REFERRER_BLOCKED",
                                    "API_KEY_IP_ADDRESS_BLOCKED",
                                    "API_KEY_ANDROID_APP_BLOCKED",
                                    "API_KEY_IOS_APP_BLOCKED",
                                }:
                                    raise GooglePollenAuthError(
                                        "API key is invalid or not authorized"
                                    )
                resp.raise_for_status()
                data = await resp.json()
        except GooglePollenAuthError:
            raise
        except aiohttp.ClientResponseError as err:
            raise GooglePollenApiError(f"HTTP error {err.status}") from None
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise GooglePollenApiError(
                f"Request failed: {type(err).__name__}"
            ) from None

        # Navigate to pollenTypeInfo from the first day's entry
        daily_info = data.get("dailyInfo") or []
        pollen_type_info: list[dict[str, Any]] = []
        if daily_info and isinstance(daily_info, list):
            pollen_type_info = daily_info[0].get("pollenTypeInfo") or []

        # Map API codes to lowercase keys used by sensor entities
        code_map = {"GRASS": "grass", "TREE": "tree", "WEED": "weed"}

        types: dict[str, dict[str, Any]] = {}
        for entry in pollen_type_info:
            code = entry.get("code", "")
            key = code_map.get(code)
            if key is None:
                continue

            index_info = entry.get("indexInfo") or {}
            value = index_info.get("value")
            category = index_info.get("category")

            types[key] = {
                "value": value,
                "category": category,
                "index_description": index_info.get("indexDescription"),
                "color": _color_to_hex(index_info.get("color")),
                "health_recommendations": "; ".join(
                    entry.get("healthRecommendations") or []
                ),
            }

        return PollenCurrentConditionsData(types=types)
