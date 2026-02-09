"""Minimal async client and model for Google's Pollen API.

This is a lightweight client intended to be sufficient for the integration.
The real Google API response shape may differ; parsing is defensive and
only extracts basic index and per-type values.
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
    """Simple client for Google Pollen API.

    The client expects an aiohttp session and an API key. It makes a single
    GET request to the pollen endpoint and returns a parsed data model.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/pollen/v1"

    def __init__(
        self, session: aiohttp.ClientSession, api_key: str, referrer: str | None = None
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._referrer = referrer

    async def async_get_current_conditions(
        self, lat: float, lon: float
    ) -> PollenCurrentConditionsData:
        """Fetch current pollen conditions for the given coordinates.

        The implementation is defensive: it accepts a variety of JSON shapes and
        extracts an overall index and per-type values (tree, grass, weed) if
        present.
        """
        params = {"key": self._api_key, "location": f"{lat},{lon}"}
        url = f"{self.BASE_URL}/currentConditions"
        headers = {}
        if self._referrer:
            headers["Referer"] = self._referrer

        try:
            async with self._session.get(
                url, params=params, headers=headers, timeout=20
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as err:
            raise GooglePollenApiError(str(err)) from err

        # Defensive parsing: try common shapes
        # Overall index
        index = None
        category = None
        types: dict[str, dict[str, Any]] = {}

        # Look under top-level keys that are likely
        idx = data.get("index") or data.get("indexes") or {}
        if isinstance(idx, dict):
            # Could be {'pollen': {'value': 3, 'category': 'High'}}
            pollen_idx = idx.get("pollen") or idx.get("overall") or idx
            if isinstance(pollen_idx, dict):
                index = pollen_idx.get("value")
                category = pollen_idx.get("category")
            else:
                try:
                    index = int(pollen_idx)
                except Exception:
                    index = None

        # per-type values
        types_blob = (
            data.get("types") or data.get("pollenTypes") or data.get("data") or {}
        )
        if isinstance(types_blob, dict):
            for key, val in types_blob.items():
                if isinstance(val, dict):
                    types[key] = {
                        "value": val.get("value"),
                        "category": val.get("category"),
                    }
                else:
                    # if value is scalar
                    types[key] = {"value": val}

        # Try alternate locations
        if not types:
            # Some responses embed pollen info under 'current' -> 'pollen'
            current = data.get("current") or {}
            pollen = current.get("pollen") or {}
            if isinstance(pollen, dict):
                for key, val in pollen.items():
                    if isinstance(val, dict):
                        types[key] = {
                            "value": val.get("value"),
                            "category": val.get("category"),
                        }
                    else:
                        types[key] = {"value": val}

        return PollenCurrentConditionsData(index=index, category=category, types=types)
