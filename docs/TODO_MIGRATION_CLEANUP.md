# TODO: Migration System Cleanup

## Übersicht
Dieses Dokument beschreibt die Schritte zur Bereinigung und Aktivierung des neuen Migration-Systems für die Lambda Heat Pumps Integration.

## Problem
- Es existieren zwei parallele Migration-Systeme (altes in `utils.py` und neues in `migration.py`)
- Das neue Migration-System wird nicht verwendet, obwohl es implementiert ist
- Die alte Migration läuft bei jedem Start über `load_lambda_config()`

## Phase 1: Zwei getrennte Migration-Systeme implementieren

### 1. Alte Migration in load_lambda_config() auskommentieren
- **Datei:** `custom_components/lambda_heat_pumps/utils.py`
- **Funktion:** `load_lambda_config()`
- **Aktion:** `await migrate_lambda_config(hass)` auskommentieren
- **Zweck:** Verhindert, dass die alte Migration bei jedem Start läuft

### 2. Neue Migration-Struktur implementieren
- **Datei:** `custom_components/lambda_heat_pumps/migration.py`
- **Aktion:** Aktuelle Migration-Funktionen durch zwei getrennte Systeme ersetzen
- **Neue Struktur:**
  - `migrate_sensor_and_config()` - Entity/Registry Migration
  - `migrate_lambda_wp_config_yaml()` - YAML Config Migration
- **Zweck:** Klare Trennung der Verantwortlichkeiten

### 3. Entity/Registry Migration implementieren
- **Funktion:** `migrate_sensor_and_config()`
- **Zweck:** Home Assistant Entity Registry und Config Entry Migration
- **Beispiele:**
  - Entity-Namen ändern (Version 2)
  - Neue Sensoren hinzufügen
  - Entity-Struktur optimieren
- **Versionierung:** Config Entry Version

### 4. YAML Config Migration implementieren
- **Funktion:** `migrate_lambda_wp_config_yaml()`
- **Zweck:** lambda_wp_config.yaml Migration
- **Beispiele:**
  - cycling_offsets hinzufügen (Version 3)
  - Robustheits-Features aktivieren
  - Endianness-Konfiguration
- **Versionierung:** YAML Version (unabhängig von Config Entry)

### 5. Versionierung trennen
- **Config Entry Version:** Für Entity-Migration (Home Assistant Registry)
- **YAML Version:** Für YAML-Migration (lambda_wp_config.yaml)
- **Zweck:** Unabhängige Versionierung für bessere Flexibilität

## Phase 2: Migration-Systeme aktivieren und testen

### 6. Entity/Registry Migration aktivieren
- **Funktion:** `migrate_sensor_and_config()` in `__init__.py` integrieren
- **Aufruf:** Bei Config Entry Version-Änderungen
- **Zweck:** Entity Registry Migration automatisch ausführen

### 7. YAML Config Migration aktivieren
- **Funktion:** `migrate_lambda_wp_config_yaml()` in `utils.py` integrieren
- **Aufruf:** Bei YAML Version-Änderungen
- **Zweck:** YAML Config Migration automatisch ausführen

### 8. Getrennte Tests implementieren
- **Entity-Migration Tests:** Unit Tests für `migrate_sensor_and_config()`
- **YAML-Migration Tests:** Unit Tests für `migrate_lambda_wp_config_yaml()`
- **Integration Tests:** Beide Systeme zusammen testen
- **Ausführung:** `pytest` laufen lassen
- **Zweck:** Sicherstellen, dass beide Systeme funktionieren

### 9. Vollständige Kompatibilität testen
- **Modbus YAML:** Test der modbus_yaml Konfiguration
- **Integration v1.0.9:** Test mit alter Version
- **Integration v1.22:** Test mit neuer Version
- **Zweck:** Vollständige Kompatibilität sicherstellen

### 10. Entwicklungssystem-Tests
- **Aktion:** Tests in verschiedenen Entwicklungsumgebungen ausführen
- **Zweck:** Sicherstellen, dass alles in verschiedenen Konfigurationen funktioniert

## Phase 3: Cleanup und Optimierung

### 11. Alte Migration-Funktionen entfernen
- **Datei:** `custom_components/lambda_heat_pumps/utils.py`
- **Funktion:** `migrate_lambda_config()` komplett entfernen
- **Aufrufe:** Alle Referenzen zu dieser Funktion entfernen
- **Imports:** Nicht mehr benötigte Imports bereinigen
- **Zweck:** Code-Bereinigung, keine toten Funktionen

### 12. Alte Migration-Struktur entfernen
- **Datei:** `custom_components/lambda_heat_pumps/migration.py`
- **Funktionen zu entfernen:**
  - `migrate_to_legacy_names()` (ersetzt durch `migrate_sensor_and_config()`)
  - `migrate_to_cycling_offsets()` (ersetzt durch `migrate_lambda_wp_config_yaml()`)
  - `migrate_to_entity_optimization()` (nicht mehr benötigt)
  - `migrate_to_config_restructure()` (nicht mehr benötigt)
- **Zweck:** Alte, komplexe Migration-Funktionen entfernen

### 13. Migration-Konstanten bereinigen
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** Alte Migration-Versionen entfernen
- **Behalten:** Nur die neuen, getrennten Versionen
- **Zweck:** Konsistente Migration-Konstanten

## Zusätzliche wichtige Schritte

### 14. lambda_wp_config.yaml Vorlage anpassen
- **Datei:** `lambda_wp_config.yaml`
- **Aktion:** `cycling_offsets` aktivieren (nicht mehr auskommentiert)
- **Zweck:** YAML-Migration erkennt "bereits vorhanden" und macht nichts

### 15. Neue Migration-Konstanten definieren
- **Datei:** `custom_components/lambda_heat_pumps/const_migration.py`
- **Aktion:** Neue Konstanten für zwei getrennte Systeme
- **Neue Struktur:**
  - `ENTITY_MIGRATION_VERSION` - Für Entity/Registry Migration
  - `YAML_MIGRATION_VERSION` - Für YAML Config Migration
- **Zweck:** Klare Trennung der Versionierung

### 16. Energy Consumption Migration implementieren
- **Entity-Migration:** Energy Consumption Sensoren in `migrate_sensor_and_config()`
- **YAML-Migration:** Energy Consumption Config in `migrate_lambda_wp_config_yaml()`
- **Zweck:** Energy Consumption Sensoren nach Betriebsart
- **Config:** `energy_consumption_sensors` und `energy_consumption_offsets` hinzufügen

### 17. Vollständige Migration-Kette testen
- **Test-Szenario:** 
  - Config Entry Version 2 → 3 (Entity-Migration)
  - YAML Version 2 → 3 (YAML-Migration)
- **Zweck:** Vollständige Migration-Kette beider Systeme testen
- **Erwartung:** Saubere Übergänge zwischen allen Versionen

### 18. Zwei-Versionen-Problem lösen
- **Problem:** Config Entry Version (2) vs. YAML Version (3) sind nicht synchronisiert
- **Lösung:** Zwei getrennte Migration-Systeme mit unabhängiger Versionierung
- **Neue Struktur:**
  - Config Entry Version: Für Entity/Registry Migration
  - YAML Version: Für YAML Config Migration
- **Vorteil:** Unabhängige Versionierung, keine Synchronisationsprobleme

### 19. Version-Synchronisation implementieren
- **Problem:** Migration-Logik berücksichtigt nur Config Entry Version
- **Lösung:** Zwei getrennte Migration-Systeme mit eigenen Versionen
- **Implementierung:** 
  - Entity-Migration: Prüft Config Entry Version
  - YAML-Migration: Prüft YAML Version
- **Zweck:** Keine Inkonsistenzen zwischen verschiedenen Versionen

## Migration-Struktur Analyse

### Aktuelle Struktur: Einheitliche Migration
- **Vorteile:**
  - Einfache Versionierung (eine Version pro Migration)
  - Zentrale Steuerung aller Migrationen
  - Einheitliche Backup- und Rollback-Logik
- **Nachteile:**
  - Vermischung von Entity-Migration und YAML-Migration
  - Komplexe Funktionen mit gemischten Verantwortlichkeiten
  - Schwerer zu testen und zu warten

### Alternative: Zwei getrennte Migration-Systeme
**Vorschlag:** Aufteilen in zwei spezialisierte Systeme:

#### 1. `migrate_sensor_and_config()` - Entity/Registry Migration
- **Zweck:** Home Assistant Entity Registry und Config Entry Migration
- **Beispiele:** 
  - Entity-Namen ändern (Version 2)
  - Neue Sensoren hinzufügen
  - Entity-Struktur optimieren
- **Verantwortlichkeit:** Nur Home Assistant Registry-Änderungen

#### 2. `migrate_lambda_wp_config_yaml()` - YAML Config Migration  
- **Zweck:** lambda_wp_config.yaml Migration
- **Beispiele:**
  - cycling_offsets hinzufügen (Version 3)
  - Robustheits-Features aktivieren
  - Endianness-Konfiguration
- **Verantwortlichkeit:** Nur YAML-Config-Änderungen

### Empfehlung: Zwei getrennte Systeme
**Warum zwei Systeme besser wären:**

#### ✅ **Bessere Übersichtlichkeit**
- Klare Trennung der Verantwortlichkeiten
- Einfacher zu verstehen, was jede Migration macht
- Weniger komplexe Funktionen

#### ✅ **Bessere Wartbarkeit**
- Unabhängige Entwicklung und Testing
- Einfacher zu debuggen
- Weniger Abhängigkeiten zwischen Migrationen

#### ✅ **Flexiblere Versionierung**
- Entity-Migration: Config Entry Version
- YAML-Migration: YAML Version
- Unabhängige Versionierung möglich

#### ✅ **Einfachere Tests**
- Getrennte Test-Suites
- Weniger Mocking erforderlich
- Klarere Test-Szenarien

### Implementierungsvorschlag
```python
# Entity/Registry Migration
async def migrate_sensor_and_config(
    hass: HomeAssistant, 
    config_entry: ConfigEntry,
    target_version: int
) -> bool:
    """Migration für Entity Registry und Config Entry"""
    pass

# YAML Config Migration  
async def migrate_lambda_wp_config_yaml(
    hass: HomeAssistant,
    target_version: int
) -> bool:
    """Migration für lambda_wp_config.yaml"""
    pass
```

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
1. ✅ Zwei getrennte Migration-Systeme implementiert
2. ✅ Unabhängige Versionierung (Config Entry Version ≠ YAML Version)
3. ✅ Klare Trennung der Verantwortlichkeiten
4. ✅ Energy Consumption Sensoren implementiert
5. ✅ Vollständige Test-Abdeckung für beide Systeme
6. ✅ Keine toten Code-Funktionen
7. ✅ Bessere Übersichtlichkeit und Wartbarkeit

## Empfehlung: Zwei getrennte Migration-Systeme

**Basierend auf der Analyse empfehle ich die Implementierung von zwei getrennten Migration-Systemen:**

### Warum zwei Systeme besser sind:

#### 🎯 **Ziel: Übersichtlichkeit**
- **Aktuell:** Eine komplexe Migration-Funktion für alles
- **Neu:** Zwei spezialisierte, einfache Funktionen
- **Vorteil:** Klare Verantwortlichkeiten, einfacher zu verstehen

#### 🔧 **Ziel: Wartbarkeit**  
- **Aktuell:** Gemischte Verantwortlichkeiten in einer Funktion
- **Neu:** Getrennte Systeme für Entity- und YAML-Migration
- **Vorteil:** Unabhängige Entwicklung, einfacher zu debuggen

#### 📊 **Ziel: Flexibilität**
- **Aktuell:** Starre Versionierung (eine Version für alles)
- **Neu:** Unabhängige Versionierung für Entity und YAML
- **Vorteil:** Flexiblere Migration-Strategien

### Implementierungsplan für zwei Systeme:

#### Phase 1: Struktur aufteilen
1. **Entity-Migration:** `migrate_sensor_and_config()`
2. **YAML-Migration:** `migrate_lambda_wp_config_yaml()`

#### Phase 2: Versionierung trennen
1. **Config Entry Version:** Für Entity-Migration
2. **YAML Version:** Für YAML-Migration

#### Phase 3: Tests anpassen
1. **Getrennte Test-Suites**
2. **Unabhängige Test-Szenarien**
3. **Weniger komplexe Mocks**

**Fazit: Zwei getrennte Migration-Systeme sind definitiv besser für Übersichtlichkeit und Wartbarkeit!**

## Status
- [ ] Phase 1: Zwei getrennte Migration-Systeme implementieren
- [ ] Phase 2: Migration-Systeme aktivieren und testen
- [ ] Phase 3: Cleanup und Optimierung
- [ ] Zusätzliche Schritte
- [ ] Tests und Validierung

**Letzte Aktualisierung:** 2025-09-03
**Verantwortlich:** Development Team
**Status:** TODO angepasst für zwei getrennte Migration-Systeme
