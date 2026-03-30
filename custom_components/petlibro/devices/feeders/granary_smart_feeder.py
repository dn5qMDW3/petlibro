"""PETLIBRO Granary Smart Feeder"""
from datetime import datetime, timezone
from logging import getLogger

from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class GranarySmartFeeder(Feeder):
    """PETLIBRO Granary Smart Feeder device."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        max_cup = self._data.get("maxFeedingCup")
        if max_cup and isinstance(max_cup, int):
            self.max_feed_portions = max_cup

    # ------------------------------------------------------------------
    # Granary-specific properties
    # ------------------------------------------------------------------

    @property
    def bowl_mode(self) -> str:
        return self._data.get("realInfo", {}).get("bowlMode", "unknown")

    @property
    def grain_outlet_state(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("grainOutletState", True))

    @property
    def motor_state(self) -> int:
        return self._data.get("realInfo", {}).get("motorState", 0)

    @property
    def volume(self) -> int:
        return self._data.get("realInfo", {}).get("volume", 50)

    @property
    def auto_threshold(self) -> int:
        return self._data.get("realInfo", {}).get("autoThreshold", 0)

    @property
    def last_online_time(self) -> datetime | None:
        ts = self._data.get("realInfo", {}).get("lastOnlineTime")
        if ts and isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return None

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_default_matrix = await self.api.get_default_matrix(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            self.update_data({
                "grainStatus": grain_status or {},
                "getUpgrade": get_upgrade or {},
                "getDefaultMatrix": get_default_matrix or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record if get_work_record is not None else [],
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for GranarySmartFeeder: %s", err)
