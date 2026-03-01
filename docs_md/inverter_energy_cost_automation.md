# Automatisierung: Stromkostenanalyse für Wechselrichter

## Übersicht

Diese Automatisierung berechnet die täglichen Stromkosten basierend auf drei verschiedenen Zeitzonen mit unterschiedlichen Strompreisen. Sie trackt Energie-Import, Battery-Ladung und Battery-Entladung pro Zeitzone und berechnet drei verschiedene Kostenwerte.

## Strompreis-Zeitzonen

Die Automatisierung verwendet drei Zeitzonen mit unterschiedlichen Strompreisen:

| Zeitzone | Zeiträume | Preis |
|----------|-----------|-------|
| **Niedrig** | 02:00-06:00, 12:00-16:00 | 0,27 €/kWh |
| **Standard** | 06:00-12:00, 16:00-18:00, 21:00-02:00 | 0,34 €/kWh |
| **Hoch** | 18:00-21:00 | 0,39 €/kWh |

## Funktionsweise

### 1. Template-Sensoren für Leistungsmessung

Die Automatisierung nutzt drei Template-Sensoren, die die Leistung (W) in verschiedene Komponenten aufteilen:

#### Grid-Import (Netzbezug)
- **Sensor**: `sensor.inverter_grid_power_import`
- **Funktion**: Filtert nur positive Werte aus `sensor.inverter_grid_power`
- **Bedeutung**: Positive Werte = Energie wird aus dem Netz bezogen (kostenpflichtig)
- **Formel**: `grid_power if grid_power > 0 else 0`

#### Battery-Ladung
- **Sensor**: `sensor.inverter_battery_power_charge`
- **Funktion**: Konvertiert negative Battery-Power zu positiver Ladungs-Leistung
- **Bedeutung**: Negative Werte = Battery wird geladen
- **Formel**: `(-battery_power) if battery_power < 0 else 0`

#### Battery-Entladung
- **Sensor**: `sensor.inverter_battery_power_discharge`
- **Funktion**: Filtert nur positive Werte aus Battery-Power
- **Bedeutung**: Positive Werte = Battery wird entladen
- **Formel**: `battery_power if battery_power > 0 else 0`

### 2. Energie-Tracking pro Zeitzone

Eine Automatisierung läuft **alle 9 Sekunden** und trackt kontinuierlich:

1. **Energie-Import pro Zeitzone** (aus dem Netz)
2. **Battery-Ladung pro Zeitzone** (wann wurde die Battery geladen?)
3. **Battery-Entladung pro Zeitzone** (wann wurde die Battery entladen?)

#### Berechnung der Energie-Deltas

Für jeden 9-Sekunden-Zyklus wird die Energie wie folgt berechnet:

```
Energie (kWh) = (Leistung (W) / 1000) × (9 Sekunden / 3600 Sekunden/Stunde)
```

**Beispiel**:
- Grid-Power: 2000 W (Import)
- Energie-Delta: (2000 / 1000) × (9 / 3600) = 0.005 kWh

Diese Energie wird zur entsprechenden Zeitzone hinzugefügt.

#### Input Number Entitäten

Die kumulierten Energiewerte werden in folgenden `input_number` Entitäten gespeichert:

**Energie-Import pro Zeitzone:**
- `input_number.inverter_energy_import_low`
- `input_number.inverter_energy_import_standard`
- `input_number.inverter_energy_import_high`

**Battery-Ladung pro Zeitzone:**
- `input_number.inverter_battery_charge_low`
- `input_number.inverter_battery_charge_standard`
- `input_number.inverter_battery_charge_high`

**Battery-Entladung pro Zeitzone:**
- `input_number.inverter_battery_discharge_low`
- `input_number.inverter_battery_discharge_standard`
- `input_number.inverter_battery_discharge_high`

### 3. Reset um Mitternacht

Eine separate Automatisierung setzt alle `input_number` Entitäten um Mitternacht (00:00:00) auf 0 zurück, um die tägliche Berechnung zu starten.

## Die drei Kostenwerte

Die Automatisierung berechnet drei verschiedene Kostenwerte, die unterschiedliche Szenarien abbilden:

### 1. Tatsächliche Tageskosten

**Sensor**: `sensor.inverter_today_energy_cost`  
**Einheit**: €  
**Beschreibung**: Die tatsächlichen Kosten für den Tag, basierend auf dem Energie-Import pro Zeitzone.

#### Berechnung

```
Kosten_tatsächlich = (Import_Niedrig × 0,27€) + 
                     (Import_Standard × 0,34€) + 
                     (Import_Hoch × 0,39€)
```

**Formel im Template-Sensor**:
```yaml
{% set import_low = states('input_number.inverter_energy_import_low') | float(0) %}
{% set import_standard = states('input_number.inverter_energy_import_standard') | float(0) %}
{% set import_high = states('input_number.inverter_energy_import_high') | float(0) %}
{{ (import_low * 0.27 + import_standard * 0.34 + import_high * 0.39) | round(2) }}
```

**Beispiel**:
- Import Niedrig: 10 kWh × 0,27€ = 2,70€
- Import Standard: 15 kWh × 0,34€ = 5,10€
- Import Hoch: 5 kWh × 0,39€ = 1,95€
- **Gesamt**: 9,75€

**Wichtig**: Diese Kosten enthalten auch die Battery-Ladung, die aus dem Netz bezogen wurde.

### 2. Hypothetische Kosten ohne Battery-Ladung

**Sensor**: `sensor.inverter_today_energy_cost_without_battery`  
**Einheit**: €  
**Beschreibung**: Was es gekostet hätte, wenn die Battery **nicht** aus dem Netz geladen worden wäre.

#### Berechnung

Die Berechnung berücksichtigt:
- **Battery-Ladung wird abgezogen** (würde nicht stattfinden)
- **Battery-Entladung wird addiert** (müsste aus dem Netz bezogen werden)

```
Netto-Import_Zeitzone = Import_Zeitzone - Battery_Ladung_Zeitzone + Battery_Entladung_Zeitzone

Kosten_hypothetisch = (Netto-Import_Niedrig × 0,27€) + 
                     (Netto-Import_Standard × 0,34€) + 
                     (Netto-Import_Hoch × 0,39€)
```

**Formel im Template-Sensor**:
```yaml
{% set import_low = states('input_number.inverter_energy_import_low') | float(0) %}
{% set import_standard = states('input_number.inverter_energy_import_standard') | float(0) %}
{% set import_high = states('input_number.inverter_energy_import_high') | float(0) %}
{% set charge_low = states('input_number.inverter_battery_charge_low') | float(0) %}
{% set charge_standard = states('input_number.inverter_battery_charge_standard') | float(0) %}
{% set charge_high = states('input_number.inverter_battery_charge_high') | float(0) %}
{% set discharge_low = states('input_number.inverter_battery_discharge_low') | float(0) %}
{% set discharge_standard = states('input_number.inverter_battery_discharge_standard') | float(0) %}
{% set discharge_high = states('input_number.inverter_battery_discharge_high') | float(0) %}

{# Ohne Battery: Import - Ladung + Entladung #}
{% set net_import_low = import_low - charge_low + discharge_low %}
{% set net_import_standard = import_standard - charge_standard + discharge_standard %}
{% set net_import_high = import_high - charge_high + discharge_high %}

{{ (net_import_low * 0.27 + net_import_standard * 0.34 + net_import_high * 0.39) | round(2) }}
```

**Beispiel**:
- Import Niedrig: 10 kWh (davon 5 kWh Battery-Ladung)
- Import Standard: 15 kWh
- Import Hoch: 5 kWh
- Battery-Entladung Niedrig: 0 kWh
- Battery-Entladung Standard: 5 kWh (Battery wurde in Standard-Zeitzone entladen)

**Berechnung**:
- Netto-Import Niedrig: 10 - 5 + 0 = 5 kWh × 0,27€ = 1,35€
- Netto-Import Standard: 15 - 0 + 5 = 20 kWh × 0,34€ = 6,80€
- Netto-Import Hoch: 5 - 0 + 0 = 5 kWh × 0,39€ = 1,95€
- **Gesamt**: 10,10€

**Logik**: 
- Die Battery wurde in der günstigen Zeitzone (Niedrig: 0,27€) geladen
- Ohne Battery müsste der Verbrauch direkt aus dem Netz bezogen werden
- Die Battery-Entladung erfolgt in der Standard-Zeitzone (0,34€), daher wird diese Energie zu den hypothetischen Kosten addiert

### 3. Battery Ersparnis

**Sensor**: `sensor.inverter_today_battery_savings`  
**Einheit**: €  
**Beschreibung**: Die Ersparnis durch strategische Battery-Ladung in günstigen Zeitzonen.

#### Berechnung

```
Ersparnis = Hypothetische_Kosten - Tatsächliche_Kosten
```

**Formel im Template-Sensor**:
```yaml
{% set actual_cost = states('sensor.inverter_today_energy_cost') | float(0) %}
{% set hypothetical_cost = states('sensor.inverter_today_energy_cost_without_battery') | float(0) %}
{{ (hypothetical_cost - actual_cost) | round(2) }}
```

**Beispiel** (basierend auf obigen Werten):
- Tatsächliche Kosten: 9,75€
- Hypothetische Kosten: 10,10€
- **Ersparnis**: 10,10€ - 9,75€ = **0,35€**

**Warum gibt es eine Ersparnis?**
- Die Battery wurde in der günstigen Zeitzone (Niedrig: 0,27€) geladen
- Ohne Battery müsste der Verbrauch in der teureren Zeitzone (Standard: 0,34€) direkt aus dem Netz bezogen werden
- Die Ersparnis entsteht durch die **Preisdifferenz** zwischen Ladungs- und Verbrauchszeit

## Zusammenfassung der Berechnungslogik

```
┌─────────────────────────────────────────────────────────────┐
│ TATSÄCHLICHE KOSTEN (mit Battery-Ladung aus dem Netz)     │
├─────────────────────────────────────────────────────────────┤
│ Import Niedrig:   10 kWh × 0,27€ = 2,70€                  │
│   └─ davon Battery-Ladung: 5 kWh                            │
│ Import Standard:  15 kWh × 0,34€ = 5,10€                  │
│ Import Hoch:       5 kWh × 0,39€ = 1,95€                   │
│ ─────────────────────────────────────────────────────────── │
│ GESAMT:           30 kWh             9,75€                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ HYPOTHETISCHE KOSTEN (ohne Battery-Ladung)                 │
├─────────────────────────────────────────────────────────────┤
│ Annahme: Battery-Ladung (5 kWh) würde nicht stattfinden     │
│          Battery-Entladung (5 kWh) müsste aus dem Netz     │
│          (fällt in Standard-Zeitzone an: 0,34€)            │
│                                                             │
│ Netto-Import Niedrig:   (10-5) × 0,27€ = 1,35€           │
│ Netto-Import Standard:  (15+5) × 0,34€ = 6,80€  ← +5 kWh! │
│ Netto-Import Hoch:       5 × 0,39€ = 1,95€                │
│ ─────────────────────────────────────────────────────────── │
│ GESAMT:           25 kWh            10,10€                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ERSPARNIS durch strategische Battery-Ladung                │
├─────────────────────────────────────────────────────────────┤
│ Ersparnis = 10,10€ - 9,75€ = 0,35€                        │
│                                                             │
│ Grund: Battery wurde in günstiger Zeitzone (0,27€)         │
│        geladen, statt Verbrauch in teurerer Zeitzone       │
│        (0,34€) zu decken                                   │
└─────────────────────────────────────────────────────────────┘
```

## Technische Details

### Automatisierung: Energie-Tracking

**Trigger**: Alle 9 Sekunden (`time_pattern: seconds: "/9"`)

**Aktionen**:
1. Bestimmt aktuelle Zeitzone basierend auf Tageszeit
2. Liest aktuelle Leistungswerte:
   - `sensor.inverter_grid_power` (Grid-Import)
   - `sensor.inverter_battery_power` (Battery-Ladung/Entladung)
3. Berechnet Energie-Delta für 9 Sekunden
4. Kumuliert Energie in entsprechender `input_number` Entität

**Zeitzonen-Logik**:
- **Niedrig**: `(hour >= 2 and hour < 6) or (hour >= 12 and hour < 16)`
- **Hoch**: `hour >= 18 and hour < 21`
- **Standard**: Alle anderen Zeiten (Fallback)

### Automatisierung: Mitternacht-Reset

**Trigger**: Um Mitternacht (`time: at: "00:00:00"`)

**Aktionen**:
- Setzt alle 9 `input_number` Entitäten auf 0 zurück

## Verwendete Sensoren

### Quellsensoren (müssen angepasst werden)

- `sensor.inverter_grid_power` - Grid-Power Sensor (W)
  - Positive Werte = Import aus dem Netz
  - Negative Werte = Export ins Netz
- `sensor.inverter_battery_power` - Battery-Power Sensor (W)
  - Positive Werte = Entladung
  - Negative Werte = Ladung

### Template-Sensoren (automatisch erstellt)

- `sensor.inverter_grid_power_import` - Nur Grid-Import (W)
- `sensor.inverter_battery_power_charge` - Nur Battery-Ladung (W)
- `sensor.inverter_battery_power_discharge` - Nur Battery-Entladung (W)
- `sensor.inverter_current_electricity_price` - Aktueller Strompreis (€/kWh)
- `sensor.inverter_today_energy_cost` - Tatsächliche Tageskosten (€)
- `sensor.inverter_today_energy_cost_without_battery` - Hypothetische Kosten (€)
- `sensor.inverter_today_battery_savings` - Battery Ersparnis (€)

### Input Number Entitäten (kumulierte Energie)

- 9 Entitäten für Energie-Import, Battery-Ladung und Battery-Entladung pro Zeitzone

## Anpassung für andere Systeme

Um die Automatisierung für andere Systeme zu verwenden, müssen folgende Variablen in der Automatisierung angepasst werden:

1. **Quellsensoren** (in `variables:` Abschnitt):
   - `source_grid_power`: Grid-Power Sensor (z.B. `"sensor.inverter_grid_power"`)
   - `source_battery_power`: Battery-Power Sensor (z.B. `"sensor.inverter_battery_power"`)

2. **Template-Sensoren** (in `template:` Abschnitt):
   - Quellsensoren in den Template-Sensoren anpassen

3. **Strompreise** (in Template-Sensoren):
   - Preise in den Berechnungsformeln anpassen (aktuell: 0.27, 0.34, 0.39)

4. **Zeitzonen** (in Automatisierung):
   - Zeiträume für Niedrig/Standard/Hoch anpassen

## Visualisierung

Die drei Kostenwerte können in einer History-Graph Card visualisiert werden:

```yaml
type: history-graph
title: Energie-Kosten Vergleich
hours_to_show: 24
refresh_interval: 60
entities:
  - entity: sensor.inverter_today_energy_cost
    name: Tatsächliche Kosten
  - entity: sensor.inverter_today_energy_cost_without_battery
    name: Kosten ohne Battery
  - entity: sensor.inverter_today_battery_savings
    name: Battery Ersparnis
```

## Wichtige Hinweise

1. **Genauigkeit**: Die Automatisierung trackt alle 9 Sekunden, was eine hohe Genauigkeit gewährleistet
2. **Ressourcenverbrauch**: Die Automatisierung läuft kontinuierlich, sollte aber bei modernen Home Assistant Installationen kein Problem darstellen
3. **Neustart**: Bei einem Neustart von Home Assistant werden die `input_number` Werte beibehalten (persistiert)
4. **Zeitzonen**: Die Zeitzonen sind fest codiert und müssen bei Bedarf angepasst werden
5. **Strompreise**: Die Preise sind fest codiert und müssen bei Tarifänderungen angepasst werden

