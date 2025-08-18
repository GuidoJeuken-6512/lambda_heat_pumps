# Changelog

**Deutsche Version siehe unten / German version see below**

## ⚠️ IMPORTANT WARNING - WICHTIGE WARNUNG

### English
**BREAKING CHANGES IN THIS RELEASE - BACKUP REQUIRED**

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
**A Copy of the core.config_entries, core.device_registry and core.entity_registry  is    created before the sensors are migrated and can be copied back from the /lambda_heat_pumps folder to the hidden .storage folder to undo the changes. However, version 1.0.9 of the integration must then be reinstalled for the system to work properly.** 

### Deutsch
**TIEFGREIFENDE ÄNDERUNGEN IN DIESEM RELEASE - BACKUP ERFORDERLICH**

Dieses Release enthält bedeutende Änderungen am Entity Registry und den Sensor-Namenskonventionen. **Bitte erstellen Sie vor dem Update ein vollständiges Backup Ihrer Home Assistant Konfiguration.**

**Was sich ändert:**
- Automatische Migration bestehender Sensor-Entities zur Vermeidung von Duplikaten
- Aktualisiertes unique_id Format für bessere Konsistenz
- Sensor-Filterung basierend auf Firmware-Kompatibilität

**Nach der Migration bitte prüfen:**
- Sensor-Namen und Langzeitdaten sind korrekt erhalten
- Keine doppelten Entities in Ihrem System existieren
- Alle Sensoren funktionieren wie erwartet
- **Automatisierungen müssen möglicherweise angepasst werden**, falls sie auf migrierte Sensor-Entities verweisen
**Eine Kopie der Dateien core.config_entries, core.device_registry und core.entity_registry wird vor der Migration der Sensoren erstellt und kann aus dem Order /lambda_heat_pumps wieder in den versteckten Ordner .storage kopiert werden, um die Änderungen rückgängig zu machen. Dann muss aber auch die Version 1.0.9 der Integration wieder installiert werden, damit das System sauber funktioniert.**

## [1.1.0] - 2025-08-03

### Major Changes
- **Switch to asynchronous Modbus clients** - Complete migration from synchronous to asynchronous Modbus communication for better compatibility with other integrations
- **Runtime API compatibility** - Automatic detection and adaptation to different pymodbus versions (1.x, 2.x, 3.x)
- **Performance improvements** - Non-blocking Modbus operations for better system performance
- **Entity Registry Migration** - Automatic migration of general and climate sensors to prevent duplicate entities with consistent unique_id format

### Added
- Asynchronous Modbus wrapper functions in `modbus_utils.py`
- Runtime API compatibility detection for pymodbus versions
- Comprehensive error handling for async Modbus operations
- Extended cycling counters with daily, yesterday and total values for all operating modes

### Changed
- All Modbus operations migrated to `AsyncModbusTcpClient`
- Coordinator, config_flow, services, and climate modules updated for async operations
- Removed `async_add_executor_job` wrappers in favor of direct async calls

### Fixed
- RuntimeWarning: "coroutine was never awaited" in automation setup
- Callback function implementation corrected
- Code quality improvements and linting issues resolved
- Duplicate sensor entities with "_2" suffix after updates
- Inconsistent unique_id format for general and climate sensors
- Sensor filtering based upon firmware settings

### Removed
- **`use_legacy_modbus_names` configuration option** - This option has been removed as it became obsolete after the automatic migration of all sensors to the legacy naming scheme (`use_legacy=true`). All existing installations will automatically use the legacy naming format.

## [1.0.9] - 2024-12-19

### Added
- Compatibility with pymodbus >= 3.6.0
- Counters for heat pump cycling by operating mode
- Extended statistics for different operating modes

### Changed
- Updated to new pymodbus API (3.x)
- Removed redundant parameters in `read_holding_registers` calls
- Synchronous `connect()` calls instead of asynchronous
- Code style improvements (flake8-compatible)

### Fixed
- Import errors in all modules fixed
- Whitespace issues resolved
- HACS validation errors corrected
- Manifest keys properly sorted

## [1.0.0] - Initial Release

### Added
- First version of Lambda Heat Pumps Integration
- Modbus communication for heat pumps
- Cycle counter detection
- Climate entity for heat pump control

---

# Changelog (Deutsch)

## [1.1.0] - 2025-07-24

### Major Changes
- **Umstellung auf asynchrone Modbus-Clients** - Vollständige Migration von synchroner zu asynchroner Modbus-Kommunikation für bessere Kompatibilität mit anderen Integrationen
- **Runtime API-Kompatibilität** - Automatische Erkennung und Anpassung an verschiedene pymodbus Versionen (1.x, 2.x, 3.x)
- **Performance-Verbesserungen** - Nicht-blockierende Modbus-Operationen für bessere Systemleistung
- **Entity Registry Migration** - Automatische Migration von General- und Climate-Sensoren zur Vermeidung doppelter Entities mit konsistentem unique_id Format

### Added
- Asynchrone Modbus-Wrapper-Funktionen in `modbus_utils.py`
- Runtime API-Kompatibilitätserkennung für pymodbus Versionen
- Umfassende Fehlerbehandlung für asynchrone Modbus-Operationen
- Erweiterte Zyklenzähler mit täglichen, gestern und insgesamt Werten für alle Betriebsarten

### Changed
- Alle Modbus-Operationen auf `AsyncModbusTcpClient` migriert
- Coordinator, config_flow, services und climate Module für asynchrone Operationen aktualisiert
- Entfernung von `async_add_executor_job` Wrappern zugunsten direkter async Aufrufe

### Fixed
- RuntimeWarning: "coroutine was never awaited" in Automation-Setup
- Callback-Funktionsimplementierung korrigiert
- Code-Qualitätsverbesserungen und Linting-Probleme behoben
- Doppelte Sensor-Entities mit "_2" Suffix nach Updates
- Inkonsistentes unique_id Format für General- und Climate-Sensoren
- Sensor Filterung basierend auf der Firmware

### Removed
- **`use_legacy_modbus_names` Konfigurationsoption** - Diese Option wurde entfernt, da sie nach der automatischen Migration aller Sensoren auf das Legacy-Namensschema (`use_legacy=true`) obsolet geworden ist. Alle bestehenden Installationen verwenden automatisch das Legacy-Namensformat.

## [1.0.9] - 2024-12-19

### Added
- Kompatibilität mit pymodbus >= 3.6.0
- Zähler für Wärmepumpen-Taktung nach Betriebsart
- Erweiterte Statistiken für verschiedene Betriebsmodi

### Changed
- Aktualisiert auf neue pymodbus API (3.x)
- Entfernt überflüssige Parameter bei `read_holding_registers` Aufrufen
- Synchroner Aufruf von `connect()` statt asynchron
- Code-Style Verbesserungen (flake8-kompatibel)

### Fixed
- Import-Fehler in allen Modulen behoben
- Whitespace-Probleme bereinigt
- HACS-Validierungsfehler korrigiert
- Manifest-Schlüssel korrekt sortiert

## [1.0.0] - Initial Release

### Added
- Erste Version der Lambda Heat Pumps Integration
- Modbus-Kommunikation für Wärmepumpen
- Zyklenzähler-Erfassung
- Climate-Entity für Wärmepumpensteuerung 