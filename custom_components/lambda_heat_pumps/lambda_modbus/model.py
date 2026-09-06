"""Shared base for every Lambda sub-system, and its scaled measurements.

The controller does not leave a register it has no value for empty — it answers
with a code. `0x8000` says the register is not there on this firmware, and
`-3000` says the sensor that feeds it is not connected. Scaled like readings
they come out as -327.68 °C and -300.0 °C, which look entirely plausible next to
a real temperature and are recorded into long-term statistics as if they were
one. So a measurement declares them, and reads as unknown instead.

They are declared on :func:`gauge` — every scaled measurement the controller
reports — and not on plain integers, where the same raw value can be a real
reading: 32768 W is a believable power, and a config parameter is whatever
number the controller wants to put there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modbus_connection import ModbusError
from modbus_connection.model import Component
from modbus_connection.model import enum as _enum, gauge as _gauge

# What the controller answers with instead of a measurement.
NO_REGISTER = 0x8000  # the firmware does not have this register
NO_SENSOR = 0xF448  # -3000: nothing is connected to it
SENTINELS = (NO_REGISTER, NO_SENSOR)

# 0xFFFF (-1) means "no request"/"nothing fed in" on a handful of registers —
# not declared on SENTINELS itself, because -1 is a genuine value on others
# (e.g. a temperature offset). Pass ``nan=SENTINELS + (NO_REQUEST,)`` on those
# specific fields instead (see buffer.py, heating_circuit.py, general.py).
NO_REQUEST = 0xFFFF


def gauge(address: int, scale: float, /, **kwargs: Any):
    """A scaled measurement, reading as unknown when the controller has none."""
    kwargs.setdefault("nan", SENTINELS)
    return _gauge(address, scale, **kwargs)


def enum(address: int, states, /, **kwargs: Any):
    """A state code, reading as unknown when the controller has none.

    A state register reports the same codes, and while an unmapped one already
    decodes to ``None``, it is warned about first — which for a sensor that is
    simply not connected would be a warning on every poll.
    """
    kwargs.setdefault("nan", SENTINELS)
    return _enum(address, states, **kwargs)


@dataclass(frozen=True)
class UpdateReport:
    """What one poll refreshed, by sub-system name.

    The names are the controller's own two sub-systems, ``ambient`` and
    ``e_manager``, and one per installed module — ``hp1``, ``boil1``, ``hc2``.

    A failed sub-system kept the values it had and did not notify its listeners;
    the error that failed it rides along. A controller that answered nothing at
    all is never in here — the update raises instead of reporting a silence that
    belongs to no one sub-system.
    """

    updated: set[str]
    failed: dict[str, ModbusError]

    @property
    def complete(self) -> bool:
        """Whether every polled sub-system refreshed."""
        return not self.failed


class LambdaComponent(Component):
    """A Lambda sub-system.

    The controller's readable ranges are not a property of a single sub-system —
    they depend on how many modules are configured — so :class:`LambdaHeatPump`
    computes them once and assigns ``register_ranges`` to every component it
    builds. See :mod:`.ranges`.
    """

    # Every value the controller exposes lives in holding registers (FC03); it
    # has no input registers, coils or discrete inputs.
    register_space = "holding"
