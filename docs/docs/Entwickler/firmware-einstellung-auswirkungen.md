---
title: "Firmware-Einstellung – technische Auswirkungen"
---

# Firmware-Einstellung – technische Auswirkungen

*Zuletzt geändert am 25.07.2026*

Diese Seite beschreibt, wo die Firmware-Version in der Integration gesetzt wird, wie sie ausgewertet wird und welche Folgen die **initiale Konfiguration** gegenüber einer **späteren Änderung** der Firmware haben.

## Speicherort der Firmware-Version

- **Initiale Konfiguration (Config Flow, Schritt „user“):** Die gewählte Firmware wird nur in den **Optionen** des Eintrags gespeichert (`entry.options["firmware_version"]`). Sie wird bewusst **nicht** in `entry.data` übernommen ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 333–336: `firmware_version` wird aus `user_input` für `data_for_entry` entfernt).
- **Options-Flow (spätere Änderung):** Die Firmware ist im Options-Schema ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 871–877). Beim Speichern werden die Optionen aktualisiert, inkl. `firmware_version`.
- **Reconfigure-Flow:** Beim Neukonfigurieren der Integration wird die Firmware in **`entry.data`** geschrieben ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 689–697). Nach Reconfigure kann die Firmware also in `data` stehen.

Die Auswertung erfolgt einheitlich über die Hilfsfunktionen in [utils.py](custom_components/lambda_heat_pumps/utils.py): zuerst `entry.options`, Fallback `entry.data`, sonst `DEFAULT_FIRMWARE`.

---

## Auswertung im Code

### Konstanten ([const_base.py](custom_components/lambda_heat_pumps/const_base.py))

Seit V2.7.0 ist `FIRMWARE_CONFIG` die Primärstruktur und trägt **zwei** von der Firmware-Zeichenkette abhängige Werte: die numerische Version (Kompatibilitätsprüfung, siehe unten) **und** den Default für `int32_register_order` (`reg_order`). `FIRMWARE_VERSION` wird automatisch davon abgeleitet und bleibt für alle bestehenden Aufrufer unverändert nutzbar:

```python
FIRMWARE_CONFIG: dict = {
    "V1.1.0-3K":  {"version": 9, "reg_order": "low_first"},
    "V0.0.10-3K": {"version": 8, "reg_order": "low_first"},
    "V0.0.9-3K":  {"version": 7, "reg_order": "high_first"},
    # ...
    "V0.0.3-3K":  {"version": 1, "reg_order": "high_first"},
}
FIRMWARE_VERSION: dict = {k: v["version"] for k, v in FIRMWARE_CONFIG.items()}
```

Jede Firmware-*Zeichenkette* ist einer **numerischen Version** (aktuell 1–9) zugeordnet. Diese Zahl wird für die Kompatibilitätsprüfung verwendet.

### Register-Reihenfolge für 32-Bit-Werte (`int32_register_order`) — ebenfalls firmware-abhängig

Seit V2.7.0 ist nicht nur die Sensor-*Verfügbarkeit* firmware-abhängig, sondern auch die **Interpretation** der bereits vorhandenen int32-Sensoren (z. B. Energie-Akkumulation): `get_int32_register_order(hass, entry)` ([modbus_utils.py](custom_components/lambda_heat_pumps/modbus_utils.py)) liest den `reg_order`-Wert aus `FIRMWARE_CONFIG[fw_version]` als Default, sofern kein manueller `int32_register_order`-Override in `lambda_wp_config.yaml` gesetzt ist (Priorität: YAML-Override > FW-Default > absoluter Fallback `"high_first"`).

Der Wert wird **einmalig beim Setup** ausgelesen und in `coordinator._int32_register_order` gespeichert ([__init__.py](custom_components/lambda_heat_pumps/__init__.py)) — **nicht** bei jedem Update-Zyklus neu. Das heißt aber auch: Ein Reload (z. B. durch Ändern der Firmware-Version im Options-Flow, siehe unten) wertet den FW-Default **neu** aus. Details zur Prioritätskette und den beiden 32-Bit-Reihenfolgen: [Register-Reihenfolge int32](register-reihenfolge-int32.md).

**Wichtige Konsequenz beim Firmware-Wechsel:** Ändert sich durch den neuen `fw_version` der `reg_order`-Default (z. B. bei einem Wechsel zwischen den beiden neuesten und einer älteren Firmware-Version, siehe Tabelle oben), werden bestehende int32-Sensoren ab dem Reload **anders interpretiert** — ohne dass sich am Gerät etwas geändert hat. Das kann bei Energie-Zählern zu einem scheinbaren Sprung führen. Der in [Release 2.8.0](../Releases/release-2-8-0.md) eingeführte `calculate_energy_delta()`-Schutz (verwirft implausible Deltas über `MAX_ENERGY_DELTA_WH` statt sie zu kappen und einzubuchen) fängt genau diesen Fall ab.

### Abfrage der Firmware

- **`get_firmware_version(entry)`** – liefert die Zeichenkette (z. B. `"V0.0.8-3K"`), u. a. für Anzeige und `device_info`.
- **`get_firmware_version_int(entry)`** – liefert die Zahl (1–8). Wird überall genutzt, wo nach Firmware gefiltert wird.

Reihenfolge: `entry.options` → `entry.data` → `DEFAULT_FIRMWARE`.

### Sensor-Filterung

**`get_compatible_sensors(sensor_templates, fw_version)`** ([utils.py](custom_components/lambda_heat_pumps/utils.py)), seit V2.8.0 mit zwei Feldern pro Template (Priorität von hoch nach niedrig):

1. **`firmware_versions`** (Range-Notation, neu in V2.8.0): Liste aus `"X-Y"` (Bereich inklusive), `"-X"` (Version X ausschließen) oder `X` (einzelne Version einschließen), ausgewertet über `_parse_firmware_versions()`. Erlaubt — anders als `firmware_version` — auch eine **Obergrenze**, z. B. `["1-7"]` für ein Register, das ab einer neueren Steuerungsgeneration nicht mehr existiert (siehe `ambient_temperature` in [const_sensor.py](custom_components/lambda_heat_pumps/const_sensor.py) und [Release 2.8.0](../Releases/release-2-8-0.md)).
2. **`firmware_version`** (Minimum, bestehendes Verhalten): Sensor aktiv, wenn `template["firmware_version"] <= fw_version`.
3. **Kein Feld**: Sensor gilt für alle Firmware-Versionen.

`firmware_versions` hat Vorrang vor `firmware_version`, falls beide gesetzt sind. Vollständig rückwärtskompatibel — bestehende `firmware_version: X`-Sensoren sind unverändert.

In den Konstanten ([const_sensor.py](custom_components/lambda_heat_pumps/const_sensor.py), [const_calculated_sensors.py](custom_components/lambda_heat_pumps/const_calculated_sensors.py)) haben die allermeisten Sensoren `"firmware_version": 1`; einzelne können höhere Werte oder (seit V2.8.0) `firmware_versions`-Bereiche haben.

**Wichtig — General Sensors (`SENSOR_TYPES`):** Bis einschließlich V2.7.0 wurde diese Sensorgruppe **nirgends** durch `get_compatible_sensors()` gefiltert — weder in `sensor.py` (Entity-Erzeugung) noch in `coordinator.py` (`_read_general_sensors_batch`). Ein `firmware_version`/`firmware_versions`-Feld bei einem General Sensor hatte dadurch **nie** eine Wirkung. Seit V2.8.0 ist das behoben; die Tabelle unten ist entsprechend aktuell.

### Sentinel-Filterung als ergänzender Schutz

Unabhängig von der FW-Filterung schützt seit V2.8.0 `is_sentinel_value()` ([utils.py](custom_components/lambda_heat_pumps/utils.py)) vor Lambda-Protokoll-Sentinel-Rohwerten (`0x8000` = Register nicht vorhanden, `-3000` als `int16` = Fühler nicht angeschlossen), die sonst unskaliert als reale Messwerte gespeichert würden. Ein optionales `sentinel_values`-Feld im Template aktiviert zusätzlich `-1` (`0xFFFF`) als Sentinel für einen einzelnen Sensor — global ist `-1` bewusst **kein** Sentinel, da er bei manchen Sensoren (z. B. Temperatur-Offsets) ein gültiger Wert ist. Details: [Release 2.8.0](../Releases/release-2-8-0.md).

---

## Wo die Firmware-Version verwendet wird

| Komponente | Verwendung |
|------------|------------|
| **Coordinator** | Beim Aufbau der Register-/Sensor-Mappings ([coordinator.py](custom_components/lambda_heat_pumps/coordinator.py) Zeilen 1317–1343) und in `_async_update_data` (Zeilen 1527–1545): `get_firmware_version_int(entry)` und `get_compatible_sensors(...)` für HP, Boil, Buff, Sol, HC. Nur zu den kompatiblen Sensoren gehörende Register werden gelesen. |
| **Sensor-Plattform** | [sensor.py](custom_components/lambda_heat_pumps/sensor.py) Zeilen 108–113: `fw_version = get_firmware_version_int(entry)`; es werden nur Entities für Sensoren aus `get_compatible_sensors(...)` erstellt. |
| **Climate-Plattform** | [climate.py](custom_components/lambda_heat_pumps/climate.py) Zeilen 191–194: gleiche Logik – nur kompatible Climate-Templates. |
| **Template-Sensoren** | [template_sensor.py](custom_components/lambda_heat_pumps/template_sensor.py) Zeilen 79–82: Filterung nach Firmware-Version. |
| **Migration/Cleanup** | [migration.py](custom_components/lambda_heat_pumps/migration.py) nutzt `get_firmware_version_int` für kompatible Sensoren. |
| **device_info** | [utils.py](custom_components/lambda_heat_pumps/utils.py) `build_device_info`: `model` wird mit `get_firmware_version(entry)` (Zeichenkette) gesetzt. |
| **32-Bit-Register-Reihenfolge** | [modbus_utils.py](custom_components/lambda_heat_pumps/modbus_utils.py) `get_int32_register_order(hass, entry)`: FW-abhängiger `reg_order`-Default aus `FIRMWARE_CONFIG[fw_version]` (seit V2.7.0), sofern kein YAML-Override gesetzt ist. Einmalig beim Setup ausgewertet, siehe unten. |

---

## Initiale Konfiguration

- Der Nutzer wählt im Config Flow eine Firmware aus der Liste `FIRMWARE_VERSION.keys()` ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 397–398, 266).
- Beim Erstellen des Eintrags landet die Firmware nur in **options**.
- Beim ersten `async_setup_entry` lesen alle Plattformen und der Coordinator die Firmware aus den Optionen (über `get_firmware_version_int(entry)`) und erstellen ausschließlich zu dieser Version passende Entities bzw. Register-Zuordnungen.
- **Effekt:** Von Anfang an existieren nur Sensoren/Climate-Entities, die zur gewählten Firmware passen; es werden nur die zugehörigen Modbus-Register gelesen.

---

## Spätere Änderung der Firmware

### Über den Options-Flow

- Nutzer ändert unter „Optionen“ der Integration die Firmware und speichert.
- `entry.options["firmware_version"]` wird aktualisiert.
- Der **Update-Listener** löst `async_reload_entry` aus ([__init__.py](custom_components/lambda_heat_pumps/__init__.py) Zeile 319).
- **Ablauf:**
  1. `async_unload_entry`: Alle Plattformen (Sensor, Climate, etc.) und der Coordinator werden entladen, Entities entfernt.
  2. `async_setup_entry`: Setup läuft erneut; `get_firmware_version_int(entry)` liefert die **neue** Firmware.
  3. Alle Plattformen und der Coordinator bauen ihre Listen ausschließlich mit `get_compatible_sensors(..., fw_version)` für die neue Version auf.

**Folgen:**

- **Firmware-Erhöhung (z. B. 1 → 6):** Es werden **mehr** Sensoren/Register kompatibel. Es entstehen **neue** Entities; ggf. erscheinen neue Entity-IDs (und bei bereits belegten IDs im Entity-Register z. B. Suffixe wie `_2`).
- **Firmware-Absenkung (z. B. 6 → 1):** Sensoren mit `firmware_version` > 1 werden aus der Liste gestrichen. Die zugehörigen Entities werden beim Unload **entfernt**. Die alten Entity-IDs können im Entity-Register als „verwaist“ (restored) zurückbleiben; die zugehörigen Verlaufsdaten bleiben in der Recorder-Datenbank unter der alten Entity-ID, sind aber für die neue Konfiguration nicht mehr sichtbar.
- **Register-Reihenfolge (`int32_register_order`):** Ändert der Firmware-Wechsel auch den `reg_order`-Default (siehe oben), werden bestehende int32-Sensoren ab dem Reload anders interpretiert - ohne YAML-Override. Betroffene Energie-Zähler können dadurch einen scheinbaren Sprung zeigen; der `calculate_energy_delta()`-Schutz (Release 2.8.0) verwirft diesen statt ihn einzubuchen.

Es findet **keine** automatische Migration von Entity-IDs oder Verlaufsdaten beim Firmware-Wechsel statt.

### Über den Reconfigure-Flow

- Beim Rekonfigurieren wird die Firmware in **`entry.data`** geschrieben und der Eintrag per `async_reload` neu geladen.
- Danach greifen `get_firmware_version` / `get_firmware_version_int` wegen der Fallback-Reihenfolge (options vor data) weiterhin zuerst auf `entry.options` zu. Wenn options unverändert bleiben, kann die neue Firmware aus `data` erst nach einer Options-Anpassung oder wenn options leer sind wirksam werden. In der Praxis wird nach Reconfigure oft die Integration neu gesetzt; dann sind die gleichen inhaltlichen Auswirkungen wie bei der Options-Änderung zu erwarten (Reload, Neuaufbau der Entities nach neuer Firmware).

---

## Kurzüberblick

| Aspekt | Initiale Konfiguration | Spätere Änderung (Options) |
|--------|-------------------------|----------------------------|
| **Speicherort** | Nur `entry.options` | `entry.options` aktualisiert |
| **Wann wirksam** | Beim ersten Setup | Nach Speichern der Optionen und Reload |
| **Entities** | Nur zur gewählten Firmware passend | Beim Reload komplett neu aufgebaut; je nach Richtung (Hoch/Runter) neue oder weniger Entities |
| **Modbus** | Nur Register für kompatible Sensoren | Nach Reload nur noch Register für die neue Firmware |
| **Register-Reihenfolge (int32)** | FW-abhängiger `reg_order`-Default aus `FIRMWARE_CONFIG` (seit V2.7.0) | Wird beim Reload neu ausgewertet — kann bestehende int32-Sensoren anders interpretieren (siehe Folgen oben) |
| **Verlauf/Statistik** | Keine Besonderheit | Keine Migration; bei entfernten Entities bleiben alte IDs ggf. als Waisen im Register, Verlauf bleibt unter alter Entity-ID |

Die technische Grundlage für die Anzeige und Konfiguration der Firmware im UI bildet die gleiche Stelle im Config Flow ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 397–398: `firmware_options = list(FIRMWARE_VERSION.keys())` für die Dropdown-Liste; die tatsächlichen Auswirkungen entstehen durch die beschriebene Filterung in Coordinator und allen Plattformen.
