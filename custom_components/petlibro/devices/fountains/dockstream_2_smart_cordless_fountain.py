import aiohttp

from ...exceptions import PetLibroAPIError
from .fountain import Fountain
from typing import cast
from logging import getLogger

_LOGGER = getLogger(__name__)

class Dockstream2SmartCordlessFountain(Fountain):
    """Represents the Dockstream 2 Smart Cordless Fountain device."""

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            data_real_info = await self.api.device_data_real_info(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial, record_types=["DRINK"])
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
            _LOGGER.error(f"Error refreshing data for Dockstream2SmartCordlessFountain: {err}")

    # ── properties unique to Cordless fountain ────────────────────

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
                label = "Unknown"
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
    def radar_sensing_level(self) -> str:
        """Get the radar sensing level (e.g. 'NearTrigger')."""
        return self._data.get("dataRealInfo", {}).get("radarSensingLevel", "unknown")

    @property
    def filter_led_switch(self) -> bool:
        """Check if the filter LED indicator is on."""
        return bool(self._data.get("dataRealInfo", {}).get("filterLedSwitch", False))

    @property
    def radar_gain(self) -> int:
        """Get the radar gain value."""
        value = self._data.get("dataRealInfo", {}).get("radarGain")
        return value if isinstance(value, int) else 0

    @property
    def radar_sensing_threshold(self) -> int:
        """Get the radar sensing threshold."""
        value = self._data.get("dataRealInfo", {}).get("radarSensingThreshold")
        return value if isinstance(value, int) else 0

    @property
    def human_sensitivity_level(self) -> float:
        """Get the human detection sensitivity level."""
        value = self._data.get("dataRealInfo", {}).get("humanSensitivityLevel")
        return float(value) if value is not None else 0.0

    @property
    def battery_supply_8_hours(self) -> bool:
        """Return True if battery can supply 8 hours."""
        return bool(self._data.get("dataRealInfo", {}).get("batterySupply8Hours", False))

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
    def power_state(self) -> str:
        """Get the current power source.

        Known API values:
          1 = DC adapter (mains power)
          2 = Battery
          3 = USB
        """
        api_value = self._data.get("dataRealInfo", {}).get("powerType", 0)
        return {1: "DC", 2: "Battery", 3: "USB"}.get(api_value, "Unknown")

    @property
    def electric_quantity(self) -> int:
        return self._data.get("realInfo", {}).get("electricQuantity", 0)
