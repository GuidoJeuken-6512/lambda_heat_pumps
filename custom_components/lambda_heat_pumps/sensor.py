"""Platform for Lambda WP sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.template import Template
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.dispatcher import async_dispatcher_connect


from .const import (
    DOMAIN,
    SENSOR_TYPES,
    HP_SENSOR_TEMPLATES,
    BOIL_SENSOR_TEMPLATES,
    HC_SENSOR_TEMPLATES,
    BUFF_SENSOR_TEMPLATES,
    SOL_SENSOR_TEMPLATES,
    CALCULATED_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_SENSOR_TEMPLATES,
    ENERGY_CONSUMPTION_MODES,
    ENERGY_CONSUMPTION_PERIODS,
)
from .coordinator import LambdaDataUpdateCoordinator
from .utils import (
    build_device_info,
    build_subdevice_info,
    extract_device_info_from_sensor_id,
    generate_base_addresses,
    generate_sensor_names,
    load_sensor_translations,
    get_firmware_version_int,
    get_compatible_sensors,
    get_entity_icon,
)
from .const_mapping import HP_ERROR_STATE  # noqa: F401
from .const_mapping import HP_STATE  # noqa: F401

from .const_mapping import HP_RELAIS_STATE_2ND_HEATING_STAGE  # noqa: F401
from .const_mapping import HP_OPERATING_STATE  # noqa: F401
from .const_mapping import HP_REQUEST_TYPE  # noqa: F401
from .const_mapping import BOIL_CIRCULATION_PUMP_STATE  # noqa: F401
from .const_mapping import BOIL_OPERATING_STATE  # noqa: F401
from .const_mapping import HC_OPERATING_STATE  # noqa: F401
from .const_mapping import HC_OPERATING_MODE  # noqa: F401
from .const_mapping import BUFF_OPERATING_STATE  # noqa: F401
from .const_mapping import BUFF_REQUEST_TYPE  # noqa: F401
from .const_mapping import SOL_OPERATING_STATE  # noqa: F401
from .const_mapping import MAIN_CIRCULATION_PUMP_STATE  # noqa: F401
from .const_mapping import MAIN_AMBIENT_OPERATING_STATE  # noqa: F401
from .const_mapping import MAIN_E_MANAGER_OPERATING_STATE  # noqa: F401

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lambda Heat Pumps sensors."""
    _LOGGER.debug("Setting up Lambda sensors for entry %s", entry.entry_id)

    # Get coordinator from hass.data
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    if not coordinator_data or "coordinator" not in coordinator_data:
        _LOGGER.error("No coordinator found for entry %s", entry.entry_id)
        return

    coordinator = coordinator_data["coordinator"]
    _LOGGER.debug("Found coordinator: %s", coordinator)

    # Get device counts from config
    num_hps = entry.data.get("num_hps", 1)
    num_boil = entry.data.get("num_boil", 1)
    num_buff = entry.data.get("num_buff", 0)
    num_sol = entry.data.get("num_sol", 0)
    num_hc = entry.data.get("num_hc", 1)

    # Hole den Legacy-Modbus-Namen-Switch aus der Config
    use_legacy_modbus_names = entry.data.get("use_legacy_modbus_names", True)
    name_prefix = entry.data.get("name", "").lower().replace(" ", "")
    sensor_translations = await load_sensor_translations(hass)

    # Get firmware version and filter compatible sensors
    fw_version = get_firmware_version_int(entry)
    _LOGGER.debug(
        "Filtering sensors for firmware version (numeric: %d)",
        fw_version,
    )

    # Create sensors for each device type using a generic loop
    sensors = []

    TEMPLATES = [
        ("hp", num_hps, get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)),
        ("boil", num_boil, get_compatible_sensors(BOIL_SENSOR_TEMPLATES, fw_version)),
        ("buff", num_buff, get_compatible_sensors(BUFF_SENSOR_TEMPLATES, fw_version)),
        ("sol", num_sol, get_compatible_sensors(SOL_SENSOR_TEMPLATES, fw_version)),
        ("hc", num_hc, get_compatible_sensors(HC_SENSOR_TEMPLATES, fw_version)),
    ]

    for prefix, count, template in TEMPLATES:
        for idx in range(1, count + 1):
            base_address = generate_base_addresses(prefix, count)[idx]
            # Always use lowercased name_prefix for all entity_id/unique_id generation
            name_prefix_lc = name_prefix.lower() if name_prefix else ""
            for sensor_id, sensor_info in template.items():
                address = base_address + sensor_info["relative_address"]
                if coordinator.is_register_disabled(address):
                    _LOGGER.debug(
                        "Skipping sensor %s (address %d) because register is disabled",
                        f"{prefix}{idx}_{sensor_id}",
                        address,
                    )
                    continue

                device_class = sensor_info.get("device_class")
                if not device_class and sensor_info.get("unit") == "°C":
                    device_class = SensorDeviceClass.TEMPERATURE
                elif not device_class and sensor_info.get("unit") == "W":
                    device_class = SensorDeviceClass.POWER
                elif not device_class and sensor_info.get("unit") == "Wh":
                    device_class = SensorDeviceClass.ENERGY
                elif not device_class and sensor_info.get("unit") == "kWh":
                    device_class = SensorDeviceClass.ENERGY

                # Prüfe auf Override-Name
                override_name = None
                if use_legacy_modbus_names and hasattr(coordinator, "sensor_overrides"):
                    override_name = coordinator.sensor_overrides.get(
                        f"{prefix}{idx}_{sensor_id}"
                    )
                if override_name:
                    name = override_name
                    sensor_id_final = f"{prefix}{idx}_{sensor_id}"
                    # Data key (original format)
                    entity_id = f"sensor.{name_prefix_lc}_{override_name}"
                    unique_id = f"{name_prefix_lc}_{override_name}"
                else:
                    device_prefix = f"{prefix}{idx}"

                    # Verwende die zentrale Namensgenerierung
                    names = generate_sensor_names(
                        device_prefix,
                        sensor_info["name"],
                        sensor_id,
                        name_prefix,
                        use_legacy_modbus_names,
                        translations=sensor_translations,
                    )

                    sensor_id_final = f"{prefix}{idx}_{sensor_id}"
                    entity_id = names["entity_id"]
                    unique_id = names["unique_id"]
                    name = names["name"]

                device_type = (
                    prefix.upper()
                    if prefix
                    in [
                        "hp",
                        "boil",
                        "hc",
                        "buff",
                        "sol",
                    ]
                    else sensor_info.get("device_type", "main")
                )

                sensors.append(
                    LambdaSensor(
                        coordinator=coordinator,
                        entry=entry,
                        sensor_id=sensor_id_final,
                        name=name,
                        unit=sensor_info.get("unit", ""),
                        address=address,
                        scale=sensor_info.get("scale", 1.0),
                        state_class=sensor_info.get("state_class", ""),
                        device_class=device_class,
                        relative_address=sensor_info.get("relative_address", 0),
                        data_type=sensor_info.get("data_type", ""),
                        device_type=device_type,
                        txt_mapping=sensor_info.get("txt_mapping", False),
                        precision=sensor_info.get("precision", None),
                        entity_id=entity_id,
                        unique_id=unique_id,
                        options=sensor_info.get("options", None),
                        sensor_info=sensor_info,
                    )
                )

    # General Sensors (SENSOR_TYPES)
    for sensor_id, sensor_info in SENSOR_TYPES.items():
        address = sensor_info["address"]
        if coordinator.is_register_disabled(address):
            _LOGGER.debug(
                "Skipping general sensor %s (address %d) because register is disabled",
                sensor_id,
                address,
            )
            continue
        device_class = sensor_info.get("device_class")
        if not device_class and sensor_info.get("unit") == "°C":
            device_class = SensorDeviceClass.TEMPERATURE
        elif not device_class and sensor_info.get("unit") == "W":
            device_class = SensorDeviceClass.POWER
        elif not device_class and sensor_info.get("unit") == "Wh":
            device_class = SensorDeviceClass.ENERGY
        elif not device_class and sensor_info.get("unit") == "kWh":
            device_class = SensorDeviceClass.ENERGY

        # Name und Entity-ID für General Sensors
        if use_legacy_modbus_names and "override_name" in sensor_info:
            override_name = sensor_info["override_name"]
            sensor_id_final = sensor_info["override_name"]
            _LOGGER.info(
                f"Override name for sensor '{sensor_id}': '{override_name}' "
                f"wird als Name und sensor_id verwendet."
            )
        else:
            override_name = None
            sensor_id_final = sensor_id

        # Verwende die zentrale Namensgenerierung für General Sensors
        # Für General Sensors ist der sensor_id der device_prefix
        names = generate_sensor_names(
            sensor_id,  # device_prefix für General Sensors ist der sensor_id
            sensor_info["name"],
            sensor_id_final,  # sensor_id für die Namensgenerierung
            name_prefix,
            use_legacy_modbus_names,
            translations=sensor_translations,
        )

        entity_id = names["entity_id"]
        unique_id = names["unique_id"]
        
        # Wenn override_name verwendet wird, nutze diesen; sonst den übersetzten Namen
        final_name = override_name if override_name else names["name"]

        sensors.append(
            LambdaSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id=sensor_id_final,
                name=final_name,  # Verwende override_name oder den übersetzten Namen
                unit=sensor_info.get("unit", ""),
                address=address,
                scale=sensor_info.get("scale", 1.0),
                state_class=sensor_info.get("state_class", ""),
                device_class=device_class,
                relative_address=sensor_info.get("address", 0),
                data_type=sensor_info.get("data_type", ""),
                device_type=sensor_info.get("device_type", "main"),
                txt_mapping=sensor_info.get("txt_mapping", False),
                precision=sensor_info.get("precision", None),
                entity_id=entity_id,
                unique_id=unique_id,
                options=sensor_info.get("options", None),
                sensor_info=sensor_info,
            )
        )

    # Extended/undocumented sensors sind jetzt direkt in HP_SENSOR_TEMPLATES integriert
    # --- Cycling Total Sensors (echte Entities, keine Templates) ---
    cycling_modes = [
        ("heating", "heating_cycling_total"),
        ("hot_water", "hot_water_cycling_total"),
        ("cooling", "cooling_cycling_total"),
        ("defrost", "defrost_cycling_total"),
        ("compressor_start", "compressor_start_cycling_total"),
    ]
    cycling_sensor_count = 0
    cycling_sensor_ids = []
    cycling_entities = {}  # Dictionary für schnellen Zugriff

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in cycling_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            # Entity-ID und unique_id generieren
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            cycling_sensor_ids.append(names["entity_id"])

            cycling_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(cycling_sensor)
            cycling_entities[names["entity_id"]] = cycling_sensor
            cycling_sensor_count += 1

    # --- Yesterday Cycling Sensors (echte Entities - speichern gestern Werte) ---
    yesterday_modes = [
        ("heating", "heating_cycling_yesterday"),
        ("hot_water", "hot_water_cycling_yesterday"),
        ("cooling", "cooling_cycling_yesterday"),
        ("defrost", "defrost_cycling_yesterday"),
    ]
    yesterday_sensor_count = 0
    yesterday_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in yesterday_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            # Entity-ID und unique_id generieren
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            yesterday_sensor_ids.append(names["entity_id"])

            yesterday_sensor = LambdaYesterdaySensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
                mode=mode,
            )

            sensors.append(yesterday_sensor)
            yesterday_sensor_count += 1

    # --- Daily Cycling Sensors (echte Entities - werden täglich um Mitternacht auf 0 gesetzt) ---
    daily_modes = [
        ("heating", "heating_cycling_daily"),
        ("hot_water", "hot_water_cycling_daily"),
        ("cooling", "cooling_cycling_daily"),
        ("defrost", "defrost_cycling_daily"),
        ("compressor_start", "compressor_start_cycling_daily"),
    ]
    daily_sensor_count = 0
    daily_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in daily_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            daily_sensor_ids.append(names["entity_id"])

            daily_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(daily_sensor)
            daily_sensor_count += 1

    # --- 2h Cycling Sensors (echte Entities - werden alle 2 Stunden auf 0 gesetzt) ---
    two_hour_modes = [
        ("heating", "heating_cycling_2h"),
        ("hot_water", "hot_water_cycling_2h"),
        ("cooling", "cooling_cycling_2h"),
        ("defrost", "defrost_cycling_2h"),
        ("compressor_start", "compressor_start_cycling_2h"),
    ]
    two_hour_sensor_count = 0
    two_hour_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in two_hour_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            two_hour_sensor_ids.append(names["entity_id"])

            two_hour_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(two_hour_sensor)
            two_hour_sensor_count += 1

    # --- 4h Cycling Sensors (echte Entities - werden alle 4 Stunden auf 0 gesetzt) ---
    four_hour_modes = [
        ("heating", "heating_cycling_4h"),
        ("hot_water", "hot_water_cycling_4h"),
        ("cooling", "cooling_cycling_4h"),
        ("defrost", "defrost_cycling_4h"),
        ("compressor_start", "compressor_start_cycling_4h"),
    ]
    four_hour_sensor_count = 0
    four_hour_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in four_hour_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            four_hour_sensor_ids.append(names["entity_id"])

            four_hour_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(four_hour_sensor)
            four_hour_sensor_count += 1

    # --- Monthly Cycling Sensors (echte Entities - werden am 1. des Monats auf 0 gesetzt) ---
    monthly_modes = [
        ("compressor_start", "compressor_start_cycling_monthly"),
    ]
    monthly_sensor_count = 0
    monthly_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in monthly_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names,
                translations=sensor_translations,
            )
            monthly_sensor_ids.append(names["entity_id"])

            monthly_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(monthly_sensor)
            monthly_sensor_count += 1

    # Speichere die Cycling-Entities für schnellen Zugriff
    if "lambda_heat_pumps" not in hass.data:
        hass.data["lambda_heat_pumps"] = {}
    if entry.entry_id not in hass.data["lambda_heat_pumps"]:
        hass.data["lambda_heat_pumps"][entry.entry_id] = {}
    
    # Erweitere cycling_entities um alle neuen Sensor-Typen
    all_cycling_entities = cycling_entities.copy()
    
    # Füge Yesterday-Sensoren hinzu
    for sensor in sensors:
        if hasattr(sensor, 'entity_id') and sensor.entity_id in yesterday_sensor_ids:
            all_cycling_entities[sensor.entity_id] = sensor
    
    # Füge Daily-Sensoren hinzu
    for sensor in sensors:
        if hasattr(sensor, 'entity_id') and sensor.entity_id in daily_sensor_ids:
            all_cycling_entities[sensor.entity_id] = sensor
    
    # Füge 2H-Sensoren hinzu
    for sensor in sensors:
        if hasattr(sensor, 'entity_id') and sensor.entity_id in two_hour_sensor_ids:
            all_cycling_entities[sensor.entity_id] = sensor
    
    # Füge 4H-Sensoren hinzu
    for sensor in sensors:
        if hasattr(sensor, 'entity_id') and sensor.entity_id in four_hour_sensor_ids:
            all_cycling_entities[sensor.entity_id] = sensor
    
    # Füge Monthly-Sensoren hinzu
    for sensor in sensors:
        if hasattr(sensor, 'entity_id') and sensor.entity_id in monthly_sensor_ids:
            all_cycling_entities[sensor.entity_id] = sensor
    
    hass.data["lambda_heat_pumps"][entry.entry_id]["cycling_entities"] = all_cycling_entities
    _LOGGER.info(
        "Total-Cycling-Sensoren erzeugt: %d, Entity-IDs: %s",
        cycling_sensor_count,
        cycling_sensor_ids,
    )
    _LOGGER.info(
        "Yesterday-Sensoren erzeugt: %d, Entity-IDs: %s",
        yesterday_sensor_count,
        yesterday_sensor_ids,
    )
    _LOGGER.info(
        "Daily-Sensoren erzeugt: %d, Entity-IDs: %s",
        daily_sensor_count,
        daily_sensor_ids,
    )
    _LOGGER.info(
        "2h-Sensoren erzeugt: %d, Entity-IDs: %s",
        two_hour_sensor_count,
        two_hour_sensor_ids,
    )
    _LOGGER.info(
        "4h-Sensoren erzeugt: %d, Entity-IDs: %s",
        four_hour_sensor_count,
        four_hour_sensor_ids,
    )

    # Energy consumption sensors (nur total und daily)
    for hp_idx in range(1, num_hps + 1):
        for mode in ENERGY_CONSUMPTION_MODES:
            for period in ENERGY_CONSUMPTION_PERIODS:
                sensor_id = f"{mode}_energy_{period}"
                sensor_template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES.get(sensor_id)
                if not sensor_template:
                    _LOGGER.warning(f"Template not found for {sensor_id}")
                    continue
                
                device_prefix = f"hp{hp_idx}"
                names = generate_sensor_names(
                    device_prefix,
                    sensor_template["name"],
                    sensor_id,
                    name_prefix,
                    use_legacy_modbus_names,
                    translations=sensor_translations,
                )
                
                sensor = LambdaEnergyConsumptionSensor(
                    hass,
                    entry,
                    sensor_id,
                    names["name"],
                    names["entity_id"],
                    names["unique_id"],
                    sensor_template["unit"],
                    sensor_template["state_class"],
                    sensor_template.get("device_class"),
                    sensor_template["device_type"],
                    hp_idx,
                    mode,
                    period,
                )
                sensors.append(sensor)
                _LOGGER.debug(f"Created energy consumption sensor: {names['entity_id']}")

    # Thermal energy sensors (per HP, per mode, per period)
    for hp_idx in range(1, num_hps + 1):
        for mode in ENERGY_CONSUMPTION_MODES:
            for period in ENERGY_CONSUMPTION_PERIODS:
                sensor_id = f"{mode}_thermal_energy_{period}"
                sensor_template = ENERGY_CONSUMPTION_SENSOR_TEMPLATES.get(sensor_id)
                if not sensor_template:
                    # Thermal energy sensors sind optional, kein Warning
                    continue
                
                # Prüfe ob es ein thermal_calculated Sensor ist
                if sensor_template.get("data_type") != "thermal_calculated":
                    continue
                
                device_prefix = f"hp{hp_idx}"
                names = generate_sensor_names(
                    device_prefix,
                    sensor_template["name"],
                    sensor_id,
                    name_prefix,
                    use_legacy_modbus_names,
                    translations=sensor_translations,
                )
                
                sensor = LambdaEnergyConsumptionSensor(
                    hass,
                    entry,
                    sensor_id,
                    names["name"],
                    names["entity_id"],
                    names["unique_id"],
                    sensor_template["unit"],
                    sensor_template["state_class"],
                    sensor_template.get("device_class"),
                    sensor_template["device_type"],
                    hp_idx,
                    mode,
                    period,
                )
                sensors.append(sensor)
                _LOGGER.debug(f"Created thermal energy consumption sensor: {names['entity_id']}")

    _LOGGER.info(
        "Alle Sensoren (inkl. Cycling und Energy Consumption) erzeugt: %d",
        len(sensors),
    )
    async_add_entities(sensors)
    
    # Registriere Energy Consumption Entities in hass.data für direkten Zugriff
    energy_entities = {}
    for sensor in sensors:
        if isinstance(sensor, LambdaEnergyConsumptionSensor):
            energy_entities[sensor.entity_id] = sensor
    
    # Speichere Energy Entities in hass.data
    if "energy_entities" not in coordinator_data:
        coordinator_data["energy_entities"] = {}
    coordinator_data["energy_entities"].update(energy_entities)
    
    _LOGGER.info(f"Registered {len(energy_entities)} energy consumption entities")

    # Load template sensors from template_sensor.py (parallel, non-blocking)
    from .template_sensor import async_setup_entry as setup_template_sensors

    async def setup_templates():
        try:
            await setup_template_sensors(hass, entry, async_add_entities)
        except Exception as e:
            _LOGGER.error("Error setting up template sensors: %s", e)

    # Starte Template Sensor Setup im Hintergrund (non-blocking)
    hass.async_create_task(setup_templates())
    _LOGGER.debug("Started template sensor setup in background")

    # Markiere Coordinator-Initialisierung als abgeschlossen
    # Dies ermöglicht die Flankenerkennung nach der Entity-Registrierung
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    if coordinator_data and "coordinator" in coordinator_data:
        coordinator = coordinator_data["coordinator"]
        coordinator.mark_initialization_complete()


# --- Entity-Klasse für Cycling Total Sensoren ---
class LambdaCyclingSensor(RestoreEntity, SensorEntity):
    """Cycling total sensor (echte Entity, Wert wird von increment_cycling_counter gesetzt)."""

    def __init__(
        self,
        hass,
        entry,
        sensor_id,
        name,
        entity_id,
        unique_id,
        unit,
        state_class,
        device_class,
        device_type,
        hp_index,
    ):
        self.hass = hass
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self.entity_id = entity_id
        self._unique_id = unique_id
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._hp_index = hp_index
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_name = name
        self._attr_unique_id = unique_id
        # Initialisiere cycling_value mit 0
        self._cycling_value = 0
        # Yesterday-Wert für Daily-Berechnung
        self._yesterday_value = 0
        # Last 2h-Wert für 2h-Berechnung
        self._last_2h_value = 0
        # Last 4h-Wert für 4h-Berechnung
        self._last_4h_value = 0
        # Signal-Unsubscribe-Funktionen
        self._unsub_dispatcher = None
        self._unsub_2h_dispatcher = None
        self._unsub_4h_dispatcher = None

        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None
        self._attr_device_class = device_class

    def set_cycling_value(self, value):
        """Set the cycling value and update state."""
        self._cycling_value = int(value)  # Stelle sicher, dass es ein Integer ist
        # Stelle sicher, dass der State korrekt aktualisiert wird
        self.async_write_ha_state()
        _LOGGER.debug(f"Cycling sensor {self.entity_id} value set to {value}")

    def update_yesterday_value(self):
        """Update yesterday value with current total value (called at midnight)."""
        old_yesterday = self._yesterday_value
        self._yesterday_value = self._cycling_value
        _LOGGER.info(
            f"Yesterday value updated for {self.entity_id}: {old_yesterday} -> {self._yesterday_value}"
        )

    def update_2h_value(self):
        """Update last 2h value with current total value (called every 2 hours)."""
        old_2h = self._last_2h_value
        self._last_2h_value = self._cycling_value
        _LOGGER.info(
            f"Last 2h value updated for {self.entity_id}: {old_2h} -> {self._last_2h_value}"
        )

    def update_4h_value(self):
        """Update last 4h value with current total value (called every 4 hours)."""
        old_4h = self._last_4h_value
        self._last_4h_value = self._cycling_value
        _LOGGER.info(
            f"Last 4h value updated for {self.entity_id}: {old_4h} -> {self._last_4h_value}"
        )

    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()

        # RestoreEntity provides async_get_last_state() method
        last_state = await self.async_get_last_state()
        await self.restore_state(last_state)

        # Registriere Signal-Handler für Reset-Signale
        from .automations import SIGNAL_RESET_DAILY, SIGNAL_RESET_2H, SIGNAL_RESET_4H, SIGNAL_RESET_MONTHLY, SIGNAL_RESET_YEARLY  # noqa: F401

        # Wrapper-Funktionen für asynchrone Handler mit @callback
        @callback
        def _wrap_daily_reset(entry_id: str):
            self.hass.async_create_task(self._handle_daily_reset(entry_id))
        
        @callback
        def _wrap_2h_reset(entry_id: str):
            self.hass.async_create_task(self._handle_2h_reset(entry_id))
        
        @callback
        def _wrap_4h_reset(entry_id: str):
            self.hass.async_create_task(self._handle_4h_reset(entry_id))
        
        @callback
        def _wrap_monthly_reset(entry_id: str):
            self.hass.async_create_task(self._handle_monthly_reset(entry_id))
        
        @callback
        def _wrap_yearly_reset(entry_id: str):
            self.hass.async_create_task(self._handle_yearly_reset(entry_id))

        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_DAILY, _wrap_daily_reset
        )
        self._unsub_2h_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_2H, _wrap_2h_reset
        )
        self._unsub_4h_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_4H, _wrap_4h_reset
        )
        self._unsub_monthly_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_MONTHLY, _wrap_monthly_reset
        )
        self._unsub_yearly_dispatcher = async_dispatcher_connect(
            self.hass, SIGNAL_RESET_YEARLY, _wrap_yearly_reset
        )

        # Schreibe den State sofort ins UI
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Clean up when entity is removed."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()
            self._unsub_dispatcher = None
        if self._unsub_2h_dispatcher:
            self._unsub_2h_dispatcher()
            self._unsub_2h_dispatcher = None
        if self._unsub_4h_dispatcher:
            self._unsub_4h_dispatcher()
            self._unsub_4h_dispatcher = None
        if self._unsub_monthly_dispatcher:
            self._unsub_monthly_dispatcher()
            self._unsub_monthly_dispatcher = None
        if self._unsub_yearly_dispatcher:
            self._unsub_yearly_dispatcher()
            self._unsub_yearly_dispatcher = None
        await super().async_will_remove_from_hass()

    async def restore_state(self, last_state):
        """Restore state from database to prevent reset on reload."""
        if last_state is not None:
            try:
                # Lade den letzten Wert aus der Datenbank
                last_value = last_state.state
                if last_value not in (None, "unknown", "unavailable"):
                    self._cycling_value = int(float(last_value))
                    _LOGGER.debug(
                        f"Cycling sensor {self.entity_id} restored from database: {self._cycling_value}"
                    )
                else:
                    # Fallback auf 0 nur wenn wirklich kein Wert in der DB
                    self._cycling_value = 0
                    _LOGGER.info(
                        f"Cycling sensor {self.entity_id} initialized with 0 (no previous state)"
                    )
                
                # Lade den bereits angewendeten Offset aus den Attributen
                if hasattr(last_state, 'attributes') and last_state.attributes:
                    self._applied_offset = last_state.attributes.get("applied_offset", 0)
                    _LOGGER.info(
                        f"Restored applied offset for {self.entity_id}: {self._applied_offset}"
                    )
                else:
                    self._applied_offset = 0
                    _LOGGER.info(
                        f"No applied offset found for {self.entity_id}, initializing with 0"
                    )
                    
            except (ValueError, TypeError) as e:
                _LOGGER.warning(
                    f"Could not restore state for {self.entity_id}: {e}, using 0"
                )
                self._cycling_value = 0
                self._applied_offset = 0
        else:
            # Kein vorheriger State vorhanden, initialisiere mit 0
            self._cycling_value = 0
            self._applied_offset = 0
            _LOGGER.info(
                f"Cycling sensor {self.entity_id} initialized with 0 (no previous state)"
            )

        # Stelle sicher, dass der Wert ein Integer ist
        self._cycling_value = int(self._cycling_value)
        
        # Wende Cycling-Offsets an (nur für Total-Sensoren und nur wenn noch nicht angewendet)
        if self._sensor_id.endswith("_total"):
            await self._apply_cycling_offset()

    async def _apply_cycling_offset(self):
        """Apply cycling offset from configuration."""
        try:
            # Lade die Cycling-Offsets aus der Konfiguration
            from .utils import load_lambda_config
            config = await load_lambda_config(self.hass)
            cycling_offsets = config.get("cycling_offsets", {})
            
            if not cycling_offsets:
                _LOGGER.debug(f"No cycling offsets found for {self.entity_id}")
                return
            
            # Bestimme den Device-Key (z.B. "hp1")
            device_key = f"hp{self._hp_index}"
            
            if device_key not in cycling_offsets:
                _LOGGER.debug(f"No cycling offsets found for device {device_key}")
                return
            
            # Hole den aktuellen Offset für diesen Sensor
            current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
            
            # Hole den bereits angewendeten Offset aus den Attributen
            applied_offset = getattr(self, "_applied_offset", 0)
            
            # Berechne die Differenz zwischen aktuellem und bereits angewendetem Offset
            offset_difference = current_offset - applied_offset
            
            # Debug-Log für bessere Nachverfolgung
            _LOGGER.debug(
                f"Offset calculation for {self.entity_id}: current={current_offset}, applied={applied_offset}, difference={offset_difference}"
            )
            
            if offset_difference != 0:
                old_value = self._cycling_value
                self._cycling_value = int(self._cycling_value + offset_difference)
                self._applied_offset = current_offset
                
                if offset_difference > 0:
                    _LOGGER.info(
                        f"Applied cycling offset change for {self.entity_id}: {old_value} + {offset_difference} = {self._cycling_value} (total offset: {current_offset})"
                    )
                else:
                    _LOGGER.info(
                        f"Applied cycling offset change for {self.entity_id}: {old_value} - {abs(offset_difference)} = {self._cycling_value} (total offset: {current_offset})"
                    )
                
                # Aktualisiere den State sofort
                self.async_write_ha_state()
            else:
                _LOGGER.debug(f"No offset change for {self.entity_id} (offset: {current_offset}, already applied: {applied_offset})")
                
        except Exception as e:
            _LOGGER.error(f"Error applying cycling offset for {self.entity_id}: {e}")

    async def _handle_daily_reset(self, entry_id: str):
        """Handle daily reset signal."""
        if entry_id == self._entry.entry_id and self._sensor_id.endswith("_daily"):
            # Daily-Sensoren auf 0 zurücksetzen
            self._cycling_value = 0
            self.async_write_ha_state()
            _LOGGER.info(f"Daily sensor {self.entity_id} reset to 0")

    async def _handle_2h_reset(self, entry_id: str):
        """Handle 2h reset signal."""
        if entry_id == self._entry.entry_id and self._sensor_id.endswith("_2h"):
            # 2H-Sensoren auf 0 zurücksetzen
            self._cycling_value = 0
            self.async_write_ha_state()
            _LOGGER.info(f"2H sensor {self.entity_id} reset to 0")

    async def _handle_4h_reset(self, entry_id: str):
        """Handle 4h reset signal."""
        if entry_id == self._entry.entry_id and self._sensor_id.endswith("_4h"):
            # 4H-Sensoren auf 0 zurücksetzen
            self._cycling_value = 0
            self.async_write_ha_state()
            _LOGGER.info(f"4H sensor {self.entity_id} reset to 0")

    async def _handle_monthly_reset(self, entry_id: str):
        """Handle monthly reset signal."""
        if entry_id == self._entry.entry_id and self._sensor_id.endswith("_monthly"):
            # Monthly-Sensoren auf 0 zurücksetzen
            self._cycling_value = 0
            self.async_write_ha_state()
            _LOGGER.info(f"Monthly sensor {self.entity_id} reset to 0")

    async def _handle_yearly_reset(self, entry_id: str):
        """Handle yearly reset signal."""
        if entry_id == self._entry.entry_id and self._sensor_id.endswith("_yearly"):
            # Yearly-Sensoren auf 0 zurücksetzen
            self._cycling_value = 0
            self.async_write_ha_state()
            _LOGGER.info(f"Yearly sensor {self.entity_id} reset to 0")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def device_info(self):
        if self._device_type and self._hp_index:
            return build_subdevice_info(
                self._entry, self._device_type, self._hp_index
            )
        return build_device_info(self._entry)

    @property
    def native_value(self):
        """Return the current cycling value."""
        # Wert aus Attribut, Standard 0
        value = getattr(self, "_cycling_value", 0)
        if value is None:
            value = 0
        return int(value)  # Stelle sicher, dass es ein Integer ist

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {
            "yesterday_value": self._yesterday_value,
            "hp_index": self._hp_index,
            "sensor_type": "cycling_total",
        }
        
        # Füge den angewendeten Offset hinzu (nur für Total-Sensoren)
        if self._sensor_id.endswith("_total"):
            applied_offset = getattr(self, "_applied_offset", 0)
            attrs["applied_offset"] = applied_offset
            
        return attrs


# --- Entity-Klasse für Energy Consumption Sensoren ---
class LambdaEnergyConsumptionSensor(RestoreEntity, SensorEntity):
    """Energy consumption sensor (echte Entity, Wert wird von increment_energy_consumption_counter gesetzt)."""

    def __init__(
        self,
        hass,
        entry,
        sensor_id,
        name,
        entity_id,
        unique_id,
        unit,
        state_class,
        device_class,
        device_type,
        hp_index,
        mode,
        period,
    ):
        self.hass = hass
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self.entity_id = entity_id
        self._unique_id = unique_id
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._hp_index = hp_index
        self._mode = mode
        self._period = period  # Speichere period für Tests und native_value Berechnung
        self._reset_interval = period  # period ist auch reset_interval
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_name = name
        self._attr_unique_id = unique_id
        # Initialisiere energy_value mit 0.0
        self._energy_value = 0.0
        # Yesterday-Wert für Daily-Berechnung
        self._yesterday_value = 0.0
        # Previous Period-Werte für Monthly/Yearly-Berechnung
        self._previous_monthly_value = 0.0
        self._previous_yearly_value = 0.0
        # Track applied offset to prevent duplicate application
        self._applied_offset = 0.0
        # Signal-Unsubscribe-Funktionen
        self._unsub_dispatcher = None

        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None
        self._attr_device_class = device_class

    def set_energy_value(self, value):
        """Set the energy value and update state."""
        old_value = self._energy_value
        self._energy_value = float(value)
        self.async_write_ha_state()
        _LOGGER.debug(f"Energy sensor {self.entity_id} value updated from {old_value:.2f} to {self._energy_value:.2f}")

    def update_yesterday_value(self):
        """Update yesterday value with current total value (called at midnight)."""
        old_yesterday = self._yesterday_value
        self._yesterday_value = self._energy_value
        _LOGGER.info(
            f"Yesterday value updated for {self.entity_id}: {old_yesterday:.2f} -> {self._yesterday_value:.2f}"
        )

    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()

        # RestoreEntity provides async_get_last_state() method
        last_state = await self.async_get_last_state()
        await self.restore_state(last_state)

        # Registriere Signal-Handler für Reset-Signale
        # Verwende zentrale Signale wie Cycling Sensoren
        from .automations import SIGNAL_RESET_DAILY, SIGNAL_RESET_2H, SIGNAL_RESET_4H, SIGNAL_RESET_MONTHLY, SIGNAL_RESET_YEARLY  # noqa: F401
        
        # Wrapper-Funktion für asynchronen Handler mit @callback
        @callback
        def _wrap_reset(entry_id: str):
            self.hass.async_create_task(self._handle_reset(entry_id))
        
        if self._reset_interval == "daily":
            self._unsub_dispatcher = async_dispatcher_connect(
                self.hass, SIGNAL_RESET_DAILY, _wrap_reset
            )
        elif self._reset_interval == "2h":
            self._unsub_dispatcher = async_dispatcher_connect(
                self.hass, SIGNAL_RESET_2H, _wrap_reset
            )
        elif self._reset_interval == "4h":
            self._unsub_dispatcher = async_dispatcher_connect(
                self.hass, SIGNAL_RESET_4H, _wrap_reset
            )
        elif self._reset_interval == "monthly":
            self._unsub_dispatcher = async_dispatcher_connect(
                self.hass, SIGNAL_RESET_MONTHLY, _wrap_reset
            )
        elif self._reset_interval == "yearly":
            self._unsub_dispatcher = async_dispatcher_connect(
                self.hass, SIGNAL_RESET_YEARLY, _wrap_reset
            )

    async def async_will_remove_from_hass(self):
        """Clean up when entity is removed."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()
        await super().async_will_remove_from_hass()

    async def restore_state(self, last_state):
        """Restore the state from the last state."""
        if last_state is not None and last_state.state != STATE_UNKNOWN:
            try:
                self._energy_value = float(last_state.state)
                _LOGGER.debug(f"Restored energy value for {self.entity_id}: {self._energy_value:.2f}")
                # Restore applied_offset if it exists (for total sensors)
                if hasattr(last_state, 'attributes') and last_state.attributes:
                    self._applied_offset = last_state.attributes.get("applied_offset", 0.0)
            except ValueError as e:
                _LOGGER.error(f"Failed to restore state for {self.entity_id}: {e}")
                self._energy_value = 0.0
        else:
            self._energy_value = 0.0
            _LOGGER.debug(f"No state to restore for {self.entity_id}, initializing to 0.0")
        self.async_write_ha_state()

    async def _apply_energy_offset(self):
        """Apply energy consumption offset for total sensors (only once, like cycling sensors)."""
        try:
            # Lade die Energy Consumption Offsets aus der Konfiguration (wie bei Cycling)
            from .utils import load_lambda_config
            config = await load_lambda_config(self.hass)
            energy_offsets = config.get("energy_consumption_offsets", {})
            
            if not energy_offsets:
                _LOGGER.debug(f"No energy consumption offsets found for {self.entity_id}")
                return
            
            # Bestimme den Device-Key (z.B. "hp1")
            device_key = f"hp{self._hp_index}"
            
            if device_key not in energy_offsets:
                _LOGGER.debug(f"No energy consumption offsets found for device {device_key}")
                return
            
            # Hole den aktuellen Offset für diesen Sensor
            sensor_id = f"{self._mode}_energy_total"
            current_offset = energy_offsets[device_key].get(sensor_id, 0.0)
            
            # Hole den bereits angewendeten Offset aus den Attributen (wie bei Cycling)
            applied_offset = getattr(self, "_applied_offset", 0.0)
            
            # Berechne die Differenz zwischen aktuellem und bereits angewendetem Offset
            offset_difference = current_offset - applied_offset
            
            if offset_difference > 0:
                # Apply only the difference to current value
                self._energy_value += float(offset_difference)
                self._applied_offset = current_offset  # Update applied offset
                self.async_write_ha_state()
                _LOGGER.info(
                    f"Applied energy offset for {self.entity_id}: +{offset_difference:.2f} kWh (new total: {self._energy_value:.2f} kWh)"
                )
            elif offset_difference < 0:
                # Offset was reduced, subtract the difference
                self._energy_value += float(offset_difference)  # offset_difference is negative
                self._applied_offset = current_offset
                self.async_write_ha_state()
                _LOGGER.info(
                    f"Reduced energy offset for {self.entity_id}: {offset_difference:.2f} kWh (new total: {self._energy_value:.2f} kWh)"
                )
            else:
                _LOGGER.debug(f"No offset change for {self.entity_id}")
        except Exception as e:
            _LOGGER.error(f"Error applying energy offset for {self.entity_id}: {e}")

    async def _handle_reset(self, entry_id: str):
        """Handle reset signal."""
        _LOGGER.info(f"Resetting energy sensor {self.entity_id}")
        
        # Einfache Reset-Logik: Alle außer Total werden auf 0 gesetzt
        if self._reset_interval != "total":
            self._energy_value = 0.0
            _LOGGER.info(f"Sensor {self.entity_id} reset to 0.0 kWh.")
        else:
            _LOGGER.debug(f"Total sensor {self.entity_id} not reset.")
        
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the current value based on period."""
        if self._period == "total":
            return self._energy_value
        elif self._period == "daily":
            # Daily = Total - Yesterday
            daily_value = self._energy_value - self._yesterday_value
            return max(0.0, daily_value)  # Clamp to 0
        elif self._period == "monthly":
            # Monthly = Total - Previous Monthly
            monthly_value = self._energy_value - self._previous_monthly_value
            return max(0.0, monthly_value)  # Clamp to 0
        elif self._period == "yearly":
            # Yearly = Total - Previous Yearly
            yearly_value = self._energy_value - self._previous_yearly_value
            return max(0.0, yearly_value)  # Clamp to 0
        else:
            return self._energy_value

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {
            "sensor_type": "energy_consumption",
            "mode": self._mode,
            "period": self._period,
            "reset_interval": self._reset_interval,
            "hp_index": self._hp_index,
            "applied_offset": self._applied_offset,
        }
        return attrs

    @property
    def device_info(self):
        """Return device information."""
        if self._device_type and self._hp_index:
            return build_subdevice_info(
                self._entry, self._device_type, self._hp_index
            )
        return build_device_info(self._entry)


class LambdaYesterdaySensor(RestoreEntity, SensorEntity):
    """Yesterday cycling sensor (speichert Total-Werte für Daily-Berechnung)."""

    def __init__(
        self,
        hass,
        entry,
        sensor_id,
        name,
        entity_id,
        unique_id,
        unit,
        state_class,
        device_class,
        device_type,
        hp_index,
        mode,
    ):
        self.hass = hass
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self.entity_id = entity_id
        self._unique_id = unique_id
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._hp_index = hp_index
        self._mode = mode
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_name = name
        self._attr_unique_id = unique_id
        # Yesterday-Wert (wird von Daily-Sensor übernommen)
        self._yesterday_value = 0

        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None
        self._attr_device_class = device_class

    async def set_cycling_value(self, value):
        """Set the cycling value and update state."""
        old_value = self._yesterday_value
        self._yesterday_value = int(value)
        _LOGGER.info(
            f"Yesterday sensor {self.entity_id} updated: {old_value} -> {self._yesterday_value}"
        )
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()

        # RestoreEntity provides async_get_last_state() method
        last_state = await self.async_get_last_state()
        await self.restore_state(last_state)

        # Yesterday-Sensoren werden direkt von _update_yesterday_sensors() aktualisiert
        # Keine Signal-Handler mehr nötig

        # Schreibe den State sofort ins UI
        self.async_write_ha_state()

    async def restore_state(self, last_state):
        """Restore state from database to prevent reset on reload."""
        if last_state is not None:
            try:
                # Lade den letzten Wert aus der Datenbank
                last_value = last_state.state
                if last_value not in (None, "unknown", "unavailable"):
                    self._yesterday_value = int(float(last_value))
                    _LOGGER.debug(
                        f"Yesterday sensor {self.entity_id} restored from database: {self._yesterday_value}"
                    )
                else:
                    # Fallback auf 0 nur wenn wirklich kein Wert in der DB
                    self._yesterday_value = 0
                    _LOGGER.info(
                        f"Yesterday sensor {self.entity_id} initialized with 0 (no previous state)"
                    )
            except (ValueError, TypeError) as e:
                _LOGGER.warning(
                    f"Could not restore state for {self.entity_id}: {e}, using 0"
                )
                self._yesterday_value = 0
        else:
            # Kein vorheriger State vorhanden, initialisiere mit 0
            self._yesterday_value = 0
            _LOGGER.info(
                f"Yesterday sensor {self.entity_id} initialized with 0 (no previous state)"
            )

        # Stelle sicher, dass der Wert ein Integer ist
        self._yesterday_value = int(self._yesterday_value)

    # Yesterday-Sensoren werden direkt von _update_yesterday_sensors() aktualisiert
    # Keine Signal-Handler mehr nötig

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def device_info(self):
        """Return device info."""
        if self._device_type and self._hp_index:
            return build_subdevice_info(
                self._entry, self._device_type, self._hp_index
            )
        return build_device_info(self._entry)

    @property
    def native_value(self):
        """Return the yesterday value."""
        value = getattr(self, "_yesterday_value", 0)
        if value is None:
            value = 0
        return int(value)

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "mode": self._mode,
            "hp_index": self._hp_index,
            "sensor_type": "cycling_yesterday",
        }


class LambdaSensor(CoordinatorEntity[LambdaDataUpdateCoordinator], SensorEntity):
    """Representation of a Lambda sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        address: int,
        scale: float,
        state_class: str,
        device_class: SensorDeviceClass,
        relative_address: int,
        data_type: str,
        device_type: str,
        txt_mapping: bool = False,
        precision: int | None = None,
        entity_id: str | None = None,
        unique_id: str | None = None,
        options: list[str] | None = None,
        sensor_info: dict | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_id = sensor_id
        self._attr_name = name
        self._attr_unique_id = unique_id  # Immer die generierte ID verwenden
        self.entity_id = entity_id or f"sensor.{sensor_id}"
        self._unit = unit
        self._address = address
        self._scale = scale
        self._state_class = state_class
        self._device_class = device_class
        self._relative_address = relative_address
        self._data_type = data_type
        self._device_type = device_type
        self._txt_mapping = txt_mapping
        self._precision = precision
        self._options = options
        self._sensor_info = sensor_info or {}
        self._base_state_name = None
        if sensor_info:
            self._base_state_name = sensor_info.get("name")
        self._entity_enabled = False  # Track if entity is enabled
        
        # Setze Icon aus sensor_info (zentrale Steuerung)
        self._attr_icon = get_entity_icon(sensor_info)

        # Debug log sensor creation with register option
        if sensor_info and sensor_info.get("options", {}).get("register", False):
            _LOGGER.info(
                "Created sensor %s with register option, address=%s", sensor_id, address
            )

        if txt_mapping:
            _LOGGER.info("Created state sensor %s (txt_mapping=True)", sensor_id)

        # Store the address in coordinator for polling control
        if hasattr(coordinator, "_entity_addresses"):
            coordinator._entity_addresses[entity_id] = address
        else:
            coordinator._entity_addresses = {entity_id: address}

        _LOGGER.debug(
            "Sensor initialized with ID: %s and config: %s",
            sensor_id,
            {
                "name": name,
                "unit": unit,
                "address": address,
                "scale": scale,
                "state_class": state_class,
                "device_class": device_class,
                "relative_address": relative_address,
                "data_type": data_type,
                "device_type": device_type,
                "txt_mapping": txt_mapping,
                "precision": precision,
            },
        )

        self._is_state_sensor = txt_mapping

        if self._is_state_sensor:
            self._attr_device_class = None
            self._attr_state_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_suggested_display_precision = None
        else:
            self._attr_native_unit_of_measurement = unit
            if precision is not None and isinstance(precision, int):
                self._attr_suggested_display_precision = precision
            if unit == "°C":
                self._attr_device_class = SensorDeviceClass.TEMPERATURE
            elif unit == "W":
                self._attr_device_class = SensorDeviceClass.POWER
            elif unit == "Wh":
                self._attr_device_class = SensorDeviceClass.ENERGY
            if state_class:
                if state_class == "total":
                    self._attr_state_class = SensorStateClass.TOTAL
                elif state_class == "total_increasing":
                    self._attr_state_class = SensorStateClass.TOTAL_INCREASING
                elif state_class == "measurement":
                    self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def should_poll(self) -> bool:
        """Only poll if the entity is enabled and added to HA."""
        return self._entity_enabled

    async def async_added_to_hass(self):
        """Setup polling when entity is enabled and added to HA."""
        await super().async_added_to_hass()
        self._entity_enabled = True

        # Add this address to enabled addresses in coordinator
        if hasattr(self.coordinator, "_enabled_addresses"):
            if self.coordinator._enabled_addresses:
                self.coordinator._enabled_addresses.add(self._address)
            else:
                self.coordinator._enabled_addresses = {self._address}

        _LOGGER.debug(
            "Entity %s (address %d) added to HA - polling enabled",
            self.entity_id,
            self._address,
        )

    async def async_will_remove_from_hass(self):
        """Called when entity is removed/disabled - stop polling."""
        self._entity_enabled = False

        # Remove this address from enabled addresses in coordinator
        if hasattr(self.coordinator, "_enabled_addresses"):
            self.coordinator._enabled_addresses.discard(self._address)

        _LOGGER.debug(
            "Entity %s (address %d) removed from HA - polling disabled",
            self.entity_id,
            self._address,
        )
        await super().async_will_remove_from_hass()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        use_legacy_modbus_names = self.coordinator.entry.data.get(
            "use_legacy_modbus_names", True
        )
        if use_legacy_modbus_names and hasattr(self.coordinator, "sensor_overrides"):
            override_name = self.coordinator.sensor_overrides.get(self._sensor_id)
            if override_name:
                # Verwende den Override-Namen als sensor_id
                _LOGGER.debug(
                    "Overriding sensor_id from %s to %s",
                    self._sensor_id,
                    override_name,
                )
                self._sensor_id = override_name
                return override_name
        return self._attr_name or ""

    @property
    def native_value(self) -> float | str | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self._sensor_id)

        # Debug logging für undokumentierte Register
        if self._sensor_id and (
            "extended" in self._sensor_id
            or "config" in self._sensor_id
            or "additional" in self._sensor_id
            or "ambient" in self._sensor_id
            or "compressor_outlet" in self._sensor_id
            or "maximum_value" in self._sensor_id
        ):
            _LOGGER.debug(
                "Debug sensor %s: value=%s, coordinator.data has %d entries",
                self._sensor_id,
                value,
                len(self.coordinator.data) if self.coordinator.data else 0,
            )

        if value is None:
            return None
        if self._is_state_sensor:
            try:
                numeric_value = int(float(value))
            except (ValueError, TypeError):
                return f"Unknown state ({value})"

            # Extract base name without index
            # (e.g. "HP1 Operating State" -> "Operating State")
            if self._base_state_name:
                base_name = self._base_state_name
            else:
                base_name = self._attr_name or ""
                if (
                    self._device_type
                    and base_name
                    and self._device_type.upper() in base_name
                ):
                    # Remove prefix and index (e.g. "HP1 " oder "BOIL2 ")
                    base_name = " ".join(base_name.split()[1:])
            # Ersetze auch Bindestriche durch Unterstriche
            if base_name:
                mapping_name = (
                    f"{self._device_type.upper()}_"
                    f"{base_name.upper().replace(' ', '_').replace('-', '_')}"
                )
            try:
                state_mapping = globals().get(mapping_name)
                if state_mapping is not None:
                    return state_mapping.get(
                        numeric_value, f"Unknown state ({numeric_value})"
                    )
                _LOGGER.warning(
                    "No state mapping found f. sensor '%s' (tried mapping: %s)"
                    "with value %s. Sensor details: device_type=%s, "
                    "register=%d, data_type=%s. This sensor is marked as state"
                    "sensor (txt_mapping=True) but no corresponding mapping "
                    "dictionary was found.",
                    self._attr_name,
                    mapping_name,
                    numeric_value,
                    self._device_type,
                    self._relative_address,
                    self._data_type,
                )
                return f"Unknown mapping for state ({numeric_value})"
            except Exception as e:
                _LOGGER.error(
                    "Error accessing mapping dictionary: %s",
                    str(e),
                )
                return f"Error loading mappings ({numeric_value})"
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor."""
        return self._attr_native_unit_of_measurement

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class of the sensor."""
        if self._state_class == "measurement":
            return SensorStateClass.MEASUREMENT
        elif self._state_class == "total":
            return SensorStateClass.TOTAL
        elif self._state_class == "total_increasing":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        if self._device_class == "temperature":
            return SensorDeviceClass.TEMPERATURE
        elif self._device_class == "power":
            return SensorDeviceClass.POWER
        elif self._device_class == "energy":
            return SensorDeviceClass.ENERGY
        elif self._device_class == "enum":
            return SensorDeviceClass.ENUM
        return None

    @property
    def options(self) -> list[str] | None:
        """Return the available options for enum sensors."""
        if self._device_class == "enum" and self._options:
            return self._options
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | list] | None:
        """Return extra state attributes."""
        _LOGGER.debug("extra_state_attributes called for sensor %s", self._sensor_id)
        attrs = {}

        # Add register address for ALL sensors (not just those with register option)
        _LOGGER.debug(
            "Adding register %s for sensor %s", self._address, self._sensor_id
        )
        attrs["register"] = self._address

        # For txt_mapping sensors (state sensors), add enum options
        if self._txt_mapping and self._is_state_sensor:
            _LOGGER.debug(
                "Processing state sensor %s for enum options", self._sensor_id
            )
            # Get the mapping dictionary name
            if self._base_state_name:
                base_name = self._base_state_name
            else:
                base_name = self._attr_name or ""
                if (
                    self._device_type
                    and base_name
                    and self._device_type.upper() in base_name
                ):
                    base_name = " ".join(base_name.split()[1:])

            if base_name:
                mapping_name = (
                    f"{self._device_type.upper()}_"
                    f"{base_name.upper().replace(' ', '_').replace('-', '_')}"
                )
                _LOGGER.debug("Looking for state mapping: %s", mapping_name)

                try:
                    state_mapping = globals().get(mapping_name)
                    if state_mapping is not None:
                        # Convert mapping to options list
                        options = list(state_mapping.values())
                        _LOGGER.debug(
                            "Found enum options for %s: %s", self._sensor_id, options
                        )
                        attrs["options"] = options
                    else:
                        _LOGGER.debug("No state mapping found for %s", mapping_name)

                except Exception as e:
                    _LOGGER.debug(
                        "Error getting state mapping for %s: %s", mapping_name, e
                    )

        _LOGGER.debug("Final attributes for %s: %s", self._sensor_id, attrs)
        return attrs

    @property
    def device_info(self):
        """Return device info for this sensor."""
        device_type, device_index = extract_device_info_from_sensor_id(
            self._sensor_id
        )
        if device_type and device_index:
            return build_subdevice_info(self._entry, device_type, device_index)
        return build_device_info(self._entry)


class LambdaTemplateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Lambda template sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        state_class: str,
        device_class: SensorDeviceClass,
        device_type: str,
        precision: int | float | None = None,
        entity_id: str | None = None,
        unique_id: str | None = None,
        template_str: str = "",
    ) -> None:
        """Initialize the template sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._precision = precision
        self._entity_id = entity_id
        self._unique_id = unique_id
        self._template_str = template_str
        self._state = None
        _LOGGER.info(
            f"Template-Sensor erstellt: {self._name} (ID: {self._sensor_id}) mit Template: {self._template_str}"
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id or ""

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor."""
        return self._unit

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class of the sensor."""
        if self._state_class == "measurement":
            return SensorStateClass.MEASUREMENT
        elif self._state_class == "total":
            return SensorStateClass.TOTAL
        elif self._state_class == "total_increasing":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        if self._device_class == "temperature":
            return SensorDeviceClass.TEMPERATURE
        elif self._device_class == "power":
            return SensorDeviceClass.POWER
        elif self._device_class == "energy":
            return SensorDeviceClass.ENERGY
        return None

    @property
    def device_info(self):
        """Return device info."""
        device_type, device_index = extract_device_info_from_sensor_id(self._sensor_id)
        if not device_type and hasattr(self, "_device_type"):
            device_type = getattr(self, "_device_type", None)
        if not device_index and hasattr(self, "_hp_index"):
            device_index = getattr(self, "_hp_index", None)
        if device_type and device_index:
            return build_subdevice_info(self._entry, device_type, device_index)
        return build_device_info(self._entry)

    @callback
    def handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        try:
            template = Template(self._template_str, self.hass)
            rendered_value = template.async_render()
            if rendered_value is None or rendered_value == "unavailable":
                self._state = None
                return
            if isinstance(rendered_value, str) and (
                rendered_value.startswith("{{") or "states(" in rendered_value
            ):
                _LOGGER.debug(
                    "Template not yet ready for sensor %s, waiting for dependencies",
                    self._sensor_id,
                )
                self._state = None
                return
            try:
                float_value = float(rendered_value)
                if self._precision is not None and isinstance(self._precision, int):
                    self._state = round(float_value, self._precision)
                else:
                    self._state = float_value
                _LOGGER.info(
                    f"Template-Sensor berechnet: {self._name} (ID: {self._sensor_id}) = {self._state}"
                )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not convert template result to float for sensor %s: %s",
                    self._sensor_id,
                    rendered_value,
                )
                self._state = None
        except TemplateError as err:
            _LOGGER.warning("Template error for sensor %s: %s", self._sensor_id, err)
            self._state = None
        except Exception as err:
            _LOGGER.warning(
                "Error rendering template for sensor %s: %s", self._sensor_id, err
            )
            self._state = None
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator (for testing)."""
        self.handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.handle_coordinator_update()



