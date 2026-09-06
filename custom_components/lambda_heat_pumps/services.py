"""Services for the Lambda Heat Pumps integration.

Two things the controller acts on cannot be measured by it: the temperature in
the room, which some other thermostat entity knows, and how much solar power is
going spare, which the inverter knows. Both are handed to it by writing a
register — on a timer for as long as the feature is on, because the controller
only keeps acting on a value while it keeps arriving.

The other two services read and write a register by address, for working out what
an undocumented one does.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_track_time_interval
from modbus_connection import ModbusError

from .const import (
    CONF_PV_POWER_SENSOR_ENTITY,
    CONF_PV_SURPLUS,
    CONF_PV_SURPLUS_MODE,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CONF_WRITE_INTERVAL,
    DEFAULT_PV_SURPLUS_MODE,
    DEFAULT_WRITE_INTERVAL,
    DOMAIN,
)
from .coordinator import LambdaCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_UPDATE_ROOM_TEMPERATURE = "update_room_temperature"
SERVICE_READ_MODBUS_REGISTER = "read_modbus_register"
SERVICE_WRITE_MODBUS_REGISTER = "write_modbus_register"

ATTR_REGISTER_ADDRESS = "register_address"
ATTR_VALUE = "value"

# The register the controller reads a PV surplus from.
PV_SURPLUS_REGISTER = 102

# The field a heating circuit reads its room temperature from.
ROOM_TEMPERATURE_FIELD = "room_device_temperature"

_REGISTER_SCHEMA = vol.Schema(
    {vol.Required(ATTR_REGISTER_ADDRESS): vol.All(int, vol.Range(min=0, max=65535))}
)
_WRITE_SCHEMA = _REGISTER_SCHEMA.extend(
    {vol.Required(ATTR_VALUE): vol.All(int, vol.Range(min=-32768, max=65535))}
)


def _controllers(hass: HomeAssistant) -> list[LambdaCoordinator]:
    """Every Lambda controller that is currently set up."""
    return [
        entry.runtime_data
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
    ]


def _number(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """A number off another entity, or None if it has nothing to say."""
    if not entity_id or (state := hass.states.get(entity_id)) is None:
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


async def async_write_room_temperatures(coordinator: LambdaCoordinator) -> None:
    """Feed each circuit the room temperature it is configured to follow."""
    options = coordinator.config_entry.options
    if not options.get(CONF_ROOM_THERMOSTAT_CONTROL, False):
        return

    for index in range(1, coordinator.counts["hc"] + 1):
        entity_id = options.get(CONF_ROOM_TEMPERATURE_ENTITY.format(index))
        temperature = _number(coordinator.hass, entity_id)
        if temperature is None:
            continue
        try:
            await coordinator.component("hc", index).write(
                ROOM_TEMPERATURE_FIELD, temperature
            )
        except ModbusError as err:
            _LOGGER.warning(
                "Could not send the room temperature to circuit %d: %s", index, err
            )


async def async_write_pv_surplus(coordinator: LambdaCoordinator) -> None:
    """Tell the controller how much solar power is going spare."""
    hass = coordinator.hass
    options = coordinator.config_entry.options
    if not options.get(CONF_PV_SURPLUS, False):
        return

    entity_id = options.get(CONF_PV_POWER_SENSOR_ENTITY)
    power = _number(hass, entity_id)
    if power is None:
        return
    state = hass.states.get(entity_id)
    if state is not None and state.attributes.get("unit_of_measurement") == "kW":
        power *= 1000

    if options.get(CONF_PV_SURPLUS_MODE, DEFAULT_PV_SURPLUS_MODE) == "neg":
        # The controller reads this register as signed, so a shortfall can be
        # sent as well as a surplus.
        raw = max(-32768, min(32767, int(power))) & 0xFFFF
    else:
        raw = max(0, min(65535, int(power)))

    try:
        await coordinator.unit.write_register(PV_SURPLUS_REGISTER, raw)
    except ModbusError as err:
        _LOGGER.warning("Could not send the PV surplus: %s", err)


def _only_controller(hass: HomeAssistant) -> LambdaCoordinator:
    """The one controller the register services address.

    A register address means nothing without a controller to read it on, and
    these services take no target — so they only work while there is no question
    about which controller is meant.
    """
    controllers = _controllers(hass)
    if not controllers:
        raise ServiceValidationError("No Lambda controller is set up")
    if len(controllers) > 1:
        raise ServiceValidationError(
            "More than one Lambda controller is set up, so there is no telling "
            "which one this register belongs to"
        )
    return controllers[0]


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the services, which are shared by every configured controller."""
    if hass.services.has_service(DOMAIN, SERVICE_READ_MODBUS_REGISTER):
        return

    async def _update_room_temperature(call: ServiceCall) -> None:
        """Send every controller the room temperatures it is configured for."""
        for coordinator in _controllers(hass):
            await async_write_room_temperatures(coordinator)

    async def _read_register(call: ServiceCall) -> ServiceResponse:
        """Read one register, by address."""
        coordinator = _only_controller(hass)
        address = call.data[ATTR_REGISTER_ADDRESS]
        try:
            registers = await coordinator.unit.read_holding_registers(address, 1)
        except ModbusError as err:
            raise HomeAssistantError(
                f"Could not read register {address}: {err}"
            ) from err
        return {"value": registers[0]}

    async def _write_register(call: ServiceCall) -> None:
        """Write one register, by address."""
        coordinator = _only_controller(hass)
        address = call.data[ATTR_REGISTER_ADDRESS]
        try:
            await coordinator.unit.write_register(
                address, call.data[ATTR_VALUE] & 0xFFFF
            )
        except ModbusError as err:
            raise HomeAssistantError(
                f"Could not write register {address}: {err}"
            ) from err

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_ROOM_TEMPERATURE, _update_room_temperature
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_MODBUS_REGISTER,
        _read_register,
        schema=_REGISTER_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_WRITE_MODBUS_REGISTER, _write_register, schema=_WRITE_SCHEMA
    )


def async_setup_writers(coordinator: LambdaCoordinator) -> None:
    """Keep sending the values the controller only acts on while they arrive."""
    entry = coordinator.config_entry
    options = entry.options
    if not (
        options.get(CONF_ROOM_THERMOSTAT_CONTROL, False)
        or options.get(CONF_PV_SURPLUS, False)
    ):
        return

    async def _write(_now: datetime) -> None:
        await async_write_room_temperatures(coordinator)
        await async_write_pv_surplus(coordinator)

    entry.async_on_unload(
        async_track_time_interval(
            coordinator.hass,
            _write,
            timedelta(
                seconds=options.get(CONF_WRITE_INTERVAL, DEFAULT_WRITE_INTERVAL)
            ),
        )
    )
