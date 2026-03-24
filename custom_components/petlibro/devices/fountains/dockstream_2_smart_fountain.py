import aiohttp

from ...exceptions import PetLibroAPIError
from .fountain import Fountain
from logging import getLogger

_LOGGER = getLogger(__name__)

class Dockstream2SmartFountain(Fountain):
    """Represents the Dockstream 2 Smart Fountain device."""

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
            _LOGGER.error(f"Error refreshing data for Dockstream2SmartFountain: {err}")

    # ── properties unique to Dockstream 2 ─────────────────────────

    @property
    def water_state(self) -> bool:
        """Check if water stop switch is on."""
        return not self._data.get("dataRealInfo", {}).get("waterStopSwitch", False)

    @property
    def water_dispensing_mode(self) -> str:
        """Get current water dispensing mode."""
        real = self._data.get("dataRealInfo", {}) or {}

        stop_raw = real.get("waterStopSwitch")
        mode_raw = real.get("useWaterType")

        stop = bool(stop_raw)
        try:
            mode = int(mode_raw) if mode_raw is not None else None
        except (TypeError, ValueError):
            mode = None

        if stop:
            label = "Off"
        elif mode == 0:
            label = "Flowing Water (Constant)"
        elif mode == 1:
            label = "Intermittent Water (Scheduled)"
        else:
            label = "Unknown"

        return label

    # Not currently supported by the device, API accepts, but device doesnt apply. hoping for future firmware update.
    # @property
    # def water_sensing_delay(self) -> float:
    #     return self._data.get("dataRealInfo", {}).get("sensingWaterDuration", 0)

    # async def set_water_sensing_delay(self, value: float) -> None:
    #     _LOGGER.debug(f"Setting water sensing delay to {value} for {self.serial}")
    #     try:
    #         current_mode = self._data.get("dataRealInfo", {}).get("useWaterType", 0)
    #         await self.api.set_water_sensing_delay(self.serial, value, current_mode)
    #         await self.refresh()  # Refresh the state after the action
    #     except aiohttp.ClientError as err:
    #         _LOGGER.error(f"Failed to set water sensing delay using {current_mode} for {self.serial}: {err}")
    #         raise PetLibroAPIError(f"Error setting water sensing delay using {current_mode}: {err}")

    @property
    def water_low_threshold(self) -> float:
        threshold = self._data.get("dataRealInfo", {}).get("lowWater")
        return threshold if isinstance(threshold, (int, float)) else 0

    async def set_water_low_threshold(self, value: float) -> None:
        _LOGGER.debug(f"Setting water low threshold to {value} for {self.serial}")
        try:
            await self.api.set_water_low_threshold(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set water low threshold to {value} for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting water low threshold: {err}")

    @property
    def power_state(self) -> int:
        api_value = self._data.get("dataRealInfo", {}).get("powerType", 0)

        if api_value == 2:
            return False
        elif api_value == 3:
            return True
        else:
            return "Unknown"
