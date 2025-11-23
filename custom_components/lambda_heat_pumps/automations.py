"""
Lambda Heat Pumps - Cycling Automations
Handles cycling counter resets and automation setup.
"""

import logging
from datetime import datetime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

# Signal für Daily-Reset (täglich um Mitternacht)
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
# Signal für 2H-Reset (alle 2 Stunden)
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h"
# Signal für 4H-Reset (alle 4 Stunden)
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"
# Signal für Monthly-Reset (1. des Monats um Mitternacht)
SIGNAL_RESET_MONTHLY = "lambda_heat_pumps_reset_monthly"
# Signal für Yearly-Reset (1. Januar um Mitternacht)
SIGNAL_RESET_YEARLY = "lambda_heat_pumps_reset_yearly"


def setup_cycling_automations(hass: HomeAssistant, entry_id: str) -> None:
    """Set up cycling-related automations for the integration."""
    _LOGGER.info("Setting up cycling automations for entry %s", entry_id)

    # Täglicher Reset der Daily-Sensoren um Mitternacht
    @callback
    def reset_daily_sensors(now: datetime) -> None:
        """Reset daily sensors at midnight and update yesterday sensors."""
        _LOGGER.info("Resetting daily cycling sensors at midnight")

        # 1. Erst Yesterday-Sensoren auf aktuelle Daily-Werte setzen (asynchron)
        hass.async_create_task(_update_yesterday_sensors_async(hass, entry_id))
        
        # 2. Dann Daily-Sensoren auf 0 zurücksetzen (asynchron)
        hass.async_create_task(_send_reset_signal_async(hass, SIGNAL_RESET_DAILY, entry_id))

    # 2-Stunden Reset der 2H-Sensoren
    @callback
    def reset_2h_sensors(now: datetime) -> None:
        """Reset 2h sensors every 2 hours."""
        _LOGGER.info("Resetting 2h cycling sensors (all modes)")

        # Sende Signal an alle 2H-Sensoren (asynchron)
        hass.async_create_task(
            _send_reset_signal_async(hass, SIGNAL_RESET_2H, entry_id)
        )

    # 4-Stunden Reset der 4H-Sensoren
    @callback
    def reset_4h_sensors(now: datetime) -> None:
        """Reset 4h sensors every 4 hours."""
        _LOGGER.info("Resetting 4h cycling sensors (all modes)")

        # Sende Signal an alle 4H-Sensoren (asynchron)
        hass.async_create_task(
            _send_reset_signal_async(hass, SIGNAL_RESET_4H, entry_id)
        )

    # Monatlicher Reset der Monthly-Sensoren (1. des Monats um Mitternacht)
    @callback
    def reset_monthly_sensors(now: datetime) -> None:
        """Reset monthly sensors on the 1st of each month."""
        # Prüfe ob es der 1. des Monats ist
        if now.day == 1:
            _LOGGER.info(
                "Resetting monthly sensors (cycling, energy) on 1st of month"
            )
            # Sende Signal an alle Monthly-Sensoren (asynchron)
            hass.async_create_task(
                _send_reset_signal_async(hass, SIGNAL_RESET_MONTHLY, entry_id)
            )

    # Jährlicher Reset der Yearly-Sensoren (1. Januar um Mitternacht)
    @callback
    def reset_yearly_sensors(now: datetime) -> None:
        """Reset yearly sensors on January 1st."""
        # Prüfe ob es der 1. Januar ist
        if now.month == 1 and now.day == 1:
            _LOGGER.info("Resetting yearly energy sensors on January 1st")
            # Sende Signal an alle Yearly-Sensoren (asynchron)
            hass.async_create_task(_send_reset_signal_async(hass, SIGNAL_RESET_YEARLY, entry_id))

    # Registriere die Zeit-basierten Automatisierungen
    # async_track_time_change ist KEINE Coroutine, daher KEIN await!
    daily_listener = async_track_time_change(
        hass, reset_daily_sensors, hour=0, minute=0, second=0
    )
    
    # 2h-Listener: alle 2 Stunden (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
    two_hour_listener = async_track_time_change(
        hass, 
        reset_2h_sensors, 
        hour=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22], 
        minute=0, 
        second=0
    )
    
    # 4h-Listener: alle 4 Stunden (0, 4, 8, 12, 16, 20)
    four_hour_listener = async_track_time_change(
        hass, 
        reset_4h_sensors, 
        hour=[0, 4, 8, 12, 16, 20], 
        minute=0, 
        second=0
    )
    
    # Monatlicher Reset der Monthly-Sensoren (1. des Monats um Mitternacht)
    # Verwende async_track_time_change mit hour=0, minute=0, second=0
    # und prüfe in der Callback-Funktion ob es der 1. des Monats ist
    monthly_listener = async_track_time_change(
        hass, reset_monthly_sensors, hour=0, minute=0, second=0
    )
    
    # Jährlicher Reset der Yearly-Sensoren (1. Januar um Mitternacht)
    # Verwende async_track_time_change mit hour=0, minute=0, second=0
    # und prüfe in der Callback-Funktion ob es der 1. Januar ist
    yearly_listener = async_track_time_change(
        hass, reset_yearly_sensors, hour=0, minute=0, second=0
    )

    # Speichere die Listener für späteres Cleanup
    if "lambda_heat_pumps" not in hass.data:
        hass.data["lambda_heat_pumps"] = {}
    if entry_id not in hass.data["lambda_heat_pumps"]:
        hass.data["lambda_heat_pumps"][entry_id] = {}
    hass.data["lambda_heat_pumps"][entry_id]["daily_listener"] = daily_listener
    hass.data["lambda_heat_pumps"][entry_id]["two_hour_listener"] = two_hour_listener
    hass.data["lambda_heat_pumps"][entry_id]["four_hour_listener"] = four_hour_listener
    hass.data["lambda_heat_pumps"][entry_id]["monthly_listener"] = monthly_listener
    hass.data["lambda_heat_pumps"][entry_id]["yearly_listener"] = yearly_listener

    _LOGGER.info("Cycling automations set up successfully")


async def _send_reset_signal_async(hass: HomeAssistant, signal: str, entry_id: str) -> None:
    """Send reset signal asynchronously."""
    _LOGGER.info(f"Sending reset signal {signal} for entry {entry_id}")
    async_dispatcher_send(hass, signal, entry_id)

async def _update_yesterday_sensors_async(hass: HomeAssistant, entry_id: str) -> None:
    """Update yesterday sensors with current daily values before reset (async)."""
    _LOGGER.info("Updating yesterday sensors with current daily values")
    
    # Hole alle Cycling-Entities für diese Entry
    if ("lambda_heat_pumps" not in hass.data or 
        entry_id not in hass.data["lambda_heat_pumps"] or
        "cycling_entities" not in hass.data["lambda_heat_pumps"][entry_id]):
        _LOGGER.warning("No cycling entities found for entry %s", entry_id)
        return
    
    cycling_entities = hass.data["lambda_heat_pumps"][entry_id]["cycling_entities"]
    
    # Für jeden Daily-Sensor den entsprechenden Yesterday-Sensor aktualisieren
    for entity_id, entity in cycling_entities.items():
        if entity_id.endswith("_daily"):
            # Extrahiere den Modus aus der Entity-ID
            # z.B. "sensor.eu08l_hp1_heating_cycling_daily" -> "heating"
            parts = entity_id.split("_")
            if len(parts) >= 4:
                # mode = parts[-3]  # "heating" - nicht mehr benötigt
                # hp_part = parts[-4]  # "hp1" - nicht mehr benötigt
                
                # Erstelle Yesterday-Entity-ID
                yesterday_entity_id = entity_id.replace("_daily", "_yesterday")
                
                # Hole den aktuellen Daily-Wert
                daily_state = hass.states.get(entity_id)
                if daily_state and daily_state.state not in ("unknown", "unavailable"):
                    try:
                        daily_value = int(float(daily_state.state))
                        
                        # Setze Yesterday-Sensor auf Daily-Wert
                        yesterday_entity = cycling_entities.get(yesterday_entity_id)
                        if yesterday_entity and hasattr(yesterday_entity, "set_cycling_value"):
                            await yesterday_entity.set_cycling_value(daily_value)
                            _LOGGER.info(
                                f"Yesterday sensor {yesterday_entity_id} updated to {daily_value} from {entity_id}"
                            )
                        else:
                            _LOGGER.warning(f"Yesterday entity {yesterday_entity_id} not found")
                    except (ValueError, TypeError) as e:
                        _LOGGER.warning(f"Could not update yesterday sensor {yesterday_entity_id}: {e}")


def _update_yesterday_sensors(hass: HomeAssistant, entry_id: str) -> None:
    """Update yesterday sensors with current daily values before reset (sync, deprecated)."""
    _LOGGER.warning("Using deprecated sync _update_yesterday_sensors, use async version")
    # Diese Funktion wird nicht mehr verwendet, aber für Rückwärtskompatibilität behalten


def cleanup_cycling_automations(hass: HomeAssistant, entry_id: str) -> None:
    """Clean up cycling-related automations."""
    _LOGGER.info("Cleaning up cycling automations for entry %s", entry_id)

    # Cleanup der Listener
    if (
        "lambda_heat_pumps" in hass.data
        and entry_id in hass.data["lambda_heat_pumps"]
    ):
        entry_data = hass.data["lambda_heat_pumps"][entry_id]
        
        # Cleanup Daily-Listener
        if "daily_listener" in entry_data:
            listener = entry_data["daily_listener"]
            if listener:
                listener()
                _LOGGER.info("Cleaned up daily listener for entry %s", entry_id)
            del entry_data["daily_listener"]
        
        # Cleanup 2h-Listener
        if "two_hour_listener" in entry_data:
            listener = entry_data["two_hour_listener"]
            if listener:
                listener()
                _LOGGER.info("Cleaned up 2h listener for entry %s", entry_id)
            del entry_data["two_hour_listener"]
        
        # Cleanup 4h-Listener
        if "four_hour_listener" in entry_data:
            listener = entry_data["four_hour_listener"]
            if listener:
                listener()
                _LOGGER.info("Cleaned up 4h listener for entry %s", entry_id)
            del entry_data["four_hour_listener"]
        
        # Cleanup Monthly-Listener
        if "monthly_listener" in entry_data:
            listener = entry_data["monthly_listener"]
            if listener:
                listener()
                _LOGGER.info("Cleaned up monthly listener for entry %s", entry_id)
            del entry_data["monthly_listener"]
        
        # Cleanup Yearly-Listener
        if "yearly_listener" in entry_data:
            listener = entry_data["yearly_listener"]
            if listener:
                listener()
                _LOGGER.info("Cleaned up yearly listener for entry %s", entry_id)
            del entry_data["yearly_listener"]
