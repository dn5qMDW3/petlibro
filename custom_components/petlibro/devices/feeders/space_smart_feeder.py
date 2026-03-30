"""PETLIBRO Space Smart Feeder"""
from logging import getLogger

from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class SpaceSmartFeeder(Feeder):
    """PETLIBRO Space Smart Feeder device."""

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_device_events = await self.api.device_events(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            self.update_data({
                "grainStatus": grain_status or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "getDeviceEvents": get_device_events or {},
                "getUpgrade": get_upgrade or {},
                "workRecord": get_work_record if get_work_record is not None else [],
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for SpaceSmartFeeder: %s", err)

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
        return {"LEARNING": "Study", "NORMAL": "Normal", "MANUAL": "Manual"}.get(api_value, "Unknown")

    @property
    def sound_level(self) -> float:
        return self._data.get("getAttributeSetting", {}).get("volume", 0)

    # ------------------------------------------------------------------
    # Space-specific setters
    # ------------------------------------------------------------------

    async def set_vacuum_mode(self, value: str) -> None:
        await self.api.set_vacuum_mode(self.serial, value)
        await self.refresh()

    async def set_sound_on(self) -> None:
        await self.api.set_sound_on(self.serial)
        await self.refresh()

    async def set_sound_off(self) -> None:
        await self.api.set_sound_off(self.serial)
        await self.refresh()

    async def set_sound_level(self, value: float) -> None:
        await self.api.set_sound_level(self.serial, value)
        await self.refresh()

    async def set_sleep_on(self) -> None:
        await self.api.set_sleep_on(self.serial)
        await self.refresh()

    async def set_sleep_off(self) -> None:
        await self.api.set_sleep_off(self.serial)
        await self.refresh()
