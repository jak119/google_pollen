"""Creates the sensor entities for Google Pollen."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GooglePollenUpdateCoordinator
from .google_pollen_api import PollenCurrentConditionsData

_LOGGER = logging.getLogger(__name__)
# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PollenSensorEntityDescription(SensorEntityDescription):
    """Describes Pollen sensor entity."""

    exists_fn: Callable[[PollenCurrentConditionsData], bool] = lambda _: True
    value_fn: Callable[[PollenCurrentConditionsData], StateType]


POLLEN_SENSOR_TYPES: tuple[PollenSensorEntityDescription, ...] = (
    PollenSensorEntityDescription(
        key="pollen_index",
        translation_key="pollen_index",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.index,
    ),
    PollenSensorEntityDescription(
        key="pollen_category",
        translation_key="pollen_category",
        value_fn=lambda x: x.category,
    ),
    PollenSensorEntityDescription(
        key="tree_pollen",
        translation_key="tree_pollen",
        exists_fn=lambda x: "tree" in x.types,
        value_fn=lambda x: x.types.get("tree", {}).get("value"),
    ),
    PollenSensorEntityDescription(
        key="grass_pollen",
        translation_key="grass_pollen",
        exists_fn=lambda x: "grass" in x.types,
        value_fn=lambda x: x.types.get("grass", {}).get("value"),
    ),
    PollenSensorEntityDescription(
        key="weed_pollen",
        translation_key="weed_pollen",
        exists_fn=lambda x: "weed" in x.types,
        value_fn=lambda x: x.types.get("weed", {}).get("value"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinators = entry.runtime_data.subentries_runtime_data

    for subentry_id, subentry in entry.subentries.items():
        coordinator: GooglePollenUpdateCoordinator = coordinators[subentry_id]
        _LOGGER.debug("subentry.data: %s", subentry.data)
        async_add_entities(
            (
                PollenSensorEntity(coordinator, description, subentry_id, subentry)
                for description in POLLEN_SENSOR_TYPES
                if description.exists_fn(coordinator.data)
            ),
            config_subentry_id=subentry_id,
        )


class PollenSensorEntity(
    CoordinatorEntity[GooglePollenUpdateCoordinator], SensorEntity
):
    """Defining the Pollen Sensors with PollenSensorEntityDescription."""

    entity_description: PollenSensorEntityDescription
    _attr_attribution = "Data provided by Google Pollen"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GooglePollenUpdateCoordinator,
        description: PollenSensorEntityDescription,
        subentry_id: str,
        subentry: ConfigSubentry,
    ) -> None:
        """Set up Pollen Sensors."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{description.key}_{subentry.data[CONF_LATITUDE]}_{subentry.data[CONF_LONGITUDE]}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{self.coordinator.config_entry.entry_id}_{subentry_id}")
            },
            name=subentry.title,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
