---
title: "Migrationssystem"
---

# Migrationssystem

*Zuletzt geändert am 28.03.2026*

Das Migrationssystem der Lambda Heat Pumps Integration sorgt dafür, dass bestehende Installationen bei einem Update automatisch und sicher auf den neuesten Stand gebracht werden – ohne manuellen Eingriff und ohne Datenverlust.

---

## Übersicht

Das System besteht aus zwei Schichten:

| Schicht | Datei | Zweck |
|---------|-------|-------|
| Versionierte Migrationen | `migration.py` | Einmalige, versionsgebundene Änderungen (Entity-Registry, Config-Entry-Daten) |
| Config-Datei-Migration | `migration.py` → `migrate_lambda_config_sections()` | Laufende Pflege der `lambda_wp_config.yaml` (neue Abschnitte, neue Schlüssel) |
| Konstanten | `const_migration.py` | Versionsnummern, Timeouts, Backup-Parameter, Standardwerte |

---

## Versionsverwaltung (`MigrationVersion`)

Jede strukturelle Änderung erhält eine eigene Versionsnummer in der `MigrationVersion`-Enum (`const_migration.py`):

```python
class MigrationVersion(IntEnum):
    INITIAL                   = 1   # Ursprüngliche Version
    LEGACY_NAMES              = 2   # Entity-Namen Migration
    CYCLING_OFFSETS           = 3   # lambda_wp_config.yaml: cycling_offsets
    ENERGY_CONSUMPTION        = 4   # energy_consumption_sensors & offsets
    ENTITY_OPTIMIZATION       = 5   # Entity-Struktur optimieren
    CONFIG_RESTRUCTURE        = 6   # Konfigurationsschema
    UNIFIED_CONFIG_MIGRATION  = 7   # Template-basierte Migration aller Abschnitte
    REGISTER_ORDER_TERMINOLOGY = 8  # int32_byte_order → int32_register_order
```

Die aktuelle Version wird automatisch aus dem höchsten Wert ermittelt:

```python
MIGRATION_VERSION = MigrationVersion.get_latest().value  # = 8
```

Beim Setup einer neuen Installation wird diese Versionsnummer im Config-Entry gespeichert. Beim Start prüft die Integration, ob die gespeicherte Version kleiner als `MIGRATION_VERSION` ist, und führt alle ausstehenden Migrationen in Reihenfolge aus.

---

## Ablauf beim HA-Start

```
HA-Start
  └── async_setup_entry()
        ├── Versionsvergleich: config_entry.version vs. MIGRATION_VERSION
        │     └── falls veraltet: async_migrate_entry() → versionierte Migrationen
        └── load_lambda_config()
              ├── ensure_lambda_config()        (Datei anlegen falls nicht vorhanden)
              └── migrate_lambda_config_sections()  (Config-Datei pflegen, einmal pro Session)
```

Der Flag `hass.data["_lambda_migration_done"]` verhindert, dass `migrate_lambda_config_sections()` innerhalb einer HA-Session mehrfach ausgeführt wird.

---

## Config-Datei-Migration (`migrate_lambda_config_sections`)

Diese Funktion läuft bei **jedem HA-Start** (einmal pro Session) und prüft die `lambda_wp_config.yaml` auf fehlende oder veraltete Inhalte. Sie arbeitet rein textbasiert, um Kommentare und Formatierung zu erhalten.

### Ablauf im Detail

```
1. Datei einlesen (UTF-8)
2. YAML parsen → current_config
3. Schritt A: energy_consumption_sensors-Format upgrade
4. Schritt B: thermal_sensor_entity_id-Zeilen ergänzen
5. Schritt C: compressor_start_cycling_total ergänzen     ← V2.4.0
6. Abschnitte mit _find_section_ranges_in_content() lokalisieren
7. Fehlende Abschnitte (aus Template) an korrekter Position einfügen
8. Backup anlegen → Datei schreiben
```

### Schritt A – energy_consumption_sensors Formatupgrade

Ältere Installationen enthielten einen veralteten Kommentar-Header ohne den Hinweis auf `thermal_sensor_entity_id`. Die Migration ersetzt den alten Header durch den neuen:

```yaml
# Alter Header (wird ersetzt):
# Das System konvertiert automatisch zu kWh für die Berechnungen
# Beispiel:
energy_consumption_sensors:

# Neuer Header (nach Migration):
# Das System konvertiert automatisch zu kWh für die Berechnungen
# sensor_entity_id = elektrisch, thermal_sensor_entity_id = thermisch (optional)
# Beispiel:
energy_consumption_sensors:
```

### Schritt B – `thermal_sensor_entity_id` ergänzen

Nach jeder `sensor_entity_id:`-Zeile im `energy_consumption_sensors`-Block wird geprüft, ob die Folgezeile bereits `thermal_sensor_entity_id:` enthält. Falls nicht, wird die optionale Kommentarzeile eingefügt – mit identischem Einrückungs-Präfix (auch für auskommentierte `#  hp2`-Blöcke):

```yaml
# Vorher:
  hp1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"

# Nachher:
  hp1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"
    # thermal_sensor_entity_id: "sensor.lambda_wp_waerme"  # optional
```

### Schritt C – `compressor_start_cycling_total` ergänzen (V2.4.0)

Nach jeder `defrost_cycling_total:`-Zeile im `cycling_offsets`-Block wird geprüft, ob die Folgezeile bereits `compressor_start_cycling_total:` enthält. Falls nicht, wird die Zeile eingefügt. Das Präfix (Kommentarzeichen `#` und Einrückung) wird aus der `defrost_cycling_total:`-Zeile übernommen – korrekt für auskommentierte Beispiele und aktive Konfigurationen:

```yaml
# Vorher (auskommentiert):
#    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles

# Nachher:
#    defrost_cycling_total: 0      # Offset for HP1 defrost total cycles
#    compressor_start_cycling_total: 0      # Offset for compressor start total
```

```yaml
# Vorher (aktiv):
    defrost_cycling_total: 5

# Nachher:
    defrost_cycling_total: 5
    compressor_start_cycling_total: 0      # Offset for compressor start total
```

### Schritt D – Fehlende Abschnitte einfügen

Die fünf Template-Abschnitte werden anhand ihrer eindeutigen Header-Zeilen in der Datei gesucht:

| Abschnitt | Header-Zeile |
|-----------|-------------|
| `sensors_names_override` | `# Override sensor names (only works if use_legacy_modbus_names is true)` |
| `cycling_offsets` | `# Cycling counter offsets for total sensors` |
| `energy_consumption_sensors` | `# Energy consumption sensor configuration` |
| `energy_consumption_offsets` | `# Energy consumption offsets for total sensors` |
| `modbus` | `# Modbus configuration` |

Fehlt ein Abschnitt (weder im Dateitext noch als aktiver YAML-Schlüssel), wird er aus dem `LAMBDA_WP_CONFIG_TEMPLATE` (`const_base.py`) in der korrekten Reihenfolge eingefügt. Bestehende Abschnitte bleiben **unverändert**.

**Wichtig:** Die Funktion führt nie ein blindes Anhängen am Dateiende durch. Fehlende Abschnitte werden exakt an der richtigen Position zwischen den vorhandenen Abschnitten eingefügt.

---

## Backup-System

Vor jeder Änderung an der `lambda_wp_config.yaml` wird ein Backup angelegt:

```
config/
└── lambda_heat_pumps/
    └── backup/
        ├── lambda_wp_config.yaml.backup          ← Inline-Backup (direkt neben Originaldatei)
        └── lambda_wp_config.<migration>_<timestamp>.yaml
```

Backup-Retention-Zeiten (konfigurierbar in `const_migration.py`):

| Dateityp | Aufbewahrung |
|----------|-------------|
| Registry-Backups (Entity, Device, Config) | 30 Tage |
| `lambda_wp_config.yaml`-Backups | 60 Tage |
| Alte `.backup`-Dateien | 7 Tage |

---

## Versionierte Migrations­funktionen

Diese Funktionen werden einmalig ausgeführt, wenn eine Installation von einer älteren Version hochgestuft wird:

### `migrate_to_legacy_names()` – Version 2

Bereinigt die Entity-Registry: Entfernt alle Climate- und Sensor-Entities, die nicht mehr dem aktuellen Namensschema entsprechen. Wird benötigt, wenn `use_legacy_modbus_names` umgestellt wurde oder das Namensschema sich geändert hat.

### `migrate_to_cycling_offsets()` – Version 3 (deprecated)

Fügte den `cycling_offsets`-Abschnitt zur `lambda_wp_config.yaml` hinzu. Seit Version 7 übernimmt `migrate_lambda_config_sections()` diese Aufgabe template-basiert. Die Funktion bleibt für Rückwärtskompatibilität erhalten.

### `migrate_to_unified_config()` – Version 7

Führte die template-basierte Migration aller Config-Abschnitte ein. Ersetzt die einzelnen Abschnittsmigrations-Funktionen der Versionen 3–6.

---

## Entity-Duplikat-Cleanup (`async_remove_duplicate_entity_suffixes`)

Home Assistant vergibt bei Konflikten in der Entity-Registry automatisch Suffixe wie `_2`, `_3`. Diese Funktion bereinigt solche Duplikate beim Setup:

**Sammelphase:**
1. Alle Entities des aktuellen Config-Eintrags mit `_2`/`_3`-Suffix
2. Verwaiste Duplikate (Config-Entry-ID existiert nicht mehr, aber Entity ist noch registriert)

**Löschphase** (für jeden Kandidaten):
- Ist die Ziel-`entity_id` (ohne Suffix) noch frei? → **Umbenennen** statt Löschen (verhindert ungewollte Wiederherstellung durch HA beim nächsten Start)
- Gleiche `unique_id` wie Basiseintrag? → Basiseintrag erst entfernen, dann umbenennen
- Echtes Duplikat mit anderer `unique_id`? → Löschen

Ausgenommen sind Entities mit `config_parameter_` in der `entity_id` (interne Konfigurationsparameter).

---

## Erweiterung: Neue Migrations­schritte hinzufügen

### Neuen Versions-Schritt (einmalig)

1. `const_migration.py`: Neuen Eintrag in `MigrationVersion` hinzufügen
2. `migration.py`: Neue `migrate_to_<name>()` Funktion implementieren
3. `__init__.py`: In `async_migrate_entry()` den neuen Schritt einbinden

### Neuen Config-Datei-Schritt (laufend)

1. `const_base.py`: `LAMBDA_WP_CONFIG_TEMPLATE` aktualisieren (neuen Schlüssel/Abschnitt einfügen)
2. `migration.py` → `migrate_lambda_config_sections()`: Neuen Prüf- und Einfüge-Block nach dem Muster der bestehenden Schritte B/C hinzufügen:

```python
# Muster für neuen Migrationsschritt:
if "abschnittsname" in section_ranges:
    s, e = section_ranges["abschnittsname"]
    section_text = content_n[s:e]
    inserts = []
    for match in re.finditer(r"\n((?:#\s+|\s+))anker_schluessel:[^\n]*", section_text):
        line_end = section_text.find("\n", match.end())
        if line_end == -1:
            line_end = len(section_text)
        next_start = line_end + 1
        next_end = section_text.find("\n", next_start)
        if next_end == -1:
            next_end = len(section_text)
        next_line = section_text[next_start:next_end] if next_start < len(section_text) else ""
        if "neuer_schluessel:" in next_line:
            continue
        prefix = match.group(1)
        new_line = "\n" + prefix + "neuer_schluessel: 0      # Beschreibung"
        inserts.append((line_end, new_line))
    for pos, new_line in sorted(inserts, key=lambda x: -x[0]):
        section_text = section_text[:pos] + new_line + section_text[pos:]
    if inserts:
        content_n = content_n[:s] + section_text + content_n[e:]
        content = content_n
        content_modified = True
        # Positionen neu berechnen
        content_n, ranges = _find_section_ranges_in_content(content)
        section_ranges = {name: (s, e) for s, e, name in ranges}
```

3. Tests in `tests/test_offset_features.py` (oder passendem Testmodul) ergänzen

---

## Wichtige Konstanten (`const_migration.py`)

| Konstante | Wert | Bedeutung |
|-----------|------|-----------|
| `MIGRATION_TIMEOUT_SECONDS` | 300 | Timeout pro Migrationsschritt |
| `BACKUP_RETENTION_DAYS["lambda_config"]` | 60 | Aufbewahrung Config-Backups |
| `CLEANUP_INTERVAL_DAYS` | 7 | Cleanup-Intervall für alte Backups |
| `ROLLBACK_ENABLED` | True | Rollback bei kritischen Fehlern aktiv |
| `CRITICAL_ERROR_THRESHOLD` | 0.5 | Ab 50% fehlgeschlagener Migrationen: Rollback |
| `MIGRATION_MAX_RETRIES` | 3 | Wiederholungsversuche pro Migration |

---

## Betroffene Dateien

| Datei | Rolle |
|-------|-------|
| `custom_components/lambda_heat_pumps/migration.py` | Alle Migrationsfunktionen |
| `custom_components/lambda_heat_pumps/const_migration.py` | Versionsnummern, Konstanten, Standardwerte |
| `custom_components/lambda_heat_pumps/const_base.py` | `LAMBDA_WP_CONFIG_TEMPLATE` (Vorlage für neue Abschnitte) |
| `custom_components/lambda_heat_pumps/utils.py` | `migrate_lambda_config_sections()` Delegation, `load_lambda_config()` |
| `custom_components/lambda_heat_pumps/__init__.py` | `async_migrate_entry()` – Einstiegspunkt für versionierte Migrationen |
| `tests/test_offset_features.py` | Tests für Offset- und Config-Migrationsschritte |
