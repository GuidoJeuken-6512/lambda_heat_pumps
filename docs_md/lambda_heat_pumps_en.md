# Lambda Heat Pumps Integration for Home Assistant

The Lambda Heat Pumps integration is a custom component for Home Assistant that establishes a connection to Lambda heat pumps via the Modbus TCP/RTU protocol. This documentation describes the structure and functionality of the integration.

## Table of Contents

1. [Integration Structure](#integration-structure)
2. [Sensor Types](#sensor-types)
3. [Sensor Initialization](#sensor-initialization)
4. [Sensor Data Retrieval](#sensor-data-retrieval)
5. [Configuration](#configuration)
6. [Function Overview](#function-overview)
7. [Modbus Register Services](#modbus-register-services)
8. [Dynamic Entity Creation](#dynamic-entity-creation)
9. [Template-based Climate Entities](#template-based-climate-entities)
10. [New Features (Version 1.4.0)](#new-features-version-140)
11. [Automatic Configuration](#automatic-configuration)
12. [Energy Consumption Sensors](#energy-consumption-sensors)
13. [Cycling Sensors](#cycling-sensors)
14. [Endianness Configuration](#endianness-configuration)
15. [Sensor Change Detection](#sensor-change-detection)
16. [Modbus Tools for Testing](#modbus-tools-for-testing)

## Integration Structure

The integration consists of the following main components:

- **__init__.py**: Main entry point of the integration, registers the component with Home Assistant
- **config_flow.py**: User interface for configuring the integration
- **const.py**: Constants and configuration values, including sensor types and register addresses
- **coordinator.py**: Data coordinator that manages data exchange with the heat pump
- **sensor.py**: Implementation of sensors for various heat pump parameters
- **climate.py**: Implementation of climate entities for heating and hot water
- **services.py**: Service functions, e.g., for room temperature retrieval
- **utils.py**: Helper functions for the entire integration

The integration supports various devices:
- Up to 3 Heat Pumps
- Up to 5 Boilers
- Up to 12 Heating Circuits
- Up to 5 Buffers
- Up to 2 Solar systems

## Sensor Types

The integration supports various sensor types defined in `const.py`:

### General Sensors (SENSOR_TYPES)
- Ambient temperature
- Error numbers
- Operating states
- E-Manager values (power consumption, setpoints)

### Heat Pump Sensors (HP_SENSOR_TEMPLATES)
- Flow and return line temperatures
- Volume flow
- Energy source temperatures
- Compressor power
- COP (Coefficient of Performance)
- Power consumption
- Energy consumption

### Boiler Sensors (BOIL_SENSOR_TEMPLATES)
- Temperatures (high/low)
- Operating states
- Circulation

### Heating Circuit Sensors (HC_SENSOR_TEMPLATES)
- Flow and return line temperatures
- Room temperatures
- Operating modes
- Setpoints

### Buffer Sensors (BUFFER_SENSOR_TEMPLATES)
- Temperatures (high/low)
- Operating states
- Request types

### Solar Sensors (SOLAR_SENSOR_TEMPLATES)
- Collector temperatures
- Storage temperatures
- Power and energy yield

## Sensor Initialization

Sensors are initialized at integration startup in `sensor.py`:

1. The data coordinator is loaded
2. The configured firmware version is determined
3. Sensors are filtered based on their compatibility with the firmware
4. For each sensor category, corresponding objects are created and registered
5. Each sensor receives a unique ID and is connected to the data coordinator

Example from `sensor.py`:
```python
entities = []
name_prefix = entry.data.get("name", "lambda_wp").lower().replace(" ", "")
prefix = f"{name_prefix}_"

compatible_static_sensors = get_compatible_sensors(SENSOR_TYPES, fw_version)
for sensor_id, sensor_config in compatible_static_sensors.items():
    # Check for disabled registers
    if coordinator.is_register_disabled(sensor_config["address"]):
        continue
    
    # Create and add entities
    entities.append(
        LambdaSensor(
            coordinator=coordinator,
            config_entry=entry,
            sensor_id=sensor_id,
            sensor_config=sensor_config_with_name,
            unique_id=f"{entry.entry_id}_{sensor_id}",
        )
    )
```

## Sensor Data Retrieval

Data retrieval is handled by the `LambdaDataUpdateCoordinator` in `coordinator.py`:

1. A Modbus TCP/RTU connection is established to the heat pump
2. Registers are queried according to the configuration
3. The data is processed and converted to a structured format
4. Sensors are updated with the new data

Retrieval occurs regularly at the configured interval (default: 30 seconds).

```python
async def _async_update_data(self):
    """Fetch data from Lambda device."""
    from pymodbus.client import ModbusTcpClient
    
    # Establish connection
    if not self.client:
        self.client = ModbusTcpClient(self.host, port=self.port)
        if not await self.hass.async_add_executor_job(self.client.connect):
            raise ConnectionError("Could not connect to Modbus TCP")
    
    # Retrieve data (Static sensors, HP, Boiler, HC, etc.)
    try:
        data = {}
        # 1. Query static sensors
        for sensor_id, sensor_config in compatible_static_sensors.items():
            if self.is_register_disabled(sensor_config["address"]):
                continue
                
            result = await self.hass.async_add_executor_job(
                self.client.read_holding_registers,
                sensor_config["address"],
                count,
                self.slave_id,
            )
            
            # Process and store data
            # ...
    except Exception as ex:
        _LOGGER.error("Exception during data update: %s", ex)
    
    return data
```

## Configuration

Configuration is done via the Home Assistant user interface with `config_flow.py`:

### Basic Settings
- **Name**: Name of the installation
- **Host**: IP address or hostname of the heat pump
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus slave ID (default: 1)
- **Firmware Version**: Firmware of the heat pump (determines available sensors)

### Device Count
- Number of heat pumps (1-3)
- Number of boilers (0-5)
- Number of heating circuits (0-12)
- Number of buffers (0-5)
- Number of solar systems (0-2)

### Temperature Settings
- Hot water temperature range (min/max)
- Heating circuit temperature range (min/max)
- Temperature step size for heating circuits

### Room Temperature Control
- Option to use external temperature sensors for heating circuits

## Function Overview

### __init__.py
- **async_setup**: Initializes the integration in Home Assistant
- **async_setup_entry**: Sets up a configured integration
- **async_unload_entry**: Unloads an integration
- **async_reload_entry**: Reloads an integration after configuration changes

### config_flow.py
- **LambdaConfigFlow**: Configuration flow for initial setup
- **LambdaOptionsFlow**: Configuration flow for options (e.g., temperature settings)
- **async_step_user**: First step of configuration
- **async_step_init**: Management of options
- **async_step_room_sensor**: Configuration of room temperature sensors

### coordinator.py
- **LambdaDataUpdateCoordinator**: Coordinates data retrieval from the heat pump
- **async_init**: Initializes the coordinator
- **_async_update_data**: Retrieves data from the heat pump
- **is_register_disabled**: Checks if a register is disabled

### sensor.py
- **async_setup_entry**: Sets up sensors based on configuration
- **LambdaSensor**: Sensor class for Lambda heat pump data

### climate.py
- **async_setup_entry**: Sets up climate entities
- **LambdaClimateBoiler**: Class for boilers as climate entities
- **LambdaClimateHC**: Class for heating circuits as climate entities

### services.py
- **async_setup_services**: Registers services for the integration
- **async_update_room_temperature**: Service for updating room temperature

### utils.py
- **get_compatible_sensors**: Filters sensors by firmware compatibility
- **build_device_info**: Creates device information for the HA device registry
- **load_disabled_registers**: Loads disabled registers from YAML file
- **is_register_disabled**: Checks if a register is disabled

## Firmware Filtering

The integration supports different firmware versions and filters available sensors accordingly:

```python
def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version."""
    return {
        k: v
        for k, v in sensor_templates.items()
        if v.get("firmware_version", 1) <= fw_version
    }
```

Each sensor has a `firmware_version` attribute that indicates the minimum version from which the sensor is available.

## Modbus Register Services

The integration provides two Home Assistant services for advanced Modbus access:
- `lambda_heat_pumps.read_modbus_register`: Read any Modbus register from the Lambda controller.
- `lambda_heat_pumps.write_modbus_register`: Write a value to any Modbus register of the Lambda controller.

These services can be used via the Developer Tools. See the documentation for details.

## Dynamic Entity Creation

- Heating circuit climate entities are only created if a room thermostat sensor is configured for the respective circuit in the integration options.
- Boiler and other device entities are created based on the configured device count.

## Template-based Climate Entities

- All climate entities (boiler, heating circuit) are now defined by templates in `const.py`.
- This makes it easy to extend or adjust entity properties centrally.

## New Features (Version 1.4.0)

Version 1.4.0 introduces significant new features and improvements to the Lambda Heat Pumps integration:

### Key New Features

- **Energy Consumption Sensors by Operating Mode**: Configurable energy consumption sensors that track energy usage by operating mode (heating, hot water, cooling, defrost) with customizable source sensors
- **Endianness Configuration**: Configurable byte order (big-endian/little-endian) for different Lambda models
- **Sensor Change Detection**: Automatic detection of energy sensor changes with intelligent handling of sensor value transitions
- **Enhanced Cycling Sensors**: Comprehensive cycling counters with monthly and yearly tracking
- **Automatic Configuration**: DHCP discovery and auto-detection of existing configurations
- **Configuration File Support**: YAML-based configuration via `lambda_wp_config.yaml`

## Automatic Configuration

The integration now supports automatic configuration detection and setup:

### DHCP Discovery
- **Auto-Detection**: Automatically detects Lambda heat pumps on the network
- **Existing Configuration Check**: Prevents duplicate configurations
- **Smart Defaults**: Uses sensible default values for IP, port, and slave ID

### Configuration Flow Improvements
- **Streamlined Setup**: Simplified configuration process
- **Validation**: Enhanced configuration validation
- **Error Handling**: Better error messages and recovery

Example of automatic configuration:
```python
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

## Energy Consumption Sensors

Advanced energy tracking with configurable source sensors and operating mode detection:

### Features
- **Operating Mode Tracking**: Tracks energy consumption by heating, hot water, cooling, and defrost modes
- **Configurable Source Sensors**: Use any existing power consumption sensor as data source
- **Automatic Unit Conversion**: Supports Wh, kWh, and MWh with automatic conversion to kWh
- **Monthly and Yearly Tracking**: Long-term energy consumption monitoring
- **Sensor Change Detection**: Automatic handling of sensor changes to prevent incorrect calculations

### Configuration
Configure energy consumption sensors in `lambda_wp_config.yaml`:

```yaml
energy_consumption_sensors:
  1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"
  2:
    sensor_entity_id: "sensor.lambda_wp_verbrauch_2"
```

### Implementation
```python
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

## Cycling Sensors

Comprehensive cycling tracking with multiple time periods and automatic reset functionality:

### Features
- **Multiple Time Periods**: Total, daily, yesterday, 2h, 4h, monthly, and yearly cycling sensors
- **Automatic Reset**: Daily reset at midnight, monthly reset on 1st of month, yearly reset on January 1st
- **Generalized Reset Functions**: Unified reset mechanism for all sensor types
- **Enhanced Automation**: Improved daily reset automation with proper yesterday value handling
- **Configurable Offsets**: Support for cycling offsets when replacing heat pumps

### Sensor Types
- **Total Sensors**: Cumulative cycling count since installation
- **Daily Sensors**: Daily cycling values (reset to 0 daily at midnight)
- **Yesterday Sensors**: Store yesterday's daily values
- **2H/4H Sensors**: Short-term cycling values (reset every 2/4 hours)
- **Monthly Sensors**: Monthly cycling values (reset on 1st of each month)
- **Yearly Sensors**: Yearly cycling values (reset on January 1st)

### Configuration
Configure cycling offsets in `lambda_wp_config.yaml`:

```yaml
cycling_offsets:
  1:
    total: 1000
    daily: 50
  2:
    total: 2000
    daily: 100
```

### Implementation
```python
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

## Endianness Configuration

The integration now supports configurable byte order (endianness) for different Lambda models:

### Configuration
Set endianness in `lambda_wp_config.yaml`:

```yaml
# Endianness configuration
endianness: "big"    # Big-Endian (Default)
# or
endianness: "little" # Little-Endian
```

### When is this important?
- **Big-Endian**: Default for most Lambda models
- **Little-Endian**: Required for certain Lambda models or firmware versions
- **Automatic Detection**: The integration tries to automatically detect the correct endianness

### Implementation
```python
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

### Data Processing
```python
# Process data with endianness support
if data_type == "int32":
    # Use configured endianness for proper byte order
    if self._endianness == "little":
        value = result.registers[0] | (result.registers[1] << 16)
    else:  # big-endian (default)
        value = (result.registers[0] << 16) | result.registers[1]
else:
    value = result.registers[0]
```

## Sensor Change Detection

Automatic detection and handling of energy sensor changes to prevent incorrect energy consumption calculations:

### Features
- **Automatic Detection**: Detects when the configured energy sensor changes
- **Intelligent Handling**: Adjusts `last_energy_readings` to match the new sensor's initial value
- **Retry Mechanism**: Robust handling of sensor availability during startup
- **Persistence**: Stores sensor IDs across Home Assistant restarts
- **Comprehensive Logging**: Detailed logging for easy tracking of changes

### Implementation
```python
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

### Utility Functions
```python
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

## Modbus Tools for Testing

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
