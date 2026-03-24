from logging import getLogger
from ...exceptions import PetLibroAPIError
from .feeder import Feeder

_LOGGER = getLogger(__name__)


class GranarySmartCameraFeeder(Feeder):
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
            _LOGGER.error(f"Error refreshing data for GranarySmartCameraFeeder: {err}")

    # ------------------------------------------------------------------
    # Camera-specific properties
    # ------------------------------------------------------------------

    @property
    def resolution(self) -> str:
        """Return the camera resolution."""
        return self._data.get("realInfo", {}).get("resolution", "unknown")

    @property
    def night_vision(self) -> str:
        """Return the current night vision mode."""
        return self._data.get("realInfo", {}).get("nightVision", "unknown")

    @property
    def enable_video_record(self) -> bool:
        """Return whether video recording is enabled."""
        return self._data.get("realInfo", {}).get("enableVideoRecord", False)

    @property
    def video_record_switch(self) -> bool:
        """Return the state of the video recording switch."""
        return self._data.get("realInfo", {}).get("videoRecordSwitch", False)

    @property
    def video_record_mode(self) -> str:
        """Return the current video recording mode."""
        return self._data.get("realInfo", {}).get("videoRecordMode", "unknown")
