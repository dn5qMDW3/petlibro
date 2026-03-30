"""Support for PETLIBRO text entities."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable
from logging import getLogger
from homeassistant.components.text import TextEntity, TextEntityDescription

from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription, create_platform_setup
from .devices import Device
from .devices.feeders.one_rfid_smart_feeder import OneRFIDSmartFeeder

_LOGGER = getLogger(__name__)


@dataclass(frozen=True)
class PetLibroTextEntityDescription(TextEntityDescription, PetLibroEntityDescription[_DeviceT]):
    """A class that describes device text entities."""
    native_value: Callable[[_DeviceT], str] = lambda _: True


class PetLibroTextEntity(PetLibroEntity[_DeviceT], TextEntity):
    """PETLIBRO text entity."""

    entity_description: PetLibroTextEntityDescription[_DeviceT]

    @property
    def native_value(self) -> str | None:
        """Return the current display text."""
        return self.device.display_text

    async def async_set_value(self, native_value: str) -> None:
        """Set the current text value."""
        if not native_value:
            _LOGGER.warning("Empty value provided for %s", self.device.name)
            return
        uppercase_value = native_value.upper()
        try:
            await self.device.set_display_text(uppercase_value)
            self.device.display_text = uppercase_value
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error setting value %s for %s: %s", native_value, self.device.name, e)


DEVICE_TEXT_MAP: dict[type[Device], list[PetLibroTextEntityDescription]] = {
    OneRFIDSmartFeeder: [
        PetLibroTextEntityDescription[OneRFIDSmartFeeder](
            key="display_text",
            translation_key="display_text",
            icon="mdi:text-recognition",
            mode="text",
            native_max=100,
            native_min=1,
            pattern=r"^(?!\s*$)[a-zA-Z0-9 ]{1,20}$",
            name="Text on Display"
        )
    ],
}

async_setup_entry = create_platform_setup(
    PetLibroTextEntity, DEVICE_TEXT_MAP, "text"
)
