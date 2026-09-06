"""What a controller that answers only partly costs.

A poll reads each module on its own, so one that stops answering is contained:
it keeps the values it had, its entities say they are stale, and the rest of the
controller carries on. These pin that boundary from both sides — what a failure
takes down, and what it must not.

The totals are the exception that matters most. A gap in a running total reads
as a counter reset, which takes the long-term statistics and the energy
dashboard with it, so those stay available whatever the controller said.
"""

from __future__ import annotations

import logging

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from modbus_connection import ModbusTimeoutError

from custom_components.lambda_heat_pumps.coordinator import _TIMEOUTS_BEFORE_RECYCLING

from .conftest import Controller
from .test_init import setup_entry, state_of
from .test_reads import CAPACITY_POLL

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


# --------------------------------------------------------------------------
# One module failing
# --------------------------------------------------------------------------


async def test_a_healthy_poll_reads_every_installed_module(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Nothing is missing from the report when the controller is answering."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    await coordinator.async_refresh()

    assert coordinator.updated == {"ambient", "e_manager", "hp1", "boil1", "hc1"}
    assert not coordinator.failed


async def test_a_module_that_stops_answering_keeps_the_values_it_had(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The reads that landed are not thrown away because a later one did not."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"

    controller.answer_busy(1004)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert set(coordinator.failed) == {"hp1"}
    # The poll as a whole succeeded: the other four modules answered.
    assert coordinator.last_update_success
    # The heat pump still holds what it last read, even though it is now stale.
    assert coordinator.component("hp", 1).flow_line_temperature == 34.12


async def test_only_the_failed_modules_entities_go_unavailable(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A faulty module does not take the rest of the controller with it.

    This is the whole point of reading them apart: before, one module that would
    not answer made every entity on the controller unavailable, every poll.
    """
    entry = await setup_entry(hass, controller, legacy=True)

    controller.answer_busy(1004)  # inside the heat pump's block
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "unavailable"
    # Everything else is read and reported as usual.
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") == "48.0"
    assert state_of(hass, "eu08l_ambient_temperature_calculated") == "3.8"
    assert state_of(hass, "eu08l_hc1_room_device_temperature") == "21.5"


async def test_the_controllers_own_sub_systems_are_named_the_same_way(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Ambient and the e-manager are not modules, and still go unavailable alone.

    They are named in the report by the attribute they hang off the device as,
    and the sensors reading them name the same thing. A mismatch would not
    error — the sensors would simply never go unavailable — so it is worth
    asserting from the outside.
    """
    entry = await setup_entry(hass, controller, legacy=True)

    controller.answer_busy(2)  # the ambient block
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert set(entry.runtime_data.failed) == {"ambient"}
    assert state_of(hass, "eu08l_ambient_temperature_calculated") == "unavailable"
    # The e-manager sits in its own block and is unaffected.
    assert state_of(hass, "eu08l_emgr_actual_power") == "1500"
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_a_module_that_stops_answering_is_logged_once(
    hass: HomeAssistant, controller: Controller, caplog: pytest.LogCaptureFixture
) -> None:
    """A controller with one module off does not log on every poll."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.answer_busy(1004)
    with caplog.at_level(logging.WARNING):
        await coordinator.async_refresh()
        await coordinator.async_refresh()
        await coordinator.async_refresh()

    assert caplog.text.count("Failed to fetch hp1") == 1


async def test_a_module_that_answers_again_is_read_again(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Nothing has to be rebuilt for a module that comes back."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.answer_busy(1004)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "unavailable"

    controller.registers[1004] = 3500
    controller.answer_again_for(1004)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert not coordinator.failed
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "35.0"


async def test_a_controller_that_answers_nothing_says_what_went_wrong(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Every module refusing is a failed poll, carrying all of the reasons.

    Not one of them picked to stand for the rest: a controller refusing
    everything is worth reporting in full, and each module refused in its own
    right rather than the link having gone.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    for address in (0, 100, 1000, 2000, 5000):
        controller.answer_busy(address)
    await coordinator.async_refresh()

    assert not coordinator.last_update_success
    assert isinstance(coordinator.last_exception.__cause__, ExceptionGroup)
    assert len(coordinator.last_exception.__cause__.exceptions) == 5


async def test_listeners_fire_only_once_every_module_has_been_tried(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A listener sees a whole poll, not half of one.

    Each module is updated with its listeners held back, and they are fired
    afterwards — so nothing reads the controller mid-cycle, with some modules
    refreshed and the rest still holding the previous poll's values.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    device = entry.runtime_data.device

    seen: list[str] = []
    # The last module in the read order; if listeners fired as each module was
    # read, the ambient one would fire while this still held the old value.
    device.ambient.add_update_listener(
        lambda: seen.append(f"hc1={device.heating_circuits[0].room_device_temperature}")
    )

    controller.registers[5004] = 225
    await entry.runtime_data.async_refresh()

    assert seen == ["hc1=22.5"]


# --------------------------------------------------------------------------
# A controller that says nothing at all
# --------------------------------------------------------------------------


async def test_a_controller_that_answers_nothing_is_not_walked_module_by_module(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A silent controller costs one timeout, not one per module.

    Nothing answered — not a value, not even a refusal, which would at least
    prove the controller is there — so the rest would only time out too. Walking
    them all would make every poll take five timeouts and report every module as
    stale, when the truth is that the controller is not talking.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.stop_answering()
    controller.forget_reads()
    await coordinator.async_refresh()

    assert not coordinator.last_update_success
    assert len(controller.reads) == 1


async def test_a_module_that_times_out_after_another_answered_is_contained(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A timeout is only fatal while nothing has answered.

    Once a module has answered, the controller is demonstrably there, so one
    that times out after it is that module's problem and is contained like any
    other failure.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.stop_answering_for(1004)  # the heat pump, read after ambient
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success
    assert set(coordinator.failed) == {"hp1"}
    assert isinstance(coordinator.failed["hp1"], ModbusTimeoutError)
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") == "48.0"


async def test_a_silent_controller_does_not_reload_the_entry(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Being unreachable says nothing about what the controller has."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.go_offline()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert not coordinator.last_update_success
    assert entry.runtime_data is coordinator


async def test_a_silent_controller_reports_nothing_as_answered(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A poll that never got a report leaves the last one's behind.

    The diagnostics download names what answered so a module that is not
    answering can be told from one whose registers read oddly. Holding the last
    successful poll's names says the opposite of what happened.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    await coordinator.async_refresh()
    assert coordinator.updated

    controller.go_offline()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.updated == set()
    assert coordinator.failed == {}


async def test_a_contained_timeout_leaves_the_link_alone(
    hass: HomeAssistant, controller: Controller
) -> None:
    """One module timing out is not a wedged link, however often it repeats.

    The link is thrown away when nothing answers at all. A timeout the poll
    contained proves the opposite — the controller is there, and one module is
    not answering, which reopening the socket would not change.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    connection = coordinator.connection

    dropped = 0
    reopen = connection.disconnect

    async def count_drop() -> None:
        nonlocal dropped
        dropped += 1
        await reopen()

    connection.disconnect = count_drop  # type: ignore[method-assign]

    controller.stop_answering_for(1004)
    for _ in range(_TIMEOUTS_BEFORE_RECYCLING + 2):
        await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert "hp1" in coordinator.failed
    assert coordinator.updated
    assert dropped == 0


# --------------------------------------------------------------------------
# The totals, which have to survive all of it
# --------------------------------------------------------------------------


async def test_a_failed_modules_totals_stay_available(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A heat pump that stops answering does not gap its own energy history.

    A hole in a TOTAL_INCREASING sensor reads as a meter reset, which is what
    would take the long-term statistics with it.
    """
    entry = await setup_entry(hass, controller, legacy=True)

    controller.answer_busy(1004)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "unavailable"
    # The counters the module carries keep reporting what they last read.
    assert state_of(hass, "eu08l_hp1_compressor_power_consumption_accumulated") == "100000"
    assert state_of(hass, "eu08l_hp1_compressor_thermal_energy_output_accumulated") == "400000"


async def test_a_silent_controller_leaves_the_totals_alone(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Even a controller that answers nothing at all leaves the totals reporting.

    This is why the "names no sub-system" test comes before the coordinator's
    own: a heat pump switched off for the season should not take its own
    lifetime energy history down with it.
    """
    entry = await setup_entry(hass, controller, legacy=True)

    controller.go_offline()
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "unavailable"
    assert state_of(hass, "eu08l_hp1_compressor_power_consumption_accumulated") == "100000"
    # The derived sensors hold their own values too.
    assert state_of(hass, "eu08l_hp1_cop_calc") == "4.0"


async def test_a_total_that_dips_by_a_hair_keeps_what_it_had(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A carry caught mid-read is not a meter reset.

    These are 32-bit counters read as two registers, so a poll that catches the
    controller between the two words reads a value just under the last one. Home
    Assistant would take the difference for a reset and start the statistics
    again.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    key = "eu08l_hp1_compressor_power_consumption_accumulated"
    assert state_of(hass, key) == "100000"

    controller.registers[1021] = 0x869F  # 100000 -> 99999 Wh
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, key) == "100000"

    # And it goes on counting from where it was once the reading climbs again.
    controller.registers[1021] = 0x86A1  # 100001 Wh
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, key) == "100001"


async def test_a_total_that_really_falls_is_published(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A counter that was actually reset is reported as read.

    The guard is deliberately narrow — under one percent — so a replaced heat
    pump or a genuinely reset counter still comes through.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    key = "eu08l_hp1_compressor_power_consumption_accumulated"
    assert state_of(hass, key) == "100000"

    controller.registers[1020] = 0
    controller.registers[1021] = 5000
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, key) == "5000"


# --------------------------------------------------------------------------
# The capacity limits, on their own poll
# --------------------------------------------------------------------------


async def test_the_capacity_limits_fail_on_their_own(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The two polls are independent in both directions."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    [capacity] = coordinator.capacity_limits

    # The full poll failing does not take the limits down.
    controller.answer_busy(1004)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert capacity.last_update_success
    assert state_of(hass, "eu08l_hp1_cooling_max_output_power") != "unavailable"

    # And the limits failing does not touch the full poll.
    controller.answer_again_for(1004)
    controller.answer_busy(1055)
    await coordinator.async_refresh()
    await capacity.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success
    assert not capacity.last_update_success
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_the_capacity_poll_never_recycles_the_link(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Only the full poll may throw the link away.

    Two pollers counting timeouts over one connection would race to drop it, and
    the slow one could tear it down under a poll already in flight. Liveness is
    the full poll's job; this one only reports its own failure.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    [capacity] = coordinator.capacity_limits
    connection = coordinator.connection

    controller.stop_answering_for(1050)
    for _ in range(4):
        await capacity.async_refresh()

    assert not capacity.last_update_success
    assert connection.connected


async def test_the_capacity_limits_are_polled_on_the_hour(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The slow poll is really armed, and really is an hour apart.

    Carving the limits out is only a saving if they are still read; a
    coordinator that was built but never scheduled would look identical to every
    other test here.
    """
    from datetime import timedelta

    from freezegun.api import FrozenDateTimeFactory
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    [capacity] = coordinator.capacity_limits
    assert capacity.update_interval == timedelta(hours=1)

    controller.registers[1059] = 250  # cooling_max_output_power -> 25.0 kW
    controller.forget_reads()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=1, seconds=1))
    await hass.async_block_till_done()

    # An hour's worth of the fast and full polls lands too, so this asks only
    # that the limits were among what was read — and that the new value arrived.
    assert CAPACITY_POLL <= set(controller.reads)
    assert state_of(hass, "eu08l_hp1_cooling_max_output_power") == "25.0"


async def test_a_second_heat_pump_gets_its_own_capacity_poll(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Each heat pump's limits are their own component on their own coordinator.

    The limits share a block with the heat pump they belong to, so a second one
    is the case where an off-by-one in the indexing would show up: two
    coordinators both reading HP1's block, or HP2's sensors reading HP1's values.
    """
    # Give the controller a second heat pump, and stop refusing its block.
    controller.registers.update(
        {1100: 0, 1102: 5, 1103: 1, 1104: 2000, 1110: 5000, 1159: 300}
    )
    controller.install(1100)
    controller.refuse(1200)  # and no third one

    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    assert coordinator.counts["hp"] == 2
    assert len(coordinator.capacity_limits) == 2

    controller.forget_reads()
    for capacity in coordinator.capacity_limits:
        await capacity.async_refresh()
    await hass.async_block_till_done()

    # One coordinator reads 1050-1060, the other 1150-1160 — not the same block.
    assert set(controller.reads) == {
        *((address, 1) for address in range(1050, 1061)),
        *((address, 1) for address in range(1150, 1161)),
    }
    # And each heat pump's sensor reports its own controller's value.
    assert state_of(hass, "eu08l_hp1_cooling_max_output_power") == "0.0"
    assert state_of(hass, "eu08l_hp2_cooling_max_output_power") == "30.0"
