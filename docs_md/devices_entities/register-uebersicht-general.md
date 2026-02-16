# Register-Übersicht: General (0–1000)

Native Modbus-Register im Bereich **0–1000** (Hauptgerät/Ambient + E-Manager). Basis: `SENSOR_TYPES` in `const.py` – feste Adressen, kein Subdevice-Offset.

| Register | Sensor-ID | Name | Typ | Einheit | Skalierung | Schreibbar |
|----------|------------|------|-----|---------|------------|------------|
| R0 | ambient_error_number | Ambient Error Number | int16 | — | 1 | nein |
| R1 | ambient_operating_state | Ambient Operating State | uint16 | — | 1 | nein |
| R2 | ambient_temperature | Ambient Temperature | int16 | °C | 0.1 | nein |
| R3 | ambient_temperature_1h | Ambient Temperature 1h | int16 | °C | 0.1 | nein |
| R4 | ambient_temperature_calculated | Ambient Temperature Calculated | int16 | °C | 0.1 | nein |
| R100 | emgr_error_number | E-Manager Error Number | int16 | — | 1 | nein |
| R101 | emgr_operating_state | E-Manager Operating State | uint16 | — | 1 | nein |
| R102 | emgr_actual_power | E-Manager Actual Power | int16 | W | 1 | nein |
| R103 | emgr_actual_power_consumption | E-Manager Power Consumption | int16 | W | 1 | nein |
| R104 | emgr_power_consumption_setpoint | E-Manager Power Consumption Setpoint | int16 | W | 1 | nein |

Quelle: `const.py` – `SENSOR_TYPES` (device_type: main).
