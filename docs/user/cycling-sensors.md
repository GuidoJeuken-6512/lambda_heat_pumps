# Cycling Sensors

Cycling sensors track the number of operating cycles for different modes of your heat pump.

## Overview

Cycling sensors count how many times your heat pump has started in different operating modes. This helps you monitor system usage and efficiency.

## Available Cycling Sensors

For each operating mode, multiple cycling sensors are available:

### Operating Modes

- **Heating**: Cycles when heating is active
- **Hot Water**: Cycles when hot water is being heated
- **Cooling**: Cycles when cooling is active
- **Defrost**: Cycles when defrosting is active

### Time Periods

For each operating mode, sensors are available for:

- **Total**: Total cycles since installation
- **Daily**: Cycles today (resets at midnight)
- **Yesterday**: Cycles from yesterday
- **2h**: Cycles in the last 2 hours
- **4h**: Cycles in the last 4 hours
- **Monthly**: Cycles this month

## Entity Names

Example entity names:

- `sensor.*_heating_cycling_total`
- `sensor.*_heating_cycling_daily`
- `sensor.*_heating_cycling_2h`
- `sensor.*_hot_water_cycling_total`
- `sensor.*_cooling_cycling_total`
- `sensor.*_defrost_cycling_total`

## Automatic Reset

- **Daily sensors**: Reset automatically at midnight
- **2h and 4h sensors**: Reset automatically every 2/4 hours
- **Monthly sensors**: Reset at the beginning of each month

## Configuration

### Cycling Offsets

You can configure offsets to adjust cycle counts:

```yaml
lambda_heat_pumps:
  cycling_offsets:
    heating: 0
    hot_water: 0
    cooling: 0
    defrost: 0
```

## Usage Examples

### Monitoring System Health

Track cycling patterns to identify issues:

- Unusually high cycling may indicate problems
- Compare daily cycles to detect changes
- Monitor 2h/4h cycles for immediate feedback

### Energy Efficiency

Use cycling data to optimize energy usage:

- Reduce unnecessary cycling
- Optimize operating schedules
- Identify peak usage times

## Related Documentation

- [Energy Consumption Sensors](energy-consumption.md)
- [Features Overview](features.md)

