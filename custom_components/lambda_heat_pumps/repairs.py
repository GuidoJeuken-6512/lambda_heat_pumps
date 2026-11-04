"""Repairs for the Lambda Heat Pumps integration.

Only one is fixable from the repair itself: the restart a newly written
dashboard needs before Lovelace shows it. Confirming restarts Home Assistant.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import ISSUE_DASHBOARD_RESTART


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


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """The flow that fixes an issue; only the dashboard restart has one."""
    if issue_id == ISSUE_DASHBOARD_RESTART:
        return RestartRequiredFlow()
    raise ValueError(f"No fix flow for {issue_id}")
