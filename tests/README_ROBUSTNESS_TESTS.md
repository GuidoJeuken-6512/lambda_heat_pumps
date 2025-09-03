# Robustheit-Features Tests

## Übersicht

Dieses Dokument beschreibt die Tests für die neuen Robustheit-Features der Lambda Heat Pumps Integration.

## Implementierte Test-Dateien

### 1. `test_circuit_breaker.py`
**Tests für SmartCircuitBreaker Klasse**
- ✅ Initialisierung mit Standard- und benutzerdefinierten Parametern
- ✅ Circuit Breaker Zustände (geschlossen/offen)
- ✅ Recovery-Timeout Verhalten
- ✅ Force-Open Verhalten (verhindert automatische Wiederherstellung)
- ✅ Erfolgreiche Ausführung (Reset des Circuit Breakers)
- ✅ Netzwerkfehler-Behandlung (normale Circuit Breaker Logik)
- ✅ Modbus-Protokollfehler (sofortiger Force-Open)
- ✅ Andere Fehlertypen (normale Circuit Breaker Logik)
- ✅ ModbusException-Erkennung (mit pymodbus und Fallback)
- ✅ Status-Informationen abrufen
- ✅ Manueller Reset
- ✅ Komplette Integration-Workflows

**15 Tests - Alle erfolgreich**

### 2. `test_offline_manager.py`
**Tests für HACompatibleOfflineManager Klasse**
- ✅ Initialisierung mit Standard- und benutzerdefinierten Parametern
- ✅ Daten-Update Funktionalität
- ✅ Offline-Daten abrufen (online/offline Zustände)
- ✅ Maximale Offline-Dauer überschreiten
- ✅ HA-Attribute bewahren (device_class, state_class, last_reset)
- ✅ Energie-Sensor last_reset spezifisch bewahren
- ✅ Offline-Status erkennen
- ✅ Offline-Dauer berechnen
- ✅ Status-Informationen abrufen
- ✅ Daten löschen
- ✅ Kompletter Offline-Workflow
- ✅ Offline-Dauer-Limit Verhalten

**14 Tests - Alle erfolgreich**

### 3. `test_utils_robustness.py`
**Tests für Exponential Backoff Funktion**
- ✅ Erfolgreiche Lesevorgänge (erster Versuch)
- ✅ Erfolgreiche Lesevorgänge nach Retries
- ✅ Alle Retries fehlgeschlagen
- ✅ Exponential Backoff Timing
- ✅ Maximale Verzögerung begrenzen
- ✅ Minimale Verzögerung (mindestens 1 Sekunde)
- ✅ Jitter-Variation
- ✅ Timeout-Parameter korrekt übergeben
- ✅ Verschiedene Exception-Typen behandeln
- ✅ Parameter-Validierung
- ✅ Logging bei Retries
- ✅ Logging bei finalem Fehler

**12 Tests - Alle erfolgreich**

### 4. `test_circuit_breaker_sensor.py`
**Tests für CircuitBreakerSensor Klasse**
- ✅ Sensor-Initialisierung
- ✅ is_on Property (Circuit geschlossen/offen)
- ✅ Extra State Attributes
- ✅ Available Property (immer verfügbar)
- ✅ Update-Methode
- ✅ Device Class (CONNECTIVITY)
- ✅ Sensor-Zustandsänderungen
- ✅ Status-Attribute Updates
- ✅ Force-Open Attribut
- ✅ Unique ID Format
- ✅ Sensor-Name
- ✅ Icon Property
- ✅ Circuit Breaker Integration

**14 Tests - Alle erfolgreich**

## Test-Statistiken

- **Gesamt: 55 Tests**
- **Erfolgreich: 55 Tests (100%)**
- **Fehlgeschlagen: 0 Tests**
- **Warnungen: 2 (nur Home Assistant Deprecation Warnings)**

## Test-Abdeckung

Die Tests decken alle wichtigen Aspekte der Robustheit-Features ab:

### SmartCircuitBreaker
- ✅ Alle Zustände und Übergänge
- ✅ Fehlerdifferenzierung (Netzwerk vs. Protokoll)
- ✅ Recovery-Mechanismen
- ✅ Force-Open Verhalten
- ✅ Status-Reporting

### HACompatibleOfflineManager
- ✅ Online/Offline-Zustände
- ✅ HA-Attribute bewahren
- ✅ Offline-Dauer-Limits
- ✅ Daten-Management
- ✅ Status-Reporting

### Exponential Backoff
- ✅ Retry-Logik
- ✅ Timing-Verhalten
- ✅ Jitter-Variation
- ✅ Exception-Behandlung
- ✅ Logging

### CircuitBreakerSensor
- ✅ Home Assistant Integration
- ✅ Sensor-Properties
- ✅ State Management
- ✅ Attribute Updates

## Ausführung

```bash
# Alle Robustheit-Tests ausführen
python -m pytest tests/test_circuit_breaker.py tests/test_offline_manager.py tests/test_utils_robustness.py tests/test_circuit_breaker_sensor.py -v

# Einzelne Test-Dateien
python -m pytest tests/test_circuit_breaker.py -v
python -m pytest tests/test_offline_manager.py -v
python -m pytest tests/test_utils_robustness.py -v
python -m pytest tests/test_circuit_breaker_sensor.py -v
```

## Hinweise

- Alle Tests verwenden das `.venv` virtuelle Environment
- Tests sind kompatibel mit Home Assistant und pymodbus >= 3.0
- Mocking wird verwendet für externe Abhängigkeiten
- Asyncio-Tests verwenden pytest-asyncio
- Coverage-Analyse ist aufgrund von HA-Import-Konflikten eingeschränkt, aber Tests funktionieren vollständig
