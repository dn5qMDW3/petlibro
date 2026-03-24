import aiohttp

from logging import getLogger
from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class GranarySmartFeeder(Feeder):
    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            # Fetch specific data for this device
            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            get_default_matrix = await self.api.get_default_matrix(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            # Update internal data with fetched API data
            self.update_data({
                "grainStatus": grain_status or {},
                "getUpgrade": get_upgrade or {},
                "getDefaultMatrix": get_default_matrix or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record if get_work_record is not None else []
            })
        except PetLibroAPIError as err:
            _LOGGER.error(f"Error refreshing data for GranarySmartFeeder: {err}")
