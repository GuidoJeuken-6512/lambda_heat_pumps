# Lambda WP Configuration Reference

**Complete guide to all configuration options in `lambda_wp_config.yaml`**

*For German version, see [Deutsche Version](#deutsche-version) below.*

## Overview

The `lambda_wp_config.yaml` file is the main configuration file for the Lambda Heat Pumps integration. It allows you to customize various aspects of the integration's behavior, including sensor settings, energy consumption tracking, and Modbus communication parameters.

## Configuration Sections

### 1. Disabled Registers

Disable specific Modbus registers that are not needed or cause issues.

```yaml
disabled_registers:
  - 2004  # boil1_actual_circulation_temp
  - 100000  # Example disabled register
```

**Purpose**: Prevents reading of problematic or unnecessary registers  
**Format**: List of register addresses (integers)  
**Default**: Empty list (all registers enabled)

### 2. Sensor Name Overrides

Override default sensor names .

```yaml
sensors_names_override:
  - id: name_of_the_sensor_to_override_example
    override_name: new_name_of_the_sensor_example
  - id: hp1_flow_temp
    override_name: "Living Room Temperature"
```

**Purpose**: Customize sensor display names  
**Format**: List of objects with `id` and `override_name`  
**Default**: Empty list (use default names)

### 3. Cycling Counter Offsets

Add offsets to cycling counters for total sensors. Useful when replacing heat pumps or resetting counters.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 0      # Offset for HP1 heating total cycles
    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles
  hp2:
    heating_cycling_total: 1500   # Example: HP2 already had 1500 heating cycles
    hot_water_cycling_total: 800  # Example: HP2 already had 800 hot water cycles
    cooling_cycling_total: 200    # Example: HP2 already had 200 cooling cycles
    defrost_cycling_total: 50     # Example: HP2 already had 50 defrost cycles
```

**Purpose**: Compensate for existing cycling counts when replacing hardware  
**Format**: Nested objects by heat pump (hp1, hp2, etc.)  
**Default**: Empty object (no offsets)

### 4. Energy Consumption Sensors

To calculate the power consumption according to the operating mode, we use the standard Lambda sensor "sensor.eu08l_hp1_compressor_power_consumption_accumulated" (HeatPump1). If another consumption meter, such as a Shelly3EM, is connected before the system, the sensor can be used to calculate the consumption values. 

**Note**: These sensors must provide energy consumption data in Wh or kWh. The system automatically converts to kWh for calculations.

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"  # Example: External consumption sensor
  hp2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch2" # Example: Second consumption sensor
  hp3:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"  # Custom sensor
```

**Purpose**: Define which sensors provide base energy consumption data  
**Format**: Objects by heat pump with `sensor_entity_id`  
**Default**: Uses default sensor entity IDs  
**Units**: Sensors must provide data in Wh or kWh (automatic conversion to kWh)

### 5. Energy Consumption Offsets

Add offsets to energy consumption values for total sensors. Useful when replacing heat pumps or resetting counters.

**⚠️ IMPORTANT: All values must be specified in kWh!**

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh offset for HP1 heating total
    hot_water_energy_total: 0.0     # kWh offset for HP1 hot water total
    cooling_energy_total: 0.0       # kWh offset for HP1 cooling total
    defrost_energy_total: 0.0       # kWh offset for HP1 defrost total
  hp2:
    heating_energy_total: 150.5     # Example: HP2 already consumed 150.5 kWh heating
    hot_water_energy_total: 45.25   # Example: HP2 already consumed 45.25 kWh hot water
    cooling_energy_total: 12.8      # Example: HP2 already consumed 12.8 kWh cooling
    defrost_energy_total: 3.1       # Example: HP2 already consumed 3.1 kWh defrost
```

**Purpose**: Compensate for existing energy consumption when replacing hardware  
**Format**: Nested objects by heat pump with energy values in kWh  
**Default**: Empty object (no offsets)  
**Units**: All values must be in kWh (kilowatt-hours)  
**Application**: Only applied to TOTAL sensors, not Daily/Monthly/Yearly sensors  
**Decimal notation**: Use dot (.) as decimal separator in YAML, comma (,) in display

### 6. Modbus Configuration

Configure Modbus communication parameters.

```yaml
modbus:
  # Endianness for 32-bit registers (int32 sensors)
  # Some Lambda devices may require different byte order for correct int32 value interpretation
  # "big" = Big-Endian (default, current behavior)
  # "little" = Little-Endian (alternative byte order for some devices)
  int32_byte_order: "big"  # or "little"
```

**Purpose**: Configure byte order for 32-bit register interpretation  
**Format**: Object with `int32_byte_order` property  
**Default**: `"big"` (Big-Endian)

**Options**:
- `"big"`: Big-Endian (default, most devices)
- `"little"`: Little-Endian (some newer devices)

## Complete Example Configuration

```yaml
# Disable problematic registers
disabled_registers:
  - 2004  # boil1_actual_circulation_temp
  - 100000

# Override sensor names 
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Living Room Temperature"
  - id: hp1_return_temp
    override_name: "Return Temperature"

# Cycling counter offsets
cycling_offsets:
  hp1:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
  hp2:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50

# Energy consumption sensor configuration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

# Energy consumption offsets
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

# Modbus configuration
modbus:
  int32_byte_order: "big"  # or "little" for some devices
```

## Troubleshooting

### Common Issues

1. **Invalid YAML syntax**: Use a YAML validator to check syntax
2. **Sensor not found**: Verify entity IDs exist in Home Assistant
3. **Offsets not applied**: Restart Home Assistant after configuration changes
4. **Wrong energy values**: Check `int32_byte_order` setting

### Validation

The integration validates configuration on startup and logs any issues. Check the Home Assistant logs for configuration errors.

---

## Deutsche Version {#deutsche-version}

**Vollständige Anleitung zu allen Konfigurationsoptionen in `lambda_wp_config.yaml`**

### Übersicht

Die `lambda_wp_config.yaml` Datei ist die Hauptkonfigurationsdatei für die Lambda Wärmepumpen-Integration. Sie ermöglicht es, verschiedene Aspekte des Integrationsverhaltens anzupassen, einschließlich Sensoreinstellungen, Energieverbrauchserfassung und Modbus-Kommunikationsparametern.

### Konfigurationsabschnitte

#### 1. Deaktivierte Register

Deaktiviert spezifische Modbus-Register, die nicht benötigt werden oder Probleme verursachen.

```yaml
disabled_registers:
  - 2004  # boil1_actual_circulation_temp
  - 100000  # Beispiel deaktiviertes Register
```

**Zweck**: Verhindert das Lesen von problematischen oder unnötigen Registern  
**Format**: Liste von Register-Adressen (Ganzzahlen)  
**Standard**: Leere Liste (alle Register aktiviert)

#### 2. Sensor-Name-Überschreibungen

Überschreibt Standard-Sensornamen.

```yaml
sensors_names_override:
  - id: name_of_the_sensor_to_override_example
    override_name: new_name_of_the_sensor_example
  - id: hp1_flow_temp
    override_name: "Wohnzimmer Temperatur"
```

**Zweck**: Sensornamen anpassen  
**Format**: Liste von Objekten mit `id` und `override_name`  
**Standard**: Leere Liste (Standard-Namen verwenden)

#### 3. Cycling-Zähler-Offsets

Fügt Offsets zu Cycling-Zählern für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 0      # Offset für HP1 Heizungs-Total-Zyklen
    hot_water_cycling_total: 0    # Offset für HP1 Warmwasser-Total-Zyklen
    cooling_cycling_total: 0      # Offset für HP1 Kühlungs-Total-Zyklen
    defrost_cycling_total: 0      # Offset für HP1 Abtau-Total-Zyklen
  hp2:
    heating_cycling_total: 1500   # Beispiel: HP2 hatte bereits 1500 Heizungszyklen
    hot_water_cycling_total: 800  # Beispiel: HP2 hatte bereits 800 Warmwasserzyklen
    cooling_cycling_total: 200    # Beispiel: HP2 hatte bereits 200 Kühlungszyklen
    defrost_cycling_total: 50     # Beispiel: HP2 hatte bereits 50 Abtauzyklen
```

**Zweck**: Bestehende Cycling-Zählstände beim Hardware-Austausch kompensieren  
**Format**: Verschachtelte Objekte nach Wärmepumpe (hp1, hp2, etc.)  
**Standard**: Leeres Objekt (keine Offsets)

#### 4. Energieverbrauchs-Sensoren

Zur Berechnung der Stromaufnahme nach Betriebsart nehmen wir im standart den Lambda eigene Sensor "sensor.eu08l_hp1_compressor_power_consumption_accumulated"  (HeatPump1), ist eine anderer Verbrauchsmesser, wie z.B. ein Shelly3EM vorgeschaltet, kann der Sensor zur Berechnung der Verbrauchswerte genutzt werden.

**Hinweis**: Diese Sensoren müssen Energieverbrauchsdaten in Wh oder kWh liefern. Das System konvertiert automatisch zu kWh für die Berechnungen.

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"  # Beispiel: Externer Verbrauchssensor
  hp2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch2" # Beispiel: Zweiter Verbrauchssensor
  hp3:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"  # Benutzerdefinierter Sensor
```

**Zweck**: Definiert welche Sensoren Basis-Energieverbrauchsdaten liefern  
**Format**: Objekte nach Wärmepumpe mit `sensor_entity_id`  
**Standard**: Verwendet Standard-Sensor-Entity-IDs  
**Einheiten**: Sensoren müssen Daten in Wh oder kWh liefern (automatische Konvertierung zu kWh)

#### 5. Energieverbrauchs-Offsets

Fügt Offsets zu Energieverbrauchswerten für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern.

**⚠️ WICHTIG: Alle Werte müssen in kWh angegeben werden!**

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh Offset für HP1 Heizungs-Total
    hot_water_energy_total: 0.0     # kWh Offset für HP1 Warmwasser-Total
    cooling_energy_total: 0.0       # kWh Offset für HP1 Kühlungs-Total
    defrost_energy_total: 0.0       # kWh Offset für HP1 Abtau-Total
  hp2:
    heating_energy_total: 150.5     # Beispiel: HP2 verbrauchte bereits 150,5 kWh Heizung
    hot_water_energy_total: 45.25   # Beispiel: HP2 verbrauchte bereits 45,25 kWh Warmwasser
    cooling_energy_total: 12.8      # Beispiel: HP2 verbrauchte bereits 12,8 kWh Kühlung
    defrost_energy_total: 3.1       # Beispiel: HP2 verbrauchte bereits 3,1 kWh Abtau
```

**Zweck**: Bestehenden Energieverbrauch beim Hardware-Austausch kompensieren  
**Format**: Verschachtelte Objekte nach Wärmepumpe mit Energie-Werten in kWh  
**Standard**: Leeres Objekt (keine Offsets)  
**Einheiten**: Alle Werte müssen in kWh (Kilowattstunden) angegeben werden  
**Anwendung**: Nur auf TOTAL-Sensoren angewendet, nicht auf Daily/Monthly/Yearly Sensoren  
**Dezimalnotation**: Punkt (.) als Dezimaltrennzeichen in YAML, Komma (,) in der Anzeige

#### 6. Modbus-Konfiguration

Konfiguriert Modbus-Kommunikationsparameter.

```yaml
modbus:
  # Endianness für 32-Bit-Register (int32-Sensoren)
  # Einige Lambda-Geräte erfordern möglicherweise eine andere Byte-Reihenfolge für die korrekte int32-Wert-Interpretation
  # "big" = Big-Endian (Standard, aktuelles Verhalten)
  # "little" = Little-Endian (alternative Byte-Reihenfolge für einige Geräte)
  int32_byte_order: "big"  # oder "little"
```

**Zweck**: Byte-Reihenfolge für 32-Bit-Register-Interpretation konfigurieren  
**Format**: Objekt mit `int32_byte_order` Eigenschaft  
**Standard**: `"big"` (Big-Endian)

**Optionen**:
- `"big"`: Big-Endian (Standard, die meisten Geräte)
- `"little"`: Little-Endian (einige neuere Geräte)

### Vollständiges Beispiel-Konfiguration

```yaml
# Problematische Register deaktivieren
disabled_registers:
  - 2004  # boil1_actual_circulation_temp
  - 100000

# Sensornamen überschreiben 
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Wohnzimmer Temperatur"
  - id: hp1_return_temp
    override_name: "Rücklauf Temperatur"

# Cycling-Zähler-Offsets
cycling_offsets:
  hp1:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
  hp2:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50

# Energieverbrauchs-Sensor-Konfiguration
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
  hp2:
    sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"

# Energieverbrauchs-Offsets
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

# Modbus-Konfiguration
modbus:
  int32_byte_order: "big"  # oder "little" für einige Geräte
```

### Fehlerbehebung

#### Häufige Probleme

1. **Ungültige YAML-Syntax**: Verwenden Sie einen YAML-Validator zur Syntaxprüfung
2. **Sensor nicht gefunden**: Überprüfen Sie, ob Entity-IDs in Home Assistant existieren
3. **Offsets nicht angewendet**: Starten Sie Home Assistant nach Konfigurationsänderungen neu
4. **Falsche Energie-Werte**: Überprüfen Sie die `int32_byte_order` Einstellung

#### Validierung

Die Integration validiert die Konfiguration beim Start und protokolliert alle Probleme. Überprüfen Sie die Home Assistant Logs auf Konfigurationsfehler.
