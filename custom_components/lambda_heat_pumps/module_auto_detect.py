"""Finding out which modules a controller has.

A Lambda system is built from modules — heat pumps, boilers, buffers, solar
modules, heating circuits — each occupying its own block of registers. The
controller does not report how many of each are installed, but it refuses to
read the block of one that is not there, which is answer enough.
"""

from __future__ import annotations

import logging

from modbus_connection import (
    ModbusError,
    ModbusExceptionError,
    ModbusTimeoutError,
    ModbusUnit,
)

from .lambda_modbus import ILLEGAL_DATA_ADDRESS
from .lambda_modbus.ranges import base_address

_LOGGER = logging.getLogger(__name__)

# How many of each module a controller can have.
MAX_MODULE_COUNTS = {"hp": 3, "boil": 5, "buff": 5, "sol": 2, "hc": 12}

# A module's first register is its error number. A module that is not installed
# does not answer for it — and neither does any module beyond it.
_PROBE_REGISTER = 0


async def async_detect_modules(unit: ModbusUnit) -> dict[str, int]:
    """Probe the controller for the modules it has.

    Raises ModbusError if the controller cannot be reached at all; a module that
    merely answers "no such register" is simply not installed.
    """
    counts = {}
    for module, maximum in MAX_MODULE_COUNTS.items():
        counts[module] = await _count(unit, module, maximum)

    if counts["hp"] == 0:
        # Every Lambda system has at least one, so a controller that will not
        # admit to one is telling us something we cannot act on.
        raise ModbusError("The controller reports no heat pump")

    _LOGGER.debug("Detected modules: %s", counts)
    return counts


async def _count(unit: ModbusUnit, module: str, maximum: int) -> int:
    """How many of one module type answer, counting up from the first.

    A module that is not installed says there is nothing at its address, or
    stays silent. Anything else is the controller declining to answer rather
    than telling us what it has: a busy or faulted controller would otherwise be
    read as a system with fewer modules than it has, and the count is kept for
    the life of the config entry. So it propagates, and setup is retried.
    """
    for index in range(1, maximum + 1):
        register = base_address(module, index) + _PROBE_REGISTER
        try:
            await unit.read_holding_registers(register, 1)
        except ModbusExceptionError as err:
            if err.exception_code != ILLEGAL_DATA_ADDRESS:
                raise
            return index - 1
        except ModbusTimeoutError:
            # Silence is how some controllers answer for a module they do not
            # have, so it still ends the count.
            return index - 1
    return maximum
