"""Diagnostics support for PETLIBRO."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .hub import PetLibroHub

TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    "api_token",
    "token",
    "serial",
    "mac",
    # MQTT client credentials are per-account secrets.
    "mqtt_cert_pem",
    "mqtt_key_pem",
    "mqtt_ca_pem",
    "client_id",
    "member_topic",
}

# Field names in raw PETLIBRO payloads that identify the account, the device or
# the home network, or that carry credentials. Field *names* are kept so the
# dump can still be used to map new fields; only the values are redacted.
RAW_TO_REDACT = TO_REDACT | {
    "deviceSn",
    "sn",
    "id",
    "deviceId",
    "memberId",
    "ownerId",
    "shareId",
    "petId",
    "account",
    "phone",
    "nickname",
    "cameraId",
    "cameraAuthInfo",
    "userToken",
    "appTutkUrl",
    "wifiSsid",
    "ssid",
    "bssid",
    "ip",
    "avatar",
    "icon",
    "url",
    "imageUrl",
    "videoUrl",
    "thumbnailUrl",
    "rfid",
    "rfidCode",
}

# Record lists grow without bound and repeat the same shape; a few entries are
# enough to see the fields.
_MAX_LIST_ITEMS = 3


def _scrub(value: Any, secrets: set[str]) -> Any:
    """Truncate long lists and blank out any string containing a known identifier."""
    if isinstance(value, dict):
        return {key: _scrub(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item, secrets) for item in value[:_MAX_LIST_ITEMS]]
    if isinstance(value, str) and any(secret in value for secret in secrets):
        return "**REDACTED**"
    return value


def _raw_payload(data: Any, secrets: set[str]) -> Any:
    """Return a raw API payload that is safe to attach to an issue."""
    if not isinstance(data, dict):
        return None
    return async_redact_data(_scrub(data, secrets), RAW_TO_REDACT)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub: PetLibroHub = entry.runtime_data

    # Values that must never leave the instance, wherever they appear in a payload.
    secrets = {
        str(value)
        for device in hub.devices.values()
        for value in (device.serial, device.mac)
        if value and len(str(value)) >= 6
    }
    for candidate in (entry.data.get(CONF_EMAIL), getattr(hub.member, "email", None)):
        if candidate:
            secrets.add(str(candidate))

    devices_data = []
    for device in hub.devices.values():
        devices_data.append(
            {
                "name": device.name,
                "model": device.model,
                "serial": device.serial,
                "mac": device.mac,
                "software_version": getattr(device, "software_version", None),
                "hardware_version": getattr(device, "hardware_version", None),
                "online": getattr(device, "online", None),
                "type": type(device).__name__,
                "raw": _raw_payload(getattr(device, "_data", None), secrets),
            }
        )

    member_data = None
    if hub.member:
        member_data = {
            "email": getattr(hub.member, "email", None),
            "nickname": getattr(hub.member, "nickname", None),
            "feedUnitType": str(getattr(hub.member, "feedUnitType", None)),
            "waterUnitType": str(getattr(hub.member, "waterUnitType", None)),
            "weightUnitType": str(getattr(hub.member, "weightUnitType", None)),
        }

    pets_data = []
    for pet in hub.pets.values():
        pets_data.append(
            {
                "name": getattr(pet, "name", None),
                "id": getattr(pet, "id", None),
                "type": type(pet).__name__,
                "raw": _raw_payload(getattr(pet, "_data", None), secrets),
            }

        )

    return async_redact_data(
        {
            "entry": {
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "devices": devices_data,
            "member": member_data,
            "pets": pets_data,
            "device_count": len(hub.devices),
            "pet_count": len(hub.pets),
            "mqtt": hub.mqtt.diagnostics if hub.mqtt else {"status": "not started"},
            "poll_interval_seconds": (
                hub.coordinator.update_interval.total_seconds()
                if hub.coordinator.update_interval
                else None
            ),
        },
        TO_REDACT,
    )
