import aiohttp

from typing import cast
from ...exceptions import PetLibroAPIError
from .fountain import Fountain
from logging import getLogger

_LOGGER = getLogger(__name__)

class Dockstream2SmartCordlessFountain(Fountain):
    """Represents the Dockstream 2 Smart Cordless Fountain device."""

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            real_info = await self.api.device_real_info(self.serial)
            data_real_info = await self.api.device_data_real_info(self.serial)
            attribute_settings = await self.api.device_attribute_settings(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial, record_types=["DRINK"])
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_drink_water = await self.api.get_device_drink_water(self.serial)

            self.update_data({
                "realInfo": real_info or {},
                "dataRealInfo": data_real_info or {},
                "getDrinkWater": get_drink_water or {},
                "getAttributeSetting": attribute_settings or {},
                "getUpgrade": get_upgrade or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "workRecord": get_work_record if get_work_record is not None else []
            })

        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for Dockstream2SmartCordlessFountain: %s", err)

    # -------------------------------------------------------------------------
    # Device-specific properties
    # -------------------------------------------------------------------------

    @property
    def detection_sensitivity(self) -> str:
        """Get the detection sensitivity."""
        return self._data.get("dataRealInfo", {}).get("radarSensingLevel", "unknown")

    @property
    def water_state(self) -> bool:
        """Check if water switch is on."""
        return not self._data.get("dataRealInfo", {}).get("waterStopSwitch", False)

    @property
    def water_dispensing_mode(self) -> str:
        """Get current water dispensing mode."""
        real = self._data.get("dataRealInfo", {}) or {}

        stop_raw = real.get("waterStopSwitch")
        mode_raw = real.get("useWaterType")
        radar = real.get("radarSensingLevel")

        stop = bool(stop_raw)
        try:
            mode = int(mode_raw) if mode_raw is not None else None
        except (TypeError, ValueError):
            mode = None

        if stop:
            label = "Off"
        elif mode == 0:
            label = "Flowing Water (Constant)"
        elif mode == 2:
            if radar == "NearTrigger":
                label = "Sensor-Activated (Near)"
            elif radar == "FarTrigger":
                label = "Sensor-Activated (Far)"
            else:
                label = "Unknown"  # waiting for radar to land
        else:
            label = "Unknown"

        return label

    @property
    def water_low_threshold(self) -> float:
        threshold = self._data.get("dataRealInfo", {}).get("lowWater")
        return threshold if isinstance(threshold, (int, float)) else 0

    async def set_water_low_threshold(self, value: float) -> None:
        _LOGGER.debug("Setting water low threshold to %s for %s", value, self.serial)
        try:
            await self.api.set_water_low_threshold(self.serial, value)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to set water low threshold to %s for %s: %s", value, self.serial, err)
            raise PetLibroAPIError(f"Error setting water low threshold: {err}")

    @property
    def battery_state(self) -> str:
        return cast(str, self._data.get("realInfo", {}).get("batteryState", "unknown"))

    @property
    def battery_charge_state(self) -> str:
        real = self._data.get("dataRealInfo") or self._data.get("realInfo") or {}
        api_value = (real.get("powerState") or "").upper()
        if api_value == "CHARGED":
            return "Fully Charged"
        if api_value == "CHARGING":
            return "Charging"
        if api_value == "USING":
            return "Discharging"
        return "Unknown"

    @property
    def power_state(self) -> bool | None:
        """Whether the device is on AC power. None if power source is unknown."""
        api_value = self._data.get("dataRealInfo", {}).get("powerType", 0)
        if api_value == 2:
            return False  # Battery
        if api_value == 3:
            return True   # AC adapter
        return None  # Unknown

    @property
    def electric_quantity(self) -> int:
        return self._data.get("realInfo", {}).get("electricQuantity", 0)

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
