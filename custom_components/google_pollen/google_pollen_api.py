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


@dataclass
class PollenCurrentConditionsData:
    """Parsed pollen data model."""

    index: int | None
    category: str | None
    types: dict[str, dict[str, Any]]


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

        Parses the first day of the v1 forecast response and extracts
        an overall index (max across in-season types) and per-type values
        for tree, grass, and weed pollen.
        """
        params = {
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
                resp.raise_for_status()
                data = await resp.json()
        except Exception as err:
            raise GooglePollenApiError(str(err)) from err

        # Navigate to pollenTypeInfo from the first day's entry
        daily_info = data.get("dailyInfo") or []
        pollen_type_info: list[dict[str, Any]] = []
        if daily_info and isinstance(daily_info, list):
            pollen_type_info = daily_info[0].get("pollenTypeInfo") or []

        # Map API codes to lowercase keys used by sensor entities
        code_map = {"GRASS": "grass", "TREE": "tree", "WEED": "weed"}

        types: dict[str, dict[str, Any]] = {}
        max_value: int | None = None
        max_category: str | None = None

        for entry in pollen_type_info:
            code = entry.get("code", "")
            key = code_map.get(code)
            if key is None:
                continue

            index_info = entry.get("indexInfo") or {}
            value = index_info.get("value")
            category = index_info.get("category")

            types[key] = {"value": value, "category": category}

            # Track the highest index across in-season types for the overall reading
            if entry.get("inSeason") and value is not None:
                if max_value is None or value > max_value:
                    max_value = value
                    max_category = category

        return PollenCurrentConditionsData(
            index=max_value,
            category=max_category,
            types=types,
        )
