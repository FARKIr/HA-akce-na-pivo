"""Tlačidlo pre okamžitú aktualizáciu."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BeerConfigEntry
from .coordinator import BeerDealsCoordinator
from .entity import BeerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: BeerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RefreshButton(entry.runtime_data)])


class RefreshButton(BeerEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"
    _attr_translation_key = "refresh"

    def __init__(self, coordinator: BeerDealsCoordinator) -> None:
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
