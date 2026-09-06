"""A Lambda heat pump controller, as an object over Modbus.

This package talks to the controller and nothing else — it has no Home Assistant
import, takes a :class:`modbus_connection.ModbusUnit` rather than a host or a
connection, and is tested against the in-memory mock backend. It lives inside the
integration for now because Home Assistant can only load what it ships; it is
shaped to be lifted out into its own PyPI package unchanged, which is what Core
would require.

    from modbus_connection import ModbusTcpParams
    from modbus_connection.tmodbus import ModbusConnection
    from lambda_modbus import LambdaHeatPump

    connection = ModbusConnection(ModbusTcpParams(host="192.168.1.50", port=502))
    try:
        controller = LambdaHeatPump(connection.for_unit(1), num_hps=2)
        await controller.async_setup()
        await controller.async_update()
        print(controller.ambient.temperature)
        print(controller.heat_pumps[0].flow_line_temperature)
    finally:
        await connection.close()

A controller's register map depends on its firmware: it serves a subset of the
registers a module could have, and refuses a block read that reaches a register
it does not serve — which, read atomically, would take the served registers
around it down too. So the layout is declared here but *confirmed* against the
controller. :meth:`LambdaHeatPump.async_setup` reads each module a run at a time,
drops to one register at a time on a run the controller refuses, and narrows each
module to the registers it actually answered for. A register it does not serve is
dropped from that module's read plan, so it is never read and reads as ``None``,
while everything else stays the ordinary typed component with the ordinary
update.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusError,
    ModbusTimeoutError,
)

from .boiler import Boiler
from .buffer import Buffer
from .general import Ambient, EManager
from .heat_pump import HeatPump, HeatPumpCapacityLimits, HeatPumpLowFirst
from .heating_circuit import HeatingCircuit
from .model import LambdaComponent, UpdateReport
from .ranges import (
    AMBIENT_RANGES,
    E_MANAGER_RANGES,
    HP_CAPACITY_RANGES,
    Range,
    base_address,
    module_ranges,
)
from .solar import Solar, SolarLowFirst

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit, WordOrder

__all__ = [
    "Ambient",
    "Boiler",
    "Buffer",
    "EManager",
    "HeatPump",
    "HeatPumpCapacityLimits",
    "HeatingCircuit",
    "LambdaComponent",
    "LambdaHeatPump",
    "Solar",
    "UpdateReport",
]


async def _probe_served(unit: ModbusUnit, ranges: tuple[Range, ...]) -> set[int]:
    """The addresses in ``ranges`` the controller answers for.

    Each run is tried as one block read; a run the controller says it has nothing
    at is retried one register at a time, so the served registers in it are still
    found.

    Only the one answer that describes the register map is taken as one — the
    controller saying it has nothing at that address. A controller that is busy
    or has faulted is refusing to answer *now*, which tells us nothing about what
    it has; since this map is kept for the life of the config entry, believing it
    would leave registers missing until someone reloaded. Those propagate, and
    setup is retried.
    """
    served: set[int] = set()
    for low, high in ranges:
        try:
            await unit.read_holding_registers(low, high - low + 1)
        except IllegalDataAddressError:
            for address in range(low, high + 1):
                try:
                    await unit.read_holding_registers(address, 1)
                except IllegalDataAddressError:
                    continue  # a register the controller does not have
                served.add(address)
        else:
            served.update(range(low, high + 1))
    return served


class LambdaHeatPump:
    """A Lambda controller with the modules that are installed on it.

    `word_order` is how the controller lays out its 32-bit counters across two
    registers: `"big"` (the default, high word first) or `"little"`. It varies by
    controller, which is why it is configurable rather than modelled.

    Construct, then :meth:`async_setup` once to probe the register map, then
    :meth:`async_update` on a schedule.
    """

    def __init__(
        self,
        unit: ModbusUnit,
        *,
        num_hps: int = 1,
        num_boil: int = 1,
        num_buff: int = 0,
        num_sol: int = 0,
        num_hc: int = 1,
        word_order: WordOrder = "big",
    ) -> None:
        self._unit = unit
        self._word_order = word_order
        self._counts = {
            "hp": num_hps,
            "boil": num_boil,
            "buff": num_buff,
            "sol": num_sol,
            "hc": num_hc,
        }

        # Populated by async_setup; declared here so the attributes always exist.
        self.ambient: Ambient
        self.e_manager: EManager
        self.heat_pumps: list[HeatPump] = []
        self.boilers: list[Boiler] = []
        self.buffers: list[Buffer] = []
        self.solar_modules: list[Solar] = []
        self.heating_circuits: list[HeatingCircuit] = []
        # Read apart from the poll, on their own schedule; see `async_setup`.
        self.capacity_limits: list[HeatPumpCapacityLimits] = []

        # What a poll reads, named as the report names it. The capacity limits
        # are deliberately not in here: they are polled on their own schedule,
        # so they are in no report and fail on their own.
        self._polled: dict[str, LambdaComponent] = {}

    async def async_setup(self) -> None:
        """Probe the controller and build each module from what it serves."""
        heat_pump_class = HeatPump if self._word_order == "big" else HeatPumpLowFirst
        solar_class = Solar if self._word_order == "big" else SolarLowFirst

        self.ambient = await self._build(Ambient, 0, AMBIENT_RANGES)
        self.e_manager = await self._build(EManager, 0, E_MANAGER_RANGES)
        self.heat_pumps = await self._build_all(heat_pump_class, "hp")
        self.boilers = await self._build_all(Boiler, "boil")
        self.buffers = await self._build_all(Buffer, "buff")
        self.solar_modules = await self._build_all(solar_class, "sol")
        self.heating_circuits = await self._build_all(HeatingCircuit, "hc")
        self.capacity_limits = await self._build_all(
            HeatPumpCapacityLimits, "hp", HP_CAPACITY_RANGES
        )

        self._polled = {
            "ambient": self.ambient,
            "e_manager": self.e_manager,
            **{
                f"{module}{index}": component
                for module, components in (
                    ("hp", self.heat_pumps),
                    ("boil", self.boilers),
                    ("buff", self.buffers),
                    ("sol", self.solar_modules),
                    ("hc", self.heating_circuits),
                )
                for index, component in enumerate(components, 1)
            },
        }

    async def _build_all[C: LambdaComponent](
        self,
        component_class: type[C],
        module: str,
        relative_ranges: tuple[Range, ...] | None = None,
    ) -> list[C]:
        """One component per installed module, each at its own 100-register block.

        `relative_ranges` overrides the module's own runs, for a second component
        sharing the block — the heat pump's capacity limits.
        """
        ranges = module_ranges(module) if relative_ranges is None else relative_ranges
        return [
            await self._build(
                component_class,
                base_address(module, index),
                ranges,
                index=index,
            )
            for index in range(1, self._counts[module] + 1)
        ]

    async def _build[C: LambdaComponent](
        self,
        component_class: type[C],
        base: int,
        relative_ranges: tuple[Range, ...],
        index: int = 1,
    ) -> C:
        """Probe one module's runs and keep only the fields it answers for.

        The component is the ordinary typed one — same fields, same update — with
        its read plan narrowed to the registers this controller serves. A field
        the controller does not serve is dropped from the plan, so it is never
        read and reads as ``None``.
        """
        # The probe talks to the wire, so it works in absolute addresses.
        served = await _probe_served(
            self._unit,
            tuple((base + low, base + high) for low, high in relative_ranges),
        )

        component = component_class(self._unit, index=index, base_offset=base)
        # Ranges are declared in the same coordinates as the field addresses, so
        # they are stated relative to the block and the component shifts them.
        component.register_ranges = relative_ranges
        # Keeping only the fields the controller serves also splits the ranges
        # around the ones it does not, so a block never spans a refused register.
        component.restrict_fields(
            [
                name
                for name, field in component_class.declared_fields.items()
                if all(
                    base + field.address + offset in served
                    for offset in range(field.count)
                )
            ]
        )
        return component

    @property
    def components(self) -> tuple[LambdaComponent, ...]:
        """Every sub-system this controller has, whichever schedule reads it."""
        return (*self._polled.values(), *self.capacity_limits)

    async def async_update(self) -> UpdateReport:
        """Refresh every polled sub-system, one at a time.

        Each module is read on its own, so they are independent: one that stops
        answering keeps the values it had and is named in the report, while the
        rest still refresh. Listeners fire only once every sub-system has been
        tried, and only for the ones that did refresh — so what a listener reads
        is one poll's worth of the controller, not half of it.

        A silence that belongs to no one module raises instead of being
        reported: the link itself failing, and a first sub-system that times out
        with nothing having answered yet — walking the rest of a controller that
        is not talking costs a full timeout per module and reports every one of
        them as stale.
        """
        updated: set[str] = set()
        failed: dict[str, ModbusError] = {}
        for name, component in self._polled.items():
            try:
                await component.async_update(notify=False)
            except ModbusConnectionError:
                raise
            except ModbusTimeoutError as err:
                if not updated and not failed:
                    # Nothing has answered yet — not a value, not even a refusal,
                    # which would at least prove the controller is there. Assume
                    # the rest would time out too rather than paying for each.
                    raise
                failed[name] = err
            except ModbusError as err:
                failed[name] = err
            else:
                updated.add(name)
        for name in updated:
            self._polled[name].notify()
        return UpdateReport(updated, failed)
