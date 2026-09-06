"""Constants for the Lambda Heat Pumps integration.

Sensor, climate and number metadata lives on the entity descriptions in each
platform module, not here.
"""

from __future__ import annotations

from typing import Any, Final

DOMAIN: Final = "lambda_heat_pumps"

# Bumped when an entry's data or options change shape. Version 9 moved the
# settings that used to live in lambda_wp_config.yaml into the entry.
ENTRY_VERSION: Final = 9

# Every firmware a controller can be running, newest first. `version` is the
# ordinal a sensor's `firmware_version` / `firmware_versions` is compared
# against, and `reg_order` is how that firmware lays out its 32-bit counters,
# which is what the register-order option defaults to.
FIRMWARE_CONFIG: Final[dict[str, dict[str, Any]]] = {
    "V1.1.0-3K": {"version": 9, "reg_order": "low_first"},
    "V0.0.10-3K": {"version": 8, "reg_order": "low_first"},
    "V0.0.9-3K": {"version": 7, "reg_order": "high_first"},
    "V0.0.8-3K": {"version": 6, "reg_order": "high_first"},
    "V0.0.7-3K": {"version": 5, "reg_order": "high_first"},
    "V0.0.6-3K": {"version": 4, "reg_order": "high_first"},
    "V0.0.5-3K": {"version": 3, "reg_order": "high_first"},
    "V0.0.4-3K": {"version": 2, "reg_order": "high_first"},
    "V0.0.3-3K": {"version": 1, "reg_order": "high_first"},
}

# Offered when setting up a controller.
FIRMWARE_VERSIONS: Final = list(FIRMWARE_CONFIG)

# Connection.
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SLAVE_ID: Final = "slave_id"
CONF_FIRMWARE_VERSION: Final = "firmware_version"
DEFAULT_PORT: Final = 502
DEFAULT_SLAVE_ID: Final = 1
DEFAULT_NAME: Final = "EU08L"
# modbus-connection only serializes concurrent reads/writes on a connection
# (via its internal Pacer lock) when a nonzero spacing is configured — with
# none, the poll loop and the write timer can hit the wire at the same time,
# which is exactly the transaction desync that Issue #105 reported. 50ms is
# imperceptible next to the multi-second poll/write intervals.
DEFAULT_MODBUS_MESSAGE_SPACING: Final = 0.05

# How the controller lays out the two registers of a 32-bit value. It varies by
# controller, so the user picks it; everything else about the wire format is
# fixed by the register model.
CONF_INT32_REGISTER_ORDER: Final = "int32_register_order"
REGISTER_ORDER_HIGH_FIRST: Final = "high_first"
REGISTER_ORDER_LOW_FIRST: Final = "low_first"
DEFAULT_INT32_REGISTER_ORDER: Final = REGISTER_ORDER_HIGH_FIRST

# Entity naming. Unique ids are `{name}_{module}{index}_{key}` in legacy mode and
# `{module}{index}_{key}` otherwise. The flag is fixed when the entry is created
# and exists only to keep existing installations' entities stable.
CONF_NAME_PREFIX: Final = "name"
CONF_USE_LEGACY_MODBUS_NAMES: Final = "use_legacy_modbus_names"

# Feature toggles.
CONF_ROOM_THERMOSTAT_CONTROL: Final = "room_thermostat_control"
CONF_PV_SURPLUS: Final = "pv_surplus"
CONF_COOLING_MODE: Final = "cooling_mode_enabled"
CONF_ROOM_TEMPERATURE_ENTITY: Final = "room_temperature_entity_{0}"
CONF_PV_POWER_SENSOR_ENTITY: Final = "pv_power_sensor_entity"
CONF_PV_SURPLUS_MODE: Final = "pv_surplus_mode"
DEFAULT_PV_SURPLUS_MODE: Final = "pos"
PV_SURPLUS_MODE_OPTIONS: Final = ["pos", "neg"]

# Polling. The full poll reads the whole controller. The fast poll reads only the
# two registers the cycle counters watch for an edge — a compressor start can
# begin and end well inside one 30 s window.
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_FAST_UPDATE_INTERVAL: Final = "fast_update_interval"
CONF_WRITE_INTERVAL: Final = "write_interval"
DEFAULT_UPDATE_INTERVAL: Final = 30
DEFAULT_FAST_UPDATE_INTERVAL: Final = 2
DEFAULT_WRITE_INTERVAL: Final = 9

# How often a heat pump's capacity limits are read. They change when an installer
# changes them, so an hour is soon enough — and they cost eleven single-register
# requests, close to half of what a poll of the whole controller costs.
CAPACITY_LIMIT_UPDATE_INTERVAL: Final = 3600

# Setpoint bounds, asked for in the options flow.
CONF_HEATING_CIRCUIT_MIN_TEMP: Final = "heating_circuit_min_temp"
CONF_HEATING_CIRCUIT_MAX_TEMP: Final = "heating_circuit_max_temp"
CONF_HEATING_CIRCUIT_TEMP_STEP: Final = "heating_circuit_temp_step"
DEFAULT_HEATING_CIRCUIT_MIN_TEMP: Final = 15.0
DEFAULT_HEATING_CIRCUIT_MAX_TEMP: Final = 35.0
DEFAULT_HEATING_CIRCUIT_TEMP_STEP: Final = 0.5

CONF_HOT_WATER_MIN_TEMP: Final = "hot_water_min_temp"
CONF_HOT_WATER_MAX_TEMP: Final = "hot_water_max_temp"
DEFAULT_HOT_WATER_MIN_TEMP: Final = 25.0
DEFAULT_HOT_WATER_MAX_TEMP: Final = 65.0

# The modules a controller can have, and the LambdaHeatPump attribute holding
# each one's list of components.
MODULES: Final = {
    "hp": "heat_pumps",
    "boil": "boilers",
    "buff": "buffers",
    "sol": "solar_modules",
    "hc": "heating_circuits",
}

# The operating modes that cycles and energy are attributed to, and the heat
# pump operating-state code that means each one. Code 4 (CIRCULATE) counts as
# standby, and anything unrecognised does too.
MODE_STBY: Final = "stby"
MODE_HEATING: Final = "heating"
MODE_HOT_WATER: Final = "hot_water"
MODE_COOLING: Final = "cooling"
MODE_DEFROST: Final = "defrost"
MODE_COMPRESSOR_START: Final = "compressor_start"

OPERATING_STATE_MODE: Final = {
    0: MODE_STBY,
    1: MODE_HEATING,
    2: MODE_HOT_WATER,
    3: MODE_COOLING,
    4: MODE_STBY,
    5: MODE_DEFROST,
}

# The modes a cycle is counted for. `compressor_start` is not an operating state
# — it is the compressor rating going from zero to non-zero.
CYCLE_MODES: Final = (
    MODE_HEATING,
    MODE_HOT_WATER,
    MODE_COOLING,
    MODE_DEFROST,
    MODE_COMPRESSOR_START,
)

# Modes energy is attributed to. Electrical covers standby, thermal does not —
# a heat pump produces no heat while idle.
ELECTRICAL_ENERGY_MODES: Final = (
    MODE_HEATING,
    MODE_HOT_WATER,
    MODE_COOLING,
    MODE_DEFROST,
    MODE_STBY,
)
THERMAL_ENERGY_MODES: Final = (
    MODE_HEATING,
    MODE_HOT_WATER,
    MODE_COOLING,
    MODE_DEFROST,
)

# How much of a counter's total came from a manual offset in the config file,
# kept on the entity so that changing the offset moves the total by the
# difference instead of adding it again.
ATTR_APPLIED_OFFSET: Final = "applied_offset"

# A single poll can never legitimately add more than this; a larger jump means
# the controller's counter was reset or replaced.
MAX_ENERGY_DELTA_KWH: Final = 100.0

# The periods a counter can be reported over. `total` never rolls over; the rest
# zero at their boundary, all of which fall on the start of an hour.
PERIOD_TOTAL: Final = "total"
PERIOD_HOURLY: Final = "hourly"
PERIOD_2H: Final = "2h"
PERIOD_4H: Final = "4h"
PERIOD_DAILY: Final = "daily"
PERIOD_MONTHLY: Final = "monthly"
PERIOD_YEARLY: Final = "yearly"

# Sent when a period rolls over, so its counters can zero themselves.
SIGNAL_PERIOD_ROLLOVER: Final = "lambda_heat_pumps_rollover_{entry_id}_{period}"

# The heating curve. The user gives the flow temperature they want at three
# outside temperatures, and the curve is read off by interpolating between them.
# Shared between the number entities that set them and the sensor that reads the
# curve. (outside temperature, setting key, default flow temperature).
CURVE_POINTS: Final = (
    (-22.0, "heating_curve_cold_outside_temp", 48.3),
    (0.0, "heating_curve_mid_outside_temp", 39.0),
    (22.0, "heating_curve_warm_outside_temp", 32.0),
)
CURVE_FLOW_MIN: Final = 15.0
CURVE_FLOW_MAX: Final = 75.0

# How far the flow drops in eco mode. Configured as a negative number, because
# it is added to the curve.
DEFAULT_ECO_TEMP_REDUCTION: Final = -1.0
ECO_TEMP_REDUCTION_MIN: Final = -10.0
ECO_TEMP_REDUCTION_MAX: Final = 0.0

# How hard the circuit chases the room setpoint when it follows a thermostat.
DEFAULT_ROOM_THERMOSTAT_OFFSET: Final = 0.0
DEFAULT_ROOM_THERMOSTAT_FACTOR: Final = 1.0

# What the controller's flow-line offset register can be set to.
FLOW_LINE_OFFSET_MIN: Final = -10.0
FLOW_LINE_OFFSET_MAX: Final = 10.0
