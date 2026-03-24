"""Support for PETLIBRO text entities."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any
import logging
from homeassistant.components.text import (
    TextEntity,
    TextEntityDescription,
)


_LOGGER = logging.getLogger(__name__)

from .devices import Device
from .devices.feeders.feeder import Feeder
from .devices.feeders.air_smart_feeder import AirSmartFeeder
from .devices.feeders.granary_smart_feeder import GranarySmartFeeder
from .devices.feeders.granary_smart_camera_feeder import GranarySmartCameraFeeder
from .devices.feeders.one_rfid_smart_feeder import OneRFIDSmartFeeder
from .devices.feeders.polar_wet_food_feeder import PolarWetFoodFeeder
from .devices.feeders.space_smart_feeder import SpaceSmartFeeder
from .devices.fountains.dockstream_smart_fountain import DockstreamSmartFountain
from .devices.fountains.dockstream_smart_rfid_fountain import DockstreamSmartRFIDFountain
from .devices.fountains.dockstream_2_smart_cordless_fountain import Dockstream2SmartCordlessFountain
from .devices.fountains.dockstream_2_smart_fountain import Dockstream2SmartFountain
from .devices.litterboxes.luma_smart_litter_box import LumaSmartLitterBox
from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription, create_platform_setup

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
        _LOGGER.debug(f"Setting value {native_value} for {self.device.name}")
        try:
            if not native_value:
                _LOGGER.warning(f"Empty value provided for {self.device.name}")
                return
            # Set text to uppercase as this is what API accepts.
            uppercase_value = native_value.upper()
            _LOGGER.debug(f"Calling method with value={uppercase_value} for {self.device.name}")
            await self.device.set_display_text(uppercase_value)
            # Update value in HA to uppercase as well
            self.device.display_text = uppercase_value
            _LOGGER.debug(f"Original: {native_value}, Uppercased: {uppercase_value} for {self.device.name}")
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Error setting value {native_value} for {self.device.name}: {e}")

DEVICE_TEXT_MAP: dict[type[Device], list[PetLibroTextEntityDescription]] = {
    Feeder: [
    ],
    AirSmartFeeder: [
    ],
    GranarySmartFeeder: [
    ],
    GranarySmartCameraFeeder: [
    ],
    PolarWetFoodFeeder: [
    ],
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
    SpaceSmartFeeder: [
    ],
    DockstreamSmartFountain: [
    ],
    DockstreamSmartRFIDFountain: [
    ],
    Dockstream2SmartFountain: [
    ],
    Dockstream2SmartCordlessFountain: [
    ],
    LumaSmartLitterBox: [
    ],
}

async_setup_entry = create_platform_setup(
    PetLibroTextEntity, DEVICE_TEXT_MAP, "text"
)

