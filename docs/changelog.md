# Changelog

All notable changes to the Lambda Heat Pumps integration are documented in this file.

## [2.0.1] - 2025-01-XX

### New Features
- **Flow Line Offset Number Entity**: Added bidirectional Modbus-synchronized Number entity for flow line offset temperature adjustment
  - Automatically created for each heating circuit (HC1, HC2, etc.)
  - Range: -10.0°C to +10.0°C with 0.1°C step size
  - Reads current value from Modbus register and writes changes directly back
  - Appears in device configuration alongside heating curve support points
  - Modbus Register: Register 50 (relative to heating circuit base address)

### Fixed
- **Heating Curve Validation**: Fixed validation logic to check both conditions independently
  - Changed `elif` to `if` to ensure both validation checks are performed
  - Now reports all validation problems when multiple heating curve values are misconfigured
- **Hot Water Temperature Limits**: Adjusted minimum/maximum values for hot water to Lambda standard (25/65°C)

### Changed
- **Git Configuration**: Removed `automations.yaml` from gitignore

## [2.0.0] - 2025-01-XX

### Major Changes
- Complete rewrite with modern Home Assistant integration framework
- Improved entity naming and organization
- Enhanced error handling and retry logic
- Better Modbus communication reliability

### New Features
- Automatic module detection
- Heating curve configuration
- Room thermostat integration
- PV surplus control
- Comprehensive cycling sensors
- Energy consumption tracking

### Breaking Changes
- Entity IDs have changed - see migration guide
- Configuration format updated
- Some sensor names changed

## Previous Versions

For older changelog entries, see [GitHub Releases](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases).

