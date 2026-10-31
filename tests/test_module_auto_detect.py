"""Counting the modules a controller has, when it is slow to answer."""

from __future__ import annotations

from modbus_connection import IllegalDataAddressError, ModbusTimeoutError

from custom_components.lambda_heat_pumps.module_auto_detect import _count


class _Unit:
    """Answers for the first `installed` modules of a type, with scripted hiccups."""

    def __init__(self, installed: int, *, slow_once: set[int] = frozenset(), silent: bool = False):
        self.installed = installed
        self.slow_once = set(slow_once)
        self.silent = silent
        self.reads: list[int] = []

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        self.reads.append(address)
        if address in self.slow_once:
            self.slow_once.discard(address)
            raise ModbusTimeoutError("slow")
        index = (address - 4000) // 100 + 1
        if index > self.installed:
            if self.silent:
                raise ModbusTimeoutError("nothing there")
            raise IllegalDataAddressError()
        return [0]


async def test_a_module_that_is_slow_once_is_still_found() -> None:
    """#101: one slow answer at setup used to drop the module until a reload."""
    unit = _Unit(installed=1, slow_once={4000})

    assert await _count(unit, "sol", 2) == 1
    assert unit.reads.count(4000) == 2


async def test_an_absent_module_is_not_asked_twice() -> None:
    """"No such register" is unambiguous."""
    unit = _Unit(installed=0)

    assert await _count(unit, "sol", 2) == 0
    assert unit.reads == [4000]


async def test_a_controller_silent_for_absent_modules_is_asked_once_more() -> None:
    """Silence is how some controllers say "not installed"; that takes two tries."""
    unit = _Unit(installed=1, silent=True)

    assert await _count(unit, "sol", 2) == 1
    assert unit.reads == [4000, 4100, 4100]
