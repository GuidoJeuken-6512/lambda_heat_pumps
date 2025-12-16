# Heating Curve Configuration

The heating curve configuration allows you to fine-tune how your heat pump responds to outside temperature changes.

## Overview

The heating curve defines the relationship between outside temperature and flow temperature. The integration uses three support points to create a linear interpolation curve.

## Support Points

### Cold Point (-22°C)

The flow temperature when the outside temperature is very cold (-22°C).

### Mid Point (0°C)

The flow temperature at moderate outside temperatures (0°C).

### Warm Point (+22°C)

The flow temperature when the outside temperature is warm (+22°C).

## Configuration

### Number Entities

For each heating circuit (HC1, HC2, etc.), the following Number entities are automatically created:

- `number.*_hc1_heating_curve_cold_outside_temp` - Cold point at -22°C
- `number.*_hc1_heating_curve_mid_outside_temp` - Mid point at 0°C
- `number.*_hc1_heating_curve_warm_outside_temp` - Warm point at +22°C

### Flow Line Offset

The **Flow Line Offset** allows fine-tuning of the calculated heating curve flow temperature:

- **Range**: -10.0°C to +10.0°C
- **Step Size**: 0.1°C
- **Modbus Register**: Register 50 (relative to the heating circuit's base address)
- **Bidirectional Synchronization**: Reads current value from Modbus register and writes changes directly back

**Example**: If the calculated heating curve temperature is 35.0°C and you set an offset of +2.0°C, the actual flow temperature will be increased to 37.0°C.

## Usage

1. Go to **Settings → Devices & Services**
2. Select your heating circuit (e.g., "HC1")
3. Find the Number entities section
4. Adjust the heating curve support points as needed
5. Optionally adjust the flow line offset for fine-tuning

## Best Practices

- Start with default values and adjust gradually
- Monitor system performance after changes
- Consider seasonal adjustments
- Use the flow line offset for minor adjustments

## Related Documentation

- [Configuration Guide](configuration.md)
- [Features Overview](features.md)

