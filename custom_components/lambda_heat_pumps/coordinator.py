"""Data update coordinator for Lambda."""

from __future__ import annotations
from datetime import timedelta
import logging
import os
import yaml
import json
import asyncio
import aiofiles
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
from .modbus_utils import async_read_holding_registers, get_int32_byte_order, combine_int32_registers
import time

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


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

        # self._load_offsets_and_persisted() ENTFERNT!

    async def _persist_counters(self):
        """Persist counter data and state information to file using Home Assistant's file operations."""
        data = {
            "heating_cycles": self._heating_cycles,
            "heating_energy": self._heating_energy,
            "last_operating_states": getattr(self, "_last_operating_state", {}),
            "energy_consumption": self._energy_consumption,
            "last_energy_readings": self._last_energy_reading,
            "energy_offsets": self._energy_offsets,
            "sensor_ids": getattr(self, "_sensor_ids", {}),
        }

        def _write_data():
            os.makedirs(os.path.dirname(self._persist_file), exist_ok=True)
            with open(self._persist_file, "w") as f:
                f.write(json.dumps(data))

        await self.hass.async_add_executor_job(_write_data)

    def mark_initialization_complete(self):
        """Markiere die Initialisierung als abgeschlossen - ermöglicht Flankenerkennung."""
        if not self._initialization_complete:
            self._initialization_complete = True
            _LOGGER.info("Coordinator-Initialisierung abgeschlossen - Flankenerkennung aktiviert")

    async def _load_offsets_and_persisted(self):
        # Lade Offsets aus lambda_wp_config.yaml
        config_dir = self.hass.config.config_dir
        config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        _LOGGER.info(f"Loading config from: {config_path}")
        
        if os.path.exists(config_path):
            _LOGGER.info("Config file exists, loading...")

            def _read_config():
                with open(config_path) as f:
                    content = f.read()
                    config = yaml.safe_load(content) or {}
                    return config

            try:
                config = await self.hass.async_add_executor_job(_read_config)
                _LOGGER.info(f"Loaded config keys: {list(config.keys())}")
                self._cycling_offsets = config.get("cycling_offsets", {})
                self._energy_offsets = config.get("energy_consumption_offsets", {})
                self._energy_sensor_configs = config.get("energy_consumption_sensors", {})
                _LOGGER.info(f"Loaded energy sensor configs: {self._energy_sensor_configs}")
            except Exception as e:
                _LOGGER.error(f"Error loading config: {e}")
        else:
            _LOGGER.warning(f"Config file not found: {config_path}")

        # Lade persistierte Zählerstände (falls vorhanden)
        if os.path.exists(self._persist_file):

            def _read_persist():
                with open(self._persist_file) as f:
                    content = f.read()
                    return json.loads(content)

            data = await self.hass.async_add_executor_job(_read_persist)
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
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung für {len(self._energy_sensor_configs)} konfigurierte Sensoren")
        await self._detect_and_handle_sensor_changes()

    async def _detect_and_handle_sensor_changes(self):
        """Erkenne Sensor-Wechsel und behandle sie entsprechend."""
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Starte Sensor-Wechsel-Erkennung")
        
        try:
            from .utils import detect_sensor_change, get_stored_sensor_id, store_sensor_id
            
            # Erstelle persist_data dict für die Hilfsfunktionen
            persist_data = {"sensor_ids": self._sensor_ids}
            
            for hp_key, sensor_config in self._energy_sensor_configs.items():
                # Extrahiere hp_idx aus hp_key (z.B. "hp1" -> 1)
                try:
                    hp_idx = int(hp_key.replace("hp", ""))
                except (ValueError, AttributeError):
                    _LOGGER.warning(f"SENSOR-CHANGE-DETECTION: Ungültiger hp_key: {hp_key}")
                    continue
                
                current_sensor_id = sensor_config.get("sensor_entity_id")
                if not current_sensor_id:
                    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Kein sensor_entity_id für {hp_key} konfiguriert")
                    continue
                
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
                _LOGGER.info(f"SENSOR-CHANGE-DETECTION: sensor_ids erfolgreich gespeichert")
            
            _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Sensor-Wechsel-Erkennung abgeschlossen")
            
        except Exception as e:
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Fehler bei Sensor-Wechsel-Erkennung: {e}")
            import traceback
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Traceback: {traceback.format_exc()}")

    async def _handle_sensor_change(self, hp_idx: int, new_sensor_id: str):
        """Behandle Sensor-Wechsel durch Anpassung der last_energy_readings."""
        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Behandle Sensor-Wechsel für HP{hp_idx} -> {new_sensor_id}")
        
        try:
            # Warte bis der neue Sensor verfügbar ist (max. 5 Versuche, 2 Sekunden Abstand)
            max_retries = 5
            retry_delay = 2.0
            
            for attempt in range(max_retries):
                new_sensor_state = self.hass.states.get(new_sensor_id)
                _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Versuch {attempt + 1}/{max_retries} - Neuer Sensor {new_sensor_id} Status: {new_sensor_state.state if new_sensor_state else 'None'}")
                
                if new_sensor_state and new_sensor_state.state not in ("unknown", "unavailable", "None"):
                    try:
                        new_sensor_value = float(new_sensor_state.state)
                        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Neuer Sensor-Wert nach {attempt + 1} Versuchen: {new_sensor_value}")
                        
                        # Hole alten Wert für Vergleich
                        hp_key = f"hp{hp_idx}"
                        old_value = self._last_energy_reading.get(hp_key, 0.0)
                        
                        # Ersetze last_energy_readings mit dem ersten Wert des neuen Sensors
                        self._last_energy_reading[hp_key] = new_sensor_value
                        
                        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: last_energy_readings für {hp_key} geändert: {old_value} -> {new_sensor_value}")
                        
                        # Speichere Änderungen in JSON
                        await self._persist_counters()
                        _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Änderungen für {hp_key} in JSON gespeichert")
                        return  # Erfolgreich abgeschlossen
                        
                    except (ValueError, TypeError) as e:
                        _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Fehler beim Konvertieren des Sensor-Werts: {e}")
                        break  # Keine weiteren Versuche bei Konvertierungsfehler
                
                # Warte vor dem nächsten Versuch (außer beim letzten Versuch)
                if attempt < max_retries - 1:
                    _LOGGER.info(f"SENSOR-CHANGE-DETECTION: Warte {retry_delay}s vor nächstem Versuch...")
                    await asyncio.sleep(retry_delay)
            
            # Alle Versuche fehlgeschlagen - verwende 0 als Fallback
            _LOGGER.warning(f"SENSOR-CHANGE-DETECTION: Neuer Sensor {new_sensor_id} nach {max_retries} Versuchen nicht verfügbar, verwende 0")
            self._last_energy_reading[f"hp{hp_idx}"] = 0.0
            await self._persist_counters()
                
        except Exception as e:
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Fehler beim Behandeln des Sensor-Wechsels für HP{hp_idx}: {e}")
            import traceback
            _LOGGER.error(f"SENSOR-CHANGE-DETECTION: Traceback: {traceback.format_exc()}")

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

        # Sort addresses for potential batch optimization
        sorted_addresses = sorted(address_list.keys())

        # Group addresses for batch reading, avoiding INT32 boundaries and mixed types
        batches = []
        current_batch = []
        current_type = None
        last_addr = None

        def get_type(addr):
            return address_list[addr].get("data_type")

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
                        batch[0], address_list[batch[0]], sensor_mapping, data
                    )
                    continue
                start_addr = batch[0]
                count = len(batch)
                batch_key = (start_addr, count)

                # For small batches or single registers, use individual reads
                if count == 1 or count > 100:
                    for addr in batch:
                        await self._read_single_register(
                            addr, address_list[addr], sensor_mapping, data
                        )
                    continue

                # Prüfe ob dieser Batch bereits zu oft fehlgeschlagen ist
                if batch_key in self._individual_read_addresses:
                    _LOGGER.debug(f"Using individual reads for {start_addr}-{start_addr + count - 1} (previous failures)")
                    for addr in batch:
                        await self._read_single_register(
                            addr, address_list[addr], sensor_mapping, data
                        )
                    continue

                # PrÃƒÂ¼fe ob Register in der Individual-Read-Liste stehen
                if any(addr in INDIVIDUAL_READ_REGISTERS for addr in batch):
                    _LOGGER.debug(f"Using individual reads for {start_addr}-{start_addr + count - 1} (configured individual read)")
                    for addr in batch:
                        await self._read_single_register(
                            addr, address_list[addr], sensor_mapping, data
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

        except Exception as ex:
            _LOGGER.debug(f"Error reading register {address}: {ex}")

    async def _read_general_sensors_batch(self, data):
        """Read general sensors using batch optimization."""
        address_list = {}
        sensor_mapping = {}

        for sensor_id, sensor_info in SENSOR_TYPES.items():
            if self.is_register_disabled(sensor_info["address"]):
                continue

            address = sensor_info["address"]
            address_list[address] = sensor_info
            sensor_mapping[address] = sensor_id

        if address_list:
            batch_data = await self._read_registers_batch(address_list, sensor_mapping)
            data.update(batch_data)

    async def _read_heatpump_sensors_batch(self, data, num_hps, compatible_hp_sensors):
        """Read heat pump sensors in optimized batches."""
        for hp_idx in range(1, num_hps + 1):
            base_address = generate_base_addresses("hp", num_hps)[hp_idx]

            # Group sensors by consecutive addresses
            address_groups = {}
            sensor_mapping = {}
            for sensor_id, sensor_info in compatible_hp_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                address_groups[address] = sensor_info
                sensor_mapping[address] = f"hp{hp_idx}_{sensor_id}"

            # Read in batches
            batch_results = await self._read_registers_batch(
                address_groups, sensor_mapping
            )
            data.update(batch_results)

    async def _read_boiler_sensors_batch(self, data, num_boil, compatible_boil_sensors):
        """Read boiler sensors in optimized batches."""
        for boil_idx in range(1, num_boil + 1):
            base_address = generate_base_addresses("boil", num_boil)[boil_idx]

            # Group sensors by consecutive addresses
            address_groups = {}
            sensor_mapping = {}
            for sensor_id, sensor_info in compatible_boil_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                address_groups[address] = sensor_info
                sensor_mapping[address] = f"boil{boil_idx}_{sensor_id}"

            # Read in batches
            batch_results = await self._read_registers_batch(
                address_groups, sensor_mapping
            )
            data.update(batch_results)

    async def _read_buffer_sensors_batch(self, data, num_buff, compatible_buff_sensors):
        """Read buffer sensors in optimized batches."""
        for buff_idx in range(1, num_buff + 1):
            base_address = generate_base_addresses("buff", num_buff)[buff_idx]

            # Group sensors by consecutive addresses
            address_groups = {}
            sensor_mapping = {}
            for sensor_id, sensor_info in compatible_buff_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                address_groups[address] = sensor_info
                sensor_mapping[address] = f"buff{buff_idx}_{sensor_id}"

            # Read in batches
            batch_results = await self._read_registers_batch(
                address_groups, sensor_mapping
            )
            data.update(batch_results)

    async def _read_solar_sensors_batch(self, data, num_sol, compatible_sol_sensors):
        """Read solar sensors in optimized batches."""
        for sol_idx in range(1, num_sol + 1):
            base_address = generate_base_addresses("sol", num_sol)[sol_idx]

            # Group sensors by consecutive addresses
            address_groups = {}
            sensor_mapping = {}
            for sensor_id, sensor_info in compatible_sol_sensors.items():
                address = base_address + sensor_info["relative_address"]
                if not self.is_address_enabled_by_entity(address):
                    continue

                address_groups[address] = sensor_info
                sensor_mapping[address] = f"sol{sol_idx}_{sensor_id}"

            # Read in batches
            batch_results = await self._read_registers_batch(
                address_groups, sensor_mapping
            )
            data.update(batch_results)

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
                timeout=5  # Short timeout for health check
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

            # Flankenerkennung und Energieintegration nach dem Auslesen aller Wärmepumpen-Sensoren
            for hp_idx in range(1, num_hps + 1):
                op_state_val = data.get(f"hp{hp_idx}_operating_state")
                if op_state_val is None:
                    continue

                # Get last operating state
                last_op_state = self._last_operating_state.get(hp_idx, "UNBEKANNT")
                
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
                last_op_state = self._last_operating_state.get(hp_idx, "UNBEKANNT")
                
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
                                f"Cycling {mode} erhöht: HP{hp_idx} von {old_count} auf {new_count}"
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
                self._last_operating_state[hp_idx] = op_state_val
            await self._persist_counters()

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

            # Read heating circuit sensors
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
                                f"hc{hc_idx}_{sensor_id}"
                            )
                        key = (
                            override_name
                            if override_name
                            else f"hc{hc_idx}_{sensor_id}"
                        )
                        data[key] = value
                    except Exception as ex:
                        _LOGGER.debug(
                            "Error reading register %d: %s",
                            address,
                            ex,
                        )

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

            # Energy Consumption Tracking
            _LOGGER.debug(f"DEBUG-001: Starting energy consumption tracking")
            await self._track_energy_consumption(data)
            _LOGGER.debug(f"DEBUG-002: Energy consumption tracking completed")

            _LOGGER.debug(f"DEBUG-003: Returning data from _async_update_data")
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

    async def _track_energy_consumption(self, data):
        """Track energy consumption by operating mode."""
        _LOGGER.debug(f"DEBUG-004: Entering _track_energy_consumption")
        try:
            # Get number of heat pumps from config entry
            num_hps = self.entry.data.get("num_hps", 1)
            _LOGGER.debug(f"DEBUG-005: Number of heat pumps: {num_hps}")
            
            # Get current operating states for all heat pumps
            current_states = {}
            for hp_idx in range(1, num_hps + 1):
                state_key = f"hp{hp_idx}_operating_state"
                if state_key in data:
                    current_states[hp_idx] = data[state_key]
                else:
                    current_states[hp_idx] = 0  # Default to 0 if not available
                _LOGGER.debug(f"DEBUG-006: HP{hp_idx} operating state: {current_states[hp_idx]}")

            # Track energy consumption for each heat pump
            for hp_idx in range(1, num_hps + 1):
                _LOGGER.debug(f"DEBUG-007: Tracking energy consumption for HP{hp_idx}")
                await self._track_hp_energy_consumption(hp_idx, current_states[hp_idx], data)
                _LOGGER.debug(f"DEBUG-008: Completed tracking energy consumption for HP{hp_idx}")

            _LOGGER.debug(f"DEBUG-009: Completed _track_energy_consumption")

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

            # Get unit from sensor attributes and convert to kWh
            unit = current_energy_state.attributes.get("unit_of_measurement", "")
            from .utils import convert_energy_to_kwh
            original_energy = current_energy
            current_energy_kwh = convert_energy_to_kwh(current_energy, unit)
            
            # Log conversion details (analog zur PV Surplus Konvertierung)
            if unit and unit.lower() not in ["kwh", "kilowattstunden"]:
                _LOGGER.debug(f"DEBUG-021: Energy unit conversion for HP{hp_idx}: {original_energy} {unit} -> {current_energy_kwh} kWh")
            else:
                _LOGGER.debug(f"DEBUG-021: Energy value for HP{hp_idx}: {current_energy_kwh} kWh (unit: {unit or 'none'})")

            # Get last energy reading for this heat pump
            last_energy = self._last_energy_reading.get(f"hp{hp_idx}", 0.0)
            _LOGGER.debug(f"DEBUG-019: Last energy reading: {last_energy:.6f}")
            
            # Calculate energy delta
            from .utils import calculate_energy_delta
            raw_delta = current_energy_kwh - last_energy
            energy_delta = calculate_energy_delta(current_energy_kwh, last_energy, max_delta=100.0)
            _LOGGER.debug(f"DEBUG-020: Raw delta: {raw_delta:.6f}, Calculated delta: {energy_delta:.6f}")
            
            # Only skip if delta is negative (overflow) or if we're not in STBY mode
            if energy_delta < 0:
                return

            # Update last energy reading
            self._last_energy_reading[f"hp{hp_idx}"] = current_energy_kwh

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



