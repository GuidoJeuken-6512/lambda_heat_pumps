"""Setting up a controller: what it finds, and what it creates."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, valid_entity_id
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lambda_heat_pumps.const import (
    CONF_FIRMWARE_VERSION,
    CONF_INT32_REGISTER_ORDER,
    CONF_SLAVE_ID,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DOMAIN,
    ENTRY_VERSION,
    REGISTER_ORDER_LOW_FIRST,
)

from .conftest import HOST, PORT, SLAVE_ID, Controller


pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def entry_data(*, legacy: bool = False) -> dict:
    """A config entry for the controller the `controller` fixture stands up."""
    return {
        CONF_NAME: "EU08L",
        CONF_HOST: HOST,
        CONF_PORT: PORT,
        CONF_SLAVE_ID: SLAVE_ID,
        CONF_FIRMWARE_VERSION: "V0.0.8-3K",
        CONF_USE_LEGACY_MODBUS_NAMES: legacy,
    }


async def setup_entry(
    hass: HomeAssistant, controller: Controller, *, legacy: bool = False, options=None
) -> MockConfigEntry:
    """Set up the controller."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=ENTRY_VERSION,
        data=entry_data(legacy=legacy),
        options=options or {},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_detects_the_modules_the_controller_has(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The probe finds one of each installed module, and none of the rest."""
    entry = await setup_entry(hass, controller)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.counts == {"hp": 1, "boil": 1, "buff": 0, "sol": 0, "hc": 1}


def state_of(hass: HomeAssistant, unique_id: str) -> str:
    """A sensor's state, found the way its identity is actually defined."""
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id, f"no entity for {unique_id}"
    return hass.states.get(entity_id).state


async def enable_sensors(
    hass: HomeAssistant, entry: MockConfigEntry, *unique_ids: str
) -> None:
    """Turn on entities that ship disabled, as a user would, and reload.

    The per-period counters are off by default; a test that reads one has to
    enable it first, then reload so it comes up with a state.
    """
    registry = er.async_get(hass)
    for unique_id in unique_ids:
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entity_id, f"no entity for {unique_id}"
        registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_reads_the_controller(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Values come back decoded — scaled, signed, and state codes resolved."""
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_ambient_temperature") == "4.2"
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"
    assert state_of(hass, "eu08l_hp1_state") == "START COMPRESSOR"
    assert state_of(hass, "eu08l_hp1_operating_state") == "CH"
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") == "48.0"
    # A 32-bit counter, over two registers.
    assert (
        state_of(hass, "eu08l_hp1_compressor_power_consumption_accumulated") == "100000"
    )


async def test_unique_ids_are_unchanged(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An existing installation's entities keep the ids they have always had."""
    entry = await setup_entry(hass, controller, legacy=True)
    registry = er.async_get(hass)

    for unique_id in (
        "eu08l_ambient_temperature",
        "eu08l_hp1_flow_line_temperature",
        "eu08l_hp1_heating_cycling_total",
        "eu08l_hp1_heating_cycling_yesterday",
        "eu08l_hp1_heating_energy_daily",
        "eu08l_hp1_heating_thermal_energy_monthly",
        "eu08l_hp1_heating_cop_total",
        "eu08l_boil1_target_high_temperature",
        "eu08l_hc1_heating_curve_flow_line_temperature_calc",
    ):
        assert registry.async_get_entity_id("sensor", DOMAIN, unique_id), unique_id

    assert registry.async_get_entity_id("climate", DOMAIN, "eu08l_boil1_hot_water")
    assert registry.async_get_entity_id(
        "number", DOMAIN, "eu08l_hc1_flow_line_offset_temperature_number"
    )
    assert entry.state is ConfigEntryState.LOADED


async def test_entity_ids_are_named_from_the_register_not_the_translation(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The entity id is the register's key, so it does not vary by language.

    Home Assistant would otherwise build it from the translated name, which
    makes the id depend on the language the instance runs in, and lets two names
    that differ only by a sign collide.
    """
    await setup_entry(hass, controller, legacy=True)
    registry = er.async_get(hass)

    for domain, unique_id in (
        ("sensor", "eu08l_ambient_temperature"),
        ("sensor", "eu08l_hp1_flow_line_temperature"),
        ("sensor", "eu08l_boil1_actual_high_temperature"),
        ("climate", "eu08l_boil1_hot_water"),
        ("number", "eu08l_hc1_flow_line_offset_temperature_number"),
    ):
        entity_id = registry.async_get_entity_id(domain, DOMAIN, unique_id)
        assert entity_id == f"{domain}.{unique_id}", unique_id


async def test_a_register_its_firmware_withdrew_is_not_modelled(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A register only older firmware serves is left out on a newer controller.

    The controller still answers for it — it just stops reporting anything
    through it — so probing cannot tell, and the sensor says which versions it
    is good on instead.
    """
    registry = er.async_get(hass)

    # V0.0.8-3K is version 6, inside the register's 1-7 range.
    entry = await setup_entry(hass, controller, legacy=True)
    assert state_of(hass, "eu08l_ambient_temperature") == "4.2"
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    # V1.1.0-3K is version 9, past it.
    data = entry_data(legacy=True) | {CONF_FIRMWARE_VERSION: "V1.1.0-3K"}
    newer = MockConfigEntry(domain=DOMAIN, version=ENTRY_VERSION, data=data)
    newer.add_to_hass(hass)
    assert await hass.config_entries.async_setup(newer.entry_id)
    await hass.async_block_till_done()

    assert not registry.async_get_entity_id(
        "sensor", DOMAIN, "eu08l_ambient_temperature"
    )
    # Its neighbours in the same block are unaffected.
    assert registry.async_get_entity_id(
        "sensor", DOMAIN, "eu08l_ambient_temperature_calculated"
    )


async def test_a_register_with_nothing_behind_it_reads_unknown(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The controller's "no value" codes are not read as measurements.

    It answers 0x8000 for a register its firmware does not have and -3000 for a
    sensor that is not connected. Scaled like readings those are -327.68 °C and
    -300.0 °C, which look plausible enough to be recorded as real.
    """
    controller.registers[1008] = 0x8000  # energy source outlet: no such register
    controller.registers[5003] = 0xF448  # hc return line: no sensor connected
    controller.registers[5006] = 0xF448  # and its operating mode with it
    await setup_entry(hass, controller, legacy=True)

    for unique_id in (
        "eu08l_hp1_energy_source_outlet_temperature",
        "eu08l_hc1_return_line_temperature",
        "eu08l_hc1_operating_mode",
    ):
        assert state_of(hass, unique_id) in ("unknown", "unavailable"), unique_id

    # A real reading in the same block is untouched.
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_modules_are_their_own_devices(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Each module hangs off the controller as its own device."""
    entry = await setup_entry(hass, controller)
    devices = dr.async_get(hass)

    main = devices.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert main is not None
    assert main.name == "EU08L"

    heat_pump = devices.async_get_device(
        identifiers={(DOMAIN, entry.entry_id, "hp", 1)}
    )
    assert heat_pump is not None
    assert heat_pump.name == "EU08L - HP1"
    assert heat_pump.via_device_id == main.id


async def test_unload_closes_the_connection(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The integration owns the link, so it lets go of it."""
    entry = await setup_entry(hass, controller)
    connection = entry.runtime_data.connection

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not connection.connected


async def test_a_controller_that_changes_is_looked_at_again(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A register that stops answering makes the integration re-probe itself.

    The map was read off the controller at setup, so a block it now refuses
    means that map is stale. Rather than sitting there failing until the user
    reloads it, the integration sets itself up again and carries on with what
    the controller serves now.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"

    # The controller stops serving a register it served at setup.
    controller.refuse(1004)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    # It set itself up again, and is working — without the refused register.
    coordinator = entry.runtime_data
    assert entry.state is ConfigEntryState.LOADED
    assert coordinator.last_update_success
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") in (
        "unknown",
        "unavailable",
    )
    # Its neighbours, which the controller still serves, are read as before.
    assert state_of(hass, "eu08l_hp1_return_line_temperature") == "28.9"


async def test_a_boiler_that_serves_only_part_of_its_block(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A controller that answers only some of a module's registers keeps those.

    The reported case: the boiler serves its temperatures but refuses the
    circulation registers at the end of its block. The probe reads the block a
    register at a time and builds the boiler from what answered, so the served
    temperatures — and the hot-water climate's controls — come through instead of
    the whole boiler going unavailable.
    """
    controller.refuse(2004)  # actual_circulation_temperature
    controller.refuse(2005)  # actual_circulation_pump_state
    entry = await setup_entry(hass, controller, legacy=True)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.counts["boil"] == 1
    # The served temperatures are read; the climate's current/target read these.
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") == "48.0"
    assert state_of(hass, "eu08l_boil1_target_high_temperature") == "52.0"
    # Only the refused registers are unavailable, and nothing else broke.
    assert state_of(hass, "eu08l_boil1_actual_circulation_temperature") in (
        "unknown",
        "unavailable",
    )
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_an_unserved_register_between_two_served_ones(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A hole in the middle of a block does not take the block down with it.

    Dropping the field is not enough: the registers on either side would still be
    read as one block, which spans the hole and is refused. The read has to be
    split at the hole, so both sides still come through.
    """
    controller.refuse(2002)  # actual_high_temperature, between 2001 and 2003
    entry = await setup_entry(hass, controller, legacy=True)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.last_update_success
    # Both sides of the hole are read.
    assert state_of(hass, "eu08l_boil1_operating_state") == "DHW"
    assert state_of(hass, "eu08l_boil1_actual_low_temperature") == "0.0"
    assert state_of(hass, "eu08l_boil1_target_high_temperature") == "52.0"
    # Only the hole itself is unavailable.
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") in (
        "unknown",
        "unavailable",
    )


async def test_a_heat_pump_without_the_undocumented_registers(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A firmware that lacks the refrigerant and capacity registers still sets up.

    They sit at the end of the heat pump's block and some firmware does not serve
    them; the probe leaves them out, and the documented values are unaffected.
    """
    for address in (*range(1024, 1034), *range(1051, 1061)):
        controller.refuse(address)
    entry = await setup_entry(hass, controller, legacy=True)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.last_update_success
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"
    # A refrigerant register the controller does not serve reads unavailable.
    assert state_of(hass, "eu08l_hp1_hot_gas_temperature") in ("unknown", "unavailable")
    # The one config register just before the capacity block is still served.
    assert state_of(hass, "eu08l_hp1_config_parameter_50") == "0"


async def test_a_controller_that_stores_its_counters_low_word_first(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A low-first controller decodes its counters, and still names its states.

    The low-first heat pump is a subclass that overrides only the two counters,
    so it is the case where a field is inherited rather than declared on the
    class being read — the state sensor has to find its labels all the same.
    """
    # The same 100000 Wh, stored low word first.
    controller.registers[1020] = 0x86A0
    controller.registers[1021] = 0x0001
    await setup_entry(
        hass,
        controller,
        legacy=True,
        options={CONF_INT32_REGISTER_ORDER: REGISTER_ORDER_LOW_FIRST},
    )

    assert (
        state_of(hass, "eu08l_hp1_compressor_power_consumption_accumulated") == "100000"
    )
    # The state registers are declared on the base class, not the override.
    assert state_of(hass, "eu08l_hp1_state") == "START COMPRESSOR"
    assert state_of(hass, "eu08l_hp1_operating_state") == "CH"


async def test_a_momentary_drop_is_reconnected_in_the_same_poll(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A blip costs nothing: the poll re-establishes the link and carries on."""
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.drop_the_link()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success
    assert entry.state is ConfigEntryState.LOADED
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_an_unreachable_controller_goes_unavailable_without_reloading(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A controller that cannot be reached marks its entities unavailable.

    Reloading would tear down every entity and re-probe the register map for
    what is usually a temporary outage. The coordinator keeps trying to
    reconnect on its own schedule instead, so the entities stay where they are.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, "eu08l_hp1_flow_line_temperature"
    )

    controller.go_offline()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # The device is down, but the entry was never reloaded.
    assert not coordinator.last_update_success
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id).state == "unavailable"

    # When it answers again the values come back — to the same entity, so
    # nothing was recreated and its history is intact.
    controller.come_back_online()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success
    assert hass.states.get(entity_id).state == "34.12"
    assert (
        registry.async_get_entity_id("sensor", DOMAIN, "eu08l_hp1_flow_line_temperature")
        == entity_id
    )


async def test_the_register_order_defaults_to_what_the_firmware_uses(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Without the setting, the counters are read the way that firmware writes them.

    V1.1.0-3K writes its 32-bit counters low word first, so a controller running
    it reads correctly with nothing configured.
    """
    controller.registers[1020] = 0x86A0  # the same 100000 Wh, low word first
    controller.registers[1021] = 0x0001
    data = entry_data(legacy=True) | {CONF_FIRMWARE_VERSION: "V1.1.0-3K"}
    entry = MockConfigEntry(domain=DOMAIN, version=ENTRY_VERSION, data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (
        state_of(hass, "eu08l_hp1_compressor_power_consumption_accumulated") == "100000"
    )


async def test_only_the_totals_are_enabled_by_default(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A fresh install ships the running totals; the per-period counters are off."""
    await setup_entry(hass, controller, legacy=True)
    registry = er.async_get(hass)

    def enabled(unique_id: str) -> bool:
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entity_id, unique_id
        return not registry.async_get(entity_id).disabled

    # The totals a user actually builds on — and feeds to the energy dashboard.
    assert enabled("eu08l_hp1_heating_cycling_total")
    assert enabled("eu08l_hp1_heating_energy_total")
    assert enabled("eu08l_hp1_heating_thermal_energy_total")
    assert enabled("eu08l_hp1_heating_cop_total")
    # The device's own lifetime register counters stay on too.
    assert enabled("eu08l_hp1_compressor_power_consumption_accumulated")

    # Everything reported over a period is created but disabled.
    for unique_id in (
        "eu08l_hp1_heating_cycling_daily",
        "eu08l_hp1_heating_cycling_2h",
        "eu08l_hp1_heating_cycling_yesterday",
        "eu08l_hp1_compressor_start_cycling_monthly",
        "eu08l_hp1_heating_energy_daily",
        "eu08l_hp1_heating_energy_hourly",
        "eu08l_hp1_heating_thermal_energy_yearly",
        "eu08l_hp1_heating_cop_daily",
    ):
        assert not enabled(unique_id), unique_id


async def test_a_float_unit_id_is_coerced_to_int(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An entry storing the port and unit id as floats still connects.

    The number selector that set them hands back floats, and older entries kept
    them; the Modbus frame needs ints, so the backend must be handed ints.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=ENTRY_VERSION,  # already migrated, so migration does not re-run
        data={
            CONF_NAME: "EU08L",
            CONF_HOST: HOST,
            CONF_PORT: 502.0,
            CONF_SLAVE_ID: 1.0,
            CONF_FIRMWARE_VERSION: "V0.0.8-3K",
            CONF_USE_LEGACY_MODBUS_NAMES: True,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    # Never a float — that is what tmodbus's struct.pack rejects.
    assert controller.ports and all(type(p) is int for p in controller.ports)
    assert controller.unit_ids and all(type(u) is int for u in controller.unit_ids)


async def test_a_busy_controller_is_not_read_as_a_smaller_one(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Being too busy to answer is not the same as having nothing to say.

    The module count is taken once and kept for the life of the entry, so a
    controller that is merely busy while it is being probed must not come up
    with modules missing. Setup fails instead, and Home Assistant retries it.
    """
    controller.answer_busy(2000)  # the boiler's own probe register
    entry = MockConfigEntry(domain=DOMAIN, version=ENTRY_VERSION, data=entry_data())
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_a_busy_controller_is_not_read_as_a_shorter_register_map(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The same, for the registers a module serves rather than the modules.

    The map is probed once. A busy answer recorded as "no such register" would
    leave those entities unavailable until someone reloaded the integration.
    """
    controller.answer_busy(1024)  # inside the heat pump's block, past the probe
    entry = MockConfigEntry(domain=DOMAIN, version=ENTRY_VERSION, data=entry_data())
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize(
    ("name", "unique_prefix", "id_prefix"),
    [
        ("EU08L", "eu08l", "eu08l"),
        # A name with spaces: the shape the entities were registered under drops
        # them, so the unique id has to as well or every entity is a new one.
        ("Lambda EU10L", "lambdaeu10l", "lambdaeu10l"),
        ("Meine WP", "meinewp", "meinewp"),
        # An accented name keeps its accents in the unique id, because that is
        # what the installation registered — but an entity id cannot have them.
        ("Wärmepumpe Süd", "wärmepumpesüd", "warmepumpesud"),
    ],
)
async def test_a_device_name_is_folded_the_way_it_always_was(
    hass: HomeAssistant,
    controller: Controller,
    name: str,
    unique_prefix: str,
    id_prefix: str,
) -> None:
    """The device name is free text, and both ids have to cope with it."""
    data = entry_data(legacy=True) | {CONF_NAME: name}
    entry = MockConfigEntry(domain=DOMAIN, version=ENTRY_VERSION, data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{unique_prefix}_hp1_flow_line_temperature"
    )
    assert entity_id == f"sensor.{id_prefix}_hp1_flow_line_temperature"
    assert valid_entity_id(entity_id)


async def test_the_lifetime_coefficient_is_still_there(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The controller's own lifetime COP, from its two accumulated counters.

    It is the one sensor the rewrite dropped; existing installations have it,
    with its history.
    """
    await setup_entry(hass, controller, legacy=True)

    # 400000 Wh of heat for 100000 Wh of electricity.
    assert state_of(hass, "eu08l_hp1_cop_calc") == "4.0"


async def test_a_link_that_stops_answering_is_thrown_away(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A link can be up and useless; after a few silent polls it is reopened.

    The socket stays open and the controller stops answering — the failure mode
    of the serial-to-network bridges these are often reached through. Reopening
    costs nothing: the same handles are used and nothing is rebuilt.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data
    connection = coordinator.connection

    controller.stop_answering()
    for _ in range(2):
        await coordinator.async_refresh()
    # Two silent polls are bad luck, not a wedged link.
    assert connection.connected
    assert not coordinator.last_update_success

    await coordinator.async_refresh()
    # The third throws the link away, to be reopened by the next request.
    assert not connection.connected

    controller.answer_again()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "34.12"


async def test_a_busy_answer_mid_poll_does_not_re_probe_the_controller(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Being busy is not the controller telling us it has changed.

    A block it will not serve any more means the map read at setup is stale, and
    the integration sets itself up again to find out what it has now. A block it
    cannot serve *at this moment* means nothing of the sort — re-probing on that
    would tear down every entity because the controller was briefly busy.
    """
    entry = await setup_entry(hass, controller, legacy=True)
    coordinator = entry.runtime_data

    controller.answer_busy(1004)  # inside a block the heat pump serves
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # The heat pump is the only module that could not be read; it is reported
    # rather than raised, so the rest of the controller carries on.
    assert set(coordinator.failed) == {"hp1"}
    assert "boil1" in coordinator.updated
    assert state_of(hass, "eu08l_hp1_flow_line_temperature") == "unavailable"
    assert state_of(hass, "eu08l_boil1_actual_high_temperature") == "48.0"
    # The entry was not reloaded: it is still the same coordinator.
    assert entry.runtime_data is coordinator
    assert entry.state is ConfigEntryState.LOADED
