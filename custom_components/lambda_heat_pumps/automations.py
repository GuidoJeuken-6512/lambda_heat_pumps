"""
Lambda Heat Pumps - Cycling Automations
Handles cycling counter resets and automation setup.
"""

import logging
from homeassistant.core import HomeAssistant

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
# Signal für Hourly-Reset (jede volle Stunde)
SIGNAL_RESET_HOURLY = "lambda_heat_pumps_reset_hourly"


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

    # WICHTIG: cycling_entities ist ueber unique_id geschluesselt (stabil), nicht ueber
    # entity_id (kann von der realen, registrierten entity_id abweichen - siehe
    # increment_cycling_counter()). Die tatsaechliche entity_id fuer den State-Zugriff
    # kommt deshalb von der Entity-Instanz selbst (entity.entity_id, zur Laufzeit immer
    # der reale Wert); fuer die Yesterday-Zuordnung wird weiterhin der stabile
    # unique_id-Schluessel verwendet.
    for unique_id, entity in cycling_entities.items():
        if not unique_id.endswith("_daily"):
            continue
        entity_id = getattr(entity, "entity_id", None)
        if not entity_id:
            continue
        parts = unique_id.split("_")
        if len(parts) >= 4:
            yesterday_unique_id = unique_id.replace("_daily", "_yesterday")

            daily_state = hass.states.get(entity_id)
            if daily_state and daily_state.state not in ("unknown", "unavailable"):
                try:
                    daily_value = int(float(daily_state.state))

                    yesterday_entity = cycling_entities.get(yesterday_unique_id)
                    if yesterday_entity and hasattr(yesterday_entity, "set_cycling_value"):
                        await yesterday_entity.set_cycling_value(daily_value)
                        _LOGGER.info(
                            "Yesterday sensor %s updated to %d from %s",
                            getattr(yesterday_entity, "entity_id", yesterday_unique_id),
                            daily_value, entity_id,
                        )
                    else:
                        _LOGGER.warning(
                            "Yesterday entity %s not found", yesterday_unique_id
                        )
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(
                        "Could not update yesterday sensor %s: %s",
                        yesterday_unique_id, e,
                    )
