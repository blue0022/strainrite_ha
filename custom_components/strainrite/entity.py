from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StrainriteCoordinator


class StrainriteEntity(CoordinatorEntity[StrainriteCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: StrainriteCoordinator) -> None:
        super().__init__(coordinator)
        serial = coordinator.data.get("serial", coordinator.host)
        model = coordinator.data.get("model", "Energizer")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Strainrite {model}",
            manufacturer="Strainrite",
            model=model,
            sw_version=coordinator.data.get("version"),
            configuration_url=f"http://{coordinator.host}",
        )
