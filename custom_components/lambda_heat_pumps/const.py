from __future__ import annotations

# Retry-Parameter für automatische Modulerkennung
AUTO_DETECT_RETRIES = 3
AUTO_DETECT_RETRY_DELAY = 5  # Sekunden

# PV Surplus mode options
PV_SURPLUS_MODE_OPTIONS = {
    "entry": "E-Eintrag (nur positiv, UINT16)",
    "pos": "Pos. E-Überschuss (nur positiv, UINT16)",
    "neg": "Neg. E-Überschuss (positiv/negativ, INT16)",
}
DEFAULT_PV_SURPLUS_MODE = "pos"
"""Constants for Lambda WP integration."""

# Integration Constants
DOMAIN = "lambda_heat_pumps"
DEFAULT_NAME = "EU08L"
DEFAULT_HOST = "192.168.178.194"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_FIRMWARE = "V0.0.8-3K"  # Updated to match current hardware
DEFAULT_ROOM_THERMOSTAT_CONTROL = False
DEFAULT_PV_SURPLUS = False

# Default counts for devices
DEFAULT_NUM_HPS = 1
DEFAULT_NUM_BOIL = 1
DEFAULT_NUM_HC = 1
DEFAULT_NUM_BUFFER = 0
DEFAULT_NUM_SOLAR = 0

# Maximum counts for devices (from Modbus documentation)
MAX_NUM_HPS = 3  # Heat pumps
MAX_NUM_BOIL = 5  # Boilers
MAX_NUM_HC = 12  # Heating circuits
MAX_NUM_BUFFER = 5  # Buffers
MAX_NUM_SOLAR = 2  # Solar modules

# Default temperature settings
DEFAULT_HOT_WATER_MIN_TEMP = 40
DEFAULT_HOT_WATER_MAX_TEMP = 60

# Configuration Constants
CONF_SLAVE_ID = "slave_id"
CONF_ROOM_TEMPERATURE_ENTITY = "room_temperature_entity_{0}"
CONF_PV_POWER_SENSOR_ENTITY = "pv_power_sensor_entity"
CONF_FIRMWARE_VERSION = "firmware_version"
CONF_HOST = "host"
CONF_NAME = "name"
CONF_PORT = "port"
# Format string for room_temperature_entity_1, _2, etc.
# Format string for pv_power_sensor_entity_1, _2, etc.

# Debug and Logging
DEBUG = False
DEBUG_PREFIX = "lambda_wp"
LOG_LEVELS = {"error": "ERROR", "warning": "WARNING", "info": "INFO", "debug": "DEBUG"}

# Firmware Versions
FIRMWARE_VERSION = {
    "V0.0.9-3K": 7,  # Latest firmware
    "V0.0.8-3K": 6,  # Previous firmware - most common in the field
    "V0.0.7-3K": 5,
    "V0.0.6-3K": 4,
    "V0.0.5-3K": 3,
    "V0.0.4-3K": 2,
    "V0.0.3-3K": 1,
}

# State Mappings
# are outsourced to const_mapping.py

# Sensor Templates

# Heat Pump Sensors
HP_SENSOR_TEMPLATES = {
    "error_state": {
        "relative_address": 0,
        "name": "Error State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "txt_mapping": True,
        "options": {"register": True},
    },
    "error_number": {
        "relative_address": 1,
        "name": "Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "state": {
        "relative_address": 2,
        "name": "State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "txt_mapping": True,
        "options": {"register": True},
    },
    "operating_state": {
        "relative_address": 3,
        "name": "Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "txt_mapping": True,
        "options": {"register": True},
    },
    "flow_line_temperature": {
        "relative_address": 4,
        "name": "Flow Line Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "return_line_temperature": {
        "relative_address": 5,
        "name": "Return Line Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "volume_flow_heat_sink": {
        "relative_address": 6,
        "name": "Volume Flow Heat Sink",
        "unit": "l/min",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "energy_source_inlet_temperature": {
        "relative_address": 7,
        "name": "Energy Source Inlet Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "energy_source_outlet_temperature": {
        "relative_address": 8,
        "name": "Energy Source Outlet Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "volume_flow_energy_source": {
        "relative_address": 9,
        "name": "Volume Flow Energy Source",
        "unit": "l/min",
        "scale": 0.01,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "compressor_unit_rating": {
        "relative_address": 10,
        "name": "Compressor Unit Rating",
        "unit": "%",
        "scale": 0.01,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "actual_heating_capacity": {
        "relative_address": 11,
        "name": "Actual Heating Capacity",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "inverter_power_consumption": {
        "relative_address": 12,
        "name": "Inverter Power Consumption",
        "unit": "W",
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "cop": {
        "relative_address": 13,
        "name": "COP",
        "unit": None,
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total",
    },
    "request_type": {
        "relative_address": 15,
        "name": "Request-Type",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "total",
    },
    "requested_flow_line_temperature": {
        "relative_address": 16,
        "name": "Requested Flow Line Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
    },
    "requested_return_line_temperature": {
        "relative_address": 17,
        "name": "Requested Return Line Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
    },
    "requested_flow_to_return_line_temperature_difference": {
        "relative_address": 18,
        "name": "Requested Flow to Return Line Temperature Difference",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
    },
    "relais_state_2nd_heating_stage": {
        "relative_address": 19,
        "name": "Relais State 2nd Heating Stage",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "txt_mapping": True,
    },
    "compressor_power_consumption_accumulated": {
        "relative_address": 20,
        "name": "Compressor Power Consumption Accumulated",
        "unit": "Wh",
        "scale": 1,
        "precision": 0,
        "data_type": "int32",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total_increasing",
    },
    "compressor_thermal_energy_output_accumulated": {
        "relative_address": 22,
        "name": "Compressor Thermal Energy Output Accumulated",
        "unit": "Wh",
        "scale": 1,
        "precision": 0,
        "data_type": "int32",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "total_increasing",
    },
    # Undocumented registers discovered on hardware - Always enabled
    "config_parameter_24": {
        "relative_address": 24,
        "name": "Unknown Parameter (R1024)",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "vda_rating": {
        "relative_address": 25,
        "name": "VdA Rating",
        "unit": "%",
        "scale": 0.01,
        "precision": 2,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "hot_gas_temperature": {
        "relative_address": 26,
        "name": "Hot Gas Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
    },
    "subcooling_temperature": {
        "relative_address": 27,
        "name": "Subcooling Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
    },
    "suction_gas_temperature": {
        "relative_address": 28,
        "name": "Suction Gas Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
    },
    "condensation_temperature": {
        "relative_address": 29,
        "name": "Condensation Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
    },
    "evaporation_temperature": {
        "relative_address": 30,
        "name": "Evaporation Temperature",
        "unit": "°C",
        "scale": 0.01,
        "precision": 2,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
        "device_class": "temperature",
    },
    "eqm_rating": {
        "relative_address": 31,
        "name": "EqM Rating",
        "unit": "%",
        "scale": 0.01,
        "precision": 2,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "expansion_valve_opening_angle": {
        "relative_address": 32,
        "name": "Expansion Valve Opening Angle",
        "unit": "%",
        "scale": 0.01,
        "precision": 2,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
     "config_parameter_33": {
        "relative_address": 33,
        "name": "Unknown Parameter (R1033)",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },   
    "config_parameter_50": {
        "relative_address": 50,
        "name": "Unknown Parameter (R1050)",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
    "dhw_output_power_15c": {
        "relative_address": 51,
        "name": "DHW Output Power at 15°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_min_output_power_15c": {
        "relative_address": 52,
        "name": "Heating Min Output Power at 15°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_max_output_power_15c": {
        "relative_address": 53,
        "name": "Heating Max Output Power at 15°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_min_output_power_0c": {
        "relative_address": 54,
        "name": "Heating Min Output Power at 0°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_max_output_power_0c": {
        "relative_address": 55,
        "name": "Heating Max Output Power at 0°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_min_output_power_minus15c": {
        "relative_address": 56,
        "name": "Heating Min Output Power at -15°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "heating_max_output_power_minus15c": {
        "relative_address": 57,
        "name": "Heating Max Output Power at -15°C",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "cooling_min_output_power": {
        "relative_address": 58,
        "name": "Cooling Min Output Power",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "cooling_max_output_power": {
        "relative_address": 59,
        "name": "Cooling Max Output Power",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": True,
        "state_class": "measurement",
        "device_class": "power",
    },
    "config_parameter_60": {
        "relative_address": 60,
        "name": "Unknown Parameter (R1060)",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "Hp",
        "writeable": False,
        "state_class": "measurement",
    },
}

# Boiler Sensors
BOIL_SENSOR_TEMPLATES = {
    "error_number": {
        "relative_address": 0,
        "name": "Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "state_class": "total",
    },
    "operating_state": {
        "relative_address": 1,
        "name": "Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "txt_mapping": True,
        "options": {"register": True},
    },
    "actual_high_temperature": {
        "relative_address": 2,
        "name": "Actual High Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "state_class": "measurement",
    },
    "actual_low_temperature": {
        "relative_address": 3,
        "name": "Actual Low Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "state_class": "measurement",
    },
    "target_high_temperature": {
        "relative_address": 50,
        "name": "Target High Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": True,
        "state_class": "measurement",
    },
    "actual_circulation_temperature": {
        "relative_address": 4,
        "name": "Actual Circulation Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "state_class": "measurement",
    },
    "actual_circulation_pump_state": {
        "relative_address": 5,
        "name": "Circulation Pump State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": False,
        "txt_mapping": True,
    },
    "maximum_boiler_temperature": {
        "relative_address": 50,
        "name": "Maximum Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": True,
        "state_class": "measurement",
    },
    
}

# Buffer Sensors
BUFF_SENSOR_TEMPLATES = {
    "error_number": {
        "relative_address": 0,
        "name": "Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "operating_state": {
        "relative_address": 1,
        "name": "Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
        "txt_mapping": True,
    },
    "actual_high_temperature": {
        "relative_address": 2,
        "name": "Actual High Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "actual_low_temperature": {
        "relative_address": 3,
        "name": "Actual Low Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "buffer_temperature_high_setpoint": {
        "relative_address": 4,
        "name": "Buffer High Temperature Setpoint",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": True,
    },
    "request_type": {
        "relative_address": 5,
        "name": "Request Type",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
        "txt_mapping": True,
    },
    "request_flow_line_temp_setpoint": {
        "relative_address": 6,
        "name": "Flow Line Temperature Setpoint",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "request_return_line_temp_setpoint": {
        "relative_address": 7,
        "name": "Return Line Temperature Setpoint",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "request_heat_sink_temp_diff_setpoint": {
        "relative_address": 8,
        "name": "Heat Sink Temperature Difference Setpoint",
        "unit": "K",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "modbus_request_heating_capacity": {
        "relative_address": 9,
        "name": "Requested Heating Capacity",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": False,
    },
    "maximum_buffer_temp": {
        "relative_address": 50,
        "name": "Maximum Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "buff",
        "writeable": True,
    },
}

# Solar Sensors
SOL_SENSOR_TEMPLATES = {
    "error_number": {
        "relative_address": 0,
        "name": "Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
    },
    "operating_state": {
        "relative_address": 1,
        "name": "Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
        "txt_mapping": True,
    },
    "collector_temperature": {
        "relative_address": 2,
        "name": "Collector Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
    },
    "storage_temperature": {
        "relative_address": 3,
        "name": "Storage Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
    },
    "power_current": {
        "relative_address": 4,
        "name": "Power Current",
        "unit": "kW",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
    },
    "energy_total": {
        "relative_address": 5,
        "name": "Energy Total",
        "unit": "kWh",
        "scale": 1,
        "precision": 0,
        "data_type": "int32",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": False,
    },
    "maximum_buffer_temperature": {
        "relative_address": 50,
        "name": "Maximum Buffer Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": True,
    },
    "buffer_changeover_temperature": {
        "relative_address": 51,
        "name": "Buffer Changeover Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "sol",
        "writeable": True,
    },
}

# Heating Circuit Sensors
HC_SENSOR_TEMPLATES = {
    "error_number": {
        "relative_address": 0,
        "name": "Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": False,
        "state_class": "total",
    },
    "operating_state": {
        "relative_address": 1,
        "name": "Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": False,
        "txt_mapping": True,
    },
    "flow_line_temperature": {
        "relative_address": 2,
        "name": "Flow Line Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": False,
        "state_class": "measurement",
    },
    "return_line_temperature": {
        "relative_address": 3,
        "name": "Return Line Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": False,
        "state_class": "measurement",
    },
    "room_device_temperature": {
        "relative_address": 4,
        "name": "Room Device Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "state_class": "measurement",
    },
    "set_flow_line_temperature": {
        "relative_address": 5,
        "name": "Set Flow Line Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "state_class": "measurement",
    },
    "operating_mode": {
        "relative_address": 6,
        "name": "Operating Mode",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "txt_mapping": True,
    },
    "set_flow_line_offset_temperature": {
        "relative_address": 50,
        "name": "Set Flow Line Offset Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "state_class": "measurement",
    },
    "target_room_temperature": {
        "relative_address": 51,
        "name": "Target Room Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "state_class": "measurement",
    },
    "set_cooling_mode_room_temperature": {
        "relative_address": 52,
        "name": "Set Cooling Mode Room Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "state_class": "measurement",
    },
     "target_temp_flow_line": {
         "relative_address": 7,
         "name": "Target Flow Line Temperature",
         "unit": "°C",
         "scale": 0.1,
         "precision": 1,
         "data_type": "int16",
         "firmware_version": 3,
         "device_type": "hc",
         "writeable": False,
         "state_class": "measurement",
     },
}

# General Sensors
SENSOR_TYPES = {
    # General Ambient
    "ambient_error_number": {
        "address": 0,
        "name": "Ambient Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "total",
        "options": {"register": True},
    },
    "ambient_operating_state": {
        "address": 1,
        "name": "Ambient Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "txt_mapping": True,
        "options": {"register": True},
    },
    "ambient_temperature": {
        "address": 2,
        "name": "Ambient Temperature",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },
    "ambient_temperature_1h": {
        "address": 3,
        "name": "Ambient Temperature 1h",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },
    "ambient_temperature_calculated": {
        "address": 4,
        "name": "Ambient Temperature Calculated",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },
    "emgr_error_number": {
        "address": 100,
        "name": "E-Manager Error Number",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "total",
    },
    "emgr_operating_state": {
        "address": 101,
        "name": "E-Manager Operating State",
        "unit": None,
        "scale": 1,
        "precision": 0,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "txt_mapping": True,
    },
    "emgr_actual_power": {
        "address": 102,
        "name": "E-Manager Actual Power",
        "unit": "W",
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },
    "emgr_actual_power_consumption": {
        "address": 103,
        "name": "E-Manager Power Consumption",
        "unit": "W",
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },
    "emgr_power_consumption_setpoint": {
        "address": 104,
        "name": "E-Manager Power Consumption Setpoint",
        "unit": "W",
        "scale": 1,
        "precision": 0,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "main",
        "writeable": False,
        "state_class": "measurement",
    },

}

# Climate Sensors
CLIMATE_TEMPLATES = {
    "hot_water": {
        "relative_address": 2,
        "relative_set_address": 50,
        "name": "Hot Water",
        "unit": "°C",
        "scale": 0.1,
        "precision": 0.5,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "boil",
        "writeable": True,
        "hvac_mode": {"heat"},
        "state_class": "measurement",
    },
    "heating_circuit": {
        "relative_address": 4,  # room_device_temperature
        "relative_set_address": 51,  # target_room_temperature
        "name": "Heating Circuit",
        "unit": "°C",
        "scale": 0.1,
        "precision": 0.1,
        "data_type": "uint16",
        "firmware_version": 1,
        "device_type": "hc",
        "writeable": True,
        "hvac_mode": {"heat"},
        "state_class": "measurement",
    },
}

# Default update interval for Modbus communication (in seconds)
# Lambda requires 1 minute timeout, so we use 30 seconds to stay well below
DEFAULT_UPDATE_INTERVAL = 30

# Default interval for writing room temperature and PV surplus (in seconds)
# Changed from 30 to 41 to avoid timing collisions with coordinator reads (30s)
DEFAULT_WRITE_INTERVAL = 41

# Lambda-specific Modbus configuration
LAMBDA_MODBUS_TIMEOUT = 60  # Lambda requires 1 minute timeout
LAMBDA_MODBUS_UNIT_ID = 1   # Lambda Unit ID
LAMBDA_MODBUS_PORT = 502    # Standard Modbus TCP port
LAMBDA_MAX_RETRIES = 3      # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5      # Delay between retries in seconds

DEFAULT_HEATING_CIRCUIT_MIN_TEMP = 15
DEFAULT_HEATING_CIRCUIT_MAX_TEMP = 35
DEFAULT_HEATING_CIRCUIT_TEMP_STEP = 0.5

# Base addresses for all device types
BASE_ADDRESSES = {
    "hp": 1000,  # Heat pumps start at 1000
    "boil": 2000,  # Boilers start at 2000
    "buff": 3000,  # Buffers start at 3000
    "sol": 4000,  # Solar starts at 4000
    "hc": 5000,  # Heating circuits start at 5000
}

# Individual Read Registers
# These registers are read individually instead of in batches due to known issues
INDIVIDUAL_READ_REGISTERS = [
    1020, 1021,  # compressor_power_consumption_accumulated (int32) - requires individual read for correct register order handling
    1022, 1023,  # compressor_thermal_energy_output_accumulated (int32) - requires individual read for correct register order handling
    1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 5007
]


# Calculated Sensor Templates
CALCULATED_SENSOR_TEMPLATES = {
    # Beispiel für einen berechneten Sensor: COP
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
        "reset_signal": None,
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
        "reset_signal": None,
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
        "reset_signal": None,
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
        "reset_signal": None,
        "description": "Zählt, wie oft in den Modus Abtauen (DEFROST) gewechselt wurde.",
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
        "reset_signal": None,
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
        "reset_signal": None,
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
        "reset_signal": None,
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
        "reset_signal": None,
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

# Energy Consumption Sensor Templates
ENERGY_CONSUMPTION_SENSOR_TEMPLATES = {
    # Heating Energy Sensoren
    "heating_energy_total": {
        "name": "Heating Energy Total",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": "energy",
        "mode_value": 1,  # CH
        "operating_state": "heating",
        "period": "total",
        "reset_interval": None,
        "reset_signal": None,
        "description": "Gesamtverbrauch für Heizen in kWh",
    },
    "heating_energy_daily": {
        "name": "Heating Energy Daily",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "heating",
        "reset_interval": "daily",
        "description": "Täglicher Verbrauch für Heizen in kWh",
    },
    # Hot Water Energy Sensoren
    "hot_water_energy_total": {
        "name": "Hot Water Energy Total",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": "energy",
        "mode_value": 2,  # DHW
        "operating_state": "hot_water",
        "period": "total",
        "reset_interval": None,
        "reset_signal": None,
        "description": "Gesamtverbrauch für Warmwasser in kWh",
    },
    "hot_water_energy_daily": {
        "name": "Hot Water Energy Daily",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "hot_water",
        "reset_interval": "daily",
        "description": "Täglicher Verbrauch für Warmwasser in kWh",
    },
    # Cooling Energy Sensoren
    "cooling_energy_total": {
        "name": "Cooling Energy Total",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": "energy",
        "mode_value": 3,  # CC
        "operating_state": "cooling",
        "period": "total",
        "reset_interval": None,
        "reset_signal": None,
        "description": "Gesamtverbrauch für Kühlen in kWh",
    },
    "cooling_energy_daily": {
        "name": "Cooling Energy Daily",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "cooling",
        "reset_interval": "daily",
        "description": "Täglicher Verbrauch für Kühlen in kWh",
    },
    # Defrost Energy Sensoren
    "defrost_energy_total": {
        "name": "Defrost Energy Total",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": "energy",
        "mode_value": 5,  # DEFROST
        "operating_state": "defrost",
        "period": "total",
        "reset_interval": None,
        "reset_signal": None,
        "description": "Gesamtverbrauch für Abtauen in kWh",
    },
    "defrost_energy_daily": {
        "name": "Defrost Energy Daily",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "defrost",
        "reset_interval": "daily",
        "description": "Täglicher Verbrauch für Abtauen in kWh",
    },
    # STBY Energy Sensoren
    "stby_energy_total": {
        "name": "STBY Energy Total",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total_increasing",
        "device_class": "energy",
        "operating_state": "stby",
        "period": "total",
        "reset_interval": None,
        "reset_signal": None,
        "description": "Gesamtverbrauch für Standby in kWh",
    },
    "stby_energy_daily": {
        "name": "STBY Energy Daily",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "stby",
        "reset_interval": "daily",
        "description": "Täglicher Verbrauch für Standby in kWh",
    },
    # Monthly Energy Sensoren
    "heating_energy_monthly": {
        "name": "Heating Energy Monthly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "heating",
        "reset_interval": "monthly",
        "description": "Monatlicher Verbrauch für Heizen in kWh",
    },
    "hot_water_energy_monthly": {
        "name": "Hot Water Energy Monthly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "hot_water",
        "reset_interval": "monthly",
        "description": "Monatlicher Verbrauch für Warmwasser in kWh",
    },
    "cooling_energy_monthly": {
        "name": "Cooling Energy Monthly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "cooling",
        "reset_interval": "monthly",
        "description": "Monatlicher Verbrauch für Kühlen in kWh",
    },
    "defrost_energy_monthly": {
        "name": "Defrost Energy Monthly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "defrost",
        "reset_interval": "monthly",
        "description": "Monatlicher Verbrauch für Abtauen in kWh",
    },
    "stby_energy_monthly": {
        "name": "STBY Energy Monthly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "stby",
        "reset_interval": "monthly",
        "description": "Monatlicher Verbrauch für Standby in kWh",
    },
    # Yearly Energy Sensoren
    "heating_energy_yearly": {
        "name": "Heating Energy Yearly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "heating",
        "reset_interval": "yearly",
        "description": "Jährlicher Verbrauch für Heizen in kWh",
    },
    "hot_water_energy_yearly": {
        "name": "Hot Water Energy Yearly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "hot_water",
        "reset_interval": "yearly",
        "description": "Jährlicher Verbrauch für Warmwasser in kWh",
    },
    "cooling_energy_yearly": {
        "name": "Cooling Energy Yearly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "cooling",
        "reset_interval": "yearly",
        "description": "Jährlicher Verbrauch für Kühlen in kWh",
    },
    "defrost_energy_yearly": {
        "name": "Defrost Energy Yearly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "defrost",
        "reset_interval": "yearly",
        "description": "Jährlicher Verbrauch für Abtauen in kWh",
    },
    "stby_energy_yearly": {
        "name": "STBY Energy Yearly",
        "unit": "kWh",
        "precision": 6,
        "data_type": "calculated",
        "firmware_version": 1,
        "device_type": "hp",
        "writeable": False,
        "state_class": "total",
        "device_class": "energy",
        "operating_state": "stby",
        "reset_interval": "yearly",
        "description": "Jährlicher Verbrauch für Standby in kWh",
    },
}

# Legacy-Konstanten für Rückwärtskompatibilität - Direkt aus Templates berechnet
ENERGY_CONSUMPTION_MODES = sorted(list(set(
    template["operating_state"] 
    for template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.values()
    if "operating_state" in template
)))

ENERGY_CONSUMPTION_PERIODS = sorted(list(set(
    template["period"] if "period" in template 
    else template["reset_interval"] 
    for template in ENERGY_CONSUMPTION_SENSOR_TEMPLATES.values()
    if "period" in template or (template.get("reset_interval") is not None)
) | {"monthly", "yearly"}))

# Energy Consumption Migration Version
ENERGY_CONSUMPTION_MIGRATION_VERSION = 4

# Energy Consumption Default Offsets
DEFAULT_ENERGY_CONSUMPTION_OFFSETS = {
    "hp1": {
        "heating_energy_total": 0,
        "hot_water_energy_total": 0,
        "cooling_energy_total": 0,
        "defrost_energy_total": 0,
        "stby_energy_total": 0,
    }
}

# Statusmapping für operating_state - DEPRECATED
# Diese Map ist deprecated. Verwende stattdessen die operating_state Attribute
# in den Sensor-Templates oder die Funktionen get_operating_state_from_template()
# und get_reset_signal_from_template().
#
# Für Rückwärtskompatibilität bleibt diese Map bestehen, sollte aber nicht
# mehr direkt verwendet werden.
OPERATING_STATE_MAP = {
    0: "STBY",
    1: "CH",
    2: "DHW", 
    3: "CC",
    4: "CIRCULATE",
    5: "DEFROST",
    6: "OFF",
    7: "FROST",
    8: "STBY-FROST",
    9: "Not used",
    10: "SUMMER",
    11: "HOLIDAY",
    12: "ERROR",
    13: "WARNING",
    14: "INFO-MESSAGE",
    15: "TIME-BLOCK",
    16: "RELEASE-BLOCK",
    17: "MINTEMP-BLOCK",
    18: "FIRMWARE-DOWNLOAD",
}

# Lambda WP Configuration Template
LAMBDA_WP_CONFIG_TEMPLATE = """# Lambda WP configuration
# This file is used by Lambda WP Integration to define the configuration of
# Lambda WP.
# The file is created during the installation of the Lambda WP Integration and
# can then be edited with the file editor or visual studio code.

# Modbus registrations that are not required can be deactivated here.
# Disabled registrations as an example:
#disabled_registers:
# - 2004 # boil1_actual_circulation_temp

# Override sensor names (only works if use_legacy_modbus_names is true)
# sensors_names_override does only functions if use_legacy_modbus_names is
# set to true!!!
#sensors_names_override:
#- id: name_of_the_sensor_to_override_example
#  override_name: new_name_of_the_sensor_example

# Cycling counter offsets for total sensors
# These offsets are added to the calculated cycling counts
# Useful when replacing heat pumps or resetting counters
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0      # Offset for HP1 heating total cycles
#    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
#    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
#    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles
#  hp2:
#    heating_cycling_total: 1500   # Example: HP2 already had 1500 heating cycles
#    hot_water_cycling_total: 800  # Example: HP2 already had 800 hot water cycles
#    cooling_cycling_total: 200    # Example: HP2 already had 200 cooling cycles
#    defrost_cycling_total: 50     # Example: HP2 already had 50 defrost cycles

# Energy consumption sensor configuration (Quellsensoren für den Energieverbrauch)
# Diese Sensoren müssen den Gesamtverbrauch in Wh oder kWh anzeigen
# Das System konvertiert automatisch zu kWh für die Berechnungen
# Beispiel:
#energy_consumption_sensors:
#  hp1:
#    sensor_entity_id: "sensor.lambda_wp_verbrauch"  # Beispiel: Externer Verbrauchssensor
#  hp2:
#    sensor_entity_id: "sensor.lambda_wp_verbrauch2" # Beispiel: Zweiter Verbrauchssensor

# Energy consumption offsets for total sensors (WICHTIG: Alle Werte müssen in kWh angegeben werden!)
# Diese Offsets werden nur auf die TOTAL-Sensoren angewendet, nicht auf Daily/Monthly/Yearly
# Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen der Zähler
# Beispiel mit Nachkommastellen:
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0       # kWh offset for HP1 heating total
#    hot_water_energy_total: 0.0     # kWh offset for HP1 hot water total
#    cooling_energy_total: 0.0       # kWh offset for HP1 cooling total
#    defrost_energy_total: 0.0       # kWh offset for HP1 defrost total
#  hp2:
#    heating_energy_total: 150.5     # Beispiel: HP2 bereits 150,5 kWh Heizen verbraucht
#    hot_water_energy_total: 45.25   # Beispiel: HP2 bereits 45,25 kWh Warmwasser verbraucht
#    cooling_energy_total: 12.8      # Beispiel: HP2 bereits 12,8 kWh Kühlen verbraucht
#    defrost_energy_total: 3.1       # Beispiel: HP2 bereits 3,1 kWh Abtauen verbraucht

# Modbus configuration
# Register order for 32-bit registers (int32 sensors)
# This refers to the order of 16-bit registers when combining to 32-bit values (Register/Word Order),
# NOT byte endianness within a register. Modbus uses Big-Endian for bytes within a register,
# but the order of multiple registers varies by device manufacturer.
# "high_first" = High-order register first (Register[0] contains MSW) - default
# "low_first" = Low-order register first (Register[0] contains LSW)
# Example:
#modbus:
#  int32_register_order: "high_first"  # or "low_first"
"""

