"""PETLIBRO entities for common data and methods."""

from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .devices import Device
from .devices.event import EVENT_UPDATE
from .const import DOMAIN
from .hub import PetLibroHub

_LOGGER = logging.getLogger(__name__)

_DeviceT = TypeVar("_DeviceT", bound=Device)


class PetLibroEntity(
    CoordinatorEntity[DataUpdateCoordinator[bool]], Generic[_DeviceT]
):
    """Generic PETLIBRO entity representing common data and methods."""

    _attr_has_entity_name = True

    def __init__(
        self, device: _DeviceT, hub: PetLibroHub, description: PetLibroEntityDescription[_DeviceT]
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.device = device
        self.hub = hub
        self.member = hub.member
        self.entity_description = description
        self.key = description.key
        self._attr_unique_id = f"{self.device.serial}-{description.key}"

        if not self.device.device_id:
            self.device.set_device_id()
        if not self.device.saved_to_options:
            self.device.save_to_options()

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device information for a PETLIBRO."""
        assert self.device.serial
        return DeviceInfo(
            identifiers=self.device.device_identifiers,
            connections={(CONNECTION_NETWORK_MAC, self.device.mac)},
            manufacturer="PETLIBRO",
            model=self.device.model,
            name=self.device.name,
            sw_version=self.device.software_version,
            hw_version=self.device.hardware_version,
            serial_number=self.device.serial,
        )

    @property
    def entity_picture(self) -> str | None:
        """Return the device product icon as entity picture.

        Consumed by petlibro-cards (getDeviceImage in utils.ts) to render
        the device image on the dashboard card. Do not remove without
        updating the cards' image-resolution logic.
        """
        return getattr(self.device, "icon_url", None)

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.async_on_remove(self.device.on(EVENT_UPDATE, self.async_write_ha_state))

class PetLibroEntityDescription(EntityDescription, Generic[_DeviceT]):
    """PETLIBRO Entity description"""


def create_platform_setup(
    entity_class: type[PetLibroEntity[Any]],
    device_map: dict[type[Device], list[Any]],
    platform_name: str,
):
    """Create a standard async_setup_entry for a platform.

    This factory eliminates the duplicated setup boilerplate across
    platforms that only create entities from device-to-description mappings.
    """

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        hub: PetLibroHub | None = getattr(entry, "runtime_data", None)

        if not hub:
            _LOGGER.error("Hub not found for entry: %s", entry.entry_id)
            return

        if not hub.devices:
            _LOGGER.warning("No devices found in hub during %s setup.", platform_name)
            return

        entities = [
            entity_class(device, hub, description)
            for device in hub.devices.values()
            for device_type, entity_descriptions in device_map.items()
            if isinstance(device, device_type)
            for description in entity_descriptions
        ]

        if entities:
            _LOGGER.debug("Adding %d PetLibro %s entities", len(entities), platform_name)
            async_add_entities(entities)

    return async_setup_entry
