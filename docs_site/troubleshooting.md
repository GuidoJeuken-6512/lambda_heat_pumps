# Troubleshooting

This guide helps you solve common issues with the Lambda Heat Pumps integration.

## Connection Issues

### Cannot Connect to Lambda Controller

**Symptoms:**
- Integration shows "Unavailable"
- Connection errors in logs

**Solutions:**
1. Verify IP address and port are correct
2. Check network connectivity
3. Ensure Modbus/TCP is enabled on the controller
4. Check firewall settings
5. Verify slave ID is correct

### Intermittent Connection Loss

**Symptoms:**
- Entities become unavailable periodically
- Connection timeouts

**Solutions:**
1. Check network stability
2. Increase update interval
3. Verify controller is not overloaded
4. Check for network interference

## Entity Issues

### Entities Not Appearing

**Symptoms:**
- Expected entities are missing
- Only some entities are created

**Solutions:**
1. Check firmware version setting
2. Verify module detection
3. Review integration logs
4. Restart Home Assistant

### Incorrect Values

**Symptoms:**
- Sensor values seem wrong
- Temperatures are off

**Solutions:**
1. Check register order configuration
2. Verify scaling factors
3. Check for firmware compatibility
4. Review Modbus register documentation

## Configuration Issues

### Configuration Not Saving

**Symptoms:**
- Changes don't persist
- Options reset after restart

**Solutions:**
1. Check file permissions
2. Verify YAML syntax
3. Review integration options
4. Check for conflicting configurations

### Migration Errors

**Symptoms:**
- Errors during version upgrade
- Entities missing after update

**Solutions:**
1. Check migration logs
2. Verify backup before upgrade
3. Review breaking changes in changelog
4. Report issue if migration fails

## Performance Issues

### High CPU Usage

**Symptoms:**
- Home Assistant becomes slow
- High CPU usage

**Solutions:**
1. Increase update interval
2. Reduce number of entities
3. Check for error loops in logs
4. Optimize Modbus reading

### Slow Updates

**Symptoms:**
- Entities update slowly
- Delayed responses

**Solutions:**
1. Check network latency
2. Reduce update frequency
3. Optimize batch reading
4. Check controller performance

## Getting Help

If you're still experiencing issues:

1. Check the [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
2. Enable debug logging:
   ```yaml
   logger:
     logs:
       custom_components.lambda_heat_pumps: debug
   ```
3. Collect relevant logs
4. Create a detailed issue report

## Related Documentation

- [Installation Guide](user/installation.md)
- [Configuration Guide](user/configuration.md)

