# Lambda Heat Pumps: Cycling Sensors (Total, Daily, Yesterday, 2H, 4H)

**🇩🇪 [Deutsche Version siehe unten](#deutsche-version)**

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
  - [Sensor Types](#sensor-types)
  - [Flank Detection](#flank-detection)
  - [Automations](#automations)
  - [How the New Architecture Works](#how-the-new-architecture-works)
- [Automatic Creation](#automatic-creation)
- [Benefits of the Complete Solution](#benefits-of-the-complete-solution)
- [Conclusion](#conclusion)

---

## Overview
The cycling sensors are a **simplified and robust solution** for tracking operating mode changes of Lambda heat pumps. They include:

- **Total Sensors**: Total count of all cycling events since installation
- **Daily Sensors**: Daily cycling values (reset to 0 daily at midnight)
- **Yesterday Sensors**: Store yesterday's daily values
- **2H Sensors**: 2-hour cycling values (reset to 0 every 2 hours)
- **4H Sensors**: 4-hour cycling values (reset to 0 every 4 hours)

**New simplified architecture:**
- All sensors are **simultaneously** incremented on each flank detection

Flank detection is performed centrally in the Coordinator for maximum robustness and performance.

## Architecture

### 1. Sensor Types

#### Total Cycling Sensors (Real Entities)
- **Purpose**: Count the total number of cycling events since installation
- **Type**: Real Python entities (`LambdaCyclingSensor`)
- **Persistence**: Values are stored directly in the entities
- **Update**: On each flank detection via `increment_cycling_counter`
- **Examples**: 
  - `sensor.eu08l_hp1_heating_cycling_total`
  - `sensor.eu08l_hp1_hot_water_cycling_total`
  - `sensor.eu08l_hp1_cooling_cycling_total`
  - `sensor.eu08l_hp1_defrost_cycling_total`

#### Yesterday Cycling Sensors (Real Entities)
- **Purpose**: Store yesterday's daily cycling values
- **Type**: Real Python entities (`LambdaYesterdaySensor`)
- **Update**: Set to daily value at midnight (before daily reset)
- **Examples**:
  - `sensor.eu08l_hp1_heating_cycling_yesterday`
  - `sensor.eu08l_hp1_hot_water_cycling_yesterday`
  - `sensor.eu08l_hp1_cooling_cycling_yesterday`
  - `sensor.eu08l_hp1_defrost_cycling_yesterday`

#### Daily Cycling Sensors (Real Entities)
- **Purpose**: Count daily cycling values since midnight
- **Type**: Real Python entities (`LambdaCyclingSensor`)
- **Update**: Incremented on each flank detection, reset to 0 daily at midnight
- **Examples**:
  - `sensor.eu08l_hp1_heating_cycling_daily`
  - `sensor.eu08l_hp1_hot_water_cycling_daily`
  - `sensor.eu08l_hp1_cooling_cycling_daily`
  - `sensor.eu08l_hp1_defrost_cycling_daily`

#### 2H Cycling Sensors (Real Entities)
- **Purpose**: Count 2-hour cycling values
- **Type**: Real Python entities (`LambdaCyclingSensor`)
- **Update**: Incremented on each flank detection, reset to 0 every 2 hours
- **Reset Times**: 00:00, 02:00, 04:00, 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00
- **Examples**:
  - `sensor.eu08l_hp1_heating_cycling_2h`
  - `sensor.eu08l_hp1_hot_water_cycling_2h`
  - `sensor.eu08l_hp1_cooling_cycling_2h`
  - `sensor.eu08l_hp1_defrost_cycling_2h`

#### 4H Cycling Sensors (Real Entities)
- **Purpose**: Count 4-hour cycling values
- **Type**: Real Python entities (`LambdaCyclingSensor`)
- **Update**: Incremented on each flank detection, reset to 0 every 4 hours
- **Reset Times**: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
- **Examples**:
  - `sensor.eu08l_hp1_heating_cycling_4h`
  - `sensor.eu08l_hp1_hot_water_cycling_4h`
  - `sensor.eu08l_hp1_cooling_cycling_4h`
  - `sensor.eu08l_hp1_defrost_cycling_4h`

### 2. Flank Detection

#### Central Flank Detection in Coordinator
Flank detection is performed centrally in the `LambdaDataUpdateCoordinator` for maximum robustness:

```python
# In coordinator.py
def _detect_cycling_flank(self, hp_index: int, old_state: int, new_state: int) -> None:
    """Detect cycling flank and increment all relevant counters."""
    if old_state != new_state and old_state is not None:
        # Increment all sensor types simultaneously
        await increment_cycling_counter(
            self.hass, mode, hp_index, name_prefix, use_legacy_modbus_names, cycling_offsets
        )
```

#### Timing Protection
- **Startup Protection**: `_initialization_complete` flag prevents false flanks during startup
- **Robust Flank Detection**: Only on real status changes with proper state validation
- **Error Handling**: Graceful handling of missing values and invalid states
- **State Persistence**: `_last_operating_state` is persisted and restored on restart

### 3. Automations

#### Flank Detection (Edge Detection)
The cycling sensors use **flank detection** to detect when the heat pump changes operating modes:

**Source Sensor for Flank Detection:**
- **HP1**: `hp1_operating_state` (Register 1003)
- **HP2**: `hp2_operating_state` (Register 1103) 
- **HP3**: `hp3_operating_state` (Register 1203)

**Register Calculation:**
```
HP1 operating_state = 1000 (Base) + 3 (relative_address) = 1003
HP2 operating_state = 1100 (Base) + 3 (relative_address) = 1103
HP3 operating_state = 1200 (Base) + 3 (relative_address) = 1203
```

**Operating State Values (Handled by Cycling Sensors):**
- `1` = CH (Heating) ✅
- `2` = DHW (Hot Water) ✅
- `3` = CC (Cooling) ✅
- `5` = DEFROST (Defrost) ✅

**Other Operating States (Not Handled):**
- `0` = STBY (Standby)
- `4` = CIRCULATE (Circulation)
- `6` = OFF (Off)
- `7` = FROST (Frost)
- `8` = STBY-FROST (Standby-Frost)

**Flank Detection Logic:**
```python
# In coordinator.py
if (self._initialization_complete and 
    last_op_state != "UNBEKANNT" and
    last_op_state != mode_val and 
    op_state_val == mode_val):
    # Increment cycling counter for this mode
```

**Robustness Features:**
- **Startup Protection**: `_initialization_complete` flag prevents false flanks during startup
- **Unknown State Protection**: `last_op_state != "UNBEKANNT"` prevents flanks from unknown states
- **Invalid Value Handling**: Invalid `operating_state` values (like 66) are ignored
- **Timing Protection**: `_last_operating_state` is updated AFTER flank detection

#### Reset-based Logic
The new architecture uses **reset-based logic** instead of update-based logic:

```python
# In automations.py
@callback
def reset_daily_sensors(now: datetime) -> None:
    """Reset daily sensors at midnight and update yesterday sensors."""
    # 1. First set yesterday sensors to current daily values
    _update_yesterday_sensors(hass, entry_id)
    
    # 2. Then reset daily sensors to 0
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY, entry_id)
```

#### Time-based Resets
- **Daily Reset**: Daily at midnight (00:00:00)
- **2H Reset**: Every 2 hours at :00 (00:00, 02:00, 04:00, etc.)
- **4H Reset**: Every 4 hours at :00 (00:00, 04:00, 08:00, etc.)

### 4. Cycling Offsets Configuration

#### 4.1. Purpose of Offsets
Cycling offsets allow you to add a base value to total cycling sensors. This is useful when:
- **Replacing heat pumps**: Add the previous pump's cycle count
- **Resetting counters**: Compensate for manual resets
- **Migration scenarios**: Preserve historical data

#### 4.2. Configuration File
Offsets are configured in `lambda_wp_config.yaml`:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500    # HP1 already had 1500 heating cycles
    hot_water_cycling_total: 800   # HP1 already had 800 hot water cycles
    cooling_cycling_total: 200     # HP1 already had 200 cooling cycles
    defrost_cycling_total: 50      # HP1 already had 50 defrost cycles
  hp2:
    heating_cycling_total: 0       # HP2 starts fresh
    hot_water_cycling_total: 0     # HP2 starts fresh
    cooling_cycling_total: 0       # HP2 starts fresh
    defrost_cycling_total: 0       # HP2 starts fresh
```

#### 4.3. How Offsets Work
1. **At Startup**: Offsets are applied to total sensors when they are initialized
2. **During Operation**: Offsets are added to each increment operation
3. **Only Total Sensors**: Offsets only apply to `*_cycling_total` sensors
4. **Automatic Application**: Offsets are loaded and applied automatically
5. **Offset Tracking**: System tracks applied offsets to prevent double-application
6. **Bidirectional Changes**: Supports both increasing and decreasing offset values

#### 4.4. Offset Application Process
```python
# In sensor.py - LambdaCyclingSensor._apply_cycling_offset()
async def _apply_cycling_offset(self):
    """Apply cycling offset from configuration."""
    # Load offsets from lambda_wp_config.yaml
    config = await load_lambda_config(self.hass)
    cycling_offsets = config.get("cycling_offsets", {})
    
    # Get current and previously applied offsets
    current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
    applied_offset = getattr(self, "_applied_offset", 0)
    
    # Calculate difference to prevent double-application
    offset_difference = current_offset - applied_offset
    
    if offset_difference != 0:
        # Apply only the difference
        self._cycling_value = int(self._cycling_value + offset_difference)
        self._applied_offset = current_offset
```

#### 4.5. Offset Tracking System
The system uses intelligent offset tracking to handle various scenarios:

**Key Features:**
- **`_applied_offset`**: Tracks the currently applied offset value
- **`applied_offset`**: Stored in entity attributes for persistence
- **Difference Calculation**: Only applies the difference between old and new offsets
- **Bidirectional Support**: Handles both increases and decreases

**Example Scenarios:**

**Scenario 1: First Time Application**
```yaml
# Configuration: heating_cycling_total: 30
# Sensor value: 0, applied_offset: 0
# Result: 0 + (30-0) = 30 ✅
```

**Scenario 2: Offset Increase**
```yaml
# Configuration: heating_cycling_total: 50 (was 30)
# Sensor value: 100, applied_offset: 30
# Result: 100 + (50-30) = 120 ✅
```

**Scenario 3: Offset Decrease**
```yaml
# Configuration: heating_cycling_total: 20 (was 30)
# Sensor value: 100, applied_offset: 30
# Result: 100 + (20-30) = 90 ✅
```

**Scenario 4: Offset Removal**
```yaml
# Configuration: heating_cycling_total: 0 (was 30)
# Sensor value: 100, applied_offset: 30
# Result: 100 + (0-30) = 70 ✅
```

#### 4.6. Example Scenarios

**Scenario 1: Heat Pump Replacement**
```yaml
# Old pump had 2500 heating cycles, new pump starts at 0
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    hot_water_cycling_total: 1200
    cooling_cycling_total: 300
    defrost_cycling_total: 80
```

**Scenario 2: Counter Reset**
```yaml
# Manual reset of counters, but want to preserve history
cycling_offsets:
  hp1:
    heating_cycling_total: 5000  # Previous total before reset
    hot_water_cycling_total: 2000
    cooling_cycling_total: 500
    defrost_cycling_total: 150
```

**Scenario 3: Fresh Installation**
```yaml
# New installation, no previous data
cycling_offsets:
  hp1:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
```

### 5. How the New Architecture Works

#### 5.1. Flank Detection and Incrementation
1. **Flank Detection**: Coordinator detects status changes
2. **Simultaneous Incrementation**: All sensor types are incremented simultaneously
3. **Persistence**: Values are stored in the entities

#### 5.2. Reset Cycles
1. **Daily Reset at Midnight**:
   - Yesterday sensors are set to current daily values
   - Daily sensors are reset to 0

2. **2H Reset Every 2 Hours**:
   - 2H sensors are reset to 0

3. **4H Reset Every 4 Hours**:
   - 4H sensors are reset to 0

#### 5.3. Benefits of the New Architecture
- **Simplicity**: No complex template calculations
- **Robustness**: All sensors are real entities
- **Performance**: No continuous calculations
- **Maintainability**: Clear separation of responsibilities
- **Scalability**: Easy extension with new time periods

### 6. Automatic Creation

#### 6.1. Based on HP Configuration
All cycling sensors are automatically created based on the HP configuration:

```python
# From the config
num_hps = entry.data.get("num_hps", 1)  # e.g. 2 HPs

# Automatic creation for each HP
for hp_idx in range(1, num_hps + 1):  # 1, 2
    for mode, template_id in cycling_modes:  # heating, hot_water, cooling, defrost
        # Creates Total-, Yesterday-, Daily-, 2H- and 4H-sensors
```

#### 6.2. Consistent Naming
All sensors use the central `generate_sensor_names` function:

```python
# For all sensor types
names = generate_sensor_names(
    device_prefix,        # "hp1"
    template["name"],     # "Heating Cycling Total"
    template_id,          # "heating_cycling_total"
    name_prefix,          # "eu08l"
    use_legacy_modbus_names  # False
)
```

#### 6.3. Example Output (2 HPs)
**Total Sensors (4 modes × 2 HPs = 8 sensors):**
- `sensor.eu08l_hp1_heating_cycling_total`
- `sensor.eu08l_hp1_hot_water_cycling_total`
- `sensor.eu08l_hp1_cooling_cycling_total`
- `sensor.eu08l_hp1_defrost_cycling_total`
- `sensor.eu08l_hp2_heating_cycling_total`
- `sensor.eu08l_hp2_hot_water_cycling_total`
- `sensor.eu08l_hp2_cooling_cycling_total`
- `sensor.eu08l_hp2_defrost_cycling_total`

**Yesterday Sensors (4 modes × 2 HPs = 8 sensors):**
- `sensor.eu08l_hp1_heating_cycling_yesterday`
- `sensor.eu08l_hp1_hot_water_cycling_yesterday`
- `sensor.eu08l_hp1_cooling_cycling_yesterday`
- `sensor.eu08l_hp1_defrost_cycling_yesterday`
- `sensor.eu08l_hp2_heating_cycling_yesterday`
- `sensor.eu08l_hp2_hot_water_cycling_yesterday`
- `sensor.eu08l_hp2_cooling_cycling_yesterday`
- `sensor.eu08l_hp2_defrost_cycling_yesterday`

**Daily Sensors (4 modes × 2 HPs = 8 sensors):**
- `sensor.eu08l_hp1_heating_cycling_daily`
- `sensor.eu08l_hp1_hot_water_cycling_daily`
- `sensor.eu08l_hp1_cooling_cycling_daily`
- `sensor.eu08l_hp1_defrost_cycling_daily`
- `sensor.eu08l_hp2_heating_cycling_daily`
- `sensor.eu08l_hp2_hot_water_cycling_daily`
- `sensor.eu08l_hp2_cooling_cycling_daily`
- `sensor.eu08l_hp2_defrost_cycling_daily`

**2H Sensors (4 modes × 2 HPs = 8 sensors):**
- `sensor.eu08l_hp1_heating_cycling_2h`
- `sensor.eu08l_hp1_hot_water_cycling_2h`
- `sensor.eu08l_hp1_cooling_cycling_2h`
- `sensor.eu08l_hp1_defrost_cycling_2h`
- `sensor.eu08l_hp2_heating_cycling_2h`
- `sensor.eu08l_hp2_hot_water_cycling_2h`
- `sensor.eu08l_hp2_cooling_cycling_2h`
- `sensor.eu08l_hp2_defrost_cycling_2h`

**4H Sensors (4 modes × 2 HPs = 8 sensors):**
- `sensor.eu08l_hp1_heating_cycling_4h`
- `sensor.eu08l_hp1_hot_water_cycling_4h`
- `sensor.eu08l_hp1_cooling_cycling_4h`
- `sensor.eu08l_hp1_defrost_cycling_4h`
- `sensor.eu08l_hp2_heating_cycling_4h`
- `sensor.eu08l_hp2_hot_water_cycling_4h`
- `sensor.eu08l_hp2_cooling_cycling_4h`
- `sensor.eu08l_hp2_defrost_cycling_4h`

**For 2 HPs, a total of 40 sensors are created (5 types × 4 modes × 2 HPs)**

### 7. Benefits of the Complete Solution

#### 7.1. Robustness
- **Central Flank Detection**: All logic in the coordinator
- **Real Entities**: All sensors are real Python entities
- **Reset-based Logic**: Simple and understandable reset mechanisms
- **Error Handling**: Graceful handling of missing values
- **Timing Protection**: Robust handling of startup sequences
- **Offset Support**: Flexible configuration for different scenarios

#### 7.2. Performance
- **Efficient Flank Detection**: Only on real status changes
- **No Template Calculations**: All sensors are real entities
- **Minimal Resource Usage**: No continuous polling operations
- **Simultaneous Updates**: All sensors are updated in one operation
- **Fast Offset Application**: Offsets applied once at startup

#### 7.3. Maintainability
- **Central Definition**: All sensors defined in `const.py`
- **Consistent Naming**: Uses `generate_sensor_names`
- **Clear Separation**: Flank detection, reset logic and entity management are separated
- **Easy Extension**: New time periods can be easily added
- **Configuration-based Offsets**: Easy to modify without code changes

#### 7.4. Extensibility
- **New Modes**: Easy extension with new operating modes
- **New Time Periods**: Easy extension with new reset time periods
- **New HPs**: Automatic scaling based on configuration
- **New Features**: Easy integration of new functions
- **Flexible Offsets**: Support for various migration scenarios

## Conclusion

The new cycling sensor architecture provides a **significantly simplified, robust and performant solution** for tracking operating mode changes. The combination of:

- **Central flank detection** in the coordinator with timing protection
- **Real entities** for all sensor types
- **Reset-based logic** instead of complex template calculations
- **Simultaneous incrementation** of all sensor types
- **Automatic creation** based on HP configuration
- **Consistent naming** with `generate_sensor_names`
- **Robust error handling** for startup sequences
- **Flexible offset configuration** for various scenarios

---

## German Version / Deutsche Version

**📖 [Jump to German Version](#deutsche-version)**

---

# Lambda Heat Pumps: Cycling Sensoren (Total, Daily, Yesterday, 2H, 4H)

## Inhaltsverzeichnis
- [Übersicht](#übersicht)
- [Architektur](#architektur)
  - [Sensor-Typen](#sensor-typen)
  - [Flankenerkennung](#flankenerkennung)
  - [Automatisierungen](#automatisierungen)
  - [Funktionsweise der neuen Architektur](#funktionsweise-der-neuen-architektur)
- [Automatische Erstellung](#automatische-erstellung)
- [Vorteile der Gesamtlösung](#vorteile-der-gesamtlösung)
- [Fazit](#fazit)

---

## Übersicht
Die Cycling-Sensoren sind eine **vereinfachte und robuste Lösung** zur Verfolgung von Betriebsmodus-Wechseln der Lambda Wärmepumpen. Sie umfassen:

- **Total-Sensoren**: Gesamtanzahl aller Cycling-Ereignisse seit Installation
- **Daily-Sensoren**: Tägliche Cycling-Werte (werden täglich um Mitternacht auf 0 gesetzt)
- **Yesterday-Sensoren**: Speichern die gestern erreichten Daily-Werte
- **2H-Sensoren**: 2-Stunden Cycling-Werte (werden alle 2 Stunden auf 0 gesetzt)
- **4H-Sensoren**: 4-Stunden Cycling-Werte (werden alle 4 Stunden auf 0 gesetzt)

**Neue vereinfachte Architektur:**
- Alle Sensoren werden **gleichzeitig** bei jeder Flankenerkennung erhöht

Die Flankenerkennung erfolgt zentral im Coordinator für maximale Robustheit und Performance.

## Architektur

### 1. Sensor-Typen

#### Total Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die Gesamtanzahl der Cycling-Ereignisse seit Installation
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Persistenz**: Werte werden direkt in den Entities gespeichert
- **Update**: Bei jeder Flankenerkennung durch `increment_cycling_counter`
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_cycling_total`
  - `sensor.eu08l_hp1_hot_water_cycling_total`
  - `sensor.eu08l_hp1_cooling_cycling_total`
  - `sensor.eu08l_hp1_defrost_cycling_total`

#### Yesterday Cycling Sensoren (echte Entities)
- **Zweck**: Speichern die gestern erreichten Daily-Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaYesterdaySensor`)
- **Update**: Täglich um Mitternacht auf Daily-Wert gesetzt (vor Daily-Reset)
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_yesterday`
  - `sensor.eu08l_hp1_hot_water_cycling_yesterday`
  - `sensor.eu08l_hp1_cooling_cycling_yesterday`
  - `sensor.eu08l_hp1_defrost_cycling_yesterday`

#### Daily Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die täglichen Cycling-Werte seit Mitternacht
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, täglich um Mitternacht auf 0 gesetzt
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_daily`
  - `sensor.eu08l_hp1_hot_water_cycling_daily`
  - `sensor.eu08l_hp1_cooling_cycling_daily`
  - `sensor.eu08l_hp1_defrost_cycling_daily`

#### 2H Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die 2-Stunden Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, alle 2 Stunden auf 0 gesetzt
- **Reset-Zeiten**: 00:00, 02:00, 04:00, 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_2h`
  - `sensor.eu08l_hp1_hot_water_cycling_2h`
  - `sensor.eu08l_hp1_cooling_cycling_2h`
  - `sensor.eu08l_hp1_defrost_cycling_2h`

#### 4H Cycling Sensoren (echte Entities)
- **Zweck**: Zählen die 4-Stunden Cycling-Werte
- **Typ**: Echte Python-Entities (`LambdaCyclingSensor`)
- **Update**: Bei jeder Flankenerkennung erhöht, alle 4 Stunden auf 0 gesetzt
- **Reset-Zeiten**: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_cycling_4h`
  - `sensor.eu08l_hp1_hot_water_cycling_4h`
  - `sensor.eu08l_hp1_cooling_cycling_4h`
  - `sensor.eu08l_hp1_defrost_cycling_4h`

### 2. Flankenerkennung

#### Zentrale Flankenerkennung im Coordinator
Die Flankenerkennung erfolgt zentral im `LambdaDataUpdateCoordinator` für maximale Robustheit:

```python
# In coordinator.py
def _detect_cycling_flank(self, hp_index: int, old_state: int, new_state: int) -> None:
    """Detect cycling flank and increment all relevant counters."""
    if old_state != new_state and old_state is not None:
        # Alle Sensor-Typen gleichzeitig erhöhen
            await increment_cycling_counter(
            self.hass, mode, hp_index, name_prefix, use_legacy_modbus_names, cycling_offsets
        )
```

#### Timing-Schutz
- **Startup-Schutz**: `_initialization_complete` Flag verhindert falsche Flanken beim Start
- **Robuste Flankenerkennung**: Nur bei echten Statuswechseln mit korrekter Zustandsvalidierung
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten und ungültigen Zuständen
- **Zustands-Persistierung**: `_last_operating_state` wird persistiert und beim Neustart wiederhergestellt

### 3. Automatisierungen

#### Flankenerkennung (Edge Detection)
Die Cycling-Sensoren verwenden **Flankenerkennung** um zu erkennen, wann die Wärmepumpe den Betriebsmodus wechselt:

**Quell-Sensor für Flankenerkennung:**
- **HP1**: `hp1_operating_state` (Register 1003)
- **HP2**: `hp2_operating_state` (Register 1103) 
- **HP3**: `hp3_operating_state` (Register 1203)

**Register-Berechnung:**
```
HP1 operating_state = 1000 (Base) + 3 (relative_address) = 1003
HP2 operating_state = 1100 (Base) + 3 (relative_address) = 1103
HP3 operating_state = 1200 (Base) + 3 (relative_address) = 1203
```

**Operating State Werte (von Cycling-Sensoren behandelt):**
- `1` = CH (Heizen) ✅
- `2` = DHW (Warmwasser) ✅
- `3` = CC (Kühlen) ✅
- `5` = DEFROST (Abtauen) ✅

**Andere Operating States (nicht behandelt):**
- `0` = STBY (Standby)
- `4` = CIRCULATE (Zirkulation)
- `6` = OFF (Aus)
- `7` = FROST (Frost)
- `8` = STBY-FROST (Standby-Frost)

**Flankenerkennungs-Logik:**
```python
# In coordinator.py
if (self._initialization_complete and 
    last_op_state != "UNBEKANNT" and
    last_op_state != mode_val and 
    op_state_val == mode_val):
    # Cycling-Counter für diesen Modus erhöhen
```

**Robustheits-Features:**
- **Startup-Schutz**: `_initialization_complete` Flag verhindert falsche Flanken beim Start
- **Unbekannter Status-Schutz**: `last_op_state != "UNBEKANNT"` verhindert Flanken von unbekannten Zuständen
- **Ungültige Werte-Behandlung**: Ungültige `operating_state` Werte (wie 66) werden ignoriert
- **Timing-Schutz**: `_last_operating_state` wird NACH der Flankenerkennung aktualisiert

#### Reset-basierte Logik
Die neue Architektur verwendet **Reset-basierte Logik** statt Update-basierte Logik:

```python
# In automations.py
@callback
def reset_daily_sensors(now: datetime) -> None:
    """Reset daily sensors at midnight and update yesterday sensors."""
    # 1. Erst Yesterday-Sensoren auf aktuelle Daily-Werte setzen
    _update_yesterday_sensors(hass, entry_id)
    
    # 2. Dann Daily-Sensoren auf 0 zurücksetzen
    async_dispatcher_send(hass, SIGNAL_RESET_DAILY, entry_id)
```

#### Zeit-basierte Resets
- **Daily-Reset**: Täglich um Mitternacht (00:00:00)
- **2H-Reset**: Alle 2 Stunden um :00 Uhr (00:00, 02:00, 04:00, etc.)
- **4H-Reset**: Alle 4 Stunden um :00 Uhr (00:00, 04:00, 08:00, etc.)

### 4. Cycling-Offsets Konfiguration

#### 4.1. Zweck der Offsets
Cycling-Offsets ermöglichen es, einen Basiswert zu Total-Cycling-Sensoren hinzuzufügen. Dies ist nützlich bei:
- **Wärmepumpen-Austausch**: Zählerstand der vorherigen Pumpe hinzufügen
- **Zähler-Reset**: Manuelle Resets kompensieren
- **Migrations-Szenarien**: Historische Daten erhalten

#### 4.2. Konfigurationsdatei
Offsets werden in `lambda_wp_config.yaml` konfiguriert:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500    # HP1 hatte bereits 1500 Heizzyklen
    hot_water_cycling_total: 800   # HP1 hatte bereits 800 Warmwasserzyklen
    cooling_cycling_total: 200     # HP1 hatte bereits 200 Kühlzyklen
    defrost_cycling_total: 50      # HP1 hatte bereits 50 Abtauzyklen
  hp2:
    heating_cycling_total: 0       # HP2 startet frisch
    hot_water_cycling_total: 0     # HP2 startet frisch
    cooling_cycling_total: 0       # HP2 startet frisch
    defrost_cycling_total: 0       # HP2 startet frisch
```

#### 4.3. Funktionsweise der Offsets
1. **Beim Start**: Offsets werden auf Total-Sensoren angewendet, wenn sie initialisiert werden
2. **Während des Betriebs**: Offsets werden zu jeder Inkrementierung hinzugefügt
3. **Nur Total-Sensoren**: Offsets gelten nur für `*_cycling_total` Sensoren
4. **Automatische Anwendung**: Offsets werden automatisch geladen und angewendet
5. **Offset-Tracking**: System verfolgt angewendete Offsets, um Doppelanwendung zu verhindern
6. **Bidirektionale Änderungen**: Unterstützt sowohl Erhöhung als auch Verringerung von Offset-Werten

#### 4.4. Offset-Anwendungsprozess
```python
# In sensor.py - LambdaCyclingSensor._apply_cycling_offset()
async def _apply_cycling_offset(self):
    """Apply cycling offset from configuration."""
    # Lade Offsets aus lambda_wp_config.yaml
    config = await load_lambda_config(self.hass)
    cycling_offsets = config.get("cycling_offsets", {})
    
    # Hole aktuelle und bereits angewendete Offsets
    current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
    applied_offset = getattr(self, "_applied_offset", 0)
    
    # Berechne Differenz, um Doppelanwendung zu verhindern
    offset_difference = current_offset - applied_offset
    
    if offset_difference != 0:
        # Wende nur die Differenz an
        self._cycling_value = int(self._cycling_value + offset_difference)
        self._applied_offset = current_offset
```

#### 4.5. Offset-Tracking-System
Das System verwendet intelligentes Offset-Tracking für verschiedene Szenarien:

**Wichtige Funktionen:**
- **`_applied_offset`**: Verfolgt den aktuell angewendeten Offset-Wert
- **`applied_offset`**: Wird in Entity-Attributen für Persistenz gespeichert
- **Differenz-Berechnung**: Wendet nur die Differenz zwischen alten und neuen Offsets an
- **Bidirektionale Unterstützung**: Behandelt sowohl Erhöhungen als auch Verringerungen

**Beispiel-Szenarien:**

**Szenario 1: Erste Anwendung**
```yaml
# Konfiguration: heating_cycling_total: 30
# Sensor-Wert: 0, applied_offset: 0
# Ergebnis: 0 + (30-0) = 30 ✅
```

**Szenario 2: Offset-Erhöhung**
```yaml
# Konfiguration: heating_cycling_total: 50 (war 30)
# Sensor-Wert: 100, applied_offset: 30
# Ergebnis: 100 + (50-30) = 120 ✅
```

**Szenario 3: Offset-Verringerung**
```yaml
# Konfiguration: heating_cycling_total: 20 (war 30)
# Sensor-Wert: 100, applied_offset: 30
# Ergebnis: 100 + (20-30) = 90 ✅
```

**Szenario 4: Offset-Entfernung**
```yaml
# Konfiguration: heating_cycling_total: 0 (war 30)
# Sensor-Wert: 100, applied_offset: 30
# Ergebnis: 100 + (0-30) = 70 ✅
```

#### 4.6. Beispiel-Szenarien

**Szenario 1: Wärmepumpen-Austausch**
```yaml
# Alte Pumpe hatte 2500 Heizzyklen, neue Pumpe startet bei 0
cycling_offsets:
  hp1:
    heating_cycling_total: 2500
    hot_water_cycling_total: 1200
    cooling_cycling_total: 300
    defrost_cycling_total: 80
```

**Szenario 2: Zähler-Reset**
```yaml
# Manueller Reset der Zähler, aber Historie erhalten
cycling_offsets:
  hp1:
    heating_cycling_total: 5000  # Vorheriger Gesamtwert vor Reset
    hot_water_cycling_total: 2000
    cooling_cycling_total: 500
    defrost_cycling_total: 150
```

**Szenario 3: Neue Installation**
```yaml
# Neue Installation, keine vorherigen Daten
cycling_offsets:
  hp1:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
```

### 5. Funktionsweise der neuen Architektur

#### 5.1. Flankenerkennung und Inkrementierung
1. **Flankenerkennung**: Coordinator erkennt Statuswechsel
2. **Gleichzeitige Inkrementierung**: Alle Sensor-Typen werden gleichzeitig erhöht
3. **Persistenz**: Werte werden in den Entities gespeichert

#### 5.2. Reset-Zyklen
1. **Daily-Reset um Mitternacht**:
   - Yesterday-Sensoren werden auf aktuelle Daily-Werte gesetzt
   - Daily-Sensoren werden auf 0 zurückgesetzt

2. **2H-Reset alle 2 Stunden**:
   - 2H-Sensoren werden auf 0 zurückgesetzt

3. **4H-Reset alle 4 Stunden**:
   - 4H-Sensoren werden auf 0 zurückgesetzt

#### 5.3. Vorteile der neuen Architektur
- **Einfachheit**: Keine komplexen Template-Berechnungen
- **Robustheit**: Alle Sensoren sind echte Entities
- **Performance**: Keine kontinuierlichen Berechnungen
- **Wartbarkeit**: Klare Trennung der Verantwortlichkeiten
- **Skalierbarkeit**: Einfache Erweiterung um neue Zeiträume

### 6. Automatische Erstellung

#### 6.1. Basierend auf HP-Konfiguration
Alle Cycling-Sensoren werden automatisch basierend auf der HP-Konfiguration erstellt:

```python
# Aus der Config
num_hps = entry.data.get("num_hps", 1)  # z.B. 2 HPs

# Automatische Erstellung für jede HP
for hp_idx in range(1, num_hps + 1):  # 1, 2
    for mode, template_id in cycling_modes:  # heating, hot_water, cooling, defrost
        # Erstellt Total-, Yesterday-, Daily-, 2H- und 4H-Sensoren
```

#### 6.2. Konsistente Namensgebung
Alle Sensoren verwenden die zentrale `generate_sensor_names` Funktion:

```python
# Für alle Sensor-Typen
names = generate_sensor_names(
    device_prefix,        # "hp1"
    template["name"],     # "Heating Cycling Total"
    template_id,          # "heating_cycling_total"
    name_prefix,          # "eu08l"
    use_legacy_modbus_names  # False
)
```

#### 6.3. Beispiel-Output (2 HPs)
**Total-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_total`
- `sensor.eu08l_hp1_hot_water_cycling_total`
- `sensor.eu08l_hp1_cooling_cycling_total`
- `sensor.eu08l_hp1_defrost_cycling_total`
- `sensor.eu08l_hp2_heating_cycling_total`
- `sensor.eu08l_hp2_hot_water_cycling_total`
- `sensor.eu08l_hp2_cooling_cycling_total`
- `sensor.eu08l_hp2_defrost_cycling_total`

**Yesterday-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_yesterday`
- `sensor.eu08l_hp1_hot_water_cycling_yesterday`
- `sensor.eu08l_hp1_cooling_cycling_yesterday`
- `sensor.eu08l_hp1_defrost_cycling_yesterday`
- `sensor.eu08l_hp2_heating_cycling_yesterday`
- `sensor.eu08l_hp2_hot_water_cycling_yesterday`
- `sensor.eu08l_hp2_cooling_cycling_yesterday`
- `sensor.eu08l_hp2_defrost_cycling_yesterday`

**Daily-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_daily`
- `sensor.eu08l_hp1_hot_water_cycling_daily`
- `sensor.eu08l_hp1_cooling_cycling_daily`
- `sensor.eu08l_hp1_defrost_cycling_daily`
- `sensor.eu08l_hp2_heating_cycling_daily`
- `sensor.eu08l_hp2_hot_water_cycling_daily`
- `sensor.eu08l_hp2_cooling_cycling_daily`
- `sensor.eu08l_hp2_defrost_cycling_daily`

**2H-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_2h`
- `sensor.eu08l_hp1_hot_water_cycling_2h`
- `sensor.eu08l_hp1_cooling_cycling_2h`
- `sensor.eu08l_hp1_defrost_cycling_2h`
- `sensor.eu08l_hp2_heating_cycling_2h`
- `sensor.eu08l_hp2_hot_water_cycling_2h`
- `sensor.eu08l_hp2_cooling_cycling_2h`
- `sensor.eu08l_hp2_defrost_cycling_2h`

**4H-Sensoren (4 Modi × 2 HPs = 8 Sensoren):**
- `sensor.eu08l_hp1_heating_cycling_4h`
- `sensor.eu08l_hp1_hot_water_cycling_4h`
- `sensor.eu08l_hp1_cooling_cycling_4h`
- `sensor.eu08l_hp1_defrost_cycling_4h`
- `sensor.eu08l_hp2_heating_cycling_4h`
- `sensor.eu08l_hp2_hot_water_cycling_4h`
- `sensor.eu08l_hp2_cooling_cycling_4h`
- `sensor.eu08l_hp2_defrost_cycling_4h`

**Für 2 HPs werden insgesamt 40 Sensoren erstellt (5 Typen × 4 Modi × 2 HPs)**

### 7. Vorteile der Gesamtlösung

#### 7.1. Robustheit
- **Zentrale Flankenerkennung**: Alle Logik im Coordinator
- **Echte Entities**: Alle Sensoren sind echte Python-Entities
- **Reset-basierte Logik**: Einfache und verständliche Reset-Mechanismen
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten
- **Timing-Schutz**: Robuste Behandlung von Startup-Sequenzen
- **Offset-Unterstützung**: Flexible Konfiguration für verschiedene Szenarien

#### 7.2. Performance
- **Effiziente Flankenerkennung**: Nur bei echten Statuswechseln
- **Keine Template-Berechnungen**: Alle Sensoren sind echte Entities
- **Minimaler Ressourcenverbrauch**: Keine kontinuierlichen Polling-Operationen
- **Gleichzeitige Updates**: Alle Sensoren werden in einem Vorgang aktualisiert
- **Schnelle Offset-Anwendung**: Offsets werden einmal beim Start angewendet

#### 7.3. Wartbarkeit
- **Zentrale Definition**: Alle Sensoren in `const.py` definiert
- **Konsistente Namensgebung**: Verwendet `generate_sensor_names`
- **Klare Trennung**: Flankenerkennung, Reset-Logik und Entity-Management sind getrennt
- **Einfache Erweiterung**: Neue Zeiträume können einfach hinzugefügt werden
- **Konfigurations-basierte Offsets**: Einfache Änderung ohne Code-Änderungen

#### 7.4. Erweiterbarkeit
- **Neue Modi**: Einfache Erweiterung um neue Betriebsmodi
- **Neue Zeiträume**: Einfache Erweiterung um neue Reset-Zeiträume
- **Neue HPs**: Automatische Skalierung basierend auf Konfiguration
- **Neue Features**: Einfache Integration neuer Funktionen
- **Flexible Offsets**: Unterstützung für verschiedene Migrations-Szenarien

## Fazit

Die neue Cycling-Sensor-Architektur bietet eine **deutlich vereinfachte, robuste und performante Lösung** für die Verfolgung von Betriebsmodus-Wechseln. Die Kombination aus:

- **Zentraler Flankenerkennung** im Coordinator mit Timing-Schutz
- **Echten Entities** für alle Sensor-Typen
- **Reset-basierter Logik** statt komplexer Template-Berechnungen
- **Gleichzeitiger Inkrementierung** aller Sensor-Typen
- **Automatischer Erstellung** basierend auf HP-Konfiguration
- **Konsistenter Namensgebung** mit `generate_sensor_names`
- **Robuster Fehlerbehandlung** für Startup-Sequenzen

---

**📖 [Back to English Version](#overview)**