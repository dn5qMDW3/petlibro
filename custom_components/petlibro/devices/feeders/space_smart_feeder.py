import aiohttp

from logging import getLogger
from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class SpaceSmartFeeder(Feeder):
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            # Fetch specific data for this device
            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_device_events = await self.api.device_events(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            # Update internal data with fetched API data
            self.update_data({
                "grainStatus": grain_status or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "getDeviceEvents": get_device_events or {},
                "getUpgrade": get_upgrade or {},
                "workRecord": get_work_record if get_work_record is not None else []
            })
        except PetLibroAPIError as err:
            _LOGGER.error(f"Error refreshing data for SpaceSmartFeeder: {err}")

    # ------------------------------------------------------------------
    # Space-specific overrides: event-based states
    # ------------------------------------------------------------------

    @property
    def vacuum_state(self) -> bool:
        events = self._data.get("getDeviceEvents", {}).get("data", {}).get("eventInfos", [])
        return any(event.get("eventKey") == "VACUUM_FAILED" for event in events)

    @property
    def food_dispenser_state(self) -> bool:
        events = self._data.get("getDeviceEvents", {}).get("data", {}).get("eventInfos", [])
        return any(event.get("eventKey") == "GRAIN_OUTLET_BLOCKED_OVERTIME" for event in events)

    @property
    def food_outlet_state(self) -> bool:
        events = self._data.get("getDeviceEvents", {}).get("data", {}).get("eventInfos", [])
        return any(event.get("eventKey") == "FOOD_OUTLET_DOOR_FAILED_CLOSE" for event in events)

    # ------------------------------------------------------------------
    # Space-specific properties
    # ------------------------------------------------------------------

    @property
    def sound_switch(self) -> bool:
        return self._data.get("realInfo", {}).get("soundSwitch", False)

    @property
    def vacuum_mode(self) -> str:
        api_value = self._data.get("realInfo", {}).get("vacuumMode", "NORMAL")

        if api_value == "LEARNING":
            return "Study"
        elif api_value == "NORMAL":
            return "Normal"
        elif api_value == "MANUAL":
            return "Manual"
        else:
            return "Unknown"

    async def set_vacuum_mode(self, value: str) -> None:
        _LOGGER.debug(f"Setting vacuum mode to {value} for {self.serial}")
        try:
            await self.api.set_vacuum_mode(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set vacuum mode for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting vacuum mode: {err}")

    async def set_sound_on(self) -> None:
        _LOGGER.debug(f"Turning on the sound for {self.serial}")
        try:
            await self.api.set_sound_on(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn on the sound for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning on the sound: {err}")

    async def set_sound_off(self) -> None:
        _LOGGER.debug(f"Turning off the sound for {self.serial}")
        try:
            await self.api.set_sound_off(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn off the sound for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning off the sound: {err}")

    @property
    def sound_level(self) -> float:
        return self._data.get("getAttributeSetting", {}).get("volume", 0)

    async def set_sound_level(self, value: float) -> None:
        _LOGGER.debug(f"Setting sound level to {value} for {self.serial}")
        try:
            await self.api.set_sound_level(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set sound level for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting sound level: {err}")

    async def set_sleep_on(self) -> None:
        _LOGGER.debug(f"Turning on sleep mode for {self.serial}")
        try:
            await self.api.set_sleep_on(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn on sleep mode for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning on sleep mode: {err}")

    async def set_sleep_off(self) -> None:
        _LOGGER.debug(f"Turning off sleep mode for {self.serial}")
        try:
            await self.api.set_sleep_off(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn off sleep mode for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning off sleep mode: {err}")
