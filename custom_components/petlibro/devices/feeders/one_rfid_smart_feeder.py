"""PETLIBRO One RFID Smart Feeder"""
from logging import getLogger

from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class OneRFIDSmartFeeder(Feeder):
    """PETLIBRO One RFID Smart Feeder device."""

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_default_matrix = await self.api.get_default_matrix(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("realInfo", {}).get("enableFeedingPlan") else [])

            self.update_data({
                "grainStatus": grain_status or {},
                "getUpgrade": get_upgrade or {},
                "getDefaultMatrix": get_default_matrix or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record if get_work_record is not None else [],
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for OneRFIDSmartFeeder: %s", err)

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

    @property
    def lid_speed(self) -> str:
        api_value = self._data.get("getAttributeSetting", {}).get("coverCloseSpeed", "FAST")
        return {"FAST": "Fast", "MEDIUM": "Medium", "SLOW": "Slow"}.get(api_value, "Unknown")

    @property
    def lid_mode(self) -> str:
        api_value = self._data.get("getAttributeSetting", {}).get("coverOpenMode", "CUSTOM")
        return {
            "KEEP_OPEN": "Open Mode (Stays Open Until Closed)",
            "CUSTOM": "Personal Mode (Opens on Detection)",
        }.get(api_value, "Unknown")

    @property
    def lid_close_time(self) -> float:
        return self._data.get("getAttributeSetting", {}).get("closeDoorTimeSec", 0)

    @property
    def display_text(self) -> str:
        return self._data.get("getDefaultMatrix", {}).get("screenLetter", "ERROR")

    @property
    def display_icon(self) -> str:
        api_value = self._data.get("getDefaultMatrix", {}).get("screenDisplayId")
        return {5: "Heart", 6: "Dog", 7: "Cat", 8: "Elk"}.get(api_value, "Unknown")

    @property
    def display_selection(self) -> str:
        display_text = self._data.get("getDefaultMatrix", {}).get("screenLetter")
        display_icon = self._data.get("getDefaultMatrix", {}).get("screenDisplayId")

        if isinstance(display_text, str):
            return f"Displaying Text: {display_text}"
        if isinstance(display_icon, int):
            icon_map = {5: "Heart", 6: "Dog", 7: "Cat", 8: "Elk"}
            return f"Displaying Icon: {icon_map.get(display_icon, 'Unknown')}"
        return "No valid display data found"

    # ------------------------------------------------------------------
    # RFID-specific setters
    # ------------------------------------------------------------------

    async def set_desiccant_cycle(self, value: float) -> None:
        await self.api.set_maintenance_frequency(self.serial, "DESSICANT", value)
        await self.refresh()

    async def set_sound_level(self, value: float) -> None:
        await self.api.set_sound_level(self.serial, value)
        await self.refresh()

    async def set_manual_lid_open(self) -> None:
        await self.api.set_manual_lid_open(self.serial)
        await self.refresh()

    async def set_display_on(self) -> None:
        await self.api.set_display_on(self.serial)
        await self.refresh()

    async def set_display_off(self) -> None:
        await self.api.set_display_off(self.serial)
        await self.refresh()

    async def set_sound_on(self) -> None:
        await self.api.set_sound_on(self.serial)
        await self.refresh()

    async def set_sound_off(self) -> None:
        await self.api.set_sound_off(self.serial)
        await self.refresh()

    async def set_lid_speed(self, value: str) -> None:
        await self.api.set_lid_speed(self.serial, value)
        await self.refresh()

    async def set_lid_mode(self, value: str) -> None:
        await self.api.set_lid_mode(self.serial, value)
        await self.refresh()

    async def set_lid_close_time(self, value: float) -> None:
        await self.api.set_lid_close_time(self.serial, value)
        await self.refresh()

    async def set_display_text(self, value: str) -> None:
        await self.api.set_display_text(self.serial, value)
        await self.refresh()

    async def set_display_icon(self, value: float) -> None:
        await self.api.set_display_icon(self.serial, value)
        await self.refresh()
