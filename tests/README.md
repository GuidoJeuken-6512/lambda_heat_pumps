# Lambda Heat Pumps Integration Tests

Diese Test-Suite stellt sicher, dass die Lambda Heat Pumps Integration korrekt funktioniert und zukünftige Änderungen keine Regressionen verursachen.

## Test-Struktur

### `test_utils.py`
Tests für Utility-Funktionen:
- **`generate_sensor_names()`**: Umfassende Tests für `unique_id`-Generierung
- **Eindeutigkeit**: Sicherstellung, dass alle `unique_id`s eindeutig sind
- **Config-Name-Integration**: Prüfung der korrekten Integration des Config-Namens
- **Legacy vs. Standard-Modus**: Tests für beide Namenskonventionen
- **General vs. Template-Sensoren**: Unterschiedliche Logik für verschiedene Sensor-Typen
- **Edge Cases**: Leere/None-Werte, Groß-/Kleinschreibung, Sonderzeichen

### `test_migration.py`
Tests für Migration-Logik:
- **Version-Check**: Migration läuft nur bei alten Versionen
- **Duplikat-Entfernung**: Entfernung von Entities mit "_2", "_3" Suffixen
- **General-Sensor-Migration**: Aktualisierung von `unique_id`s ohne Config-Name
- **Climate-Entity-Migration**: Migration und Entfernung alter Climate-Entities
- **Cycling-Sensor-Migration**: Konsistenz-Checks für Cycling-Sensoren
- **Error-Handling**: Robuste Behandlung von Fehlern
- **Edge Cases**: Leere Registry, keine Änderungen nötig

### `test_sensor.py`
Tests für Sensor-Entitäten:
- **Initialisierung**: Korrekte Erstellung von Sensor-Objekten
- **Properties**: `name`, `unique_id`, `entity_id` Properties
- **Template-Sensoren**: Spezielle Tests für Template-basierte Sensoren

### `test_energy_consumption.py`
Tests für Energy Consumption Funktionalität:
- **`calculate_energy_delta()`**: Energie-Delta-Berechnung mit Überlauf-Schutz
- **`generate_energy_sensor_names()`**: Name-Generierung für Energy-Sensoren
- **`increment_energy_consumption_counter()`**: Counter-Inkrementierung
- **`get_energy_consumption_sensor_template()`**: Template-Abruf
- **`validate_energy_consumption_config()`**: Config-Validierung
- **Konstanten-Tests**: Überprüfung aller Energy Consumption Konstanten
- **Integration-Tests**: Vollständige Workflow-Tests

### `test_energy_consumption_migration.py`
Tests für Energy Consumption Migration:
- **`migrate_to_energy_consumption()`**: Migration zu Version 4
- **Config-Erweiterung**: Hinzufügung von Energy Consumption Sektionen
- **Offset-Konfiguration**: Standard-Offset-Werte
- **Error-Handling**: Robuste Fehlerbehandlung
- **Bestehende Config**: Erhaltung bestehender Konfiguration

### `test_energy_consumption_sensors.py`
Tests für Energy Consumption Sensoren:
- **`LambdaEnergyConsumptionSensor`**: Sensor-Entity-Klasse
- **Initialisierung**: Korrekte Sensor-Erstellung
- **Properties**: Alle Sensor-Properties und -Attribute
- **State-Management**: Energie-Wert-Setzung und -Abfrage
- **Daily-Berechnung**: Tages-Wert-Berechnung (Total - Yesterday)
- **Dispatcher-Integration**: Home Assistant Dispatcher-Integration
- **Alle Modi/Perioden**: Tests für alle Betriebsarten und Zeiträume

### `conftest.py`
Gemeinsame Test-Fixtures:
- **`mock_hass`**: Mock Home Assistant Instance
- **`mock_entry`**: Mock ConfigEntry mit Test-Daten
- **`mock_coordinator`**: Mock LambdaCoordinator
- **`mock_entity_registry`**: Mock Entity Registry
- **`sample_sensor_data`**: Beispiel-Sensor-Daten
- **`sample_climate_data`**: Beispiel-Climate-Daten

## Test-Ausführung

### Alle Tests ausführen:
```bash
pytest tests/
```

### Spezifische Test-Datei:
```bash
pytest tests/test_utils.py
pytest tests/test_migration.py
pytest tests/test_sensor.py
```

### Mit Coverage:
```bash
pytest tests/ --cov=custom_components.lambda_heat_pumps --cov-report=html
```

### Mit detaillierter Ausgabe:
```bash
pytest tests/ -v
```

## Test-Szenarien

### `generate_sensor_names()` Tests

#### 1. Eindeutigkeit
```python
def test_generate_sensor_names_unique_id_uniqueness():
    """Test that generate_sensor_names produces unique unique_ids."""
    # Testet, dass alle generierten unique_ids eindeutig sind
    # Verhindert Duplikate wie "_2" Suffixe
```

#### 2. Config-Name-Integration
```python
def test_generate_sensor_names_config_name_integration():
    """Test that unique_ids contain config name in legacy mode."""
    # Legacy Mode: name_prefix muss in unique_id enthalten sein
    # Standard Mode: name_prefix darf nicht enthalten sein
```

#### 3. Legacy vs. Standard
```python
def test_generate_sensor_names_legacy_vs_standard():
    """Test differences between legacy and standard naming modes."""
    # Legacy: eu08l_hp1_flow_temp
    # Standard: hp1_flow_temp
```

#### 4. General vs. Template
```python
def test_generate_sensor_names_general_vs_template():
    """Test differences between general and template sensors."""
    # General: eu08l_ambient_temp (device_prefix == sensor_id)
    # Template: eu08l_hp1_flow_temp (device_prefix != sensor_id)
```

### Migration Tests

#### 1. Version-Check
```python
def test_migrate_entry_version_check():
    """Test that migration only runs for old versions."""
    # Version 1: Migration läuft
    # Version 3: Keine Migration
```

#### 2. Duplikat-Entfernung
```python
def test_migrate_entity_registry_duplicate_removal():
    """Test removal of duplicate entities with numeric suffixes."""
    # Entfernt sensor.eu08l_ambient_temp_2
    # Behält sensor.eu08l_ambient_temp
```

#### 3. Climate-Entity-Entfernung
```python
def test_migrate_entity_registry_old_climate_entity_removal():
    """Test removal of old climate entities with incompatible format."""
    # Entfernt climate.hot_water_1 (altes Format)
    # Behält climate.eu08l_boil1_hot_water (neues Format)
```

## Wichtige Test-Prinzipien

### 1. Eindeutigkeit
- **Alle `unique_id`s müssen eindeutig sein**
- **Keine Duplikate mit "_2", "_3" Suffixen**
- **Config-Name korrekt integriert**

### 2. Rückwärtskompatibilität
- **Legacy-Modus funktioniert weiterhin**
- **Migration aktualisiert bestehende Entities**
- **Keine Datenverluste**

### 3. Robustheit
- **Error-Handling für alle Szenarien**
- **Edge Cases abgedeckt**
- **Leere/ungültige Eingaben behandelt**

### 4. Vollständigkeit
- **Alle Funktionen getestet**
- **Alle Pfade abgedeckt**
- **Alle Entity-Typen berücksichtigt**

## CI/CD Integration

### GitHub Actions (empfohlen):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=custom_components.lambda_heat_pumps
```

### Pre-commit Hooks:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Test-Wartung

### Neue Tests hinzufügen:
1. **Test-Funktion erstellen** mit beschreibendem Namen
2. **Docstring hinzufügen** mit Erklärung
3. **Assertions schreiben** für erwartetes Verhalten
4. **Edge Cases abdecken** für Robustheit

### Tests aktualisieren:
1. **Bestehende Tests prüfen** bei Code-Änderungen
2. **Neue Szenarien abdecken** wenn nötig
3. **Deprecated Tests entfernen** wenn Funktionen entfernt werden

### Test-Daten:
- **Realistische Test-Daten** verwenden
- **Verschiedene Config-Szenarien** abdecken
- **Edge Cases** in Test-Daten berücksichtigen

## Troubleshooting

### Häufige Probleme:

#### 1. Import-Fehler
```bash
# Lösung: PYTHONPATH setzen
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

#### 2. Async-Test-Fehler
```python
# Lösung: @pytest.mark.asyncio verwenden
@pytest.mark.asyncio
async def test_async_function():
    # Test-Code
```

#### 3. Mock-Probleme
```python
# Lösung: Korrekte Mock-Pfade verwenden
with patch('custom_components.lambda_heat_pumps.utils.function_name'):
    # Test-Code
```

#### 4. Coverage-Probleme
```bash
# Lösung: Vollständige Pfade angeben
pytest tests/ --cov=custom_components.lambda_heat_pumps --cov-report=html
```

## Best Practices

### 1. Test-Namen
- **Beschreibend und eindeutig**
- **Erklärt was getestet wird**
- **Erklärt erwartetes Verhalten**

### 2. Test-Struktur
- **Arrange**: Test-Daten vorbereiten
- **Act**: Funktion ausführen
- **Assert**: Ergebnisse prüfen

### 3. Mocking
- **Minimal mocken** - nur was nötig ist
- **Realistische Mock-Daten** verwenden
- **Mock-Verhalten dokumentieren**

### 4. Assertions
- **Spezifische Assertions** verwenden
- **Mehrere Aspekte prüfen** wenn nötig
- **Aussagekräftige Fehlermeldungen**

### 5. Test-Isolation
- **Tests sind unabhängig** voneinander
- **Keine Seiteneffekte** zwischen Tests
- **Cleanup nach Tests** wenn nötig 