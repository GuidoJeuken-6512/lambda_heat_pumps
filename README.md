# Lambda Heat Pumps Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40GuidoJeuken--6512-blue.svg)](https://github.com/GuidoJeuken-6512)
[![version](https://img.shields.io/badge/version-1.4.3-blue.svg)](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---
Für die deutsche Anleitung bitte weiter unten schauen.

## 🚀 Quickstart (English)

**Lambda Heat Pumps** is a Home Assistant custom integration for Lambda heat pumps via Modbus/TCP.

**HACS Installation:**
1. Install HACS (if not already done)
2. Search for "Lambda heat pumps" and download the integration
3. Restart Hoem assistant
4. Go to Settings -> Devices and services -> 
   Add integration and search for "Lambda Heat Pumps".


### Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "EU08L")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Firmware Version**: Select your Lambda controller's firmware version
- Everything else will be configured automatically.

### Automatic Configuration

The integration features **automatic module detection** and **smart configuration**:

- **Auto-Detection**: Automatically detects available modules (heat pumps, boilers, buffers, solar, heating circuits)
- **Dynamic Entity Creation**: Creates sensors and entities based on detected hardware
- **Smart Defaults**: Applies optimal settings for your specific Lambda configuration
- **Configuration Validation**: Prevents duplicate configurations and validates existing connections

#### Firmware Version
The firmware version is only important to decide which sensors are available.<br>
To find the firmware version follow this from the main screen:
* Click on the heat pump
* Click on the "i" button on the left
* Click on the button on the right that looks like a computer chip (last one)

### Integration Options

After initial setup, you can modify additional settings in the integration options:

1. Go to Configuration → Integrations
2. Find your Lambda Heat Pump integration and click "Configure"
3. Here you can adjust:
   - Hot water temperature range (min/max)
   - Heating circuit temperature range (min/max)
   - Temperature step size
   - Room thermostat control (using external sensors)
   - PV surplus control for solar power integration

**Features:**
- **Full Modbus/TCP Support**: Complete support for Lambda heat pumps via Modbus/TCP
- **Automatic Module Detection**: Auto-detects available modules and creates appropriate entities
- **Cycling Sensors**: Comprehensive cycling counters for all operating modes (heating, hot water, cooling, defrost)
  - Total, daily, yesterday, 2h, and 4h cycling sensors
  - Automatic daily reset at midnight
  - Configurable cycling offsets for counter adjustments
- **Energy Consumption Sensors**: Detailed energy tracking by operating mode
  - Heating, hot water, cooling, and defrost energy consumption
  - Monthly and yearly energy consumption tracking
  - Configurable source sensors with automatic unit conversion (Wh/kWh/MWh)
  - Smart sensor change detection to prevent incorrect calculations
- **Room Thermostat Control**: External sensor integration for precise temperature control
- **PV Surplus Control**: Solar power integration for optimal energy usage
- **Advanced Configuration**: YAML-based configuration with debug logging
- **Register Order Configuration**: Configurable register order for 32-bit values from multiple 16-bit registers

**Documentation:**
- [English Guide](docs/lambda_heat_pumps_en.md)
- [Troubleshooting](docs/lambda_heat_pumps_troubleshooting.md)
- 

**Support:**
- [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

---

## 🇩🇪 Schnelleinstieg (Deutsch)

**Lambda Heat Pumps** ist eine benutzerdefinierte Komponente für Home Assistant, die eine Verbindung zu Lambda Wärmepumpen über das Modbus TCP/RTU-Protokoll herstellt.

**HACS Installation:**
1. **HACS installieren** (falls noch nicht geschehen)
2. **Custom Repository hinzufügen:**
   - HACS → Integrations → suche nach "lambda Heat Pumps"
3. **Integration herunterladen:**
   - „Lambda Heat Pumps“ auswählen und installieren
   - Home Assistant neu starten

### Erstkonfiguration

Bei der Einrichtung müssen Sie Folgendes angeben:

- **Name**: Ein Name für Ihre Lambda-Wärmepumpe (z. B. „EU08L")
- **Host**: IP-Adresse oder Hostname Ihres Lambda-Controllers
- **Port**: Modbus-TCP-Port (Standard: 502)
- **Slave ID**: Modbus-Slave-ID (Standard: 1)
- **Firmware-Version**: Firmware-Version Ihres Lambda-Controllers auswählen
- Alles andere wird automatisch konfiguriert

### Automatische Konfiguration

Die Integration bietet **automatische Modulerkennung** und **intelligente Konfiguration**:

- **Auto-Detection**: Erkennt automatisch verfügbare Module (Wärmepumpen, Kessel, Puffer, Solar, Heizkreise)
- **Dynamische Entity-Erstellung**: Erstellt Sensoren und Entities basierend auf erkanntem Hardware
- **Intelligente Standardeinstellungen**: Wendet optimale Einstellungen für Ihre spezifische Lambda-Konfiguration an
- **Konfigurationsvalidierung**: Verhindert doppelte Konfigurationen und validiert bestehende Verbindungen

#### Firmware Version
Die Firmware-Version is nur wichtig um zu entscheiden welche Sensoren verfügbar sind.<br>
Um die Firmware-Version zu finden, folgen Sie diesen Schritten am Hauptbildschirm:
1. Klicken Sie auf die Wärmepumpe
2. Klicken Sie auf die "i" Taste auf der linken Seite
3. Klicken Sie auf die Taste auf der rechten Seite, die wie ein Computerchip aussieht (letzte Taste)

### Integrationsoptionen

Nach der Ersteinrichtung können Sie zusätzliche Einstellungen in den Integrationsoptionen ändern:

1. Gehen Sie zu „Konfiguration“ → „Integrationen“.
2. Suchen Sie Ihre Lambda-Wärmepumpen-Integration und klicken Sie auf „Konfigurieren“.
3. Hier können Sie Folgendes anpassen:
   - Warmwassertemperaturbereich (min./max.)
   - Heizkreistemperaturbereich (min./max.)
   - Temperaturstufengröße
   - Raumthermostatsteuerung (mit externen Sensoren)
   - PV Überschuss zur Heizkurvenanhebung der Lambda

---

## 🔄 Cycling & Verbrauchssensoren

Die Integration bietet umfassende **Cycling-Sensoren** und **Energieverbrauchssensoren** für detaillierte Überwachung Ihrer Lambda-Wärmepumpe:

### Cycling-Sensoren
- **Betriebsmodi**: Heizen, Warmwasser, Kühlen, Abtauen
- **Zeiträume**: Total, Täglich, Gestern, 2h, 4h
- **Automatischer Reset**: Tägliche Sensoren werden um Mitternacht zurückgesetzt
- **Offset-Konfiguration**: Anpassbare Zählerstände für Wärmepumpenwechsel

### Energieverbrauchssensoren
- **Betriebsmodi**: Heizen, Warmwasser, Kühlen, Abtauen
- **Zeiträume**: Täglich, Monatlich, Jährlich
- **Konfigurierbare Quellsensoren**: Beliebige Energiezähler als Datenquelle
- **Automatische Einheitenkonvertierung**: Wh/kWh/MWh
- **Sensor-Wechsel-Erkennung**: Intelligente Behandlung von Sensor-Änderungen

### Konfiguration
Die Sensoren werden automatisch erstellt und können über `lambda_wp_config.yaml` konfiguriert werden:
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: sensor.your_energy_meter
cycling_offsets:
  hp1:
    heating_cycling_total: 100
    hot_water_cycling_total: 50
# Register-Reihenfolge für 32-Bit-Register (int32-Sensoren)
modbus:
  int32_register_order: "high_first"  # "high_first" oder "low_first" - Standard: "high_first"
```

---

## ⚙️ Register-Reihenfolge-Konfiguration

Die Integration unterstützt **konfigurierbare Register-Reihenfolge** für 32-Bit-Werte aus mehreren 16-Bit-Registern. Dies bezieht sich auf die Reihenfolge der Register (Register/Word Order) bei der Kombination mehrerer Register zu einem 32-Bit-Wert.

### Konfiguration
In der `lambda_wp_config.yaml` können Sie die Register-Reihenfolge festlegen:

```yaml
# Modbus-Konfiguration
modbus:
  # Register-Reihenfolge für 32-Bit-Register (int32-Sensoren)
  # "high_first" = Höherwertiges Register zuerst (Standard)
  # "low_first" = Niedrigwertiges Register zuerst
  int32_register_order: "high_first"  # oder "low_first"
```

### Wann ist das wichtig?
- **"high_first"**: Standard für die meisten Lambda-Modelle (höherwertiges Register zuerst)
- **"low_first"**: Erforderlich für bestimmte Lambda-Modelle oder Firmware-Versionen (niedrigwertiges Register zuerst)
- **Rückwärtskompatibilität**: Alte Config mit `int32_byte_order` oder alten Werten (`big`/`little`) wird automatisch erkannt und migriert

### Fehlerbehebung
Falls Sie falsche Werte in den Sensoren sehen, versuchen Sie die andere Register-Reihenfolge-Einstellung.

---

## 🌞 PV-Überschuss-Steuerung

Die Integration unterstützt die Steuerung der Wärmepumpe basierend auf verfügbarem PV-Überschuss. Diese Funktion ermöglicht es der Wärmepumpe, überschüssigen Solarstrom zu nutzen.

### Funktionen:
- **PV-Überschuss-Erkennung**: Automatische Überwachung der PV-Leistung
- **Modbus-Register 102**: Schreiben der aktuellen PV-Leistung in Watt
- **Konfigurierbare Sensoren**: Auswahl beliebiger PV-Leistungssensoren
- **Automatische Aktualisierung**: Regelmäßiges Schreiben der PV-Daten (standardmäßig alle 10 Sekunden)
- **Einheitenkonvertierung**: Automatische Umrechnung von kW in W

### Konfiguration:
1. **PV-Überschuss aktivieren**: In den Integration-Optionen "PV-Überschuss" aktivieren
2. **PV-Sensor auswählen**: Einen PV-Leistungssensor auswählen (z.B. Template-Sensor für PV-Überschuss)
3. **Intervall anpassen**: Das Schreibintervall in den Optionen konfigurieren

### Unterstützte Sensoren:
- **Watt-Sensoren**: Direkte Verwendung (z.B. 1500 W)
- **Kilowatt-Sensoren**: Automatische Umrechnung (z.B. 1.5 kW → 1500 W)
- **Template-Sensoren**: Für komplexe PV-Überschuss-Berechnungen

### Modbus-Register:
- **Register 102**: E-Manager Actual Power (globales Register)
- **Wertebereich**: -32768 bis 32767 (int16)
- **Einheit**: Watt

---

## 🔄 Cycling & Energy Consumption Sensors

The integration provides comprehensive **Cycling Sensors** and **Energy Consumption Sensors** for detailed monitoring of your Lambda heat pump:

### Cycling Sensors
- **Operating Modes**: Heating, Hot Water, Cooling, Defrost
- **Time Periods**: Total, Daily, Yesterday, 2h, 4h
- **Automatic Reset**: Daily sensors reset at midnight
- **Offset Configuration**: Adjustable counters for heat pump replacement

### Energy Consumption Sensors
- **Operating Modes**: Heating, Hot Water, Cooling, Defrost
- **Time Periods**: Daily, Monthly, Yearly
- **Configurable Source Sensors**: Any energy meter as data source
- **Automatic Unit Conversion**: Wh/kWh/MWh
- **Sensor Change Detection**: Intelligent handling of sensor changes

### Configuration
Sensors are automatically created and can be configured via `lambda_wp_config.yaml`:
```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: sensor.your_energy_meter
cycling_offsets:
  hp1:
    heating_cycling_total: 100
    hot_water_cycling_total: 50
# Register order for 32-bit registers (int32 sensors)
modbus:
  int32_register_order: "high_first"  # "high_first" or "low_first" - Default: "high_first"
```

---

## ⚙️ Register Order Configuration

The integration supports **configurable register order** for 32-bit values from multiple 16-bit registers. This refers to the order of registers (Register/Word Order) when combining multiple registers into a 32-bit value.

### Configuration
In the `lambda_wp_config.yaml` you can set the register order:

```yaml
# Modbus configuration
modbus:
  # Register order for 32-bit registers (int32 sensors)
  # "high_first" = High-order register first (Default)
  # "low_first" = Low-order register first
  int32_register_order: "high_first"  # or "low_first"
```

### When is this important?
- **"high_first"**: Default for most Lambda models (high-order register first)
- **"low_first"**: Required for certain Lambda models or firmware versions (low-order register first)
- **Backward Compatibility**: Old config with `int32_byte_order` or old values (`big`/`little`) is automatically detected and migrated

### Troubleshooting
If you see incorrect values in the sensors, try the other register order setting.

---

## 🌞 PV Surplus Control

The integration supports controlling the heat pump based on available PV surplus. This feature allows the heat pump to utilize excess solar power.

### Features:
- **PV Surplus Detection**: Automatic monitoring of PV power output
- **Modbus Register 102**: Writing current PV power in watts
- **Configurable Sensors**: Selection of any PV power sensors
- **Automatic Updates**: Regular writing of PV data (default: every 10 seconds)
- **Unit Conversion**: Automatic conversion from kW to W

### Configuration:
1. **Enable PV Surplus**: Activate "PV Surplus" in integration options
2. **Select PV Sensor**: Choose a PV power sensor (e.g., template sensor for PV surplus)
3. **Adjust Interval**: Configure the write interval in options

### Supported Sensors:
- **Watt Sensors**: Direct usage (e.g., 1500 W)
- **Kilowatt Sensors**: Automatic conversion (e.g., 1.5 kW → 1500 W)
- **Template Sensors**: For complex PV surplus calculations

### Modbus Register:
- **Register 102**: E-Manager Actual Power (global register)
- **Value Range**: -32768 to 32767 (int16)
- **Unit**: Watts

---

## 📦 Manual Installation (without HACS)

If you do not use HACS, you can install the integration manually:

1. **Create the folder** `/config/custom_components` on your Home Assistant server if it does not exist.

2. **If you have terminal access to your Home Assistant server:**
   ```bash
   cd /config/custom_components
   - Download the integration from:  
     https://github.com/GuidoJeuken-6512/lambda_wp_hacs
   - Copy the entire folder `lambda_heat_pumps` into `/config/custom_components/` on your Home Assistant server.

4. **Restart Home Assistant** to activate the integration.

---

## 🛠️ Troubleshooting & Support
- **Log-Analyse:** Aktiviere Debug-Logging für detaillierte Fehlerausgabe
- **Häufige Probleme:** Siehe Abschnitt „Troubleshooting“ unten
- **Support:**
  - [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
  - [Home Assistant Community](https://community.home-assistant.io/)

---

## 📄 Lizenz & Haftung
MIT License. Nutzung auf eigene Gefahr. Siehe [LICENSE](LICENSE).

---

## 📚 Weitere Dokumentation
- [Quick Start (DE)](docs/lambda_heat_pumps_quick_start.md)
- [FAQ (DE)](docs/lambda_heat_pumps_faq.md)
- [Entwickler-Guide](docs/lambda_heat_pumps_developer_guide.md)
- [Modbus Register (DE/EN)](docs/lambda_heat_pumps_modbus_register_de.md), [EN](docs/lambda_heat_pumps_modbus_register_en.md)
- [Troubleshooting](docs/lambda_heat_pumps_troubleshooting.md)
- [HACS Publishing Guide](docs/lambda_heat_pumps_hacs_publishing.md)

---

## 📝 Changelog
Siehe [Releases](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases) für Änderungen und Breaking Changes.

---

**Developed with ❤️ for the Home Assistant Community**
