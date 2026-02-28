---
title: "Firmware-Einstellung – technische Auswirkungen"
---

# Firmware-Einstellung – technische Auswirkungen

Diese Seite beschreibt, wo die Firmware-Version in der Integration gesetzt wird, wie sie ausgewertet wird und welche Folgen die **initiale Konfiguration** gegenüber einer **späteren Änderung** der Firmware haben.

## Speicherort der Firmware-Version

- **Initiale Konfiguration (Config Flow, Schritt „user“):** Die gewählte Firmware wird nur in den **Optionen** des Eintrags gespeichert (`entry.options["firmware_version"]`). Sie wird bewusst **nicht** in `entry.data` übernommen ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 333–336: `firmware_version` wird aus `user_input` für `data_for_entry` entfernt).
- **Options-Flow (spätere Änderung):** Die Firmware ist im Options-Schema ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 871–877). Beim Speichern werden die Optionen aktualisiert, inkl. `firmware_version`.
- **Reconfigure-Flow:** Beim Neukonfigurieren der Integration wird die Firmware in **`entry.data`** geschrieben ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 689–697). Nach Reconfigure kann die Firmware also in `data` stehen.

Die Auswertung erfolgt einheitlich über die Hilfsfunktionen in [utils.py](custom_components/lambda_heat_pumps/utils.py): zuerst `entry.options`, Fallback `entry.data`, sonst `DEFAULT_FIRMWARE`.

---

## Auswertung im Code

### Konstanten ([const_base.py](custom_components/lambda_heat_pumps/const_base.py))

```text
FIRMWARE_VERSION = {
    "V1.1.0-3K": 8,
    "V0.0.9-3K": 7,
    "V0.0.8-3K": 6,
    "V0.0.7-3K": 5,
    "V0.0.6-3K": 4,
    "V0.0.5-3K": 3,
    "V0.0.4-3K": 2,
    "V0.0.3-3K": 1,
}
```

Jede Firmware-*Zeichenkette* ist einer **numerischen Version** (1–8) zugeordnet. Diese Zahl wird für die Kompatibilitätsprüfung verwendet.

### Abfrage der Firmware

- **`get_firmware_version(entry)`** – liefert die Zeichenkette (z. B. `"V0.0.8-3K"`), u. a. für Anzeige und `device_info`.
- **`get_firmware_version_int(entry)`** – liefert die Zahl (1–8). Wird überall genutzt, wo nach Firmware gefiltert wird.

Reihenfolge: `entry.options` → `entry.data` → `DEFAULT_FIRMWARE`.

### Sensor-Filterung

**`get_compatible_sensors(sensor_templates, fw_version)`** ([utils.py](custom_components/lambda_heat_pumps/utils.py) Zeilen 50–67):

- Ein Sensor-Template wird **einbezogen**, wenn:
  - es ein numerisches `firmware_version` hat und `template["firmware_version"] <= fw_version` ist, **oder**
  - es **kein** numerisches `firmware_version` hat (dann gilt der Sensor für alle Firmware-Versionen).
- Templates mit `firmware_version` **größer** als die konfigurierte Firmware werden **nicht** verwendet.

In den Konstanten ([const_sensor.py](custom_components/lambda_heat_pumps/const_sensor.py), [const_calculated_sensors.py](custom_components/lambda_heat_pumps/const_calculated_sensors.py)) haben die allermeisten Sensoren `"firmware_version": 1`; einzelne können höhere Werte haben (z. B. `firmware_version: 3`). Nur bei höherer konfigurierter Firmware werden diese zusätzlichen Sensoren erzeugt.

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
| **Verlauf/Statistik** | Keine Besonderheit | Keine Migration; bei entfernten Entities bleiben alte IDs ggf. als Waisen im Register, Verlauf bleibt unter alter Entity-ID |

Die technische Grundlage für die Anzeige und Konfiguration der Firmware im UI bildet die gleiche Stelle im Config Flow ([config_flow.py](custom_components/lambda_heat_pumps/config_flow.py) Zeilen 397–398: `firmware_options = list(FIRMWARE_VERSION.keys())` für die Dropdown-Liste; die tatsächlichen Auswirkungen entstehen durch die beschriebene Filterung in Coordinator und allen Plattformen.
