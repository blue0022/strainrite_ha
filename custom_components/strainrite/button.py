from __future__ import annotations

import dataclasses

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StrainriteCoordinator
from .entity import StrainriteEntity


@dataclasses.dataclass(frozen=True, kw_only=True)
class StrainriteButtonDescription(ButtonEntityDescription):
    command: str = ""


BUTTONS: tuple[StrainriteButtonDescription, ...] = (
    StrainriteButtonDescription(
        key="clear_alarm",
        name="Clear Alarm",
        icon="mdi:alarm-off",
        command="clear;",
    ),
    StrainriteButtonDescription(
        key="mute_alarm",
        name="Mute Alarm",
        icon="mdi:volume-off",
        command="mute;",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StrainriteCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StrainriteButton(coordinator, description) for description in BUTTONS
    )


class StrainriteButton(StrainriteEntity, ButtonEntity):
    entity_description: StrainriteButtonDescription

    def __init__(
        self,
        coordinator: StrainriteCoordinator,
        description: StrainriteButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = coordinator.data.get("serial", coordinator.host)
        self._attr_unique_id = f"{serial}_{description.key}"

    async def async_press(self) -> None:
        await self.coordinator.async_send_command(self.entity_description.command)
