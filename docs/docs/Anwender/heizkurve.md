---
title: "Heizkurve / berechnete Vorlauftemperatur"
---

# Heizkurve

*Zuletzt geändert am 17.10.2026*

Die Lambda Wärmepumpen Integration berechnet die Vorlauftemperatur des Heizkreises.
Die Heizkurve bestimmt die Vorlauftemperatur basierend auf der Außentemperatur und ermöglicht eine energieeffiziente und komfortable Heizungssteuerung. Der Sensor "heating_curve_flow_line_temperature_calc" / "Heizkurve Vorlauf ber." wird dazu zur Verfügung gestellt.

## Übersicht

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 50%; min-width: 300px;">
    <img src="../../assets/Integration_Heizkurve_de.png" alt="Heizkurven-Konfiguration" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 300px;">
    <p>Damit die Berechnung der Vorlauftemperatur für den Heizkreis erfolgen kann, müssen die Einstellungen zur Heizkurve von der Lambda in die Home Assistant Integration per Hand übertragen werden. Leider stellt die Lambda Wärmepumpe keine Möglichkeit zur Verfügung, diese Werte automatisch auszulesen.</p>
    
    <p>Die drei Stützpunkte, die Eco Temperatur Reduktion und das Vorlauf Offset müssen immer eingetragen werden, damit die Vorlauftemperatur berechnet werden kann.</p>
    
    <p>Wenn ein Raumthermometer in dem Heizkreis aktiviert ist, so müssen auch die Felder "Raum Temperatur Faktor", "Raum Temperatur Offset" konfiguriert werden. Diese Felder werden nur sichtbar in der Integration, wenn ein Raumthermometer in dem Heizkreis konfiguriert ist.</p>
  </div>
</div>

!!! info "Die Heizkurve der Lambda bleibt maßgeblich"
    Die drei Stützpunkte, die Eco-Absenkung und die Raumthermostat-Werte sind **Handwerte in Home Assistant**. Die Integration liest sie nicht von der Lambda und schreibt sie nicht an die Lambda. Sie dienen nur dem Sensor „Heizkurve Vorlauf berechnet“. Die Lambda regelt immer mit ihrer eigenen Heizkurve.

    Ab Werk zeigen die Stützpunkte die Standardwerte der Integration (48,3 / 39,0 / 32,0 °C), nicht die Werte Ihrer Lambda. Ändern Sie die Heizkurve am Display der Lambda, müssen Sie die Werte in Home Assistant von Hand nachziehen. Den tatsächlichen Vorlauf-Sollwert der Lambda zeigt der Sensor `hc1_target_temp_flow_line` (Firmware ab V0.0.5-3K) bzw. `hc1_flow_line_temperature_setpoint` (ältere Firmware). Weicht er dauerhaft vom berechneten Wert ab, passen die Stützpunkte in Home Assistant nicht mehr zur Lambda.

Weitere Informationen: [Raumthermometer](raumthermometer.md)

Anleitungen zur Lambda Wärmepumpe <a href="https://lambda-wp.at/tutorials/" target="_blank" rel="noopener noreferrer">Lambda Anleitungen</a>


