# Lambda Heat Pumps: Sensor-Wechsel-Erkennung für Energieverbrauchs-Sensoren

**🇩🇪 [Deutsche Version siehe unten](#deutsche-version)**

## Table of Contents
- [Problem Description](#problem-description)
- [Solution Approach](#solution-approach)
- [Technical Implementation](#technical-implementation)
- [Benefits](#benefits)
- [Implementation Plan](#implementation-plan)

---

## Problem Description

### The Issue
When the source sensor for energy consumption calculation is changed in the configuration, incorrect energy consumption values are calculated due to sensor value jumps.

### Scenario
- **Old Sensor**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated` = 4000 kWh
- **New Sensor**: `sensor.lambda_wp_verbrauch` = 0 kWh
- **Delta Calculation**: 0 - 4000 = -4000 kWh (incorrect!)

### Root Cause
The `last_energy_readings` value in `cycle_energy_persist.json` still contains the last value from the old sensor, causing incorrect delta calculations when the new sensor starts with a different value.

### When This Occurs
- **Integration Restart**: When Home Assistant restarts
- **Integration Reload**: When the integration is reloaded
- **Configuration Change**: When `sensor_entity_id` is changed in `lambda_wp_config.yaml`

## Solution Approach

### Core Concept
Detect sensor changes during configuration loading and adjust `last_energy_readings` to match the first value of the new sensor.

### Key Principles
1. **Detection Point**: During configuration loading, not during runtime
2. **Simple Logic**: Replace `last_energy_readings` with new sensor's first value
3. **No Complex Offsets**: No need for complex offset calculations
4. **Persistent**: Changes are saved to `cycle_energy_persist.json`

### Example Flow
1. **Before**: `last_energy_readings: {"hp1": 4000.0}` (old sensor)
2. **Sensor Change**: `sensor.lambda_wp_verbrauch` = 0 kWh
3. **After**: `last_energy_readings: {"hp1": 0.0}` (new sensor)
4. **Delta Calculation**: `current_value - 0.0 = correct deltas`

## Technical Implementation

### 1. Sensor Change Detection
```python
def detect_sensor_change(stored_sensor_id: str, current_sensor_id: str) -> bool:
    """Detect sensor change by comparing stored and current sensor IDs."""
    return stored_sensor_id and stored_sensor_id != current_sensor_id
```

### 2. Configuration Loading Enhancement
```python
async def _load_energy_sensor_configs(self):
    """Load energy sensor configurations and detect sensor changes."""
    config = await load_lambda_config(self.hass)
    energy_sensors = config.get("energy_consumption_sensors", {})
    
    for hp_idx, sensor_config in energy_sensors.items():
        current_sensor_id = sensor_config.get("sensor_entity_id")
        stored_sensor_id = self._get_stored_sensor_id(hp_idx)  # from JSON
        
        if detect_sensor_change(stored_sensor_id, current_sensor_id):
            _LOGGER.info(f"Sensor change detected for {hp_idx}: {stored_sensor_id} -> {current_sensor_id}")
            await self._handle_sensor_change(hp_idx, current_sensor_id)
        
        # Store new sensor for next comparison
        self._store_sensor_id(hp_idx, current_sensor_id)
```

### 3. Sensor Change Handling
```python
async def _handle_sensor_change(self, hp_idx, new_sensor_id):
    """Handle sensor change by adjusting last_energy_readings."""
    try:
        # Load first value of new sensor
        new_sensor_state = self.hass.states.get(new_sensor_id)
        if new_sensor_state and new_sensor_state.state not in ("unknown", "unavailable"):
            new_sensor_value = float(new_sensor_state.state)
            
            # Replace last_energy_readings with new sensor's first value
            self._last_energy_reading[f"hp{hp_idx}"] = new_sensor_value
            
            _LOGGER.info(f"last_energy_readings for {hp_idx} set to {new_sensor_value} (new sensor)")
            
            # Save changes to JSON
            await self._persist_counters()
            
        else:
            _LOGGER.warning(f"New sensor {new_sensor_id} not available, using 0")
            self._last_energy_reading[f"hp{hp_idx}"] = 0.0
            
    except Exception as e:
        _LOGGER.error(f"Error handling sensor change for {hp_idx}: {e}")
```

### 4. JSON Structure Enhancement
```json
{
  "heating_cycles": {},
  "heating_energy": {},
  "last_operating_states": {},
  "energy_consumption": {},
  "last_energy_readings": {"hp1": 0.0, "hp2": 10.0, "hp3": 0.0},
  "energy_offsets": {},
  "sensor_ids": {
    "hp1": "sensor.lambda_wp_verbrauch",
    "hp2": "sensor.eu08l_hp2_compressor_power_consumption_accumulated",
    "hp3": "sensor.eu08l_hp3_compressor_power_consumption_accumulated"
  }
}
```

## Benefits

### 1. Simplicity
- **Minimal Code**: Only a few lines of code needed
- **Clear Logic**: Easy to understand and maintain
- **No Complex Calculations**: No need for complex offset calculations

### 2. Reliability
- **Robust**: Works for any sensor change scenario
- **Persistent**: Survives restarts and reloads
- **Error Handling**: Graceful handling of unavailable sensors

### 3. Performance
- **Efficient**: Only runs during configuration loading
- **No Runtime Impact**: No performance impact during normal operation
- **Minimal Memory**: No additional state management needed

### 4. User Experience
- **Transparent**: Users don't need to manually configure anything
- **Automatic**: Works automatically when sensors are changed
- **Seamless**: No interruption to energy consumption tracking

## Implementation Plan

### Phase 1: Core Functions
1. **Create Helper Functions** in `utils.py`:
   - `detect_sensor_change()`
   - `get_stored_sensor_id()`
   - `store_sensor_id()`

### Phase 2: Configuration Loading
2. **Enhance Configuration Loading** in `coordinator.py`:
   - Add sensor change detection to `_load_energy_sensor_configs()`
   - Implement `_handle_sensor_change()` method

### Phase 3: JSON Persistence
3. **Extend JSON Structure**:
   - Add `sensor_ids` section to `cycle_energy_persist.json`
   - Update `_persist_counters()` and `_load_offsets_and_persisted()`

### Phase 4: Testing
4. **Test Scenarios**:
   - Test sensor change detection
   - Test with unavailable sensors
   - Test with different sensor values
   - Test persistence across restarts

### Phase 5: Documentation
5. **Update Documentation**:
   - Update `ENERGY_CONSUMPTION_SENSORS.md`
   - Add troubleshooting section
   - Update configuration examples

---

## Deutsche Version

# Lambda Heat Pumps: Sensor-Wechsel-Erkennung für Energieverbrauchs-Sensoren

## Problembeschreibung

### Das Problem
Wenn der Quellsensor für die Energieverbrauchsberechnung in der Konfiguration geändert wird, werden aufgrund von Sensorwert-Sprüngen falsche Energieverbrauchswerte berechnet.

### Szenario
- **Alter Sensor**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated` = 4000 kWh
- **Neuer Sensor**: `sensor.lambda_wp_verbrauch` = 0 kWh
- **Delta-Berechnung**: 0 - 4000 = -4000 kWh (falsch!)

### Ursache
Der `last_energy_readings`-Wert in `cycle_energy_persist.json` enthält noch den letzten Wert des alten Sensors, was zu falschen Delta-Berechnungen führt, wenn der neue Sensor mit einem anderen Wert startet.

### Wann tritt das auf
- **Integration-Neustart**: Wenn Home Assistant neu startet
- **Integration-Reload**: Wenn die Integration neu geladen wird
- **Konfigurationsänderung**: Wenn `sensor_entity_id` in `lambda_wp_config.yaml` geändert wird

## Lösungsansatz

### Kernkonzept
Sensor-Wechsel beim Konfigurationsladen erkennen und `last_energy_readings` an den ersten Wert des neuen Sensors anpassen.

### Wichtige Prinzipien
1. **Erkennungspunkt**: Beim Konfigurationsladen, nicht zur Laufzeit
2. **Einfache Logik**: `last_energy_readings` durch ersten Wert des neuen Sensors ersetzen
3. **Keine komplexen Offsets**: Keine Notwendigkeit für komplexe Offset-Berechnungen
4. **Persistent**: Änderungen werden in `cycle_energy_persist.json` gespeichert

### Beispiel-Ablauf
1. **Vorher**: `last_energy_readings: {"hp1": 4000.0}` (alter Sensor)
2. **Sensor-Wechsel**: `sensor.lambda_wp_verbrauch` = 0 kWh
3. **Nachher**: `last_energy_readings: {"hp1": 0.0}` (neuer Sensor)
4. **Delta-Berechnung**: `aktueller_wert - 0.0 = korrekte Deltas`

## Technische Implementierung

### 1. Sensor-Wechsel-Erkennung
```python
def detect_sensor_change(stored_sensor_id: str, current_sensor_id: str) -> bool:
    """Erkenne Sensor-Wechsel durch Vergleich der gespeicherten und aktuellen Sensor-IDs."""
    return stored_sensor_id and stored_sensor_id != current_sensor_id
```

### 2. Konfigurationsladen-Erweiterung
```python
async def _load_energy_sensor_configs(self):
    """Lade Energie-Sensor-Konfigurationen und erkenne Sensor-Wechsel."""
    config = await load_lambda_config(self.hass)
    energy_sensors = config.get("energy_consumption_sensors", {})
    
    for hp_idx, sensor_config in energy_sensors.items():
        current_sensor_id = sensor_config.get("sensor_entity_id")
        stored_sensor_id = self._get_stored_sensor_id(hp_idx)  # aus JSON
        
        if detect_sensor_change(stored_sensor_id, current_sensor_id):
            _LOGGER.info(f"Sensor-Wechsel erkannt für {hp_idx}: {stored_sensor_id} -> {current_sensor_id}")
            await self._handle_sensor_change(hp_idx, current_sensor_id)
        
        # Speichere neuen Sensor für nächsten Vergleich
        self._store_sensor_id(hp_idx, current_sensor_id)
```

### 3. Sensor-Wechsel-Behandlung
```python
async def _handle_sensor_change(self, hp_idx, new_sensor_id):
    """Behandle Sensor-Wechsel durch Anpassung der last_energy_readings."""
    try:
        # Lade ersten Wert des neuen Sensors
        new_sensor_state = self.hass.states.get(new_sensor_id)
        if new_sensor_state and new_sensor_state.state not in ("unknown", "unavailable"):
            new_sensor_value = float(new_sensor_state.state)
            
            # Ersetze last_energy_readings mit dem ersten Wert des neuen Sensors
            self._last_energy_reading[f"hp{hp_idx}"] = new_sensor_value
            
            _LOGGER.info(f"last_energy_readings für {hp_idx} auf {new_sensor_value} gesetzt (neuer Sensor)")
            
            # Speichere Änderungen in JSON
            await self._persist_counters()
            
        else:
            _LOGGER.warning(f"Neuer Sensor {new_sensor_id} nicht verfügbar, verwende 0")
            self._last_energy_reading[f"hp{hp_idx}"] = 0.0
            
    except Exception as e:
        _LOGGER.error(f"Fehler beim Behandeln des Sensor-Wechsels für {hp_idx}: {e}")
```

### 4. JSON-Struktur-Erweiterung
```json
{
  "heating_cycles": {},
  "heating_energy": {},
  "last_operating_states": {},
  "energy_consumption": {},
  "last_energy_readings": {"hp1": 0.0, "hp2": 10.0, "hp3": 0.0},
  "energy_offsets": {},
  "sensor_ids": {
    "hp1": "sensor.lambda_wp_verbrauch",
    "hp2": "sensor.eu08l_hp2_compressor_power_consumption_accumulated",
    "hp3": "sensor.eu08l_hp3_compressor_power_consumption_accumulated"
  }
}
```

## Vorteile

### 1. Einfachheit
- **Minimaler Code**: Nur wenige Zeilen Code erforderlich
- **Klare Logik**: Einfach zu verstehen und zu warten
- **Keine komplexen Berechnungen**: Keine Notwendigkeit für komplexe Offset-Berechnungen

### 2. Zuverlässigkeit
- **Robust**: Funktioniert für jedes Sensor-Wechsel-Szenario
- **Persistent**: Überlebt Neustarts und Reloads
- **Fehlerbehandlung**: Elegante Behandlung nicht verfügbarer Sensoren

### 3. Leistung
- **Effizient**: Läuft nur beim Konfigurationsladen
- **Keine Laufzeit-Auswirkungen**: Keine Leistungsauswirkungen während des normalen Betriebs
- **Minimaler Speicher**: Keine zusätzliche State-Verwaltung erforderlich

### 4. Benutzerfreundlichkeit
- **Transparent**: Benutzer müssen nichts manuell konfigurieren
- **Automatisch**: Funktioniert automatisch bei Sensor-Änderungen
- **Nahtlos**: Keine Unterbrechung der Energieverbrauchsverfolgung

## Implementierungsplan

### Phase 1: Kernfunktionen
1. **Hilfsfunktionen erstellen** in `utils.py`:
   - `detect_sensor_change()`
   - `get_stored_sensor_id()`
   - `store_sensor_id()`

### Phase 2: Konfigurationsladen
2. **Konfigurationsladen erweitern** in `coordinator.py`:
   - Sensor-Wechsel-Erkennung zu `_load_energy_sensor_configs()` hinzufügen
   - `_handle_sensor_change()`-Methode implementieren

### Phase 3: JSON-Persistierung
3. **JSON-Struktur erweitern**:
   - `sensor_ids`-Sektion zu `cycle_energy_persist.json` hinzufügen
   - `_persist_counters()` und `_load_offsets_and_persisted()` aktualisieren

### Phase 4: Testing
4. **Testszenarien**:
   - Sensor-Wechsel-Erkennung testen
   - Mit nicht verfügbaren Sensoren testen
   - Mit verschiedenen Sensorwerten testen
   - Persistierung über Neustarts testen

### Phase 5: Dokumentation
5. **Dokumentation aktualisieren**:
   - `ENERGY_CONSUMPTION_SENSORS.md` aktualisieren
   - Troubleshooting-Sektion hinzufügen
   - Konfigurationsbeispiele aktualisieren
