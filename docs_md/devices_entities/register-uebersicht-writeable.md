# Übersicht: Alle beschreibbaren Register

Alle **native Modbus-Register mit writeable: True** aus den Sensor-Templates (HP, Boil, Buff, Sol, HC). Basisadressen: HP 1000, Boil 2000, Buff 3000, Sol 4000, HC 5000; weitere Geräte +100 pro Index (z. B. HP2 = 1100, HC2 = 5100).

| Gerät | Rel. | Register (Index 1) | Sensor-ID | Name | Typ | Einheit |
|-------|------|--------------------|------------|------|-----|---------|
| **HP** | 15 | R1015 | request_type | Request-Type | int16 | — |
| HP | 16 | R1016 | requested_flow_line_temperature | Requested Flow Line Temperature | int16 | °C |
| HP | 17 | R1017 | requested_return_line_temperature | Requested Return Line Temperature | int16 | °C |
| HP | 18 | R1018 | requested_flow_to_return_line_temperature_difference | Requested Flow to Return Line Temperature Difference | int16 | °C |
| HP | 51 | R1051 | dhw_output_power_15c | DHW Output Power at 15°C | uint16 | kW |
| HP | 52 | R1052 | heating_min_output_power_15c | Heating Min Output Power at 15°C | uint16 | kW |
| HP | 53 | R1053 | heating_max_output_power_15c | Heating Max Output Power at 15°C | uint16 | kW |
| HP | 54 | R1054 | heating_min_output_power_0c | Heating Min Output Power at 0°C | uint16 | kW |
| HP | 55 | R1055 | heating_max_output_power_0c | Heating Max Output Power at 0°C | uint16 | kW |
| HP | 56 | R1056 | heating_min_output_power_minus15c | Heating Min Output Power at -15°C | uint16 | kW |
| HP | 57 | R1057 | heating_max_output_power_minus15c | Heating Max Output Power at -15°C | uint16 | kW |
| HP | 58 | R1058 | cooling_min_output_power | Cooling Min Output Power | uint16 | kW |
| HP | 59 | R1059 | cooling_max_output_power | Cooling Max Output Power | uint16 | kW |
| **Boil** | 50 | R2050 | target_high_temperature | Target High Temperature (Warmwasser-Soll) | int16 | °C |
| **Buff** | 4 | R3004 | buffer_temperature_high_setpoint | Buffer High Temperature Setpoint | int16 | °C |
| Buff | 50 | R3050 | maximum_buffer_temp | Maximum Temperature | int16 | °C |
| **Sol** | 50 | R4050 | maximum_buffer_temperature | Maximum Buffer Temperature | int16 | °C |
| Sol | 51 | R4051 | buffer_changeover_temperature | Buffer Changeover Temperature | int16 | °C |
| **HC** | 4 | R5004 | room_device_temperature | Room Device Temperature | int16 | °C |
| HC | 5 | R5005 | set_flow_line_temperature | Set Flow Line Temperature | int16 | °C |
| HC | 6 | R5006 | operating_mode | Operating Mode | int16 | — |
| HC | 50 | R5050 | set_flow_line_offset_temperature | Set Flow Line Offset Temperature | int16 | °C |
| HC | 51 | R5051 | target_room_temperature | Target Room Temperature | int16 | °C |
| HC | 52 | R5052 | set_cooling_mode_room_temperature | Set Cooling Mode Room Temperature | int16 | °C |

**Hinweis:** Das Warmwasser-Climate schreibt in R2050 (bzw. 2150, 2200 …); das Heizkreis-Climate in R5051 (bzw. 5151, 5251 …).

Quelle: `const.py` – HP/BOIL/BUFF/SOL/HC_SENSOR_TEMPLATES mit `writeable: True`.
