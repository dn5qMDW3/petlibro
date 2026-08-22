"""Base class for PETLIBRO litter boxes."""

from logging import getLogger
from typing import Any

from . import Device

_LOGGER = getLogger(__name__)


class LitterBox(Device):
    """Shared behaviour for every PETLIBRO litter box.

    Cleaning schedules live behind their own endpoints rather than in
    ``getAttributeSetting``, so they are fetched separately and cached on the
    device under ``cleanPlans``.
    """

    async def refresh_clean_plans(self) -> list[dict[str, Any]]:
        """Fetch the cleaning schedules and cache them on the device."""
        try:
            plans = await self.api.get_clean_plans(self.serial)
        except Exception:
            _LOGGER.debug("Clean plans unavailable for %s", self.serial, exc_info=True)
            return self.clean_plans
        self._data["cleanPlans"] = plans
        return plans

    @property
    def clean_plans(self) -> list[dict[str, Any]]:
        """Cleaning schedules: ``planId``, ``executionTime``, ``repeatDay``, ``enable``."""
        value = self._data.get("cleanPlans")
        return value if isinstance(value, list) else []

    @property
    def clean_plan_count(self) -> int:
        """How many cleaning schedules exist."""
        return len(self.clean_plans)

    @staticmethod
    def format_repeat_days(days) -> str:
        """Render a day list the way the API expects it, e.g. ``"[1,2,3]"``.

        Days are 1 (Monday) through 7 (Sunday); an empty list means one-shot.
        """
        if isinstance(days, str):
            return days
        return "[" + ",".join(str(int(d)) for d in (days or [])) + "]"

    async def add_clean_plan(self, execution_time: str, days, enable: bool = True) -> None:
        """Create a cleaning schedule (``execution_time`` is ``"HH:MM"``)."""
        await self.api.add_clean_plan(
            self.serial, execution_time[:5], self.format_repeat_days(days), enable
        )
        await self.refresh_clean_plans()

    async def update_clean_plan(
        self, plan_id, execution_time: str, days, enable: bool = True
    ) -> None:
        """Modify an existing cleaning schedule."""
        await self.api.update_clean_plan(
            self.serial, plan_id, execution_time[:5], self.format_repeat_days(days), enable
        )
        await self.refresh_clean_plans()

    async def delete_clean_plan(self, plan_id) -> None:
        """Remove a cleaning schedule."""
        await self.api.delete_clean_plan(self.serial, plan_id)
        await self.refresh_clean_plans()
