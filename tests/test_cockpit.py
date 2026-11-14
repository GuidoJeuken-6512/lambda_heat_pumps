"""The Lambda Cockpit: its counters, sensors, settings, dashboard and repair."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant.common import async_fire_time_changed

from custom_components.lambda_heat_pumps.const import (
    CONF_DEFROST_ROOM_BOOST,
    CONF_INSTALL_DASHBOARD,
    DOMAIN,
    ISSUE_DASHBOARD_HEATING_CIRCUITS,
    ISSUE_DASHBOARD_RESTART,
)
from custom_components.lambda_heat_pumps.repairs import async_create_fix_flow
from custom_components.lambda_heat_pumps.sensor import _read_curve_backwards

from .conftest import Controller
from .test_init import setup_entry, state_of

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

_OPERATING_STATE = 1003
_HEATING, _HOT_WATER, _STANDBY, _DEFROST = 1, 2, 0, 5


async def _poll(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    """Let time pass and the fast poll run."""
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)


def _number_id(hass: HomeAssistant, unique_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("number", DOMAIN, unique_id)


# --------------------------------------------------------------------------
# Counters
# --------------------------------------------------------------------------


async def test_a_switch_from_heating_to_hot_water_is_counted(
    hass: HomeAssistant, controller: Controller, freezer: FrozenDateTimeFactory
) -> None:
    """Straight across, or through a short standby; a long pause is no switch."""
    controller.registers[_OPERATING_STATE] = _HEATING
    await setup_entry(hass, controller, legacy=True)
    key = "eu08l_hp1_heating_to_hot_water_cycling_total"
    assert state_of(hass, key) == "0"

    controller.registers[_OPERATING_STATE] = _HOT_WATER
    await _poll(hass, freezer, 3)
    assert state_of(hass, key) == "1"

    # Back to heating, a short standby, then hot water: still a switch.
    controller.registers[_OPERATING_STATE] = _HEATING
    await _poll(hass, freezer, 3)
    controller.registers[_OPERATING_STATE] = _STANDBY
    await _poll(hass, freezer, 3)
    controller.registers[_OPERATING_STATE] = _HOT_WATER
    await _poll(hass, freezer, 60)
    assert state_of(hass, key) == "2"

    # Heating, then a long standby before hot water: not a switch.
    controller.registers[_OPERATING_STATE] = _HEATING
    await _poll(hass, freezer, 3)
    controller.registers[_OPERATING_STATE] = _STANDBY
    await _poll(hass, freezer, 3)
    for _ in range(8):
        await _poll(hass, freezer, 120)
    controller.registers[_OPERATING_STATE] = _HOT_WATER
    await _poll(hass, freezer, 3)
    assert state_of(hass, key) == "2"


async def test_runtime_is_booked_against_the_mode(
    hass: HomeAssistant, controller: Controller, freezer: FrozenDateTimeFactory
) -> None:
    """Time in a mode adds up in hours; a gap with no answer adds nothing."""
    controller.registers[_OPERATING_STATE] = _HEATING
    await setup_entry(hass, controller, legacy=True)

    for _ in range(30):  # 30 polls of 2 minutes: an hour of heating
        await _poll(hass, freezer, 120)
    assert float(state_of(hass, "eu08l_hp1_heating_runtime_total")) == pytest.approx(1.0, abs=0.01)
    assert float(state_of(hass, "eu08l_hp1_hot_water_runtime_total")) == 0

    # Ten minutes without a look: too long to say what happened, so not booked.
    await _poll(hass, freezer, 600)
    assert float(state_of(hass, "eu08l_hp1_heating_runtime_total")) == pytest.approx(1.0, abs=0.01)


async def test_the_heating_rod_runtime_follows_its_relay(
    hass: HomeAssistant, controller: Controller, freezer: FrozenDateTimeFactory
) -> None:
    """The second heating stage counts while its relay is on."""
    controller.registers[1019] = 1  # 2nd heating stage on
    await setup_entry(hass, controller, legacy=True)

    for _ in range(15):
        await _poll(hass, freezer, 120)
    assert float(state_of(hass, "eu08l_hp1_heating_rod_runtime_total")) == pytest.approx(0.5, abs=0.01)


# --------------------------------------------------------------------------
# The heating schedule's outside temperature
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("flow", "outside"),
    [
        (39.0, 0.0),  # the middle point
        (48.3, -22.0),  # the cold point
        (32.0, 22.0),  # the warm point
        (35.5, 11.0),  # between middle and warm
        (50.0, -26.0),  # beyond the cold point, along the outer segment
    ],
)
def test_the_curve_reads_backwards(flow: float, outside: float) -> None:
    """The inverse of the curve, on the default points."""
    curve = [(-22.0, 48.3), (0.0, 39.0), (22.0, 32.0)]
    assert _read_curve_backwards(flow, curve) == pytest.approx(outside, abs=0.05)


def test_a_curve_that_does_not_fall_has_no_inverse() -> None:
    """Points mixed up by the user give no answer rather than a wrong one."""
    assert _read_curve_backwards(35.0, [(-22.0, 30.0), (0.0, 39.0), (22.0, 32.0)]) is None


async def test_the_schedule_outside_temperature_comes_from_the_setpoint(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The controller's flow setpoint, minus its offset, read off the curve."""
    controller.registers[5007] = 375  # flow setpoint 37.5 °C
    controller.registers[5050] = 20  # offset +2.0 K -> the curve gives 35.5 °C
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_hc1_schedule_outside_temperature_calc") == "11.0"


async def test_no_schedule_outside_temperature_without_a_request(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A circuit in standby reports a setpoint of 0; that reads back as nothing."""
    controller.registers[5007] = 0
    controller.registers[5050] = 10
    await setup_entry(hass, controller, legacy=True)

    assert state_of(hass, "eu08l_hc1_schedule_outside_temperature_calc") == "unknown"


# --------------------------------------------------------------------------
# Numbers
# --------------------------------------------------------------------------


async def test_the_room_setpoint_and_buffer_maximum_are_writable(
    hass: HomeAssistant, controller: Controller
) -> None:
    """5051 has a number of its own; one without a buffer has no 3050."""
    await setup_entry(hass, controller, legacy=True)

    entity_id = _number_id(hass, "eu08l_hc1_target_room_temperature_number")
    assert entity_id
    assert hass.states.get(entity_id).state == "21.0"
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 22.5}, blocking=True
    )
    assert controller.registers[5051] == 225
    # The fixture controller has no buffer.
    assert _number_id(hass, "eu08l_buff1_maximum_buffer_temp_number") is None


async def test_the_pv_increases_are_not_created_on_todays_firmware(
    hass: HomeAssistant, controller: Controller
) -> None:
    """No released firmware is known to have registers 2051/3051/5053."""
    await setup_entry(hass, controller, legacy=True)

    assert _number_id(hass, "eu08l_boil1_pv_temperature_increase_number") is None
    assert _number_id(hass, "eu08l_hc1_pv_temperature_increase_number") is None


async def test_the_cockpit_settings_come_with_the_dashboard(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The switching-point settings exist only with the dashboard installed."""
    await setup_entry(hass, controller, legacy=True)
    assert _number_id(hass, "eu08l_boil1_dhw_switch_on_hysteresis_number") is None

    hass.config_entries.async_entries(DOMAIN)[0]
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config_entries.async_update_entry(entry, options={CONF_INSTALL_DASHBOARD: True})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_id = _number_id(hass, "eu08l_boil1_dhw_switch_on_hysteresis_number")
    assert entity_id
    assert hass.states.get(entity_id).state == "-5.0"
    assert _number_id(hass, "eu08l_hc1_hc_temperature_spread_number")


# --------------------------------------------------------------------------
# Winter: room setpoint after defrosts
# --------------------------------------------------------------------------


async def test_defrosts_raise_the_room_setpoint_until_midnight(
    hass: HomeAssistant, controller: Controller, freezer: FrozenDateTimeFactory
) -> None:
    """The fourth defrost of a day raises it; midnight puts it back."""
    controller.registers[_OPERATING_STATE] = _HEATING
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_DEFROST_ROOM_BOOST: True}
    )

    for count in range(1, 5):
        controller.registers[_OPERATING_STATE] = _DEFROST
        await _poll(hass, freezer, 3)
        controller.registers[_OPERATING_STATE] = _HEATING
        await _poll(hass, freezer, 3)
        if count < 4:
            assert controller.registers[5051] == 210
    assert controller.registers[5051] == 220  # raised to 22.0 °C

    # A fifth defrost writes nothing again.
    controller.registers[5051] = 215
    controller.registers[_OPERATING_STATE] = _DEFROST
    await _poll(hass, freezer, 3)
    assert controller.registers[5051] == 215

    entry.runtime_data._rollover(datetime(2026, 11, 5, 0, 0))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert controller.registers[5051] == 210  # back to 21.0 °C
    assert entry.runtime_data.defrosts_today == 0


async def test_defrosts_change_nothing_without_the_option(
    hass: HomeAssistant, controller: Controller, freezer: FrozenDateTimeFactory
) -> None:
    """Off by default."""
    await setup_entry(hass, controller, legacy=True)
    for _ in range(5):
        controller.registers[_OPERATING_STATE] = _DEFROST
        await _poll(hass, freezer, 3)
        controller.registers[_OPERATING_STATE] = _HEATING
        await _poll(hass, freezer, 3)
    assert controller.registers[5051] == 210


# --------------------------------------------------------------------------
# Dashboard and repair
# --------------------------------------------------------------------------


async def test_the_dashboard_is_written_with_the_option(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """Its config and its entry in the dashboard list, plus the restart repair."""
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    config = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]
    card = config["views"][0]["cards"][0]
    assert card["type"] == "custom:lambda-cockpit-card"
    assert card["entities"]["vl"] == "sensor.eu08l_hp1_flow_line_temperature"
    assert card["entities"]["offset"] == "number.eu08l_hc1_flow_line_offset_temperature_number"
    # Only functions that exist; nothing for unreleased firmware.
    assert card["features"] == {"room_thermostat": False, "pv_surplus": False}
    assert config["views"][1]["cards"][0]["type"] == "custom:lambda-entities-card"
    # One heating circuit: no tabs, no further tiles, the cockpit's icon as before.
    assert "heating_circuits" not in card
    assert config["views"][0]["icon"] == "mdi:heat-pump"

    items = hass_storage["lovelace_dashboards"]["data"]["items"]
    assert [item["url_path"] for item in items] == ["lambda-cockpit"]
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_DASHBOARD_RESTART)

    # The per-day counters the cockpit shows are switched on.
    registry = er.async_get(hass)
    for slot in ("strom_hz", "starts_vd"):
        daily = registry.async_get(card["entities"][slot])
        assert daily is not None and daily.disabled_by is None
    assert card["entities"]["starts_vd"] == "sensor.eu08l_hp1_compressor_start_cycling_daily"

    # Not written again on a reload.
    del hass_storage["lovelace.lambda_cockpit"]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "lovelace.lambda_cockpit" not in hass_storage


async def test_a_cockpit_from_an_older_version_gets_the_compressor_starts(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """A dashboard written before the slot existed is kept; the counter is switched on."""
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    config = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]
    card = config["views"][0]["cards"][0]
    entity_id = card["entities"].pop("starts_vd")

    # As in 3.7.0: the counter was created switched off by the integration.
    registry = er.async_get(hass)
    registry.async_update_entity(
        entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    # The dashboard is not rewritten (the card finds the slot itself) ...
    card = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"][0]["cards"][0]
    assert "starts_vd" not in card["entities"]
    # ... and the counter it shows is on.
    assert registry.async_get(entity_id).disabled_by is None


async def test_the_dashboard_finds_renamed_entities(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """The entity ids come from the registry, not from the device name."""
    await setup_entry(hass, controller, legacy=True)
    registry = er.async_get(hass)
    old = registry.async_get_entity_id("sensor", DOMAIN, "eu08l_hp1_flow_line_temperature")
    registry.async_update_entity(old, new_entity_id="sensor.my_flow")

    await hass.services.async_call(DOMAIN, "generate_dashboard", blocking=True)

    card = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"][0]["cards"][0]
    assert card["entities"]["vl"] == "sensor.my_flow"


async def test_no_dashboard_without_the_option(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """Off by default."""
    await setup_entry(hass, controller, legacy=True)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "lovelace.lambda_cockpit" not in hass_storage
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_DASHBOARD_RESTART) is None


async def test_the_repair_restarts_home_assistant(hass: HomeAssistant) -> None:
    """Confirming the repair calls the restart service."""
    restart = AsyncMock()

    async def _restart(call: ServiceCall) -> None:
        await restart(call)

    hass.services.async_register("homeassistant", "restart", _restart)
    flow = await async_create_fix_flow(hass, ISSUE_DASHBOARD_RESTART, None)
    flow.hass = hass

    result = await flow.async_step_init()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    restart.assert_not_called()

    result = await flow.async_step_confirm({})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    restart.assert_awaited_once()


async def test_switching_the_option_off_removes_the_dashboard(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """The dashboard, its settings and the pending restart repair all go."""
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "lovelace.lambda_cockpit" in hass_storage
    assert _number_id(hass, "eu08l_boil1_dhw_switch_on_hysteresis_number")

    hass.config_entries.async_update_entry(entry, options={CONF_INSTALL_DASHBOARD: False})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "lovelace.lambda_cockpit" not in hass_storage
    assert hass_storage["lovelace_dashboards"]["data"]["items"] == []
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_DASHBOARD_RESTART) is None
    assert _number_id(hass, "eu08l_boil1_dhw_switch_on_hysteresis_number") is None

    # Switched on again, it is written again.
    hass.config_entries.async_update_entry(entry, options={CONF_INSTALL_DASHBOARD: True})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "lovelace.lambda_cockpit" in hass_storage


async def test_an_entry_that_no_longer_exists_does_not_keep_the_dashboard(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """A controller deleted earlier left its mark; switching off still removes it."""
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    # What a deleted and newly set up integration leaves behind.
    hass_storage["lambda_heat_pumps.dashboard"]["data"]["deleted_entry_id"] = 1

    hass.config_entries.async_update_entry(entry, options={CONF_INSTALL_DASHBOARD: False})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "lovelace.lambda_cockpit" not in hass_storage
    assert hass_storage["lovelace_dashboards"]["data"]["items"] == []
    assert hass_storage["lambda_heat_pumps.dashboard"]["data"] == {}


async def test_a_dashboard_the_integration_did_not_write_is_left_alone(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """With the option never on, nothing is removed."""
    hass_storage["lovelace_dashboards"] = {
        "version": 1,
        "minor_version": 1,
        "key": "lovelace_dashboards",
        "data": {"items": [{"id": "lambda_cockpit", "url_path": "lambda-cockpit"}]},
    }
    await setup_entry(hass, controller, legacy=True)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass_storage["lovelace_dashboards"]["data"]["items"]


# --------------------------------------------------------------------------
# Further heating circuits
# --------------------------------------------------------------------------


async def test_a_second_heating_circuit_gets_its_own_card(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """Several circuits: a tile each in the cockpit, and a tab each with the details."""
    controller.install(5100)  # heating circuit 2
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    circuits = entry.runtime_data.counts["hc"]
    assert circuits >= 2

    views = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"]
    assert [view["path"] for view in views] == [
        "cockpit",
        *(f"heating-circuit-{circuit}" for circuit in range(1, circuits + 1)),
        "lambda-cockpit-entities",
    ]
    # Tabs with titles, not bare icons, so they are found.
    assert all(view.get("icon") is None for view in views[: circuits + 1])

    # The cockpit keeps circuit 1 and gets a tile for each further one.
    cockpit = views[0]["cards"][0]
    assert cockpit["entities"]["hc_vl"] == "sensor.eu08l_hc1_flow_line_temperature"
    assert [c["circuit"] for c in cockpit["heating_circuits"]] == list(range(2, circuits + 1))
    extra = cockpit["heating_circuits"][0]["entities"]
    assert extra["hc_vl"] == "sensor.eu08l_hc2_flow_line_temperature"
    assert "vl" not in extra

    # One tab per circuit, each with the circuit's own card.
    for index, circuit in ((1, 1), (2, 2)):
        card = views[index]["cards"][0]
        assert card["type"] == "custom:lambda-heating-circuit-card"
        assert card["circuit"] == circuit
        assert card["entities"]["hc_vl"] == f"sensor.eu08l_hc{circuit}_flow_line_temperature"
        assert card["entities"]["offset"] == (
            f"number.eu08l_hc{circuit}_flow_line_offset_temperature_number"
        )
    # Nothing to offer: the new cockpit already has them.
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_DASHBOARD_HEATING_CIRCUITS) is None


async def test_an_existing_cockpit_is_only_rewritten_after_asking(
    hass: HomeAssistant, controller: Controller, hass_storage: dict
) -> None:
    """A cockpit written with one circuit gets a repair, not a silent rewrite."""
    entry = await setup_entry(
        hass, controller, legacy=True, options={CONF_INSTALL_DASHBOARD: True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, ISSUE_DASHBOARD_HEATING_CIRCUITS) is None
    assert len(hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"]) == 2

    # A second circuit turns up: the user is asked, the dashboard stays as it is.
    controller.install(5100)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    issue = issues.async_get_issue(DOMAIN, ISSUE_DASHBOARD_HEATING_CIRCUITS)
    assert issue is not None and issue.is_fixable
    assert len(hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"]) == 2

    flow = await async_create_fix_flow(hass, ISSUE_DASHBOARD_HEATING_CIRCUITS, issue.data)
    flow.hass = hass
    result = await flow.async_step_init()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await flow.async_step_confirm({})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done(wait_background_tasks=True)
    views = hass_storage["lovelace.lambda_cockpit"]["data"]["config"]["views"]
    assert [view["path"] for view in views][1:3] == ["heating-circuit-1", "heating-circuit-2"]
    assert views[0].get("icon") is None
    assert views[0]["cards"][0]["heating_circuits"][0]["circuit"] == 2
    assert issues.async_get_issue(DOMAIN, ISSUE_DASHBOARD_HEATING_CIRCUITS) is None

    # Asked once: a reload does not ask again.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert issues.async_get_issue(DOMAIN, ISSUE_DASHBOARD_HEATING_CIRCUITS) is None

