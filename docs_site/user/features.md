# Features

The Lambda Heat Pumps integration provides comprehensive monitoring and control of your Lambda heat pump system.

## Core Features

### Automatic Module Detection

The integration automatically detects available modules:

- Heat pumps
- Boilers
- Buffers
- Solar modules
- Heating circuits

Based on detected hardware, appropriate entities are created automatically.

### Modbus/TCP Support

Full support for Lambda heat pumps via Modbus/TCP protocol:

- Real-time data reading
- Bidirectional communication
- Register-based configuration
- Error handling and retry logic

## Sensor Features

### Temperature Sensors

Monitor temperatures throughout your system:

- Heat pump temperatures
- Boiler temperatures
- Buffer temperatures
- Heating circuit temperatures
- Hot water temperatures

### Cycling Sensors

Comprehensive cycling counters for all operating modes:

- **Heating cycles**: Total, daily, yesterday, 2h, 4h, monthly
- **Hot water cycles**: Total, daily, yesterday, 2h, 4h, monthly
- **Cooling cycles**: Total, daily, yesterday, 2h, 4h, monthly
- **Defrost cycles**: Total, daily, yesterday, 2h, 4h, monthly

All cycling sensors automatically reset at midnight.

### Energy Consumption Sensors

Detailed energy tracking by operating mode:

- Heating energy consumption
- Hot water energy consumption
- Cooling energy consumption
- Defrost energy consumption
- Monthly and yearly totals

## Control Features

### Climate Control

Control your heating and hot water:

- Set target temperatures
- Monitor current temperatures
- Adjust temperature ranges
- Control heating circuits independently

### Heating Curve Configuration

Easy adjustment of heating curve parameters:

- Cold point configuration (-22°C)
- Mid point configuration (0°C)
- Warm point configuration (+22°C)
- Flow line offset adjustment (-10°C to +10°C)

See [Heating Curve Guide](heating-curve.md) for details.

### Room Thermostat Integration

External sensor integration for precise control:

- Room temperature offset
- Room temperature factor
- Automatic flow temperature adjustment

### PV Surplus Control

Solar power integration:

- Automatic PV surplus detection
- Energy-optimized operation modes
- Configurable thresholds

## Advanced Features

### Entity Naming

Flexible entity naming options:

- Legacy Modbus names (compatible with older configurations)
- Modern descriptive names
- Custom prefixes

### Migration System

Automatic migration between versions:

- Preserves entity configurations
- Handles breaking changes
- Maintains compatibility

### Debug Logging

Comprehensive logging for troubleshooting:

- Modbus communication logs
- Entity creation logs
- Error tracking
- Performance metrics

## Related Documentation

- [Heating Curve Configuration](heating-curve.md)
- [Cycling Sensors](cycling-sensors.md)
- [Energy Consumption](energy-consumption.md)
- [Configuration Guide](configuration.md)

