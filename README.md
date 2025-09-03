# Lambda Heat Pumps Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40GuidoJeuken--6512-blue.svg)](https://github.com/GuidoJeuken-6512)
[![version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases)
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


## Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "EU08L")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Firmware Version**: Select your Lambda controller's firmware version
- Everything else will be configured automatically.

## Integration Options

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
- Full Modbus/TCP support for Lambda heat pumps
- Dynamic entity and sensor detection
- Room thermostat control with external sensors
- PV surplus control for solar power integration
- advanced YAML config, debug logging

**Documentation:**
- [English Guide](docs/lambda_heat_pumps_en.md)
- [Troubleshooting](docs/lambda_heat_pumps_troubleshooting.md)
- 

**Support:**
- [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

---

## 🇩🇪 Schnelleinstieg (Deutsch)

> **HACS Custom Integration**  
> Diese Integration verbindet Lambda Wärmepumpen mit Home Assistant via Modbus/TCP.

### 🚀 Quickstart (HACS)
#### Installation

1. **HACS installieren** (falls noch nicht geschehen)
2. **Custom Repository hinzufügen:**
   - HACS → Integrations → suche nach "lambda Heat Pumps"
3. **Integration herunterladen:**
   - „Lambda Heat Pumps“ auswählen und installieren
   - Home Assistant neu starten

## Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "Main Heat Pump")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Firmware Version**: Select your Lambda controller's firmware version
- alles Andere wird automatisch konfiguriert

## Integration Options

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
