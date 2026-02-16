# Register-Übersicht: HC (Heizkreis) Subdevice

Nur **native Modbus-Register** des Heizkreises (HC), ohne Number- oder Template-Sensoren. Basis: `HC_SENSOR_TEMPLATES` in `const.py`, Basisadresse HC1 = **5000** (HC2 = 5100, HC3 = 5200, …).

**Hinweis:** `relative_address` bezieht sich auf das jeweilige HC-Subdevice; die absolute Modbus-Registeradresse für HC1 ist `5000 + relative_address`.

---

## HC1 – Absolute Register (Beispiel)

| Rel. | Register (HC1 abs.) | Sensor-ID | Name | Typ | Einheit | Skalierung | Schreibbar |
|------|---------------------|------------|------|-----|---------|------------|------------|
| 0 | R5000 | error_number | Error Number | int16 | — | 1 | nein |
| 1 | R5001 | operating_state | Operating State | uint16 | — | 1 | nein |
| 2 | R5002 | flow_line_temperature | Flow Line Temperature | int16 | °C | 0.1 | nein |
| 3 | R5003 | return_line_temperature | Return Line Temperature | int16 | °C | 0.1 | nein |
| 4 | R5004 | room_device_temperature | Room Device Temperature | int16 | °C | 0.1 | ja |
| 5 | R5005 | set_flow_line_temperature | Set Flow Line Temperature | int16 | °C | 0.1 | ja |
| 6 | R5006 | operating_mode | Operating Mode | int16 | — | 1 | ja |
| 7 | R5007 | target_temp_flow_line | Target Flow Line Temperature | int16 | °C | 0.1 | nein |
| 50 | R5050 | set_flow_line_offset_temperature | Set Flow Line Offset Temperature | int16 | °C | 0.1 | ja |
| 51 | R5051 | target_room_temperature | Target Room Temperature | int16 | °C | 0.1 | ja |
| 52 | R5052 | set_cooling_mode_room_temperature | Set Cooling Mode Room Temperature | int16 | °C | 0.1 | ja |

**Hinweis:** `target_temp_flow_line` (R5007) ist ab Firmware-Version 3 verfügbar.

---

## HC2 / HC3 / …

- **HC2:** Basisadresse **5100** → R5100, R5101, … R5050→R5150, R5151, R5152
- **HC3:** Basisadresse **5200** → R5200, R5201, …
- Formel: **absolute Adresse = 5000 + (HC-Index − 1) × 100 + relative_address**

---

## Nicht enthalten (keine nativen HC-Register)

- Heizkurve-Parameter (Number-Entities, z. B. aus `HC_HEATING_CURVE_NUMBER_CONFIG`)
- Raumthermostat-/Offset-/Eco-Number-Entities
- Template-Sensoren (z. B. berechnete Vorlaufsolltemperatur)

Quelle: `custom_components/lambda_heat_pumps/const.py` – `HC_SENSOR_TEMPLATES`, `BASE_ADDRESSES["hc"] = 5000`.
