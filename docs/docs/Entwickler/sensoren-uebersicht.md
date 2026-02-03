---
title: "Sensoren-Übersicht - Technische Dokumentation"
---

# Sensoren-Übersicht - Technische Dokumentation

Diese Dokumentation listet alle Sensoren der Lambda Heat Pumps Integration auf, gruppiert nach Device-Typ und kategorisiert nach nativ (direkt aus Modbus) oder berechnet.

## Legende

- **Nativ**: Sensor liest Werte direkt aus Modbus-Registern
- **Berechnet**: Sensor berechnet Werte aus anderen Sensoren oder internen Logiken
- **Register**: Modbus-Register-Adresse (relative_address oder address)
- **Scale**: Skalierungsfaktor für Register-Werte
- **State Class**: Home Assistant State Class (measurement, total, total_increasing)
- **Device Class**: Home Assistant Device Class (temperature, power, energy, etc.)


## Main (Hauptgerät)

### Nativ (10 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_ambient_error_number` | `ambient_error_number` | 0 | 1 | total | - | Ambient Error Number |
| `eu08l_ambient_operating_state` | `ambient_operating_state` | 1 | 1 | - | - | Ambient Operating State |
| `eu08l_ambient_temperature` | `ambient_temperature` | 2 | 0.1 | measurement | temperature | Ambient Temperature |
| `eu08l_ambient_temperature_1h` | `ambient_temperature_1h` | 3 | 0.1 | measurement | temperature | Ambient Temperature 1h |
| `eu08l_ambient_temperature_calculated` | `ambient_temperature_calculated` | 4 | 0.1 | measurement | temperature | Ambient Temperature Calculated |
| `eu08l_emgr_error_number` | `emgr_error_number` | 100 | 1 | total | - | E-Manager Error Number |
| `eu08l_emgr_operating_state` | `emgr_operating_state` | 101 | 1 | - | - | E-Manager Operating State |
| `eu08l_emgr_actual_power` | `emgr_actual_power` | 102 | 1 | measurement | power | E-Manager Actual Power |
| `eu08l_emgr_actual_power_consumption` | `emgr_actual_power_consumption` | 103 | 1 | measurement | power | E-Manager Power Consumption |
| `eu08l_emgr_power_consumption_setpoint` | `emgr_power_consumption_setpoint` | 104 | 1 | measurement | power | E-Manager Power Consumption Setpoint |


## Heat Pump (Wärmepumpe)

### Nativ (42 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_hp1_error_state` | `error_state` | 0 | 1 | - | - | Error State |
| `eu08l_hp1_error_number` | `error_number` | 1 | 1 | total | - | Error Number |
| `eu08l_hp1_state` | `state` | 2 | 1 | - | - | State |
| `eu08l_hp1_operating_state` | `operating_state` | 3 | 1 | - | - | Operating State |
| `eu08l_hp1_flow_line_temperature` | `flow_line_temperature` | 4 | 0.01 | measurement | temperature | Flow Line Temperature |
| `eu08l_hp1_return_line_temperature` | `return_line_temperature` | 5 | 0.01 | measurement | temperature | Return Line Temperature |
| `eu08l_hp1_volume_flow_heat_sink` | `volume_flow_heat_sink` | 6 | 1 | total | - | Volume Flow Heat Sink |
| `eu08l_hp1_energy_source_inlet_temperature` | `energy_source_inlet_temperature` | 7 | 0.01 | measurement | temperature | Energy Source Inlet Temperature |
| `eu08l_hp1_energy_source_outlet_temperature` | `energy_source_outlet_temperature` | 8 | 0.01 | measurement | temperature | Energy Source Outlet Temperature |
| `eu08l_hp1_volume_flow_energy_source` | `volume_flow_energy_source` | 9 | 0.01 | total | - | Volume Flow Energy Source |
| `eu08l_hp1_compressor_unit_rating` | `compressor_unit_rating` | 10 | 0.01 | total | - | Compressor Unit Rating |
| `eu08l_hp1_actual_heating_capacity` | `actual_heating_capacity` | 11 | 0.1 | measurement | power | Actual Heating Capacity |
| `eu08l_hp1_inverter_power_consumption` | `inverter_power_consumption` | 12 | 1 | measurement | power | Inverter Power Consumption |
| `eu08l_hp1_cop` | `cop` | 13 | 0.01 | total | - | COP |
| `eu08l_hp1_request_type` | `request_type` | 15 | 1 | total | - | Request-Type |
| `eu08l_hp1_requested_flow_line_temperature` | `requested_flow_line_temperature` | 16 | 0.1 | measurement | temperature | Requested Flow Line Temperature |
| `eu08l_hp1_requested_return_line_temperature` | `requested_return_line_temperature` | 17 | 0.1 | measurement | temperature | Requested Return Line Temperature |
| `eu08l_hp1_requested_flow_to_return_line_temperature_difference` | `requested_flow_to_return_line_temperature_difference` | 18 | 0.1 | measurement | temperature | Requested Flow to Return Line Temperature Difference |
| `eu08l_hp1_relais_state_2nd_heating_stage` | `relais_state_2nd_heating_stage` | 19 | 1 | - | - | Relais State 2nd Heating Stage |
| `eu08l_hp1_compressor_power_consumption_accumulated` | `compressor_power_consumption_accumulated` | 20 | 1 | total_increasing | energy | Compressor Power Consumption Accumulated |
| `eu08l_hp1_compressor_thermal_energy_output_accumulated` | `compressor_thermal_energy_output_accumulated` | 22 | 1 | total_increasing | energy | Compressor Thermal Energy Output Accumulated |
| `eu08l_hp1_config_parameter_24` | `config_parameter_24` | 24 | 1 | measurement | - | Unknown Parameter (R1024) |
| `eu08l_hp1_vda_rating` | `vda_rating` | 25 | 0.01 | measurement | - | VdA Rating |
| `eu08l_hp1_hot_gas_temperature` | `hot_gas_temperature` | 26 | 0.01 | measurement | temperature | Hot Gas Temperature |
| `eu08l_hp1_subcooling_temperature` | `subcooling_temperature` | 27 | 0.01 | measurement | temperature | Subcooling Temperature |
| `eu08l_hp1_suction_gas_temperature` | `suction_gas_temperature` | 28 | 0.01 | measurement | temperature | Suction Gas Temperature |
| `eu08l_hp1_condensation_temperature` | `condensation_temperature` | 29 | 0.01 | measurement | temperature | Condensation Temperature |
| `eu08l_hp1_evaporation_temperature` | `evaporation_temperature` | 30 | 0.01 | measurement | temperature | Evaporation Temperature |
| `eu08l_hp1_eqm_rating` | `eqm_rating` | 31 | 0.01 | measurement | - | EqM Rating |
| `eu08l_hp1_expansion_valve_opening_angle` | `expansion_valve_opening_angle` | 32 | 0.01 | measurement | - | Expansion Valve Opening Angle |
| `eu08l_hp1_config_parameter_33` | `config_parameter_33` | 33 | 1 | measurement | - | Unknown Parameter (R1033) |
| `eu08l_hp1_config_parameter_50` | `config_parameter_50` | 50 | 1 | measurement | - | Unknown Parameter (R1050) |
| `eu08l_hp1_dhw_output_power_15c` | `dhw_output_power_15c` | 51 | 0.1 | measurement | power | DHW Output Power at 15°C |
| `eu08l_hp1_heating_min_output_power_15c` | `heating_min_output_power_15c` | 52 | 0.1 | measurement | power | Heating Min Output Power at 15°C |
| `eu08l_hp1_heating_max_output_power_15c` | `heating_max_output_power_15c` | 53 | 0.1 | measurement | power | Heating Max Output Power at 15°C |
| `eu08l_hp1_heating_min_output_power_0c` | `heating_min_output_power_0c` | 54 | 0.1 | measurement | power | Heating Min Output Power at 0°C |
| `eu08l_hp1_heating_max_output_power_0c` | `heating_max_output_power_0c` | 55 | 0.1 | measurement | power | Heating Max Output Power at 0°C |
| `eu08l_hp1_heating_min_output_power_minus15c` | `heating_min_output_power_minus15c` | 56 | 0.1 | measurement | power | Heating Min Output Power at -15°C |
| `eu08l_hp1_heating_max_output_power_minus15c` | `heating_max_output_power_minus15c` | 57 | 0.1 | measurement | power | Heating Max Output Power at -15°C |
| `eu08l_hp1_cooling_min_output_power` | `cooling_min_output_power` | 58 | 0.1 | measurement | power | Cooling Min Output Power |
| `eu08l_hp1_cooling_max_output_power` | `cooling_max_output_power` | 59 | 0.1 | measurement | power | Cooling Max Output Power |
| `eu08l_hp1_config_parameter_60` | `config_parameter_60` | 60 | 1 | measurement | - | Unknown Parameter (R1060) |

### Berechnet (75 Sensoren, inkl. COP)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Data Type | Name |
|-----------|-----------|----------|-------|-------------|--------------|-----------|------|
| `eu08l_hp1_compressor_start_cycling_2h` | `compressor_start_cycling_2h` | - | - | total | - | calculated | Compressor Start Cycling 2h |
| `eu08l_hp1_compressor_start_cycling_4h` | `compressor_start_cycling_4h` | - | - | total | - | calculated | Compressor Start Cycling 4h |
| `eu08l_hp1_compressor_start_cycling_daily` | `compressor_start_cycling_daily` | - | - | total | - | calculated | Compressor Start Cycling Daily |
| `eu08l_hp1_compressor_start_cycling_monthly` | `compressor_start_cycling_monthly` | - | - | total | - | calculated | Compressor Start Cycling Monthly |
| `eu08l_hp1_compressor_start_cycling_total` | `compressor_start_cycling_total` | - | - | total_increasing | - | calculated | Compressor Start Cycling Total |
| `eu08l_hp1_compressor_start_cycling_yesterday` | `compressor_start_cycling_yesterday` | - | - | total | - | calculated | Compressor Start Cycling Yesterday |
| `eu08l_hp1_cooling_cycling_2h` | `cooling_cycling_2h` | - | - | total | - | calculated | Cooling Cycling 2h |
| `eu08l_hp1_cooling_cycling_4h` | `cooling_cycling_4h` | - | - | total | - | calculated | Cooling Cycling 4h |
| `eu08l_hp1_cooling_cycling_daily` | `cooling_cycling_daily` | - | - | total | - | calculated | Cooling Cycling Daily |
| `eu08l_hp1_cooling_cycling_total` | `cooling_cycling_total` | - | - | total_increasing | - | calculated | Cooling Cycling Total |
| `eu08l_hp1_cooling_cycling_yesterday` | `cooling_cycling_yesterday` | - | - | total | - | calculated | Cooling Cycling Yesterday |
| `eu08l_hp1_cooling_energy_daily` | `cooling_energy_daily` | - | - | total | energy | calculated | Cooling Energy Daily |
| `eu08l_hp1_cooling_energy_monthly` | `cooling_energy_monthly` | - | - | total | energy | calculated | Cooling Energy Monthly |
| `eu08l_hp1_cooling_energy_total` | `cooling_energy_total` | - | - | total_increasing | energy | calculated | Cooling Energy Total |
| `eu08l_hp1_cooling_energy_yearly` | `cooling_energy_yearly` | - | - | total | energy | calculated | Cooling Energy Yearly |
| `eu08l_hp1_cooling_thermal_energy_daily` | `cooling_thermal_energy_daily` | - | - | total | energy | thermal_calculated | Cooling Thermal Energy Daily |
| `eu08l_hp1_cooling_thermal_energy_monthly` | `cooling_thermal_energy_monthly` | - | - | total | energy | thermal_calculated | Cooling Thermal Energy Monthly |
| `eu08l_hp1_cooling_thermal_energy_total` | `cooling_thermal_energy_total` | - | - | total_increasing | energy | thermal_calculated | Cooling Thermal Energy Total |
| `eu08l_hp1_cooling_thermal_energy_yearly` | `cooling_thermal_energy_yearly` | - | - | total | energy | thermal_calculated | Cooling Thermal Energy Yearly |
| `eu08l_hp1_cop_calc` | `cop_calc` | - | - | measurement | - | calculated | COP Calculated |
| `eu08l_hp1_defrost_cycling_2h` | `defrost_cycling_2h` | - | - | total | - | calculated | Defrost Cycling 2h |
| `eu08l_hp1_defrost_cycling_4h` | `defrost_cycling_4h` | - | - | total | - | calculated | Defrost Cycling 4h |
| `eu08l_hp1_defrost_cycling_daily` | `defrost_cycling_daily` | - | - | total | - | calculated | Defrost Cycling Daily |
| `eu08l_hp1_defrost_cycling_total` | `defrost_cycling_total` | - | - | total_increasing | - | calculated | Defrost Cycling Total |
| `eu08l_hp1_defrost_cycling_yesterday` | `defrost_cycling_yesterday` | - | - | total | - | calculated | Defrost Cycling Yesterday |
| `eu08l_hp1_defrost_energy_daily` | `defrost_energy_daily` | - | - | total | energy | calculated | Defrost Energy Daily |
| `eu08l_hp1_defrost_energy_monthly` | `defrost_energy_monthly` | - | - | total | energy | calculated | Defrost Energy Monthly |
| `eu08l_hp1_defrost_energy_total` | `defrost_energy_total` | - | - | total_increasing | energy | calculated | Defrost Energy Total |
| `eu08l_hp1_defrost_energy_yearly` | `defrost_energy_yearly` | - | - | total | energy | calculated | Defrost Energy Yearly |
| `eu08l_hp1_defrost_thermal_energy_daily` | `defrost_thermal_energy_daily` | - | - | total | energy | thermal_calculated | Defrost Thermal Energy Daily |
| `eu08l_hp1_defrost_thermal_energy_monthly` | `defrost_thermal_energy_monthly` | - | - | total | energy | thermal_calculated | Defrost Thermal Energy Monthly |
| `eu08l_hp1_defrost_thermal_energy_total` | `defrost_thermal_energy_total` | - | - | total_increasing | energy | thermal_calculated | Defrost Thermal Energy Total |
| `eu08l_hp1_defrost_thermal_energy_yearly` | `defrost_thermal_energy_yearly` | - | - | total | energy | thermal_calculated | Defrost Thermal Energy Yearly |
| `eu08l_hp1_heating_cycling_2h` | `heating_cycling_2h` | - | - | total | - | calculated | Heating Cycling 2h |
| `eu08l_hp1_heating_cycling_4h` | `heating_cycling_4h` | - | - | total | - | calculated | Heating Cycling 4h |
| `eu08l_hp1_heating_cycling_daily` | `heating_cycling_daily` | - | - | total | - | calculated | Heating Cycling Daily |
| `eu08l_hp1_heating_cycling_total` | `heating_cycling_total` | - | - | total_increasing | - | calculated | Heating Cycling Total |
| `eu08l_hp1_heating_cycling_yesterday` | `heating_cycling_yesterday` | - | - | total | - | calculated | Heating Cycling Yesterday |
| `eu08l_hp1_heating_energy_daily` | `heating_energy_daily` | - | - | total | energy | calculated | Heating Energy Daily |
| `eu08l_hp1_heating_energy_monthly` | `heating_energy_monthly` | - | - | total | energy | calculated | Heating Energy Monthly |
| `eu08l_hp1_heating_energy_total` | `heating_energy_total` | - | - | total_increasing | energy | calculated | Heating Energy Total |
| `eu08l_hp1_heating_energy_yearly` | `heating_energy_yearly` | - | - | total | energy | calculated | Heating Energy Yearly |
| `eu08l_hp1_heating_thermal_energy_daily` | `heating_thermal_energy_daily` | - | - | total | energy | thermal_calculated | Heating Thermal Energy Daily |
| `eu08l_hp1_heating_thermal_energy_monthly` | `heating_thermal_energy_monthly` | - | - | total | energy | thermal_calculated | Heating Thermal Energy Monthly |
| `eu08l_hp1_heating_thermal_energy_total` | `heating_thermal_energy_total` | - | - | total_increasing | energy | thermal_calculated | Heating Thermal Energy Total |
| `eu08l_hp1_heating_thermal_energy_yearly` | `heating_thermal_energy_yearly` | - | - | total | energy | thermal_calculated | Heating Thermal Energy Yearly |
| `eu08l_hp1_hot_water_cycling_2h` | `hot_water_cycling_2h` | - | - | total | - | calculated | Hot Water Cycling 2h |
| `eu08l_hp1_hot_water_cycling_4h` | `hot_water_cycling_4h` | - | - | total | - | calculated | Hot Water Cycling 4h |
| `eu08l_hp1_hot_water_cycling_daily` | `hot_water_cycling_daily` | - | - | total | - | calculated | Hot Water Cycling Daily |
| `eu08l_hp1_hot_water_cycling_total` | `hot_water_cycling_total` | - | - | total_increasing | - | calculated | Hot Water Cycling Total |
| `eu08l_hp1_hot_water_cycling_yesterday` | `hot_water_cycling_yesterday` | - | - | total | - | calculated | Hot Water Cycling Yesterday |
| `eu08l_hp1_hot_water_energy_daily` | `hot_water_energy_daily` | - | - | total | energy | calculated | Hot Water Energy Daily |
| `eu08l_hp1_hot_water_energy_monthly` | `hot_water_energy_monthly` | - | - | total | energy | calculated | Hot Water Energy Monthly |
| `eu08l_hp1_hot_water_energy_total` | `hot_water_energy_total` | - | - | total_increasing | energy | calculated | Hot Water Energy Total |
| `eu08l_hp1_hot_water_energy_yearly` | `hot_water_energy_yearly` | - | - | total | energy | calculated | Hot Water Energy Yearly |
| `eu08l_hp1_hot_water_thermal_energy_daily` | `hot_water_thermal_energy_daily` | - | - | total | energy | thermal_calculated | Hot Water Thermal Energy Daily |
| `eu08l_hp1_hot_water_thermal_energy_monthly` | `hot_water_thermal_energy_monthly` | - | - | total | energy | thermal_calculated | Hot Water Thermal Energy Monthly |
| `eu08l_hp1_hot_water_thermal_energy_total` | `hot_water_thermal_energy_total` | - | - | total_increasing | energy | thermal_calculated | Hot Water Thermal Energy Total |
| `eu08l_hp1_hot_water_thermal_energy_yearly` | `hot_water_thermal_energy_yearly` | - | - | total | energy | thermal_calculated | Hot Water Thermal Energy Yearly |
| `eu08l_hp1_stby_energy_daily` | `stby_energy_daily` | - | - | total | energy | calculated | STBY Energy Daily |
| `eu08l_hp1_stby_energy_monthly` | `stby_energy_monthly` | - | - | total | energy | calculated | STBY Energy Monthly |
| `eu08l_hp1_stby_energy_total` | `stby_energy_total` | - | - | total_increasing | energy | calculated | STBY Energy Total |
| `eu08l_hp1_stby_energy_yearly` | `stby_energy_yearly` | - | - | total | energy | calculated | STBY Energy Yearly |

### COP-Sensoren (berechnet, 12 pro Wärmepumpe)

COP = thermische Energie / elektrische Energie (Quellen: Thermal- und Energy-Sensoren). Kein Register, State Class: measurement.

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Data Type | Name |
|-----------|-----------|----------|-------|-------------|--------------|-----------|------|
| `eu08l_hp1_heating_cop_daily` | `heating_cop_daily` | - | - | measurement | - | cop | Heating COP Daily |
| `eu08l_hp1_heating_cop_monthly` | `heating_cop_monthly` | - | - | measurement | - | cop | Heating COP Monthly |
| `eu08l_hp1_heating_cop_yearly` | `heating_cop_yearly` | - | - | measurement | - | cop | Heating COP Yearly |
| `eu08l_hp1_heating_cop_total` | `heating_cop_total` | - | - | measurement | - | cop | Heating COP Total |
| `eu08l_hp1_hot_water_cop_daily` | `hot_water_cop_daily` | - | - | measurement | - | cop | Hot Water COP Daily |
| `eu08l_hp1_hot_water_cop_monthly` | `hot_water_cop_monthly` | - | - | measurement | - | cop | Hot Water COP Monthly |
| `eu08l_hp1_hot_water_cop_yearly` | `hot_water_cop_yearly` | - | - | measurement | - | cop | Hot Water COP Yearly |
| `eu08l_hp1_hot_water_cop_total` | `hot_water_cop_total` | - | - | measurement | - | cop | Hot Water COP Total |
| `eu08l_hp1_cooling_cop_daily` | `cooling_cop_daily` | - | - | measurement | - | cop | Cooling COP Daily |
| `eu08l_hp1_cooling_cop_monthly` | `cooling_cop_monthly` | - | - | measurement | - | cop | Cooling COP Monthly |
| `eu08l_hp1_cooling_cop_yearly` | `cooling_cop_yearly` | - | - | measurement | - | cop | Cooling COP Yearly |
| `eu08l_hp1_cooling_cop_total` | `cooling_cop_total` | - | - | measurement | - | cop | Cooling COP Total |


## Boiler (Warmwasserspeicher)

### Nativ (8 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_boil1_error_number` | `error_number` | 0 | 1 | total | - | Error Number |
| `eu08l_boil1_operating_state` | `operating_state` | 1 | 1 | - | - | Operating State |
| `eu08l_boil1_actual_high_temperature` | `actual_high_temperature` | 2 | 0.1 | measurement | temperature | Actual High Temperature |
| `eu08l_boil1_actual_low_temperature` | `actual_low_temperature` | 3 | 0.1 | measurement | temperature | Actual Low Temperature |
| `eu08l_boil1_actual_circulation_temperature` | `actual_circulation_temperature` | 4 | 0.1 | measurement | temperature | Actual Circulation Temperature |
| `eu08l_boil1_actual_circulation_pump_state` | `actual_circulation_pump_state` | 5 | 1 | - | - | Circulation Pump State |
| `eu08l_boil1_maximum_boiler_temperature` | `maximum_boiler_temperature` | 50 | 0.1 | measurement | temperature | Maximum Temperature |
| `eu08l_boil1_target_high_temperature` | `target_high_temperature` | 50 | 0.1 | measurement | temperature | Target High Temperature |


## Buffer (Pufferspeicher)

### Nativ (11 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_buff1_error_number` | `error_number` | 0 | 1 | total | - | Error Number |
| `eu08l_buff1_operating_state` | `operating_state` | 1 | 1 | - | - | Operating State |
| `eu08l_buff1_actual_high_temperature` | `actual_high_temperature` | 2 | 0.1 | measurement | temperature | Actual High Temperature |
| `eu08l_buff1_actual_low_temperature` | `actual_low_temperature` | 3 | 0.1 | measurement | temperature | Actual Low Temperature |
| `eu08l_buff1_buffer_temperature_high_setpoint` | `buffer_temperature_high_setpoint` | 4 | 0.1 | measurement | temperature | Buffer High Temperature Setpoint |
| `eu08l_buff1_request_type` | `request_type` | 5 | 1 | - | - | Request Type |
| `eu08l_buff1_request_flow_line_temp_setpoint` | `request_flow_line_temp_setpoint` | 6 | 0.1 | measurement | temperature | Flow Line Temperature Setpoint |
| `eu08l_buff1_request_return_line_temp_setpoint` | `request_return_line_temp_setpoint` | 7 | 0.1 | measurement | temperature | Return Line Temperature Setpoint |
| `eu08l_buff1_request_heat_sink_temp_diff_setpoint` | `request_heat_sink_temp_diff_setpoint` | 8 | 0.1 | measurement | - | Heat Sink Temperature Difference Setpoint |
| `eu08l_buff1_modbus_request_heating_capacity` | `modbus_request_heating_capacity` | 9 | 0.1 | measurement | power | Requested Heating Capacity |
| `eu08l_buff1_maximum_buffer_temp` | `maximum_buffer_temp` | 50 | 0.1 | measurement | temperature | Maximum Temperature |


## Solar (Solarmodul)

### Nativ (8 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_sol1_error_number` | `error_number` | 0 | 1 | total | - | Error Number |
| `eu08l_sol1_operating_state` | `operating_state` | 1 | 1 | - | - | Operating State |
| `eu08l_sol1_collector_temperature` | `collector_temperature` | 2 | 0.1 | measurement | temperature | Collector Temperature |
| `eu08l_sol1_storage_temperature` | `storage_temperature` | 3 | 0.1 | measurement | temperature | Storage Temperature |
| `eu08l_sol1_power_current` | `power_current` | 4 | 0.1 | measurement | power | Power Current |
| `eu08l_sol1_energy_total` | `energy_total` | 5 | 1 | total_increasing | energy | Energy Total |
| `eu08l_sol1_maximum_buffer_temperature` | `maximum_buffer_temperature` | 50 | 0.1 | measurement | temperature | Maximum Buffer Temperature |
| `eu08l_sol1_buffer_changeover_temperature` | `buffer_changeover_temperature` | 51 | 0.1 | measurement | temperature | Buffer Changeover Temperature |


## Heating Circuit (Heizkreis)

### Nativ (11 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Name |
|-----------|-----------|----------|-------|-------------|--------------|------|
| `eu08l_hc1_error_number` | `error_number` | 0 | 1 | total | - | Error Number |
| `eu08l_hc1_operating_state` | `operating_state` | 1 | 1 | - | - | Operating State |
| `eu08l_hc1_flow_line_temperature` | `flow_line_temperature` | 2 | 0.1 | measurement | temperature | Flow Line Temperature |
| `eu08l_hc1_return_line_temperature` | `return_line_temperature` | 3 | 0.1 | measurement | temperature | Return Line Temperature |
| `eu08l_hc1_room_device_temperature` | `room_device_temperature` | 4 | 0.1 | measurement | temperature | Room Device Temperature |
| `eu08l_hc1_set_flow_line_temperature` | `set_flow_line_temperature` | 5 | 0.1 | measurement | temperature | Set Flow Line Temperature |
| `eu08l_hc1_operating_mode` | `operating_mode` | 6 | 1 | - | - | Operating Mode |
| `eu08l_hc1_target_temp_flow_line` | `target_temp_flow_line` | 7 | 0.1 | measurement | temperature | Target Flow Line Temperature |
| `eu08l_hc1_set_flow_line_offset_temperature` | `set_flow_line_offset_temperature` | 50 | 0.1 | measurement | temperature | Set Flow Line Offset Temperature |
| `eu08l_hc1_target_room_temperature` | `target_room_temperature` | 51 | 0.1 | measurement | temperature | Target Room Temperature |
| `eu08l_hc1_set_cooling_mode_room_temperature` | `set_cooling_mode_room_temperature` | 52 | 0.1 | measurement | temperature | Set Cooling Mode Room Temperature |

### Berechnet (1 Sensoren)

| unique_id | sensor_id | Register | Scale | State Class | Device Class | Data Type | Name |
|-----------|-----------|----------|-------|-------------|--------------|-----------|------|
| `eu08l_hc1_heating_curve_flow_line_temperature_calc` | `heating_curve_flow_line_temperature_calc` | - | - | measurement | temperature | calculated | Heating Curve Flow Line Temperature Calc |

## Verwandte Dokumentation- [COP-Sensoren](cop-sensoren.md) – Technische Details zu COP-Sensoren (Quellen: Thermal- und Energy-Sensoren)
- [Energieverbrauchssensoren](energieverbrauchssensoren.md) – Energy- und Thermal-Energy-Sensoren
- [Cycling-Sensoren](cycling-sensoren.md) – Cycling- und Yesterday-Sensoren