---
title: "Reset-Manager - Technische Dokumentation"
---

# Reset-Manager - Technische Dokumentation

Diese Dokumentation beschreibt die zentrale Reset-Logik für alle Sensor-Typen (Cycling und Energy) in der Lambda Heat Pumps Integration.

## Übersicht

Der **ResetManager** ist eine zentrale Klasse, die alle Reset-Automatisierungen für periodische Sensoren verwaltet. Er ersetzt die frühere `setup_cycling_automations()` Funktion und bietet eine einheitliche Schnittstelle für alle Reset-Operationen.

### Vorteile der Zentralisierung

- **Code-Deduplizierung**: Einheitliche Handler-Struktur für Cycling- und Energy-Sensoren
- **Wartbarkeit**: Änderungen an Reset-Logik nur an einem Ort
- **Klarheit**: Funktion heißt nicht mehr "cycling_automations" wenn sie für alle verwendet wird
- **Konsistenz**: Beide Sensor-Typen verwenden die gleiche Handler-Struktur

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    __init__.py                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  async_setup_entry()                                  │  │
│  │    - ResetManager(hass, entry.entry_id)               │  │
│  │    - reset_manager.setup_reset_automations()          │  │
│  │    - Speichere in hass.data                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    reset_manager.py                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ResetManager                                         │  │
│  │    - __init__(hass, entry_id)                         │  │
│  │    - setup_reset_automations()                        │  │
│  │    - _send_reset_signal_async()                       │  │
│  │    - cleanup()                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Dispatcher-Signale)
┌─────────────────────────────────────────────────────────────┐
│                    sensor.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaCyclingSensor                                 │  │
│  │    - _handle_reset() (einheitlich für alle Perioden) │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaEnergyConsumptionSensor                       │  │
│  │    - _handle_reset() (einheitlich)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Implementierung

### 1. ResetManager Klasse

**Datei**: `custom_components/lambda_heat_pumps/reset_manager.py`

```python
class ResetManager:
    """Zentrale Reset-Logik für alle Sensor-Typen und Perioden."""
    
    def __init__(self, hass: HomeAssistant, entry_id: str):
        """Initialize ResetManager."""
        self.hass = hass
        self._entry_id = entry_id
        self._unsub_timers = {}
    
    def setup_reset_automations(self):
        """Richte Reset-Automatisierungen ein."""
        # Daily Reset
        @callback
        def reset_daily(now: datetime) -> None:
            """Reset daily sensors at midnight and update yesterday sensors."""
            _LOGGER.info("Resetting daily sensors at midnight")
            
            # 1. Erst Yesterday-Sensoren auf aktuelle Daily-Werte setzen
            self.hass.async_create_task(
                _update_yesterday_sensors_async(self.hass, self._entry_id)
            )
            
            # 2. Dann Daily-Sensoren auf 0 zurücksetzen
            self.hass.async_create_task(
                self._send_reset_signal_async(SIGNAL_RESET_DAILY)
            )
        
        self._unsub_timers["daily"] = async_track_time_change(
            self.hass, reset_daily, hour=0, minute=0, second=0
        )
        
        # 2h, 4h, Monthly, Yearly ähnlich...
    
    def cleanup(self):
        """Cleanup Reset-Automatisierungen."""
        for period, listener in self._unsub_timers.items():
            if listener:
                listener()
        self._unsub_timers = {}
```

### 2. Initialisierung in __init__.py

**Datei**: `custom_components/lambda_heat_pumps/__init__.py`

```python
# In async_setup_entry()
from .reset_manager import ResetManager

# Set up reset automations using ResetManager
reset_manager = ResetManager(hass, entry.entry_id)
reset_manager.setup_reset_automations()

# Store reset_manager for cleanup
if "lambda_heat_pumps" not in hass.data:
    hass.data["lambda_heat_pumps"] = {}
if entry.entry_id not in hass.data["lambda_heat_pumps"]:
    hass.data["lambda_heat_pumps"][entry.entry_id] = {}
hass.data["lambda_heat_pumps"][entry.entry_id]["reset_manager"] = reset_manager
```

### 3. Cleanup in __init__.py

**Datei**: `custom_components/lambda_heat_pumps/__init__.py`

```python
# In async_unload_entry()
if (
    "lambda_heat_pumps" in hass.data
    and entry.entry_id in hass.data["lambda_heat_pumps"]
    and "reset_manager" in hass.data["lambda_heat_pumps"][entry.entry_id]
):
    reset_manager = hass.data["lambda_heat_pumps"][entry.entry_id]["reset_manager"]
    reset_manager.cleanup()
    del hass.data["lambda_heat_pumps"][entry.entry_id]["reset_manager"]
```

## Reset-Intervalle

Der ResetManager verwaltet folgende Reset-Intervalle:

- **Daily**: Jeden Tag um Mitternacht (00:00:00)
- **2h**: Alle 2 Stunden (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
- **4h**: Alle 4 Stunden (0, 4, 8, 12, 16, 20)
- **Monthly**: 1. des Monats um Mitternacht (00:00:00)
- **Yearly**: 1. Januar um Mitternacht (00:00:00)

Jedes Reset-Intervall sendet ein entsprechendes Dispatcher-Signal:
- `SIGNAL_RESET_DAILY`
- `SIGNAL_RESET_2H`
- `SIGNAL_RESET_4H`
- `SIGNAL_RESET_MONTHLY`
- `SIGNAL_RESET_YEARLY`

## Sensor-Handler: Cycling vs. Energy

**Cycling-Sensoren**: Pro Periode ein **eigener Zähler** (`_cycling_value`). Beim Reset wird der Zähler auf 0 gesetzt. Es gibt keine Differenzberechnung „Anzeige = Total − Yesterday“; daher **kein Konsistenzproblem** (yesterday/previous_* > current) wie bei Energy.

**Energy-Sensoren (Daily/Monthly/Yearly)**: **Ein** Total-Zähler (`_energy_value`), Anzeige = `_energy_value - _yesterday_value` (bzw. `_previous_monthly_value` / `_previous_yearly_value`). Beim Reset wird nur der Basis-Wert (yesterday/previous_*) aktualisiert, nicht `_energy_value`. Damit nach Neustart keine negativen Periodenwerte entstehen, gibt es **Konsistenzprüfungen** (Basis-Wert ≤ energy_value) bei Restore, Persist-Anwendung und Persist-Schreiben. Details: [Reset-Logik und Yesterday-Sensoren](reset-logik-yesterday-sensoren.md#4-konsistenz-yesterdayprevious_-energy_value-nach-neustart).

### Cycling-Sensoren

Cycling-Sensoren verwenden eine **einheitliche `_handle_reset()` Methode** für alle Perioden:

```python
async def _handle_reset(self, entry_id: str):
    """Handle reset signal for all periods (einheitlich, wie Energy)."""
    if entry_id != self._entry.entry_id:
        return
    
    # Prüfe Periode basierend auf sensor_id und reset_interval
    if self._sensor_id.endswith("_daily") and self._reset_interval == "daily":
        self._cycling_value = 0
        self.async_write_ha_state()
    elif self._sensor_id.endswith("_2h") and self._reset_interval == "2h":
        self._cycling_value = 0
        self.async_write_ha_state()
    # ... weitere Perioden
```

**Vorteil**: Statt 5 separater Methoden (`_handle_daily_reset`, `_handle_2h_reset`, etc.) gibt es jetzt nur noch 1 einheitliche Methode.

### Energy-Sensoren

Energy-Sensoren verwenden bereits eine einheitliche `_handle_reset()` Methode (unverändert):

```python
async def _handle_reset(self, entry_id: str):
    """Handle reset signal."""
    if self._reset_interval == "daily" and self._period == "daily":
        # Update _yesterday_value from total sensor
        # ...
    elif self._reset_interval != "total":
        self._energy_value = 0.0
    # ...
```

## Signal-Registrierung

Sensoren registrieren sich weiterhin direkt auf die Dispatcher-Signale:

```python
# In LambdaCyclingSensor.async_added_to_hass()
@callback
def _wrap_reset(entry_id: str):
    self.hass.async_create_task(self._handle_reset(entry_id))

# Registriere für alle Perioden (einheitlicher Wrapper)
self._unsub_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_DAILY, _wrap_reset
)
self._unsub_2h_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_2H, _wrap_reset
)
# ... weitere Perioden
```

**Vorteil**: Statt 5 separater Wrapper-Funktionen gibt es jetzt nur noch 1 einheitliche Wrapper-Funktion.

## Code-Deduplizierung

### Vorher (5 separate Methoden)

```python
async def _handle_daily_reset(self, entry_id: str):
    if entry_id == self._entry.entry_id and self._sensor_id.endswith("_daily"):
        self._cycling_value = 0
        self.async_write_ha_state()

async def _handle_2h_reset(self, entry_id: str):
    if entry_id == self._entry.entry_id and self._sensor_id.endswith("_2h"):
        self._cycling_value = 0
        self.async_write_ha_state()
# ... 3 weitere ähnliche Methoden
```

### Nachher (1 einheitliche Methode)

```python
async def _handle_reset(self, entry_id: str):
    if entry_id != self._entry.entry_id:
        return
    
    if self._sensor_id.endswith("_daily") and self._reset_interval == "daily":
        self._cycling_value = 0
        self.async_write_ha_state()
    elif self._sensor_id.endswith("_2h") and self._reset_interval == "2h":
        self._cycling_value = 0
        self.async_write_ha_state()
    # ... weitere Perioden
```

**Ergebnis**: 5 Methoden → 1 Methode (Code-Deduplizierung)

## Migration von setup_cycling_automations()

Die alte `setup_cycling_automations()` Funktion wurde durch `ResetManager` ersetzt:

### Vorher

```python
# In __init__.py
from .automations import setup_cycling_automations
setup_cycling_automations(hass, entry.entry_id)

# In async_unload_entry()
from .automations import cleanup_cycling_automations
cleanup_cycling_automations(hass, entry.entry_id)
```

### Nachher

```python
# In __init__.py
from .reset_manager import ResetManager
reset_manager = ResetManager(hass, entry.entry_id)
reset_manager.setup_reset_automations()

# In async_unload_entry()
if "reset_manager" in hass.data["lambda_heat_pumps"][entry.entry_id]:
    reset_manager = hass.data["lambda_heat_pumps"][entry.entry_id]["reset_manager"]
    reset_manager.cleanup()
```

## Vorteile

1. **Code-Deduplizierung**: Cycling-Handler von 5 Methoden auf 1 Methode reduziert
2. **Konsistenz**: Beide Sensor-Typen verwenden die gleiche Handler-Struktur
3. **Zentrale Logik**: ResetManager verwaltet alle Reset-Operationen
4. **Klarheit**: Funktion heißt nicht mehr "cycling_automations" wenn sie für alle verwendet wird
5. **Wartbarkeit**: Änderungen an Reset-Logik nur an einem Ort

## Verwandte Dokumentation

- [Reset-Logik und Yesterday-Sensoren](reset-logik-yesterday-sensoren.md) – Details zur Energy-Sensor Reset-Logik inkl. Konsistenz (yesterday/previous_* ≤ energy_value)
- [Energieverbrauchssensoren](energieverbrauchssensoren.md) – Technische Details inkl. Konsistenz-Korrektur bei Restore/Persist
- [Cycling-Sensoren](cycling-sensoren.md) – Details zur Cycling-Sensor Reset-Logik

