---
title: "lambda_wp_config.yaml Konfiguration"
---

# lambda_wp_config.yaml Konfiguration

*Zuletzt geändert am 06.09.2026*

Die `lambda_wp_config.yaml` Datei deckt seit Version 3.5 nur noch drei Dinge ab, für die Home Assistant selbst keinen Platz hat: manuelle Zähler-Offsets (Cycling und Energie) und externe Energiezähler. Alles andere, was diese Datei früher regelte, hat einen eigenen Home-Assistant-Weg bekommen:

| Frühere Einstellung | Heutiger Weg |
|---|---|
| Register deaktivieren | Entität in Home Assistant deaktivieren (siehe [Entitäten löschen](entitaeten_loeschen.md)) |
| Sensor-Namen überschreiben | Entität in Home Assistant umbenennen |
| Register-Reihenfolge für 32-Bit-Werte | Integrations-Option „Register-Reihenfolge" (siehe [Optionen des config_flow](optionen-config-flow.md)) |

## Datei-Location

Die Konfigurationsdatei befindet sich im folgenden Verzeichnis:

```
/config/lambda_wp_config.yaml
```

**Hinweis**: Falls die Datei nicht existiert, wird sie beim ersten Start der Integration automatisch erstellt – vollständig auskommentiert, als Vorlage zum Eintragen eigener Werte.

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
- **Anführungszeichen**: Verwenden Sie Anführungszeichen für Strings mit Sonderzeichen

Ein fehlerhafter Abschnitt wird beim Einlesen übersprungen und in den Logs gemeldet; die übrigen Abschnitte bleiben davon unberührt.

## Konfigurationsoptionen

### 1. Cycling-Zähler-Offsets

Fügt Offsets zu Cycling-Zählern für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen, nach einem Zählerreset oder zur Korrektur eines falschen Ausgangswertes. Positive und **negative** Werte sind erlaubt.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50
    compressor_start_cycling_total: 5000
```

Ausführliche Beschreibung, alle Szenarien und negative Offsets: [Offsets – Historische Daten übernehmen](offsets.md)

### 2. Energieverbrauchs-Sensoren

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

**Hinweis:** Die Quellsensoren müssen kumulative Verbrauchswerte in Wh oder kWh liefern. Das System konvertiert automatisch zu kWh. Liefert ein konfigurierter externer Sensor gerade `unknown`/`unavailable`, wird für diesen Poll nichts gebucht – die Integration schaltet nicht automatisch auf das Controller-Register zurück.

**Beispiel: Nur elektrischer externer Sensor (Shelly3EM), thermisch intern**
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly3em_channel_1_energy"  # Shelly3EM Kanal 1
```

Weitere Informationen: [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md)

### 3. Energieverbrauchs-Offsets

Fügt Offsets zu Energieverbrauchswerten für Total-Sensoren hinzu. Nützlich beim Austausch von Wärmepumpen, nach einem Zählerreset oder zur Korrektur eines falschen Ausgangswertes.

**⚠️ WICHTIG: Alle Werte müssen in kWh angegeben werden!** Positive und **negative** Werte sind erlaubt.

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0              # kWh elektrisch
    hot_water_energy_total: 2000.0
    cooling_energy_total: 500.0
    defrost_energy_total: 150.0
    heating_thermal_energy_total: 18000.0     # kWh thermisch (optional)
    hot_water_thermal_energy_total: 7200.0
    cooling_thermal_energy_total: 1500.0
    defrost_thermal_energy_total: 480.0
```

Ausführliche Beschreibung, alle Szenarien, thermische Offsets und negative Offsets: [Offsets – Historische Daten übernehmen](offsets.md)

## Vollständiges Beispiel

```yaml
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
```

## Anwendung der Konfiguration

### Schritt 1: Datei bearbeiten

1. **Datei öffnen:**
   - Öffnen Sie `/config/lambda_wp_config.yaml`
   - Falls die Datei nicht existiert, wird sie beim nächsten Start automatisch erstellt

2. **Konfiguration hinzufügen:**
   - Fügen Sie die gewünschten Konfigurationsabschnitte hinzu
   - Verwenden Sie die Beispiele oben als Vorlage
   - Achten Sie auf korrekte YAML-Syntax

3. **Datei speichern:**
   - Speichern Sie die Datei
   - Überprüfen Sie die YAML-Syntax (z.B. mit einem Online-YAML-Validator)

### Schritt 2: Home Assistant neu starten (oder Integration neu laden)

Die Datei wird einmal pro Setup gelesen – ein Reload der Integration genügt, ein voller HA-Neustart ist nicht zwingend nötig.

1. **Integration neu laden oder Home Assistant neu starten**
2. **Überprüfen Sie die Logs** auf Konfigurationsfehler
3. **Überprüfen Sie die Sensoren:** Offsets, Quellsensoren etc. korrekt angewendet?

## Häufige Probleme

### "Ungültige YAML-Syntax"

**Ursache**: Syntaxfehler in der YAML-Datei

**Lösung**:
- Verwenden Sie einen YAML-Validator zur Syntaxprüfung (chatgpt und co können das ganz gut)
- Überprüfen Sie Einrückungen (nur Leerzeichen, keine Tabs)
- Überprüfen Sie Doppelpunkte nach Schlüsseln
- Überprüfen Sie Anführungszeichen für Strings

## Validierung

Die Integration validiert die Konfiguration automatisch beim Start. Ein fehlerhafter Abschnitt wird übersprungen und in den Logs gemeldet, statt die gesamte Datei zu verwerfen.

**Tipp**: Überprüfen Sie die Home Assistant Logs nach jedem Neustart, um Konfigurationsfehler frühzeitig zu erkennen.

**Tipp**: Sollten Sie zu viele Fehler haben nach der Änderung an der Datei, Sie können die Datei ganz löschen, sie wird beim Neustart der Integration neu angelegt. Damit sind alle Ihre Konfigurationen auf den Default zurück gesetzt.

## Nächste Schritte

Nach der Konfiguration der `lambda_wp_config.yaml` können Sie:

- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel
- [Energie- und Wärmeverbrauchsberechnung](Energieverbrauchsberechnung.md) mit externen Sensoren einrichten
- [Optionen des config_flow](optionen-config-flow.md) – dort finden Sie u. a. die Register-Reihenfolge
