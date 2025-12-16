# Installation

This guide will help you install the Lambda Heat Pumps integration in Home Assistant.

## Prerequisites

- Home Assistant installed and running
- HACS (Home Assistant Community Store) installed
- Lambda heat pump with Modbus/TCP interface
- Network access to the Lambda controller

## Installation via HACS

### Step 1: Install HACS

If you haven't installed HACS yet:

1. Go to [HACS Installation Guide](https://hacs.xyz/docs/setup/download)
2. Follow the instructions to install HACS
3. Restart Home Assistant

### Step 2: Add Custom Repository

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots menu (⋮) in the top right
4. Select **Custom repositories**
5. Add the repository:
   - **Repository**: `GuidoJeuken-6512/lambda_wp_hacs`
   - **Category**: Integration
6. Click **Add**

### Step 3: Install Integration

1. Search for "Lambda Heat Pumps" in HACS
2. Click on the integration
3. Click **Download**
4. Restart Home Assistant

## Manual Installation

If you prefer to install manually:

1. Download the latest release from [GitHub Releases](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases)
2. Extract the ZIP file
3. Copy the `lambda_heat_pumps` folder to your `custom_components` directory:
   ```
   config/custom_components/lambda_heat_pumps/
   ```
4. Restart Home Assistant

## Configuration

After installation, configure the integration:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for "Lambda Heat Pumps"
4. Enter your configuration:
   - **Name**: A name for your installation (e.g., "EU08L")
   - **Host**: IP address of your Lambda controller
   - **Port**: Modbus TCP port (default: 502)
   - **Slave ID**: Modbus Slave ID (default: 1)
   - **Firmware Version**: Select your firmware version

## Finding Your Firmware Version

To find your Lambda controller's firmware version:

1. From the main screen, click on the heat pump
2. Click the "i" button on the left
3. Click the button on the right that looks like a computer chip (last one)
4. The firmware version will be displayed

## Next Steps

- [Configuration Guide](configuration.md) - Learn about advanced configuration options
- [Features Overview](features.md) - Discover all available features
- [Troubleshooting](../../troubleshooting.md) - Solve common issues

