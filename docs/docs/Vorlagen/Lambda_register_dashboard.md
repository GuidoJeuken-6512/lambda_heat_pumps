---
title: "Lambda Register-Dashboard"
---

# Lambda Register-Dashboard (Vorlage)

*Zuletzt geändert am 06.09.2026*

!!! warning "Seit Version 3.5 angepasst"
    Frühere Fassungen dieser Vorlage filterten über ein Attribut `register`, das die Integration an jedem Sensor gesetzt hat. Dieses Attribut gibt es seit dem 3.5-Rewrite nicht mehr. Die Vorlage unten trägt die Register-Adressen deshalb fest im Template ein und prüft nur noch, ob die Entität überhaupt existiert (ein Sensor, dessen Register die Firmware oder der Controller nicht bedient, wird von der Integration gar nicht erst angelegt).

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 320px;">
    <a href="../assets/lambda-register-dashboard-general.png" target="_blank" rel="noopener noreferrer" title="Bild groß öffnen">
      <img src="../../assets/lambda-register-dashboard-general.png" alt="Lambda Register-Dashboard – General / Ambient & E-Manager" style="width: 100%; height: auto; border-radius: 8px;">
    </a>
  </div>
  <div style="flex: 1; min-width: 280px;">
    <p>Diese Vorlage erstellt ein Lovelace-Dashboard <strong>„Lambda Register“</strong> mit vier Reitern. In jeder Ansicht wird eine Tabelle angezeigt: <strong>Register</strong> (Modbus-Adresse), <strong>Name</strong> (Sensor) und <strong>Wert</strong>. Es werden nur <strong>native Modbus-Sensoren</strong> der Lambda-Integration einbezogen (keine berechneten oder Template-Sensoren).</p>
    <p><strong>Reiter:</strong></p>
    <ul>
      <li><strong>General (R0–R104)</strong> – Ambient und E-Manager (feste Adressen 0–4, 100–104)</li>
      <li><strong>Wärmepumpe (HP1)</strong> – Native HP-Sensoren (ab R1000)</li>
      <li><strong>Warmwasser (Boiler)</strong> – Boiler-Sensoren (ab R2000)</li>
      <li><strong>Heizkreis (HC1)</strong> – Heizkreis-Sensoren (ab R5000)</li>
    </ul>
    <p>Die Register-Adressen sind fest im Template hinterlegt. Sensoren, die es bei deiner Firmware oder Konfiguration nicht gibt (z. B. andere FW-Version), werden automatisch ausgeblendet, weil ihre Entität schlicht nicht existiert.</p>
  </div>
</div>

## Einbindung in Home Assistant

1. **Einstellungen** → **Dashboard** → **„+ Dashboard“** → **„Mit YAML konfigurieren“**  
   oder ein bestehendes Dashboard bearbeiten und den Inhalt ersetzen bzw. einfügen.
2. Den unten stehenden YAML-Code komplett kopieren und einfügen.
3. **Präfix anpassen (falls nötig):** Wenn deine Sensor-IDs nicht mit `eu08l` beginnen, ersetze im YAML einmal **`eu08l`** durch deinen Präfix (z. B. `lambda`). Den Präfix siehst du unter **Einstellungen** → **Geräte & Dienste** → **Geräte** → deine Lambda-Integration (z. B. „EU08L“ → oft `eu08l` in Kleinbuchstaben).

## YAML (Copy & Paste)

```yaml
# Lambda Register-Dashboard – nur native Modbus-Sensoren
# Anzeige: Register | Name | Wert. Präfix "eu08l" ggf. durch deinen ersetzen.
# Register-Adressen sind fest im Template hinterlegt (siehe Hinweis oben);
# eine Zeile erscheint nur, wenn die Entität tatsächlich existiert.

title: Lambda Register
views:
  - title: General (R0–R104)
    path: general
    icon: mdi:chip
    cards:
      - type: markdown
        title: General / Ambient & E-Manager
        content: |
          {% set list = [
            (0, 'sensor.eu08l_ambient_error_number'),
            (1, 'sensor.eu08l_ambient_operating_state'),
            (2, 'sensor.eu08l_ambient_temperature'),
            (3, 'sensor.eu08l_ambient_temperature_1h'),
            (4, 'sensor.eu08l_ambient_temperature_calculated'),
            (100, 'sensor.eu08l_emgr_error_number'),
            (101, 'sensor.eu08l_emgr_operating_state'),
            (102, 'sensor.eu08l_emgr_actual_power'),
            (103, 'sensor.eu08l_emgr_actual_power_consumption'),
            (104, 'sensor.eu08l_emgr_power_consumption_setpoint')
          ] %}
          | Register | Name | Wert |
          |----------|------|------|
          {% for reg, e in list %}
          {% if states[e] is not none %}
          | R{{ reg }} | {{ state_attr(e, 'friendly_name') or '—' }} | {{ states(e) }} {{ state_attr(e, 'unit_of_measurement') or '' }} |
          {% endif %}
          {% endfor %}

  - title: Wärmepumpe (HP1)
    path: hp1
    icon: mdi:heat-pump
    cards:
      - type: markdown
        title: HP1 – Native Register
        content: |
          {% set list = [
            (1000, 'sensor.eu08l_hp1_error_state'),
            (1001, 'sensor.eu08l_hp1_error_number'),
            (1002, 'sensor.eu08l_hp1_state'),
            (1003, 'sensor.eu08l_hp1_operating_state'),
            (1004, 'sensor.eu08l_hp1_flow_line_temperature'),
            (1005, 'sensor.eu08l_hp1_return_line_temperature'),
            (1006, 'sensor.eu08l_hp1_volume_flow_heat_sink'),
            (1007, 'sensor.eu08l_hp1_energy_source_inlet_temperature'),
            (1008, 'sensor.eu08l_hp1_energy_source_outlet_temperature'),
            (1009, 'sensor.eu08l_hp1_volume_flow_energy_source'),
            (1010, 'sensor.eu08l_hp1_compressor_unit_rating'),
            (1011, 'sensor.eu08l_hp1_actual_heating_capacity'),
            (1012, 'sensor.eu08l_hp1_inverter_power_consumption'),
            (1013, 'sensor.eu08l_hp1_cop'),
            (1015, 'sensor.eu08l_hp1_request_type'),
            (1016, 'sensor.eu08l_hp1_requested_flow_line_temperature'),
            (1017, 'sensor.eu08l_hp1_requested_return_line_temperature'),
            (1018, 'sensor.eu08l_hp1_requested_flow_to_return_line_temperature_difference'),
            (1019, 'sensor.eu08l_hp1_relais_state_2nd_heating_stage'),
            (1020, 'sensor.eu08l_hp1_compressor_power_consumption_accumulated'),
            (1022, 'sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated'),
            (1024, 'sensor.eu08l_hp1_config_parameter_24'),
            (1025, 'sensor.eu08l_hp1_vda_rating'),
            (1026, 'sensor.eu08l_hp1_hot_gas_temperature'),
            (1027, 'sensor.eu08l_hp1_subcooling_temperature'),
            (1028, 'sensor.eu08l_hp1_suction_gas_temperature'),
            (1029, 'sensor.eu08l_hp1_condensation_temperature'),
            (1030, 'sensor.eu08l_hp1_evaporation_temperature'),
            (1031, 'sensor.eu08l_hp1_eqm_rating'),
            (1032, 'sensor.eu08l_hp1_expansion_valve_opening_angle'),
            (1033, 'sensor.eu08l_hp1_config_parameter_33'),
            (1050, 'sensor.eu08l_hp1_config_parameter_50'),
            (1051, 'sensor.eu08l_hp1_dhw_output_power_15c'),
            (1052, 'sensor.eu08l_hp1_heating_min_output_power_15c'),
            (1053, 'sensor.eu08l_hp1_heating_max_output_power_15c'),
            (1054, 'sensor.eu08l_hp1_heating_min_output_power_0c'),
            (1055, 'sensor.eu08l_hp1_heating_max_output_power_0c'),
            (1056, 'sensor.eu08l_hp1_heating_min_output_power_minus15c'),
            (1057, 'sensor.eu08l_hp1_heating_max_output_power_minus15c'),
            (1058, 'sensor.eu08l_hp1_cooling_min_output_power'),
            (1059, 'sensor.eu08l_hp1_cooling_max_output_power'),
            (1060, 'sensor.eu08l_hp1_config_parameter_60')
          ] %}
          | Register | Name | Wert |
          |----------|------|------|
          {% for reg, e in list %}
          {% if states[e] is not none %}
          | R{{ reg }} | {{ state_attr(e, 'friendly_name') or '—' }} | {{ states(e) }} {{ state_attr(e, 'unit_of_measurement') or '' }} |
          {% endif %}
          {% endfor %}

  - title: Warmwasser (Boiler)
    path: boil
    icon: mdi:water-thermometer
    cards:
      - type: markdown
        title: Boiler1 – Native Register
        content: |
          {% set list = [
            (2000, 'sensor.eu08l_boil1_error_number'),
            (2001, 'sensor.eu08l_boil1_operating_state'),
            (2002, 'sensor.eu08l_boil1_actual_high_temperature'),
            (2003, 'sensor.eu08l_boil1_actual_low_temperature'),
            (2004, 'sensor.eu08l_boil1_actual_circulation_temperature'),
            (2005, 'sensor.eu08l_boil1_actual_circulation_pump_state'),
            (2050, 'sensor.eu08l_boil1_target_high_temperature')
          ] %}
          | Register | Name | Wert |
          |----------|------|------|
          {% for reg, e in list %}
          {% if states[e] is not none %}
          | R{{ reg }} | {{ state_attr(e, 'friendly_name') or '—' }} | {{ states(e) }} {{ state_attr(e, 'unit_of_measurement') or '' }} |
          {% endif %}
          {% endfor %}

  - title: Heizkreis (HC1)
    path: hc1
    icon: mdi:radiator
    cards:
      - type: markdown
        title: HC1 – Native Register
        content: |
          {% set list = [
            (5000, 'sensor.eu08l_hc1_error_number'),
            (5001, 'sensor.eu08l_hc1_operating_state'),
            (5002, 'sensor.eu08l_hc1_flow_line_temperature'),
            (5003, 'sensor.eu08l_hc1_return_line_temperature'),
            (5004, 'sensor.eu08l_hc1_room_device_temperature'),
            (5005, 'sensor.eu08l_hc1_set_flow_line_temperature'),
            (5006, 'sensor.eu08l_hc1_operating_mode'),
            (5007, 'sensor.eu08l_hc1_flow_line_temperature_setpoint'),
            (5007, 'sensor.eu08l_hc1_target_temp_flow_line'),
            (5050, 'sensor.eu08l_hc1_set_flow_line_offset_temperature'),
            (5051, 'sensor.eu08l_hc1_target_room_temperature'),
            (5052, 'sensor.eu08l_hc1_set_cooling_mode_room_temperature')
          ] %}
          | Register | Name | Wert |
          |----------|------|------|
          {% for reg, e in list %}
          {% if states[e] is not none %}
          | R{{ reg }} | {{ state_attr(e, 'friendly_name') or '—' }} | {{ states(e) }} {{ state_attr(e, 'unit_of_measurement') or '' }} |
          {% endif %}
          {% endfor %}
```

## Hinweise

- **Fehlende Zeilen:** Sensoren, die bei deiner Firmware-Version oder Konfiguration nicht angelegt werden (z. B. manche HC-Sensoren erst ab FW 3), erscheinen nicht in der Tabelle – die Anzeige filtert sie automatisch.
- **Puffer/Solar:** Wenn du Puffer- oder Solar-Module konfiguriert hast, können weitere Reiter mit den zugehörigen Entity-IDs ergänzt werden (Register ab R3000 bzw. R4000).
- **Mehrere Wärmepumpen/Heizkreise:** Bei HP2, HC2 usw. die Entity-IDs im YAML anpassen (z. B. `hp2`, `hc2` statt `hp1`, `hc1`).
