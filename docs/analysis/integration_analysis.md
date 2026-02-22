# Lambda Heat Pumps – Integrationsanalyse und Verbesserungsplan

**Version:** 2.3
**Analysedatum:** 21. Februar 2026
**Branch:** Release2.3 (Commit fcd9a83)
**Dokumentstatus:** Technische Interne Analyse

---

## Inhaltsverzeichnis

1. [Executive Summary](#1-executive-summary)
2. [Offene Punkte – Übersicht](#2-offene-punkte--übersicht)
3. [Architektur-Überblick](#3-architektur-überblick)
4. [Qualitätsbewertung](#4-qualitätsbewertung)
5. [Kritischer Bug: Duplizierte Entities mit `_2`-Suffix](#5-kritischer-bug-duplizierte-entities-mit-_2-suffix)
6. [Vollständige Problemliste nach Schweregrad](#6-vollständige-problemliste-nach-schweregrad)
7. [Konkrete Code-Verbesserungsbeispiele](#7-konkrete-code-verbesserungsbeispiele)
8. [Priorisierter Umsetzungsfahrplan](#8-priorisierter-umsetzungsfahrplan)
9. [Positive Aspekte der Integration](#9-positive-aspekte-der-integration)

---

## 1. Executive Summary

Die Lambda Heat Pumps Integration ist eine funktionsfähige Home Assistant Custom Integration für Lambda Wärmepumpen via Modbus TCP. Sie bietet umfangreiche Sensor-Abdeckung (Temperatur, Energie, Zyklen, COP), Firmware-Versionierung, automatische Modul-Erkennung und ein eigenes Migrationssystem.

Die Integration litt unter einem **kritischen, reproduzierbaren Bug**: Beim Reload entstanden duplizierte Entities mit `_2`-Suffix in der Entity-Registry. Die drei kritischsten Wurzelursachen (K-01, K-02, K-03) wurden in **Release2.3** behoben. Zwei weitere Ursachen (H-02 unique_id-Design, H-03 Template-Sensoren außerhalb von PLATFORMS) sind als mittelfristige Aufgaben offen.

Darüber hinaus weist die Codebasis erhebliche **Wartbarkeits-Defizite** auf: Die zentralen Dateien `sensor.py` (3.010 Zeilen), `coordinator.py` (2.413 Zeilen) und `utils.py` (2.265 Zeilen) sind für einzelne Dateien weit zu groß.

**Bewertungszusammenfassung:**

| Kategorie | Bewertung | Begründung |
|---|---|---|
| Stabilität | 5/10 | Kritischer Reload-Bug, Race Conditions |
| Wartbarkeit | 4/10 | Zu große Dateien, fehlende Typisierung |
| Codequalität | 6/10 | Gute Muster, aber Inkonsistenzen |
| HA-Konformität | 6/10 | Coordinator-Pattern korrekt, Logging-Konvention verletzt |
| Architektur | 7/10 | Sinnvolle Schichtentrennung, Module gut aufgeteilt |

---

## 2. Offene Punkte – Übersicht

Stand: Release2.3 — alle **Kritisch**-Punkte (K-01/02/03) und alle **Niedrig**-Punkte (N-01–N-07) sind behoben.
Die folgende Tabelle zeigt die verbleibenden offenen Punkte nach Priorität.

| ID | Schweregrad | Beschreibung | Datei(en) | Fix-Komplexität | Empfehlung |
|---|---|---|---|---|---|
| H-02 | 🔴 Hoch | `unique_id` enthält `name_prefix` → Waisenentities bei Umbenennung der Integration | utils.py, migration.py | ⬛ Sehr hoch – Migration erforderlich | Phase 4 |
| H-03 | 🔴 Hoch | Template-Sensoren nicht in `PLATFORMS` → werden beim Unload nicht sauber entladen | __init__.py, sensor.py | 🟧 Mittel – PLATFORMS-Mechanismus erweitern | Phase 3 |
| H-05 | 🟠 Mittel | `sensor.py` (3.010 Z.) und `coordinator.py` (2.413 Z.) kaum noch wartbar | sensor.py, coordinator.py | ⬛ Sehr hoch – Refactoring mehrerer Klassen | Phase 4 |
| M-01 | 🟠 Mittel | `asyncio.sleep(0.05)` als fragiler Timing-Workaround für Device-Registry | sensor.py | 🟧 Mittel – HA-Event statt Sleep verwenden | Phase 3 |
| M-03 | 🟡 Niedrig | `self._unique_id` **und** `self._attr_unique_id` in allen Entity-Klassen redundant doppelt gesetzt | sensor.py | 🟩 Niedrig – eine Zuweisung pro Klasse entfernen | Phase 3 |
| M-04 | 🟠 Mittel | `LambdaCyclingSensor` / `LambdaEnergyConsumptionSensor` erben nicht von `CoordinatorEntity` | sensor.py | 🟧 Mittel – Vererbung anpassen, Listener prüfen | Phase 3 |
| M-02 | 🟡 Niedrig | ~130 f-String-Logging-Aufrufe statt `%s`-Format (HA-Konvention, keine Lazy-Evaluation) | coordinator.py, utils.py | 🟩 Niedrig – mechanische Textersetzung | Phase 3 |
| M-08 | 🟡 Niedrig | `lambda`-Ausdrücke in `async_add_executor_job()` (schwer debuggbar, keine Stack-Traces) | utils.py, migration.py | 🟩 Niedrig – Lambda durch benannte Funktion ersetzen | Phase 3 |
| 4d | 🔴 Hoch | `unique_id` vom `name_prefix` entkoppeln + Migration erstellen | utils.py, migration.py | ⬛ Sehr hoch – Breaking Change, Migration nötig | Phase 4 |
| 4a | 🟠 Mittel | `sensor.py` aufteilen: EntityFactory und Klassen trennen | sensor.py | ⬛ Sehr hoch – viele Abhängigkeiten | Phase 4 |
| 4b | 🟠 Mittel | `coordinator.py` aufteilen: Energy-Logik in eigene Klasse | coordinator.py | 🟫 Hoch – DataUpdateCoordinator-Vererbung beachten | Phase 4 |
| 4f | 🟡 Niedrig | Unit-Tests für `generate_sensor_names()` und Reload-Logik fehlen | tests/ | 🟧 Mittel – Test-Fixtures für Coordinator nötig | Phase 4 |

**Fix-Komplexität:** 🟩 Niedrig (< 1h) · 🟧 Mittel (halber Tag) · 🟫 Hoch (1–3 Tage) · ⬛ Sehr hoch (> 3 Tage, Architekturentscheidung)

---

## 3. Architektur-Überblick

### 3.1 Dateistruktur und Verantwortlichkeiten

```
custom_components/lambda_heat_pumps/
├── __init__.py           378 Zeilen  – Integration Setup, Reload, Unload
├── coordinator.py       2413 Zeilen  – DataUpdateCoordinator, Modbus-Polling, Persist
├── sensor.py            3010 Zeilen  – Alle Sensor-Entities (5 Klassen)
├── const.py             2625 Zeilen  – Sensor-Templates, Konstanten
├── utils.py             2265 Zeilen  – Utilities, generate_sensor_names(), Device-Info
├── config_flow.py       1026 Zeilen  – Config-UI, Options-Flow
├── migration.py         1347 Zeilen  – Migration, Duplikat-Cleanup
├── template_sensor.py    959 Zeilen  – Template-Sensoren (via background task)
├── services.py           749 Zeilen  – HA-Services (Modbus-Lesen/Schreiben)
├── number.py             587 Zeilen  – Number-Entities (Heizkurven)
├── modbus_utils.py       518 Zeilen  – Modbus-Hilfsfunktionen mit Retry-Logik
├── climate.py            245 Zeilen  – Climate-Entities
├── module_auto_detect.py 179 Zeilen  – Automatische Modul-Erkennung
├── reset_manager.py      150 Zeilen  – Zyklischer Reset (täglich, 2h, 4h, monatlich)
├── automations.py         87 Zeilen  – Signal-Konstanten (größtenteils deprecated)
├── cycling_sensor.py       0 Zeilen  – Leer (Geisterdatei)
├── const_mapping.py      176 Zeilen  – Zustandsmappings (Enum-artig)
└── const_migration.py    188 Zeilen  – Migrations-Versionierung
```

**Gesamtumfang:** ~16.900 Zeilen Python-Code (~725 KB)

### 3.2 Datenfluss

```
Home Assistant Core
        │
        ▼
  async_setup_entry()                          [__init__.py]
        │
        ├─► LambdaDataUpdateCoordinator        [coordinator.py]
        │         │
        │         ├─► AsyncModbusTcpClient (pymodbus)
        │         ├─► cycle_energy_persist.json (lokale Persistenz)
        │         └─► 30s Poll → _async_update_data() → coordinator.data
        │
        ├─► Platform SENSOR                    [sensor.py]
        │         ├─► LambdaSensor             (CoordinatorEntity + RestoreEntity)
        │         ├─► LambdaCyclingSensor      (RestoreEntity)
        │         ├─► LambdaEnergyConsumptionSensor (RestoreEntity)
        │         ├─► LambdaCOPSensor          (RestoreEntity)
        │         └─► LambdaTemplateSensor     (via background task)
        │
        ├─► Platform CLIMATE                   [climate.py]
        │         └─► LambdaClimateEntity      (CoordinatorEntity)
        │
        ├─► Platform NUMBER                    [number.py]
        │         └─► LambdaHeatingCurveNumber (RestoreNumber)
        │
        └─► ResetManager                       [reset_manager.py]
```

### 3.3 Device-Hierarchie

```
Lambda WP (Hauptgerät)
├── HP1, HP2, HP3   (1–3 Wärmepumpen, Basis-Adresse 1000/1100/1200)
├── Boil1–Boil5     (1–5 Boiler, Basis-Adresse 2000–2400)
├── Buff1–Buff5     (0–5 Puffer, Basis-Adresse 3000–3400)
├── Sol1–Sol2       (0–2 Solar, Basis-Adresse 4000–4100)
└── HC1–HC12        (1–12 Heizkreise, Basis-Adresse 5000–6100)
```

Jedes Sub-Device referenziert das Hauptgerät via `via_device`. Die Haupt-Sensoren (`SENSOR_TYPES`) werden **zuerst** registriert, damit das Hauptgerät in der Device-Registry existiert bevor Sub-Devices darauf verweisen.

### 3.4 Unique-ID-Generierung

Alle `entity_id`- und `unique_id`-Werte werden zentral durch `generate_sensor_names()` in [utils.py](../../custom_components/lambda_heat_pumps/utils.py) erzeugt:

```python
# Legacy-Modus:
unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
# Beispiel: "eu08l_hp1_flow_line_temperature"

# Standard-Modus:
unique_id = f"{device_prefix}_{sensor_id}"
# Beispiel: "hp1_flow_line_temperature"
```

---

## 4. Qualitätsbewertung

### 4.1 Stabilität: 5/10

Im Normalbetrieb ist die Integration grundsätzlich stabil. Das zentrale Problem ist der Reload-Bug (Kapitel 4), der zu inkonsistenten Zuständen in der Entity-Registry führt. Weitere Stabilitätsrisiken:

- Race Condition beim Hintergrund-Setup von Template-Sensoren
- Potential-Reload-Schleife durch background_auto_detect()
- Fragile Timing-Abhängigkeit: `asyncio.sleep(0.05)` für Device-Registry-Registrierung

### 4.2 Wartbarkeit: 4/10

Die Dateigröße ist das größte Wartbarkeitsproblem:

| Datei | Zeilen | Problem |
|---|---|---|
| sensor.py | 3.010 | `async_setup_entry()` allein: ~700 Zeilen |
| coordinator.py | 2.413 | Eine Klasse mit ~50 Methoden |
| utils.py | 2.265 | ~40 freie Funktionen ohne klare Gruppierung |

Eine einzelne `async_setup_entry()`-Funktion in sensor.py erstellt Sensoren aller Typen (General, HP, Boil, HC, Buff, Sol, Cycling, Energy, COP, Template). Das macht Unit-Tests faktisch unmöglich.

### 4.3 Codequalität: 6/10

**Positiv:**
- Konsistente Verwendung des CoordinatorEntity-Patterns
- Zentralisierte unique_id-Generierung via `generate_sensor_names()`
- Modbus-Lock verhindert Transaction-ID-Konflikte
- Retry-Logik und Timeout in modbus_utils.py

**Negativ:**
- ~130 f-String-Logging-Aufrufe (HA-Konvention: `%s`-Formatierung)
- ~136 Emoji-Zeichen in Log-Nachrichten (`🔄`, `✅`, `❌`)
- `self._unique_id` UND `self._attr_unique_id` gleichzeitig gesetzt (redundant)
- Fehlende Typ-Annotationen für viele Funktionssignaturen
- `global _reload_in_progress` als Modul-Variable, nicht per Config-Entry

---

## 5. Kritischer Bug: Duplizierte Entities mit `_2`-Suffix

### 4.1 Symptom

Nach einem Reload der Integration entstehen Entities mit angehängtem `_2`-Suffix:

```
sensor.eu08l_hp1_operating_state     ← Original (bleibt)
sensor.eu08l_hp1_operating_state_2   ← Duplikat (entsteht)
```

Home Assistant hängt dieses Suffix automatisch an, wenn eine Entity mit einer bereits vergebenen `entity_id` registriert wird. Die vorhandene `async_remove_duplicate_entity_suffixes()`-Funktion in [migration.py](../../custom_components/lambda_heat_pumps/migration.py) kann Entities nachträglich bereinigen, verhindert aber nicht die Entstehung.

### 4.2 Wurzelursache 1: Template-Task wird nicht beim Unload abgebrochen

**Ort:** [sensor.py](../../custom_components/lambda_heat_pumps/sensor.py), Zeile ~807

```python
# Aktueller Code (fehlerhaft):
async def setup_templates():
    try:
        await setup_template_sensors(hass, entry, async_add_entities)
    except Exception as e:
        _LOGGER.error("Error setting up template sensors: %s", e)

hass.async_create_task(setup_templates())
# ↑ Task wird gestartet, aber NICHT gespeichert und beim Unload NICHT abgebrochen
```

**Problem:** Wenn ein Reload stattfindet während dieser Task noch läuft, ruft der alte Task `async_add_entities()` auf. Kurz darauf ruft auch das neue Setup `async_add_entities()` auf. Beide versuchen Entities mit denselben `entity_id`s zu registrieren → HA hängt `_2` an.

### 4.3 Wurzelursache 2: Auto-Detection-Loop erzeugt mehrfache Reloads

**Ort:** [__init__.py](../../custom_components/lambda_heat_pumps/__init__.py), Zeile ~149–179

```python
async def background_auto_detect():
    await asyncio.sleep(38)          # Warte 38 Sekunden
    # ...
    updated = await update_entry_with_detected_modules(hass, entry, detected)
    # update_entry_with_detected_modules() ruft intern auf:
    # hass.config_entries.async_update_entry(entry, data=...)
    # → triggert update_listener → async_reload_entry()
    # → neues Setup startet → startet ERNEUT background_auto_detect()
```

**Problem:** Wenn zwei Tasks parallel laufen (alter Task noch aktiv, neuer Task bereits gestartet), können beide ein Config-Update auslösen → doppelter Reload.

Zusätzlich ist das `is_reload`-Flag fehlerhaft:
```python
# Zeile ~149 – immer True, da hass.data bereits am Anfang von async_setup_entry gesetzt wird:
is_reload = hass.data.get(DOMAIN, {}).get(entry.entry_id) is not None
```

### 4.4 Wurzelursache 3: Cleanup läuft vor Platform-Setup

**Ort:** [__init__.py](../../custom_components/lambda_heat_pumps/__init__.py), Zeile ~258–262

```python
# Falsche Reihenfolge:
await async_remove_duplicate_entity_suffixes(hass, entry.entry_id)  # ← VORHER
# ...
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)  # ← NACHHER
```

**Problem:** Die Cleanup-Funktion bereinigt Reste aus dem *vorherigen* Setup-Durchlauf, kann aber keine Duplikate verhindern, die im *aktuellen* Durchlauf entstehen. Der Cleanup muss nach dem Platform-Setup laufen.

### 4.5 Wurzelursache 4: Template-Sensoren nicht in PLATFORMS

**Ort:** [__init__.py](../../custom_components/lambda_heat_pumps/__init__.py), Zeile ~43–47

```python
PLATFORMS = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    # Template-Sensoren fehlen hier!
]
```

**Problem:** Template-Sensoren werden direkt aus `sensor.py` via Hintergrund-Task aufgerufen, nicht als eigene Platform registriert. `async_unload_platforms()` entlädt sie deshalb nicht → Geist-Entities nach Reload.

### 4.6 Wurzelursache 5: `unique_id` enthält `name_prefix`

**Ort:** [utils.py](../../custom_components/lambda_heat_pumps/utils.py), Funktion `generate_sensor_names()`

```python
# name_prefix ist Teil der unique_id:
unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
# "eu08l_hp1_operating_state"
```

**Problem:** `unique_id` soll die *persistente Identität* einer Entity repräsentieren und sich nie ändern. Wenn der Benutzer den Gerätenamen in den Config-Optionen ändert (z.B. von `eu08l` auf `lambda1`), erzeugt `generate_sensor_names()` neue unique_ids. Die alten Entities bleiben als Waisenentities in der Registry und können zu `_2`-Konflikten führen.

### 4.7 Kausalitätskette

```
Reload-Trigger (Config-Update ODER HA-Neustart)
        │
        ▼
async_unload_entry()
        ├─► Unload PLATFORMS (SENSOR, CLIMATE, NUMBER) ← Template-Sensoren NICHT
        └─► Hintergrund-Task (setup_templates) läuft WEITER
                │
                ▼
async_setup_entry()
        ├─► async_remove_duplicate_entity_suffixes()  ← zu früh, hilft nicht
        ├─► async_forward_entry_setups()
        │   └─► Neue Entities mit entity_id ohne _2 registriert
        ├─► setup_templates() (neuer Task) → Template-Entities registriert
        └─► Alter setup_templates()-Task endet
            └─► async_add_entities() erneut mit denselben entity_ids
                └─► HA hängt _2 an  ← BUG
```

### 4.8 Empfohlene Korrekturen

#### Fix 1: Template-Task tracken und beim Unload abbrechen

```python
# sensor.py – async_setup_entry():
# Statt:
hass.async_create_task(setup_templates())

# So (Task speichern):
template_task = hass.async_create_task(setup_templates())
hass.data[DOMAIN][entry.entry_id]["_template_setup_task"] = template_task
```

```python
# __init__.py – async_unload_entry() (vor async_unload_platforms ergänzen):
coordinator_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
template_task = coordinator_data.pop("_template_setup_task", None)
if template_task is not None and not template_task.done():
    _LOGGER.debug("Cancelling template setup task for entry %s", entry.entry_id)
    template_task.cancel()
    try:
        await template_task
    except asyncio.CancelledError:
        pass
```

#### Fix 2: Auto-Detection-Loop mit Guard sichern

```python
# __init__.py – background_auto_detect():
async def background_auto_detect():
    try:
        await asyncio.sleep(38)
        # Guard: Prüfe ob Entry noch geladen ist
        if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
            _LOGGER.debug("Entry %s already unloaded, skipping auto-detection", entry.entry_id)
            return
        await wait_for_stable_connection(coordinator)
        detected = await auto_detect_modules(coordinator.client, coordinator.slave_id)
        updated = await update_entry_with_detected_modules(hass, entry, detected)
        if updated:
            _LOGGER.info("Auto-detection: module counts updated, reload triggered")
        # KEIN erneuter background_auto_detect() hier
    except asyncio.CancelledError:
        _LOGGER.debug("Background auto-detection cancelled for entry %s", entry.entry_id)
        raise
```

Den Task ebenfalls in `hass.data` speichern und beim Unload abbrechen (analog Fix 1).

#### Fix 3: Cleanup nach Platform-Setup verschieben

```python
# __init__.py – async_setup_entry():
# VORHER (falsch):
await async_remove_duplicate_entity_suffixes(hass, entry.entry_id)
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

# NACHHER (korrekt):
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
await asyncio.sleep(0.1)  # Kurz warten bis Entity-Registry aktualisiert
await async_remove_duplicate_entity_suffixes(hass, entry.entry_id)
```

#### Fix 4: `unique_id` vom `name_prefix` entkoppeln

```python
# utils.py – generate_sensor_names() – unique_id vom entry_id ableiten:
# Statt:
unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"

# So (entry_id ist UUID und ändert sich nie):
unique_id = f"{entry_id}_{device_prefix}_{sensor_id}"
```

> **Hinweis:** Fix 4 erfordert eine Migration aller vorhandenen Entity-Registry-Einträge
> über das bereits vorhandene Migrationssystem in [migration.py](../../custom_components/lambda_heat_pumps/migration.py).

---

## 6. Vollständige Problemliste nach Schweregrad

### Kritisch

| ID | Status | Beschreibung | Datei | Zeile (ca.) |
|---|---|---|---|---|
| K-01 | ✅ **Behoben** (Release2.3) | Template-Task wird beim Unload abgebrochen – Task-Referenz in `coordinator_data` gespeichert | sensor.py | 807 |
| K-02 | ✅ **Behoben** (Release2.3) | Per-Entry Lock/Flag statt modul-global; auto_detect_task wird beim Unload abgebrochen | __init__.py | 74 |
| K-03 | ✅ **Behoben** (Release2.3) | Zweite `async_remove_duplicate_entity_suffixes`-Bereinigung nach Platform-Setup eingefügt | __init__.py | 262 |

### Hoch

| ID | Status | Beschreibung | Datei | Zeile (ca.) |
|---|---|---|---|---|
| H-01 | ✅ Behoben | ~~`_reload_lock` modul-global~~ → per-Entry-Dicts (K-02) | __init__.py | 40 |
| H-02 | Offen | `unique_id` enthält `name_prefix` → Waisenentities bei Umbenennung | utils.py | generate_sensor_names |
| H-03 | Offen | Template-Sensoren nicht in PLATFORMS → beim Unload nicht entladen | __init__.py | 43 |
| H-04 | ✅ Behoben | ~~`is_reload`-Flag race condition~~ → `_previously_setup_entries` set | __init__.py | 149 |
| H-05 | Offen | `sensor.py` und `coordinator.py` mit >2.400 Zeilen nicht mehr wartbar | sensor.py, coordinator.py | gesamt |

### Mittel

| ID | Status | Beschreibung | Datei |
|---|---|---|---|
| M-01 | Offen | `asyncio.sleep(0.05)` als fragiler Timing-Workaround für Device-Registry | sensor.py |
| M-02 | ✅ Behoben | ~~130 f-String-Logging-Aufrufe~~ → `%s`-Formatierung (124 Stellen in 3 Dateien) | coordinator.py, utils.py |
| M-03 | ✅ Behoben | ~~`self._unique_id` UND `self._attr_unique_id`~~ → nur `_attr_unique_id` | sensor.py |
| M-04 | Offen | `LambdaCyclingSensor` / `LambdaEnergyConsumptionSensor` erben nicht von `CoordinatorEntity` | sensor.py |
| M-05 | ✅ Behoben | ~~`cycling_sensor.py` leer~~ → Datei gelöscht | – |
| M-06 | ✅ Behoben | ~~`global _reload_in_progress`~~ → per-Entry-State (K-02) | __init__.py |
| M-07 | ✅ Behoben | ~~Config-Cache nie invalidiert~~ → Cache-Keys beim Setup entfernt | __init__.py |
| M-08 | ✅ Behoben | ~~`lambda`-Ausdrücke~~ → `os.path.exists`, `shutil.copy2`, `Path.read_text/write_text`, `functools.partial` | utils.py, migration.py |
| M-09 | ✅ Behoben | ~~`async_read_input_registers()` ohne Retry~~ → Lock + Timeout + Retry | modbus_utils.py |

### Niedrig

| ID | Status | Beschreibung | Datei |
|---|---|---|---|
| N-01 | ✅ Behoben | ~~91 Emoji-Zeichen in Log-Nachrichten (`🔄`, `✅`, `❌`) – inkonsistent, schwer grep-bar~~ → entfernt aus __init__, modbus_utils, services, coordinator, utils | überall |
| N-02 | ✅ Behoben | ~~`automations.py` enthält verwaiste Kommentarblöcke und ungenutzte Imports~~ → bereinigt | automations.py |
| N-03 | ✅ Behoben | ~~`_update_yesterday_sensors()` als deprecated markiert aber nicht entfernt~~ → gelöscht | automations.py |
| N-04 | ✅ Behoben | ~~`SCAN_INTERVAL = timedelta(seconds=30)` doppelt definiert~~ → aus `__init__.py` entfernt | __init__.py |
| N-05 | ✅ Behoben | ~~Fehlende Typ-Annotationen~~ → `-> None`/`-> dict`/`-> str` für Coordinator + Sensor Lifecycle-Methoden | sensor.py, coordinator.py |
| N-06 | ✅ Behoben | ~~`_generate_entity_id()` hardcoded `"eu08l"` Fallback~~ → verwendet `self._name_prefix = entry.data.get("name", "eu08l")` | coordinator.py |
| N-07 | ✅ Behoben | ~~`const.py` mit 2.625 Zeilen schwer navigierbar~~ → aufgeteilt in `const_base.py` (266 Z.), `const_sensor.py` (1.904 Z.), `const_calculated_sensors.py` (467 Z.); `const.py` ist Shim | const.py → 3 Module |

---

## 7. Konkrete Code-Verbesserungsbeispiele

### 6.1 Template-Task korrekt abbrechen

```python
# sensor.py – async_setup_entry() (korrigiert):
template_task = hass.async_create_task(setup_templates())
hass.data[DOMAIN][entry.entry_id]["_template_setup_task"] = template_task

# __init__.py – async_unload_entry() (ergänzt):
async def _cancel_background_tasks(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Storniere alle laufenden Hintergrund-Tasks für diesen Entry."""
    coordinator_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    for task_key in ("_template_setup_task", "_auto_detect_task"):
        task: asyncio.Task | None = coordinator_data.pop(task_key, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
```

### 6.2 Reload-Lock pro Config-Entry

```python
# __init__.py – aktuell (problematisch):
_reload_lock = asyncio.Lock()    # Modul-global
_reload_in_progress = False      # Modul-global

# __init__.py – verbessert (pro Entry):
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reload config entry mit per-Entry Lock."""
    entry_data = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    reload_lock: asyncio.Lock = entry_data.setdefault("_reload_lock", asyncio.Lock())

    if reload_lock.locked():
        _LOGGER.warning("Reload bereits aktiv für Entry %s, wird übersprungen", entry.entry_id)
        return True

    async with reload_lock:
        _LOGGER.info("Reload für Entry %s gestartet", entry.entry_id)
        unload_ok = await async_unload_entry(hass, entry)
        if not unload_ok:
            return False
        return await async_setup_entry(hass, entry)
```

### 6.3 Logging-Konvention korrigieren

```python
# Aktuell (verletzt HA-Konvention):
_LOGGER.info(f"🔍 AUTO-DETECT: Background auto-detection started for coordinator_id={id(coordinator)}")
_LOGGER.error(f"SENSOR-CHANGE-DETECTION: Fehler: {e}")

# Korrekt (HA-Standard – String wird nur formatiert wenn Level aktiv):
_LOGGER.info("AUTO-DETECT: Background auto-detection started for coordinator_id=%s", id(coordinator))
_LOGGER.error("SENSOR-CHANGE-DETECTION: Fehler: %s", e, exc_info=True)
```

### 6.4 Redundante unique_id-Zuweisung bereinigen

```python
# Aktuell (doppelt, in LambdaCyclingSensor.__init__):
self._unique_id = unique_id          # Wird in @property referenziert
self._attr_unique_id = unique_id     # HA-Standard-Attribut

@property
def unique_id(self):
    return self._unique_id           # Redundant

# Korrigiert (nur _attr_unique_id reicht):
class LambdaCyclingSensor(RestoreEntity, SensorEntity):
    def __init__(self, ..., unique_id: str, ...):
        self._attr_unique_id = unique_id
        # self._unique_id und @property unique_id entfallen
```

### 6.5 async_add_executor_job mit benannten Funktionen

```python
# Aktuell (lambda ohne Context-Manager, schwer debuggbar):
content = await hass.async_add_executor_job(
    lambda: open(lambda_config_path, "r").read()
)

# Korrekt (benannte Funktion mit Context-Manager):
def _read_config_file() -> str:
    with open(lambda_config_path, encoding="utf-8") as fh:
        return fh.read()

content = await hass.async_add_executor_job(_read_config_file)
```

### 6.6 Config-Cache invalidieren

```python
# utils.py – load_lambda_config() (ergänzt):
async def load_lambda_config(hass: HomeAssistant, invalidate_cache: bool = False) -> dict:
    """Load complete Lambda configuration from lambda_wp_config.yaml."""
    if invalidate_cache:
        hass.data.pop("_lambda_config_cache", None)

    if "_lambda_config_cache" in hass.data:
        return hass.data["_lambda_config_cache"]
    # ... restlicher Ladevorgang ...

# __init__.py – async_setup_entry() (Cache immer invalidieren):
await load_lambda_config(hass, invalidate_cache=True)
```

### 6.7 sensor.py in Factory-Funktionen aufteilen

Die 700-zeilige `async_setup_entry()`-Funktion sollte in benannte Factory-Funktionen aufgeteilt werden:

```python
# Ziel-Struktur für sensor.py:
async def _create_general_sensors(coordinator, entry, ...) -> list[LambdaSensor]: ...
async def _create_subdevice_sensors(coordinator, entry, ...) -> list[LambdaSensor]: ...
async def _create_cycling_sensors(hass, entry, ...) -> tuple[list, dict]: ...
async def _create_energy_sensors(hass, entry, ...) -> list: ...
async def _create_cop_sensors(hass, entry, ...) -> list: ...

async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Koordinierter Setup-Einstiegspunkt."""
    general_sensors = await _create_general_sensors(...)
    async_add_entities(general_sensors, update_before_add=False)
    await asyncio.sleep(0.05)  # Device-Registry stabilisieren

    all_sensors = (
        await _create_subdevice_sensors(...) +
        (await _create_cycling_sensors(...))[0] +
        await _create_energy_sensors(...) +
        await _create_cop_sensors(...)
    )
    async_add_entities(all_sensors, update_before_add=False)

    # Template-Task mit Cancel-Handle
    template_task = hass.async_create_task(_setup_templates(hass, entry, async_add_entities))
    hass.data[DOMAIN][entry.entry_id]["_template_setup_task"] = template_task
```

---

## 8. Priorisierter Umsetzungsfahrplan

### ✅ Phase 1: Kritische Bugfixes — abgeschlossen (Release2.3)

**Ziel:** Den `_2`-Duplikat-Bug beheben. Keine API-Breaking-Changes.

| Prio | Aufgabe | Dateien | Status |
|---|---|---|---|
| 1a | Template-Task tracken + beim Unload abbrechen (→ K-01) | sensor.py, __init__.py | ✅ Erledigt |
| 1b | Cleanup nach Platform-Setup (→ K-03) | __init__.py | ✅ Erledigt |
| 1c | Auto-Detection-Loop via per-Entry Guard sichern (→ K-02) | __init__.py | ✅ Erledigt |
| 1d | `_reload_lock` auf per-Entry umstellen (→ H-01, M-06) | __init__.py | ✅ Erledigt |

### ✅ Phase 2: Stabilisierungsmaßnahmen — abgeschlossen (Release2.3)

**Ziel:** Weitere Stabilitätsrisiken eliminieren.

| Prio | Aufgabe | Dateien | Status |
|---|---|---|---|
| 2a | `is_reload` via `_previously_setup_entries` (→ H-04) | __init__.py | ✅ Erledigt |
| 2b | Auto-Detection-Task beim Unload abbrechen | __init__.py | ✅ Erledigt (Teil von K-02) |
| 2c | Config-Cache bei jedem Setup invalidieren (→ M-07) | __init__.py | ✅ Erledigt |
| 2d | `async_read_input_registers()` mit Lock + Retry + Timeout (→ M-09) | modbus_utils.py | ✅ Erledigt |
| 2e | Leere `cycling_sensor.py` gelöscht (→ M-05) | cycling_sensor.py | ✅ Erledigt |

### Phase 3: Code-Qualität ✅ abgeschlossen (Release2.3)

**Ziel:** Codequalität und HA-Konformität verbessern.

| Prio | Aufgabe | Dateien | Status |
|---|---|---|---|
| 3a | ~~f-String-Logging durch `%s`-Formatierung ersetzen (~130 Stellen) (→ M-02)~~ | coordinator.py, utils.py | ✅ Erledigt |
| 3b | ~~Emoji-Zeichen aus Logging entfernen (~136 Stellen) (→ N-01)~~ | überall | ✅ Erledigt |
| 3c | ~~Doppelte `_unique_id`/`_attr_unique_id`-Zuweisung bereinigen (→ M-03)~~ | sensor.py | ✅ Erledigt |
| 3d | ~~`lambda`-Ausdrücke in `async_add_executor_job()` ersetzen (→ M-08)~~ | utils.py, migration.py | ✅ Erledigt |
| 3e | ~~Deprecated Funktionen in automations.py entfernen (→ N-02, N-03)~~ | automations.py | ✅ Erledigt |
| 3f | ~~`SCAN_INTERVAL`-Doppeldefinition bereinigen (→ N-04)~~ | __init__.py | ✅ Erledigt |
| 3g | ~~`generate_entity_id()` Hardcode-Fallback fixen (→ N-06)~~ | coordinator.py | ✅ Erledigt |
| 3h | ~~Typ-Annotationen für Lifecycle-Methoden ergänzen (→ N-05)~~ | sensor.py, coordinator.py | ✅ Erledigt |

### Phase 4: Architektur-Refactoring (langfristig)

**Ziel:** Langfristige Wartbarkeit durch Strukturverbesserungen.

| Prio | Aufgabe | Dateien | Risiko |
|---|---|---|---|
| 4a | `sensor.py` aufteilen: Factory-Funktionen extrahieren (→ H-05) | sensor.py | Hoch |
| 4b | `coordinator.py` aufteilen: Energy-Logik in eigene Klasse | coordinator.py | Hoch |
| 4c | ~~`const.py` aufteilen nach Modul-Typ (→ N-07)~~ → `const_base.py`, `const_sensor.py`, `const_calculated_sensors.py` | ✅ Erledigt | Mittel |
| 4d | `unique_id` vom `name_prefix` entkoppeln + Migration erstellen (→ H-02) | utils.py, migration.py | Sehr hoch |
| 4e | ~~Typ-Hints für alle Funktionssignaturen ergänzen (→ N-05)~~ | überall | ✅ Erledigt |
| 4f | Unit-Tests für kritische Funktionen (generate_sensor_names, Reload-Logik) | tests/ | Niedrig |

### Empfohlene Prioritätenreihenfolge

```
Phase 1 → Stabile, duplikat-freie Entities
   ↓
Phase 2 → Weitere Stabilitätsverbesserungen
   ↓
Phase 3 → Codequalität auf HA-Standard heben
   ↓
Phase 4 → Architektur für Langzeitwartbarkeit
```

---

## 9. Positive Aspekte der Integration

### 8.1 Korrekter DataUpdateCoordinator-Einsatz
Die Integration verwendet den HA-Standard-`DataUpdateCoordinator` korrekt. Alle Poll-Entitäten erben von `CoordinatorEntity` und empfangen Updates via Callback. Das 30-Sekunden-Polling-Intervall ist via Options konfigurierbar.

### 8.2 Modbus-Lock gegen Transaction-ID-Konflikte
`modbus_utils.py` verwendet einen globalen `asyncio.Lock()` für alle Modbus-Read- und Write-Operationen. Dies verhindert parallele Anfragen, die zu Transaction-ID-Mismatches führen würden – ein häufiges Problem bei pymodbus-basierten Integrationen.

### 8.3 Retry-Logik mit Timeout
`async_read_holding_registers()` implementiert 3 Retry-Versuche mit konfigurierbarem Delay und einem `asyncio.wait_for()`-Timeout. Die Funktion erkennt ob HA gestoppt wird und loggt dann auf DEBUG- statt ERROR-Level.

### 8.4 Batch-Register-Lesen
Der Coordinator sammelt alle benötigten Register-Adressen und liest sie in optimierten Batches. Ein globaler Cache (`_global_register_cache`) verhindert doppelte Lesevorgänge innerhalb eines Update-Zyklus. Ein Fallback schaltet problematische Adressen nach 3 Fehlern auf Einzellesungen um.

### 8.5 Firmware-Versions-Filterung
Sensoren in `const.py` haben ein `firmware_version`-Feld. `get_compatible_sensors()` filtert automatisch inkompatible Sensoren heraus. Das ermöglicht sichere Vorwärtskompatibilität ohne Code-Änderungen.

### 8.6 JSON-Persistenz mit Korruptionstruktur-Reparatur
`cycle_energy_persist.json` speichert Cycling-Zähler, Energiewerte und Sensor-IDs. Der Coordinator repariert korrupte JSON-Dateien durch Regex-basierte Schlüssel-Deduplizierung und erstellt automatisch Backups.

### 8.7 Automatische Modul-Erkennung
`module_auto_detect.py` testet per Modbus-Read welche Geräte-Module vorhanden sind und aktualisiert die Config-Entry entsprechend. Dies vereinfacht die initiale Konfiguration erheblich.

### 8.8 Strukturiertes Migrationssystem
`migration.py` implementiert ein versioniertes Migrationssystem mit Registry-Backups, Rollback-Unterstützung und Section-basierter YAML-Migration. `async_remove_duplicate_entity_suffixes()` ist als Safety-Net auch nach den beschriebenen Fixes weiterhin sinnvoll.

### 8.9 Zentralisierte Namensgenerierung
`generate_sensor_names()` in `utils.py` ist der einzige Punkt für die Erzeugung von `entity_id`, `unique_id` und Anzeigename. Alle Platform-Dateien rufen diese Funktion konsistent auf. Das ist architektonisch der richtige Ansatz – lediglich die Abhängigkeit vom `name_prefix` in der `unique_id` ist das Problem.

---

*Dokument erstellt durch automatisierte Codeanalyse. Alle Zeilenangaben (ca.) beziehen sich auf den Stand des Release2.3-Branches (Commit fcd9a83).*
