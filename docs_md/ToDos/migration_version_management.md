# Migration Version Management - TODO

## Problemstellung

Das aktuelle Migrationssystem hat mehrere Probleme bei der Versionsverwaltung:

1. **Version wird nicht nach Migration aktualisiert**: Nach erfolgreichen Migrationen wird die Version im Config Entry nicht aktualisiert, was dazu führt, dass bei jedem Neustart alle Migrationen erneut ausgeführt werden.

2. **Veraltete Version in config_flow.py**: Die `VERSION = 4` in `config_flow.py` ist veraltet (aktuelle Migration-Version ist 8), was dazu führt, dass neue Config Entries mit einer falschen Version erstellt werden.

3. **Keine zentrale Versionsverwaltung**: Die Version ist an mehreren Stellen hardcodiert, was zu Inkonsistenzen führen kann.

## Geplante Lösung

### 1. Zentrale Versionskonstante in `const_migration.py`

**Ziel**: Eine zentrale Konstante `MIGRATION_VERSION` erstellen, die automatisch die neueste Migration-Version enthält.

**Implementierung**:
```python
# In const_migration.py nach der MigrationVersion Klasse hinzufügen:

# Aktuelle Migration-Version (wird automatisch aus MigrationVersion.get_latest() ermittelt)
MIGRATION_VERSION = MigrationVersion.get_latest().value
```

**Vorteile**:
- Zentrale Quelle für die aktuelle Version
- Automatische Aktualisierung bei neuen Migration-Versionen
- Keine manuelle Synchronisation erforderlich

### 2. Config Flow verwendet zentrale Konstante

**Ziel**: `config_flow.py` importiert und verwendet die zentrale Konstante statt einer hardcodierten Version.

**Implementierung**:
```python
# In config_flow.py am Anfang der Datei:
from .const_migration import MIGRATION_VERSION

# In der LambdaConfigFlow Klasse:
class LambdaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = MIGRATION_VERSION  # Wird aus const_migration.py importiert
```

**Vorteile**:
- Neue Config Entries erhalten automatisch die aktuelle Version
- Keine manuelle Aktualisierung in `config_flow.py` erforderlich
- Konsistenz zwischen Migration-System und Config Flow

### 3. Version nach jeder erfolgreichen Migration aktualisieren

**Ziel**: Nach jeder erfolgreichen Migration wird die Version im Config Entry sofort auf die spezifische Versionsnummer der gerade durchgeführten Migration gesetzt.

**Implementierung**:
```python
# In migration.py, Zeile 779-784 ändern:

if success:
    successful_migrations += 1
    # Version sofort nach erfolgreicher Migration aktualisieren
    # Verwendet die spezifische Versionsnummer dieser Migration
    hass.config_entries.async_update_entry(
        config_entry,
        version=migration_version.value
    )
    _LOGGER.info(
        "Migration zu Version %s (v%d) für Config %s erfolgreich - Version aktualisiert", 
        migration_version.name, migration_version.value, entry_id
    )
```

**Vorteile**:
- **Robustheit bei Fehlern**: Wenn eine Migration fehlschlägt, ist die Version bereits auf die letzte erfolgreiche Migration gesetzt
- **Überspringen möglich**: Wenn eine Migration per Code übersprungen wird, bleibt die Version korrekt
- **Fortschritt erhalten**: Bei Neustart wird nur ab der letzten erfolgreichen Migration fortgesetzt
- **Reihenfolge-Fehler abgefangen**: Auch wenn die Reihenfolge falsch ist, wird jede Migration einzeln dokumentiert

## Beispiel-Szenario

**Szenario**: Migrationen 2, 3, 4, 5 müssen durchgeführt werden

**Mit sofortiger Aktualisierung**:
- Migration 2 erfolgreich → Version = 2 ✅
- Migration 3 erfolgreich → Version = 3 ✅
- Migration 4 fehlgeschlagen → Version bleibt 3 ✅
- Bei Neustart: Nur Migration 4 und 5 werden erneut versucht ✅

**Ohne sofortige Aktualisierung (aktueller Zustand)**:
- Alle Migrationen durchgeführt, aber Version bleibt auf 1 ❌
- Bei Neustart: Alle Migrationen werden erneut ausgeführt ❌
- Kann zu Problemen führen (z.B. doppelte Entity-Entfernung) ❌

## Aufgabenliste

- [x] **const_migration.py**: Konstante `MIGRATION_VERSION` hinzufügen
  - [x] Nach `MigrationVersion` Klasse hinzufügen
  - [x] Wert aus `MigrationVersion.get_latest().value` ableiten
  - [x] Dokumentation hinzufügen

- [x] **config_flow.py**: Zentrale Konstante verwenden
  - [x] Import von `MIGRATION_VERSION` hinzufügen
  - [x] `VERSION = 4` durch `VERSION = MIGRATION_VERSION` ersetzen
  - [x] Alten Kommentar entfernen/aktualisieren

- [x] **migration.py**: Version nach jeder Migration aktualisieren
  - [x] In `perform_structured_migration()` nach erfolgreicher Migration (Zeile 779)
  - [x] `hass.config_entries.async_update_entry()` mit `version=migration_version.value` aufrufen
  - [x] Log-Message erweitern um Versionsnummer

- [ ] **Tests**: Testfälle für Versionsaktualisierung
  - [ ] Test: Version wird nach erfolgreicher Migration aktualisiert
  - [ ] Test: Version bleibt bei fehlgeschlagener Migration unverändert
  - [ ] Test: Neue Config Entries erhalten aktuelle Version
  - [ ] Test: Mehrere Migrationen nacheinander aktualisieren Version korrekt

- [x] **Dokumentation**: Migration-System Dokumentation aktualisieren
  - [x] `docs/lambda_heat_pumps_migration_system.md` aktualisieren
  - [x] Versionsaktualisierung im Ablaufplan dokumentieren
  - [x] Beispiel-Szenarien hinzufügen

## Technische Details

### Dateien die geändert werden müssen

1. `custom_components/lambda_heat_pumps/const_migration.py`
   - Hinzufügen: `MIGRATION_VERSION = MigrationVersion.get_latest().value`

2. `custom_components/lambda_heat_pumps/config_flow.py`
   - Import: `from .const_migration import MIGRATION_VERSION`
   - Änderung: `VERSION = MIGRATION_VERSION`

3. `custom_components/lambda_heat_pumps/migration.py`
   - Änderung in `perform_structured_migration()` Zeile 779-784
   - Hinzufügen: `async_update_entry()` Aufruf

### Abhängigkeiten

- Home Assistant `config_entries.async_update_entry()` API
- Migration-Versionen müssen sequenziell sein (bereits gegeben durch `IntEnum`)

### Risiken

- **Niedrig**: Änderungen sind rückwärtskompatibel
- **Niedrig**: Bestehende Config Entries werden bei nächstem Neustart korrekt migriert
- **Mittel**: Bei fehlerhafter Implementierung könnten Migrationen doppelt ausgeführt werden

### Validierung

Nach Implementierung sollte geprüft werden:

1. Neue Config Entry erstellt → Version = 8 (oder aktuelle Version)
2. Migration durchgeführt → Version wird auf Zielversion aktualisiert
3. Neustart nach teilweise erfolgreicher Migration → Nur ausstehende Migrationen werden ausgeführt
4. Fehlgeschlagene Migration → Version bleibt auf letzter erfolgreicher Migration

## Status

- **Erstellt**: 2025-01-XX
- **Umsetzungsdatum**: 2025-01-XX
- **Priorität**: Hoch
- **Geschätzte Dauer**: 1-2 Stunden
- **Abhängigkeiten**: Keine
- **Code-Implementierung**: ✅ Abgeschlossen
- **Dokumentation**: ✅ Abgeschlossen
- **Tests**: ⏳ Ausstehend

## Notizen

- Die Lösung wurde in Diskussion mit dem Entwickler erarbeitet
- Die sofortige Versionsaktualisierung nach jeder Migration ist wichtig für Robustheit
- Zentrale Konstante verhindert Inkonsistenzen zwischen verschiedenen Dateien
- Die Version sollte nach jeder einzelnen Migration aktualisiert werden (nicht erst am Ende), damit bei einem Neustart während mehrerer Migrationen der Fortschritt erhalten bleibt

