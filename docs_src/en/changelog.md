# Changelog

## English Version

#### New Features since last release
- **Device Hierarchy**: Separation into main devices and sub-devices for better organization and clearer entity structure
- **Multilingual Support**: Comprehensive translations in German and English for all entity names
- **Heating Curve Calculation**: Intelligent heating curve calculation with three support points (cold, mid, warm) and automatic flow temperature calculation
- **Compressor Start Cycling Sensor**: New cycling sensor for tracking compressor start events with total, daily, 2h, 4h, and monthly variants
- **Flow Line Offset Number Entity**: Bidirectional Modbus-synchronized Number entity for easy adjustment of flow line offset temperature (-10°C to +10°C)

### [2.0.1] - 2025-01-XX

#### New Features
- **Flow Line Offset Number Entity**: Added bidirectional Modbus-synchronized Number entity for flow line offset temperature adjustment
  - Automatically created for each heating circuit (HC1, HC2, etc.)
  - Range: -10.0°C to +10.0°C with 0.1°C step size
  - Reads current value from Modbus register and writes changes directly back
  - Appears in device configuration alongside heating curve support points
  - Modbus Register: Register 50 (relative to heating circuit base address)

#### Fixed
- **Heating Curve Validation**: Fixed validation logic to check both conditions independently
  - Changed `elif` to `if` to ensure both validation checks are performed
  - Now reports all validation problems when multiple heating curve values are misconfigured
  - Previously only the first issue was reported when all three temperature points were in wrong order
- **Hot Water Temperature Limits**: Adjusted minimum/maximum values for hot water to Lambda standard (25/65°C)


#### Changed
- **Git Configuration**: Removed `automations.yaml` from gitignore to prevent it from being tracked in git

### [2.0.0] - 2025-01-XX

#### New Features
- **Device Hierarchy**: Implemented separation into main devices and sub-devices for better organization and clearer entity structure
- **Multilingual Support**: Added comprehensive translations in German and English for all entity names, ensuring proper localization support
- **Heating Curve Calculation**: Implemented intelligent heating curve calculation with three support points (cold, mid, warm) and automatic flow temperature calculation based on outside temperature
  - **Cold Point**: Defines the heating curve at low outside temperatures
  - **Mid Point**: Defines the heating curve at medium outside temperatures
  - **Warm Point**: Defines the heating curve at high outside temperatures
  - **New Sensor**: `heating_curve_flow_line_temperature_calc` automatically calculates the optimal flow temperature based on current outside temperature and the configured support points
- **Compressor Start Cycling Sensor**: Added new cycling sensor for tracking compressor start events
  - **Total Sensor**: `compressor_start_cycling_total` - Tracks total compressor starts since installation
  - **Daily Sensor**: `compressor_start_cycling_daily` - Tracks daily compressor starts (resets at midnight)
  - **2H Sensor**: `compressor_start_cycling_2h` - Tracks 2-hour compressor starts (resets every 2 hours)
  - **4H Sensor**: `compressor_start_cycling_4h` - Tracks 4-hour compressor starts (resets every 4 hours)
  - **Monthly Sensor**: `compressor_start_cycling_monthly` - Tracks monthly compressor starts (resets on 1st of month)
  - **Flank Detection**: Uses HP_STATE register (1002) instead of HP_OPERATING_STATE, detecting "START COMPRESSOR" state (value 5)

#### Improvements
- Enhanced entity naming with proper device and sub-device prefixes
- Improved translation loading and application for all entity types
- Better integration with Home Assistant's translation system
- **Write Interval Optimization**: Reduced write interval from 41 seconds to 9 seconds for faster response times
- **External Energy Sensor Validation**: Enhanced validation of external energy consumption sensors with Entity Registry fallback check, allowing sensors to be accepted even when not yet available in state during startup. Runtime retry mechanism handles temporary unavailability gracefully.

### [1.4.3] - 2025-11-04
#### Fixed
- **ISSUE 39** Modbus batch reads incorrectly detect errors: Faster switching to individual reads so that correct sensors become available again
- **ISSUE 22** Additional logging added to identify errors
- **Unit of sensor volume_flow_heat_sink corrected** to l/h

### [1.4.2] - 2025-10-24

#### Fixed
- Fixed failing tests by replacing Mock objects with proper test implementations
- Improved test reliability and reduced false failures
- Fixed integration reload errors
- Fixed `default_config` in `load_lambda_config()` to include all required keys (`energy_consumption_sensors`, `energy_consumption_offsets`, `modbus`)

#### Changed
- **Register Order Values**: Changed configuration values from `"big"`/`"little"` to `"high_first"`/`"low_first"` for better clarity
  - Old values (`big`/`little`) are still supported with automatic conversion
  - New default is `"high_first"` (replaces `"big"`)
  - Improved documentation and comments to clarify register order vs. byte endianness

#### Improvements
- Test optimization: 57 tests successfully repaired and optimized
- Gitignore correction: Fixed .gitignore for proper inclusion of all docs subdirectories
- Service documentation: Created comprehensive documentation for future service optimizations
- **Service Scheduler Optimization**: Implemented intelligent service scheduler that only activates when PV-Surplus or Room Thermostat control options are enabled, significantly reducing resource usage when services are not needed

---

### [1.4.1] - 2025-10-21

#### New Features
- **Massive Performance Improvements**: Dramatically improved integration startup and update performance
  - **Startup Time**: Reduced by ~72% (from ~7.3s to ~2.05s) through intelligent background auto-detection
  - **Update Cycles**: Reduced by ~50% (from >30s to <15s) through global register deduplication
  - **Modbus Traffic**: Reduced by ~80% through elimination of duplicate register reads
- **Intelligent Auto-Detection**: Implemented background auto-detection for existing configurations, eliminating startup delays while maintaining hardware change detection
- **Global Register Cache**: Added comprehensive register deduplication system that eliminates duplicate Modbus reads across all modules (HP, Boiler, Buffer, Solar, HC)
- **Optimized Batch Reading**: Improved Modbus batch reading with larger consecutive register ranges and reduced individual read thresholds
- **Parallel Template Setup**: Template sensors now load in background tasks, preventing startup blocking
- **Persist I/O Optimization**: Added debouncing and dirty-flag mechanisms to reduce unnecessary file writes
- **Connection Health Optimization**: Reduced connection timeout from 5s to 2s for faster failure detection

#### Improvements
- **Enhanced Energy Tracking**: Improved energy consumption tracking with automatic unit conversion (Wh/kWh/MWh)
- **Robust Sensor Handling**: Added retry mechanism for sensor availability during startup
- **Comprehensive Logging**: Added detailed logging for sensor change detection and energy calculations
- **Monthly & Yearly Power Consumption Sensors**: Added monthly and yearly energy consumption sensors for long-term tracking
- **Service Setup Optimization**: Services are now set up only once, regardless of the number of entries
- **Configuration Flow Improvements**: Enhanced validation for existing connections and IP addresses, removed obsolete modules
- **Generalized Reset Functions**: Implemented generalized reset functions for all sensor types with extended tests
- **Code Cleanup**: Cleaned up const.py, YAML templates, and general code structure
- **Documentation Updates**: Updated documentation and created program flow diagrams

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.4.0] - 2025-10-05

#### New Features
- **Energy Consumption Sensors by Operating Mode**: Added configurable energy consumption sensors that track energy usage by operating mode (heating, hot water, cooling, defrost) with customizable source sensors (Issue #21)
- **Register Order Configuration**: Added register order configuration in `lambda_wp_config.yaml` for proper 32-bit value interpretation from multiple 16-bit registers (Issue #22)
- **Sensor Change Detection**: Implemented automatic detection of energy sensor changes with intelligent handling of sensor value transitions to prevent incorrect energy consumption calculations

#### Bug Fixes
- **Register Order Fix**: Fixed register order issues for 32-bit values with initial quick fix approach (Issue #22)
- **Daily Sensor Reset Automation**: Fixed errors in automation for resetting daily sensors (Issue #29)
- **Auto-Detection**: Fixed auto-detection not recognizing existing configurations (IP/Port/SlaveId)
- **DCHP Discovery**: Fixed DCHP discovery error messages
- **HASS Validation**: Fixed Home Assistant validation errors
- **Daily Reset Function**: Repaired daily reset function for sensors

#### Improvements
- **Enhanced Energy Tracking**: Improved energy consumption tracking with automatic unit conversion (Wh/kWh/MWh)
- **Robust Sensor Handling**: Added retry mechanism for sensor availability during startup
- **Comprehensive Logging**: Added detailed logging for sensor change detection and energy calculations
- **Monthly & Yearly Power Consumption Sensors**: Added monthly and yearly energy consumption sensors for long-term tracking
- **Service Setup Optimization**: Services are now set up only once, regardless of the number of entries
- **Configuration Flow Improvements**: Enhanced validation for existing connections and IP addresses, removed obsolete modules
- **Generalized Reset Functions**: Implemented generalized reset functions for all sensor types with extended tests
- **Code Cleanup**: Cleaned up const.py, YAML templates, and general code structure
- **Documentation Updates**: Updated documentation and created program flow diagrams

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.3.0] - 2025-01-03

#### New Features
- **New 2H/4H Cycling Sensors**: Added 2-hour and 4-hour cycling sensors for detailed heat pump operation monitoring
- **Enhanced Cycling Offsets**: Improved cycling counter offset functionality for total sensor adjustments when replacing heat pumps or resetting counters
- **Robust Flank Detection**: Implemented robust flank detection for heat pump operating states with improved reliability
- **Dynamic Error Handling**: Enhanced batch read error handling with automatic fallback to individual reads after threshold failures
- **Cycling Warnings Management**: Added cycling warnings suppression logic to manage entity registration issues

#### Bug Fixes
- **Configuration File Creation**: Fixed issue where `lambda_wp_config.yaml` was not automatically created from template, ensuring proper configuration setup
- **Daily Cycling Sensors**: Fixed daily cycling sensors now properly displaying values and functioning correctly

#### Improvements
- **Coordinator Initialization**: Enhanced coordinator initialization process with improved error handling
- **Debug Logging**: Added comprehensive debug logs for tracking offset changes and system behavior
- **Documentation**: Updated documentation to reflect new functions and configuration options
- **Modbus Configuration**: Extended Lambda Heat Pumps integration with specific Modbus configurations

#### Technical Changes
- Automatic `lambda_wp_config.yaml` creation from `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration of config file creation into existing migration pipeline
- Enhanced error handling in `LambdaDataUpdateCoordinator`
- Improved sensor attribute loading with better error recovery

---

### [1.2.2] - 2025-08-18

#### ⚠️ BREAKING CHANGES IN THIS RELEASE - BACKUP REQUIRED

This release contains significant changes to the Entity Registry and sensor naming conventions. **Please create a complete backup of your Home Assistant configuration before updating.**

**What will change:**
- Automatic migration of existing sensor entities to prevent duplicates
- Updated unique_id format for better consistency
- Sensor filtering based on firmware compatibility

**After migration, please verify:**
- Sensor names and long-term data are preserved correctly
- No duplicate entities exist in your system
- All sensors are functioning as expected
- **Automations may need to be updated** if they reference sensor entities that were migrated

**A Copy of the core.config_entries, core.device_registry and core.entity_registry is created before the sensors are migrated and can be copied back from the /lambda_heat_pumps folder to the hidden .storage folder to undo the changes. However, version 1.0.9 of the integration must then be reinstalled for the system to work properly.**

---

### [1.1.0] - 2025-08-03

#### Major Changes
- **Switch to asynchronous Modbus clients** - Complete migration from synchronous to asynchronous Modbus communication for better compatibility with other integrations
- **Runtime API compatibility** - Automatic detection and adaptation to different pymodbus versions (1.x, 2.x, 3.x)
- **Performance improvements** - Non-blocking Modbus operations for better system performance
- **Entity Registry Migration** - Automatic migration of general and climate sensors to prevent duplicate entities with consistent unique_id format

#### Added
- Asynchronous Modbus wrapper functions in `modbus_utils.py`
- Runtime API compatibility detection for pymodbus versions
- Comprehensive error handling for async Modbus operations
- Extended cycling counters with daily, yesterday and total values for all operating modes

#### Changed
- All Modbus operations migrated to `AsyncModbusTcpClient`
- Coordinator, config_flow, services, and climate modules updated for async operations
- Removed `async_add_executor_job` wrappers in favor of direct async calls

#### Fixed
- RuntimeWarning: "coroutine was never awaited" in automation setup
- Callback function implementation corrected
- Code quality improvements and linting issues resolved
- Duplicate sensor entities with "_2" suffix after updates
- Inconsistent unique_id format for general and climate sensors
- Sensor filtering based upon firmware settings

#### Removed
- **`use_legacy_modbus_names` configuration option** - This option has been removed as it became obsolete after the automatic migration of all sensors to the legacy naming scheme (`use_legacy=true`). All existing installations will automatically use the legacy naming format.

---

### [1.0.9] - 2024-12-19

#### Added
- Compatibility with pymodbus >= 3.6.0
- Counters for heat pump cycling by operating mode
- Extended statistics for different operating modes

#### Changed
- Updated to new pymodbus API (3.x)
- Removed redundant parameters in `read_holding_registers` calls
- Synchronous `connect()` calls instead of asynchronous
- Code style improvements (flake8-compatible)

#### Fixed
- Import errors in all modules fixed
- Whitespace issues resolved
- HACS validation errors corrected
- Manifest keys properly sorted

---

### [1.0.0] - Initial Release

#### Added
- First version of Lambda Heat Pumps Integration
- Modbus communication for heat pumps
- Cycle counter detection
- Climate entity for heat pump control

---

## Deutsche Version {#deutsche-version}
