from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StrainriteCoordinator
from .entity import StrainriteEntity


def _parse_signal(value: str) -> int | None:
    """Extract numeric dBm from strings like '-69 dbi'."""
    try:
        return int(value.split()[0])
    except (ValueError, AttributeError, IndexError):
        return None


def _nonempty(value: str) -> str | None:
    return value if value else None


@dataclasses.dataclass(frozen=True, kw_only=True)
class StrainriteSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Any], Any] = lambda v: v or None


SENSORS: tuple[StrainriteSensorDescription, ...] = (
    StrainriteSensorDescription(
        key="volts",
        name="Fence Voltage",
        native_unit_of_measurement="kV",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda v: float(v) if v else None,
    ),
    StrainriteSensorDescription(
        key="joules",
        name="Energy Output",
        native_unit_of_measurement="J",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        value_fn=lambda v: float(v) if v else None,
    ),
    StrainriteSensorDescription(
        key="vin",
        name="Supply Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda v: float(v) if v else None,
    ),
    StrainriteSensorDescription(
        key="temp",
        name="CPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda v: float(v) if v else None,
    ),
    StrainriteSensorDescription(
        key="signal",
        name="Signal Strength",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_parse_signal,
    ),
    StrainriteSensorDescription(
        key="runtime",
        name="Runtime",
        icon="mdi:clock-outline",
        value_fn=_nonempty,
    ),
    StrainriteSensorDescription(
        key="alarm",
        name="Alarm",
        icon="mdi:alarm-light",
        value_fn=_nonempty,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StrainriteCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StrainriteSensor(coordinator, description) for description in SENSORS
    )


class StrainriteSensor(StrainriteEntity, SensorEntity):
    entity_description: StrainriteSensorDescription

    def __init__(
        self,
        coordinator: StrainriteCoordinator,
        description: StrainriteSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = coordinator.data.get("serial", coordinator.host)
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def native_value(self) -> Any:
        raw = self.coordinator.data.get(self.entity_description.key)
        return self.entity_description.value_fn(raw)
