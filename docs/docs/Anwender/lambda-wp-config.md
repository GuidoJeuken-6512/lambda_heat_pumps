---
title: "lambda_wp_config.yaml Konfiguration"
---

# lambda_wp_config.yaml Konfiguration

Die `lambda_wp_config.yaml` Datei ist die Hauptkonfigurationsdatei für erweiterte Einstellungen der Lambda Heat Pumps Integration. Sie ermöglicht es, Sensoreinstellungen, Energieverbrauchserfassung und Modbus-Kommunikationsparameter anzupassen.

## Datei-Location

Die Konfigurationsdatei befindet sich im folgenden Verzeichnis:

```
/config/lambda_wp_config.yaml
```

**Hinweis**: Falls die Datei nicht existiert, wird sie beim ersten Start der Integration automatisch erstellt.

## Datei bearbeiten

### Über Home Assistant

1. **Datei-Editor verwenden:**
   - Installieren Sie das "File editor" oder "Studio Code Server" Add-on in Home Assistant
   - Öffnen Sie die Datei `/config/lambda_wp_config.yaml`
   - Bearbeiten Sie die Datei
   - Speichern Sie die Änderungen

2. **SSH/Terminal-Zugriff:**
   - Verwenden Sie SSH oder Terminal-Zugriff zu Ihrem Home Assistant
   - Navigieren Sie zum Verzeichnis `/config/`
   - Bearbeiten Sie die Datei mit einem Texteditor (z.B. `nano` oder `vi`)

### YAML-Syntax beachten

⚠️ **WICHTIG**: YAML ist sehr empfindlich gegenüber Einrückungen und Syntax:

- **Einrückungen**: Verwenden Sie **Leerzeichen** (keine Tabs)
- **Doppelpunkt**: Nach jedem Schlüssel muss ein Doppelpunkt (`:`) folgen
- **Bindestriche**: Für Listen verwenden Sie Bindestriche (`-`)
- **Anführungszeichen**: Verwenden Sie Anführungszeichen für Strings mit Sonderzeichen


## Konfigurationsoptionen

### 1. Deaktivierte Register

Deaktiviert spezifische Modbus-Register, die nicht benötigt werden oder Probleme verursachen.

```yaml
disabled_registers:
  - 2004  # boil1_actual_circulation_temp
  - 100000  # Beispiel deaktiviertes Register
```

**Wann verwenden?**
- Register verursacht Fehler im Log
- Register wird von Ihrer Firmware-Version nicht unterstützt
- Register wird nicht benötigt und reduziert Modbus-Traffic z.B. nicht vorhandene Zirkulationspumpe

**Beispiel:**
```yaml
disabled_registers:
  - 2004  # Kessel-Zirkulationstemperatur (nicht verfügbar)
  - 2005
```

### 2. Sensor-Name-Überschreibungen

Überschreibt Standard-Sensornamen für bessere Lesbarkeit oder Lokalisierung.
**Bitte sehr vorsichtig mit dieser Option sein und auf jeden Fall vorher ein Backup von Home Assistant  machen** 
Um hsitorische Daten anderer Sensoren zu übernehmen ist dieser Schritt besser geeignet:  [Historische Daten übernehmen](historische-daten.md)

```yaml
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Wohnzimmer Temperatur"
  - id: hp1_return_temp
    override_name: "Rücklauf Temperatur"
```

**Wann verwenden?**
- bei Migration von einer anderen Lösung zu dieser Integration um historische Daten der alten Sensoren zu erhalten


**Beispiel:**
```yaml
sensors_names_override:
  - id: hp1_flow_temp
    override_name: "Vorlauf Wohnzimmer"
  - id: hp1_return_temp
    override_name: "Rücklauf Wohnzimmer"
  - id: hp1_operating_state
    override_name: "Betriebszustand"
```

### 3. Cycling-Zähler-Offsets
> ⚠️ **Warnung:**  
> Die Funktion *Offsets* ist zur Zeit fehlerhaft und sollte **nicht verwendet werden**!  
> Bitte auf ein zukünftiges Update warten, bevor diese Option genutzt wird!

Fügt Offsets zu Cycling-Zählern für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500    # HP1 hatte bereits 1500 Heizungszyklen
    hot_water_cycling_total: 800   # HP1 hatte bereits 800 Warmwasserzyklen
    cooling_cycling_total: 200     # HP1 hatte bereits 200 Kühlungszyklen
    defrost_cycling_total: 50      # HP1 hatte bereits 50 Abtauzyklen
    compressor_start_cycling_total: 5000  # HP1 hatte bereits 5000 Kompressor-Starts
  hp2:
    heating_cycling_total: 0       # HP2 startet frisch
    hot_water_cycling_total: 0     # HP2 startet frisch
    cooling_cycling_total: 0       # HP2 startet frisch
    defrost_cycling_total: 0       # HP2 startet frisch
    compressor_start_cycling_total: 0     # HP2 startet frisch
```

**Wann verwenden?**
- Wärmepumpen-Austausch: Zählerstand der vorherigen Pumpe hinzufügen
- Zähler-Reset: Manuelle Resets kompensieren
- Historische Daten erhalten: Kontinuität der Daten beibehalten

**Beispiel-Szenario: Wärmepumpen-Austausch**
```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 2500    # Alte Pumpe hatte 2500 Heizungszyklen
    hot_water_cycling_total: 1200  # Alte Pumpe hatte 1200 Warmwasserzyklen
    cooling_cycling_total: 300     # Alte Pumpe hatte 300 Kühlungszyklen
    defrost_cycling_total: 80      # Alte Pumpe hatte 80 Abtauzyklen
```

Weitere Informationen: [Historische Daten übernehmen](historische-daten.md)

### 4. Energieverbrauchs-Sensoren

Definiert, welche Sensoren die Basis-Energieverbrauchsdaten liefern. Pro Wärmepumpe können Sie **elektrischen** und **thermischen** Verbrauch getrennt konfigurieren.

- **`sensor_entity_id`**: Quellsensor für **Stromverbrauch** (elektrisch). Wenn nicht gesetzt, wird der Lambda-interne Sensor verwendet.
- **`thermal_sensor_entity_id`** (optional): Quellsensor für **Wärmeabgabe** (thermisch). Wenn nicht gesetzt, wird der Lambda-interne Thermik-Sensor verwendet.

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"   # elektrisch (Strom)
    thermal_sensor_entity_id: "sensor.lambda_wp_waerme"       # optional, thermisch (Wärme)
  hp2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch2"
    # thermal_sensor_entity_id weglassen = interner Thermik-Sensor
```

**Standard-Sensoren (wenn nichts konfiguriert):**

| Typ      | HP1 | HP2 | HP3 |
|----------|-----|-----|-----|
| Elektrisch | `sensor.eu08l_hp1_compressor_power_consumption_accumulated` | `sensor.eu08l_hp2_compressor_power_consumption_accumulated` | … |
| Thermisch  | `sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated` | `sensor.eu08l_hp2_compressor_thermal_energy_output_accumulated` | … |

**Hinweis:** Die Quellsensoren müssen kumulative Verbrauchswerte in Wh oder kWh liefern. Das System konvertiert automatisch zu kWh.

**Beispiel: Nur elektrischer externer Sensor (Shelly3EM), thermisch intern**
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly3em_channel_1_energy"  # Shelly3EM Kanal 1
```

Weitere Informationen: [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md)

### 5. Energieverbrauchs-Offsets

Fügt Offsets zu Energieverbrauchswerten für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern.
> ⚠️ **Warnung:**  
> Die Funktion *Offsets* ist zur Zeit fehlerhaft und sollte **nicht verwendet werden**!  
> Bitte auf ein zukünftiges Update warten, bevor diese Option genutzt wird!

**⚠️ WICHTIG: Alle Werte müssen in kWh angegeben werden!**

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh Offset für HP1 Heizungs-Total
    hot_water_energy_total: 0.0     # kWh Offset für HP1 Warmwasser-Total
    cooling_energy_total: 0.0       # kWh Offset für HP1 Kühlungs-Total
    defrost_energy_total: 0.0       # kWh Offset für HP1 Abtau-Total
  hp2:
    heating_energy_total: 150.5     # Beispiel: HP2 verbrauchte bereits 150.5 kWh Heizung
    hot_water_energy_total: 45.25   # Beispiel: HP2 verbrauchte bereits 45.25 kWh Warmwasser
    cooling_energy_total: 12.8      # Beispiel: HP2 verbrauchte bereits 12.8 kWh Kühlung
    defrost_energy_total: 3.1       # Beispiel: HP2 verbrauchte bereits 3.1 kWh Abtau
```

**Wann verwenden?**
- Wärmepumpen-Austausch: Energieverbrauch der vorherigen Pumpe hinzufügen
- Zähler-Reset: Manuelle Resets kompensieren
- Historische Daten erhalten: Energieverbrauchshistorie beibehalten

**Beispiel-Szenario: Wärmepumpen-Austausch**
```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0    # Alte Pumpe verbrauchte 5000 kWh Heizung
    hot_water_energy_total: 2000.0  # Alte Pumpe verbrauchte 2000 kWh Warmwasser
    cooling_energy_total: 500.0     # Alte Pumpe verbrauchte 500 kWh Kühlung
    defrost_energy_total: 150.0     # Alte Pumpe verbrauchte 150 kWh Abtau
```

**Hinweis**: 
- Alle Werte müssen in **kWh** angegeben werden
- Verwenden Sie Punkt (.) als Dezimaltrennzeichen in YAML
- Offsets werden nur auf TOTAL-Sensoren angewendet, nicht auf Daily/Monthly/Yearly Sensoren

Weitere Informationen: [Historische Daten übernehmen](historische-daten.md)

### 6. Modbus-Konfiguration

Konfiguriert Modbus-Kommunikationsparameter für 32-Bit-Register.

```yaml
modbus:
  # Register-Reihenfolge für 32-Bit-Register (int32-Sensoren)
  # "high_first" = Höherwertiges Register zuerst (Standard)
  # "low_first" = Niedrigwertiges Register zuerst
  int32_register_order: "high_first"  # oder "low_first"
```

**Optionen:**
- **"high_first"**: Höherwertiges Register zuerst (Standard für die meisten Lambda-Modelle)
- **"low_first"**: Niedrigwertiges Register zuerst (für bestimmte Lambda-Modelle oder Firmware-Versionen)

**Wann verwenden?**
- Falsche Werte in 32-Bit-Sensoren (z.B. Energieverbrauchssensoren)
- Nach Firmware-Update, wenn Sensoren falsche Werte anzeigen
- Bei bestimmten Lambda-Modellen, die eine andere Register-Reihenfolge benötigen

**Beispiel: Falsche Werte korrigieren**
```yaml
modbus:
  int32_register_order: "low_first"  # Wechsel von "high_first" zu "low_first"
```

**Hinweis**: 
- Alte Config mit `int32_byte_order` oder alten Werten (`big`/`little`) wird automatisch erkannt und migriert
- Nach Änderung Home Assistant neu starten

Weitere Informationen: [Anpassungen der Sensoren abhängig von der Firmware](anpassungen-sensoren-firmware.md)

## Vollständiges Beispiel

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
    compressor_start_cycling_total: 0
  hp2:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50
    compressor_start_cycling_total: 5000

# Energieverbrauchs-Sensor-Konfiguration (elektrisch + optional thermisch)
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
    # thermal_sensor_entity_id: "sensor.xyz"  # optional, sonst interner Thermik-Sensor
  hp2:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"  # Externer Sensor

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
  int32_register_order: "high_first"  # oder "low_first" für einige Geräte
```

## Anwendung der Konfiguration

### Schritt 1: Datei bearbeiten

1. **Datei öffnen:**
   - Öffnen Sie `/config/lambda_heat_pumps/lambda_wp_config.yaml`
   - Falls die Datei nicht existiert, wird sie beim nächsten Start automatisch erstellt

2. **Konfiguration hinzufügen:**
   - Fügen Sie die gewünschten Konfigurationsabschnitte hinzu
   - Verwenden Sie die Beispiele oben als Vorlage
   - Achten Sie auf korrekte YAML-Syntax

3. **Datei speichern:**
   - Speichern Sie die Datei
   - Überprüfen Sie die YAML-Syntax (z.B. mit einem Online-YAML-Validator)

### Schritt 2: Home Assistant neu starten

1. **Home Assistant neu starten:**
   - Starten Sie Home Assistant vollständig neu
   - Die Konfiguration wird beim Start automatisch geladen

2. **Überprüfen Sie die Logs:**
   - Überprüfen Sie die Home Assistant Logs auf Konfigurationsfehler
   - Die Integration validiert die Konfiguration beim Start

3. **Überprüfen Sie die Sensoren:**
   - Überprüfen Sie, ob die Änderungen korrekt angewendet wurden
   - Überprüfen Sie die Sensor-Namen, Offsets, etc.

## Häufige Probleme

### "Ungültige YAML-Syntax"

**Ursache**: Syntaxfehler in der YAML-Datei

**Lösung**:
- Verwenden Sie einen YAML-Validator zur Syntaxprüfung (chatgpt und co können das ganz gut)
- Überprüfen Sie Einrückungen (nur Leerzeichen, keine Tabs)
- Überprüfen Sie Doppelpunkte nach Schlüsseln
- Überprüfen Sie Anführungszeichen für Strings


## Validierung

Die Integration validiert die Konfiguration automatisch beim Start:

- **YAML-Syntax**: Überprüfung der Datei-Syntax
- **Sensor-Existenz**: Überprüfung, ob konfigurierte Sensoren existieren
- **Werte-Bereiche**: Überprüfung von Temperatur- und Offset-Werten
- **Log-Meldungen**: Alle Probleme werden in den Logs protokolliert

**Tipp**: Überprüfen Sie die Home Assistant Logs nach jedem Neustart, um Konfigurationsfehler frühzeitig zu erkennen.

**Tipp**: Sollten Sie zu viele Fehler haben nach der Änderung an der Datei, Sie können die Datei ganz löschen, sie wird beim Neustart der Integration neu angelegt. Damit sind alle Ihre Konfigurationen auf den Default zurück gesetzt.

## Nächste Schritte

Nach der Konfiguration der `lambda_wp_config.yaml` können Sie:

- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel
- [Stromverbrauchsberechnung](stromverbrauchsberechnung.md) mit externen Sensoren einrichten
- [Anpassungen der Sensoren abhängig von der Firmware](anpassungen-sensoren-firmware.md) vornehmen

