"""The services: room temperature, PV surplus, and raw register access.

Two of these run on a timer for as long as a feature stays on (see
`async_setup_writers`); the register services take no target and so only make
sense while there is exactly one controller.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.util import dt as dt_util
import pytest
from modbus_connection import ModbusTimeoutError
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.lambda_heat_pumps.const import (
    CONF_PV_POWER_SENSOR_ENTITY,
    CONF_PV_SURPLUS,
    CONF_PV_SURPLUS_MODE,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CONF_WRITE_INTERVAL,
    DOMAIN,
)
from custom_components.lambda_heat_pumps.services import (
    ATTR_REGISTER_ADDRESS,
    ATTR_VALUE,
    SERVICE_READ_MODBUS_REGISTER,
    SERVICE_UPDATE_ROOM_TEMPERATURE,
    SERVICE_WRITE_MODBUS_REGISTER,
)

from .conftest import Controller
from .test_init import setup_entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

# Heating circuit 1's room-device-temperature register (5000 + 4).
ROOM_TEMPERATURE_REGISTER = 5004
# The register both the PV-surplus write and the e-manager power reading share.
PV_SURPLUS_REGISTER = 102


async def _update_room_temperature(hass: HomeAssistant) -> None:
    await hass.services.async_call(
        DOMAIN, SERVICE_UPDATE_ROOM_TEMPERATURE, {}, blocking=True
    )


async def test_room_temperature_is_sent_to_the_configured_circuit(
    hass: HomeAssistant, controller: Controller
) -> None:
    """The circuit's room-device-temperature register follows the sensor."""
    hass.states.async_set("sensor.living_room", "22.5")
    await setup_entry(
        hass,
        controller,
        options={
            CONF_ROOM_THERMOSTAT_CONTROL: True,
            CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room",
        },
    )

    await _update_room_temperature(hass)

    assert controller.registers[ROOM_TEMPERATURE_REGISTER] == 225


async def test_room_temperature_is_not_sent_when_the_feature_is_off(
    hass: HomeAssistant, controller: Controller
) -> None:
    """No option, no write — the register keeps what the controller had."""
    hass.states.async_set("sensor.living_room", "22.5")
    await setup_entry(
        hass,
        controller,
        options={CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room"},
    )

    await _update_room_temperature(hass)

    assert controller.registers[ROOM_TEMPERATURE_REGISTER] == 215


async def test_a_sensor_with_no_number_is_not_sent(
    hass: HomeAssistant, controller: Controller
) -> None:
    """An unavailable room sensor is not turned into a bogus temperature."""
    hass.states.async_set("sensor.living_room", "unavailable")
    await setup_entry(
        hass,
        controller,
        options={
            CONF_ROOM_THERMOSTAT_CONTROL: True,
            CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room",
        },
    )

    await _update_room_temperature(hass)

    assert controller.registers[ROOM_TEMPERATURE_REGISTER] == 215


async def test_a_refused_write_is_logged_not_raised(
    hass: HomeAssistant, controller: Controller, caplog: pytest.LogCaptureFixture
) -> None:
    """The controller refusing one circuit's write does not fail the service."""
    hass.states.async_set("sensor.living_room", "22.5")
    entry = await setup_entry(
        hass,
        controller,
        options={
            CONF_ROOM_THERMOSTAT_CONTROL: True,
            CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room",
        },
    )
    entry.runtime_data.unit.fail_write(
        ROOM_TEMPERATURE_REGISTER, ModbusTimeoutError("no answer")
    )

    await _update_room_temperature(hass)

    assert controller.registers[ROOM_TEMPERATURE_REGISTER] == 215
    assert "Could not send the room temperature" in caplog.text


async def test_pv_surplus_is_sent_in_watts(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A surplus reported in kW is converted to the watts the register wants."""
    hass.states.async_set(
        "sensor.pv_surplus", "1.5", {"unit_of_measurement": "kW"}
    )
    entry = await setup_entry(
        hass,
        controller,
        options={
            CONF_PV_SURPLUS: True,
            CONF_PV_POWER_SENSOR_ENTITY: "sensor.pv_surplus",
        },
    )

    from custom_components.lambda_heat_pumps.services import async_write_pv_surplus

    await async_write_pv_surplus(entry.runtime_data)

    assert controller.registers[PV_SURPLUS_REGISTER] == 1500


async def test_pv_surplus_negative_mode_encodes_a_shortfall(
    hass: HomeAssistant, controller: Controller
) -> None:
    """In 'neg' mode a shortfall is sent as a negative register, not clamped to 0."""
    hass.states.async_set("sensor.pv_surplus", "-500")
    entry = await setup_entry(
        hass,
        controller,
        options={
            CONF_PV_SURPLUS: True,
            CONF_PV_POWER_SENSOR_ENTITY: "sensor.pv_surplus",
            CONF_PV_SURPLUS_MODE: "neg",
        },
    )

    from custom_components.lambda_heat_pumps.services import async_write_pv_surplus

    await async_write_pv_surplus(entry.runtime_data)

    # -500 as an unsigned 16-bit register: two's complement of 500.
    assert controller.registers[PV_SURPLUS_REGISTER] == (-500 & 0xFFFF)


async def test_pv_surplus_positive_mode_clamps_a_shortfall_to_zero(
    hass: HomeAssistant, controller: Controller
) -> None:
    """In the default 'pos' mode a shortfall cannot be expressed, so it is 0."""
    hass.states.async_set("sensor.pv_surplus", "-500")
    entry = await setup_entry(
        hass,
        controller,
        options={
            CONF_PV_SURPLUS: True,
            CONF_PV_POWER_SENSOR_ENTITY: "sensor.pv_surplus",
        },
    )

    from custom_components.lambda_heat_pumps.services import async_write_pv_surplus

    await async_write_pv_surplus(entry.runtime_data)

    assert controller.registers[PV_SURPLUS_REGISTER] == 0


async def test_the_writers_run_on_their_own_timer(
    hass: HomeAssistant, controller: Controller
) -> None:
    """Room temperature and PV surplus are re-sent for as long as the feature is on."""
    hass.states.async_set("sensor.living_room", "19.0")
    await setup_entry(
        hass,
        controller,
        options={
            CONF_ROOM_THERMOSTAT_CONTROL: True,
            CONF_ROOM_TEMPERATURE_ENTITY.format(1): "sensor.living_room",
            CONF_WRITE_INTERVAL: 5,
        },
    )
    # The initial write interval fires on setup already; change the value and
    # confirm the timer, not the service call, is what sends it again.
    controller.registers[ROOM_TEMPERATURE_REGISTER] = 0
    hass.states.async_set("sensor.living_room", "23.0")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()

    assert controller.registers[ROOM_TEMPERATURE_REGISTER] == 230


async def test_no_writer_timer_when_neither_feature_is_on(
    hass: HomeAssistant, controller: Controller
) -> None:
    """No room control and no PV surplus means nothing is scheduled at all."""
    with patch(
        "custom_components.lambda_heat_pumps.services.async_track_time_interval"
    ) as track_time_interval:
        await setup_entry(hass, controller)

    track_time_interval.assert_not_called()


async def test_reading_a_register(hass: HomeAssistant, controller: Controller) -> None:
    """The raw register service reads back what is on the controller."""
    await setup_entry(hass, controller)

    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_READ_MODBUS_REGISTER,
        {ATTR_REGISTER_ADDRESS: 1013},
        blocking=True,
        return_response=True,
    )

    assert result == {"value": 431}


async def test_writing_a_register(hass: HomeAssistant, controller: Controller) -> None:
    """The raw register service writes exactly the value it was given."""
    await setup_entry(hass, controller)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_WRITE_MODBUS_REGISTER,
        {ATTR_REGISTER_ADDRESS: 5051, ATTR_VALUE: 225},
        blocking=True,
    )

    assert controller.registers[5051] == 225


async def test_writing_a_negative_value_wraps_to_16_bits(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A negative value is sent as the two's-complement word the wire expects."""
    await setup_entry(hass, controller)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_WRITE_MODBUS_REGISTER,
        {ATTR_REGISTER_ADDRESS: 5051, ATTR_VALUE: -10},
        blocking=True,
    )

    assert controller.registers[5051] == (-10 & 0xFFFF)


async def test_a_read_error_becomes_a_home_assistant_error(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A refused read is surfaced as a service error, not swallowed."""
    entry = await setup_entry(hass, controller)
    entry.runtime_data.unit.fail_read(1013, ModbusTimeoutError("no answer"))

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_READ_MODBUS_REGISTER,
            {ATTR_REGISTER_ADDRESS: 1013},
            blocking=True,
            return_response=True,
        )


async def test_a_write_error_becomes_a_home_assistant_error(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A refused write is surfaced as a service error, not swallowed."""
    entry = await setup_entry(hass, controller)
    entry.runtime_data.unit.fail_write(5051, ModbusTimeoutError("no answer"))

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_WRITE_MODBUS_REGISTER,
            {ATTR_REGISTER_ADDRESS: 5051, ATTR_VALUE: 1},
            blocking=True,
        )


async def test_the_register_services_refuse_without_a_controller(
    hass: HomeAssistant,
) -> None:
    """Nothing is set up, so there is no controller a register could belong to."""
    from custom_components.lambda_heat_pumps.services import async_setup_services

    async_setup_services(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_READ_MODBUS_REGISTER,
            {ATTR_REGISTER_ADDRESS: 0},
            blocking=True,
            return_response=True,
        )


async def test_the_register_services_refuse_with_two_controllers(
    hass: HomeAssistant, controller: Controller
) -> None:
    """A register address means nothing without knowing which controller it is on."""
    await setup_entry(hass, controller)
    await setup_entry(hass, controller)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_READ_MODBUS_REGISTER,
            {ATTR_REGISTER_ADDRESS: 0},
            blocking=True,
            return_response=True,
        )
