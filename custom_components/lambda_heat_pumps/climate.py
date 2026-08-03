"""Climate platform for the Lambda Heat Pumps integration.

A thermostat for each thing the user sets a temperature on: the hot water in each
boiler, and — when the circuit is set up to follow a room thermostat, or to cool
— the room temperature of each heating circuit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from modbus_connection import ModbusError

from .const import (
    CONF_COOLING_MODE,
    CONF_HEATING_CIRCUIT_MAX_TEMP,
    CONF_HEATING_CIRCUIT_MIN_TEMP,
    CONF_HEATING_CIRCUIT_TEMP_STEP,
    CONF_HOT_WATER_MAX_TEMP,
    CONF_HOT_WATER_MIN_TEMP,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_ROOM_THERMOSTAT_CONTROL,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HOT_WATER_MIN_TEMP,
)
from .coordinator import LambdaConfigEntry, LambdaCoordinator
from .entity import LambdaEntity


@dataclass(frozen=True, kw_only=True)
class LambdaClimateDescription(ClimateEntityDescription):
    """A thermostat over one module's current and target temperature."""

    module: str
    current: str
    target: str
    hvac_mode: HVACMode


HOT_WATER = LambdaClimateDescription(
    key="hot_water",
    module="boil",
    current="actual_high_temperature",
    target="target_high_temperature",
    hvac_mode=HVACMode.HEAT,
)
HEATING_CIRCUIT = LambdaClimateDescription(
    key="heating_circuit",
    module="hc",
    current="room_device_temperature",
    target="target_room_temperature",
    hvac_mode=HVACMode.HEAT,
)
COOLING_CIRCUIT = LambdaClimateDescription(
    key="cooling_circuit",
    module="hc",
    current="room_device_temperature",
    target="set_cooling_mode_room_temperature",
    hvac_mode=HVACMode.COOL,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LambdaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a thermostat for every temperature the user can set."""
    coordinator = entry.runtime_data
    options = entry.options

    entities = [
        LambdaClimate(coordinator, HOT_WATER, index)
        for index in range(1, coordinator.counts["boil"] + 1)
    ]
    for index in range(1, coordinator.counts["hc"] + 1):
        # A circuit only becomes a room thermostat once it has a room to read.
        if options.get(CONF_ROOM_THERMOSTAT_CONTROL, False) and options.get(
            CONF_ROOM_TEMPERATURE_ENTITY.format(index)
        ):
            entities.append(LambdaClimate(coordinator, HEATING_CIRCUIT, index))
        if options.get(CONF_COOLING_MODE, False):
            entities.append(LambdaClimate(coordinator, COOLING_CIRCUIT, index))

    async_add_entities(entities)


class LambdaClimate(LambdaEntity, ClimateEntity):
    """One temperature the user sets on the controller."""

    _entity_domain = "climate"

    entity_description: LambdaClimateDescription

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: LambdaClimateDescription,
        index: int,
    ) -> None:
        """Bind the thermostat to the module it controls."""
        super().__init__(coordinator, description.key, description.module, index)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._attr_hvac_mode = description.hvac_mode
        self._attr_hvac_modes = [description.hvac_mode]

        options = coordinator.config_entry.options
        if description is HOT_WATER:
            self._attr_min_temp = options.get(
                CONF_HOT_WATER_MIN_TEMP, DEFAULT_HOT_WATER_MIN_TEMP
            )
            self._attr_max_temp = options.get(
                CONF_HOT_WATER_MAX_TEMP, DEFAULT_HOT_WATER_MAX_TEMP
            )
        else:
            self._attr_min_temp = options.get(
                CONF_HEATING_CIRCUIT_MIN_TEMP, DEFAULT_HEATING_CIRCUIT_MIN_TEMP
            )
            self._attr_max_temp = options.get(
                CONF_HEATING_CIRCUIT_MAX_TEMP, DEFAULT_HEATING_CIRCUIT_MAX_TEMP
            )
        self._attr_target_temperature_step = options.get(
            CONF_HEATING_CIRCUIT_TEMP_STEP, DEFAULT_HEATING_CIRCUIT_TEMP_STEP
        )

    @property
    def _component(self):
        """The module this thermostat controls."""
        return self.coordinator.component(
            self.entity_description.module, self._index
        )

    @property
    def current_temperature(self) -> float | None:
        """What it is now."""
        return getattr(self._component, self.entity_description.current)

    @property
    def target_temperature(self) -> float | None:
        """What the controller is aiming for."""
        return getattr(self._component, self.entity_description.target)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Ask the controller for a different temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        try:
            await self._component.write(self.entity_description.target, temperature)
        except ModbusError as err:
            raise HomeAssistantError(
                f"Could not set the target temperature: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
