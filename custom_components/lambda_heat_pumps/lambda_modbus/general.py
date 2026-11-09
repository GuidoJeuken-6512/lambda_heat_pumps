"""The controller's two always-present sub-systems: ambient and E-Manager."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import AmbientOperatingState, EManagerOperatingState
from .model import NO_REGISTER, LambdaComponent, enum, gauge


class Ambient(LambdaComponent):
    """Outside-air readings (registers 0-4)."""

    error_number = integer(0)
    operating_state = enum(1, AmbientOperatingState)
    # 0xFFFF is -0.1 °C here, a genuine reading around freezing (#153): a
    # missing sensor reports -3000 (NO_SENSOR), which SENTINELS already covers.
    temperature = gauge(2, 0.1, unit="°C")
    temperature_1h = gauge(3, 0.1, unit="°C")
    temperature_calculated = gauge(4, 0.1, unit="°C")


class EManager(LambdaComponent):
    """The energy manager (registers 100-104)."""

    error_number = integer(100)
    operating_state = enum(101, EManagerOperatingState)
    # Signed, so 0x8000 would be -32768 W: what a V0.0.8-3K controller reports
    # with its energy manager not set to Modbus (#91), not a power.
    actual_power = integer(102, unit="W", nan=NO_REGISTER)
    actual_power_consumption = integer(103, unit="W", nan=NO_REGISTER)
    power_consumption_setpoint = integer(104, unit="W", nan=NO_REGISTER)
