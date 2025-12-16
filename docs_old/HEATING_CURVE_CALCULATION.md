# Heating Curve Calculation with Room Thermostat

This document explains how the sensor `*_heating_curve_flow_line_temperature_calc` derives the target flow temperature. It is based on the current implementation (November 2025) and a real-world configuration of heating circuit `HC1`. All numbers below are taken from the same snapshot to keep the calculation transparent.

- Outdoor temperature (`sensor.eu08l_ambient_temperature_calculated`): **10.7 °C**
- Heating-curve support points (number entities):
  - `number.eu08l_hc1_heating_curve_cold_outside_temp` = **48.3 °C** at −22 °C
  - `number.eu08l_hc1_heating_curve_mid_outside_temp` = **39.0 °C** at 0 °C
  - `number.eu08l_hc1_heating_curve_warm_outside_temp` = **32.0 °C** at +22 °C
- Flow-line offset (`hc1_set_flow_line_offset_temperature`): **0.0 °C**
- Room thermostat enabled (`room_thermostat_control = true`)
  - Room setpoint (`hc1_target_room_temperature`): **23.5 °C**
  - Room actual (`hc1_room_device_temperature`): **22.6 °C**
  - `number.eu08l_hc1_room_thermostat_offset` = **0.0**
  - `number.eu08l_hc1_room_thermostat_factor` = **1.0**

## 1. Base value from the heating curve

We interpolate linearly between the support points. For an outdoor temperature of 10.7 °C we are between 0 °C and +22 °C:

```text
T_base = y_mid + (T_out - x_mid) * (y_warm - y_mid) / (x_warm - x_mid)
       = 39.0 + (10.7 - 0) * (32.0 - 39.0) / (22 - 0)
       ≈ 35.6 °C
```

## 2. Flow-line offset

The Modbus value `hc1_set_flow_line_offset_temperature` is always added. In this snapshot it is 0.0 °C, so the value remains unchanged:

```text
T_flow = T_base + 0.0 = 35.6 °C
```

## 3. Room thermostat adjustment

Because the room thermostat is active, the delta between room setpoint and actual temperature is taken into account:

```text
Δ_RT = (T_set - T_actual - offset) * factor
     = (23.5 - 22.6 - 0.0) * 1.0
     = 0.9 °C

T_final = T_flow + Δ_RT = 35.6 + 0.9 = 36.5 °C
```

The sensor rounds to one decimal place → **36.5 °C**. Home Assistant logs exactly this value. 

## Summary

1. Interpolate the heating curve using the three number entities.  
2. Add the Modbus flow-line offset (register 50).  
3. Apply room-thermostat shift `(setpoint − actual − offset) * factor`.  
4. Round the result to one decimal place for presentation.



---

# Heizkurven-Berechnung mit Raumthermostat (Deutsch)

> **Hinweis:** Eine englische Beschreibung derselben Rechnung befindet sich im oberen Abschnitt. Dieser deutsche Teil führt die gleichen Zahlen aus und ergänzt Hinweise auf mögliche Differenzen zur Geräteanzeige.

Dieses Kapitel beschreibt ebenfalls den Sensor `*_heating_curve_flow_line_temperature_calc` anhand der folgenden Werte:

- Außentemperatur (`sensor.eu08l_ambient_temperature_calculated`): **10,7 °C**
- Heizkurven-Stützpunkte (Number-Entities):
  - `number.eu08l_hc1_heating_curve_cold_outside_temp` = **48,3 °C** bei −22 °C
  - `number.eu08l_hc1_heating_curve_mid_outside_temp` = **39,0 °C** bei 0 °C
  - `number.eu08l_hc1_heating_curve_warm_outside_temp` = **32,0 °C** bei +22 °C
- Flow-Line-Offset (`hc1_set_flow_line_offset_temperature`): **0,0 °C**
- Raumthermostat aktiviert (Option `room_thermostat_control = true`)
  - Raum-Soll (`hc1_target_room_temperature`): **23,5 °C**
  - Raum-Ist (`hc1_room_device_temperature`): **22,6 °C**
  - `number.eu08l_hc1_room_thermostat_offset` = **0,0**
  - `number.eu08l_hc1_room_thermostat_factor` = **1,0**

## 1. Grundwert aus Heizkurve

Zwischen den Stützpunkten wird linear interpoliert. Für 10,7 °C liegt die Außentemperatur zwischen 0 °C und 22 °C:

```text
T_base = y_mid + (T_out - x_mid) * (y_warm - y_mid) / (x_warm - x_mid)
       = 39,0 + (10,7 - 0) * (32,0 - 39,0) / (22 - 0)
       ≈ 35,6 °C
```

## 2. Flow-Line-Offset

Der Modbus-Wert `hc1_set_flow_line_offset_temperature` wird immer addiert. Im Beispiel ist er 0,0 °C, daher bleibt der Wert unverändert:

```text
T_flow = T_base + 0,0 = 35,6 °C
```

## 3. Raumthermostat-Korrektur

Da die Raumthermostat-Steuerung aktiv ist, wird das Delta zwischen Soll- und Ist-Temperatur berücksichtigt:

```text
Δ_RT = (T_soll - T_ist - offset) * factor
     = (23,5 - 22,6 - 0,0) * 1,0
     = 0,9 °C

T_final = T_flow + Δ_RT = 35,6 + 0,9 = 36,5 °C
```

Der Sensor rundet auf eine Nachkommastelle → **36,5 °C**. Genau diesen Wert protokolliert Home Assistant im Log (`Heizkurven-Wert ... -> 36.50°C`). 

## Zusammenfassung

1. Interpolation der Heizkurve aus den drei Number-Entitäten.  
2. Addieren des Flow-Line-Offsets aus Register 50.  
3. Additive Verschiebung durch Raumthermostat: `(Soll - Ist - Offset) * Faktor`.  
4. Ergebnis auf eine Nachkommastelle runden.



