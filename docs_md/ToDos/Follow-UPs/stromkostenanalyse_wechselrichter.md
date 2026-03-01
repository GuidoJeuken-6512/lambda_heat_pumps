# Stromkostenanalyse für Wechselrichter

## Zusammenfassung: Empfohlene Lösung

**Beste Umsetzung**: **Utility Meter Integration** + Template-Sensor für Energie-Kumulation

**Warum?**
- ✅ Nutzt native Home Assistant Features
- ✅ Minimaler Konfigurationsaufwand
- ✅ Robust und wartungsarm
- ✅ Automatische Fehlerbehandlung
- ✅ Nutzt vorhandene Sensoren optimal

**Alternative**: Template-Sensor mit History-Analyse von `sensor.inverter_today_energy_import`

**Nicht empfohlen**: Automatisierung alle 9 Sekunden (zu ressourcenintensiv und komplex)

## Ziel

Erstellung von Template-Sensoren zur Berechnung:
1. **Aktuelle Tageskosten**: Kosten basierend auf `sensor.inverter_today_energy_import` und den Strompreis-Zeitzonen
2. **Hypothetische Kosten ohne Battery-Ladung**: Was es gekostet hätte, wenn die Battery nicht aus dem Netz geladen worden wäre

## Strompreis-Zeitzonen

- **Niedrig (0,27€/kWh)**: 02:00-06:00, 12:00-16:00
- **Standard (0,34€/kWh)**: 06:00-12:00, 16:00-18:00, 21:00-02:00
- **Hoch (0,39€/kWh)**: 18:00-21:00

## Implementierung

### 1. Template-Sensor: Aktueller Strompreis basierend auf Tageszeit

Erstellt einen Sensor, der den aktuellen Strompreis basierend auf der Tageszeit zurückgibt.

**Datei**: `configuration.yaml` - `template:` Abschnitt

### 2. Template-Sensor: Tageskosten (aktuell)

Berechnet die aktuellen Kosten für den Tag basierend auf:
- Kumulierter Energieverbrauch pro Zeitzone (durch Automatisierung alle 9 Sekunden)
- Preis pro Zeitzone

**Implementierung**: Automatisierung trackt kontinuierlich den Verbrauch pro Zeitzone (siehe Option 4).

### 3. Template-Sensor: Hypothetische Kosten ohne Battery-Ladung

Berechnet, was es gekostet hätte, wenn die Battery nicht geladen worden wäre.

**Wichtig**: Die Berechnung hängt davon ab, **wann** die Battery geladen wurde (in welcher Zeitzone).

**Ansatz A: Vereinfacht (wenn Ladungszeit unbekannt)**
- `sensor.inverter_today_energy_import` - `sensor.inverter_today_battery_charge`
- Multipliziert mit dem gewichteten Durchschnittspreis
- **Nachteil**: Ungenau, wenn Battery in günstigen Zeitzonen geladen wurde

**Ansatz B: Präzise (wenn Ladungszeit bekannt)**
- Tracke Battery-Ladung pro Zeitzone separat
- Subtrahiere nur die Battery-Ladung aus der entsprechenden Zeitzone
- **Vorteil**: Genau, zeigt echte Ersparnis durch günstige Ladung

**Hinweis**: Die Inverter-Verluste (`sensor.inverter_today_losses`) bleiben in beiden Berechnungen enthalten, da sie unabhängig von der Battery-Ladung anfallen.

### 4. Template-Sensor: Ersparnis durch Battery-Ladung

Differenz zwischen hypothetischen Kosten und tatsächlichen Kosten.

**Berechnung**:
```
Ersparnis = Tatsächliche Kosten - Hypothetische Kosten
```

**Beispiel**:
- Tatsächliche Kosten: 5,00€ (inkl. Battery-Ladung in günstiger Zeitzone)
- Hypothetische Kosten: 6,50€ (ohne Battery-Ladung, hätte in teurerer Zeitzone geladen werden müssen)
- **Ersparnis**: 1,50€

## Kostenberechnung: Battery-Ladung aus dem Netz vs. ohne Battery-Ladung

### Problemstellung

Wir wollen berechnen:
1. **Tatsächliche Kosten**: Was kostet es tatsächlich, wenn die Battery aus dem Netz geladen wird?
2. **Hypothetische Kosten**: Was hätte es gekostet, wenn die Battery NICHT aus dem Netz geladen worden wäre?

### Herausforderung

Die Battery wird **strategisch in günstigen Zeitzonen geladen** (z.B. 02:00-06:00 mit 0,27€/kWh). Wenn wir die Battery-Ladung einfach vom Gesamtimport abziehen, erhalten wir nicht die echten hypothetischen Kosten.

### Lösungsansatz

#### Schritt 1: Energie pro Zeitzone tracken

**Tatsächliche Situation**:
```
Zeitzone Niedrig (0,27€):  10 kWh Import (davon 5 kWh Battery-Ladung)
Zeitzone Standard (0,34€): 15 kWh Import
Zeitzone Hoch (0,39€):      5 kWh Import
────────────────────────────────────────────
Gesamt:                    30 kWh Import
Tatsächliche Kosten:       10×0,27 + 15×0,34 + 5×0,39 = 8,55€
```

#### Schritt 2: Hypothetische Kosten berechnen

**Szenario ohne Battery-Ladung**:
- Die 5 kWh Battery-Ladung würde **nicht** in der günstigen Zeitzone stattfinden
- Stattdessen müsste der Verbrauch (der normalerweise durch Battery gedeckt wird) **später** aus dem Netz bezogen werden
- **Frage**: In welcher Zeitzone würde dieser Verbrauch anfallen?

**Option A: Vereinfacht (Konservativ)**
```
Hypothetische Kosten = (Gesamtimport - Battery-Ladung) × Durchschnittspreis
                    = (30 - 5) × 0,321€ = 8,03€
Ersparnis = 8,55€ - 8,03€ = 0,52€
```
**Problem**: Unterschätzt die Ersparnis, da Battery in günstiger Zeitzone geladen wurde

**Option B: Präzise (Empfohlen)**
```
1. Tracke Battery-Ladung pro Zeitzone:
   - Battery-Ladung Niedrig: 5 kWh
   - Battery-Ladung Standard: 0 kWh
   - Battery-Ladung Hoch: 0 kWh

2. Berechne hypothetische Kosten:
   - Ohne Battery-Ladung: 30 - 5 = 25 kWh Import
   - Aber: Diese 25 kWh würden zu anderen Zeiten benötigt werden
   - Annahme: Verbrauch würde in Standard-Zeitzone anfallen (0,34€)
   
   Hypothetische Kosten = (10-5)×0,27 + (15+5)×0,34 + 5×0,39
                        = 5×0,27 + 20×0,34 + 5×0,39
                        = 1,35 + 6,80 + 1,95 = 10,10€
   
   Ersparnis = 10,10€ - 8,55€ = 1,55€
```

**Option C: Realistisch (Beste Annahme)**
```
Die Battery wird in günstiger Zeitzone geladen und später entladen.
Ohne Battery müsste der Verbrauch direkt aus dem Netz bezogen werden.

1. Tatsächliche Kosten (mit Battery):
   - Import Niedrig: 10 kWh × 0,27€ = 2,70€
   - Import Standard: 15 kWh × 0,34€ = 5,10€
   - Import Hoch: 5 kWh × 0,39€ = 1,95€
   - Gesamt: 9,75€

2. Hypothetische Kosten (ohne Battery):
   - Die 5 kWh Battery-Ladung würde nicht stattfinden
   - Aber: Der Verbrauch, der durch Battery gedeckt wird, müsste direkt aus dem Netz
   - Annahme: Dieser Verbrauch fällt in Standard-Zeitzone an (0,34€)
   
   Import Niedrig: (10-5) × 0,27€ = 1,35€
   Import Standard: (15+5) × 0,34€ = 6,80€  (5 kWh mehr, da Battery fehlt)
   Import Hoch: 5 × 0,39€ = 1,95€
   Gesamt: 10,10€
   
3. Ersparnis = 10,10€ - 9,75€ = 0,35€
```

### Zusammenfassung: Berechnungslogik

```
┌─────────────────────────────────────────────────────────────┐
│ TATSÄCHLICHE KOSTEN (mit Battery-Ladung aus dem Netz)       │
├─────────────────────────────────────────────────────────────┤
│ Import Niedrig:   10 kWh × 0,27€ = 2,70€                    │
│   └─ davon Battery-Ladung: 5 kWh                            │
│ Import Standard:  15 kWh × 0,34€ = 5,10€                   │
│ Import Hoch:       5 kWh × 0,39€ = 1,95€                   │
│ ─────────────────────────────────────────────────────────── │
│ GESAMT:           30 kWh             9,75€                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ HYPOTHETISCHE KOSTEN (ohne Battery-Ladung)                  │
├─────────────────────────────────────────────────────────────┤
│ Annahme: Battery-Ladung (5 kWh) würde nicht stattfinden     │
│          Verbrauch müsste direkt aus dem Netz              │
│          (fällt in Standard-Zeitzone an: 0,34€)            │
│                                                             │
│ Import Niedrig:   (10-5) × 0,27€ = 1,35€                  │
│ Import Standard:  (15+5) × 0,34€ = 6,80€  ← 5 kWh mehr!    │
│ Import Hoch:       5 × 0,39€ = 1,95€                       │
│ ─────────────────────────────────────────────────────────── │
│ GESAMT:           25 kWh            10,10€                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ERSPARNIS durch strategische Battery-Ladung                  │
├─────────────────────────────────────────────────────────────┤
│ Ersparnis = 10,10€ - 9,75€ = 0,35€                         │
│                                                             │
│ Grund: Battery wurde in günstiger Zeitzone (0,27€)         │
│        geladen, statt Verbrauch in teurerer Zeitzone       │
│        (0,34€) zu decken                                    │
└─────────────────────────────────────────────────────────────┘
```

### Implementierung

**Für präzise Berechnung benötigen wir**:
1. Energie-Import pro Zeitzone (bereits geplant)
2. **Battery-Ladung pro Zeitzone** (muss auch getrackt werden!)

**Template-Sensor für Battery-Ladung pro Zeitzone**:
```yaml
template:
  - sensor:
    - name: "Inverter Battery Charge - Niedrig"
      unique_id: inverter_battery_charge_low
      state: >
        {# Nutze History von sensor.inverter_today_battery_charge
           und sensor.inverter_battery_power, um zu bestimmen,
           wann die Battery geladen wurde #}
```

**ODER - Vereinfacht**:
- Nutze `sensor.inverter_today_battery_charge` (Gesamt)
- Annahme: Battery wird hauptsächlich in günstiger Zeitzone geladen
- Subtrahiere Battery-Ladung nur von Niedrig-Zeitzone

### Genaueste Berechnungsformel

**Tatsächliche Kosten**:
```
Kosten_tatsächlich = Σ(Import_Zeitzone_i × Preis_Zeitzone_i)
```

**Hypothetische Kosten (ohne Battery)**:
```
Netto-Import_Zeitzone_i = Import_Zeitzone_i - Battery_Ladung_Zeitzone_i + Battery_Entladung_Zeitzone_i

Kosten_hypothetisch = Σ(Netto-Import_Zeitzone_i × Preis_Zeitzone_i)
```

**Ersparnis**:
```
Ersparnis = Kosten_hypothetisch - Kosten_tatsächlich
```

**Erklärung**:
- **Battery-Ladung** wird abgezogen (würde nicht stattfinden)
- **Battery-Entladung** wird addiert (müsste aus dem Netz bezogen werden)
- Die Berechnung erfolgt **pro Zeitzone**, um die Preisdifferenz zu berücksichtigen

### Wichtige Erkenntnisse

1. **Einfaches Abziehen der Battery-Ladung ist nicht korrekt**
   - Die Battery wird in günstigen Zeitzonen geladen (0,27€)
   - Ohne Battery müsste der Verbrauch in teureren Zeitzonen gedeckt werden (0,34€ oder 0,39€)
   - Die Ersparnis entsteht durch die **Preisdifferenz** zwischen Ladungs- und Verbrauchszeit

2. **Für genaue Berechnung brauchen wir**:
   - ✅ Energie-Import pro Zeitzone (wird getrackt)
   - ✅ Battery-Ladung pro Zeitzone (wird getrackt)
   - ✅ Battery-Entladung pro Zeitzone (wird getrackt für genaueste Berechnung)

3. **Warum Battery-Entladung wichtig ist**:
   - Wenn die Battery entladen wird, deckt sie Verbrauch, der sonst aus dem Netz käme
   - Diese Entladung muss in der hypothetischen Berechnung berücksichtigt werden
   - Die Entladung erfolgt in der Zeitzone, in der sie stattfindet (kann teurer sein als die Ladung)

## Empfohlene Lösung (Basierend auf verfügbaren Sensoren)

### Beste Umsetzung: Utility Meter + Template-Sensor mit History

**Warum diese Lösung?**
1. **`sensor.inverter_today_energy_import`** wird bereits täglich um Mitternacht auf 0 gesetzt
2. Home Assistant speichert automatisch die **History** aller Sensoren
3. Wir können die History nutzen, um zu sehen, wie viel Energie in welcher Zeitzone verbraucht wurde
4. **Utility Meter** kann automatisch pro Zeitzone tracken, wenn wir die richtige Quelle nutzen

**Implementierungsstrategie**:

**Schritt 1**: Template-Sensor, der die Energie kumuliert (aus `sensor.inverter_grid_power`)
```yaml
template:
  - sensor:
    - name: "Inverter Grid Energy Import"
      unique_id: inverter_grid_energy_import
      unit_of_measurement: "kWh"
      device_class: energy
      state_class: total_increasing
      state: >
        {% set current = states('sensor.inverter_grid_energy_import') | default(0) | float(0) %}
        {% set grid_power = states('sensor.inverter_grid_power') | float(0) %}
        {% if grid_power > 0 %}
          {{ (current + (grid_power / 1000 / 3600)) | round(6) }}
        {% else %}
          {{ current }}
        {% endif %}
```

**Schritt 2**: Utility Meter für jede Zeitzone
**Schritt 3**: Automatisierung wechselt Utility Meter basierend auf Zeitzone

**ODER - Einfacherer Ansatz mit History-Analyse**:

Da `sensor.inverter_today_energy_import` bereits täglich resetet wird, können wir die History dieses Sensors nutzen, um den Verbrauch pro Zeitzone zu berechnen. Dies erfordert einen Template-Sensor, der die History analysiert.

## Technische Details

### Problem: Gewichtete Preisberechnung

**Wichtig**: Ein einfacher gewichteter Durchschnittspreis basierend nur auf der Anzahl der Stunden ist **nicht korrekt**, da er nur dann stimmt, wenn der Stromverbrauch über alle Zeitslots gleich ist.

**Korrekte Berechnung**:
```
Gesamtkosten = Σ(Energie_Zeitslot_i × Preis_Zeitslot_i)
Gewichteter Durchschnittspreis = Gesamtkosten / Gesamtenergie
```

**Beispiel**:
- Zeitslot 1 (Niedrig): 2 kWh × 0,27€ = 0,54€
- Zeitslot 2 (Standard): 5 kWh × 0,34€ = 1,70€
- Zeitslot 3 (Hoch): 1 kWh × 0,39€ = 0,39€
- **Gesamt**: 8 kWh, **Gesamtkosten**: 2,63€, **Durchschnitt**: 0,329€/kWh

### Lösungsansätze

#### Option 1: Energieverbrauch pro Zeitslot tracken (Empfohlen)

Für eine **genaue Berechnung** muss der Energieverbrauch pro Zeitslot getrackt werden:

1. **Utility Meter Integration** verwenden, um den Verbrauch pro Zeitslot zu erfassen
2. **Template-Sensor** mit History-Funktion, der den Verbrauch pro Zeitslot speichert
3. **Integration** (z.B. Recorder) nutzen, um historische Daten pro Zeitslot abzufragen

**Vorteil**: Präzise Kostenberechnung basierend auf tatsächlichem Verbrauch

#### Option 2: Näherung mit gleichmäßiger Verteilung (Einfach, aber ungenau)

Annahme: Der Verbrauch ist gleichmäßig über den Tag verteilt.

**Gewichteter Durchschnittspreis** (nur für Näherung):
- Niedrig: 8 Stunden (02:00-06:00 = 4h, 12:00-16:00 = 4h) × 0,27€
- Standard: 11 Stunden (06:00-12:00 = 6h, 16:00-18:00 = 2h, 21:00-02:00 = 3h) × 0,34€
- Hoch: 3 Stunden (18:00-21:00) × 0,39€
- **Durchschnitt**: ~0,321€/kWh (nur wenn Verbrauch gleichmäßig)

**Nachteil**: Ungenau, wenn der Verbrauch nicht gleichmäßig verteilt ist

#### Option 3: Template-Sensor mit History-Attributen

Nutze die History-Funktion von Home Assistant, um den Verbrauch pro Zeitslot zu berechnen:

```yaml
template:
  - sensor:
    - name: "Inverter Energy Cost Today"
      state: >
        {% set now = now() %}
        {% set midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) %}
        {% set total_cost = 0.0 %}
        {% set total_energy = 0.0 %}
        
        {# Berechne Verbrauch und Kosten pro Zeitslot #}
        {% for hour in range(0, 24) %}
          {% set slot_start = midnight + timedelta(hours=hour) %}
          {% set slot_end = midnight + timedelta(hours=hour+1) %}
          {% set price = ... %} {# Preis basierend auf Zeitslot #}
          {% set energy = ... %} {# Energie aus History #}
          {% set total_cost = total_cost + (energy * price) %}
          {% set total_energy = total_energy + energy %}
        {% endfor %}
        
        {{ (total_cost / total_energy) if total_energy > 0 else 0 }}
```

**Vorteil**: Genau, nutzt vorhandene Daten
**Nachteil**: Komplexer, benötigt History-Zugriff

#### Option 4: Utility Meter Integration (BESTE LÖSUNG) ⭐⭐⭐

**Nutze die Utility Meter Integration** von Home Assistant, um automatisch den Energieverbrauch pro Zeitzone zu tracken:

**Funktionsweise**:
1. Utility Meter erstellt automatisch Sensoren für jede Zeitzone
2. Nutzt `sensor.inverter_grid_power` als Quelle (nur positive Werte)
3. Automatisches Tracking basierend auf Perioden (Zeitzonen)
4. Automatischer Reset um Mitternacht
5. Keine manuelle Automatisierung nötig!

**Vorteile**:
- ✅ **Einfachste Lösung**: Minimaler Konfigurationsaufwand
- ✅ **Nativ unterstützt**: Home Assistant Feature, keine Custom-Logik
- ✅ **Robust**: Automatische Fehlerbehandlung
- ✅ **Präzise**: Nutzt die automatisch gespeicherte History
- ✅ **Wartungsarm**: Keine komplexen Automatisierungen

**Implementierung für genaue Berechnung**:

```yaml
# configuration.yaml

# Template-Sensoren: Trenne Import/Export und Battery-Ladung/Entladung
template:
  - sensor:
    # Grid-Import (nur positive Werte = aus dem Netz)
    - name: "Inverter Grid Power Import"
      unique_id: inverter_grid_power_import
      unit_of_measurement: "W"
      device_class: power
      state: >
        {% set grid_power = states('sensor.inverter_grid_power') | float(0) %}
        {{ grid_power if grid_power > 0 else 0 }}
    
    # Battery-Ladung (nur negative Werte = wird geladen)
    - name: "Inverter Battery Power Charge"
      unique_id: inverter_battery_power_charge
      unit_of_measurement: "W"
      device_class: power
      state: >
        {% set battery_power = states('sensor.inverter_battery_power') | float(0) %}
        {{ (-battery_power) if battery_power < 0 else 0 }}
    
    # Battery-Entladung (nur positive Werte = wird entladen)
    - name: "Inverter Battery Power Discharge"
      unique_id: inverter_battery_power_discharge
      unit_of_measurement: "W"
      device_class: power
      state: >
        {% set battery_power = states('sensor.inverter_battery_power') | float(0) %}
        {{ battery_power if battery_power > 0 else 0 }}

# Utility Meter für Energie-Import pro Zeitzone
utility_meter:
  inverter_energy_import_low:
    source: sensor.inverter_grid_power_import
    cycle: daily
    tariffs:
      - low_price
  inverter_energy_import_standard:
    source: sensor.inverter_grid_power_import
    cycle: daily
    tariffs:
      - standard_price
  inverter_energy_import_high:
    source: sensor.inverter_grid_power_import
    cycle: daily
    tariffs:
      - high_price

# Utility Meter für Battery-Ladung pro Zeitzone
utility_meter:
  inverter_battery_charge_low:
    source: sensor.inverter_battery_power_charge
    cycle: daily
    tariffs:
      - low_price
  inverter_battery_charge_standard:
    source: sensor.inverter_battery_power_charge
    cycle: daily
    tariffs:
      - standard_price
  inverter_battery_charge_high:
    source: sensor.inverter_battery_power_charge
    cycle: daily
    tariffs:
      - high_price

# Utility Meter für Battery-Entladung pro Zeitzone (optional, für genauere Berechnung)
utility_meter:
  inverter_battery_discharge_low:
    source: sensor.inverter_battery_power_discharge
    cycle: daily
    tariffs:
      - low_price
  inverter_battery_discharge_standard:
    source: sensor.inverter_battery_power_discharge
    cycle: daily
    tariffs:
      - standard_price
  inverter_battery_discharge_high:
    source: sensor.inverter_battery_power_discharge
    cycle: daily
    tariffs:
      - high_price

# Automatisierung: Wechsle alle Utility Meter basierend auf Zeitzone
automation:
  - id: switch_utility_meters_by_price_zone
    alias: "Switch Utility Meters by Price Zone"
    trigger:
      - platform: time
        at: "02:00:00"  # Start Niedrig
      - platform: time
        at: "06:00:00"  # Start Standard
      - platform: time
        at: "12:00:00"  # Start Niedrig
      - platform: time
        at: "16:00:00"  # Start Standard
      - platform: time
        at: "18:00:00"  # Start Hoch
      - platform: time
        at: "21:00:00"  # Start Standard
    action:
      - service: utility_meter.select_tariff
        target:
          entity_id:
            - utility_meter.inverter_energy_import_low
            - utility_meter.inverter_energy_import_standard
            - utility_meter.inverter_energy_import_high
            - utility_meter.inverter_battery_charge_low
            - utility_meter.inverter_battery_charge_standard
            - utility_meter.inverter_battery_charge_high
            - utility_meter.inverter_battery_discharge_low
            - utility_meter.inverter_battery_discharge_standard
            - utility_meter.inverter_battery_discharge_high
        data:
          tariff: >
            {% set hour = now().hour %}
            {% if (hour >= 2 and hour < 6) or (hour >= 12 and hour < 16) %}
              low_price
            {% elif hour >= 18 and hour < 21 %}
              high_price
            {% else %}
              standard_price
            {% endif %}

# Template-Sensoren für Kostenberechnung
template:
  - sensor:
    # Tatsächliche Tageskosten
    - name: "Inverter Today Energy Cost"
      unique_id: inverter_today_energy_cost
      unit_of_measurement: "€"
      state: >
        {% set import_low = states('sensor.inverter_energy_import_low_low_price') | float(0) %}
        {% set import_standard = states('sensor.inverter_energy_import_standard_standard_price') | float(0) %}
        {% set import_high = states('sensor.inverter_energy_import_high_high_price') | float(0) %}
        {{ (import_low * 0.27 + import_standard * 0.34 + import_high * 0.39) | round(2) }}
    
    # Hypothetische Kosten ohne Battery
    - name: "Inverter Today Energy Cost Without Battery"
      unique_id: inverter_today_energy_cost_without_battery
      unit_of_measurement: "€"
      state: >
        {% set import_low = states('sensor.inverter_energy_import_low_low_price') | float(0) %}
        {% set import_standard = states('sensor.inverter_energy_import_standard_standard_price') | float(0) %}
        {% set import_high = states('sensor.inverter_energy_import_high_high_price') | float(0) %}
        {% set charge_low = states('sensor.inverter_battery_charge_low_low_price') | float(0) %}
        {% set charge_standard = states('sensor.inverter_battery_charge_standard_standard_price') | float(0) %}
        {% set charge_high = states('sensor.inverter_battery_charge_high_high_price') | float(0) %}
        {% set discharge_low = states('sensor.inverter_battery_discharge_low_low_price') | float(0) %}
        {% set discharge_standard = states('sensor.inverter_battery_discharge_standard_standard_price') | float(0) %}
        {% set discharge_high = states('sensor.inverter_battery_discharge_high_high_price') | float(0) %}
        {# Ohne Battery: Import - Ladung + Entladung (Entladung muss aus Netz bezogen werden) #}
        {% set net_import_low = import_low - charge_low + discharge_low %}
        {% set net_import_standard = import_standard - charge_standard + discharge_standard %}
        {% set net_import_high = import_high - charge_high + discharge_high %}
        {{ (net_import_low * 0.27 + net_import_standard * 0.34 + net_import_high * 0.39) | round(2) }}
    
    # Ersparnis durch Battery
    - name: "Inverter Today Battery Savings"
      unique_id: inverter_today_battery_savings
      unit_of_measurement: "€"
      state: >
        {% set actual_cost = states('sensor.inverter_today_energy_cost') | float(0) %}
        {% set hypothetical_cost = states('sensor.inverter_today_energy_cost_without_battery') | float(0) %}
        {{ (hypothetical_cost - actual_cost) | round(2) }}
```

**Hinweis**: Utility Meter funktioniert am besten mit `state_class: total_increasing` Sensoren. Da `sensor.inverter_grid_power` eine Leistung (W) ist, nicht Energie (kWh), müssen wir einen Template-Sensor erstellen, der die Energie kumuliert, ODER wir nutzen `sensor.inverter_today_energy_import` direkt.

**Alternative mit `sensor.inverter_today_energy_import`**:
Da dieser Sensor bereits täglich resetet wird, können wir die History nutzen, um den Verbrauch pro Zeitzone zu berechnen (siehe Option 5).

#### Option 5: Automatisierung alle 9 Sekunden (Alternative, wenn Utility Meter nicht funktioniert)

**Kontinuierliches Tracking** des Energieverbrauchs pro Zeitzone durch eine Automatisierung:

**Funktionsweise**:
1. **Automatisierung** läuft alle 9 Sekunden
2. Liest Energieverbrauch:
   - **Option A**: `sensor.inverter_grid_power` (nur positive Werte = Import aus dem Netz)
     - Positive Werte = Energie wird aus dem Netz bezogen (kostenpflichtig)
     - Negative Werte = Energie wird ins Netz eingespeist (wird ignoriert für Kostenberechnung)
   - **Option B**: `sensor.bitshake_smartmeterreader_ebz_e_inop` (kumulativer Wert)
     - Delta-Berechnung: Aktueller Wert - Letzter Wert
     - Vorteil: Höhere Genauigkeit (direkte Zählermessung)
3. Bestimmt aktuelle Zeitzone und Preis basierend auf Tageszeit
4. Berechnet Energie-Delta:
   - **Option A**: `(grid_power / 1000) * (9 / 3600)` kWh
   - **Option B**: `(aktueller_zählerwert - letzter_zählerwert)` kWh
5. Kumuliert Energie pro Zeitzone in `input_number` Entitäten
6. Um Mitternacht: Zähler zurücksetzen

**Vorteile**:
- ✅ **Präzise**: Erfasst tatsächlichen Verbrauch pro Zeitzone
- ✅ **Echtzeit**: Kosten können jederzeit berechnet werden
- ✅ **Keine History nötig**: Daten werden kontinuierlich gesammelt

**Nachteile**:
- ❌ **Ressourcenintensiv**: Läuft alle 9 Sekunden
- ❌ **Komplex**: Viele Automatisierungen nötig
- ❌ **Fehleranfällig**: Bei Neustart können Daten verloren gehen
- ❌ **Wartungsaufwand**: Manuelle Reset-Logik nötig

**Implementierung**:

```yaml
# input_number für kumulierte Energie pro Zeitzone
input_number:
  inverter_energy_price_low:
    name: "Inverter Energy - Niedrig"
    min: 0
    max: 1000
    step: 0.001
    unit_of_measurement: "kWh"
  inverter_energy_price_standard:
    name: "Inverter Energy - Standard"
    min: 0
    max: 1000
    step: 0.001
    unit_of_measurement: "kWh"
  inverter_energy_price_high:
    name: "Inverter Energy - Hoch"
    min: 0
    max: 1000
    step: 0.001
    unit_of_measurement: "kWh"

# Template-Sensor für Kostenberechnung
template:
  - sensor:
    - name: "Inverter Today Energy Cost"
      unique_id: inverter_today_energy_cost
      unit_of_measurement: "€"
      state: >
        {% set energy_low = states('input_number.inverter_energy_price_low') | float(0) %}
        {% set energy_standard = states('input_number.inverter_energy_price_standard') | float(0) %}
        {% set energy_high = states('input_number.inverter_energy_price_high') | float(0) %}
        {{ (energy_low * 0.27 + energy_standard * 0.34 + energy_high * 0.39) | round(2) }}

# Automatisierung (in automations.yaml)
- id: track_inverter_energy_by_price_zone
  alias: "Track Inverter Energy by Price Zone"
  trigger:
    - platform: time_pattern
      seconds: "/9"  # Alle 9 Sekunden
  action:
    - choose:
        # Niedrig: 02:00-06:00, 12:00-16:00
        - conditions:
            - condition: or
              conditions:
                - condition: time
                  after: "02:00:00"
                  before: "06:00:00"
                - condition: time
                  after: "12:00:00"
                  before: "16:00:00"
          sequence:
            - service: input_number.set_value
              target:
                entity_id: input_number.inverter_energy_price_low
              data:
                value: >
                  {% set current = states('input_number.inverter_energy_price_low') | float(0) %}
                  {# Option A: Wechselrichter-Sensor (Echtzeit-Leistung) #}
                  {% set grid_power = states('sensor.inverter_grid_power') | float(0) %}
                  {# Nur positive Werte = Import aus dem Netz (kostenpflichtig) #}
                  {% if grid_power > 0 %}
                    {# Energie in 9 Sekunden: (W / 1000) * (9s / 3600s/h) = kWh #}
                    {{ (current + (grid_power / 1000 * 9 / 3600)) | round(6) }}
                  {% else %}
                    {{ current }}
                  {% endif %}
                  
                  {# Option B: Stromzähler-Sensor (kumulativer Wert) #}
                  {# {% set meter_current = states('sensor.bitshake_smartmeterreader_ebz_e_inop') | float(0) %} #}
                  {# {% set meter_last = states('input_number.inverter_meter_last_value') | float(0) %} #}
                  {# {% set delta = meter_current - meter_last %} #}
                  {# {% if delta > 0 %} #}
                  {#   {{ (current + delta) | round(6) }} #}
                  {# {% else %} #}
                  {#   {{ current }} #}
                  {# {% endif %} #}
                  {# {% set meter_last = meter_current %} #}
        # Hoch: 18:00-21:00
        - conditions:
            - condition: time
              after: "18:00:00"
              before: "21:00:00"
          sequence:
            - service: input_number.set_value
              target:
                entity_id: input_number.inverter_energy_price_high
              data:
                value: >
                  {% set current = states('input_number.inverter_energy_price_high') | float(0) %}
                  {% set grid_power = states('sensor.inverter_grid_power') | float(0) %}
                  {% if grid_power > 0 %}
                    {{ (current + (grid_power / 1000 * 9 / 3600)) | round(6) }}
                  {% else %}
                    {{ current }}
                  {% endif %}
        # Standard: Alle anderen Zeiten (06:00-12:00, 16:00-18:00, 21:00-02:00)
        - conditions: []
          sequence:
            - service: input_number.set_value
              target:
                entity_id: input_number.inverter_energy_price_standard
              data:
                value: >
                  {% set current = states('input_number.inverter_energy_price_standard') | float(0) %}
                  {% set grid_power = states('sensor.inverter_grid_power') | float(0) %}
                  {% if grid_power > 0 %}
                    {{ (current + (grid_power / 1000 * 9 / 3600)) | round(6) }}
                  {% else %}
                    {{ current }}
                  {% endif %}

# Reset um Mitternacht
- id: reset_inverter_energy_price_zones
  alias: "Reset Inverter Energy Price Zones"
  trigger:
    - platform: time
      at: "00:00:00"
  action:
    - service: input_number.set_value
      target:
        entity_id:
          - input_number.inverter_energy_price_low
          - input_number.inverter_energy_price_standard
          - input_number.inverter_energy_price_high
      data:
        value: 0
```

**Alternative mit Template-Sensor statt input_number**:
- Template-Sensoren mit `state_class: total_increasing` für jede Zeitzone
- Automatisierung aktualisiert diese Sensoren kontinuierlich

## Dateien

- `configuration.yaml` - Template-Sensoren hinzufügen

## Sensoren

1. `sensor.inverter_current_electricity_price` - Aktueller Preis basierend auf Tageszeit
2. `sensor.inverter_today_energy_cost` - Aktuelle Tageskosten
3. `sensor.inverter_today_energy_cost_without_battery` - Hypothetische Kosten ohne Battery
4. `sensor.inverter_today_battery_savings` - Ersparnis durch Battery-Ladung

## Verwendete Entitäten

### Grid-Sensoren (Netzwerte)
- `sensor.inverter_grid_power` - **Aktuelle Netzleistung** (W)
  - **Positive Werte** = Import aus dem Netz (kostenpflichtig)
  - **Negative Werte** = Export ins Netz (Einspeisung)
  - **Wichtig**: Dies ist der Sensor für die Kostenberechnung!
- `sensor.inverter_today_energy_import` - Gesamtimport heute (kWh)
- `sensor.inverter_today_energy_export` - Gesamtexport heute (kWh)

### Load-Sensoren (Hausverbrauch)
- `sensor.inverter_load_power` - Verbrauch des Hauses, der durch den Inverter abgedeckt wird (W)
  - **Hinweis**: Nicht direkt für Kostenberechnung verwendet, da Grid-Power bereits den tatsächlichen Netzbezug zeigt

### Battery-Sensoren
- `sensor.inverter_today_battery_charge` - Battery-Ladung heute (kWh)
- `sensor.inverter_battery_power` - Aktuelle Battery-Leistung (W)
  - Positive Werte = Entladung (Battery gibt Energie ab)
  - Negative Werte = Ladung (Battery wird geladen)

### Inverter-Verluste
- `sensor.inverter_today_losses` - **Tägliche Verluste des Inverters** (kWh)
  - Summierender Wert, wird um Mitternacht auf 0 gesetzt
  - **Wichtig**: Verluste verbrauchen auch Energie aus dem Netz und müssen in die Kostenberechnung einbezogen werden
  - Die Verluste entstehen durch Umwandlungsverluste, Standby-Verbrauch, etc.
  - **Hinweis**: Die Verluste sind bereits in `sensor.inverter_grid_power` enthalten, wenn der Inverter Energie aus dem Netz bezieht

### Stromzähler (Separate Messung)
- `sensor.bitshake_smartmeterreader_ebz_e_inop` - **Stromeinkauf** (kWh) - Gesamtimport aus dem Netz
- `sensor.bitshake_smartmeterreader_ebz_e_outop` - **Einspeisung** (kWh) - Gesamtexport ins Netz
- **Hinweis**: Diese Sensoren messen direkt am Netzanschluss und sind möglicherweise genauer als die Wechselrichter-Sensoren

### Strompreis
- `sensor.octopus_a_10fc0646_electricity_price` - Aktueller Strompreis (kann ignoriert werden, da wir auf Zeitsteuerung gehen)

## System-Architektur (Netzparallel)

Der Inverter arbeitet **netzparallel**:
- **Grid-Sensoren** zeigen die tatsächlichen Netzwerte (Import/Export)
- **Load-Sensoren** zeigen den Hausverbrauch, der durch den Inverter abgedeckt wird
- **Stromzähler-Sensoren** messen direkt am Netzanschluss (separate Hardware)

### Datenquellen für Kostenberechnung

**Option 1: Wechselrichter-Sensoren** (aktuell geplant)
- `sensor.inverter_grid_power` - Aktuelle Netzleistung (W)
- Vorteil: Echtzeitdaten, bereits vorhanden
- Nachteil: Möglicherweise weniger genau als separater Zähler

**Option 2: Stromzähler-Sensoren** (Alternative, möglicherweise genauer)
- `sensor.bitshake_smartmeterreader_ebz_e_inop` - Stromeinkauf (kWh)
- Vorteil: Direkte Messung am Netzanschluss, höhere Genauigkeit
- Nachteil: Möglicherweise nur kumulative Werte (nicht Echtzeit-Leistung)

**Empfehlung**: 
- Für **Echtzeit-Tracking** (alle 9 Sekunden): `sensor.inverter_grid_power` verwenden
- Für **Tagesabrechnung/Validierung**: `sensor.bitshake_smartmeterreader_ebz_e_inop` als Referenz verwenden

## Todos

### Phase 1: Grundlegende Sensoren (Einfache Näherung)

- [ ] Template-Sensor für aktuellen Strompreis basierend auf Tageszeit erstellen (0,27€/0,34€/0,39€ je nach Zeitzone)
- [ ] Template-Sensor für aktuelle Tageskosten erstellen (sensor.inverter_today_energy_import × Näherungspreis)
  - **Hinweis**: Ungenau, da Verbrauch nicht gleichmäßig verteilt ist
- [ ] Template-Sensor für hypothetische Kosten ohne Battery-Ladung erstellen ((sensor.inverter_today_energy_import - sensor.inverter_today_battery_charge) × Näherungspreis)
- [ ] Template-Sensor für Ersparnis durch Battery-Ladung erstellen (Differenz zwischen hypothetischen und tatsächlichen Kosten)

### Phase 2: Präzise Berechnung (Empfohlen) ⭐

**Ziel**: Genaueste Berechnung mit Tracking aller Komponenten pro Zeitzone

#### Notwendige Komponenten für genaue Berechnung:

1. **Energie-Import pro Zeitzone** (aus dem Netz)
2. **Battery-Ladung pro Zeitzone** (wann wurde die Battery geladen?)
3. **Battery-Entladung pro Zeitzone** (wann wurde die Battery entladen?)
4. **Template-Sensoren** für Kostenberechnung

#### Option A: Utility Meter Integration (BESTE LÖSUNG) ⭐⭐⭐

- [ ] Template-Sensor erstellen: `sensor.inverter_grid_power_import` (nur positive Werte)
- [ ] Utility Meter Integration konfigurieren für 3 Zeitzonen
- [ ] Automatisierung erstellen, die den Utility Meter basierend auf Zeitzone wechselt
- [ ] **Energie-Import pro Zeitzone tracken**:
  - [ ] Utility Meter für `sensor.inverter_grid_power_import` (nur positive Werte)
  - [ ] Automatisierung wechselt Utility Meter basierend auf Zeitzone
- [ ] **Battery-Ladung pro Zeitzone tracken**:
  - [ ] Utility Meter für `sensor.inverter_battery_power_charge` (nur negative Werte = Ladung)
  - [ ] Gleiche Automatisierung wechselt auch Battery-Utility Meter
- [ ] **Battery-Entladung pro Zeitzone tracken** (optional, für noch genauere Berechnung):
  - [ ] Utility Meter für `sensor.inverter_battery_power_discharge` (nur positive Werte = Entladung)
- [ ] Template-Sensor für Gesamtkosten: Nutze Utility Meter Sensoren
  - [ ] `sensor.inverter_today_energy_cost` = Σ(Import_Zeitzone_i × Preis_Zeitzone_i)
- [ ] Template-Sensor für hypothetische Kosten ohne Battery:
  - [ ] `sensor.inverter_today_energy_cost_without_battery` = Σ((Import_Zeitzone_i - Battery_Ladung_Zeitzone_i + Battery_Entladung_Zeitzone_i) × Preis_Zeitzone_i)
  - [ ] **Logik**: Ohne Battery müsste der durch Battery gedeckte Verbrauch direkt aus dem Netz (in der entsprechenden Zeitzone)
- [ ] Template-Sensor für Ersparnis:
  - [ ] `sensor.inverter_today_battery_savings` = Tatsächliche Kosten - Hypothetische Kosten
- [ ] **Vorteil**: Genaueste Berechnung, nutzt native Home Assistant Features

#### Option B: Automatisierung alle 9 Sekunden (Alternative)

- [ ] **Nur wenn Utility Meter nicht funktioniert:**
- [ ] `input_number` Entitäten für kumulierte Energie pro Zeitzone erstellen
  - [ ] `input_number.inverter_energy_price_low` (Niedrig: 0,27€)
  - [ ] `input_number.inverter_energy_price_standard` (Standard: 0,34€)
  - [ ] `input_number.inverter_energy_price_high` (Hoch: 0,39€)
- [ ] Entscheidung: Welche Datenquelle verwenden?
  - [ ] **Option A**: `sensor.inverter_grid_power` (Echtzeit-Leistung, alle 9 Sekunden)
  - [ ] **Option B**: `sensor.bitshake_smartmeterreader_ebz_e_inop` (kumulativer Zähler, Delta-Berechnung)
- [ ] Automatisierung erstellen, die alle 9 Sekunden läuft:
  - [ ] Liest Energieverbrauch:
    - **Option A**: `sensor.inverter_grid_power` (nur positive Werte = Import)
      - Positive Werte = Energiebezug aus dem Netz (kostenpflichtig)
      - Negative Werte = Einspeisung ins Netz (werden ignoriert)
      - Delta: `(grid_power / 1000) * (9 / 3600)` kWh
    - **Option B**: `sensor.bitshake_smartmeterreader_ebz_e_inop` (kumulativer Wert)
      - Delta: `(aktueller_wert - letzter_wert)` kWh
      - Letzter Wert muss in `input_number` oder Template-Sensor gespeichert werden
  - [ ] Bestimmt aktuelle Zeitzone basierend auf Tageszeit
  - [ ] Kumuliert Energie in entsprechender `input_number` Entität
- [ ] Automatisierung für Mitternacht-Reset erstellen:
  - [ ] Setzt alle drei `input_number` Entitäten auf 0 zurück
- [ ] Template-Sensor für Gesamtkosten erstellen:
  - [ ] `sensor.inverter_today_energy_cost` = Σ(Energie_Zeitzone_i × Preis_Zeitzone_i)
  - [ ] **Hinweis**: Enthält bereits die Inverter-Verluste, da diese in `sensor.inverter_grid_power` enthalten sind
- [ ] Template-Sensor für hypothetische Kosten ohne Battery:
  - [ ] `sensor.inverter_today_energy_cost_without_battery` = (Gesamtkosten - Battery-Ladungskosten)
  - [ ] **Hinweis**: Verluste bleiben enthalten, da sie unabhängig von Battery-Ladung anfallen
- [ ] Template-Sensor für Ersparnis:
  - [ ] `sensor.inverter_today_battery_savings` = Differenz zwischen hypothetischen und tatsächlichen Kosten
- [ ] Optional: Template-Sensor für Verlustkosten:
  - [ ] `sensor.inverter_today_losses_cost` = `sensor.inverter_today_losses` × gewichteter Durchschnittspreis
  - [ ] Zeigt die Kosten, die durch Inverter-Verluste entstehen

### Alternative: Andere Methoden (Optional)

- [ ] Option 1: Utility Meter Integration
- [ ] Option 2: Template-Sensor mit History-Attributen
- [ ] Option 3: Integration mit Recorder für historische Daten

