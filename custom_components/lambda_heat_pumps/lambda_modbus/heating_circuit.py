"""A heating circuit (HC1-n)."""

from __future__ import annotations

from modbus_connection.model import integer

from .enums import HeatingCircuitOperatingMode, HeatingCircuitOperatingState
from .model import NO_REQUEST, SENTINELS, LambdaComponent, enum, gauge


class HeatingCircuit(LambdaComponent):
    """One heating circuit. Addresses are relative; the block sits at 5000 + 100n."""

    error_number = integer(0)
    operating_state = enum(1, HeatingCircuitOperatingState)
    flow_line_temperature = gauge(2, 0.1, unit="°C")
    return_line_temperature = gauge(3, 0.1, unit="°C")
    room_device_temperature = gauge(4, 0.1, writable=True, unit="°C")
    set_flow_line_temperature = gauge(5, 0.1, writable=True, unit="°C")
    # 0xFFFF (-1) means "no request" here — not a real HeatingCircuitOperatingMode
    # code, so it reads as unknown instead of a bogus mode.
    operating_mode = enum(
        6, HeatingCircuitOperatingMode, signed=True, writable=True,
        nan=SENTINELS + (NO_REQUEST,),
    )
    flow_line_temperature_setpoint = gauge(7, 0.1, writable=True, unit="°C")

    # Firmware 3+ reports the setpoint the controller actually acts on at the
    # same address; the integration exposes it as its own read-only sensor.
    target_temp_flow_line = gauge(7, 0.1, unit="°C")

    set_flow_line_offset_temperature = gauge(50, 0.1, writable=True, unit="°C")
    target_room_temperature = gauge(51, 0.1, writable=True, unit="°C")
    set_cooling_mode_room_temperature = gauge(52, 0.1, writable=True, unit="°C")
