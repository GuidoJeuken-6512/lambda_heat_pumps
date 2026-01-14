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


# setup_cycling_automations() wurde durch ResetManager ersetzt
# Diese Funktion wird nicht mehr verwendet - ResetManager übernimmt die Logik


# _send_reset_signal_async() wurde durch ResetManager._send_reset_signal_async() ersetzt
# Diese Funktion wird nicht mehr verwendet - ResetManager übernimmt die Logik

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


# cleanup_cycling_automations() wurde durch ResetManager.cleanup() ersetzt
# Diese Funktion wird nicht mehr verwendet - ResetManager übernimmt die Logik
