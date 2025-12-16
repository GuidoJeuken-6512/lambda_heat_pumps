# Architecture

This document describes the architecture and design of the Lambda Heat Pumps integration.

## Overview

The Lambda Heat Pumps integration is built on Home Assistant's modern integration framework, using:

- **Data Update Coordinator**: Centralized data management
- **Platform-based Entities**: Modular entity creation
- **Modbus/TCP Communication**: pymodbus library
- **Configuration Flow**: User-friendly setup

## System Components

### Core Components

```
┌─────────────────────────────────────────┐
│         Home Assistant Core              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Lambda Heat Pumps Integration      │
│  ┌──────────────────────────────────┐ │
│  │   Config Flow (config_flow.py)   │ │
│  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────┐ │
│  │  Coordinator (coordinator.py)    │ │
│  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────┐ │
│  │   Modbus Utils (modbus_utils.py) │ │
│  └──────────────────────────────────┘ │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Modbus/TCP Interface            │
│         (Lambda Controller)            │
└─────────────────────────────────────────┘
```

### Entity Platforms

The integration uses multiple platforms:

- **Sensor Platform**: Reading sensors from Modbus
- **Climate Platform**: Temperature control
- **Number Platform**: Configuration entities
- **Template Sensor Platform**: Calculated sensors

## Data Flow

### Reading Data

1. **Coordinator** initiates update cycle
2. **Modbus Utils** reads registers from Lambda controller
3. **Coordinator** processes and caches data
4. **Entities** update their state from coordinator cache

### Writing Data

1. **Entity** receives user action (e.g., set temperature)
2. **Entity** validates input
3. **Modbus Utils** writes to Modbus register
4. **Coordinator** updates cache
5. **Entity** updates state

## Coordinator Pattern

The `LambdaDataUpdateCoordinator` manages:

- Modbus connection lifecycle
- Data update scheduling
- Entity state caching
- Error handling and retries
- Persistent data storage

## Entity Creation

Entities are created dynamically based on:

- Detected hardware modules
- Configuration options
- Firmware version
- User preferences

See [Entity Creation Guide](entity-creation.md) for details.

## Modbus Communication

### Register Addressing

- **Base Addresses**: Starting addresses for each module type
- **Relative Addresses**: Offsets from base addresses
- **Register Types**: Holding registers, input registers

### Data Types

- **16-bit integers**: Signed and unsigned
- **32-bit integers**: From multiple 16-bit registers
- **Floating point**: Scaled integer values

See [Modbus Registers Documentation](modbus-registers.md) for details.

## Migration System

The integration includes a migration system for:

- Version upgrades
- Breaking changes
- Entity registry updates
- Configuration updates

See [Migration System Guide](migration-system.md) for details.

## Error Handling

### Connection Errors

- Automatic retry with exponential backoff
- Connection state tracking
- User notifications

### Data Errors

- Validation of register values
- Fallback to default values
- Error logging

## Performance Considerations

- **Caching**: Coordinator caches all register values
- **Batch Reading**: Multiple registers read in single request
- **Update Intervals**: Configurable update frequency
- **Lazy Loading**: Entities created only when needed

## Related Documentation

- [Entity Creation](entity-creation.md)
- [Modbus Registers](modbus-registers.md)
- [Migration System](migration-system.md)
- [Contributing Guide](contributing.md)

