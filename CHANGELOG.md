# Changelog

**Deutsche Version siehe unten / [German version see below](#deutsche-version)**

<!-- lang:en -->
## English Version

> **📚 Documentation**: A German documentation is currently being built at [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps)
 


### [2.1] - 2025-12-20

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
  - Fixed issue when all three heating curve points have identical values (Issue #48)

- **Hot Water Temperature Limits**: Adjusted minimum/maximum values for hot water to Lambda standard (25/65°C) (Issue #50)
- **Eco Mode in Heating Curve**: Added eco temperature reduction feature for heating circuits (Issue #51)
  - New Number entity `eco_temp_reduction` per heating circuit with range -10.0 to 0.0°C (default: -1.0°C)
  - Automatically reduces calculated flow temperature when heating circuit is in ECO mode (operating_state = 1)
  - Integrated into heating curve calculation alongside flow line offset and room thermostat adjustments 


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
<!-- /lang:en -->
## Deutsche Version {#deutsche-version}


<!-- lang:de -->

> **📚 Dokumentation**: Eine deutsche Dokumentation wird derzeit unter [https://guidojeuken-6512.github.io/lambda_heat_pumps](https://guidojeuken-6512.github.io/lambda_heat_pumps) aufgebaut


### [2.0.1] - 2025-01-XX

#### Neue Funktionen
- **Vorlauf-Offset Number Entity**: Hinzugefügte bidirektionale Modbus-synchronisierte Number-Entity zur Anpassung der Vorlauf-Offset-Temperatur
  - Wird automatisch für jeden Heizkreis (HC1, HC2, etc.) erstellt
  - Bereich: -10.0°C bis +10.0°C mit 0.1°C Schrittweite
  - Liest aktuellen Wert aus Modbus-Register und schreibt Änderungen direkt zurück
  - Erscheint in der Geräte-Konfiguration neben den Heizkurven-Stützpunkten
  - Modbus-Register: Register 50 (relativ zur Base-Adresse des Heizkreises)

#### Behoben
- **Heizkurven-Validierung**: Validierungslogik korrigiert, um beide Bedingungen unabhängig zu prüfen
  - `elif` zu `if` geändert, um sicherzustellen, dass beide Validierungsprüfungen durchgeführt werden
  - Meldet jetzt alle Validierungsprobleme, wenn mehrere Heizkurven-Werte falsch konfiguriert sind
  - Zuvor wurde nur das erste Problem gemeldet, wenn alle drei Temperaturpunkte in falscher Reihenfolge waren
  - Behoben: Problem wenn alle drei Heizkurven-Punkte identische Werte haben (Issue #48)
- **Warmwasser-Temperaturgrenzen**: Minimum/Maximum-Werte für Warmwasser auf Lambda-Standard (25/65°C) angepasst (Issue #50)
- **Eco-Modus in Heizkurve**: Hinzugefügte Eco-Temperaturreduktion für Heizkreise (Issue #51)
  - Neue Number-Entity `eco_temp_reduction` pro Heizkreis mit Bereich -10,0 bis 0,0°C (Standard: -1,0°C)
  - Reduziert automatisch die berechnete Vorlauftemperatur, wenn der Heizkreis im ECO-Modus ist (operating_state = 1)
  - In die Heizkurven-Berechnung integriert, zusammen mit Vorlauf-Offset und Raumthermostat-Anpassungen


### [2.0.0] - 2025-01-XX

#### Neue Funktionen
- **Geräte-Hierarchie**: Implementierte Aufteilung in Haupt- und Sub-Geräte für bessere Organisation und klarere Entity-Struktur
- **Mehrsprachige Unterstützung**: Hinzugefügte umfassende Übersetzungen in Deutsch und Englisch für alle Entity-Namen, gewährleistet ordnungsgemäße Lokalisierungsunterstützung
- **Heizkurven-Berechnung**: Implementierte intelligente Heizkurven-Berechnung mit drei Stützpunkten (Kalt, Mittel, Warm) und automatischer Vorlauftemperatur-Berechnung basierend auf Außentemperatur
  - **Kalter Punkt**: Definiert die Heizkurve bei niedrigen Außentemperaturen
  - **Mittlerer Punkt**: Definiert die Heizkurve bei mittleren Außentemperaturen
  - **Warmer Punkt**: Definiert die Heizkurve bei hohen Außentemperaturen
  - **Neuer Sensor**: `heating_curve_flow_line_temperature_calc` berechnet automatisch die optimale Vorlauftemperatur basierend auf aktueller Außentemperatur und den konfigurierten Stützpunkten
- **Kompressor-Start Cycling Sensor**: Hinzugefügter neuer Cycling-Sensor zur Verfolgung von Kompressor-Start-Ereignissen
  - **Total-Sensor**: `compressor_start_cycling_total` - Verfolgt Gesamtanzahl der Kompressor-Starts seit Installation
  - **Daily-Sensor**: `compressor_start_cycling_daily` - Verfolgt tägliche Kompressor-Starts (Reset um Mitternacht)
  - **2H-Sensor**: `compressor_start_cycling_2h` - Verfolgt 2-Stunden Kompressor-Starts (Reset alle 2 Stunden)
  - **4H-Sensor**: `compressor_start_cycling_4h` - Verfolgt 4-Stunden Kompressor-Starts (Reset alle 4 Stunden)
  - **Monthly-Sensor**: `compressor_start_cycling_monthly` - Verfolgt monatliche Kompressor-Starts (Reset am 1. des Monats)
  - **Flankenerkennung**: Verwendet HP_STATE Register (1002) statt HP_OPERATING_STATE, erkennt "START COMPRESSOR" Status (Wert 5)

#### Verbesserungen
- Verbesserte Entity-Namensgebung mit ordnungsgemäßen Geräte- und Sub-Geräte-Präfixen
- Verbesserte Übersetzungs-Ladung und -Anwendung für alle Entity-Typen
- Bessere Integration mit Home Assistants Übersetzungssystem
- **Write-Interval-Optimierung**: Reduziertes Write-Interval von 41 Sekunden auf 9 Sekunden für schnellere Reaktionszeiten
- **Externe Verbrauchssensor-Validierung**: Verbesserte Validierung externer Verbrauchssensoren mit Entity Registry Fallback-Prüfung, ermöglicht Sensoren auch dann zu akzeptieren, wenn sie beim Start noch nicht im State verfügbar sind. Runtime Retry-Mechanismus behandelt temporäre Nicht-Verfügbarkeit elegant.

### [1.4.3] - 2025-11-04
#### Fehlerbehebungen
- **ISSUE 39**  Modebus batch Reads erkennen Fehler falsch: Schnelleres Umsschalten zu individual reads, damit korrekte Sensoren wieder zur Verfügung stehen
- **ISSUE 22** Zusätzliches logging eingefügt, um Fehler zu identifizieren
- **Einheit des Sensors volume_flow_heat_sink korregiert** zu l/h

### [1.4.2] - 2025-10-24

#### Fehlerbehebungen
- **Test-Reparaturen**: Behoben fehlgeschlagene Tests durch Ersetzen von Mock-Objekten mit ordnungsgemäßen Test-Implementierungen
- **Verbesserte Test-Zuverlässigkeit**: Reduzierte false-positive Test-Fehler und verbesserte Test-Stabilität
- **Integration-Reload-Fehler**: Behoben Fehler beim Neuladen der Integration
- **Konfigurations-Fix**: Behoben `default_config` in `load_lambda_config()` um alle erforderlichen Keys einzubinden (`energy_consumption_sensors`, `energy_consumption_offsets`, `modbus`)

#### Geändert
- **Register-Order-Werte**: Konfigurationswerte von `"big"`/`"little"` auf `"high_first"`/`"low_first"` geändert für bessere Klarheit
  - Alte Werte (`big`/`little`) werden weiterhin mit automatischer Konvertierung unterstützt
  - Neuer Standard ist `"high_first"` (ersetzt `"big"`)
  - Verbesserte Dokumentation und Kommentare zur Klärung von Register-Reihenfolge vs. Byte-Endianness

#### Verbesserungen
- **Test-Optimierung**: 57 Tests erfolgreich repariert und optimiert
- **Gitignore-Korrektur**: Korrigiert .gitignore für ordnungsgemäße Einbindung aller docs-Unterverzeichnisse
- **Service-Dokumentation**: Erstellt umfassende Dokumentation für zukünftige Service-Optimierungen
- **Service-Scheduler-Optimierung**: Implementierte intelligente Service-Scheduler, die nur aktiviert werden, wenn PV-Surplus oder Raumthermostat-Steuerungsoptionen aktiviert sind, wodurch der Ressourcenverbrauch erheblich reduziert wird, wenn Services nicht benötigt werden

---



### [1.4.1] - 2025-10-21

#### Neue Funktionen
- **Massive Performance-Verbesserungen**: Dramatisch verbesserte Start- und Update-Performance der Integration
  - **Startzeit**: Reduziert um ~72% (von ~7,3s auf ~2,05s) durch intelligente Background-Auto-Detection
  - **Update-Zyklen**: Reduziert um ~50% (von >30s auf <15s) durch globale Register-Deduplizierung
  - **Modbus-Traffic**: Reduziert um ~80% durch Eliminierung von Duplikat-Register-Reads
- **Intelligente Auto-Detection**: Implementierte Background-Auto-Detection für bestehende Konfigurationen, eliminiert Startverzögerungen bei gleichzeitiger Aufrechterhaltung der Hardware-Änderungserkennung
- **Globaler Register-Cache**: Hinzugefügtes umfassendes Register-Deduplizierungssystem, das Duplikat-Modbus-Reads über alle Module (HP, Boiler, Buffer, Solar, HC) eliminiert
- **Optimiertes Batch-Reading**: Verbesserte Modbus-Batch-Reads mit größeren zusammenhängenden Register-Bereichen und reduzierten individuellen Read-Schwellenwerten
- **Paralleles Template-Setup**: Template-Sensoren laden nun in Background-Tasks, verhindert Start-Blockierung
- **Persist-I/O-Optimierung**: Hinzugefügte Debouncing- und Dirty-Flag-Mechanismen zur Reduzierung unnötiger Datei-Schreibvorgänge
- **Verbindungs-Health-Optimierung**: Reduzierte Verbindungs-Timeout von 5s auf 2s für schnellere Fehlererkennung

#### Verbesserungen
- **Erweiterte Energieverfolgung**: Verbesserte Verbrauchsverfolgung mit automatischer Einheitenkonvertierung (Wh/kWh/MWh)
- **Robuste Sensor-Behandlung**: Hinzugefügter Retry-Mechanismus für Sensor-Verfügbarkeit beim Start
- **Umfassende Protokollierung**: Hinzugefügte detaillierte Protokollierung für Sensor-Wechsel-Erkennung und Energieberechnungen
- **Monatliche & Jährliche Verbrauchssensoren**: Hinzugefügte monatliche und jährliche Energieverbrauchssensoren für Langzeitverfolgung
- **Service-Setup-Optimierung**: Dienste werden nun nur einmal eingerichtet, unabhängig von der Anzahl der Einträge
- **Konfigurationsfluss-Verbesserungen**: Erweiterte Validierung für bestehende Verbindungen und IP-Adressen, veraltete Module entfernt
- **Generalisierte Reset-Funktionen**: Implementierte generalisierte Reset-Funktionen für alle Sensor-Typen mit erweiterten Tests
- **Code-Bereinigung**: Bereinigt const.py, YAML-Templates und allgemeine Codestruktur
- **Dokumentations-Updates**: Aktualisierte Dokumentation und erstellte Programmablaufdiagramme

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.4.0] - 2025-10-05

#### Neue Funktionen
- **Verbrauchssensoren nach Betriebsart**: Hinzugefügte konfigurierbare Verbrauchssensoren, die den Energieverbrauch nach Betriebsart (Heizen, Warmwasser, Kühlen, Abtauen) mit anpassbaren Quellsensoren verfolgen (Issue #21)
- **Register-Reihenfolge-Konfiguration**: Hinzugefügte Register-Reihenfolge-Konfiguration in `lambda_wp_config.yaml` für ordnungsgemäße 32-Bit-Wert-Interpretation aus mehreren 16-Bit-Registern (Issue #22)
- **Sensor-Wechsel-Erkennung**: Implementierte automatische Erkennung von Energie-Sensor-Wechseln mit intelligenter Behandlung von Sensor-Wert-Übergängen zur Vermeidung falscher Verbrauchsberechnungen

#### Fehlerbehebungen
- **Register-Reihenfolge-Fix**: Behoben Register-Reihenfolge-Probleme für 32-Bit-Werte mit initialem Quick-Fix-Ansatz (Issue #22)
- **Daily-Sensor-Reset-Automatisierung**: Behoben Fehler in der Automatisierung zum Zurücksetzen der täglichen Sensoren (Issue #29)
- **Auto-Detection**: Behoben Auto-Detection erkannte bestehende Konfigurationen (IP/Port/SlaveId) nicht
- **DCHP Discovery**: Behoben DCHP Discovery Fehlermeldungen
- **HASS Validation**: Behoben Home Assistant Validierungsfehler
- **Daily Reset Funktion**: Repariert Daily Reset-Funktion für Sensoren

#### Verbesserungen
- **Erweiterte Energieverfolgung**: Verbesserte Verbrauchsverfolgung mit automatischer Einheitenkonvertierung (Wh/kWh/MWh)
- **Robuste Sensor-Behandlung**: Hinzugefügter Retry-Mechanismus für Sensor-Verfügbarkeit beim Start
- **Umfassende Protokollierung**: Hinzugefügte detaillierte Protokollierung für Sensor-Wechsel-Erkennung und Energieberechnungen
- **Monatliche & Jährliche Verbrauchssensoren**: Hinzugefügte monatliche und jährliche Energieverbrauchssensoren für Langzeitverfolgung
- **Service-Setup-Optimierung**: Dienste werden nun nur einmal eingerichtet, unabhängig von der Anzahl der Einträge
- **Konfigurationsfluss-Verbesserungen**: Erweiterte Validierung für bestehende Verbindungen und IP-Adressen, veraltete Module entfernt
- **Generalisierte Reset-Funktionen**: Implementierte generalisierte Reset-Funktionen für alle Sensor-Typen mit erweiterten Tests
- **Code-Bereinigung**: Bereinigt const.py, YAML-Templates und allgemeine Codestruktur
- **Dokumentations-Updates**: Aktualisierte Dokumentation und erstellte Programmablaufdiagramme

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.3.0] - 2025-01-03

#### Neue Funktionen
- **Neue 2H/4H Cycling-Sensoren**: Hinzugefügte 2-Stunden- und 4-Stunden-Cycling-Sensoren für detaillierte Wärmepumpen-Betriebsüberwachung
- **Erweiterte Cycling-Offsets**: Verbesserte Cycling-Counter-Offset-Funktionalität für Gesamtsensor-Anpassungen beim Austausch von Wärmepumpen oder Zurücksetzen von Zählern
- **Robuste Flankenerkennung**: Implementierung einer robusten Flankenerkennung für Wärmepumpen-Betriebszustände mit verbesserter Zuverlässigkeit
- **Dynamische Fehlerbehandlung**: Erweiterte Batch-Read-Fehlerbehandlung mit automatischem Fallback auf Einzel-Lesevorgänge nach Schwellenwert-Fehlern
- **Cycling-Warnungen-Management**: Hinzugefügte Cycling-Warnungen-Unterdrückungslogik zur Verwaltung von Entity-Registrierungsproblemen

#### Fehlerbehebungen
- **Konfigurationsdatei-Erstellung**: Behoben, dass `lambda_wp_config.yaml` nicht automatisch aus der Vorlage erstellt wurde, um eine ordnungsgemäße Konfiguration sicherzustellen
- **Tägliche Cycling-Sensoren**: Behoben, dass tägliche Cycling-Sensoren nun ordnungsgemäß Werte anzeigen und korrekt funktionieren

#### Verbesserungen
- **Coordinator-Initialisierung**: Verbesserter Coordinator-Initialisierungsprozess mit erweiterter Fehlerbehandlung
- **Debug-Protokollierung**: Umfassende Debug-Protokolle für die Nachverfolgung von Offset-Änderungen und Systemverhalten hinzugefügt
- **Dokumentation**: Aktualisierte Dokumentation zur Widerspiegelung neuer Funktionen und Konfigurationsoptionen
- **Modbus-Konfiguration**: Erweiterte Lambda Heat Pumps Integration mit spezifischen Modbus-Konfigurationen

#### Technische Änderungen
- Automatische `lambda_wp_config.yaml`-Erstellung aus `LAMBDA_WP_CONFIG_TEMPLATE`
- Integration der Konfigurationsdatei-Erstellung in bestehende Migrations-Pipeline
- Erweiterte Fehlerbehandlung in `LambdaDataUpdateCoordinator`
- Verbesserte Sensor-Attribut-Ladung mit besserer Fehlerwiederherstellung

---

### [1.2.2] - 2025-08-18

#### ⚠️ BREAKING CHANGES IN DIESER VERSION - BACKUP ERFORDERLICH

Diese Version enthält wesentliche Änderungen an der Entity Registry und den Sensor-Namenskonventionen. **Bitte erstellen Sie ein vollständiges Backup Ihrer Home Assistant-Konfiguration vor dem Update.**

**Was sich ändern wird:**
- Automatische Migration bestehender Sensor-Entities zur Vermeidung von Duplikaten
- Aktualisiertes unique_id-Format für bessere Konsistenz
- Sensor-Filterung basierend auf Firmware-Kompatibilität

**Nach der Migration bitte überprüfen:**
- Sensor-Namen und Langzeitdaten sind korrekt erhalten
- Keine doppelten Entities in Ihrem System vorhanden
- Alle Sensoren funktionieren wie erwartet
- **Automatisierungen müssen möglicherweise aktualisiert werden**, wenn sie auf migrierte Sensor-Entities verweisen

**Eine Kopie der core.config_entries, core.device_registry und core.entity_registry wird vor der Sensor-Migration erstellt und kann aus dem /lambda_heat_pumps-Ordner in den versteckten .storage-Ordner kopiert werden, um die Änderungen rückgängig zu machen. Allerdings muss dann Version 1.0.9 der Integration neu installiert werden, damit das System ordnungsgemäß funktioniert.**

---

### [1.1.0] - 2025-08-03

#### Wichtige Änderungen
- **Wechsel zu asynchronen Modbus-Clients** - Vollständige Migration von synchroner zu asynchroner Modbus-Kommunikation für bessere Kompatibilität mit anderen Integrationen
- **Runtime API-Kompatibilität** - Automatische Erkennung und Anpassung an verschiedene pymodbus-Versionen (1.x, 2.x, 3.x)
- **Leistungsverbesserungen** - Nicht-blockierende Modbus-Operationen für bessere Systemleistung
- **Entity Registry Migration** - Automatische Migration von allgemeinen und Klima-Sensoren zur Vermeidung doppelter Entities mit konsistentem unique_id-Format

#### Hinzugefügt
- Asynchrone Modbus-Wrapper-Funktionen in `modbus_utils.py`
- Runtime API-Kompatibilitätserkennung für pymodbus-Versionen
- Umfassende Fehlerbehandlung für asynchrone Modbus-Operationen
- Erweiterte Cycling-Counter mit täglichen, gestrigen und Gesamtwerten für alle Betriebsarten

#### Geändert
- Alle Modbus-Operationen zu `AsyncModbusTcpClient` migriert
- Coordinator, config_flow, services und climate Module für asynchrone Operationen aktualisiert
- `async_add_executor_job`-Wrapper zugunsten direkter asynchroner Aufrufe entfernt

#### Behoben
- RuntimeWarning: "coroutine was never awaited" in der Automatisierungseinrichtung
- Callback-Funktionsimplementierung korrigiert
- Code-Qualitätsverbesserungen und Linting-Probleme behoben
- Doppelte Sensor-Entities mit "_2"-Suffix nach Updates
- Inkonsistentes unique_id-Format für allgemeine und Klima-Sensoren
- Sensor-Filterung basierend auf Firmware-Einstellungen

#### Entfernt
- **`use_legacy_modbus_names` Konfigurationsoption** - Diese Option wurde entfernt, da sie nach der automatischen Migration aller Sensoren zum Legacy-Namensschema (`use_legacy=true`) obsolet wurde. Alle bestehenden Installationen verwenden automatisch das Legacy-Namensformat.

---

### [1.0.9] - 2024-12-19

#### Hinzugefügt
- Kompatibilität mit pymodbus >= 3.6.0
- Zähler für Wärmepumpen-Cycling nach Betriebsart
- Erweiterte Statistiken für verschiedene Betriebsarten

#### Geändert
- Aktualisiert auf neue pymodbus API (3.x)
- Redundante Parameter in `read_holding_registers`-Aufrufen entfernt
- Synchrone `connect()`-Aufrufe statt asynchroner
- Code-Stil-Verbesserungen (flake8-kompatibel)

#### Behoben
- Import-Fehler in allen Modulen behoben
- Leerzeichen-Probleme gelöst
- HACS-Validierungsfehler korrigiert
- Manifest-Schlüssel ordnungsgemäß sortiert

---

### [1.0.0] - Erste Version

#### Hinzugefügt
- Erste Version der Lambda Heat Pumps Integration
- Modbus-Kommunikation für Wärmepumpen
- Cycle Counter-Erkennung
- Climate Entity für Wärmepumpen-Steuerung

<!-- /lang:de -->