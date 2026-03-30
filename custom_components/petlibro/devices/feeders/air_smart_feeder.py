"""PETLIBRO Air Smart Feeder"""
from logging import getLogger

from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class AirSmartFeeder(Feeder):
    """PETLIBRO Air Smart Feeder device."""

    feed_conv_factor = 0.5
    max_feed_portions = 16

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            grain_status = await self.api.device_grain_status(self.serial)
            real_info = await self.api.device_real_info(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            attribute_settings = await self.api.device_attribute_settings(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            self.update_data({
                "grainStatus": grain_status or {},
                "realInfo": real_info or {},
                "getUpgrade": get_upgrade or {},
                "getAttributeSetting": attribute_settings or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record or [],
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for AirSmartFeeder: %s", err)
