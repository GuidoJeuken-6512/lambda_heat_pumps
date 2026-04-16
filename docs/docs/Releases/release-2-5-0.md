---
title: "Release 2.5.0"
---

# Release 2.5.0

*Zuletzt geändert am 16.04.2026*

> **Aktueller Release** · Branch `V2.5.0`

---

## Zusammenfassung

Release 2.5.0 ist ein reines Code-Qualitäts- und Stabilitätsrelease ohne Breaking Changes. Es behebt 3 kritische Probleme (Race Condition im Reload-Mechanismus, Event-Loop-gebundene Modbus-Locks, unbehandelte Exceptions im Auto-Detection-Hintergrundtask), 4 Probleme hoher Priorität (Entity-Registry-Listener ohne Debounce, nicht-atomares Sensor-ID-Update, fehlender Persist-Flush beim Shutdown, State-Inkonsistenz bei fehlgeschlagenem Climate-Write) und 4 Probleme mittlerer Priorität (fragile JSON-Repair-Logik, fehlende Temperaturvalidierung, Batch-Limit-Optimierung, fehlendes Versionsfeld in der Persist-Datei). Zusätzlich wurden ~110 Zeilen hardcodierter Debug-Code und toter Code entfernt sowie Log-Level vereinheitlicht.

**Keine Auswirkung auf `unique_id`, `entity_id` oder `sensor_id` — alle Änderungen sind non-destruktiv.**

---

## Kritische Fixes

### K-01 · Race Condition im Reload-Flag behoben

**Betroffen:** `custom_components/lambda_heat_pumps/__init__.py` · `async_reload_entry()`

**Problem:** Der Fast-Path-Check vor dem Lock-Erwerb las `_entry_reload_flags` ohne den Lock zu halten. Zwischen dem ersten Check (False) und dem Erwerb des Locks konnte ein paralleler Aufruf denselben Zustand sehen und ebenfalls fortfahren.

**Fix:** Der Fast-Path verwendet jetzt `lock.locked()` — ein atomarer, nicht-blockierender Check. Das Flag wird unmittelbar nach Lock-Erwerb gesetzt (kein Fenster mehr zwischen Check und Setzen):

```python
# Vorher (fehlerhaft):
if _entry_reload_flags.get(entry_id, False):   # ohne Lock — TOCTOU
    return True
async with reload_lock:
    if _entry_reload_flags.get(entry_id, False):
        return True
    _entry_reload_flags[entry_id] = True       # zu spät

# Nachher (korrekt):
if reload_lock.locked():                       # atomar, kein Lock nötig
    return True
async with reload_lock:
    _entry_reload_flags[entry_id] = True       # sofort nach Lock-Erwerb
```

---

### K-02 · Exception im Background-Auto-Detection-Task korrekt geloggt

**Betroffen:** `custom_components/lambda_heat_pumps/__init__.py` · `background_auto_detect()`

**Problem:** Wenn die Hintergrundaufgabe zur Modul-Erkennung fehlschlug, wurde die Exception nur als `INFO` geloggt — ohne vollständigen Traceback. Fehler waren im Log kaum auffindbar.

**Fix:** Log-Level auf `WARNING` angehoben, `exc_info=True` für vollständigen Traceback:

```python
# Vorher:
_LOGGER.info("AUTO-DETECT: Background auto-detection failed: %s ...", ex)

# Nachher:
_LOGGER.warning("AUTO-DETECT: Background auto-detection failed: %s ...", ex, exc_info=True)
```

---

### K-03 · Modbus-Locks Lazy-Initialized

**Betroffen:** `custom_components/lambda_heat_pumps/modbus_utils.py`

**Problem:** `asyncio.Lock()`-Objekte wurden auf Modul-Ebene beim Import erstellt und sind damit an den asyncio-Event-Loop zum Importzeitpunkt gebunden. Bei Loop-Neuerstellung (z. B. in Testumgebungen) werden die Locks invalid und können zu `RuntimeError` führen.

**Fix:** Lazy-Initialization über Getter-Funktionen — der Lock wird erst beim ersten Aufruf erstellt:

```python
# Vorher:
_modbus_read_lock = asyncio.Lock()   # beim Import gebunden

# Nachher:
_modbus_read_lock: asyncio.Lock | None = None

def _get_modbus_read_lock() -> asyncio.Lock:
    global _modbus_read_lock
    if _modbus_read_lock is None:
        _modbus_read_lock = asyncio.Lock()
    return _modbus_read_lock
```

---

## Hohe Priorität

### H-01 · Entity-Registry-Listener mit Debounce

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_on_entity_registry_changed()`

**Problem:** Jede Änderung im Entity-Registry erzeugte sofort einen neuen `async_create_task`-Aufruf für `_update_entity_address_mapping()`. Beim gleichzeitigen Ändern vieler Entitäten (z. B. beim ersten Laden) entstanden viele parallele Mapping-Updates mit redundanten Modbus-Reads.

**Fix:** 250ms Debounce mit `async_call_later` — überlappende Ereignisse werden zu einem einzigen Update zusammengefasst:

```python
if self._registry_update_cancel is not None:
    self._registry_update_cancel()

@callback
def _delayed_update(_now):
    self._registry_update_cancel = None
    self.hass.async_create_task(self._update_entity_address_mapping())

self._registry_update_cancel = async_call_later(self.hass, 0.25, _delayed_update)
```

---

### H-02 · Sensor-ID-Updates atomar

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_detect_and_handle_sensor_changes()`

**Problem:** `self._sensor_ids` und `self._thermal_sensor_ids` wurden innerhalb der Verarbeitungsschleife bei jeder Iteration direkt überschrieben. An `await`-Punkten zwischen den Iterationen konnte ein gleichzeitiger `_persist_counters`-Aufruf einen inkonsistenten Zwischenzustand sehen.

**Fix:** Verarbeitung auf lokalen Kopien; atomarer Tausch am Ende — kein `await` zwischen den Zuweisungen:

```python
local_sensor_ids = dict(self._sensor_ids)
local_thermal_sensor_ids = dict(self._thermal_sensor_ids)
# ... Verarbeitung auf lokalen Kopien ...
# Atomar tauschen:
self._sensor_ids = persist_data["sensor_ids"]
self._thermal_sensor_ids = persist_data["thermal_sensor_ids"]
```

---

### H-03 · Persist-Flush bei Shutdown

**Betroffen:** `custom_components/lambda_heat_pumps/__init__.py` · `async_unload_entry()`  
**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_persist_counters()`

**Problem:** Der 30-Sekunden-Debounce für Disk-Writes konnte dazu führen, dass Änderungen innerhalb des Debounce-Fensters beim HA-Shutdown verloren gingen (kein erzwungener Flush).

**Fix:** `_persist_counters()` erhält einen optionalen `force`-Parameter; beim Unload der Integration wird `force=True` aufgerufen:

```python
# In _persist_counters():
async def _persist_counters(self, force: bool = False):
    if not force and current_time - self._persist_last_write < self._persist_debounce_seconds:
        return  # debounce

# In async_unload_entry():
if getattr(coordinator, "_persist_dirty", False):
    await coordinator._persist_counters(force=True)
```

---

### H-04 · Climate Write-Fehler State-Inkonsistenz behoben

**Betroffen:** `custom_components/lambda_heat_pumps/climate.py` · `async_set_temperature()`

**Problem:** Wenn `async_write_registers()` `None` zurückgab (kein `isError`-Attribut), wurde trotzdem `coordinator.data[key] = temperature` gesetzt — ein falscher lokaler State-Update ohne bestätigten Modbus-Write.

**Fix:** Explizite Prüfung auf `None` vor dem State-Update; bei Fehler wird der Gerätewert per `async_request_refresh()` neu geladen:

```python
if result is None or (hasattr(result, "isError") and result.isError()):
    _LOGGER.error("Failed to write target temperature: %s", result)
    await self.coordinator.async_request_refresh()
    return

# Nur bei Erfolg: lokaler State-Update
self.coordinator.data[key] = temperature
self.async_write_ha_state()
await self.coordinator.async_request_refresh()
```

---

## Mittlere Priorität

### M-01 · JSON-Repair-Logik vereinfacht

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_repair_and_load_persist_file()`

**Problem:** Die Funktion enthielt eine fragile Regex-basierte JSON-Reparatur für doppelte Schlüssel (die `json.loads()` ohnehin automatisch auflöst) sowie einen Bug, bei dem `required_fields` nur geprüft wurden wenn `last_operating_states` im JSON vorhanden war.

**Fix:** Regex-Reparatur entfernt. Klare Strategie: valides JSON normalisieren + fehlende Felder auffüllen; korruptes JSON → Backup erstellen → leer beginnen. `required_fields` werden immer geprüft:

```python
# Bei Korruption (früher: Regex-Repair):
backup_file = self._persist_file + ".backup"
# Backup erstellen, Datei löschen, leer beginnen
os.remove(self._persist_file)
return {}
```

---

### M-02 · Modbus-Batch-Größe optimiert

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py`

**Problem:** Die Batch-Größe war auf 120 Register gesetzt. Der Modbus-Standard erlaubt maximal 125 Holding-Register pro Request — ohne Sicherheitspuffer für Protokoll-Overhead.

**Fix:** Limit auf 100 Register gesenkt (konservativer Puffer):

```python
# Vorher:
or len(current_batch) >= 120  # Modbus safety margin

# Nachher:
or len(current_batch) >= 100  # Modbus max 125 holding regs; 100 = safe margin
```

---

### M-03 · Climate Temperaturbereich-Validierung

**Betroffen:** `custom_components/lambda_heat_pumps/climate.py` · `LambdaClimateEntity.__init__()`

**Problem:** `min_temp` und `max_temp` wurden aus den Entry-Optionen übernommen ohne zu prüfen, ob `min_temp < max_temp`. Bei ungültiger Konfiguration würde HA keine Temperatur mehr setzen können.

**Fix:** Validierung mit automatischem Fallback auf Defaults:

```python
if min_temp >= max_temp:
    _LOGGER.warning(
        "Invalid temperature range min=%s >= max=%s for %s, using defaults",
        min_temp, max_temp, climate_type,
    )
    min_temp, max_temp = default_min, default_max
```

---

### M-05 · Persist-Datei mit Versionsfeld

**Betroffen:** `custom_components/lambda_heat_pumps/coordinator.py` · `_persist_counters()`

**Problem:** `cycle_energy_persist.json` enthielt kein Versionsfeld. Strukturänderungen in zukünftigen Versionen können ohne Versionsfeld nicht migriert werden.

**Fix:** Feld `"version": 1` wird in alle neu geschriebenen Persist-Dateien eingefügt:

```json
{
  "version": 1,
  "heating_cycles": { ... },
  ...
}
```

---

## Code-Qualität

### Q-01 · Log-Level vereinheitlicht

Verbindungsfehler und Health-Check-Ergebnisse in `modbus_utils.py` und `coordinator.py` wurden von `INFO` auf das semantisch korrekte Level korrigiert:

| Situation | Vorher | Nachher |
|-----------|--------|---------|
| Modbus-Verbindung fehlgeschlagen | `INFO` | `WARNING` |
| Health-Check Fehler / kein Client | `INFO` | `DEBUG` |
| Modbus-Read fehlgeschlagen | `INFO` | `WARNING` |
| Background-Task-Fehler | `INFO` | `WARNING` |

---

### Q-02 · Hardcodierte Register 1020/1022 Debug-Blöcke entfernt

~110 Zeilen hardcodierter INT32-Register-Debug-Code für die Register 1020 und 1022 wurden aus `coordinator.py` entfernt. Der Code enthielt bedingte Log-Ausgaben, die für den Produktivbetrieb nicht geeignet waren und den Lesbarkeit verschlechterten.

---

### Q-03 · Dead Code `_generate_entity_id()` entfernt

`coordinator.py` enthielt eine Methode `_generate_entity_id()`, die laut eigenem DEAD-CODE-GUARD-Kommentar nie aufgerufen wird. Die Methode wurde nach Verifikation (kein Aufruf in der gesamten Codebasis) entfernt.

---

### Q-04 · Log-Prefix-Konstanten definiert

In `__init__.py` wurden Log-Präfix-Konstanten für die häufigsten Log-Kategorien definiert:

```python
_LOG_RELOAD = "RELOAD"
_LOG_AUTODETECT = "AUTO-DETECT"
_LOG_SETUP = "SETUP"
```

---

### Q-05 · Inline-Imports nach oben verschoben

Fünf Utility-Funktionen (`detect_sensor_change`, `get_stored_sensor_id`, `store_sensor_id`, `get_stored_thermal_sensor_id`, `store_thermal_sensor_id`) wurden aus dem Methoden-Körper von `_detect_and_handle_sensor_changes()` an den Anfang von `coordinator.py` verschoben.

---

## Betroffene Dateien

| Datei | Art |
|-------|-----|
| `custom_components/lambda_heat_pumps/__init__.py` | Fix: Race Condition (K-01), Warning-Log (K-02), Persist-Flush beim Shutdown (H-03), Log-Konstanten (Q-04) |
| `custom_components/lambda_heat_pumps/coordinator.py` | Fix: Debounce (H-01), Atomares Sensor-Update (H-02), Persist-Version (M-05), JSON-Repair (M-01), Batch-Limit (M-02), Lazy-Import (Q-05), Debug-Code-Entfernung (Q-02), Dead-Code-Entfernung (Q-03), Log-Level (Q-01) |
| `custom_components/lambda_heat_pumps/modbus_utils.py` | Fix: Lazy-Locks (K-03), Log-Level (Q-01) |
| `custom_components/lambda_heat_pumps/climate.py` | Fix: State-Inkonsistenz (H-04), Temperaturvalidierung (M-03) |
| `tests/test_climate.py` | Test-Anpassung: `async_request_refresh` statt `async_refresh` |
| `tests/test_init_simple.py` | Test-Anpassung: `lock.locked()` statt Flag-Check; `_get_modbus_read_lock()` statt direkter Lock-Zugriff |

---

## Migration / Breaking Changes

**Keine Breaking Changes für Endanwender.**

`unique_id`, `entity_id` und `sensor_id` aller Entitäten bleiben unverändert. Bestehende Dashboards, Automationen und Entity-Registry-Einträge sind nicht betroffen.

Für Entwickler: Die internen Funktionen `_get_modbus_read_lock()` und `_get_health_check_lock()` ersetzen den direkten Zugriff auf `_modbus_read_lock` / `_health_check_lock`. Eigene Tests, die den Lock direkt importieren, müssen auf den Getter umgestellt werden.
