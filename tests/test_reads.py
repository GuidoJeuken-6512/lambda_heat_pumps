"""Where the integration reads, and how wide.

These assert the shape of the traffic rather than the values that come out of
it, because the failure they guard against does not change the values. A read
plan that stops pooling still decodes everything correctly — it just asks the
controller twenty-three questions instead of, or sixty-two instead of
twenty-three. Nothing else in the suite would notice.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from .conftest import Controller
from .test_init import setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

# What one poll of the test controller — a heat pump, a boiler and a heating
# circuit — should ask for. Each entry is one Modbus read: (address, registers).
#
# The runs come from the module's readable ranges, and the single-register reads
# in them are deliberate: the heat pump's capacity limits (1050-1060) and the
# heating circuit's flow-line setpoint (5007) return garbage when they are read
# as part of a wider block, so each is read on its own. The two-register reads at
# 1020 and 1022 are the 32-bit counters, each read whole and neither merged with
# the other.
POLL = {
    (0, 5),  # ambient
    (100, 5),  # e-manager
    (1000, 14),  # heat pump: the documented block
    (1015, 5),
    (1020, 2),  # electrical counter
    (1022, 2),  # thermal counter
    (1024, 10),  # the undocumented refrigerant registers
    *((address, 1) for address in range(1050, 1061)),  # capacity limits
    (2000, 6),  # boiler
    (2050, 1),
    (5000, 7),  # heating circuit
    (5007, 1),  # its flow-line setpoint, on its own
    (5050, 3),
}


async def test_a_poll_reads_the_blocks_the_ranges_describe(
    hass: HomeAssistant, controller: Controller
) -> None:
    """One poll asks exactly these questions, no more and no narrower.

    Reading a register at a time gives the same values, so this is what stands
    between a working integration and one that quietly makes sixty-odd round
    trips where twenty-three would do.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    controller.forget_reads()

    await entry.runtime_data.async_refresh()

    assert set(controller.reads) == POLL
    # And each block is read once, not once per field in it.
    assert len(controller.reads) == len(POLL)


async def test_no_read_covers_a_register_the_controller_refuses(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A block never spans a register the controller will not serve.

    Its neighbours are still pooled around it — the block is split, not
    abandoned — so the reads either side of the hole stay wide.
    """
    controller.refuse(2002)  # in the middle of the boiler's block
    entry = await setup_entry(hass, controller, legacy=True)
    controller.forget_reads()

    await entry.runtime_data.async_refresh()

    for address, count in controller.reads:
        assert not address <= 2002 < address + count, (address, count)
    # Both sides of it are still read as blocks.
    assert (2000, 2) in controller.reads
    assert (2003, 3) in controller.reads


async def test_a_module_that_is_not_installed_is_never_read(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Nothing is asked of a buffer or solar module the controller does not have."""
    entry = await setup_entry(hass, controller, legacy=True)
    controller.forget_reads()

    await entry.runtime_data.async_refresh()

    for address, count in controller.reads:
        assert not 3000 <= address < 5000, f"read {address} of an absent module"
