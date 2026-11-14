"""Repairs for the Lambda Heat Pumps integration.

Two are fixable from the repair itself: the restart a newly written dashboard
needs before Lovelace shows it, and adding further heating circuits to a cockpit
written before the heating circuit card existed (which rewrites it).
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import ISSUE_DASHBOARD_HEATING_CIRCUITS, ISSUE_DASHBOARD_RESTART


class RestartRequiredFlow(RepairsFlow):
    """Ask, then restart Home Assistant."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Go straight to the confirmation."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Restart once the user confirms."""
        if user_input is not None:
            # Closing the issue first: the restart does not come back here.
            result = self.async_create_entry(data={})
            await self.hass.services.async_call("homeassistant", "restart")
            return result
        return self.async_show_form(step_id="confirm")


class HeatingCircuitsFlow(RepairsFlow):
    """Ask, then write the cockpit again with the further heating circuits."""

    def __init__(self, entry_id: str | None) -> None:
        """Remember which controller's dashboard this is."""
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Go straight to the confirmation."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Rewrite the dashboard once the user confirms."""
        if user_input is not None:
            entry = (
                self.hass.config_entries.async_get_entry(self._entry_id)
                if self._entry_id
                else None
            )
            if entry is not None and getattr(entry, "runtime_data", None) is not None:
                from .dashboard import async_regenerate_dashboard

                await async_regenerate_dashboard(self.hass, entry)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm")


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """The flow that fixes an issue."""
    if issue_id == ISSUE_DASHBOARD_RESTART:
        return RestartRequiredFlow()
    if issue_id == ISSUE_DASHBOARD_HEATING_CIRCUITS:
        return HeatingCircuitsFlow((data or {}).get("entry_id"))
    raise ValueError(f"No fix flow for {issue_id}")
