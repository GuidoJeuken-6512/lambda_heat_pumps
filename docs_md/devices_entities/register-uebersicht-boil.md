# Register-Übersicht: Boiler (Warmwasser)

Nur **native Modbus-Register** des Warmwasser-Speichers (Boiler). Basis: `BOIL_SENSOR_TEMPLATES` in `const.py`, Basisadresse Boil1 = **2000** (Boil2 = 2100, …).

| Rel. | Register (Boil1 abs.) | Sensor-ID | Name | Typ | Einheit | Skalierung | Schreibbar |
|------|------------------------|------------|------|-----|---------|------------|------------|
| 0 | R2000 | error_number | Error Number | int16 | — | 1 | nein |
| 1 | R2001 | operating_state | Operating State | uint16 | — | 1 | nein |
| 2 | R2002 | actual_high_temperature | Actual High Temperature | int16 | °C | 0.1 | nein |
| 3 | R2003 | actual_low_temperature | Actual Low Temperature | int16 | °C | 0.1 | nein |
| 4 | R2004 | actual_circulation_temperature | Actual Circulation Temperature | int16 | °C | 0.1 | nein |
| 5 | R2005 | actual_circulation_pump_state | Circulation Pump State | int16 | — | 1 | nein |
| 50 | R2050 | target_high_temperature | Target High Temperature | int16 | °C | 0.1 | **ja** |

**HC/Climate:** Das Warmwasser-Climate nutzt für die Solltemperatur das Boiler-Register **R2050** (Boil1) bzw. 2150, 2200 … bei mehreren Speichern.

Quelle: `const.py` – `BOIL_SENSOR_TEMPLATES`, `BASE_ADDRESSES["boil"] = 2000`.
