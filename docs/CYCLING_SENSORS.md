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
- **Startup Protection**: First 30 seconds after start are ignored
- **Robust Flank Detection**: Only on real status changes
- **Error Handling**: Graceful handling of missing values

### 3. Automations

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

### 4. How the New Architecture Works

#### 4.1. Flank Detection and Incrementation
1. **Flank Detection**: Coordinator detects status changes
2. **Simultaneous Incrementation**: All sensor types are incremented simultaneously
3. **Persistence**: Values are stored in the entities

#### 4.2. Reset Cycles
1. **Daily Reset at Midnight**:
   - Yesterday sensors are set to current daily values
   - Daily sensors are reset to 0

2. **2H Reset Every 2 Hours**:
   - 2H sensors are reset to 0

3. **4H Reset Every 4 Hours**:
   - 4H sensors are reset to 0

#### 4.3. Benefits of the New Architecture
- **Simplicity**: No complex template calculations
- **Robustness**: All sensors are real entities
- **Performance**: No continuous calculations
- **Maintainability**: Clear separation of responsibilities
- **Scalability**: Easy extension with new time periods

### 5. Automatic Creation

#### 5.1. Based on HP Configuration
All cycling sensors are automatically created based on the HP configuration:

```python
# From the config
num_hps = entry.data.get("num_hps", 1)  # e.g. 2 HPs

# Automatic creation for each HP
for hp_idx in range(1, num_hps + 1):  # 1, 2
    for mode, template_id in cycling_modes:  # heating, hot_water, cooling, defrost
        # Creates Total-, Yesterday-, Daily-, 2H- and 4H-sensors
```

#### 5.2. Consistent Naming
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

#### 5.3. Example Output (2 HPs)
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

### 6. Benefits of the Complete Solution

#### 6.1. Robustness
- **Central Flank Detection**: All logic in the coordinator
- **Real Entities**: All sensors are real Python entities
- **Reset-based Logic**: Simple and understandable reset mechanisms
- **Error Handling**: Graceful handling of missing values
- **Timing Protection**: Robust handling of startup sequences

#### 6.2. Performance
- **Efficient Flank Detection**: Only on real status changes
- **No Template Calculations**: All sensors are real entities
- **Minimal Resource Usage**: No continuous polling operations
- **Simultaneous Updates**: All sensors are updated in one operation

#### 6.3. Maintainability
- **Central Definition**: All sensors defined in `const.py`
- **Consistent Naming**: Uses `generate_sensor_names`
- **Clear Separation**: Flank detection, reset logic and entity management are separated
- **Easy Extension**: New time periods can be easily added

#### 6.4. Extensibility
- **New Modes**: Easy extension with new operating modes
- **New Time Periods**: Easy extension with new reset time periods
- **New HPs**: Automatic scaling based on configuration
- **New Features**: Easy integration of new functions

## Conclusion

The new cycling sensor architecture provides a **significantly simplified, robust and performant solution** for tracking operating mode changes. The combination of:

- **Central flank detection** in the coordinator with timing protection
- **Real entities** for all sensor types
- **Reset-based logic** instead of complex template calculations
- **Simultaneous incrementation** of all sensor types
- **Automatic creation** based on HP configuration
- **Consistent naming** with `generate_sensor_names`
- **Robust error handling** for startup sequences

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
- **Startup-Schutz**: Erste 30 Sekunden nach Start werden ignoriert
- **Robuste Flankenerkennung**: Nur bei echten Statuswechseln
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten

### 3. Automatisierungen

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

### 4. Funktionsweise der neuen Architektur

#### 4.1. Flankenerkennung und Inkrementierung
1. **Flankenerkennung**: Coordinator erkennt Statuswechsel
2. **Gleichzeitige Inkrementierung**: Alle Sensor-Typen werden gleichzeitig erhöht
3. **Persistenz**: Werte werden in den Entities gespeichert

#### 4.2. Reset-Zyklen
1. **Daily-Reset um Mitternacht**:
   - Yesterday-Sensoren werden auf aktuelle Daily-Werte gesetzt
   - Daily-Sensoren werden auf 0 zurückgesetzt

2. **2H-Reset alle 2 Stunden**:
   - 2H-Sensoren werden auf 0 zurückgesetzt

3. **4H-Reset alle 4 Stunden**:
   - 4H-Sensoren werden auf 0 zurückgesetzt

#### 4.3. Vorteile der neuen Architektur
- **Einfachheit**: Keine komplexen Template-Berechnungen
- **Robustheit**: Alle Sensoren sind echte Entities
- **Performance**: Keine kontinuierlichen Berechnungen
- **Wartbarkeit**: Klare Trennung der Verantwortlichkeiten
- **Skalierbarkeit**: Einfache Erweiterung um neue Zeiträume

### 5. Automatische Erstellung

#### 5.1. Basierend auf HP-Konfiguration
Alle Cycling-Sensoren werden automatisch basierend auf der HP-Konfiguration erstellt:

```python
# Aus der Config
num_hps = entry.data.get("num_hps", 1)  # z.B. 2 HPs

# Automatische Erstellung für jede HP
for hp_idx in range(1, num_hps + 1):  # 1, 2
    for mode, template_id in cycling_modes:  # heating, hot_water, cooling, defrost
        # Erstellt Total-, Yesterday-, Daily-, 2H- und 4H-Sensoren
```

#### 5.2. Konsistente Namensgebung
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

#### 5.3. Beispiel-Output (2 HPs)
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

### 6. Vorteile der Gesamtlösung

#### 6.1. Robustheit
- **Zentrale Flankenerkennung**: Alle Logik im Coordinator
- **Echte Entities**: Alle Sensoren sind echte Python-Entities
- **Reset-basierte Logik**: Einfache und verständliche Reset-Mechanismen
- **Fehlerbehandlung**: Graceful handling bei fehlenden Werten
- **Timing-Schutz**: Robuste Behandlung von Startup-Sequenzen

#### 6.2. Performance
- **Effiziente Flankenerkennung**: Nur bei echten Statuswechseln
- **Keine Template-Berechnungen**: Alle Sensoren sind echte Entities
- **Minimaler Ressourcenverbrauch**: Keine kontinuierlichen Polling-Operationen
- **Gleichzeitige Updates**: Alle Sensoren werden in einem Vorgang aktualisiert

#### 6.3. Wartbarkeit
- **Zentrale Definition**: Alle Sensoren in `const.py` definiert
- **Konsistente Namensgebung**: Verwendet `generate_sensor_names`
- **Klare Trennung**: Flankenerkennung, Reset-Logik und Entity-Management sind getrennt
- **Einfache Erweiterung**: Neue Zeiträume können einfach hinzugefügt werden

#### 6.4. Erweiterbarkeit
- **Neue Modi**: Einfache Erweiterung um neue Betriebsmodi
- **Neue Zeiträume**: Einfache Erweiterung um neue Reset-Zeiträume
- **Neue HPs**: Automatische Skalierung basierend auf Konfiguration
- **Neue Features**: Einfache Integration neuer Funktionen

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