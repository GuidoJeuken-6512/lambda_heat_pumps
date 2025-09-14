"""Utility functions for Lambda Heat Pumps integration."""

from __future__ import annotations

import logging
import os
import yaml
import aiofiles
from datetime import datetime
from typing import List, Tuple, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity_component import async_update_entity

from .const import (
    BASE_ADDRESSES,
    CALCULATED_SENSOR_TEMPLATES,
    DOMAIN,
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
)

_LOGGER = logging.getLogger(__name__)


def _get_coordinator(hass: HomeAssistant):
    """Helper function to get the coordinator instance."""

    
    # Find the first (and typically only) coordinator instance
    try:
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if hasattr(coordinator, '_cycling_warnings'):
                return coordinator
    except (KeyError, AttributeError):
        pass
    return None


def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version.
    Args:
       sensor_templates: Dictionary of sensor templates
       fw_version: The firmware version to check against
    Returns:
       Filtered dictionary of compatible sensors
    """
    return {
        k: v
        for k, v in sensor_templates.items()
        if (
            isinstance(v.get("firmware_version"), (int, float))
            and v.get("firmware_version", 1) <= fw_version
        )
        or not isinstance(
            v.get("firmware_version"), (int, float)
        )  # Include sensors without firmware_version
    }


def get_firmware_version(entry):
    """
    Get firmware version from entry with fallback logic.
    First tries entry.options, then falls back to entry.data for backward compatibility.
    Returns the firmware name as string (e.g., "V0.0.3-3K").
    """
    from .const import DEFAULT_FIRMWARE

    # First try to get from options (new way)
    fw_version = entry.options.get("firmware_version")
    if fw_version:
        return fw_version

    # Fallback to data (old way, for backward compatibility)
    fw_version = entry.data.get("firmware_version")
    if fw_version:
        return fw_version

    # Default fallback
    return DEFAULT_FIRMWARE


def get_firmware_version_int(entry):
    """
    Get firmware version as integer from entry with fallback logic.
    Returns the integer version for compatibility checking (e.g., 1, 2, 3).
    """
    from .const import DEFAULT_FIRMWARE, FIRMWARE_VERSION

    # First try to get from options (new way)
    fw_version = entry.options.get("firmware_version")
    if fw_version:
        return FIRMWARE_VERSION.get(fw_version, 1)

    # Fallback to data (old way, for backward compatibility)
    fw_version = entry.data.get("firmware_version")
    if fw_version:
        return FIRMWARE_VERSION.get(fw_version, 1)

    # Default fallback
    return FIRMWARE_VERSION.get(DEFAULT_FIRMWARE, 1)


def build_device_info(entry):
    """
    Build device_info dict for Home Assistant device registry.
    """
    DOMAIN = entry.domain if hasattr(entry, "domain") else "lambda_heat_pumps"
    entry_id = entry.entry_id
    fw_version = get_firmware_version(entry)
    host = entry.data.get("host")
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": entry.data.get("name", "Lambda WP"),
        "manufacturer": "Lambda",
        "model": fw_version,
        "configuration_url": f"http://{host}",
        "sw_version": fw_version,
        "entry_type": None,
        "suggested_area": None,
        "via_device": None,
        "hw_version": None,
        "serial_number": None,
    }


async def migrate_lambda_config(hass: HomeAssistant) -> bool:
    """Migrate existing lambda_wp_config.yaml to include cycling_offsets.

    Returns:
        bool: True if migration was performed, False otherwise
    """
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    if not os.path.exists(lambda_config_path):
        _LOGGER.debug("No existing lambda_wp_config.yaml found, no migration needed")
        return False

    try:
        # Read current config
        content = await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "r").read()
        )
        current_config = yaml.safe_load(content)

        if not current_config:
            _LOGGER.debug("Empty config file, no migration needed")
            return False

        # Check if cycling_offsets already exists
        if "cycling_offsets" in current_config:
            _LOGGER.info(
                "lambda_wp_config.yaml already contains cycling_offsets - "
                "no migration needed"
            )
            return False

        _LOGGER.info("Migrating lambda_wp_config.yaml to include cycling_offsets")

        # Create backup
        backup_path = lambda_config_path + ".backup"
        await hass.async_add_executor_job(lambda: open(backup_path, "w").write(content))
        _LOGGER.info("Created backup at %s", backup_path)

        # Add cycling_offsets section
        current_config["cycling_offsets"] = {
            "hp1": {
                "heating_cycling_total": 0,
                "hot_water_cycling_total": 0,
                "cooling_cycling_total": 0,
                "defrost_cycling_total": 0,
            }
        }

        # Add documentation comment
        if "# Cycling counter offsets" not in content:
            # Insert cycling_offsets documentation before the existing sections
            cycling_docs = """# Cycling counter offsets for total sensors
# These offsets are added to the calculated cycling counts
# Useful when replacing heat pumps or resetting counters
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0      # Offset for HP1 heating total cycles
#    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
#    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
#  hp2:
#    heating_cycling_total: 1500   # Example: HP2 already had 1500 heating cycles
#    hot_water_cycling_total: 800  # Example: HP2 already had 800 hot water cycles
#    cooling_cycling_total: 200    # Example: HP2 already had 200 cooling cycles

"""
            # Find a good place to insert the documentation
            lines = content.split("\n")
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("disabled_registers:"):
                    insert_pos = i
                    break

            lines.insert(insert_pos, cycling_docs.rstrip())
            content = "\n".join(lines)

        # Write updated config
        await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "w").write(content)
        )

        _LOGGER.info(
            "Successfully migrated lambda_wp_config.yaml to version 1.1.0 - "
            "Added cycling_offsets section with default values for hp1. "
            "Backup created at %s.backup",
            lambda_config_path,
        )
        return True

    except Exception as e:
        _LOGGER.error("Error during config migration: %s", e)
        return False


async def ensure_lambda_config(hass: HomeAssistant) -> bool:
    """Ensure lambda_wp_config.yaml exists, create from template if missing.
    
    Returns:
        bool: True if config file exists or was created successfully
    """
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
    
    if os.path.exists(lambda_config_path):
        _LOGGER.debug("lambda_wp_config.yaml already exists")
        return True
    
    try:
        # Import template from const.py
        from .const import LAMBDA_WP_CONFIG_TEMPLATE
        
        _LOGGER.info("Creating lambda_wp_config.yaml from template")
        
        # Create config file from template
        await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "w").write(LAMBDA_WP_CONFIG_TEMPLATE)
        )
        
        _LOGGER.info("Successfully created lambda_wp_config.yaml from template")
        return True
        
    except Exception as e:
        _LOGGER.error("Failed to create lambda_wp_config.yaml: %s", e)
        return False


async def load_lambda_config(hass: HomeAssistant) -> dict:
    """Load complete Lambda configuration from lambda_wp_config.yaml."""
    # Check if config is already cached in hass.data
    if DOMAIN in hass.data and "lambda_config_cache" in hass.data[DOMAIN]:
        _LOGGER.debug("Using cached Lambda config")
        return hass.data[DOMAIN]["lambda_config_cache"]
    
    # First, ensure config file exists
    await ensure_lambda_config(hass)
    
    # Then, try to migrate if needed
    await migrate_lambda_config(hass)

    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    default_config = {
        "disabled_registers": set(),
        "sensors_names_override": {},
        "cycling_offsets": {},
    }

    if not os.path.exists(lambda_config_path):
        _LOGGER.warning("lambda_wp_config.yaml not found, using default configuration")
        return default_config

    try:
        content = await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "r").read()
        )
        config = yaml.safe_load(content)

        if not config:
            _LOGGER.warning(
                "lambda_wp_config.yaml is empty, using default configuration"
            )
            return default_config

        # Load disabled registers
        disabled_registers = set()
        if "disabled_registers" in config:
            try:
                disabled_registers = set(int(x) for x in config["disabled_registers"])
            except (ValueError, TypeError) as e:
                _LOGGER.error("Invalid disabled_registers format: %s", e)
                disabled_registers = set()

        # Load sensor overrides
        sensors_names_override = {}
        if "sensors_names_override" in config:
            try:
                for override in config["sensors_names_override"]:
                    if "id" in override and "override_name" in override:
                        sensors_names_override[override["id"]] = override[
                            "override_name"
                        ]
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid sensors_names_override format: %s", e)
                sensors_names_override = {}

        # Load cycling offsets
        cycling_offsets = {}
        if "cycling_offsets" in config:
            try:
                cycling_offsets = config["cycling_offsets"]
                # Validate cycling offsets structure
                for device, offsets in cycling_offsets.items():
                    if not isinstance(offsets, dict):
                        _LOGGER.warning(
                            "Invalid cycling_offsets format for device %s", device
                        )
                        continue
                    for offset_type, value in offsets.items():
                        if not isinstance(value, (int, float)):
                            _LOGGER.warning(
                                "Invalid cycling offset value for %s.%s: %s",
                                device,
                                offset_type,
                                value,
                            )
                            cycling_offsets[device][offset_type] = 0
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid cycling_offsets format: %s", e)
                cycling_offsets = {}

        # Load energy consumption offsets
        energy_consumption_offsets = {}
        if "energy_consumption_offsets" in config:
            try:
                energy_consumption_offsets = config["energy_consumption_offsets"]
                # Validate energy consumption offsets structure
                for device, offsets in energy_consumption_offsets.items():
                    if not isinstance(offsets, dict):
                        _LOGGER.warning(
                            "Invalid energy_consumption_offsets format for device %s", device
                        )
                        continue
                    for offset_type, value in offsets.items():
                        if not isinstance(value, (int, float)):
                            _LOGGER.warning(
                                "Invalid energy consumption offset value for %s.%s: %s",
                                device,
                                offset_type,
                                value,
                            )
                            energy_consumption_offsets[device][offset_type] = 0.0
            except (TypeError, KeyError) as e:
                _LOGGER.error("Invalid energy_consumption_offsets format: %s", e)
                energy_consumption_offsets = {}

        _LOGGER.debug(
            "Loaded Lambda config: %d disabled registers, %d sensor "
            "overrides, %d cycling device offsets, %d energy consumption device offsets",
            len(disabled_registers),
            len(sensors_names_override),
            len(cycling_offsets),
            len(energy_consumption_offsets),
        )

        config_result = {
            "disabled_registers": disabled_registers,
            "sensors_names_override": sensors_names_override,
            "cycling_offsets": cycling_offsets,
            "energy_consumption_offsets": energy_consumption_offsets,
        }
        
        # Cache the config in hass.data to avoid repeated loading
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN]["lambda_config_cache"] = config_result
        
        return config_result

    except Exception as e:
        _LOGGER.error(
            "Error loading configuration from lambda_wp_config.yaml: %s",
            str(e),
        )
        return default_config


# Keep the old function for backward compatibility
async def load_disabled_registers(hass: HomeAssistant) -> set[int]:
    """Load disabled registers from lambda_wp_config in config directory.

    DEPRECATED: Use load_lambda_config() instead.
    """
    config = await load_lambda_config(hass)
    return config["disabled_registers"]


def is_register_disabled(address: int, disabled_registers: set[int]) -> bool:
    """Check if a register is disabled.

    Args:
        address: The register address to check
        disabled_registers: Set of disabled register addresses

    Returns:
        bool: True if the register is disabled, False otherwise
    """
    is_disabled = address in disabled_registers
    if is_disabled:
        _LOGGER.debug(
            "Register %d is disabled (in set: %s)",
            address,
            disabled_registers,
        )
    return is_disabled


def generate_base_addresses(device_type: str, count: int) -> dict:
    """Generate base addresses for a given device type and count.

    Args:
        device_type: Type of device (hp, boil, buff, sol, hc)
        count: Number of devices

    Returns:
        dict: Dictionary with device numbers as keys
        and base addresses as values
    """
    base_addresses = BASE_ADDRESSES

    start_address = base_addresses.get(device_type, 0)
    if start_address == 0:
        return {}

    return {i: start_address + (i - 1) * 100 for i in range(1, count + 1)}


def to_signed_16bit(val):
    """Wandelt einen 16-Bit-Wert in signed um."""
    return val - 0x10000 if val >= 0x8000 else val


def to_signed_32bit(val):
    """Wandelt einen 32-Bit-Wert in signed um."""
    return val - 0x100000000 if val >= 0x80000000 else val


def clamp_to_int16(value: float, context: str = "value") -> int:
    """Clamp a value to int16 range (-32768 to 32767).

    Args:
        value: The value to clamp
        context: Context string for logging (e.g., "temperature", "power")

    Returns:
        int: The clamped value in int16 range
    """
    raw_value = int(value)
    if raw_value < -32768:
        _LOGGER.warning(
            "%s value %d is below int16 minimum (-32768), clamping to -32768",
            context.capitalize(),
            raw_value,
        )
        return -32768
    elif raw_value > 32767:
        _LOGGER.warning(
            "%s value %d is above int16 maximum (32767), clamping to 32767",
            context.capitalize(),
            raw_value,
        )
        return 32767
    else:
        return raw_value


def generate_sensor_names(
    device_prefix: str,
    sensor_name: str,
    sensor_id: str,
    name_prefix: str,
    use_legacy_modbus_names: bool,
) -> dict:
    """Generate consistent sensor names, entity IDs, and unique IDs.

    Args:
        device_prefix: Device prefix like "hp1", "boil1", etc. or sensor_id for general sensors
        sensor_name: Human readable sensor name like "COP Calculated"
        sensor_id: Sensor identifier like "cop_calc"
        name_prefix: Name prefix like "eu08l" (used in legacy mode)
        use_legacy_modbus_names: Whether to use legacy naming convention

    Returns:
        dict: Contains 'name', 'entity_id', and 'unique_id'
    """
    # Display name logic - identical to sensor.py
    # Both legacy and standard modes use the same display name format
    # The name_prefix will be added automatically by Home Assistant's device naming
    if device_prefix == sensor_id:
        # Für General Sensors nur den sensor_name verwenden
        display_name = sensor_name
    else:
        display_name = f"{device_prefix.upper()} {sensor_name}"

    # Always use lowercase for name_prefix to unify entity_id generation
    name_prefix_lc = name_prefix.lower() if name_prefix else ""

    # Entity ID und unique_id wie in der alten Version generieren
    if use_legacy_modbus_names:
        # Für General Sensors nur name_prefix_sensor_id verwenden
        if device_prefix == sensor_id:
            entity_id = f"sensor.{name_prefix_lc}_{sensor_id}"
            unique_id = f"{name_prefix_lc}_{sensor_id}"
        else:
            entity_id = f"sensor.{name_prefix_lc}_{device_prefix}_{sensor_id}"
            unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
    else:
        # Für General Sensors (device_prefix == sensor_id) nur sensor_id verwenden
        if device_prefix == sensor_id:
            entity_id = f"sensor.{sensor_id}"
            unique_id = f"{sensor_id}"
        else:
            entity_id = f"sensor.{device_prefix}_{sensor_id}"
            unique_id = f"{device_prefix}_{sensor_id}"

    return {"name": display_name, "entity_id": entity_id, "unique_id": unique_id}


def generate_template_entity_prefix(
    device_prefix: str, name_prefix: str, use_legacy_modbus_names: bool
) -> str:
    """Generate entity prefix for templates based on naming mode.

    Args:
        device_prefix: Device prefix like "hp1", "boil1", etc.
        name_prefix: Name prefix like "eu08l" (used in legacy mode)
        use_legacy_modbus_names: Whether to use legacy naming convention

    Returns:
        str: Entity prefix for use in templates
    """
    if use_legacy_modbus_names:
        return f"{name_prefix}_{device_prefix}"
    else:
        return device_prefix


# --- Cycling Counter Increment Function ---


async def increment_cycling_counter(
    hass: HomeAssistant,
    mode: str,
    hp_index: int,
    name_prefix: str,
    use_legacy_modbus_names: bool = True,
    cycling_offsets: dict = None,
):
    """
    Increment ALL cycling counters for a given mode and heat pump index.
    This should be called only on a real flank (state change)!
    
    Increments: Total, Daily, 2H, 4H sensors

    Args:
        hass: HomeAssistant instance
        mode: One of ["heating", "hot_water", "cooling", "defrost"]
        hp_index: Index of the heat pump (1-based)
        name_prefix: Name prefix (e.g. "eu08l")
        use_legacy_modbus_names: Use legacy entity naming
        cycling_offsets: Optional dict with cycling offsets from config
    """

    device_prefix = f"hp{hp_index}"
    
    # Liste aller Sensor-Typen, die erhöht werden sollen
    sensor_types = [
        f"{mode}_cycling_total",
        f"{mode}_cycling_daily", 
        f"{mode}_cycling_2h",
        f"{mode}_cycling_4h"
    ]
    
    for sensor_id in sensor_types:
        names = generate_sensor_names(
            device_prefix,
            CALCULATED_SENSOR_TEMPLATES[sensor_id]["name"],
            sensor_id,
            name_prefix,
            use_legacy_modbus_names,
        )
        entity_id = names["entity_id"]

        # Check if entity is already registered
        entity_registry = async_get_entity_registry(hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None:
            # Dynamische Meldungsunterdrückung
            coordinator = _get_coordinator(hass)
            if coordinator:
                warning_count = coordinator._cycling_warnings.get(entity_id, 0)
                coordinator._cycling_warnings[entity_id] = warning_count + 1
                
                if warning_count < coordinator._max_cycling_warnings:
                    _LOGGER.debug(
                        f"Entity {entity_id} not yet registered (attempt {warning_count + 1}/{coordinator._max_cycling_warnings})"
                    )
                else:
                    _LOGGER.warning(
                        f"Entity {entity_id} not yet registered after {coordinator._max_cycling_warnings} attempts"
                    )
            else:
                _LOGGER.warning(
                    f"Skipping cycling counter increment: {entity_id} not yet registered"
                )
            continue

        # Zusätzliche Prüfung: Ist die Entity tatsächlich verfügbar?
        state_obj = hass.states.get(entity_id)
        if state_obj is None:
            # Dynamische Meldungsunterdrückung für State-Problem
            coordinator = _get_coordinator(hass)
            if coordinator:
                state_warning_key = f"{entity_id}_state"
                warning_count = coordinator._cycling_warnings.get(state_warning_key, 0)
                coordinator._cycling_warnings[state_warning_key] = warning_count + 1
                
                if warning_count < coordinator._max_cycling_warnings:
                    _LOGGER.debug(
                        f"Entity {entity_id} state not available yet (attempt {warning_count + 1}/{coordinator._max_cycling_warnings})"
                    )
                else:
                    _LOGGER.warning(
                        f"Entity {entity_id} state not available after {coordinator._max_cycling_warnings} attempts"
                    )
            else:
                _LOGGER.warning(
                    f"Skipping cycling counter increment: {entity_id} state not available yet"
                )
            continue

        # Erfolgreiche Registrierung - Reset Counter
        coordinator = _get_coordinator(hass)
        if coordinator:
            if entity_id in coordinator._cycling_warnings:
                del coordinator._cycling_warnings[entity_id]
            state_warning_key = f"{entity_id}_state"
            if state_warning_key in coordinator._cycling_warnings:
                del coordinator._cycling_warnings[state_warning_key]

        # Get current state
        if state_obj.state in (None, STATE_UNKNOWN, "unknown"):
            current = 0
        else:
            try:
                current = int(float(state_obj.state))
            except Exception:
                current = 0

        # Offset nur für Total-Sensoren anwenden
        offset = 0
        if cycling_offsets is not None and sensor_id.endswith("_total"):
            device_key = device_prefix
            if device_key in cycling_offsets:
                offset = int(cycling_offsets[device_key].get(sensor_id, 0))

        new_value = int(current + 1)

        # Versuche die Entity-Instanz zu finden
        cycling_entity = None
        try:
            # Suche in der neuen Cycling-Entities-Struktur
            for entry_id, comp_data in hass.data.get("lambda_heat_pumps", {}).items():
                if isinstance(comp_data, dict) and "cycling_entities" in comp_data:
                    cycling_entity = comp_data["cycling_entities"].get(entity_id)
                    if cycling_entity:
                        break
        except Exception as e:
            _LOGGER.debug(f"Error searching for entity {entity_id}: {e}")

        final_value = int(new_value + offset)
        if cycling_entity is not None and hasattr(cycling_entity, "set_cycling_value"):
            cycling_entity.set_cycling_value(final_value)
            _LOGGER.info(
                f"Cycling counter incremented: {entity_id} = {final_value} (was {current}, offset {offset}) [entity updated]"
            )
        else:
            # Fallback: State setzen wie bisher
            _LOGGER.warning(
                f"Cycling entity {entity_id} not found, using fallback state update"
            )
            hass.states.async_set(
                entity_id, final_value, state_obj.attributes if state_obj else {}
            )
            _LOGGER.info(
                f"Cycling counter incremented: {entity_id} = {final_value} (was {current}, offset {offset}) [state only]"
            )

        # Optional: Entity zum Update zwingen (z.B. für Recorder)
        try:
            await async_update_entity(hass, entity_id)
        except Exception as e:
            _LOGGER.debug(f"Could not force update for {entity_id}: {e}")


# =============================================================================
# UNIVERSAL FILE AGEING HELPER FUNCTIONS
# =============================================================================

async def analyze_file_ageing(
    hass: HomeAssistant,
    directory_path: str,
    filename_mask: str,
    recursive: bool = False
) -> List[Tuple[str, int, Optional[str]]]:
    """
    Analysiere das Alter aller Dateien in einem Verzeichnis basierend auf Dateinamen-Maske.
    
    Args:
        hass: Home Assistant Instanz
        directory_path: Pfad zum Verzeichnis
        filename_mask: Substring-Maske für Dateinamen (leerer String = alle Dateien)
        recursive: True für rekursive Suche in Unterverzeichnissen
    
    Returns:
        List[Tuple[str, int, Optional[str]]]: Liste von (dateipfad, tage_alt, fehler_nachricht)
        - dateipfad: Vollständiger Pfad zur Datei
        - tage_alt: Anzahl der Tage, die die Datei alt ist
        - fehler_nachricht: Fehlermeldung falls etwas schiefgeht, sonst None
    """
    
    results = []
    
    try:
        if not os.path.exists(directory_path):
            return [(directory_path, 0, "Verzeichnis existiert nicht")]
        
        if not os.path.isdir(directory_path):
            return [(directory_path, 0, "Pfad ist kein Verzeichnis")]
        
        # Liste alle Dateien im Verzeichnis auf
        if recursive:
            # ASYNCHRON: os.walk in async_add_executor_job ausführen
            def walk_directory(directory):
                file_paths = []
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_paths.append(os.path.join(root, file))
                return file_paths

            file_paths = await hass.async_add_executor_job(
                walk_directory, directory_path
            )
        else:
            try:
                files = await hass.async_add_executor_job(
                    lambda: os.listdir(directory_path)
                )
                file_paths = [
                    os.path.join(directory_path, f) for f in files
                    if os.path.isfile(os.path.join(directory_path, f))
                ]
            except Exception as e:
                return [(directory_path, 0, f"Fehler beim Auflisten des Verzeichnisses: {e}")]
        
        # Analysiere jede Datei
        for file_path in file_paths:
            try:
                # Prüfe Dateinamen-Maske (Substring-Suche)
                filename = os.path.basename(file_path)
                if (not filename_mask or 
                        filename_mask.lower() in filename.lower()):
                    # Hole Datei-Informationen
                    stat = await hass.async_add_executor_job(
                        lambda: os.stat(file_path)
                    )
                    
                    # Berechne Datei-Alter
                    file_date = datetime.fromtimestamp(stat.st_mtime)
                    today = datetime.now()
                    days_old = (today - file_date).days
                    
                    results.append((file_path, days_old, None))
                    
            except Exception as e:
                error_msg = f"Fehler beim Analysieren der Datei {file_path}: {e}"
                results.append((file_path, 0, error_msg))
                continue
        
        return results
        
    except Exception as e:
        return [(directory_path, 0, f"Fehler beim Verarbeiten des Verzeichnisses: {e}")]

async def analyze_single_file_ageing(
    hass: HomeAssistant,
    file_path: str
) -> Tuple[str, int, Optional[str]]:
    """
    Analysiere das Alter einer einzelnen Datei.
    
    Args:
        hass: Home Assistant Instanz
        file_path: Vollständiger Pfad zur Datei
    
    Returns:
        Tuple[str, int, Optional[str]]: (dateipfad, tage_alt, fehler_nachricht)
        - dateipfad: Vollständiger Pfad zur Datei
        - tage_alt: Anzahl der Tage, die die Datei alt ist
        - fehler_nachricht: Fehlermeldung falls etwas schiefgeht, sonst None
    """
    
    try:
        if not os.path.exists(file_path):
            return file_path, 0, f"Datei existiert nicht: {file_path}"
        
        # Hole Datei-Informationen
        stat = await hass.async_add_executor_job(
            lambda: os.stat(file_path)
        )
        
        # Berechne Datei-Alter
        file_date = datetime.fromtimestamp(stat.st_mtime)
        today = datetime.now()
        days_old = (today - file_date).days
        
        return file_path, days_old, None
        
    except Exception as e:
        error_msg = f"Fehler beim Analysieren der Datei {file_path}: {e}"
        return file_path, 0, error_msg

async def delete_files(
    hass: HomeAssistant,
    file_paths: List[str],
    dry_run: bool = True
) -> Tuple[int, List[str]]:
    """
    Lösche eine Liste von Dateien.
    
    Args:
        hass: Home Assistant Instanz
        file_paths: Liste der zu löschenden Dateipfade
        dry_run: True für Testlauf ohne Löschung, False für tatsächliche Löschung
    
    Returns:
        Tuple[int, List[str]]: (gelöschte_dateien, fehler_liste)
    """
    
    deleted_files = 0
    errors = []
    
    for file_path in file_paths:
        try:
            if dry_run:
                _LOGGER.info(
                    "[DRY RUN] Würde Datei löschen: %s",
                    file_path
                )
                deleted_files += 1
            else:
                await hass.async_add_executor_job(
                    lambda: os.remove(file_path)
                )
                deleted_files += 1
                _LOGGER.info("Datei gelöscht: %s", file_path)
                
        except Exception as e:
            error_msg = f"Fehler beim Löschen von {file_path}: {e}"
            errors.append(error_msg)
            _LOGGER.error(error_msg)
    
    return deleted_files, errors


# =============================================================================
# ENERGY CONSUMPTION HELPER FUNCTIONS
# =============================================================================

def convert_energy_to_kwh(value: float, unit: str) -> float:
    """
    Konvertiert Energie-Werte zu kWh basierend auf der Einheit.
    Analog zur PV Surplus Konvertierung in services.py.
    
    Args:
        value: Energie-Wert
        unit: Einheit des Wertes (Wh, kWh, etc.)
    
    Returns:
        float: Wert in kWh
    """
    if not unit:
        # Wenn keine Einheit angegeben, versuche basierend auf der Größe zu schätzen
        if value > 10000:  # Wahrscheinlich Wh
            return value / 1000.0
        return value
    
    unit_lower = unit.lower().strip()
    
    # Standard Energie-Einheiten
    if unit_lower in ["wh", "wattstunden"]:
        return value / 1000.0
    elif unit_lower in ["kwh", "kilowattstunden"]:
        return value
    elif unit_lower in ["mwh", "megawattstunden"]:
        return value * 1000.0
    else:
        # Unbekannte Einheit - versuche basierend auf der Größe zu schätzen
        # Analog zur PV Surplus Logik: große Werte sind wahrscheinlich Wh
        if value > 10000:
            return value / 1000.0
        return value


def calculate_energy_delta(
    current_reading: float,
    last_reading: float,
    max_delta: float = 100.0
) -> float:
    """
    Berechne Energie-Delta mit Überlauf-Schutz.
    
    Args:
        current_reading: Aktueller Energieverbrauch in kWh
        last_reading: Letzter Energieverbrauch in kWh
        max_delta: Maximale erlaubte Delta (Schutz vor unrealistischen Sprüngen)
    
    Returns:
        float: Berechnetes Delta in kWh
    """
    if current_reading < last_reading:
        # Überlauf erkannt - nehme aktuellen Wert
        _LOGGER.debug(
            "Energy overflow detected: current=%.6f < last=%.6f, using current value",
            current_reading, last_reading
        )
        return current_reading
    else:
        delta = current_reading - last_reading
        # Schutz vor unrealistischen Sprüngen
        if delta > max_delta:
            _LOGGER.warning(
                "Energy delta %.6f exceeds maximum %.6f, clamping to maximum",
                delta, max_delta
            )
            return max_delta
        # Rückgabe mit hoher Präzision (6 Nachkommastellen)
        return round(delta, 6)


def generate_energy_sensor_names(
    device_prefix: str,
    mode: str,
    period: str,
    name_prefix: str,
    use_legacy_modbus_names: bool,
) -> dict:
    """
    Generiere konsistente Namen für Energy Consumption Sensoren.
    
    Args:
        device_prefix: Device prefix wie "hp1", "boil1", etc.
        mode: Betriebsart wie "heating", "hot_water", "cooling", "defrost"
        period: Zeitraum wie "total", "daily"
        name_prefix: Name prefix wie "eu08l" (wird im legacy mode verwendet)
        use_legacy_modbus_names: Ob legacy naming convention verwendet werden soll
    
    Returns:
        dict: Enthält 'name', 'entity_id' und 'unique_id'
    """
    sensor_id = f"{mode}_energy_{period}"
    sensor_name = f"{mode.title()} Energy {period.title()}"
    
    return generate_sensor_names(
        device_prefix, sensor_name, sensor_id, name_prefix, use_legacy_modbus_names
    )


async def increment_energy_consumption_counter(
    hass: HomeAssistant,
    mode: str,
    hp_index: int,
    energy_delta: float,
    name_prefix: str,
    use_legacy_modbus_names: bool = True,
    energy_offsets: dict = None,
):
    """
    Increment energy consumption counters for a given mode and heat pump.
    Analog zu increment_cycling_counter aber für Energieverbrauch.
    
    Args:
        hass: HomeAssistant instance
        mode: One of ["heating", "hot_water", "cooling", "defrost"]
        hp_index: Index of the heat pump (1-based)
        energy_delta: Energy consumption delta in kWh
        name_prefix: Name prefix (e.g. "eu08l")
        use_legacy_modbus_names: Use legacy entity naming
        energy_offsets: Optional dict with energy offsets from config
    """
    if mode not in ENERGY_CONSUMPTION_MODES:
        _LOGGER.error("Invalid energy consumption mode: %s", mode)
        return
    
    if energy_delta <= 0:
        _LOGGER.debug("Energy delta %.2f is not positive, skipping increment", energy_delta)
        return

    device_prefix = f"hp{hp_index}"
    
    # Liste aller Sensor-Typen, die erhöht werden sollen
    sensor_types = [
        f"{mode}_energy_total",
        f"{mode}_energy_daily", 
    ]
    
    for sensor_id in sensor_types:
        names = generate_energy_sensor_names(
            device_prefix,
            mode,
            "total" if sensor_id.endswith("_total") else "daily",
            name_prefix,
            use_legacy_modbus_names,
        )
        entity_id = names["entity_id"]

        # Check if entity is already registered
        entity_registry = async_get_entity_registry(hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None:
            # Dynamische Meldungsunterdrückung
            coordinator = _get_coordinator(hass)
            if coordinator:
                warning_count = coordinator._energy_warnings.get(entity_id, 0)
                coordinator._energy_warnings[entity_id] = warning_count + 1
                
                if warning_count < coordinator._max_energy_warnings:
                    _LOGGER.debug(
                        f"Energy entity {entity_id} not yet registered (attempt {warning_count + 1}/{coordinator._max_energy_warnings})"
                    )
                else:
                    _LOGGER.warning(
                        f"Energy entity {entity_id} not yet registered after {coordinator._max_energy_warnings} attempts"
                    )
            else:
                _LOGGER.warning(
                    f"Skipping energy counter increment: {entity_id} not yet registered"
                )
            continue

        # Zusätzliche Prüfung: Ist die Entity tatsächlich verfügbar?
        state_obj = hass.states.get(entity_id)
        if state_obj is None:
            # Dynamische Meldungsunterdrückung für State-Problem
            coordinator = _get_coordinator(hass)
            if coordinator:
                state_warning_key = f"{entity_id}_state"
                warning_count = coordinator._energy_warnings.get(state_warning_key, 0)
                coordinator._energy_warnings[state_warning_key] = warning_count + 1
                
                if warning_count < coordinator._max_energy_warnings:
                    _LOGGER.debug(
                        f"Energy entity {entity_id} state not available yet (attempt {warning_count + 1}/{coordinator._max_energy_warnings})"
                    )
                else:
                    _LOGGER.warning(
                        f"Energy entity {entity_id} state not available after {coordinator._max_energy_warnings} attempts"
                    )
            else:
                _LOGGER.warning(
                    f"Skipping energy counter increment: {entity_id} state not available yet"
                )
            continue

        # Erfolgreiche Registrierung - Reset Counter
        coordinator = _get_coordinator(hass)
        if coordinator:
            if entity_id in coordinator._energy_warnings:
                del coordinator._energy_warnings[entity_id]
            state_warning_key = f"{entity_id}_state"
            if state_warning_key in coordinator._energy_warnings:
                del coordinator._energy_warnings[state_warning_key]

        # Get current state
        if state_obj.state in (None, STATE_UNKNOWN, "unknown"):
            current = 0.0
        else:
            try:
                current = float(state_obj.state)
            except Exception:
                current = 0.0

        # Offset nur für Total-Sensoren anwenden
        offset = 0.0
        if energy_offsets is not None and sensor_id.endswith("_total"):
            device_key = device_prefix
            if device_key in energy_offsets:
                device_offsets = energy_offsets[device_key]
                if isinstance(device_offsets, dict):
                    offset = float(device_offsets.get(sensor_id, 0.0))
                else:
                    _LOGGER.warning(f"Invalid energy offsets structure for {device_key}: {device_offsets}")

        # Debug: Check energy_delta type
        if not isinstance(energy_delta, (int, float)):
            _LOGGER.error(f"energy_delta is not a number: {type(energy_delta)} = {energy_delta}")
            return
        
        new_value = current + energy_delta

        # Versuche die Entity-Instanz zu finden
        energy_entity = None
        try:
            # Suche in der Energy-Entities-Struktur
            for entry_id, comp_data in hass.data.get("lambda_heat_pumps", {}).items():
                if isinstance(comp_data, dict) and "energy_entities" in comp_data:
                    energy_entity = comp_data["energy_entities"].get(entity_id)
                    if energy_entity:
                        break
        except Exception as e:
            _LOGGER.debug(f"Error searching for energy entity {entity_id}: {e}")

        final_value = new_value + offset
        if energy_entity is not None and hasattr(energy_entity, "set_energy_value"):
            energy_entity.set_energy_value(final_value)
            _LOGGER.info(
                f"Energy counter incremented: {entity_id} = {final_value:.2f} kWh (was {current:.2f}, delta {energy_delta:.2f}, offset {offset:.2f}) [entity updated]"
            )
        else:
            # Fallback: State setzen wie bisher
            # Energy entity not found, using fallback state update (normal behavior)
            hass.states.async_set(
                entity_id, final_value, state_obj.attributes if state_obj else {}
            )
            _LOGGER.info(
                f"Energy counter incremented: {entity_id} = {final_value:.2f} kWh (was {current:.2f}, delta {energy_delta:.2f}, offset {offset:.2f}) [state only]"
            )

        # Optional: Entity zum Update zwingen (z.B. für Recorder)
        try:
            await async_update_entity(hass, entity_id)
        except Exception as e:
            _LOGGER.debug(f"Could not force update for {entity_id}: {e}")


def get_energy_consumption_sensor_template(mode: str, period: str) -> dict:
    """
    Hole das Template für einen Energy Consumption Sensor.
    
    Args:
        mode: Betriebsart wie "heating", "hot_water", "cooling", "defrost"
        period: Zeitraum wie "total", "daily"
    
    Returns:
        dict: Sensor template oder None wenn nicht gefunden
    """
    sensor_id = f"{mode}_energy_{period}"
    return ENERGY_CONSUMPTION_SENSOR_TEMPLATES.get(sensor_id)


def validate_energy_consumption_config(config: dict) -> bool:
    """
    Validiere die Energy Consumption Konfiguration.
    
    Args:
        config: Konfigurationsdictionary
    
    Returns:
        bool: True wenn Konfiguration gültig ist
    """
    if "energy_consumption_sensors" not in config:
        _LOGGER.warning("energy_consumption_sensors not found in config")
        return False
    
    if "energy_consumption_offsets" not in config:
        _LOGGER.warning("energy_consumption_offsets not found in config")
        return False
    
    # Validiere energy_consumption_sensors
    sensors_config = config["energy_consumption_sensors"]
    for device, sensor_config in sensors_config.items():
        if not isinstance(sensor_config, dict):
            _LOGGER.error("Invalid sensor config for device %s", device)
            return False
        if "sensor_entity_id" not in sensor_config:
            _LOGGER.error("Missing sensor_entity_id for device %s", device)
            return False
    
    # Validiere energy_consumption_offsets
    offsets_config = config["energy_consumption_offsets"]
    for device, offsets in offsets_config.items():
        if not isinstance(offsets, dict):
            _LOGGER.error("Invalid offsets config for device %s", device)
            return False
        for mode in ENERGY_CONSUMPTION_MODES:
            offset_key = f"{mode}_energy_total"
            if offset_key not in offsets:
                _LOGGER.warning("Missing offset for %s.%s", device, offset_key)
            elif not isinstance(offsets[offset_key], (int, float)):
                _LOGGER.error("Invalid offset value for %s.%s", device, offset_key)
                return False
    
    return True
