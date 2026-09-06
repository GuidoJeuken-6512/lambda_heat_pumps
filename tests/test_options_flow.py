"""The options flow: setpoint bounds, the optional features, and their sensors."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.lambda_heat_pumps.const import (
    CONF_COOLING_MODE,
    CONF_HEATING_CIRCUIT_MAX_TEMP,
    CONF_HEATING_CIRCUIT_MIN_TEMP,
    CONF_HEATING_CIRCUIT_TEMP_STEP,
    CONF_HOT_WATER_MAX_TEMP,
    CONF_HOT_WATER_MIN_TEMP,
    CONF_INT32_REGISTER_ORDER,
    CONF_PV_POWER_SENSOR_ENTITY,
    CONF_PV_SURPLUS,
    CONF_PV_SURPLUS_MODE,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_INT32_REGISTER_ORDER,
    DEFAULT_PV_SURPLUS_MODE,
)

from .conftest import Controller
from .test_init import setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def _init_input(**overrides) -> dict:
    """A valid answer to the init step, with everything optional turned off."""
    values = {
        CONF_HOT_WATER_MIN_TEMP: 25.0,
        CONF_HOT_WATER_MAX_TEMP: 65.0,
        CONF_HEATING_CIRCUIT_MIN_TEMP: 15.0,
        CONF_HEATING_CIRCUIT_MAX_TEMP: 35.0,
        CONF_HEATING_CIRCUIT_TEMP_STEP: 0.5,
        CONF_UPDATE_INTERVAL: 30,
        CONF_INT32_REGISTER_ORDER: DEFAULT_INT32_REGISTER_ORDER,
        CONF_ROOM_THERMOSTAT_CONTROL: False,
        CONF_COOLING_MODE: False,
        CONF_PV_SURPLUS: False,
        CONF_PV_SURPLUS_MODE: DEFAULT_PV_SURPLUS_MODE,
    }
    values.update(overrides)
    return values


async def _start(hass: HomeAssistant, entry) -> dict:
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    return result


async def test_the_plain_options_are_saved_directly(
    hass: HomeAssistant, controller: Controller
) -> None:
    """With neither optional feature on, the flow ends after the one step."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], _init_input()
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_UPDATE_INTERVAL] == 30


async def test_a_hot_water_range_that_does_not_make_sense_is_refused(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A minimum at or above the maximum is rejected, not silently swapped."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        _init_input(**{CONF_HOT_WATER_MIN_TEMP: 65.0, CONF_HOT_WATER_MAX_TEMP: 65.0}),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOT_WATER_MIN_TEMP: "min_temp_higher"}


async def test_a_heating_circuit_range_that_does_not_make_sense_is_refused(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Same check, for the heating circuit's own bounds."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        _init_input(
            **{CONF_HEATING_CIRCUIT_MIN_TEMP: 35.0, CONF_HEATING_CIRCUIT_MAX_TEMP: 30.0}
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HEATING_CIRCUIT_MIN_TEMP: "min_temp_higher"}


async def test_room_thermostat_control_asks_for_a_room_sensor(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Turning it on adds a step asking which entity each circuit follows."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], _init_input(**{CONF_ROOM_THERMOSTAT_CONTROL: True})
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "room_sensors"
    # One heating circuit, one field to fill in.
    assert list(result["data_schema"].schema) == [
        CONF_ROOM_TEMPERATURE_ENTITY.format(1)
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ROOM_TEMPERATURE_ENTITY.format(1)] == "sensor.living_room"
    assert entry.options[CONF_ROOM_THERMOSTAT_CONTROL] is True


async def test_cooling_mode_alone_also_asks_for_a_room_sensor(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Cooling needs the room temperature too, without thermostat control."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], _init_input(**{CONF_COOLING_MODE: True})
    )

    assert result["step_id"] == "room_sensors"


async def test_pv_surplus_asks_for_a_power_sensor(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Turning PV surplus on, without room control, skips straight to it."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], _init_input(**{CONF_PV_SURPLUS: True})
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pv_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_PV_POWER_SENSOR_ENTITY: "sensor.pv_surplus"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PV_POWER_SENSOR_ENTITY] == "sensor.pv_surplus"


async def test_room_control_and_pv_surplus_ask_for_both_in_turn(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Both features on visits both extra steps, room sensors before PV."""
    entry = await setup_entry(hass, controller)
    result = await _start(hass, entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        _init_input(**{CONF_ROOM_THERMOSTAT_CONTROL: True, CONF_PV_SURPLUS: True}),
    )
    assert result["step_id"] == "room_sensors"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room"}
    )
    assert result["step_id"] == "pv_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_PV_POWER_SENSOR_ENTITY: "sensor.pv_surplus"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ROOM_TEMPERATURE_ENTITY.format(1)] == "sensor.living_room"
    assert entry.options[CONF_PV_POWER_SENSOR_ENTITY] == "sensor.pv_surplus"
