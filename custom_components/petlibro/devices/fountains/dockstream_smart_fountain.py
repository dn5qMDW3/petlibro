import aiohttp

from ...exceptions import PetLibroAPIError
from .fountain import Fountain
from typing import cast
from logging import getLogger

_LOGGER = getLogger(__name__)

class DockstreamSmartFountain(Fountain):
    """Represents the Dockstream Smart Fountain device."""

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            data_real_info = await self.api.device_data_real_info(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_drink_water = await self.api.get_device_drink_water(self.serial)

            self.update_data({
                "dataRealInfo": data_real_info or {},
                "getDrinkWater": get_drink_water or {},
                "getUpgrade": get_upgrade or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "workRecord": get_work_record if get_work_record is not None else []
            })
        except PetLibroAPIError as err:
            _LOGGER.error(f"Error refreshing data for DockstreamSmartFountain: {err}")

    # ── properties unique to Dockstream 1 ─────────────────────────

    @property
    def battery_display_type(self) -> float:
        """Get the battery percentage state."""
        try:
            value = str(self._data.get("realInfo", {}).get("batteryDisplayType", "percentage"))
            return cast(float, float(value))
        except (TypeError, ValueError):
            return 0.0

    @property
    def vacuum_state(self) -> bool:
        """Check if the vacuum state is active."""
        return self._data.get("realInfo", {}).get("vacuumState", False)

    @property
    def pump_air_state(self) -> bool:
        """Check if the air pump is active."""
        return self._data.get("realInfo", {}).get("pumpAirState", False)

    @property
    def barn_door_error(self) -> bool:
        """Check if there's a barn door error."""
        return self._data.get("realInfo", {}).get("barnDoorError", False)

    @property
    def running_state(self) -> str:
        """Get the current running state of the device."""
        return self._data.get("realInfo", {}).get("runningState", "unknown")

    @property
    def water_dispensing_mode(self) -> str:
        """Return the user-friendly water dispensing mode."""
        api_value = self._data.get("realInfo", {}).get("useWaterType", 0)

        if api_value == 0:
            return "Flowing Water (Constant)"
        elif api_value == 1:
            return "Intermittent Water (Scheduled)"
        else:
            return "Unknown"

    @property
    def electric_quantity(self) -> int:
        return self._data.get("realInfo", {}).get("electricQuantity", 0)

    @property
    def enable_sound(self) -> bool:
        return self._data.get("realInfo", {}).get("enableSound", False)

    @property
    def enable_light(self) -> bool:
        return self._data.get("realInfo", {}).get("enableLight", False)

    @property
    def desiccant_frequency(self) -> int:
        return self._data.get("realInfo", {}).get("desiccantFrequency", 0)

    @property
    def use_water_interval(self) -> int:
        """Get the water usage interval."""
        water_interval = self._data.get("realInfo", {}).get("useWaterInterval")
        return water_interval if isinstance(water_interval, int) else 0

    @property
    def use_water_duration(self) -> int:
        """Get the water usage duration."""
        water_duration = self._data.get("realInfo", {}).get("useWaterDuration", 0)
        return water_duration if isinstance(water_duration, int) else 0
