"""Sensor platform for the Lambda Heat Pumps integration.

Four kinds of sensor live here.

**Register sensors** report a value the controller holds. They read it straight
off the device model, which has already decoded it.

**Counters** report something the controller does not hold at all — how often it
entered a mode, and how much energy it spent there. The coordinator counts both
from what it sees while polling; a counter entity restores its own value across
restarts and adds on whatever has been counted since. A counter reported over a
period zeroes itself when that period rolls over.

**COP sensors** divide the heat a mode produced by the electricity it used, over
the same period.

**The heating-curve sensor** works out what flow temperature a circuit should be
asking for, from the curve the user configured and the weather outside.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import cached_property

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ATTR_APPLIED_OFFSET,
    CONF_ROOM_THERMOSTAT_CONTROL,
    CURVE_POINTS,
    CYCLE_MODES,
    DEFAULT_ECO_TEMP_REDUCTION,
    DEFAULT_ROOM_THERMOSTAT_FACTOR,
    DEFAULT_ROOM_THERMOSTAT_OFFSET,
    ELECTRICAL_ENERGY_MODES,
    MODE_COMPRESSOR_START,
    MODE_COOLING,
    MODE_HEATING,
    MODE_HOT_WATER,
    PERIOD_2H,
    PERIOD_4H,
    PERIOD_DAILY,
    PERIOD_HOURLY,
    PERIOD_MONTHLY,
    PERIOD_TOTAL,
    PERIOD_YEARLY,
    SIGNAL_PERIOD_ROLLOVER,
    THERMAL_ENERGY_MODES,
)
from .coordinator import (
    LambdaCapacityLimitCoordinator,
    LambdaConfigEntry,
    LambdaCoordinator,
)
from .entity import LambdaEntity
from .firmware import firmware_level, serves
from .lambda_modbus.enums import HeatingCircuitOperatingState, LambdaState

# --------------------------------------------------------------------------
# Register sensors
# --------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class LambdaSensorDescription(SensorEntityDescription):
    """A sensor reading one field off one of the device model's components."""

    # The model attribute to read. Defaults to the key, which is how they are
    # named for every module sensor; the controller-level ones differ because
    # their keys carry the sub-system they belong to.
    attribute: str | None = None
    # Which of the controller's own components to read it from, for the sensors
    # that do not belong to a module.
    component: str | None = None
    # The firmware versions whose register map has this register. See
    # `firmware.py`; unset means every firmware serves it.
    firmware_version: int | None = None
    firmware_versions: tuple[int | str, ...] | None = None

    @cached_property
    def is_total(self) -> bool:
        """Whether this sensor accumulates rather than measures.

        A total feeds long-term statistics, which is what makes it worth holding
        on to when the controller stops answering. Caching writes into the
        instance dict rather than through ``__setattr__``, so the description
        stays frozen.
        """
        return self.state_class in (
            SensorStateClass.TOTAL,
            SensorStateClass.TOTAL_INCREASING,
        )


def _temperature(key: str, **kwargs) -> LambdaSensorDescription:
    return LambdaSensorDescription(
        key=key,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        **kwargs,
    )


def _state(key: str, **kwargs) -> LambdaSensorDescription:
    """A register holding one of the controller's own state codes."""
    return LambdaSensorDescription(key=key, device_class=SensorDeviceClass.ENUM, **kwargs)


def _power(key: str, unit=UnitOfPower.WATT, precision=0) -> LambdaSensorDescription:
    return LambdaSensorDescription(
        key=key,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=precision,
    )


def _percent(key: str, precision: int = 0) -> LambdaSensorDescription:
    return LambdaSensorDescription(
        key=key,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=precision,
    )


def _count(key: str) -> LambdaSensorDescription:
    """A bare number the controller reports — an error code, a request type.

    No state class: these are codes, not quantities. Averaging an error number
    says nothing, and summing one says less — so there are no statistics to
    generate for them.
    """
    return LambdaSensorDescription(key=key, suggested_display_precision=0)


def _energy_register(key: str) -> LambdaSensorDescription:
    """One of the controller's own accumulating energy counters."""
    return LambdaSensorDescription(
        key=key,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    )


# The controller itself: outside air, and the energy manager.
CONTROLLER_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("ambient_error_number"),
    _state("ambient_operating_state"),
    # Readable only up to V0.0.9-3K; newer controllers answer the register but
    # report nothing through it (0x8000).
    _temperature("ambient_temperature", firmware_versions=("1-7",)),
    _temperature("ambient_temperature_1h"),
    _temperature("ambient_temperature_calculated"),
    _count("emgr_error_number"),
    _state("emgr_operating_state"),
    _power("emgr_actual_power"),
    _power("emgr_actual_power_consumption"),
    _power("emgr_power_consumption_setpoint"),
)

HP_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _state("error_state"),
    _count("error_number"),
    _state("state"),
    _state("operating_state"),
    _temperature("flow_line_temperature"),
    _temperature("return_line_temperature"),
    LambdaSensorDescription(
        key="volume_flow_heat_sink",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _temperature("energy_source_inlet_temperature"),
    _temperature("energy_source_outlet_temperature"),
    LambdaSensorDescription(
        key="volume_flow_energy_source",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _percent("compressor_unit_rating"),
    _power("actual_heating_capacity", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("inverter_power_consumption"),
    LambdaSensorDescription(
        key="cop",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _count("request_type"),
    _temperature("requested_flow_line_temperature"),
    _temperature("requested_return_line_temperature"),
    _temperature("requested_flow_to_return_line_temperature_difference"),
    _state("relais_state_2nd_heating_stage"),
    _energy_register("compressor_power_consumption_accumulated"),
    _energy_register("compressor_thermal_energy_output_accumulated"),
    _count("config_parameter_24"),
    _percent("vda_rating", precision=2),
    _temperature("hot_gas_temperature"),
    _temperature("subcooling_temperature"),
    _temperature("suction_gas_temperature"),
    _temperature("condensation_temperature"),
    _temperature("evaporation_temperature"),
    _percent("eqm_rating", precision=2),
    _percent("expansion_valve_opening_angle", precision=2),
    _count("config_parameter_33"),
)

# The capacity limits, read on their own slow poll rather than with the rest of
# the heat pump. Same keys, so the entities they back are the ones that existed.
HP_CAPACITY_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("config_parameter_50"),
    _power("dhw_output_power_15c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_min_output_power_15c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_max_output_power_15c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_min_output_power_0c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_max_output_power_0c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_min_output_power_minus15c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("heating_max_output_power_minus15c", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("cooling_min_output_power", unit=UnitOfPower.KILO_WATT, precision=1),
    _power("cooling_max_output_power", unit=UnitOfPower.KILO_WATT, precision=1),
    _count("config_parameter_60"),
)

BOIL_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("error_number"),
    _state("operating_state"),
    _temperature("actual_high_temperature"),
    _temperature("actual_low_temperature"),
    _temperature("actual_circulation_temperature"),
    _state("actual_circulation_pump_state"),
    _temperature("target_high_temperature"),
)

BUFF_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("error_number"),
    _state("operating_state"),
    _temperature("actual_high_temperature"),
    _temperature("actual_low_temperature"),
    _temperature("buffer_temperature_high_setpoint"),
    _state("request_type"),
    _temperature("request_flow_line_temp_setpoint"),
    _temperature("request_return_line_temp_setpoint"),
    LambdaSensorDescription(
        key="request_heat_sink_temp_diff_setpoint",
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _power("modbus_request_heating_capacity", unit=UnitOfPower.KILO_WATT, precision=1),
    _temperature("maximum_buffer_temp"),
)

SOL_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("error_number"),
    _state("operating_state"),
    _temperature("collector_temperature"),
    _temperature("storage_temperature"),
    _power("power_current", unit=UnitOfPower.KILO_WATT, precision=1),
    LambdaSensorDescription(
        key="energy_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    _temperature("maximum_buffer_temperature"),
    _temperature("buffer_changeover_temperature"),
)

HC_SENSORS: tuple[LambdaSensorDescription, ...] = (
    _count("error_number"),
    _state("operating_state"),
    _temperature("flow_line_temperature"),
    _temperature("return_line_temperature"),
    _temperature("room_device_temperature"),
    _temperature("set_flow_line_temperature"),
    _state("operating_mode"),
    _temperature("flow_line_temperature_setpoint"),
    _temperature("target_temp_flow_line", firmware_version=3),
    _temperature("set_flow_line_offset_temperature"),
    _temperature("target_room_temperature"),
    _temperature("set_cooling_mode_room_temperature"),
)

MODULE_SENSORS: dict[str, tuple[LambdaSensorDescription, ...]] = {
    "hp": HP_SENSORS,
    "boil": BOIL_SENSORS,
    "buff": BUFF_SENSORS,
    "sol": SOL_SENSORS,
    "hc": HC_SENSORS,
}

# The controller's two sub-systems, and the key prefix that names each.
CONTROLLER_COMPONENTS = {"ambient_": "ambient", "emgr_": "e_manager"}


# --------------------------------------------------------------------------
# Counters
# --------------------------------------------------------------------------

# Which periods each family of counter is reported over. These are exactly the
# entities the integration has always created — the combinations are not
# symmetrical, and changing them would orphan existing entities.
CYCLE_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_2H, PERIOD_4H)
COMPRESSOR_START_PERIODS = (*CYCLE_PERIODS, PERIOD_MONTHLY)
ENERGY_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_MONTHLY, PERIOD_YEARLY)
HEATING_ENERGY_PERIODS = (*ENERGY_PERIODS, PERIOD_HOURLY)

# A coefficient of performance needs both an electrical and a thermal counter, so
# it exists only for the modes that have both, over the periods they share.
COP_MODES = (MODE_HEATING, MODE_HOT_WATER, MODE_COOLING)
COP_PERIODS = ENERGY_PERIODS
COP_HEATING_PERIODS = HEATING_ENERGY_PERIODS

_CYCLE_UNIT = "cycles"


def _read_curve(outside: float, curve: list[tuple[float, float]]) -> float | None:
    """The flow temperature the curve gives for an outside temperature.

    The curve is a few (outside, flow) points, coldest first. Between them the
    flow is interpolated; beyond the ends it is held flat. A curve that does not
    fall as it gets warmer outside is not a heating curve — the user has mixed
    the points up — and there is no sensible answer to give.
    """
    flows = [flow for _, flow in curve]
    if len(set(flows)) == 1:
        return flows[0]  # a flat curve: the same flow whatever the weather
    if any(warmer >= colder for colder, warmer in zip(flows, flows[1:], strict=False)):
        return None

    for (cold_x, cold_y), (warm_x, warm_y) in zip(curve, curve[1:], strict=False):
        if outside <= cold_x:
            return cold_y
        if outside <= warm_x:
            span = (outside - cold_x) / (warm_x - cold_x)
            return cold_y + span * (warm_y - cold_y)
    return flows[-1]


@dataclass(frozen=True, kw_only=True)
class CounterDescription(SensorEntityDescription):
    """A counter the coordinator accumulates, reported over one period."""

    mode: str
    period: str
    # Which of the coordinator's running totals to read.
    total: Callable[[LambdaCoordinator, int], float]
    # How the total is reported. Cycles are counted, so they are whole.
    decimals: int = 0


def _cycle_description(mode: str, period: str) -> CounterDescription:
    return CounterDescription(
        key=f"{mode}_cycling_{period}",
        mode=mode,
        period=period,
        native_unit_of_measurement=_CYCLE_UNIT,
        state_class=(
            SensorStateClass.TOTAL_INCREASING
            if period == PERIOD_TOTAL
            else SensorStateClass.TOTAL
        ),
        # Only the running total is on by default; the per-period counters are
        # derivable from it (the energy dashboard and utility_meter do exactly
        # that), so they are left for the user to enable rather than shipped as
        # a dozen entities per heat pump.
        entity_registry_enabled_default=period == PERIOD_TOTAL,
        suggested_display_precision=0,
        total=lambda coordinator, index, mode=mode: coordinator.totals[index].cycles.get(
            mode, 0
        ),
    )


def _energy_description(mode: str, period: str, *, thermal: bool) -> CounterDescription:
    kind = "thermal_energy" if thermal else "energy"
    return CounterDescription(
        key=f"{mode}_{kind}_{period}",
        mode=mode,
        period=period,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=(
            SensorStateClass.TOTAL_INCREASING
            if period == PERIOD_TOTAL
            else SensorStateClass.TOTAL
        ),
        # The total feeds the energy dashboard, which derives the periods itself.
        entity_registry_enabled_default=period == PERIOD_TOTAL,
        suggested_display_precision=2,
        decimals=2,
        total=(
            (lambda coordinator, index, mode=mode: coordinator.totals[index].thermal.get(mode, 0.0))
            if thermal
            else (lambda coordinator, index, mode=mode: coordinator.totals[index].electrical.get(mode, 0.0))
        ),
    )


def _counter_descriptions() -> Iterable[CounterDescription]:
    """Every counter a heat pump has."""
    for mode in CYCLE_MODES:
        periods = (
            COMPRESSOR_START_PERIODS
            if mode == MODE_COMPRESSOR_START
            else CYCLE_PERIODS
        )
        for period in periods:
            yield _cycle_description(mode, period)

    for mode in ELECTRICAL_ENERGY_MODES:
        periods = HEATING_ENERGY_PERIODS if mode == MODE_HEATING else ENERGY_PERIODS
        for period in periods:
            yield _energy_description(mode, period, thermal=False)

    for mode in THERMAL_ENERGY_MODES:
        periods = HEATING_ENERGY_PERIODS if mode == MODE_HEATING else ENERGY_PERIODS
        for period in periods:
            yield _energy_description(mode, period, thermal=True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LambdaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up every sensor the controller's modules give it."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    # A register the configured firmware is not known to serve is not modelled
    # at all — probing finds what the controller answers for, not what it
    # answers meaningfully.
    level = firmware_level(entry)

    for description in CONTROLLER_SENSORS:
        if not serves(description, level):
            continue
        prefix = next(p for p in CONTROLLER_COMPONENTS if description.key.startswith(p))
        entities.append(
            _register_sensor(description)(
                coordinator,
                description,
                component=CONTROLLER_COMPONENTS[prefix],
                attribute=description.key.removeprefix(prefix),
            )
        )

    for module, descriptions in MODULE_SENSORS.items():
        for index in range(1, coordinator.counts[module] + 1):
            entities += [
                _register_sensor(d)(coordinator, d, module=module, index=index)
                for d in descriptions
                if serves(d, level)
            ]

    for capacity in coordinator.capacity_limits:
        entities += [
            LambdaCapacityLimitSensor(capacity, description)
            for description in HP_CAPACITY_SENSORS
            if serves(description, level)
        ]

    for index in range(1, coordinator.counts["hp"] + 1):
        # A yesterday counter mirrors the daily one it is paired with: the daily
        # counter hands its value over at midnight, on the way past zero.
        yesterdays = {
            mode: YesterdayCycleSensor(coordinator, mode, index) for mode in CYCLE_MODES
        }
        entities += yesterdays.values()

        counters: dict[str, LambdaCounterSensor] = {}
        for description in _counter_descriptions():
            yesterday = (
                yesterdays[description.mode]
                if description.key.endswith("_cycling_daily")
                else None
            )
            counter = LambdaCounterSensor(coordinator, description, index, yesterday)
            counters[description.key] = counter
        entities += counters.values()

        # A COP is one counter divided by another over the same period, so it is
        # handed the pair rather than looking them up by name at read time.
        for mode in COP_MODES:
            periods = COP_HEATING_PERIODS if mode == MODE_HEATING else COP_PERIODS
            entities += [
                LambdaCopSensor(
                    coordinator,
                    mode,
                    period,
                    index,
                    thermal=counters[f"{mode}_thermal_energy_{period}"],
                    electrical=counters[f"{mode}_energy_{period}"],
                )
                for period in periods
            ]

    entities += [
        LambdaLifetimeCopSensor(coordinator, index)
        for index in range(1, coordinator.counts["hp"] + 1)
    ]

    entities += [
        LambdaHeatingCurveSensor(coordinator, index)
        for index in range(1, coordinator.counts["hc"] + 1)
    ]

    async_add_entities(entities)


class LambdaRegisterEntity(LambdaEntity):
    """What the two kinds of register sensor share: which field they report."""

    _entity_domain = "sensor"

    entity_description: LambdaSensorDescription

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: LambdaSensorDescription,
        *,
        module: str | None = None,
        index: int | None = None,
        component: str | None = None,
        attribute: str | None = None,
    ) -> None:
        """Bind the sensor to the field it reports."""
        # A gap in a running total reads as a counter reset, so it holds what it
        # last read rather than going unavailable with its module.
        polled = None if description.is_total else component or f"{module}{index}"
        super().__init__(coordinator, description.key, module, index, component=polled)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._component = component
        self._attribute = attribute or description.key
        # Every state a state register can report. Home Assistant requires an
        # enum sensor to declare them and refuses a state that is not among
        # them, so they are resolved here: the labels come from the enum the
        # field decodes to, which the class fixes once and for all.
        if description.device_class is SensorDeviceClass.ENUM:
            self._attr_options = [
                state.label for state in self._field(coordinator).convert
            ]

    def _component_of(self, coordinator: LambdaCoordinator):
        """The modelled sub-system this sensor reads from."""
        if self._component is not None:
            return getattr(coordinator.device, self._component)
        return coordinator.component(self._module, self._index)

    def _field(self, coordinator: LambdaCoordinator):
        """The declared field behind this sensor.

        `declared_fields` describes what the class declares, so it still has the
        field even when the controller does not serve that register and it was
        narrowed out of the read.
        """
        return self._component_of(coordinator).declared_fields[self._attribute]

    def _read(self) -> float | str | None:
        """The decoded field, or its label if it is one of the state codes."""
        value = getattr(self._component_of(self.coordinator), self._attribute)
        if isinstance(value, LambdaState):
            return value.label
        return value


class LambdaSensor(LambdaRegisterEntity, SensorEntity):
    """A value the controller holds, read straight off the device model.

    There is nothing to keep here: the model holds the value, and the entity
    goes unavailable with the module that stopped answering for it.
    """

    @property
    def native_value(self) -> float | str | None:
        """What the model holds for this field right now."""
        return self._read()


class LambdaTotalSensor(LambdaRegisterEntity, RestoreSensor):
    """One of the controller's own accumulating counters.

    It feeds long-term statistics, so it holds the last value it read and
    restores it across a restart: a heat pump that is not answering when Home
    Assistant starts does not leave a hole in its own history.
    """

    async def async_added_to_hass(self) -> None:
        """Take the last value back up before the first poll lands."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value
        self._process_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Take this poll's reading before the state is written."""
        self._process_data()
        super()._handle_coordinator_update()

    def _process_data(self) -> None:
        """Read the total, and keep the one we had if it reads as nothing.

        The controller has not un-generated the energy it already counted, and
        publishing the gap would take its long-term statistics with it.

        A counter that dips by a hair is the same thing said differently: these
        are 32-bit counters read as two registers, so a poll that catches the
        controller mid-carry reads a value just below the last one. Home
        Assistant would take that for a meter reset. Only a counter that can
        just as well fall on its own — a ``TOTAL`` — is published as read.
        """
        if (value := self._read()) is None:
            return
        last = self._attr_native_value
        if (
            self.entity_description.state_class is SensorStateClass.TOTAL_INCREASING
            and last is not None
            and last * 0.99 <= value < last
        ):
            return  # ignore firmware issue causing minor decrease
        self._attr_native_value = value


def _register_sensor(
    description: LambdaSensorDescription,
) -> type[LambdaSensor | LambdaTotalSensor]:
    """Which kind of register sensor a description asks for.

    Only a total has a value of its own to keep, and only it is worth handing to
    Home Assistant's restore store — which writes every entity registered with
    it to disk on a timer, whether or not that entity ever restores anything.
    """
    return LambdaTotalSensor if description.is_total else LambdaSensor


class LambdaCapacityLimitSensor(LambdaRegisterEntity, SensorEntity):
    """One of a heat pump's capacity limits, off its own slow poll.

    Its coordinator polls a single component, so it either read or it did not:
    naming the heat pump costs nothing and the availability comes down to
    whether that read succeeded.
    """

    def __init__(
        self,
        coordinator: LambdaCapacityLimitCoordinator,
        description: LambdaSensorDescription,
    ) -> None:
        """Bind the sensor to the limit it reports."""
        super().__init__(coordinator, description, module="hp", index=coordinator.index)

    def _component_of(self, coordinator: LambdaCapacityLimitCoordinator):
        """The limits component, which is all this coordinator polls."""
        return coordinator.limits

    @property
    def native_value(self) -> float | str | None:
        """What the model holds for this limit right now."""
        return self._read()


async def _restored_value(entity: RestoreSensor) -> float | None:
    """What this counter was at before the restart.

    A sensor stores its value as typed extra data, which is where it is read
    from. An installation coming from a version that stored only the recorded
    state has none of that, so fall back to the state itself — otherwise
    upgrading would silently start every cumulative counter again at zero.
    """
    if (last := await entity.async_get_last_sensor_data()) is not None:
        if last.native_value is not None:
            return float(last.native_value)
    if (state := await entity.async_get_last_state()) is not None:
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None  # it was unknown or unavailable when it was written
    return None


class LambdaCounterSensor(LambdaEntity, RestoreSensor):
    """A running total the coordinator keeps, over one period.

    The value is the entity's own: it restores what it had before the restart and
    adds on whatever the coordinator has counted since. A counter over a period
    drops back to zero when that period rolls over.
    """

    _entity_domain = "sensor"

    entity_description: CounterDescription

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        description: CounterDescription,
        index: int,
        yesterday: YesterdayCycleSensor | None = None,
    ) -> None:
        """Bind the counter to the total it follows."""
        super().__init__(coordinator, description.key, "hp", index)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._value = 0.0
        # How much of the coordinator's total is already in `_value`.
        self._counted = 0.0
        self._yesterday = yesterday
        # How much of the configured offset is already in `_value`. Kept so that
        # changing the offset moves the total by the difference rather than
        # adding it again on every restart.
        self._applied_offset = 0.0

    @property
    def native_value(self) -> float | int:
        """What this counter has accumulated over its period."""
        decimals = self.entity_description.decimals
        return round(self._value, decimals) if decimals else round(self._value)

    async def async_added_to_hass(self) -> None:
        """Pick up where the last run left off, and arm the rollover."""
        await super().async_added_to_hass()

        if (restored := await _restored_value(self)) is not None:
            self._value = restored
        if (state := await self.async_get_last_state()) is not None:
            self._applied_offset = float(
                state.attributes.get(ATTR_APPLIED_OFFSET, 0.0)
            )
        # Whatever the coordinator counted before this entity existed belongs to
        # the run that is starting, not to the value we just restored.
        self._counted = self._total()
        self._apply_offset()

        if self.entity_description.period != PERIOD_TOTAL:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    SIGNAL_PERIOD_ROLLOVER.format(
                        entry_id=self.coordinator.config_entry.entry_id,
                        period=self.entity_description.period,
                    ),
                    self._handle_rollover,
                )
            )

    def _apply_offset(self) -> None:
        """Take up whatever the configured offset has moved by.

        Only a lifetime total carries one: a counter over a period reports what
        happened in that period, which nothing that came before changes.
        """
        if self.entity_description.period != PERIOD_TOTAL:
            return
        offset = self.coordinator.file_config.offset(
            self._index, self.entity_description.key
        )
        self._value += offset - self._applied_offset
        self._applied_offset = offset

    @property
    def extra_state_attributes(self) -> dict[str, float] | None:
        """The offset already counted, so a changed one moves the total once."""
        if not self._applied_offset:
            return None
        return {ATTR_APPLIED_OFFSET: self._applied_offset}

    def _total(self) -> float:
        """The coordinator's running total for this counter's mode."""
        return self.entity_description.total(self.coordinator, self._index)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Add on whatever has been counted since we last looked."""
        total = self._total()
        self._value += total - self._counted
        self._counted = total
        super()._handle_coordinator_update()

    @callback
    def _handle_rollover(self) -> None:
        """Start the period again at zero."""
        if self._yesterday is not None:
            self._yesterday.set_value(self._value)
        self._value = 0.0
        self.async_write_ha_state()


class YesterdayCycleSensor(LambdaEntity, RestoreSensor):
    """What a daily cycle counter reached before midnight.

    It holds no counter of its own — the daily counter hands its value over on
    the way past zero.
    """

    _entity_domain = "sensor"

    _attr_native_unit_of_measurement = _CYCLE_UNIT
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 0
    # A per-day figure, so off by default like the other per-period counters.
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: LambdaCoordinator, mode: str, index: int) -> None:
        """Name the mode this mirrors."""
        key = f"{mode}_cycling_yesterday"
        super().__init__(coordinator, key, "hp", index)
        self._attr_translation_key = key
        self._value = 0.0

    @property
    def native_value(self) -> float:
        """Yesterday's count."""
        return round(self._value)

    async def async_added_to_hass(self) -> None:
        """Yesterday is still yesterday after a restart."""
        await super().async_added_to_hass()
        if (restored := await _restored_value(self)) is not None:
            self._value = restored

    @callback
    def set_value(self, value: float) -> None:
        """Take over the day that just ended."""
        self._value = value
        self.async_write_ha_state()


class LambdaCopSensor(LambdaEntity, SensorEntity):
    """The heat a mode produced divided by the electricity it used.

    Both are counters over the same period, so the coefficient is just their
    ratio — there is nothing of its own here to accumulate or restore.
    """

    _entity_domain = "sensor"

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: LambdaCoordinator,
        mode: str,
        period: str,
        index: int,
        *,
        thermal: LambdaCounterSensor,
        electrical: LambdaCounterSensor,
    ) -> None:
        """Pair the two counters this divides."""
        key = f"{mode}_cop_{period}"
        super().__init__(coordinator, key, "hp", index)
        self._attr_translation_key = key
        # The lifetime coefficient is on by default; the per-period ones follow
        # the counters they divide, which are off by default.
        self._attr_entity_registry_enabled_default = period == PERIOD_TOTAL
        self._thermal = thermal
        self._electrical = electrical

    @property
    def native_value(self) -> float | None:
        """The coefficient of performance.

        None until the heat pump has used some electricity in this mode this
        period — before that there is no ratio to report, only a division by
        zero.
        """
        electrical = self._electrical.native_value
        if not electrical:
            return None
        return round(self._thermal.native_value / electrical, 2)


class LambdaLifetimeCopSensor(LambdaEntity, SensorEntity):
    """The coefficient of performance over the controller's own lifetime.

    Not one of the coefficients beside it: those divide what this integration
    has counted since it started watching, mode by mode. This divides the two
    totals the controller has kept for itself since it was installed, which is
    every mode together and everything that happened before Home Assistant did.
    """

    _entity_domain = "sensor"

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_translation_key = "cop_calc"

    def __init__(self, coordinator: LambdaCoordinator, index: int) -> None:
        """Bind it to one heat pump's pair of lifetime counters."""
        super().__init__(coordinator, "cop_calc", "hp", index)

    @property
    def native_value(self) -> float | None:
        """Heat out over electricity in, or nothing yet."""
        heat_pump = self.coordinator.component("hp", self._index)
        electrical = heat_pump.compressor_power_consumption_accumulated
        thermal = heat_pump.compressor_thermal_energy_output_accumulated
        if not electrical or thermal is None:
            return None
        return round(thermal / electrical, 2)


class LambdaHeatingCurveSensor(LambdaEntity, SensorEntity):
    """The flow temperature a heating circuit should be asking for.

    The controller does not compute this: the user draws a curve through three
    points — how hot the flow should be at -22 °C, at 0 °C and at +22 °C outside
    — and this reads today's outside temperature off it, then applies the
    corrections the circuit is configured for.
    """

    _entity_domain = "sensor"

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_translation_key = "heating_curve_flow_line_temperature_calc"

    def __init__(self, coordinator: LambdaCoordinator, index: int) -> None:
        """Bind the sensor to one heating circuit."""
        super().__init__(
            coordinator, "heating_curve_flow_line_temperature_calc", "hc", index
        )

    @property
    def native_value(self) -> float | None:
        """Where the curve sits right now, or None if it is not usable."""
        outside = self.coordinator.device.ambient.temperature_calculated
        if outside is None:
            return None

        curve = [
            (point, self._setting(key, default))
            for point, key, default in CURVE_POINTS
        ]
        flow = _read_curve(outside, curve)
        if flow is None:
            return None

        circuit = self.coordinator.component("hc", self._index)
        flow += self._room_correction(circuit)
        flow += circuit.set_flow_line_offset_temperature or 0.0
        if circuit.operating_state == HeatingCircuitOperatingState.ECO:
            # The reduction is configured as a negative number.
            flow += self._setting("eco_temp_reduction", DEFAULT_ECO_TEMP_REDUCTION)
        return round(flow, 1)

    def _room_correction(self, circuit) -> float:
        """How far to push the flow to close the gap in the room.

        Zero unless the circuit is set to follow a room thermostat.
        """
        if not self.coordinator.config_entry.options.get(
            CONF_ROOM_THERMOSTAT_CONTROL, False
        ):
            return 0.0
        current = circuit.room_device_temperature
        target = circuit.target_room_temperature
        if current is None or target is None:
            return 0.0
        factor = self._setting("room_thermostat_factor", DEFAULT_ROOM_THERMOSTAT_FACTOR)
        offset = self._setting("room_thermostat_offset", DEFAULT_ROOM_THERMOSTAT_OFFSET)
        if factor <= 0:
            return 0.0
        return ((target - current) - offset) * factor

    def _setting(self, key: str, default: float) -> float:
        """A value the user set on one of this circuit's number entities."""
        return self.coordinator.settings.get((self._index, key), default)
