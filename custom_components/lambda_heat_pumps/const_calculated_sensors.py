from __future__ import annotations

"""Calculated sensor templates for Lambda Heat Pumps integration."""

from .const_sensor import HC_HEATING_CURVE_TEMPLATE_PARAMS  # noqa: E402

# Calculated Sensor Templates
CALCULATED_SENSOR_TEMPLATES = {
    # Beispiel für einen berechneten Sensor: COP (alt, basierend auf Accumulated Registern)
    "cop_calc": {
        "name": "COP Calculated",
        "unit": None,
        "precision": 2,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": None,
        "template": (
            "{{% set thermal = states('sensor.{full_entity_prefix}_compressor_thermal_energy_output_accumulated') | float(0) %}}"
            "{{% set power = states('sensor.{full_entity_prefix}_compressor_power_consumption_accumulated') | float(1) %}}"
            "{{{{ (thermal / power) | round(2) if power > 0 else 0 }}}}"
        ),
    },
    # COP Sensoren werden jetzt als echte Python-Sensoren (LambdaCOPSensor) erstellt
    # und nicht mehr als Template-Sensoren. Siehe sensor.py für die Implementierung.
    # Statuswechsel-Sensoren (Flankenerkennung) - TOTAL
    # Diese Sensoren werden dynamisch für jede HP (und ggf. andere Geräte) erzeugt
    # und zählen, wie oft in einen bestimmten Modus gewechselt wurde (z.B. CH, DHW, CC, DEFROST)
    # Die Namensgebung und Indizierung erfolgt dynamisch je nach Konfiguration (legacy_name, HP-Index)
    # Die Logik zur Erkennung und Zählung erfolgt später im Code (z.B. im Coordinator)
    "heating_cycling_total": {
        "name": "Heating Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 1,  # CH
        "operating_state": "heating",
        "period": "total",
        "reset_interval": None,
        "description": "Zählt, wie oft in den Modus Heizen (CH) gewechselt wurde.",
    },
    "hot_water_cycling_total": {
        "name": "Hot Water Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 2,  # DHW
        "operating_state": "hot_water",
        "period": "total",
        "reset_interval": None,
        "description": "Zählt, wie oft in den Modus Warmwasser (DHW) gewechselt wurde.",
    },
    "cooling_cycling_total": {
        "name": "Cooling Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 3,  # CC
        "operating_state": "cooling",
        "period": "total",
        "reset_interval": None,
        "description": "Zählt, wie oft in den Modus Kühlen (CC) gewechselt wurde.",
    },
    "defrost_cycling_total": {
        "name": "Defrost Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 5,  # DEFROST
        "operating_state": "defrost",
        "period": "total",
        "reset_interval": None,
        "description": "Zählt, wie oft in den Modus Abtauen (DEFROST) gewechselt wurde.",
    },
    "compressor_start_cycling_total": {
        "name": "Compressor Start Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 5,  # START COMPRESSOR (HP_STATE)
        "operating_state": "compressor_start",
        "period": "total",
        "reset_interval": None,
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "Zählt, wie oft der Kompressor gestartet wurde (HP_STATE = START COMPRESSOR).",
    },
    # Yesterday Cycling Sensoren (echte Entities - speichern gestern Werte)
    "heating_cycling_yesterday": {
        "name": "Heating Cycling Yesterday",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "heating",
        "period": "yesterday",
        "reset_interval": None,
        "description": "Speichert die gestern erreichten Daily-Cycling-Werte.",
    },
    "hot_water_cycling_yesterday": {
        "name": "Hot Water Cycling Yesterday",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "hot_water",
        "period": "yesterday",
        "reset_interval": None,
        "description": "Speichert die gestern erreichten Daily-Cycling-Werte.",
    },
    "cooling_cycling_yesterday": {
        "name": "Cooling Cycling Yesterday",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "cooling",
        "period": "yesterday",
        "reset_interval": None,
        "description": "Speichert die gestern erreichten Daily-Cycling-Werte.",
    },
    "defrost_cycling_yesterday": {
        "name": "Defrost Cycling Yesterday",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "defrost",
        "period": "yesterday",
        "reset_interval": None,
        "description": "Speichert die gestern erreichten Daily-Cycling-Werte.",
    },
    "compressor_start_cycling_yesterday": {
        "name": "Compressor Start Cycling Yesterday",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "compressor_start",
        "period": "yesterday",
        "reset_interval": None,
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "Speichert die gestern erreichten Daily-Cycling-Werte.",
    },

    # Daily Cycling Sensoren (echte Entities - werden täglich um Mitternacht auf 0 gesetzt)
    "heating_cycling_daily": {
        "name": "Heating Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "heating",
        "reset_interval": "daily",
        "description": "Tägliche Cycling-Zähler für Heizen, werden täglich um Mitternacht auf 0 gesetzt.",
    },
    "hot_water_cycling_daily": {
        "name": "Hot Water Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "hot_water",
        "reset_interval": "daily",
        "description": "Tägliche Cycling-Zähler für Warmwasser, werden täglich um Mitternacht auf 0 gesetzt.",
    },
    "cooling_cycling_daily": {
        "name": "Cooling Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "cooling",
        "reset_interval": "daily",
        "description": "Tägliche Cycling-Zähler für Kühlen, werden täglich um Mitternacht auf 0 gesetzt.",
    },
    "defrost_cycling_daily": {
        "name": "Defrost Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "defrost",
        "reset_interval": "daily",
        "description": "Tägliche Cycling-Zähler für Abtauen, werden täglich um Mitternacht auf 0 gesetzt.",
    },
    "compressor_start_cycling_daily": {
        "name": "Compressor Start Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "compressor_start",
        "reset_interval": "daily",
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "Tägliche Cycling-Zähler für Kompressor-Starts, werden täglich um Mitternacht auf 0 gesetzt.",
    },
    "compressor_start_cycling_monthly": {
        "name": "Compressor Start Cycling Monthly",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "compressor_start",
        "reset_interval": "monthly",
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "Monatliche Cycling-Zähler für Kompressor-Starts, werden am 1. des Monats auf 0 gesetzt.",
    },
    "compressor_start_cycling_2h": {
        "name": "Compressor Start Cycling 2h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "compressor_start",
        "reset_interval": "2h",
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "2-Stunden Cycling-Zähler für Kompressor-Starts, werden alle 2 Stunden auf 0 gesetzt.",
    },
    "compressor_start_cycling_4h": {
        "name": "Compressor Start Cycling 4h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "compressor_start",
        "reset_interval": "4h",
        "state_source": "hp_state",  # WICHTIG: Verwendet HP_STATE statt HP_OPERATING_STATE
        "description": "4-Stunden Cycling-Zähler für Kompressor-Starts, werden alle 4 Stunden auf 0 gesetzt.",
    },
    "heating_curve_flow_line_temperature_calc": {
        "name": "Heating Curve Flow Line Temperature Calc",
        "unit": "°C",
        "precision": 1,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
        "format_params": HC_HEATING_CURVE_TEMPLATE_PARAMS,
        # HINWEIS: Dieses Template wird NICHT verwendet!
        # Stattdessen wird die Python-Implementierung LambdaHeatingCurveCalcSensor verwendet
        # (siehe template_sensor.py, Zeile 202-224).
        # Die Berechnung erfolgt über die _lerp() Funktion (template_sensor.py, Zeile 564-567),
        # die eine lineare Interpolation durchführt: y = y_a + (x - x_a) * (y_b - y_a) / (x_b - x_a)
        # Die _lerp() Funktion hat Schutz vor Division durch Null (wenn x_b == x_a, wird y_a zurückgegeben).
        # Das Template unten ist veraltet und wird nicht mehr verwendet.
        # "template": (
        #     "{{% set t_out = states('{ambient_sensor}') | float(10) %}}"
        #     "{{% set x_cold = {cold_point} %}}"
        #     "{{% set x_mid = {mid_point} %}}"
        #     "{{% set x_warm = {warm_point} %}}"
        #     "{{% set y_cold = states('number.{full_entity_prefix}_heating_curve_cold_outside_temp') | float({default_cold}) %}}"
        #     "{{% set y_mid = states('number.{full_entity_prefix}_heating_curve_mid_outside_temp') | float({default_mid}) %}}"
        #     "{{% set y_warm = states('number.{full_entity_prefix}_heating_curve_warm_outside_temp') | float({default_warm}) %}}"
        #     "{{% macro lin(x, xA, yA, xB, yB) -%}}"
        #     "{{{{ yA + (x - xA) * (yB - yA) / (xB - xA) }}}}"
        #     "{{%- endmacro %}}"
        #     "{{% if t_out >= x_warm %}}"
        #     "{{{{ y_warm | round(1) }}}}"
        #     "{{% elif t_out > x_mid %}}"
        #     "{{{{ lin(t_out, x_mid, y_mid, x_warm, y_warm) | float | round(1) }}}}"
        #     "{{% elif t_out > x_cold %}}"
        #     "{{{{ lin(t_out, x_cold, y_cold, x_mid, y_mid) | float | round(1) }}}}"
        #     "{{% else %}}"
        #     "{{{{ y_cold | round(1) }}}}"
        #     "{{% endif %}}"
        # ),
    },
    # 2h Cycling Sensoren (echte Entities - werden alle 2 Stunden auf 0 gesetzt)
    "heating_cycling_2h": {
        "name": "Heating Cycling 2h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "heating",
        "reset_interval": "2h",
        "description": "2-Stunden Cycling-Zähler für Heizen, werden alle 2 Stunden auf 0 gesetzt.",
    },
    "hot_water_cycling_2h": {
        "name": "Hot Water Cycling 2h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "hot_water",
        "reset_interval": "2h",
        "description": "2-Stunden Cycling-Zähler für Warmwasser, werden alle 2 Stunden auf 0 gesetzt.",
    },
    "cooling_cycling_2h": {
        "name": "Cooling Cycling 2h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "cooling",
        "reset_interval": "2h",
        "description": "2-Stunden Cycling-Zähler für Kühlen, werden alle 2 Stunden auf 0 gesetzt.",
    },
    "defrost_cycling_2h": {
        "name": "Defrost Cycling 2h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "defrost",
        "reset_interval": "2h",
        "description": "2-Stunden Cycling-Zähler für Abtauen, werden alle 2 Stunden auf 0 gesetzt.",
    },
    # 4h Cycling Sensoren (echte Entities - ktionalität mit den änderungen an den sensorenwerden alle 4 Stunden auf 0 gesetzt)
    "heating_cycling_4h": {
        "name": "Heating Cycling 4h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "heating",
        "reset_interval": "4h",
        "description": "4-Stunden Cycling-Zähler für Heizen, werden alle 4 Stunden auf 0 gesetzt.",
    },
    "hot_water_cycling_4h": {
        "name": "Hot Water Cycling 4h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "hot_water",
        "reset_interval": "4h",
        "description": "4-Stunden Cycling-Zähler für Warmwasser, werden alle 4 Stunden auf 0 gesetzt.",
    },
    "cooling_cycling_4h": {
        "name": "Cooling Cycling 4h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "cooling",
        "reset_interval": "4h",
        "description": "4-Stunden Cycling-Zähler für Kühlen, werden alle 4 Stunden auf 0 gesetzt.",
    },
    "defrost_cycling_4h": {
        "name": "Defrost Cycling 4h",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": None,
        "operating_state": "defrost",
        "reset_interval": "4h",
        "description": "4-Stunden Cycling-Zähler für Abtauen, werden alle 4 Stunden auf 0 gesetzt.",
    },
    # Weitere Modi können nach Bedarf ergänzt werden (siehe Statusmapping unten)
}

# =============================================================================
# ENERGY CONSUMPTION SENSOR TEMPLATES
# =============================================================================

