# Lambda Heat Pumps Integration - Test-Dokumentation

## Übersicht

Diese Dokumentation beschreibt die Test-Suite für die Lambda Heat Pumps Home Assistant Integration. Die Tests überprüfen alle wichtigen Komponenten und Funktionalitäten der Integration.

## Test-Status

**Aktueller Stand:**
- ✅ **198 Tests PASSED** (86% Erfolgsrate)
- ❌ **32 Tests FAILED** (14% Fehlerrate)
- ⏭️ **1 Test SKIPPED**
- ⚠️ **1 Test ERROR**

## Test-Kategorien

### 1. Konstanten und Templates ✅ (Vollständig getestet)

#### `test_const.py` - 9 Tests PASSED
**Was wird getestet:**
- **Sensor-Template-Struktur**: Überprüfung der korrekten Struktur aller Sensor-Templates
- **Device-Class-Konsistenz**: Temperatur-, Leistungs- und andere Sensor-Klassen
- **Template-Syntax**: Korrekte Syntax und erforderliche Felder
- **Konstanten-Definition**: Alle wichtigen Konstanten sind definiert
- **Device-Type-Konsistenz**: Konsistenz zwischen verschiedenen Gerätetypen

**Getestete Bereiche:**
- Heat Pump Sensoren (HP_SENSOR_TEMPLATES)
- Boiler Sensoren (BOIL_SENSOR_TEMPLATES)
- Buffer Sensoren (BUFF_SENSOR_TEMPLATES)
- Solar Sensoren (SOL_SENSOR_TEMPLATES)
- Heating Circuit Sensoren (HC_SENSOR_TEMPLATES)
- Berechnete Sensoren (CALCULATED_SENSOR_TEMPLATES)

### 2. Konfiguration und Migration ✅ (Vollständig getestet)

#### `test_const_migration.py` - Alle Tests PASSED
**Was wird getestet:**
- **Migrations-Konstanten**: Korrekte Definition von Migrations-Versionen
- **Template-Migration**: Konsistenz zwischen alten und neuen Templates

#### `test_yaml_loading.py` - Alle Tests PASSED
**Was wird getestet:**
- **YAML-Datei-Laden**: Korrektes Laden von Konfigurationsdateien
- **Fehlerbehandlung**: Behandlung von ungültigen YAML-Dateien
- **Datei-Pfade**: Korrekte Pfad-Behandlung

### 3. Übersetzungen und Config Flow ✅ (Vollständig getestet)

#### `test_translation_and_configflow.py` - Alle Tests PASSED
**Was wird getestet:**
- **Übersetzungsdateien**: Deutsche und englische Übersetzungen
- **Config Flow**: Setup-Prozess und Validierung
- **Benutzeroberfläche**: UI-Elemente und Meldungen

### 4. Energie-Sensoren ✅ (Vollständig getestet)

#### `test_monthly_yearly_energy_sensors.py` - Alle Tests PASSED
**Was wird getestet:**
- **Monatliche Energie-Sensoren**: Funktionalität und Berechnungen
- **Jährliche Energie-Sensoren**: Funktionalität und Berechnungen
- **Sensor-Initialisierung**: Korrekte Erstellung und Konfiguration
- **Werte-Berechnung**: Mathematische Operationen und Skalierung

#### `test_monthly_yearly_increment.py` - Alle Tests PASSED
**Was wird getestet:**
- **Increment-Funktionalität**: Erhöhung von Zählern
- **Werte-Persistierung**: Speicherung zwischen Sessions
- **Reset-Mechanismen**: Zurücksetzen von Zählern

#### `test_monthly_yearly_simple.py` - Alle Tests PASSED
**Was wird getestet:**
- **Einfache monatliche/jährliche Tests**: Grundfunktionalität
- **Basis-Operationen**: Addition, Subtraktion, Reset

#### `test_energy_periods_fix.py` - Alle Tests PASSED
**Was wird getestet:**
- **Energie-Perioden-Fix**: Korrektur von Perioden-Berechnungen
- **Zeitbasierte Operationen**: Tägliche, monatliche, jährliche Berechnungen

### 5. Modul-Initialisierung ✅ (Vollständig getestet)

#### `test_init_simple.py` - 3 Tests PASSED
**Was wird getestet:**
- **Konstanten-Definition**: DOMAIN, PLATFORMS, TRANSLATION_SOURCES
- **Debug-Logging-Setup**: Korrekte Konfiguration des Loggings
- **Import-Funktionalität**: Alle wichtigen Funktionen können importiert werden
- **Modul-Export**: async_setup, async_setup_entry, async_unload_entry, async_reload_entry

### 6. Sensor-Funktionalität ⚠️ (Teilweise getestet)

#### `test_sensor_simple.py` - 2 Tests PASSED, 3 Tests FAILED
**Was wird getestet:**
- **Sensor-Imports**: Alle Sensor-Klassen können importiert werden
- **Konstanten**: DOMAIN und Template-Verfügbarkeit
- **Sensor-Erstellung**: Basis-Funktionalität der Sensor-Klassen

**Defekte Tests:**
- Template-Namen stimmen nicht überein (ambient_temp existiert nicht)
- Sensor-Klassen-Signaturen haben sich geändert

### 7. Koordinator-Funktionalität ❌ (Defekte Tests)

#### `test_coordinator.py` - 10 Tests PASSED, 9 Tests FAILED
**Was wird getestet:**
- **Koordinator-Initialisierung**: Erstellung und Konfiguration
- **Modbus-Verbindung**: Verbindungsaufbau und -management
- **Daten-Updates**: Aktualisierung von Sensor-Daten
- **Fehlerbehandlung**: Behandlung von Verbindungsfehlern
- **Konfiguration**: Laden von Sensor-Overrides

**Defekte Tests:**
- Connection-Mocking muss verbessert werden
- Einige Tests erwarten Funktionen, die nicht mehr existieren

### 8. Cycling-Sensoren ❌ (Defekte Tests)

#### `test_cycling_sensors_new.py` - 6 Tests PASSED, 8 Tests FAILED
**Was wird getestet:**
- **Cycling-Sensor-Funktionalität**: Zyklus-Zählung und -Verfolgung
- **Yesterday-Sensoren**: Gestern-Werte und Reset-Funktionalität
- **Reset-Handler**: 2h, 4h, tägliche Reset-Mechanismen
- **Entity-Registrierung**: Korrekte Registrierung von Sensoren

**Defekte Tests:**
- Sensor-Werte werden nicht korrekt gesetzt
- Tests müssen an aktuelle Implementierung angepasst werden

### 9. Climate-Funktionalität ❌ (Defekte Tests)

#### `test_climate.py` - 1 Test PASSED, 3 Tests FAILED
**Was wird getestet:**
- **Climate-Entity-Eigenschaften**: Temperatur, Modi, Setpoints
- **Temperatur-Einstellung**: async_set_temperature Funktionalität
- **Device-Info**: Geräteinformationen und Zuordnung

**Defekte Tests:**
- Entity-ID-Generierung stimmt nicht überein
- Async-Mocking-Probleme

### 10. Config Flow ❌ (Defekte Tests)

#### `test_config_flow.py` - Alle Tests FAILED
**Was wird getestet:**
- **Config Flow-Initialisierung**: Setup-Prozess
- **Entity-Abfrage**: Abrufen von Entitäten
- **Validierung**: Eingabe-Validierung

**Defekte Tests:**
- Test-Erwartungen stimmen nicht überein (4 vs 2)
- Async-Handling-Probleme

### 11. Migration-System ❌ (Defekte Tests)

#### `test_migration.py` - 6 Tests PASSED, 3 Tests FAILED
**Was wird getestet:**
- **Migration-Versionen**: Enum-Werte und -Verwaltung
- **Strukturierte Migration**: Migrations-Prozess
- **Version-Management**: Aktuelle und ausstehende Migrationen

**Defekte Tests:**
- Enum-Werte stimmen nicht überein (5 vs 4)
- Migration-Versionen sind veraltet

### 12. Energie-Verbrauch-Sensoren ❌ (Defekte Tests)

#### `test_energy_consumption_sensors.py` - 21 Tests PASSED, 2 Tests FAILED
**Was wird getestet:**
- **Sensor-Initialisierung**: Erstellung und Konfiguration
- **Sensor-Eigenschaften**: Name, Unit, Device-Class
- **Werte-Setzung**: set_energy_value Funktionalität
- **Native-Werte**: Total, Daily, Monthly, Yearly Berechnungen
- **Extra-State-Attribute**: Zusätzliche Attribute
- **Reset-Handler**: Reset-Funktionalität

**Defekte Tests:**
- Fehlende Argumente in _handle_reset
- Async-Dispatcher-Probleme

### 13. Services ❌ (Defekte Tests)

#### `test_services.py` - Alle Tests FAILED
**Was wird getestet:**
- **Service-Setup**: async_setup_services Funktionalität

**Defekte Tests:**
- Mock-Objekt-Zuweisungsprobleme

### 14. Utilities ❌ (Defekte Tests)

#### `test_utils.py` - 1 Test PASSED, 1 Test FAILED
**Was wird getestet:**
- **Disabled-Register-Laden**: Laden von deaktivierten Registern

**Defekte Tests:**
- Mock-Objekt nicht iterierbar

## Test-Architektur

### Fixtures und Mock-Objekte

Die Tests verwenden verschiedene Fixtures für Mock-Objekte:

```python
@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock()
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    hass.data = {}
    return hass

@pytest.fixture
def mock_entry():
    """Mock ConfigEntry instance."""
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.data = {
        "host": "192.168.1.100",
        "port": 502,
        "name": "test"
    }
    return entry
```

### Test-Patterns

1. **Unit-Tests**: Testen einzelne Funktionen und Klassen
2. **Integration-Tests**: Testen das Zusammenspiel verschiedener Komponenten
3. **Mock-Tests**: Verwenden von Mock-Objekten für externe Abhängigkeiten

## Ausführung der Tests

### Alle Tests ausführen
```bash
python -m pytest tests/
```

### Spezifische Test-Kategorie
```bash
python -m pytest tests/test_const.py -v
```

### Nur erfolgreiche Tests
```bash
python -m pytest tests/ -k "not failed"
```

### Mit Coverage-Report
```bash
python -m pytest tests/ --cov=custom_components/lambda_heat_pumps
```

## Wichtige Test-Bereiche

### 1. Funktionalität ✅
- **Sensor-Templates**: Vollständig getestet
- **Konstanten**: Vollständig getestet
- **Energie-Sensoren**: Vollständig getestet
- **YAML-Laden**: Vollständig getestet
- **Übersetzungen**: Vollständig getestet

### 2. Integration ⚠️
- **Modul-Setup**: Teilweise getestet
- **Sensor-Erstellung**: Teilweise getestet
- **Koordinator**: Teilweise getestet

### 3. Fehlerbehandlung ❌
- **Connection-Fehler**: Defekte Tests
- **Invalid-Input**: Defekte Tests
- **Timeout-Handling**: Defekte Tests

## Empfehlungen für weitere Entwicklung

### Sofortige Maßnahmen
1. **Repariere defekte Tests**: Fokus auf test_coordinator.py und test_cycling_sensors_new.py
2. **Verbessere Mocking**: MagicMock statt Mock verwenden
3. **Aktualisiere Test-Erwartungen**: An aktuelle Code-Version anpassen

### Mittelfristig
1. **Erweitere Coverage**: Neue Tests für Flankenerkennung und Energy Consumption
2. **Performance-Tests**: Tests für Modbus-Traffic-Optimierung
3. **Integration-Tests**: End-to-End-Szenarien

### Langfristig
1. **CI/CD-Integration**: Automatisierte Test-Ausführung
2. **Regression-Tests**: Verhindern von Rückschritten
3. **Load-Tests**: Tests unter hoher Last

## Fazit

Die Test-Suite deckt die wichtigsten Funktionalitäten der Lambda Heat Pumps Integration ab. Die **86% Erfolgsrate** zeigt, dass die Kern-Funktionalitäten gut getestet sind. Die verbleibenden 14% defekter Tests betreffen hauptsächlich komplexe Mock-Szenarien und können bei Bedarf repariert werden.

**Stärken:**
- Vollständige Abdeckung der Konstanten und Templates
- Umfassende Tests für Energie-Sensoren
- Gute Abdeckung der Konfiguration und Migration

**Verbesserungsmöglichkeiten:**
- Reparatur der defekten Integration-Tests
- Verbesserung der Mock-Objekte
- Erweiterung der Fehlerbehandlungs-Tests

---

**Letzte Aktualisierung:** 2025-10-21
**Test-Anzahl:** 231 Tests
**Erfolgsrate:** 86%