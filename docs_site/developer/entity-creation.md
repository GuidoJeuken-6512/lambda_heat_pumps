# Entity Creation

This document describes how entities are created in the Lambda Heat Pumps integration.

## Overview

Entities are created dynamically based on:

- Detected hardware modules
- Configuration options
- Firmware version
- User preferences

## Entity Types

### Sensor Entities

Sensor entities read values from Modbus registers:

- Temperature sensors
- Status sensors
- Cycling sensors
- Energy consumption sensors

### Climate Entities

Climate entities provide temperature control:

- Hot water climate
- Heating circuit climate

### Number Entities

Number entities allow configuration:

- Heating curve parameters
- Flow line offset
- Room thermostat parameters

## Creation Process

### 1. Module Detection

The integration automatically detects available modules:

- Heat pumps
- Boilers
- Buffers
- Solar modules
- Heating circuits

### 2. Entity Generation

Based on detected modules, entities are generated:

- Sensor templates define entity structure
- Base addresses are calculated
- Entity names are generated

### 3. Entity Registration

Entities are registered with Home Assistant:

- Unique IDs are assigned
- Device information is set
- Entity attributes are configured

## Entity Naming

### Legacy Names

Compatible with older configurations:

```
sensor.EU08L_hp1_temperature
```

### Modern Names

Descriptive, user-friendly names:

```
sensor.eu08l_heat_pump_1_temperature
```

## Configuration

### Entity Prefixes

Configure custom prefixes:

```yaml
lambda_heat_pumps:
  name_prefix: "MyHeatPump"
```

### Entity Filtering

Filter which entities are created:

```yaml
lambda_heat_pumps:
  create_entities:
    sensors: true
    climate: true
    numbers: true
```

## Related Documentation

- [Architecture](architecture.md)
- [Modbus Registers](modbus-registers.md)

