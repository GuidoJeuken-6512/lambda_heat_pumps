"""A buffer tank (BUFF1-n)."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import BufferOperatingState, BufferRequestType
from .model import LambdaComponent, enum, gauge


class Buffer(LambdaComponent):
    """One buffer. Addresses are relative; the block sits at 3000 + 100n."""

    error_number = integer(0)
    operating_state = enum(1, BufferOperatingState)
    actual_high_temperature = gauge(2, 0.1, unit="°C")
    actual_low_temperature = gauge(3, 0.1, unit="°C")
    buffer_temperature_high_setpoint = gauge(4, 0.1, writable=True, unit="°C")
    request_type = enum(5, BufferRequestType, signed=True)
    request_flow_line_temp_setpoint = gauge(6, 0.1, unit="°C")
    request_return_line_temp_setpoint = gauge(7, 0.1, unit="°C")
    request_heat_sink_temp_diff_setpoint = gauge(8, 0.1, unit="K")
    modbus_request_heating_capacity = gauge(9, 0.1, unit="kW")

    maximum_buffer_temp = gauge(50, 0.1, writable=True, unit="°C")
