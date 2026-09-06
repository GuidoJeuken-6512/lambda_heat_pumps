---
title: "COP-Sensoren (Leistungszahl)"
---

# COP-Sensoren (Leistungszahl)

*Zuletzt geändert am 06.09.2026*

Die Lambda Heat Pumps Integration bietet **COP-Sensoren** (Coefficient of Performance / Leistungszahl), die das Verhältnis von erzeugter Wärme zu eingesetztem Strom anzeigen. Diese Sensoren helfen Ihnen, die Effizienz Ihrer Wärmepumpe zu überwachen und zu analysieren.

## Was ist COP?

Der **COP (Coefficient of Performance)** ist die Leistungszahl einer Wärmepumpe und gibt an, wie viel Wärmeenergie pro eingesetzter elektrischer Energie erzeugt wird.

**Formel:** `COP = Thermische Energie (kWh) / Elektrische Energie (kWh)`

**Beispiel:** 
- Thermische Energie: 10 kWh
- Elektrische Energie: 2 kWh
- **COP = 10 / 2 = 5.0**

Ein COP von 5.0 bedeutet, dass die Wärmepumpe aus 1 kWh Strom 5 kWh Wärme erzeugt.

## Verfügbare COP-Sensoren

Die Integration erstellt automatisch COP-Sensoren für folgende Betriebsarten:

- **Heizen (Heating)**
- **Warmwasser (Hot Water)**
- **Kühlen (Cooling)**

**Nicht für Defrost**: COP-Sensoren werden nicht für den Abtau-Modus erstellt, da dieser Modus primär der Wartung dient.

### Zeiträume

Für Warmwasser und Kühlen werden vier Zeiträume angeboten, für Heizen zusätzlich ein fünfter:

- **Daily (Täglich)**: COP-Wert für den aktuellen Tag
- **Monthly (Monatlich)**: COP-Wert für den aktuellen Monat
- **Yearly (Jährlich)**: COP-Wert für das aktuelle Jahr
- **Total (Gesamt)**: COP-Wert seit dem letzten Neustart von Home Assistant (siehe Hinweis unten)
- **Hourly (Stündlich, nur Heizen)**: COP-Wert für die aktuelle Stunde

Nur die Total-Sensoren sind standardmäßig aktiviert; die übrigen Perioden lassen sich in der Entity-Registry bei Bedarf einschalten.

Daneben gibt es pro Wärmepumpe einen zusätzlichen `cop_calc`-Sensor, der nicht auf den oben genannten Zählern basiert, sondern direkt aus den beiden **Lifetime**-Registern des Controllers berechnet wird (siehe Abschnitt „Zusammenhang mit Energieverbrauchssensoren" unten) – der einzige COP-Wert, der auch die Zeit vor der ersten Home-Assistant-Installation einschließt.

### Entity-IDs

Die Sensoren werden mit folgenden Entity-IDs erstellt (Beispiel Legacy-Namensschema):

- `sensor.{name_prefix}_hp1_heating_cop_daily`
- `sensor.{name_prefix}_hp1_heating_cop_monthly`
- `sensor.{name_prefix}_hp1_heating_cop_yearly`
- `sensor.{name_prefix}_hp1_heating_cop_total`
- `sensor.{name_prefix}_hp1_heating_cop_hourly`
- `sensor.{name_prefix}_hp1_hot_water_cop_daily` / `_monthly` / `_yearly` / `_total`
- `sensor.{name_prefix}_hp1_cooling_cop_daily` / `_monthly` / `_yearly` / `_total`
- `sensor.{name_prefix}_hp1_cop_calc` (Lifetime-COP, siehe oben)

**Beispiel:** `sensor.eu08l_hp1_heating_cop_daily`

## Funktionsweise

### Automatische Berechnung

Die COP-Sensoren berechnen sich automatisch aus den vorhandenen Energieverbrauchssensoren:

- **Quell-Sensoren (thermisch)**: `sensor.{prefix}_{mode}_thermal_energy_{period}`
- **Quell-Sensoren (elektrisch)**: `sensor.{prefix}_{mode}_energy_{period}`

### Automatische Aktualisierung

Die COP-Sensoren aktualisieren sich automatisch, wenn sich die Quellsensoren (thermische oder elektrische Energie) ändern. Sie müssen nichts konfigurieren.

### Berechnungslogik

1. **COP-Berechnung**: `COP = Thermische Energie / Elektrische Energie`
2. **Division durch Null**: Solange in der Periode noch keine elektrische Energie erfasst wurde, zeigt der Sensor `unknown` (nicht `0.0`) – ein COP von 0 wäre eine falsche Effizienzaussage
3. **Präzision**: 2 Dezimalstellen (z.B. 3.45)

### Periodische Werte und Anzeige

Die periodischen COP-Sensoren (Daily, Monthly, Yearly) **bauen sich erst im Lauf der Zeit auf**. Bis in der jeweiligen Periode sowohl thermische als auch elektrische Energie erfasst wurden, kann der Sensor **`unknown`** oder **`0`** anzeigen – das ist normal. Sobald beide Quellwerte in der Periode anfallen, wird der COP berechnet. Siehe auch [FAQ – COP-Sensoren](../FAQ/cop-sensoren.md).

## Technische Details

- **Unit**: Keine (COP ist dimensionslos)
- **State Class**: `measurement` (für historische Daten)
- **Device Class**: `None`
- **Precision**: 2 Dezimalstellen
- **Historische Daten**: Werden automatisch im Home Assistant Recorder gespeichert

## Verwendung in Dashboards

### COP-Übersicht

```yaml
type: entities
title: COP-Werte HP1 (Leistungszahl)
entities:
  - entity: sensor.eu08l_hp1_heating_cop_daily
    name: Heizen COP (Täglich)
  - entity: sensor.eu08l_hp1_heating_cop_monthly
    name: Heizen COP (Monatlich)
  - entity: sensor.eu08l_hp1_heating_cop_total
    name: Heizen COP (Gesamt)
  - entity: sensor.eu08l_hp1_hot_water_cop_daily
    name: Warmwasser COP (Täglich)
  - entity: sensor.eu08l_hp1_hot_water_cop_monthly
    name: Warmwasser COP (Monatlich)
  - entity: sensor.eu08l_hp1_hot_water_cop_total
    name: Warmwasser COP (Gesamt)
  - entity: sensor.eu08l_hp1_cooling_cop_daily
    name: Kühlen COP (Täglich)
  - entity: sensor.eu08l_hp1_cooling_cop_monthly
    name: Kühlen COP (Monatlich)
  - entity: sensor.eu08l_hp1_cooling_cop_total
    name: Kühlen COP (Gesamt)
```

### COP-Trend-Analyse

```yaml
type: history-graph
title: COP-Werte HP1 (Trend)
entities:
  - sensor.eu08l_hp1_heating_cop_daily
  - sensor.eu08l_hp1_hot_water_cop_daily
  - sensor.eu08l_hp1_cooling_cop_daily
hours_to_show: 168
refresh_interval: 30
```

### Energieeffizienz-Karte

```yaml
type: gauge
title: COP Heizen (Gesamt)
entity: sensor.eu08l_hp1_heating_cop_total
min: 0
max: 10
severity:
  green: 4
  yellow: 3
  red: 0
```

## Interpretation der Werte

### Typische COP-Werte für Wärmepumpen

- **COP > 4.0**: Sehr effizient (moderne Wärmepumpen)
- **COP 3.0 - 4.0**: Gut (durchschnittliche Wärmepumpen)
- **COP 2.0 - 3.0**: Akzeptabel (ältere oder schlecht dimensionierte Systeme)
- **COP < 2.0**: Ineffizient (möglicherweise Fehler oder falsche Dimensionierung)

### Faktoren, die den COP beeinflussen

- **Außentemperatur**: Höhere Temperaturen = besserer COP
- **Vorlauftemperatur**: Niedrigere Temperaturen = besserer COP
- **Betriebsmodus**: Heizen vs. Kühlen vs. Warmwasser haben unterschiedliche COPs
- **Systemzustand**: Verschmutzte Filter, defekte Komponenten reduzieren COP

## Häufige Probleme & Lösungen

### COP zeigt unknown

**Ursache**: In der jeweiligen Periode wurde noch keine elektrische Energie für diesen Modus erfasst – normal direkt nach einem Neustart oder bevor die Wärmepumpe in diesem Modus überhaupt gelaufen ist.

**Lösung**:
- Abwarten, bis die Wärmepumpe im entsprechenden Modus (Heizen/Warmwasser/Kühlen) gelaufen ist
- Prüfen Sie, ob die zugrundeliegenden Energieverbrauchssensoren existieren und Werte liefern

### COP-Werte erscheinen unrealistisch (sehr hoch oder sehr niedrig)

**Ursache**: Fehlerhafte Quellsensoren-Werte oder falsche Konfiguration.

**Lösung**:
- Prüfen Sie die Quellsensoren (thermal_energy und energy) auf realistische Werte
- Prüfen Sie die Einheiten (müssen beide in kWh sein)

### COP-Sensor aktualisiert sich nicht

**Ursache**: Quellsensoren aktualisieren sich nicht oder State-Tracking funktioniert nicht.

**Lösung**:
- Prüfen Sie, ob sich die Quellsensoren aktualisieren
- Prüfen Sie die Logs auf Fehlermeldungen
- Home Assistant-Neustart kann helfen

## Zusammenhang mit Energieverbrauchssensoren

Die COP-Sensoren basieren auf den [Energieverbrauchssensoren](Energieverbrauchsberechnung.md):

- **Thermische Energie**: Wird aus `compressor_thermal_energy_output_accumulated` (Modbus Register) berechnet
- **Elektrische Energie**: Wird aus `compressor_power_consumption_accumulated` (Modbus Register) oder externem Sensor berechnet

Für weitere Informationen zu den Energieverbrauchssensoren siehe [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md).

## Nächste Schritte

- [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md) - Detaillierte Informationen zu den Quellsensoren
- [Historische Daten übernehmen](historische-daten.md) - Offsets für historische Daten
- [Dashboard-Erstellung](features.md) - Weitere Dashboard-Beispiele

