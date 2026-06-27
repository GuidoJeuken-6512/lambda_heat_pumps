---
title: "Alle Sensoren der Integration"
---

# Alle Sensoren der Integration

*Zuletzt geändert am 20.04.2026*

Diese Seite listet alle Sensoren auf, die die Lambda Heat Pumps Integration in Home Assistant erzeugt. Die Sensoren sind nach Gerät und Funktion gruppiert.

> **Hinweis zur Benennung:** Die tatsächlichen Entitäts-IDs hängen vom konfigurierten `name_prefix` ab. Das Beispiel-Präfix in dieser Seite lautet `eu08l`. Bei einem anderen Präfix, z.B. `lambda`, beginnen alle IDs entsprechend mit `sensor.lambda_…`.

---

## Hauptgerät (Umgebung & E-Manager)

Diese Sensoren liefern allgemeine Umgebungsdaten und den Status des Energiemanagers.

### Umgebungstemperaturen

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_ambient_temperature` | °C | Aktuelle Außentemperatur |
| `sensor.eu08l_ambient_temperature_1h` | °C | Außentemperatur (Stundenmittel) |
| `sensor.eu08l_ambient_temperature_calculated` | °C | Berechnete Außentemperatur |

### Fehlerstatus

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.eu08l_ambient_error_number` | Fehlercode des Umgebungsmoduls |
| `sensor.eu08l_ambient_operating_state` | Betriebszustand des Umgebungsmoduls |

### E-Manager

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_emgr_actual_power` | W | Aktuelle Leistung am E-Manager |
| `sensor.eu08l_emgr_actual_power_consumption` | W | Tatsächlicher Stromverbrauch |
| `sensor.eu08l_emgr_power_consumption_setpoint` | W | Leistungssollwert des E-Managers |
| `sensor.eu08l_emgr_operating_state` | – | Betriebszustand des E-Managers |
| `sensor.eu08l_emgr_error_number` | – | Fehlercode des E-Managers |

---

## Wärmepumpe (HP)

Bei mehreren Wärmepumpen wird die Nummer hochgezählt: `hp1`, `hp2`, `hp3`.

### Betriebszustand

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.eu08l_hp1_state` | Aktueller Zustand der Wärmepumpe |
| `sensor.eu08l_hp1_operating_state` | Betriebsmodus (Heizen, Warmwasser, Kühlen, Standby …) |
| `sensor.eu08l_hp1_error_state` | Fehlerstatus |
| `sensor.eu08l_hp1_error_number` | Fehlercode |
| `sensor.eu08l_hp1_relais_state_2nd_heating_stage` | Status der zweiten Heizstufe |
| `sensor.eu08l_hp1_request_type` | Aktuelle Anforderungsart |

### Temperaturen

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hp1_flow_line_temperature` | °C | Vorlauftemperatur |
| `sensor.eu08l_hp1_return_line_temperature` | °C | Rücklauftemperatur |
| `sensor.eu08l_hp1_requested_flow_line_temperature` | °C | Geforderter Vorlauf-Sollwert |
| `sensor.eu08l_hp1_requested_return_line_temperature` | °C | Geforderter Rücklauf-Sollwert |
| `sensor.eu08l_hp1_requested_flow_to_return_line_temperature_difference` | °C | Geforderter Spreizungssollwert |
| `sensor.eu08l_hp1_energy_source_inlet_temperature` | °C | Quelleneinlauftemperatur (Sole/Luft) |
| `sensor.eu08l_hp1_energy_source_outlet_temperature` | °C | Quellenauslauftemperatur (Sole/Luft) |
| `sensor.eu08l_hp1_hot_gas_temperature` | °C | Heißgastemperatur |
| `sensor.eu08l_hp1_subcooling_temperature` | °C | Unterkühlung |
| `sensor.eu08l_hp1_suction_gas_temperature` | °C | Sauggastemperatur |
| `sensor.eu08l_hp1_condensation_temperature` | °C | Kondensationstemperatur |
| `sensor.eu08l_hp1_evaporation_temperature` | °C | Verdampfungstemperatur |

### Leistung & Volumenströme

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hp1_actual_heating_capacity` | kW | Aktuelle Heizleistung |
| `sensor.eu08l_hp1_inverter_power_consumption` | W | Stromaufnahme des Inverters |
| `sensor.eu08l_hp1_cop` | – | COP (Modbus-Rohwert) |
| `sensor.eu08l_hp1_compressor_unit_rating` | % | Kompressor-Auslastung |
| `sensor.eu08l_hp1_vda_rating` | % | VdA-Bewertung |
| `sensor.eu08l_hp1_eqm_rating` | % | EqM-Bewertung |
| `sensor.eu08l_hp1_expansion_valve_opening_angle` | % | Öffnungswinkel Expansionsventil |
| `sensor.eu08l_hp1_volume_flow_heat_sink` | l/h | Volumenstrom Wärmeabnehmer |
| `sensor.eu08l_hp1_volume_flow_energy_source` | l/min | Volumenstrom Energiequelle |

### Maximalleistungen (Konfigurationsparameter)

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hp1_dhw_output_power_15c` | kW | Warmwasser-Leistung bei +15 °C |
| `sensor.eu08l_hp1_heating_min_output_power_15c` | kW | Min. Heizleistung bei +15 °C |
| `sensor.eu08l_hp1_heating_max_output_power_15c` | kW | Max. Heizleistung bei +15 °C |
| `sensor.eu08l_hp1_heating_min_output_power_0c` | kW | Min. Heizleistung bei 0 °C |
| `sensor.eu08l_hp1_heating_max_output_power_0c` | kW | Max. Heizleistung bei 0 °C |
| `sensor.eu08l_hp1_heating_min_output_power_minus15c` | kW | Min. Heizleistung bei −15 °C |
| `sensor.eu08l_hp1_heating_max_output_power_minus15c` | kW | Max. Heizleistung bei −15 °C |
| `sensor.eu08l_hp1_cooling_min_output_power` | kW | Min. Kühlleistung |
| `sensor.eu08l_hp1_cooling_max_output_power` | kW | Max. Kühlleistung |

### Gesamtenergie (akkumuliert, aus Modbus)

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hp1_compressor_power_consumption_accumulated` | Wh | Gesamtstromverbrauch (akkumuliert) |
| `sensor.eu08l_hp1_compressor_thermal_energy_output_accumulated` | Wh | Gesamtwärmeabgabe (akkumuliert) |

### Elektrischer Energieverbrauch (berechnet, nach Zeitraum)

Die Integration berechnet den Stromverbrauch je Betriebsmodus und Zeitraum:

| Modus | Täglich | Monatlich | Jährlich | Gesamt |
|-------|---------|-----------|----------|--------|
| **Heizen** | `heating_energy_daily` | `heating_energy_monthly` | `heating_energy_yearly` | `heating_energy_total` |
| **Warmwasser** | `hot_water_energy_daily` | `hot_water_energy_monthly` | `hot_water_energy_yearly` | `hot_water_energy_total` |
| **Kühlen** | `cooling_energy_daily` | `cooling_energy_monthly` | `cooling_energy_yearly` | `cooling_energy_total` |
| **Abtauen** | `defrost_energy_daily` | `defrost_energy_monthly` | `defrost_energy_yearly` | `defrost_energy_total` |
| **Standby** | `stby_energy_daily` | `stby_energy_monthly` | `stby_energy_yearly` | `stby_energy_total` |

Alle mit Präfix `sensor.eu08l_hp1_`, Einheit: **kWh**. Zusätzlich gibt es `heating_energy_hourly` für stündliche Auflösung.

### Thermische Energie (berechnet, nach Zeitraum)

Entsprechend wie oben, aber für die thermische Wärmeabgabe (Suffix `_thermal_energy_...`):

| Modus | Täglich | Monatlich | Jährlich | Gesamt |
|-------|---------|-----------|----------|--------|
| **Heizen** | `heating_thermal_energy_daily` | `heating_thermal_energy_monthly` | `heating_thermal_energy_yearly` | `heating_thermal_energy_total` |
| **Warmwasser** | `hot_water_thermal_energy_daily` | `hot_water_thermal_energy_monthly` | `hot_water_thermal_energy_yearly` | `hot_water_thermal_energy_total` |
| **Kühlen** | `cooling_thermal_energy_daily` | `cooling_thermal_energy_monthly` | `cooling_thermal_energy_yearly` | `cooling_thermal_energy_total` |
| **Abtauen** | `defrost_thermal_energy_daily` | `defrost_thermal_energy_monthly` | `defrost_thermal_energy_yearly` | `defrost_thermal_energy_total` |

Alle mit Präfix `sensor.eu08l_hp1_`, Einheit: **kWh**.

### Effizienz – COP-Sensoren (berechnet)

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.eu08l_hp1_heating_cop_daily` | Tages-COP Heizen |
| `sensor.eu08l_hp1_heating_cop_monthly` | Monats-COP Heizen |
| `sensor.eu08l_hp1_heating_cop_yearly` | Jahres-COP Heizen |
| `sensor.eu08l_hp1_heating_cop_total` | Gesamt-COP Heizen |
| `sensor.eu08l_hp1_hot_water_cop_daily` | Tages-COP Warmwasser |
| `sensor.eu08l_hp1_hot_water_cop_monthly` | Monats-COP Warmwasser |
| `sensor.eu08l_hp1_hot_water_cop_yearly` | Jahres-COP Warmwasser |
| `sensor.eu08l_hp1_hot_water_cop_total` | Gesamt-COP Warmwasser |
| `sensor.eu08l_hp1_cooling_cop_daily` | Tages-COP Kühlen |
| `sensor.eu08l_hp1_cooling_cop_monthly` | Monats-COP Kühlen |
| `sensor.eu08l_hp1_cooling_cop_yearly` | Jahres-COP Kühlen |
| `sensor.eu08l_hp1_cooling_cop_total` | Gesamt-COP Kühlen |

> Mehr Infos: [COP-Sensoren](cop-sensoren.md)

### Kompressorstarts & Zyklen (berechnet)

| Zeitraum | Sensor-Suffix | Beschreibung |
|----------|--------------|--------------|
| Gesamt | `_total` | Gesamtzahl seit Installation |
| Täglich | `_daily` | Heutige Starts (Reset Mitternacht) |
| Gestern | `_yesterday` | Starts vom Vortag |
| Monatlich | `_monthly` | Starts im aktuellen Monat |
| 2 Stunden | `_2h` | Starts der letzten 2 Stunden |
| 4 Stunden | `_4h` | Starts der letzten 4 Stunden |

Verfügbare Zähler mit Präfix `sensor.eu08l_hp1_`:

| Betriebsmodus | Basis-Name |
|---------------|-----------|
| Kompressorstarts | `compressor_start_cycling_…` |
| Heizen | `heating_cycling_…` |
| Warmwasser | `hot_water_cycling_…` |
| Kühlen | `cooling_cycling_…` |
| Abtauen | `defrost_cycling_…` |

> Mehr Infos: [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md)

---

## Warmwasserspeicher (Boiler)

Bei mehreren Boilern: `boil1`, `boil2`, …

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_boil1_operating_state` | – | Betriebszustand |
| `sensor.eu08l_boil1_error_number` | – | Fehlercode |
| `sensor.eu08l_boil1_actual_high_temperature` | °C | Ist-Temperatur oben |
| `sensor.eu08l_boil1_actual_low_temperature` | °C | Ist-Temperatur unten |
| `sensor.eu08l_boil1_actual_circulation_temperature` | °C | Zirkulationstemperatur |
| `sensor.eu08l_boil1_actual_circulation_pump_state` | – | Zirkulationspumpenstatus |
| `sensor.eu08l_boil1_target_high_temperature` | °C | Solltemperatur oben |

> Warmwasser-Solltemperatur kann auch über die Climate-Entität gesteuert werden. Mehr: [Warmwasser Solltemperatur Steuerung](warmwasser-solltemperatur.md)

---

## Pufferspeicher (Buffer)

Bei mehreren Puffern: `buff1`, `buff2`, …

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_buff1_operating_state` | – | Betriebszustand |
| `sensor.eu08l_buff1_error_number` | – | Fehlercode |
| `sensor.eu08l_buff1_actual_high_temperature` | °C | Ist-Temperatur oben |
| `sensor.eu08l_buff1_actual_low_temperature` | °C | Ist-Temperatur unten |
| `sensor.eu08l_buff1_buffer_temperature_high_setpoint` | °C | Temperatursollwert oben |
| `sensor.eu08l_buff1_request_type` | – | Anforderungsart |
| `sensor.eu08l_buff1_request_flow_line_temp_setpoint` | °C | Vorlauf-Solltemperatur |
| `sensor.eu08l_buff1_request_return_line_temp_setpoint` | °C | Rücklauf-Solltemperatur |
| `sensor.eu08l_buff1_request_heat_sink_temp_diff_setpoint` | K | Spreizungs-Sollwert |
| `sensor.eu08l_buff1_modbus_request_heating_capacity` | kW | Angeforderter Heizbedarf |
| `sensor.eu08l_buff1_maximum_buffer_temp` | °C | Maximale Puffertemperatur |

---

## Solarmodul (Solar)

Bei mehreren Solarmodulen: `sol1`, `sol2`.

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_sol1_operating_state` | – | Betriebszustand |
| `sensor.eu08l_sol1_error_number` | – | Fehlercode |
| `sensor.eu08l_sol1_collector_temperature` | °C | Kollektortemperatur |
| `sensor.eu08l_sol1_storage_temperature` | °C | Speichertemperatur |
| `sensor.eu08l_sol1_power_current` | kW | Aktuelle Solarleistung |
| `sensor.eu08l_sol1_energy_total` | kWh | Gesamtertrag |
| `sensor.eu08l_sol1_maximum_buffer_temperature` | °C | Maximale Puffertemperatur |
| `sensor.eu08l_sol1_buffer_changeover_temperature` | °C | Puffer-Umschalttemperatur |

---

## Heizkreis (HC)

Bei mehreren Heizkreisen: `hc1`, `hc2`, `hc3`, …

### Betrieb & Temperaturen

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hc1_operating_state` | – | Betriebszustand des Heizkreises |
| `sensor.eu08l_hc1_operating_mode` | – | Betriebsmodus (Heizen, Kühlen, ECO …) |
| `sensor.eu08l_hc1_error_number` | – | Fehlercode |
| `sensor.eu08l_hc1_flow_line_temperature` | °C | Vorlauftemperatur |
| `sensor.eu08l_hc1_return_line_temperature` | °C | Rücklauftemperatur |
| `sensor.eu08l_hc1_room_device_temperature` | °C | Raumtemperatur (Gerät oder Thermostat) |
| `sensor.eu08l_hc1_set_flow_line_temperature` | °C | Vorlauf-Sollwert |
| `sensor.eu08l_hc1_target_temp_flow_line` | °C | Berechneter Vorlauf-Zielwert (FW 3+) |
| `sensor.eu08l_hc1_set_flow_line_offset_temperature` | °C | Vorlauf-Offset |
| `sensor.eu08l_hc1_target_room_temperature` | °C | Raum-Solltemperatur |
| `sensor.eu08l_hc1_set_cooling_mode_room_temperature` | °C | Soll-Raumtemperatur im Kühlbetrieb |

### Berechneter Sensor

| Sensor | Einheit | Beschreibung |
|--------|---------|--------------|
| `sensor.eu08l_hc1_heating_curve_flow_line_temperature_calc` | °C | Heizkurve: berechnete Vorlauftemperatur auf Basis der Außentemperatur |

> Mehr Infos zur Heizkurve: [Heizkurve](heizkurve.md)

---

## Übersicht: Anzahl Sensoren

| Gerät | Nativ | Berechnet | Gesamt |
|-------|-------|-----------|--------|
| Hauptgerät (Main) | 10 | 0 | 10 |
| Wärmepumpe (HP) | 42 | 89 | 131 |
| Boiler | 7 | 0 | 7 |
| Pufferspeicher | 11 | 0 | 11 |
| Solarmodul | 8 | 0 | 8 |
| Heizkreis | 11 | 1 | 12 |

> Alle Sensoren außer dem Hauptgerät werden je Instanz erstellt. Mit 2 Wärmepumpen, 2 Heizkreisen, 1 Boiler usw. verdoppeln sich die entsprechenden Sensoren.

---

## Verwandte Seiten

- [COP-Sensoren](cop-sensoren.md) – Erklärung der Effizienz-Sensoren
- [Energieverbrauchsberechnung](Energieverbrauchsberechnung.md) – Wie die Energiesensoren berechnet werden
- [Heizkurve](heizkurve.md) – Heizkurvenberechnung und -konfiguration
- [Anpassungen abhängig von der Firmware](anpassungen-sensoren-firmware.md) – Welche Sensoren bei welcher Firmware verfügbar sind
- [Historische Daten übernehmen](historische-daten.md) – Zählerstände bei Migration übernehmen
