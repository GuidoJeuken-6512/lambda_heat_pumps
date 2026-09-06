"""A solar thermal module (SOL1-n)."""

from __future__ import annotations

from modbus_connection.model import int32, integer

from .enums import SolarOperatingState
from .model import LambdaComponent, enum, gauge


class Solar(LambdaComponent):
    """One solar module. Addresses are relative; the block sits at 4000 + 100n."""

    error_number = integer(0)
    operating_state = enum(1, SolarOperatingState)
    collector_temperature = gauge(2, 0.1, unit="°C")
    storage_temperature = gauge(3, 0.1, unit="°C")
    power_current = gauge(4, 0.1, unit="kW")
    energy_total = int32(5, unit="kWh")

    maximum_buffer_temperature = gauge(50, 0.1, writable=True, unit="°C")
    buffer_changeover_temperature = gauge(51, 0.1, writable=True, unit="°C")


class SolarLowFirst(Solar):
    """A solar module whose 32-bit counter puts the low word first (CDAB)."""

    energy_total = int32(5, word_order="little", unit="kWh")
