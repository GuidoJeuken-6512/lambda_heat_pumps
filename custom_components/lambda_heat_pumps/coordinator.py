"""Data update coordinator for Lambda."""

from __future__ import annotations
from datetime import timedelta
import logging
import os
import yaml
import json
import asyncio
# import aiofiles  # Unused import removed
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import async_track_time_interval
from .const import (
    SENSOR_TYPES,
    HP_SENSOR_TEMPLATES,
    BOIL_SENSOR_TEMPLATES,
    BUFF_SENSOR_TEMPLATES,
    SOL_SENSOR_TEMPLATES,
    HC_SENSOR_TEMPLATES,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_FAST_UPDATE_INTERVAL,
    CALCULATED_SENSOR_TEMPLATES,
    LAMBDA_MODBUS_UNIT_ID,
    LAMBDA_MODBUS_PORT,
    INDIVIDUAL_READ_REGISTERS,
)
from .utils import (
    load_disabled_registers,
    is_register_disabled,
    generate_base_addresses,
    to_signed_16bit,
    to_signed_32bit,
    increment_cycling_counter,
    get_firmware_version_int,
    get_compatible_sensors,
    normalize_name_prefix,
)
from .modbus_utils import async_read_holding_registers, combine_int32_registers, wait_for_stable_connection
import time

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)

# Sensor-Wechsel-Erkennung läuft bei jedem Start, um alle Sensor-Wechsel zu erkennen


class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Lambda data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize."""
        # Lese update_interval aus den Optionen, falls vorhanden
        update_interval = entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Update interval from options: %s seconds", update_interval)
        _LOGGER.debug("Entry options: %s", entry.options)
        _LOGGER.debug(
            "Room thermostat control: %s",
            entry.options.get("room_thermostat_control", "nicht gefunden"),
        )

        super().__init__(
            hass,
            _LOGGER,
            name="Lambda Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        self.host = entry.data["host"]
        self.port = entry.data.get("port", LAMBDA_MODBUS_PORT)
        self.slave_id = entry.data.get("slave_id", LAMBDA_MODBUS_UNIT_ID)
        self.debug_mode = entry.data.get("debug_mode", False)
        if self.debug_mode:
            _LOGGER.setLevel(logging.DEBUG)
        self.client = None
        self.config_entry_id = entry.entry_id
        self._config_dir = hass.config.config_dir
        self._config_path = os.path.join(self._config_dir, "lambda_heat_pumps")
        self.hass = hass
        self.entry = entry
        self._last_operating_state = {}
        self._last_compressor_rating = {}  # Für compressor_unit_rating Flankenerkennung (0 → >0)
        self._heating_cycles = {}
        self._heating_energy = {}
        self._last_energy_update = {}
        self._cycling_offsets = {}
        self._energy_offsets = {}
        
        # Energy Consumption Tracking
        self._last_energy_reading = {}  # {hp_index: last_kwh_value}
        self._energy_consumption = {}   # {hp_index: {mode: {period: value}}}
        self._energy_sensor_configs = {}  # Sensor-Konfigurationen aus Config (optional)
        self._sensor_ids = {}  # {hp_index: sensor_entity_id} für Sensor-Wechsel-Erkennung (elektrisch)
        self._thermal_sensor_ids = {}  # {hp_index: sensor_entity_id} für Thermik-Sensor-Wechsel-Erkennung
        self._energy_sensor_states = {}  # {entity_id: {state, energy_value, yesterday_value, ...}} aus cycle_energy_persist
        self._energy_unit_cache = {}  # {hp_index: unit_string} - Memory-only cache for performance
        self._energy_first_value_seen = {}  # {hp_index: bool} - In-Memory Flag für Zero-Value Protection
        self._last_thermal_energy_reading = {}  # {hp_index: last_kwh_value} for thermal
        self._thermal_energy_first_value_seen = {}  # {hp_index: bool} for thermal
        self._sensor_detection_executed = False  # Flag to prevent multiple sensor detection runs
        self._use_legacy_names = entry.data.get("use_legacy_modbus_names", True)
        self._name_prefix = entry.data.get("name", "eu08l")
        self._persist_file = os.path.join(
            self._config_path, "cycle_energy_persist.json"
        )

        # Entity-based polling control - simplified approach
        self._enabled_addresses = set()  # Aktuell aktivierte Register-Adressen
        self._entity_addresses = {}  # Mapping entity_id -> address from sensors
        
        # Int32 Register Order Support (Issue #22)
        self._int32_register_order = "high_first"  # Default value
        self._entity_address_mapping = {}  # Initialize entity address mapping
        self._entity_registry = None  # Initialize entity registry reference
        self._registry_listener = None  # Initialize registry listener reference

        # Dynamische Batch-Read-Fehlerbehandlung
        self._batch_failures = {}  # Dict: (start_addr, count) -> failure_count
        self._max_batch_failures = 3  # Nach 3 Fehlern auf Individual-Reads umstellen
        self._individual_read_addresses = set()  # Adressen die nur einzeln gelesen werden
        
        # Dynamische Cycling-Sensor-Meldungen
        self._cycling_warnings = {}  # Dict: entity_id -> warning_count
        self._max_cycling_warnings = 3  # Nach 3 Warnings unterdrücken
        
        # Dynamische Energy-Sensor-Meldungen
        self._energy_warnings = {}  # Dict: entity_id -> warning_count
        self._max_energy_warnings = 3  # Nach 3 Warnings unterdrücken
        
        # Flag für Initialisierung - verhindert Flankenerkennung beim ersten Update
        self._initialization_complete = False

        # Fast polling for edge detection (HP_STATE / HP_OPERATING_STATE only)
        self._full_update_running = False  # True while _async_update_data holds Modbus
        self._unsub_fast_poll = None

        # Persist File I/O Optimierung
        self._persist_dirty = False  # Dirty-Flag für Änderungen
        self._persist_last_write = 0  # Timestamp des letzten Schreibens
        self._persist_debounce_seconds = 30  # Max 1x pro 30 Sekunden schreiben
        
        # Globale Register-Deduplizierung für bessere Performance
        self._global_register_cache = {}  # Cache für bereits gelesene Register pro Update-Zyklus
        self._global_register_requests = {}  # Sammle alle Register-Requests vor dem Lesen

        # self._load_offsets_and_persisted() ENTFERNT!

    async def _increment_thermal_energy_consumption(self, hp_idx, mode, energy_delta):
        """Increment thermal energy consumption for a specific mode and heat pump."""
        try:
            from .utils import increment_energy_consumption_counter
            hp_key = f"hp{hp_idx}"
            energy_offsets = self._energy_offsets.get(hp_key, {})
            name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
            await increment_energy_consumption_counter(
                hass=self.hass,
                mode=mode,
                hp_index=hp_idx,
                energy_delta=energy_delta,
                name_prefix=name_prefix,
                use_legacy_modbus_names=self._use_legacy_names,
                energy_offsets=energy_offsets,
                sensor_type="thermal",
            )
        except Exception as ex:
            _LOGGER.error("Error incrementing thermal energy consumption for HP%s %s: %s", hp_idx, mode, ex)

    def _add_register_request(self, address, sensor_info, sensor_id):
        """Füge einen Register-Request zur globalen Sammlung hinzu."""
        if address not in self._global_register_requests:
            self._global_register_requests[address] = {
                'sensor_info': sensor_info,
                'sensor_ids': set()
            }
        self._global_register_requests[address]['sensor_ids'].add(sensor_id)

    async def _read_all_registers_globally(self):
        """Lese alle gesammelten Register in einem großen Batch."""
        if not self._global_register_requests:
            return {}
        
        _LOGGER.debug("Reading %s unique registers globally", len(self._global_register_requests))
        
        # Konvertiere zu address_list und sensor_mapping Format
        address_list = {}
        sensor_mapping = {}
        
        for address, request_data in self._global_register_requests.items():
            address_list[address] = request_data['sensor_info']
            # Verwende den ersten sensor_id als Hauptschlüssel
            primary_sensor_id = list(request_data['sensor_ids'])[0]
            sensor_mapping[address] = primary_sensor_id
        
        # Lese alle Register in einem Batch
        return await self._read_registers_batch(address_list, sensor_mapping)

    def _normalize_operating_states(self, states_dict):
        """Normalisiere last_operating_states (HP_OPERATING_STATE, Register 1003) - konvertiere alle Schlüssel zu Strings."""
        if not isinstance(states_dict, dict):
            return {}
        
        normalized = {}
        for key, value in states_dict.items():
            # Konvertiere Schlüssel zu String
            normalized[str(key)] = value
        
        return normalized
    
    def _normalize_states(self, states_dict):
        """Normalisiere last_states (HP_STATE, Register 1002) - konvertiere alle Schlüssel zu Strings.
        
        Diese Methode ist für HP_STATE Werte (z.B. START COMPRESSOR = 5) gedacht,
        die sich semantisch von HP_OPERATING_STATE Werten unterscheiden.
        """
        if not isinstance(states_dict, dict):
            return {}
        
        normalized = {}
        for key, value in states_dict.items():
            # Konvertiere Schlüssel zu String
            normalized[str(key)] = value
        
        return normalized

    async def _repair_and_load_persist_file(self):
        """Lade und repariere persistierte JSON-Datei bei Bedarf."""
        
        def _repair_json():
            try:
                with open(self._persist_file) as f:
                    content = f.read().strip()
                    
                if not content:
                    _LOGGER.warning("Persist file %s is empty, using defaults", self._persist_file)
                    return {}
                    
                # Versuche normales Laden
                data = json.loads(content)
                
                # Repariere doppelte Schlüssel in last_operating_states
                if "last_operating_states" in data and isinstance(data["last_operating_states"], dict):
                    states = data["last_operating_states"]
                    # Entferne doppelte Schlüssel - behalte den letzten Wert
                    clean_states = {}
                    for key, value in states.items():
                        clean_states[str(key)] = value  # Normalisiere zu String
                    data["last_operating_states"] = clean_states
                    _LOGGER.info(
                        f"Repaired duplicate keys in last_operating_states: {clean_states}"
                    )
                
                    # Stelle sicher, dass alle wichtigen Felder existieren
                    required_fields = [
                        "heating_cycles", "heating_energy", "last_operating_states",
                        "energy_consumption", "last_energy_readings", "energy_offsets",
                        "energy_sensor_states",
                    ]
                    for field in required_fields:
                        if field not in data:
                            data[field] = {}
                            _LOGGER.info("Added missing field %s to repaired JSON", field)
                    
                    # sensor_ids / thermal_sensor_ids nur hinzufügen wenn komplett fehlt
                    if "sensor_ids" not in data:
                        data["sensor_ids"] = {}
                        _LOGGER.info("Added missing sensor_ids field to repaired JSON")
                    if "thermal_sensor_ids" not in data:
                        data["thermal_sensor_ids"] = {}
                    if "last_thermal_energy_readings" not in data:
                        data["last_thermal_energy_readings"] = {}
                    
                return data
                
            except json.JSONDecodeError as e:
                _LOGGER.error("JSON decode error in %s: %s", self._persist_file, e)
                _LOGGER.warning("Attempting to repair corrupted JSON file")
                
                # Versuche einfache Reparatur durch Entfernung doppelter Schlüssel
                try:
                    # Erstelle Backup der ursprünglichen Datei
                    backup_file = self._persist_file + ".backup"
                    with open(self._persist_file, 'r') as src, open(backup_file, 'w') as dst:
                        dst.write(src.read())
                    
                    # Versuche Reparatur durch Regex
                    import re
                    # Entferne doppelte Schlüssel: "key": value, "key": value
                    duplicate_pattern = r'("[^"]+"\s*:\s*[^,}]+),\s*\1'
                    
                    with open(self._persist_file, 'r') as f:
                        content = f.read()
                    
                    # Repariere doppelte Schlüssel
                    repaired_content = content
                    while re.search(duplicate_pattern, repaired_content):
                        repaired_content = re.sub(duplicate_pattern, r'\1', repaired_content)
                    
                    # Versuche das reparierte JSON zu laden
                    data = json.loads(repaired_content)
                    
                    # Stelle sicher, dass alle wichtigen Felder existieren
                    required_fields = [
                        "heating_cycles", "heating_energy", "last_operating_states",
                        "energy_consumption", "last_energy_readings", "last_thermal_energy_readings",
                        "energy_offsets", "sensor_ids", "thermal_sensor_ids",
                        "energy_sensor_states",
                    ]
                    for field in required_fields:
                        if field not in data:
                            data[field] = {}
                    
                    # Speichere reparierte Version
                    with open(self._persist_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    _LOGGER.info("Successfully repaired corrupted JSON file")
                    return data
                    
                except Exception as repair_error:
                    _LOGGER.error("Failed to repair JSON file: %s", repair_error)
                    _LOGGER.warning("Deleting corrupted persist file and starting fresh")
                    try:
                        os.remove(self._persist_file)
                    except Exception:
                        pass  # Ignore if file can't be deleted
                    return {}
            except Exception as e:
                _LOGGER.error("Error reading persist file %s: %s", self._persist_file, e)
                return {}
        
        return await self.hass.async_add_executor_job(_repair_json)

    async def _persist_counters(self):
        """Persist counter data and state information to file using optimized I/O with debouncing."""
        # Also persist thermal energy readings
        # (Extend this logic if you want to persist more types in the future)
        import time
        
        # Prüfe Dirty-Flag - nur schreiben wenn sich etwas geändert hat
        if not self._persist_dirty:
            _LOGGER.debug("No changes to persist, skipping write")
            return
        
        current_time = time.time()
        
        # Debouncing: Max 1x pro 30 Sekunden schreiben
        if current_time - self._persist_last_write < self._persist_debounce_seconds:
            _LOGGER.debug("Persist write debounced (last write %.1fs ago)", 
                         current_time - self._persist_last_write)
            return
        
        # Stelle sicher, dass alle Schlüssel konsistent sind
        # Verwende separate Normalisierungsmethoden für semantisch unterschiedliche State-Typen
        normalized_operating_states = self._normalize_operating_states(
            getattr(self, "_last_operating_state", {})
        )
        normalized_states = self._normalize_states(
            getattr(self, "_last_state", {})
        )
        
        # Prüfe ob sensor_ids/thermal_sensor_ids in der Datei existieren, falls im Speicher leer
        sensor_ids_to_save = getattr(self, "_sensor_ids", {})
        thermal_sensor_ids_to_save = getattr(self, "_thermal_sensor_ids", {})
        if (not sensor_ids_to_save or not thermal_sensor_ids_to_save) and os.path.exists(self._persist_file):

            def _read_existing_sensor_ids():
                try:
                    with open(self._persist_file) as f:
                        existing_data = json.loads(f.read())
                        out_sensor = sensor_ids_to_save or existing_data.get("sensor_ids", {})
                        out_thermal = thermal_sensor_ids_to_save or existing_data.get("thermal_sensor_ids", {})
                        return out_sensor, out_thermal
                except Exception:
                    return sensor_ids_to_save, thermal_sensor_ids_to_save

            sensor_ids_to_save, thermal_sensor_ids_to_save = await self.hass.async_add_executor_job(_read_existing_sensor_ids)

        # Energy-Sensor-States aus Entities sammeln (electrical + thermal, alle Perioden)
        energy_sensor_states_to_save = self._collect_energy_sensor_states()

        data = {
            "heating_cycles": self._heating_cycles,
            "heating_energy": self._heating_energy,
            "last_operating_states": normalized_operating_states,
            "last_states": normalized_states,
            "energy_consumption": self._energy_consumption,
            "last_energy_readings": self._last_energy_reading,
            "last_thermal_energy_readings": getattr(self, "_last_thermal_energy_reading", {}),
            "energy_offsets": self._energy_offsets,
            "sensor_ids": sensor_ids_to_save,
            "thermal_sensor_ids": thermal_sensor_ids_to_save,
            "energy_sensor_states": energy_sensor_states_to_save,
        }

        def _write_data():
            os.makedirs(os.path.dirname(self._persist_file), exist_ok=True)
            with open(self._persist_file, "w") as f:
                json.dump(data, f, indent=2)  # Mit Indentation für bessere Lesbarkeit

        # Schreibe als Background-Task (non-blocking)
        try:
            await self.hass.async_add_executor_job(_write_data)
            self._persist_last_write = current_time
            self._persist_dirty = False  # Reset Dirty-Flag nach erfolgreichem Schreiben
            _LOGGER.debug("Persist file written successfully")
        except Exception as e:
            _LOGGER.error("Failed to write persist file: %s", e)
            # Dirty-Flag bleibt True für nächsten Versuch

    def mark_initialization_complete(self) -> None:
        """Markiere die Initialisierung als abgeschlossen - ermöglicht Flankenerkennung."""
        if not self._initialization_complete:
            self._initialization_complete = True
            _LOGGER.info("Coordinator-Initialisierung abgeschlossen - Flankenerkennung aktiviert")

    def _collect_energy_sensor_states(self):
        """Sammle State + Attribute aller Energy-Consumption-Entities für Persist (electrical + thermal)."""
        out = {}
        try:
            comp = self.hass.data.get("lambda_heat_pumps", {}).get(self.entry.entry_id, {})
            entities = comp.get("energy_entities", {})
            for entity_id, ent in entities.items():
                if not hasattr(ent, "_energy_value"):
                    continue
                state_val = ent.native_value
                if state_val is None:
                    continue
                energy_val = round(getattr(ent, "_energy_value", 0), 2)
                yesterday_val = round(getattr(ent, "_yesterday_value", 0), 2)
                prev_monthly_val = round(getattr(ent, "_previous_monthly_value", 0), 2)
                prev_yearly_val = round(getattr(ent, "_previous_yearly_value", 0), 2)
                # Konsistenz: Basis-Wert darf nicht größer als energy_value sein (Periodenwert wäre sonst negativ)
                if "_daily" in entity_id and yesterday_val > energy_val:
                    yesterday_val = energy_val
                if "_monthly" in entity_id and prev_monthly_val > energy_val:
                    prev_monthly_val = energy_val
                if "_yearly" in entity_id and prev_yearly_val > energy_val:
                    prev_yearly_val = energy_val
                attrs = {
                    "energy_value": energy_val,
                    "yesterday_value": yesterday_val,
                    "previous_monthly_value": prev_monthly_val,
                    "previous_yearly_value": prev_yearly_val,
                }
                out[entity_id] = {"state": round(float(state_val), 2), "attributes": attrs}
        except Exception as e:
            _LOGGER.debug("Collect energy_sensor_states: %s", e)
        return out

    def get_energy_sensor_persisted_state(self, entity_id):
        """Liefert den aus cycle_energy_persist geladenen State für eine Entity (oder None)."""
        return self._energy_sensor_states.get(entity_id)

    def set_energy_persist_dirty(self) -> None:
        """Markiert Persist als geändert, damit Energy-States beim nächsten Schreibzyklus mit gespeichert werden."""
        self._persist_dirty = True

    async def _load_offsets_and_persisted(self):
        # Lade Offsets aus lambda_wp_config.yaml über das zentrale Config-System
        from .utils import load_lambda_config
        
        try:
            config = await load_lambda_config(self.hass)
            _LOGGER.info("Loaded config keys: %s", list(config.keys()))
            self._cycling_offsets = config.get("cycling_offsets", {})
            self._energy_offsets = config.get("energy_consumption_offsets", {})
            # Lade und validiere Energy Sensor Konfigurationen
            raw_energy_sensor_configs = config.get("energy_consumption_sensors", {})
            
            # Validiere externe Sensoren
            from .utils import validate_external_sensors
            self._energy_sensor_configs = validate_external_sensors(self.hass, raw_energy_sensor_configs)
            
            _LOGGER.info("Loaded energy sensor configs: %s", self._energy_sensor_configs)
            
            # Info-Message: Anzeige der verwendeten Quellsensoren für Verbrauchswerte
            if self._energy_sensor_configs:
                _LOGGER.info("=== ENERGY CONSUMPTION SENSORS ===")
                for hp_key, sensor_config in self._energy_sensor_configs.items():
                    sensor_id = sensor_config.get("sensor_entity_id")
                    _LOGGER.info("Energy consumption tracking for %s: using custom sensor '%s'", hp_key.upper(), sensor_id)
            else:
                _LOGGER.info("=== ENERGY CONSUMPTION SENSORS ===")
                _LOGGER.info("Energy consumption tracking: using default internal Modbus sensors")
                _LOGGER.info("(Configure custom sensors in lambda_wp_config.yaml if needed)")
        except Exception as e:
            _LOGGER.error("Error loading config: %s", e)
            # Fallback zu leeren Werten
            self._cycling_offsets = {}
            self._energy_offsets = {}
            self._energy_sensor_configs = {}

        # Lade persistierte Zählerstände (falls vorhanden) mit Reparatur-Funktion
        if os.path.exists(self._persist_file):
            data = await self._repair_and_load_persist_file()
        else:
            data = {}
        
        self._heating_cycles = data.get("heating_cycles", {})
        self._heating_energy = data.get("heating_energy", {})
        
        # Lade persistierte State-Informationen
        self._last_operating_state = data.get("last_operating_states", {})
        self._last_state = data.get("last_states", {})
        
        # Lade persistierte Energy Consumption Daten
        self._energy_consumption = data.get("energy_consumption", {})
        self._sensor_ids = data.get("sensor_ids", {})
        self._thermal_sensor_ids = data.get("thermal_sensor_ids", {})
        self._energy_sensor_states = data.get("energy_sensor_states", {})
        # Energy Offsets werden bereits aus der Config geladen

        # last_energy_reading: Bei Sensor-Wechsel sofort auf None setzen (bevor es verwendet wird),
        # damit kein falsches Delta (alter last + neuer Sensor) addiert wird – verhindert Sprung/Spike.
        loaded_last = data.get("last_energy_readings", {})
        corrected_last = dict(loaded_last)
        from .utils import detect_sensor_change, get_stored_sensor_id, get_stored_thermal_sensor_id
        all_hp_keys = set(self._energy_sensor_configs.keys()) | set(self._sensor_ids.keys()) | set(self._thermal_sensor_ids.keys())
        persist_data = {"sensor_ids": self._sensor_ids, "thermal_sensor_ids": self._thermal_sensor_ids}
        for hp_key in all_hp_keys:
            try:
                hp_idx = int(hp_key.replace("hp", ""))
            except (ValueError, AttributeError):
                continue
            current_sensor_id = None
            if hp_key in self._energy_sensor_configs:
                current_sensor_id = self._energy_sensor_configs[hp_key].get("sensor_entity_id")
            if not current_sensor_id:
                name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
                current_sensor_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
            stored_sensor_id = get_stored_sensor_id(persist_data, hp_idx)
            if detect_sensor_change(stored_sensor_id, current_sensor_id):
                corrected_last[hp_key] = None
                self._energy_first_value_seen[hp_key] = False
                _LOGGER.info(
                    "SENSOR-CHANGE-DETECTION: %s last_energy_reading sofort auf None gesetzt (Sensor-Wechsel, verhindert Delta-Sprung)",
                    hp_key,
                )
        self._last_energy_reading = corrected_last

        # Thermik: last_thermal_energy_reading bei Sensor-Wechsel auf None setzen
        loaded_thermal_last = data.get("last_thermal_energy_readings", {})
        corrected_thermal_last = dict(loaded_thermal_last)
        for hp_key in all_hp_keys:
            try:
                hp_idx = int(hp_key.replace("hp", ""))
            except (ValueError, AttributeError):
                continue
            current_thermal_id = None
            if hp_key in self._energy_sensor_configs:
                current_thermal_id = self._energy_sensor_configs[hp_key].get("thermal_sensor_entity_id")
            if not current_thermal_id:
                name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
                current_thermal_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_thermal_energy_output_accumulated"
            stored_thermal_id = get_stored_thermal_sensor_id(persist_data, hp_idx)
            if detect_sensor_change(stored_thermal_id, current_thermal_id):
                corrected_thermal_last[hp_key] = None
                self._thermal_energy_first_value_seen[hp_key] = False
                _LOGGER.info(
                    "SENSOR-CHANGE-DETECTION: %s last_thermal_energy_reading auf None (Thermik-Sensor-Wechsel)",
                    hp_key,
                )
        self._last_thermal_energy_reading = corrected_thermal_last

        _LOGGER.info("SENSOR-CHANGE-DETECTION: Geladene sensor_ids: %s", self._sensor_ids)
        
        _LOGGER.info(
            f"Restored last_operating_state: {self._last_operating_state}"
        )

        # Sensor-Wechsel-Erkennung für Energy Consumption Sensoren (NACH dem Laden der persistierten Daten)
        # Führe die Erkennung bei jedem Start aus, um Sensor-Wechsel zu erkennen
        _LOGGER.info("SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung für %s konfigurierte Sensoren", len(self._energy_sensor_configs))
        await self._detect_and_handle_sensor_changes()

    async def _detect_and_handle_sensor_changes(self):
        """Erkenne Sensor-Wechsel und behandle sie entsprechend."""
        _LOGGER.info("SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung")
        
        try:
            from .utils import (
                detect_sensor_change,
                get_stored_sensor_id,
                store_sensor_id,
                get_stored_thermal_sensor_id,
                store_thermal_sensor_id,
            )
            # Erstelle persist_data dict für die Hilfsfunktionen
            persist_data = {"sensor_ids": self._sensor_ids, "thermal_sensor_ids": self._thermal_sensor_ids}
            
            # Prüfe alle Wärmepumpen, die in _sensor_ids gespeichert sind (auch wenn keine Custom-Sensoren konfiguriert sind)
            all_hp_keys = set()
            
            # Füge Custom-Sensoren hinzu
            for hp_key in self._energy_sensor_configs.keys():
                all_hp_keys.add(hp_key)
            
            # Füge alle Wärmepumpen aus _sensor_ids und _thermal_sensor_ids hinzu
            for hp_key in self._sensor_ids.keys():
                all_hp_keys.add(hp_key)
            for hp_key in self._thermal_sensor_ids.keys():
                all_hp_keys.add(hp_key)
            
            _LOGGER.info("SENSOR-CHANGE-DETECTION: Prüfe %s Wärmepumpen: %s", len(all_hp_keys), sorted(all_hp_keys))
            
            for hp_key in all_hp_keys:
                # Extrahiere hp_idx aus hp_key (z.B. "hp1" -> 1)
                try:
                    hp_idx = int(hp_key.replace("hp", ""))
                except (ValueError, AttributeError):
                    _LOGGER.warning("SENSOR-CHANGE-DETECTION: Ungültiger hp_key: %s", hp_key)
                    continue
                
                # Bestimme aktuellen Sensor (Custom oder Default)
                current_sensor_id = None
                
                # Prüfe zuerst Custom-Sensor
                if hp_key in self._energy_sensor_configs:
                    current_sensor_id = self._energy_sensor_configs[hp_key].get("sensor_entity_id")
                    _LOGGER.info("SENSOR-CHANGE-DETECTION: %s - Custom-Sensor: %s", hp_key, current_sensor_id)
                
                # Falls kein Custom-Sensor, verwende Default-Sensor (lowercase wie entity_id)
                if not current_sensor_id:
                    name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
                    current_sensor_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
                    _LOGGER.info("SENSOR-CHANGE-DETECTION: %s - Default-Sensor: %s", hp_key, current_sensor_id)
                
                _LOGGER.info("SENSOR-CHANGE-DETECTION: Prüfe %s - aktueller Sensor: %s", hp_key, current_sensor_id)
                
                # Hole gespeicherte Sensor-ID
                stored_sensor_id = get_stored_sensor_id(persist_data, hp_idx)
                
                # Prüfe auf Sensor-Wechsel
                if detect_sensor_change(stored_sensor_id, current_sensor_id):
                    _LOGGER.info("SENSOR-CHANGE-DETECTION: Sensor-Wechsel erkannt für %s: %s -> %s", hp_key, stored_sensor_id, current_sensor_id)
                    await self._handle_sensor_change(hp_idx, current_sensor_id)
                
                # Speichere neue Sensor-ID für nächsten Vergleich
                store_sensor_id(persist_data, hp_idx, current_sensor_id)
                self._sensor_ids = persist_data["sensor_ids"]
                
                _LOGGER.info("SENSOR-CHANGE-DETECTION: Sensor-ID für %s aktualisiert: %s", hp_key, current_sensor_id)

            # Thermik-Sensor-Wechsel prüfen (analog zu elektrisch)
            for hp_key in all_hp_keys:
                try:
                    hp_idx = int(hp_key.replace("hp", ""))
                except (ValueError, AttributeError):
                    continue
                current_thermal_id = None
                if hp_key in self._energy_sensor_configs:
                    current_thermal_id = self._energy_sensor_configs[hp_key].get("thermal_sensor_entity_id")
                if not current_thermal_id:
                    name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
                    current_thermal_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_thermal_energy_output_accumulated"
                stored_thermal_id = get_stored_thermal_sensor_id(persist_data, hp_idx)
                if detect_sensor_change(stored_thermal_id, current_thermal_id):
                    _LOGGER.info(
                        "SENSOR-CHANGE-DETECTION: Thermik-Sensor-Wechsel für %s: %s -> %s",
                        hp_key, stored_thermal_id, current_thermal_id,
                    )
                    await self._handle_thermal_sensor_change(hp_idx, current_thermal_id)
                store_thermal_sensor_id(persist_data, hp_idx, current_thermal_id)
                self._thermal_sensor_ids = persist_data["thermal_sensor_ids"]

            # Speichere alle Änderungen in der JSON-Datei
            if self._sensor_ids or self._thermal_sensor_ids:
                _LOGGER.info(
                    "SENSOR-CHANGE-DETECTION: Speichere sensor_ids + thermal_sensor_ids in JSON"
                )
                self._persist_dirty = True
                await self._persist_counters()
                _LOGGER.info("SENSOR-CHANGE-DETECTION: sensor_ids erfolgreich gespeichert")
            
            _LOGGER.info("SENSOR-CHANGE-DETECTION: Sensor-Wechsel-Erkennung abgeschlossen")
            
        except Exception as e:
            _LOGGER.error("SENSOR-CHANGE-DETECTION: Fehler bei Sensor-Wechsel-Erkennung: %s", e)
            import traceback
            _LOGGER.error("SENSOR-CHANGE-DETECTION: Traceback: %s", traceback.format_exc())

    async def _handle_sensor_change(self, hp_idx: int, new_sensor_id: str):
        """Behandle Sensor-Wechsel mit intelligenter DB-Wert-Nutzung."""
        _LOGGER.info("SENSOR-CHANGE: === SENSOR-WECHSEL ERKANNT HP%s ===", hp_idx)
        _LOGGER.info("SENSOR-CHANGE: Neuer Sensor: %s", new_sensor_id)
        
        hp_key = f"hp{hp_idx}"
        
        # Prüfe ob es ein Default-Sensor ist (interner Modbus-Sensor)
        name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
        default_sensor_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
        
        is_default_sensor = (new_sensor_id == default_sensor_id)
        _LOGGER.info("SENSOR-CHANGE: Erwarteter Default-Sensor: %s", default_sensor_id)
        _LOGGER.info("SENSOR-CHANGE: Ist Default-Sensor: %s", is_default_sensor)
        
        if is_default_sensor:
            # SCHRITT 3: Wechsel zu Default-Sensor (interner Modbus)
            _LOGGER.info("SENSOR-CHANGE: → SCHRITT 3: Wechsel zu Default-Sensor (interner Modbus)")
            _LOGGER.info("SENSOR-CHANGE: → Lese DB-Wert vom Default-Sensor...")
            
            # Lese letzten DB-Wert vom Default-Sensor
            db_state = self.hass.states.get(new_sensor_id)
            _LOGGER.info("SENSOR-CHANGE: → DB-State: %s", (db_state.state if db_state else 'None'))
            
            if db_state and db_state.state not in ("unknown", "unavailable", "None"):
                try:
                    db_value = float(db_state.state)
                    _LOGGER.info("SENSOR-CHANGE: → DB-Wert konvertiert: %.2f kWh", db_value)
                    
                    if db_value > 0:
                        _LOGGER.info("SENSOR-CHANGE: → DB-Wert > 0: %.2f kWh", db_value)
                        _LOGGER.info("SENSOR-CHANGE: → Setze als Referenz für sofortige Delta-Berechnung")
                        _LOGGER.info("SENSOR-CHANGE: → Nächster Messwert wird mit diesem DB-Wert verglichen")
                        
                        # Setze DB-Wert als last_energy
                        self._last_energy_reading[hp_key] = db_value
                        self._energy_first_value_seen[hp_key] = True
                        self._persist_dirty = True
                        await self._persist_counters()
                        _LOGGER.info("SENSOR-CHANGE: → Referenzwert gesetzt, warte auf ersten Messwert")
                        _LOGGER.info("SENSOR-CHANGE: === SENSOR-WECHSEL ABGESCHLOSSEN: DB-REFERENZ GESETZT ===")
                        return
                        
                    else:
                        # DB-Wert ist 0
                        _LOGGER.info("SENSOR-CHANGE: → DB-Wert = 0, keine Historie verfügbar")
                        _LOGGER.info("SENSOR-CHANGE: → Starte Zero-Value Protection")
                        
                except (ValueError, TypeError) as e:
                    _LOGGER.warning("SENSOR-CHANGE: → Fehler beim Konvertieren des DB-Werts: %s", e)
                    _LOGGER.info("SENSOR-CHANGE: → Starte Zero-Value Protection")
            else:
                _LOGGER.info("SENSOR-CHANGE: → Kein DB-Wert verfügbar (State: %s)", (db_state.state if db_state else 'None'))
                _LOGGER.info("SENSOR-CHANGE: → Starte Zero-Value Protection")
        
        else:
            # SCHRITT 4: Wechsel zu externem/Custom Sensor
            _LOGGER.info("SENSOR-CHANGE: → SCHRITT 4: Wechsel zu externem/Custom Sensor")
            _LOGGER.info("SENSOR-CHANGE: → Keine DB-Historie verfügbar für externe Sensoren")
            _LOGGER.info("SENSOR-CHANGE: → Starte Zero-Value Protection")
        
        # Fallback: Zero-Value Protection
        _LOGGER.info("SENSOR-CHANGE: → AKTIVIERE ZERO-VALUE PROTECTION")
        _LOGGER.info("SENSOR-CHANGE: → Warte auf 2 aufeinanderfolgende Werte > 0")
        _LOGGER.info("SENSOR-CHANGE: → Erster Wert wird gespeichert, aber kein Delta berechnet")
        _LOGGER.info("SENSOR-CHANGE: → Ab zweitem Wert wird Delta berechnet")
        
        self._last_energy_reading[hp_key] = None
        self._energy_first_value_seen[hp_key] = False
        self._persist_dirty = True
        await self._persist_counters()
        _LOGGER.info("SENSOR-CHANGE: === SENSOR-WECHSEL ABGESCHLOSSEN: ZERO-VALUE PROTECTION AKTIV ===")

    async def _handle_thermal_sensor_change(self, hp_idx: int, new_sensor_id: str):
        """Behandle Thermik-Sensor-Wechsel (analog zu _handle_sensor_change)."""
        _LOGGER.info("SENSOR-CHANGE: === THERMIK-SENSOR-WECHSEL HP%s === Neuer Sensor: %s", hp_idx, new_sensor_id)
        hp_key = f"hp{hp_idx}"
        name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
        default_thermal_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_thermal_energy_output_accumulated"
        is_default = new_sensor_id == default_thermal_id
        if is_default:
            db_state = self.hass.states.get(new_sensor_id)
            if db_state and db_state.state not in ("unknown", "unavailable", "None"):
                try:
                    db_value = float(db_state.state)
                    if db_value > 0:
                        self._last_thermal_energy_reading[hp_key] = db_value
                        self._thermal_energy_first_value_seen[hp_key] = True
                        self._persist_dirty = True
                        await self._persist_counters()
                        _LOGGER.info("SENSOR-CHANGE: Thermik-Referenzwert gesetzt HP%s: %.2f kWh", hp_idx, db_value)
                        return
                except (ValueError, TypeError):
                    pass
        self._last_thermal_energy_reading[hp_key] = None
        self._thermal_energy_first_value_seen[hp_key] = False
        self._persist_dirty = True
        await self._persist_counters()
        _LOGGER.info("SENSOR-CHANGE: Thermik Zero-Value Protection aktiv HP%s", hp_idx)

    def _generate_entity_id(self, sensor_type: str, idx: int) -> str:
        # DEAD CODE GUARD: This method should no longer be called.
        # It is a remnant of the old template-sensor architecture where cycling/energy
        # values were written into coordinator.data under entity-ID keys.
        # Cycling and energy sensors now use internal state (_cycling_value / _energy_value)
        # updated via dispatcher signals, not coordinator.data lookups.
        # If this warning appears in the logs, the caller must be investigated.
        _LOGGER.warning(
            "_generate_entity_id called unexpectedly (possible dead-code remnant) – "
            "sensor_type=%s, idx=%s. Please report this at "
            "https://github.com/lambdanerds/lambda_heat_pumps/issues",
            sensor_type,
            idx,
        )
        if self._use_legacy_names:
            return f"sensor.hp{idx + 1}_{sensor_type}"
        else:
            return f"sensor.{self._name_prefix}_hp{idx + 1}_{sensor_type}"

    async def async_init(self) -> None:
        """Async initialization (inkl. Modbus-Connect für Auto-Detection)."""
        _LOGGER.debug("Initializing Lambda coordinator")
        _LOGGER.debug("Config directory: %s", self._config_dir)
        _LOGGER.debug("Config path: %s", self._config_path)

        try:
            await self._ensure_config_dir()
            _LOGGER.debug("Config directory ensured")

            self.disabled_registers = await load_disabled_registers(self.hass)
            _LOGGER.debug("Loaded disabled registers: %s", self.disabled_registers)

            # Lade sensor_overrides direkt beim Init
            self.sensor_overrides = await self._load_sensor_overrides()
            _LOGGER.debug("Loaded sensor name overrides: %s", self.sensor_overrides)

            # Initialize HA started flag
            self._ha_started = False

            # Register event listener for Home Assistant started
            self.hass.bus.async_listen_once(
                "homeassistant_started", self._on_ha_started
            )

            if not self.disabled_registers:
                _LOGGER.debug(
                    "No disabled registers configured - this is normal if you "
                    "haven't disabled any registers"
                )
            
            # Lade Offsets und persistierte Daten (immer, unabhängig von disabled registers)
            await self._load_offsets_and_persisted()

            # Modbus-Connect für Auto-Detection (wird im Produktivbetrieb ohnehin benötigt)
            await self._connect()

            # Initialize Entity Registry monitoring
            # Entity-based polling control now handled by entity lifecycle methods

        except Exception as e:
            _LOGGER.error("Failed to initialize coordinator: %s", str(e))
            self.disabled_registers = set()
            self.sensor_overrides = {}
            raise

    async def _ensure_config_dir(self):
        """Ensure config directory exists."""
        try:

            def _create_dirs():
                os.makedirs(self._config_dir, exist_ok=True)
                os.makedirs(self._config_path, exist_ok=True)
                _LOGGER.debug(
                    "Created directories: %s and %s",
                    self._config_dir,
                    self._config_path,
                )

            await self.hass.async_add_executor_job(_create_dirs)
        except Exception as e:
            _LOGGER.error("Failed to create config directories: %s", str(e))
            raise

    def _address_matches_individual_read_template(self, address: int, templates: list) -> bool:
        """
        Prüft ob eine Register-Adresse zu einem Individual-Read-Template passt.
        
        Für Register >= 1000: Konvertiert zu Template-Format (z.B. 5107 → "5n07")
        und prüft gegen die Template-Liste.
        Für Register < 1000: Direkter Vergleich mit Templates.
        
        Args:
            address: Register-Adresse als Integer
            templates: Liste von Templates (Strings wie "5n07" oder Integers < 1000)
        
        Returns:
            True wenn Adresse zu einem Template passt
        """
        if address < 1000:
            # Direkter Vergleich für statische Adressen < 1000
            return address in templates or str(address) in templates
        
        # Für Register >= 1000: Konvertiere zu Template-Format
        # Ersetze einfach das 2. Zeichen (Index 1) durch "n"
        # z.B. 5007 → "5n07", 5107 → "5n07", 5207 → "5n07"
        #     1020 → "1n20", 1050 → "1n50"
        address_str = str(address)
        template = address_str[0] + "n" + address_str[2:]
        return template in templates

    async def _read_registers_batch(self, address_list, sensor_mapping):
        """Read multiple registers in robust, type-safe batches."""
        data = {}

        # DEBUG: Log alle int32-Adressen
        int32_addresses = {addr: info for addr, info in address_list.items() 
                           if info.get("data_type") == "int32"}
        if int32_addresses:
            _LOGGER.debug(
                "INT32-REGISTER-DEBUG: address_list enthält %d int32-Register: %s",
                len(int32_addresses), list(int32_addresses.keys())
            )
        
        # DEBUG: Prüfe spezifisch Register 1020/1022
        if 1020 in address_list or 1022 in address_list:
            _LOGGER.debug(
                "INT32-REGISTER-DEBUG: Register 1020/1022 gefunden in address_list: "
                "1020=%s, 1022=%s, enabled_addresses 1020=%s, 1022=%s",
                1020 in address_list, 1022 in address_list,
                1020 in self._enabled_addresses if hasattr(self, '_enabled_addresses') else 'N/A',
                1022 in self._enabled_addresses if hasattr(self, '_enabled_addresses') else 'N/A'
            )

        # Globale Deduplizierung - verhindere mehrfaches Lesen der gleichen Register über alle Module
        unique_addresses = {}
        for address, sensor_info in address_list.items():
            # DEBUG: Spezifisch für 1020/1022
            if address in [1020, 1022]:
                _LOGGER.debug(
                    "INT32-REGISTER-DEBUG: Prüfe Register %d - "
                    "Im Cache: %s, Wert: %s",
                    address,
                    address in self._global_register_cache,
                    self._global_register_cache.get(address, "NICHT_GEFUNDEN")
                )
            
            # Prüfe globalen Cache zuerst
            if address in self._global_register_cache:
                # DEBUG: Für 1020/1022 - Zeige Cache-Status
                if address in [1020, 1022]:
                    _LOGGER.debug(
                        "INT32-REGISTER-DEBUG: Register %d ist im Cache (Wert: %s) - wird verwendet",
                        address, self._global_register_cache[address]
                    )
                # Verwende gecachten Wert (Cache wird pro Update-Zyklus geleert)
                sensor_id = sensor_mapping.get(address, f"addr_{address}")
                data[sensor_id] = self._global_register_cache[address]
                _LOGGER.debug("Using cached value for register %s", address)
                continue
            # Nur hinzufügen wenn nicht bereits gelesen
            if address not in unique_addresses:
                unique_addresses[address] = sensor_info

        # Sort addresses for potential batch optimization
        sorted_addresses = sorted(unique_addresses.keys())

        # Group addresses for batch reading, avoiding INT32 boundaries and mixed types
        batches = []
        current_batch = []
        current_type = None
        last_addr = None

        def get_type(addr):
            return unique_addresses[addr].get("data_type", "uint16")

        for addr in sorted_addresses:
            dtype = get_type(addr)
            # If INT32, always treat as a pair (addr, addr+1)
            if dtype == "int32":
                # If current batch is not empty, flush it first
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_type = None
                # Add both registers as a single batch
                batches.append([addr, addr + 1])
                last_addr = addr + 1
                continue
            # For INT16/UINT16, group only if consecutive and same type
            if (
                not current_batch
                or addr != last_addr + 1
                or current_type != dtype
                or len(current_batch) >= 120  # Modbus safety margin
            ):
                if current_batch:
                    batches.append(current_batch)
                current_batch = [addr]
                current_type = dtype
            else:
                current_batch.append(addr)
            last_addr = addr
        if current_batch:
            batches.append(current_batch)

        # Read batches
        for batch in batches:
            try:
                # If batch is a single INT32 (2 addresses), handle as such
                if len(batch) == 2 and get_type(batch[0]) == "int32":
                    await self._read_single_register(
                        batch[0], unique_addresses[batch[0]], sensor_mapping, data
                    )
                    continue
                start_addr = batch[0]
                count = len(batch)
                batch_key = (start_addr, count)

                # For very small batches, use individual reads (optimiert: 2 statt 3)
                if count < 2 or count > 100:
                    for addr in batch:
                        await self._read_single_register(
                            addr, unique_addresses[addr], sensor_mapping, data
                        )
                    continue

                # Prüfe ob dieser Batch bereits zu oft fehlgeschlagen ist
                if batch_key in self._individual_read_addresses:
                    _LOGGER.debug("Using individual reads for %s-%s (previous failures)", start_addr, start_addr + count - 1)
                    for addr in batch:
                        await self._read_single_register(
                            addr, unique_addresses[addr], sensor_mapping, data
                        )
                    continue

                # Prüfe ob Register in der Individual-Read-Liste stehen
                matched_addresses = [addr for addr in batch if self._address_matches_individual_read_template(addr, INDIVIDUAL_READ_REGISTERS)]
                if matched_addresses:
                    _LOGGER.debug("Using individual reads for %s-%s (configured individual read) - matched addresses: %s", start_addr, start_addr + count - 1, matched_addresses)
                    for addr in batch:
                        await self._read_single_register(
                            addr, unique_addresses[addr], sensor_mapping, data
                        )
                    continue

                _LOGGER.debug("Reading batch: start=%s, count=%s", start_addr, count)
                result = await async_read_holding_registers(
                    self.client,
                    start_addr,
                    count,
                    self.entry.data.get("slave_id", 1),
                )

                if hasattr(result, "isError") and result.isError():
                    # Erhöhe Fehlerzähler
                    self._batch_failures[batch_key] = self._batch_failures.get(batch_key, 0) + 1
                    
                    if self._batch_failures[batch_key] <= self._max_batch_failures:
                        _LOGGER.info(
                            "❌ MODBUS READ FAILED: Batch read error, addresses=%s, attempt=%d/%d, caller=_async_update_data",
                            f"{start_addr}-{start_addr + count - 1}", self._batch_failures[batch_key], self._max_batch_failures
                        )
                    else:
                        _LOGGER.info(
                            f"Switching to individual reads for {start_addr}-{start_addr + count - 1} after {self._max_batch_failures} failures"
                        )
                        self._individual_read_addresses.add(batch_key)
                else:
                    # Erfolgreicher Batch-Read
                    _LOGGER.debug(
                        "✅ MODBUS READ SUCCESS: Batch read successful, addresses=%s, caller=_async_update_data",
                        f"{start_addr}-{start_addr + count - 1}"
                    )
                    
                    # Process batch results - KEIN Fallback zu Individual-Reads!
                    i = 0
                    while i < len(batch):
                        addr = batch[i]
                        sensor_info = address_list[addr]
                        sensor_id = sensor_mapping[addr]
                        
                        # Extrahiere Wert aus Batch-Result
                        if i < len(result.registers):
                            value = result.registers[i]
                            
                            # Verarbeite den Wert basierend auf dem Datentyp
                            if sensor_info.get("data_type") == "int32":
                                # Für INT32: Kombiniere mit nächstem Register
                                if i + 1 < len(result.registers):
                                    next_value = result.registers[i + 1]
                                    # Verwende Sensor-spezifische register_order falls vorhanden, sonst globale Konfiguration
                                    # Rückwärtskompatibilität: byte_order wird auch akzeptiert
                                    register_order = sensor_info.get("register_order") or sensor_info.get("byte_order") or self._int32_register_order
                                    
                                    # DEBUG: Für 1020/1022
                                    if addr in [1020, 1022]:
                                        _LOGGER.debug(
                                            "INT32-REGISTER-DEBUG: Batch-Verarbeitung Register %d: "
                                            "Register[%d]=%d, Register[%d]=%d, order=%s",
                                            addr, i, value, i+1, next_value, register_order
                                        )
                                    
                                    value = combine_int32_registers([value, next_value], register_order)
                                    value = to_signed_32bit(value)
                                    
                                    # DEBUG: Für 1020/1022
                                    if addr in [1020, 1022]:
                                        _LOGGER.debug(
                                            "INT32-REGISTER-DEBUG: Register %d kombiniert (vor Scale): %d",
                                            addr, value
                                        )
                                    
                                    # Überspringe das nächste Register (bereits verarbeitet)
                                    i += 1
                                else:
                                    _LOGGER.warning(
                                        "Missing second register for int32 sensor %s at address %d (batch ended)",
                                        sensor_id, addr
                                    )
                                    i += 1
                                    continue
                            else:
                                # Für INT16/UINT16: Signed-Konvertierung falls nötig
                                if sensor_info.get("data_type") == "int16":
                                    value = to_signed_16bit(value)
                            
                            # WICHTIG: Scale-Wert anwenden (war zuvor fehlend!)
                            if "scale" in sensor_info:
                                value = value * sensor_info["scale"]
                            
                            # Cache den skalierten Wert global
                            self._global_register_cache[addr] = value
                            
                            # Speichere den skalierten Wert
                            data[sensor_id] = value
                        
                        i += 1
                
                # Erfolgreicher Batch-Read - Reset Fehlerzähler
                if batch_key in self._batch_failures:
                    del self._batch_failures[batch_key]
                if batch_key in self._individual_read_addresses:
                    self._individual_read_addresses.remove(batch_key)
                    _LOGGER.info("Batch reads restored for %s-%s", start_addr, start_addr + count - 1)
            except Exception as ex:
                _LOGGER.info(
                    "❌ MODBUS READ FAILED: Batch read error, addresses=%s, error=%s, caller=_async_update_data",
                    f"{batch[0]}-{batch[-1]}", ex
                )
                for addr in batch:
                    await self._read_single_register(
                        addr, address_list[addr], sensor_mapping, data
                    )
        return data

    async def _read_single_register(self, address, sensor_info, sensor_mapping, data):
        """Read a single register with error handling."""
        try:
            sensor_id = sensor_mapping[address]
            count = 2 if sensor_info.get("data_type") == "int32" else 1

            # DEBUG: Für 1020/1022
            if address in [1020, 1022]:
                _LOGGER.debug(
                    "INT32-REGISTER-DEBUG: _read_single_register aufgerufen für %d, "
                    "sensor_id=%s, count=%d, data_type=%s, register_order=%s",
                    address, sensor_id, count, sensor_info.get("data_type"),
                    self._int32_register_order
                )

            _LOGGER.debug(
                f"Address {address} polling status: enabled=True (entity-based)"
            )
            result = await async_read_holding_registers(
                self.client,
                address,
                count,
                self.entry.data.get("slave_id", 1),
            )

            if hasattr(result, "isError") and result.isError():
                _LOGGER.debug("Error reading register %s: %s", address, result)
                return

            if count == 2:
                # DEBUG: Für 1020/1022
                if address in [1020, 1022]:
                    _LOGGER.debug(
                        "INT32-REGISTER-DEBUG: Kombiniere Register %d: "
                        "Register[0]=%d, Register[1]=%d, order=%s",
                        address, result.registers[0], result.registers[1], 
                        self._int32_register_order
                    )
                value = combine_int32_registers(result.registers, self._int32_register_order)
                value = to_signed_32bit(value)
                # DEBUG: Für 1020/1022
                if address in [1020, 1022]:
                    _LOGGER.debug(
                        "INT32-REGISTER-DEBUG: Register %d kombiniert (vor Scale): %d",
                        address, value
                    )
            else:
                value = result.registers[0]
                if sensor_info.get("data_type") == "int16":
                    value = to_signed_16bit(value)

            if "scale" in sensor_info:
                value = value * sensor_info["scale"]
                # DEBUG: Für 1020/1022
                if address in [1020, 1022]:
                    _LOGGER.debug(
                        "INT32-REGISTER-DEBUG: Register %d nach Scale (%s): %s",
                        address, sensor_info["scale"], value
                    )

            data[sensor_id] = value
            
            # Cache den Wert im globalen Cache für andere Module
            self._global_register_cache[address] = value
            if address in [1020, 1022]:
                _LOGGER.debug("INT32-REGISTER-DEBUG: Cached register %s = %s", address, value)
            else:
                _LOGGER.debug("Cached register %s = %s", address, value)

        except Exception as ex:
            _LOGGER.info("MODBUS READ FAILED: address=%s, error=%s, caller=_async_update_data", address, ex)

    async def _read_general_sensors_batch(self, data):
        """Read general sensors using global register collection."""
        for sensor_id, sensor_info in SENSOR_TYPES.items():
            if self.is_register_disabled(sensor_info["address"]):
                continue
            if not self.is_address_enabled_by_entity(sensor_info["address"]):
                continue

            # Sammle Register-Request statt sofort zu lesen
            self._add_register_request(sensor_info["address"], sensor_info, sensor_id)

    async def _read_heatpump_sensors_batch(self, data, num_hps, compatible_hp_sensors):
        """Read heat pump sensors using global register collection."""
        for hp_idx in range(1, num_hps + 1):
            base_address = generate_base_addresses("hp", num_hps)[hp_idx]

            for sensor_id, sensor_info in compatible_hp_sensors.items():
                address = base_address + sensor_info["relative_address"]
                
                # DEBUG: Spezifisch für int32-Sensoren
                if sensor_info.get("data_type") == "int32":
                    _LOGGER.debug(
                        "INT32-REGISTER-DEBUG: Sensor %s (hp%d_%s), address=%d, "
                        "enabled=%s, disabled=%s",
                        sensor_id, hp_idx, sensor_id, address,
                        self.is_address_enabled_by_entity(address),
                        self.is_register_disabled(address)
                    )
                
                if not self.is_address_enabled_by_entity(address):
                    if address in [1020, 1022]:
                        _LOGGER.debug(
                            "INT32-REGISTER-DEBUG: Register %d ist NICHT enabled - "
                            "Entity-basiertes Polling blockiert!",
                            address
                        )
                    continue

                # Sammle Register-Request statt sofort zu lesen
                self._add_register_request(address, sensor_info, f"hp{hp_idx}_{sensor_id}")

    async def _read_boiler_sensors_batch(self, data, num_boil, compatible_boil_sensors):
        """Read boiler sensors using global register collection."""
        for boil_idx in range(1, num_boil + 1):
            base_address = generate_base_addresses("boil", num_boil)[boil_idx]

            for sensor_id, sensor_info in compatible_boil_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                # Sammle Register-Request statt sofort zu lesen
                self._add_register_request(address, sensor_info, f"boil{boil_idx}_{sensor_id}")

    async def _read_buffer_sensors_batch(self, data, num_buff, compatible_buff_sensors):
        """Read buffer sensors using global register collection."""
        for buff_idx in range(1, num_buff + 1):
            base_address = generate_base_addresses("buff", num_buff)[buff_idx]

            for sensor_id, sensor_info in compatible_buff_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                # Sammle Register-Request statt sofort zu lesen
                self._add_register_request(address, sensor_info, f"buff{buff_idx}_{sensor_id}")

    async def _read_solar_sensors_batch(self, data, num_sol, compatible_sol_sensors):
        """Read solar sensors using global register collection."""
        for sol_idx in range(1, num_sol + 1):
            base_address = generate_base_addresses("sol", num_sol)[sol_idx]

            for sensor_id, sensor_info in compatible_sol_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                # Sammle Register-Request statt sofort zu lesen
                self._add_register_request(address, sensor_info, f"sol{sol_idx}_{sensor_id}")

    async def _setup_entity_registry_monitoring(self):
        """Setup Entity Registry monitoring for dynamic polling."""
        try:
            self._entity_registry = async_get_entity_registry(self.hass)

            # Build initial entity-to-address mapping
            await self._update_entity_address_mapping()

            # Register listener for entity registry changes via event bus
            self.hass.bus.async_listen(
                "entity_registry_updated", self._on_entity_registry_changed
            )

            _LOGGER.debug(
                "Entity Registry monitoring setup complete. "
                "Initial enabled addresses: %s",
                len(self._enabled_addresses),
            )

        except Exception as e:
            _LOGGER.error("Failed to setup entity registry monitoring: %s", str(e))
            raise

    async def _update_entity_address_mapping(self):
        """Update the mapping of entity_id to register address."""
        if not self._entity_registry:
            return

        try:
            # Get all entities for this integration
            entities = self._entity_registry.entities

            # Reset mappings
            self._entity_address_mapping.clear()
            self._enabled_addresses.clear()

            # Get device counts from config
            num_hps = self.entry.data.get("num_hps", 1)
            num_boil = self.entry.data.get("num_boil", 1)
            num_buff = self.entry.data.get("num_buff", 0)
            num_sol = self.entry.data.get("num_sol", 0)
            num_hc = self.entry.data.get("num_hc", 1)

            # Get firmware version for sensor filtering
            fw_version = get_firmware_version_int(self.entry)

            # Templates for each device type
            templates = [
                (
                    "hp",
                    num_hps,
                    get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version),
                ),
                (
                    "boil",
                    num_boil,
                    get_compatible_sensors(BOIL_SENSOR_TEMPLATES, fw_version),
                ),
                (
                    "buff",
                    num_buff,
                    get_compatible_sensors(BUFF_SENSOR_TEMPLATES, fw_version),
                ),
                (
                    "sol",
                    num_sol,
                    get_compatible_sensors(SOL_SENSOR_TEMPLATES, fw_version),
                ),
                ("hc", num_hc, get_compatible_sensors(HC_SENSOR_TEMPLATES, fw_version)),
            ]

            # Build mapping for each device type
            for prefix, count, template in templates:
                for idx in range(1, count + 1):
                    base_address = generate_base_addresses(prefix, count)[idx]
                    for sensor_id, sensor_info in template.items():
                        address = base_address + sensor_info["relative_address"]

                        # Create potential entity IDs (both legacy and new format)
                        name_prefix = normalize_name_prefix(
                            self.entry.data.get("name", "")
                        )
                        potential_entity_ids = [
                            f"sensor.{name_prefix}_{prefix}{idx}_{sensor_id}",
                            f"sensor.{name_prefix}_{prefix.upper()}{idx}_{sensor_id}",
                            f"sensor.{name_prefix}{prefix}{idx}_{sensor_id}",
                        ]

                        # Check if any variant exists and is enabled
                        for entity_id in potential_entity_ids:
                            if entity_id in entities:
                                entity = entities[entity_id]
                                self._entity_address_mapping[entity_id] = address

                                # Check if entity is enabled (not disabled)
                                if not entity.disabled:
                                    self._enabled_addresses.add(address)
                                    _LOGGER.debug(
                                        "Entity %s (address %d) is enabled",
                                        entity_id,
                                        address,
                                    )
                                else:
                                    _LOGGER.debug(
                                        "Entity %s (address %d) is disabled",
                                        entity_id,
                                        address,
                                    )
                                break

            # Also add general sensors (SENSOR_TYPES)
            for sensor_id, sensor_info in SENSOR_TYPES.items():
                address = sensor_info["address"]
                entity_id = f"sensor.{name_prefix}_{sensor_id}"

                if entity_id in entities:
                    entity = entities[entity_id]
                    self._entity_address_mapping[entity_id] = address

                    if not entity.disabled:
                        self._enabled_addresses.add(address)
                        _LOGGER.debug(
                            "General entity %s (address %d) is enabled",
                            entity_id,
                            address,
                        )
                    else:
                        _LOGGER.debug(
                            "General entity %s (address %d) is disabled",
                            entity_id,
                            address,
                        )

            _LOGGER.debug(
                "Updated entity mappings: %d entities, %d enabled addresses",
                len(self._entity_address_mapping),
                len(self._enabled_addresses),
            )

        except Exception as e:
            _LOGGER.error("Failed to update entity address mapping: %s", str(e))

    @callback
    def _on_entity_registry_changed(self, event):
        """Handle entity registry changes."""
        try:
            data = event.data
            entity_id = data.get("entity_id")
            _name_prefix = normalize_name_prefix(self.entry.data.get("name", ""))
            if entity_id and _name_prefix and entity_id.startswith(
                f"sensor.{_name_prefix}_"
            ):
                # This is one of our entities
                _LOGGER.debug("Entity registry change for %s: %s", entity_id, data)

                # Schedule update of address mapping
                self.hass.async_create_task(self._update_entity_address_mapping())

        except Exception as e:
            _LOGGER.error("Error handling entity registry change: %s", str(e))

    def is_address_enabled_by_entity(self, address: int) -> bool:
        """Check if a register address should be polled based on entity state."""
        # Use simple enabled addresses set from entity lifecycle methods
        is_enabled = address in self._enabled_addresses

        _LOGGER.debug(
            "Address %d polling status: enabled=%s (entity-based)", address, is_enabled
        )

        return is_enabled

    def is_register_disabled(self, address: int) -> bool:
        """Check if a register is disabled."""
        if not hasattr(self, "disabled_registers"):
            _LOGGER.error("disabled_registers not initialized")
            return False

        # Debug: Ausgabe der Typen und Inhalte
        _LOGGER.debug(
            "Check if address %r (type: %s) is in disabled_registers: %r (types: %r)",
            address,
            type(address),
            self.disabled_registers,
            {type(x) for x in self.disabled_registers},
        )

        is_disabled = is_register_disabled(address, self.disabled_registers)
        if is_disabled:
            _LOGGER.debug(
                "Register %d is disabled (in set: %s)",
                address,
                self.disabled_registers,
            )
        else:
            _LOGGER.debug(
                "Register %d is not disabled (checked against set: %s)",
                address,
                self.disabled_registers,
            )
        return is_disabled

    async def _connect(self) -> None:
        """Connect to the Modbus device."""
        try:
            from pymodbus.client import AsyncModbusTcpClient

            if (
                self.client
                and hasattr(self.client, "connected")
                and self.client.connected
            ):
                _LOGGER.info("🔌 MODBUS CONNECT: Already connected to %s:%s", self.host, self.port)
                return

            _LOGGER.info("🔌 MODBUS CONNECT: Starting connection to %s:%s (coordinator_id=%s)", self.host, self.port, id(self))
            self.client = AsyncModbusTcpClient(
                host=self.host, port=self.port, timeout=10
            )

            if not await self.client.connect():
                msg = f"Failed to connect to {self.host}:{self.port}"
                _LOGGER.info("MODBUS CONNECT: Failed to connect to %s:%s", self.host, self.port)
                raise UpdateFailed(msg)

            _LOGGER.info("MODBUS CONNECT: Successfully connected to %s:%s (coordinator_id=%s)", self.host, self.port, id(self))

        except Exception as e:
            _LOGGER.info("MODBUS CONNECT: Failed to connect to %s:%s, error=%s (coordinator_id=%s)", self.host, self.port, e, id(self))
            self.client = None
            msg = f"Connection failed: {e}"
            raise UpdateFailed(msg) from e

    def _cycling_entities_ready(self) -> bool:
        """Check whether cycling counter entities are registered and ready."""
        try:
            return (
                "lambda_heat_pumps" in self.hass.data
                and self.entry.entry_id in self.hass.data["lambda_heat_pumps"]
                and "cycling_entities" in self.hass.data["lambda_heat_pumps"][self.entry.entry_id]
            )
        except Exception:
            return False

    async def _run_cycling_edge_detection(self, data: dict) -> None:
        """Run edge detection on HP_OPERATING_STATE (reg 1003) and compressor_unit_rating (reg 1010).

        Called exclusively by _async_fast_update. Increments cycling counters on
        rising-edge transitions. Updates _last_operating_state and _last_compressor_rating.
        """
        num_hps = self.entry.data.get("num_hps", 1)
        MODES = {
            "heating": 1,
            "hot_water": 2,
            "cooling": 3,
            "defrost": 5,
        }

        # --- HP_OPERATING_STATE edge detection ---
        for hp_idx in range(1, num_hps + 1):
            op_state_val = data.get(f"hp{hp_idx}_operating_state")
            if op_state_val is None:
                continue

            last_op_state = self._last_operating_state.get(str(hp_idx), "UNBEKANNT")

            if last_op_state == "UNBEKANNT":
                _LOGGER.info(
                    "Fast poll: init _last_operating_state HP%d = %s", hp_idx, op_state_val
                )
            elif last_op_state != op_state_val:
                _LOGGER.debug(
                    "Fast poll: HP%d operating_state %s -> %s", hp_idx, last_op_state, op_state_val
                )

            for mode, mode_val in MODES.items():
                cycling_key = f"{mode}_cycles"
                if not hasattr(self, cycling_key):
                    setattr(self, cycling_key, {})
                cycles = getattr(self, cycling_key)

                _LOGGER.debug(
                    "FAST EDGE HP%s: init=%s last=%s mode_val=%s cur=%s",
                    hp_idx, self._initialization_complete, last_op_state, mode_val, op_state_val,
                )

                if (
                    self._initialization_complete
                    and last_op_state != "UNBEKANNT"
                    and last_op_state != mode_val
                    and op_state_val == mode_val
                ):
                    _LOGGER.info(
                        "Edge detected: HP%d operating state → %s (was %s)",
                        hp_idx, mode, last_op_state,
                    )
                    if self._cycling_entities_ready():
                        await increment_cycling_counter(
                            self.hass,
                            mode=mode,
                            hp_index=hp_idx,
                            name_prefix=self.entry.data.get("name", "eu08l"),
                            use_legacy_modbus_names=self._use_legacy_names,
                        )
                        old_count = cycles.get(hp_idx, 0)
                        if not isinstance(old_count, (int, float)):
                            old_count = 0
                        new_count = old_count + 1
                        cycles[hp_idx] = new_count
                        _LOGGER.info(
                            "🔄 FAST EDGE: HP%d %s → %s | %s: %d → %d",
                            hp_idx, last_op_state, op_state_val, mode, old_count, new_count,
                        )
                    else:
                        _LOGGER.debug(
                            "Fast poll: cycling entities not ready, skipping HP%d %s", hp_idx, mode
                        )
                elif not self._initialization_complete:
                    _LOGGER.debug(
                        "Fast poll: HP%d %s edge suppressed during init", hp_idx, mode
                    )

            self._last_operating_state[str(hp_idx)] = op_state_val

        # --- compressor_unit_rating edge detection (0 → >0 = compressor start) ---
        for hp_idx in range(1, num_hps + 1):
            rating_val = data.get(f"hp{hp_idx}_compressor_unit_rating")
            if rating_val is None:
                continue

            last_rating = self._last_compressor_rating.get(str(hp_idx), "UNBEKANNT")

            if last_rating == "UNBEKANNT":
                _LOGGER.info(
                    "Fast poll: init _last_compressor_rating HP%d = %s", hp_idx, rating_val
                )
            elif last_rating != rating_val:
                _LOGGER.debug(
                    "Fast poll: HP%d compressor_unit_rating %s -> %s", hp_idx, last_rating, rating_val
                )

            mode = "compressor_start"
            cycling_key = f"{mode}_cycles"
            if not hasattr(self, cycling_key):
                setattr(self, cycling_key, {})
            cycles = getattr(self, cycling_key)

            if (
                self._initialization_complete
                and last_rating != "UNBEKANNT"
                and last_rating == 0
                and rating_val != 0
            ):
                _LOGGER.info(
                    "Edge detected: HP%d compressor started (rating 0 → %s)",
                    hp_idx, rating_val,
                )
                if self._cycling_entities_ready():
                    await increment_cycling_counter(
                        self.hass,
                        mode=mode,
                        hp_index=hp_idx,
                        name_prefix=self.entry.data.get("name", "eu08l"),
                        use_legacy_modbus_names=self._use_legacy_names,
                    )
                    old_count = cycles.get(hp_idx, 0)
                    if not isinstance(old_count, (int, float)):
                        old_count = 0
                    new_count = old_count + 1
                    cycles[hp_idx] = new_count
                    _LOGGER.info(
                        "🔄 FAST EDGE compressor_unit_rating: HP%d 0 → %s | %s: %d → %d",
                        hp_idx, rating_val, mode, old_count, new_count,
                    )
                else:
                    _LOGGER.debug(
                        "Fast poll: cycling entities not ready, skipping HP%d %s (compressor_unit_rating)", hp_idx, mode
                    )
            elif not self._initialization_complete:
                _LOGGER.debug(
                    "Fast poll: HP%d %s (compressor_unit_rating) edge suppressed during init", hp_idx, mode
                )

            self._last_compressor_rating[str(hp_idx)] = rating_val

        self._persist_dirty = True

    async def _async_fast_update(self, now) -> None:
        """Fast poll: read HP_OPERATING_STATE (1003) and compressor_unit_rating (1010) for edge detection.

        Runs on fast_update_interval (default 2s). Serialized with the full update
        via _modbus_lock. Skips this cycle if the lock is already held.
        """
        if not self._initialization_complete or self.hass.is_stopping or self.client is None:
            return

        if self._full_update_running:
            _LOGGER.debug("Fast poll skipped: full update in progress")
            return

        try:
            num_hps = self.entry.data.get("num_hps", 1)
            data = {}
            for hp_idx in range(1, num_hps + 1):
                base_addr = 1000 + (hp_idx - 1) * 100
                # HP_OPERATING_STATE (register offset 3)
                result = await async_read_holding_registers(
                    self.client, base_addr + 3, 1, self.slave_id
                )
                if result is not None and not result.isError():
                    data[f"hp{hp_idx}_operating_state"] = result.registers[0]
                # compressor_unit_rating (register offset 10)
                result = await async_read_holding_registers(
                    self.client, base_addr + 10, 1, self.slave_id
                )
                if result is not None and not result.isError():
                    data[f"hp{hp_idx}_compressor_unit_rating"] = result.registers[0]

            _LOGGER.debug(
                "Fast poll: read %d HP(s) — %s",
                num_hps,
                ", ".join(
                    f"HP{i} op_state={data.get(f'hp{i}_operating_state', 'n/a')} comp_rating={data.get(f'hp{i}_compressor_unit_rating', 'n/a')}"
                    for i in range(1, num_hps + 1)
                ),
            )
            await self._run_cycling_edge_detection(data)

        except Exception as ex:
            _LOGGER.debug("Fast poll error (non-fatal): %s", ex)

    async def _async_update_data(self) -> dict:
        """Fetch data from Lambda device."""
        self._full_update_running = True
        try:
            _LOGGER.debug("PRODUCTION: Starting data update (coordinator_id=%s)", id(self))
            # Check if Home Assistant is shutting down
            if self.hass.is_stopping:
                _LOGGER.debug("Home Assistant is stopping, skipping data update")
                return self.data

            # Reset global register cache für neuen Update-Zyklus
            self._global_register_cache = {}
            self._global_register_requests = {}  # Sammle alle Register-Requests vor dem Lesen
            _LOGGER.debug("Reset global register cache for new update cycle")
            
            # 🎯 NEUE LOGIK: Warte auf stabile Verbindung vor Datenupdate
            _LOGGER.debug("COORDINATOR: Checking connection stability before data update...")
            await wait_for_stable_connection(self)
            _LOGGER.debug("COORDINATOR: Connection stable, proceeding with data update")

            # Get firmware version for sensor filtering
            fw_version = get_firmware_version_int(self.entry)

            # Filter compatible sensors based on firmware version
            compatible_hp_sensors = get_compatible_sensors(
                HP_SENSOR_TEMPLATES, fw_version
            )
            compatible_boil_sensors = get_compatible_sensors(
                BOIL_SENSOR_TEMPLATES, fw_version
            )
            compatible_buff_sensors = get_compatible_sensors(
                BUFF_SENSOR_TEMPLATES, fw_version
            )
            compatible_sol_sensors = get_compatible_sensors(
                SOL_SENSOR_TEMPLATES, fw_version
            )
            compatible_hc_sensors = get_compatible_sensors(
                HC_SENSOR_TEMPLATES, fw_version
            )

            data = {}
            update_interval_seconds = self.entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            interval = update_interval_seconds / 3600.0  # Intervall in Stunden
            
            # Debug: Start data update
            _LOGGER.debug("Starting _async_update_data")
            num_hps = self.entry.data.get("num_hps", 1)
            # Generische Flankenerkennung für alle relevanten Modi
            MODES = {
                "heating": 1,  # CH
                "hot_water": 2,  # DHW
                "cooling": 3,  # CC
                "defrost": 5,  # DEFROST
            }
            # HP_STATE Modi (separat, da auf HP_STATE Register basierend)
            HP_STATE_MODES = {
                "compressor_start": 2,  # RESTART-BLOCK
            }
            # Initialisiere _last_operating_state nur wenn nicht bereits aus Persistierung geladen
            if not hasattr(self, "_last_operating_state"):
                self._last_operating_state = {}
            # Initialisiere _last_state nur wenn nicht bereits aus Persistierung geladen
            if not hasattr(self, "_last_state"):
                self._last_state = {}

            # Read general sensors with batch optimization
            await self._read_general_sensors_batch(data)

            # Read heat pump sensors with batch optimization
            num_hps = self.entry.data.get("num_hps", 1)
            await self._read_heatpump_sensors_batch(
                data, num_hps, compatible_hp_sensors
            )

            # Flankenerkennung wird nach dem Lesen der Register ausgeführt

            # Read boiler sensors
            num_boil = self.entry.data.get("num_boil", 1)
            for boil_idx in range(1, num_boil + 1):
                base_address = generate_base_addresses("boil", num_boil)[boil_idx]
                for sensor_id, sensor_info in compatible_boil_sensors.items():
                    address = base_address + sensor_info["relative_address"]
                    if not self.is_address_enabled_by_entity(address):
                        _LOGGER.debug(
                            "Skipping BOIL%d sensor %s (address %d) - entity disabled or not found",
                            boil_idx,
                            sensor_id,
                            address,
                        )
                        continue
                    try:
                        address = base_address + sensor_info["relative_address"]
                        count = 2 if sensor_info.get("data_type") == "int32" else 1
                        result = await async_read_holding_registers(
                            self.client,
                            address,
                            count,
                            self.entry.data.get("slave_id", 1),
                        )
                        if hasattr(result, "isError") and result.isError():
                            _LOGGER.info(
                                "❌ MODBUS READ FAILED: address=%d, result=%s, caller=_async_update_data",
                                address, result
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_register_order)
                            value = to_signed_32bit(value)
                        else:
                            value = result.registers[0]
                            if sensor_info.get("data_type") == "int16":
                                value = to_signed_16bit(value)
                        if "scale" in sensor_info:
                            value = value * sensor_info["scale"]
                        # Prüfe auf Override-Name
                        override_name = None
                        if hasattr(self, "sensor_overrides"):
                            override_name = self.sensor_overrides.get(
                                f"boil{boil_idx}_{sensor_id}"
                            )
                        key = (
                            override_name
                            if override_name
                            else f"boil{boil_idx}_{sensor_id}"
                        )
                        data[key] = value
                    except Exception as ex:
                        _LOGGER.debug(
                            "Error reading register %d: %s",
                            address,
                            ex,
                        )

            # Read buffer sensors
            num_buff = self.entry.data.get("num_buff", 0)
            for buff_idx in range(1, num_buff + 1):
                base_address = generate_base_addresses("buff", num_buff)[buff_idx]
                for sensor_id, sensor_info in compatible_buff_sensors.items():
                    address = base_address + sensor_info["relative_address"]
                    if not self.is_address_enabled_by_entity(address):
                        _LOGGER.debug(
                            "Skipping BUFF%d sensor %s (address %d) - entity disabled or not found",
                            buff_idx,
                            sensor_id,
                            address,
                        )
                        continue
                    try:
                        address = base_address + sensor_info["relative_address"]
                        count = 2 if sensor_info.get("data_type") == "int32" else 1
                        result = await async_read_holding_registers(
                            self.client,
                            address,
                            count,
                            self.entry.data.get("slave_id", 1),
                        )
                        if hasattr(result, "isError") and result.isError():
                            _LOGGER.info(
                                "❌ MODBUS READ FAILED: address=%d, result=%s, caller=_async_update_data",
                                address, result
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_register_order)
                            value = to_signed_32bit(value)
                        else:
                            value = result.registers[0]
                            if sensor_info.get("data_type") == "int16":
                                value = to_signed_16bit(value)
                        if "scale" in sensor_info:
                            value = value * sensor_info["scale"]
                        # Prüfe auf Override-Name
                        override_name = None
                        if hasattr(self, "sensor_overrides"):
                            override_name = self.sensor_overrides.get(
                                f"buff{buff_idx}_{sensor_id}"
                            )
                        key = (
                            override_name
                            if override_name
                            else f"buff{buff_idx}_{sensor_id}"
                        )
                        data[key] = value
                    except Exception as ex:
                        _LOGGER.debug(
                            "Error reading register %d: %s",
                            address,
                            ex,
                        )

            # Read solar sensors
            num_sol = self.entry.data.get("num_sol", 0)
            for sol_idx in range(1, num_sol + 1):
                base_address = generate_base_addresses("sol", num_sol)[sol_idx]
                for sensor_id, sensor_info in compatible_sol_sensors.items():
                    address = base_address + sensor_info["relative_address"]
                    if not self.is_address_enabled_by_entity(address):
                        _LOGGER.debug(
                            "Skipping SOL%d sensor %s (address %d) - entity disabled or not found",
                            sol_idx,
                            sensor_id,
                            address,
                        )
                        continue
                    try:
                        address = base_address + sensor_info["relative_address"]
                        count = 2 if sensor_info.get("data_type") == "int32" else 1
                        result = await async_read_holding_registers(
                            self.client,
                            address,
                            count,
                            self.entry.data.get("slave_id", 1),
                        )
                        if hasattr(result, "isError") and result.isError():
                            _LOGGER.info(
                                "❌ MODBUS READ FAILED: address=%d, result=%s, caller=_async_update_data",
                                address, result
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_register_order)
                            value = to_signed_32bit(value)
                        else:
                            value = result.registers[0]
                            if sensor_info.get("data_type") == "int16":
                                value = to_signed_16bit(value)
                        if "scale" in sensor_info:
                            value = value * sensor_info["scale"]
                        # Prüfe auf Override-Name
                        override_name = None
                        if hasattr(self, "sensor_overrides"):
                            override_name = self.sensor_overrides.get(
                                f"sol{sol_idx}_{sensor_id}"
                            )
                        key = (
                            override_name
                            if override_name
                            else f"sol{sol_idx}_{sensor_id}"
                        )
                        data[key] = value
                    except Exception as ex:
                        _LOGGER.debug(
                            "Error reading register %d: %s",
                            address,
                            ex,
                        )

            # Read heating circuit sensors using global register collection
            num_hc = self.entry.data.get("num_hc", 1)
            for hc_idx in range(1, num_hc + 1):
                base_address = generate_base_addresses("hc", num_hc)[hc_idx]
                for sensor_id, sensor_info in compatible_hc_sensors.items():
                    address = base_address + sensor_info["relative_address"]
                    if not self.is_address_enabled_by_entity(address):
                        _LOGGER.debug(
                            "Skipping HC%d sensor %s (address %d) - entity disabled or not found",
                            hc_idx,
                            sensor_id,
                            address,
                        )
                        continue

                    # Sammle Register-Request statt sofort zu lesen
                    self._add_register_request(address, sensor_info, f"hc{hc_idx}_{sensor_id}")

            # Dummy-Keys für Template-Sensoren einfügen
            # Erzeuge alle möglichen Template-Sensor-IDs
            num_hps = self.entry.data.get("num_hps", 1)
            num_boil = self.entry.data.get("num_boil", 1)
            num_buff = self.entry.data.get("num_buff", 0)
            num_sol = self.entry.data.get("num_sol", 0)
            num_hc = self.entry.data.get("num_hc", 1)
            DEVICE_COUNTS = {
                "hp": num_hps,
                "boil": num_boil,
                "buff": num_buff,
                "sol": num_sol,
                "hc": num_hc,
            }
            for device_type, count in DEVICE_COUNTS.items():
                for idx in range(1, count + 1):
                    device_prefix = f"{device_type}{idx}"
                    for sensor_id, sensor_info in CALCULATED_SENSOR_TEMPLATES.items():
                        if sensor_info.get("device_type") == device_type:
                            key = f"{device_prefix}_{sensor_id}"
                            # Setze einen sich ändernden Wert, z.B. Zeitstempel
                            data[key] = time.time()

            # Update room temperature and PV surplus only after Home Assistant
            # has started. This prevents timing issues with template sensors
            if hasattr(self, "_ha_started") and self._ha_started:
                # Note: Writing operations moved to services.py
                pass

            # 🚀 NEUE OPTIMIERUNG: Lese alle gesammelten Register in einem großen Batch
            global_data = await self._read_all_registers_globally()
            data.update(global_data)
            _LOGGER.debug("Global register reading completed: %s values", len(global_data))

            # Energieintegration für aktiven Modus (Cycling-Flankenerkennung läuft via _async_fast_update)
            for hp_idx in range(1, num_hps + 1):
                op_state_val = data.get(f"hp{hp_idx}_operating_state")
                if op_state_val is None:
                    continue

                for mode, mode_val in MODES.items():
                    energy_key = f"{mode}_energy"
                    if not hasattr(self, energy_key):
                        setattr(self, energy_key, {})
                    energy = getattr(self, energy_key)

                    if hp_idx not in energy:
                        energy[hp_idx] = 0.0
                    elif isinstance(energy[hp_idx], dict):
                        _LOGGER.warning("energy[%s] is a dict, converting to 0.0: %s", hp_idx, energy[hp_idx])
                        energy[hp_idx] = 0.0

                    power_info = HP_SENSOR_TEMPLATES.get("actual_heating_capacity")
                    if power_info:
                        power_val = data.get(f"hp{hp_idx}_actual_heating_capacity", 0.0)
                        if op_state_val == mode_val:
                            if not isinstance(energy[hp_idx], (int, float)):
                                energy[hp_idx] = 0.0
                            energy[hp_idx] = energy[hp_idx] + (power_val * interval)

            await self._persist_counters()
            
            # Setze Dirty-Flag wenn sich Werte geändert haben
            self._persist_dirty = True

            # Energy Consumption Tracking - NACH dem Lesen der Register
            _LOGGER.debug("DEBUG-001: Starting energy consumption tracking")
            await self._track_energy_consumption(data)
            _LOGGER.debug("DEBUG-002: Energy consumption tracking completed")

            _LOGGER.debug("PRODUCTION: Data update completed successfully (coordinator_id=%s)", id(self))
            return data

        except Exception as ex:
            _LOGGER.error("DEBUG-ERROR: Error updating data: %s", ex)
            import traceback
            _LOGGER.error("DEBUG-ERROR: Traceback: %s", traceback.format_exc())
            if (
                self.client is not None
                and hasattr(self.client, "close")
                and callable(getattr(self.client, "close", None))
            ):
                try:
                    self.client.close()
                except Exception as close_ex:
                    _LOGGER.debug("Error closing client connection: %s", close_ex)
                finally:
                    self.client = None
            raise UpdateFailed(f"Error fetching Lambda data: {ex}")
        finally:
            self._full_update_running = False

    def _is_energy_unit(self, unit: str) -> bool:
        """Check if unit is a valid energy unit."""
        if not unit:
            return True  # Leer ist OK (kWh)
        
        unit_lower = unit.lower().strip()
        valid_units = ["wh", "wattstunden", "kwh", "kilowattstunden", "mwh", "megawattstunden"]
        return unit_lower in valid_units

    def _convert_energy_to_kwh_cached(self, value: float, unit: str) -> float:
        """Optimized energy conversion using cached unit."""
        if not unit:  # Keine Einheit = kWh (Standard)
            return value
        
        if unit == "kWh":
            return value
        elif unit == "Wh":
            return value / 1000.0
        elif unit == "MWh":
            return value * 1000.0
        else:
            # Sollte nie erreicht werden, da ungültige Einheiten abgefangen werden
            _LOGGER.error("Unexpected unit '%s' in conversion function", unit)
            return value

    async def _track_energy_consumption(self, data):
        """Track energy consumption by operating mode."""
        _LOGGER.debug("DEBUG-004: Entering _track_energy_consumption")
        try:
            # Get number of heat pumps from config entry
            num_hps = self.entry.data.get("num_hps", 1)
            _LOGGER.debug("DEBUG-005: Number of heat pumps: %s", num_hps)
            
            # Get current operating states for all heat pumps
            current_states = {}
            for hp_idx in range(1, num_hps + 1):
                state_key = f"hp{hp_idx}_operating_state"
                _LOGGER.debug("DEBUG-006A: Available keys in data: %s", list(data.keys()))
                _LOGGER.debug("DEBUG-006B: Looking for key: %s", state_key)
                if state_key in data:
                    current_states[hp_idx] = data[state_key]
                    _LOGGER.debug("DEBUG-006C: Found %s = %s", state_key, data[state_key])
                else:
                    current_states[hp_idx] = 0  # Default to 0 if not available
                    _LOGGER.debug("DEBUG-006D: Key %s not found, using default 0", state_key)
                _LOGGER.debug("DEBUG-006: HP%s operating state: %s", hp_idx, current_states[hp_idx])

            # Track energy consumption for each heat pump
            for hp_idx in range(1, num_hps + 1):
                _LOGGER.debug("DEBUG-007: Tracking energy consumption for HP%s", hp_idx)
                await self._track_hp_energy_consumption(hp_idx, current_states[hp_idx], data)
                _LOGGER.debug("DEBUG-008: Completed tracking energy consumption for HP%s", hp_idx)

            _LOGGER.debug("DEBUG-009: Completed _track_energy_consumption")

        except Exception as ex:
            _LOGGER.error("DEBUG-ERROR: Error tracking energy consumption: %s", ex)
            import traceback
            _LOGGER.error("DEBUG-ERROR: Traceback in _track_energy_consumption: %s", traceback.format_exc())

    async def _track_hp_energy_consumption(self, hp_idx, current_state, data):
        """Track energy consumption for a specific heat pump (both electrical and thermal)."""
        _LOGGER.debug("DEBUG-010: Entering _track_hp_energy_consumption for HP%s", hp_idx)
        try:
            # --- ELECTRICAL ENERGY (existing logic) ---
            await self._track_hp_energy_type_consumption(
                hp_idx, current_state, data,
                sensor_type="electrical",
                default_sensor_id_template="sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated",
                unit_check_fn=self._is_energy_unit,
                convert_to_kwh_fn=self._convert_energy_to_kwh_cached,
                last_reading_dict=self._last_energy_reading,
                first_value_seen_dict=self._energy_first_value_seen,
                increment_fn=self._increment_energy_consumption
            )

            # --- THERMAL ENERGY (new logic) ---
            await self._track_hp_energy_type_consumption(
                hp_idx, current_state, data,
                sensor_type="thermal",
                default_sensor_id_template="sensor.{name_prefix}_hp{hp_idx}_compressor_thermal_energy_output_accumulated",
                unit_check_fn=self._is_energy_unit,  # Assume same unit check for now
                convert_to_kwh_fn=self._convert_energy_to_kwh_cached,  # Assume same conversion for now
                last_reading_dict=getattr(self, '_last_thermal_energy_reading', {}),
                first_value_seen_dict=getattr(self, '_thermal_energy_first_value_seen', {}),
                increment_fn=getattr(self, '_increment_thermal_energy_consumption', None)
            )
        except Exception as ex:
            _LOGGER.error("Error tracking energy consumption for HP%s: %s", hp_idx, ex)

    async def _track_hp_energy_type_consumption(
        self, hp_idx, current_state, data, sensor_type, default_sensor_id_template,
        unit_check_fn, convert_to_kwh_fn, last_reading_dict, first_value_seen_dict, increment_fn
    ):
        """Generic tracking for electrical or thermal energy sensors."""
        # Get sensor configuration for this heat pump (optional)
        hp_key = f"hp{hp_idx}"
        sensor_config = self._energy_sensor_configs.get(hp_key, {})
        sensor_entity_id = sensor_config.get(f"{sensor_type}_sensor_entity_id")
        if not sensor_entity_id and sensor_type == "electrical":
            # Fallback: generischer sensor_entity_id aus Config (nur für elektrisch)
            sensor_entity_id = sensor_config.get("sensor_entity_id")
        if not sensor_entity_id:
            # Entity-IDs der Sensoren werden in sensor.py mit kleingeschriebenem name_prefix erzeugt
            name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"
            sensor_entity_id = default_sensor_id_template.format(name_prefix=name_prefix, hp_idx=hp_idx)
            _LOGGER.debug(
                "[Energy] HP%s %s: Verwende Modbus-Sensor %s",
                hp_idx, sensor_type, sensor_entity_id,
            )
        # Get current energy reading from the configured sensor
        current_energy_state = self.hass.states.get(sensor_entity_id)
        if not current_energy_state or current_energy_state.state in ["unknown", "unavailable"]:
            _LOGGER.debug(
                "[Energy] HP%s %s: Sensor %s nicht verfügbar (state=%s)",
                hp_idx, sensor_type, sensor_entity_id,
                current_energy_state.state if current_energy_state else "None",
            )
            return
        try:
            current_energy = float(current_energy_state.state)
        except (ValueError, TypeError):
            return
        unit = current_energy_state.attributes.get("unit_of_measurement", "")
        cache_key = f"{sensor_type}_hp{hp_idx}"
        if not hasattr(self, '_energy_unit_cache_all'):
            self._energy_unit_cache_all = {}
        if cache_key not in self._energy_unit_cache_all:
            if not unit_check_fn(unit):
                self._energy_unit_cache_all[cache_key] = None
                return
            else:
                self._energy_unit_cache_all[cache_key] = unit
        elif self._energy_unit_cache_all[cache_key] != unit:
            if not unit_check_fn(unit):
                self._energy_unit_cache_all[cache_key] = None
                return
            else:
                self._energy_unit_cache_all[cache_key] = unit
        if self._energy_unit_cache_all[cache_key] is None:
            return
        cached_unit = self._energy_unit_cache_all[cache_key]
        original_energy = current_energy
        current_energy_kwh = convert_to_kwh_fn(current_energy, cached_unit)
        # Get last energy reading for this heat pump
        last_energy = last_reading_dict.get(f"hp{hp_idx}", None)
        first_value_seen = first_value_seen_dict.get(f"hp{hp_idx}", False)
        if current_energy_kwh == 0.0:
            first_value_seen_dict[f"hp{hp_idx}"] = False
            return
        if not first_value_seen or last_energy is None:
            last_reading_dict[f"hp{hp_idx}"] = current_energy_kwh
            first_value_seen_dict[f"hp{hp_idx}"] = True
            await self._persist_counters()
            return
        from .utils import calculate_energy_delta
        if current_energy_kwh < last_energy:
            first_value_seen_dict[f"hp{hp_idx}"] = False
            last_reading_dict[f"hp{hp_idx}"] = None
            await self._persist_counters()
            return
        energy_delta = calculate_energy_delta(current_energy_kwh, last_energy, max_delta=100.0)
        if energy_delta < 0:
            return
        last_reading_dict[f"hp{hp_idx}"] = current_energy_kwh
        # Get last operating state for this heat pump
        last_state = self._last_operating_state.get(str(hp_idx), 0)
        mode_mapping = {
            0: "stby", 1: "heating", 2: "hot_water", 3: "cooling", 4: "stby", 5: "defrost",
        }
        if current_state in mode_mapping:
            mode = mode_mapping[current_state]
        else:
            mode = "stby"
        if current_state != last_state:
            if increment_fn:
                _LOGGER.info(
                    "[Energy] HP%s Modus %s: Inkrement %.4f kWh (Modbus: %.2f -> %.2f kWh)",
                    hp_idx, mode, energy_delta, last_energy, current_energy_kwh,
                )
                await increment_fn(hp_idx, mode, energy_delta)
        else:
            if mode == "stby" or energy_delta > 0:
                if increment_fn:
                    _LOGGER.debug(
                        "[Energy] HP%s Modus %s: Inkrement %.4f kWh (Modbus: %.2f -> %.2f kWh)",
                        hp_idx, mode, energy_delta, last_energy, current_energy_kwh,
                    )
                    await increment_fn(hp_idx, mode, energy_delta)
        self._last_operating_state[str(hp_idx)] = current_state

    async def _increment_energy_consumption(self, hp_idx, mode, energy_delta):
        """Increment energy consumption for a specific mode and heat pump."""
        try:
            from .utils import increment_energy_consumption_counter
            
            # Get energy offsets for this heat pump
            hp_key = f"hp{hp_idx}"
            _LOGGER.debug("DEBUG-014: Getting energy offsets for %s", hp_key)
            energy_offsets = self._energy_offsets.get(hp_key, {})
            _LOGGER.debug("DEBUG-015: Energy offsets for %s: %s", hp_key, energy_offsets)
            _LOGGER.debug("DEBUG-016: Type of energy_offsets: %s", type(energy_offsets))
            
            # Get name prefix from entry data
            name_prefix = normalize_name_prefix(self.entry.data.get("name", "")) or "eu08l"

            # Increment both total and daily counters
            await increment_energy_consumption_counter(
                hass=self.hass,
                mode=mode,
                hp_index=hp_idx,
                energy_delta=energy_delta,
                name_prefix=name_prefix,
                use_legacy_modbus_names=self._use_legacy_names,
                energy_offsets=energy_offsets,
            )

        except Exception as ex:
            _LOGGER.error("Error incrementing energy consumption for HP%s %s: %s", hp_idx, mode, ex)

    def _on_ha_started(self, event):
        """Handle Home Assistant started event."""
        self._ha_started = True
        _LOGGER.debug(
            "Home Assistant started - enabling room temperature and PV surplus updates"
        )
        self._start_fast_poll()

    def _start_fast_poll(self) -> None:
        """Register the fast polling timer for edge detection."""
        if self._unsub_fast_poll is not None:
            return
        fast_interval = self.entry.options.get("fast_update_interval", DEFAULT_FAST_UPDATE_INTERVAL)
        _LOGGER.info(
            "Starting fast edge-detection poll at %ds interval", fast_interval
        )
        self._unsub_fast_poll = async_track_time_interval(
            self.hass,
            self._async_fast_update,
            timedelta(seconds=fast_interval),
        )

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        _LOGGER.debug("Shutting down Lambda coordinator")
        try:
            # Stop periodic updates by unsubscribing from refresh callback
            # This prevents new refresh tasks from being created
            if hasattr(self, "_unsub_refresh") and self._unsub_refresh:
                try:
                    self._unsub_refresh()
                    self._unsub_refresh = None
                    _LOGGER.debug("Stopped periodic refresh updates")
                except Exception as unsub_ex:
                    _LOGGER.debug("Error unsubscribing from refresh: %s", unsub_ex)

            if self._unsub_fast_poll is not None:
                try:
                    self._unsub_fast_poll()
                    self._unsub_fast_poll = None
                    _LOGGER.debug("Stopped fast edge-detection polling")
                except Exception as unsub_ex:
                    _LOGGER.debug("Error unsubscribing fast poll: %s", unsub_ex)
            
            # Close Modbus connection immediately to cancel any pending operations
            # This should cause any running Modbus operations to fail gracefully
            if self.client is not None:
                try:
                    # Try to close gracefully first
                    if hasattr(self.client, "close") and callable(getattr(self.client, "close", None)):
                        self.client.close()
                        _LOGGER.debug("Closed Modbus client connection")
                except Exception as close_ex:
                    _LOGGER.debug("Error closing client connection: %s", close_ex)
                finally:
                    self.client = None
            
            # Clean up entity registry listener
            if hasattr(self, "_registry_listener") and self._registry_listener:
                try:
                    self._registry_listener()
                    self._registry_listener = None
                    _LOGGER.debug("Cleaned up entity registry listener")
                except Exception as listener_ex:
                    _LOGGER.debug("Error cleaning up registry listener: %s", listener_ex)
                    
        except Exception as ex:
            _LOGGER.error("Error during coordinator shutdown: %s", ex)

    async def _load_sensor_overrides(self) -> dict[str, str]:
        """Load sensor name overrides from YAML config file."""
        config_path = os.path.join(self._config_dir, "lambda_wp_config.yaml")
        if not os.path.exists(config_path):
            return {}
        try:

            def _read_config():
                with open(config_path) as f:
                    content = f.read()
                    config = yaml.safe_load(content) or {}
                    overrides = {}
                    for sensor in config.get("sensors_names_override", []):
                        if "id" in sensor and "override_name" in sensor:
                            overrides[sensor["id"]] = sensor["override_name"]
                    return overrides

            return await self.hass.async_add_executor_job(_read_config)
        except Exception as e:
            _LOGGER.error("Fehler beim Laden der Sensor-Namen-Überschreibungen: %s", e)
            return {}



