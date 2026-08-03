"""Config flow for the Lambda Heat Pumps integration.

The user is asked how to reach the controller, and nothing else. Which modules it
has is not a question they should have to answer — the controller is probed for
that on every setup.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from modbus_connection import ModbusError, ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from .const import (
    CONF_COOLING_MODE,
    CONF_FIRMWARE_VERSION,
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
    CONF_SLAVE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_USE_LEGACY_MODBUS_NAMES,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HOT_WATER_MIN_TEMP,
    DEFAULT_INT32_REGISTER_ORDER,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_PV_SURPLUS_MODE,
    DEFAULT_SLAVE_ID,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ENTRY_VERSION,
    FIRMWARE_VERSIONS,
    PV_SURPLUS_MODE_OPTIONS,
    REGISTER_ORDER_HIGH_FIRST,
    REGISTER_ORDER_LOW_FIRST,
)

# The MAC prefix Lambda controllers are shipped with.
DHCP_MACADDRESS = "0050F4*"

# Register 0 is the general error number: every controller answers it.
_PROBE_REGISTER = 0


def _number(minimum: float, maximum: float, step: float = 1) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum, max=maximum, step=step, mode=NumberSelectorMode.BOX
        )
    )


def _select(options: list[str]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
    )


CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): TextSelector(),
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT, default=DEFAULT_PORT): _number(1, 65535),
        vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): _number(1, 247),
        vol.Required(CONF_FIRMWARE_VERSION, default=FIRMWARE_VERSIONS[0]): _select(
            FIRMWARE_VERSIONS
        ),
    }
)


async def async_can_connect(data: dict[str, Any]) -> bool:
    """Whether the controller answers where the user says it is."""
    # Building the connection does no I/O; the read below is what reaches out.
    connection = ModbusConnection(
        ModbusTcpParams(host=data[CONF_HOST], port=int(data[CONF_PORT]))
    )
    try:
        unit = connection.for_unit(int(data[CONF_SLAVE_ID]))
        await unit.read_holding_registers(_PROBE_REGISTER, 1)
    except ModbusError:
        return False
    else:
        return True
    finally:
        await connection.close()


class LambdaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask the user how to reach the controller."""

    VERSION = ENTRY_VERSION

    def __init__(self) -> None:
        """Start with no discovered host."""
        self._discovered_host: str | None = None

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        """A controller announced itself on the network."""
        await self.async_set_unique_id(discovery_info.macaddress)
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        # An entry created before discovery set the unique id has no MAC to match
        # on, so fall back to the address — otherwise a controller that is already
        # set up keeps being offered as a new one.
        self._async_abort_entries_match({CONF_HOST: discovery_info.ip})
        self._discovered_host = discovery_info.ip
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the connection."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                **user_input,
                CONF_PORT: int(user_input[CONF_PORT]),
                CONF_SLAVE_ID: int(user_input[CONF_SLAVE_ID]),
                # Entries made from here on name their entities the way Home
                # Assistant does; only older ones carry the name prefix.
                CONF_USE_LEGACY_MODBUS_NAMES: False,
            }
            self._async_abort_entries_match(
                {
                    CONF_HOST: data[CONF_HOST],
                    CONF_PORT: data[CONF_PORT],
                    CONF_SLAVE_ID: data[CONF_SLAVE_ID],
                }
            )
            if await async_can_connect(data):
                return self.async_create_entry(title=data[CONF_NAME], data=data)
            errors["base"] = "cannot_connect"

        schema = self.add_suggested_values_to_schema(
            CONNECTION_SCHEMA,
            user_input or ({CONF_HOST: self._discovered_host} if self._discovered_host else {}),
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """The controller moved, or was given a different address."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                **entry.data,
                **user_input,
                CONF_PORT: int(user_input[CONF_PORT]),
                CONF_SLAVE_ID: int(user_input[CONF_SLAVE_ID]),
            }
            if await async_can_connect(data):
                return self.async_update_reload_and_abort(entry, data_updates=data)
            errors["base"] = "cannot_connect"

        schema = self.add_suggested_values_to_schema(
            CONNECTION_SCHEMA, user_input or entry.data
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        """Get the options flow."""
        return LambdaOptionsFlow()


class LambdaOptionsFlow(OptionsFlowWithReload):
    """Everything about the controller that is a preference, not a fact."""

    def __init__(self) -> None:
        """Collect the options across the steps."""
        self._options: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the setpoint bounds, the features, and the polling."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_HOT_WATER_MIN_TEMP] >= user_input[CONF_HOT_WATER_MAX_TEMP]:
                errors[CONF_HOT_WATER_MIN_TEMP] = "min_temp_higher"
            if (
                user_input[CONF_HEATING_CIRCUIT_MIN_TEMP]
                >= user_input[CONF_HEATING_CIRCUIT_MAX_TEMP]
            ):
                errors[CONF_HEATING_CIRCUIT_MIN_TEMP] = "min_temp_higher"
            if not errors:
                self._options = dict(user_input)
                if user_input[CONF_ROOM_THERMOSTAT_CONTROL] or user_input[
                    CONF_COOLING_MODE
                ]:
                    return await self.async_step_room_sensors()
                if user_input[CONF_PV_SURPLUS]:
                    return await self.async_step_pv_sensor()
                return self.async_create_entry(data=self._options)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOT_WATER_MIN_TEMP,
                    default=options.get(
                        CONF_HOT_WATER_MIN_TEMP, DEFAULT_HOT_WATER_MIN_TEMP
                    ),
                ): _number(25, 65),
                vol.Required(
                    CONF_HOT_WATER_MAX_TEMP,
                    default=options.get(
                        CONF_HOT_WATER_MAX_TEMP, DEFAULT_HOT_WATER_MAX_TEMP
                    ),
                ): _number(25, 65),
                vol.Required(
                    CONF_HEATING_CIRCUIT_MIN_TEMP,
                    default=options.get(
                        CONF_HEATING_CIRCUIT_MIN_TEMP,
                        DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
                    ),
                ): _number(10, 40),
                vol.Required(
                    CONF_HEATING_CIRCUIT_MAX_TEMP,
                    default=options.get(
                        CONF_HEATING_CIRCUIT_MAX_TEMP,
                        DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
                    ),
                ): _number(10, 40),
                vol.Required(
                    CONF_HEATING_CIRCUIT_TEMP_STEP,
                    default=options.get(
                        CONF_HEATING_CIRCUIT_TEMP_STEP,
                        DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
                    ),
                ): _number(0.1, 2.0, step=0.1),
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): _number(10, 300),
                vol.Required(
                    CONF_INT32_REGISTER_ORDER,
                    default=options.get(
                        CONF_INT32_REGISTER_ORDER, DEFAULT_INT32_REGISTER_ORDER
                    ),
                ): _select([REGISTER_ORDER_HIGH_FIRST, REGISTER_ORDER_LOW_FIRST]),
                vol.Required(
                    CONF_ROOM_THERMOSTAT_CONTROL,
                    default=options.get(CONF_ROOM_THERMOSTAT_CONTROL, False),
                ): BooleanSelector(),
                vol.Required(
                    CONF_COOLING_MODE,
                    default=options.get(CONF_COOLING_MODE, False),
                ): BooleanSelector(),
                vol.Required(
                    CONF_PV_SURPLUS, default=options.get(CONF_PV_SURPLUS, False)
                ): BooleanSelector(),
                vol.Required(
                    CONF_PV_SURPLUS_MODE,
                    default=options.get(
                        CONF_PV_SURPLUS_MODE, DEFAULT_PV_SURPLUS_MODE
                    ),
                ): _select(PV_SURPLUS_MODE_OPTIONS),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    async def async_step_room_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which entity knows the temperature in each circuit's room."""
        if user_input is not None:
            self._options.update(user_input)
            if self._options[CONF_PV_SURPLUS]:
                return await self.async_step_pv_sensor()
            return self.async_create_entry(data=self._options)

        options = self.config_entry.options
        temperature = EntitySelector(
            EntitySelectorConfig(domain="sensor", device_class="temperature")
        )
        schema = vol.Schema(
            {
                vol.Optional(
                    key,
                    description={"suggested_value": options.get(key)},
                ): temperature
                for index in range(1, self._num_heating_circuits() + 1)
                if (key := CONF_ROOM_TEMPERATURE_ENTITY.format(index))
            }
        )
        return self.async_show_form(step_id="room_sensors", data_schema=schema)

    async def async_step_pv_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which entity knows how much solar power is going spare."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(data=self._options)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PV_POWER_SENSOR_ENTITY,
                    description={
                        "suggested_value": self.config_entry.options.get(
                            CONF_PV_POWER_SENSOR_ENTITY
                        )
                    },
                ): EntitySelector(
                    EntitySelectorConfig(domain="sensor", device_class="power")
                )
            }
        )
        return self.async_show_form(step_id="pv_sensor", data_schema=schema)

    def _num_heating_circuits(self) -> int:
        """How many circuits the controller was found to have."""
        return self.config_entry.runtime_data.counts["hc"]
