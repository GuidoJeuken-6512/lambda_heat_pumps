---
title: "Reset-Logik und Yesterday-Sensoren - Technische Dokumentation"
---

# Reset-Logik und Yesterday-Sensoren - Technische Dokumentation

Diese Dokumentation beschreibt die technische Implementierung der Reset-Logik für Energieverbrauchssensoren (Daily, Monthly, Yearly) und die Yesterday-Wert-Verwaltung in der Lambda Heat Pumps Integration.

## Übersicht

Die Integration verwendet eine spezielle Reset-Logik für periodische Sensoren (Daily, Monthly, Yearly), die auf **Differenzberechnung** basiert statt auf einfachem Zurücksetzen auf 0. Dies ermöglicht kontinuierliche Tracking und korrekte Berechnung auch nach Neustarts.

### Konzept

**Differenzberechnung statt Reset auf 0:**

- **Total-Sensor**: Speichert den kumulativen Gesamtwert (`_energy_value`)
- **Daily-Sensor**: Berechnet `daily_value = _energy_value - _yesterday_value`
- **Monthly-Sensor**: Berechnet `monthly_value = _energy_value - _previous_monthly_value`
- **Yearly-Sensor**: Berechnet `yearly_value = _energy_value - _previous_yearly_value`

**Vorteile:**
- Kontinuierliches Tracking ohne Datenverlust
- Robustheit bei Neustarts
- Korrekte Berechnung auch wenn Reset-Signale verspätet ankommen
- Einfache Initialisierung beim Start

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    reset_manager.py                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ResetManager                                         │  │
│  │    - setup_reset_automations()                        │  │
│  │      ├─ reset_daily() (Mitternacht)                   │  │
│  │      ├─ reset_monthly() (1. des Monats)               │  │
│  │      └─ reset_yearly() (1. Januar)                    │  │
│  │    - _send_reset_signal_async()                       │  │
│  │      - Sendet Reset-Signale via async_dispatcher_send │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  automations.py                                       │  │
│  │  _update_yesterday_sensors_async()                   │  │
│  │    - Aktualisiert Yesterday-Sensoren (Cycling)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Dispatcher-Signale)
┌─────────────────────────────────────────────────────────────┐
│                    sensor.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaEnergyConsumptionSensor                        │  │
│  │    - _handle_reset()                                  │  │
│  │    - _initialize_daily_yesterday_value()              │  │
│  │    - _yesterday_value (für Daily)                     │  │
│  │    - _previous_monthly_value (für Monthly)            │  │
│  │    - _previous_yearly_value (für Yearly)              │  │
│  │    - native_value (berechnet Differenz)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    utils.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  increment_energy_consumption_counter()               │  │
│  │    - Liest _energy_value direkt (nicht State!)        │  │
│  │    - Aktualisiert alle Perioden gleichzeitig          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Reset-Intervalle

### Daily Reset (Täglich)

**Zeitpunkt**: Jeden Tag um Mitternacht (00:00:00)

**Ablauf** (Reihenfolge garantiert):
1. **Zuerst** wird `_update_yesterday_sensors_async` ausgeführt und **abgewartet** (Yesterday-Sensoren erhalten die aktuellen Daily-Werte).
2. **Danach** wird `SIGNAL_RESET_DAILY` gesendet.
3. Alle Daily-Cycling- und Daily-Energy-Sensoren empfangen das Signal.
4. Bei Energy: `_handle_reset()` ruft `apply_energy_period_reset()` auf, `_yesterday_value` wird auf den Total-Wert gesetzt; `_energy_value` bleibt unverändert.
5. Bei Cycling: Daily-Zähler wird auf 0 gesetzt.

**Code** (`reset_manager.py`):
```python
@callback
def reset_daily(now: datetime) -> None:
    """Reset daily sensors at midnight after updating yesterday sensors."""
    _LOGGER.info("Resetting daily sensors at midnight")

    async def _daily_reset_sequence() -> None:
        await _update_yesterday_sensors_async(self.hass, self._entry_id)
        await self._send_reset_signal_async(SIGNAL_RESET_DAILY)

    self.hass.async_create_task(_daily_reset_sequence())
```

### Monthly Reset (Monatlich)

**Zeitpunkt**: 1. des Monats um Mitternacht (00:00:00)

**Ablauf**:
1. Reset-Signal senden: `SIGNAL_RESET_MONTHLY`
2. Alle Monthly-Energy-Sensoren empfangen Signal
3. `_handle_reset()` wird aufgerufen
4. `_previous_monthly_value` wird auf aktuellen Total-Wert gesetzt
5. `_energy_value` bleibt unverändert

**Code** (`reset_manager.py`):
```python
@callback
def reset_monthly(now: datetime) -> None:
    """Reset monthly sensors on the 1st of each month."""
    if now.day == 1:
        _LOGGER.info("Resetting monthly sensors (cycling, energy) on 1st of month")
        self.hass.async_create_task(
            self._send_reset_signal_async(SIGNAL_RESET_MONTHLY)
        )
```

### Yearly Reset (Jährlich)

**Zeitpunkt**: 1. Januar um Mitternacht (00:00:00)

**Ablauf**:
1. Reset-Signal senden: `SIGNAL_RESET_YEARLY`
2. Alle Yearly-Energy-Sensoren empfangen Signal
3. `_handle_reset()` wird aufgerufen
4. `_previous_yearly_value` wird auf aktuellen Total-Wert gesetzt
5. `_energy_value` bleibt unverändert

**Code** (`reset_manager.py`):
```python
@callback
def reset_yearly(now: datetime) -> None:
    """Reset yearly sensors on January 1st."""
    if now.month == 1 and now.day == 1:
        _LOGGER.info("Resetting yearly sensors on January 1st")
        self.hass.async_create_task(
            self._send_reset_signal_async(SIGNAL_RESET_YEARLY)
        )
```

Monthly- und Yearly-Reset sind in `_handle_reset()` über `apply_energy_period_reset(self, self._period)` (utils.py) implementiert; dabei werden `_previous_monthly_value` bzw. `_previous_yearly_value` aus dem Total-Sensor gesetzt.

### Hourly Reset (Stündlich, nur Energy Debug)

**Zeitpunkt**: Jede volle Stunde. Nur für Heating Energy Hourly (Debug-Sensor). Ablauf wie bei Daily/Monthly/Yearly: `apply_energy_period_reset(self, "hourly")` setzt `_last_hour_value` aus dem Total-Sensor.

## Implementierung

### 1. Reset-Handler (`_handle_reset`)

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`

**Methode**: `LambdaEnergyConsumptionSensor._handle_reset()`

**Ablauf** (aktueller Code):
- Für **daily, hourly, monthly, yearly**: Aufruf von `apply_energy_period_reset(self, self._period)` (utils.py). Diese Funktion setzt den jeweiligen Basis-Wert (`_yesterday_value`, `_last_hour_value`, `_previous_monthly_value`, `_previous_yearly_value`) aus dem Total-Sensor und synchronisiert `_energy_value` mit dem Total-Wert. **`_energy_value` wird nicht auf 0 gesetzt**, sondern weiterhin von `increment_energy_consumption_counter` erhöht.
- Für **2h, 4h**: `_energy_value` wird auf 0 gesetzt (eigenständige Zähler pro Fenster).
- Total-Sensoren reagieren nicht auf Reset-Signale.

**Kritischer Punkt** (Daily/Monthly/Yearly/Hourly):
- `_energy_value` wird **nicht** auf 0 gesetzt
- Nur der Basis-Wert (yesterday/previous_*) wird aktualisiert
- `_energy_value` wird weiterhin von `increment_energy_consumption_counter` erhöht

### 2. Berechnung (`native_value`)

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`

**Property**: `LambdaEnergyConsumptionSensor.native_value`

**Implementierung**:

```python
@property
def native_value(self) -> float:
    """Return the current value based on period."""
    if self._period == "total":
        return self._energy_value
    elif self._period == "daily":
        # Daily = Total - Yesterday
        daily_value = self._energy_value - self._yesterday_value
        return max(0.0, daily_value)  # Clamp to 0
    elif self._period == "monthly":
        # Monthly = Total - Previous Monthly
        monthly_value = self._energy_value - self._previous_monthly_value
        return max(0.0, monthly_value)  # Clamp to 0
    elif self._period == "yearly":
        # Yearly = Total - Previous Yearly
        yearly_value = self._energy_value - self._previous_yearly_value
        return max(0.0, yearly_value)  # Clamp to 0
    else:
        return self._energy_value
```

**Beispiel-Berechnung**:

1. **Vor Mitternacht**:
   - `_energy_value = 100.0 kWh`
   - `_yesterday_value = 0.0 kWh`
   - `native_value = 100.0 - 0.0 = 100.0 kWh` ✅

2. **Nach Mitternacht-Reset**:
   - `_yesterday_value = 100.0 kWh` (wird aktualisiert)
   - `_energy_value = 100.0 kWh` (bleibt unverändert)
   - `native_value = 100.0 - 100.0 = 0.0 kWh` ✅

3. **Nach neuem Energieverbrauch**:
   - `_energy_value = 102.0 kWh` (wird erhöht)
   - `_yesterday_value = 100.0 kWh` (bleibt unverändert)
   - `native_value = 102.0 - 100.0 = 2.0 kWh` ✅

### 3. Initialisierung beim Start (`_initialize_daily_yesterday_value`)

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`

**Methode**: `LambdaEnergyConsumptionSensor._initialize_daily_yesterday_value()`

**Zweck**: Initialisiert Yesterday-Werte für Daily-Sensoren beim Start der Integration, falls Home Assistant nicht 24h durchläuft (z.B. Dev-Instanzen).

**Ablauf**:

```python
async def _initialize_daily_yesterday_value(self):
    """Initialisiere Yesterday-Wert für Daily-Sensoren beim Start."""
    # Finde Total-Sensor
    total_entity_id = self.entity_id.replace("_daily", "_total")
    total_state = self.hass.states.get(total_entity_id)
    
    if total_state:
        total_value = float(total_state.state)
        current_daily = self._energy_value - self._yesterday_value
        
        # Korrigiere Yesterday-Wert wenn notwendig
        if self._yesterday_value == 0.0 and total_value > 0:
            # Yesterday = 0, aber Total > 0 → setze Yesterday auf Total
            self._yesterday_value = total_value
        elif current_daily < 0:
            # Daily-Wert negativ → korrigiere Yesterday
            self._yesterday_value = self._energy_value
        elif current_daily > total_value * 1.1:
            # Daily-Wert größer als Total (unmöglich) → korrigiere Yesterday
            self._yesterday_value = self._energy_value - total_value
```

**Aufruf**:

```python
async def async_added_to_hass(self):
    """Initialize the sensor when added to Home Assistant."""
    await super().async_added_to_hass()
    
    # Restore state
    last_state = await self.async_get_last_state()
    await self.restore_state(last_state)
    
    # Für Daily-Sensoren: Initialisiere Yesterday-Wert beim Start
    if self._period == "daily" and self._reset_interval == "daily":
        import asyncio
        await asyncio.sleep(0.1)  # 100ms Verzögerung für Total-Sensor-Laden
        await self._initialize_daily_yesterday_value()
```

### 4. Kritische Behebung: `_energy_value` vs `native_value`

**Problem**: `increment_energy_consumption_counter` las den aktuellen Wert aus `state_obj.state` (dem berechneten `native_value`) statt aus `_energy_value`.

**Folge**: Nach Mitternacht-Reset:
- `_energy_value = 100 kWh`
- `_yesterday_value = 100 kWh`
- `native_value = 100 - 100 = 0 kWh` ✅ (korrekt)
- Wenn `increment_energy_consumption_counter` aufgerufen wird:
  - Liest: `current_value = state_obj.state = 0.0` ❌ (falsch!)
  - Berechnet: `new_value = 0.0 + delta = delta` ❌
  - Setzt: `_energy_value = delta` ❌ (sollte `100 + delta` sein!)

**Lösung** (`utils.py`):

```python
# Finde die Entity-Instanz ZUERST (vor der current_value Berechnung)
energy_entity = None
try:
    for entry_id, comp_data in hass.data.get("lambda_heat_pumps", {}).items():
        if isinstance(comp_data, dict) and "energy_entities" in comp_data:
            energy_entity = comp_data["energy_entities"].get(entity_id)
            if energy_entity:
                break
except Exception as e:
    _LOGGER.debug(f"Error searching for energy entity {entity_id}: {e}")

# Hole aktuellen Wert des Sensors
# WICHTIG: Für Daily/Monthly/Yearly-Sensoren muss _energy_value direkt gelesen werden,
# nicht der berechnete native_value (State), da native_value = _energy_value - _yesterday_value
if energy_entity is not None and hasattr(energy_entity, "_energy_value"):
    # Verwende _energy_value direkt (korrekt für alle Perioden)
    current_value = energy_entity._energy_value
else:
    # Fallback: Verwende State (nur wenn Entity nicht gefunden wurde)
    # Für Total-Sensoren ist das OK, da native_value = _energy_value
    current_value = float(state_obj.state)
```

**Ergebnis**: `increment_energy_consumption_counter` liest jetzt `_energy_value` direkt von der Entity, nicht aus dem State.

### 5. Persistierung

**Yesterday-Werte werden in `extra_state_attributes` gespeichert**:

```python
@property
def extra_state_attributes(self):
    """Return extra state attributes."""
    attrs = {
        "sensor_type": "energy_consumption",
        "mode": self._mode,
        "period": self._period,
        "hp_index": self._hp_index,
    }
    
    # Füge Yesterday-Werte für Daily/Monthly/Yearly-Sensoren hinzu (für Persistierung)
    if self._period == "daily":
        attrs["yesterday_value"] = round(self._yesterday_value, 2)
        attrs["current_daily_value"] = round(self._energy_value - self._yesterday_value, 2)
    elif self._period == "monthly":
        attrs["previous_monthly_value"] = round(self._previous_monthly_value, 2)
    elif self._period == "yearly":
        attrs["previous_yearly_value"] = round(self._previous_yearly_value, 2)
    
    return attrs
```

**Wiederherstellung** (`restore_state`):

- Bei Daily/Monthly/Yearly wird **nicht** `_energy_value = last_state.state` gesetzt (State ist der Anzeigewert, nicht der Total). Stattdessen werden `energy_value` und `yesterday_value` bzw. `previous_monthly_value` / `previous_yearly_value` aus den Attributen gelesen; falls `energy_value` fehlt (Migration), werden Werte aus dem Total-Sensor abgeleitet.
- **Konsistenzprüfung** am Ende des Daily-/Monthly-/Yearly-Blocks: Ist der Basis-Wert (yesterday/previous_monthly/previous_yearly) größer als `_energy_value`, wird er auf `_energy_value` gesetzt (Korrektur + Log-Warnung). Siehe Abschnitt „Konsistenz (yesterday/previous_* ≤ energy_value)“.

## Signal-Registrierung

### Signal-Handler

**Datei**: `custom_components/lambda_heat_pumps/sensor.py`

**Registrierung** (`async_added_to_hass`):

```python
from .automations import SIGNAL_RESET_DAILY, SIGNAL_RESET_2H, SIGNAL_RESET_4H, SIGNAL_RESET_MONTHLY, SIGNAL_RESET_YEARLY

@callback
def _wrap_reset(entry_id: str):
    self.hass.async_create_task(self._handle_reset(entry_id))

if self._reset_interval == "daily":
    self._unsub_dispatcher = async_dispatcher_connect(
        self.hass, SIGNAL_RESET_DAILY, _wrap_reset
    )
elif self._reset_interval == "monthly":
    self._unsub_dispatcher = async_dispatcher_connect(
        self.hass, SIGNAL_RESET_MONTHLY, _wrap_reset
    )
elif self._reset_interval == "yearly":
    self._unsub_dispatcher = async_dispatcher_connect(
        self.hass, SIGNAL_RESET_YEARLY, _wrap_reset
    )
```

### Signal-Definitionen

**Datei**: `custom_components/lambda_heat_pumps/automations.py`

```python
SIGNAL_RESET_DAILY = "lambda_heat_pumps_reset_daily"
SIGNAL_RESET_2H = "lambda_heat_pumps_reset_2h"
SIGNAL_RESET_4H = "lambda_heat_pumps_reset_4h"
SIGNAL_RESET_MONTHLY = "lambda_heat_pumps_reset_monthly"
SIGNAL_RESET_YEARLY = "lambda_heat_pumps_reset_yearly"
```

## Datenfluss

### Beispiel: Daily-Sensor über 24 Stunden

**Tag 1 (vor Mitternacht)**:
1. Start: `_energy_value = 0 kWh`, `_yesterday_value = 0 kWh`
2. Energieverbrauch: `increment_energy_consumption_counter()` → `_energy_value = 50 kWh`
3. `native_value = 50 - 0 = 50 kWh` ✅

**Tag 1 → Tag 2 (Mitternacht-Reset)**:
1. Automation: `reset_daily_sensors()` wird aufgerufen
2. Signal: `SIGNAL_RESET_DAILY` wird gesendet
3. Handler: `_handle_reset()` wird aufgerufen
4. Update: `_yesterday_value = 50 kWh` (aus Total-Sensor)
5. `_energy_value = 50 kWh` (bleibt unverändert)
6. `native_value = 50 - 50 = 0 kWh` ✅

**Tag 2 (nach Mitternacht)**:
1. Energieverbrauch: `increment_energy_consumption_counter()` → `_energy_value = 52 kWh`
2. `native_value = 52 - 50 = 2 kWh` ✅

**Tag 2 → Tag 3 (Mitternacht-Reset)**:
1. Automation: `reset_daily_sensors()` wird aufgerufen
2. Update: `_yesterday_value = 52 kWh`
3. `_energy_value = 52 kWh` (bleibt unverändert)
4. `native_value = 52 - 52 = 0 kWh` ✅

## Fehlerbehandlung

### 1. Total-Sensor nicht gefunden

**Fallback**: Verwendet `_energy_value` direkt:

```python
if total_state:
    self._yesterday_value = float(total_state.state)
else:
    # Fallback: Verwende aktuellen _energy_value
    self._yesterday_value = self._energy_value
```

### 2. Initialisierung bei Dev-Instanzen

**Problem**: Home Assistant läuft nicht 24h durch, Yesterday-Werte werden nicht aktualisiert.

**Lösung**: `_initialize_daily_yesterday_value()` korrigiert Yesterday-Werte beim Start:

- Wenn `yesterday_value = 0` aber `total > 0`: Setze `yesterday = total` (oder aus angezeigtem Wert ableiten)
- Wenn `daily < 0`: Korrigiere `yesterday_value = energy_value` (Konsistenz, siehe Abschnitt 4)
- Wenn `daily > total * 1.1`: Korrigiere Yesterday
- Nach Korrektur wird `set_energy_persist_dirty()` aufgerufen, damit die korrigierten Werte beim nächsten Zyklus in `cycle_energy_persist.json` gespeichert werden

### 3. Division durch Null Schutz

**Berechnung**: `daily_value = _energy_value - _yesterday_value`

**Schutz**: `max(0.0, daily_value)` verhindert negative Werte.

### 4. Konsistenz (yesterday/previous_* ≤ energy_value) nach Neustart

**Problem**: Nach Neustart können persistierte Daten (Recorder oder `cycle_energy_persist`) inkonsistent sein: `yesterday_value` bzw. `previous_monthly_value` / `previous_yearly_value` sind größer als `energy_value`. Dann wäre der Periodenwert (daily = energy_value − yesterday_value usw.) negativ.

**Lösung in der Implementierung** (Details siehe [Energieverbrauchssensoren](energieverbrauchssensoren.md#konsistenz-dailymonthlyyearly-yesterdayprevious_-energy_value)):

1. **Restore** (`restore_state`): Nach dem Setzen der Werte wird geprüft: Ist der Basis-Wert (yesterday/previous_monthly/previous_yearly) größer als `_energy_value`, wird er auf `_energy_value` gesetzt. Die Rekonstruktion „displayed = yesterday + displayed“ erfolgt nur, wenn `_yesterday_value <= _energy_value`.
2. **Persist-Anwendung** (`_apply_persisted_energy_state`): Nach dem Übernehmen der Werte aus `cycle_energy_persist` dieselbe Prüfung; bei Bedarf Korrektur.
3. **Persist-Schreiben** (Coordinator `_collect_energy_sensor_states`): Es wird nie ein Paar mit Basis-Wert > `energy_value` gespeichert; der Basis-Wert wird vor dem Schreiben auf `energy_value` begrenzt.
4. **Daily-Init** (`_initialize_daily_yesterday_value`): Erkennt negativen Tageswert, setzt `yesterday_value = energy_value` und markiert Persist als „dirty“.

**Cycling-Sensoren** sind davon nicht betroffen: Sie haben pro Periode einen eigenen Zähler (`_cycling_value`), der beim Reset auf 0 gesetzt wird; es gibt keine Formel „Anzeige = Total − Yesterday“. Siehe [Reset-Manager](reset-manager.md).

### 5. Entity nicht gefunden in `increment_energy_consumption_counter`

**Fallback**: Verwendet State (nur für Total-Sensoren OK):

```python
if energy_entity is not None and hasattr(energy_entity, "_energy_value"):
    current_value = energy_entity._energy_value
else:
    # Fallback: Verwende State (nur wenn Entity nicht gefunden wurde)
    current_value = float(state_obj.state)
```

## Debugging

### Wichtige Log-Meldungen

**Reset-Logik**:
- `"Resetting energy sensor {entity_id} (period: {period}, reset_interval: {reset_interval})"`
- `"Updated yesterday value for {entity_id}: {old} -> {new} kWh (from {total_entity_id})"`
- `"Daily sensor {entity_id} reset complete: yesterday_value = {yesterday_value} kWh"`

**Initialisierung**:
- `"Initialized yesterday value for {entity_id}: 0.0 -> {yesterday_value} kWh (from {total_entity_id})"`
- `"Corrected invalid yesterday value for {entity_id}: yesterday was too high (daily would be negative). Set yesterday = energy_value = ..."`
- `"Daily init {entity_id}: Werte gültig, keine Änderung: energy=..., yesterday=..., daily=..., total=... kWh"`

**Kritische Behebung**:
- `"Reading _energy_value directly from entity {entity_id}: {value} kWh (period: {period})"`
- `"Reading value from state for {entity_id}: {value} kWh (fallback, entity not found)"`

### Debug-Logging aktivieren

```yaml
logger:
  default: info
  logs:
    custom_components.lambda_heat_pumps.sensor: debug
    custom_components.lambda_heat_pumps.utils: debug
    custom_components.lambda_heat_pumps.automations: debug
```

## Erweiterungen

### Monthly/Yearly Reset-Logik implementieren

**Aktueller Status**: Nur Daily-Reset-Logik ist vollständig implementiert.

**Zu implementieren** in `_handle_reset()`:

```python
elif self._reset_interval == "monthly" and self._period == "monthly":
    # Finde Total-Sensor
    total_entity_id = self.entity_id.replace("_monthly", "_total")
    total_state = self.hass.states.get(total_entity_id)
    
    if total_state:
        total_value = float(total_state.state)
        self._previous_monthly_value = total_value
    else:
        self._previous_monthly_value = self._energy_value

elif self._reset_interval == "yearly" and self._period == "yearly":
    # Finde Total-Sensor
    total_entity_id = self.entity_id.replace("_yearly", "_total")
    total_state = self.hass.states.get(total_entity_id)
    
    if total_state:
        total_value = float(total_state.state)
        self._previous_yearly_value = total_value
    else:
        self._previous_yearly_value = self._energy_value
```

### Initialisierung für Monthly/Yearly

**Zu implementieren** ähnlich wie `_initialize_daily_yesterday_value()`:

```python
async def _initialize_monthly_yearly_value(self):
    """Initialisiere Previous-Monthly/Yearly-Werte beim Start."""
    if self._period == "monthly":
        total_entity_id = self.entity_id.replace("_monthly", "_total")
        # ... ähnlich wie Daily ...
    elif self._period == "yearly":
        total_entity_id = self.entity_id.replace("_yearly", "_total")
        # ... ähnlich wie Daily ...
```

## Zusammenfassung

### Wichtige Punkte

1. **Differenzberechnung**: Daily/Monthly/Yearly-Sensoren berechnen ihren Wert als Differenz: `value = _energy_value - _previous_value`

2. **Reset = Update Previous-Value**: Reset bedeutet nicht "auf 0 setzen", sondern "Previous-Value aktualisieren"

3. **`_energy_value` bleibt unverändert**: Nach Reset wird `_energy_value` NICHT auf 0 gesetzt, es wird weiterhin aktualisiert

4. **Kritische Behebung**: `increment_energy_consumption_counter` muss `_energy_value` direkt von der Entity lesen, nicht aus dem State (`native_value`)

5. **Initialisierung**: `_initialize_daily_yesterday_value()` korrigiert Yesterday-Werte beim Start für Dev-Instanzen

6. **Persistierung**: Yesterday-Werte werden in `extra_state_attributes` gespeichert und beim Start wiederhergestellt

### Code-Stellen

- **Reset-Handler**: `custom_components/lambda_heat_pumps/sensor.py` → `LambdaEnergyConsumptionSensor._handle_reset()`
- **Berechnung**: `custom_components/lambda_heat_pumps/sensor.py` → `LambdaEnergyConsumptionSensor.native_value`
- **Initialisierung**: `custom_components/lambda_heat_pumps/sensor.py` → `LambdaEnergyConsumptionSensor._initialize_daily_yesterday_value()`
- **Reset-Manager**: `custom_components/lambda_heat_pumps/reset_manager.py` → `ResetManager.setup_reset_automations()`
- **Kritische Behebung**: `custom_components/lambda_heat_pumps/utils.py` → `increment_energy_consumption_counter()`

## Verwandte Dokumentation

- [Energieverbrauchssensoren](energieverbrauchssensoren.md) - Technische Details zu Energieverbrauchssensoren
- [COP-Sensoren](cop-sensoren.md) - Technische Details zu COP-Sensoren (verwenden Energy-Sensoren als Quellen)

