import logging

from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntry
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
from .devices.litterboxes.litter_box import LitterBox
from .devices.litterboxes.luma_smart_litter_box import LumaSmartLitterBox
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, PLATFORMS
from .hub import PetLibroHub

_LOGGER = logging.getLogger(__name__)

type PetLibroConfigEntry = ConfigEntry[PetLibroHub]


# All device types currently support the same set of platforms
DEFAULT_PLATFORMS = (
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
    Platform.UPDATE,
)

PLATFORMS_BY_TYPE = {
    cls: DEFAULT_PLATFORMS
    for cls in [
        Feeder,
        AirSmartFeeder,
        GranarySmartFeeder,
        GranarySmartCameraFeeder,
        OneRFIDSmartFeeder,
        PolarWetFoodFeeder,
        SpaceSmartFeeder,
        DockstreamSmartFountain,
        DockstreamSmartRFIDFountain,
        Dockstream2SmartCordlessFountain,
        Dockstream2SmartFountain,
        LumaSmartLitterBox,
    ]
}


def get_platforms_for_devices(devices: list[Device]) -> set[Platform]:
    """Get platforms for devices."""
    return {
        platform
        for device in devices
        for device_type, platforms in PLATFORMS_BY_TYPE.items()
        if isinstance(device, device_type)
        for platform in platforms
    }


async def async_setup_entry(hass: HomeAssistant, entry: PetLibroConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    email = entry.data.get(CONF_EMAIL)
    password = entry.data.get(CONF_PASSWORD)

    if not email or not password:
        _LOGGER.error("Email or password is missing in the configuration entry.")
        return False

    try:
        hub = PetLibroHub(hass, entry)
        entry.runtime_data = hub

        await hub.load_member()
        await hub.load_devices()
        await hub._initialize_helpers()
        await hub.coordinator.async_config_entry_first_refresh()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("Successfully set up PetLibro integration for %s", email)
        return True

    except Exception as err:
        _LOGGER.error("Failed to set up PetLibro integration: %s", err, exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: PetLibroConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.async_unload()
        _LOGGER.info("Successfully unloaded PetLibro entry for %s", entry.data.get(CONF_EMAIL))
    else:
        _LOGGER.error("Failed to unload PetLibro entry for %s", entry.data.get(CONF_EMAIL))

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: PetLibroConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    hub = entry.runtime_data

    return not any(
        identifier
        for identifier in device_entry.identifiers
        if identifier[0] == DOMAIN
        for device in hub.devices
        if device.serial == identifier[1]
    )