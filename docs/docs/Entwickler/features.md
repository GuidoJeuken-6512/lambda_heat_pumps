---
title: "Features (Technische Übersicht)"
---

# Features – Technische Übersicht

Diese Seite bietet eine technische Übersicht der wichtigsten Features der Lambda Heat Pumps Integration mit Code-Beispielen und Implementierungsdetails.

## Architektur-Übersicht

Die Integration basiert auf dem **Coordinator-Pattern** von Home Assistant:

```python
# custom_components/lambda_heat_pumps/coordinator.py
class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Lambda data."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name="Lambda Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = None  # Modbus-Client
        self._last_operating_state = {}  # Für Flankenerkennung
        self._heating_cycles = {}  # Cycling-Tracking
        self._energy_consumption = {}  # Energie-Tracking
```

**Hauptkomponenten:**
- `coordinator.py`: Datenkoordinator für Modbus-Kommunikation
- `sensor.py`: Sensor-Entities (über 100 verschiedene Sensoren)
- `climate.py`: Climate-Entities für Heizung/Warmwasser
- `number.py`: Number-Entities für Heizkurven-Parameter
- `services.py`: Custom Services (PV-Überschuss, Raumthermostat)
- `utils.py`: Hilfsfunktionen und Konfigurations-Loading

## Modbus-Kommunikation

### Asynchrone Modbus-Operationen

Die Integration nutzt asynchrone Modbus-Operationen für nicht-blockierende Kommunikation:

```python
# custom_components/lambda_heat_pumps/modbus_utils.py
async def async_read_holding_registers(
    client, address: int, count: int, unit: int
) -> list[int]:
    """Asynchrones Lesen von Holding-Registern."""
    try:
        result = await client.read_holding_registers(address, count, unit=unit)
        return result.registers
    except Exception as e:
        _LOGGER.error("Modbus read error: %s", e)
        raise
```

### Batch-Reading mit Fallback

Optimiertes Batch-Reading mit automatischem Fallback auf Einzel-Lesevorgänge:

```python
# custom_components/lambda_heat_pumps/coordinator.py
async def _read_registers_batch(self, registers: list[tuple]) -> dict:
    """Batch-Reading mit Fehlerbehandlung."""
    # Versuche Batch-Read
    try:
        result = await self._read_consecutive_registers(start_addr, count)
        return result
    except Exception:
        # Fallback: Einzel-Lesevorgänge
        for addr, count in registers:
            result[addr] = await self._read_single_register(addr)
```

### Register-Deduplizierung

Globale Register-Deduplizierung reduziert Modbus-Traffic um ~80%:

```python
# custom_components/lambda_heat_pumps/coordinator.py
async def _async_update_data(self):
    """Daten-Update mit Register-Cache."""
    # Sammle alle benötigten Register
    all_registers = self._collect_all_registers()
    
    # Dedupliziere Register-Adressen
    unique_registers = self._deduplicate_registers(all_registers)
    
    # Batch-Read für deduplizierte Register
    data = await self._read_registers_batch(unique_registers)
    
    # Verteile Daten an alle Module
    return self._distribute_data(data)
```

## Automatische Modulerkennung

### Background-Auto-Detection

Hardware-Erkennung läuft im Hintergrund, ohne Startverzögerungen:

```python
# custom_components/lambda_heat_pumps/module_auto_detect.py
async def auto_detect_modules(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Automatische Erkennung verfügbarer Module."""
    detected = {
        "heat_pumps": [],
        "boilers": [],
        "buffers": [],
        "solar": [],
        "heating_circuits": [],
    }
    
    # Prüfe Register für jedes Modul
    for module_type in detected.keys():
        if await _check_module_exists(module_type):
            detected[module_type].append(module_index)
    
    return detected
```

### Dynamische Entity-Erstellung

Sensoren werden basierend auf erkannten Modulen erstellt:

```python
# custom_components/lambda_heat_pumps/sensor.py
async def async_setup_entry(hass, entry, async_add_entities):
    """Dynamische Sensor-Erstellung."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Erkenne verfügbare Module
    modules = coordinator.detected_modules
    
    # Erstelle Sensoren für jedes Modul
    for module_type, module_list in modules.items():
        for module_idx in module_list:
            sensors = _create_sensors_for_module(module_type, module_idx)
            async_add_entities(sensors)
```

## Cycling-Sensoren

### Flankenerkennung

Robuste Flankenerkennung für Betriebszustandsänderungen:

```python
# custom_components/lambda_heat_pumps/coordinator.py
def _detect_operating_state_change(
    self, hp_idx: int, current_state: int, last_state: int
) -> str | None:
    """Erkenne Betriebszustandsänderung (Flanke)."""
    if current_state != last_state:
        # Mapping: Betriebszustand → Modus
        mode_map = {
            1: "heating",      # CH
            2: "hot_water",    # DHW
            3: "cooling",       # CC
            5: "defrost",       # DEFROST
        }
        return mode_map.get(current_state)
    return None
```

### Cycling-Counter-Inkrementierung

Automatische Inkrementierung der Cycling-Counter:

```python
# custom_components/lambda_heat_pumps/utils.py
async def increment_cycling_counter(
    hass: HomeAssistant,
    entry_id: str,
    device_id: str,
    mode: str,
    period: str,
) -> None:
    """Inkrementiere Cycling-Counter."""
    entity_id = f"sensor.{device_id}_{mode}_cycling_{period}"
    
    # Lade aktuellen Wert
    state = hass.states.get(entity_id)
    current_value = int(state.state) if state else 0
    
    # Wende Offset an
    offset = get_cycling_offset(device_id, mode, period)
    new_value = current_value + 1 + offset
    
    # Speichere neuen Wert
    await hass.services.async_call(
        "lambda_heat_pumps",
        "set_cycling_value",
        {"entity_id": entity_id, "value": new_value},
    )
```

### Automatische Resets

Tägliche Sensoren werden um Mitternacht automatisch zurückgesetzt:

```python
# custom_components/lambda_heat_pumps/automations.py
def setup_cycling_automations(hass: HomeAssistant, entry_id: str):
    """Richte Automatisierungen für Cycling-Resets ein."""
    # Täglicher Reset um Mitternacht
    hass.services.async_call(
        "automation",
        "trigger",
        {
            "entity_id": f"automation.{entry_id}_daily_reset",
            "at": "00:00:00",
        },
    )
```

## Energieverbrauchssensoren

### Sensor-Wechsel-Erkennung

Intelligente Erkennung von Sensor-Änderungen zur Vermeidung falscher Berechnungen:

```python
# custom_components/lambda_heat_pumps/coordinator.py
async def _detect_energy_sensor_change(
    self, hp_idx: int, current_sensor_id: str
) -> bool:
    """Erkenne Sensor-Wechsel."""
    last_sensor_id = self._sensor_ids.get(hp_idx)
    
    if last_sensor_id and last_sensor_id != current_sensor_id:
        _LOGGER.warning(
            "Energy sensor changed for HP%d: %s → %s",
            hp_idx, last_sensor_id, current_sensor_id
        )
        # Setze Tracking zurück
        self._last_energy_reading[hp_idx] = None
        return True
    
    self._sensor_ids[hp_idx] = current_sensor_id
    return False
```

### Energie-Tracking

Automatisches Tracking des Energieverbrauchs nach Betriebsart:

```python
# custom_components/lambda_heat_pumps/coordinator.py
async def _track_energy_consumption(self, data: dict):
    """Tracke Energieverbrauch für alle Wärmepumpen."""
    for hp_idx in range(1, 4):  # HP1, HP2, HP3
        current_state = data.get(f"hp{hp_idx}_operating_state")
        if current_state is None:
            continue
        
        # Bestimme Betriebsmodus
        mode = self._get_operating_mode(current_state)
        
        # Tracke Energie für diesen Modus
        await self._track_hp_energy_consumption(hp_idx, mode, data)
```

### Einheitenkonvertierung

Automatische Konvertierung zwischen Wh/kWh/MWh:

```python
# custom_components/lambda_heat_pumps/utils.py
def convert_energy_to_kwh(value: float, unit: str) -> float:
    """Konvertiere Energie-Wert zu kWh."""
    unit_map = {
        "Wh": 0.001,
        "kWh": 1.0,
        "MWh": 1000.0,
    }
    return value * unit_map.get(unit, 1.0)
```

## Heizkurven-Berechnung

### Template-Sensor für Vorlauftemperatur

Automatische Berechnung der Vorlauftemperatur basierend auf Außentemperatur:

```python
# custom_components/lambda_heat_pumps/template_sensor.py
class LambdaHeatingCurveCalcSensor(CoordinatorEntity, SensorEntity):
    """Sensor für berechnete Heizkurven-Vorlauftemperatur."""
    
    @property
    def native_value(self) -> float | None:
        """Berechne Vorlauftemperatur aus Heizkurven-Stützpunkten."""
        outside_temp = self._get_outside_temperature()
        cold_point = self._get_cold_point()  # -22°C
        mid_point = self._get_mid_point()    # 0°C
        warm_point = self._get_warm_point()  # +22°C
        
        # Lineare Interpolation
        if outside_temp <= -22:
            return cold_point
        elif outside_temp >= 22:
            return warm_point
        else:
            # Interpolation zwischen Stützpunkten
            return self._interpolate(outside_temp, cold_point, mid_point, warm_point)
```

### Number-Entities mit Modbus-Synchronisation

Bidirektionale Synchronisation zwischen Home Assistant und Modbus:

```python
# custom_components/lambda_heat_pumps/number.py
class LambdaFlowLineOffsetNumber(CoordinatorEntity, NumberEntity):
    """Number-Entity für Vorlauf-Offset mit Modbus-Sync."""
    
    async def async_set_native_value(self, value: float) -> None:
        """Setze Wert und schreibe nach Modbus."""
        # Validiere Wert
        if not -10.0 <= value <= 10.0:
            raise ValueError("Value out of range")
        
        # Schreibe nach Modbus
        await self.coordinator.write_modbus_register(
            self._register_address, int(value * 10)  # Skalierung
        )
        
        # Aktualisiere lokalen Wert
        self._attr_native_value = value
```

## PV-Überschuss-Steuerung

### Service-Scheduler

Intelligenter Service-Scheduler, der nur aktiviert wird, wenn benötigt:

```python
# custom_components/lambda_heat_pumps/services.py
async def setup_pv_surplus_service(hass: HomeAssistant, entry: ConfigEntry):
    """Richte PV-Überschuss-Service ein."""
    if not entry.options.get("pv_surplus_control"):
        return  # Service nicht aktivieren
    
    async def update_pv_power(call: ServiceCall):
        """Schreibe PV-Leistung nach Modbus Register 102."""
        sensor_id = entry.options.get("pv_surplus_sensor")
        power_w = await _get_power_from_sensor(hass, sensor_id)
        
        # Konvertiere kW → W falls nötig
        if power_w < 1000:
            power_w = power_w * 1000
        
        # Schreibe nach Modbus
        await coordinator.write_modbus_register(102, int(power_w))
    
    # Registriere Service mit Intervall
    hass.services.async_register(
        DOMAIN, "update_pv_power", update_pv_power
    )
```

## Raumthermostat-Steuerung

### Externe Sensor-Integration

Integration externer Temperatursensoren für Raumthermostat-Steuerung:

```python
# custom_components/lambda_heat_pumps/services.py
async def _handle_update_room_temperature(
    hass: HomeAssistant,
    coordinator: LambdaDataUpdateCoordinator,
    sensor_id: str,
    hc_idx: int,
) -> None:
    """Aktualisiere Raumtemperatur aus externem Sensor."""
    # Lese Sensor-Wert
    state = hass.states.get(sensor_id)
    if not state:
        return
    
    room_temp = float(state.state)
    
    # Wende Offset und Faktor an
    offset = coordinator.entry.options.get(f"hc{hc_idx}_room_thermostat_offset", 0)
    factor = coordinator.entry.options.get(f"hc{hc_idx}_room_thermostat_factor", 1.0)
    
    adjusted_temp = (room_temp + offset) * factor
    
    # Schreibe nach Modbus
    register = 5004 + (hc_idx - 1) * 100  # HC Room Device Temperature
    await coordinator.write_modbus_register(register, int(adjusted_temp * 10))
```

## Konfigurations-Management

### YAML-Konfiguration mit Caching

Effizientes Laden und Caching der `lambda_wp_config.yaml`:

```python
# custom_components/lambda_heat_pumps/utils.py
async def load_lambda_config(hass: HomeAssistant) -> dict:
    """Lade Lambda-Konfiguration mit Caching."""
    # Prüfe Cache
    if "_lambda_config_cache" in hass.data:
        return hass.data["_lambda_config_cache"]
    
    # Lade YAML
    config_path = os.path.join(hass.config.config_dir, "lambda_wp_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Parse Konfiguration
    result = {
        "disabled_registers": set(config.get("disabled_registers", [])),
        "sensors_names_override": _parse_sensor_overrides(config),
        "cycling_offsets": config.get("cycling_offsets", {}),
        "energy_consumption_sensors": config.get("energy_consumption_sensors", {}),
        "modbus": config.get("modbus", {}),
    }
    
    # Cache Ergebnis
    hass.data["_lambda_config_cache"] = result
    return result
```

## Performance-Optimierungen

### Register-Cache

Globale Register-Deduplizierung reduziert Modbus-Traffic:

```python
# custom_components/lambda_heat_pumps/coordinator.py
class RegisterCache:
    """Cache für Modbus-Register-Lesevorgänge."""
    
    def __init__(self):
        self._cache = {}  # {address: (value, timestamp)}
        self._cache_ttl = 1.0  # 1 Sekunde TTL
    
    def get(self, address: int) -> int | None:
        """Hole Wert aus Cache."""
        if address in self._cache:
            value, timestamp = self._cache[address]
            if time.time() - timestamp < self._cache_ttl:
                return value
        return None
    
    def set(self, address: int, value: int):
        """Setze Wert im Cache."""
        self._cache[address] = (value, time.time())
```

### Background-Template-Loading

Template-Sensoren laden im Hintergrund, ohne Start zu blockieren:

```python
# custom_components/lambda_heat_pumps/sensor.py
async def _setup_template_sensors_async(hass, coordinator, async_add_entities):
    """Lade Template-Sensoren im Hintergrund."""
    # Starte Background-Task
    hass.async_create_task(
        _load_templates_in_background(hass, coordinator, async_add_entities)
    )
```

## Mehrsprachige Unterstützung

### Translation-System

Automatisches Laden und Anwenden von Übersetzungen:

```python
# custom_components/lambda_heat_pumps/utils.py
def load_sensor_translations(hass: HomeAssistant, language: str) -> dict:
    """Lade Sensor-Übersetzungen."""
    translation_file = f"custom_components/lambda_heat_pumps/translations/{language}.json"
    with open(translation_file, "r") as f:
        translations = json.load(f)
    return translations.get("entity", {}).get("sensor", {})
```

## Zusammenfassung

Die Integration bietet:

- **Asynchrone Modbus-Kommunikation** mit Batch-Reading und Fallback
- **Automatische Modulerkennung** im Hintergrund
- **Cycling-Sensoren** mit Flankenerkennung und automatischen Resets
- **Energieverbrauchssensoren** mit Sensor-Wechsel-Erkennung
- **Heizkurven-Berechnung** mit Template-Sensoren
- **PV-Überschuss-Steuerung** mit Service-Scheduler
- **Raumthermostat-Integration** mit externen Sensoren
- **Performance-Optimierungen** durch Register-Caching und Deduplizierung
- **Mehrsprachige Unterstützung** mit automatischem Translation-Loading

Alle Features sind modular aufgebaut und können unabhängig erweitert werden.

