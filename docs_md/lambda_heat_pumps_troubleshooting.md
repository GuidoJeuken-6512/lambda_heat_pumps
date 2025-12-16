# Lambda Heat Pumps - Troubleshooting Guide

This document provides solutions to common problems encountered when using the Lambda Heat Pumps integration with Home Assistant.

## Connection Issues

### Cannot Connect to Lambda Controller

If you receive a "Cannot connect" error during setup:

1. **Check Network Connectivity**
   - Verify that the Lambda controller is powered on and connected to your network
   - Try to ping the controller from your Home Assistant host: `ping <your-controller-ip>`
   - Check if there are any firewalls blocking port 502 (Modbus TCP)

2. **Verify Modbus Settings**
   - Confirm that the Modbus TCP port is set to 502 (or your custom port)
   - Verify that the Slave ID (typically 1) is correct
   - Check if Modbus TCP is enabled in your Lambda controller settings

3. **Network Configuration**
   - If your Lambda controller is on a different subnet, ensure proper routing is configured

### Connection Timeouts

If the integration connects but frequently times out:

1. Check for network stability issues
2. Try increasing the polling interval in the integration options
3. Make sure no other device is actively writing to the same Modbus registers

## Entity Issues

### MODBUS READ FAILED Errors

If you see repeated log messages like `❌ MODBUS READ FAILED: address=2004, error=...`:

**What it means:**
- The integration tried to read a Modbus register from your Lambda controller
- The read operation failed, which could indicate:
  - The register is not available on your specific device/model
  - The register is only available under certain conditions
  - A temporary communication issue occurred

**When to take action:**
- If the same address appears repeatedly in the logs (e.g., address=2004 appears consistently)
- If the error message includes "Considering disabling the register" (this indicates a systematic problem)
- This suggests the register is not available on your Wärmepumpe (heat pump) model

**Solution:**
Disable the problematic register in your `lambda_wp_config.yaml` file:

```yaml
disabled_registers:
  - 2004  # Example: Disable register 2004 if it's not available
  - 2005  # Add other problematic register addresses here
```

For more details about configuration options, see [Lambda WP Configuration Reference](lambda_wp_config_reference.md).

**Note:** Some registers may be model-specific. If a register consistently fails, it's safe to disable it - the integration will skip reading it, preventing unnecessary error messages in your logs.

### Missing Entities

If some expected entities are not appearing:

1. Check your device counts in the integration configuration (heat pumps, heating circuits, etc.)
2. Verify that the devices are actually present and configured in your Lambda system
3. Review logs for any entity initialization errors

### Incorrect Values

If entities show incorrect or implausible values:

1. Verify the firmware version setting matches your Lambda controller
2. Check if the entity is properly registered in the Lambda controller
3. Compare values with those shown directly on the Lambda controller

## Climate Control Issues

### Heating Circuit Not Responding

If the heating circuit climate entity doesn't respond to changes:

1. Check if the operating mode is set to a mode that allows changes (AUTOMATIC, not MANUAL)
2. Verify if write access is enabled for the relevant Modbus registers
3. Check if the temperature setpoint is within the valid range (15.0°C - 65.0°C)

### Boiler Not Heating

If the hot water boiler is not responding to temperature changes:

1. Verify the boiler's operating state (should not be in ERROR or OFF state)
2. Check if the maximum boiler temperature setting is properly configured
3. Ensure the setpoint temperature is below the maximum allowed temperature

## Room Temperature Update Issues

If the room temperature update service is not working:

1. Verify that room thermostat control is enabled in the integration options
2. Check if the source sensor entity exists and provides valid temperature values
3. Ensure the heating circuit is configured to accept external room temperature inputs

## Log Analysis

To enable debug logging for the Lambda integration:

1. Add the following to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.lambda_heat_pumps: debug
   ```
2. Restart Home Assistant
3. Check the logs for error messages related to the Lambda integration

## Reset Procedure

If you encounter persistent issues:

1. Remove the integration from Home Assistant
2. Restart Home Assistant
3. Clear browser cache
4. Re-add the integration with correct settings

## Contact Support

If you continue to experience issues after trying these troubleshooting steps:

1. Gather your Home Assistant logs with debug logging enabled
2. Create an issue on the GitHub repository with:
   - Description of the problem
   - Steps to reproduce
   - Home Assistant version
   - Lambda controller firmware version
   - Log excerpts showing the issue
