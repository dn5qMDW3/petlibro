import aiohttp

from logging import getLogger
from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class OneRFIDSmartFeeder(Feeder):
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            # Fetch specific data for this device
            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_default_matrix = await self.api.get_default_matrix(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            # Update internal data with fetched API data
            self.update_data({
                "grainStatus": grain_status or {},
                "getUpgrade": get_upgrade or {},
                "getDefaultMatrix": get_default_matrix or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record if get_work_record is not None else []
            })
        except PetLibroAPIError as err:
            _LOGGER.error(f"Error refreshing data for OneRFIDSmartFeeder: {err}")

    # ------------------------------------------------------------------
    # RFID-specific properties
    # ------------------------------------------------------------------

    @property
    def today_eating_times(self) -> int:
        return self._data.get("grainStatus", {}).get("todayEatingTimes", 0)

    @property
    def today_eating_time(self) -> int:
        return self._data.get("grainStatus", {}).get("petEatingTime", 0)

    @property
    def door_state(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("barnDoorState", False))

    @property
    def door_blocked(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("barnDoorError", False))

    @property
    def display_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("screenDisplaySwitch", False))

    @property
    def desiccant_cycle(self) -> float:
        return self._data.get("realInfo", {}).get("changeDesiccantFrequency", 0)

    @property
    def sound_switch(self) -> bool:
        return self._data.get("realInfo", {}).get("soundSwitch", False)

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

    # Override: passes extra key parameter
    async def set_desiccant_cycle(self, value: float) -> None:
        _LOGGER.debug(f"Setting desiccant cycle to {value} for {self.serial}")
        try:
            key = "DESSICANT"
            await self.api.set_desiccant_cycle(self.serial, value, key)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set desiccant cycle for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting desiccant cycle: {err}")

    async def set_manual_lid_open(self) -> None:
        _LOGGER.debug(f"Triggering manual lid opening for {self.serial}")
        try:
            await self.api.set_manual_lid_open(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to trigger manual lid opening for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error triggering manual lid opening: {err}")

    async def set_display_on(self) -> None:
        _LOGGER.debug(f"Turning on the display matrix for {self.serial}")
        try:
            await self.api.set_display_on(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn on the display for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning on the display: {err}")

    async def set_display_off(self) -> None:
        _LOGGER.debug(f"Turning off the display for {self.serial}")
        try:
            await self.api.set_display_off(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn off the display for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning off the display: {err}")

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
    def lid_speed(self) -> str:
        """Return the user-friendly lid speed (mapped directly from the API value)."""
        api_value = self._data.get("getAttributeSetting", {}).get("coverCloseSpeed", "FAST")

        if api_value == "FAST":
            return "Fast"
        elif api_value == "MEDIUM":
            return "Medium"
        elif api_value == "SLOW":
            return "Slow"
        else:
            return "Unknown"

    async def set_lid_speed(self, value: str) -> None:
        _LOGGER.debug(f"Setting lid speed to {value} for {self.serial}")
        try:
            await self.api.set_lid_speed(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set lid speed for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting lid speed: {err}")

    @property
    def lid_mode(self) -> str:
        """Return the user-friendly lid mode (mapped directly from the API value)."""
        api_value = self._data.get("getAttributeSetting", {}).get("coverOpenMode", "CUSTOM")

        if api_value == "KEEP_OPEN":
            return "Open Mode (Stays Open Until Closed)"
        elif api_value == "CUSTOM":
            return "Personal Mode (Opens on Detection)"
        else:
            return "Unknown"

    async def set_lid_mode(self, value: str) -> None:
        _LOGGER.debug(f"Setting lid mode to {value} for {self.serial}")
        try:
            await self.api.set_lid_mode(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set lid mode for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting lid mode: {err}")

    @property
    def lid_close_time(self) -> float:
        return self._data.get("getAttributeSetting", {}).get("closeDoorTimeSec", 0)

    async def set_lid_close_time(self, value: float) -> None:
        _LOGGER.debug(f"Setting lid close time to {value} for {self.serial}")
        try:
            await self.api.set_lid_close_time(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set lid close time for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting lid close time: {err}")

    @property
    def display_text(self) -> str:
        """Return the current display text from local data."""
        return self._data.get("getDefaultMatrix", {}).get("screenLetter", "ERROR")

    async def set_display_text(self, value: str) -> None:
        _LOGGER.debug(f"Setting display text to {value} for {self.serial}")
        try:
            await self.api.set_display_text(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set display text for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting display text: {err}")

    @property
    def display_icon(self) -> float:
        """Return the user-friendly display icon (mapped directly from the API value)."""
        api_value = self._data.get("getDefaultMatrix", {}).get("screenDisplayId", None)

        if api_value == 5:
            return "Heart"
        elif api_value == 6:
            return "Dog"
        elif api_value == 7:
            return "Cat"
        elif api_value == 8:
            return "Elk"
        else:
            return "Unknown"

    async def set_display_icon(self, value: float) -> None:
        _LOGGER.debug(f"Setting display icon to {value} for {self.serial}")
        try:
            await self.api.set_display_icon(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set display icon for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting display icon: {err}")

    @property
    def display_selection(self) -> str:
        display_text = self._data.get("getDefaultMatrix", {}).get("screenLetter", None)
        display_icon = self._data.get("getDefaultMatrix", {}).get("screenDisplayId", None)

        if isinstance(display_text, str):
            return f"Displaying Text: {display_text}"

        if isinstance(display_icon, int):
            icon_map = {
                5: "Heart",
                6: "Dog",
                7: "Cat",
                8: "Elk",
            }
            return f"Displaying Icon: {icon_map.get(display_icon, 'Unknown')}"

        return "No valid display data found"
