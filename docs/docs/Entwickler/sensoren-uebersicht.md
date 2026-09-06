---
title: "Sensoren-Übersicht - Technische Dokumentation"
---

# Sensoren-Übersicht - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Dokumentation listet alle Sensoren der Lambda Heat Pumps Integration
auf, gruppiert nach Device-Typ. Register-Adressen, Skalierung und Zustände
stammen direkt aus `lambda_modbus/` (dem Register-Modell); die
Home-Assistant-Metadaten (State Class, Device Class) aus `sensor.py`.

## Legende

- **Register**: Adresse relativ zur Basis-Adresse des Moduls (siehe
  [Ablaufdiagramm – Modbus-Adressschema](Ablaufdiagramm.md#11-modbus-adressschema)).
- **Scale**: Skalierungsfaktor, mit dem der rohe Registerwert multipliziert wird.
- **unique_id**: Beispiel im **Legacy**-Namensschema (`use_legacy_modbus_names=True`,
  jede vor 3.5 angelegte Installation). Neue Installationen (ab 3.5) bilden
  die unique_id **ohne** `name_prefix` (`{module}{index}_{sensor_id}`) — siehe
  [unique_id und name_prefix](unique-id-name-prefix-kopplung.md).

## Main (Controller: Ambient + E-Manager)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_ambient_error_number` | `ambient_error_number` | 0 | 1 | - | - | Ambient Error Number |
| `eu08l_ambient_operating_state` | `ambient_operating_state` | 1 | 1 | - | enum | Ambient Operating State |
| `eu08l_ambient_temperature` | `ambient_temperature` | 2 | 0.1 | measurement | temperature | Ambient Temperature — **nur Firmware 1–7** |
| `eu08l_ambient_temperature_1h` | `ambient_temperature_1h` | 3 | 0.1 | measurement | temperature | Ambient Temperature 1h |
| `eu08l_ambient_temperature_calculated` | `ambient_temperature_calculated` | 4 | 0.1 | measurement | temperature | Ambient Temperature Calculated |
| `eu08l_emgr_error_number` | `emgr_error_number` | 100 | 1 | - | - | E-Manager Error Number |
| `eu08l_emgr_operating_state` | `emgr_operating_state` | 101 | 1 | - | enum | E-Manager Operating State |
| `eu08l_emgr_actual_power` | `emgr_actual_power` | 102 | 1 | measurement | power | E-Manager Actual Power |
| `eu08l_emgr_actual_power_consumption` | `emgr_actual_power_consumption` | 103 | 1 | measurement | power | E-Manager Power Consumption |
| `eu08l_emgr_power_consumption_setpoint` | `emgr_power_consumption_setpoint` | 104 | 1 | measurement | power | E-Manager Power Consumption Setpoint |

`ambient_temperature` liest auf Firmware ab V0.0.10-3K zwar noch etwas zurück,
aber keinen Messwert mehr (`0x8000`) — das Sensor-Template ist deshalb ab
Firmware 8 nicht mehr aktiv (`firmware_versions=("1-7",)` in `sensor.py`).

## Heat Pump (Wärmepumpe, voller Poll alle 30s)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_hp1_error_state` | `error_state` | 0 | 1 | - | enum | Error State |
| `eu08l_hp1_error_number` | `error_number` | 1 | 1 | - | - | Error Number |
| `eu08l_hp1_state` | `state` | 2 | 1 | - | enum | State |
| `eu08l_hp1_operating_state` | `operating_state` | 3 | 1 | - | enum | Operating State |
| `eu08l_hp1_flow_line_temperature` | `flow_line_temperature` | 4 | 0.01 | measurement | temperature | Flow Line Temperature |
| `eu08l_hp1_return_line_temperature` | `return_line_temperature` | 5 | 0.01 | measurement | temperature | Return Line Temperature |
| `eu08l_hp1_volume_flow_heat_sink` | `volume_flow_heat_sink` | 6 | 1 | measurement | - | Volume Flow Heat Sink (l/h) |
| `eu08l_hp1_energy_source_inlet_temperature` | `energy_source_inlet_temperature` | 7 | 0.01 | measurement | temperature | Energy Source Inlet Temperature |
| `eu08l_hp1_energy_source_outlet_temperature` | `energy_source_outlet_temperature` | 8 | 0.01 | measurement | temperature | Energy Source Outlet Temperature |
| `eu08l_hp1_volume_flow_energy_source` | `volume_flow_energy_source` | 9 | 0.01 | measurement | - | Volume Flow Energy Source (l/min) |
| `eu08l_hp1_compressor_unit_rating` | `compressor_unit_rating` | 10 | 0.01 | measurement | - | Compressor Unit Rating (%) |
| `eu08l_hp1_actual_heating_capacity` | `actual_heating_capacity` | 11 | 0.1 | measurement | power | Actual Heating Capacity (kW) |
| `eu08l_hp1_inverter_power_consumption` | `inverter_power_consumption` | 12 | 1 | measurement | power | Inverter Power Consumption |
| `eu08l_hp1_cop` | `cop` | 13 | 0.01 | measurement | - | COP (Controller-eigener Momentanwert) |
| `eu08l_hp1_request_type` | `request_type` | 15 | 1 | - | - | Request Type |
| `eu08l_hp1_requested_flow_line_temperature` | `requested_flow_line_temperature` | 16 | 0.1 | measurement | temperature | Requested Flow Line Temperature |
| `eu08l_hp1_requested_return_line_temperature` | `requested_return_line_temperature` | 17 | 0.1 | measurement | temperature | Requested Return Line Temperature |
| `eu08l_hp1_requested_flow_to_return_line_temperature_difference` | `requested_flow_to_return_line_temperature_difference` | 18 | 0.1 | measurement | temperature | Requested Flow to Return Line Temperature Difference |
| `eu08l_hp1_relais_state_2nd_heating_stage` | `relais_state_2nd_heating_stage` | 19 | 1 | - | enum | Relais State 2nd Heating Stage |
| `eu08l_hp1_compressor_power_consumption_accumulated` | `compressor_power_consumption_accumulated` | 20-21 (int32) | 1 | total_increasing | energy | Compressor Power Consumption Accumulated (Wh) |
| `eu08l_hp1_compressor_thermal_energy_output_accumulated` | `compressor_thermal_energy_output_accumulated` | 22-23 (int32) | 1 | total_increasing | energy | Compressor Thermal Energy Output Accumulated (Wh) |
| `eu08l_hp1_config_parameter_24` | `config_parameter_24` | 24 | 1 | - | - | Unknown Parameter (R1024) |
| `eu08l_hp1_vda_rating` | `vda_rating` | 25 | 0.01 | measurement | - | VdA Rating (%) |
| `eu08l_hp1_hot_gas_temperature` | `hot_gas_temperature` | 26 | 0.01 | measurement | temperature | Hot Gas Temperature |
| `eu08l_hp1_subcooling_temperature` | `subcooling_temperature` | 27 | 0.01 | measurement | temperature | Subcooling Temperature |
| `eu08l_hp1_suction_gas_temperature` | `suction_gas_temperature` | 28 | 0.01 | measurement | temperature | Suction Gas Temperature |
| `eu08l_hp1_condensation_temperature` | `condensation_temperature` | 29 | 0.01 | measurement | temperature | Condensation Temperature |
| `eu08l_hp1_evaporation_temperature` | `evaporation_temperature` | 30 | 0.01 | measurement | temperature | Evaporation Temperature |
| `eu08l_hp1_eqm_rating` | `eqm_rating` | 31 | 0.01 | measurement | - | EqM Rating (%) |
| `eu08l_hp1_expansion_valve_opening_angle` | `expansion_valve_opening_angle` | 32 | 0.01 | measurement | - | Expansion Valve Opening Angle (%) |
| `eu08l_hp1_config_parameter_33` | `config_parameter_33` | 33 | 1 | - | - | Unknown Parameter (R1033) |

Register 14 existiert nicht im Modell (unbelegt); Register 20-23 werden als
zwei 32-Bit-Zähler gelesen, siehe [Register-Reihenfolge](register-reihenfolge-int32.md).

### Heat Pump – Capacity Limits (eigener stündlicher Poll)

Elf Register, die der Controller nur einzeln beantwortet — daher auf einem
eigenen `LambdaCapacityLimitCoordinator` (siehe [Ablaufdiagramm](Ablaufdiagramm.md)),
nicht Teil des 30-Sekunden-Polls:

| sensor_id | Register | Scale | Name |
|-----------|----------|-------|------|
| `config_parameter_50` | 50 | 1 | Unknown Parameter (R1050) |
| `dhw_output_power_15c` | 51 | 0.1 | DHW Output Power at 15°C (kW) |
| `heating_min_output_power_15c` | 52 | 0.1 | Heating Min Output Power at 15°C (kW) |
| `heating_max_output_power_15c` | 53 | 0.1 | Heating Max Output Power at 15°C (kW) |
| `heating_min_output_power_0c` | 54 | 0.1 | Heating Min Output Power at 0°C (kW) |
| `heating_max_output_power_0c` | 55 | 0.1 | Heating Max Output Power at 0°C (kW) |
| `heating_min_output_power_minus15c` | 56 | 0.1 | Heating Min Output Power at -15°C (kW) |
| `heating_max_output_power_minus15c` | 57 | 0.1 | Heating Max Output Power at -15°C (kW) |
| `cooling_min_output_power` | 58 | 0.1 | Cooling Min Output Power (kW) |
| `cooling_max_output_power` | 59 | 0.1 | Cooling Max Output Power (kW) |
| `config_parameter_60` | 60 | 1 | Unknown Parameter (R1060) |

Alle zehn Leistungswerte sind über `number`-artige `writable`-Felder auch
beschreibbar (Installateur-Einstellungen), werden aber als `sensor`-Entities
dargestellt.

### Heat Pump – Zähler und COP (berechnet, kein eigenes Register)

Vollständige Aufschlüsselung nach Modus und Periode:
[Cycling-Sensoren](cycling-sensoren.md#Übersicht),
[Energieverbrauchssensoren](energieverbrauchssensoren.md),
[COP-Sensoren](cop-sensoren.md#sensoren-pro-wärmepumpe). Kurzfassung:

| Familie | Modi | Perioden | Anzahl je HP |
|---|---|---|---:|
| Cycling | heating, hot_water, cooling, defrost | total, daily, 2h, 4h | 16 |
| Cycling | compressor_start | total, daily, 2h, 4h, monthly | 5 |
| Yesterday (Cycling) | alle fünf Cycling-Modi | — (1 Wert je Modus) | 5 |
| Energie elektrisch | heating, hot_water, cooling, defrost, stby | total, daily, monthly, yearly (heating zusätzlich hourly) | 21 |
| Energie thermisch | heating, hot_water, cooling, defrost | total, daily, monthly, yearly (heating zusätzlich hourly) | 17 |
| COP | heating, hot_water, cooling | total, daily, monthly, yearly (heating zusätzlich hourly) | 13 |
| COP Lifetime | — | — | 1 |

**Summe: 78 berechnete Sensoren pro Wärmepumpe**, davon standardmäßig aktiv
nur die Total-Zähler (5 Cycling + 5 elektrisch + 4 thermisch), die drei
Total-COPs und `cop_calc` — 18 von 78. Der Rest (Perioden-Zähler, Yesterday,
Perioden-COPs) ist in der Entity-Registry deaktiviert, aber jederzeit
aktivierbar.

## Boiler (Warmwasserspeicher)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_boil1_error_number` | `error_number` | 0 | 1 | - | - | Error Number |
| `eu08l_boil1_operating_state` | `operating_state` | 1 | 1 | - | enum | Operating State |
| `eu08l_boil1_actual_high_temperature` | `actual_high_temperature` | 2 | 0.1 | measurement | temperature | Actual High Temperature |
| `eu08l_boil1_actual_low_temperature` | `actual_low_temperature` | 3 | 0.1 | measurement | temperature | Actual Low Temperature |
| `eu08l_boil1_actual_circulation_temperature` | `actual_circulation_temperature` | 4 | 0.1 | measurement | temperature | Actual Circulation Temperature |
| `eu08l_boil1_actual_circulation_pump_state` | `actual_circulation_pump_state` | 5 | 1 | - | enum | Circulation Pump State |
| `eu08l_boil1_target_high_temperature` | `target_high_temperature` | 50 | 0.1 | measurement | temperature | Target High Temperature (schreibbar über climate-Entity) |

## Buffer (Pufferspeicher)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_buff1_error_number` | `error_number` | 0 | 1 | - | - | Error Number |
| `eu08l_buff1_operating_state` | `operating_state` | 1 | 1 | - | enum | Operating State |
| `eu08l_buff1_actual_high_temperature` | `actual_high_temperature` | 2 | 0.1 | measurement | temperature | Actual High Temperature |
| `eu08l_buff1_actual_low_temperature` | `actual_low_temperature` | 3 | 0.1 | measurement | temperature | Actual Low Temperature |
| `eu08l_buff1_buffer_temperature_high_setpoint` | `buffer_temperature_high_setpoint` | 4 | 0.1 | measurement | temperature | Buffer High Temperature Setpoint |
| `eu08l_buff1_request_type` | `request_type` | 5 | 1 | - | enum | Request Type |
| `eu08l_buff1_request_flow_line_temp_setpoint` | `request_flow_line_temp_setpoint` | 6 | 0.1 | measurement | temperature | Flow Line Temperature Setpoint |
| `eu08l_buff1_request_return_line_temp_setpoint` | `request_return_line_temp_setpoint` | 7 | 0.1 | measurement | temperature | Return Line Temperature Setpoint |
| `eu08l_buff1_request_heat_sink_temp_diff_setpoint` | `request_heat_sink_temp_diff_setpoint` | 8 | 0.1 | measurement | - | Heat Sink Temperature Difference Setpoint (Kelvin) |
| `eu08l_buff1_modbus_request_heating_capacity` | `modbus_request_heating_capacity` | 9 | 0.1 | measurement | power | Requested Heating Capacity (kW) |
| `eu08l_buff1_maximum_buffer_temp` | `maximum_buffer_temp` | 50 | 0.1 | measurement | temperature | Maximum Buffer Temperature |

Register 5-9 melden `0xFFFF` (-1), solange kein aktiver Wunsch vorliegt — die
Integration liest das als `unknown`, nicht als -1 °C/kW (siehe
`lambda_modbus/buffer.py`).

## Solar (Solarmodul)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_sol1_error_number` | `error_number` | 0 | 1 | - | - | Error Number |
| `eu08l_sol1_operating_state` | `operating_state` | 1 | 1 | - | enum | Operating State |
| `eu08l_sol1_collector_temperature` | `collector_temperature` | 2 | 0.1 | measurement | temperature | Collector Temperature |
| `eu08l_sol1_storage_temperature` | `storage_temperature` | 3 | 0.1 | measurement | temperature | Storage Temperature |
| `eu08l_sol1_power_current` | `power_current` | 4 | 0.1 | measurement | power | Power Current (kW) |
| `eu08l_sol1_energy_total` | `energy_total` | 5-6 (int32) | 1 | total_increasing | energy | Energy Total (kWh) |
| `eu08l_sol1_maximum_buffer_temperature` | `maximum_buffer_temperature` | 50 | 0.1 | measurement | temperature | Maximum Buffer Temperature |
| `eu08l_sol1_buffer_changeover_temperature` | `buffer_changeover_temperature` | 51 | 0.1 | measurement | temperature | Buffer Changeover Temperature |

## Heating Circuit (Heizkreis)

| unique_id (Legacy) | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_hc1_error_number` | `error_number` | 0 | 1 | - | - | Error Number |
| `eu08l_hc1_operating_state` | `operating_state` | 1 | 1 | - | enum | Operating State |
| `eu08l_hc1_flow_line_temperature` | `flow_line_temperature` | 2 | 0.1 | measurement | temperature | Flow Line Temperature |
| `eu08l_hc1_return_line_temperature` | `return_line_temperature` | 3 | 0.1 | measurement | temperature | Return Line Temperature |
| `eu08l_hc1_room_device_temperature` | `room_device_temperature` | 4 | 0.1 | measurement | temperature | Room Device Temperature (auch von climate-Entities gelesen) |
| `eu08l_hc1_set_flow_line_temperature` | `set_flow_line_temperature` | 5 | 0.1 | measurement | temperature | Set Flow Line Temperature |
| `eu08l_hc1_operating_mode` | `operating_mode` | 6 | 1 | - | enum | Operating Mode |
| `eu08l_hc1_flow_line_temperature_setpoint` | `flow_line_temperature_setpoint` | 7 | 0.1 | measurement | temperature | Flow Line Temperature Setpoint (schreibbar) |
| `eu08l_hc1_target_temp_flow_line` | `target_temp_flow_line` | 7 | 0.1 | measurement | temperature | Target Flow Line Temperature — **nur Firmware ≥ 3**, read-only, gleiches Register wie oben |
| `eu08l_hc1_set_flow_line_offset_temperature` | `set_flow_line_offset_temperature` | 50 | 0.1 | measurement | temperature | Set Flow Line Offset Temperature (auch als `number`-Entity) |
| `eu08l_hc1_target_room_temperature` | `target_room_temperature` | 51 | 0.1 | measurement | temperature | Target Room Temperature (auch von climate-Entity geschrieben) |
| `eu08l_hc1_set_cooling_mode_room_temperature` | `set_cooling_mode_room_temperature` | 52 | 0.1 | measurement | temperature | Set Cooling Mode Room Temperature (auch von climate-Entity geschrieben) |

### Heating Circuit – Berechnet

| unique_id (Legacy) | sensor_id | State Class | Device Class | Name |
|-----------|-----------|-------------|--------------|------|
| `eu08l_hc1_heating_curve_flow_line_temperature_calc` | `heating_curve_flow_line_temperature_calc` | measurement | temperature | Heating Curve Flow Line Temperature Calc |

Berechnung: [Heizkurve](heizkurve.md).

## Verwandte Dokumentation

- [COP-Sensoren](cop-sensoren.md)
- [Energieverbrauchssensoren](energieverbrauchssensoren.md)
- [Cycling-Sensoren](cycling-sensoren.md)
- [Features](features.md) — Sentinel-Behandlung, Firmware-Filterung
- [Ablaufdiagramm](Ablaufdiagramm.md) — Adressschema, Poll-Ablauf
