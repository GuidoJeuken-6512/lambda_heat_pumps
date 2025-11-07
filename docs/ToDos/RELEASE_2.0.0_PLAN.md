# Release 2.0.0 - Implementierungsplan

**Status**: Geplant  
**Geplantes Release**: TBA

## Übersicht

Dieser Plan umfasst die Implementierung von 4 Hauptfeatures für Release 2.0.0:

1. Subdevices für Module (HP, Boiler, Buffer, Solar, HC)
2. Heizkurve-Berechnung mit Eingabemöglichkeit
3. Pro-Heizkreis Raumthermostat-Steuerung
4. Dedicated Compressor Cycle Start Sensor
5. 32 bit support für Services (read/Write) siehe plan

---

## Feature 1: Subdevices für Module (Issue #14)

### Ziel

Jedes Modul (hp1, hp2, hc1, hc2, buffer1, buffer2, boiler1, etc.) soll ein eigenes Device in Home Assistant bekommen.

### WICHTIG: Rückwärtskompatibilität

- **unique_id muss identisch bleiben** (z.B. "hp1_operating_state") - sonst gehen historische Daten verloren
- **entity_id muss identisch bleiben** (z.B. "sensor.hp1_operating_state") - sonst gehen Dashboard-Referenzen verloren
- Nur die `device_info`-Zuordnung ändert sich (Entity wird neuem Subdevice zugeordnet)
- Home Assistant erkennt Entities über unique_id, daher bleiben Daten erhalten bei Device-Änderung

### Implementierung

1. **Erweitere `build_device_info()` in `utils.py`**:
   - Neue Funktion `build_subdevice_info(entry, device_type, device_index)` erstellen
   - Jedes Subdevice erhält eigene `identifiers` mit `(DOMAIN, entry_id, device_type, device_index)`
   - Device-Namen: "Lambda WP - HP1", "Lambda WP - HC2", etc.
   - Hauptdevice bleibt als Parent-Device mit `via_device` Referenz
   - **unique_id Generation bleibt unverändert** - nur device_info ändert sich

2. **Anpassung aller Entities in `sensor.py`, `climate.py`, `template_sensor.py`**:
   - Jede Entity muss `device_info` basierend auf ihrem `device_type` und Index zurückgeben
   - Logik: `device_prefix` (z.B. "hp1", "hc2") aus `sensor_id` oder Konstruktor-Parameter extrahieren
   - **unique_id und entity_id bleiben unverändert** - nur device_info Property ändert sich
   - Für General Sensors: weiterhin Hauptdevice verwenden

3. **Coordinator-Integration**:
   - Keine Änderungen notwendig (Coordinator bleibt auf Entry-Ebene)

### Migration

- **Keine Migration nötig**: Da unique_ids identisch bleiben, werden Entities automatisch dem neuen Subdevice zugeordnet
- Home Assistant Device Registry wird Entities beim ersten Update automatisch dem neuen Device zuordnen
- Historie und Dashboard-Referenzen bleiben erhalten

### Dateien

- `custom_components/lambda_heat_pumps/utils.py` - Neue `build_subdevice_info()` Funktion
- `custom_components/lambda_heat_pumps/sensor.py` - Device-Info-Anpassung für alle Sensoren (unique_id/entity_id bleiben gleich)
- `custom_components/lambda_heat_pumps/climate.py` - Device-Info-Anpassung für Climate Entities (unique_id/entity_id bleiben gleich)
- `custom_components/lambda_heat_pumps/template_sensor.py` - Device-Info-Anpassung (unique_id/entity_id bleiben gleich)

---

## Feature 2: Heizkurve-Berechnung (Issue #33)

### Ziel

Die Sensoren "Requested Flow Line Temperature" sollen basierend auf konfigurierbarer Heizkurve berechnet werden. Pro Heating Circuit gibt es drei Input-Sensoren (cold, mid, warm) für die Heizkurven-Stützpunkte und einen Template-Sensor für die berechnete Vorlauftemperatur.

### Implementierung

1. **Drei Input-Sensoren pro HC (Number-Entities)**:
   - `heating_curve_cold_outside_temp` - Außentemperatur für "cold" Stützpunkt (Standard: -22°C)
   - `heating_curve_mid_outside_temp` - Außentemperatur für "mid" Stützpunkt (Standard: 0°C)
   - `heating_curve_warm_outside_temp` - Außentemperatur für "warm" Stützpunkt (Standard: 22°C)
   - Diese 3 Sensoren werden als Number-Entities erstellt und können über die UI angepasst werden
   - Die entsprechenden Vorlauftemperaturen (y_cold=49.0°C, y_mid=40.0°C, y_warm=31.5°C) sind im Template-Sensor fest codiert

2. **Template-Sensor in `const.py` einpflegen**:
   - Neuer Eintrag in `CALCULATED_SENSOR_TEMPLATES` für "heating_curve_flow_temp_calc" pro HC
   - Template-Logik analog zu Issue #33:
     - Verwendet `ambient_temperature_calculated` als Außentemperatur-Input
     - Verwendet die drei Input-Sensoren (cold, mid, warm) als Stützpunkte für Außentemperatur
     - Lineare Interpolation zwischen den Stützpunkten
     - Vorlauftemperaturen sind fest codiert: y_cold=49.0°C, y_mid=40.0°C, y_warm=31.5°C
     - Wenn Außentemperatur >= warm → warm Vorlauftemperatur (31.5°C)
     - Wenn Außentemperatur > mid → Interpolation zwischen mid und warm
     - Wenn Außentemperatur > cold → Interpolation zwischen cold und mid
     - Wenn Außentemperatur <= cold → cold Vorlauftemperatur (49.0°C)

3. **Modbus-Register-Schreiben**:
   - **Wird nicht automatisch geschrieben** - nur Template-Sensor zur Anzeige wird erstellt
   - Optional kann der Benutzer den Template-Sensor-Wert manuell verwenden oder über Automation/Service schreiben

4. **Sensor-Erstellung in `sensor.py`**:
   - Erstelle Number-Entities für die 3 Input-Sensoren pro HC:
     - `heating_curve_cold_outside_temp` (Standard: -22.0°C)
     - `heating_curve_mid_outside_temp` (Standard: 0.0°C)
     - `heating_curve_warm_outside_temp` (Standard: 22.0°C)
   - Erstelle Template-Sensor für berechnete Vorlauftemperatur pro HC
   - Template-Sensor nutzt LambdaTemplateSensor-Klasse
   - Number-Entities können als neue Entity-Klasse `LambdaNumberEntity` implementiert werden oder über Home Assistant Number Platform

### Template-Formel (Beispiel für HC1)

```jinja2
{% set t_out = states('sensor.ambient_temperature_calculated') | float(10) %}
{% set x_cold = states('sensor.hc1_heating_curve_cold_outside_temp') | float(-22.0) %}
{% set x_mid = states('sensor.hc1_heating_curve_mid_outside_temp') | float(0.0) %}
{% set x_warm = states('sensor.hc1_heating_curve_warm_outside_temp') | float(22.0) %}
{# Vorlauftemperaturen sind fest codiert #}
{% set y_cold = 49.0 %}
{% set y_mid = 40.0 %}
{% set y_warm = 31.5 %}

{% macro lin(x, xA, yA, xB, yB) -%}
  {{ yA + (x - xA) * (yB - yA) / (xB - xA) }}
{%- endmacro %}

{% if t_out >= x_warm %}
  {{ y_warm | round(1) }}
{% elif t_out > x_mid %}
  {{ lin(t_out, x_mid, y_mid, x_warm, y_warm) | float | round(1) }}
{% elif t_out > x_cold %}
  {{ lin(t_out, x_cold, y_cold, x_mid, y_mid) | float | round(1) }}
{% else %}
  {{ y_cold | round(1) }}
{% endif %}
```

### Dateien

- `custom_components/lambda_heat_pumps/const.py` - Neue Sensor-Templates für Input-Sensoren und Template-Sensor in CALCULATED_SENSOR_TEMPLATES
- `custom_components/lambda_heat_pumps/sensor.py` - Erstellung der Number-Entities (Input-Sensoren) und Template-Sensor
- Optional: Neue Datei `custom_components/lambda_heat_pumps/number.py` für Number-Entities (oder Integration in sensor.py)

---

## Feature 3: Pro-Heizkreis Raumthermostat-Steuerung (Issue #13)

### Ziel

Raumthermostat-Steuerung soll pro Heizkreis einzeln aktiviert/deaktiviert werden können.

### Implementierung

1. **Options Flow anpassen (`config_flow.py`)**:
   - Entferne globale `room_thermostat_control` Option
   - Neue Option: `room_thermostat_control_hc1`, `room_thermostat_control_hc2`, etc. (boolean pro HC)
   - Wenn für einen HC aktiviert, dann Sensor-Auswahl für diesen HC anzeigen

2. **Service-Logik anpassen (`services.py`)**:
   - `_process_room_temperature_entry()` prüft pro HC, ob Raumthermostat für diesen HC aktiviert ist
   - Nur für aktivierte HCs wird Register 5004 geschrieben
   - Logik: `if config_entry.options.get(f"room_thermostat_control_hc{hc_idx}", False):`

3. **Service-Scheduler (`services.py`)**:
   - Scheduler nur starten, wenn mindestens ein HC Raumthermostat aktiviert hat
   - Änderung in `async_setup_services()`: Prüfe alle HCs statt nur globale Option

4. **Migration**:
   - Beim Update von 1.4.x: Wenn `room_thermostat_control` global aktiviert war, aktiviere für alle HCs
   - Migrations-Logik in `migration.py`

### Dateien

- `custom_components/lambda_heat_pumps/config_flow.py` - Options Flow Anpassung
- `custom_components/lambda_heat_pumps/services.py` - Service-Logik pro HC
- `custom_components/lambda_heat_pumps/migration.py` - Migration von global zu pro-HC

---

## Feature 4: Compressor Cycle Start Sensor (Issue #38)

### Ziel

Neuer dedizierter Sensor `compressor_cycle_start` der nur bei echtem Compressor-Start (State-Wechsel zu "START COMPRESSOR" = State 2) hochzählt.

### Implementierung

1. **Neuer Sensor-Template in `const.py`**:
   - `compressor_cycle_start_total` - Gesamtanzahl aller Compressor-Starts
   - `compressor_cycle_start_daily` - Tägliche Compressor-Starts (resettet um Mitternacht)
   - `compressor_cycle_start_yesterday` - Gestern erreichte Daily-Werte
   - `compressor_cycle_start_2h` - 2-Stunden Compressor-Starts (resettet alle 2 Stunden)
   - `compressor_cycle_start_4h` - 4-Stunden Compressor-Starts (resettet alle 4 Stunden)
   - Sensor-Typ: `LambdaCyclingSensor` und `LambdaYesterdaySensor` (wie andere Cycling-Sensoren)
   - Analog zu bestehenden cycling sensors mit allen Zeiträumen

2. **Flankenerkennung erweitern (`coordinator.py`)**:
   - Neue Logik in `_detect_cycling_flank()` oder separate Funktion
   - Erkennung: `operating_state` wechselt zu State 2 ("START COMPRESSOR")
   - Unterschied zu Cycling: Nur bei Wechsel zu "START COMPRESSOR", nicht bei jedem Betriebsmodus-Wechsel
   - Separater Tracking für Compressor-Starts unabhängig von Betriebsmodus-Cycling

3. **Sensor-Erstellung in `sensor.py`**:
   - Neue `LambdaCyclingSensor` Instanzen für compressor_cycle_start (total, daily, 2h, 4h)
   - Neue `LambdaYesterdaySensor` Instanz für compressor_cycle_start_yesterday
   - Analog zu bestehenden cycling sensors, aber eigene Kategorie

4. **Persistierung**:
   - Nutzt bestehende Persistierung über `RestoreEntity`
   - Separate Offsets in `lambda_wp_config.yaml` (optional): `compressor_cycle_start_offsets`

### Dateien

- `custom_components/lambda_heat_pumps/const.py` - Neue Sensor-Templates für compressor_cycle_start (total, daily, yesterday, 2h, 4h)
- `custom_components/lambda_heat_pumps/coordinator.py` - Erweiterte Flankenerkennung für Compressor-Starts (State 2)
- `custom_components/lambda_heat_pumps/sensor.py` - Sensor-Erstellung (LambdaCyclingSensor und LambdaYesterdaySensor)
- `custom_components/lambda_heat_pumps/utils.py` - Optional: Increment-Funktion für compressor cycles

---

## Technische Details

### Breaking Changes

- **Device-Struktur**: Bestehende Automations/Scenes die Device-IDs verwenden müssen angepasst werden (aber Entities bleiben über unique_id erhalten)
- **Raumthermostat-Konfiguration**: Globale Option wird zu pro-HC Optionen

### Migration

- Automatische Migration von 1.4.x zu 2.0.0:
  - Device-Migration: Bestehende Entities erhalten neue Device-IDs, aber unique_ids bleiben gleich → keine Datenverluste
  - Raumthermostat: Global aktiviert → alle HCs aktivieren
  - Heizkurve: Keine Migration nötig (neues Feature)
  - Compressor Sensor: Neues Feature, keine Migration nötig

### Testing

- Unit Tests für neue Device-Info-Logik
- Integration Tests für Heizkurve-Berechnung
- Tests für pro-HC Raumthermostat-Steuerung
- Tests für Compressor Cycle Start Erkennung
- Tests für Rückwärtskompatibilität (unique_id/entity_id)

---

## Reihenfolge der Implementierung

1. **Feature 1 (Subdevices)** - Grundlage für bessere Device-Struktur
   - Kritisch: unique_id/entity_id müssen identisch bleiben

2. **Feature 4 (Compressor Sensor)** - Einfachste Implementierung
   - Analog zu bestehenden cycling sensors

3. **Feature 3 (Pro-HC Raumthermostat)** - Mittlere Komplexität
   - Änderungen in Config Flow und Services

4. **Feature 2 (Heizkurve)** - Komplexeste Implementierung
   - Number-Entities müssen implementiert werden
   - Template-Sensor mit komplexer Logik

---

## TODOs

### Feature 1: Subdevices
- [x] Erweitere utils.py mit build_subdevice_info() Funktion für Module-spezifische Device-Infos
- [x] Anpasse alle Entities in sensor.py um device_info basierend auf device_type und Index zurückzugeben (unique_id/entity_id bleiben gleich)
- [x] Anpasse climate.py und template_sensor.py für Subdevice-Unterstützung

### Feature 2: Heizkurve
- [ ] Erweitere const.py mit Sensor-Templates für Input-Sensoren (3 Number-Entities pro HC) und Template-Sensor
- [ ] Implementiere Number-Entities in sensor.py oder neue number.py Datei
- [ ] Implementiere Template-Sensor mit Heizkurven-Berechnung (fest codierte Vorlauftemperaturen)

### Feature 3: Pro-HC Raumthermostat
- [ ] Ändere config_flow.py: Ersetze globale room_thermostat_control Option durch pro-HC Optionen
- [ ] Anpasse services.py: Prüfe pro HC ob Raumthermostat aktiviert ist, nur für aktivierte HCs Register schreiben
- [ ] Implementiere Migration in migration.py: Global aktiviert → alle HCs aktivieren

### Feature 4: Compressor Sensor
- [ ] Erweitere const.py mit Sensor-Templates für compressor_cycle_start (total, daily, yesterday, 2h, 4h)
- [ ] Implementiere Flankenerkennung für Compressor-Starts in coordinator.py (State-Wechsel zu 2 = START COMPRESSOR)
- [ ] Erstelle compressor_cycle_start Sensoren in sensor.py analog zu cycling sensors (inkl. Yesterday-Sensor)

### Allgemein
- [ ] Aktualisiere Version auf 2.0.0 in __init__.py und manifest.json
- [ ] Erstelle CHANGELOG.md Eintrag für Version 2.0.0 mit allen neuen Features

---

**Letzte Aktualisierung**: 2025-11-07

