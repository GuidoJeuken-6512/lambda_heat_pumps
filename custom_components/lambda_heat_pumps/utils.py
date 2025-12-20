"""Utility functions for Lambda Heat Pumps integration."""

from __future__ import annotations

import asyncio
import logging
import os
import yaml
from datetime import datetime
from typing import Any, List, Optional, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.translation import async_get_translations

from .const import (
    BASE_ADDRESSES,
    CALCULATED_SENSOR_TEMPLATES,
    DOMAIN,
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    LAMBDA_WP_CONFIG_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)
_MISSING_SENSOR_TRANSLATIONS: set[str] = set()


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


def build_subdevice_info(entry, device_type: str, device_index: int):
    """Build device_info dict for module subdevices like HP1, HC2, etc."""

    if not device_type or not device_index:
        return build_device_info(entry)

    DOMAIN = entry.domain if hasattr(entry, "domain") else "lambda_heat_pumps"
    entry_id = entry.entry_id
    fw_version = get_firmware_version(entry)
    host = entry.data.get("host")
    main_device_name = entry.data.get("name", "Lambda WP")

    device_type_lc = device_type.lower()
    device_type_names = {
        "hp": "HP",
        "boil": "Boiler",
        "hc": "HC",
        "buff": "Buffer",
        "sol": "Solar",
    }
    display_type = device_type_names.get(device_type_lc, device_type.upper())
    device_name = f"{main_device_name} - {display_type}{device_index}"

    main_identifier = (DOMAIN, entry_id)
    sub_identifier = (DOMAIN, entry_id, device_type_lc, device_index)

    return {
        "identifiers": {sub_identifier},
        "name": device_name,
        "manufacturer": "Lambda",
        "model": fw_version,
        "configuration_url": f"http://{host}",
        "sw_version": fw_version,
        "entry_type": None,
        "suggested_area": None,
        "via_device": main_identifier,
        "hw_version": None,
        "serial_number": None,
    }


def extract_device_info_from_sensor_id(sensor_id: str) -> tuple[str | None, int | None]:
    """Extract device type and index from a sensor_id like 'hp1_operating_state'."""

    if not sensor_id:
        return None, None

    device_prefixes = ["hp", "boil", "hc", "buff", "sol"]

    for prefix in device_prefixes:
        if sensor_id.startswith(prefix):
            suffix = sensor_id[len(prefix) :]
            digits = ""
            for char in suffix:
                if char.isdigit():
                    digits += char
                else:
                    break
            if digits:
                try:
                    return prefix, int(digits)
                except ValueError:
                    return None, None
            return None, None

    return None, None


async def migrate_lambda_config(hass: HomeAssistant) -> bool:
    """Migrate existing lambda_wp_config.yaml to include cycling_offsets.
    
    DEPRECATED: Use migrate_lambda_config_sections() instead.
    This function is kept for backward compatibility.

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


def _extract_config_sections() -> dict[str, str]:
    """
    Extrahiert alle Konfigurationsabschnitte aus dem LAMBDA_WP_CONFIG_TEMPLATE.
    
    Returns:
        dict: Dictionary mit Abschnittsnamen als Keys und vollständigen Abschnitten als Values
    """
    sections = {}
    lines = LAMBDA_WP_CONFIG_TEMPLATE.split('\n')
    
    # Definiere die Abschnitts-Header und ihre Namen
    section_headers = {
        "# Override sensor names (only works if use_legacy_modbus_names is true)": "sensors_names_override",
        "# Cycling counter offsets for total sensors": "cycling_offsets",
        "# Energy consumption sensor configuration": "energy_consumption_sensors", 
        "# Energy consumption offsets for total sensors": "energy_consumption_offsets",
        "# Modbus configuration": "modbus"
    }
    
    current_section = None
    current_content = []
    
    for line in lines:
        # Prüfe ob dies ein neuer Abschnitts-Header ist
        if line.strip() in section_headers:
            # Speichere vorherigen Abschnitt falls vorhanden
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Starte neuen Abschnitt
            current_section = section_headers[line.strip()]
            current_content = [line]
        elif current_section:
            # Füge Zeile zum aktuellen Abschnitt hinzu
            current_content.append(line)
        else:
            # Wir sind noch nicht in einem relevanten Abschnitt
            continue
    
    # Speichere den letzten Abschnitt
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    _LOGGER.debug("Extracted config sections: %s", list(sections.keys()))
    return sections


async def migrate_lambda_config_sections(hass: HomeAssistant) -> bool:
    """
    Template-basierte Migration aller Konfigurationsabschnitte.
    
    Returns:
        bool: True wenn Migration durchgeführt wurde, False sonst
    """
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    if not os.path.exists(lambda_config_path):
        _LOGGER.debug("No existing lambda_wp_config.yaml found, no migration needed")
        return False

    try:
        # Lade aktuelle Konfiguration (Rohtext + geparst)
        content = await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "r").read()
        )
        current_config = yaml.safe_load(content)

        if not current_config:
            _LOGGER.debug("Empty config file, no migration needed")
            return False

        # Extrahiere alle Abschnitte aus dem Template
        template_sections = _extract_config_sections()
        
        # Prüfe welche Abschnitte fehlen
        missing_sections = []
        for section_name, section_content in template_sections.items():
            # Prüfe ob der vollständige Abschnitt bereits im Rohtext vorhanden ist
            # (nicht nur der Header, sondern der komplette Abschnitt)
            if section_content.strip() not in content:
                # Prüfe auch ob Key im Dictionary vorhanden ist
                if section_name not in current_config:
                    missing_sections.append((section_name, section_content))
                    _LOGGER.debug("Missing section: %s", section_name)
                else:
                    _LOGGER.debug("Section %s exists in dictionary but not as comment", section_name)
            else:
                _LOGGER.debug("Section %s already exists as complete comment", section_name)

        if not missing_sections:
            _LOGGER.info("All config sections already present - no migration needed")
            return False

        _LOGGER.info("Migrating lambda_wp_config.yaml - adding %d missing sections", len(missing_sections))

        # Erstelle Backup
        backup_path = lambda_config_path + ".backup"
        await hass.async_add_executor_job(lambda: open(backup_path, "w").write(content))
        _LOGGER.info("Created backup at %s", backup_path)

        # Füge fehlende Abschnitte hinzu
        updated_content = content.rstrip() + "\n\n"
        for section_name, section_content in missing_sections:
            updated_content += section_content + "\n\n"
            _LOGGER.info("Added section: %s", section_name)

        # Schreibe aktualisierte Konfiguration
        await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "w").write(updated_content)
        )

        _LOGGER.info(
            "Successfully migrated lambda_wp_config.yaml - added %d sections. Backup created at %s",
            len(missing_sections), backup_path
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
    if "_lambda_config_cache" in hass.data:
        _LOGGER.debug("Using cached Lambda config")
        return hass.data["_lambda_config_cache"]
    
    # First, ensure config file exists
    await ensure_lambda_config(hass)
    
    # Then, try to migrate if needed (only once per session)
    if "_lambda_migration_done" not in hass.data:
        await migrate_lambda_config_sections(hass)
        hass.data["_lambda_migration_done"] = True

    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    default_config = {
        "disabled_registers": set(),
        "sensors_names_override": {},
        "cycling_offsets": {},
        "energy_consumption_sensors": {},
        "energy_consumption_offsets": {},
        "modbus": {},
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
            "energy_consumption_sensors": config.get("energy_consumption_sensors", {}),
            "energy_consumption_offsets": energy_consumption_offsets,
            "modbus": config.get("modbus", {}),  # Include modbus configuration
        }
        
        # Cache the config in hass.data to avoid repeated loading
        hass.data["_lambda_config_cache"] = config_result
        
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


async def load_sensor_translations(
    hass: HomeAssistant, language: str | None = None
) -> dict[str, str]:
    """Load translated entity names for the current language (sensor, number, climate).

    Args:
        hass: Home Assistant instance
        language: Optional language code (e.g. "de"). Defaults to hass config language.

    Returns:
        dict: Mapping entity_id -> translated name (includes sensor, number, and climate)
    """
    lang = language
    if not lang:
        lang = getattr(hass.config, "language", None)
    if not lang:
        config_locale = getattr(hass.config, "locale", None)
        lang = getattr(config_locale, "language", None)
    if not lang:
        lang = "en"

    try:
        translation_data = await async_get_translations(
            hass,
            lang,
            "entity",
            integrations=[DOMAIN],
        )
    except Exception as err:
        _LOGGER.warning(
            "Konnte Entity-Übersetzungen für Sprache %s nicht laden: %s",
            lang,
            err,
        )
        return {}

    translations = {}
    
    # Load translations from sensor, number, and climate categories
    for category in ["sensor", "number", "climate"]:
        prefix = f"component.{DOMAIN}.entity.{category}."
        suffix = ".name"
        
        for key, value in translation_data.items():
            if not isinstance(value, str):
                continue
            if not key.startswith(prefix) or not key.endswith(suffix):
                continue
            entity_key = key[len(prefix) : -len(suffix)]
            if entity_key:
                translations[entity_key] = value

    _LOGGER.debug(
        "Geladene Entity-Übersetzungen: %d Einträge für Sprache %s (sensor/number/climate)", 
        len(translations), 
        lang
    )
    return translations


def _log_missing_translation(sensor_id: str) -> None:
    """Log translation warning once per sensor_id."""
    if not sensor_id or sensor_id in _MISSING_SENSOR_TRANSLATIONS:
        return
    _MISSING_SENSOR_TRANSLATIONS.add(sensor_id)
    _LOGGER.warning(
        "Keine Übersetzung für Sensor '%s' gefunden – verwende Fallback-Namen.", sensor_id
    )


def generate_sensor_names(
    device_prefix: str,
    sensor_name: str,
    sensor_id: str,
    name_prefix: str,
    use_legacy_modbus_names: bool,
    translations: dict[str, str] | None = None,
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
    resolved_sensor_name = sensor_name
    if translations is not None:
        translated_name = translations.get(sensor_id)
        if translated_name:
            resolved_sensor_name = translated_name
        else:
            _log_missing_translation(sensor_id)

    if device_prefix == sensor_id:
        # Für General Sensors nur den sensor_name verwenden
        display_name = resolved_sensor_name
    else:
        # Sensor name without device prefix
        # Home Assistant adds the device prefix automatically in the UI
        display_name = resolved_sensor_name

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


def get_entity_icon(spec: dict[str, Any] | None, default_icon: str | None = None) -> str | None:
    """Get icon from entity spec with fallback.
    
    Args:
        spec: Entity specification dictionary (sensor_info, spec, etc.)
        default_icon: Optional default icon to use if no icon is specified in spec
        
    Returns:
        Icon string if found, default_icon if provided, or None
    """
    if not spec:
        return default_icon
    
    icon = spec.get("icon")
    if icon:
        return icon
    
    return default_icon


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
    
    # Für compressor_start: auch monthly hinzufügen
    if mode == "compressor_start":
        sensor_types.append(f"{mode}_cycling_monthly")
    
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
    max_delta: float = 100.0  # Zurück auf 100.0 kWh
) -> float:
    """
    Berechne Energie-Delta mit Überlauf-Schutz.
    
    Args:
        current_reading: Aktueller Energieverbrauch in kWh
        last_reading: Letzter Energieverbrauch in kWh (kann None sein)
        max_delta: Maximale erlaubte Delta (Schutz vor unrealistischen Sprüngen)
    
    Returns:
        float: Berechnetes Delta in kWh
    """
    # Wenn last_reading None ist, ist es ein neuer Sensor oder erster Start
    if last_reading is None:
        _LOGGER.info("Energy delta calculation: last_reading is None (sensor not yet initialized), returning 0")
        return 0.0
    
    if current_reading < last_reading:
        # Überlauf erkannt - nehme aktuellen Wert
        _LOGGER.debug(
            "Energy overflow detected: current=%.6f < last=%.6f, using current value",
            current_reading, last_reading
        )
        return current_reading
    else:
        delta = current_reading - last_reading
        
        # Wenn last_reading 0 ist, ist es wahrscheinlich ein Sensor-Wechsel oder Neustart
        # In diesem Fall kein Maximum anwenden
        if last_reading == 0.0:
            _LOGGER.info(
                "Energy delta %.6f kWh (last_reading was 0, likely sensor change or restart)",
                delta
            )
            return round(delta, 6)
        
        # Schutz vor unrealistischen Sprüngen (nur wenn last_reading > 0)
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
    # Format mode name: "hot_water" -> "Hot_Water", "heating" -> "Heating"
    mode_display = mode.replace("_", " ").title().replace(" ", "_")
    sensor_name = f"{mode_display} Energy {period.title()}"
    
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
    
    Einfacher Delta-Ansatz: Alle Sensoren (total, daily, monthly, yearly) bekommen
    das gleiche Delta addiert: sensor.value = sensor.value + delta
    
    Args:
        hass: HomeAssistant instance
        mode: One of ["heating", "hot_water", "cooling", "defrost", "stby"]
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
    
    if energy_delta < 0.001:
        _LOGGER.debug("Energy delta %.6f is too small, skipping increment", energy_delta)
        return

    device_prefix = f"hp{hp_index}"
    
    # Alle Sensor-Perioden, die aktualisiert werden sollen
    sensor_periods = ["total", "daily", "monthly", "yearly", "2h", "4h"]
    changes_summary = []
    
    for period in sensor_periods:
        # Generiere Entity-ID für diesen Sensor
        names = generate_energy_sensor_names(
            device_prefix, mode, period, name_prefix, use_legacy_modbus_names
        )
        entity_id = names["entity_id"]

        # Prüfe ob Entity registriert ist
        entity_registry = async_get_entity_registry(hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None:
            coordinator = _get_coordinator(hass)
            if coordinator:
                warning_count = coordinator._energy_warnings.get(entity_id, 0)
                coordinator._energy_warnings[entity_id] = warning_count + 1
                if warning_count < coordinator._max_energy_warnings:
                    _LOGGER.debug(
                        f"Energy entity {entity_id} not yet registered "
                        f"(attempt {warning_count + 1}/{coordinator._max_energy_warnings})"
                    )
            continue

        # Prüfe ob State verfügbar ist
        state_obj = hass.states.get(entity_id)
        if state_obj is None:
            continue

        # Reset Warning Counter bei erfolgreicher Registrierung
        coordinator = _get_coordinator(hass)
        if coordinator and entity_id in coordinator._energy_warnings:
            del coordinator._energy_warnings[entity_id]

        # Hole aktuellen Wert des Sensors
        if state_obj.state in (None, STATE_UNKNOWN, "unknown"):
            current_value = 0.0
        else:
            try:
                current_value = float(state_obj.state)
            except Exception:
                current_value = 0.0

        # Finde die Entity-Instanz
        energy_entity = None
        try:
            for entry_id, comp_data in hass.data.get("lambda_heat_pumps", {}).items():
                if isinstance(comp_data, dict) and "energy_entities" in comp_data:
                    energy_entity = comp_data["energy_entities"].get(entity_id)
                    if energy_entity:
                        break
        except Exception as e:
            _LOGGER.debug(f"Error searching for energy entity {entity_id}: {e}")

        # Berechne neuen Wert: Einfache Delta-Addition
        new_value = current_value + energy_delta
        
        # Offset nur für Total-Sensor berücksichtigen
        if period == "total" and energy_offsets is not None:
            device_key = device_prefix
            if device_key in energy_offsets:
                device_offsets = energy_offsets[device_key]
                if isinstance(device_offsets, dict):
                    sensor_id = f"{mode}_energy_total"
                    offset = float(device_offsets.get(sensor_id, 0.0))
                    # Prüfe ob Offset bereits angewendet wurde
                    if hasattr(energy_entity, "_applied_offset"):
                        if energy_entity._applied_offset != offset:
                            new_value += offset - energy_entity._applied_offset
                            energy_entity._applied_offset = offset
                            _LOGGER.info(f"Applied offset {offset:.2f} kWh to {entity_id}")

        # Setze neuen Wert
        if energy_entity is not None and hasattr(energy_entity, "set_energy_value"):
            energy_entity.set_energy_value(new_value)
            if abs(new_value - current_value) > 0.001:
                changes_summary.append(
                    f"{entity_id} = {new_value:.2f} kWh (was {current_value:.2f})"
                )
        else:
            # Fallback: State setzen
            _LOGGER.debug(f"Using fallback state update for {entity_id}")
            hass.states.async_set(
                entity_id, new_value, state_obj.attributes if state_obj else {}
            )
            if abs(new_value - current_value) > 0.001:
                changes_summary.append(
                    f"{entity_id} = {new_value:.2f} kWh (was {current_value:.2f})"
                )

        # Optional: Entity zum Update zwingen
        try:
            await async_update_entity(hass, entity_id)
        except Exception as e:
            _LOGGER.debug(f"Could not force update for {entity_id}: {e}")

    # Zentrale Logging-Meldung nur bei tatsächlichen Änderungen
    if changes_summary:
        _LOGGER.info(
            f"Energy counters updated for {mode} HP{hp_index}: {', '.join(changes_summary)} (delta {energy_delta:.2f} kWh)"
        )


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


def validate_external_sensors(hass: HomeAssistant, energy_sensor_configs: dict) -> dict:
    """
    Validiere externe Sensoren und gib bereinigte Konfiguration zurück.
    
    Args:
        hass: Home Assistant Instanz
        energy_sensor_configs: Dictionary mit Sensor-Konfigurationen
    
    Returns:
        dict: Bereinigte Konfiguration (fehlerhafte Sensoren entfernt)
    """
    validated_configs = {}
    fallback_used = False
    
    for hp_key, sensor_config in energy_sensor_configs.items():
        sensor_id = sensor_config.get("sensor_entity_id")
        
        if not sensor_id:
            _LOGGER.warning(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Keine sensor_entity_id konfiguriert")
            continue
        
        # Prüfe ob Sensor existiert
        sensor_state = hass.states.get(sensor_id)
        
        if sensor_state is None:
            # Sensor nicht im State gefunden - prüfe Entity Registry
            _LOGGER.warning(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' "
                f"nicht im State gefunden, prüfe Entity Registry..."
            )
            
            entity_registry = async_get_entity_registry(hass)
            entity_entry = entity_registry.async_get(sensor_id)
            
            if entity_entry is None:
                # Sensor existiert weder im State noch in der Registry
                _LOGGER.error(
                    f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' "
                    f"existiert weder im State noch in der Entity Registry!"
                )
                _LOGGER.error(
                    f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Bitte prüfen Sie die Sensor-ID "
                    f"in lambda_wp_config.yaml"
                )
                _LOGGER.error(
                    f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Fallback auf internen Modbus-Sensor"
                )
                fallback_used = True
                continue
            
            # Sensor existiert in Registry, aber noch nicht im State
            # Akzeptiere ihn trotzdem - er wird beim Start möglicherweise noch geladen
            # Die Verbrauchsberechnung wartet dann automatisch auf den ersten Wert
            # (ähnlich wie _energy_first_value_seen Mechanismus)
            _LOGGER.info(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' "
                f"in Entity Registry gefunden, aber noch nicht im State verfügbar"
            )
            _LOGGER.info(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor wird akzeptiert und "
                f"wird zur Verbrauchsberechnung verwendet (kann beim Start noch nicht verfügbar sein)"
            )
            _LOGGER.info(
                f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Zero-Value Protection wird automatisch "
                f"aktiviert bis Sensor verfügbar ist (wie bei _energy_first_value_seen)"
            )
            
            # Sensor ist gültig (existiert in Registry)
            validated_configs[hp_key] = sensor_config
            continue
        
        # Prüfe ob Sensor verfügbar ist
        if sensor_state.state in ("unknown", "unavailable", None):
            _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' ist nicht verfügbar (State: {sensor_state.state})")
            _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor wird trotzdem verwendet, aber Zero-Value Protection aktiviert")
        
        # Sensor ist gültig
        validated_configs[hp_key] = sensor_config
        _LOGGER.info(f"EXTERNAL-SENSOR-VALIDATION: {hp_key} - Sensor '{sensor_id}' ist gültig und verfügbar - wird zur Verbrauchsberechnung verwendet")
    
    if fallback_used:
        _LOGGER.info("EXTERNAL-SENSOR-VALIDATION: Einige externe Sensoren sind fehlerhaft - verwende interne Modbus-Sensoren als Fallback")
    
    return validated_configs


# =============================================================================
# Reset-Signal Factory Functions
# =============================================================================

def create_reset_signal(sensor_type: str, period: str) -> str:
    """
    Erstellt ein standardisiertes Reset-Signal für einen Sensor-Typ und eine Periode.
    
    Args:
        sensor_type: Art des Sensors ('cycling', 'energy', 'general')
        period: Reset-Periode ('daily', '2h', '4h')
        
    Returns:
        Signal-Name: 'lambda_heat_pumps_reset_{period}_{sensor_type}'
        
    Raises:
        ValueError: Wenn sensor_type oder period ungültig ist
    """
    # Validiere sensor_type
    valid_sensor_types = ['cycling', 'energy', 'general']
    if sensor_type not in valid_sensor_types:
        raise ValueError(f"Ungültiger sensor_type: {sensor_type}. Erlaubt: {valid_sensor_types}")
    
    # Validiere period
    valid_periods = ['daily', '2h', '4h']
    if period not in valid_periods:
        raise ValueError(f"Ungültige period: {period}. Erlaubt: {valid_periods}")
    
    return f"lambda_heat_pumps_reset_{period}_{sensor_type}"


def get_reset_signal_for_period(period: str) -> str:
    """
    Holt das korrekte Reset-Signal für eine Periode (rückwärtskompatibel).
    
    Args:
        period: Reset-Periode ('daily', '2h', '4h')
        
    Returns:
        Signal-Name: 'lambda_heat_pumps_reset_{period}'
        
    Raises:
        ValueError: Wenn period ungültig ist
    """
    # Validiere period
    valid_periods = ['daily', '2h', '4h']
    if period not in valid_periods:
        raise ValueError(f"Ungültige period: {period}. Erlaubt: {valid_periods}")
    
    return f"lambda_heat_pumps_reset_{period}"


def get_all_reset_signals() -> dict:
    """
    Gibt alle verfügbaren Reset-Signale zurück.
    
    Returns:
        Dictionary mit allen Signal-Kombinationen
    """
    sensor_types = ['cycling', 'energy', 'general']
    periods = ['daily', '2h', '4h']
    
    signals = {}
    for sensor_type in sensor_types:
        signals[sensor_type] = {}
        for period in periods:
            signals[sensor_type][period] = create_reset_signal(sensor_type, period)
    
    return signals


def validate_reset_signal(signal: str) -> bool:
    """
    Validiert ob ein Signal ein gültiges Reset-Signal ist.
    
    Args:
        signal: Zu validierendes Signal
        
    Returns:
        True wenn gültig, False sonst
    """
    if not isinstance(signal, str):
        return False
    
    # Prüfe Format: lambda_heat_pumps_reset_{period}_{sensor_type}
    parts = signal.split('_')
    if len(parts) < 4:
        return False
    
    if parts[0] != 'lambda' or parts[1] != 'heat' or parts[2] != 'pumps' or parts[3] != 'reset':
        return False
    
    # Prüfe ob es ein spezifisches Signal ist (mit sensor_type)
    if len(parts) == 6:  # lambda_heat_pumps_reset_{period}_{sensor_type}
        period = parts[4]
        sensor_type = parts[5]
        return period in ['daily', '2h', '4h'] and sensor_type in ['cycling', 'energy', 'general']
    
    # Prüfe ob es ein allgemeines Signal ist (ohne sensor_type)
    elif len(parts) == 5:  # lambda_heat_pumps_reset_{period}
        period = parts[4]
        return period in ['daily', '2h', '4h']
    
    return False


# =============================================================================
# Sensor Reset Registry
# =============================================================================

class SensorResetRegistry:
    """
    Zentrales Registry für alle Sensor-Reset-Handler.
    
    Verwaltet die Registrierung von Sensoren für automatische Resets
    und sendet Reset-Signale an alle registrierten Sensoren.
    """
    
    def __init__(self):
        """Initialisiert das Registry."""
        self._handlers = {}  # {sensor_type: {entry_id: {period: callback}}}
        self._hass = None
    
    def set_hass(self, hass: HomeAssistant):
        """Setzt die Home Assistant Instanz."""
        self._hass = hass
    
    def register(self, sensor_type: str, entry_id: str, period: str, callback) -> None:
        """
        Registriert einen Sensor für automatische Resets.
        
        Args:
            sensor_type: Art des Sensors ('cycling', 'energy', 'general')
            entry_id: Entry ID des Sensors
            period: Reset-Periode ('daily', '2h', '4h')
            callback: Callback-Funktion für Reset
        """
        if sensor_type not in self._handlers:
            self._handlers[sensor_type] = {}
        
        if entry_id not in self._handlers[sensor_type]:
            self._handlers[sensor_type][entry_id] = {}
        
        self._handlers[sensor_type][entry_id][period] = callback
        
        _LOGGER.debug(
            "Sensor registriert: %s/%s/%s -> %s",
            sensor_type, entry_id, period, callback.__name__ if hasattr(callback, '__name__') else str(callback)
        )
    
    def unregister(self, sensor_type: str, entry_id: str, period: str = None) -> None:
        """
        Entfernt einen Sensor aus der Registrierung.
        
        Args:
            sensor_type: Art des Sensors
            entry_id: Entry ID des Sensors
            period: Reset-Periode (optional, entfernt alle Perioden wenn None)
        """
        if sensor_type not in self._handlers:
            return
        
        if entry_id not in self._handlers[sensor_type]:
            return
        
        if period is None:
            # Entferne alle Perioden für diesen Sensor
            del self._handlers[sensor_type][entry_id]
            _LOGGER.debug("Alle Sensoren entfernt: %s/%s", sensor_type, entry_id)
        else:
            # Entferne nur die spezifische Periode
            if period in self._handlers[sensor_type][entry_id]:
                del self._handlers[sensor_type][entry_id][period]
                _LOGGER.debug("Sensor entfernt: %s/%s/%s", sensor_type, entry_id, period)
    
    def get_signal(self, sensor_type: str, period: str) -> str:
        """
        Holt das korrekte Reset-Signal für einen Sensor-Typ.
        
        Args:
            sensor_type: Art des Sensors
            period: Reset-Periode
            
        Returns:
            Signal-Name
        """
        return create_reset_signal(sensor_type, period)
    
    def send_reset(self, sensor_type: str, period: str, entry_id: str = None) -> int:
        """
        Sendet Reset-Signal an alle registrierten Sensoren.
        
        Args:
            sensor_type: Art des Sensors
            period: Reset-Periode
            entry_id: Entry ID (optional, sendet an alle wenn None)
            
        Returns:
            Anzahl der aufgerufenen Callbacks
        """
        if not self._hass:
            _LOGGER.error("Home Assistant Instanz nicht gesetzt")
            return 0
        
        if sensor_type not in self._handlers:
            _LOGGER.debug("Keine Handler für %s registriert", sensor_type)
            return 0
        
        callbacks_called = 0
        
        # Sende an alle Entry IDs für diesen Sensor-Typ
        for eid, periods in self._handlers[sensor_type].items():
            if entry_id is not None and eid != entry_id:
                continue  # Überspringe andere Entry IDs wenn spezifische angefordert
            
            if period in periods:
                callback = periods[period]
                try:
                    # Rufe Callback asynchron auf
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback())
                    else:
                        callback()
                    callbacks_called += 1
                    _LOGGER.debug("Reset-Callback aufgerufen: %s/%s/%s", sensor_type, eid, period)
                except Exception as e:
                    _LOGGER.error("Fehler beim Aufrufen des Reset-Callbacks: %s", e)
        
        _LOGGER.debug("Reset-Signal gesendet: %s/%s -> %d Callbacks", sensor_type, period, callbacks_called)
        return callbacks_called
    
    def send_reset_to_all(self, period: str, entry_id: str = None) -> int:
        """
        Sendet Reset-Signal an alle registrierten Sensor-Typen.
        
        Args:
            period: Reset-Periode
            entry_id: Entry ID (optional, sendet an alle wenn None)
            
        Returns:
            Gesamtanzahl der aufgerufenen Callbacks
        """
        total_callbacks = 0
        
        for sensor_type in self._handlers.keys():
            callbacks = self.send_reset(sensor_type, period, entry_id)
            total_callbacks += callbacks
        
        _LOGGER.debug("Reset-Signal an alle gesendet: %s -> %d Callbacks", period, total_callbacks)
        return total_callbacks
    
    def get_registered_sensors(self) -> dict:
        """
        Gibt alle registrierten Sensoren zurück.
        
        Returns:
            Dictionary mit allen registrierten Sensoren
        """
        return self._handlers.copy()
    
    def get_sensor_count(self, sensor_type: str = None) -> int:
        """
        Gibt die Anzahl der registrierten Sensoren zurück.
        
        Args:
            sensor_type: Sensor-Typ (optional, zählt alle wenn None)
            
        Returns:
            Anzahl der registrierten Sensoren
        """
        if sensor_type is None:
            total = 0
            for handlers in self._handlers.values():
                for periods in handlers.values():
                    total += len(periods)
            return total
        
        if sensor_type not in self._handlers:
            return 0
        
        total = 0
        for periods in self._handlers[sensor_type].values():
            total += len(periods)
        return total
    
    def clear(self) -> None:
        """Löscht alle Registrierungen."""
        self._handlers.clear()
        _LOGGER.debug("Alle Registrierungen gelöscht")


# Globale Registry-Instanz
_sensor_reset_registry = SensorResetRegistry()


def get_sensor_reset_registry() -> SensorResetRegistry:
    """
    Holt die globale Sensor Reset Registry Instanz.
    
    Returns:
        SensorResetRegistry Instanz
    """
    return _sensor_reset_registry


def register_sensor_reset_handler(hass: HomeAssistant, sensor_type: str, entry_id: str, period: str, callback) -> None:
    """
    Registriert einen Sensor für automatische Resets (Convenience-Funktion).
    
    Args:
        hass: Home Assistant Instanz
        sensor_type: Art des Sensors
        entry_id: Entry ID des Sensors
        period: Reset-Periode
        callback: Callback-Funktion für Reset
    """
    registry = get_sensor_reset_registry()
    registry.set_hass(hass)
    registry.register(sensor_type, entry_id, period, callback)


def unregister_sensor_reset_handler(sensor_type: str, entry_id: str, period: str = None) -> None:
    """
    Entfernt einen Sensor aus der Registrierung (Convenience-Funktion).
    
    Args:
        sensor_type: Art des Sensors
        entry_id: Entry ID des Sensors
        period: Reset-Periode (optional)
    """
    registry = get_sensor_reset_registry()
    registry.unregister(sensor_type, entry_id, period)


def send_reset_signal(sensor_type: str, period: str, entry_id: str = None) -> int:
    """
    Sendet Reset-Signal an registrierte Sensoren (Convenience-Funktion).
    
    Args:
        sensor_type: Art des Sensors
        period: Reset-Periode
        entry_id: Entry ID (optional)
        
    Returns:
        Anzahl der aufgerufenen Callbacks
    """
    registry = get_sensor_reset_registry()
    return registry.send_reset(sensor_type, period, entry_id)


# =============================================================================
# ENERGY CONSUMPTION HELPER FUNCTIONS
# =============================================================================

def get_energy_consumption_periods():
    """Get all energy consumption periods."""
    try:
        from .const import ENERGY_CONSUMPTION_PERIODS
        return ENERGY_CONSUMPTION_PERIODS
    except ImportError:
        # Fallback für direkte Ausführung
        from const import ENERGY_CONSUMPTION_PERIODS
        return ENERGY_CONSUMPTION_PERIODS

def get_energy_consumption_reset_intervals():
    """Get all energy consumption reset intervals."""
    try:
        from .const import ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    except ImportError:
        # Fallback für direkte Ausführung
        from const import ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    
    return sorted(list(set(
        template["reset_interval"] 
        for template in templates.values()
        if template.get("reset_interval") is not None
    )))

def get_all_reset_intervals():
    """Get all reset intervals from all sensor templates."""
    try:
        from .const import CALCULATED_SENSOR_TEMPLATES, ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        cycling_templates = CALCULATED_SENSOR_TEMPLATES
        energy_templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    except ImportError:
        # Fallback für direkte Ausführung
        from const import CALCULATED_SENSOR_TEMPLATES, ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        cycling_templates = CALCULATED_SENSOR_TEMPLATES
        energy_templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    
    all_intervals = set()
    
    # From cycling templates
    for template in cycling_templates.values():
        if template.get("reset_interval") is not None:
            all_intervals.add(template["reset_interval"])
    
    # From energy consumption templates
    for template in energy_templates.values():
        if template.get("reset_interval") is not None:
            all_intervals.add(template["reset_interval"])
    
    return sorted(list(all_intervals))

def get_all_periods():
    """Get all periods from all sensor templates."""
    try:
        from .const import CALCULATED_SENSOR_TEMPLATES, ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        cycling_templates = CALCULATED_SENSOR_TEMPLATES
        energy_templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    except ImportError:
        # Fallback für direkte Ausführung
        from const import CALCULATED_SENSOR_TEMPLATES, ENERGY_CONSUMPTION_SENSOR_TEMPLATES
        cycling_templates = CALCULATED_SENSOR_TEMPLATES
        energy_templates = ENERGY_CONSUMPTION_SENSOR_TEMPLATES
    
    all_periods = set()
    
    # From cycling templates
    for template in cycling_templates.values():
        if template.get("period") is not None:
            all_periods.add(template["period"])
    
    # From energy consumption templates
    for template in energy_templates.values():
        if template.get("period") is not None:
            all_periods.add(template["period"])
    
    # Add monthly and yearly periods
    all_periods.add("monthly")
    all_periods.add("yearly")
    
    return sorted(list(all_periods))


# =============================================================================
# SENSOR CHANGE DETECTION HELPER FUNCTIONS
# =============================================================================

def detect_sensor_change(stored_sensor_id: str, current_sensor_id: str) -> bool:
    """Erkenne Sensor-Wechsel durch Vergleich der gespeicherten und aktuellen Sensor-IDs.
    
    Args:
        stored_sensor_id: Die zuletzt gespeicherte Sensor-ID (kann None sein)
        current_sensor_id: Die aktuelle Sensor-ID aus der Konfiguration
    
    Returns:
        bool: True wenn ein Sensor-Wechsel erkannt wurde
    """
    # Normalisiere die Strings (entferne führende/nachfolgende Leerzeichen und Anführungszeichen)
    stored_normalized = str(stored_sensor_id).strip().strip("'\"") if stored_sensor_id else None
    current_normalized = str(current_sensor_id).strip().strip("'\"") if current_sensor_id else None
    
    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Prüfe Sensor-Wechsel - gespeichert: '{stored_normalized}', aktuell: '{current_normalized}'")
    
    # Wenn kein gespeicherter Sensor vorhanden ist, ist es kein Wechsel
    if not stored_normalized:
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Kein gespeicherter Sensor für Vergleich vorhanden")
        return False
    
    # Wenn die IDs unterschiedlich sind, ist es ein Wechsel
    is_change = stored_normalized != current_normalized
    if is_change:
        _LOGGER.warning(f"SENSOR-CHANGE-DETECTION: Sensor wurde gewechselt - '{stored_normalized}' -> '{current_normalized}'. {current_normalized} wird zur Verbrauchsberechnung verwendet")
    else:
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Kein Sensor-Wechsel - IDs identisch")
    
    return is_change


def get_stored_sensor_id(persist_data: dict, hp_idx: int) -> str:
    """Hole die gespeicherte Sensor-ID für eine Wärmepumpe aus den persistierten Daten.
    
    Args:
        persist_data: Die persistierten Daten aus cycle_energy_persist.json
        hp_idx: Der Index der Wärmepumpe (1, 2, 3, ...)
    
    Returns:
        str: Die gespeicherte Sensor-ID oder None wenn nicht vorhanden
    """
    hp_key = f"hp{hp_idx}"
    sensor_ids = persist_data.get("sensor_ids", {})
    stored_id = sensor_ids.get(hp_key)
    
    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Gespeicherte Sensor-ID für {hp_key}: '{stored_id}'")
    return stored_id


def store_sensor_id(persist_data: dict, hp_idx: int, sensor_id: str) -> None:
    """Speichere die Sensor-ID für eine Wärmepumpe in den persistierten Daten.
    
    Args:
        persist_data: Die persistierten Daten (wird modifiziert)
        hp_idx: Der Index der Wärmepumpe (1, 2, 3, ...)
        sensor_id: Die Sensor-ID die gespeichert werden soll
    """
    hp_key = f"hp{hp_idx}"
    
    # Normalisiere die Sensor-ID (entferne führende/nachfolgende Leerzeichen und Anführungszeichen)
    normalized_sensor_id = str(sensor_id).strip().strip("'\"") if sensor_id else None
    
    # Stelle sicher, dass sensor_ids existiert
    if "sensor_ids" not in persist_data:
        persist_data["sensor_ids"] = {}
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Erstelle neue sensor_ids Sektion in persistierten Daten")
    
    # Speichere die normalisierte Sensor-ID
    old_id = persist_data["sensor_ids"].get(hp_key)
    persist_data["sensor_ids"][hp_key] = normalized_sensor_id
    
    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Sensor-ID für {hp_key} gespeichert: '{old_id}' -> '{normalized_sensor_id}'")


async def async_cleanup_all_components(hass: HomeAssistant, entry_id: str) -> None:
    """Zentrale Shutdown-Funktion für alle Lambda Heat Pumps Komponenten.
    
    Args:
        hass: Home Assistant instance
        entry_id: Config entry ID to cleanup
    """
    _LOGGER.info("🧹 CLEANUP: Starting centralized cleanup for entry: %s", entry_id)
    
    try:
        # 1. Cleanup Coordinator
        if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
            coordinator_data = hass.data[DOMAIN][entry_id]
            if "coordinator" in coordinator_data:
                coordinator = coordinator_data["coordinator"]
                _LOGGER.info("🧹 CLEANUP: Shutting down coordinator (coordinator_id=%s)", id(coordinator))
                try:
                    await coordinator.async_shutdown()
                    _LOGGER.info("✅ CLEANUP: Coordinator shutdown completed")
                except Exception as coord_ex:
                    _LOGGER.error("❌ CLEANUP: Error during coordinator shutdown: %s", coord_ex)
                finally:
                    # Entferne Coordinator aus hass.data
                    coordinator_data.pop("coordinator", None)
        
        # 2. Cleanup Services
        try:
            from .services import async_unload_services
            _LOGGER.info("🧹 CLEANUP: Unloading services...")
            await async_unload_services(hass)
            _LOGGER.info("✅ CLEANUP: Services unloaded")
        except Exception as service_ex:
            _LOGGER.error("❌ CLEANUP: Error during services cleanup: %s", service_ex)
        
        # 3. Cleanup Automations
        try:
            from .automations import cleanup_cycling_automations
            _LOGGER.info("🧹 CLEANUP: Cleaning up automations...")
            cleanup_cycling_automations(hass, entry_id)
            _LOGGER.info("✅ CLEANUP: Automations cleaned up")
        except Exception as auto_ex:
            _LOGGER.error("❌ CLEANUP: Error during automations cleanup: %s", auto_ex)
        
        # 4. Remove entry from hass.data
        if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry_id, None)
            _LOGGER.info("✅ CLEANUP: Entry removed from hass.data")
        
        # 5. Final cleanup check
        if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
            _LOGGER.warning("⚠️ CLEANUP: Entry still exists in hass.data after cleanup")
        else:
            _LOGGER.info("✅ CLEANUP: Entry successfully removed from hass.data")
            
    except Exception as ex:
        _LOGGER.error("❌ CLEANUP: Error during centralized cleanup: %s", ex)
        raise
    
    _LOGGER.info("🎉 CLEANUP: Centralized cleanup completed for entry: %s", entry_id)