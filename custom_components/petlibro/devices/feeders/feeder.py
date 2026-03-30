"""Generic PETLIBRO feeder"""
import ast
from zoneinfo import ZoneInfo
import aiohttp

from typing import cast
from logging import getLogger
from datetime import datetime, timedelta, time

from homeassistant.util import dt as dt_util

from ...exceptions import PetLibroAPIError
from ..device import Device


_LOGGER = getLogger(__name__)


UNITS = {
    1: "cup",
    2: "oz",
    3: "g",
    4: "mL"
}

UNITS_RATIO = {
    1: 1/12,
    2: 0.35,
    3: 10,
    4: 20
}


class Feeder(Device):
    """Generic PETLIBRO feeder device.

    Shared properties and setters common to all dry feeders live here.
    Subclasses only override refresh() and add device-specific extras.
    """

    # Subclasses can override these to match device-specific limits
    feed_conv_factor: float = 0.5
    max_feed_portions: int = 16

    def __init__(self, *args, **kwargs):
        """Initialize the feeder with default values."""
        super().__init__(*args, **kwargs)
        self._manual_feed_quantity = None

    async def refresh(self):
        await super().refresh()
        self.update_data({
            "feedingPlanTodayNew": await self.api.device_feeding_plan_today_new(self.serial)
        })

    # ------------------------------------------------------------------
    # Unit helpers
    # ------------------------------------------------------------------

    @property
    def unit_id(self) -> int | None:
        return self._data.get("unitType")

    @property
    def unit_type(self) -> int:
        return self._data.get("realInfo", {}).get("unitType", 1)

    @property
    def unit_type_name(self) -> str | None:
        if unit_id := self.unit_id:
            return UNITS.get(unit_id)
        return None

    def convert_unit(self, value: int) -> int:
        if self.unit_id:
            return value * UNITS_RATIO.get(self.unit_id, 1)
        return value

    # ------------------------------------------------------------------
    # Online / available
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        return self.online

    @property
    def online(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("online", False))

    # ------------------------------------------------------------------
    # realInfo properties (common across feeders)
    # ------------------------------------------------------------------

    @property
    def battery_state(self) -> str:
        return cast(str, self._data.get("realInfo", {}).get("batteryState", "unknown"))

    @property
    def battery_display_type(self) -> float:
        try:
            value = str(self._data.get("realInfo", {}).get("batteryDisplayType", "percentage"))
            return cast(float, float(value))
        except (TypeError, ValueError):
            return 0.0

    @property
    def food_dispenser_state(self) -> bool:
        return not bool(self._data.get("realInfo", {}).get("grainOutletState", True))

    @property
    def food_low(self) -> bool:
        return not bool(self._data.get("realInfo", {}).get("surplusGrain", True))

    @property
    def running_state(self) -> bool:
        return self._data.get("realInfo", {}).get("runningState", "IDLE") == "RUNNING"

    @property
    def wifi_ssid(self) -> str:
        return self._data.get("realInfo", {}).get("wifiSsid", "unknown")

    @property
    def wifi_rssi(self) -> int:
        wifi_rssi = self._data.get("realInfo", {}).get("wifiRssi")
        return wifi_rssi if isinstance(wifi_rssi, int) else -100

    @property
    def electric_quantity(self) -> float:
        quantity = self._data.get("realInfo", {}).get("electricQuantity")
        return quantity if isinstance(quantity, (float, int)) else 0

    @property
    def enable_feeding_plan(self) -> bool:
        return self._data.get("realInfo", {}).get("enableFeedingPlan", False)

    @property
    def enable_sound(self) -> bool:
        return self._data.get("realInfo", {}).get("enableSound", False)

    @property
    def enable_light(self) -> bool:
        return self._data.get("realInfo", {}).get("enableLight", False)

    @property
    def light_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("lightSwitch", False))

    @property
    def vacuum_state(self) -> bool:
        return self._data.get("realInfo", {}).get("vacuumState", False)

    @property
    def pump_air_state(self) -> bool:
        return self._data.get("realInfo", {}).get("pumpAirState", False)

    @property
    def cover_close_speed(self) -> str:
        return self._data.get("realInfo", {}).get("coverCloseSpeed", "unknown")

    @property
    def enable_re_grain_notice(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableReGrainNotice", False))

    @property
    def child_lock_switch(self) -> bool:
        return self._data.get("realInfo", {}).get("childLockSwitch", False)

    @property
    def close_door_time_sec(self) -> int:
        time_sec = self._data.get("realInfo", {}).get("closeDoorTimeSec")
        return time_sec if isinstance(time_sec, int) else 0

    @property
    def screen_display_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("screenDisplaySwitch", False))

    @property
    def device_sn(self) -> str:
        return self._data.get("realInfo", {}).get("deviceSn", "unknown")

    @property
    def mac_address(self) -> str:
        return self._data.get("realInfo", {}).get("mac", "unknown")

    @property
    def whether_in_sleep_mode(self) -> bool:
        return bool(self._data.get("getAttributeSetting", {}).get("enableSleepMode", False))

    @property
    def enable_low_battery_notice(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableLowBatteryNotice", False))

    @property
    def enable_power_change_notice(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enablePowerChangeNotice", False))

    @property
    def enable_grain_outlet_blocked_notice(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableGrainOutletBlockedNotice", False))

    # ------------------------------------------------------------------
    # Feeding plan state
    # ------------------------------------------------------------------

    @property
    def feeding_plan_state(self) -> bool:
        return bool(self._data.get("enableFeedingPlan", False))

    @property
    def feeding_plan(self) -> bool:
        return self._data.get("enableFeedingPlan", False)

    async def set_feeding_plan(self, value: bool) -> None:
        await self.api.set_feeding_plan(self.serial, value)
        await self.refresh()

    @property
    def feeding_plan_today_all(self) -> bool:
        return not cast(bool, self._data.get("feedingPlanTodayNew", {}).get("allSkipped"))

    async def set_feeding_plan_today_all(self, value: bool):
        await self.api.feeding_plan_today_all(self.serial, value)
        await self.refresh()

    # ------------------------------------------------------------------
    # grainStatus properties
    # ------------------------------------------------------------------

    @property
    def today_feeding_quantities(self) -> list[int]:
        return self._data.get("grainStatus", {}).get("todayFeedingQuantities", [])

    @property
    def today_feeding_quantity(self) -> float:
        quantity = self._data.get("grainStatus", {}).get("todayFeedingQuantity")
        return quantity if isinstance(quantity, (int, float)) else 0

    @property
    def today_feeding_times(self) -> int:
        times = self._data.get("grainStatus", {}).get("todayFeedingTimes")
        return times if isinstance(times, int) else 0

    # ------------------------------------------------------------------
    # Desiccant
    # ------------------------------------------------------------------

    @property
    def remaining_desiccant(self) -> float | None:
        value = self._data.get("remainingDesiccantDays")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def desiccant_frequency(self) -> float:
        frequency = self._data.get("realInfo", {}).get("changeDesiccantFrequency")
        return frequency if isinstance(frequency, (float, int)) else 0

    # ------------------------------------------------------------------
    # Work record (last feed)
    # ------------------------------------------------------------------

    @property
    def last_feed_time(self) -> datetime | None:
        raw = self._data.get("workRecord", [])
        if not raw or not isinstance(raw, list):
            return None

        for day_entry in raw:
            for record in day_entry.get("workRecords", []):
                if record.get("type") == "GRAIN_OUTPUT_SUCCESS":
                    timestamp_ms = record.get("recordTime", 0)
                    if timestamp_ms:
                        return dt_util.utc_from_timestamp(timestamp_ms / 1000)
        return None

    @property
    def last_feed_quantity(self) -> int:
        raw = self._data.get("workRecord", [])
        if raw and isinstance(raw, list):
            for day_entry in raw:
                for record in day_entry.get("workRecords", []):
                    if record.get("type") == "GRAIN_OUTPUT_SUCCESS":
                        actualGrainNum = record.get("actualGrainNum")
                        return actualGrainNum if isinstance(actualGrainNum, int) else 0
        return 0

    # ------------------------------------------------------------------
    # Feeding plan data properties
    # ------------------------------------------------------------------

    @property
    def feeding_plan_today_data(self) -> dict:
        return self._data.get("getfeedingplantoday", {})

    @property
    def feeding_plan_data(self) -> dict:
        return {
            str(plan["id"]): plan
            for plan in self._data.get("feedingPlan", [])
            if isinstance(plan, dict) and "id" in plan
        } or {}

    @property
    def get_next_feed(self) -> dict:
        now_utc = dt_util.now(dt_util.UTC)
        next_feed = {}

        for feed in self.feeding_plan_data.values():
            if not (feed.get("id") and feed.get("enable") and ":" in feed.get("executionTime", "")):
                continue

            timezone = ZoneInfo(feed.get("timezone", "UTC"))
            repeat_days = ast.literal_eval(feed.get("repeatDay", ""))
            now_local = now_utc.astimezone(timezone)
            hour, minute = map(int, feed["executionTime"].split(":"))

            candidate_dt_local = None

            if not repeat_days:
                plan_dt_local = datetime.combine(now_local.date(), time(hour, minute), timezone)
                if plan_dt_local > now_local:
                    candidate_dt_local = plan_dt_local
                else:
                    candidate_dt_local = plan_dt_local + timedelta(days=1)
            else:
                for i in range(8):
                    day_dt_local = now_local + timedelta(days=i)
                    if day_dt_local.isoweekday() not in repeat_days:
                        continue
                    plan_dt_local = datetime.combine(day_dt_local.date(), time(hour, minute), timezone)
                    if plan_dt_local > now_local:
                        candidate_dt_local = plan_dt_local
                        break

            if candidate_dt_local:
                candidate_dt_utc = candidate_dt_local.astimezone(dt_util.UTC)
                if not next_feed or candidate_dt_utc < next_feed["utc_time"]:
                    next_feed = {"id": feed["id"], "utc_time": candidate_dt_utc}
        return next_feed

    @property
    def next_feed_time(self) -> datetime | None:
        next_feed = self.get_next_feed
        if next_feed and (utc_time := next_feed.get("utc_time")):
            return utc_time
        return None

    @property
    def next_feed_quantity(self) -> int:
        next_feed = self.get_next_feed
        if next_feed and (plan_id := next_feed.get("id")):
            feeding_plan = self.feeding_plan_data.get(str(plan_id), {})
            if feeding_plan:
                grainNum = feeding_plan.get("grainNum")
                return grainNum if isinstance(grainNum, int) else 0
        return 0

    # ------------------------------------------------------------------
    # Manual feed quantity
    # ------------------------------------------------------------------

    @property
    def manual_feed_quantity(self):
        if self._manual_feed_quantity is None:
            self._manual_feed_quantity = 1
        return self._manual_feed_quantity

    @manual_feed_quantity.setter
    def manual_feed_quantity(self, value: float):
        self._manual_feed_quantity = value

    async def set_manual_feed_quantity(self, value: float):
        self.manual_feed_quantity = max(1, min(value, self.max_feed_portions))

    # ------------------------------------------------------------------
    # Update properties
    # ------------------------------------------------------------------

    @property
    def update_available(self) -> bool:
        return bool(self._data.get("getUpgrade", {}).get("jobItemId"))

    @property
    def update_release_notes(self) -> str:
        return self._data.get("getUpgrade", {}).get("upgradeDesc", "")

    @property
    def update_version(self) -> str:
        return self._data.get("getUpgrade", {}).get("targetVersion", "")

    @property
    def update_name(self) -> str:
        return self._data.get("getUpgrade", {}).get("jobName", "")

    @property
    def update_progress(self) -> float:
        progress = self._data.get("getUpgrade", {}).get("progress")
        try:
            return float(progress) if progress is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Common setter methods
    # ------------------------------------------------------------------

    async def set_manual_feed(self) -> None:
        feed_quantity = getattr(self, "manual_feed_quantity", 1)
        await self.api.set_manual_feed(self.serial, feed_quantity)
        await self.refresh()

    async def set_child_lock(self, value: bool) -> None:
        await self.api.set_child_lock(self.serial, value)
        await self.refresh()

    async def set_light_enable(self, value: bool) -> None:
        await self.api.set_light_enable(self.serial, value)
        await self.refresh()

    async def set_light_switch(self, value: bool) -> None:
        await self.api.set_light_switch(self.serial, value)
        await self.refresh()

    async def set_sound_enable(self, value: bool) -> None:
        await self.api.set_sound_enable(self.serial, value)
        await self.refresh()

    async def set_sound_switch(self, value: bool) -> None:
        await self.api.set_sound_switch(self.serial, value)
        await self.refresh()

    async def set_light_on(self) -> None:
        await self.api.set_light_on(self.serial)
        await self.refresh()

    async def set_light_off(self) -> None:
        await self.api.set_light_off(self.serial)
        await self.refresh()

    async def set_desiccant_cycle(self, value: float) -> None:
        await self.api.set_desiccant_cycle(self.serial, value, "changeDesiccantFrequency")
        await self.refresh()

    async def set_desiccant_reset(self) -> None:
        await self.api.set_desiccant_reset(self.serial)
        await self.refresh()
