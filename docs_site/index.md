# Lambda Heat Pumps Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40GuidoJeuken--6512-blue.svg)](https://github.com/GuidoJeuken-6512)
[![version](https://img.shields.io/badge/version-2.0.1-blue.svg)](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/blob/main/LICENSE)

**Lambda Heat Pumps** is a Home Assistant custom integration for Lambda heat pumps via Modbus/TCP.

## Quick Start

### HACS Installation

1. Install HACS (if not already done)
2. Search for "Lambda heat pumps" and download the integration
3. Restart Home Assistant
4. Go to **Settings → Devices & Services**
5. Click **Add Integration** and search for "Lambda Heat Pumps"

### Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "EU08L")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Firmware Version**: Select your Lambda controller's firmware version

Everything else will be configured automatically.

## Key Features

- **Full Modbus/TCP Support**: Complete support for Lambda heat pumps via Modbus/TCP
- **Automatic Module Detection**: Auto-detects available modules and creates appropriate entities
- **Heating Curve Configuration**: Number entities for easy adjustment of heating curve support points
- **Cycling Sensors**: Comprehensive cycling counters for all operating modes
- **Energy Consumption Sensors**: Detailed energy tracking by operating mode
- **Room Thermostat Control**: External sensor integration for precise temperature control
- **PV Surplus Control**: Solar power integration for optimal energy usage

## Documentation

### For Users

- [Installation Guide](user/installation.md) - How to install and set up the integration
- [Configuration](user/configuration.md) - Detailed configuration options
- [Features](user/features.md) - Overview of all available features
- [Heating Curve](user/heating-curve.md) - Heating curve configuration guide
- [Cycling Sensors](user/cycling-sensors.md) - Understanding cycling sensors
- [Energy Consumption](user/energy-consumption.md) - Energy tracking features

### For Developers

- [Architecture](developer/architecture.md) - System architecture and design
- [Entity Creation](developer/entity-creation.md) - How entities are created
- [Modbus Registers](developer/modbus-registers.md) - Modbus register documentation
- [Migration System](developer/migration-system.md) - Version migration system
- [Contributing](developer/contributing.md) - How to contribute to the project

## Support

- [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
- [Troubleshooting Guide](troubleshooting.md)
- [Home Assistant Community](https://community.home-assistant.io/)

## License

MIT License - See [LICENSE](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/blob/main/LICENSE) for details.

---

**Developed with ❤️ for the Home Assistant Community**

