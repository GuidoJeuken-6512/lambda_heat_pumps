# Configuration

This guide covers all configuration options available for the Lambda Heat Pumps integration.

## Initial Setup

When you first add the integration, you'll need to provide:

- **Name**: A descriptive name for your Lambda installation
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Firmware Version**: Your Lambda controller's firmware version

## Integration Options

After initial setup, you can modify additional settings:

1. Go to **Settings → Devices & Services**
2. Find your Lambda Heat Pump integration
3. Click **Configure**

### Temperature Settings

#### Hot Water Temperature

- **Minimum Temperature**: Minimum hot water temperature (default: 25°C)
- **Maximum Temperature**: Maximum hot water temperature (default: 65°C)

#### Heating Circuit Temperature

- **Minimum Temperature**: Minimum heating circuit temperature
- **Maximum Temperature**: Maximum heating circuit temperature
- **Temperature Step**: Step size for temperature adjustments

### Advanced Features

#### Room Thermostat Control

Enable external sensor integration for precise temperature control:

- **Room Thermostat Control**: Enable/disable room thermostat integration
- **Room Temperature Offset**: Offset for room temperature readings
- **Room Temperature Factor**: Factor for room temperature calculations

#### PV Surplus Control

Solar power integration for optimal energy usage:

- **PV Surplus**: Enable/disable PV surplus control
- **PV Surplus Mode**: Operating mode for PV surplus control

## YAML Configuration

For advanced users, you can configure the integration via YAML:

```yaml
lambda_heat_pumps:
  name: "EU08L"
  host: "192.168.1.100"
  port: 502
  slave_id: 1
  firmware_version: "2.0"
  hot_water_min_temp: 25
  hot_water_max_temp: 65
  heating_circuit_min_temp: 20
  heating_circuit_max_temp: 60
  room_thermostat_control: true
  pv_surplus: true
```

## Debug Logging

To enable debug logging, add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.lambda_heat_pumps: debug
```

## Register Order Configuration

For 32-bit values from multiple 16-bit registers, you can configure the register order:

```yaml
lambda_heat_pumps:
  register_order: "low_high"  # or "high_low"
```

## Next Steps

- [Features Overview](features.md) - Learn about all available features
- [Heating Curve Configuration](heating-curve.md) - Configure heating curves
- [Troubleshooting](../../troubleshooting.md) - Solve configuration issues

