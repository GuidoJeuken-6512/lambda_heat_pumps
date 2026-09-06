"""What the entities do: the heating curve, and the things that write back."""

from __future__ import annotations

import pytest
from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.lambda_heat_pumps.const import (
    CONF_ROOM_THERMOSTAT_CONTROL,
    DOMAIN,
)

from .conftest import Controller
from .test_init import setup_entry, state_of

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def entity_id(hass: HomeAssistant, platform: str, unique_id: str) -> str:
    """The entity Home Assistant gave this unique id."""
    found = er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
    assert found, f"no {platform} entity for {unique_id}"
    return found


async def test_the_heating_curve_is_read_off_the_points(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The flow temperature is interpolated from the curve at today's weather."""
    await setup_entry(hass, controller, legacy=True)

    # It is 3.8 °C outside. The curve runs 48.3 °C at -22, 39.0 at 0, 32.0 at +22,
    # so between 0 and +22 the flow falls by 7 °C over 22 — at 3.8 that is
    # 39.0 - 3.8/22 * 7 = 37.79 °C.
    assert state_of(hass, "eu08l_hc1_heating_curve_flow_line_temperature_calc") == "37.8"


async def test_moving_a_curve_point_moves_the_curve(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The number entities are what the curve is drawn through."""
    await setup_entry(hass, controller, legacy=True)
    number = entity_id(
        hass, NUMBER_DOMAIN, "eu08l_hc1_heating_curve_mid_outside_temp_number"
    )

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: number, ATTR_VALUE: 45.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    # The 0 °C point moved from 39.0 to 45.0, so at 3.8 °C outside the flow is
    # 45.0 - 3.8/22 * 13 = 42.75 °C.
    assert state_of(hass, "eu08l_hc1_heating_curve_flow_line_temperature_calc") == "42.8"


async def test_the_curve_follows_the_flow_line_offset(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The offset is a register: writing it moves the curve, and the controller."""
    await setup_entry(hass, controller, legacy=True)
    number = entity_id(
        hass, NUMBER_DOMAIN, "eu08l_hc1_flow_line_offset_temperature_number"
    )

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: number, ATTR_VALUE: 2.5},
        blocking=True,
    )
    await hass.async_block_till_done()

    # The controller now holds it, scaled by 0.1 as the register wants.
    assert controller.registers[5050] == 25
    assert hass.states.get(number).state == "2.5"
    # And the curve carries it: 37.79 + 2.5.
    assert state_of(hass, "eu08l_hc1_heating_curve_flow_line_temperature_calc") == "40.3"


async def test_a_room_thermostat_pushes_the_curve(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A room below its setpoint asks the circuit for a hotter flow."""
    await setup_entry(
        hass, controller, legacy=True, options={CONF_ROOM_THERMOSTAT_CONTROL: True}
    )

    # The room is at 21.5 °C and wants 21.0 — it is half a degree too warm, so
    # the curve is pulled down by (21.0 - 21.5) * 1.0 = -0.5.
    assert state_of(hass, "eu08l_hc1_heating_curve_flow_line_temperature_calc") == "37.3"


async def test_setting_the_hot_water_temperature(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The boiler's thermostat writes the register the controller aims at."""
    await setup_entry(hass, controller, legacy=True)
    climate = entity_id(hass, CLIMATE_DOMAIN, "eu08l_boil1_hot_water")

    assert hass.states.get(climate).attributes[ATTR_CURRENT_TEMPERATURE] == 48.0

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: climate, ATTR_TEMPERATURE: 55.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert controller.registers[2050] == 550
    assert hass.states.get(climate).attributes["temperature"] == 55.0


async def test_the_hot_water_climate_keeps_its_controls_when_part_is_refused(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The boiler refuses its circulation registers; the thermostat still works.

    This is the reported symptom: a controller that answers the boiler's
    temperatures but refuses the registers after them left the hot-water card
    showing only "Heat", with no current or target temperature. The probe keeps
    the served registers, so the climate reads both again.
    """
    controller.refuse(2004)  # actual_circulation_temperature
    controller.refuse(2005)  # actual_circulation_pump_state
    await setup_entry(hass, controller, legacy=True)
    climate = entity_id(hass, CLIMATE_DOMAIN, "eu08l_boil1_hot_water")

    state = hass.states.get(climate)
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 48.0
    assert state.attributes["temperature"] == 52.0

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: climate, ATTR_TEMPERATURE: 55.0},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert controller.registers[2050] == 550


async def test_a_circuit_only_becomes_a_thermostat_when_it_has_a_room(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Without a room sensor there is nothing for a heating-circuit climate to do."""
    await setup_entry(hass, controller, legacy=True)
    registry = er.async_get(hass)

    assert registry.async_get_entity_id(CLIMATE_DOMAIN, DOMAIN, "eu08l_boil1_hot_water")
    assert not registry.async_get_entity_id(
        CLIMATE_DOMAIN, DOMAIN, "eu08l_hc1_heating_circuit"
    )
