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
from .const import (
    SENSOR_TYPES,
    HP_SENSOR_TEMPLATES,
    BOIL_SENSOR_TEMPLATES,
    BUFF_SENSOR_TEMPLATES,
    SOL_SENSOR_TEMPLATES,
    HC_SENSOR_TEMPLATES,
    DEFAULT_UPDATE_INTERVAL,
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
)
from .modbus_utils import async_read_holding_registers, combine_int32_registers
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
        self._heating_cycles = {}
        self._heating_energy = {}
        self._last_energy_update = {}
        self._cycling_offsets = {}
        self._energy_offsets = {}
        
        # Energy Consumption Tracking
        self._last_energy_reading = {}  # {hp_index: last_kwh_value}
        self._energy_consumption = {}   # {hp_index: {mode: {period: value}}}
        self._energy_sensor_configs = {}  # Sensor-Konfigurationen aus Config (optional)
        self._sensor_ids = {}  # {hp_index: sensor_entity_id} für Sensor-Wechsel-Erkennung
        self._energy_unit_cache = {}  # {hp_index: unit_string} - Memory-only cache for performance
        self._energy_first_value_seen = {}  # {hp_index: bool} - In-Memory Flag für Zero-Value Protection
        self._sensor_detection_executed = False  # Flag to prevent multiple sensor detection runs
        
        self._use_legacy_names = entry.data.get("use_legacy_modbus_names", True)
        self._persist_file = os.path.join(
            self._config_path, "cycle_energy_persist.json"
        )

        # Entity-based polling control - simplified approach
        self._enabled_addresses = set()  # Aktuell aktivierte Register-Adressen
        self._entity_addresses = {}  # Mapping entity_id -> address from sensors
        
        # Int32 Endianness Support (Issue #22)
        self._int32_byte_order = "big"  # Default value
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

        # Persist File I/O Optimierung
        self._persist_dirty = False  # Dirty-Flag für Änderungen
        self._persist_last_write = 0  # Timestamp des letzten Schreibens
        self._persist_debounce_seconds = 30  # Max 1x pro 30 Sekunden schreiben
        
        # Globale Register-Deduplizierung für bessere Performance
        self._global_register_cache = {}  # Cache für bereits gelesene Register pro Update-Zyklus
        self._global_register_requests = {}  # Sammle alle Register-Requests vor dem Lesen

        # self._load_offsets_and_persisted() ENTFERNT!

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
        
        _LOGGER.debug(f"Reading {len(self._global_register_requests)} unique registers globally")
        
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
        """Normalisiere last_operating_states - konvertiere alle Schlüssel zu Strings."""
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
                    _LOGGER.warning(f"Persist file {self._persist_file} is empty, using defaults")
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
                        "energy_consumption", "last_energy_readings", "energy_offsets"
                    ]
                    for field in required_fields:
                        if field not in data:
                            data[field] = {}
                            _LOGGER.info(f"Added missing field {field} to repaired JSON")
                    
                    # sensor_ids nur hinzufügen wenn komplett fehlt, nicht wenn leer
                    if "sensor_ids" not in data:
                        data["sensor_ids"] = {}
                        _LOGGER.info("Added missing sensor_ids field to repaired JSON")
                    
                return data
                
            except json.JSONDecodeError as e:
                _LOGGER.error(f"JSON decode error in {self._persist_file}: {e}")
                _LOGGER.warning(f"Attempting to repair corrupted JSON file")
                
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
                        "energy_consumption", "last_energy_readings", "energy_offsets", "sensor_ids"
                    ]
                    for field in required_fields:
                        if field not in data:
                            data[field] = {}
                    
                    # Speichere reparierte Version
                    with open(self._persist_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    _LOGGER.info(f"Successfully repaired corrupted JSON file")
                    return data
                    
                except Exception as repair_error:
                    _LOGGER.error(f"Failed to repair JSON file: {repair_error}")
                    _LOGGER.warning(f"Deleting corrupted persist file and starting fresh")
                    try:
                        os.remove(self._persist_file)
                    except Exception:
                        pass  # Ignore if file can't be deleted
                    return {}
            except Exception as e:
                _LOGGER.error(f"Error reading persist file {self._persist_file}: {e}")
                return {}
        
        return await self.hass.async_add_executor_job(_repair_json)

    async def _persist_counters(self):
        """Persist counter data and state information to file using optimized I/O with debouncing."""
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
        normalized_operating_states = self._normalize_operating_states(
            getattr(self, "_last_operating_state", {})
        )
        
        # Prüfe ob sensor_ids in der aktuellen Datei existieren und verwende sie falls self._sensor_ids leer ist
        sensor_ids_to_save = getattr(self, "_sensor_ids", {})
        if not sensor_ids_to_save and os.path.exists(self._persist_file):
            
            def _read_existing_sensor_ids():
                try:
                    with open(self._persist_file) as f:
                        existing_data = json.loads(f.read())
                        existing_sensor_ids = existing_data.get("sensor_ids", {})
                        if existing_sensor_ids:
                            _LOGGER.debug(f"Using existing sensor_ids from file: {existing_sensor_ids}")
                            return existing_sensor_ids
                except Exception:
                    pass  # Ignore errors when reading existing file
                return {}
            
            sensor_ids_to_save = await self.hass.async_add_executor_job(_read_existing_sensor_ids)
        
        data = {
            "heating_cycles": self._heating_cycles,
            "heating_energy": self._heating_energy,
            "last_operating_states": normalized_operating_states,
            "energy_consumption": self._energy_consumption,
            "last_energy_readings": self._last_energy_reading,
            "energy_offsets": self._energy_offsets,
            "sensor_ids": sensor_ids_to_save,
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

    def mark_initialization_complete(self):
        """Markiere die Initialisierung als abgeschlossen - ermöglicht Flankenerkennung."""
        if not self._initialization_complete:
            self._initialization_complete = True
            _LOGGER.info("Coordinator-Initialisierung abgeschlossen - Flankenerkennung aktiviert")

    async def _load_offsets_and_persisted(self):
        # Lade Offsets aus lambda_wp_config.yaml über das zentrale Config-System
        from .utils import load_lambda_config
        
        try:
            config = await load_lambda_config(self.hass)
            _LOGGER.info(f"Loaded config keys: {list(config.keys())}")
            self._cycling_offsets = config.get("cycling_offsets", {})
            self._energy_offsets = config.get("energy_consumption_offsets", {})
            # Lade und validiere Energy Sensor Konfigurationen
            raw_energy_sensor_configs = config.get("energy_consumption_sensors", {})
            
            # Validiere externe Sensoren
            from .utils import validate_external_sensors
            self._energy_sensor_configs = validate_external_sensors(self.hass, raw_energy_sensor_configs)
            
            _LOGGER.info(f"Loaded energy sensor configs: {self._energy_sensor_configs}")
            
            # Info-Message: Anzeige der verwendeten Quellsensoren für Verbrauchswerte
            if self._energy_sensor_configs:
                _LOGGER.info("=== ENERGY CONSUMPTION SENSORS ===")
                for hp_key, sensor_config in self._energy_sensor_configs.items():
                    sensor_id = sensor_config.get("sensor_entity_id")
                    _LOGGER.info(f"Energy consumption tracking for {hp_key.upper()}: using custom sensor '{sensor_id}'")
            else:
                _LOGGER.info("=== ENERGY CONSUMPTION SENSORS ===")
                _LOGGER.info("Energy consumption tracking: using default internal Modbus sensors")
                _LOGGER.info("(Configure custom sensors in lambda_wp_config.yaml if needed)")
        except Exception as e:
            _LOGGER.error(f"Error loading config: {e}")
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
        
        # Lade persistierte Energy Consumption Daten
        self._energy_consumption = data.get("energy_consumption", {})
        self._last_energy_reading = data.get("last_energy_readings", {})
        self._sensor_ids = data.get("sensor_ids", {})
        # Energy Offsets werden bereits aus der Config geladen
        
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Geladene sensor_ids: {self._sensor_ids}")
        
        _LOGGER.info(
            f"Restored last_operating_state: {self._last_operating_state}"
        )

        # Sensor-Wechsel-Erkennung für Energy Consumption Sensoren (NACH dem Laden der persistierten Daten)
        # Führe die Erkennung bei jedem Start aus, um Sensor-Wechsel zu erkennen
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung für {len(self._energy_sensor_configs)} konfigurierte Sensoren")
        await self._detect_and_handle_sensor_changes()

    async def _detect_and_handle_sensor_changes(self):
        """Erkenne Sensor-Wechsel und behandle sie entsprechend."""
        _LOGGER.info("SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung")
        
        try:
            from .utils import detect_sensor_change, get_stored_sensor_id, store_sensor_id
            
            # Erstelle persist_data dict für die Hilfsfunktionen
            persist_data = {"sensor_ids": self._sensor_ids}
            
            # Prüfe alle Wärmepumpen, die in _sensor_ids gespeichert sind (auch wenn keine Custom-Sensoren konfiguriert sind)
            all_hp_keys = set()
            
            # Füge Custom-Sensoren hinzu
            for hp_key in self._energy_sensor_configs.keys():
                all_hp_keys.add(hp_key)
            
            # Füge alle Wärmepumpen aus _sensor_ids hinzu (für Default-Sensor-Wechsel)
            for hp_key in self._sensor_ids.keys():
                all_hp_keys.add(hp_key)
            
            _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Prüfe {len(all_hp_keys)} Wärmepumpen: {sorted(all_hp_keys)}")
            
            for hp_key in all_hp_keys:
                # Extrahiere hp_idx aus hp_key (z.B. "hp1" -> 1)
                try:
                    hp_idx = int(hp_key.replace("hp", ""))
                except (ValueError, AttributeError):
                    _LOGGER.warning(f"SENSOR-CHANGE-DETECTION: Ungültiger hp_key: {hp_key}")
                    continue
                
                # Bestimme aktuellen Sensor (Custom oder Default)
                current_sensor_id = None
                
                # Prüfe zuerst Custom-Sensor
                if hp_key in self._energy_sensor_configs:
                    current_sensor_id = self._energy_sensor_configs[hp_key].get("sensor_entity_id")
                    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: {hp_key} - Custom-Sensor: {current_sensor_id}")
                
                # Falls kein Custom-Sensor, verwende Default-Sensor
                if not current_sensor_id:
                    name_prefix = self.entry.data.get("name", "eu08l")
                    current_sensor_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
                    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: {hp_key} - Default-Sensor: {current_sensor_id}")
                
                _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Prüfe {hp_key} - aktueller Sensor: {current_sensor_id}")
                
                # Hole gespeicherte Sensor-ID
                stored_sensor_id = get_stored_sensor_id(persist_data, hp_idx)
                
                # Prüfe auf Sensor-Wechsel
                if detect_sensor_change(stored_sensor_id, current_sensor_id):
                    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Sensor-Wechsel erkannt für {hp_key}: {stored_sensor_id} -> {current_sensor_id}")
                    await self._handle_sensor_change(hp_idx, current_sensor_id)
                
                # Speichere neue Sensor-ID für nächsten Vergleich
                store_sensor_id(persist_data, hp_idx, current_sensor_id)
                self._sensor_ids = persist_data["sensor_ids"]
                
                _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Sensor-ID für {hp_key} aktualisiert: {current_sensor_id}")
            
            # Speichere alle Änderungen in der JSON-Datei
            if self._sensor_ids:
                _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Speichere sensor_ids in JSON: {self._sensor_ids}")
                await self._persist_counters()
                _LOGGER.info("SENSOR-CHANGE-DETECTION: sensor_ids erfolgreich gespeichert")
            
            _LOGGER.info("SENSOR-CHANGE-DETECTION: Sensor-Wechsel-Erkennung abgeschlossen")
            
        except Exception as e:
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Fehler bei Sensor-Wechsel-Erkennung: {e}")
            import traceback
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Traceback: {traceback.format_exc()}")

    async def _handle_sensor_change(self, hp_idx: int, new_sensor_id: str):
        """Behandle Sensor-Wechsel mit intelligenter DB-Wert-Nutzung."""
        _LOGGER.info(f"SENSOR-CHANGE: === SENSOR-WECHSEL ERKANNT HP{hp_idx} ===")
        _LOGGER.info(f"SENSOR-CHANGE: Neuer Sensor: {new_sensor_id}")
        
        hp_key = f"hp{hp_idx}"
        
        # Prüfe ob es ein Default-Sensor ist (interner Modbus-Sensor)
        name_prefix = self.entry.data.get("name", "eu08l")
        default_sensor_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
        
        is_default_sensor = (new_sensor_id == default_sensor_id)
        _LOGGER.info(f"SENSOR-CHANGE: Erwarteter Default-Sensor: {default_sensor_id}")
        _LOGGER.info(f"SENSOR-CHANGE: Ist Default-Sensor: {is_default_sensor}")
        
        if is_default_sensor:
            # SCHRITT 3: Wechsel zu Default-Sensor (interner Modbus)
            _LOGGER.info(f"SENSOR-CHANGE: → SCHRITT 3: Wechsel zu Default-Sensor (interner Modbus)")
            _LOGGER.info(f"SENSOR-CHANGE: → Lese DB-Wert vom Default-Sensor...")
            
            # Lese letzten DB-Wert vom Default-Sensor
            db_state = self.hass.states.get(new_sensor_id)
            _LOGGER.info(f"SENSOR-CHANGE: → DB-State: {db_state.state if db_state else 'None'}")
            
            if db_state and db_state.state not in ("unknown", "unavailable", "None"):
                try:
                    db_value = float(db_state.state)
                    _LOGGER.info(f"SENSOR-CHANGE: → DB-Wert konvertiert: {db_value:.2f} kWh")
                    
                    if db_value > 0:
                        _LOGGER.info(f"SENSOR-CHANGE: → ✅ DB-Wert > 0: {db_value:.2f} kWh")
                        _LOGGER.info(f"SENSOR-CHANGE: → ✅ Setze als Referenz für sofortige Delta-Berechnung")
                        _LOGGER.info(f"SENSOR-CHANGE: → ✅ Nächster Messwert wird mit diesem DB-Wert verglichen")
                        
                        # Setze DB-Wert als last_energy
                        self._last_energy_reading[hp_key] = db_value
                        self._energy_first_value_seen[hp_key] = True
                        
                        await self._persist_counters()
                        _LOGGER.info(f"SENSOR-CHANGE: → ✅ Referenzwert gesetzt, warte auf ersten Messwert")
                        _LOGGER.info(f"SENSOR-CHANGE: === SENSOR-WECHSEL ABGESCHLOSSEN: DB-REFERENZ GESETZT ===")
                        return
                        
                    else:
                        # DB-Wert ist 0
                        _LOGGER.info(f"SENSOR-CHANGE: → ❌ DB-Wert = 0, keine Historie verfügbar")
                        _LOGGER.info(f"SENSOR-CHANGE: → ❌ Starte Zero-Value Protection")
                        
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(f"SENSOR-CHANGE: → ❌ Fehler beim Konvertieren des DB-Werts: {e}")
                    _LOGGER.info(f"SENSOR-CHANGE: → ❌ Starte Zero-Value Protection")
            else:
                _LOGGER.info(f"SENSOR-CHANGE: → ❌ Kein DB-Wert verfügbar (State: {db_state.state if db_state else 'None'})")
                _LOGGER.info(f"SENSOR-CHANGE: → ❌ Starte Zero-Value Protection")
        
        else:
            # SCHRITT 4: Wechsel zu externem/Custom Sensor
            _LOGGER.info(f"SENSOR-CHANGE: → SCHRITT 4: Wechsel zu externem/Custom Sensor")
            _LOGGER.info(f"SENSOR-CHANGE: → ❌ Keine DB-Historie verfügbar für externe Sensoren")
            _LOGGER.info(f"SENSOR-CHANGE: → ❌ Starte Zero-Value Protection")
        
        # Fallback: Zero-Value Protection
        _LOGGER.info(f"SENSOR-CHANGE: → 🔄 AKTIVIERE ZERO-VALUE PROTECTION")
        _LOGGER.info(f"SENSOR-CHANGE: → 🔄 Warte auf 2 aufeinanderfolgende Werte > 0")
        _LOGGER.info(f"SENSOR-CHANGE: → 🔄 Erster Wert wird gespeichert, aber kein Delta berechnet")
        _LOGGER.info(f"SENSOR-CHANGE: → 🔄 Ab zweitem Wert wird Delta berechnet")
        
        self._last_energy_reading[hp_key] = None
        self._energy_first_value_seen[hp_key] = False
        await self._persist_counters()
        _LOGGER.info(f"SENSOR-CHANGE: === SENSOR-WECHSEL ABGESCHLOSSEN: ZERO-VALUE PROTECTION AKTIV ===")


    def _generate_entity_id(self, sensor_type, idx):
        if self._use_legacy_names:
            return f"sensor.hp{idx + 1}_{sensor_type}"
        else:
            return f"sensor.eu08l_hp{idx + 1}_{sensor_type}"

    async def async_init(self):
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

    async def _read_registers_batch(self, address_list, sensor_mapping):
        """Read multiple registers in robust, type-safe batches."""
        data = {}

        # Globale Deduplizierung - verhindere mehrfaches Lesen der gleichen Register über alle Module
        unique_addresses = {}
        for address, sensor_info in address_list.items():
            # Prüfe globalen Cache zuerst
            if address in self._global_register_cache:
                # Verwende gecachten Wert
                sensor_id = sensor_mapping.get(address, f"addr_{address}")
                data[sensor_id] = self._global_register_cache[address]
                _LOGGER.debug(f"Using cached value for register {address}")
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
                    _LOGGER.debug(f"Using individual reads for {start_addr}-{start_addr + count - 1} (previous failures)")
                    for addr in batch:
                        await self._read_single_register(
                            addr, unique_addresses[addr], sensor_mapping, data
                        )
                    continue

                # PrÃƒÂ¼fe ob Register in der Individual-Read-Liste stehen
                if any(addr in INDIVIDUAL_READ_REGISTERS for addr in batch):
                    _LOGGER.debug(f"Using individual reads for {start_addr}-{start_addr + count - 1} (configured individual read)")
                    for addr in batch:
                        await self._read_single_register(
                            addr, unique_addresses[addr], sensor_mapping, data
                        )
                    continue

                _LOGGER.debug(f"Reading batch: start={start_addr}, count={count}")
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
                        _LOGGER.warning(
                            f"Batch read failed for {start_addr}-{start_addr + count - 1} (attempt {self._batch_failures[batch_key]}/{self._max_batch_failures})"
                        )
                    else:
                        _LOGGER.info(
                            f"Switching to individual reads for {start_addr}-{start_addr + count - 1} after {self._max_batch_failures} failures"
                        )
                        self._individual_read_addresses.add(batch_key)
                    
                    # Fallback zu Individual-Reads
                    for addr in batch:
                        await self._read_single_register(
                            addr, address_list[addr], sensor_mapping, data
                        )
                    continue
                
                # Erfolgreicher Batch-Read - Reset Fehlerzähler
                if batch_key in self._batch_failures:
                    del self._batch_failures[batch_key]
                if batch_key in self._individual_read_addresses:
                    self._individual_read_addresses.remove(batch_key)
                    _LOGGER.info(f"Batch reads restored for {start_addr}-{start_addr + count - 1}")

                # Process batch results
                for i, addr in enumerate(batch):
                    sensor_info = address_list[addr]
                    sensor_id = sensor_mapping[addr]
                    try:
                        if sensor_info.get("data_type") == "int32":
                            # Should not happen in batch, but safety check
                            if i + 1 < len(result.registers):
                                value = (result.registers[i] << 16) | result.registers[
                                    i + 1
                                ]
                                value = to_signed_32bit(value)
                            else:
                                continue
                        else:
                            value = result.registers[i]
                            if sensor_info.get("data_type") == "int16":
                                value = to_signed_16bit(value)
                        if "scale" in sensor_info:
                            value = value * sensor_info["scale"]
                        data[sensor_id] = value
                        
                        # Cache den Wert im globalen Cache für andere Module
                        self._global_register_cache[addr] = value
                        _LOGGER.debug(f"Cached register {addr} = {value} (batch)")
                    except Exception as ex:
                        _LOGGER.debug(
                            f"Error processing register {addr} in batch: {ex}"
                        )
            except Exception as ex:
                _LOGGER.warning(
                    f"Error reading batch {batch[0]}-{batch[-1]}: {ex}, falling back to individual reads"
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
                _LOGGER.debug(f"Error reading register {address}: {result}")
                return

            if count == 2:
                value = combine_int32_registers(result.registers, self._int32_byte_order)
                if sensor_info.get("data_type") == "int32":
                    value = to_signed_32bit(value)
            else:
                value = result.registers[0]
                if sensor_info.get("data_type") == "int16":
                    value = to_signed_16bit(value)

            if "scale" in sensor_info:
                value = value * sensor_info["scale"]

            data[sensor_id] = value
            
            # Cache den Wert im globalen Cache für andere Module
            self._global_register_cache[address] = value
            _LOGGER.debug(f"Cached register {address} = {value}")

        except Exception as ex:
            _LOGGER.debug(f"Error reading register {address}: {ex}")

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
                if not self.is_address_enabled_by_entity(address):
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
                        name_prefix = (
                            self.entry.data.get("name", "").lower().replace(" ", "")
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
            if entity_id and entity_id.startswith(
                f"sensor.{self.entry.data.get('name', '').lower().replace(' ', '')}_"
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

    async def _connect(self):
        """Connect to the Modbus device."""
        try:
            from pymodbus.client import AsyncModbusTcpClient

            if (
                self.client
                and hasattr(self.client, "connected")
                and self.client.connected
            ):
                return

            self.client = AsyncModbusTcpClient(
                host=self.host, port=self.port, timeout=10
            )

            if not await self.client.connect():
                msg = f"Failed to connect to {self.host}:{self.port}"
                raise UpdateFailed(msg)

            _LOGGER.debug("Connected to Lambda device at %s:%s", self.host, self.port)

        except Exception as e:
            _LOGGER.error("Connection to %s:%s failed: %s", self.host, self.port, e)
            self.client = None
            msg = f"Connection failed: {e}"
            raise UpdateFailed(msg) from e

    async def _is_connection_healthy(self) -> bool:
        """Check if the Modbus connection is healthy."""
        if not self.client:
            return False
        
        try:
            # Try a simple read to test connection health
            # Use register 0 (General Error Number) as a health check
            result = await asyncio.wait_for(
                self.client.read_holding_registers(0, count=1, slave=self.slave_id),
                timeout=2  # Reduziert von 5s auf 2s für schnelleren Health Check
            )
            return result is not None
        except Exception:
            return False

    async def _async_update_data(self):
        """Fetch data from Lambda device."""
        try:
            # Check if Home Assistant is shutting down
            if self.hass.is_stopping:
                _LOGGER.debug("Home Assistant is stopping, skipping data update")
                return self.data
            
            # Reset global register cache für neuen Update-Zyklus
            self._global_register_cache = {}
            self._global_register_requests = {}  # Sammle alle Register-Requests vor dem Lesen
            _LOGGER.debug("Reset global register cache for new update cycle")
            
            # Check connection health and reconnect if necessary
            if not self.client or not await self._is_connection_healthy():
                _LOGGER.debug("Connection unhealthy, reconnecting to %s:%s", self.host, self.port)
                await self._connect()

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
            interval = DEFAULT_UPDATE_INTERVAL / 3600.0  # Intervall in Stunden
            
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
            # Initialisiere _last_operating_state nur wenn nicht bereits aus Persistierung geladen
            if not hasattr(self, "_last_operating_state"):
                self._last_operating_state = {}

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
                            _LOGGER.debug(
                                "Error reading register %d: %s",
                                address,
                                result,
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_byte_order)
                            if sensor_info.get("data_type") == "int32":
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
                            _LOGGER.debug(
                                "Error reading register %d: %s",
                                address,
                                result,
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_byte_order)
                            if sensor_info.get("data_type") == "int32":
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
                            _LOGGER.debug(
                                "Error reading register %d: %s",
                                address,
                                result,
                            )
                            continue
                        if count == 2:
                            value = combine_int32_registers(result.registers, self._int32_byte_order)
                            if sensor_info.get("data_type") == "int32":
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
            _LOGGER.debug(f"Global register reading completed: {len(global_data)} values")

            # Flankenerkennung und Energieintegration NACH dem Lesen aller Register
            for hp_idx in range(1, num_hps + 1):
                op_state_val = data.get(f"hp{hp_idx}_operating_state")
                if op_state_val is None:
                    continue

                # Get last operating state
                last_op_state = self._last_operating_state.get(str(hp_idx), "UNBEKANNT")
                
                # Initialisierung beim ersten Update: Logge den aktuellen operating_state
                if last_op_state == "UNBEKANNT":
                    _LOGGER.info(
                        f"Initialisiere _last_operating_state für HP {hp_idx} mit operating_state {op_state_val}"
                    )
                
                # Info-Meldung bei Änderung
                if last_op_state != op_state_val:
                    _LOGGER.info(
                        "Wärmepumpe %d: operating_state geändert von %s auf %s",
                        hp_idx,
                        last_op_state,
                        op_state_val,
                    )
                # Speichere den alten Wert für die Flankenerkennung
                last_op_state = self._last_operating_state.get(str(hp_idx), "UNBEKANNT")
                
                for mode, mode_val in MODES.items():
                    cycling_key = f"{mode}_cycles"
                    energy_key = f"{mode}_energy"
                    if not hasattr(self, cycling_key):
                        setattr(self, cycling_key, {})
                    if not hasattr(self, energy_key):
                        setattr(self, energy_key, {})
                    cycles = getattr(self, cycling_key)
                    energy = getattr(self, energy_key)
                    
                    # Debug: Check energy structure
                    _LOGGER.debug(f"energy structure for {energy_key}: {energy}")
                    
                    # Ensure energy[hp_idx] is a number, not a dict
                    if hp_idx not in energy:
                        energy[hp_idx] = 0.0
                    elif isinstance(energy[hp_idx], dict):
                        _LOGGER.warning(f"energy[{hp_idx}] is a dict, converting to 0.0: {energy[hp_idx]}")
                        energy[hp_idx] = 0.0
                    
                    # Debug: Check energy structure before any operations
                    _LOGGER.debug(f"energy[{hp_idx}] before processing: {energy[hp_idx]} (type: {type(energy[hp_idx])})")
                    # Flanke: operating_state wechselt von etwas anderem auf mode_val
                    # ABER: Nur wenn Initialisierung abgeschlossen ist
                    _LOGGER.debug(f"FLANKENERKENNUNG DEBUG HP{hp_idx}: init_complete={self._initialization_complete}, last_op_state='{last_op_state}', mode_val='{mode_val}', op_state_val='{op_state_val}'")
                    
                    if (self._initialization_complete and 
                        last_op_state != "UNBEKANNT" and
                        last_op_state != mode_val and 
                        op_state_val == mode_val):
                        
                        
                        # Prüfe, ob die Cycling-Entities bereits registriert sind
                        cycling_entities_ready = False
                        try:
                            # Prüfe, ob die Cycling-Entities in hass.data verfügbar sind
                            if (
                                "lambda_heat_pumps" in self.hass.data
                                and self.entry.entry_id
                                in self.hass.data["lambda_heat_pumps"]
                                and "cycling_entities"
                                in self.hass.data["lambda_heat_pumps"][
                                    self.entry.entry_id
                                ]
                            ):
                                cycling_entities_ready = True
                        except Exception:
                            pass

                        if cycling_entities_ready:
                            # Zentrale Funktion für total-Zähler aufrufen
                            await increment_cycling_counter(
                                self.hass,
                                mode=mode,
                                hp_index=hp_idx,
                                name_prefix=self.entry.data.get("name", "eu08l"),
                                use_legacy_modbus_names=self._use_legacy_names,
                                cycling_offsets=self._cycling_offsets,
                            )
                            # Get current cycling count for logging
                            cycling_key = f"{mode}_cycles"
                            cycles = getattr(self, cycling_key)
                            old_count = cycles.get(hp_idx, 0)
                            
                            # Debug: Check old_count type
                            if not isinstance(old_count, (int, float)):
                                _LOGGER.error(f"cycles[{hp_idx}] is not a number: {type(old_count)} = {old_count}")
                                old_count = 0
                            
                            new_count = old_count + 1
                            cycles[hp_idx] = new_count
                            
                            _LOGGER.info(
                                f"🔄 FLANKENERKENNUNG: HP{hp_idx} {last_op_state} → {op_state_val} | Cycling {mode} erhöht: {old_count} → {new_count}"
                            )
                            _LOGGER.debug(
                                f"Flankenwechsel Details: HP{hp_idx} operating_state von '{last_op_state}' auf '{op_state_val}' geändert, {mode} Modus aktiviert"
                            )
                        else:
                            _LOGGER.debug(
                                "Wärmepumpe %d: %s Modus aktiviert "
                                "(Cycling-Entities noch nicht bereit)",
                                hp_idx,
                                mode,
                            )
                    elif not self._initialization_complete:
                        # Flankenerkennung während Initialisierung unterdrückt
                        _LOGGER.debug(
                            "Wärmepumpe %d: %s Modus erkannt, aber Flankenerkennung "
                            "während Initialisierung unterdrückt",
                            hp_idx,
                            mode,
                        )
                    else:
                        # Flankenerkennung aus anderen Gründen nicht ausgelöst
                        _LOGGER.debug(
                            f"FLANKENERKENNUNG NICHT AUSGELÖST HP{hp_idx}: init_complete={self._initialization_complete}, last_op_state='{last_op_state}', mode_val='{mode_val}', op_state_val='{op_state_val}'"
                        )
                    # Nur für Debug-Zwecke, nicht als Info-Log:
                    # _LOGGER.debug(
                    #     "HP %d, Modus %s: last_mode_state=%s, op_state_val=%s",
                    #     hp_idx, mode, last_mode_state, op_state_val
                    # )

                    # Energieintegration für aktiven Modus
                    power_info = HP_SENSOR_TEMPLATES.get("actual_heating_capacity")
                    if power_info:
                        power_val = data.get(f"hp{hp_idx}_actual_heating_capacity", 0.0)
                        if op_state_val == mode_val:
                            # energy[hp_idx] ist ein dict, nicht eine Zahl
                            if hp_idx not in energy:
                                energy[hp_idx] = 0.0
                            elif isinstance(energy[hp_idx], dict):
                                _LOGGER.warning(f"energy[{hp_idx}] is a dict, converting to 0.0: {energy[hp_idx]}")
                                energy[hp_idx] = 0.0
                            # Debug: Check types before addition
                            _LOGGER.debug(f"Before addition: energy[{hp_idx}] = {energy[hp_idx]} (type: {type(energy[hp_idx])}), power_val * interval = {power_val * interval} (type: {type(power_val * interval)})")
                            # Ensure energy[hp_idx] is a number before addition
                            if not isinstance(energy[hp_idx], (int, float)):
                                _LOGGER.error(f"energy[{hp_idx}] is not a number: {type(energy[hp_idx])} = {energy[hp_idx]}")
                                energy[hp_idx] = 0.0
                            energy[hp_idx] = energy[hp_idx] + (power_val * interval)
                    # Sensorwerte bereitstellen (inkl. Offset)
                    cycling_entity_id = self._generate_entity_id(
                        f"{mode}_cycling_daily", hp_idx - 1
                    )
                    energy_entity_id = self._generate_entity_id(
                        f"{mode}_energy_daily", hp_idx - 1
                    )
                    # Get cycling offset for this specific sensor (correct nested structure)
                    hp_cycling_offsets = self._cycling_offsets.get(f"hp{hp_idx}", {})
                    if isinstance(hp_cycling_offsets, dict):
                        cycling_offset = hp_cycling_offsets.get(f"{mode}_cycling_daily", 0)
                    else:
                        _LOGGER.warning(f"Invalid cycling offset structure for hp{hp_idx}: {hp_cycling_offsets}")
                        cycling_offset = 0
                    energy_offset = self._energy_offsets.get(f"hp{hp_idx}", {})
                    # Energy offset is a dict, we need to get the specific sensor offset
                    energy_sensor_offset = 0.0
                    if isinstance(energy_offset, dict):
                        energy_sensor_offset = energy_offset.get(f"{mode}_energy_daily", 0.0)
                    else:
                        _LOGGER.warning(f"Invalid energy offset structure for hp{hp_idx}: {energy_offset}")
                    
                    data[cycling_entity_id] = cycles.get(hp_idx, 0) + cycling_offset
                    
                    # Debug: Check energy structure
                    energy_value = energy.get(hp_idx, 0.0)
                    if not isinstance(energy_value, (int, float)):
                        _LOGGER.error(f"energy[{hp_idx}] is not a number: {type(energy_value)} = {energy_value}")
                        energy_value = 0.0
                    
                    data[energy_entity_id] = energy_value + energy_sensor_offset
                
                # Aktualisiere _last_operating_state NACH der Flankenerkennung
                self._last_operating_state[str(hp_idx)] = op_state_val
            
            await self._persist_counters()
            
            # Setze Dirty-Flag wenn sich Werte geändert haben
            self._persist_dirty = True

            # Energy Consumption Tracking - NACH dem Lesen der Register
            _LOGGER.debug("DEBUG-001: Starting energy consumption tracking")
            await self._track_energy_consumption(data)
            _LOGGER.debug("DEBUG-002: Energy consumption tracking completed")

            _LOGGER.debug("DEBUG-003: Returning data from _async_update_data")
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
            _LOGGER.error(f"Unexpected unit '{unit}' in conversion function")
            return value

    async def _track_energy_consumption(self, data):
        """Track energy consumption by operating mode."""
        _LOGGER.debug("DEBUG-004: Entering _track_energy_consumption")
        try:
            # Get number of heat pumps from config entry
            num_hps = self.entry.data.get("num_hps", 1)
            _LOGGER.debug(f"DEBUG-005: Number of heat pumps: {num_hps}")
            
            # Get current operating states for all heat pumps
            current_states = {}
            for hp_idx in range(1, num_hps + 1):
                state_key = f"hp{hp_idx}_operating_state"
                _LOGGER.debug(f"DEBUG-006A: Available keys in data: {list(data.keys())}")
                _LOGGER.debug(f"DEBUG-006B: Looking for key: {state_key}")
                if state_key in data:
                    current_states[hp_idx] = data[state_key]
                    _LOGGER.debug(f"DEBUG-006C: Found {state_key} = {data[state_key]}")
                else:
                    current_states[hp_idx] = 0  # Default to 0 if not available
                    _LOGGER.debug(f"DEBUG-006D: Key {state_key} not found, using default 0")
                _LOGGER.debug(f"DEBUG-006: HP{hp_idx} operating state: {current_states[hp_idx]}")

            # Track energy consumption for each heat pump
            for hp_idx in range(1, num_hps + 1):
                _LOGGER.debug(f"DEBUG-007: Tracking energy consumption for HP{hp_idx}")
                await self._track_hp_energy_consumption(hp_idx, current_states[hp_idx], data)
                _LOGGER.debug(f"DEBUG-008: Completed tracking energy consumption for HP{hp_idx}")

            _LOGGER.debug("DEBUG-009: Completed _track_energy_consumption")

        except Exception as ex:
            _LOGGER.error("DEBUG-ERROR: Error tracking energy consumption: %s", ex)
            import traceback
            _LOGGER.error("DEBUG-ERROR: Traceback in _track_energy_consumption: %s", traceback.format_exc())

    async def _track_hp_energy_consumption(self, hp_idx, current_state, data):
        """Track energy consumption for a specific heat pump."""
        _LOGGER.debug(f"DEBUG-010: Entering _track_hp_energy_consumption for HP{hp_idx}")
        try:
            # Get sensor configuration for this heat pump (optional)
            hp_key = f"hp{hp_idx}"
            _LOGGER.debug(f"DEBUG-011: HP key: {hp_key}")
            sensor_config = self._energy_sensor_configs.get(hp_key, {})
            _LOGGER.debug(f"DEBUG-012: Sensor config: {sensor_config}")
            sensor_entity_id = sensor_config.get("sensor_entity_id")
            _LOGGER.debug(f"DEBUG-013: Sensor entity ID: {sensor_entity_id}")
            
            # If no custom sensor configured, use the default power consumption sensor
            if not sensor_entity_id:
                name_prefix = self.entry.data.get("name", "eu08l")
                sensor_entity_id = f"sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated"
                _LOGGER.info(f"INTERNAL-SENSOR: HP{hp_idx} - Verwende internen Modbus-Sensor '{sensor_entity_id}' zur Verbrauchsberechnung")
                _LOGGER.debug(f"Using default energy sensor for HP {hp_idx}: {sensor_entity_id}")
            else:
                _LOGGER.debug(f"Using custom energy sensor for HP {hp_idx}: {sensor_entity_id}")

            # Get current energy reading from the configured sensor
            current_energy_state = self.hass.states.get(sensor_entity_id)
            _LOGGER.debug(f"DEBUG-017: Energy sensor state: {current_energy_state.state if current_energy_state else 'None'}")
            if not current_energy_state or current_energy_state.state in ["unknown", "unavailable"]:
                # Template sensors might not be ready yet - this is normal during startup
                if current_energy_state and current_energy_state.state == "unknown":
                    _LOGGER.debug(f"Energy sensor {sensor_entity_id} not ready yet (state: unknown) - will retry on next update")
                else:
                    _LOGGER.warning(f"Energy sensor {sensor_entity_id} not available (state: {current_energy_state.state if current_energy_state else 'None'})")
                return

            try:
                current_energy = float(current_energy_state.state)
                _LOGGER.debug(f"DEBUG-018: Current energy value: {current_energy:.6f}")
            except (ValueError, TypeError):
                _LOGGER.warning(f"DEBUG-ERROR: Could not convert energy state to float: {current_energy_state.state}")
                return

            # Get unit from sensor attributes
            unit = current_energy_state.attributes.get("unit_of_measurement", "")
            
            # Cache unit in memory (auto-detection on first run or change)
            cache_key = f"hp{hp_idx}"
            if cache_key not in self._energy_unit_cache:
                # First time - validate and cache the unit
                if not self._is_energy_unit(unit):
                    _LOGGER.warning(f"Invalid energy unit '{unit}' detected for HP{hp_idx} - energy tracking disabled")
                    self._energy_unit_cache[cache_key] = None  # Mark as invalid
                    return  # ABBRUCH - keine Werteänderung
                else:
                    self._energy_unit_cache[cache_key] = unit
                    _LOGGER.info(f"Energy unit detected and cached for HP{hp_idx}: {unit or 'kWh (default)'}")
            elif self._energy_unit_cache[cache_key] != unit:
                # Unit changed - validate and update cache
                if not self._is_energy_unit(unit):
                    _LOGGER.warning(f"Energy unit changed to invalid '{unit}' for HP{hp_idx} - energy tracking disabled")
                    self._energy_unit_cache[cache_key] = None  # Mark as invalid
                    return  # ABBRUCH - keine Werteänderung
                else:
                    old_unit = self._energy_unit_cache[cache_key]
                    self._energy_unit_cache[cache_key] = unit
                    _LOGGER.warning(f"Energy unit changed for HP{hp_idx}: {old_unit or 'kWh (default)'} -> {unit or 'kWh (default)'}")
            
            # Check if unit is valid (not None)
            if self._energy_unit_cache[cache_key] is None:
                _LOGGER.debug(f"Energy tracking disabled for HP{hp_idx} due to invalid unit")
                return  # ABBRUCH - keine Werteänderung
            
            # Use cached unit for fast conversion
            cached_unit = self._energy_unit_cache[cache_key]
            original_energy = current_energy
            current_energy_kwh = self._convert_energy_to_kwh_cached(current_energy, cached_unit)
            
            # Log conversion details
            if cached_unit and cached_unit.lower() not in ["kwh", "kilowattstunden"]:
                _LOGGER.debug(f"DEBUG-021: Energy unit conversion for HP{hp_idx}: {original_energy} {cached_unit} -> {current_energy_kwh} kWh")
            else:
                _LOGGER.debug(f"DEBUG-021: Energy value for HP{hp_idx}: {current_energy_kwh} kWh (unit: {cached_unit or 'none'})")

            # Get last energy reading for this heat pump
            last_energy = self._last_energy_reading.get(f"hp{hp_idx}", None)
            first_value_seen = self._energy_first_value_seen.get(f"hp{hp_idx}", False)

            # SCHRITT 1: Prüfe ob current_energy_kwh == 0.0
            if current_energy_kwh == 0.0:
                _LOGGER.info(
                    f"ENERGY-DELTA: HP{hp_idx} - ❌ 0-WERT ERKANNT: {current_energy_kwh} kWh"
                )
                _LOGGER.info(
                    f"ENERGY-DELTA: HP{hp_idx} - ❌ Reset Zero-Value Protection (Flag war: {first_value_seen})"
                )
                # Reset bei 0-Wert
                self._energy_first_value_seen[f"hp{hp_idx}"] = False
                # WICHTIG: last_energy NICHT updaten!
                return

            # SCHRITT 2: Erster valider Wert > 0
            if not first_value_seen or last_energy is None:
                _LOGGER.info(
                    f"ENERGY-DELTA: HP{hp_idx} - 🔄 ERSTER WERT > 0: {current_energy_kwh:.2f} kWh"
                )
                _LOGGER.info(
                    f"ENERGY-DELTA: HP{hp_idx} - 🔄 Speichere als Referenz, KEIN Delta berechnet"
                )
                _LOGGER.info(
                    f"ENERGY-DELTA: HP{hp_idx} - 🔄 Warte auf zweiten Wert für Delta-Berechnung"
                )
                self._last_energy_reading[f"hp{hp_idx}"] = current_energy_kwh
                self._energy_first_value_seen[f"hp{hp_idx}"] = True
                await self._persist_counters()
                return  # KEIN Delta beim ersten Wert!

            # SCHRITT 3: Zweiter valider Wert > 0 - ABER prüfe auf Rückwärts-Sprung
            from .utils import calculate_energy_delta

            _LOGGER.info(
                f"ENERGY-DELTA: HP{hp_idx} - 📊 DELTA-BERECHNUNG: {current_energy_kwh:.2f} kWh vs {last_energy:.2f} kWh"
            )

            # Prüfe ob aktueller Wert kleiner als letzter Wert (verdächtig!)
            if current_energy_kwh < last_energy:
                _LOGGER.warning(
                    f"ENERGY-DELTA: HP{hp_idx} - ⚠️ RÜCKWÄRTS-SPRUNG ERKANNT!"
                )
                _LOGGER.warning(
                    f"ENERGY-DELTA: HP{hp_idx} - ⚠️ Aktuell ({current_energy_kwh:.2f} kWh) < Letzt ({last_energy:.2f} kWh)"
                )
                _LOGGER.warning(
                    f"ENERGY-DELTA: HP{hp_idx} - ⚠️ Möglicher Sensor-Reset/Überlauf - Reset Zero-Value Protection"
                )
                # Reset: Warte wieder auf 2 Werte
                self._energy_first_value_seen[f"hp{hp_idx}"] = False
                self._last_energy_reading[f"hp{hp_idx}"] = None
                await self._persist_counters()
                return

            # Normale Delta-Berechnung
            _LOGGER.info(
                f"ENERGY-DELTA: HP{hp_idx} - ✅ WERTE OK: {current_energy_kwh:.2f} >= {last_energy:.2f} kWh"
            )
            _LOGGER.info(
                f"ENERGY-DELTA: HP{hp_idx} - ✅ Starte normale Delta-Berechnung..."
            )
            
            energy_delta = calculate_energy_delta(current_energy_kwh, last_energy, max_delta=100.0)
            _LOGGER.info(f"ENERGY-DELTA: HP{hp_idx} - ✅ DELTA BERECHNET: {energy_delta:.6f} kWh")

            # Only proceed if delta is valid (>= 0)
            if energy_delta < 0:
                _LOGGER.warning(f"ENERGY-DELTA: HP{hp_idx} - ❌ Delta negativ, überspringe")
                return

            # Update last energy reading
            self._last_energy_reading[f"hp{hp_idx}"] = current_energy_kwh
            _LOGGER.info(f"ENERGY-DELTA: HP{hp_idx} - ✅ Delta-Berechnung abgeschlossen, last_energy aktualisiert")

            # Get last operating state for this heat pump
            last_state = self._last_operating_state.get(str(hp_idx), 0)
            
            # Map operating state to mode - alle nicht-definierten Modi gehen auf STBY
            mode_mapping = {
                0: "stby",         # STBY
                1: "heating",      # CH
                2: "hot_water",    # DHW
                3: "cooling",      # CC
                4: "stby",         # CIRCULATE -> geht auf STBY Counter
                5: "defrost",      # DEFROST
            }
            
            # Bestimme den Modus - alle nicht-definierten Modi werden auf STBY umgeleitet
            if current_state in mode_mapping:
                mode = mode_mapping[current_state]
            else:
                # Unbekannter Betriebsmodus -> auf STBY umleiten
                mode = "stby"
            
            # Determine which mode to increment based on state change
            if current_state != last_state:
                # State changed, increment the new mode
                _LOGGER.info(f"Verbrauchssensor {mode} aktiv: HP{hp_idx} (Betriebsmodus: {current_state})")
                await self._increment_energy_consumption(hp_idx, mode, energy_delta)
            else:
                # Same state, increment the current mode
                # For STBY mode, always update even with delta=0 to keep sensors alive
                if mode == "stby" or energy_delta > 0:
                    await self._increment_energy_consumption(hp_idx, mode, energy_delta)

            # Update last operating state
            self._last_operating_state[str(hp_idx)] = current_state

        except Exception as ex:
            _LOGGER.error(f"Error tracking energy consumption for HP{hp_idx}: %s", ex)

    async def _increment_energy_consumption(self, hp_idx, mode, energy_delta):
        """Increment energy consumption for a specific mode and heat pump."""
        try:
            from .utils import increment_energy_consumption_counter
            
            # Get energy offsets for this heat pump
            hp_key = f"hp{hp_idx}"
            _LOGGER.debug(f"DEBUG-014: Getting energy offsets for {hp_key}")
            energy_offsets = self._energy_offsets.get(hp_key, {})
            _LOGGER.debug(f"DEBUG-015: Energy offsets for {hp_key}: {energy_offsets}")
            _LOGGER.debug(f"DEBUG-016: Type of energy_offsets: {type(energy_offsets)}")
            
            # Get name prefix from entry data
            name_prefix = self.entry.data.get("name", "eu08l")
            
            # Increment both total and daily counters
            await increment_energy_consumption_counter(
                hass=self.hass,
                mode=mode,
                hp_index=hp_idx,
                energy_delta=energy_delta,
                name_prefix=name_prefix,
                use_legacy_modbus_names=True,
                energy_offsets=energy_offsets,
            )

        except Exception as ex:
            _LOGGER.error(f"Error incrementing energy consumption for HP{hp_idx} {mode}: %s", ex)

    def _on_ha_started(self, event):
        """Handle Home Assistant started event."""
        self._ha_started = True
        _LOGGER.debug(
            "Home Assistant started - enabling room temperature and PV surplus updates"
        )

    async def async_shutdown(self):
        """Shutdown the coordinator."""
        _LOGGER.debug("Shutting down Lambda coordinator")
        try:
            # Clean up entity registry listener
            if hasattr(self, "_registry_listener") and self._registry_listener:
                self._registry_listener()
                self._registry_listener = None

            # Close Modbus connection
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
            _LOGGER.error(f"Fehler beim Laden der Sensor-Namen-Überschreibungen: {e}")
            return {}



