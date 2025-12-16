# Modbus Registers

This document describes the Modbus register structure used by the Lambda Heat Pumps integration.

## Overview

The integration communicates with Lambda controllers via Modbus/TCP, reading and writing to specific registers.

## Register Addressing

### Base Addresses

Each module type has a base address:

- **Heat Pumps**: Starting at 4000
- **Boilers**: Starting at 4500
- **Buffers**: Starting at 4700
- **Heating Circuits**: Starting at 5000 (HC1), 5100 (HC2), etc.
- **Solar Modules**: Starting at 6000

### Relative Addresses

Registers are addressed relative to the base address:

- **Register 0**: First register of the module
- **Register 6**: Operating mode (for heating circuits)
- **Register 50**: Flow line offset (for heating circuits)

## Register Types

### Holding Registers

Read/write registers for configuration:

- Temperature settings
- Operating modes
- Configuration parameters

### Input Registers

Read-only registers for status:

- Current temperatures
- System status
- Sensor readings

## Data Types

### 16-bit Integers

Single register values:

- Signed integers: -32768 to 32767
- Unsigned integers: 0 to 65535

### 32-bit Integers

Two register values:

- Low-high order
- High-low order
- Configurable via `register_order`

### Scaled Values

Floating point values stored as scaled integers:

- Temperature: Register value × 0.1
- Pressure: Register value × 0.01

## Reading Registers

### Batch Reading

Multiple registers read in a single request:

```python
registers = await client.read_holding_registers(
    address=base_address,
    count=100,
    slave=slave_id
)
```

### Error Handling

- Retry logic for connection errors
- Validation of register values
- Fallback to default values

## Writing Registers

### Single Register Write

```python
await client.write_register(
    address=base_address + offset,
    value=scaled_value,
    slave=slave_id
)
```

### Multiple Register Write

```python
await client.write_registers(
    address=base_address,
    values=[value1, value2, value3],
    slave=slave_id
)
```

## Register Documentation

For detailed register mappings, see the Lambda Modbus documentation.

## Related Documentation

- [Architecture](architecture.md)
- [Entity Creation](entity-creation.md)

