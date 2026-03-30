"""Diagnostics support for PETLIBRO."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .hub import PetLibroHub

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, "api_token", "token", "serial", "mac"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub: PetLibroHub = entry.runtime_data

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
        },
        TO_REDACT,
    )
