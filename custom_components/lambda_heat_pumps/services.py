"""Services for Lambda WP integration."""

from __future__ import annotations
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_ROOM_TEMPERATURE_ENTITY,
    DEFAULT_WRITE_INTERVAL,
    CONF_PV_POWER_SENSOR_ENTITY,
)
from .modbus_utils import async_read_holding_registers, async_write_registers

# Konstanten für Zustandsarten definieren
STATE_UNAVAILABLE = "unavailable"
STATE_UNKNOWN = "unknown"

_LOGGER = logging.getLogger(__name__)


def should_start_scheduler(hass: HomeAssistant) -> bool:
    """Prüfe ob mindestens eine Option aktiv ist."""
    lambda_entries = hass.data.get(DOMAIN, {})
    for entry_id, entry_data in lambda_entries.items():
        config_entry = hass.config_entries.async_get_entry(entry_id)
        if config_entry and config_entry.options:
            if (config_entry.options.get("room_thermostat_control", False) or 
                config_entry.options.get("pv_surplus", False)):
                return True
    return False


# Service Schema
UPDATE_ROOM_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.string,
    }
)

# Service Schema für read_modbus_register
READ_MODBUS_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required("register_address"): vol.All(
            vol.Coerce(int),
            vol.Range(min=0, max=65535),
        ),
    }
)

# Service Schema für write_modbus_register
WRITE_MODBUS_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required("register_address"): vol.All(
            vol.Coerce(int),
            vol.Range(min=0, max=65535),
        ),
        vol.Required("value"): vol.All(
            vol.Coerce(int),
            vol.Range(min=-32768, max=65535),
        ),
    }
)


async def _handle_update_room_temperature(
    hass: HomeAssistant, call: ServiceCall
) -> None:
    """Handle room temperature update service call."""
    # Hole alle Lambda-Integrationen
    lambda_entries = hass.data.get(DOMAIN, {})
    _LOGGER.debug(
        "[Service] Lambda entries: %s",
        list(lambda_entries.keys()),
    )
    if not lambda_entries:
        _LOGGER.error(
            "No Lambda WP integrations found",
        )
        return

    # Optional spezifisches Entity_ID zur Einschränkung
    target_entity_id = call.data.get(ATTR_ENTITY_ID)
    _LOGGER.debug(
        "[Service] ServiceCall ATTR_ENTITY_ID: %s",
        target_entity_id,
    )

    for entry_id, entry_data in lambda_entries.items():
        await _process_room_temperature_entry(
            hass, entry_id, entry_data, target_entity_id
        )


async def _process_room_temperature_entry(
    hass: HomeAssistant, entry_id: str, entry_data: dict, target_entity_id: str
) -> None:
    """Process room temperature update for a specific entry."""
    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or not config_entry.options:
        _LOGGER.debug(
            "No config entry or options for entry_id %s",
            entry_id,
        )
        return

    _LOGGER.debug(
        "[Service] Options for entry_id %s: %s",
        entry_id,
        config_entry.options,
    )

    # Prüfe, ob Raumthermostat aktiviert ist
    if not config_entry.options.get("room_thermostat_control", False):
        _LOGGER.debug(
            "Room thermostat control not enabled for entry_id %s",
            entry_id,
        )
        return

    # Anzahl Heizkreise ermitteln
    num_hc = config_entry.data.get("num_hc", 1)
    _LOGGER.debug(
        "[Service] num_hc for entry_id %s: %s",
        entry_id,
        num_hc,
    )

    # Wenn eine spezifische Entity-ID angegeben wurde
    # und nicht übereinstimmt, überspringe
    if target_entity_id and target_entity_id != entry_id:
        _LOGGER.debug(
            "Skipping entry_id %s due to ATTR_ENTITY_ID filter",
            entry_id,
        )
        return

    # Hole Coordinator für gemeinsame Nutzung
    coordinator = entry_data.get("coordinator")
    if not coordinator or not coordinator.client:
        _LOGGER.error(
            "Coordinator or Modbus client not available for entry_id %s",
            entry_id,
        )
        return
    
    # Check if coordinator client is connected
    # Lambda WP hält Verbindung 60 Sekunden offen - nur bei echten Problemen überspringen
    if not hasattr(coordinator.client, 'connected') or not coordinator.client.connected:
        _LOGGER.info("Modbus client not connected for entry_id %s, skipping operation", entry_id)
        return

    # Für jeden Heizkreis prüfen und aktualisieren
    for hc_idx in range(1, num_hc + 1):
        await _update_heating_circuit_temperature(
            hass, config_entry, coordinator, hc_idx, entry_id, entry_data
        )


async def _update_heating_circuit_temperature(
    hass: HomeAssistant,
    config_entry,
    coordinator,
    hc_idx: int,
    entry_id: str,
    entry_data: dict,
) -> None:
    """Update temperature for a specific heating circuit."""
    entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
    room_temp_entity_id = config_entry.options.get(entity_key)
    _LOGGER.debug(
        "[Service] Prüfe Heizkreis %s: entity_key=%s, room_temp_entity_id=%s",
        hc_idx,
        entity_key,
        room_temp_entity_id,
    )

    if not room_temp_entity_id:
        _LOGGER.error(
            "No room temperature entity selected for heating circuit %s in entry_id %s",
            hc_idx,
            entry_id,
        )
        return

    # Holen der Temperatur vom Sensor
    state = hass.states.get(room_temp_entity_id)
    _LOGGER.debug(
        "State for %s: %s",
        room_temp_entity_id,
        state,
    )

    if state is None or state.state in (
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
        "",
    ):
        _LOGGER.warning(
            "Room temperature entity %s is not available for "
            "heating circuit %s (state: %s)",
            room_temp_entity_id,
            hc_idx,
            state.state if state else None,
        )
        return

    try:
        temperature = float(state.state)
        raw_value = int(temperature * 10)
        # Registeradresse: 5004, 5104, 5204, ...
        register_address = 5004 + (hc_idx - 1) * 100

        _LOGGER.info(
            "[Service] Schreibe Modbus-Register %s mit Wert %s "
            "(Temperatur: %s°C) für Heizkreis %s, entry_id %s",
            register_address,
            raw_value,
            temperature,
            hc_idx,
            entry_id,
        )

        result = await async_write_registers(
            coordinator.client,
            register_address,
            [raw_value],
            entry_data.get("slave_id", 1),
        )

        if result.isError():
            _LOGGER.error(
                "Failed to write room temperature: %s",
                result,
            )

    except (ValueError, TypeError) as ex:
        _LOGGER.error(
            "Unable to convert temperature from %s for heating circuit %s: %s",
            room_temp_entity_id,
            hc_idx,
            ex,
        )
    except Exception as ex:
        _LOGGER.error(
            "Error updating room temperature for heating circuit %s: %s",
            hc_idx,
            ex,
        )


async def _handle_read_modbus_register(hass: HomeAssistant, call: ServiceCall) -> dict:
    """Handle read Modbus register service call."""
    lambda_entries = hass.data.get(DOMAIN, {})
    if not lambda_entries:
        _LOGGER.error(
            "No Lambda WP integrations found",
        )
        return {"error": "No Lambda WP integrations found"}

    register_address = call.data.get("register_address")

    for entry_id, entry_data in lambda_entries.items():
        coordinator = entry_data.get("coordinator")
        if not coordinator or not coordinator.client:
            _LOGGER.error(
                "Coordinator or Modbus client not available for entry_id %s",
                entry_id,
            )
            continue

        try:
            result = await async_read_holding_registers(
                coordinator.client,
                register_address,
                1,
            )
            if result.isError():
                _LOGGER.error(
                    "Failed to read Modbus register: %s",
                    result,
                )
                return {"error": str(result)}
            else:
                value = result.registers[0]
                _LOGGER.info(
                    "Read Modbus register %s: %s",
                    register_address,
                    value,
                )
                return {"value": value}
        except Exception as ex:
            _LOGGER.error(
                "Error reading Modbus register: %s",
                ex,
            )
            return {"error": str(ex)}
    return {"error": "No valid coordinator found"}


async def _handle_write_modbus_register(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle write Modbus register service call."""
    register_address = call.data.get("register_address")
    value = call.data.get("value")

    _LOGGER.debug(
        "Service call `write_modbus_register` - Address: %s, Value: %s",
        register_address,
        value,
    )

    lambda_entries = hass.data.get(DOMAIN, {})
    if not lambda_entries:
        _LOGGER.error("No Lambda WP integrations found")
        return

    for entry_id, entry_data in lambda_entries.items():
        coordinator = entry_data.get("coordinator")
        if not coordinator or not coordinator.client:
            _LOGGER.error(
                "Coordinator or Modbus client not available for entry_id %s",
                entry_id,
            )
            continue

        try:
            result = await async_write_registers(
                coordinator.client,
                register_address,
                [value],
                entry_data.get("slave_id", 1),
            )
            if result.isError():
                _LOGGER.error(
                    "Failed to write Modbus register: %s",
                    result,
                )
            else:
                _LOGGER.info(
                    "Wrote Modbus register %s with value %s",
                    register_address,
                    value,
                )
        except Exception as ex:
            _LOGGER.error(
                "Error writing Modbus register: %s",
                ex,
            )


async def _handle_write_room_and_pv(hass: HomeAssistant) -> None:
    """
    Write room temperature and PV surplus to Modbus registers
    for all entries.
    """
    lambda_entries = hass.data.get(DOMAIN, {})
    if not lambda_entries:
        _LOGGER.info("No Lambda WP integrations found yet, skipping write operation")
        return

    # Prüfe ob mindestens eine Option aktiv ist
    if not should_start_scheduler(hass):
        _LOGGER.debug("No service options are active, skipping write operation")
        return

    # Create a copy of the dictionary to avoid "dictionary changed size during iteration"
    entries_copy = dict(lambda_entries)
    for entry_id, entry_data in entries_copy.items():
        await _write_room_and_pv_for_entry(hass, entry_id, entry_data)


async def _write_room_and_pv_for_entry(
    hass: HomeAssistant, entry_id: str, entry_data: dict
) -> None:
    """Write room temperature and PV surplus for a specific entry."""
    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or not config_entry.options:
        return

    coordinator = entry_data.get("coordinator")
    if not coordinator or not coordinator.client:
        _LOGGER.error(
            "Coordinator or Modbus client not available for entry_id %s",
            entry_id,
        )
        return
    
    # Check if coordinator client is connected
    # Lambda WP hält Verbindung 60 Sekunden offen - nur bei echten Problemen überspringen
    if not hasattr(coordinator.client, 'connected') or not coordinator.client.connected:
        _LOGGER.info("Modbus client not connected for entry_id %s, skipping operation", entry_id)
        return

    # Debug: Log current options
    room_thermostat_control = config_entry.options.get("room_thermostat_control", False)
    pv_surplus = config_entry.options.get("pv_surplus", False)
    _LOGGER.info("Entry %s options: room_thermostat_control=%s, pv_surplus=%s", 
                 entry_id, room_thermostat_control, pv_surplus)

    # Prüfe ob mindestens eine Option für diese Entry aktiv ist
    if not room_thermostat_control and not pv_surplus:
        _LOGGER.debug("No service options are active for entry %s, skipping write operation", entry_id)
        return
    
    # Raumthermostat schreiben
    if room_thermostat_control:
        _LOGGER.info("Writing room temperatures for entry %s", entry_id)
        await _write_room_temperatures(
            hass, config_entry, coordinator, entry_id, entry_data
        )

    # PV-Überschuss schreiben
    if pv_surplus:
        _LOGGER.info("Writing PV surplus for entry %s", entry_id)
        await _write_pv_surplus(hass, config_entry, coordinator, entry_id, entry_data)


async def _write_room_temperatures(
    hass: HomeAssistant, config_entry, coordinator, entry_id: str, entry_data: dict
) -> None:
    """Write room temperatures for all heating circuits."""
    num_hc = config_entry.data.get("num_hc", 1)
    for hc_idx in range(1, num_hc + 1):
        entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
        room_temp_entity_id = config_entry.options.get(entity_key)
        if not room_temp_entity_id:
            continue

        state = hass.states.get(room_temp_entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            continue

        try:
            temperature = float(state.state)
            raw_value = int(temperature * 10)
            register_address = 5004 + (hc_idx - 1) * 100
            _LOGGER.info(
                "[Scheduled] Writing room temperature to "
                "register %s: %s (%s°C) for HC %s",
                register_address,
                raw_value,
                temperature,
                hc_idx,
            )
            await async_write_registers(
                coordinator.client,
                register_address,
                [raw_value],
                entry_data.get("slave_id", 1),
            )
        except Exception as ex:
            _LOGGER.error(
                "Error writing room temperature for HC %d: %s",
                hc_idx,
                ex,
            )


async def _write_pv_surplus(
    hass: HomeAssistant, config_entry, coordinator, entry_id: str, entry_data: dict
) -> None:
    """Write PV surplus to Modbus register."""
    entity_id = config_entry.options.get(CONF_PV_POWER_SENSOR_ENTITY)
    if not entity_id:
        return

    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return

    try:
        power_value = float(state.state)
        unit = state.attributes.get("unit_of_measurement", "")
        if unit == "kW":
            power_value *= 1000  # in W

        # Determine surplus mode
        surplus_mode = config_entry.options.get("pv_surplus_mode", "pos")
        if surplus_mode in ("entry", "pos"):
            # UINT16: only positive values allowed
            raw_value = max(0, int(power_value))
            write_type = "UINT16"
        elif surplus_mode == "neg":
            # INT16: allow negative values, encode as 2's complement
            from .utils import clamp_to_int16

            raw_value = clamp_to_int16(power_value, context="PV surplus") & 0xFFFF
            write_type = "INT16"
        else:
            # fallback: treat as UINT16
            raw_value = max(0, int(power_value))
            write_type = "UINT16 (fallback)"

        _LOGGER.info(
            "PV-surplus gesendet: Value nativ %s %s, value %s W (Register: %s, Mode: %s)",
            state.state,
            unit,
            raw_value,
            102,
            write_type,
        )

        # Check if coordinator client is connected
        # Lambda WP hält Verbindung 60 Sekunden offen - nur bei echten Problemen überspringen
        if not coordinator.client or not hasattr(coordinator.client, 'connected') or not coordinator.client.connected:
            _LOGGER.debug("Modbus client not connected, skipping PV surplus write")
            return

        await async_write_registers(
            coordinator.client,
            102,  # register_address for PV surplus
            [raw_value],
            entry_data.get("slave_id", 1),
        )
    except Exception as ex:
        _LOGGER.error("Error writing PV surplus: %s", ex)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Lambda WP services."""
    _LOGGER.info("Setting up Lambda WP services...")

    # Check if services are already set up and stop them first
    if "_lambda_service_callbacks" in hass.data:
        _LOGGER.info("Services already exist, stopping old services first...")
        await async_unload_services(hass)

    # Speichere die Unsubscribe-Funktionen pro Entry,
    # um sie später entfernen zu können
    unsub_update_callbacks = {}
    
    # Store callbacks in hass.data for cleanup
    hass.data["_lambda_service_callbacks"] = unsub_update_callbacks

    async def async_update_room_temperature(call: ServiceCall) -> None:
        """Update room temperature from the selected sensor to Modbus register."""
        await _handle_update_room_temperature(hass, call)

    async def async_read_modbus_register(call: ServiceCall) -> dict:
        """Read a value from a Modbus register of the Lambda heat pump."""
        return await _handle_read_modbus_register(hass, call)

    async def async_write_modbus_register(call: ServiceCall) -> None:
        """Write a value to a Modbus register of the Lambda heat pump."""
        await _handle_write_modbus_register(hass, call)

    async def async_write_room_and_pv(call: ServiceCall = None) -> None:
        """Write room temperature and PV surplus to Modbus registers."""
        await _handle_write_room_and_pv(hass)

    # Setup regelmäßige Aktualisierungen für alle Entries
    @callback
    def setup_scheduled_updates() -> None:
        """Set up scheduled updates for all entries."""
        for unsub in unsub_update_callbacks.values():
            unsub()
        unsub_update_callbacks.clear()

        # Prüfe ob mindestens eine Option aktiv ist
        if not should_start_scheduler(hass):
            _LOGGER.info("No service options are active, skipping scheduler setup")
            return

        # Gemeinsamer Timer für beide Schreibvorgänge
        update_interval = timedelta(seconds=DEFAULT_WRITE_INTERVAL)
        _LOGGER.info("Setting up scheduled updates with interval: %s seconds", DEFAULT_WRITE_INTERVAL)

        async def scheduled_update_callback(_):
            _LOGGER.info("Scheduled update callback triggered")
            await async_write_room_and_pv()

        unsub = async_track_time_interval(
            hass,
            scheduled_update_callback,
            update_interval,
        )
        unsub_update_callbacks["write_room_and_pv"] = unsub
        _LOGGER.info("Scheduled updates setup completed")

    # Bei Änderungen in der Konfiguration die Timers neu einrichten
    @callback
    def config_entry_updated() -> None:
        """Reagiere auf Konfigurationsänderungen."""
        _LOGGER.debug("Config entry updated, resetting scheduled updates")
        setup_scheduled_updates()

    # Registriere Listener für Konfigurationsänderungen
    hass.bus.async_listen("config_entry_updated", config_entry_updated)

    # Initialen Setup durchführen
    setup_scheduled_updates()
    
    # WICHTIG: Speichere die setup-Funktion für späteres Restart nach Reload
    hass.data.setdefault(f"{DOMAIN}_services", {})["setup_scheduled_updates"] = setup_scheduled_updates

    # Registriere Services
    hass.services.async_register(
        DOMAIN,
        "update_room_temperature",
        async_update_room_temperature,
        schema=UPDATE_ROOM_TEMPERATURE_SCHEMA,
    )

    # Registriere read_modbus_register Service
    hass.services.async_register(
        DOMAIN,
        "read_modbus_register",
        async_read_modbus_register,
        schema=READ_MODBUS_REGISTER_SCHEMA,
        supports_response=True,
    )

    # Registriere write_modbus_register Service
    hass.services.async_register(
        DOMAIN,
        "write_modbus_register",
        async_write_modbus_register,
        schema=WRITE_MODBUS_REGISTER_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Lambda WP services and stop all timers."""
    _LOGGER.info("Unloading Lambda WP services...")
    
    # Stop all service callbacks
    if "_lambda_service_callbacks" in hass.data:
        callbacks = hass.data["_lambda_service_callbacks"]
        for callback_name, unsub in callbacks.items():
            try:
                unsub()
                _LOGGER.info("Stopped service callback: %s", callback_name)
            except Exception as e:
                _LOGGER.warning("Error stopping callback %s: %s", callback_name, e)
        callbacks.clear()
        del hass.data["_lambda_service_callbacks"]
    
    # Remove services
    if hass.services.has_service(DOMAIN, "update_room_temperature"):
        hass.services.async_remove(DOMAIN, "update_room_temperature")
    if hass.services.has_service(DOMAIN, "read_modbus_register"):
        hass.services.async_remove(DOMAIN, "read_modbus_register")
    if hass.services.has_service(DOMAIN, "write_modbus_register"):
        hass.services.async_remove(DOMAIN, "write_modbus_register")
    
    _LOGGER.info("Lambda WP services unloaded successfully")


async def setup_scheduled_timer(hass: HomeAssistant) -> None:
    """Restart scheduled timer after reload (when services already exist)."""
    services_data = hass.data.get(f"{DOMAIN}_services", {})
    setup_func = services_data.get("setup_scheduled_updates")
    
    if setup_func:
        setup_func()
        _LOGGER.info("Scheduled timer restarted successfully after reload")
    else:
        _LOGGER.error(
            "Cannot restart scheduled timer: setup function not found after reload. "
            "This should not happen! Check service initialization."
        )
