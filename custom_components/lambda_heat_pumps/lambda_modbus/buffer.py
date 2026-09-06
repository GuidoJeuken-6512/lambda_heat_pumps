"""A buffer tank (BUFF1-n)."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import BufferOperatingState, BufferRequestType
from .model import NO_REQUEST, SENTINELS, LambdaComponent, enum, gauge

# The controller answers these five registers with 0xFFFF (-1) when it has no
# active request of that kind — not a plausible reading (e.g. -6553.6 °C), so
# they read as unknown instead. 0xFFFF is not a global sentinel: it is a
# genuine value on other registers.
_NAN_WITH_NO_REQUEST = SENTINELS + (NO_REQUEST,)


class Buffer(LambdaComponent):
    """One buffer. Addresses are relative; the block sits at 3000 + 100n."""

    error_number = integer(0)
    operating_state = enum(1, BufferOperatingState)
    actual_high_temperature = gauge(2, 0.1, unit="°C")
    actual_low_temperature = gauge(3, 0.1, unit="°C")
    # force_fc16: see heating_circuit.py — Lambda's protocol has no FC06.
    buffer_temperature_high_setpoint = gauge(4, 0.1, writable=True, force_fc16=True, unit="°C")
    request_type = enum(5, BufferRequestType, signed=True, nan=_NAN_WITH_NO_REQUEST)
    request_flow_line_temp_setpoint = gauge(6, 0.1, unit="°C", nan=_NAN_WITH_NO_REQUEST)
    request_return_line_temp_setpoint = gauge(7, 0.1, unit="°C", nan=_NAN_WITH_NO_REQUEST)
    request_heat_sink_temp_diff_setpoint = gauge(8, 0.1, unit="K", nan=_NAN_WITH_NO_REQUEST)
    modbus_request_heating_capacity = gauge(9, 0.1, unit="kW", nan=_NAN_WITH_NO_REQUEST)

    maximum_buffer_temp = gauge(50, 0.1, writable=True, force_fc16=True, unit="°C")
