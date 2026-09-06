---
title: "Firmware-Einstellung – technische Auswirkungen"
---

# Firmware-Einstellung – technische Auswirkungen

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Seite beschreibt, wo die Firmware-Version gespeichert wird, wie sie
ausgewertet wird und welche Sensoren davon abhängen.

## Speicherort: nur noch `entry.data`

Die Firmware landet ausschließlich in `entry.data[CONF_FIRMWARE_VERSION]` —
egal ob beim ersten Einrichten (`config_flow.py::async_step_user`) oder bei
einer späteren Änderung über den **Reconfigure**-Flow
(`async_step_reconfigure`). Beide Schritte teilen sich dasselbe
`CONNECTION_SCHEMA`, das die Firmware-Auswahl enthält.

**Es gibt keinen Weg mehr, die Firmware über die Integrations-Optionen zu
ändern** — `LambdaOptionsFlow` (`config_flow.py`) fragt Setpoints, Features
und Polling ab, aber keine Firmware. Wer die Firmware ändern will, muss die
Integration **rekonfigurieren** (Einstellungen → Integrationen → Lambda Heat
Pumps → Neu konfigurieren), nicht die Optionen öffnen. Das beseitigt die
frühere Unklarheit, ob der Wert gerade in `options` oder in `data` steht.

## Auswertung: `firmware.py`

```python
def firmware_level(entry) -> int:
    """The version ordinal of the firmware this entry is configured for."""
    name = entry.data.get(CONF_FIRMWARE_VERSION)
    firmware = FIRMWARE_CONFIG.get(name)
    return int(firmware["version"]) if firmware else 1
```

Ein unbekannter Firmware-Name (z. B. eine Entry, die von einer neueren
Integrationsversion geschrieben wurde) fällt auf `1` zurück — die älteste,
von jedem Controller garantiert bediente Registerkarte, nicht auf die neueste.

`FIRMWARE_CONFIG` (`const.py`) ordnet jedem Firmware-Namen sowohl die
Versions-Ordinalzahl als auch die Standard-Register-Reihenfolge zu (siehe
[Register-Reihenfolge](register-reihenfolge-int32.md)):

```python
FIRMWARE_CONFIG: Final[dict[str, dict[str, Any]]] = {
    "V1.1.0-3K": {"version": 9, "reg_order": "low_first"},
    "V0.0.9-3K": {"version": 7, "reg_order": "high_first"},
    # ...
    "V0.0.3-3K": {"version": 1, "reg_order": "high_first"},
}
```

## Sensor-Filterung: `serves()`

Jede `LambdaSensorDescription` (`sensor.py`) trägt optional
`firmware_version` (ab dieser Version) oder `firmware_versions` (exakte,
eventuell lückenhafte Menge). `firmware.py::serves()` entscheidet:

```python
def serves(description, level: int) -> bool:
    if description.firmware_versions is not None:
        return level in parse_firmware_versions(description.firmware_versions)
    if description.firmware_version is not None:
        return description.firmware_version <= level
    return True
```

Ein Sensor ganz ohne Deklaration gilt für jede Firmware. Beispiel für eine
Ausnahme (Außentemperatur nur bis einschließlich Firmware 7 lesbar):

```python
_temperature("ambient_temperature", firmware_versions=("1-7",)),
```

## Wo gefiltert wird

| Komponente | Filtert nach Firmware? |
|---|---|
| `sensor.py::async_setup_entry` | Ja — `level = firmware_level(entry)`, dann `serves(description, level)` für Controller-, Modul- und Capacity-Limit-Sensoren |
| `climate.py::async_setup_entry` | Nein — Thermostate hängen nur von den Optionen ab (Raumthermostat/Kühlung aktiviert), nicht von der Firmware |
| `number.py::async_setup_entry` | Nein — Heizkurven-Einstellungen sind reine Integrations-Werte, keine Register |
| `lambda_modbus`-Modell (`async_setup`) | Nein, aber unabhängig relevant: probt zusätzlich, welche Register der **konkrete** Controller tatsächlich beantwortet, unabhängig von der konfigurierten Firmware (siehe [Ablaufdiagramm](Ablaufdiagramm.md#3-coordinator-initialisierung-_async_setup)) |

Ein Sensor entsteht also nur, wenn **beide** Filter ihn durchlassen: die
konfigurierte Firmware muss ihn laut `serves()` kennen, **und** der Controller
muss beim Setup tatsächlich auf sein Register geantwortet haben. Das sind zwei
unabhängige Mechanismen — der eine ist eine Behauptung über die Firmware, der
andere eine Beobachtung am realen Gerät.

## Auswirkung einer Firmware-Änderung

Weil eine Firmware-Änderung nur über den Reconfigure-Flow möglich ist und
dieser die Entry per `async_update_reload_and_abort` immer neu lädt, gibt es
nur noch **einen** Ablauf, nicht mehr getrennte Fälle für „initiale
Konfiguration“ und „spätere Änderung“:

1. `async_unload_entry` entlädt alle Plattformen; die Verbindung schließt über
   `entry.async_on_unload`.
2. `async_setup_entry` läuft komplett neu: Module werden erneut geprobt,
   `firmware_level(entry)` liest die neue Firmware, alle Plattformen bauen
   ihre Entity-Listen ausschließlich mit den dazu kompatiblen Sensoren neu auf.

**Firmware-Erhöhung:** mehr Sensoren werden kompatibel, neue Entities
entstehen. **Firmware-Absenkung:** nicht mehr kompatible Entities werden beim
Unload entfernt; ihre `unique_id` bleibt in der Entity-Registry als „verwaist“
zurück, Verlaufsdaten bleiben unter der alten `entity_id` in der
Recorder-Datenbank erhalten, aber für die neue Konfiguration nicht mehr
sichtbar. Es findet keine automatische Migration von Entity-IDs oder
Verlaufsdaten beim Firmware-Wechsel statt.
