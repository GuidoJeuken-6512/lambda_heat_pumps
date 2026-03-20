# Release 2.3.2

> Version 2.3.1 wurde übersprungen.

---

## Verbesserungen

### Flankenerkennung: Sensor für Kompressorstart gewechselt (`4b1dddd`)

Der Sensor zur Erkennung eines Kompressorstarts wurde geändert:

| | Vorher (2.3) | Jetzt (2.3.2) |
|---|---|---|
| **Quelle** | `HP_STATE` (Register 1002) | `compressor_unit_rating` (Register 1010) |
| **Erkennungsbedingung** | Übergang in State `2` (RESTART-BLOCK) | Anstieg von `0 → >0` (Rising Edge) |
| **Semantik** | Zählt abgeschlossene Zyklen (nach Sperrzeit) | Zählt aktive Kompressorstarts (bei Einschaltmoment) |

`compressor_unit_rating` gibt die aktuelle Kompressorleistung in Prozent (0–100 %) zurück. Eine steigende Flanke von 0 auf einen Wert größer 0 zeigt an, dass der Kompressor gerade gestartet hat. Das ist präziser und unabhängiger von internen HP-State-Übergängen.

```
Kompressor aus:  rating = 0
Kompressor an:   rating > 0  ← Flanke hier, Zähler wird inkrementiert
```

---

### Fast Polling für Flankenerkennung (`4b1dddd`)

Die Flankenerkennung wurde aus dem regulären 30-Sekunden-Update herausgelöst und in einen eigenen schnellen Polling-Loop mit **2-Sekunden-Intervall** ausgelagert.

#### Architektur

```
┌──────────────────────────────────────────────────────────┐
│  _async_fast_update()  [alle 2 Sekunden]                 │
│    └─ liest nur Register 1003 + 1010 pro Wärmepumpe     │
│    └─ _run_cycling_edge_detection()                      │
│         └─ increment_cycling_counter()                   │
├──────────────────────────────────────────────────────────┤
│  _async_update_data()  [alle 30 Sekunden, konfigurierbar]│
│    └─ vollständiger Modbus-Read aller Register           │
│    └─ Energieintegration (kWh) — keine Flankenerkennung  │
└──────────────────────────────────────────────────────────┘
```

#### Warum Fast Polling?

Kurze Betriebsmodüs-Übergänge (z. B. kurze Abtauphasen oder schnell wechselnde Starts) konnten im 30-Sekunden-Raster übersehen werden. Mit 2-Sekunden-Polling wird jede Flanke zuverlässig erfasst und die stündlichen Sensoren sind genauer.

#### Was wird im Fast Poll gelesen?

Pro Wärmepumpe werden nur **zwei Register** gelesen:

| Register | Adresse | Inhalt | Verwendung |
|----------|---------|--------|------------|
| `HP_OPERATING_STATE` | 1003 | Betriebsmodus (Heizen/WW/Kühlen/Abtauen) | Modus-Flankenerkennung |
| `compressor_unit_rating` | 1010 | Kompressorleistung in % | Kompressorstart-Erkennung |

#### Neue Konstante

```python
DEFAULT_FAST_UPDATE_INTERVAL = 2  # Sekunden
```

Das Intervall ist fest konfiguriert und nicht über die UI einstellbar.

#### Kollisionsschutz mit Vollupdate

Ein `_full_update_running`-Flag verhindert, dass der Fast Poll einen laufenden 30-Sekunden-Vollupdate stört:

```python
self._full_update_running = False  # True während _async_update_data die Modbus-Verbindung hält
self._unsub_fast_poll = None       # Handle zum Abmelden des Fast-Poll-Timers
```

---

## Interne Refactorings

### `_run_cycling_edge_detection()` als eigene Methode

Die Flankenerkennung wurde in die dedizierte Methode `_run_cycling_edge_detection()` ausgelagert. Sie wird ausschließlich von `_async_fast_update()` aufgerufen und aktualisiert `_last_operating_state` sowie `_last_compressor_rating`.

### `_last_state` umbenannt in `_last_compressor_rating`

Das interne State-Tracking-Dictionary für den Kompressorstart wurde von `_last_state` in `_last_compressor_rating` umbenannt, um den neuen Sensor (`compressor_unit_rating`) semantisch korrekt zu spiegeln.

```python
# Vorher
self._last_state = {}  # HP_STATE Flankenerkennung

# Nachher
self._last_compressor_rating = {}  # compressor_unit_rating Flankenerkennung (0 → >0)
```
