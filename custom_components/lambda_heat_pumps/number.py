"""Number platform for the Lambda Heat Pumps integration.

Two kinds of number.

**Settings** are not registers at all. The three points of the heating curve,
the eco reduction and how hard a circuit chases a room thermostat are what the
integration computes the curve from. The cockpit's switching points (hysteresis,
spread, heating limit, …) and the winter defrost boost are copies of controller
settings Modbus does not expose, which the user enters once from the display.
The controller knows nothing about any of them. They are kept by the entity,
restored across restarts, and published to the coordinator for the sensors and
the cockpit to read.

**Register numbers** write a register on the controller, and read it back like
any other value: the flow-line offset, the room setpoint, the buffer's maximum
temperature, and the PV temperature increases where the firmware has them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from modbus_connection import ModbusError

from .const import (
    CONF_DEFROST_ROOM_BOOST,
    CONF_HEATING_CIRCUIT_MAX_TEMP,
    CONF_HEATING_CIRCUIT_MIN_TEMP,
    CONF_INSTALL_DASHBOARD,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CURVE_FLOW_MAX,
    CURVE_FLOW_MIN,
    CURVE_POINTS,
    DEFAULT_DEFROST_BOOST_COUNT,
    DEFAULT_DEFROST_BOOST_ROOM_TEMP,
    DEFAULT_DEFROST_NORMAL_ROOM_TEMP,
    DEFAULT_ECO_TEMP_REDUCTION,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_ROOM_THERMOSTAT_FACTOR,
    DEFAULT_ROOM_THERMOSTAT_OFFSET,
    ECO_TEMP_REDUCTION_MAX,
    ECO_TEMP_REDUCTION_MIN,
    FLOW_LINE_OFFSET_MAX,
    FLOW_LINE_OFFSET_MIN,
    PV_OFFSET_FIRMWARE_VERSIONS,
)
from .coordinator import LambdaConfigEntry, LambdaCoordinator
from .entity import LambdaEntity
from .firmware import firmware_level, parse_firmware_versions

_KELVIN = "K"


@dataclass(frozen=True, kw_only=True)
class LambdaSettingDescription(NumberEntityDescription):
    """A value the user sets that the controller never sees."""

    default: float
    # The module whose device the setting belongs to.
    module: str = "hc"


def _temperature_setting(
    key: str,
    default: float,
    minimum: float,
    maximum: float,
    *,
    module: str = "hc",
    step: float = 0.1,
) -> LambdaSettingDescription:
    return LambdaSettingDescription(
        key=key,
        default=default,
        module=module,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=step,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.BOX,
    )


def _difference_setting(
    key: str, default: float, minimum: float, maximum: float, *, module: str
) -> LambdaSettingDescription:
    """A temperature difference, in kelvin.

    Not a temperature device class: Home Assistant would convert kelvin as an
    absolute temperature.
    """
    return LambdaSettingDescription(
        key=key,
        default=default,
        module=module,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=0.5,
        native_unit_of_measurement=_KELVIN,
        mode=NumberMode.BOX,
    )


def _config(description: LambdaSettingDescription) -> LambdaSettingDescription:
    return replace(description, entity_category=EntityCategory.CONFIG)


# The three points of the heating curve, plus the eco reduction.
CURVE_SETTINGS: tuple[LambdaSettingDescription, ...] = (
    *(
        _temperature_setting(key, default, CURVE_FLOW_MIN, CURVE_FLOW_MAX)
        for _, key, default in CURVE_POINTS
    ),
    _temperature_setting(
        "eco_temp_reduction",
        DEFAULT_ECO_TEMP_REDUCTION,
        ECO_TEMP_REDUCTION_MIN,
        ECO_TEMP_REDUCTION_MAX,
    ),
)

# How the circuit reacts to a room thermostat. Only offered when it follows one.
ROOM_THERMOSTAT_SETTINGS: tuple[LambdaSettingDescription, ...] = (
    _temperature_setting(
        "room_thermostat_offset", DEFAULT_ROOM_THERMOSTAT_OFFSET, -10.0, 10.0
    ),
    LambdaSettingDescription(
        key="room_thermostat_factor",
        default=DEFAULT_ROOM_THERMOSTAT_FACTOR,
        native_min_value=1.0,
        native_max_value=5.0,
        native_step=0.1,
        mode=NumberMode.BOX,
    ),
)

# What the cockpit draws its switching points from. Copies of the controller's
# settings; only created when the cockpit dashboard is installed.
COCKPIT_SETTINGS: tuple[LambdaSettingDescription, ...] = tuple(
    _config(description)
    for description in (
        _difference_setting("dhw_switch_on_hysteresis", -5.0, -20.0, 0.0, module="boil"),
        _difference_setting("dhw_switch_off_hysteresis", 0.0, -10.0, 10.0, module="boil"),
        _temperature_setting(
            "dhw_maximum_temperature", 60.0, 40.0, 70.0, module="boil", step=0.5
        ),
        _difference_setting(
            "buffer_switch_on_hysteresis_25", -3.0, -20.0, 0.0, module="buff"
        ),
        _difference_setting(
            "buffer_switch_on_hysteresis_50", -5.0, -20.0, 0.0, module="buff"
        ),
        _difference_setting(
            "buffer_switch_off_hysteresis", 0.0, -10.0, 10.0, module="buff"
        ),
        _difference_setting("buffer_setpoint_offset", 1.0, -10.0, 10.0, module="buff"),
        _difference_setting("hc_switch_on_hysteresis", -2.0, -10.0, 10.0, module="hc"),
        _difference_setting("hc_switch_off_hysteresis", 2.0, -10.0, 15.0, module="hc"),
        _difference_setting("hc_temperature_spread", 5.0, 1.0, 15.0, module="hc"),
        _temperature_setting(
            "heating_limit_outside_temperature", 15.0, 5.0, 25.0, step=0.5
        ),
        _temperature_setting(
            "hc_maximum_flow_temperature", 45.0, 25.0, 60.0, step=0.5
        ),
    )
)

# Winter: raise the room setpoint after a number of defrosts in a day.
DEFROST_BOOST_SETTINGS: tuple[LambdaSettingDescription, ...] = (
    _config(
        LambdaSettingDescription(
            key="defrost_boost_count",
            default=DEFAULT_DEFROST_BOOST_COUNT,
            native_min_value=1,
            native_max_value=20,
            native_step=1,
            mode=NumberMode.BOX,
        )
    ),
    _config(
        _temperature_setting(
            "defrost_boost_room_temperature",
            DEFAULT_DEFROST_BOOST_ROOM_TEMP,
            15.0,
            28.0,
            step=0.5,
        )
    ),
    _config(
        _temperature_setting(
            "defrost_normal_room_temperature",
            DEFAULT_DEFROST_NORMAL_ROOM_TEMP,
            15.0,
            28.0,
            step=0.5,
        )
    ),
)


@dataclass(frozen=True, kw_only=True)
class LambdaRegisterNumberDescription(NumberEntityDescription):
    """A writable register, shown as a number."""

    module: str
    # The field on the module's component that holds the register.
    field: str


def _register_temperature(
    key: str, module: str, field: str, minimum: float, maximum: float, step: float
) -> LambdaRegisterNumberDescription:
    return LambdaRegisterNumberDescription(
        key=key,
        module=module,
        field=field,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=step,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.BOX,
    )


def _register_difference(
    key: str, module: str, field: str
) -> LambdaRegisterNumberDescription:
    return LambdaRegisterNumberDescription(
        key=key,
        module=module,
        field=field,
        native_min_value=0.0,
        native_max_value=10.0,
        native_step=0.5,
        native_unit_of_measurement=_KELVIN,
        mode=NumberMode.BOX,
    )


FLOW_LINE_OFFSET = _register_temperature(
    "flow_line_offset_temperature",
    "hc",
    "set_flow_line_offset_temperature",
    FLOW_LINE_OFFSET_MIN,
    FLOW_LINE_OFFSET_MAX,
    0.1,
)

MAXIMUM_BUFFER_TEMPERATURE = _register_temperature(
    "maximum_buffer_temp", "buff", "maximum_buffer_temp", 20.0, 70.0, 0.5
)

# The PV temperature increases, only on a firmware that has them.
PV_OFFSETS: tuple[LambdaRegisterNumberDescription, ...] = (
    _register_difference("pv_temperature_increase", "boil", "pv_temperature_increase"),
    _register_difference("pv_temperature_increase", "buff", "pv_temperature_increase"),
    _register_difference("pv_temperature_increase", "hc", "pv_temperature_increase"),
)


def _room_setpoint(entry: LambdaConfigEntry) -> LambdaRegisterNumberDescription:
    """The room setpoint, bounded like the heating-circuit climate."""
    return _register_temperature(
        "target_room_temperature",
        "hc",
        "target_room_temperature",
        float(
            entry.options.get(
                CONF_HEATING_CIRCUIT_MIN_TEMP, DEFAULT_HEATING_CIRCUIT_MIN_TEMP
            )
        ),
        float(
            entry.options.get(
                CONF_HEATING_CIRCUIT_MAX_TEMP, DEFAULT_HEATING_CIRCUIT_MAX_TEMP
            )
        ),
        0.5,
    )


def pv_offsets_served(entry: LambdaConfigEntry) -> bool:
    """Whether the configured firmware has the PV temperature increases."""
    return firmware_level(entry) in parse_firmware_versions(PV_OFFSET_FIRMWARE_VERSIONS)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LambdaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the settings and the writable registers."""
    coordinator = entry.runtime_data
    settings = CURVE_SETTINGS
    if entry.options.get(CONF_ROOM_THERMOSTAT_CONTROL, False):
        settings += ROOM_THERMOSTAT_SETTINGS
    if entry.options.get(CONF_INSTALL_DASHBOARD, False):
        settings += COCKPIT_SETTINGS
    if entry.options.get(CONF_DEFROST_ROOM_BOOST, False):
        settings += DEFROST_BOOST_SETTINGS

    registers = [FLOW_LINE_OFFSET, _room_setpoint(entry), MAXIMUM_BUFFER_TEMPERATURE]
    if pv_offsets_served(entry):
        registers += PV_OFFSETS

    entities: list[NumberEntity] = []
    for description in settings:
        for index in range(1, coordinator.counts[description.module] + 1):
            entities.append(LambdaSettingNumber(coordinator, description, index))
    for description in registers:
        for index in range(1, coordinator.counts[description.module] + 1):
            entities.append(LambdaRegisterNumber(coordinator, description, index))
    async_add_entities(entities)


class LambdaSettingNumber(LambdaEntity, RestoreNumber):
    """A value the user sets, which only the integration reads.

    It is published to the coordinator so the sensors can read it without going
    back through the state machine.
    """

    _entity_domain = "number"

    entity_description: LambdaSettingDescription

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: LambdaSettingDescription,
        index: int,
    ) -> None:
        """Bind the setting to one module."""
        # These entities have always carried a `_number` suffix on their unique
        # id, to keep them apart from the sensors they feed.
        super().__init__(
            coordinator, f"{description.key}_number", description.module, index
        )
        self.entity_description = description
        self._attr_translation_key = description.key
        self._publish(description.default)

    @property
    def _setting_key(self) -> tuple[str, int, str]:
        return (self.entity_description.module, self._index, self.entity_description.key)

    @property
    def native_value(self) -> float:
        """What the user set, or the default until they set anything."""
        return self.coordinator.settings[self._setting_key]

    async def async_added_to_hass(self) -> None:
        """Restore what the user set before the restart."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            if last.native_value is not None:
                self._publish(last.native_value)

    async def async_set_native_value(self, value: float) -> None:
        """Take a new setting."""
        self._publish(value)
        self.async_write_ha_state()
        # The sensors that read the setting have to be told.
        self.coordinator.async_update_listeners()

    def _publish(self, value: float) -> None:
        """Put the setting where the sensors can find it."""
        self.coordinator.settings[self._setting_key] = value


class LambdaRegisterNumber(LambdaEntity, NumberEntity):
    """A register the controller holds, written as a number.

    There is nothing to restore — the controller remembers.
    """

    _entity_domain = "number"

    entity_description: LambdaRegisterNumberDescription

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: LambdaRegisterNumberDescription,
        index: int,
    ) -> None:
        """Bind the number to one module's register."""
        super().__init__(
            coordinator,
            f"{description.key}_number",
            description.module,
            index,
            component=f"{description.module}{index}",
        )
        self.entity_description = description
        self._attr_translation_key = description.key

    @property
    def native_value(self) -> float | None:
        """What the controller currently holds."""
        return getattr(self._component, self.entity_description.field)

    @property
    def _component(self):
        return self.coordinator.component(self.entity_description.module, self._index)

    async def async_set_native_value(self, value: float) -> None:
        """Write the value; the field turns it back into a register."""
        try:
            await self._component.write(self.entity_description.field, value)
        except ModbusError as err:
            raise HomeAssistantError(
                f"Could not set {self.entity_description.key}: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
