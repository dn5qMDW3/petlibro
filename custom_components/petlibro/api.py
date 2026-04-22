from logging import getLogger
from hashlib import md5
from urllib.parse import urljoin
from typing import Any
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import utcnow
from .exceptions import PetLibroAPIError
from aiohttp import ClientSession

import aiohttp
import asyncio
import uuid  # To generate unique request IDs

async def make_api_call(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
_LOGGER = getLogger(__name__)

class PetLibroSession:
    """PetLibro AIOHTTP session"""
    
    def __init__(self, base_url: str, websession: ClientSession, email: str, password: str, region: str, token: str | None = None, time_zone: str | None = None):
        self.base_url = base_url
        self.websession = websession
        self.token = token
        self.email = email
        self.password = password
        self.region = region
        self.headers = {
            "source": "ANDROID",
            "language": "EN",
            "timezone": time_zone or "America/Chicago",
            "version": "1.8.10",
        }

    async def post(self, path: str, **kwargs: Any) -> JSON:
        """POST method for PetLibro API."""
        return await self.request("POST", path, **kwargs)

    async def post_serial(self, path: str, serial: str, **kwargs: Any) -> JSON:
        """POST request with device serial in the payload."""
        json_data = kwargs.get("json", {})
        json_data["id"] = serial  # Add serial as 'id'
        json_data["deviceSn"] = serial  # Add serial as 'deviceSn'
        kwargs["json"] = json_data
        return await self.request("POST", path, **kwargs)

    async def get(self, path: str, params: dict = None, **kwargs: Any) -> JSON:
        """GET method for the PetLibro API."""
        return await self.request("GET", path, params=params, **kwargs)

    async def request(self, method: str, url: str, **kwargs: Any) -> JSON:
        """Make a request."""
        joined_url = urljoin(self.base_url, url)
        _LOGGER.debug("Making %s request to %s", method, joined_url)

        if "headers" not in kwargs:
            kwargs["headers"] = {}

        # Add default headers
        headers = self.headers.copy()
        headers.update(kwargs["headers"].copy())
        kwargs["headers"] = headers

        # Set Content-Type to JSON explicitly
        kwargs["headers"]["Content-Type"] = "application/json; charset=utf-8"

        if self.token is not None:
            kwargs["headers"]["token"] = self.token
            _LOGGER.debug("Using token: %s...", self.token[:8] if self.token else "None")
        else:
            _LOGGER.warning("No token available for request. Attempting to log in...")

        # Send the request
        async with self.websession.request(method, joined_url, **kwargs) as resp:
            _LOGGER.debug("Received response status: %s", resp.status)
            try:
                data = await resp.json()
            except Exception as e:
                raise PetLibroAPIError(f"Error parsing response JSON: {e}")

            _LOGGER.debug("Response data: %s", data)

            if resp.status != 200:
                raise PetLibroAPIError(f"Request failed with status: {resp.status}")

            if data.get("code") == 1009:  # NOT_YET_LOGIN error code
                _LOGGER.debug("NOT_YET_LOGIN error occurred for %s. Trying re-login.", joined_url)
                # Trigger a re-login and get the new token
                new_token = await self.re_login()
                kwargs["headers"]["token"] = new_token
                _LOGGER.debug("Retrying request with new token: %s...", new_token[:8] if new_token else "None")

                # Retry the request with the new token
                async with self.websession.request(method, joined_url, **kwargs) as retry_resp:
                    retry_data = await retry_resp.json()
                    _LOGGER.debug("Retry response: %s", retry_data)
                    return retry_data.get("data")

            if data.get("code") != 0:
                raise PetLibroAPIError(f"Code: {data.get('code')}, Message: {data.get('msg')}")

            return data.get("data") or {}

    async def re_login(self) -> str:
        """Re-login to get a new token when the old one expires."""
        try:
            _LOGGER.debug("Attempting re-login with email: %s and region: %s", self.email, self.region)

            async with self.websession.post(
                urljoin(self.base_url, "/member/auth/login"),
                json={
                    "appId": PetLibroAPI.APPID,
                    "appSn": PetLibroAPI.APPSN,
                    "country": self.region,
                    "email": self.email,
                    "password": PetLibroAPI.hash_password(self.password),
                    "phoneBrand": "",
                    "phoneSystemVersion": "",
                    "timezone": self.headers["timezone"],
                    "thirdId": None,
                    "type": None
                },
                headers=self.headers
            ) as response:
                _LOGGER.debug("Re-login response status: %s", response.status)

                if response.status != 200:
                    raise PetLibroAPIError(f"Failed to login, status: {response.status}")

                response_data = await response.json()
                _LOGGER.debug("Re-login response data: %s", response_data)

                if not isinstance(response_data, dict) or "token" not in response_data.get("data", {}):
                    raise PetLibroAPIError("Token not found during login.")

                # Get the new token from response data
                new_token = response_data["data"]["token"]
                self.token = new_token  # Update the session token

                # Save the new token in the config entry
                if hasattr(self, 'api') and self.api.hass and self.api.config_entry:
                    _LOGGER.debug("Saving new token to config entry: %s...", self.token[:8] if self.token else "None")
                    self.api.hass.config_entries.async_update_entry(
                        self.api.config_entry,
                        data={**self.api.config_entry.data, "token": self.token}
                    )

                return new_token

        except aiohttp.ClientError as e:
            _LOGGER.error("Re-login failed due to a client error: %s", e)
            raise PetLibroAPIError(f"Client error during re-login: {e}")

        except Exception as e:
            _LOGGER.error("Re-login attempt failed due to an unexpected error: %s", e)
            raise PetLibroAPIError(f"Unexpected error during re-login: {e}")

class PetLibroAPI:
    """PetLibro API class"""

    APPID = 1
    APPSN = "c35772530d1041699c87fe62348507a8"
    API_URLS = {
        "US": "https://api.us.petlibro.com",
        "CN": "https://api.designlibro.com.cn",
    }

    def __init__(self, session: ClientSession, time_zone: str, region: str, email: str, password: str, token: str | None = None, config_entry=None, hass=None):
        """Initialize."""
        self.session = PetLibroSession(self.API_URLS[region], session, email, password, region, token, time_zone)
        self.region = region
        self.time_zone = time_zone
        self.email = email  # Store email for login/re-login
        self.password = password  # Store password for login/re-login
        self.token = token
        self.config_entry = config_entry
        self.hass = hass

        # Inject the API reference into the session for token saving
        self.session.api = self

        # Load the saved token if available
        if config_entry and "token" in config_entry.data:
            self.token = config_entry.data["token"]
            _LOGGER.debug("Loaded saved token: %s...", self.token[:8] if self.token else "None")

        self._last_api_call_times = {}  # To store last call time per device
        self._cached_responses = {}  # To store cached responses for short periods

        from .pets.api import PL_PetAPI
        self.pets = PL_PetAPI(self.hass, self.config_entry, self.session)

    @staticmethod
    def hash_password(password: str) -> str:
        """Generate the password hash for the API"""
        return md5(password.encode("UTF-8")).hexdigest()

    async def login(self, email: str, password: str) -> str:
        """Login to the API and retrieve the token"""
        _LOGGER.debug("Attempting to log in with email: %s", email)
        
        try:
            # Use the request method with "POST" instead of post()
            data = await self.session.request("POST", "/member/auth/login", json={
                "appId": self.APPID,
                "appSn": self.APPSN,
                "country": self.region,
                "email": email,
                "password": self.hash_password(password),
                "phoneBrand": "",
                "phoneSystemVersion": "",
                "timezone": self.time_zone,
                "thirdId": None,
                "type": None
            })

            if not isinstance(data, dict) or "token" not in data or not isinstance(data["token"], str):
                _LOGGER.error("No token found during login. Response data: %s", data)
                raise PetLibroAPIError("No token found during login.")

            self.session.token = data["token"]
            _LOGGER.debug("Login successful, token: %s...", self.session.token[:8] if self.session.token else "None")
            return self.session.token

        except Exception as e:
            _LOGGER.error("Login failed: %s", e)
            raise PetLibroAPIError(f"Login attempt failed: {e}")

    async def _cached_request(
        self,
        cache_key: str,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        ttl_seconds: int = 10,
    ) -> dict:
        """Make an API request with caching to prevent frequent duplicate calls."""
        now = utcnow()
        last_call_time = self._last_api_call_times.get(cache_key)

        if last_call_time and (now - last_call_time) < timedelta(seconds=ttl_seconds):
            _LOGGER.debug("Skipping %s request, using cached response.", cache_key)
            return self._cached_responses.get(cache_key, {})

        try:
            kwargs: dict[str, Any] = {}
            if json is not None:
                kwargs["json"] = json
            if params is not None:
                kwargs["params"] = params
            if headers is not None:
                kwargs["headers"] = headers

            response = await self.session.request(method, path, **kwargs)

            self._last_api_call_times[cache_key] = now
            self._cached_responses[cache_key] = response
            return response
        except Exception as e:
            _LOGGER.error("Error fetching %s: %s", cache_key, e)
            raise PetLibroAPIError(f"Error fetching {cache_key}: {e}") from e

    async def get_device_real_info(self, device_id: str) -> dict:
        """Fetch real-time information for a device."""
        return await self._cached_request(
            f"{device_id}_realInfo", "POST", "/device/device/realInfo",
            json={"id": device_id, "deviceSn": device_id},
        )

    async def get_device_data_real_info(self, device_id: str) -> dict:
        """Fetch extended real-time data for a device."""
        return await self._cached_request(
            f"{device_id}_dataRealInfo", "POST", "/data/data/realInfo",
            json={"id": device_id, "deviceSn": device_id},
        )

    async def get_device_drink_water(self, device_id: str) -> dict:
        """Fetch today's drinking data for a device."""
        return await self._cached_request(
            f"{device_id}_drinkWater", "POST", "/data/deviceDrinkWater/todayDrinkData",
            json={"id": device_id, "deviceSn": device_id},
        )

    async def get_device_attribute_settings(self, device_id: str) -> dict:
        """Fetch attribute settings for a device."""
        return await self._cached_request(
            f"{device_id}_getAttributeSetting", "POST", "/device/setting/getAttributeSetting",
            json={"id": device_id},
        )

    async def get_device_upgrade(self, device_id: str) -> dict:
        """Fetch firmware upgrade info for a device."""
        return await self._cached_request(
            f"{device_id}_getUpgrade", "POST", "/device/ota/getUpgrade",
            json={"id": device_id},
        )

    async def get_device_base_info(self, device_id: str) -> dict:
        """Fetch base info for a device."""
        return await self._cached_request(
            f"{device_id}_baseInfo", "POST", "/device/device/baseInfo",
            json={"id": device_id, "deviceSn": device_id},
        )

    async def get_device_work_record(self, device_id: str, record_types: list[str] | None = None) -> dict:
        """Fetch work record history for a device."""
        now = utcnow()
        thirty_days_ago = now - timedelta(days=30)
        return await self._cached_request(
            f"{device_id}_work_record", "POST", "/device/workRecord/list",
            json={
                "deviceSn": device_id,
                "startTime": int(thirty_days_ago.timestamp() * 1000),
                "endTime": int(now.timestamp() * 1000),
                "size": 25,
                "type": record_types or ["GRAIN_OUTPUT_SUCCESS"],
            },
        )

    async def get_device_events(self, device_id: str) -> dict:
        """Fetch active events/alerts for a device."""
        return await self._cached_request(
            f"{device_id}_events", "POST", "/data/event/deviceEventsV2",
            json={"id": device_id},
        )

    async def get_default_matrix(self, device_sn: str) -> dict:
        """Fetch the default matrix for a device using a GET request."""
        return await self._cached_request(
            f"{device_sn}_getDefaultMatrix", "GET", "/device/device/getDefaultMatrix",
            params={"deviceSn": device_sn},
            headers={"accept-encoding": "gzip"},
        )

    async def logout(self):
        """Logout of the API and reset the token"""
        await self.session.post("/member/auth/logout")
        self.session.token = None
        _LOGGER.debug("Logout successful, token cleared.")

    async def list_devices(self) -> list[dict]:
        """
        List all account devices.

        :raises PetLibroAPIError: In case of API error
        :return: List of devices
        """
        _LOGGER.debug("Requesting list of devices")
        return await self.session.post("/device/device/list", json={})  # Ensure JSON is passed here

    async def device_base_info(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/device/baseInfo", serial)

    async def device_real_info(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/device/realInfo", serial)

    async def device_data_real_info(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/data/data/realInfo", serial)

    async def device_drink_water(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/data/deviceDrinkWater/todayDrinkData", serial)

    async def device_attribute_settings(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/setting/getAttributeSetting", serial)

    async def device_events(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/data/event/deviceEventsV2", serial)

    async def device_upgrade(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/ota/getUpgrade", serial)

    async def device_grain_status(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/data/grainStatus", serial)

    async def device_feeding_plan_today_new(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/feedingPlan/todayNew", serial)

    async def device_feeding_plan_list(self, serial: str) -> list[dict[str, Any]]:
        return await self.session.post_serial("/device/feedingPlan/list", serial)

    async def device_wet_feeding_plan(self, serial: str) -> dict[str, Any]:
        return await self.session.post_serial("/device/wetFeedingPlan/wetListV3", serial)

    async def device_get_bound_pets(self, device_sn: str) -> list[dict]:
        """Get pets bound to a device."""
        _LOGGER.debug("Requesting pets bound to device sn: %s", device_sn)

        try:
            data = await self.session.post("/device/devicePetRelation/getBoundPets", json={"deviceSn": device_sn})
        except Exception as exc:
            raise PetLibroAPIError("Failed to fetch list of bound pets") from exc

        if data and not isinstance(data, list):
            raise PetLibroAPIError(f"Invalid bound pets response format: {data}")
        
        _LOGGER.debug("Bound pets retrieved successfully")
        return data or []

    # Support for new switch functions
    async def set_feeding_plan(self, serial: str, enable: bool):
        """Set the feeding plan on/off."""
        await self.session.post("/device/setting/updateFeedingPlanSwitch", json={
            "deviceSn": serial,
            "enable": enable
        })

    async def set_child_lock(self, serial: str, enable: bool):
        """Enable or disable the child lock functionality."""
        await self.session.post(
            "/device/setting/updateChildLockSwitch",
            json={"deviceSn": serial, "enable": enable}
        )

    async def set_light_enable(self, serial: str, enable: bool):
        """Enable or disable the light functionality."""
        await self.session.post(
            "/device/setting/updateLightEnableSwitch",
            json={"deviceSn": serial, "enable": enable}
        )

    async def set_light_switch(self, serial: str, enable: bool):
        """Turn the light on or off."""
        await self.session.post("/device/setting/updateLightSwitch", json={
            "deviceSn": serial,
            "enable": enable
        })

    async def set_sound_enable(self, serial: str, enable: bool):
        """Enable or disable the sound functionality."""
        await self.session.post(
            "/device/setting/updateSoundEnableSwitch",
            json={"deviceSn": serial, "enable": enable}
        )

    async def set_maintenance_frequency(self, serial: str, key: str, value: float) -> JSON:
        """Set a maintenance frequency on the device.

        Args:
            serial: Device serial number.
            key: Maintenance type key (e.g. "DESICCANT", "MACHINE_CLEANING", "FILTER").
            value: Frequency in days.
        """
        _LOGGER.debug("Setting maintenance frequency: serial=%s, key=%s, value=%s", serial, key, value)
        try:
            request_id = str(uuid.uuid4()).replace("-", "")
            response = await self.session.post("/device/device/maintenanceFrequencySetting", json={
                "deviceSn": serial,
                "key": key,
                "frequency": value,
                "requestId": request_id,
                "timeout": 5000,
            })
            _LOGGER.debug("Maintenance frequency set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set maintenance frequency for device %s: %s", serial, e)
            raise

    async def set_sound_switch(self, serial: str, enable: bool):
        """Turn the sound on or off."""
        await self.session.post("/device/setting/updateSoundSwitch", json={
            "deviceSn": serial,
            "enable": enable
        })

    async def set_sound_level(self, serial: str, value: float):
        """Set the sound level."""
        _LOGGER.debug("Setting sound level: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/setting/updateVolumeSetting", json={
                "deviceSn": serial,
                "volume": value
            })
            _LOGGER.debug("Sound level set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set sound level for device %s: %s", serial, e)
            raise

    async def set_lid_close_time(self, serial: str, value: float):
        """Set the lid close time."""
        _LOGGER.debug("Setting lid close time: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/setting/updateCoverSetting", json={
                "deviceSn": serial,
                "coverOpenMode": None,
                "coverCloseSpeed": None,
                "closeDoorTimeSec": value
            })
            _LOGGER.debug("Lid close time set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set lid close time for device %s: %s", serial, e)
            raise


    async def set_lid_speed(self, serial: str, value: str):
        """Set the lid speed."""
        _LOGGER.debug("Setting lid speed: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/setting/updateCoverSetting", json={
                "deviceSn": serial,
                "coverOpenMode": None,
                "coverCloseSpeed": value,
                "closeDoorTimeSec": None
            })
            _LOGGER.debug("Lid speed set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set lid speed for device %s: %s", serial, e)
            raise

    async def set_vacuum_mode(self, serial: str, value: str):
        """Set the vacuum mode."""
        _LOGGER.debug("Setting vacuum mode: serial=%s, value=%s", serial, value)
        try:
            # Generate a dynamic request ID for the vacuum mode.
            request_id = str(uuid.uuid4()).replace("-", "")

            response = await self.session.post("/device/device/vacuum", json={
                "deviceSn": serial,
                "vacuumMode": value,
                "requestId": request_id
            })

            # Check if response is already parsed (since response is an integer here)\
            _LOGGER.debug("Vacuum mode successful, returned code: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set water dispensing mode for device %s: %s", serial, e)
            raise


    async def exec_device_command(self, serial: str, action: str):
        """Execute a device command via execCmdService.

        Discovered actions for the Luma Smart Litter Box:
          CLEAN / STOP_CLEAN / SUSPEND_CLEAN / RESTART_CLEAN
          EMPTY / STOP_EMPTY / RESTART_EMPTY
          LEVELING / RESTART_LEVELING
          VACUUM (air purifier)
          OPEN_DOOR / CLOSE_DOOR
          STOP / CANCEL
        """
        _LOGGER.debug("Executing device command: serial=%s, action=%s", serial, action)
        try:
            request_id = str(uuid.uuid4()).replace("-", "")
            response = await self.session.post("/device/device/execCmdService", json={
                "deviceSn": serial,
                "action": action,
                "requestId": request_id,
            })
            _LOGGER.debug("execCmdService(%s) returned: %s", action, response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to exec command %s for device %s: %s", action, serial, e)
            raise

    async def trigger_manual_clean(self, serial: str):
        """Trigger a manual clean cycle on a litter box device."""
        return await self.exec_device_command(serial, "CLEAN")

    async def trigger_empty_waste(self, serial: str):
        """Trigger waste bin emptying on a litter box device."""
        return await self.exec_device_command(serial, "EMPTY")

    async def trigger_level_litter(self, serial: str):
        """Trigger litter leveling on a litter box device."""
        return await self.exec_device_command(serial, "LEVELING")

    async def trigger_stop_device_action(self, serial: str):
        """Stop the current device action."""
        return await self.exec_device_command(serial, "STOP")

    async def trigger_open_door(self, serial: str):
        """Open the litter box door."""
        return await self.exec_device_command(serial, "OPEN_DOOR")

    async def trigger_close_door(self, serial: str):
        """Close the litter box door."""
        return await self.exec_device_command(serial, "CLOSE_DOOR")

    async def trigger_vacuum(self, serial: str):
        """Trigger the air purifier (vacuum) on a litter box device."""
        return await self.exec_device_command(serial, "VACUUM")

    async def set_clean_mode(self, serial: str, clean_mode: str, auto_delay_sec: int = 60):
        """Set the litter box clean mode (AUTO/MANUAL) and auto-delay."""
        _LOGGER.debug("Setting clean mode: serial=%s, mode=%s, delay=%s", serial, clean_mode, auto_delay_sec)
        try:
            response = await self.session.post("/device/setting/updateCleanModeSetting", json={
                "deviceSn": serial,
                "cleanMode": clean_mode,
                "autoDelaySec": auto_delay_sec,
            })
            _LOGGER.debug("Clean mode update returned code: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set clean mode for device %s: %s", serial, e)
            raise

    async def set_deodorization_setting(self, serial: str, mode: str, switch: bool):
        """Update deodorization mode and master switch."""
        _LOGGER.debug("Setting deodorization: serial=%s, mode=%s, switch=%s", serial, mode, switch)
        try:
            response = await self.session.post("/device/setting/updateDeodorizationSetting", json={
                "deviceSn": serial,
                "deodorizationMode": mode,
                "deodorizationModeSwitch": switch,
            })
            _LOGGER.debug("Deodorization setting returned code: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set deodorization for device %s: %s", serial, e)
            raise

    async def set_volume(self, serial: str, volume: int):
        """Set speaker volume (0-100)."""
        _LOGGER.debug("Setting volume: serial=%s, volume=%s", serial, volume)
        try:
            response = await self.session.post("/device/setting/updateVolumeSetting", json={
                "deviceSn": serial,
                "volume": volume,
            })
            _LOGGER.debug("Volume setting returned code: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set volume for device %s: %s", serial, e)
            raise

    async def set_after_deodorization(self, serial: str, switch: bool, duration: int):
        """Set post-use deodorization switch and duration."""
        _LOGGER.debug("Setting after deodorization: serial=%s, switch=%s, duration=%s", serial, switch, duration)
        try:
            response = await self.session.post("/device/setting/updateDeodorizationSetting", json={
                "deviceSn": serial,
                "afterDeodorizationSwitch": switch,
                "durationAfterDeodorization": duration,
            })
            _LOGGER.debug("After deodorization setting returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set after deodorization for device %s: %s", serial, e)
            raise

    async def set_deodorization_wind_speed(self, serial: str, wind_speed: str):
        """Set deodorization wind speed (LOW/MEDIUM/HIGH)."""
        _LOGGER.debug("Setting deodorization wind speed: serial=%s, speed=%s", serial, wind_speed)
        try:
            response = await self.session.post("/device/setting/updateDeodorizationSetting", json={
                "deviceSn": serial,
                "deodorizationWindSpeed": wind_speed,
            })
            _LOGGER.debug("Deodorization wind speed returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set deodorization wind speed for device %s: %s", serial, e)
            raise

    async def set_clean_mode_setting(self, serial: str, clean_mode: str, auto_delay_sec: int, avoid_repeat: bool):
        """Set clean mode with avoid repeat clean option."""
        _LOGGER.debug("Setting clean mode: serial=%s, mode=%s, delay=%s, avoid_repeat=%s", serial, clean_mode, auto_delay_sec, avoid_repeat)
        try:
            response = await self.session.post("/device/setting/updateCleanModeSetting", json={
                "deviceSn": serial,
                "cleanMode": clean_mode,
                "autoDelaySec": auto_delay_sec,
                "avoidRepeatClean": avoid_repeat,
            })
            _LOGGER.debug("Clean mode setting returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set clean mode for device %s: %s", serial, e)
            raise

    async def set_sleep_mode_setting(self, serial: str, enable: bool, auto_clean: bool, deodorization: bool):
        """Set sleep mode sub-settings."""
        _LOGGER.debug("Setting sleep mode: serial=%s, enable=%s, auto_clean=%s, deodorization=%s", serial, enable, auto_clean, deodorization)
        try:
            response = await self.session.post("/device/setting/updateSleepModeSetting", json={
                "deviceSn": serial,
                "enableSleepMode": enable,
                "enableAutoCleanInSleepMode": auto_clean,
                "enableDeodorizationInSleepMode": deodorization,
            })
            _LOGGER.debug("Sleep mode setting returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set sleep mode for device %s: %s", serial, e)
            raise

    async def reset_filter(self, serial: str):
        """Reset the filter replacement timer."""
        _LOGGER.debug("Resetting filter for device: %s", serial)
        try:
            response = await self.session.post("/device/device/filterReset", json={
                "deviceSn": serial,
            })
            _LOGGER.debug("Filter reset returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to reset filter for device %s: %s", serial, e)
            raise

    async def reset_machine_cleaning(self, serial: str):
        """Reset the machine cleaning timer."""
        _LOGGER.debug("Resetting machine cleaning for device: %s", serial)
        try:
            response = await self.session.post("/device/device/machineCleaningReset", json={
                "deviceSn": serial,
            })
            _LOGGER.debug("Machine cleaning reset returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to reset machine cleaning for device %s: %s", serial, e)
            raise

    async def reset_mat(self, serial: str):
        """Reset the mat replacement timer."""
        _LOGGER.debug("Resetting mat for device: %s", serial)
        try:
            response = await self.session.post("/device/device/matReset", json={
                "deviceSn": serial,
            })
            _LOGGER.debug("Mat reset returned: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to reset mat for device %s: %s", serial, e)
            raise

    async def device_potty_today(self, serial: str) -> dict:
        """Fetch today's potty statistics for a device."""
        return await self.session.post_serial("/data/pet/potty/today", serial)

    # Not supported by the dockstream device firmware yet. hoping that maybe it will be in the future, so leaving code here.
    # async def set_water_sensing_delay(self, serial: str, value: float, current_mode: int):
    #     """Set the water sensing delay."""
    #     _LOGGER.debug("Setting water sensing delay duration: serial=%s, value=%s", serial, value)
    #     try:
    #         # Generate a dynamic request ID for water sensing delay.
    #         request_id = str(uuid.uuid4()).replace("-", "")
    #         response = await self.session.post("/device/device/waterModeSetting", json={
    #             "deviceSn": serial,
    #             "requestId": request_id,
    #             "useWaterType": current_mode,
    #             "useWaterInterval": None,
    #             "useWaterDuration": None,
    #             "sensingWaterDuration": value
    #         })
    #         _LOGGER.debug("Water sensing delay set successfully: %s", response)
    #         return response
    #     except Exception as e:
    #         _LOGGER.error("Failed to set water sensing delay for device %s: %s", serial, e)
    #         raise

    async def set_water_low_threshold(self, serial: str, value: float):
        """Set the water low threshold."""
        _LOGGER.debug("Setting water low threshold: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/setting/updateLowWaterSetting", json={
                "deviceSn": serial,
                "lowWater": value,
            })
            _LOGGER.debug("Water low threshold set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set water low threshold for device %s: %s", serial, e)
            raise

    async def set_water_interval(self, serial: str, value: float, current_mode: int, current_duration: float):
        """Set the water interval."""
        _LOGGER.debug("Setting water interval: serial=%s, value=%s", serial, value)
        try:
            # Generate a dynamic request ID for water interval.
            request_id = str(uuid.uuid4()).replace("-", "")
            response = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": current_mode,
                "useWaterInterval": value,
                "useWaterDuration": current_duration
            })
            _LOGGER.debug("Water interval set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set water interval for device %s: %s", serial, e)
            raise

    async def set_water_dispensing_duration(self, serial: str, value: float, current_mode: int, current_interval: float):
        """Set the water interval."""
        _LOGGER.debug("Setting water dispensing duration: serial=%s, value=%s", serial, value)
        try:
            # Generate a dynamic request ID for water dispensing duration.
            request_id = str(uuid.uuid4()).replace("-", "")
            response = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": current_mode,
                "useWaterInterval": current_interval,
                "useWaterDuration": value
            })
            _LOGGER.debug("Water dispensing duration set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set water dispensing duration for device %s: %s", serial, e)
            raise

    async def set_lid_mode(self, serial: str, value: str):
        """Set the lid mode."""
        _LOGGER.debug("Setting lid mode: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/setting/updateCoverSetting", json={
                "deviceSn": serial,
                "coverOpenMode": value,
                "coverCloseSpeed": None,
                "closeDoorTimeSec": None
            })
            _LOGGER.debug("Lid mode set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set lid mode for device %s: %s", serial, e)
            raise

    async def set_water_mode_off(self, serial: str):
        """Off: stop switch ON (True = off)."""
        _LOGGER.debug("set_water_mode_off: serial=%s", serial)
        try:
            resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "waterStopSwitch": True,
            })
            _LOGGER.debug("OFF set successfully: %s", resp)
            return resp
        except Exception as e:
            _LOGGER.error("Failed to set OFF for %s: %s", serial, e)
            raise

    async def set_water_mode_on(self, serial: str):
        """ON: stop switch OFF (False = on)."""
        _LOGGER.debug("set_water_mode_on: serial=%s", serial)
        try:
            resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "waterStopSwitch": False,
            })
            _LOGGER.debug("ON set successfully: %s", resp)
            return resp
        except Exception as e:
            _LOGGER.error("Failed to set ON for %s: %s", serial, e)
            raise

    async def set_water_mode_radar_near(self, serial: str, interval: int, duration: int | None = None, *, currently_off: bool | None = None):
        """Sensed (Near): set radar to NearTrigger, then useWaterType=2."""
        _LOGGER.debug("set_water_mode_radar_near: serial=%s", serial)
        try:
            if currently_off:
                await self.set_water_mode_on(serial)

            radar_resp = await self.session.post("/device/setting/updateRadarSetting", json={
                "deviceSn": serial,
                "radarSensingLevel": "NearTrigger",
            })
            _LOGGER.debug("Radar Near updated: %s", radar_resp)

            request_id = str(uuid.uuid4()).replace("-", "")
            mode_resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": 2,             # sensed
                "useWaterInterval": interval,
                "useWaterDuration": duration,
            })
            _LOGGER.debug("Sensed mode (Near) set: %s", mode_resp)
            return mode_resp
        except Exception as e:
            _LOGGER.error("Failed to set Sensed Near for %s: %s", serial, e)
            raise

    async def set_water_mode_radar_far(self, serial: str, interval: int, duration: int | None = None, *, currently_off: bool | None = None):
        """Sensed (Far): set radar to FarTrigger, then useWaterType=2."""
        _LOGGER.debug("set_water_mode_radar_far: serial=%s", serial)
        try:
            if currently_off:
                await self.set_water_mode_on(serial)

            radar_resp = await self.session.post("/device/setting/updateRadarSetting", json={
                "deviceSn": serial,
                "radarSensingLevel": "FarTrigger",
            })
            _LOGGER.debug("Radar Near updated: %s", radar_resp)

            request_id = str(uuid.uuid4()).replace("-", "")
            mode_resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": 2,             # sensed
                "useWaterInterval": interval,
                "useWaterDuration": duration,
            })
            _LOGGER.debug("Sensed mode (Far) set: %s", mode_resp)
            return mode_resp
        except Exception as e:
            _LOGGER.error("Failed to set Sensed Far for %s: %s", serial, e)
            raise

    async def set_water_mode_intermittent(self, serial: str, interval: int, duration: int | None = None, *, currently_off: bool | None = None):
        """Intermittent (Scheduled): useWaterType=1.

        If currently_off=True, the device is turned on first.
        """
        _LOGGER.debug("set_water_mode_intermittent: serial=%s", serial)
        try:
            if currently_off:
                await self.set_water_mode_on(serial)

            request_id = str(uuid.uuid4()).replace("-", "")
            resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": 1,             # intermittent
                "useWaterInterval": interval,
                "useWaterDuration": duration,
            })
            _LOGGER.debug("Intermittent set successfully: %s", resp)
            return resp
        except Exception as e:
            _LOGGER.error("Failed to set Intermittent for %s: %s", serial, e)
            raise

    async def set_water_mode_constant(self, serial: str, interval: int, duration: int | None = None, *, currently_off: bool | None = None):
        """Constant: useWaterType=0.

        If currently_off=True, the device is turned on first.
        """
        _LOGGER.debug("set_water_mode_constant: serial=%s", serial)
        try:
            if currently_off:
                await self.set_water_mode_on(serial)

            request_id = str(uuid.uuid4()).replace("-", "")
            resp = await self.session.post("/device/device/waterModeSetting", json={
                "deviceSn": serial,
                "requestId": request_id,
                "useWaterType": 0,             # constant
                "useWaterInterval": interval,
                "useWaterDuration": duration,
            })
            _LOGGER.debug("Constant set successfully: %s", resp)
            return resp
        except Exception as e:
            _LOGGER.error("Failed to set Constant for %s: %s", serial, e)
            raise

    async def set_display_icon(self, serial: str, value: float):
        """Set the display icon."""
        _LOGGER.debug("Setting display icon: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/device/displayMatrix", json={
                "deviceSn": serial,
                "screenDisplayId": value,
                "screenDisplayMatrix": None,
                "screenLetter": None
            })
            _LOGGER.debug("Display icon set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set display icon for device %s: %s", serial, e)
            raise

    async def set_display_text(self, serial: str, value: str):
        """Set the display text."""
        _LOGGER.debug("Setting display text: serial=%s, value=%s", serial, value)
        try:
            response = await self.session.post("/device/device/displayMatrix", json={
                "deviceSn": serial,
                "screenDisplayId": None,
                "screenDisplayMatrix": None,
                "screenLetter": value
            })
            _LOGGER.debug("Display text set successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to set display text for device %s: %s", serial, e)
            raise

    async def set_manual_feed(self, serial: str, feed_value=1) -> JSON: # Provide a default argument for the feed value just in case this works differently with other feeders
        """Trigger manual feeding for a specific device."""
        _LOGGER.debug("Triggering manual feeding for device with serial: %s", serial)
        try:
            # Generate a dynamic request ID for the manual feeding
            request_id = str(uuid.uuid4()).replace("-", "")

            # Send the POST request to trigger manual feeding
            response = await self.session.post("/device/device/manualFeeding", json={
                "deviceSn": serial,
                "grainNum": int(feed_value),  # Number of grains dispensed, make sure it's an integer and not a float
                "requestId": request_id  # Use dynamic request ID
            })

            # Check if response is already parsed (since response is an integer here)
            if isinstance(response, int):
                _LOGGER.debug("Manual feeding successful, returned code: %s", response)
                return response
            
            # Response is the parsed dict from session.post — already validated by session layer
            _LOGGER.debug("Manual feeding response: %s", response)
            return response

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger manual feeding for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering manual feeding: {err}")

    async def set_manual_feed_now(self, serial: str, plate: int):
        """Trigger manual feed now for a specific device. This opens the food bowl door."""
        _LOGGER.debug("Triggering manual feed now for device with serial: %s", serial)
        
        try:
            # Send the POST request to trigger manual feeding
            await self.session.post("/device/wetFeedingPlan/manualFeedNow", json={
                "deviceSn": serial,
                "plate": plate 
            })

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger manual feed now for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering manual feed now: {err}")
        
    async def set_stop_feed_now(self, serial: str, manual_feed_id: int):
        """Trigger stop feed now for a specific device. This closes the food bowl door."""
        _LOGGER.debug("Triggering stop feed now for device with serial: %s", serial)
        
        try:
            # Send the POST request to trigger stop feeding
            await self.session.post("/device/wetFeedingPlan/stopFeedNow", json={
                "deviceSn": serial,
                "feedId": manual_feed_id
            })

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger stop feed now for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering stop feed now: {err}")
        
    async def set_rotate_food_bowl(self, serial: str) -> int:
        """Trigger rotate food bowl for a specific device. This rotates the bowls counter-clockwise by one bowl."""
        _LOGGER.debug("Triggering rotate food bowl for device with serial: %s", serial)
        
        try:
            # Send the POST request to trigger plate position change
            response = await self.session.post("/device/wetFeedingPlan/platePositionChange", json={
                "deviceSn": serial,
                # The plate ID doesn't matter here - the device will always rotate one bowl counter-clockwise regardless of what the plate ID is.
                "plate": 1
            })

            _LOGGER.debug("Rotate food bowl successful, new plate position: %s", response)
            return response

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger rotate food bowl for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering rotate food bowl: {err}")
        
    async def set_feed_audio(self, serial: str):
        """Trigger feed audio for a specific device."""
        _LOGGER.debug("Triggering feed audio for device with serial: %s", serial)
        
        try:
            # Send the POST request to trigger feed audio
            await self.session.post("/device/wetFeedingPlan/feedAudio", json={
                "deviceSn": serial
            })

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger feed audio for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering feed audio: {err}")

    async def set_desiccant_reset(self, serial: str) -> JSON:
        """Trigger desiccant reset for a specific device."""
        _LOGGER.debug("Triggering desiccant reset for device with serial: %s", serial)

        try:
            # Generate a dynamic request ID for the desiccant reset
            request_id = str(uuid.uuid4()).replace("-", "")

            # Send the POST request to trigger desiccant reset
            response = await self.session.post("/device/device/desiccantReset", json={
                "deviceSn": serial,
                "requestId": request_id,  # Use dynamic request ID
                "timeout": 5000
            })

            # Granary smart feeder quirk: response can be None on success
            if response is None or response == {}:
                _LOGGER.debug("Desiccant reset set successfully, got no extra data")
                return

            # Check if response is already parsed (since response is an integer here)
            if isinstance(response, int):
                _LOGGER.debug("Desiccant reset set successfully, returned code: %s", response)
                return response
            
            # Response is the parsed dict from session.post — already validated by session layer
            _LOGGER.debug("Desiccant reset set successfully: %s", response)
            return response

            return response

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger desiccant reset for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering desiccant reset: {err}")

    async def trigger_firmware_upgrade(self, serial: str, job_item_id: str):
        """Trigger the firmware upgrade for the device."""
        _LOGGER.debug("Triggering firmware upgrade: serial=%s, jobItemId=%s", serial, job_item_id)
        try:
            response = await self.session.post("/device/ota/doUpgrade", json={
                "deviceSn": serial,
                "jobItemId": job_item_id
            })
            _LOGGER.debug("Firmware upgrade triggered successfully: %s", response)
            return response
        except Exception as e:
            _LOGGER.error("Failed to trigger firmware upgrade for device %s: %s", serial, e)
            raise

    async def set_cleaning_reset(self, serial: str) -> JSON:
        """Trigger machine cleaning reset for a specific device."""
        _LOGGER.debug("Triggering machine cleaning reset for device with serial: %s", serial)
        
        try:
            # Generate a dynamic request ID for the machine cleaning reset
            request_id = str(uuid.uuid4()).replace("-", "")

            # Send the POST request to trigger machine cleaning reset
            response = await self.session.post("/device/device/machineCleaningReset", json={
                "deviceSn": serial,
                "requestId": request_id,  # Use dynamic request ID
                "timeout": 5000
            })

            # Check if response is already parsed (since response is an integer here)
            if isinstance(response, int):
                _LOGGER.debug("Machine cleaning reset set successfully, returned code: %s", response)
                return response
            
            # Response is the parsed dict from session.post — already validated by session layer
            _LOGGER.debug("Machine cleaning reset response: %s", response)
            return response

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger machine cleaning reset for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering machine cleaning reset: {err}")

    async def set_filter_reset(self, serial: str) -> JSON:
        """Trigger machine cleaning reset for a specific device."""
        _LOGGER.debug("Triggering filter reset for device with serial: %s", serial)
        
        try:
            # Generate a dynamic request ID for the machine cleaning reset
            request_id = str(uuid.uuid4()).replace("-", "")

            # Send the POST request to trigger machine cleaning reset
            response = await self.session.post("/device/device/filterReset", json={
                "deviceSn": serial,
                "requestId": request_id,  # Use dynamic request ID
                "timeout": 5000
            })

            # Check if response is already parsed (since response is an integer here)
            if isinstance(response, int):
                _LOGGER.debug("Filter reset set successfully, returned code: %s", response)
                return response
            
            # Response is the parsed dict from session.post — already validated by session layer
            _LOGGER.debug("Filter reset response: %s", response)
            return response

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to trigger filter reset for device %s: %s", serial, err)
            raise PetLibroAPIError(f"Error triggering filter reset: {err}")

    async def set_manual_lid_open(self, serial: str):
        """Trigger manual lid opening for a specific device."""
        await self.session.post("/device/device/doorStateChange", json={
            "deviceSn": serial,
            "barnDoorState": True,
            "timeout": 8000
        })
    
    async def set_display_on(self, serial: str):
        """Trigger turn display on"""
        await self.session.post("/device/setting/updateDisplayMatrixSetting", json={
            "deviceSn": serial,
            "screenDisplayAgingType": 1,
            "screenDisplayStartTime": None,
            "screenDisplayEndTime": None,
            "screenDisplaySwitch": True
        })
    
    async def set_display_off(self, serial: str):
        """Trigger turn display off"""
        await self.session.post("/device/setting/updateDisplayMatrixSetting", json={
            "deviceSn": serial,
            "screenDisplayAgingType": 1,
            "screenDisplayStartTime": None,
            "screenDisplayEndTime": None,
            "screenDisplaySwitch": False
        })

    async def set_light_on(self, serial: str):
        """Trigger turn indicator on"""
        await self.session.post("/device/setting/updateLightingSetting", json={
            "deviceSn": serial,
            "lightAgingType": 1,
            "lightingStartTime": None,
            "lightingEndTime": None,
            "lightSwitch": True
        })
    
    async def set_light_off(self, serial: str):
        """Trigger turn indicator off"""
        await self.session.post("/device/setting/updateLightingSetting", json={
            "deviceSn": serial,
            "lightAgingType": 1,
            "lightingStartTime": None,
            "lightingEndTime": None,
            "lightSwitch": False
        })

    async def set_sound_on(self, serial: str):
        """Trigger turn sound on"""
        await self.session.post("/device/setting/updateSoundSetting", json={
            "deviceSn": serial,
            "soundSwitch": True,
            "soundAgingType": 1,
            "soundStartTime": None,
            "soundEndTime": None
        })
    
    async def set_sound_off(self, serial: str):
        """Trigger turn sound off"""
        await self.session.post("/device/setting/updateSoundSetting", json={
            "deviceSn": serial,
            "soundSwitch": False,
            "soundAgingType": 1,
            "soundStartTime": None,
            "soundEndTime": None
        })

    async def set_sleep_on(self, serial: str):
        """Trigger turn sleep mode on"""
        await self.session.post("/device/setting/updateSleepModeSetting", json={
            "deviceSn": serial,
            "enableSleepMode": True,
            "sleepEndTime": None,
            "sleepStartTime": None
        })
    
    async def set_sleep_off(self, serial: str):
        """Trigger turn sleep mode off"""
        await self.session.post("/device/setting/updateSleepModeSetting", json={
            "deviceSn": serial,
            "enableSleepMode": False,
            "sleepEndTime": None,
            "sleepStartTime": None
        })

    async def set_reposition_schedule(self, serial: str, plan: dict, template_name: str):
        """Reposition the schedule"""
        _LOGGER.debug("Triggering reposition schedule for device with serial: %s", serial)
        await self.session.post("/device/wetFeedingPlan/reposition", json={
            "deviceSn": serial,
            "plan": plan,
            "templateName": template_name,
        })

    async def member_info(self) -> dict[str, Any]:
        """Request Petlibro Account data."""
        _LOGGER.debug("Requesting member information")

        try:
            data = await self.session.post("/member/member/info", json={})
        except Exception as exc:
            _LOGGER.exception("Failed to fetch member information")
            raise PetLibroAPIError("Failed to fetch member information") from exc

        if not isinstance(data, dict):
            raise PetLibroAPIError(f"Invalid member info response format: {data}")

        if not data.get("email"):
            _LOGGER.warning("Member info response missing email: %s", data)

        _LOGGER.debug("Member info retrieved successfully")
        return data

    async def unread_quantity(self) -> dict[str, int]:
        """Fetch unread device-message and notification counts.

        Returns: {"device": <int>, "notify": <int>}
        """
        try:
            data = await self.session.get("/device/msg/unreadQuantity")
        except Exception as exc:
            raise PetLibroAPIError("Failed to fetch unread quantity") from exc
        return data if isinstance(data, dict) else {}

    async def share_pop_list(self) -> list[dict[str, Any]]:
        """Fetch pending device-share invitations for the current account."""
        try:
            data = await self.session.post(
                "/device/deviceShare/sharePopList", json={"shareId": None}
            )
        except Exception as exc:
            raise PetLibroAPIError("Failed to fetch share invitations") from exc
        return data if isinstance(data, list) else []

    async def generate_mqtt_cert(self, member_id: int | str) -> dict[str, str | int]:
        """Request a fresh client certificate for MQTT mutual-TLS.

        Generates an RSA-2048 keypair locally, builds a CSR with subject
        `CN=DesignLibro, serialNumber=<member_id>`, posts it to
        ``/member/certificate/generate``, then acknowledges the cert via
        ``/member/certificate/confirm``.

        Returns a dict with ``key_pem``, ``cert_pem``, ``serial_number`` and
        ``expire_time_ms`` (epoch milliseconds).
        """
        # Local imports keep cryptography off the hot path for users who never
        # touch MQTT; HA core already ships with cryptography, no extra dep.
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        def _build() -> tuple[str, str]:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            csr = (
                x509.CertificateSigningRequestBuilder()
                .subject_name(
                    x509.Name(
                        [
                            x509.NameAttribute(NameOID.COMMON_NAME, "DesignLibro"),
                            x509.NameAttribute(NameOID.SERIAL_NUMBER, str(member_id)),
                        ]
                    )
                )
                .sign(key, hashes.SHA256())
            )
            return (
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ).decode(),
                csr.public_bytes(serialization.Encoding.PEM).decode(),
            )

        # CPU-bound RSA generation runs in executor to avoid blocking the loop
        loop = asyncio.get_running_loop()
        key_pem, csr_pem = await loop.run_in_executor(None, _build)

        gen = await self.session.post(
            "/member/certificate/generate", json={"csr": csr_pem}
        )
        if not isinstance(gen, dict) or "certificate" not in gen:
            raise PetLibroAPIError(f"Unexpected /certificate/generate response: {gen}")

        serial = gen["serialNumber"]
        await self.session.post(
            "/member/certificate/confirm", json={"serialNumber": serial}
        )

        return {
            "key_pem": key_pem,
            "cert_pem": gen["certificate"],
            "serial_number": serial,
            "expire_time_ms": gen.get("expireTime"),
        }

    async def get_mqtt_ca_cert(self) -> str:
        """Fetch the PetlibroCA chain PEM used to verify the MQTT broker.

        The endpoint returns ``{"pem": <download-url>, "caCertificate": <PEM string>,
        "crt": <download-url>, "expireTime": <epoch_ms>}`` — we want the inline PEM.
        """
        try:
            data = await self.session.get("/member/certificate/ca")
        except Exception as exc:
            raise PetLibroAPIError("Failed to fetch MQTT CA certificate") from exc
        if isinstance(data, dict) and isinstance(data.get("caCertificate"), str):
            return data["caCertificate"]
        raise PetLibroAPIError(f"Unexpected /certificate/ca response: {data}")

    async def member_update_info(
        self, update_info: dict[str, Any], update_setting: dict[str, Any]
    ) -> bool:
        """Update Petlibro account settings."""
        if not (update_info or update_setting):
            _LOGGER.debug("No member settings provided for update; skipping request.")
            return True  # Nothing to update, considered successful.

        _LOGGER.debug(
            "Attempting to update member settings. Info: %s, Settings: %s",
            update_info,
            update_setting,
        )

        async def _post_update(endpoint: str, payload: dict[str, Any]) -> bool:
            """Helper to send settings and handle logging."""
            try:
                result = await self.session.post(endpoint, json=payload or {})
            except Exception:
                _LOGGER.exception("Failed to update via %s", endpoint)
                return False
            _LOGGER.debug("%s response (should be None): %s", endpoint, result)
            return True

        success = True
        if update_info:
            success &= await _post_update("/member/member/updateInfo", update_info)
        if update_setting:
            success &= await _post_update("/member/member/updateSetting", update_setting)

        if success:
            _LOGGER.debug("Updating member settings successful.")
        else:
            _LOGGER.error("One or more member setting updates failed.")

        return success

    async def feeding_plan_toggle(self, serial: str, plan: dict) -> None:
        """Enable or disable an existing feeding plan via the /enable endpoint."""
        await self.session.post("/device/feedingPlan/enable", json={
            "deviceSn": serial,
            "planId": plan["id"],
            "enable": plan["enable"],
        })

    async def feeding_plan_delete(self, serial: str, plan_id: int) -> None:
        """Permanently remove a feeding plan."""
        await self.session.post("/device/feedingPlan/remove", json={
            "deviceSn": serial,
            "planId": plan_id,
        })

    async def feeding_plan_add(self, serial: str, plan: dict) -> None:
        """Create a new feeding plan."""
        await self.session.post("/device/feedingPlan/add", json={
            "id": 0,
            "deviceSn": serial,
            "executionTime": plan.get("executionTime"),
            "repeatDay": plan.get("repeatDay", "[]"),
            "label": plan.get("label", ""),
            "enable": True,
            "enableAudio": plan.get("enableAudio", False),
            "audioTimes": 2,
            "grainNum": plan.get("grainNum"),
            "petIds": [],
        })

    async def feeding_plan_today_skip(self, serial: str, plan_id: int, skip: bool) -> None:
        """Skip or un-skip a single feeding plan event for today only."""
        await self.session.post("/device/feedingPlan/enableTodaySingle", json={
            "deviceSn": serial,
            "planId": plan_id,
            "enable": not skip,
        })
        
    async def feeding_plan_update(self, serial: str, plan: dict) -> None:
        """Enable, disable, or edit an existing feeding plan."""
        await self.session.post("/device/feedingPlan/update", json={
            "id": plan["id"],
            "deviceSn": serial,
            "executionTime": plan.get("executionTime"),
            "repeatDay": plan.get("repeatDay", "[]"),
            "label": plan.get("label", ""),
            "enable": plan.get("enable", True),
            "enableAudio": plan.get("enableAudio", False),
            "audioTimes": plan.get("audioTimes", 2),
            "grainNum": plan.get("grainNum"),
            "petIds": [],
        })

    async def feeding_plan_today_all(self, serial: str, enable: bool) -> None:
        """Enable or disable ALL feeding plan events for today."""
        await self.session.post("/device/feedingPlan/enableTodayAll", json={
            "deviceSn": serial,
            "enable": enable,
        })

