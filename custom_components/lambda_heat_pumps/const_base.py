from __future__ import annotations

"""Base constants for Lambda Heat Pumps integration."""

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

# Config Flow temperature limits (for NumberSelector min/max and default values)
HOT_WATER_MIN_TEMP_LIMIT = 25
HOT_WATER_MAX_TEMP_LIMIT = 65

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
    "V1.1.0-3K": 8,  # Latest firmware
    "V0.0.10-3K": 8,
    "V0.0.9-3K": 7,
    "V0.0.8-3K": 6,  # Previous firmware - most common in the field
    "V0.0.7-3K": 5,
    "V0.0.6-3K": 4,
    "V0.0.5-3K": 3,
    "V0.0.4-3K": 2,
    "V0.0.3-3K": 1,
}

# State Mappings
# are outsourced to const_mapping.py


# Default update interval for Modbus communication (in seconds)
# Lambda requires 1 minute timeout, so we use 30 seconds to stay well below
DEFAULT_UPDATE_INTERVAL = 30

# Default interval for writing room temperature and PV surplus (in seconds)
# Changed from 30 to 41 to avoid timing collisions with coordinator reads (30s)
DEFAULT_WRITE_INTERVAL = 9

# Default interval for fast modbus communication für state change detection (in seconds)
# 
DEFAULT_FAST_UPDATE_INTERVAL = 2

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
# Format for registers >= 1000: "{first_digit}n{remaining_digits}" (e.g., "5n07" matches 5007, 5107, 5207, etc.)
# Registers < 1000 are static addresses
INDIVIDUAL_READ_REGISTERS = [
    "1n20", "1n21",  # HP: compressor_power_consumption_accumulated (int32) - requires individual read for correct register order handling
    "1n22", "1n23",  # HP: compressor_thermal_energy_output_accumulated (int32) - requires individual read for correct register order handling
    "1n50", "1n51", "1n52", "1n53", "1n54", "1n55", "1n56", "1n57", "1n58", "1n59", "1n60",  # HP: other registers
    "5n07",  # HC: target_temp_flow_line (applies to all heating circuits: 5007, 5107, 5207, etc.)
]


# Zentrale Konfiguration für Energy-Sensoren nach Zeitzyklus (Basis-Attribut, Persist-Name, Entity-Suffix)
ENERGY_PERIOD_CONFIG = {
    "daily": {"baseline_attr": "_yesterday_value", "attr_name": "yesterday_value", "suffix": "_daily"},
    "hourly": {"baseline_attr": "_last_hour_value", "attr_name": "last_hour_value", "suffix": "_hourly"},
    "monthly": {"baseline_attr": "_previous_monthly_value", "attr_name": "previous_monthly_value", "suffix": "_monthly"},
    "yearly": {"baseline_attr": "_previous_yearly_value", "attr_name": "previous_yearly_value", "suffix": "_yearly"},
}

# Zeitzyklen-basierte Sensoren (Reset/Baseline-Konsistenz)
# Sensoren mit periodenbezogenem Wert (daily = total - yesterday, etc.):
# - Energy (electrical + thermal): daily, monthly, yearly – yesterday_value bzw. previous_monthly/yearly
#   dürfen nicht > energy_value sein (Konsistenz in sensor.py + coordinator _collect).
# - COP total: thermal_baseline, electrical_baseline dürfen nicht > aktueller Quellwert sein
#   (Konsistenz in LambdaCOPSensor.restore_state).
# - COP daily/monthly/yearly: lesen nur aus Energy-Sensoren, keine eigene Baseline → kein Reset-Fehler.
# - Cycling (daily, 2h, 4h, monthly, yearly): eigener Zähler pro Periode, Reset auf 0 – kein yesterday-Fehler.

# Reihenfolge der Perioden beim Inkrement der Energy-Sensoren (utils.increment_energy_consumption_counter)
ENERGY_INCREMENT_PERIODS = ["total", "daily", "monthly", "yearly", "2h", "4h", "hourly"]

# Reihenfolge bei der Registrierung der Energy-Sensoren (Total zuerst, damit Daily-Init den Total-Sensor findet)
ENERGY_REGISTRATION_ORDER = ("total", "yearly", "monthly", "daily", "hourly")

# Gültige Werte für reset_interval und für utils.create_reset_signal / get_reset_signal_for_period
RESET_VALID_PERIODS = ["daily", "2h", "4h"]
RESET_VALID_SENSOR_TYPES = ["cycling", "energy", "general"]

# COP-Sensoren: Modi und Perioden (ohne Defrost). Hourly nur für Heizen.
COP_MODES = ["heating", "hot_water", "cooling"]
COP_PERIODS = ["daily", "monthly", "yearly", "total", "hourly"]

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
# in den Sensor-Templates oder get_operating_state_from_template().
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
# These offsets are added to the calculated cycling counts once at HA start.
# Useful when replacing heat pumps or resetting counters.
# Positive values add to the total; negative values subtract.
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0               # Offset for HP1 heating total cycles
#    hot_water_cycling_total: 0             # Offset for HP1 hot water total cycles
#    cooling_cycling_total: 0               # Offset for HP1 cooling total cycles
#    defrost_cycling_total: 0               # Offset for HP1 defrost total cycles
#    compressor_start_cycling_total: 0      # Offset for HP1 compressor start total
#  hp2:
#    heating_cycling_total: 1500            # Example: HP2 already had 1500 heating cycles
#    hot_water_cycling_total: 800           # Example: HP2 already had 800 hot water cycles
#    cooling_cycling_total: 200             # Example: HP2 already had 200 cooling cycles
#    defrost_cycling_total: 50              # Example: HP2 already had 50 defrost cycles
#    compressor_start_cycling_total: 5000   # Example: HP2 already had 5000 compressor starts

# Energy consumption sensor configuration (Quellsensoren für den Energieverbrauch)
# Diese Sensoren müssen den Gesamtverbrauch in Wh oder kWh anzeigen
# Das System konvertiert automatisch zu kWh für die Berechnungen
# sensor_entity_id = elektrisch, thermal_sensor_entity_id = thermisch (optional)
# Beispiel:
#energy_consumption_sensors:
#  hp1:
#    sensor_entity_id: "sensor.lambda_wp_verbrauch"  # elektrischer Quellsensor
#    thermal_sensor_entity_id: "sensor.lambda_wp_waerme"  # optional, thermischer Quellsensor
#  hp2:
#    sensor_entity_id: "sensor.lambda_wp_verbrauch2"
#    thermal_sensor_entity_id: "sensor.lambda_wp_waerme2"  # optional

# Energy consumption offsets for total sensors (IMPORTANT: all values in kWh!)
# Applied only to TOTAL sensors, not to Daily/Monthly/Yearly.
# Useful when replacing heat pumps or resetting counters.
# Positive values add to the total; negative values subtract.
# Electrical offsets: {mode}_energy_total
# Thermal offsets:    {mode}_thermal_energy_total  (optional)
#energy_consumption_offsets:
#  hp1:
#    heating_energy_total: 0.0              # kWh offset for HP1 heating total (electrical)
#    hot_water_energy_total: 0.0            # kWh offset for HP1 hot water total (electrical)
#    cooling_energy_total: 0.0              # kWh offset for HP1 cooling total (electrical)
#    defrost_energy_total: 0.0              # kWh offset for HP1 defrost total (electrical)
#    heating_thermal_energy_total: 0.0      # kWh offset for HP1 heating total (thermal, optional)
#    hot_water_thermal_energy_total: 0.0    # kWh offset for HP1 hot water total (thermal, optional)
#    cooling_thermal_energy_total: 0.0      # kWh offset for HP1 cooling total (thermal, optional)
#    defrost_thermal_energy_total: 0.0      # kWh offset for HP1 defrost total (thermal, optional)
#  hp2:
#    heating_energy_total: 150.5            # Example: HP2 already consumed 150.5 kWh heating
#    hot_water_energy_total: 45.25          # Example: HP2 already consumed 45.25 kWh hot water
#    cooling_energy_total: 12.8             # Example: HP2 already consumed 12.8 kWh cooling
#    defrost_energy_total: 3.1              # Example: HP2 already consumed 3.1 kWh defrost
#    heating_thermal_energy_total: 620.0    # Example: HP2 already produced 620.0 kWh heating (thermal)
#    hot_water_thermal_energy_total: 180.5  # Example: HP2 already produced 180.5 kWh hot water (thermal)
#    cooling_thermal_energy_total: 45.2     # Example: HP2 already produced 45.2 kWh cooling (thermal)
#    defrost_thermal_energy_total: 12.1     # Example: HP2 already produced 12.1 kWh defrost (thermal)

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

