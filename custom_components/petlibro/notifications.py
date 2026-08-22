"""Notification toggles exposed as Home Assistant switches.

``/device/setting/getNoticeSetting`` returns the union of every notification
flag across all PETLIBRO product families, so a fountain's response still
carries feeder-only keys. Rather than surface all ~60 of them on every device,
each toggle below declares which device families it belongs to.

Each entry pairs the field name in the *read* response with the endpoint and
payload shape of the matching *write*, both recovered from the 1.8.95 client.
The write payloads are deliberately not uniform — the vendor uses
``enableNotice``, ``switchVal`` and bespoke keys depending on the endpoint.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field as dc_field
from typing import Any

from .devices import Device
from .devices.feeders.feeder import Feeder
from .devices.fountains.fountain import Fountain
from .devices.litterboxes.litter_box import LitterBox


@dataclass(frozen=True)
class NoticeToggle:
    """One notification switch."""

    key: str
    """Entity key / translation key (snake_case)."""

    field: str
    """Field name in the getNoticeSetting response."""

    endpoint: str
    """Endpoint that writes this flag."""

    name: str
    """Fallback English name."""

    families: tuple[type[Device], ...]
    """Device base classes this toggle applies to."""

    payload: Callable[[str, bool, dict[str, Any]], dict[str, Any]] = dc_field(
        default=lambda serial, value, current: {
            "deviceSn": serial,
            "enableNotice": value,
        }
    )
    """Builds the write body from (serial, new value, current notice settings)."""


def _enable_notice(serial: str, value: bool, current: dict[str, Any]) -> dict[str, Any]:
    return {"deviceSn": serial, "enableNotice": value}


def _switch_val(serial: str, value: bool, current: dict[str, Any]) -> dict[str, Any]:
    return {"deviceSn": serial, "switchVal": value}


def _offline(serial: str, value: bool, current: dict[str, Any]) -> dict[str, Any]:
    # This one also carries the delivery channel; preserve whatever is set.
    return {
        "deviceSn": serial,
        "enableNotice": value,
        "noticeType": current.get("offlineNoticeType", 3),
    }


def _named(field: str) -> Callable[[str, bool, dict[str, Any]], dict[str, Any]]:
    """Payload builder for endpoints that want the flag under its own name.

    Most notification endpoints take a generic ``enableNotice``/``switchVal``,
    but a few (the drinking-habit ones) reject that and require the same key
    the read response uses.
    """

    def build(serial: str, value: bool, current: dict[str, Any]) -> dict[str, Any]:
        return {"deviceSn": serial, field: value}

    return build


def _feeding(serial: str, value: bool, current: dict[str, Any]) -> dict[str, Any]:
    return {
        "deviceSn": serial,
        "enableFeedingPlanNotice": value,
        "enableFeedingPlanAdvanceNotice": bool(
            current.get("enableFeedingPlanAdvanceNotice")
        ),
        "feedingPlanAdvanceNoticeTime": current.get("feedingPlanAdvanceNoticeTime", 5),
    }


ALL_DEVICES = (Device,)
FEEDERS = (Feeder,)
FOUNTAINS = (Fountain,)
LITTER_BOXES = (LitterBox,)

NOTICE_TOGGLES: tuple[NoticeToggle, ...] = (
    # --- every device ------------------------------------------------------
    NoticeToggle(
        key="notice_offline",
        field="enableOfflineNotice",
        endpoint="/device/setting/updateOfflineNoticeSetting",
        name="Offline alerts",
        families=ALL_DEVICES,
        payload=_offline,
    ),
    NoticeToggle(
        key="notice_low_battery",
        field="enableLowBatteryNotice",
        endpoint="/device/setting/updateLowBatteryNoticeSetting",
        name="Low battery alerts",
        families=ALL_DEVICES,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_power_change",
        field="enablePowerChangeNotice",
        endpoint="/device/setting/updatePowerChangeNoticeSetting",
        name="Power source change alerts",
        families=ALL_DEVICES,
        payload=_enable_notice,
    ),
    # --- feeders -----------------------------------------------------------
    NoticeToggle(
        key="notice_feeding_plan",
        field="enableFeedingPlanNotice",
        endpoint="/device/setting/updateFeedingNoticeSetting",
        name="Feeding plan alerts",
        families=FEEDERS,
        payload=_feeding,
    ),
    NoticeToggle(
        key="notice_surplus_grain",
        field="enableSurplusGrainNotice",
        endpoint="/device/setting/updateSurplusGrainNoticeSetting",
        name="Low food alerts",
        families=FEEDERS,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_grain_outlet_blocked",
        field="enableGrainOutletBlockedNotice",
        endpoint="/device/setting/updateGrainOutletBlockedNoticeSetting",
        name="Food outlet blocked alerts",
        families=FEEDERS,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_desiccant",
        field="enableDesiccantNotice",
        endpoint="/device/setting/updateDesiccantNoticeSetting",
        name="Desiccant replacement alerts",
        families=FEEDERS,
        payload=_enable_notice,
    ),
    # --- fountains ---------------------------------------------------------
    NoticeToggle(
        key="notice_drinking_water",
        field="enableDrinkingWaterNotice",
        endpoint="/device/setting/enableDrinkingWaterNotice",
        name="Drinking alerts",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_low_water",
        field="enableLowWaterNotice",
        endpoint="/device/setting/enableLowWaterNotice",
        name="Low water alerts",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_filter_replacement",
        field="enableFilterReplacementReminder",
        endpoint="/device/setting/enableFilterReplacementReminder",
        name="Filter replacement reminder",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_machine_cleaning",
        field="enableMachineCleaningReminder",
        endpoint="/device/setting/enableMachineCleaningReminder",
        name="Cleaning reminder",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_tank_overturned",
        field="enableTankOverturnedNotice",
        endpoint="/device/setting/enableTankOverturnedNotice",
        name="Tank overturned alerts",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_drink_goal_reached",
        field="enableReachDrinkWaterAlertNotice",
        endpoint="/device/setting/enableReachDrinkingWaterAlertNotice",
        name="Drinking goal reached alerts",
        families=FOUNTAINS,
        payload=_switch_val,
    ),
    NoticeToggle(
        key="notice_drink_trend",
        field="drinkTrendNoticeSwitch",
        endpoint="/device/setting/updateDrinkTrendNoticeSetting",
        name="Drinking trend alerts",
        families=FOUNTAINS,
        payload=_named("drinkTrendNoticeSwitch"),
    ),
    NoticeToggle(
        key="notice_no_drink",
        field="noDrinkNoticeSwitch",
        endpoint="/device/setting/updateNoDrinkNoticeSetting",
        name="Not drinking alerts",
        families=FOUNTAINS,
        payload=_named("noDrinkNoticeSwitch"),
    ),
    # --- litter boxes ------------------------------------------------------
    NoticeToggle(
        key="notice_vacuum_success",
        field="enableVacuumSuccessNotice",
        endpoint="/device/setting/updateVacuumSuccessNoticeSetting",
        name="Cleaning completed alerts",
        families=LITTER_BOXES,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_vacuum_failed",
        field="enableVacuumFailedNotice",
        endpoint="/device/setting/updateVacuumFailedNoticeSetting",
        name="Cleaning failed alerts",
        families=LITTER_BOXES,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_motion_detection",
        field="enableMotionDetectionNotice",
        endpoint="/device/setting/updateMotionDetectionNoticeSetting",
        name="Motion detection alerts",
        families=LITTER_BOXES,
        payload=_enable_notice,
    ),
    NoticeToggle(
        key="notice_sound_detection",
        field="enableSoundDetectionNotice",
        endpoint="/device/setting/updateSoundDetectionNoticeSetting",
        name="Sound detection alerts",
        families=LITTER_BOXES,
        payload=_enable_notice,
    ),
)


def toggles_for(device: Device) -> list[NoticeToggle]:
    """Toggles that apply to a device *and* are present in its settings.

    The presence check keeps unsupported flags off a device even when it shares
    a base class with one that does support them — the server simply omits (or
    nulls) the field for products that lack the feature.
    """
    notice = device.notice_setting
    return [
        toggle
        for toggle in NOTICE_TOGGLES
        if isinstance(device, toggle.families) and notice.get(toggle.field) is not None
    ]
