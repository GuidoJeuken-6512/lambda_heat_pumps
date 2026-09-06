"""The controller's state codes.

Each member carries both the raw code the controller reports and the label it is
known by, because the labels are not Python identifiers ("START COMPRESSOR",
"RESTART-BLOCK", "Not Used"). Members are `int`s, so a state still compares
equal to its code:

    heat_pump.operating_state == 1              # True when heating
    heat_pump.operating_state.label             # "CH"
"""

from __future__ import annotations

from enum import IntEnum


class LambdaState(IntEnum):
    """A state code with the label the controller documents it under."""

    label: str

    def __new__(cls, code: int, label: str) -> LambdaState:
        member = int.__new__(cls, code)
        member._value_ = code
        member.label = label
        return member


class HeatPumpErrorState(LambdaState):
    NONE = 0, "NONE"
    MESSAGE = 1, "MESSAGE"
    WARNING = 2, "WARNING"
    ALARM = 3, "ALARM"
    FAULT = 4, "FAULT"


class HeatPumpState(LambdaState):
    INIT = 0, "INIT"
    REFERENCE = 1, "REFERENCE"
    RESTART_BLOCK = 2, "RESTART-BLOCK"
    READY = 3, "READY"
    START_PUMPS = 4, "START PUMPS"
    START_COMPRESSOR = 5, "START COMPRESSOR"
    PRE_REGULATION = 6, "PRE-REGULATION"
    REGULATION = 7, "REGULATION"
    NOT_USED = 8, "Not Used"
    COOLING = 9, "COOLING"
    DEFROSTING = 10, "DEFROSTING"
    STOPPING = 20, "STOPPING"
    FAULT_LOCK = 30, "FAULT-LOCK"
    ALARM_BLOCK = 31, "ALARM-BLOCK"
    ERROR_RESET = 40, "ERROR-RESET"


class HeatPumpOperatingState(LambdaState):
    STBY = 0, "STBY"
    CH = 1, "CH"
    DHW = 2, "DHW"
    CC = 3, "CC"
    CIRCULATE = 4, "CIRCULATE"
    DEFROST = 5, "DEFROST"
    OFF = 6, "OFF"
    FROST = 7, "FROST"
    STBY_FROST = 8, "STBY-FROST"
    NOT_USED = 9, "Not used"
    SUMMER = 10, "SUMMER"
    HOLIDAY = 11, "HOLIDAY"
    ERROR = 12, "ERROR"
    WARNING = 13, "WARNING"
    INFO_MESSAGE = 14, "INFO-MESSAGE"
    TIME_BLOCK = 15, "TIME-BLOCK"
    RELEASE_BLOCK = 16, "RELEASE-BLOCK"
    MINTEMP_BLOCK = 17, "MINTEMP-BLOCK"
    FIRMWARE_DOWNLOAD = 18, "FIRMWARE-DOWNLOAD"


class HeatPumpRequestType(LambdaState):
    NO_REQUEST = 0, "NO REQUEST"
    FLOW_PUMP_CIRCULATION = 1, "FLOW PUMP CIRCULATION"
    CENTRAL_HEATING = 2, "CENTRAL HEATING"
    CENTRAL_COOLING = 3, "CENTRAL COOLING"
    DOMESTIC_HOT_WATER = 4, "DOMESTIC HOT WATER"


class RelaisState(LambdaState):
    OFF = 0, "Off"
    ON = 1, "On"


class BoilerOperatingState(LambdaState):
    STBY = 0, "STBY"
    DHW = 1, "DHW"
    LEGIO = 2, "LEGIO"
    SUMMER = 3, "SUMMER"
    FROST = 4, "FROST"
    HOLIDAY = 5, "HOLIDAY"
    PRIO_STOP = 6, "PRIO-STOP"
    ERROR = 7, "ERROR"
    OFF = 8, "OFF"
    PROMPT_DHW = 9, "PROMPT-DHW"
    TRAILING_STOP = 10, "TRAILING-STOP"
    TEMP_LOCK = 11, "TEMP-LOCK"
    STBY_FROST = 12, "STBY-FROST"


class BufferOperatingState(LambdaState):
    STBY = 0, "STBY"
    HEATING = 1, "HEATING"
    COOLING = 2, "COOLING"
    SUMMER = 3, "SUMMER"
    FROST = 4, "FROST"
    HOLIDAY = 5, "HOLIDAY"
    PRIO_STOP = 6, "PRIO-STOP"
    ERROR = 7, "ERROR"
    OFF = 8, "OFF"
    STBY_FROST = 9, "STBY-FROST"


class BufferRequestType(LambdaState):
    INVALID_REQUEST = -1, "INVALID REQUEST"
    NO_REQUEST = 0, "NO REQUEST"
    FLOW_PUMP_CIRCULATION = 1, "FLOW PUMP CIRCULATION"
    CENTRAL_HEATING = 2, "CENTRAL HEATING"
    CENTRAL_COOLING = 3, "CENTRAL COOLING"


class SolarOperatingState(LambdaState):
    STBY = 0, "STBY"
    HEATING = 1, "HEATING"
    ERROR = 2, "ERROR"
    OFF = 3, "OFF"


class HeatingCircuitOperatingState(LambdaState):
    HEATING = 0, "HEATING"
    ECO = 1, "ECO"
    COOLING = 2, "COOLING"
    FLOORDRY = 3, "FLOORDRY"
    FROST = 4, "FROST"
    MAX_TEMP = 5, "MAX-TEMP"
    ERROR = 6, "ERROR"
    SERVICE = 7, "SERVICE"
    HOLIDAY = 8, "HOLIDAY"
    CH_SUMMER = 9, "CH-SUMMER"
    CC_WINTER = 10, "CC-WINTER"
    PRIO_STOP = 11, "PRIO-STOP"
    OFF = 12, "OFF"
    RELEASE_OFF = 13, "RELEASE-OFF"
    TIME_OFF = 14, "TIME-OFF"
    STBY = 15, "STBY"
    STBY_HEATING = 16, "STBY-HEATING"
    STBY_ECO = 17, "STBY-ECO"
    STBY_COOLING = 18, "STBY-COOLING"
    STBY_FROST = 19, "STBY-FROST"
    STBY_FLOORDRY = 20, "STBY-FLOORDRY"


class HeatingCircuitOperatingMode(LambdaState):
    UNKNOWN = -1, "Unknown"
    OFF = 0, "OFF"
    MANUAL = 1, "MANUAL"
    AUTOMATIK = 2, "AUTOMATIK"
    AUTO_HEATING = 3, "AUTO-HEATING"
    AUTO_COOLING = 4, "AUTO-COOLING"
    FROST = 5, "FROST"
    SUMMER = 6, "SUMMER"
    FLOOR_DRY = 7, "FLOOR-DRY"


class AmbientOperatingState(LambdaState):
    OFF = 0, "OFF"
    AUTOMATIK = 1, "AUTOMATIK"
    MANUAL = 2, "MANUAL"
    ERROR = 3, "ERROR"


class EManagerOperatingState(LambdaState):
    OFF = 0, "OFF"
    AUTOMATIK = 1, "AUTOMATIK"
    MANUAL = 2, "MANUAL"
    ERROR = 3, "ERROR"
    OFFLINE = 4, "OFFLINE"


class CirculationPumpState(LambdaState):
    OFF = 0, "Off"
    ON = 1, "On"
    ERROR = 2, "Error"
