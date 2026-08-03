"""A domestic hot water boiler (BOIL1-n)."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import BoilerOperatingState, RelaisState
from .model import LambdaComponent, enum, gauge


class Boiler(LambdaComponent):
    """One boiler. Addresses are relative; the block sits at 2000 + 100n."""

    error_number = integer(0)
    operating_state = enum(1, BoilerOperatingState)
    actual_high_temperature = gauge(2, 0.1, unit="°C")
    actual_low_temperature = gauge(3, 0.1, unit="°C")
    actual_circulation_temperature = gauge(4, 0.1, unit="°C")
    actual_circulation_pump_state = enum(5, RelaisState, signed=True)

    target_high_temperature = gauge(50, 0.1, writable=True, unit="°C")
