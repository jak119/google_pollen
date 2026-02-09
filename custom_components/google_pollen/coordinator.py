"""Coordinator for fetching data from Google Pollen API."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .google_pollen_api import (
    GooglePollenApi,
    GooglePollenApiError,
    PollenCurrentConditionsData,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL: Final = timedelta(hours=1)

type GooglePollenConfigEntry = ConfigEntry["GooglePollenRuntimeData"]


class GooglePollenUpdateCoordinator(DataUpdateCoordinator[PollenCurrentConditionsData]):
    """Coordinator for fetching Google Pollen data."""

    config_entry: GooglePollenConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: GooglePollenConfigEntry,
        subentry_id: str,
        client: GooglePollenApi,
    ) -> None:
        """Initialize DataUpdateCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{subentry_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        subentry = config_entry.subentries[subentry_id]
        self.lat = subentry.data[CONF_LATITUDE]
        self.long = subentry.data[CONF_LONGITUDE]

    async def _async_update_data(self) -> PollenCurrentConditionsData:
        """Fetch pollen data for this coordinate."""
        try:
            return await self.client.async_get_current_conditions(self.lat, self.long)
        except GooglePollenApiError as ex:
            _LOGGER.debug("Cannot fetch pollen data: %s", str(ex))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="unable_to_fetch",
            ) from ex


@dataclass
class GooglePollenRuntimeData:
    """Runtime data for the Google Pollen integration."""

    api: GooglePollenApi
    subentries_runtime_data: dict[str, GooglePollenUpdateCoordinator]
