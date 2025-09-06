# Lambda Heat Pumps - Robustness Features

## Overview

This document describes the robustness features implemented in the Lambda Heat Pumps Home Assistant custom integration to handle network interruptions, communication errors, and improve overall system stability.

## Table of Contents

1. [Features Overview](#features-overview)
2. [Configuration](#configuration)
3. [Individual Reads](#individual-reads)
4. [Timeout Management](#timeout-management)
5. [Multi-Client Anti-Synchronization](#multi-client-anti-synchronization)
6. [Circuit Breaker Pattern](#circuit-breaker-pattern)
7. [Exponential Backoff](#exponential-backoff)
8. [Troubleshooting](#troubleshooting)
9. [Performance Monitoring](#performance-monitoring)

## Features Overview

The integration includes several robustness features designed to handle various failure scenarios:

- **Individual Reads**: Problematic registers are read individually instead of in batches
- **Dynamic Timeout Adjustment**: Sensor-specific timeouts based on register performance
- **Multi-Client Anti-Synchronization**: Prevents Modbus conflicts in multi-client environments
- **Circuit Breaker Pattern**: Temporarily stops operations to failing services
- **Exponential Backoff**: Intelligent retry logic with jitter
- **Offline Data Handling**: Persists last known values during network outages

## Configuration

All robustness features are configured in `const.py`:

```python
# Modbus Configuration
LAMBDA_MODBUS_TIMEOUT = 3        # Base Modbus timeout in seconds
LAMBDA_MAX_RETRIES = 3           # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5           # Delay between retries in seconds

# Register-specific Timeouts (absolute addresses)
LAMBDA_REGISTER_TIMEOUTS = {
    0: 1,     # Register 0 - very short timeout (well under HA 10s limit)
    1050: 1,  # Register 1050 - very short timeout (batch read problems)
    1060: 1,  # Register 1060 - very short timeout (batch read problems)
}

# Individual Reads for problematic registers (absolute addresses)
LAMBDA_INDIVIDUAL_READ_REGISTERS = [0, 1050, 1060]  # Read individually

# Low Priority Registers (read last)
LAMBDA_LOW_PRIORITY_REGISTERS = [0, 1050, 1060]     # Low priority

# Multi-client Modbus Configuration
LAMBDA_MULTI_CLIENT_SUPPORT = True
LAMBDA_BASE_UPDATE_INTERVAL = 60  # Base interval in seconds
LAMBDA_RANDOM_INTERVAL_RANGE = 5  # Random deviation ±5 seconds
LAMBDA_MIN_INTERVAL = 45          # Minimum interval
LAMBDA_MAX_INTERVAL = 75          # Maximum interval

# Circuit Breaker Configuration
LAMBDA_CIRCUIT_BREAKER_ENABLED = True
LAMBDA_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3  # Open after 3 failures
LAMBDA_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # Recovery timeout in seconds
```

## Individual Reads

### Problem
Some Modbus registers cause timeouts when read in batches, leading to "Batch read failed" errors and HA 10-second timeout warnings.

### Solution
Problematic registers are automatically read individually instead of in batches.

### Configuration
```python
# Static configuration - registers that should always be read individually
LAMBDA_INDIVIDUAL_READ_REGISTERS = [0, 1050, 1060]

# Dynamic addition - registers added at runtime based on performance
# Thresholds: 3 timeouts or 5 failures trigger individual reads
```

### How it Works
1. **Static Individual Reads**: Configured registers are immediately read individually
2. **Dynamic Addition**: Registers with repeated timeouts/failures are automatically added
3. **Performance Tracking**: System tracks timeout and failure counters per register
4. **Automatic Recovery**: Registers can be moved back to batch reads if performance improves

### Logging
```
INFO: 🔧 INDIVIDUAL-READ: Using individual read for register 0 - configured for individual reading
INFO: 🔄 DYNAMIC-INDIVIDUAL: Register 1000 added to Individual-Reads after 3 timeouts
```

## Timeout Management

### Problem
Home Assistant shows "Update of sensor is taking over 10 seconds" warnings when Modbus reads take too long.

### Solution
Sensor-specific timeouts that are much shorter than HA's 10-second limit.

### Configuration
```python
# Register-specific timeouts (in seconds)
LAMBDA_REGISTER_TIMEOUTS = {
    0: 1,     # error_state - 1 second timeout
    1050: 1,  # Register 1050 - 1 second timeout
    1060: 1,  # Register 1060 - 1 second timeout
}

# Base Modbus timeout
LAMBDA_MODBUS_TIMEOUT = 3  # 3 seconds for all other registers
```

### How it Works
1. **Priority Timeouts**: Critical registers get very short timeouts (1s)
2. **Fallback Timeout**: Other registers use the base timeout (3s)
3. **HA Compatibility**: All timeouts are well under HA's 10s limit
4. **Automatic Adjustment**: System can dynamically adjust timeouts based on performance

### Logging
```
INFO: ⏱️ TIMEOUT-ADJUST: Using sensor-specific timeout 1s for register 0 - reduced from default 3s
```

## Multi-Client Anti-Synchronization

### Problem
Multiple clients accessing the same Lambda heat pump via Modbus can cause conflicts and timeouts.

### Solution
Randomized update intervals to prevent synchronized access.

### Configuration
```python
LAMBDA_MULTI_CLIENT_SUPPORT = True
LAMBDA_BASE_UPDATE_INTERVAL = 60  # Base interval in seconds
LAMBDA_RANDOM_INTERVAL_RANGE = 5  # Random deviation ±5 seconds
LAMBDA_MIN_INTERVAL = 45          # Minimum interval
LAMBDA_MAX_INTERVAL = 75          # Maximum interval
LAMBDA_ANTI_SYNC_ENABLED = True
LAMBDA_ANTI_SYNC_FACTOR = 0.2     # 20% jitter variation
```

### How it Works
1. **Base Interval**: All coordinators start with the same base interval (60s)
2. **Random Jitter**: Each coordinator adds random variation (±5s)
3. **Range Limits**: Final interval is constrained between 45-75 seconds
4. **Anti-Synchronization**: Different intervals prevent simultaneous Modbus access

### Benefits
- **Reduced Conflicts**: Clients access Lambda at different times
- **Better Performance**: Fewer Modbus collisions
- **Automatic**: No manual configuration required

## Circuit Breaker Pattern

### Problem
Repeated failures can overwhelm the system and cause cascading errors.

### Solution
Temporarily stop operations to failing services to allow recovery.

### Configuration
```python
LAMBDA_CIRCUIT_BREAKER_ENABLED = True
LAMBDA_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3  # Open after 3 failures
LAMBDA_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # Recovery timeout in seconds
```

### How it Works
1. **Failure Tracking**: System counts consecutive failures
2. **Circuit Opening**: After threshold failures, circuit opens
3. **Recovery Period**: Circuit stays open for recovery timeout
4. **Automatic Recovery**: Circuit closes after successful operations

### States
- **CLOSED**: Normal operation, requests allowed
- **OPEN**: Circuit open, requests blocked
- **HALF_OPEN**: Testing recovery, limited requests allowed

## Exponential Backoff

### Problem
Immediate retries after failures can worsen the situation.

### Solution
Intelligent retry logic with increasing delays and jitter.

### Configuration
```python
LAMBDA_MAX_RETRIES = 3      # Maximum retry attempts
LAMBDA_RETRY_DELAY = 5      # Base delay between retries
```

### How it Works
1. **Exponential Delays**: Each retry waits longer (5s, 10s, 20s)
2. **Jitter**: Random variation prevents thundering herd
3. **Maximum Cap**: Delays are capped at 30 seconds
4. **Minimum Delay**: Delays never go below 1 second

### Retry Sequence
- **Attempt 1**: Immediate
- **Attempt 2**: 5s ± 20% jitter
- **Attempt 3**: 10s ± 20% jitter
- **Attempt 4**: 20s ± 20% jitter

## Troubleshooting

### Common Issues

#### HA 10-Second Timeout Warnings
**Symptoms**: `WARNING: Update of sensor is taking over 10 seconds`

**Solutions**:
1. Check if register is in `LAMBDA_INDIVIDUAL_READ_REGISTERS`
2. Verify timeout is set in `LAMBDA_REGISTER_TIMEOUTS`
3. Increase update interval in `LAMBDA_BASE_UPDATE_INTERVAL`

#### Batch Read Failures
**Symptoms**: `ERROR: Batch read failed for 1050-1060`

**Solutions**:
1. Add problematic registers to `LAMBDA_INDIVIDUAL_READ_REGISTERS`
2. Check if registers are in `LAMBDA_LOW_PRIORITY_REGISTERS`
3. Verify Modbus connection stability

#### Circuit Breaker Open
**Symptoms**: `DEBUG: Circuit breaker is OPEN - skipping Modbus read`

**Solutions**:
1. Wait for recovery timeout period
2. Check network connectivity
3. Verify Lambda heat pump is responding

### Debugging

#### Enable Debug Logging
```python
# In const.py
LAMBDA_DEBUG_MODE = True
```

#### Check Individual Reads
```python
# Look for these log messages:
INFO: 🔧 INDIVIDUAL-READ: Using individual read for register X
INFO: 🔄 DYNAMIC-INDIVIDUAL: Register X added to Individual-Reads
```

#### Monitor Timeout Adjustments
```python
# Look for these log messages:
INFO: ⏱️ TIMEOUT-ADJUST: Using sensor-specific timeout Xs for register Y
```

## Performance Monitoring

### Key Metrics

#### Individual Read Performance
- **Static Individual Reads**: Pre-configured registers
- **Dynamic Individual Reads**: Auto-added registers
- **Success Rate**: Percentage of successful individual reads

#### Timeout Performance
- **Timeout Adjustments**: Number of registers with custom timeouts
- **HA Warnings**: Count of 10-second timeout warnings
- **Average Read Time**: Time taken for Modbus operations

#### Circuit Breaker Performance
- **Circuit State**: CLOSED/OPEN/HALF_OPEN
- **Failure Count**: Consecutive failures
- **Recovery Time**: Time to recover from failures

### Log Analysis

#### Successful Operation
```
INFO: ⏱️ TIMEOUT-ADJUST: Using sensor-specific timeout 1s for register 0
INFO: 🔧 INDIVIDUAL-READ: Using individual read for register 0
INFO: Circuit breaker is CLOSED - operation allowed
```

#### Problem Detection
```
INFO: 🔄 DYNAMIC-INDIVIDUAL: Register 1000 added to Individual-Reads after 3 timeouts
WARNING: Update of sensor.eu08l_hp1_error_state is taking over 10 seconds
DEBUG: Circuit breaker is OPEN - skipping Modbus read
```

## Best Practices

### Configuration
1. **Start Conservative**: Begin with default settings
2. **Monitor Performance**: Watch logs for timeout warnings
3. **Add Problematic Registers**: Move failing registers to individual reads
4. **Adjust Timeouts**: Reduce timeouts for critical registers

### Maintenance
1. **Regular Log Review**: Check for new problematic registers
2. **Performance Monitoring**: Track success rates and response times
3. **Configuration Updates**: Adjust settings based on observed behavior
4. **Network Stability**: Ensure stable network connection to Lambda

### Troubleshooting
1. **Enable Debug Logging**: For detailed operation information
2. **Check Individual Reads**: Verify problematic registers are handled
3. **Monitor Circuit Breaker**: Ensure proper failure handling
4. **Network Diagnostics**: Verify Modbus connectivity

## Conclusion

The robustness features provide comprehensive protection against various failure scenarios while maintaining optimal performance. The system automatically adapts to problematic registers and network conditions, ensuring reliable operation of the Lambda Heat Pumps integration.

For additional support or feature requests, please refer to the project documentation or create an issue in the project repository.
