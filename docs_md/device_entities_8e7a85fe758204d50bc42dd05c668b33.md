# Entitäten für Gerät: 8e7a85fe758204d50bc42dd05c668b33
**Erstellt am:** 2025-12-21 14:39:40
**Anzahl Entitäten:** 201
**Plattform:** solarman

## Übersicht nach Entitätstyp

- **binary_sensor**: 6 Entitäten
- **button**: 1 Entitäten
- **datetime**: 1 Entitäten
- **number**: 61 Entitäten
- **select**: 18 Entitäten
- **sensor**: 94 Entitäten
- **switch**: 14 Entitäten
- **time**: 6 Entitäten

---

## Detaillierte Liste

### BINARY_SENSOR

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `binary_sensor.inverter` |  | running | None | None | Nein |
| `binary_sensor.inverter_battery_alarm` | Battery Alarm | problem | None | None | Nein |
| `binary_sensor.inverter_battery_fault` | Battery Fault | problem | None | None | Nein |
| `binary_sensor.inverter_connection` | Connection | connectivity | None | diagnostic | Nein |
| `binary_sensor.inverter_grid` | Grid | power | None | None | Nein |
| `binary_sensor.inverter_microinverter` | Microinverter | power | None | None | Nein |

### BUTTON

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `button.inverter_restart` | Restart | None | None | diagnostic | Nein |

### DATETIME

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `datetime.inverter_date_time` | Date & Time | None | None | config | Nein |

### NUMBER

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `number.inverter_battery_absorption` | Battery Absorption | voltage | V | config | Nein |
| `number.inverter_battery_capacity` | Battery Capacity | None | Ah | config | Nein |
| `number.inverter_battery_charging_efficiency` | Battery Charging efficiency | None | % | config | Nein |
| `number.inverter_battery_empty` | Battery Empty | voltage | V | config | Nein |
| `number.inverter_battery_equalization` | Battery Equalization | voltage | V | config | Nein |
| `number.inverter_battery_equalization_cycle` | Battery Equalization Cycle | duration | d | config | Nein |
| `number.inverter_battery_equalization_time` | Battery Equalization Time | duration | h | config | Nein |
| `number.inverter_battery_float` | Battery Float | voltage | V | config | Nein |
| `number.inverter_battery_generator_charging_current` | Battery Generator Charging Current | current | A | config | Nein |
| `number.inverter_battery_generator_charging_start` | Battery Generator Charging Start | None | % | config | Nein |
| `number.inverter_battery_generator_charging_start_voltage` | Battery Generator Charging Start Voltage | voltage | V | config | Nein |
| `number.inverter_battery_grid_charging_current` | Battery Grid Charging Current | current | A | config | Nein |
| `number.inverter_battery_grid_charging_start` | Battery Grid Charging Start | None | % | config | Nein |
| `number.inverter_battery_grid_charging_start_voltage` | Battery Grid Charging Start Voltage | voltage | V | config | Nein |
| `number.inverter_battery_low_soc` | Battery Low SOC | None | % | config | Nein |
| `number.inverter_battery_low_voltage` | Battery Low Voltage | voltage | V | config | Nein |
| `number.inverter_battery_max_charging_current` | Battery Max Charging Current | current | A | config | Nein |
| `number.inverter_battery_max_discharging_current` | Battery Max Discharging Current | current | A | config | Nein |
| `number.inverter_battery_resistance` | Battery Resistance | None | mΩ | config | Nein |
| `number.inverter_battery_restart_soc` | Battery Restart SOC | None | % | config | Nein |
| `number.inverter_battery_restart_voltage` | Battery Restart Voltage | voltage | V | config | Nein |
| `number.inverter_battery_shutdown_soc` | Battery Shutdown SOC | None | % | config | Nein |
| `number.inverter_battery_shutdown_voltage` | Battery Shutdown Voltage | voltage | V | config | Nein |
| `number.inverter_battery_temperature_compensation` | Battery Temperature Compensation | None | mV/*C | config | Nein |
| `number.inverter_export_surplus_power` | Export Surplus Power | power | W | config | Nein |
| `number.inverter_generator_cooling_time` | Generator Cooling Time | duration | h | config | Nein |
| `number.inverter_generator_operating_time` | Generator Operating Time | duration | h | config | Nein |
| `number.inverter_generator_peak_shaving` | Generator Peak shaving | power | W | config | Nein |
| `number.inverter_grid_frequency_protection_high` | Grid frequency protection - high | frequency | Hz | config | Nein |
| `number.inverter_grid_frequency_protection_low` | Grid frequency protection - low | frequency | Hz | config | Nein |
| `number.inverter_grid_max_export_power` | Grid Max Export power | power | W | config | Nein |
| `number.inverter_grid_max_import_power` | Grid Max Import power | power | W | config | Nein |
| `number.inverter_grid_peak_shaving` | Grid Peak shaving | power | W | config | Nein |
| `number.inverter_grid_power_factor` | Grid Power Factor | power_factor | % | config | Nein |
| `number.inverter_grid_voltage_protection_high` | Grid voltage protection - high | voltage | V | config | Nein |
| `number.inverter_grid_voltage_protection_low` | Grid voltage protection - low | voltage | V | config | Nein |
| `number.inverter_program_1_power` | Program 1 Power | power | W | config | Nein |
| `number.inverter_program_1_soc` | Program 1 SOC | None | % | config | Nein |
| `number.inverter_program_1_voltage` | Program 1 Voltage | voltage | V | config | Nein |
| `number.inverter_program_2_power` | Program 2 Power | power | W | config | Nein |
| `number.inverter_program_2_soc` | Program 2 SOC | None | % | config | Nein |
| `number.inverter_program_2_voltage` | Program 2 Voltage | voltage | V | config | Nein |
| `number.inverter_program_3_power` | Program 3 Power | power | W | config | Nein |
| `number.inverter_program_3_soc` | Program 3 SOC | None | % | config | Nein |
| `number.inverter_program_3_voltage` | Program 3 Voltage | voltage | V | config | Nein |
| `number.inverter_program_4_power` | Program 4 Power | power | W | config | Nein |
| `number.inverter_program_4_soc` | Program 4 SOC | None | % | config | Nein |
| `number.inverter_program_4_voltage` | Program 4 Voltage | voltage | V | config | Nein |
| `number.inverter_program_5_power` | Program 5 Power | power | W | config | Nein |
| `number.inverter_program_5_soc` | Program 5 SOC | None | % | config | Nein |
| `number.inverter_program_5_voltage` | Program 5 Voltage | voltage | V | config | Nein |
| `number.inverter_program_6_power` | Program 6 Power | power | W | config | Nein |
| `number.inverter_program_6_soc` | Program 6 SOC | None | % | config | Nein |
| `number.inverter_program_6_voltage` | Program 6 Voltage | voltage | V | config | Nein |
| `number.inverter_pv_power` | PV Power | power | W | config | Nein |
| `number.inverter_self_check_time` | Self-check time | None | s | config | Nein |
| `number.inverter_smartload_off` | SmartLoad Off | None | % | config | Nein |
| `number.inverter_smartload_off_voltage` | SmartLoad Off Voltage | voltage | V | config | Nein |
| `number.inverter_smartload_on` | SmartLoad On | None | % | config | Nein |
| `number.inverter_smartload_on_voltage` | SmartLoad On Voltage | voltage | V | config | Nein |
| `number.inverter_zero_export_power` | Zero Export power | power | W | config | Nein |

### SELECT

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `select.inverter_ac_coupling` | AC Coupling | enum | None | config | Nein |
| `select.inverter_battery_bms_type` | Battery BMS Type | enum | None | config | Nein |
| `select.inverter_battery_control_mode` | Battery Control Mode | enum | None | config | Nein |
| `select.inverter_battery_operation_mode` | Battery Operation Mode | enum | None | config | Nein |
| `select.inverter_charging_signal` | Charging Signal | enum | None | config | Nein |
| `select.inverter_cloud` | Cloud | None | None | diagnostic | Nein |
| `select.inverter_energy_pattern` | Energy Pattern | enum | None | config | Nein |
| `select.inverter_grid_frequency` | Grid Frequency | enum | None | config | Nein |
| `select.inverter_grid_voltage` | Grid Voltage | enum | None | config | Nein |
| `select.inverter_io_mode` | IO Mode | enum | None | config | Nein |
| `select.inverter_program_1_charging` | Program 1 Charging | enum | None | config | Nein |
| `select.inverter_program_2_charging` | Program 2 Charging | enum | None | config | Nein |
| `select.inverter_program_3_charging` | Program 3 Charging | enum | None | config | Nein |
| `select.inverter_program_4_charging` | Program 4 Charging | enum | None | config | Nein |
| `select.inverter_program_5_charging` | Program 5 Charging | enum | None | config | Nein |
| `select.inverter_program_6_charging` | Program 6 Charging | enum | None | config | Nein |
| `select.inverter_time_of_use` | Time of Use | enum | None | config | Nein |
| `select.inverter_work_mode` | Work Mode | enum | None | config | Nein |

### SENSOR

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `sensor.inverter_battery` | Battery | battery | % | None | Nein |
| `sensor.inverter_battery_capacity` | Battery Capacity | energy_storage | kWh | None | Nein |
| `sensor.inverter_battery_current` | Battery Current | current | A | None | Nein |
| `sensor.inverter_battery_power` | Battery Power | power | W | None | Nein |
| `sensor.inverter_battery_soh` | Battery SOH | None | % | None | Nein |
| `sensor.inverter_battery_state` | Battery State | enum | None | None | Nein |
| `sensor.inverter_battery_temperature` | Battery Temperature | temperature | °C | None | Nein |
| `sensor.inverter_battery_voltage` | Battery Voltage | voltage | V | None | Nein |
| `sensor.inverter_dc_temperature` | DC Temperature | temperature | °C | None | Nein |
| `sensor.inverter_device` | Device | enum | None | None | Nein |
| `sensor.inverter_device_alarm` | Device Alarm | enum | None | None | Nein |
| `sensor.inverter_device_fault` | Device Fault | enum | None | None | Nein |
| `sensor.inverter_device_relay` | Device Relay | enum | None | None | Nein |
| `sensor.inverter_device_state` | Device State | enum | None | None | Nein |
| `sensor.inverter_external_ct1_current` | External CT1 Current | current | A | None | Nein |
| `sensor.inverter_external_ct1_power` | External CT1 Power | power | W | None | Nein |
| `sensor.inverter_external_ct2_current` | External CT2 Current | current | A | None | Nein |
| `sensor.inverter_external_ct2_power` | External CT2 Power | power | W | None | Nein |
| `sensor.inverter_external_ct3_current` | External CT3 Current | current | A | None | Nein |
| `sensor.inverter_external_ct3_power` | External CT3 Power | power | W | None | Nein |
| `sensor.inverter_external_power` | External Power | power | W | None | Nein |
| `sensor.inverter_grid_frequency` | Grid Frequency | frequency | Hz | None | Nein |
| `sensor.inverter_grid_l1_power` | Grid L1 Power | power | W | None | Nein |
| `sensor.inverter_grid_l1_voltage` | Grid L1 Voltage | voltage | V | None | Nein |
| `sensor.inverter_grid_l2_power` | Grid L2 Power | power | W | None | Nein |
| `sensor.inverter_grid_l2_voltage` | Grid L2 Voltage | voltage | V | None | Nein |
| `sensor.inverter_grid_l3_power` | Grid L3 Power | power | W | None | Nein |
| `sensor.inverter_grid_l3_voltage` | Grid L3 Voltage | voltage | V | None | Nein |
| `sensor.inverter_grid_power` | Grid Power | power | W | None | Nein |
| `sensor.inverter_internal_ct1_current` | Internal CT1 Current | current | A | None | Nein |
| `sensor.inverter_internal_ct1_power` | Internal CT1 Power | power | W | None | Nein |
| `sensor.inverter_internal_ct2_current` | Internal CT2 Current | current | A | None | Nein |
| `sensor.inverter_internal_ct2_power` | Internal CT2 Power | power | W | None | Nein |
| `sensor.inverter_internal_ct3_current` | Internal CT3 Current | current | A | None | Nein |
| `sensor.inverter_internal_ct3_power` | Internal CT3 Power | power | W | None | Nein |
| `sensor.inverter_internal_power` | Internal Power | power | W | None | Nein |
| `sensor.inverter_load_frequency` | Load Frequency | frequency | Hz | None | Nein |
| `sensor.inverter_load_l1_power` | Load L1 Power | power | W | None | Nein |
| `sensor.inverter_load_l1_voltage` | Load L1 Voltage | voltage | V | None | Nein |
| `sensor.inverter_load_l2_power` | Load L2 Power | power | W | None | Nein |
| `sensor.inverter_load_l2_voltage` | Load L2 Voltage | voltage | V | None | Nein |
| `sensor.inverter_load_l3_power` | Load L3 Power | power | W | None | Nein |
| `sensor.inverter_load_l3_voltage` | Load L3 Voltage | voltage | V | None | Nein |
| `sensor.inverter_load_power` | Load Power | power | W | None | Nein |
| `sensor.inverter_load_ups_l1_power` | Load UPS L1 Power | power | W | None | Nein |
| `sensor.inverter_load_ups_l2_power` | Load UPS L2 Power | power | W | None | Nein |
| `sensor.inverter_load_ups_l3_power` | Load UPS L3 Power | power | W | None | Nein |
| `sensor.inverter_load_ups_power` | Load UPS Power | power | W | None | Nein |
| `sensor.inverter_microinverter_energy` | Microinverter Energy | energy | kWh | None | Nein |
| `sensor.inverter_microinverter_energy_today` | Microinverter Energy - today | energy | kWh | None | Nein |
| `sensor.inverter_microinverter_l1_power` | Microinverter L1 Power | power | W | None | Nein |
| `sensor.inverter_microinverter_l1_voltage` | Microinverter L1 Voltage | voltage | V | None | Nein |
| `sensor.inverter_microinverter_l2_power` | Microinverter L2 Power | power | W | None | Nein |
| `sensor.inverter_microinverter_l2_voltage` | Microinverter L2 Voltage | voltage | V | None | Nein |
| `sensor.inverter_microinverter_l3_power` | Microinverter L3 Power | power | W | None | Nein |
| `sensor.inverter_microinverter_l3_voltage` | Microinverter L3 Voltage | voltage | V | None | Nein |
| `sensor.inverter_microinverter_power` | Microinverter Power | power | W | None | Nein |
| `sensor.inverter_output_frequency` | Output Frequency | frequency | Hz | None | Nein |
| `sensor.inverter_output_l1_current` | Output L1 Current | current | A | None | Nein |
| `sensor.inverter_output_l1_power` | Output L1 Power | power | W | None | Nein |
| `sensor.inverter_output_l1_voltage` | Output L1 Voltage | voltage | V | None | Nein |
| `sensor.inverter_output_l2_current` | Output L2 Current | current | A | None | Nein |
| `sensor.inverter_output_l2_power` | Output L2 Power | power | W | None | Nein |
| `sensor.inverter_output_l2_voltage` | Output L2 Voltage | voltage | V | None | Nein |
| `sensor.inverter_output_l3_current` | Output L3 Current | current | A | None | Nein |
| `sensor.inverter_output_l3_power` | Output L3 Power | power | W | None | Nein |
| `sensor.inverter_output_l3_voltage` | Output L3 Voltage | voltage | V | None | Nein |
| `sensor.inverter_power` | Power | power | W | None | Nein |
| `sensor.inverter_power_losses` | Power losses | power | W | None | Nein |
| `sensor.inverter_pv1_current` | PV1 Current | current | A | None | Nein |
| `sensor.inverter_pv1_power` | PV1 Power | power | W | None | Nein |
| `sensor.inverter_pv1_voltage` | PV1 Voltage | voltage | V | None | Nein |
| `sensor.inverter_pv2_current` | PV2 Current | current | A | None | Nein |
| `sensor.inverter_pv2_power` | PV2 Power | power | W | None | Nein |
| `sensor.inverter_pv2_voltage` | PV2 Voltage | voltage | V | None | Nein |
| `sensor.inverter_pv_power` | PV Power | power | W | None | Nein |
| `sensor.inverter_temperature` | Temperature | temperature | °C | None | Nein |
| `sensor.inverter_today_battery_charge` | Today Battery Charge | energy | kWh | None | Nein |
| `sensor.inverter_today_battery_discharge` | Today Battery Discharge | energy | kWh | None | Nein |
| `sensor.inverter_today_battery_life_cycles` | Today Battery Life Cycles | None | None | None | Nein |
| `sensor.inverter_today_energy_export` | Today Energy Export | energy | kWh | None | Nein |
| `sensor.inverter_today_energy_import` | Today Energy Import | energy | kWh | None | Nein |
| `sensor.inverter_today_load_consumption` | Today Load Consumption | energy | kWh | None | Nein |
| `sensor.inverter_today_losses` | Today Losses | energy | kWh | None | Nein |
| `sensor.inverter_today_production` | Today Production | energy | kWh | None | Nein |
| `sensor.inverter_total_battery_charge` | Total Battery Charge | energy | kWh | None | Nein |
| `sensor.inverter_total_battery_discharge` | Total Battery Discharge | energy | kWh | None | Nein |
| `sensor.inverter_total_battery_life_cycles` | Total Battery Life Cycles | None | None | None | Nein |
| `sensor.inverter_total_energy_export` | Total Energy Export | energy | kWh | None | Nein |
| `sensor.inverter_total_energy_import` | Total Energy Import | energy | kWh | None | Nein |
| `sensor.inverter_total_load_consumption` | Total Load Consumption | energy | kWh | None | Nein |
| `sensor.inverter_total_losses` | Total Losses | energy | kWh | None | Nein |
| `sensor.inverter_total_production` | Total Production | energy | kWh | None | Nein |
| `sensor.inverter_update_interval` | Update Interval | None | s | diagnostic | Nein |

### SWITCH

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `switch.inverter` |  | switch | None | config | Nein |
| `switch.inverter_access_point` | Access Point | switch | None | diagnostic | Nein |
| `switch.inverter_battery_generator_charging` | Battery Generator Charging | switch | None | config | Nein |
| `switch.inverter_battery_grid_charging` | Battery Grid Charging | switch | None | config | Nein |
| `switch.inverter_battery_wake_up` | Battery Wake Up | switch | None | config | Nein |
| `switch.inverter_export_asymmetry` | Export Asymmetry | switch | None | config | Nein |
| `switch.inverter_export_surplus` | Export Surplus | switch | None | config | Nein |
| `switch.inverter_generator_grid_side` | Generator Grid side | switch | None | config | Nein |
| `switch.inverter_generator_peak_shaving` | Generator Peak shaving | switch | None | config | Nein |
| `switch.inverter_grid_peak_shaving` | Grid Peak shaving | switch | None | config | Nein |
| `switch.inverter_microinverter` | Microinverter | switch | None | config | Nein |
| `switch.inverter_microinverter_export_cut_off` | Microinverter Export cut-off | switch | None | config | Nein |
| `switch.inverter_mppt_multi_point_scanning` | MPPT multi-point scanning | switch | None | config | Nein |
| `switch.inverter_off_grid` | Off Grid | switch | None | config | Nein |

### TIME

| Entity ID | Name | Device Class | Unit | Category | Disabled |
|-----------|------|--------------|------|----------|----------|
| `time.inverter_program_1_time` | Program 1 Time | None | None | config | Nein |
| `time.inverter_program_2_time` | Program 2 Time | None | None | config | Nein |
| `time.inverter_program_3_time` | Program 3 Time | None | None | config | Nein |
| `time.inverter_program_4_time` | Program 4 Time | None | None | config | Nein |
| `time.inverter_program_5_time` | Program 5 Time | None | None | config | Nein |
| `time.inverter_program_6_time` | Program 6 Time | None | None | config | Nein |


---

## Zusätzliche Informationen

### Entitäten mit speziellen Eigenschaften

#### Entitäten mit Capabilities

- **number.inverter_battery_absorption**: {
  "min": 38,
  "max": 61,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_capacity**: {
  "min": 0,
  "max": 2000,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_charging_efficiency**: {
  "min": 0.0,
  "max": 100.0,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_empty**: {
  "min": 38,
  "max": 61,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_equalization**: {
  "min": 38,
  "max": 61,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_equalization_cycle**: {
  "min": 0,
  "max": 90,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_equalization_time**: {
  "min": 0,
  "max": 10,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_float**: {
  "min": 38,
  "max": 61,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_generator_charging_current**: {
  "min": 0,
  "max": 240,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_generator_charging_start**: {
  "min": 0,
  "max": 100,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_generator_charging_start_voltage**: {
  "min": 0,
  "max": 63,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_grid_charging_current**: {
  "min": 0,
  "max": 350,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_grid_charging_start**: {
  "min": 0,
  "max": 100,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_grid_charging_start_voltage**: {
  "min": 0,
  "max": 63,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_low_soc**: {
  "min": 0,
  "max": 100,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_low_voltage**: {
  "min": 38,
  "max": 61,
  "step": 0.1,
  "mode": "box"
}
- **number.inverter_battery_max_charging_current**: {
  "min": 0,
  "max": 350,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_max_discharging_current**: {
  "min": 0,
  "max": 350,
  "step": 1.0,
  "mode": "box"
}
- **number.inverter_battery_resistance**: {
  "min": 0,
  "max": 6000,
  "step": 1.0,
  "mode": "auto"
}
- **number.inverter_battery_restart_soc**: {
  "min": 0,
  "max": 100,
  "step": 1.0,
  "mode": "box"
}

*... und 153 weitere Entitäten mit Capabilities*

#### Entitäten mit Options

- **binary_sensor.inverter**: {
  "conversation": {
    "should_expose": false
  }
}
- **binary_sensor.inverter_battery_alarm**: {
  "conversation": {
    "should_expose": false
  }
}
- **binary_sensor.inverter_battery_fault**: {
  "conversation": {
    "should_expose": false
  }
}
- **binary_sensor.inverter_connection**: {
  "conversation": {
    "should_expose": false
  }
}
- **binary_sensor.inverter_grid**: {
  "conversation": {
    "should_expose": false
  }
}
- **binary_sensor.inverter_microinverter**: {
  "conversation": {
    "should_expose": false
  }
}
- **button.inverter_restart**: {
  "conversation": {
    "should_expose": false
  }
}
- **datetime.inverter_date_time**: {
  "conversation": {
    "should_expose": false
  }
}
- **number.inverter_battery_absorption**: {
  "conversation": {
    "should_expose": false
  }
}
- **number.inverter_battery_capacity**: {
  "conversation": {
    "should_expose": false
  }
}

*... und 191 weitere Entitäten mit Options*

