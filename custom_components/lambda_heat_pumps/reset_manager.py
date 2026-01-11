"""
Lambda Heat Pumps - Reset Manager
Centralized reset logic for all sensor types and periods.
"""

import logging
from datetime import datetime
from typing import Callable
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.dispatcher import async_dispatcher_send

# Import signal constants from automations
from .automations import (
    SIGNAL_RESET_DAILY,
    SIGNAL_RESET_2H,
    SIGNAL_RESET_4H,
    SIGNAL_RESET_MONTHLY,
    SIGNAL_RESET_YEARLY,
    _update_yesterday_sensors_async,
)

_LOGGER = logging.getLogger(__name__)


class ResetManager:
    """Zentrale Reset-Logik für alle Sensor-Typen und Perioden."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        """Initialize ResetManager."""
        self.hass = hass
        self._entry_id = entry_id
        self._unsub_timers = {}

    def setup_reset_automations(self):
        """Richte Reset-Automatisierungen ein."""
        _LOGGER.info("Setting up reset automations for entry %s", self._entry_id)

        # Daily Reset
        @callback
        def reset_daily(now: datetime) -> None:
            """Reset daily sensors at midnight and update yesterday sensors."""
            _LOGGER.info("Resetting daily sensors at midnight")

            # 1. Erst Yesterday-Sensoren auf aktuelle Daily-Werte setzen (asynchron)
            self.hass.async_create_task(
                _update_yesterday_sensors_async(self.hass, self._entry_id)
            )

            # 2. Dann Daily-Sensoren auf 0 zurücksetzen (asynchron)
            self.hass.async_create_task(
                self._send_reset_signal_async(SIGNAL_RESET_DAILY)
            )

        self._unsub_timers["daily"] = async_track_time_change(
            self.hass, reset_daily, hour=0, minute=0, second=0
        )

        # 2h Reset (alle 2 Stunden)
        @callback
        def reset_2h(now: datetime) -> None:
            """Reset 2h sensors every 2 hours."""
            _LOGGER.info("Resetting 2h sensors (all modes)")

            # Sende Signal an alle 2H-Sensoren (asynchron)
            self.hass.async_create_task(self._send_reset_signal_async(SIGNAL_RESET_2H))

        self._unsub_timers["2h"] = async_track_time_change(
            self.hass,
            reset_2h,
            hour=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
            minute=0,
            second=0,
        )

        # 4h Reset (alle 4 Stunden)
        @callback
        def reset_4h(now: datetime) -> None:
            """Reset 4h sensors every 4 hours."""
            _LOGGER.info("Resetting 4h sensors (all modes)")

            # Sende Signal an alle 4H-Sensoren (asynchron)
            self.hass.async_create_task(self._send_reset_signal_async(SIGNAL_RESET_4H))

        self._unsub_timers["4h"] = async_track_time_change(
            self.hass, reset_4h, hour=[0, 4, 8, 12, 16, 20], minute=0, second=0
        )

        # Monthly Reset (1. des Monats)
        @callback
        def reset_monthly(now: datetime) -> None:
            """Reset monthly sensors on the 1st of each month."""
            if now.day == 1:
                _LOGGER.info("Resetting monthly sensors (cycling, energy) on 1st of month")

                # Sende Signal an alle Monthly-Sensoren (asynchron)
                self.hass.async_create_task(
                    self._send_reset_signal_async(SIGNAL_RESET_MONTHLY)
                )

        self._unsub_timers["monthly"] = async_track_time_change(
            self.hass, reset_monthly, hour=0, minute=0, second=0
        )

        # Yearly Reset (1. Januar)
        @callback
        def reset_yearly(now: datetime) -> None:
            """Reset yearly sensors on January 1st."""
            if now.month == 1 and now.day == 1:
                _LOGGER.info("Resetting yearly sensors on January 1st")

                # Sende Signal an alle Yearly-Sensoren (asynchron)
                self.hass.async_create_task(
                    self._send_reset_signal_async(SIGNAL_RESET_YEARLY)
                )

        self._unsub_timers["yearly"] = async_track_time_change(
            self.hass, reset_yearly, hour=0, minute=0, second=0
        )

        _LOGGER.info("Reset automations set up successfully")

    async def _send_reset_signal_async(self, signal: str) -> None:
        """Send reset signal asynchronously."""
        _LOGGER.debug(f"Sending reset signal {signal} for entry {self._entry_id}")
        async_dispatcher_send(self.hass, signal, self._entry_id)

    def cleanup(self):
        """Cleanup Reset-Automatisierungen."""
        _LOGGER.info("Cleaning up reset automations for entry %s", self._entry_id)

        for period, listener in self._unsub_timers.items():
            if listener:
                listener()
                _LOGGER.debug("Cleaned up %s listener for entry %s", period, self._entry_id)

        self._unsub_timers = {}

