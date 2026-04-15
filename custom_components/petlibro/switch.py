"""Support for PETLIBRO switches."""
from __future__ import annotations
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Generic
import logging
from .const import DOMAIN
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from .hub import PetLibroHub

from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription
from .devices import Device
from .devices.feeders.polar_wet_food_feeder import PolarWetFoodFeeder
from .devices.litterboxes.luma_smart_litter_box import LumaSmartLitterBox
from .pets.entity import PL_PetSwitchEntity


_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class RequiredKeysMixin(Generic[_DeviceT]):
    """A class that describes devices switch entity required keys."""
    set_fn: Callable[[_DeviceT, bool], Coroutine[Any, Any, None]]

@dataclass(frozen=True)
class PetLibroSwitchEntityDescription(SwitchEntityDescription, PetLibroEntityDescription[_DeviceT], RequiredKeysMixin[_DeviceT]):
    """A class that describes device switch entities."""
    entity_category: EntityCategory = EntityCategory.CONFIG

DEVICE_SWITCH_MAP: dict[type[Device], list[PetLibroSwitchEntityDescription]] = {
    PolarWetFoodFeeder: [
        PetLibroSwitchEntityDescription[PolarWetFoodFeeder](
            key="manual_feed_now",
            translation_key="manual_feed_now",
            set_fn=lambda device, value: device.set_manual_feed_now(value, device.plate_position),
            name="Manually Open/Close Lid"
        ),
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
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="after_deodorization_switch",
            translation_key="after_deodorization_switch",
            set_fn=lambda device, value: device.set_after_deodorization_switch(value),
            name="After-Use Deodorization",
        ),
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="avoid_repeat_clean",
            translation_key="avoid_repeat_clean",
            set_fn=lambda device, value: device.set_avoid_repeat_clean(value),
            name="Avoid Repeat Clean",
        ),
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="enable_auto_clean_in_sleep_mode",
            translation_key="enable_auto_clean_in_sleep_mode",
            set_fn=lambda device, value: device.set_enable_auto_clean_in_sleep_mode(value),
            name="Auto Clean in Sleep Mode",
        ),
        PetLibroSwitchEntityDescription[LumaSmartLitterBox](
            key="enable_deodorization_in_sleep_mode",
            translation_key="enable_deodorization_in_sleep_mode",
            set_fn=lambda device, value: device.set_enable_deodorization_in_sleep_mode(value),
            name="Deodorize in Sleep Mode",
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

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PETLIBRO switches using config entry."""
    hub: PetLibroHub = hass.data[DOMAIN].get(entry.entry_id)

    if not hub:
        _LOGGER.error("Hub not found for entry: %s", entry.entry_id)
        return

    devices = hub.devices
    pets = hub.pets

    if not (devices or pets):
        return

    entities = []

    if devices:
        entities.extend(
            PetLibroSwitchEntity(device, hub, description)
            for device in devices.values()
            for device_type, entity_descriptions in DEVICE_SWITCH_MAP.items()
            if isinstance(device, device_type)
            for description in entity_descriptions
        )

    if pets:
        for pet in pets.values():
            entities.extend(pet.entities(PL_PetSwitchEntity, hub))

    if entities:
        _LOGGER.debug("Adding %d PetLibro switch entities", len(entities))
        async_add_entities(entities)
