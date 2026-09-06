---
title: "Cycling-Sensoren - Technische Dokumentation"
---

# Cycling-Sensoren - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.2 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Dokumentation beschreibt die technische Implementierung der Cycling-Sensoren in der Lambda Heat Pumps Integration.

## Übersicht

Cycling-Sensoren zählen, wie oft die Wärmepumpe in einen bestimmten Betriebsmodus (Heizen, Warmwasser, Kühlen, Abtauen) gewechselt oder der Kompressor gestartet ist. Betroffene Modi (`CYCLE_MODES` in `const.py`):

- **Heating** (Heizen)
- **Hot Water** (Warmwasser)
- **Cooling** (Kühlen)
- **Defrost** (Abtauen)
- **Compressor Start** (Kompressorstart)

Welche Perioden ein Modus bekommt, ist absichtlich nicht symmetrisch — das
entspricht genau den Entities, die die Integration schon immer angelegt hat,
und eine Änderung würde bestehende Entities verwaisen lassen:

```python
# sensor.py
CYCLE_PERIODS = (PERIOD_TOTAL, PERIOD_DAILY, PERIOD_2H, PERIOD_4H)
COMPRESSOR_START_PERIODS = (*CYCLE_PERIODS, PERIOD_MONTHLY)
```

| Zeitraum | Heating | Hot Water | Cooling | Defrost | Compressor Start |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Total** | x | x | x | x | x |
| **Daily** | x | x | x | x | x |
| **2h** | x | x | x | x | x |
| **4h** | x | x | x | x | x |
| **Monthly** | - | - | - | - | x |
| **Yesterday** | x | x | x | x | x |

„Yesterday" ist keine eigene Periode des Zählers selbst, sondern eine eigene
Sensor-Klasse, die den Tageszähler beim Rollover mitschneidet — siehe unten.

## Architektur

Cycling- und Energie-Zähler sind **dieselbe Klasse**, `LambdaCounterSensor`
(`sensor.py`) — es gibt keine eigene `LambdaCyclingSensor`-Klasse mehr. Was
einen Cycling- von einem Energie-Zähler unterscheidet, ist ausschließlich,
welche `CounterDescription` ihn erzeugt hat (`_cycle_description()` vs.
`_energy_description()`) und auf welches `Totals`-Feld sie zeigt:

```python
# sensor.py
def _cycle_description(mode: str, period: str) -> CounterDescription:
    return CounterDescription(
        key=f"{mode}_cycling_{period}",
        ...
        total=lambda coordinator, index, mode=mode: coordinator.totals[index].cycles.get(mode, 0),
    )
```

```
Coordinator (coordinator.py)
├── _async_fast_poll()  [alle 2 Sekunden]
│     └── _track_cycles(index, operating_state, compressor_running)
├── _async_update_data() [voller Poll, Default 30 Sekunden]
│     └── ruft _track_cycles ebenfalls je HP auf
└── Totals.cycles: dict[mode, int]   [nur seit HA-Start]
        │
        ▼
sensor.py – LambdaCounterSensor
  ├── restauriert eigenen Stand über RestoreSensor
  ├── addiert bei jedem Coordinator-Update die Differenz zu Totals.cycles
  └── setzt sich beim Rollover-Signal seiner Periode auf 0
```

Vollständiger Ablauf mit Diagramm:
[Ablaufdiagramm – Schneller Poll und Flankenerkennung](Ablaufdiagramm.md#6-schneller-poll-und-flankenerkennung).

## Flankenerkennung (`_track_cycles`, `coordinator.py`)

```python
@callback
def _track_cycles(self, index: int, operating_state: int, compressor_running: bool) -> None:
    totals = self.totals[index]

    previous = self._last_operating_state.get(index)
    self._last_operating_state[index] = operating_state
    mode = OPERATING_STATE_MODE.get(operating_state, MODE_STBY)
    if previous is not None and previous != operating_state and mode in CYCLE_MODES:
        totals.cycles[mode] = totals.cycles.get(mode, 0) + 1

    was_running = self._last_compressor_running.get(index)
    self._last_compressor_running[index] = compressor_running
    if was_running is False and compressor_running:
        totals.cycles[MODE_COMPRESSOR_START] = totals.cycles.get(MODE_COMPRESSOR_START, 0) + 1
```

Diese Methode wird **sowohl** vom schnellen Poll (alle 2 Sekunden, liest nur
die Register `HP+3`/`HP+10` direkt) **als auch** vom vollen Poll (alle 30
Sekunden, liest das komplette Modell) mit denselben Argumenten aufgerufen.
Beide teilen sich dieselben `_last_*`-Dicts im Coordinator, ein Ereignis wird
also nie doppelt gezählt — der schnelle Poll schließt nur die Lücke für
Kompressorstarts, die vollständig innerhalb eines 30-Sekunden-Fensters
beginnen und enden.

**Betriebsmodus-Wechsel** braucht einen vorherigen bekannten Zustand
(`previous is not None`) — beim allerersten Poll nach dem Start wird also
kein Zähler erhöht, nur der Ausgangszustand gemerkt.

**Kompressorstart** ist unabhängig vom Betriebsmodus: erkannt wird der
Übergang von `compressor_unit_rating == 0` zu `> 0`, gleich in welchem Modus
die Wärmepumpe gerade läuft.

## `LambdaCounterSensor`: Zähler-Logik

```python
# sensor.py
@callback
def _handle_coordinator_update(self) -> None:
    total = self._total()
    self._value += total - self._counted
    self._counted = total
    super()._handle_coordinator_update()
```

`_value` ist der einzige gespeicherte Zustand — restauriert über
`RestoreSensor`, seit dem letzten Blick auf `Totals` um die Differenz erhöht.
Es gibt keine `increment_cycling_counter()`-Funktion mehr, die die Entity über
den State-Store sucht und per Service-Call aktualisiert; die Entity liest den
Coordinator direkt als Python-Objekt.

## Reset-Logik

Beim Rollover-Signal ihrer Periode (siehe
[Ablaufdiagramm – Perioden-Rollover](Ablaufdiagramm.md#8-perioden-rollover-zähler-reset))
wird `_value` schlicht auf `0.0` gesetzt — bei einem **Tages**-Zähler geht der
zuletzt erreichte Wert vorher an den passenden `YesterdayCycleSensor`:

```python
# sensor.py
@callback
def _handle_rollover(self) -> None:
    if self._yesterday is not None:
        self._yesterday.set_value(self._value)
    self._value = 0.0
    self.async_write_ha_state()
```

`YesterdayCycleSensor` (`sensor.py`) hält selbst keinen laufenden Zähler — er
existiert nur, um den letzten Tageswert bis zum nächsten Rollover
festzuhalten, und wird beim Start ebenfalls über `RestoreSensor`
wiederhergestellt.

## Cycling-Offsets

Offsets für Total-Zähler kommen aus `lambda_wp_config.yaml`
(`cycling_offsets`) und werden **einmalig** beim Hinzufügen der Entity
angewendet — derselbe Mechanismus wie bei Energie-Zählern, siehe
[Offset-System](offset-system.md).

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 1500
    hot_water_cycling_total: -50   # negative Werte sind erlaubt
```

## Unterschiede zu Energie-Zählern

| Aspekt | Cycling-Zähler | Energie-Zähler |
|--------|------------------|-----------------|
| Klasse | `LambdaCounterSensor` | `LambdaCounterSensor` (identisch) |
| Coordinator-Quelle | `Totals.cycles[mode]` | `Totals.electrical[mode]` / `Totals.thermal[mode]` |
| Erhöhung pro Ereignis | +1 pro erkannter Flanke | Delta aus Controller-Register oder externem Zähler |
| Reset-Verhalten | Identisch: `_value = 0.0`, ggf. an Yesterday übergeben | Identisch |
| Yesterday-Sensor | Ja, für `_cycling_daily` | Nein — es gibt kein Energie-Äquivalent mehr |

## Debugging

In Home Assistant: Entwicklertools → Zustände, z. B.
`sensor.eu08l_hp1_heating_cycling_total`. Diagnose-Download (siehe
[Features – Diagnose-Download](features.md#diagnose-download)) enthält
zusätzlich `coordinator.totals`, also die vom Coordinator seit HA-Start
gezählten Rohwerte unabhängig vom Entity-eigenen Restore-Stand.

## Verwandte Dokumentation

- [Features – Cycling- und Energie-Zähler](features.md)
- [Offset-System](offset-system.md)
- [Ablaufdiagramm](Ablaufdiagramm.md)
