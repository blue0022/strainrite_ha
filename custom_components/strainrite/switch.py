from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StrainriteCoordinator
from .entity import StrainriteEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StrainriteCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrainriteFenceSwitch(coordinator)])


class StrainriteFenceSwitch(StrainriteEntity, SwitchEntity):
    _attr_name = "Fence"
    _attr_icon = "mdi:electric-switch"

    def __init__(self, coordinator: StrainriteCoordinator) -> None:
        super().__init__(coordinator)
        serial = coordinator.data.get("serial", coordinator.host)
        self._attr_unique_id = f"{serial}_fence_switch"

    @property
    def is_on(self) -> bool:
        return str(self.coordinator.data.get("armed", "0")) == "1"

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_send_command("armed=1;")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send_command("armed=0;")
        await self.coordinator.async_request_refresh()
