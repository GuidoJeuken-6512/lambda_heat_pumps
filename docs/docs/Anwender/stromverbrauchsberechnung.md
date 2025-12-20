---
title: "Stromverbrauchsberechnung"
---

# Stromverbrauchsberechnung

Die Lambda Heat Pumps Integration bietet umfassende Energieverbrauchs-Sensoren, die den Stromverbrauch nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) verfolgen. Diese Sensoren ermöglichen eine detaillierte Analyse des Energieverbrauchs Ihrer Wärmepumpe.

## Übersicht

Die Energieverbrauchs-Sensoren bieten:

- **Betriebsart-spezifisches Tracking**: Verfolgung des Energieverbrauchs für jeden Betriebsmodus
- **Zeiträume**: Total, Täglich, Monatlich, Jährlich
- **Konfigurierbare Quellsensoren**: Verwendung beliebiger Energiezähler als Datenquelle
- **Automatische Einheitenkonvertierung**: Unterstützung für Wh, kWh und MWh
- **Sensor-Wechsel-Erkennung**: Intelligente Behandlung von Sensor-Änderungen

## Verfügbare Sensoren

### Total Energieverbrauchs-Sensoren

- **Zweck**: Kumulativer Energieverbrauch seit Installation
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_energy_total`
  - `sensor.eu08l_hp1_hot_water_energy_total`
  - `sensor.eu08l_hp1_cooling_energy_total`
  - `sensor.eu08l_hp1_defrost_energy_total`

### Tages Energieverbrauchs-Sensoren

- **Zweck**: Täglicher Energieverbrauch (Reset um Mitternacht)
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_energy_daily`
  - `sensor.eu08l_hp1_hot_water_energy_daily`
  - `sensor.eu08l_hp1_cooling_energy_daily`
  - `sensor.eu08l_hp1_defrost_energy_daily`

### Monatliche Energieverbrauchs-Sensoren

- **Zweck**: Monatlicher Energieverbrauch (Reset am 1. des Monats)
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_energy_monthly`
  - `sensor.eu08l_hp1_hot_water_energy_monthly`
  - `sensor.eu08l_hp1_cooling_energy_monthly`
  - `sensor.eu08l_hp1_defrost_energy_monthly`

### Jährliche Energieverbrauchs-Sensoren

- **Zweck**: Jährlicher Energieverbrauch (Reset am 1. Januar)
- **Beispiele**: 
  - `sensor.eu08l_hp1_heating_energy_yearly`
  - `sensor.eu08l_hp1_hot_water_energy_yearly`
  - `sensor.eu08l_hp1_cooling_energy_yearly`
  - `sensor.eu08l_hp1_defrost_energy_yearly`

## Konfiguration

### Standard-Konfiguration

Standardmäßig verwendet die Integration den Lambda-eigenen Sensor:

- **HP1**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- **HP2**: `sensor.eu08l_hp2_compressor_power_consumption_accumulated`
- **HP3**: `sensor.eu08l_hp3_compressor_power_consumption_accumulated`

### Externe Sensoren konfigurieren

Sie können externe Energiezähler (z.B. Shelly3EM) als Datenquelle verwenden:

**Konfiguration in `lambda_wp_config.yaml`:**

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"  # Externer Verbrauchssensor
  hp2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch2"  # Zweiter Verbrauchssensor
```

**Hinweis**: Diese Sensoren müssen Energieverbrauchsdaten in Wh oder kWh liefern. Das System konvertiert automatisch zu kWh für die Berechnungen.

### Energieverbrauchs-Offsets

Sie können Offsets für historische Daten hinzufügen (siehe [Historische Daten übernehmen](historische-daten.md)):

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # kWh Offset für HP1 Heizung Total
    hot_water_energy_total: 0.0     # kWh Offset für HP1 Warmwasser Total
    cooling_energy_total: 0.0       # kWh Offset für HP1 Kühlung Total
    defrost_energy_total: 0.0       # kWh Offset für HP1 Abtau Total
```

**⚠️ WICHTIG: Alle Werte müssen in kWh angegeben werden!**

## Funktionsweise

### Flankenerkennung

Die Integration verwendet **Flankenerkennung** zur automatischen Energiezuordnung:

1. **Betriebszustand überwachen**: Änderungen im Wärmepumpen-Betriebsmodus verfolgen
2. **Energie-Delta berechnen**: Energieverbrauch während jedes Modus messen
3. **Energie zuordnen**: Verbrauchte Energie den entsprechenden Modus-Sensoren zuweisen
4. **Zähler aktualisieren**: Total-, Tages-, Monatliche und Jährliche Sensoren gleichzeitig erhöhen

### Energie-Berechnung

Die Integration berechnet den Energieverbrauch basierend auf:

- **Quellsensor**: Der konfigurierte Energiezähler (Standard oder extern)
- **Betriebsmodus**: Der aktuelle Betriebsmodus der Wärmepumpe
- **Flankenerkennung**: Automatische Erkennung von Betriebsmodus-Wechseln

### Automatische Einheitenkonvertierung

Die Integration unterstützt automatische Einheitenkonvertierung:

- **Wh (Wattstunden)**: Automatisch zu kWh konvertiert (÷ 1000)
- **kWh (Kilowattstunden)**: Direkt verwendet (keine Konvertierung nötig)
- **MWh (Megawattstunden)**: Automatisch zu kWh konvertiert (× 1000)

## Sensor-Wechsel-Erkennung

Die Integration beinhaltet **automatische Sensor-Wechsel-Erkennung**:

### Funktionsweise

1. **Sensor-ID-Verfolgung**: Speichert die aktuelle Energie-Quellsensor-ID für jede Wärmepumpe
2. **Änderungserkennung**: Vergleicht gespeicherte Sensor-ID mit aktueller Konfiguration beim Start
3. **Automatische Behandlung**: Bei erkannten Änderungen wird `last_energy_readings` angepasst, um falsche Berechnungen zu verhindern
4. **Retry-Mechanismus**: Verwendet Retry-Logik zur Behandlung von Sensor-Unverfügbarkeit beim Start

### Schutzmechanismen

- **Null-Wert-Schutz**: Verhindert falsche Delta-Berechnungen wenn Sensoren 0-Werte beim Start oder Sensor-Wechsel zeigen
- **Kontinuierliche JSON-Persistierung**: Eigene Modbus-Sensoren werden kontinuierlich in JSON gespeichert für sofortige Verfügbarkeit nach Sensor-Wechseln
- **Zwei-Wert-Validierung**: Delta-Berechnung startet erst nach zwei aufeinanderfolgenden Werten > 0.0

## Beispiel-Konfigurationen

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

### Externe Sensoren

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"  # Shelly3EM Sensor
```

## Verwendung in Dashboards

### Energieverbrauch nach Betriebsart

Erstellen Sie ein Dashboard, das den Energieverbrauch nach Betriebsart anzeigt:

```yaml
type: entities
title: Energieverbrauch HP1
entities:
  - entity: sensor.eu08l_hp1_heating_energy_daily
    name: Heizen (Täglich)
  - entity: sensor.eu08l_hp1_hot_water_energy_daily
    name: Warmwasser (Täglich)
  - entity: sensor.eu08l_hp1_cooling_energy_daily
    name: Kühlen (Täglich)
  - entity: sensor.eu08l_hp1_defrost_energy_daily
    name: Abtauen (Täglich)
```

### Energieverbrauch über Zeit

Verwenden Sie History-Graphen für langfristige Trends:

```yaml
type: history-graph
title: Energieverbrauch HP1 (Monatlich)
entities:
  - sensor.eu08l_hp1_heating_energy_monthly
  - sensor.eu08l_hp1_hot_water_energy_monthly
  - sensor.eu08l_hp1_cooling_energy_monthly
  - sensor.eu08l_hp1_defrost_energy_monthly
hours_to_show: 720  # 30 Tage
```

## Häufige Probleme

### "Sensor nicht gefunden"
- **Ursache**: Der konfigurierte Sensor existiert nicht oder ist nicht verfügbar
- **Lösung**: 
  - Überprüfen Sie, ob der Sensor in Home Assistant existiert
  - Überprüfen Sie die Entity-ID
  - Überprüfen Sie die Logs auf Fehlermeldungen

### "Falsche Energie-Werte"
- **Ursache**: Falsche Einheiten oder Sensor-Wechsel
- **Lösung**: 
  - Überprüfen Sie die Einheiten des Quellsensors (Wh/kWh/MWh)
  - Überprüfen Sie die Sensor-Wechsel-Erkennung in den Logs
  - Überprüfen Sie die Offsets

### "Energie-Werte springen"
- **Ursache**: Sensor-Wechsel oder Neustart
- **Lösung**: 
  - Die Integration behandelt Sensor-Wechsel automatisch
  - Überprüfen Sie die Logs auf Sensor-Wechsel-Meldungen
  - Warten Sie einige Minuten, bis sich die Werte stabilisiert haben

### "Energie-Werte werden nicht aktualisiert"
- **Ursache**: Quellsensor liefert keine Werte oder Betriebsmodus-Erkennung funktioniert nicht
- **Lösung**: 
  - Überprüfen Sie, ob der Quellsensor Werte liefert
  - Überprüfen Sie die Betriebsmodus-Erkennung
  - Überprüfen Sie die Logs auf Fehlermeldungen

## Nächste Schritte

Nach der Einrichtung der Stromverbrauchsberechnung können Sie:

- [Historische Daten übernehmen](historische-daten.md) bei Wärmepumpenwechsel
- [Optionen des config_flow](optionen-config-flow.md) anpassen
- [Aktionen (read/write Modbus register)](aktionen-modbus.md) verwenden

