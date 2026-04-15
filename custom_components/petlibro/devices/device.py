# Error Mode - Used for pulling API for new devices. Enable Error Mode and Disable Debug Mode.

from logging import getLogger
import sys
from typing import cast

from .event import Event, EVENT_UPDATE
from ..const import DOMAIN, DEFAULT_MAX_FEED_PORTIONS


_LOGGER = getLogger(__name__)


class Device(Event):
    def __init__(self, data: dict, hub):
        super().__init__()
        if "PetLibroHub" not in sys.modules:
            from ..hub import PetLibroHub
        self._data: dict = {}
        self.hub: PetLibroHub = hub
        self.api = self.hub.api
        self.member = self.hub.member
        self.saved_to_options = False
        
        self.feed_conv_factor = 1
        self.max_feed_portions = DEFAULT_MAX_FEED_PORTIONS

        self.update_data(data)

    def update_data(self, data: dict) -> None:
        """Save the device info from a data dictionary."""
        try:
            # Log at debug level instead of error level
            _LOGGER.debug("Updating data with new information.")
            self._data.update(data)
            self.emit(EVENT_UPDATE)
            _LOGGER.debug("Data updated successfully.")
        except Exception as e:
            _LOGGER.error("Error updating data: %s", e)
            # Optionally log specific fields instead of the entire data
            _LOGGER.debug("Partial data: %s", data.get('deviceSn', 'Unknown Serial'))
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            data = {}
            data.update(await self.api.device_base_info(self.serial))
            data.update(await self.api.device_real_info(self.serial))
            data.update(await self.api.device_attribute_settings(self.serial))
            data.update({"boundPets": await self.api.device_get_bound_pets(self.serial)})
            self.update_data(data)
        except Exception as e:
            _LOGGER.error("Failed to refresh device data: %s", e)


    @property
    def device_id(self) -> str:
        """Home Assistant Device ID."""
        return self._data.get("device_id") or ""

    @property
    def device_identifiers(self) -> set:
        return {(DOMAIN, self.serial)}

    @property
    def owned(self) -> bool:
        """Whether this account owns the device."""
        return {
            1: False,   # Shared with me
            2: True,    # Owned, sharing with others
            3: True,    # Owned, not shared
        }.get(self._data.get("deviceShareState", 3))

    @property
    def serial(self) -> str:
        return cast(str, self._data.get("deviceSn"))

    @property
    def model(self) -> str:
        return cast(str, self._data.get("productIdentifier"))

    @property
    def model_name(self) -> str:
        return cast(str, self._data.get("productName"))

    @property
    def name(self) -> str:
        return cast(str, self._data.get("name"))

    @property
    def mac(self) -> str:
        return cast(str, self._data.get("mac"))

    @property
    def software_version(self) -> str:
        return cast(str, self._data.get("softwareVersion"))

    @property
    def hardware_version(self) -> str:
        return cast(str, self._data.get("hardwareVersion"))

    @property
    def icon_url(self) -> str | None:
        """Product icon URL from the device list API response."""
        return self._data.get("icon")

    @property
    def boundPets(self) -> list[dict]:
        return self._data.get("boundPets") or []

    def set_device_id(self) -> None:
        """Update Device object data with it's Home Assistant device ID."""
        device = self.hub.device_register.async_get_device(
            identifiers=self.device_identifiers
        )
        if device and getattr(device, "id", False):
            self.update_data({"device_id": device.id})

    def save_to_options(self) -> None:
        """Save data to the Config Entry about the device."""
        if self.device_id:
            self.hub.update_options(
                {
                    "devices": self.hub.devices_helper.cached_devices
                    | {
                        self.serial: {
                            "device_id": self.device_id,
                            "owned": self.owned,
                        },
                    }
                }
            )
            self.saved_to_options = True
