from logging import getLogger
from typing import cast

from ..api import PetLibroAPI
from .event import Event, EVENT_UPDATE
from ..member import Member
from ..const import DEFAULT_MAX_FEED_PORTIONS


_LOGGER = getLogger(__name__)


class Device(Event):
    def __init__(self, data: dict, member: Member, api: PetLibroAPI):
        super().__init__()
        self._data: dict = {}
        self.api = api
        self.member = member
        
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
            _LOGGER.error(f"Error updating data: {e}")
            # Optionally log specific fields instead of the entire data
            _LOGGER.debug(f"Partial data: {data.get('deviceSn', 'Unknown Serial')}")
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            data = {}
            data.update(await self.api.device_base_info(self.serial))
            data["realInfo"] = await self.api.device_real_info(self.serial) or {}
            data["getAttributeSetting"] = await self.api.device_attribute_settings(self.serial) or {}
            self.update_data(data)
        except Exception as e:
            _LOGGER.error("Failed to refresh device data: %s", e)

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
    def update_available(self) -> bool:
        """Return True if an update is available, False otherwise."""
        return bool(self._data.get("getUpgrade", {}).get("jobItemId"))

    @property
    def update_release_notes(self) -> str | None:
        """Return release notes if available, else None."""
        upgrade_data = self._data.get("getUpgrade")
        return upgrade_data.get("upgradeDesc") if upgrade_data else None

    @property
    def update_version(self) -> str | None:
        """Return target version if available, else None."""
        upgrade_data = self._data.get("getUpgrade")
        return upgrade_data.get("targetVersion") if upgrade_data else None

    @property
    def update_name(self) -> str | None:
        """Return update job name if available, else None."""
        upgrade_data = self._data.get("getUpgrade")
        return upgrade_data.get("jobName") if upgrade_data else None

    @property
    def update_progress(self) -> float:
        """Return update progress as a float, or 0 if not updating."""
        upgrade_data = self._data.get("getUpgrade")
        if not upgrade_data:
            return 0.0
        progress = upgrade_data.get("progress")
        return float(progress) if progress is not None else 0.0
