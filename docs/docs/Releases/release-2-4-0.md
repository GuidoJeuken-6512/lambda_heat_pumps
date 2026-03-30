---
title: "Release 2.4.0"
---

# Release 2.4.0

*Zuletzt geändert am 29.03.2026*

> **Aktueller Release** · Branch `V2.4.0`

---

## Zusammenfassung

Release 2.4.0 behebt mehrere Bugs: einen kritischen Fehler in der Offset-Logik für Cycling-Sensoren (Offsets wurden bei jedem Zyklus-Ereignis erneut addiert), einen Fehler bei der Moduserkennung für Cycling-Zähler (verpasste Zyklen durch geteilten State), einen weiteren kritischen Bug, durch den Betriebsmodus-Wechsel zuverlässig erkannt, aber nie gezählt wurden (`cycling_entity` NameError in `increment_cycling_counter()`), sowie einen Bug, durch den konfigurierte Energie-Offsets beim HA-Start komplett ignoriert wurden (`_apply_energy_offset()` wurde in `async_added_to_hass()` nie aufgerufen). Zusätzlich wurden das Konfigurations-Template, das Migrationssystem, die Test-Suite und die Dokumentation vollständig aktualisiert.

---

## Bugfixes

### Kritisch: Cycling-Offset wurde bei jedem Zyklus-Ereignis erneut addiert

**Betroffen:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Konfigurierte `cycling_offsets` aus der `lambda_wp_config.yaml` wurden nicht einmalig angewendet, sondern bei jedem erkannten Betriebsmodus-Wechsel (z. B. Wärmepumpe wechselt in Heizbetrieb) erneut auf den Gesamtzähler addiert. Bei einem konfigurierten Offset von 1500 und 10 Zyklen ergab sich:

```
Erwartet:  100 (Basiswert) + 1500 (Offset) + 10 (Zyklen) =  1610
Tatsächlich: 100 + 1500 × 11                             = 16610
```

**Ursache:** `increment_cycling_counter()` las den vollen YAML-Offset-Wert und addierte ihn bei jedem Aufruf, ohne zu prüfen, ob er bereits im Sensorwert enthalten war. Parallel dazu wendete `_apply_cycling_offset()` in `sensor.py` den Offset korrekt einmalig beim HA-Start an — die beiden Mechanismen konkurrierten.

**Fix:** Der Offset-Block wurde vollständig aus `increment_cycling_counter()` entfernt. Der Parameter `cycling_offsets` wurde aus der Funktionssignatur gestrichen. Die alleinige Verantwortung für Offsets liegt jetzt bei `_apply_cycling_offset()` in `sensor.py`, die korrekt differenzbasiert arbeitet (`_applied_offset`-Tracking).

```python
# Vorher (fehlerhaft):
final_value = int(new_value + offset)   # offset = voller YAML-Wert, jedes Mal!

# Nachher (korrekt):
final_value = new_value                 # nur +1, kein Offset hier
```

**Wie `_apply_cycling_offset()` korrekt funktioniert (unverändert):**

```
HA-Start:
  Gespeicherter Wert:      100
  _applied_offset:           0  (aus Attribut, letzte Session)
  YAML-Offset:            1500
  Differenz:              1500  → wird addiert
  Ergebnis:               1600  ✓
  _applied_offset = 1500  (für nächsten Neustart gespeichert)

Nächster HA-Start:
  Gespeicherter Wert:     1600
  _applied_offset:        1500  (wiederhergestellt)
  YAML-Offset:            1500
  Differenz:                 0  → nichts addiert  ✓

Zyklus-Ereignis (nach Fix):
  increment_cycling_counter() addiert nur +1
  Ergebnis: 1600 + 1 = 1601  ✓
```

### Cycling-Zähler: Verpasste Zyklen durch geteilten State

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_track_hp_energy_consumption()` und `_run_cycling_edge_detection()`
**Betroffen:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Zwei HA-Systeme, die dieselbe Wärmepumpe überwachen, zeigten über Zeit unterschiedliche `heating_cycling_daily`-Werte. Betriebsmodusübergänge wurden nicht immer erkannt.

**Ursache:** `_last_operating_state` wurde von zwei unabhängigen Code-Pfaden mit unterschiedlicher Semantik beschrieben:

- **Fast Poll** (alle 2s, `coordinator.py:1615`): schreibt den zuletzt gesehenen Modbus-Wert als Flanken-Gedächtnis für die Cycling-Erkennung.
- **Full Update** (alle 30s, `coordinator.py:2270` in `_track_hp_energy_consumption`): schreibt den zu Beginn des Full Updates gelesenen Zustand als Seiteneffekt der Energieattribution.

Während eines Full Updates werden alle Fast Polls blockiert (`_full_update_running`-Flag). Wenn die WP in dieser Zeit von Zustand A → B → A wechselte, schrieb das Full Update beim Abschluss `A` zurück in `_last_operating_state`. Der nächste Fast Poll sah `last=A, cur=A` → **keine Flanke, beide Zyklen verloren**.

**Fix:** Die Energieattribution erhält ein eigenes `_energy_last_operating_state`-Dict. Der Full Update schreibt ausschließlich in `_energy_last_operating_state`; `_last_operating_state` gehört allein dem Fast Poll.

Zusätzlich liest `increment_cycling_counter()` jetzt `cycling_entity._cycling_value` als Basiswert für den Zähler statt `hass.states.get()`, um eine potenzielle Veraltung nach HA-Start-Wiederherstellung zu vermeiden.

```python
# _track_hp_energy_consumption – vorher:
last_state = self._last_operating_state.get(str(hp_idx), 0)   # ← Fast-Poll-State!
...
self._last_operating_state[str(hp_idx)] = current_state        # ← überschreibt Fast-Poll!

# Nachher:
last_state = self._energy_last_operating_state.get(str(hp_idx), 0)
...
self._energy_last_operating_state[str(hp_idx)] = current_state
```

### Kritisch: Flankenerkennung erkannte Wechsel, zählte aber nie

**Betroffen:** `custom_components/lambda_heat_pumps/utils.py` · `increment_cycling_counter()`

**Symptom:** Betriebsmodus-Wechsel (z. B. STBY-FROST → CH) wurden intern korrekt erkannt und als Flanke eingestuft — der Tages- und Gesamtzähler blieb jedoch bei 0. Im HA-Log erschienen keine Fehlermeldungen auf normalem Log-Level.

**Ursache:** In `increment_cycling_counter()` wurde die Variable `cycling_entity` auf Zeile 871 referenziert (Prüfung auf `_cycling_value`), war aber erst auf Zeile 884 definiert. Bei der ersten Ausführung des `for sensor_id`-Loops löste Python einen `NameError` aus.

Dieser propagierte durch `_run_cycling_edge_detection()` (kein `try/except`) bis in `_async_fast_update()`, wo er stillschweigend abgefangen wurde:

```python
except Exception as ex:
    _LOGGER.debug("Fast poll error (non-fatal): %s", ex)  # ← nur debug, nie sichtbar
```

**Zweite Konsequenz:** Weil die Exception vor dem Schreiben von `self._last_operating_state[str(hp_idx)] = op_state_val` auftrat, wurde der gespeicherte Zustand nie aktualisiert. Beim nächsten Fast Poll (nach 2 s) sah die Flankenerkennung wieder denselben Übergang — erkannte ihn erneut, scheiterte erneut. Die Schleife lief für die gesamte Dauer des CH-Modus alle 2 Sekunden durch, ohne je einen Zyklus zu zählen.

**Fix:** Die Entity-Suche (`cycling_entity = None` + Lookup-Block) wurde **vor** die Leseoperation für `current` verschoben:

```python
# Vorher (fehlerhaft) — cycling_entity undefiniert bei erstem Aufruf:
if cycling_entity is not None and hasattr(cycling_entity, "_cycling_value"):
    current = cycling_entity._cycling_value or 0
...
cycling_entity = None   # ← zu spät!
for entry_id, comp_data in ...:
    cycling_entity = comp_data["cycling_entities"].get(entity_id)

# Nachher (korrekt):
cycling_entity = None   # ← zuerst definieren
for entry_id, comp_data in ...:
    cycling_entity = comp_data["cycling_entities"].get(entity_id)
...
if cycling_entity is not None and hasattr(cycling_entity, "_cycling_value"):
    current = cycling_entity._cycling_value or 0
```

### Kritisch: Energie-Offsets beim HA-Start komplett ignoriert

**Betroffen:** `custom_components/lambda_heat_pumps/sensor.py` · `LambdaEnergyConsumptionSensor.async_added_to_hass()`

**Symptom:** Konfigurierte `energy_consumption_offsets` aus der `lambda_wp_config.yaml` wurden beim HA-Start nicht angewendet. Sensoren wie `hot_water_energy_total` blieben am gespeicherten Rohwert — kein Offset, keine Log-Ausgabe.

**Ursache:** `_apply_energy_offset()` war korrekt implementiert (differenzbasiertes Tracking, identisch zum Cycling-Mechanismus) — wurde aber nie aufgerufen. `async_added_to_hass()` rief `restore_state()` auf und anschließend `_apply_persisted_energy_state()` (die `_energy_value` mit dem rohen Coordinator-Wert überschreiben kann) — danach endete die Funktion, ohne `_apply_energy_offset()` zu rufen.

**Fix:** `_apply_energy_offset()` wird jetzt am Ende von `async_added_to_hass()` aufgerufen, nach `_apply_persisted_energy_state()`, damit der Offset auf dem finalen Rohwert angewendet wird:

```python
# async_added_to_hass() – vorher (fehlerhaft):
await self.restore_state(last_state)
if our_state:
    self._apply_persisted_energy_state(our_state)
    self.async_write_ha_state()
# ← _apply_energy_offset() nie aufgerufen, Offset ignoriert

# Nachher (korrekt):
await self.restore_state(last_state)
if our_state:
    self._apply_persisted_energy_state(our_state)
    self.async_write_ha_state()
# Offset ZULETZT anwenden — nach _apply_persisted_energy_state()
if self._period == "total":
    await self._apply_energy_offset()
```

---

## Neue Funktionen

### Negative Offsets werden explizit unterstützt und dokumentiert

Sowohl `cycling_offsets` als auch `energy_consumption_offsets` akzeptieren negative Werte. Ein negativer Offset subtrahiert den angegebenen Betrag vom Gesamtzähler — nützlich, um einen zu hohen Ausgangswert zu korrigieren.

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: -200   # Subtrahiert 200 von der Gesamtzahl
```

Die Validierung beim Laden prüft nur, ob der Wert numerisch ist — kein `>= 0`-Check.

### Thermische Energie-Offsets dokumentiert und migriert

`energy_consumption_offsets` unterstützt neben elektrischen Offsets (`{mode}_energy_total`) auch thermische Offsets (`{mode}_thermal_energy_total`). Dies war bisher undokumentiert. Die vier thermischen Schlüssel werden jetzt auch in das `LAMBDA_WP_CONFIG_TEMPLATE` geschrieben und durch das Migrationssystem automatisch in bestehende `lambda_wp_config.yaml`-Dateien eingefügt:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0             # elektrisch
    heating_thermal_energy_total: 6500.0     # thermisch (optional)
    hot_water_thermal_energy_total: 2600.0   # thermisch (optional)
    cooling_thermal_energy_total: 800.0      # thermisch (optional)
    defrost_thermal_energy_total: 120.0      # thermisch (optional)
```

---

## Migrationssystem

### Neue Migrations-Schritte in `migrate_lambda_config_sections()`

Beim HA-Start prüft das Migrationssystem bestehende `lambda_wp_config.yaml`-Dateien auf fehlende Schlüssel und fügt sie automatisch ein — ohne andere Inhalte zu verändern.

**Schritt 1: `compressor_start_cycling_total` in `cycling_offsets`**

Dateien, die vor V2.4.0 erstellt wurden, fehlte der Schlüssel `compressor_start_cycling_total` im `cycling_offsets`-Block. Die Migration erkennt das Fehlen und fügt die Zeile nach `defrost_cycling_total:` ein — passend zur Einrückung (kommentiert oder aktiv):

```yaml
# Vorher:
cycling_offsets:
  hp1:
    defrost_cycling_total: 0

# Nachher:
cycling_offsets:
  hp1:
    defrost_cycling_total: 0
    compressor_start_cycling_total: 0      # Offset for compressor start total
```

**Schritt 2: Thermische Energie-Offset-Schlüssel in `energy_consumption_offsets`**

Die vier thermischen Schlüssel (`heating_thermal_energy_total`, `hot_water_thermal_energy_total`, `cooling_thermal_energy_total`, `defrost_thermal_energy_total`) werden kettenweise nach `defrost_energy_total:` eingefügt, falls sie fehlen. Teilweise vorhandene Schlüssel werden übersprungen.

---

## Konfigurationstemplate (`const_base.py`)

Das `LAMBDA_WP_CONFIG_TEMPLATE` wurde erweitert:

- `compressor_start_cycling_total` wurde zum Cycling-Offset-Beispiel hinzugefügt (fehlte bisher trotz Unterstützung)
- Thermische Energie-Offsets (`{mode}_thermal_energy_total`) wurden als kommentierte Beispiele ergänzt
- Hinweis auf negative Offsets wurde eingefügt
- Kommentare auf Englisch vereinheitlicht

---

## Dokumentation

### Benutzer-Dokumentation

| Datei | Änderung |
|---|---|
| `Anwender/offsets.md` | **Neu**: Eigenständige, vollständige Dokumentation für Cycling- und Energie-Offsets; erklärt Differenz-Tracking, negative Offsets, alle Szenarien |
| `Anwender/lambda-wp-config.md` | Offset-Abschnitte auf Kurzbeschreibung + Link zu `offsets.md` gekürzt; negative und thermische Offsets im Beispiel ergänzt |
| `Anwender/historische-daten.md` | Warnbanner „fehlerhaft" entfernt; Funktionsweise-Beschreibung korrigiert (Punkt 2 beschrieb fälschlicherweise das buggy Verhalten); thermische Offsets ergänzt |

> Die Hinweise `⚠️ die Funktion der Offsets ist fehlerhaft, bitte im Moment nicht einsetzen!` wurden entfernt. Cycling-Offsets können ab Version 2.4.0 ohne Einschränkung eingesetzt werden.

### Entwickler-Dokumentation

| Datei | Änderung |
|---|---|
| `Entwickler/migration-system.md` | **Neu**: Vollständige technische Beschreibung des Migrationssystems (MigrationVersion-Enum, Ablauf, alle Migrationsschritte, Backup-Logik, Erweiterungsanleitung) |
| `Entwickler/offset-system.md` | **Neu**: Vollständige technische Beschreibung des Offset-Systems (Differenz-Tracking, Persistierung via `applied_offset`, Sequenzdiagramm, YAML-Struktur) |
| `Entwickler/cycling-sensoren.md` | Flankenerkennung-Codebeispiel aktualisiert (kein `cycling_offsets`-Parameter mehr); Increment-Logik-Beispiel auf korrekten Stand gebracht; Abschnitt 8 (Cycling-Offsets) vollständig überarbeitet; Log-Meldung korrigiert |
| `Entwickler/modbus-wp-config.md` | `cycling_offsets`-Abschnitt: Codebeispiel zeigt jetzt `_apply_cycling_offset()` statt altem Bugcode; thermische Offsets ergänzt; negative Offsets dokumentiert; vollständiges Beispiel erweitert |

---

## Tests

Testdatei `tests/test_offset_features.py` mit **37 Tests** (23 bestehende + 9 neue Migrations-Tests + 5 neue Energie-Offset-Startup-Tests):

| Testgruppe | Abgedeckte Szenarien |
|---|---|
| `TestCyclingOffsetOnStartup` | Positiver Offset einmalig addiert; negativer Offset subtrahiert; Offset 0 → keine Änderung; kein Config-Eintrag → keine Änderung |
| `TestCyclingOffsetDifferentialTracking` | Gleicher Offset nicht erneut angewendet; erhöhter Offset addiert nur Delta; verringerter Offset subtrahiert nur Delta |
| `TestCyclingOffsetPersistence` | `applied_offset` in State-Attributen vorhanden; nach HA-Neustart wiederhergestellt |
| `TestIncrementCyclingCounterNoOffset` | Inkrementiert exakt um +1 ohne Offset; `cycling_offsets`-Parameter nicht mehr in Signatur (Regressionsschutz) |
| `TestEnergyOffsetApplication` | Elektrischer Offset beim Start angewendet; negativer Offset subtrahiert; gleicher Offset nicht doppelt angewendet |
| `TestEnergyOffsetIncrementDifferential` | Erster Aufruf aktualisiert `_applied_offset`; zweiter Aufruf mit gleichem Offset addiert nichts extra |
| `TestOffsetConfigValidation` | Negative Werte bestehen Validierung; nicht-numerische Werte werden auf 0 gesetzt; thermische Schlüssel sind gültig |
| `TestConfigTemplate` | Template enthält `cycling_offsets`, `thermal_energy_total`, `compressor_start_cycling_total` |
| `TestMigrateCyclingOffsetCompressorStart` | **Neu**: Migration fügt `compressor_start_cycling_total` ein wenn fehlend; überspringt vorhandene Einträge; korrekte Einrückung bei aktivem Block |
| `TestMigrateThermalEnergyOffsets` | **Neu**: Migration fügt alle 4 thermischen Energie-Schlüssel ein; korrekte Reihenfolge; überspringt bereits vorhandene; funktioniert bei mehreren HP-Blöcken |
| `TestEnergyOffsetAppliedViaAsyncAddedToHass` | **Neu**: Energie-Offset via `async_added_to_hass()` angewendet; kein erneutes Anwenden beim zweiten Neustart; Offset nach Coordinator-State-Überschreiben korrekt; Call-Site-Absicherung für Total-Sensor; Daily-Sensor bleibt unberührt |

---

## Migration / Breaking Changes

**Keine Breaking Changes für Endanwender.**

Für Entwickler: Der Parameter `cycling_offsets` wurde aus `increment_cycling_counter()` entfernt. Eigene Aufrufe dieser Funktion müssen angepasst werden:

```python
# Alt (2.3.x):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
    cycling_offsets=self._cycling_offsets,   # ← entfernen
)

# Neu (2.4.0):
await increment_cycling_counter(
    hass, mode=mode, hp_index=1, name_prefix="eu08l",
)
```

---

## Betroffene Dateien

| Datei | Art |
|---|---|
| `custom_components/lambda_heat_pumps/utils.py` | Bugfix: Offset-Block aus `increment_cycling_counter()` entfernt; Entity-Lookup vor `current`-Leseoperation verschoben (NameError-Fix); Basiswert liest jetzt `_cycling_value` statt HA-State |
| `custom_components/lambda_heat_pumps/sensor.py` | Bugfix: `_apply_energy_offset()` wird in `async_added_to_hass()` nach `_apply_persisted_energy_state()` aufgerufen (Energie-Offsets wurden zuvor komplett ignoriert) |
| `custom_components/lambda_heat_pumps/coordinator.py` | Bugfix: `_energy_last_operating_state` getrennt von `_last_operating_state`; `cycling_offsets`-Parameter aus Aufrufen entfernt |
| `custom_components/lambda_heat_pumps/const_base.py` | Erweiterung: `LAMBDA_WP_CONFIG_TEMPLATE` (thermische Offsets vollständig ergänzt) |
| `custom_components/lambda_heat_pumps/migration.py` | Neu: Migration für `compressor_start_cycling_total` und thermische Energie-Offset-Schlüssel |
| `tests/test_offset_features.py` | Erweitert: 37 Tests (9 neue für Migrations-Szenarien, 5 neue für Energie-Offset-Startup-Regression) |
| `docs/docs/Anwender/offsets.md` | Neu: eigenständige Offset-Dokumentation |
| `docs/docs/Anwender/lambda-wp-config.md` | Offset-Abschnitte gekürzt + Link zu offsets.md |
| `docs/docs/Anwender/historische-daten.md` | Dokumentation aktualisiert |
| `docs/docs/Entwickler/migration-system.md` | Neu: Technische Dokumentation Migrationssystem |
| `docs/docs/Entwickler/offset-system.md` | Neu: Technische Dokumentation Offset-System |
| `docs/docs/Entwickler/cycling-sensoren.md` | Dokumentation aktualisiert |
| `docs/docs/Entwickler/modbus-wp-config.md` | Dokumentation aktualisiert |
