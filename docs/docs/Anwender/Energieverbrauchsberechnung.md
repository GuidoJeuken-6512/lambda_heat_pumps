---
title: "Energie- und Wärmeverbrauchsberechnung"
---

# Energie- und Wärmeverbrauchsberechnung

*Zuletzt geändert am 18.10.2026*

Die Lambda Heat Pumps Integration bietet umfassende Sensoren für **Stromverbrauch** (elektrische Energie) und **Wärmeabgabe** (thermische Energie) – jeweils nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) und Zeitraum (Total, Täglich, Monatlich, Jährlich). Damit ist eine vollständige Analyse des Energie- und Wärmeflusses Ihrer Wärmepumpe möglich.

⚠️ **Die Daten der Sensoren werden in der Integration berechnet, sie können nicht aus der Lambda ausgelesen werden. Daher können sie von den Werten in der Lambda abweichen. Zudem müssen sich die Tages-, Monats- & Jahres-Werte erst aufbauen.**

Um die Total-Werte an die Anzeige der Lambda anzugleichen, können Offsets in der `lambda_wp_config.yaml` konfiguriert werden (siehe [Offsets](offsets.md) und [Historische Daten übernehmen](historische-daten.md)).
## Übersicht

Die Sensoren bieten:

- **Betriebsart-spezifisches Tracking**: Für jede Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen, Standby)
- **Zeiträume**: Total, Stündlich (nur Heizen), Täglich, Monatlich, Jährlich
- **Stromverbrauch (elektrisch)** und **Wärmeabgabe (thermisch)**
- **Konfigurierbare Quellsensoren**: Lambda eigener oder externer Energiezähler nutzbar
- **Automatische Einheitenkonvertierung**: Wh, kWh, MWh

## Verfügbare Sensoren

### Elektrische Energieverbrauchs-Sensoren (Stromverbrauch)

- **Total**: `sensor.eu08l_hp1_heating_energy_total`, ...
- **Stündlich** (nur Heizen): `sensor.eu08l_hp1_heating_energy_hourly`
- **Täglich**: `sensor.eu08l_hp1_heating_energy_daily`, ...
- **Monatlich**: `sensor.eu08l_hp1_heating_energy_monthly`, ...
- **Jährlich**: `sensor.eu08l_hp1_heating_energy_yearly`, ...
- Für alle Modi: `heating`, `hot_water`, `cooling`, `defrost`, `stby`

> **Hinweis**: `stby`-Sensoren (Standby-Energie) existieren nur als elektrische Sensoren – es gibt keine thermischen Standby-Sensoren.

### Thermische Energieverbrauchs-Sensoren (Wärmeabgabe)

- **Total**: `sensor.eu08l_hp1_heating_thermal_energy_total`, ...
- **Stündlich** (nur Heizen): `sensor.eu08l_hp1_heating_thermal_energy_hourly`
- **Täglich**: `sensor.eu08l_hp1_heating_thermal_energy_daily`, ...
- **Monatlich**: `sensor.eu08l_hp1_heating_thermal_energy_monthly`, ...
- **Jährlich**: `sensor.eu08l_hp1_heating_thermal_energy_yearly`, ...
- Für alle Modi: `heating`, `hot_water`, `cooling`, `defrost`

Jeder Sensor ist pro Wärmepumpe (`hp1`, `hp2`, ...) und Modus/Zeitraum verfügbar.

## Konfiguration

### Standard-Konfiguration

Standardmäßig verwendet die Integration die internen Modbus-Sensoren:

- **Stromverbrauch**: `sensor.eu08l_hp1_compressor_power_consumption_accumulated`
- **Wärmeabgabe**: `sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated`

### Externe Sensoren konfigurieren

Externe Zähler werden in der Datei `lambda_wp_config.yaml` im Konfigurationsordner von Home Assistant eingetragen (siehe [lambda_wp_config.yaml](lambda-wp-config.md)). Nach einer Änderung die Integration neu laden (**⋮ → Neu laden**).

Sie können pro Wärmepumpe getrennt Quellsensoren für **Stromverbrauch** und **Wärmeabgabe** festlegen. Der Sensor muss einen **steigenden Gesamtzählerstand** in Wh, kWh oder MWh liefern (z. B. „Energie gesamt“ eines Shelly 3EM), keine momentane Leistung in W:

- **`sensor_entity_id`**: Quellsensor für den elektrischen Verbrauch (z. B. Shelly3EM). Fehlt er, wird der Lambda-interne Sensor verwendet.
- **`thermal_sensor_entity_id`** (optional): Quellsensor für die thermische Energie (Wärmeabgabe). Fehlt er, wird der Lambda-interne Thermik-Sensor verwendet.

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"   # elektrisch
    thermal_sensor_entity_id: "sensor.mein_waermemesser"       # optional, thermisch
```

### Energieverbrauchs-Offsets

Offsets für historische Daten sind für alle Total-Sensoren möglich, elektrisch und thermisch (siehe [Offsets](offsets.md)):

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0
    hot_water_energy_total: 0.0
    cooling_energy_total: 0.0
    defrost_energy_total: 0.0
    heating_thermal_energy_total: 0.0
    hot_water_thermal_energy_total: 0.0
    cooling_thermal_energy_total: 0.0
    defrost_thermal_energy_total: 0.0
```

**⚠️ Die Offset Werte müssen in kWh angegeben werden!**

## Funktionsweise

### Zuordnung zur Betriebsart

Bei jeder Abfrage (Standard alle 30 Sekunden) liest die Integration die beiden Zählerstände (elektrisch und thermisch) und berechnet, um wie viel sie seit der letzten Abfrage gestiegen sind. Dieser Zuwachs wird der Betriebsart zugeordnet, in der die Wärmepumpe **gerade** ist (Heizen, Warmwasser, Kühlen, Abtauen, sonst Standby). Eine feinere Aufteilung bietet die Lambda nicht an.

### Einheiten externer Zähler

- **Wh**, **kWh** und **MWh** werden automatisch umgerechnet.
- Meldet ein externer Sensor eine andere Einheit (z. B. W), wird er nicht verwendet, und im Log erscheint eine Warnung.

### Schutzmechanismen

- **Neustart:** Der erste Wert nach dem Start dient nur als Ausgangspunkt und wird nicht gezählt.
- **Wechsel oder Ausfall des Zählers:** Fällt ein externer Zähler aus, zählt die Integration vorübergehend mit dem Zähler der Lambda weiter und wechselt zurück, sobald er wieder Werte liefert. Bei jedem Wechsel und nach jedem Ausfall (auch wenn die Lambda selbst nicht antwortet) gilt dieselbe Regel wie beim Start: Der erste Wert ist nur Ausgangspunkt, erst die zweite Differenz wird gezählt. Lieber fehlt etwas Verbrauch, als dass ein Sprung zwischen zwei Zählern in den Summen landet.
- **Nullwert:** Ein Zählerstand von 0 (meldet die Lambda während des Hochfahrens) wird ignoriert.
- **Rückwärtssprung oder unplausibler Sprung:** Fällt ein Zähler, oder steigt er um mehr als **100 kWh pro Abfrage** (z. B. nach einem Tausch der Wärmepumpe oder bei falscher Register-Reihenfolge), wird dieser Zuwachs verworfen statt gezählt.
- **Zählerstände über Neustarts:** Die Zähler stellen ihren letzten Stand beim Start von Home Assistant wieder her. Ist der letzte gespeicherte Zustand nicht brauchbar (z. B. direkt nach einem Update), greifen die Gesamtzähler auf die Langzeitstatistik von Home Assistant zurück.

## Beispiel-Konfigurationen

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_3em_lambda_energie_gesamt"   # externer Stromzähler, kWh
    # thermal_sensor_entity_id optional; weglassen = Wärmezähler der Lambda
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
- **Werte springen**: Sprünge über 100 kWh pro Abfrage werden verworfen. Springen die akkumulierten Zähler der Lambda selbst, stimmt meist die Register-Reihenfolge nicht, siehe [Falsche / keine Sensorwerte](../FAQ/falsche-keine-sensorwerte.md)
- **Keine Aktualisierung**: Quellsensor liefert keine Werte, oder der externe Zähler hat eine nicht unterstützte Einheit (Log prüfen)
- **Tages-, Monats- oder Jahreszähler fehlen**: Sie sind bei einer Neuinstallation deaktiviert und lassen sich beim Gerät unter „Entitäten“ einschalten

## Nächste Schritte

- [Historische Daten übernehmen](historische-daten.md)
- [Optionen des config_flow](optionen-config-flow.md)
- [Aktionen (read/write Modbus register)](aktionen-modbus.md)

