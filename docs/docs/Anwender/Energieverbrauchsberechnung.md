---
title: "Energie- und Wärmeverbrauchsberechnung"
---

# Energie- und Wärmeverbrauchsberechnung

Die Lambda Heat Pumps Integration bietet umfassende Sensoren für **Stromverbrauch** (elektrische Energie) und **Wärmeabgabe** (thermische Energie) – jeweils nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) und Zeitraum (Total, Täglich, Monatlich, Jährlich). Damit ist eine vollständige Analyse des Energie- und Wärmeflusses Ihrer Wärmepumpe möglich.

## Übersicht

Die Sensoren bieten:

- **Betriebsart-spezifisches Tracking**: Für jede Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen, Standby)
- **Zeiträume**: Total, Täglich, Monatlich, Jährlich
- **Stromverbrauch (elektrisch)** und **Wärmeabgabe (thermisch)**
- **Konfigurierbare Quellsensoren**: Eigene oder externe Energiezähler nutzbar
- **Automatische Einheitenkonvertierung**: Wh, kWh, MWh
- **Sensor-Wechsel-Erkennung** und Flankenerkennung

## Verfügbare Sensoren

### Elektrische Energieverbrauchs-Sensoren (Stromverbrauch)

- **Total**: `sensor.eu08l_hp1_heating_energy_total`, ...
- **Täglich**: `sensor.eu08l_hp1_heating_energy_daily`, ...
- **Monatlich**: `sensor.eu08l_hp1_heating_energy_monthly`, ...
- **Jährlich**: `sensor.eu08l_hp1_heating_energy_yearly`, ...
- Für alle Modi: heating, hot_water, cooling, defrost, stby

### Thermische Energieverbrauchs-Sensoren (Wärmeabgabe)

- **Total**: `sensor.eu08l_hp1_heating_thermal_energy_total`, ...
- **Täglich**: `sensor.eu08l_hp1_heating_thermal_energy_daily`, ...
- **Monatlich**: `sensor.eu08l_hp1_heating_thermal_energy_monthly`, ...
- **Jährlich**: `sensor.eu08l_hp1_heating_thermal_energy_yearly`, ...
- Für alle Modi: heating, hot_water, cooling, defrost

Jeder Sensor ist pro Wärmepumpe (`hp1`, `hp2`, ...) und Modus/Zeitraum verfügbar.

## Konfiguration

### Standard-Konfiguration

Standardmäßig verwendet die Integration die internen Modbus-Sensoren:

- **Stromverbrauch**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- **Wärmeabgabe**: `sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated`

### Externe Sensoren konfigurieren

Sie können externe Energiezähler (z.B. Shelly3EM) als Datenquelle für den Stromverbrauch nutzen:

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"
```

**Hinweis:** Für thermische Energie werden immer die internen Sensoren verwendet.

### Energieverbrauchs-Offsets

Offsets für historische Daten sind für alle Total-Sensoren möglich (siehe [Historische Daten übernehmen](historische-daten.md)):

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0
    hot_water_energy_total: 0.0
    cooling_energy_total: 0.0
    defrost_energy_total: 0.0
```

**⚠️ Alle Werte in kWh!**

## Funktionsweise

### Flankenerkennung

Die Integration nutzt Flankenerkennung, um Energie- und Wärme-Deltas exakt dem aktiven Betriebsmodus zuzuordnen. Bei jedem Moduswechsel wird das Delta berechnet und den passenden Sensoren (elektrisch/thermisch) zugewiesen.

### Automatische Einheitenkonvertierung

- **Wh**: Automatisch zu kWh (÷ 1000)
- **kWh**: Direkt verwendet
- **MWh**: Automatisch zu kWh (× 1000)

### Sensor-Wechsel-Erkennung & Schutzmechanismen

- Automatische Erkennung und Behandlung von Sensorwechseln
- Nullwert- und Rückwärtssprung-Schutz
- Persistenz aller Zählerstände

## Beispiel-Konfigurationen

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

## Verwendung in Dashboards

### Strom- und Wärmeverbrauch nach Betriebsart

```yaml
type: entities
title: Energie & Wärmeverbrauch HP1
entities:
  - entity: sensor.eu08l_hp1_heating_energy_daily
    name: Heizen Strom (Täglich)
  - entity: sensor.eu08l_hp1_heating_thermal_energy_daily
    name: Heizen Wärme (Täglich)
  - entity: sensor.eu08l_hp1_hot_water_energy_daily
    name: Warmwasser Strom (Täglich)
  - entity: sensor.eu08l_hp1_hot_water_thermal_energy_daily
    name: Warmwasser Wärme (Täglich)
  # usw.
```

### Langfristige Trends

```yaml
type: history-graph
title: Energie & Wärmeverbrauch HP1 (Monatlich)
entities:
  - sensor.eu08l_hp1_heating_energy_monthly
  - sensor.eu08l_hp1_heating_thermal_energy_monthly
  - sensor.eu08l_hp1_hot_water_energy_monthly
  - sensor.eu08l_hp1_hot_water_thermal_energy_monthly
hours_to_show: 720
```

## Häufige Probleme & Lösungen

- **Sensor nicht gefunden**: Entity-ID prüfen, Sensor verfügbar?
- **Falsche Werte**: Einheiten prüfen, Offsets prüfen, Sensorwechsel in Logs prüfen
- **Werte springen**: Sensorwechsel/Neustart – Integration wartet automatisch auf stabile Werte
- **Keine Aktualisierung**: Quellsensor liefert keine Werte oder Betriebsmodus nicht erkannt

## Nächste Schritte

- [Historische Daten übernehmen](historische-daten.md)
- [Optionen des config_flow](optionen-config-flow.md)
- [Aktionen (read/write Modbus register)](aktionen-modbus.md)

