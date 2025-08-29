# TODO: Migration System Cleanup

## Übersicht
Dieses Dokument beschreibt die Schritte zur Bereinigung und Aktivierung des neuen Migration-Systems für die Lambda Heat Pumps Integration.

## Problem
- Es existieren zwei parallele Migration-Systeme (altes in `utils.py` und neues in `migration.py`)
- Das neue Migration-System wird nicht verwendet, obwohl es implementiert ist
- Die alte Migration läuft bei jedem Start über `load_lambda_config()`

## Phase 1: Alte Migration deaktivieren

### 1. Alte Migration in load_lambda_config() auskommentieren
- **Datei:** `custom_components/lambda_heat_pumps/utils.py`
- **Funktion:** `load_lambda_config()`
- **Aktion:** `await migrate_lambda_config(hass)` auskommentieren
- **Zweck:** Verhindert, dass die alte Migration bei jedem Start läuft

### 2. Migrationen 4-5 aus der neuen Migrationslogik löschen
- **Datei:** `custom_components/lambda_heat_pumps/migration.py`
- **Funktionen zu löschen:**
  - `migrate_to_entity_optimization()` (Version 4)
  - `migrate_to_config_restructure()` (Version 5)
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** `ENTITY_OPTIMIZATION = 4` und `CONFIG_RESTRUCTURE = 5` entfernen
- **Zweck:** Nur echte Migrationen behalten, keine Platzhalter

### 3. Default Version in config_flow.py auf 3 setzen
- **Datei:** `custom_components/lambda_heat_pumps/config_flow.py`
- **Aktion:** `VERSION = 3` (erhöhen von 2 auf 3)
- **Zweck:** Synchronisation mit MigrationVersion.CYCLING_OFFSETS

### 4. Überprüfen, warum die neue Migrationslogik nicht anläuft
- **Problem:** `async_migrate_entry` in `__init__.py` existiert, wird aber nicht aufgerufen
- **Untersuchung:** Warum ruft Home Assistant die Funktion nicht auf?
- **Mögliche Ursachen:**
  - Config Entry Version-Problem
  - Import-Problem
  - Home Assistant erkennt die Funktion nicht

## Phase 2: Neue Migration aktivieren

### 5. Problem aus Punkt 4 beheben und Tests schreiben
- **Aktion:** Das identifizierte Problem beheben
- **Tests:** Unit Tests für Migration-System schreiben
- **Ausführung:** `pytest` laufen lassen
- **Zweck:** Sicherstellen, dass das neue System funktioniert

### 6. Testen testen testen
- **Modbus YAML:** Test der modbus_yaml Konfiguration
- **Integration v1.0.9:** Test mit alter Version
- **Integration v1.22:** Test mit neuer Version
- **Zweck:** Vollständige Kompatibilität sicherstellen

### 7. Saubere Tests in den Entwicklungssystemen
- **Aktion:** Tests in verschiedenen Entwicklungsumgebungen ausführen
- **Zweck:** Sicherstellen, dass alles in verschiedenen Konfigurationen funktioniert

## Phase 3: Cleanup

### 8. Die auskommentierte Funktion mit allen Aufrufen und Imports löschen
- **Datei:** `custom_components/lambda_heat_pumps/utils.py`
- **Funktion:** `migrate_lambda_config()` komplett entfernen
- **Aufrufe:** Alle Referenzen zu dieser Funktion entfernen
- **Imports:** Nicht mehr benötigte Imports bereinigen
- **Zweck:** Code-Bereinigung, keine toten Funktionen

## Zusätzliche wichtige Schritte

### 9. lambda_wp_config.yaml Vorlage anpassen
- **Datei:** `lambda_wp_config.yaml`
- **Aktion:** `cycling_offsets` aktivieren (nicht mehr auskommentiert)
- **Zweck:** Migration 3 erkennt "bereits vorhanden" und macht nichts

### 10. MIGRATION_NAMES in const_migration.py anpassen
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** Migrationen 4-5 aus `MIGRATION_NAMES` entfernen
- **Zweck:** Konsistenz mit gelöschten Migrationen

### 11. Energy Consumption Migration (Version 4) implementieren
- **Neue Funktion:** `migrate_to_energy_consumption()`
- **Zweck:** Energy Consumption Sensoren nach Betriebsart
- **Config:** `energy_consumption_sensors` und `energy_consumption_offsets` hinzufügen

### 12. Migration-System testen
- **Test-Szenario:** Config Entry Version 2 → 3 → 4
- **Zweck:** Vollständige Migration-Kette testen
- **Erwartung:** Saubere Übergänge zwischen allen Versionen

## Kritische Punkte

### Schritt 4 ist der Schlüssel
- **Problem:** Warum wird `async_migrate_entry` nicht aufgerufen?
- **Lösung:** Config Entry Version-Problem beheben
- **Auswirkung:** Ohne diesen Schritt funktioniert das neue System nicht

### Schritt 9 ist wichtig
- **Problem:** lambda_wp_config.yaml Vorlage muss angepasst werden
- **Lösung:** `cycling_offsets` aktivieren statt auskommentiert
- **Auswirkung:** Migration 3 läuft sauber durch

### Schritt 12 ist essentiell
- **Problem:** Das komplette Migration-System muss getestet werden
- **Lösung:** Vollständige Test-Suite
- **Auswirkung:** Sicherstellung der Funktionalität

## Erwartete Ergebnisse

Nach Abschluss aller Schritte:
1. ✅ Nur ein Migration-System (das neue aus `migration.py`)
2. ✅ Saubere Versionierung (Config Entry Version = MigrationVersion)
3. ✅ Energy Consumption Sensoren implementiert
4. ✅ Vollständige Test-Abdeckung
5. ✅ Keine toten Code-Funktionen

## Status
- [ ] Phase 1: Alte Migration deaktivieren
- [ ] Phase 2: Neue Migration aktivieren  
- [ ] Phase 3: Cleanup
- [ ] Zusätzliche Schritte
- [ ] Tests und Validierung

**Letzte Aktualisierung:** 2025-08-29
**Verantwortlich:** Development Team
