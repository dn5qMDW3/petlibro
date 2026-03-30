"""Support for PETLIBRO updates."""
from __future__ import annotations
from dataclasses import dataclass
from logging import getLogger
from homeassistant.components.update import UpdateDeviceClass, UpdateEntity, UpdateEntityDescription, UpdateEntityFeature

from .entity import PetLibroEntity, _DeviceT, PetLibroEntityDescription, create_platform_setup
from .devices import Device
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

_LOGGER = getLogger(__name__)


@dataclass(frozen=True)
class PetLibroUpdateEntityDescription(UpdateEntityDescription, PetLibroEntityDescription[_DeviceT]):
    """Describes PetLibro update entity."""


class PetLibroUpdateEntity(PetLibroEntity[_DeviceT], UpdateEntity):
    """PETLIBRO update entity."""

    def __init__(self, device, hub, description):
        super().__init__(device, hub, description)

        mac_address = getattr(device, "mac", None)
        if mac_address:
            self._attr_unique_id = f"{device.serial}-{description.key}-{mac_address.replace(':', '')}"
        else:
            self._attr_unique_id = f"{device.serial}-{description.key}"

        self._attr_device_class = UpdateDeviceClass.FIRMWARE
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
        )
        self._attr_title = f"{device.name} Firmware"
        self._attr_installed_version = "0.0.0"
        self._attr_latest_version = "0.0.0"
        self._attr_release_summary = "No firmware information available"
        self._attr_release_url = "https://petlibro.com/pages/help-center"
        self._attr_display_precision = 0
        self._attr_in_progress = False
        self._attr_update_percentage = None
        self._attr_available = True

    @property
    def installed_version(self) -> str:
        return getattr(self.device, "software_version", None) or self._attr_installed_version

    @property
    def latest_version(self) -> str:
        return self.device.update_version or self.installed_version

    @property
    def release_summary(self) -> str:
        if self.installed_version == self.latest_version:
            return ""
        return self.device.update_release_notes or "Firmware update available."

    @property
    def release_url(self) -> str:
        return self._attr_release_url

    @property
    def title(self) -> str:
        return self._attr_title

    @property
    def display_precision(self) -> int:
        return self._attr_display_precision

    @property
    def in_progress(self) -> bool:
        progress = self.device.update_progress
        return progress is not None and 0.0 < progress < 100.0

    @property
    def update_percentage(self) -> float | None:
        progress = self.device.update_progress
        return float(progress) if progress is not None and 0.0 < progress <= 100.0 else None

    @property
    def available(self) -> bool:
        return True

    async def async_release_notes(self) -> str | None:
        return self.device.update_release_notes or "No detailed release notes provided."

    async def async_install(self, version: str | None, backup: bool, **kwargs):
        upgrade_data = self.device._data.get("getUpgrade", {})
        job_item_id = upgrade_data.get("jobItemId")

        if not job_item_id:
            _LOGGER.warning("No firmware update available for %s", self.device.name)
            return

        _LOGGER.debug("Triggering firmware update for %s (jobItemId=%s)", self.device.name, job_item_id)
        await self.device.api.trigger_firmware_upgrade(self.device.serial, job_item_id)


DEVICE_UPDATE_MAP: dict[type[Device], list[PetLibroUpdateEntityDescription]] = {
    AirSmartFeeder: [
        PetLibroUpdateEntityDescription[AirSmartFeeder](key="firmware"),
    ],
    GranarySmartFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartFeeder](key="firmware"),
    ],
    GranarySmartCameraFeeder: [
        PetLibroUpdateEntityDescription[GranarySmartCameraFeeder](key="firmware"),
    ],
    OneRFIDSmartFeeder: [
        PetLibroUpdateEntityDescription[OneRFIDSmartFeeder](key="firmware"),
    ],
    PolarWetFoodFeeder: [
        PetLibroUpdateEntityDescription[PolarWetFoodFeeder](key="firmware"),
    ],
    SpaceSmartFeeder: [
        PetLibroUpdateEntityDescription[SpaceSmartFeeder](key="firmware"),
    ],
    DockstreamSmartFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartFountain](key="firmware"),
    ],
    DockstreamSmartRFIDFountain: [
        PetLibroUpdateEntityDescription[DockstreamSmartRFIDFountain](key="firmware"),
    ],
    Dockstream2SmartCordlessFountain: [
        PetLibroUpdateEntityDescription[Dockstream2SmartCordlessFountain](key="firmware"),
    ],
    Dockstream2SmartFountain: [
        PetLibroUpdateEntityDescription[Dockstream2SmartFountain](key="firmware"),
    ],
    LumaSmartLitterBox: [
        PetLibroUpdateEntityDescription[LumaSmartLitterBox](key="firmware"),
    ],
}

async_setup_entry = create_platform_setup(
    PetLibroUpdateEntity, DEVICE_UPDATE_MAP, "update"
)
