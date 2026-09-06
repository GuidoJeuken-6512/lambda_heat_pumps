---
title: "Energieverbrauchssensoren - Technische Dokumentation"
---

# Energieverbrauchssensoren - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Dokumentation beschreibt die technische Implementierung der Energieverbrauchssensoren (elektrisch und thermisch) in der Lambda Heat Pumps Integration.

## Übersicht

Die Integration bietet zwei Arten von Energiezählern, nach Betriebsart und
Zeitraum aufgeteilt:

1. **Elektrisch** (`{mode}_energy_{period}`): Stromverbrauch, aus
   `compressor_power_consumption_accumulated` oder einem externen Zähler.
2. **Thermisch** (`{mode}_thermal_energy_{period}`): Wärmeabgabe, aus
   `compressor_thermal_energy_output_accumulated` oder einem externen Zähler.

Beide sind Instanzen derselben Klasse wie die Cycling-Zähler,
`LambdaCounterSensor` (`sensor.py`) — siehe
[Cycling-Sensoren – Architektur](cycling-sensoren.md#architektur) für den
Teil, der beiden gemeinsam ist. Diese Seite beschreibt den Teil, der nur für
Energie gilt: wie der Coordinator die Deltas ermittelt und welchem Modus er
sie zuordnet.

## Perioden

```python
# sensor.py
ENERGY_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_MONTHLY, PERIOD_YEARLY)
HEATING_ENERGY_PERIODS = (*ENERGY_PERIODS, PERIOD_HOURLY)  # nur "heating"
```

Anders als bei Cycling-Zählern gibt es **kein** `2h`/`4h` für Energie, und
**kein** Yesterday-Äquivalent — der Tageswert wird beim Rollover einfach auf
0 zurückgesetzt, ohne dass ein Vortageswert irgendwo aufbewahrt wird (siehe
[Reset-Logik und Yesterday-Sensoren](reset-logik-yesterday-sensoren.md)).
`hourly` existiert ausschließlich für `heating` (Debug-Zweck).

## Betriebsmodus-Zuordnung

```python
# const.py
ELECTRICAL_ENERGY_MODES: Final = (MODE_HEATING, MODE_HOT_WATER, MODE_COOLING, MODE_DEFROST, MODE_STBY)
THERMAL_ENERGY_MODES: Final = (MODE_HEATING, MODE_HOT_WATER, MODE_COOLING, MODE_DEFROST)
```

**Elektrisch** wird auch im Standby gebucht — eine Wärmepumpe verbraucht auch
im Leerlauf Strom (Steuerung, Frostschutz). **Thermisch** nicht: eine
Wärmepumpe erzeugt im Standby keine Wärme, also gibt es keinen
`stby_thermal_energy_*`-Sensor.

## Delta-Ermittlung (`coordinator.py`)

```python
@callback
def _track_energy(self, index: int) -> None:
    heat_pump = self.component("hp", index)
    if (operating_state := heat_pump.operating_state) is None:
        return
    mode = OPERATING_STATE_MODE.get(int(operating_state), MODE_STBY)

    totals = self.totals[index]
    for kind, thermal, register, modes, bucket in (
        ("electrical", False, heat_pump.compressor_power_consumption_accumulated, ELECTRICAL_ENERGY_MODES, totals.electrical),
        ("thermal", True, heat_pump.compressor_thermal_energy_output_accumulated, THERMAL_ENERGY_MODES, totals.thermal),
    ):
        reading = self._meter_reading(index, thermal) or register
        delta = self._energy_delta(index, kind, reading)
        if delta and mode in modes:
            bucket[mode] = bucket.get(mode, 0.0) + delta
```

`_track_energy` läuft **nur** im vollen Poll (alle 30 Sekunden), nicht im
schnellen 2-Sekunden-Poll — anders als Cycling-Flanken kann ein
Energie-Delta nicht "verpasst" werden, es summiert sich einfach bis zum
nächsten vollen Poll auf.

### Externer Zähler statt Controller-Register (`_meter_reading`)

```python
def _meter_reading(self, index: int, thermal: bool) -> float | None:
    entity_id = self.file_config.meter(index, thermal)
    if entity_id is None:
        return None
    state = self.hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None  # nichts buchen, NICHT auf das Register zurückfallen
    value = float(state.state)
    unit = state.attributes.get("unit_of_measurement")
    factor = {"Wh": 1.0, "kWh": 1000.0, "MWh": 1_000_000.0}.get(unit)
    if factor is None:
        return None  # unbekannte Einheit, Warnung geloggt
    return value * factor
```

Ist in `lambda_wp_config.yaml` (`energy_consumption_sensors`) ein externer
Zähler konfiguriert und dessen State gültig, wird **er** verwendet — nicht
zusätzlich zum Register, sondern anstelle davon. Ist der State gerade
`unknown`/`unavailable`, wird für diesen Poll **nichts** gebucht; es wird
nicht auf das Controller-Register umgeschaltet, das etwas anderes misst und
beim Wiedererscheinen des externen Zählers sonst einen Sprung erzeugen würde.

### Delta-Validierung (`_energy_delta`)

```python
def _energy_delta(self, index: int, kind: str, reading: float | None) -> float:
    if reading is None or reading <= 0:
        return 0.0
    current = reading / _WH_PER_KWH
    previous = self._last_energy.get((index, kind))
    self._last_energy[(index, kind)] = current
    if previous is None:
        return 0.0  # erste Ablesung: nur Baseline setzen
    delta = current - previous
    if delta < 0 or delta > MAX_ENERGY_DELTA_KWH:
        return 0.0  # Zähler zurückgesetzt/getauscht, oder unplausibler Sprung
    return delta
```

`MAX_ENERGY_DELTA_KWH` (100 kWh, `const.py`) ist die Obergrenze für das, was
ein **einzelner Poll** legitimerweise addieren kann. Ein größerer Sprung wird
verworfen und nur geloggt, statt die Zähler zu verfälschen.

## `LambdaCounterSensor`: Von Total abgeleitet

Wie bei Cycling-Zählern addiert `_handle_coordinator_update` die Differenz
zum Coordinator-Total seit dem letzten Blick:

```python
@callback
def _handle_coordinator_update(self) -> None:
    total = self._total()          # coordinator.totals[index].electrical[mode] o.ä.
    self._value += total - self._counted
    self._counted = total
    super()._handle_coordinator_update()
```

Es gibt keinen separaten `_energy_value`, der vom angezeigten `native_value`
abweicht — beides ist `_value`, nur für die Anzeige gerundet (siehe
[Reset-Logik und Yesterday-Sensoren](reset-logik-yesterday-sensoren.md) für
den Grund, warum das die frühere Fehlerklasse rund um Restore/Persistenz
strukturell ausschließt).

## Konfiguration: externer Quellsensor

```yaml
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"   # elektrisch
    thermal_sensor_entity_id: "sensor.waermemesser_hp1"        # optional, thermisch
```

Details zur Datei und Validierung: [modbus_wp_config.yaml](modbus-wp-config.md).

## Energie-Offsets

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 5000.0
    heating_thermal_energy_total: 6500.0
```

Anwendung und Mechanik: [Offset-System](offset-system.md) (identisch zu
Cycling-Offsets, nur mit `float`-Werten in kWh).

## Zusammenfassung

- **Ein** Zähler-Delta pro Poll und Energieart, aus Controller-Register oder
  externem Zähler.
- Sicherheitsnetze gegen Zählerreset/-tausch (`delta < 0`) und unplausible
  Sprünge (`delta > 100 kWh`).
- Kein separates Yesterday-/Previous-Konzept mehr — Perioden-Reset setzt
  einfach auf 0.
- Dieselbe Sensor-Klasse wie Cycling-Zähler, derselbe Offset-Mechanismus.

## Betroffene Dateien

| Datei | Rolle |
|---|---|
| `coordinator.py` | `_track_energy()`, `_meter_reading()`, `_energy_delta()`, `Totals` |
| `sensor.py` | `LambdaCounterSensor`, `_energy_description()` |
| `config_file.py` | `LambdaFileConfig.meter()`, `.offset()` |

## Siehe auch

- [Cycling-Sensoren](cycling-sensoren.md) – gemeinsame Zähler-Architektur
- [COP-Sensoren](cop-sensoren.md) – nutzen dieselben Zähler als Quelle
- [Sensoren-Übersicht](sensoren-uebersicht.md)
