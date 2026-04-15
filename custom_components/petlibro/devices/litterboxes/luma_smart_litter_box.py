"""Luma Smart Litter Box (PLLB001)"""
from logging import getLogger
from typing import cast
from ...exceptions import PetLibroAPIError
from ..device import Device

_LOGGER = getLogger(__name__)


class LumaSmartLitterBox(Device):
    """Represents the Luma Smart Litter Box device (PLLB001).

    Data sources (confirmed from live API):
      - realInfo:             connectivity, hardware, vacuum, light/sound, filter/cleaning
                              schedules, weight, camera, sleep, door error, warehouse states
      - dataRealInfo:         filterState, cleanState, matState, doorState, remainingMatDays,
                              exceptionMessage, actDeodorizationMode, deodorization states,
                              motionSensitivityLevel, batterySupply8Hours
      - getAttributeSetting:  sleep mode, clean mode, deodorization config, camera config,
                              night vision, pet detection, hardware button lock
      - getUpgrade:           OTA firmware info (null when up-to-date)
    """

    async def refresh(self):
        """Refresh the device data from the API."""
        try:
            await super().refresh()

            real_info = await self.api.device_real_info(self.serial)
            data_real_info = await self.api.device_data_real_info(self.serial)
            attribute_settings = await self.api.device_attribute_settings(self.serial)
            get_upgrade = await self.api.get_device_upgrade(self.serial)
            potty_today = await self.api.device_potty_today(self.serial)

            self.update_data({
                "realInfo": real_info or {},
                "dataRealInfo": data_real_info or {},
                "getAttributeSetting": attribute_settings or {},
                "getUpgrade": get_upgrade or {},
                "pottyToday": potty_today or {},
            })
        except PetLibroAPIError as err:
            _LOGGER.error("Error refreshing data for LumaSmartLitterBox: %s", err)

    @property
    def available(self) -> bool:
        return self.online

    # ── Connectivity ──────────────────────────────────────────

    @property
    def online(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("online", False))

    @property
    def wifi_ssid(self) -> str:
        return self._data.get("realInfo", {}).get("wifiSsid", "unknown")

    @property
    def wifi_rssi(self) -> int:
        val = self._data.get("realInfo", {}).get("wifiRssi")
        return val if isinstance(val, int) else -100

    @property
    def wifi_rssi_level(self) -> int:
        return self._data.get("realInfo", {}).get("wifiRssiLevel", 0)

    # ── Power / Battery ───────────────────────────────────────

    @property
    def battery_state(self) -> str:
        """Battery state string (e.g. 'low', 'normal', 'charging')."""
        return cast(str, self._data.get("realInfo", {}).get("batteryState", "unknown"))

    @property
    def electric_quantity(self) -> int:
        """Battery percentage (0-100). 0 when on AC power."""
        val = self._data.get("realInfo", {}).get("electricQuantity")
        return val if isinstance(val, int) else 0

    @property
    def power_mode(self) -> int:
        """Power mode (1 = AC, etc.)."""
        return self._data.get("realInfo", {}).get("powerMode", 0)

    @property
    def power_type(self) -> int:
        return self._data.get("realInfo", {}).get("powerType", 0)

    # ── Litter Weight / Level ─────────────────────────────────

    @property
    def weight(self) -> float:
        """Litter weight in device units."""
        val = self._data.get("realInfo", {}).get("weight")
        return float(val) if val is not None else 0.0

    @property
    def weight_percent(self) -> int:
        """Litter fill percentage (0-100)."""
        val = self._data.get("realInfo", {}).get("weightPercent")
        return val if isinstance(val, int) else 0

    @property
    def weight_state(self) -> str:
        """Litter weight state (NORMAL, LOW, etc.)."""
        return self._data.get("realInfo", {}).get("weightState", "NORMAL")

    # ── Waste Management ──────────────────────────────────────

    @property
    def rubbish_full_state(self) -> bool:
        """Waste bin full indicator."""
        return bool(self._data.get("realInfo", {}).get("rubbishFullState", False))

    @property
    def rubbish_inplace_state(self) -> bool:
        """Waste bin installed/in-place."""
        return bool(self._data.get("realInfo", {}).get("rubbishInplaceState", False))

    @property
    def garbage_warehouse_state(self) -> str:
        """Garbage warehouse state (NORMAL, etc.)."""
        return self._data.get("realInfo", {}).get("garbageWarehouseState", "NORMAL")

    @property
    def garbage_warehouse_leave_state(self) -> str:
        return self._data.get("realInfo", {}).get("garbageWarehouseLeaveState", "NORMAL")

    @property
    def warehouse_surplus_grain(self) -> str:
        """Overall litter warehouse supply (GOOD, LOW, etc.)."""
        return self._data.get("realInfo", {}).get("warehouseSurplusGrain", "GOOD")

    @property
    def left_warehouse_surplus_grain(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("leftWarehouseSurplusGrain", True))

    @property
    def right_warehouse_surplus_grain(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("rightWarehouseSurplusGrain", True))

    # ── Maintenance ───────────────────────────────────────────

    @property
    def filter_state(self) -> str:
        """Filter condition (GOOD, etc.) – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("filterState", "GOOD")

    @property
    def remaining_replacement_days(self) -> int:
        """Days until filter needs replacement – from realInfo."""
        val = self._data.get("realInfo", {}).get("remainingReplacementDays")
        return val if isinstance(val, int) else 0

    @property
    def filter_replacement_frequency(self) -> int:
        """Filter replacement cycle in days."""
        return self._data.get("realInfo", {}).get("filterReplacementFrequency", 90)

    @property
    def clean_state(self) -> str:
        """Machine cleanliness state – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("cleanState", "GOOD")

    @property
    def remaining_cleaning_days(self) -> int:
        """Days until machine cleaning needed – from realInfo."""
        val = self._data.get("realInfo", {}).get("remainingCleaningDays")
        return val if isinstance(val, int) else 0

    @property
    def machine_cleaning_frequency(self) -> int:
        """Machine cleaning cycle in days."""
        return self._data.get("realInfo", {}).get("machineCleaningFrequency", 90)

    @property
    def mat_state(self) -> str:
        """Mat condition – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("matState", "GOOD")

    @property
    def remaining_mat_days(self) -> int:
        """Days until mat replacement needed – from dataRealInfo."""
        val = self._data.get("dataRealInfo", {}).get("remainingMatDays")
        return val if isinstance(val, int) else 0

    # ── Door ──────────────────────────────────────────────────

    @property
    def door_state(self) -> str:
        """Door state (OPEN/CLOSE) – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("doorState", "CLOSE")

    @property
    def door_open(self) -> bool:
        return self.door_state == "OPEN"

    @property
    def barn_door_error(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("barnDoorError", False))

    @property
    def door_error_state(self) -> str:
        return self._data.get("realInfo", {}).get("doorErrorState", "NORMAL")

    # ── Vacuum / Cleaning ─────────────────────────────────────

    @property
    def vacuum_state(self) -> bool:
        """Whether the vacuum/self-clean system is active."""
        return bool(self._data.get("realInfo", {}).get("vacuumState", False))

    @property
    def vacuum_mode(self) -> str:
        return self._data.get("realInfo", {}).get("vacuumMode", "NORMAL")

    @property
    def pump_air_state(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("pumpAirState", False))

    @property
    def throw_mode(self) -> str:
        return self._data.get("realInfo", {}).get("throwMode", "NORMAL")

    @property
    def clean_mode(self) -> str:
        """Auto-clean mode (AUTO, MANUAL, etc.) – from attributeSettings."""
        return self._data.get("getAttributeSetting", {}).get("cleanMode", "AUTO")

    @property
    def clean_mode_enable(self) -> bool:
        return bool(self._data.get("getAttributeSetting", {}).get("cleanModeEnable", False))

    @property
    def auto_delay_sec(self) -> int:
        """Delay in seconds before auto-clean triggers after use."""
        return self._data.get("getAttributeSetting", {}).get("autoDelaySec", 60)

    # ── Deodorization ─────────────────────────────────────────

    @property
    def deodorization_mode(self) -> str:
        """Active deodorization mode (SMART, MANUAL, etc.) – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("actDeodorizationMode", "SMART")

    @property
    def deodorization_state_on(self) -> bool:
        return bool(self._data.get("dataRealInfo", {}).get("deodorizationStateOn", False))

    @property
    def deodorization_mode_switch(self) -> bool:
        """Master deodorization on/off – from attributeSettings."""
        return bool(self._data.get("getAttributeSetting", {}).get("deodorizationModeSwitch", False))

    @property
    def deodorization_wind_speed(self) -> str:
        return self._data.get("getAttributeSetting", {}).get("deodorizationWindSpeed", "LOW")

    @property
    def deodorization_timer_off_switch(self) -> bool:
        return bool(self._data.get("dataRealInfo", {}).get("deodorizationTimerOffSwitch", False))

    # ── Camera ────────────────────────────────────────────────

    @property
    def enable_camera(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableCamera", False))

    @property
    def camera_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("cameraSwitch", False))

    @property
    def resolution(self) -> str:
        return self._data.get("realInfo", {}).get("resolution", "P1080")

    @property
    def cloud_video_record_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("cloudVideoRecordSwitch", False))

    @property
    def night_vision_mode(self) -> str:
        return self._data.get("getAttributeSetting", {}).get("nightVisionMode", "AUTO_BLACK_WHITE")

    @property
    def pet_detection_switch(self) -> bool:
        return bool(self._data.get("getAttributeSetting", {}).get("petDetectionSwitch", False))

    @property
    def enable_human_detection(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableHumanDetection", False))

    # ── Sound / Light / Volume ────────────────────────────────

    @property
    def enable_sound(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableSound", False))

    @property
    def sound_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("soundSwitch", False))

    @property
    def enable_light(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("enableLight", False))

    @property
    def light_switch(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("lightSwitch", False))

    @property
    def volume(self) -> int:
        """Speaker volume (0-100)."""
        val = self._data.get("realInfo", {}).get("volume")
        return val if isinstance(val, int) else 0

    # ── Device Status ─────────────────────────────────────────

    @property
    def running_state(self) -> str:
        """Running state (IDLE, RUNNING, etc.)."""
        return self._data.get("realInfo", {}).get("runningState", "IDLE")

    @property
    def device_stopped_working(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("deviceStoppedWorking", False))

    @property
    def exception_message(self) -> str:
        """Exception message – from dataRealInfo."""
        return self._data.get("dataRealInfo", {}).get("exceptionMessage", "")

    @property
    def calibration(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("calibration", False))

    # ── Sleep Mode ────────────────────────────────────────────

    @property
    def whether_in_sleep_mode(self) -> bool:
        return bool(self._data.get("realInfo", {}).get("whetherInSleepMode", False))

    @property
    def enable_sleep_mode(self) -> bool:
        return bool(self._data.get("getAttributeSetting", {}).get("enableSleepMode", False))

    # ── Hardware Button Lock ──────────────────────────────────

    @property
    def disable_hardware_button(self) -> bool:
        return bool(self._data.get("getAttributeSetting", {}).get("disableHardwareButton", False))

    # ── Potty Tracking ────────────────────────────────────────

    @property
    def today_potty_times(self) -> int:
        """Number of litter box uses today."""
        val = self._data.get("pottyToday", {}).get("times")
        return val if isinstance(val, int) else 0

    @property
    def today_potty_duration(self) -> int:
        """Total duration of litter box uses today (seconds)."""
        val = self._data.get("pottyToday", {}).get("duration")
        return val if isinstance(val, int) else 0

    # ── Battery ───────────────────────────────────────────────

    @property
    def battery_supply_8_hours(self) -> bool:
        """Whether the battery can supply power for 8 hours."""
        return bool(self._data.get("dataRealInfo", {}).get("batterySupply8Hours", False))

    # ── Deodorization Extras ──────────────────────────────────

    @property
    def after_deodorization_switch(self) -> bool:
        """Auto-deodorize after each litter box use."""
        return bool(self._data.get("getAttributeSetting", {}).get("afterDeodorizationSwitch", False))

    @property
    def duration_after_deodorization(self) -> int:
        """Duration (minutes) of post-use deodorization."""
        val = self._data.get("getAttributeSetting", {}).get("durationAfterDeodorization")
        return val if isinstance(val, int) else 2

    # ── Sleep Mode Sub-Settings ───────────────────────────────

    @property
    def enable_auto_clean_in_sleep_mode(self) -> bool:
        """Whether auto-clean runs during sleep mode."""
        return bool(self._data.get("getAttributeSetting", {}).get("enableAutoCleanInSleepMode", True))

    @property
    def enable_deodorization_in_sleep_mode(self) -> bool:
        """Whether deodorization runs during sleep mode."""
        return bool(self._data.get("getAttributeSetting", {}).get("enableDeodorizationInSleepMode", True))

    # ── Cleaning Extras ───────────────────────────────────────

    @property
    def avoid_repeat_clean(self) -> bool:
        """Avoid repeat cleaning cycles."""
        return bool(self._data.get("getAttributeSetting", {}).get("avoidRepeatClean", False))

    # ── Firmware / OTA ────────────────────────────────────────

    @property
    def update_available(self) -> bool:
        upgrade = self._data.get("getUpgrade")
        return bool(upgrade and upgrade.get("jobItemId"))

    @property
    def update_release_notes(self) -> str | None:
        upgrade = self._data.get("getUpgrade")
        return upgrade.get("upgradeDesc") if upgrade else None

    @property
    def update_version(self) -> str | None:
        upgrade = self._data.get("getUpgrade")
        return upgrade.get("targetVersion") if upgrade else None

    @property
    def update_name(self) -> str | None:
        upgrade = self._data.get("getUpgrade")
        return upgrade.get("jobName") if upgrade else None

    @property
    def update_progress(self) -> float:
        upgrade = self._data.get("getUpgrade")
        if not upgrade:
            return 0.0
        progress = upgrade.get("progress")
        return float(progress) if progress is not None else 0.0

    # ── Control Methods ───────────────────────────────────────

    async def trigger_manual_clean(self) -> None:
        """Trigger a manual clean cycle. Returns immediately; device response is async."""
        _LOGGER.debug("Triggering manual clean for %s", self.serial)
        try:
            await self.api.trigger_manual_clean(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to trigger manual clean for %s: %s", self.serial, err)

    async def trigger_empty_waste(self) -> None:
        """Trigger waste bin emptying."""
        _LOGGER.debug("Triggering empty waste for %s", self.serial)
        try:
            await self.api.trigger_empty_waste(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to trigger empty waste for %s: %s", self.serial, err)

    async def trigger_level_litter(self) -> None:
        """Trigger litter leveling."""
        _LOGGER.debug("Triggering level litter for %s", self.serial)
        try:
            await self.api.trigger_level_litter(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to trigger level litter for %s: %s", self.serial, err)

    async def trigger_stop_action(self) -> None:
        """Stop current device action."""
        _LOGGER.debug("Stopping action for %s", self.serial)
        try:
            await self.api.trigger_stop_device_action(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to stop action for %s: %s", self.serial, err)

    async def trigger_open_door(self) -> None:
        """Open the litter box door."""
        _LOGGER.debug("Opening door for %s", self.serial)
        try:
            await self.api.trigger_open_door(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to open door for %s: %s", self.serial, err)

    async def trigger_close_door(self) -> None:
        """Close the litter box door."""
        _LOGGER.debug("Closing door for %s", self.serial)
        try:
            await self.api.trigger_close_door(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to close door for %s: %s", self.serial, err)

    async def trigger_vacuum(self) -> None:
        """Trigger the air purifier (vacuum)."""
        _LOGGER.debug("Triggering air purifier for %s", self.serial)
        try:
            await self.api.trigger_vacuum(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to trigger air purifier for %s: %s", self.serial, err)

    async def set_manual_lid_open(self) -> None:
        """Open the barn door / lid (legacy doorStateChange endpoint)."""
        _LOGGER.debug("Opening lid for %s", self.serial)
        try:
            await self.api.set_manual_lid_open(self.serial)
        except Exception as err:
            _LOGGER.error("Failed to open lid for %s: %s", self.serial, err)

    async def set_sound_switch(self, value: bool) -> None:
        _LOGGER.debug("Setting sound switch to %s for %s", value, self.serial)
        try:
            await self.api.set_sound_switch(self.serial, value)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set sound switch for %s: %s", self.serial, err)

    async def set_light_switch(self, value: bool) -> None:
        _LOGGER.debug("Setting light switch to %s for %s", value, self.serial)
        try:
            await self.api.set_light_switch(self.serial, value)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set light switch for %s: %s", self.serial, err)

    async def set_deodorization_switch(self, value: bool) -> None:
        """Enable/disable deodorization (keeps current mode)."""
        _LOGGER.debug("Setting deodorization switch to %s for %s", value, self.serial)
        try:
            await self.api.set_deodorization_setting(
                self.serial, self.deodorization_mode, value
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set deodorization switch for %s: %s", self.serial, err)

    async def set_clean_mode(self, mode: str) -> None:
        """Set clean mode (AUTO/MANUAL)."""
        _LOGGER.debug("Setting clean mode to %s for %s", mode, self.serial)
        try:
            await self.api.set_clean_mode(self.serial, mode, self.auto_delay_sec)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set clean mode for %s: %s", self.serial, err)

    async def set_volume(self, volume: int) -> None:
        """Set speaker volume (0-100)."""
        _LOGGER.debug("Setting volume to %s for %s", volume, self.serial)
        try:
            await self.api.set_volume(self.serial, volume)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set volume for %s: %s", self.serial, err)

    async def set_auto_delay_sec(self, value: int) -> None:
        """Set the auto-clean delay in seconds."""
        _LOGGER.debug("Setting auto delay to %ss for %s", value, self.serial)
        try:
            await self.api.set_clean_mode(self.serial, self.clean_mode, value)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set auto delay for %s: %s", self.serial, err)

    async def set_after_deodorization_switch(self, value: bool) -> None:
        """Enable/disable post-use deodorization."""
        _LOGGER.debug("Setting after deodorization switch to %s for %s", value, self.serial)
        try:
            await self.api.set_after_deodorization(
                self.serial, value, self.duration_after_deodorization
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set after deodorization for %s: %s", self.serial, err)

    async def set_duration_after_deodorization(self, value: int) -> None:
        """Set duration (minutes) of post-use deodorization."""
        _LOGGER.debug("Setting deodorization duration to %sm for %s", value, self.serial)
        try:
            await self.api.set_after_deodorization(
                self.serial, self.after_deodorization_switch, value
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set deodorization duration for %s: %s", self.serial, err)

    async def set_avoid_repeat_clean(self, value: bool) -> None:
        """Enable/disable avoid repeat cleaning."""
        _LOGGER.debug("Setting avoid repeat clean to %s for %s", value, self.serial)
        try:
            await self.api.set_clean_mode_setting(
                self.serial, self.clean_mode, self.auto_delay_sec, value
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set avoid repeat clean for %s: %s", self.serial, err)

    async def set_enable_auto_clean_in_sleep_mode(self, value: bool) -> None:
        """Enable/disable auto-clean during sleep mode."""
        _LOGGER.debug("Setting auto clean in sleep to %s for %s", value, self.serial)
        try:
            await self.api.set_sleep_mode_setting(
                self.serial, self.enable_sleep_mode, value,
                self.enable_deodorization_in_sleep_mode
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set auto clean in sleep for %s: %s", self.serial, err)

    async def set_enable_deodorization_in_sleep_mode(self, value: bool) -> None:
        """Enable/disable deodorization during sleep mode."""
        _LOGGER.debug("Setting deodorization in sleep to %s for %s", value, self.serial)
        try:
            await self.api.set_sleep_mode_setting(
                self.serial, self.enable_sleep_mode,
                self.enable_auto_clean_in_sleep_mode, value
            )
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set deodorization in sleep for %s: %s", self.serial, err)

    async def set_deodorization_wind_speed(self, value: str) -> None:
        """Set deodorization wind speed (LOW/MEDIUM/HIGH)."""
        _LOGGER.debug("Setting deodorization wind speed to %s for %s", value, self.serial)
        try:
            await self.api.set_deodorization_wind_speed(self.serial, value)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to set wind speed for %s: %s", self.serial, err)

    async def reset_filter(self) -> None:
        """Reset the filter replacement timer."""
        _LOGGER.debug("Resetting filter for %s", self.serial)
        try:
            await self.api.reset_filter(self.serial)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to reset filter for %s: %s", self.serial, err)

    async def reset_cleaning(self) -> None:
        """Reset the machine cleaning timer."""
        _LOGGER.debug("Resetting cleaning timer for %s", self.serial)
        try:
            await self.api.reset_machine_cleaning(self.serial)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to reset cleaning for %s: %s", self.serial, err)

    async def reset_mat(self) -> None:
        """Reset the mat replacement timer."""
        _LOGGER.debug("Resetting mat for %s", self.serial)
        try:
            await self.api.reset_mat(self.serial)
            await self.refresh()
        except Exception as err:
            _LOGGER.error("Failed to reset mat for %s: %s", self.serial, err)
