---
title: "Lambda Dynamisch Dashboard"
---
 
# Lambda Dynamisch Dashboard (Vorlage)

*Zuletzt geändert am 06.09.2026*

Diese Vorlage beschreibt ein **dynamisches** Lovelace-Dashboard für die Lambda Wärmepumpen Integration.

**Besonderheit:** Der Gerätename (Prefix wie `eu08l`) wird automatisch aus der Integration ausgelesen – es muss **nichts angepasst** werden. Das Dashboard passt sich jeder Lambda-Konfiguration ohne manuelle Änderung an. Das Dashboard zeigt zudem das jeweilige Modbus Register zum Sensor an.

!!! info "Seit Version 3.5 angepasst"
    Frühere Fassungen dieser Vorlage sortierten über ein Attribut `register`, das die Integration an jedem Sensor gesetzt hat. Dieses Attribut gibt es seit dem 3.5-Rewrite nicht mehr. Die Register-Adressen sind deshalb fest im Template hinterlegt (wie beim [statischen Register-Dashboard](Lambda_register_dashboard.md)); nur die Präfix-Erkennung bleibt dynamisch.

<a href="../assets/dashboard_lambda_dynamisch1.png" target="_blank" rel="noopener noreferrer" title="Bild groß öffnen"><img src="../../assets/dashboard_lambda_dynamisch1.png" alt="Lambda Dynamisch Dashboard" width="500" style="max-width: 100%; height: auto;" /></a>

## Funktionsweise

Jede Card ermittelt zur Laufzeit den Prefix des konfigurierten Geräts über `integration_entities()`, kombiniert ihn mit einer fest hinterlegten Liste aus Register-Nummer und Sensor-Namen und zeigt daraus eine **nach Register-Nummer sortierte** Tabelle. Nur Sensoren, deren Entität tatsächlich existiert (Firmware/Hardware unterstützt das Register), erscheinen in der Tabelle. Cards für nicht konfigurierte Geräte zeigen *Keine Sensoren.*

## Einbindung in Home Assistant

1. **Einstellungen** → **Dashboards** → **„+ Dashboard hinzufügen"**
   - Name: `Lambda Dynamisch`, URL: `lambda-dyn`
2. Dashboard öffnen → oben rechts **Bleistift** → **„In YAML bearbeiten"**
3. Den unten stehenden YAML-Code einfügen und speichern.

## YAML (Copy & Paste)

Das Dashboard enthält je **ein Beispiel pro Gerätetyp**. Weitere Geräte (z. B. Heizkreis 2) durch Kopieren einer Card und Anpassen von `title`, Sub-Prefix und Register-Nummern hinzufügen – siehe [Card erweitern](#card-erweitern).

```yaml
title: Lambda WP
views:
  - title: Lambda WP
    path: default_view
    cards:

      - type: markdown
        title: Schnellübersicht
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          | Sensor | Wert |
          |--------|------|
          | COP (Lifetime, HP1) | {{ states('sensor.' + dp + '_hp1_cop_calc') }} |
          | Gesamtverbrauch (Lifetime, HP1) | {{ states('sensor.' + dp + '_hp1_compressor_power_consumption_accumulated') }} Wh |
          | Außentemperatur | {{ states('sensor.' + dp + '_ambient_temperature_calculated') }} °C |
          {%- for sub, label in [('hp1','WP 1'),('hp2','WP 2'),('hc1','HK 1'),('hc2','HK 2'),('hc3','HK 3'),('hc4','HK 4'),('boil1','WW 1'),('boil2','WW 2')] %}
          {%- set sub_sensors = states | selectattr('entity_id', 'match', '^sensor\.' + dp + '_' + sub + '_') | map(attribute='entity_id') | list %}
          {%- if sub_sensors | length > 0 %}
          | **{{ label }}** | |
          {%- for e in sub_sensors[:3] %}
          | {{ state_attr(e, 'friendly_name') or e }} | {{ states(e) }} {{ state_attr(e, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {%- endif %}
          {%- endfor %}

      - type: markdown
        title: Umgebung
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          {% set prefix = dp + '_ambient' %}
          {% set registers = {
            'error_number': 0, 'operating_state': 1, 'temperature': 2,
            'temperature_1h': 3, 'temperature_calculated': 4
          } %}
          {% set rows = [] %}
          {%- for suffix, reg in registers.items() %}
          {%- set e = 'sensor.' + prefix + '_' + suffix %}
          {%- if states[e] is not none %}
          {%- set rows = rows + [{'reg': reg, 'entity': e}] %}
          {%- endif %}
          {%- endfor %}
          {% set rows = rows | sort(attribute='reg') %}
          {% if rows | length == 0 %}
          _Keine Sensoren._
          {% else %}
          | Register | Name | Wert |
          |----------|------|------|
          {%- for row in rows %}
          | R{{ row.reg }} | {{ state_attr(row.entity, 'friendly_name') or '—' }} | {{ states(row.entity) }} {{ state_attr(row.entity, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {% endif %}

      - type: markdown
        title: Energie Manager
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          {% set prefix = dp + '_emgr' %}
          {% set registers = {
            'error_number': 100, 'operating_state': 101, 'actual_power': 102,
            'actual_power_consumption': 103, 'power_consumption_setpoint': 104
          } %}
          {% set rows = [] %}
          {%- for suffix, reg in registers.items() %}
          {%- set e = 'sensor.' + prefix + '_' + suffix %}
          {%- if states[e] is not none %}
          {%- set rows = rows + [{'reg': reg, 'entity': e}] %}
          {%- endif %}
          {%- endfor %}
          {% set rows = rows | sort(attribute='reg') %}
          {% if rows | length == 0 %}
          _Keine Sensoren._
          {% else %}
          | Register | Name | Wert |
          |----------|------|------|
          {%- for row in rows %}
          | R{{ row.reg }} | {{ state_attr(row.entity, 'friendly_name') or '—' }} | {{ states(row.entity) }} {{ state_attr(row.entity, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {% endif %}

      - type: markdown
        title: Wärmepumpe 1
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          {% set prefix = dp + '_hp1' %}
          {% set registers = {
            'error_state': 1000, 'error_number': 1001, 'state': 1002, 'operating_state': 1003,
            'flow_line_temperature': 1004, 'return_line_temperature': 1005, 'volume_flow_heat_sink': 1006,
            'energy_source_inlet_temperature': 1007, 'energy_source_outlet_temperature': 1008,
            'volume_flow_energy_source': 1009, 'compressor_unit_rating': 1010, 'actual_heating_capacity': 1011,
            'inverter_power_consumption': 1012, 'cop': 1013, 'request_type': 1015,
            'requested_flow_line_temperature': 1016, 'requested_return_line_temperature': 1017,
            'requested_flow_to_return_line_temperature_difference': 1018, 'relais_state_2nd_heating_stage': 1019,
            'compressor_power_consumption_accumulated': 1020, 'compressor_thermal_energy_output_accumulated': 1022,
            'config_parameter_24': 1024, 'vda_rating': 1025, 'hot_gas_temperature': 1026,
            'subcooling_temperature': 1027, 'suction_gas_temperature': 1028, 'condensation_temperature': 1029,
            'evaporation_temperature': 1030, 'eqm_rating': 1031, 'expansion_valve_opening_angle': 1032,
            'config_parameter_33': 1033
          } %}
          {% set rows = [] %}
          {%- for suffix, reg in registers.items() %}
          {%- set e = 'sensor.' + prefix + '_' + suffix %}
          {%- if states[e] is not none %}
          {%- set rows = rows + [{'reg': reg, 'entity': e}] %}
          {%- endif %}
          {%- endfor %}
          {% set rows = rows | sort(attribute='reg') %}
          {% if rows | length == 0 %}
          _Keine Sensoren._
          {% else %}
          | Register | Name | Wert |
          |----------|------|------|
          {%- for row in rows %}
          | R{{ row.reg }} | {{ state_attr(row.entity, 'friendly_name') or '—' }} | {{ states(row.entity) }} {{ state_attr(row.entity, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {% endif %}

      - type: markdown
        title: Warmwasser 1
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          {% set prefix = dp + '_boil1' %}
          {% set registers = {
            'error_number': 2000, 'operating_state': 2001, 'actual_high_temperature': 2002,
            'actual_low_temperature': 2003, 'actual_circulation_temperature': 2004,
            'actual_circulation_pump_state': 2005, 'target_high_temperature': 2050
          } %}
          {% set rows = [] %}
          {%- for suffix, reg in registers.items() %}
          {%- set e = 'sensor.' + prefix + '_' + suffix %}
          {%- if states[e] is not none %}
          {%- set rows = rows + [{'reg': reg, 'entity': e}] %}
          {%- endif %}
          {%- endfor %}
          {% set rows = rows | sort(attribute='reg') %}
          {% if rows | length == 0 %}
          _Keine Sensoren._
          {% else %}
          | Register | Name | Wert |
          |----------|------|------|
          {%- for row in rows %}
          | R{{ row.reg }} | {{ state_attr(row.entity, 'friendly_name') or '—' }} | {{ states(row.entity) }} {{ state_attr(row.entity, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {% endif %}

      - type: markdown
        title: Heizkreis 1
        content: |
          {% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
          {% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
          {% set prefix = dp + '_hc1' %}
          {% set registers = {
            'error_number': 5000, 'operating_state': 5001, 'flow_line_temperature': 5002,
            'return_line_temperature': 5003, 'room_device_temperature': 5004, 'set_flow_line_temperature': 5005,
            'operating_mode': 5006, 'flow_line_temperature_setpoint': 5007, 'target_temp_flow_line': 5007,
            'set_flow_line_offset_temperature': 5050, 'target_room_temperature': 5051,
            'set_cooling_mode_room_temperature': 5052
          } %}
          {% set rows = [] %}
          {%- for suffix, reg in registers.items() %}
          {%- set e = 'sensor.' + prefix + '_' + suffix %}
          {%- if states[e] is not none %}
          {%- set rows = rows + [{'reg': reg, 'entity': e}] %}
          {%- endif %}
          {%- endfor %}
          {% set rows = rows | sort(attribute='reg') %}
          {% if rows | length == 0 %}
          _Keine Sensoren._
          {% else %}
          | Register | Name | Wert |
          |----------|------|------|
          {%- for row in rows %}
          | R{{ row.reg }} | {{ state_attr(row.entity, 'friendly_name') or '—' }} | {{ states(row.entity) }} {{ state_attr(row.entity, 'unit_of_measurement') or '' }} |
          {%- endfor %}
          {% endif %}
```

## Card erweitern

Eine Card kopieren und `title`, Sub-Prefix (`dp + '_...'`) **und** die `registers`-Liste anpassen. Bei einer zweiten Wärmepumpe, einem zweiten Heizkreis usw. verschieben sich alle Register-Adressen um 100 pro Index (z. B. HP2 beginnt bei 1100 statt 1000, HC3 bei 5200 statt 5000):

| Gerät           | `title`           | Sub-Prefix        | Register-Basis |
|-----------------|-------------------|-------------------|-----------------|
| Umgebung        | `Umgebung`        | `_ambient`        | 0 (fest) |
| Energie Manager | `Energie Manager` | `_emgr`           | 100 (fest) |
| Wärmepumpe 1    | `Wärmepumpe 1`    | `_hp1`            | 1000 |
| Wärmepumpe 2    | `Wärmepumpe 2`    | `_hp2`            | 1100 |
| Warmwasser 1    | `Warmwasser 1`    | `_boil1`          | 2000 |
| Warmwasser 2    | `Warmwasser 2`    | `_boil2`          | 2100 |
| Heizkreis 1     | `Heizkreis 1`     | `_hc1`            | 5000 |
| Heizkreis 2     | `Heizkreis 2`     | `_hc2`            | 5100 |
| Heizkreis 3     | `Heizkreis 3`     | `_hc3`            | 5200 |
| Heizkreis 4     | `Heizkreis 4`     | `_hc4`            | 5300 |

Die Sensor-Namen (Schlüssel im `registers`-Dict) bleiben beim Kopieren unverändert – nur die Zahlenwerte (Register-Adressen) und der Sub-Prefix ändern sich.

## Template-Erklärung

**Prefix-Erkennung** – die ersten zwei Zeilen jeder Card:

```jinja2
{% set _e = integration_entities('lambda_heat_pumps') | select('match', '^sensor\.') | first | default('') %}
{% set dp = _e.split('.')[1].split('_')[0] if _e else '' %}
```

- `integration_entities('lambda_heat_pumps')` liefert alle Entity-IDs der Integration
- Erste Sensor-Entity: z. B. `sensor.eu08l_ambient_temperature`
- `split('.')[1]` → `eu08l_ambient_temperature`, dann `split('_')[0]` → `eu08l`

**Sensor-Tabelle:**

- `registers` ist ein fest hinterlegtes Dict `{Sensor-Suffix: Register-Nummer}` – es ersetzt das frühere `attributes.register` (siehe Hinweis oben).
- Für jeden Eintrag wird geprüft, ob `sensor.{prefix}_{suffix}` als Entität existiert (`states[e] is not none`); nur dann landet er in der Tabelle.
- `rows | sort(attribute='reg')` sortiert die gefundenen Zeilen nach Register-Nummer.
