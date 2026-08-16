"""A heat pump module (HP1-n)."""

from __future__ import annotations

from modbus_connection.model import int32, integer

from .enums import (
    HeatPumpErrorState,
    HeatPumpOperatingState,
    HeatPumpState,
    RelaisState,
)
from .model import LambdaComponent, enum, gauge


class HeatPump(LambdaComponent):
    """One heat pump. Addresses are relative; the block sits at 1000 + 100n."""

    error_state = enum(0, HeatPumpErrorState)
    error_number = integer(1)
    state = enum(2, HeatPumpState)
    operating_state = enum(3, HeatPumpOperatingState)

    flow_line_temperature = gauge(4, 0.01, unit="°C")
    return_line_temperature = gauge(5, 0.01, unit="°C")
    volume_flow_heat_sink = integer(6, unit="l/h")
    energy_source_inlet_temperature = gauge(7, 0.01, unit="°C")
    energy_source_outlet_temperature = gauge(8, 0.01, unit="°C")
    volume_flow_energy_source = gauge(9, 0.01, unit="l/min")

    compressor_unit_rating = gauge(10, 0.01, signed=False, unit="%")
    actual_heating_capacity = gauge(11, 0.1, unit="kW")
    inverter_power_consumption = integer(12, unit="W")
    cop = gauge(13, 0.01)

    request_type = integer(15, writable=True)
    requested_flow_line_temperature = gauge(16, 0.1, writable=True, unit="°C")
    requested_return_line_temperature = gauge(17, 0.1, writable=True, unit="°C")
    requested_flow_to_return_line_temperature_difference = gauge(
        18, 0.1, writable=True, unit="°C"
    )
    relais_state_2nd_heating_stage = enum(19, RelaisState, signed=True)

    compressor_power_consumption_accumulated = int32(20, unit="Wh")
    compressor_thermal_energy_output_accumulated = int32(22, unit="Wh")

    # Undocumented registers found on real hardware.
    config_parameter_24 = integer(24, signed=False)
    vda_rating = gauge(25, 0.01, signed=False, unit="%")
    hot_gas_temperature = gauge(26, 0.01, unit="°C")
    subcooling_temperature = gauge(27, 0.01, unit="°C")
    suction_gas_temperature = gauge(28, 0.01, unit="°C")
    condensation_temperature = gauge(29, 0.01, unit="°C")
    evaporation_temperature = gauge(30, 0.01, unit="°C")
    eqm_rating = gauge(31, 0.01, signed=False, unit="%")
    expansion_valve_opening_angle = gauge(32, 0.01, signed=False, unit="%")
    config_parameter_33 = integer(33, signed=False)


class HeatPumpCapacityLimits(LambdaComponent):
    """One heat pump's capacity limits, settable per outside temperature.

    Its own component, over the same block as the heat pump it belongs to,
    because it is read on its own schedule: the controller serves these eleven
    registers only one at a time, and they hold what an installer set rather
    than anything the heat pump is doing.
    """

    config_parameter_50 = integer(50, signed=False)
    dhw_output_power_15c = gauge(51, 0.1, signed=False, writable=True, unit="kW")
    heating_min_output_power_15c = gauge(52, 0.1, signed=False, writable=True, unit="kW")
    heating_max_output_power_15c = gauge(53, 0.1, signed=False, writable=True, unit="kW")
    heating_min_output_power_0c = gauge(54, 0.1, signed=False, writable=True, unit="kW")
    heating_max_output_power_0c = gauge(55, 0.1, signed=False, writable=True, unit="kW")
    heating_min_output_power_minus15c = gauge(
        56, 0.1, signed=False, writable=True, unit="kW"
    )
    heating_max_output_power_minus15c = gauge(
        57, 0.1, signed=False, writable=True, unit="kW"
    )
    cooling_min_output_power = gauge(58, 0.1, signed=False, writable=True, unit="kW")
    cooling_max_output_power = gauge(59, 0.1, signed=False, writable=True, unit="kW")
    config_parameter_60 = integer(60, signed=False)


class HeatPumpLowFirst(HeatPump):
    """A heat pump whose 32-bit counters put the low word first (CDAB)."""

    compressor_power_consumption_accumulated = int32(20, word_order="little", unit="Wh")
    compressor_thermal_energy_output_accumulated = int32(
        22, word_order="little", unit="Wh"
    )
