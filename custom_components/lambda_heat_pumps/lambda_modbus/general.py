"""The controller's two always-present sub-systems: ambient and E-Manager."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import AmbientOperatingState, EManagerOperatingState
from .model import NO_REQUEST, SENTINELS, LambdaComponent, enum, gauge


class Ambient(LambdaComponent):
    """Outside-air readings (registers 0-4)."""

    error_number = integer(0)
    operating_state = enum(1, AmbientOperatingState)
    # 0xFFFF (-1) means "no external ambient sensor fed in", not a real -300 °C
    # reading; unlike the other sentinels this is opt-in, since -1 is a
    # genuine value on some other registers (e.g. temperature offsets).
    temperature = gauge(2, 0.1, unit="°C", nan=SENTINELS + (NO_REQUEST,))
    temperature_1h = gauge(3, 0.1, unit="°C")
    temperature_calculated = gauge(4, 0.1, unit="°C")


class EManager(LambdaComponent):
    """The energy manager (registers 100-104)."""

    error_number = integer(100)
    operating_state = enum(101, EManagerOperatingState)
    actual_power = integer(102, unit="W")
    actual_power_consumption = integer(103, unit="W")
    power_consumption_setpoint = integer(104, unit="W")
