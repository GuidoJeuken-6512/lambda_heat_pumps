# Lambda Heat Pumps: Energy Consumption Sensors nach Betriebsart

**🇩🇪 [Deutsche Version siehe unten](#deutsche-version)**

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
  - [Sensor Types](#sensor-types)
  - [Energy Tracking](#energy-tracking)
  - [Configuration](#configuration)
  - [Migration](#migration)
- [Sensor Examples](#sensor-examples)
- [Configuration Examples](#configuration-examples)
- [Benefits](#benefits)
- [Technical Implementation Details](#technical-implementation-details)

---

## Overview

The Energy Consumption Sensors provide **detailed energy tracking by operating mode** for Lambda heat pumps. They track energy consumption separately for each operating mode:

- **Heating Mode (CH)**: Energy consumed during heating operations
- **Hot Water Mode (DHW)**: Energy consumed during hot water heating
- **Cooling Mode (CC)**: Energy consumed during cooling operations  
- **Defrost Mode (DEFROST)**: Energy consumed during defrost cycles

**Key Features:**
- **Total Sensors**: Cumulative energy consumption since installation
- **Daily Sensors**: Daily energy consumption (reset to 0 daily at midnight)
- **Monthly Sensors**: Monthly energy consumption (reset to 0 on 1st of each month)
- **Yearly Sensors**: Yearly energy consumption (reset to 0 on January 1st)
- **Flank Detection**: Automatic energy allocation based on operating mode changes
- **Offset Support**: Support for energy offsets when replacing heat pumps
- **Configurable Input**: Uses existing power consumption sensors as data source

## Architecture

### 1. Sensor Types

#### Total Energy Consumption Sensors (Real Entities)
- **Purpose**: Track total energy consumption per operating mode since installation
- **Type**: Real Python entities (`LambdaEnergyConsumptionSensor`)
- **Persistence**: Values are stored directly in the entities
- **Update**: On operating mode changes via `increment_energy_consumption_counter`
- **Examples**: 
  - `sensor.eu08l_hp1_heating_energy_total`
  - `sensor.eu08l_hp1_hot_water_energy_total`
  - `sensor.eu08l_hp1_cooling_energy_total`
  - `sensor.eu08l_hp1_defrost_energy_total`

#### Daily Energy Consumption Sensors (Real Entities)
- **Purpose**: Track daily energy consumption per operating mode
- **Type**: Real Python entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Daily at midnight (calculated as Total - Yesterday)
- **Examples**:
  - `sensor.eu08l_hp1_heating_energy_daily`
  - `sensor.eu08l_hp1_hot_water_energy_daily`
  - `sensor.eu08l_hp1_cooling_energy_daily`
  - `sensor.eu08l_hp1_defrost_energy_daily`

#### Monthly Energy Consumption Sensors (Real Entities)
- **Purpose**: Track monthly energy consumption per operating mode
- **Type**: Real Python entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Monthly on 1st of each month (calculated as Total - Previous Monthly)
- **Examples**:
  - `sensor.eu08l_hp1_heating_energy_monthly`
  - `sensor.eu08l_hp1_hot_water_energy_monthly`
  - `sensor.eu08l_hp1_cooling_energy_monthly`
  - `sensor.eu08l_hp1_defrost_energy_monthly`

#### Yearly Energy Consumption Sensors (Real Entities)
- **Purpose**: Track yearly energy consumption per operating mode
- **Type**: Real Python entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Yearly on January 1st (calculated as Total - Previous Yearly)
- **Examples**:
  - `sensor.eu08l_hp1_heating_energy_yearly`
  - `sensor.eu08l_hp1_hot_water_energy_yearly`
  - `sensor.eu08l_hp1_cooling_energy_yearly`
  - `sensor.eu08l_hp1_defrost_energy_yearly`

### 2. Energy Tracking

#### Flank Detection Logic
1. **Monitor Operating State**: Track changes in heat pump operating mode
2. **Calculate Energy Delta**: Measure energy consumption during each mode
3. **Allocate Energy**: Distribute consumed energy to appropriate mode sensors
4. **Update Counters**: Increment total, daily, monthly, and yearly sensors simultaneously

#### Energy Calculation
```python
# Energy delta calculation with overflow protection
energy_delta = calculate_energy_delta(
    current_reading=current_kwh,
    last_reading=last_kwh,
    max_delta=100.0  # Maximum allowed delta (kWh)
)
```

#### Input Sensor Configuration
- **Source**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- **Unit**: kWh (converted from Wh)
- **Update Frequency**: Every 30 seconds (coordinator update interval)

### 3. Configuration

#### lambda_wp_config.yaml Structure
```yaml
# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

# Energy consumption offsets for total sensors
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0       # kWh offset for HP1 heating total
    hot_water_energy_total: 0     # kWh offset for HP1 hot water total
    cooling_energy_total: 0       # kWh offset for HP1 cooling total
    defrost_energy_total: 0       # kWh offset for HP1 defrost total
  hp2:
    heating_energy_total: 150.5   # Example: HP2 already consumed 150.5 kWh heating
    hot_water_energy_total: 45.2  # Example: HP2 already consumed 45.2 kWh hot water
    cooling_energy_total: 12.8    # Example: HP2 already consumed 12.8 kWh cooling
    defrost_energy_total: 3.1     # Example: HP2 already consumed 3.1 kWh defrost
```

### 4. Migration

#### Automatic Migration (Version 4)
The integration automatically migrates existing installations to include energy consumption sensors:

1. **Config Update**: Adds `energy_consumption_sensors` and `energy_consumption_offsets` sections (optional)
2. **Sensor Creation**: Creates all energy consumption sensors for configured heat pumps
3. **Offset Application**: Applies configured offsets to total sensors via `load_lambda_config`
4. **Backward Compatibility**: Maintains existing cycling sensor functionality

**Note**: The `energy_consumption_sensors` and `energy_consumption_offsets` sections are optional. If not configured, the system uses default power consumption sensors and zero offsets.

## Sensor Examples

### For 1 Heat Pump (20 Sensors)
```
sensor.eu08l_hp1_heating_energy_total      # Total heating energy (kWh)
sensor.eu08l_hp1_heating_energy_daily      # Daily heating energy (kWh)
sensor.eu08l_hp1_heating_energy_monthly    # Monthly heating energy (kWh)
sensor.eu08l_hp1_heating_energy_yearly     # Yearly heating energy (kWh)
sensor.eu08l_hp1_hot_water_energy_total    # Total hot water energy (kWh)
sensor.eu08l_hp1_hot_water_energy_daily    # Daily hot water energy (kWh)
sensor.eu08l_hp1_hot_water_energy_monthly  # Monthly hot water energy (kWh)
sensor.eu08l_hp1_hot_water_energy_yearly   # Yearly hot water energy (kWh)
sensor.eu08l_hp1_cooling_energy_total      # Total cooling energy (kWh)
sensor.eu08l_hp1_cooling_energy_daily      # Daily cooling energy (kWh)
sensor.eu08l_hp1_cooling_energy_monthly    # Monthly cooling energy (kWh)
sensor.eu08l_hp1_cooling_energy_yearly     # Yearly cooling energy (kWh)
sensor.eu08l_hp1_defrost_energy_total      # Total defrost energy (kWh)
sensor.eu08l_hp1_defrost_energy_daily      # Daily defrost energy (kWh)
sensor.eu08l_hp1_defrost_energy_monthly    # Monthly defrost energy (kWh)
sensor.eu08l_hp1_defrost_energy_yearly     # Yearly defrost energy (kWh)
sensor.eu08l_hp1_stby_energy_total         # Total standby energy (kWh)
sensor.eu08l_hp1_stby_energy_daily         # Daily standby energy (kWh)
sensor.eu08l_hp1_stby_energy_monthly       # Monthly standby energy (kWh)
sensor.eu08l_hp1_stby_energy_yearly        # Yearly standby energy (kWh)
```

### For 2 Heat Pumps (40 Sensors)
```
# HP1 Sensors (20)
sensor.eu08l_hp1_heating_energy_total
sensor.eu08l_hp1_heating_energy_daily
sensor.eu08l_hp1_heating_energy_monthly
sensor.eu08l_hp1_heating_energy_yearly
# ... (16 more)

# HP2 Sensors (20)
sensor.eu08l_hp2_heating_energy_total
sensor.eu08l_hp2_heating_energy_daily
sensor.eu08l_hp2_heating_energy_monthly
sensor.eu08l_hp2_heating_energy_yearly
# ... (16 more)
```

## Configuration Examples

### Basic Configuration
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"

energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    hot_water_energy_total: 0
    cooling_energy_total: 0
    defrost_energy_total: 0
```

### Multi-Heat Pump Configuration
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    hot_water_energy_total: 0
    cooling_energy_total: 0
    defrost_energy_total: 0
  hp2:
    heating_energy_total: 150.5
    hot_water_energy_total: 45.2
    cooling_energy_total: 12.8
    defrost_energy_total: 3.1
```

### Custom Input Sensor
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.my_custom_power_sensor"
```

## Benefits

### 1. Detailed Energy Analysis
- **Mode-Specific Tracking**: See exactly how much energy each operating mode consumes
- **Daily Monitoring**: Track daily energy consumption patterns
- **Monthly Analysis**: Monitor monthly energy consumption trends
- **Yearly Overview**: Track yearly energy consumption and efficiency
- **Historical Data**: Maintain total consumption history

### 2. System Optimization
- **Efficiency Analysis**: Compare energy consumption between different modes
- **Usage Patterns**: Identify peak consumption periods
- **Maintenance Planning**: Use energy data for predictive maintenance

### 3. Integration Benefits
- **Home Assistant Integration**: Full integration with HA's energy management
- **Automation Support**: Use energy data in automations and scripts
- **Dashboard Integration**: Display energy consumption in custom dashboards

### 4. Reliability Features
- **Overflow Protection**: Handles sensor value overflows gracefully
- **Offset Support**: Easy migration when replacing heat pumps
- **Error Handling**: Robust error handling and logging

## Technical Implementation Details

### Sensor Attributes
Each energy consumption sensor includes helpful attributes:
- `sensor_type`: "energy_consumption"
- `mode`: Operating mode (heating, hot_water, cooling, defrost, stby)
- `reset_interval`: Time period (total, daily, monthly, yearly)
- `hp_index`: Heat pump index
- `applied_offset`: Applied offset value (total sensors only)
- `yesterday_value`: Previous daily value (daily sensors only)
- `previous_monthly_value`: Previous monthly value (monthly sensors only)
- `previous_yearly_value`: Previous yearly value (yearly sensors only)

### Implementation Details
- **Offset Loading**: Offsets are loaded via `load_lambda_config()` function from `lambda_wp_config.yaml`
- **Offset Application**: Applied in `_apply_energy_offset()` method during sensor initialization
- **Entity Registration**: Energy consumption entities are registered in `hass.data["lambda_heat_pumps"][entry_id]["energy_entities"]`
- **State Persistence**: Uses `RestoreEntity` for state persistence across restarts
- **Unit Conversion**: Automatic conversion from Wh to kWh via `convert_energy_to_kwh()` function

---

## Deutsche Version

# Lambda Heat Pumps: Energieverbrauchs-Sensoren nach Betriebsart

## Übersicht

Die Energieverbrauchs-Sensoren bieten **detailliertes Energietracking nach Betriebsart** für Lambda-Wärmepumpen. Sie verfolgen den Energieverbrauch getrennt für jeden Betriebsmodus:

- **Heizmodus (CH)**: Energieverbrauch während Heizbetrieb
- **Warmwasser-Modus (DHW)**: Energieverbrauch während Warmwassererwärmung
- **Kühlmodus (CC)**: Energieverbrauch während Kühlbetrieb
- **Abtau-Modus (DEFROST)**: Energieverbrauch während Abtauzyklen

**Hauptfunktionen:**
- **Total-Sensoren**: Kumulativer Energieverbrauch seit Installation
- **Tages-Sensoren**: Täglicher Energieverbrauch (täglich um Mitternacht auf 0 zurückgesetzt)
- **Monatliche Sensoren**: Monatlicher Energieverbrauch (monatlich am 1. auf 0 zurückgesetzt)
- **Jährliche Sensoren**: Jährlicher Energieverbrauch (jährlich am 1. Januar auf 0 zurückgesetzt)
- **Flankenerkennung**: Automatische Energiezuordnung basierend auf Betriebsart-Änderungen
- **Offset-Unterstützung**: Unterstützung für Energie-Offsets beim Wärmepumpen-Austausch
- **Konfigurierbare Eingabe**: Verwendet bestehende Stromverbrauchs-Sensoren als Datenquelle

## Architektur

### 1. Sensor-Typen

#### Total Energieverbrauchs-Sensoren (Echte Entities)
- **Zweck**: Verfolgung des Gesamtenergieverbrauchs pro Betriebsart seit Installation
- **Typ**: Echte Python-Entities (`LambdaEnergyConsumptionSensor`)
- **Persistierung**: Werte werden direkt in den Entities gespeichert
- **Update**: Bei Betriebsart-Änderungen über `increment_energy_consumption_counter`
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_energy_total`
  - `sensor.eu08l_hp1_hot_water_energy_total`
  - `sensor.eu08l_hp1_cooling_energy_total`
  - `sensor.eu08l_hp1_defrost_energy_total`

#### Tages Energieverbrauchs-Sensoren (Echte Entities)
- **Zweck**: Verfolgung des täglichen Energieverbrauchs pro Betriebsart
- **Typ**: Echte Python-Entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Täglich um Mitternacht (berechnet als Total - Gestern)
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_energy_daily`
  - `sensor.eu08l_hp1_hot_water_energy_daily`
  - `sensor.eu08l_hp1_cooling_energy_daily`
  - `sensor.eu08l_hp1_defrost_energy_daily`

#### Monatliche Energieverbrauchs-Sensoren (Echte Entities)
- **Zweck**: Verfolgung des monatlichen Energieverbrauchs pro Betriebsart
- **Typ**: Echte Python-Entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Monatlich am 1. des Monats (berechnet als Total - Vorheriger Monat)
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_energy_monthly`
  - `sensor.eu08l_hp1_hot_water_energy_monthly`
  - `sensor.eu08l_hp1_cooling_energy_monthly`
  - `sensor.eu08l_hp1_defrost_energy_monthly`

#### Jährliche Energieverbrauchs-Sensoren (Echte Entities)
- **Zweck**: Verfolgung des jährlichen Energieverbrauchs pro Betriebsart
- **Typ**: Echte Python-Entities (`LambdaEnergyConsumptionSensor`)
- **Reset**: Jährlich am 1. Januar (berechnet als Total - Vorheriges Jahr)
- **Beispiele**:
  - `sensor.eu08l_hp1_heating_energy_yearly`
  - `sensor.eu08l_hp1_hot_water_energy_yearly`
  - `sensor.eu08l_hp1_cooling_energy_yearly`
  - `sensor.eu08l_hp1_defrost_energy_yearly`

### 2. Energie-Tracking

#### Flankenerkennungs-Logik
1. **Betriebszustand überwachen**: Änderungen im Wärmepumpen-Betriebsmodus verfolgen
2. **Energie-Delta berechnen**: Energieverbrauch während jedes Modus messen
3. **Energie zuordnen**: Verbrauchte Energie den entsprechenden Modus-Sensoren zuweisen
4. **Zähler aktualisieren**: Total-, Tages-, Monatliche und Jährliche Sensoren gleichzeitig erhöhen

#### Energie-Berechnung
```python
# Energie-Delta-Berechnung mit Überlauf-Schutz
energy_delta = calculate_energy_delta(
    current_reading=current_kwh,
    last_reading=last_kwh,
    max_delta=100.0  # Maximal erlaubtes Delta (kWh)
)
```

#### Eingabe-Sensor-Konfiguration
- **Quelle**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- **Einheit**: kWh (von Wh konvertiert)
- **Update-Frequenz**: Alle 30 Sekunden (Coordinator-Update-Intervall)

### 3. Konfiguration

#### lambda_wp_config.yaml Struktur
```yaml
# Energieverbrauchs-Sensor-Konfiguration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

# Energieverbrauchs-Offsets für Total-Sensoren
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0       # kWh Offset für HP1 Heizung Total
    hot_water_energy_total: 0     # kWh Offset für HP1 Warmwasser Total
    cooling_energy_total: 0       # kWh Offset für HP1 Kühlung Total
    defrost_energy_total: 0       # kWh Offset für HP1 Abtau Total
  hp2:
    heating_energy_total: 150.5   # Beispiel: HP2 hat bereits 150.5 kWh Heizung verbraucht
    hot_water_energy_total: 45.2  # Beispiel: HP2 hat bereits 45.2 kWh Warmwasser verbraucht
    cooling_energy_total: 12.8    # Beispiel: HP2 hat bereits 12.8 kWh Kühlung verbraucht
    defrost_energy_total: 3.1     # Beispiel: HP2 hat bereits 3.1 kWh Abtau verbraucht
```

### 4. Migration

#### Automatische Migration (Version 4)
Die Integration migriert automatisch bestehende Installationen, um Energieverbrauchs-Sensoren einzuschließen:

1. **Config-Update**: Fügt `energy_consumption_sensors` und `energy_consumption_offsets` Sektionen hinzu (optional)
2. **Sensor-Erstellung**: Erstellt alle Energieverbrauchs-Sensoren für konfigurierte Wärmepumpen
3. **Offset-Anwendung**: Wendet konfigurierte Offsets auf Total-Sensoren über `load_lambda_config` an
4. **Rückwärtskompatibilität**: Behält bestehende Cycling-Sensor-Funktionalität bei

**Hinweis**: Die Sektionen `energy_consumption_sensors` und `energy_consumption_offsets` sind optional. Wenn nicht konfiguriert, verwendet das System Standard-Stromverbrauchs-Sensoren und Null-Offsets.

## Sensor-Beispiele

### Für 1 Wärmepumpe (20 Sensoren)
```
sensor.eu08l_hp1_heating_energy_total      # Gesamte Heizenergie (kWh)
sensor.eu08l_hp1_heating_energy_daily      # Tägliche Heizenergie (kWh)
sensor.eu08l_hp1_heating_energy_monthly    # Monatliche Heizenergie (kWh)
sensor.eu08l_hp1_heating_energy_yearly     # Jährliche Heizenergie (kWh)
sensor.eu08l_hp1_hot_water_energy_total    # Gesamte Warmwasserenergie (kWh)
sensor.eu08l_hp1_hot_water_energy_daily    # Tägliche Warmwasserenergie (kWh)
sensor.eu08l_hp1_hot_water_energy_monthly  # Monatliche Warmwasserenergie (kWh)
sensor.eu08l_hp1_hot_water_energy_yearly   # Jährliche Warmwasserenergie (kWh)
sensor.eu08l_hp1_cooling_energy_total      # Gesamte Kühlenergie (kWh)
sensor.eu08l_hp1_cooling_energy_daily      # Tägliche Kühlenergie (kWh)
sensor.eu08l_hp1_cooling_energy_monthly    # Monatliche Kühlenergie (kWh)
sensor.eu08l_hp1_cooling_energy_yearly     # Jährliche Kühlenergie (kWh)
sensor.eu08l_hp1_defrost_energy_total      # Gesamte Abtauenergie (kWh)
sensor.eu08l_hp1_defrost_energy_daily      # Tägliche Abtauenergie (kWh)
sensor.eu08l_hp1_defrost_energy_monthly    # Monatliche Abtauenergie (kWh)
sensor.eu08l_hp1_defrost_energy_yearly     # Jährliche Abtauenergie (kWh)
sensor.eu08l_hp1_stby_energy_total         # Gesamte Standby-Energie (kWh)
sensor.eu08l_hp1_stby_energy_daily         # Tägliche Standby-Energie (kWh)
sensor.eu08l_hp1_stby_energy_monthly       # Monatliche Standby-Energie (kWh)
sensor.eu08l_hp1_stby_energy_yearly        # Jährliche Standby-Energie (kWh)
```

### Für 2 Wärmepumpen (40 Sensoren)
```
# HP1 Sensoren (20)
sensor.eu08l_hp1_heating_energy_total
sensor.eu08l_hp1_heating_energy_daily
sensor.eu08l_hp1_heating_energy_monthly
sensor.eu08l_hp1_heating_energy_yearly
# ... (16 weitere)

# HP2 Sensoren (20)
sensor.eu08l_hp2_heating_energy_total
sensor.eu08l_hp2_heating_energy_daily
sensor.eu08l_hp2_heating_energy_monthly
sensor.eu08l_hp2_heating_energy_yearly
# ... (16 weitere)
```

## Konfigurations-Beispiele

### Grundkonfiguration
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"

energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    hot_water_energy_total: 0
    cooling_energy_total: 0
    defrost_energy_total: 0
```

### Multi-Wärmepumpen-Konfiguration
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

energy_consumption_offsets:
  hp1:
    heating_energy_total: 0
    hot_water_energy_total: 0
    cooling_energy_total: 0
    defrost_energy_total: 0
  hp2:
    heating_energy_total: 150.5
    hot_water_energy_total: 45.2
    cooling_energy_total: 12.8
    defrost_energy_total: 3.1
```

### Benutzerdefinierter Eingabe-Sensor
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.my_custom_power_sensor"
```

## Vorteile

### 1. Detaillierte Energieanalyse
- **Modus-spezifisches Tracking**: Sehen Sie genau, wie viel Energie jeder Betriebsmodus verbraucht
- **Tägliche Überwachung**: Verfolgen Sie tägliche Energieverbrauchsmuster
- **Monatliche Analyse**: Überwachen Sie monatliche Energieverbrauchstrends
- **Jährliche Übersicht**: Verfolgen Sie jährlichen Energieverbrauch und Effizienz
- **Historische Daten**: Behalten Sie Gesamtverbrauchshistorie bei

### 2. Systemoptimierung
- **Effizienzanalyse**: Vergleichen Sie Energieverbrauch zwischen verschiedenen Modi
- **Nutzungsmuster**: Identifizieren Sie Spitzenverbrauchsperioden
- **Wartungsplanung**: Verwenden Sie Energiedaten für vorausschauende Wartung

### 3. Integrationsvorteile
- **Home Assistant Integration**: Vollständige Integration mit HAs Energiemanagement
- **Automatisierungsunterstützung**: Verwenden Sie Energiedaten in Automatisierungen und Skripten
- **Dashboard-Integration**: Zeigen Sie Energieverbrauch in benutzerdefinierten Dashboards an

### 4. Zuverlässigkeitsfunktionen
- **Überlauf-Schutz**: Behandelt Sensorwert-Überläufe elegant
- **Offset-Unterstützung**: Einfache Migration beim Wärmepumpen-Austausch
- **Fehlerbehandlung**: Robuste Fehlerbehandlung und Protokollierung

## Technische Implementierungsdetails

### Sensor-Attribute
Jeder Energieverbrauchs-Sensor enthält hilfreiche Attribute:
- `sensor_type`: "energy_consumption"
- `mode`: Betriebsmodus (heating, hot_water, cooling, defrost, stby)
- `reset_interval`: Zeitraum (total, daily, monthly, yearly)
- `hp_index`: Wärmepumpen-Index
- `applied_offset`: Angewendeter Offset-Wert (nur Total-Sensoren)
- `yesterday_value`: Vorheriger Tageswert (nur Tages-Sensoren)
- `previous_monthly_value`: Vorheriger Monatswert (nur Monatliche Sensoren)
- `previous_yearly_value`: Vorheriger Jahreswert (nur Jährliche Sensoren)

### Implementierungsdetails
- **Offset-Laden**: Offsets werden über `load_lambda_config()` Funktion aus `lambda_wp_config.yaml` geladen
- **Offset-Anwendung**: Angewendet in `_apply_energy_offset()` Methode während der Sensor-Initialisierung
- **Entity-Registrierung**: Energieverbrauchs-Entities werden in `hass.data["lambda_heat_pumps"][entry_id]["energy_entities"]` registriert
- **State-Persistierung**: Verwendet `RestoreEntity` für State-Persistierung über Neustarts
- **Unit-Konvertierung**: Automatische Konvertierung von Wh zu kWh über `convert_energy_to_kwh()` Funktion


