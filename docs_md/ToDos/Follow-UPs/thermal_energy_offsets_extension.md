# Thermal Energy Offsets - Erweiterung und Fehlerbehebung

**Status**: 🔴 To-Do  
**Priorität**: Medium  
**Erstellt**: 2025-01-10  
**Betrifft**: `energy_consumption_offsets`, `_apply_energy_offset()`, `LambdaEnergyConsumptionSensor`

## Problemstellung

### Aktueller Zustand

Thermische Energie-Offsets (`heating_thermal_energy_total`, `hot_water_thermal_energy_total`, etc.) werden **nur teilweise unterstützt**:

1. ✅ **Funktioniert**: Offsets werden in `increment_energy_consumption_counter()` (utils.py) während des Betriebs bei neuen Energie-Inkrementen angewendet
2. ❌ **Funktioniert NICHT**: `_apply_energy_offset()` Methode in `LambdaEnergyConsumptionSensor` verwendet den falschen `sensor_id`
3. ❌ **Funktioniert NICHT**: `_apply_energy_offset()` wird nicht in `async_added_to_hass()` aufgerufen (im Gegensatz zu Cycling-Sensoren)
4. ❌ **Funktioniert NICHT**: Offsets werden beim Start/Neustart nicht angewendet, sondern nur bei neuen Energie-Inkrementen während des Betriebs

### Code-Stellen

**Problem 1: Falscher sensor_id in `_apply_energy_offset()`**

```python
# Aktuell (Zeile 1402 in sensor.py):
sensor_id = f"{self._mode}_energy_total"  # ❌ Falsch für Thermal-Sensoren!

# Sollte sein:
if "_thermal_energy_" in self._sensor_id:
    sensor_id = f"{self._mode}_thermal_energy_total"
else:
    sensor_id = f"{self._mode}_energy_total"
```

**Problem 2: `_apply_energy_offset()` wird nicht aufgerufen**

```python
# Aktuell in async_added_to_hass() (Zeile 1241-1277):
# KEIN Aufruf von _apply_energy_offset() für Total-Sensoren

# Sollte sein (wie bei Cycling-Sensoren):
if self._period == "total":
    await self._apply_energy_offset()
```

**Problem 3: Config-Datei Beispiel fehlt**

Die `lambda_wp_config.yaml` Template-Datei zeigt nur elektrische Energie-Offsets, nicht thermische:

```yaml
# Aktuell im Template:
energy_consumption_offsets:
  hp1:
    heating_energy_total: 0.0       # Nur elektrisch
    hot_water_energy_total: 0.0     # Nur elektrisch
    # Thermische Energie-Offsets fehlen!
```

## Geplante Lösung

### 1. Code-Erweiterung

#### A. `_apply_energy_offset()` erweitern

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`  
**Zeile**: ~1401-1402

**Änderung**:
```python
async def _apply_energy_offset(self):
    """Apply energy consumption offset for total sensors (only once, like cycling sensors)."""
    try:
        # ... existing code ...
        
        # Hole den aktuellen Offset für diesen Sensor
        # Prüfe ob es ein Thermal-Energy-Sensor ist (basierend auf sensor_id)
        if "_thermal_energy_" in self._sensor_id:
            sensor_id = f"{self._mode}_thermal_energy_total"
        else:
            sensor_id = f"{self._mode}_energy_total"
        current_offset = energy_offsets[device_key].get(sensor_id, 0.0)
        
        # ... rest of existing code ...
```

#### B. `async_added_to_hass()` erweitern

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`  
**Zeile**: ~1277 (nach Signal-Handler-Registrierungen)

**Änderung**:
```python
async def async_added_to_hass(self):
    """Initialize the sensor when added to Home Assistant."""
    await super().async_added_to_hass()

    # ... existing code (restore_state, initialize_daily_yesterday_value, signal handlers) ...

    # Für Total-Sensoren: Offset anwenden (wie bei Cycling-Sensoren)
    if self._period == "total":
        await self._apply_energy_offset()
```

### 2. Config-Template Migration

#### A. Template erweitern

**Datei**: `custom_components/lambda_heat_pumps/utils.py`  
**Funktion**: `LAMBDA_WP_CONFIG_TEMPLATE` (oder entsprechende Template-Datei)

**Änderung**:
```yaml
# Energy consumption offsets for total sensors (WICHTIG: Alle Werte müssen in kWh angegeben werden!)
# Diese Offsets werden nur auf die TOTAL-Sensoren angewendet, nicht auf Daily/Monthly/Yearly
# Nützlich beim Austausch von Wärmepumpen oder Zurücksetzen der Zähler
# Beispiel mit Nachkommastellen:
#energy_consumption_offsets:
#  hp1:
#    # Elektrische Energie-Offsets (Stromverbrauch)
#    heating_energy_total: 0.0       # kWh offset for HP1 heating total (electrical)
#    hot_water_energy_total: 0.0     # kWh offset for HP1 hot water total (electrical)
#    cooling_energy_total: 0.0       # kWh offset for HP1 cooling total (electrical)
#    defrost_energy_total: 0.0       # kWh offset for HP1 defrost total (electrical)
#    # Thermische Energie-Offsets (Wärmeabgabe)
#    heating_thermal_energy_total: 0.0       # kWh offset for HP1 heating total (thermal)
#    hot_water_thermal_energy_total: 0.0     # kWh offset for HP1 hot water total (thermal)
#    cooling_thermal_energy_total: 0.0       # kWh offset for HP1 cooling total (thermal)
#    defrost_thermal_energy_total: 0.0       # kWh offset for HP1 defrost total (thermal)
#  hp2:
#    # Elektrische Energie-Offsets
#    heating_energy_total: 150.5     # Beispiel: HP2 bereits 150,5 kWh Heizen verbraucht (electrical)
#    hot_water_energy_total: 45.25   # Beispiel: HP2 bereits 45,25 kWh Warmwasser verbraucht (electrical)
#    cooling_energy_total: 12.8      # Beispiel: HP2 bereits 12,8 kWh Kühlen verbraucht (electrical)
#    defrost_energy_total: 3.1       # Beispiel: HP2 bereits 3,1 kWh Abtauen verbraucht (electrical)
#    # Thermische Energie-Offsets
#    heating_thermal_energy_total: 500.0     # Beispiel: HP2 bereits 500 kWh Heizen erzeugt (thermal)
#    hot_water_thermal_energy_total: 200.0   # Beispiel: HP2 bereits 200 kWh Warmwasser erzeugt (thermal)
#    cooling_thermal_energy_total: 50.0      # Beispiel: HP2 bereits 50 kWh Kühlen erzeugt (thermal)
#    defrost_thermal_energy_total: 10.0      # Beispiel: HP2 bereits 10 kWh Abtauen erzeugt (thermal)
```

#### B. Migration Step implementieren

**Datei**: `custom_components/lambda_heat_pumps/utils.py`  
**Funktion**: `migrate_lambda_config_sections()` oder neue Migration-Funktion

**Migration-Logik**:
1. Prüfe ob `energy_consumption_offsets` Abschnitt vorhanden ist
2. Prüfe ob Kommentare/Beispiele für thermische Energie-Offsets vorhanden sind
3. Wenn nicht: Füge erweiterte Kommentare und Beispiele hinzu
4. **Wichtig**: Bestehende Werte bleiben unverändert! Nur Kommentare werden ergänzt

### 3. Migration Step Planung

#### Migration Version

**Datei**: `custom_components/lambda_heat_pumps/const_migration.py`

**Neue Migration-Version hinzufügen**:
```python
class MigrationVersion(IntEnum):
    # ... existing versions ...
    THERMAL_ENERGY_OFFSETS_SUPPORT = 9  # Neue Version
```

#### Migrations-Funktion

**Datei**: `custom_components/lambda_heat_pumps/migration.py`

**Neue Funktion**:
```python
async def migrate_to_thermal_energy_offsets(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """
    Migration: Erweitert energy_consumption_offsets Sektion um thermische Energie-Offsets.
    
    Aktivität:
    - Erweitert lambda_wp_config.yaml Template um thermische Energie-Offsets Kommentare/Beispiele
    - Bestehende Werte bleiben unverändert
    - Nur Kommentare werden ergänzt
    """
    try:
        config_dir = hass.config.config_dir
        lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
        
        if not os.path.exists(lambda_config_path):
            _LOGGER.debug("No lambda_wp_config.yaml found, migration not needed")
            return True
        
        # Lade aktuelle Config
        content = await hass.async_add_executor_job(
            lambda: open(lambda_config_path, "r", encoding="utf-8").read()
        )
        
        # Prüfe ob thermische Energie-Offsets bereits dokumentiert sind
        if "heating_thermal_energy_total" in content or "_thermal_energy_total" in content:
            _LOGGER.debug("Thermal energy offsets already documented, migration not needed")
            return True
        
        # Erstelle Backup
        backup_path = lambda_config_path + f".backup_v{MigrationVersion.THERMAL_ENERGY_OFFSETS_SUPPORT.value}"
        await hass.async_add_executor_job(
            lambda: open(backup_path, "w", encoding="utf-8").write(content)
        )
        _LOGGER.info("Created backup at %s", backup_path)
        
        # Erweitere energy_consumption_offsets Abschnitt
        # Finde die energy_consumption_offsets Sektion im Template
        # Füge Kommentare und Beispiele für thermische Energie-Offsets hinzu
        # Wichtig: Nur Kommentare hinzufügen, bestehende Werte nicht ändern!
        
        # Suche nach dem energy_consumption_offsets Abschnitt
        # Füge nach jedem defrost_energy_total Eintrag die entsprechenden thermischen Offsets hinzu
        
        _LOGGER.info("Successfully migrated lambda_wp_config.yaml - added thermal energy offsets documentation")
        return True
        
    except Exception as e:
        _LOGGER.error("Error during thermal energy offsets migration: %s", e)
        return False
```

**Migration registrieren**:
```python
MIGRATION_FUNCTIONS = {
    # ... existing migrations ...
    MigrationVersion.THERMAL_ENERGY_OFFSETS_SUPPORT: migrate_to_thermal_energy_offsets,
}
```

#### Alternative: Template-basierte Migration verwenden

Da bereits eine Template-basierte Migration existiert (`migrate_lambda_config_sections()`), kann die Migration auch dort integriert werden:

**Datei**: `custom_components/lambda_heat_pumps/utils.py`  
**Funktion**: `_extract_config_sections()`

Die Funktion `migrate_lambda_config_sections()` fügt automatisch fehlende Abschnitte aus dem Template hinzu. Wenn das Template erweitert wird, werden die neuen Kommentare automatisch bei der nächsten Ausführung hinzugefügt.

**Vorgehen**:
1. Erweitere `LAMBDA_WP_CONFIG_TEMPLATE` um thermische Energie-Offsets Kommentare
2. `migrate_lambda_config_sections()` wird diese automatisch bei der nächsten Ausführung hinzufügen
3. Keine separate Migration-Funktion nötig, wenn das Template-System verwendet wird

## Test-Plan

### Unit-Tests

1. **Test `_apply_energy_offset()` für Thermal-Sensoren**:
   ```python
   def test_apply_thermal_energy_offset():
       # Teste dass sensor_id korrekt erkannt wird
       # Teste dass Offset aus Config geladen wird
       # Teste dass Offset angewendet wird
   ```

2. **Test `async_added_to_hass()` ruft `_apply_energy_offset()` auf**:
   ```python
   def test_total_sensor_applies_offset_on_start():
       # Teste dass für Total-Sensoren _apply_energy_offset() aufgerufen wird
       # Teste dass für Daily/Monthly-Sensoren NICHT aufgerufen wird
   ```

### Integration-Tests

1. **Test Migration**:
   - Bestehende `lambda_wp_config.yaml` ohne thermische Offsets
   - Migration ausführen
   - Prüfe dass Kommentare hinzugefügt wurden
   - Prüfe dass bestehende Werte unverändert sind

2. **Test Offset-Anwendung beim Start**:
   - Config mit thermischen Energie-Offsets
   - Integration neu starten
   - Prüfe dass Offsets angewendet wurden (Log-Meldungen, Sensor-Werte)

## Aufgabenliste

### Code-Änderungen

- [ ] **sensor.py**: `_apply_energy_offset()` erweitern um Thermal-Sensoren zu erkennen (Zeile ~1401-1402)
- [ ] **sensor.py**: `async_added_to_hass()` erweitern um `_apply_energy_offset()` für Total-Sensoren aufzurufen (Zeile ~1277)
- [ ] **utils.py**: `LAMBDA_WP_CONFIG_TEMPLATE` erweitern um thermische Energie-Offsets Kommentare/Beispiele
- [ ] **migration.py**: Option A - Neue Migration-Funktion `migrate_to_thermal_energy_offsets()` implementieren (falls gewünscht)
- [ ] **migration.py**: Option B - Template-System verwenden (einfacher, automatisch)
- [ ] **const_migration.py**: Neue Migration-Version `THERMAL_ENERGY_OFFSETS_SUPPORT = 9` hinzufügen (falls Option A)
- [ ] **migration.py**: Migration-Funktion in `MIGRATION_FUNCTIONS` registrieren (falls Option A)

### Dokumentation

- [ ] **Anwenderdoku**: `docs/docs/Anwender/Energieverbrauchsberechnung.md` - Thermische Energie-Offsets dokumentieren (mit Hinweis auf aktuelle Einschränkungen)
- [ ] **Entwicklerdoku**: `docs/docs/Entwickler/energieverbrauchssensoren.md` - Code-Änderungen dokumentieren
- [ ] **Config-Referenz**: `docs/docs/Entwickler/modbus-wp-config.md` - Beispiel-Konfiguration erweitern

### Tests

- [ ] Unit-Tests für `_apply_energy_offset()` mit Thermal-Sensoren
- [ ] Unit-Tests für `async_added_to_hass()` Offset-Aufruf
- [ ] Integration-Test für Migration (falls Option A gewählt)
- [ ] Manueller Test: Config mit thermischen Offsets, Neustart, Prüfe Anwendung

## Erwartetes Ergebnis

Nach Implementierung:

1. ✅ Thermische Energie-Offsets werden beim Start der Integration angewendet (nicht nur bei neuen Inkrementen)
2. ✅ `_apply_energy_offset()` erkennt Thermal-Sensoren korrekt
3. ✅ `lambda_wp_config.yaml` Template enthält vollständige Beispiele für thermische Energie-Offsets
4. ✅ Migration erweitert bestehende Config-Dateien automatisch um thermische Energie-Offsets Kommentare (oder Template-System macht es automatisch)
5. ✅ Bestehende Werte bleiben bei Migration unverändert (keine Breaking Changes)

## Verwandte Issues/Dokumentation

- [Energieverbrauchssensoren - Technische Dokumentation](../docs/docs/Entwickler/energieverbrauchssensoren.md)
- [Anwenderdokumentation - Energieverbrauchsberechnung](../docs/docs/Anwender/Energieverbrauchsberechnung.md)
- [Migration System Dokumentation](../lambda_heat_pumps_migration_system.md)

## Notizen

- **Breaking Changes**: Keine erwartet - bestehende Configs funktionieren weiterhin
- **Backward Compatibility**: Vollständig gegeben - elektrische Energie-Offsets funktionieren wie bisher
- **Performance**: Keine negativen Auswirkungen erwartet - `_apply_energy_offset()` wird nur einmal beim Start aufgerufen
- **Migration-Strategie**: Zwei Optionen möglich - explizite Migration-Funktion oder Template-basierte Migration (empfohlen, da bereits vorhanden)

