from logging import getLogger
from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class AirSmartFeeder(Feeder):
    def __init__(self, *args, **kwargs):
        """Initialize the feeder with default values."""
        super().__init__(*args, **kwargs)

        self.feed_conv_factor = 0.5   # Air Smart Feeder uses #
        self.max_feed_portions = 16   #  unique values here   #

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            # Fetch specific data for this device
            grain_status = await self.api.device_grain_status(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            get_feeding_plan_today = await self.api.device_feeding_plan_today_new(self.serial)
            get_work_record = await self.api.get_device_work_record(self.serial)
            feeding_plan_list = (await self.api.device_feeding_plan_list(self.serial)
                if self._data.get("enableFeedingPlan") else [])

            # Update internal data with fetched API data
            self.update_data({
                "grainStatus": grain_status or {},
                "getUpgrade": get_upgrade or {},
                "getfeedingplantoday": get_feeding_plan_today or {},
                "feedingPlan": feeding_plan_list or [],
                "workRecord": get_work_record or [],
            })
        except PetLibroAPIError as err:
            _LOGGER.error(f"Error refreshing data for AirSmartFeeder: {err}")
