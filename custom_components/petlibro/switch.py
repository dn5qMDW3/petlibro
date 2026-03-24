"""Support for PETLIBRO switches."""
from __future__ import annotations
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Generic
import logging
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory

_LOGGER = logging.getLogger(__name__)

from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription, create_platform_setup
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

@dataclass(frozen=True)
class RequiredKeysMixin(Generic[_DeviceT]):
    """A class that describes devices switch entity required keys."""

    set_fn: Callable[[_DeviceT, bool], Coroutine[Any, Any, None]]

@dataclass(frozen=True)
class PetLibroSwitchEntityDescription(SwitchEntityDescription, PetLibroEntityDescription[_DeviceT], RequiredKeysMixin[_DeviceT]):
    """A class that describes device switch entities."""

    entity_category: EntityCategory = EntityCategory.CONFIG

DEVICE_SWITCH_MAP: dict[type[Device], list[PetLibroSwitchEntityDescription]] = {
    Feeder: [
    ],
    AirSmartFeeder: [
    ],
    GranarySmartFeeder: [
    ],
    GranarySmartCameraFeeder: [
    ],
    OneRFIDSmartFeeder: [
    ],
    PolarWetFoodFeeder: [
        PetLibroSwitchEntityDescription[PolarWetFoodFeeder](
            key="manual_feed_now",
            translation_key="manual_feed_now",
            set_fn=lambda device, value: device.set_manual_feed_now(value, device.plate_position),
            name="Manually Open/Close Lid"
        ),
    ],
    SpaceSmartFeeder: [
    ],
    DockstreamSmartFountain: [
    ],
    DockstreamSmartRFIDFountain: [
    ],
    Dockstream2SmartCordlessFountain: [
    ],
    Dockstream2SmartFountain: [
    ],
    LumaSmartLitterBox: [
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="sound_switch",
            translation_key="sound_switch",
            set_fn=lambda device, value: device.set_sound_switch(value),
            name="Sound",
        ),
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="light_switch",
            translation_key="light_switch",
            set_fn=lambda device, value: device.set_light_switch(value),
            name="Light",
        ),
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="deodorization_mode_switch",
            translation_key="deodorization_mode_switch",
            set_fn=lambda device, value: device.set_deodorization_switch(value),
            name="Deodorization",
        ),
    ],
}

class PetLibroSwitchEntity(PetLibroEntity[_DeviceT], SwitchEntity):
    """PETLIBRO switch entity."""

    entity_description: PetLibroSwitchEntityDescription[_DeviceT]  # type: ignore [reportIncompatibleVariableOverride]

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return bool(getattr(self.device, self.entity_description.key))

    @property
    def available(self) -> bool:
        """Check if the device is available."""
        return getattr(self.device, 'online', False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.set_fn(self.device, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.set_fn(self.device, False)

async_setup_entry = create_platform_setup(
    PetLibroSwitchEntity, DEVICE_SWITCH_MAP, "switch"
)

