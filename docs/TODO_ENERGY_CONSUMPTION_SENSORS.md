# TODO: Energy Consumption Sensors nach Betriebsart

## Übersicht
Implementierung von Stromverbrauchsrechnern nach Betriebsart (heating, hot water, cooling, defrost) analog zu den Cycling-Sensoren.

## Konzept
- **Basis-Sensor:** `sensor.eu08l_hp1_compressor_power_consumption_accumulated` (kWh)
- **Flankenerkennung:** Wiederverwendung der bestehenden Logik für Betriebsart-Änderungen
- **Tracking:** Kumulativer Verbrauch pro Betriebsart
- **Sensoren:** Nur `total` und `daily` (vereinfacht)
- **Sensor:** cop_calculated pro HP mit Quellsensorangabe in der yaml und Offeset

## Phase 1: Migration System erweitern

### 1. Neue Migration Version hinzufügen
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** `ENERGY_CONSUMPTION = 4` hinzufügen
- **Zweck:** Neue Migration für Energy Consumption Sensoren

### 2. Migration-Funktion implementieren
- **Datei:** `custom_components/lambda_heat_pumps/migration.py`
- **Funktion:** `migrate_to_energy_consumption()`
- **Aktion:** 
  - `energy_consumption_sensors` Sektion zur lambda_wp_config.yaml hinzufügen
  - `energy_consumption_offsets` Sektion zur lambda_wp_config.yaml hinzufügen
- **Zweck:** Automatische Konfiguration bei Migration

### 3. MIGRATION_FUNCTIONS erweitern
- **Datei:** `custom_components/lambda_heat_pumps/migration.py`
- **Aktion:** `MigrationVersion.ENERGY_CONSUMPTION: migrate_to_energy_consumption` hinzufügen
- **Zweck:** Migration in das System integrieren

### 4. MIGRATION_NAMES erweitern
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** `MigrationVersion.ENERGY_CONSUMPTION: "energy_consumption_migration"` hinzufügen
- **Zweck:** Backup-Namen für Migration

### 5. Config Flow Version erhöhen
- **Datei:** `custom_components/lambda_heat_pumps/config_flow.py`
- **Aktion:** `VERSION = 4` (erhöhen von 3 auf 4)
- **Zweck:** Neue Migration auslösen

## Phase 2: lambda_wp_config.yaml erweitern

### 6. Energy Consumption Sensor Konfiguration
- **Datei:** `lambda_wp_config.yaml`
- **Neue Sektion:** `energy_consumption_sensors`
- **Struktur:**
  ```yaml
  energy_consumption_sensors:
    hp1:
      sensor_entity_id: "sensor.eu08l_hp1_compressor_power_consumption_accumulated"
    hp2:
      sensor_entity_id: "sensor.eu08l_hp2_compressor_power_consumption_accumulated"
  ```
- **Zweck:** Konfigurierbare Input-Sensoren pro HP, wird auch für cop_calculated verwendet, wenn konfiguriert.

### 7. Energy Consumption Offsets, lese Offset Konzept cycling sensoren!
- **Datei:** `lambda_wp_config.yaml`
- **Neue Sektion:** `energy_consumption_offsets`
- **Struktur:**
  ```yaml
  energy_consumption_offsets:
    hp1:
      heating_energy_total: 0      # kWh offset for HP1 heating total
      hot_water_energy_total: 0    # kWh offset for HP1 hot water total
      cooling_energy_total: 0      # kWh offset for HP1 cooling total
      defrost_energy_total: 0      # kWh offset for HP1 defrost total
    hp2:
      heating_energy_total: 150.5  # Example: HP2 already consumed 150.5 kWh heating
      hot_water_energy_total: 45.2 # Example: HP2 already consumed 45.2 kWh hot water
      cooling_energy_total: 12.8   # Example: HP2 already consumed 12.8 kWh cooling
      defrost_energy_total: 3.1    # Example: HP2 already consumed 3.1 kWh defrost
  ```
- **Zweck:** Offsets für bestehende Verbrauchswerte (z.B. bei Wärmepumpen-Austausch)

## Phase 3: Sensor-Implementierung

### 8. Neue Sensor-Klasse erstellen
- **Datei:** `custom_components/lambda_heat_pumps/sensor.py`
- **Klasse:** `LambdaEnergyConsumptionSensor`
- **Basis:** Erbt von `LambdaCyclingSensor`
- **Eigenschaften:**
  - `native_unit_of_measurement: "kWh"`
  - `device_class: SensorDeviceClass.ENERGY`
  - `state_class: SensorStateClass.TOTAL_INCREASING`

### 9. Sensor-Erstellung implementieren
- **Datei:** `custom_components/lambda_heat_pumps/sensor.py`
- **Funktion:** In `async_setup_entry()` erweitern
- **Logik:**
  ```python
  # Energy consumption sensors (nur total und daily)
  for hp_idx in range(self.coordinator.num_heat_pumps):
      for mode in ["heating", "hot_water", "cooling", "defrost"]:
          for period in ["total", "daily"]:
              sensor = LambdaEnergyConsumptionSensor(
                  self.coordinator, hp_idx, mode, period
              )
              sensors.append(sensor)
  ```
- **Zweck:** 8 Sensoren pro HP (4 Betriebsarten × 2 Zeiträume)

### 10. Coordinator erweitern
- **Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
- **Neue Variablen:**
  - `self._last_energy_reading = {}`  # Letzter kWh-Wert pro HP
  - `self._energy_consumption = {}`   # Kumulativer Verbrauch pro Betriebsart
  - `self._energy_offsets = {}`       # Offsets für Persistierung
- **Zweck:** Energy-Tracking implementieren

### 11. Flankenerkennung implementieren
- **Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
- **Funktion:** `_track_energy_consumption()`
- **Logik:**
  - Betriebsart-Änderung erkennen
  - Energieverbrauch für vorherige Betriebsart berechnen
  - Zu entsprechender Betriebsart hinzufügen
- **Zweck:** Analog zu Cycling-Sensoren, aber für Energie

### 12. Config-Loading erweitern
- **Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
- **Funktion:** `_load_offsets_and_persisted()` erweitern
- **Aktion:**
  - `energy_consumption_sensors` laden
  - `energy_consumption_offsets` laden
- **Zweck:** Konfiguration aus lambda_wp_config.yaml laden

## Phase 4: Persistierung

### 13. Persistierung erweitern
- **Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
- **Funktion:** `_persist_counters()` erweitern
- **Neue Daten:**
  ```json
  {
    "heating_cycles": {...},
    "heating_energy": {
      "hp1_heating_energy_total": 125.5,
      "hp1_hot_water_energy_total": 45.2,
      "hp1_cooling_energy_total": 12.8,
      "hp1_defrost_energy_total": 3.1
    },
    "energy_offsets": {
      "hp1_heating_energy_total": 0,
      "hp1_hot_water_energy_total": 0,
      "hp1_cooling_energy_total": 0,
      "hp1_defrost_energy_total": 0
    }
  }
  ```
- **Zweck:** Energie-Werte über Neustarts hinweg speichern

### 14. Offset-Loading implementieren, lese OffsetKonzept der cyclimg Sensoren
- **Datei:** `custom_components/lambda_heat_pumps/coordinator.py`
- **Funktion:** `_load_offsets_and_persisted()` erweitern
- **Aktion:** Energy-Offsets aus persistierter Datei laden
- **Zweck:** Offsets bei Neustart wiederherstellen

## Phase 5: Tests

### 15. Unit Tests schreiben
- **Datei:** `tests/test_energy_consumption.py`
- **Tests:**
  - `test_energy_consumption_sensor_creation()`
  - `test_energy_consumption_tracking()`
  - `test_energy_consumption_persistence()`
  - `test_energy_consumption_offsets()`
- **Zweck:** Funktionalität testen

### 16. Migration Tests
- **Datei:** `tests/test_migration.py`
- **Tests:**
  - `test_energy_consumption_migration()`
  - `test_config_flow_version_4()`
- **Zweck:** Migration testen

### 17. Integration Tests
- **Tests:**
  - Energy Consumption Sensoren werden erstellt
  - Flankenerkennung funktioniert
  - Persistierung funktioniert
  - Offsets werden angewendet
- **Zweck:** End-to-End Funktionalität testen

## Phase 6: Dokumentation

### 18. Sensor-Dokumentation
- **Datei:** `docs/ENERGY_CONSUMPTION_SENSORS.md`
- **Inhalt:**
  - Übersicht der neuen Sensoren
  - Konfiguration in lambda_wp_config.yaml
  - Beispiele und Use Cases
- **Zweck:** Benutzer-Dokumentation

### 19. Migration-Dokumentation
- **Datei:** `docs/MIGRATION_GUIDE.md`
- **Inhalt:**
  - Migration von Version 3 zu 4
  - Neue Konfigurationsoptionen
  - Troubleshooting
- **Zweck:** Migration-Dokumentation

## Erwartete Sensoren

### Pro Heat Pump (hp1, hp2, etc.):
```
sensor.eu08l_hp1_heating_energy_consumption_total      # Gesamtverbrauch Heizen
sensor.eu08l_hp1_heating_energy_consumption_daily      # Tagesverbrauch Heizen

sensor.eu08l_hp1_hot_water_energy_consumption_total    # Gesamtverbrauch Warmwasser
sensor.eu08l_hp1_hot_water_energy_consumption_daily    # Tagesverbrauch Warmwasser

sensor.eu08l_hp1_cooling_energy_consumption_total      # Gesamtverbrauch Kühlen
sensor.eu08l_hp1_cooling_energy_consumption_daily      # Tagesverbrauch Kühlen

sensor.eu08l_hp1_defrost_energy_consumption_total      # Gesamtverbrauch Abtauen
sensor.eu08l_hp1_defrost_energy_consumption_daily      # Tagesverbrauch Abtauen
```

### Beispiel: 2 HPs = 16 Sensoren
- **1 HP:** 8 Sensoren
- **2 HPs:** 16 Sensoren  
- **3 HPs:** 24 Sensoren

## Abhängigkeiten

### Voraussetzungen:
1. ✅ Migration System Cleanup abgeschlossen
2. ✅ Neue Migration (Version 3) funktioniert
3. ✅ lambda_wp_config.yaml Vorlage angepasst

### Reihenfolge:
1. **Phase 1:** Migration System erweitern
2. **Phase 2:** lambda_wp_config.yaml erweitern
3. **Phase 3:** Sensor-Implementierung
4. **Phase 4:** Persistierung
5. **Phase 5:** Tests
6. **Phase 6:** Dokumentation

## Status
- [ ] Phase 1: Migration System erweitern
- [ ] Phase 2: lambda_wp_config.yaml erweitern
- [ ] Phase 3: Sensor-Implementierung
- [ ] Phase 4: Persistierung
- [ ] Phase 5: Tests
- [ ] Phase 6: Dokumentation

**Letzte Aktualisierung:** 2025-08-29
**Verantwortlich:** Development Team
**Abhängig von:** TODO_MIGRATION_CLEANUP.md
