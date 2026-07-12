"""Creates the sensor entities for Google Pollen."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

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
from .coordinator import GooglePollenConfigEntry, GooglePollenUpdateCoordinator
from .google_pollen_api import PollenCurrentConditionsData

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0

_POLLEN_TYPES = ("tree", "grass", "weed")


def _exists_fn(
    pollen_type: str,
) -> Callable[[PollenCurrentConditionsData], bool]:
    return lambda x: pollen_type in x.types


def _value_fn(
    pollen_type: str, field: str
) -> Callable[[PollenCurrentConditionsData], StateType]:
    return lambda x: x.types.get(pollen_type, {}).get(field)


@dataclass(frozen=True, kw_only=True)
class PollenSensorEntityDescription(SensorEntityDescription):
    """Describes Pollen sensor entity."""

    exists_fn: Callable[[PollenCurrentConditionsData], bool] = lambda _: True
    value_fn: Callable[[PollenCurrentConditionsData], StateType]


def _per_type_sensors() -> tuple[PollenSensorEntityDescription, ...]:
    """Generate sensor descriptions for each pollen type."""
    sensors: list[PollenSensorEntityDescription] = []
    for pollen_type in _POLLEN_TYPES:
        sensors.extend(
            [
                PollenSensorEntityDescription(
                    key=f"{pollen_type}_pollen_index",
                    translation_key=f"{pollen_type}_pollen_index",
                    state_class=SensorStateClass.MEASUREMENT,
                    exists_fn=_exists_fn(pollen_type),
                    value_fn=_value_fn(pollen_type, "value"),
                ),
                PollenSensorEntityDescription(
                    key=f"{pollen_type}_pollen_category",
                    translation_key=f"{pollen_type}_pollen_category",
                    exists_fn=_exists_fn(pollen_type),
                    value_fn=_value_fn(pollen_type, "category"),
                ),
                PollenSensorEntityDescription(
                    key=f"{pollen_type}_pollen_index_description",
                    translation_key=f"{pollen_type}_pollen_index_description",
                    entity_registry_enabled_default=False,
                    exists_fn=_exists_fn(pollen_type),
                    value_fn=_value_fn(pollen_type, "index_description"),
                ),
                PollenSensorEntityDescription(
                    key=f"{pollen_type}_pollen_color",
                    translation_key=f"{pollen_type}_pollen_color",
                    entity_registry_enabled_default=False,
                    exists_fn=_exists_fn(pollen_type),
                    value_fn=_value_fn(pollen_type, "color"),
                ),
                PollenSensorEntityDescription(
                    key=f"{pollen_type}_pollen_health_recommendations",
                    translation_key=f"{pollen_type}_pollen_health_recommendations",
                    entity_registry_enabled_default=False,
                    exists_fn=_exists_fn(pollen_type),
                    value_fn=_value_fn(pollen_type, "health_recommendations"),
                ),
            ]
        )
    return tuple(sensors)


POLLEN_SENSOR_TYPES: tuple[PollenSensorEntityDescription, ...] = (
    *_per_type_sensors(),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GooglePollenConfigEntry,
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
    """Pollen sensor entity."""

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
