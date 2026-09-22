import asyncio
import aiohttp
from ...exceptions import PetLibroAPIError
from .fountain import Fountain
from logging import getLogger

_LOGGER = getLogger(__name__)

class DockstreamSmartFountain(Fountain):
    """Represents the Dockstream Smart Fountain device."""

    async def _safe_fetch(self, coro):
        """Await one endpoint, returning None on failure.

        Catches both API errors and network-level errors so one failing
        endpoint never takes down the whole refresh or loses other data.
        """
        try:
            return await coro
        except (PetLibroAPIError, aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error fetching data for DockstreamSmartFountain %s: %s", self.serial, err)
            return None

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            keys = (
                "realInfo", "dataRealInfo", "getAttributeSetting", "getUpgrade",
                "workRecord", "getfeedingplantoday", "getDrinkWater",
            )
            results = await asyncio.gather(
                self._safe_fetch(self.api.device_real_info(self.serial)),
                self._safe_fetch(self.api.device_data_real_info(self.serial)),
                self._safe_fetch(self.api.device_attribute_settings(self.serial)),
                self._safe_fetch(self.api.get_device_upgrade(self.serial)),
                self._safe_fetch(self.api.get_device_work_record(self.serial, record_types=["DRINK"])),
                self._safe_fetch(self.api.device_feeding_plan_today_new(self.serial)),
                self._safe_fetch(self.api.get_device_drink_water(self.serial)),
            )

            # Only update keys that were fetched successfully so a transient
            # failure doesn't overwrite previously-good data with empty values.
            self.update_data({
                key: value for key, value in zip(keys, results) if value is not None
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for DockstreamSmartFountain: %s", err)

    # -------------------------------------------------------------------------
    # Device-specific properties
    # -------------------------------------------------------------------------

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
        """Return the user-friendly water dispensing mode (mapped directly from the API value)."""
        api_value = self._data.get("realInfo", {}).get("useWaterType", 0)

        if api_value == 0:
            return "Flowing Water (Constant)"
        elif api_value == 1:
            return "Intermittent Water (Scheduled)"
        else:
            return "Unknown"

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

    @property
    def weight_calibration_error(self) -> bool | None:
        exception = self._data.get("dataRealInfo", {}).get("exceptionMessage")
        if exception is None:
            return None
        return "calibration" in exception.lower() or "weight" in exception.lower()

    async def calibrate_weight(self) -> None:
        _LOGGER.debug("Calibrating weight sensor for %s", self.serial)
        try:
            await self.api.exec_device_command(self.serial, "CALIBRATE")
            await self.refresh()
        except (aiohttp.ClientError, PetLibroAPIError) as err:
            _LOGGER.error("Failed to calibrate weight sensor for %s: %s", self.serial, err)
            raise PetLibroAPIError(f"Error calibrating weight sensor: {err}") from err
