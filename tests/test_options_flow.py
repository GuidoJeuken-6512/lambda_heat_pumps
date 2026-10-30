"""The options flow: setpoint bounds, the optional features, and their sensors."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.lambda_heat_pumps.const import (
    CONF_COOLING_MODE,
    CONF_FIRMWARE_VERSION,
    CONF_HEATING_CIRCUIT_MAX_TEMP,
    CONF_HEATING_CIRCUIT_MIN_TEMP,
    CONF_HEATING_CIRCUIT_TEMP_STEP,
    CONF_HOT_WATER_MAX_TEMP,
    CONF_HOT_WATER_MIN_TEMP,
    CONF_INT32_REGISTER_ORDER,
    CONF_PERIOD_SENSORS_ENABLED,
    CONF_PV_POWER_SENSOR_ENTITY,
    CONF_PV_SURPLUS,
    CONF_PV_SURPLUS_MODE,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_INT32_REGISTER_ORDER,
    DEFAULT_PV_SURPLUS_MODE,
    REGISTER_ORDER_HIGH_FIRST,
    REGISTER_ORDER_LOW_FIRST,
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
        CONF_PERIOD_SENSORS_ENABLED: False,
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


def _default(result: dict, key: str):
    """The value the form offers for a field."""
    for marker in result["data_schema"].schema:
        if marker == key:
            return marker.default()
    raise KeyError(key)


@pytest.mark.parametrize(
    ("firmware", "expected"),
    [
        ("V1.1.0-3K", REGISTER_ORDER_LOW_FIRST),
        ("V1.0.4-3K", REGISTER_ORDER_LOW_FIRST),
        ("V0.0.10-3K", REGISTER_ORDER_LOW_FIRST),
        ("V0.0.8-3K", REGISTER_ORDER_HIGH_FIRST),
    ],
)
async def test_the_register_order_offered_is_the_firmwares_own(
    hass: HomeAssistant, controller: Controller, firmware: str, expected: str
) -> None:
    """With nothing set, saving the form as offered must not change the order (#133)."""
    entry = await setup_entry(hass, controller)
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_FIRMWARE_VERSION: firmware}
    )
    result = await _start(hass, entry)

    assert _default(result, CONF_INT32_REGISTER_ORDER) == expected


async def test_a_set_register_order_is_offered_as_set(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An order the user chose is what the form shows, whatever the firmware."""
    entry = await setup_entry(
        hass, controller, options={CONF_INT32_REGISTER_ORDER: REGISTER_ORDER_LOW_FIRST}
    )
    result = await _start(hass, entry)

    assert _default(result, CONF_INT32_REGISTER_ORDER) == REGISTER_ORDER_LOW_FIRST


async def test_the_2x_pv_mode_entry_is_offered_as_pos(
    hass: HomeAssistant, controller: Controller
) -> None:
    """2.x also had "entry"; 3.5 writes it like "pos", so the form offers that."""
    entry = await setup_entry(hass, controller, options={CONF_PV_SURPLUS_MODE: "entry"})
    result = await _start(hass, entry)

    assert _default(result, CONF_PV_SURPLUS_MODE) == "pos"


async def test_a_set_pv_mode_is_offered_as_set(
    hass: HomeAssistant, controller: Controller
) -> None:
    entry = await setup_entry(hass, controller, options={CONF_PV_SURPLUS_MODE: "neg"})
    result = await _start(hass, entry)

    assert _default(result, CONF_PV_SURPLUS_MODE) == "neg"


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
