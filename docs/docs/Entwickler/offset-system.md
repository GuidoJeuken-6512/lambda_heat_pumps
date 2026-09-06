---
title: "Offset-System"
---

# Offset-System – Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Das Offset-System erlaubt, historische Zählerstände beim Austausch einer
Wärmepumpe oder nach einem Zählerreset nahtlos fortzuführen. Anders als vor
3.5 gibt es dafür nur noch **einen** Mechanismus, nicht zwei getrennte für
Cycling- und Energie-Sensoren — beide sind heute Instanzen derselben Klasse.

## Ein Mechanismus für beide Zähler-Arten

`LambdaCounterSensor` (`sensor.py`) ist sowohl die Cycling- als auch die
Energie-Zähler-Klasse. Ihre Offset-Logik läuft einmalig beim Hinzufügen zu
Home Assistant, ausschließlich für `*_total`-Sensoren:

```python
# sensor.py – LambdaCounterSensor._apply_offset()
def _apply_offset(self) -> None:
    if self.entity_description.period != PERIOD_TOTAL:
        return
    offset = self.coordinator.file_config.offset(
        self._index, self.entity_description.key
    )
    self._value += offset - self._applied_offset
    self._applied_offset = offset
```

Wie bei jedem `RestoreSensor` wird `_applied_offset` als State-Attribut
persistiert und beim Neustart zurückgelesen — es wird also bei jedem Start nur
die **Differenz** zum zuletzt angewendeten Offset addiert, nie der volle Wert
erneut.

## Welcher Konfigurationsschlüssel gilt

`LambdaFileConfig.offset()` (`config_file.py`) entscheidet anhand des
Sensor-Schlüssels, in welchem der beiden Abschnitte der
`lambda_wp_config.yaml` nachgeschaut wird:

```python
# config_file.py
def offset(self, index: int, key: str) -> float:
    offsets = (
        self.cycling_offsets
        if key.endswith("_cycling_total")
        else self.energy_offsets
    )
    return float(offsets.get(f"hp{index}", {}).get(key, 0.0))
```

| Sensor-Schlüssel endet auf | Abschnitt in `lambda_wp_config.yaml` | Werttyp |
|---|---|---|
| `_cycling_total` | `cycling_offsets` | Integer (Zyklen) |
| alles andere `_total` (`_energy_total`, `_thermal_energy_total`) | `energy_consumption_offsets` | Float (kWh) |

Details zur Datei selbst: [modbus_wp_config.yaml](modbus-wp-config.md).

## Beispiel

| Ereignis | `_value` | `_applied_offset` | konfigurierter Offset | Differenz |
|---|---:|---:|---:|---:|
| Erststart, Offset = 1500 | 0 → **1500** | 0 → 1500 | 1500 | +1500 |
| HA-Neustart, Offset unverändert | 1500 (restauriert) | 1500 (restauriert) | 1500 | 0 – kein Effekt |
| Offset auf 1600 geändert | 1500 → **1600** | 1500 → 1600 | 1600 | +100 |

## Was daraus entfallen ist

Es gibt keine separaten Funktionen `_apply_cycling_offset()` /
`_apply_energy_offset()` mehr und keine `increment_cycling_counter()` /
`increment_energy_consumption_counter()` in einem `utils.py` — die Zählung
selbst läuft heute im Coordinator (`_track_cycles`/`_track_energy`, siehe
[Ablaufdiagramm](Ablaufdiagramm.md)) und kennt keinen Offset; der Offset wird
ausschließlich beim Hinzufügen der Entity angewendet, wie oben gezeigt.
`disabled_registers`, `sensors_names_override` und die alte
`modbus`-Sektion der Config-Datei haben mit dem Offset-System nichts zu tun
und existieren als YAML-Abschnitte ohnehin nicht mehr (siehe
[modbus_wp_config.yaml](modbus-wp-config.md)).

## Betroffene Dateien

| Datei | Rolle |
|---|---|
| `sensor.py` | `LambdaCounterSensor._apply_offset()`, `extra_state_attributes` |
| `config_file.py` | `LambdaFileConfig.offset()`, YAML-Schema und -Template |
| `lambda_wp_config.yaml` | Konfigurationsdatei (Laufzeit) |
