"""Number platform for the Lambda Heat Pumps integration.

Two kinds of number, one per heating circuit.

**Settings** are not registers at all — the three points of the heating curve, the
eco reduction, and how hard the circuit chases a room thermostat. The controller
knows nothing about them; the integration computes the curve itself. They are
kept by the entity, restored across restarts, and published to the coordinator
for the heating-curve sensor to read.

**The flow-line offset** is a register. It is written to the controller, and read
back from it like any other value.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from modbus_connection import ModbusError

from .const import (
    CONF_ROOM_THERMOSTAT_CONTROL,
    CURVE_FLOW_MAX,
    CURVE_FLOW_MIN,
    CURVE_POINTS,
    DEFAULT_ECO_TEMP_REDUCTION,
    DEFAULT_ROOM_THERMOSTAT_FACTOR,
    DEFAULT_ROOM_THERMOSTAT_OFFSET,
    ECO_TEMP_REDUCTION_MAX,
    ECO_TEMP_REDUCTION_MIN,
    FLOW_LINE_OFFSET_MAX,
    FLOW_LINE_OFFSET_MIN,
)
from .coordinator import LambdaConfigEntry, LambdaCoordinator
from .entity import LambdaEntity

# The register this platform writes, on the model's HeatingCircuit.
FLOW_LINE_OFFSET_FIELD = "set_flow_line_offset_temperature"


@dataclass(frozen=True, kw_only=True)
class LambdaSettingDescription(NumberEntityDescription):
    """A value the user sets that the controller never sees."""

    default: float


def _temperature_setting(
    key: str, default: float, minimum: float, maximum: float
) -> LambdaSettingDescription:
    return LambdaSettingDescription(
        key=key,
        default=default,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.BOX,
    )


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

FLOW_LINE_OFFSET = NumberEntityDescription(
    key="flow_line_offset_temperature",
    native_min_value=FLOW_LINE_OFFSET_MIN,
    native_max_value=FLOW_LINE_OFFSET_MAX,
    native_step=0.1,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=NumberDeviceClass.TEMPERATURE,
    mode=NumberMode.BOX,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LambdaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a heating circuit's numbers."""
    coordinator = entry.runtime_data
    settings = CURVE_SETTINGS
    if entry.options.get(CONF_ROOM_THERMOSTAT_CONTROL, False):
        settings += ROOM_THERMOSTAT_SETTINGS

    entities: list[NumberEntity] = []
    for index in range(1, coordinator.counts["hc"] + 1):
        entities += [
            LambdaSettingNumber(coordinator, description, index)
            for description in settings
        ]
        entities.append(LambdaFlowLineOffsetNumber(coordinator, index))
    async_add_entities(entities)


class LambdaSettingNumber(LambdaEntity, RestoreNumber):
    """A value the user sets, which only the integration reads.

    It is published to the coordinator so the heating-curve sensor can read it
    without going back through the state machine.
    """

    _entity_domain = "number"

    entity_description: LambdaSettingDescription

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: LambdaSettingDescription,
        index: int,
    ) -> None:
        """Bind the setting to one heating circuit."""
        # These entities have always carried a `_number` suffix on their unique
        # id, to keep them apart from the sensors they feed.
        super().__init__(coordinator, f"{description.key}_number", "hc", index)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._publish(description.default)

    @property
    def native_value(self) -> float:
        """What the user set, or the default until they set anything."""
        return self.coordinator.settings[(self._index, self.entity_description.key)]

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
        # The heating-curve sensor reads the setting, so it has to be told.
        self.coordinator.async_update_listeners()

    def _publish(self, value: float) -> None:
        """Put the setting where the heating-curve sensor can find it."""
        self.coordinator.settings[(self._index, self.entity_description.key)] = value


class LambdaFlowLineOffsetNumber(LambdaEntity, NumberEntity):
    """How far the controller shifts a circuit's flow temperature.

    A register, so there is nothing to restore — the controller remembers.
    """

    _entity_domain = "number"

    entity_description = FLOW_LINE_OFFSET

    def __init__(self, coordinator: LambdaCoordinator, index: int) -> None:
        """Bind the number to one heating circuit."""
        super().__init__(
            coordinator, f"{FLOW_LINE_OFFSET.key}_number", "hc", index
        )
        self._attr_translation_key = FLOW_LINE_OFFSET.key

    @property
    def native_value(self) -> float | None:
        """The offset the controller currently holds."""
        return getattr(
            self.coordinator.component("hc", self._index), FLOW_LINE_OFFSET_FIELD
        )

    async def async_set_native_value(self, value: float) -> None:
        """Write the offset in °C; the field turns it back into a register."""
        circuit = self.coordinator.component("hc", self._index)
        try:
            await circuit.write(FLOW_LINE_OFFSET_FIELD, value)
        except ModbusError as err:
            raise HomeAssistantError(
                f"Could not set the flow line offset: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
