import asyncio
import aiohttp

from datetime import datetime
from logging import getLogger

from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class PolarWetFoodFeeder(Feeder):
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            grain_status = await self.api.device_grain_status(self.serial)
            real_info = await self.api.device_real_info(self.serial)
            attribute_settings = await self.api.device_attribute_settings(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            wet_feeding_plan = await self.api.device_wet_feeding_plan(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)

            self.update_data({
                "grainStatus": grain_status or {},
                "realInfo": real_info or {},
                "getAttributeSetting": attribute_settings or {},
                "getUpgrade": get_upgrade or {},
                "wetFeedingPlan": wet_feeding_plan or {},
                "getfeedingplantoday": get_feeding_plan_today or {}
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for PolarWetFoodFeeder: %s", err)

    @property
    def door_blocked(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("barnDoorError", False))

    @property
    def next_feeding_day(self) -> str:
        """Returns the next feeding day."""
        return self._data.get("nextFeedingDay", "unknown")

    @property
    def next_feeding_time(self) -> str:
        """Returns the next feeding start time in AM/PM format."""
        raw_time = self._data.get("nextFeedingTime", "unknown")
        if raw_time == "unknown":
            return raw_time
        try:
            time_obj = datetime.strptime(raw_time, "%H:%M")
            return time_obj.strftime("%I:%M %p")
        except ValueError:
            return "Invalid time"

    @property
    def next_feeding_end_time(self) -> str:
        """Returns the next feeding end time in AM/PM format."""
        raw_time = self._data.get("nextFeedingEndTime", "unknown")
        if raw_time == "unknown":
            return raw_time
        try:
            time_obj = datetime.strptime(raw_time, "%H:%M")
            return time_obj.strftime("%I:%M %p")
        except ValueError:
            return "Invalid time"

    @property
    def manual_feed_id(self) -> int:
        """Returns the manual feed ID."""
        return self._data.get("wetFeedingPlan", {}).get("manualFeedId", None)

    @property
    def manual_feed_now(self) -> bool:
        """Returns whether the feeder is set to feed now or not."""
        return self.manual_feed_id is not None

    @property
    def online_list(self) -> list:
        """Returns a list of online status records with timestamps."""
        return self._data.get("realInfo", {}).get("onlineList", [])

    @property
    def plate_position(self) -> int:
        """Returns the current position of the plate, if applicable."""
        return self._data.get("realInfo", {}).get("platePosition", 0)

    @property
    def temperature(self) -> float:
        """Returns the current temperature in Fahrenheit, rounded to 1 decimal place."""
        celsius = self._data.get("realInfo", {}).get("temperature", 0.0)
        fahrenheit = celsius * 9 / 5 + 32
        return round(fahrenheit, 1)

    async def set_manual_feed_now(self, start: bool, plate: int) -> None:
        plate = plate if plate is not None else self.plate_position
        try:
            if start:
                _LOGGER.debug("Triggering manual feed now for %s with plate no.%s", self.serial, plate)
                await self.api.set_manual_feed_now(self.serial, plate)
            else:
                _LOGGER.debug("Triggering stop feed now for %s", self.serial)
                await self.api.set_stop_feed_now(self.serial, self.manual_feed_id)

            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger manual feed now for %s with plate no.%s: %s", self.serial, plate, err)
            raise PetLibroAPIError(f"Error triggering manual feed now: {err}")

    async def set_plate_position(self, value: str | int) -> None:
        """Rotate bowl to requested plate (1-3)"""
        try:
            target = int(value)
        except (TypeError, ValueError):
            raise PetLibroAPIError(f"Invalid plate value: {value!r}")
        if target not in (1, 2, 3):
            raise PetLibroAPIError(f"Plate must be 1, 2, or 3, got {target}")

        if not self.plate_position:
            await self.refresh()
        curr = self.plate_position or 1

        steps = (target - curr) % 3
        _LOGGER.debug("Rotate-to-plate: curr=%s target=%s steps=%s for %s", curr, target, steps, self.serial)

        ROTATE_COOLDOWN = 0.6
        for _ in range(steps):
            await self.api.set_rotate_food_bowl(self.serial)
            await asyncio.sleep(ROTATE_COOLDOWN)
            await self.refresh()

        await self.refresh()

    async def rotate_food_bowl(self) -> None:
        _LOGGER.debug("Triggering rotate food bowl for %s", self.serial)

        try:
            await self.api.set_rotate_food_bowl(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger rotate food bowl for %s: %s", self.serial, err)
            raise PetLibroAPIError(f"Error triggering rotate food bowl: {err}")

    async def feed_audio(self) -> None:
        _LOGGER.debug("Triggering feed audio for %s", self.serial)

        try:
            await self.api.set_feed_audio(self.serial)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger feed audio for %s: %s", self.serial, err)
            raise PetLibroAPIError(f"Error triggering feed audio: {err}")

    async def reposition_schedule(self) -> None:
        _LOGGER.debug("Triggering reposition the schedule for %s", self.serial)

        if not self._data.get("wetFeedingPlan"):
            _LOGGER.debug("Triggering device data refresh because wet feeding plan data is missing for %s", self.serial)
            try:
                await self.refresh()
            except aiohttp.ClientError as err:
                _LOGGER.error("Failed to refresh device data for triggering reposition the schedule for %s: %s", self.serial, err)
                raise PetLibroAPIError(f"Error refresh device data for triggering reposition schedule: {err}")

        wet_plan = self._data.get("wetFeedingPlan", {})
        plan_name = wet_plan.get("templateName")

        if not plan_name:
            _LOGGER.error("Missing template name in wetFeedingPlan for %s", self.serial)
            raise PetLibroAPIError("Missing template name in wetFeedingPlan")

        plan_data = wet_plan.get("plan", [])
        if not isinstance(plan_data, list):
            _LOGGER.error("Unexpected format for wet feeding plan: %s", plan_data)
            raise PetLibroAPIError("Invalid wet feeding plan format")

        current_feeding_plan = [
            {
                "id": plate.get("id"),
                "plate": plate.get("plate"),
                "label": plate.get("label"),
                "executionStartTime": plate.get("executionStartTime"),
                "executionEndTime": plate.get("executionEndTime"),
            }
            for plate in self._data.get("wetFeedingPlan", {}).get("plan", [])
        ]

        try:
            await self.api.set_reposition_schedule(self.serial, current_feeding_plan, plan_name)
            await self.refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger reposition the schedule for %s: %s", self.serial, err)
            raise PetLibroAPIError(f"Error triggering reposition schedule: {err}")
