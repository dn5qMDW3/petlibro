import aiohttp

from ...exceptions import PetLibroAPIError
from ..device import Device
from typing import cast
from logging import getLogger

_LOGGER = getLogger(__name__)


class Fountain(Device):
    """Base class for all PETLIBRO fountain devices."""

    # ── availability ──────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self.online

    # ── realInfo properties ───────────────────────────────────────

    @property
    def device_sn(self) -> str:
        """Return the device serial number."""
        return self._data.get("realInfo", {}).get("deviceSn", "unknown")

    @property
    def wifi_ssid(self) -> str:
        """Return the Wi-Fi SSID of the device."""
        return self._data.get("realInfo", {}).get("wifiSsid", "unknown")

    @property
    def online(self) -> bool:
        """Return the online status of the fountain."""
        return bool(self._data.get("realInfo", {}).get("online", False))

    @property
    def wifi_rssi(self) -> int:
        """Get the Wi-Fi signal strength."""
        wifi_rssi = self._data.get("realInfo", {}).get("wifiRssi")
        return wifi_rssi if isinstance(wifi_rssi, int) else -100

    @property
    def weight(self) -> float:
        """Get the current weight of the water (in grams)."""
        weight = self._data.get("realInfo", {}).get("weight")
        return weight if isinstance(weight, (int, float)) else 0

    @property
    def weight_percent(self) -> int | float:
        """Get the current weight percentage of water."""
        weight_percent = self._data.get("realInfo", {}).get("weightPercent")
        return weight_percent if isinstance(weight_percent, (int, float)) else 0

    @property
    def remaining_filter_days(self) -> float | None:
        """Get the remaining filter days."""
        value = self._data.get("realInfo", {}).get("remainingReplacementDays", 0)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def remaining_cleaning_days(self) -> float | None:
        """Get the remaining cleaning days."""
        value = self._data.get("realInfo", {}).get("remainingCleaningDays", 0)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def light_switch(self) -> bool:
        """Check if the light is enabled."""
        return bool(self._data.get("realInfo", {}).get("lightSwitch", False))

    @property
    def sound_switch(self) -> bool:
        """Check if the sound is enabled."""
        return self._data.get("realInfo", {}).get("soundSwitch", False)

    # ── water settings (realInfo) ─────────────────────────────────

    @property
    def water_interval(self) -> float:
        water_interval = self._data.get("realInfo", {}).get("useWaterInterval")
        return water_interval if isinstance(water_interval, (int, float)) else 0

    @property
    def water_dispensing_duration(self) -> float:
        duration = self._data.get("realInfo", {}).get("useWaterDuration")
        return duration if isinstance(duration, (int, float)) else 0

    # ── cycle / frequency properties ──────────────────────────────

    @property
    def cleaning_cycle(self) -> float:
        cleaning_cycle = self._data.get("realInfo", {}).get("machineCleaningFrequency")
        return cleaning_cycle if isinstance(cleaning_cycle, (int, float)) else 0

    @property
    def filter_cycle(self) -> float:
        filter_cycle = self._data.get("realInfo", {}).get("filterReplacementFrequency")
        return filter_cycle if isinstance(filter_cycle, (int, float)) else 0

    @property
    def filter_replacement_frequency(self) -> int:
        """Get the filter replacement frequency."""
        frequency = self._data.get("realInfo", {}).get("filterReplacementFrequency")
        return frequency if isinstance(frequency, int) else 0

    @property
    def machine_cleaning_frequency(self) -> int:
        """Get the machine cleaning frequency."""
        frequency = self._data.get("realInfo", {}).get("machineCleaningFrequency")
        return frequency if isinstance(frequency, int) else 0

    # ── drinking stats (getDrinkWater) ────────────────────────────

    @property
    def today_drinking_amount(self) -> float:
        """Get the total milliliters of water used today."""
        amount = self._data.get("getDrinkWater", {}).get("todayTotalMl")
        return amount if isinstance(amount, (int, float)) else 0

    @property
    def today_drinking_count(self) -> int:
        """Get the total count of times drank today."""
        drinking_count = self._data.get("getDrinkWater", {}).get("todayTotalTimes")
        return drinking_count if isinstance(drinking_count, int) else 0

    @property
    def today_drinking_time(self) -> int:
        """Get the total time spent drinking today."""
        drinking_time = self._data.get("getDrinkWater", {}).get("petEatingTime")
        return drinking_time if isinstance(drinking_time, int) else 0

    @property
    def today_avg_time(self) -> int:
        """Get the average time spent drinking in a session today."""
        avg_time = self._data.get("getDrinkWater", {}).get("avgDrinkDuration")
        return avg_time if isinstance(avg_time, int) else 0

    @property
    def yesterday_drinking_amount(self) -> float:
        """Get the total milliliters of water used yesterday."""
        amount = self._data.get("getDrinkWater", {}).get("yesterdayTotalMl")
        return amount if isinstance(amount, (int, float)) else 0

    @property
    def yesterday_drinking_count(self) -> int:
        """Get the total count of times drank yesterday."""
        drinking_count = self._data.get("getDrinkWater", {}).get("yesterdayTotalTimes")
        return drinking_count if isinstance(drinking_count, int) else 0

    # ── setter methods ────────────────────────────────────────────

    async def set_light_switch(self, value: bool):
        """Enable or disable the light."""
        await self.api.set_light_switch(self.serial, value)
        await self.refresh()

    async def set_sound_switch(self, value: bool):
        """Enable or disable the sound."""
        await self.api.set_sound_switch(self.serial, value)
        await self.refresh()

    async def set_manual_cleaning(self):
        """Trigger manual cleaning action."""
        await self.api.set_manual_cleaning(self.serial)
        await self.refresh()

    async def set_water_interval(self, value: float) -> None:
        _LOGGER.debug(f"Setting water interval to {value} for {self.serial}")
        try:
            current_mode = self._data.get("realInfo", {}).get("useWaterType", 0)
            current_duration = self._data.get("realInfo", {}).get("useWaterDuration", 0)
            await self.api.set_water_interval(self.serial, value, current_mode, current_duration)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set water interval using {current_mode} & {current_duration} for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting water interval using {current_mode} & {current_duration}: {err}")

    async def set_water_dispensing_duration(self, value: float) -> None:
        _LOGGER.debug(f"Setting water dispensing duration to {value} for {self.serial}")
        try:
            current_mode = self._data.get("realInfo", {}).get("useWaterType", 0)
            current_interval = self._data.get("realInfo", {}).get("useWaterInterval", 0)
            await self.api.set_water_dispensing_duration(self.serial, value, current_mode, current_interval)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set water dispensing duration using {current_mode} & {current_interval} for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting water dispensing duration using {current_mode} & {current_interval}: {err}")

    async def set_cleaning_cycle(self, value: float) -> None:
        _LOGGER.debug(f"Setting cleaning cycle to {value} for {self.serial}")
        try:
            key = "MACHINE_CLEANING"
            await self.api.set_filter_cycle(self.serial, value, key)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set cleaning cycle using {key} for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting cleaning cycle using {key}: {err}")

    async def set_filter_cycle(self, value: float) -> None:
        _LOGGER.debug(f"Setting filter cycle to {value} for {self.serial}")
        try:
            key = "FILTER_ELEMENT"
            await self.api.set_filter_cycle(self.serial, value, key)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to set filter cycle using {key} for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error setting filter cycle using {key}: {err}")

    async def set_cleaning_reset(self) -> None:
        _LOGGER.debug(f"Triggering machine cleaning reset for {self.serial}")
        try:
            await self.api.set_cleaning_reset(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to trigger machine cleaning reset for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error triggering machine cleaning reset: {err}")

    async def set_filter_reset(self) -> None:
        _LOGGER.debug(f"Triggering filter reset for {self.serial}")
        try:
            await self.api.set_filter_reset(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to trigger filter reset for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error triggering filter reset: {err}")

    async def set_light_on(self) -> None:
        _LOGGER.debug(f"Turning on the indicator for {self.serial}")
        try:
            await self.api.set_light_on(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn on the indicator for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning on the indicator: {err}")

    async def set_light_off(self) -> None:
        _LOGGER.debug(f"Turning off the indicator for {self.serial}")
        try:
            await self.api.set_light_off(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Failed to turn off the indicator for {self.serial}: {err}")
            raise PetLibroAPIError(f"Error turning off the indicator: {err}")
