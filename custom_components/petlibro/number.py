"""Support for PETLIBRO numbers."""
from __future__ import annotations
from .api import make_api_call
import aiohttp
from aiohttp import ClientSession, ClientError
from dataclasses import dataclass
from dataclasses import dataclass, field
from collections.abc import Callable
from functools import cached_property
from typing import Optional
from typing import Any
import logging
from .const import DOMAIN, Unit, MAX_FEED_PORTIONS
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberDeviceClass,
    NumberMode
)
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfVolume
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry  # Added ConfigEntry import
from homeassistant.util.unit_conversion import VolumeConverter
from .hub import PetLibroHub  # Adjust the import path as necessary
from .member import Member


_LOGGER = logging.getLogger(__name__)

from .devices import Device
from .devices.device import Device
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
from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription

@dataclass(frozen=True)
class PetLibroNumberEntityDescription(NumberEntityDescription, PetLibroEntityDescription[_DeviceT]):
    """A class that describes device number entities."""

    device_class_fn: Callable[[_DeviceT], NumberDeviceClass | None] = lambda _: None
    native_unit_of_measurement_fn: Callable[[Member], str | None] = lambda _: None
    native_max_value_fn: Callable[[Member], float | None] = lambda _: None
    native_min_value_fn: Callable[[Member], float | None] = lambda _: None
    native_step_fn: Callable[[Member], float | None] = lambda _: None
    value_fn: Callable[[_DeviceT, Member], float] = lambda d, m: 0
    method: Callable[[_DeviceT, Member, float], float] = lambda d, m, v: None
    device_class: Optional[NumberDeviceClass] = None

class PetLibroNumberEntity(PetLibroEntity[_DeviceT], NumberEntity):
    """PETLIBRO sensor entity."""

    entity_description: PetLibroNumberEntityDescription[_DeviceT]

    @cached_property
    def device_class(self) -> NumberDeviceClass | None:
        """Return the device class to use in the frontend, if any."""
        return self.entity_description.device_class

    @property
    def native_value(self) -> float | None:
        """Return the current state."""
        if (value_fn := self.entity_description.value_fn(self.device, self.member)) is not None:
            return value_fn
        state = getattr(self.device, self.entity_description.key, None)
        if state is None:
            _LOGGER.warning(f"Value '{self.entity_description.key}' is None for device {self.device.name}")
            return None
        _LOGGER.debug(f"Retrieved value for '{self.entity_description.key}', {self.device.name}: {state}")
        return float(state)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value of the number."""
        _LOGGER.debug(f"Setting value {value} for {self.device.name}")
        try:
            # Regular case for sound_level or other methods that only need a value
            _LOGGER.debug(f"Calling method with value={value} for {self.device.name}")
            await self.entity_description.method(self.device, self.member, value)
            self.async_write_ha_state()
            _LOGGER.debug(f"Value {value} set successfully for {self.device.name}")
        except Exception as e:
            _LOGGER.error(f"Error setting value {value} for {self.device.name}: {e}")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the native unit of measurement."""
        if (uom := self.entity_description.native_unit_of_measurement_fn(self.member)) is not None:
            return uom
        return super().native_unit_of_measurement

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        if (min_value := self.entity_description.native_min_value_fn(self.member)) is not None:
            return min_value
        return super().native_min_value

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        if (max_value := self.entity_description.native_max_value_fn(self.member)) is not None:
            return max_value
        return super().native_max_value

    @property
    def native_step(self) -> float | None:
        """Return the increment/decrement step."""
        if (native_step := self.entity_description.native_step_fn(self.member)) is not None:
            return native_step
        return super().native_step


DEVICE_NUMBER_MAP: dict[type[Device], list[PetLibroNumberEntityDescription]] = {
    Feeder: [],
    AirSmartFeeder: [
        PetLibroNumberEntityDescription[AirSmartFeeder](
            key="manual_feed_quantity",
            translation_key="manual_feed_quantity",
            name="Manual Feed Quantity",
            icon="mdi:scale",
            mode=NumberMode.SLIDER,
            native_unit_of_measurement_fn=lambda m: m.feedUnitType.symbol 
                if m.feedUnitType != Unit.CUPS else "/12 cup",
            native_max_value_fn=lambda m: Unit.round(m.feedUnitType.factor * MAX_FEED_PORTIONS, m.feedUnitType)
                if m.feedUnitType != Unit.CUPS else MAX_FEED_PORTIONS,
            native_min_value_fn=lambda m: round(m.feedUnitType.factor, 16)
                if m.feedUnitType != Unit.CUPS else 1,
            native_step_fn=lambda m: m.feedUnitType.factor 
                if m.feedUnitType != Unit.CUPS else 1,
            method=lambda d, m, v: d.set_manual_feed_quantity(Unit.convert_feed(
                v, m.feedUnitType if m.feedUnitType != Unit.CUPS else None, None)),
            value_fn=lambda d, m: Unit.convert_feed(d.manual_feed_quantity, None, m.feedUnitType, True) 
                if m.feedUnitType != Unit.CUPS else d.manual_feed_quantity,
        ),
    ],
    GranarySmartFeeder: [
        PetLibroNumberEntityDescription[GranarySmartFeeder](
            key="manual_feed_quantity",
            translation_key="manual_feed_quantity",
            name="Manual Feed Quantity",
            icon="mdi:scale",
            mode=NumberMode.SLIDER,
            native_unit_of_measurement_fn=lambda m: m.feedUnitType.symbol 
                if m.feedUnitType != Unit.CUPS else "/12 cup",
            native_max_value_fn=lambda m: Unit.round(m.feedUnitType.factor * MAX_FEED_PORTIONS, m.feedUnitType)
                if m.feedUnitType != Unit.CUPS else MAX_FEED_PORTIONS,
            native_min_value_fn=lambda m: round(m.feedUnitType.factor, 16)
                if m.feedUnitType != Unit.CUPS else 1,
            native_step_fn=lambda m: m.feedUnitType.factor 
                if m.feedUnitType != Unit.CUPS else 1,
            method=lambda d, m, v: d.set_manual_feed_quantity(Unit.convert_feed(
                v, m.feedUnitType if m.feedUnitType != Unit.CUPS else None, None)),
            value_fn=lambda d, m: Unit.convert_feed(d.manual_feed_quantity, None, m.feedUnitType, True) 
                if m.feedUnitType != Unit.CUPS else d.manual_feed_quantity,
        ),
        PetLibroNumberEntityDescription[GranarySmartFeeder](
            key="desiccant_frequency",
            translation_key="desiccant_frequency",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.desiccant_frequency,
            method=lambda device, m, value: device.set_desiccant_frequency(value),
            name="Desiccant Frequency",
        ),
    ],
    GranarySmartCameraFeeder: [
        PetLibroNumberEntityDescription[GranarySmartCameraFeeder](
            key="manual_feed_quantity",
            translation_key="manual_feed_quantity",
            name="Manual Feed Quantity",
            icon="mdi:scale",
            mode=NumberMode.SLIDER,
            native_unit_of_measurement_fn=lambda m: m.feedUnitType.symbol 
                if m.feedUnitType != Unit.CUPS else "/12 cup",
            native_max_value_fn=lambda m: Unit.round(m.feedUnitType.factor * MAX_FEED_PORTIONS, m.feedUnitType)
                if m.feedUnitType != Unit.CUPS else MAX_FEED_PORTIONS,
            native_min_value_fn=lambda m: round(m.feedUnitType.factor, 16)
                if m.feedUnitType != Unit.CUPS else 1,
            native_step_fn=lambda m: m.feedUnitType.factor 
                if m.feedUnitType != Unit.CUPS else 1,
            method=lambda d, m, v: d.set_manual_feed_quantity(Unit.convert_feed(
                v, m.feedUnitType if m.feedUnitType != Unit.CUPS else None, None)),
            value_fn=lambda d, m: Unit.convert_feed(d.manual_feed_quantity, None, m.feedUnitType, True) 
                if m.feedUnitType != Unit.CUPS else d.manual_feed_quantity,
        ),
    ],
    OneRFIDSmartFeeder: [
        PetLibroNumberEntityDescription[OneRFIDSmartFeeder](
            key="desiccant_cycle",
            translation_key="desiccant_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.desiccant_cycle,
            method=lambda device, m, value: device.set_desiccant_cycle(value),
            name="Desiccant Cycle",
        ),
        PetLibroNumberEntityDescription[OneRFIDSmartFeeder](
            key="sound_level",
            translation_key="sound_level",
            icon="mdi:volume-high",
            native_unit_of_measurement="%",
            native_max_value=100,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.sound_level,
            method=lambda device, m, value: device.set_sound_level(value),
            name="Sound Level",
        ),
        PetLibroNumberEntityDescription[OneRFIDSmartFeeder](
            key="lid_close_time",
            translation_key="lid_close_time",
            icon="mdi:timer",
            native_unit_of_measurement="s",
            native_max_value=10,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.lid_close_time,
            method=lambda device, m, value: device.set_lid_close_time(value),
            name="Lid Close Time",
        ),
        PetLibroNumberEntityDescription[OneRFIDSmartFeeder](
            key="manual_feed_quantity",
            translation_key="manual_feed_quantity",
            name="Manual Feed Quantity",
            icon="mdi:scale",
            mode=NumberMode.SLIDER,
            native_unit_of_measurement_fn=lambda m: m.feedUnitType.symbol 
                if m.feedUnitType != Unit.CUPS else "/12 cup",
            native_max_value_fn=lambda m: Unit.round(m.feedUnitType.factor * MAX_FEED_PORTIONS, m.feedUnitType)
                if m.feedUnitType != Unit.CUPS else MAX_FEED_PORTIONS,
            native_min_value_fn=lambda m: round(m.feedUnitType.factor, 16)
                if m.feedUnitType != Unit.CUPS else 1,
            native_step_fn=lambda m: m.feedUnitType.factor 
                if m.feedUnitType != Unit.CUPS else 1,
            method=lambda d, m, v: d.set_manual_feed_quantity(Unit.convert_feed(
                v, m.feedUnitType if m.feedUnitType != Unit.CUPS else None, None)),
            value_fn=lambda d, m: Unit.convert_feed(d.manual_feed_quantity, None, m.feedUnitType, True) 
                if m.feedUnitType != Unit.CUPS else d.manual_feed_quantity,
        ),
    ],
    PolarWetFoodFeeder: [],
    SpaceSmartFeeder: [
        PetLibroNumberEntityDescription[SpaceSmartFeeder](
            key="manual_feed_quantity",
            translation_key="manual_feed_quantity",
            name="Manual Feed Quantity",
            icon="mdi:scale",
            mode=NumberMode.SLIDER,
            native_unit_of_measurement_fn=lambda m: m.feedUnitType.symbol 
                if m.feedUnitType != Unit.CUPS else "/12 cup",
            native_max_value_fn=lambda m: Unit.round(m.feedUnitType.factor * MAX_FEED_PORTIONS, m.feedUnitType)
                if m.feedUnitType != Unit.CUPS else MAX_FEED_PORTIONS,
            native_min_value_fn=lambda m: round(m.feedUnitType.factor, 16)
                if m.feedUnitType != Unit.CUPS else 1,
            native_step_fn=lambda m: m.feedUnitType.factor 
                if m.feedUnitType != Unit.CUPS else 1,
            method=lambda d, m, v: d.set_manual_feed_quantity(Unit.convert_feed(
                v, m.feedUnitType if m.feedUnitType != Unit.CUPS else None, None)),
            value_fn=lambda d, m: Unit.convert_feed(d.manual_feed_quantity, None, m.feedUnitType, True) 
                if m.feedUnitType != Unit.CUPS else d.manual_feed_quantity,
        ),
        PetLibroNumberEntityDescription[SpaceSmartFeeder](
            key="sound_level",
            translation_key="sound_level",
            icon="mdi:volume-high",
            native_unit_of_measurement="%",
            native_max_value=100,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.sound_level,
            method=lambda device, m, value: device.set_sound_level(value),
            name="Sound Level",
        ),
    ],
    DockstreamSmartFountain: [
        PetLibroNumberEntityDescription[DockstreamSmartFountain](
            key="water_interval",
            translation_key="water_interval",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_interval,
            method=lambda device, m, value: device.set_water_interval(value),
            name="Water Interval",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartFountain](
            key="water_dispensing_duration",
            translation_key="water_dispensing_duration",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_dispensing_duration,
            method=lambda device, m, value: device.set_water_dispensing_duration(value),
            name="Water Dispensing Duration",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartFountain](
            key="cleaning_cycle",
            translation_key="cleaning_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.cleaning_cycle,
            method=lambda device, m, value: device.set_cleaning_cycle(value),
            name="Cleaning Cycle",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartFountain](
            key="filter_cycle",
            translation_key="filter_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.filter_cycle,
            method=lambda device, m, value: device.set_filter_cycle(value),
            name="Filter Cycle",
        ),
    ],
    DockstreamSmartRFIDFountain: [
        PetLibroNumberEntityDescription[DockstreamSmartRFIDFountain](
            key="water_interval",
            translation_key="water_interval",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_interval,
            method=lambda device, m, value: device.set_water_interval(value),
            name="Water Interval",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartRFIDFountain](
            key="water_dispensing_duration",
            translation_key="water_dispensing_duration",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_dispensing_duration,
            method=lambda device, m, value: device.set_water_dispensing_duration(value),
            name="Water Dispensing Duration",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartRFIDFountain](
            key="cleaning_cycle",
            translation_key="cleaning_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.cleaning_cycle,
            method=lambda device, m, value: device.set_cleaning_cycle(value),
            name="Cleaning Cycle",
        ),
        PetLibroNumberEntityDescription[DockstreamSmartRFIDFountain](
            key="filter_cycle",
            translation_key="filter_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.filter_cycle,
            method=lambda device, m, value: device.set_filter_cycle(value),
            name="Filter Cycle",
        ),
    ],
    Dockstream2SmartCordlessFountain: [
        # Not currently suppported by device, hoping firmware update will add this.
        # PetLibroNumberEntityDescription[Dockstream2SmartCordlessFountain](
        #     key="water_sensing_delay",
        #     translation_key="water_sensing_delay",
        #     icon="mdi:timer",
        #     mode="slider",
        #     native_unit_of_measurement="s",
        #     native_max_value=180,
        #     native_min_value=1,
        #     native_step=1,
        #     value_fn=lambda device, m: device.water_sensing_delay,
        #     method=lambda device, value: device.set_water_sensing_delay(value),
        #     name="Water Sensing Delay"
        # ),
        PetLibroNumberEntityDescription[Dockstream2SmartCordlessFountain](
            key="water_low_threshold",
            translation_key="water_low_threshold",
            icon="mdi:gauge",
            mode="slider",
            native_unit_of_measurement_fn=lambda m: m.waterUnitType.symbol,
            native_max_value_fn=lambda m: Unit.round(m.waterUnitType.factor * 3000, m.waterUnitType),
            native_min_value_fn=lambda m: Unit.round(m.waterUnitType.factor * 650, m.waterUnitType),
            native_step_fn=lambda m: Unit.round(m.waterUnitType.factor, m.waterUnitType),
            value_fn=lambda d, m: Unit.convert_feed(d.water_low_threshold, None, m.waterUnitType, True),
            method=lambda d, m, v: d.set_water_low_threshold(round(VolumeConverter.convert(
                v, m.waterUnitType.symbol, UnitOfVolume.MILLILITERS))),
            name="Water Low Threshold"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartCordlessFountain](
            key="cleaning_cycle",
            translation_key="cleaning_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.cleaning_cycle,
            method=lambda device, value: device.set_cleaning_cycle(value),
            name="Cleaning Cycle"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartCordlessFountain](
            key="filter_cycle",
            translation_key="filter_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.filter_cycle,
            method=lambda device, value: device.set_filter_cycle(value),
            name="Filter Cycle"
        ),
    ],
    Dockstream2SmartFountain: [
        # Not currently suppported by device, hoping firmware update will add this.
        # PetLibroNumberEntityDescription[Dockstream2SmartCordlessFountain](
        #     key="water_sensing_delay",
        #     translation_key="water_sensing_delay",
        #     icon="mdi:timer",
        #     mode="slider",
        #     native_unit_of_measurement="s",
        #     native_max_value=180,
        #     native_min_value=1,
        #     native_step=1,
        #     value_fn=lambda device, m: device.water_sensing_delay,
        #     method=lambda device, value: device.set_water_sensing_delay(value),
        #     name="Water Sensing Delay"
        # ),
        PetLibroNumberEntityDescription[Dockstream2SmartFountain](
            key="water_low_threshold",
            translation_key="water_low_threshold",
            icon="mdi:gauge",
            mode="slider",
            native_unit_of_measurement_fn=lambda m: m.waterUnitType.symbol,
            native_max_value_fn=lambda m: Unit.round(m.waterUnitType.factor * 3000, m.waterUnitType),
            native_min_value_fn=lambda m: Unit.round(m.waterUnitType.factor * 650, m.waterUnitType),
            native_step_fn=lambda m: Unit.round(m.waterUnitType.factor, m.waterUnitType),
            value_fn=lambda d, m: Unit.convert_feed(d.water_low_threshold, None, m.waterUnitType, True),
            method=lambda d, m, v: d.set_water_low_threshold(round(VolumeConverter.convert(
                v, m.waterUnitType.symbol, UnitOfVolume.MILLILITERS))),
            name="Water Low Threshold"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartFountain](
            key="cleaning_cycle",
            translation_key="cleaning_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.cleaning_cycle,
            method=lambda device, value: device.set_cleaning_cycle(value),
            name="Cleaning Cycle"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartFountain](
            key="filter_cycle",
            translation_key="filter_cycle",
            icon="mdi:calendar-alert",
            native_unit_of_measurement="Days",
            mode="box",
            native_max_value=60,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.filter_cycle,
            method=lambda device, value: device.set_filter_cycle(value),
            name="Filter Cycle"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartFountain](
            key="water_interval",
            translation_key="water_interval",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_interval,
            method=lambda device, value: device.set_water_interval(value),
            name="Water Interval"
        ),
        PetLibroNumberEntityDescription[Dockstream2SmartFountain](
            key="water_dispensing_duration",
            translation_key="water_dispensing_duration",
            icon="mdi:timer",
            native_unit_of_measurement="m",
            native_max_value=180,
            native_min_value=1,
            native_step=1,
            value_fn=lambda device, m: device.water_dispensing_duration,
            method=lambda device, value: device.set_water_dispensing_duration(value),
            name="Water Dispensing Duration"
        ),
    ],
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,  # Use ConfigEntry
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PETLIBRO number using config entry."""
    # Retrieve the hub from hass.data that was set up in __init__.py
    hub = hass.data[DOMAIN].get(entry.entry_id)

    if not hub:
        _LOGGER.error("Hub not found for entry: %s", entry.entry_id)
        return

    # Ensure that the devices are loaded (if load_devices is not already called elsewhere)
    if not hub.devices:
        _LOGGER.warning("No devices found in hub during number setup.")
        return

    # Log the contents of the hub data for debugging
    _LOGGER.debug("Hub data: %s", hub)

    devices = hub.devices  # Devices should already be loaded in the hub
    _LOGGER.debug("Devices in hub: %s", devices)

    # Create number entities for each device based on the number map
    entities = [
        PetLibroNumberEntity(device, hub, description)
        for device in devices  # Iterate through devices from the hub
        for device_type, entity_descriptions in DEVICE_NUMBER_MAP.items()
        if isinstance(device, device_type)
        for description in entity_descriptions
    ]

    if not entities:
        _LOGGER.warning("No number entities added, entities list is empty!")
    else:
        # Log the number of entities and their details
        _LOGGER.debug("Adding %d PetLibro number entities", len(entities))
        for entity in entities:
            _LOGGER.debug("Adding number entity: %s for device %s", entity.entity_description.name, entity.device.name)

        # Add number entities to Home Assistant
        async_add_entities(entities)
