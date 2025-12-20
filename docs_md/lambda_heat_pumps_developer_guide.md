# Lambda Heat Pumps - Developer Guide

This guide provides information for developers who want to understand, modify, or extend the Lambda Heat Pumps integration for Home Assistant.

## Code Structure

The integration follows the standard Home Assistant custom component structure:

```
lambda_heat_pumps/
├── __init__.py          # Integration initialization
├── climate.py           # Climate entity implementation
├── config_flow.py       # Configuration flow UI
├── const.py             # Constants and configuration
├── coordinator.py       # Data update coordinator
├── manifest.json        # Integration manifest
├── sensor.py            # Sensor implementation
├── services.py          # Custom services
├── services.yaml        # Service definitions
├── utils.py             # Utility functions
├── translations/        # Translation files
```

## Key Classes

### Coordinator (coordinator.py)

The `LambdaDataUpdateCoordinator` is the core of the integration. It:
- Establishes and manages the Modbus connection
- Handles periodic data updates
- Processes the raw data into usable values
- Provides access to the data for all entities

Example of extending the coordinator to add a new data source:

```python
# In coordinator.py
async def _async_update_data(self):
    # Existing code...
    
    # Add new data source
    try:
        # Example: Read new device data
        new_device_data = await self._read_new_device_data()
        data.update(new_device_data)
    except Exception as ex:
        _LOGGER.error("Error reading new device data: %s", ex)
        
    # Continue with existing code...
    
async def _read_new_device_data(self):
    """Read data from a new device type."""
    result = {}
    # Implementation here
    return result
```

### Sensors (sensor.py)

Sensors are implemented using Home Assistant's entity model. The main class is `LambdaSensor` which extends `CoordinatorEntity` and `SensorEntity`.

To add a new sensor type:

1. Define the sensor template in `const.py`:

```python
NEW_SENSOR_TEMPLATES = {
    "new_sensor": {
        "relative_address": 123,
        "name": "New Sensor",
        "unit": "unit",
        "scale": 0.1,
        "precision": 1,
        "data_type": "int16",
        "firmware_version": 1,
        "device_type": "new_type",
        "writeable": False,
        "state_class": "measurement",
    },
    # More sensors...
}
```

2. Add the sensor creation logic in `sensor.py` similar to existing sensors.

### Climate Entities (climate.py)

The climate platform provides control interfaces for boilers and heating circuits. They utilize the coordinator for both reading and writing data.

## Key Functions

### Firmware Filtering

```python
def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version."""
    return {
        k: v
        for k, v in sensor_templates.items()
        if v.get("firmware_version", 1) <= fw_version
    }
```

This function filters sensors based on firmware compatibility, allowing sensors to be tied to specific firmware versions.

### Disabled Registers

```python
def is_register_disabled(address: int, disabled_registers: set[int]) -> bool:
    """Check if a register is disabled."""
    return address in disabled_registers
```

Allows problematic registers to be disabled via configuration.

## Testing

The integration includes a test suite using pytest. Run the tests with:

```bash
pytest tests/
```

To test a specific file:

```bash
pytest tests/test_sensor.py
```

## Adding New Device Types

To add support for a new type of device:

1. Define the base addresses in `const.py`:
```python
NEW_DEVICE_BASE_ADDRESS = {1: 7000, 2: 7100, 3: 7200}
```

2. Define sensor templates for the new device:
```python
NEW_DEVICE_SENSOR_TEMPLATES = {
    "error_number": {
        "relative_address": 0,
        "name": "Error Number",
        # ...other properties
    },
    # ...more sensors
}
```

3. Add the device to the coordinator's update method:
```python
# In _async_update_data
num_new_devices = self.entry.data.get("num_new_devices", 0)
new_device_templates = get_compatible_sensors(NEW_DEVICE_SENSOR_TEMPLATES, fw_version)
for new_device_idx in range(1, num_new_devices + 1):
    # Read sensors for this device
```

4. Add the device to the sensor and/or climate setup:
```python
# In sensor.py async_setup_entry
num_new_devices = entry.data.get("num_new_devices", 0)
for new_device_idx in range(1, num_new_devices + 1):
    # Create sensor entities
```

5. Update the configuration UI in `config_flow.py` to allow configuring the number of devices:
```python
vol.Required(
    "num_new_devices",
    default=int(
        user_input.get(
            "num_new_devices",
            existing_data.get(
                "num_new_devices",
                DEFAULT_NUM_NEW_DEVICES
            ),
        )
    ),
): selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0,
        max=MAX_NUM_NEW_DEVICES,
        step=1,
        mode=selector.NumberSelectorMode.BOX,
    )
)
```

## Modbus Communication

The integration uses the `pymodbus` library to communicate with the Lambda controller. The basic pattern is:

```python
# Connect to device
client = ModbusTcpClient(host, port=port)
if not client.connect():
    raise ConnectionError("Could not connect to Modbus TCP")

# Read registers
result = client.read_holding_registers(address, count, slave_id)
if result.isError():
    # Handle error
else:
    # Process data with endianness support
    if data_type == "int32":
        # Use configured endianness for proper byte order
        if self._endianness == "little":
            value = result.registers[0] | (result.registers[1] << 16)
        else:  # big-endian (default)
            value = (result.registers[0] << 16) | result.registers[1]
    else:
        value = result.registers[0]
    
    # Scale value
    scaled_value = value * scale_factor

# Write to registers
values = [int_value]
result = client.write_registers(address, values, slave_id)
if result.isError():
    # Handle error
```

### Endianness Configuration

The integration supports configurable byte order (endianness) for different Lambda models:

```python
# In coordinator.py
async def _load_endianness_config(self):
    """Load endianness configuration from lambda_wp_config.yaml."""
    config = await load_lambda_config(self.hass)
    self._endianness = config.get("endianness", "big")  # Default: big-endian
    
    # Legacy support for old configuration
    if not self._endianness:
        modbus_config = config.get("modbus", {})
        int32_byte_order = modbus_config.get("int32_byte_order", "big")
        self._endianness = "little" if int32_byte_order == "little" else "big"
```

### Energy Consumption Sensors

The integration includes advanced energy consumption tracking with sensor change detection:

```python
# In coordinator.py
async def _detect_and_handle_sensor_changes(self):
    """Detect and handle energy sensor changes."""
    for hp_idx, sensor_config in self._energy_sensor_configs.items():
        current_sensor_id = sensor_config.get("sensor_entity_id")
        stored_sensor_id = self._sensor_ids.get(f"hp{hp_idx}")
        
        if detect_sensor_change(stored_sensor_id, current_sensor_id):
            await self._handle_sensor_change(hp_idx, current_sensor_id)
        
        # Store new sensor ID
        store_sensor_id(self._persist_data, hp_idx, current_sensor_id)

async def _handle_sensor_change(self, hp_idx: int, new_sensor_id: str):
    """Handle sensor change with retry mechanism."""
    max_retries = 5
    retry_delay = 2.0
    
    for attempt in range(max_retries):
        new_sensor_state = self.hass.states.get(new_sensor_id)
        if new_sensor_state and new_sensor_state.state not in ("unknown", "unavailable"):
            new_sensor_value = float(new_sensor_state.state)
            self._last_energy_reading[f"hp{hp_idx}"] = new_sensor_value
            await self._persist_counters()
            return
        
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    
    # Fallback to 0 if sensor not available
    self._last_energy_reading[f"hp{hp_idx}"] = 0.0
```

### Cycling Sensors

The integration provides comprehensive cycling sensors with automatic reset functionality:

```python
# In coordinator.py
async def _track_hp_cycling(self, hp_idx: int, current_mode: int):
    """Track cycling with generalized reset functions."""
    hp_key = f"hp{hp_idx}"
    
    # Increment all cycling sensors simultaneously
    for sensor_type in ["total", "daily", "yesterday", "2h", "4h", "monthly", "yearly"]:
        if sensor_type in self._cycling_counters[hp_key]:
            self._cycling_counters[hp_key][sensor_type] += 1
    
    # Handle resets
    await self._handle_cycling_resets(hp_idx)

async def _handle_cycling_resets(self, hp_idx: int):
    """Handle all cycling resets with proper yesterday value handling."""
    hp_key = f"hp{hp_idx}"
    
    # Daily reset at midnight
    if self._should_reset_daily():
        # Store yesterday's value before reset
        self._cycling_counters[hp_key]["yesterday"] = self._cycling_counters[hp_key]["daily"]
        self._cycling_counters[hp_key]["daily"] = 0
    
    # Monthly reset on 1st of month
    if self._should_reset_monthly():
        self._cycling_counters[hp_key]["monthly"] = 0
    
    # Yearly reset on January 1st
    if self._should_reset_yearly():
        self._cycling_counters[hp_key]["yearly"] = 0
```

## Common Development Tasks

### Adding a New Entity Attribute

1. Add a new key to the sensor template in `const.py`
2. Update the `LambdaSensor` class in `sensor.py` to handle the new attribute
3. Add tests for the new attribute in `tests/test_sensor.py`

### Adding a Service

1. Define the service in `services.yaml`
2. Implement the service function in `services.py`
3. Register the service in `async_setup_services`
4. Add tests for the service in `tests/test_services.py`

### Supporting New Firmware

1. Add the new firmware version to `FIRMWARE_VERSION` in `const.py`
2. Add firmware-specific sensors with the appropriate `firmware_version` value
3. Test with both the new and existing firmware versions

## Best Practices

1. **Error Handling**: Always catch and log exceptions to prevent crashes
2. **Typing**: Use Python type hints for better code quality
3. **Logging**: Use appropriate log levels (`debug`, `info`, `warning`, `error`)
4. **Configuration**: Make features configurable when possible
5. **Tests**: Write tests for new functionality
6. **Documentation**: Update docs when adding features or changing behavior
7. **Backwards Compatibility**: Maintain compatibility with existing configurations

## Contributing

When contributing to the project:

1. Create a feature branch for your changes
2. Run the test suite to ensure everything works
3. Document your changes
4. Submit a pull request with a clear description of the changes

## Debugging Tips

- Enable debug logging in Home Assistant configuration:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.lambda_heat_pumps: debug
      pymodbus: debug
  ```

- Use the Home Assistant Developer Tools to inspect entity states and attributes

- For Modbus debugging, use a tool like mbpoll or modpoll to test register access directly:
  ```bash
  mbpoll -a 1 -r 1000 -c 10 -t 3 -1 192.168.1.100 502
  ```

## Modbus Tools for Testing and Development

For comprehensive testing and development of the Lambda Heat Pumps integration, a dedicated set of Modbus tools has been developed. These tools are available in the [modbus_tools repository](https://github.com/GuidoJeuken-6512/modbus_tools) and provide simulation capabilities for Lambda heat pump behavior.

### Overview

The Modbus Tools project contains three main components specifically designed for Lambda Heat Pumps integration development:

### 1. Modbus Client (GUI) (`client_gui.py`)

A graphical user interface for interactive Modbus TCP server querying:

- **Interactive GUI**: Easy-to-use interface for testing register access
- **Pre-configured Values**: Pre-filled with common Lambda heat pump register addresses
- **Flexible Configuration**: All values (host IP, register addresses, register types) are editable
- **Real-time Response**: Displays server responses in dialog windows
- **Perfect for**: Manual testing and debugging of specific register values

### 2. Modbus Client (CLI) (`client_cli.py`)

A command-line tool for automated Modbus TCP queries:

- **Automated Testing**: Reads predefined register groups (temperature, solar, etc.)
- **Automatic Scaling**: Applies scaling factors automatically based on register configuration
- **Extensive Logging**: INFO/ERROR logging for debugging and development
- **Scriptable**: Ideal for automated tests and CI/CD pipelines
- **Example Usage**: `python client_cli.py`
- **Perfect for**: Automated testing and quick register value verification

### 3. Modbus Server (`server.py`)

A complete Modbus TCP server implementation for simulation:

- **Lambda Simulation**: Simulates Lambda heat pump behavior and register responses
- **Configurable Registers**: Register values can be customized via `registers.yaml`
- **Realistic Data**: Provides realistic sensor values and operating modes
- **Flexible Logging**: Configurable logging options for different development needs
- **Perfect for**: Integration testing without physical hardware

#### Server Logging Configuration

The server provides flexible logging options for different development scenarios:

```python
# Logging configuration constants in server.py
LOG_ERRORS = True        # Controls logging of error messages
LOG_WRITE_REGISTERS = True  # Controls logging of write operations
LOG_READ_REGISTERS = False  # Controls logging of read operations
```

**Available Logging Options:**

1. **Error Logging** (`LOG_ERRORS`)
   - When `True`: Logs all error messages and write verification failures
   - When `False`: Suppresses error messages for cleaner output
   - Default: `True`

2. **Write Register Logging** (`LOG_WRITE_REGISTERS`)
   - When `True`: Logs all write operations to registers
   - When `False`: Suppresses write operation logs
   - Default: `True`

3. **Read Register Logging** (`LOG_READ_REGISTERS`)
   - When `True`: Logs all read operations from registers
   - When `False`: Suppresses read operation logs (recommended for high-frequency reads)
   - Default: `False`

### Setup and Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/GuidoJeuken-6512/modbus_tools.git
   cd modbus_tools
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Register Values** (for server):
   - Edit `registers.yaml` to customize register values
   - Modify `lambda.txt` for specific Lambda heat pump configurations

4. **Start the Modbus Server**:
   ```bash
   python server.py
   ```

5. **Test with Client Tools**:
   ```bash
   # GUI Client
   python client_gui.py
   
   # CLI Client
   python client_cli.py
   ```

### Integration with Lambda Heat Pumps Development

These tools are specifically designed to support the development of the Lambda Heat Pumps Home Assistant integration:

- **Register Testing**: Verify that the integration correctly reads and interprets register values
- **Endianness Testing**: Test both big-endian and little-endian configurations
- **Error Handling**: Simulate various error conditions and network issues
- **Performance Testing**: Test integration behavior under different load conditions
- **Feature Development**: Develop and test new features without physical hardware

### Dependencies

- **Python 3.7+**: Required for all components
- **PyYAML**: For register configuration file parsing (automatically uses C-optimized `_yaml` if available)
- **pymodbus**: For Modbus TCP communication
- **tkinter**: For GUI client (usually included with Python)

### Disclaimer

These tools are provided for development and testing purposes. Use at your own risk. No liability is accepted for any damages, data loss, or other consequences resulting from the use of these tools.

For more information and the latest updates, visit the [modbus_tools repository](https://github.com/GuidoJeuken-6512/modbus_tools).

## Modbus Register Services

The integration provides two Home Assistant services for advanced Modbus access:
- `lambda_heat_pumps.read_modbus_register`: Read any Modbus register from the Lambda controller.
- `lambda_heat_pumps.write_modbus_register`: Write a value to any Modbus register of the Lambda controller.

These services are defined in `services.py` and documented in `services.yaml`.

## Template-based Climate Entities

All climate entities (boiler, heating circuit) are now defined by templates in `const.py`. This allows for easy extension and central management of entity properties.

## Dynamic Entity Creation

Heating circuit climate entities are only created if a room thermostat sensor is configured for the respective circuit in the integration options.

## New Features (Version 1.4.0)

### Automatic Configuration

The integration now supports automatic configuration detection:

```python
# In config_flow.py
async def async_step_dhcp(self, discovery_info):
    """Handle DHCP discovery."""
    # Auto-detect existing configurations
    existing_entries = self._async_current_entries()
    for entry in existing_entries:
        if entry.data.get("host") == discovery_info.ip:
            return self.async_abort(reason="already_configured")
    
    # Create new entry with discovered IP
    return self.async_create_entry(
        title=f"Lambda Heat Pump ({discovery_info.ip})",
        data={
            "host": discovery_info.ip,
            "port": 502,
            "slave_id": 1,
        }
    )
```

### Energy Consumption Sensors

Advanced energy tracking with configurable source sensors:

```python
# In coordinator.py
async def _track_hp_energy_consumption(self, hp_idx: int, current_mode: int):
    """Track energy consumption by operating mode."""
    hp_key = f"hp{hp_idx}"
    sensor_config = self._energy_sensor_configs.get(hp_idx, {})
    source_sensor_id = sensor_config.get("sensor_entity_id")
    
    if not source_sensor_id:
        return
    
    # Get current sensor value with unit conversion
    source_state = self.hass.states.get(source_sensor_id)
    if source_state and source_state.state not in ("unknown", "unavailable"):
        current_value = float(source_state.state)
        unit = source_state.attributes.get("unit_of_measurement", "")
        
        # Convert to kWh
        current_kwh = convert_energy_to_kwh(current_value, unit)
        
        # Calculate delta and update counters
        last_value = self._last_energy_reading.get(hp_key, 0.0)
        delta = max(0, current_kwh - last_value)
        
        # Update energy consumption by mode
        mode_key = f"{hp_key}_{current_mode}"
        if mode_key in self._energy_consumption:
            self._energy_consumption[mode_key] += delta
        
        self._last_energy_reading[hp_key] = current_kwh
```

### Sensor Change Detection

Automatic detection and handling of energy sensor changes:

```python
# In utils.py
def detect_sensor_change(stored_sensor_id: str, current_sensor_id: str) -> bool:
    """Detect sensor change by comparing stored and current sensor IDs."""
    if not stored_sensor_id:
        return False
    
    return stored_sensor_id != current_sensor_id

def convert_energy_to_kwh(value: float, unit: str) -> float:
    """Convert energy values to kWh based on unit."""
    if not unit:
        # Estimate based on value size
        if value > 10000:  # Probably Wh
            return value / 1000.0
        return value
    
    unit_lower = unit.lower().strip()
    
    if unit_lower in ["wh", "wattstunden"]:
        return value / 1000.0
    elif unit_lower in ["kwh", "kilowattstunden"]:
        return value
    elif unit_lower in ["mwh", "megawattstunden"]:
        return value * 1000.0
    else:
        # Unknown unit - estimate based on value size
        if value > 10000:
            return value / 1000.0
        return value
```

### Enhanced Cycling Sensors

Comprehensive cycling tracking with multiple time periods:

```python
# In coordinator.py
async def _setup_cycling_sensors(self):
    """Setup cycling sensors for all heat pumps."""
    for hp_idx in range(1, self._num_heat_pumps + 1):
        hp_key = f"hp{hp_idx}"
        
        # Initialize cycling counters
        self._cycling_counters[hp_key] = {
            "total": 0,
            "daily": 0,
            "yesterday": 0,
            "2h": 0,
            "4h": 0,
            "monthly": 0,
            "yearly": 0,
        }
        
        # Load persisted values
        if hp_key in self._persist_data.get("cycling_counters", {}):
            self._cycling_counters[hp_key].update(
                self._persist_data["cycling_counters"][hp_key]
            )
```

### Configuration File Support

The integration now supports configuration via `lambda_wp_config.yaml`:

```yaml
# lambda_wp_config.yaml
endianness: "big"  # or "little"

energy_consumption_sensors:
  1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"
  2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch_2"

cycling_offsets:
  1:
    total: 1000
    daily: 50
  2:
    total: 2000
    daily: 100
```

### Persistence and State Management

Enhanced persistence for all sensor data:

```python
# In coordinator.py
async def _persist_counters(self):
    """Persist all counter data to JSON file."""
    self._persist_data.update({
        "last_energy_reading": self._last_energy_reading,
        "energy_consumption": self._energy_consumption,
        "cycling_counters": self._cycling_counters,
        "sensor_ids": self._sensor_ids,
        "last_reset_daily": self._last_reset_daily,
        "last_reset_monthly": self._last_reset_monthly,
        "last_reset_yearly": self._last_reset_yearly,
    })
    
    await self.hass.async_add_executor_job(
        _write_persist, self._persist_file, self._persist_data
    )
```
