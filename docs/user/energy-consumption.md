# Energy Consumption Sensors

Energy consumption sensors track the energy usage of your heat pump by operating mode.

## Overview

These sensors provide detailed energy tracking for different operating modes, helping you understand your system's energy consumption patterns.

## Available Sensors

### By Operating Mode

- **Heating Energy**: Energy consumed during heating
- **Hot Water Energy**: Energy consumed for hot water heating
- **Cooling Energy**: Energy consumed during cooling
- **Defrost Energy**: Energy consumed during defrosting

### Time Periods

For each operating mode, sensors track:

- **Total**: Total energy since installation
- **Daily**: Energy consumed today
- **Monthly**: Energy consumed this month
- **Yearly**: Energy consumed this year

## Entity Names

Example entity names:

- `sensor.*_heating_energy_consumption_total`
- `sensor.*_heating_energy_consumption_daily`
- `sensor.*_heating_energy_consumption_monthly`
- `sensor.*_hot_water_energy_consumption_total`

## Configuration

### Source Sensors

Configure source sensors for energy readings:

```yaml
lambda_heat_pumps:
  energy_sensors:
    heating: sensor.heat_pump_power
    hot_water: sensor.heat_pump_power
```

### Unit Conversion

The integration automatically handles unit conversion:

- **Wh** (Watt-hours)
- **kWh** (Kilowatt-hours)
- **MWh** (Megawatt-hours)

## Usage Examples

### Energy Monitoring

Track energy consumption over time:

- Monitor daily energy usage
- Compare monthly consumption
- Track yearly totals

### Cost Analysis

Use energy data for cost calculations:

- Calculate operating costs
- Compare different time periods
- Identify high-consumption periods

### Efficiency Analysis

Analyze system efficiency:

- Compare energy consumption by mode
- Identify optimization opportunities
- Track efficiency improvements

## Related Documentation

- [Cycling Sensors](cycling-sensors.md)
- [Features Overview](features.md)

