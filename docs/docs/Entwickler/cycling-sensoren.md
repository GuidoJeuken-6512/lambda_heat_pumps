---
title: "Cycling-Sensoren - Technische Dokumentation"
---

# Cycling-Sensoren - Technische Dokumentation

Diese Dokumentation beschreibt die technische Implementierung der Cycling-Sensoren in der Lambda Heat Pumps Integration.

## Übersicht

Cycling-Sensoren zählen, wie oft die Wärmepumpe in einen bestimmten Betriebsmodus (Heizen, Warmwasser, Kühlen, Abtauen) gewechselt wurde. Sie messen die Anzahl der Zustandswechsel (Flanken) zwischen verschiedenen Betriebsmodi.

Die Integration bietet Cycling-Sensoren für folgende Betriebsarten:
- **Heating** (Heizen)
- **Hot Water** (Warmwasser)
- **Cooling** (Kühlen)
- **Defrost** (Abtauen)
- **Compressor Start** (Kompressorstart, nur Total und Monthly)

Jede Betriebsart wird nach Zeitraum aufgeteilt:
- **Total**: Gesamtzähler seit Installation
- **Daily**: Täglich (wird um Mitternacht auf 0 zurückgesetzt)
- **Yesterday**: Wert von gestern (wird vor Daily-Reset gespeichert)
- **2h**: Alle 2 Stunden (wird alle 2 Stunden auf 0 zurückgesetzt)
- **4h**: Alle 4 Stunden (wird alle 4 Stunden auf 0 zurückgesetzt)
- **Monthly**: Monatlich (wird am 1. des Monats auf 0 zurückgesetzt, nur für Compressor Start)
- **Yearly**: Jährlich (wird am 1. Januar auf 0 zurückgesetzt)

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _async_update_data()                                  │  │
│  │    └─ Flankenerkennung (Operating State Change)       │  │
│  │       └─ increment_cycling_counter()                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    utils.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  increment_cycling_counter()                          │  │
│  │    - mode: "heating" | "hot_water" | "cooling" | ... │  │
│  │    - hp_index: 1-based                                │  │
│  │    - Erhöht: Total, Daily, 2h, 4h, Monthly           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    sensor.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaCyclingSensor                                  │  │
│  │    - set_cycling_value()                              │  │
│  │    - native_value (gibt _cycling_value zurück)       │  │
│  │    - Reset-Handler für Daily/2h/4h/Monthly/Yearly    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    reset_manager.py                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ResetManager                                         │  │
│  │    - setup_reset_automations()                        │  │
│  │      - Daily Reset (Mitternacht)                      │  │
│  │      - 2h Reset (alle 2 Stunden)                      │  │
│  │      - 4h Reset (alle 4 Stunden)                      │  │
│  │      - Monthly Reset (1. des Monats)                  │  │
│  │      - Yearly Reset (1. Januar)                       │  │
│  │      - Yesterday-Sensor Update (vor Daily Reset)      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  automations.py                                       │  │
│  │  _update_yesterday_sensors_async()                   │  │
│  │    - Aktualisiert Yesterday-Sensoren                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss

1. **Coordinator** erkennt Betriebsmodus-Wechsel:
   - Liest Operating State Register
   - Vergleicht mit vorherigem Wert
   - Erkennt Flanke (State Change)

2. **Coordinator** ruft `increment_cycling_counter()` auf:
   - Übergibt Mode (heating, hot_water, etc.)
   - Übergibt HP-Index

3. **Utils** erhöhen alle Perioden:
   - `increment_cycling_counter()` erhöht Total, Daily, 2h, 4h
   - Für Compressor Start: auch Monthly
   - Jeder Sensor wird um +1 erhöht

4. **Entities** speichern Werte:
   - `LambdaCyclingSensor.set_cycling_value()` setzt internen Wert
   - `native_value` gibt den aktuellen Wert zurück

5. **ResetManager** resetten Perioden:
   - Daily: Um Mitternacht auf 0 (via `ResetManager.setup_reset_automations()`)
   - 2h: Alle 2 Stunden auf 0
   - 4h: Alle 4 Stunden auf 0
   - Monthly: Am 1. des Monats auf 0
   - Yearly: Am 1. Januar auf 0

## Implementierung

### 1. Sensor-Erstellung

Sensoren werden in `sensor.py` erstellt:

```python
# Total-Sensoren
for hp_idx in range(1, num_hps + 1):
    for mode in CYCLING_MODES:
        sensor_id = f"{mode}_cycling_total"
        sensor = LambdaCyclingSensor(
            hass=hass,
            entry=entry,
            sensor_id=sensor_id,
            name=names["name"],
            entity_id=names["entity_id"],
            unique_id=names["unique_id"],
            unit=template["unit"],
            state_class=template["state_class"],
            device_class=template["device_class"],
            device_type=template["device_type"],
            hp_index=hp_idx,
        )

# Daily-Sensoren
for hp_idx in range(1, num_hps + 1):
    for mode in CYCLING_MODES:
        sensor_id = f"{mode}_cycling_daily"
        sensor = LambdaCyclingSensor(...)

# Yesterday-Sensoren
for hp_idx in range(1, num_hps + 1):
    for mode in CYCLING_MODES:
        sensor_id = f"{mode}_cycling_yesterday"
        sensor = LambdaCyclingSensor(...)

# 2h, 4h, Monthly, Yearly ähnlich
```

### 2. Sensor-Templates

Sensor-Templates werden in `const.py` definiert:

```python
CALCULATED_SENSOR_TEMPLATES = {
    "heating_cycling_total": {
        "name": "Heating Cycling Total",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "state_class": "total_increasing",
        "device_class": None,
        "mode_value": 1,  # CH
        "operating_state": "heating",
        "period": "total",
        "reset_interval": None,
    },
    "heating_cycling_daily": {
        "name": "Heating Cycling Daily",
        "unit": "cycles",
        "precision": 0,
        "data_type": "calculated",
        "state_class": "total",
        "device_class": None,
        "operating_state": "heating",
        "period": "daily",
        "reset_interval": "daily",
    },
    # ... weitere Sensoren
}
```

### 3. Flankenerkennung

Die Flankenerkennung erfolgt im Coordinator (`coordinator.py`):

```python
# In _async_update_data()
last_op_state = self._last_operating_state.get(str(hp_idx), "UNBEKANNT")
op_state_val = data.get(f"hp{hp_idx}_operating_state", 0)

# Flankenerkennung: State hat sich geändert
if (self._initialization_complete and 
    last_op_state != "UNBEKANNT" and
    last_op_state != mode_val and 
    op_state_val == mode_val):
    
    # Betriebsmodus-Wechsel erkannt!
    await increment_cycling_counter(
        self.hass,
        mode=mode,
        hp_index=hp_idx,
        name_prefix=self.entry.data.get("name", "eu08l"),
        use_legacy_modbus_names=True,
        cycling_offsets=self._cycling_offsets.get(f"hp{hp_idx}", {}),
    )
```

**Wichtig**: Flankenerkennung wird nur ausgelöst, wenn:
- Initialisierung abgeschlossen ist (`_initialization_complete == True`)
- Vorheriger State nicht "UNBEKANNT" war
- State-Wechsel erkannt wurde (alter State != neuer State)
- Neuer State entspricht dem erwarteten Mode-Wert

### 4. Increment-Logik

Die Increment-Logik ist in `utils.py` implementiert:

```python
async def increment_cycling_counter(
    hass: HomeAssistant,
    mode: str,
    hp_index: int,
    name_prefix: str,
    use_legacy_modbus_names: bool = True,
    cycling_offsets: dict = None,
):
    """
    Increment ALL cycling counters for a given mode and heat pump index.
    This should be called only on a real flank (state change)!
    
    Increments: Total, Daily, 2H, 4H sensors
    """
    device_prefix = f"hp{hp_index}"
    
    # Liste aller Sensor-Typen, die erhöht werden sollen
    sensor_types = [
        f"{mode}_cycling_total",
        f"{mode}_cycling_daily", 
        f"{mode}_cycling_2h",
        f"{mode}_cycling_4h"
    ]
    
    # Für compressor_start: auch monthly hinzufügen
    if mode == "compressor_start":
        sensor_types.append(f"{mode}_cycling_monthly")
    
    for sensor_id in sensor_types:
        # Finde Entity
        names = generate_sensor_names(...)
        entity_id = names["entity_id"]
        
        # Hole aktuellen Wert
        state_obj = hass.states.get(entity_id)
        current = int(float(state_obj.state)) if state_obj else 0
        
        # Offset nur für Total-Sensoren anwenden
        offset = 0
        if cycling_offsets is not None and sensor_id.endswith("_total"):
            device_key = device_prefix
            if device_key in cycling_offsets:
                offset = int(cycling_offsets[device_key].get(sensor_id, 0))
        
        # Erhöhe um 1
        new_value = int(current + 1)
        final_value = int(new_value + offset)
        
        # Setze neuen Wert
        cycling_entity = find_cycling_entity(hass, entity_id)
        if cycling_entity:
            cycling_entity.set_cycling_value(final_value)
        else:
            # Fallback: State setzen
            hass.states.async_set(entity_id, final_value, ...)
```

**Wichtig**: 
- Alle Perioden (Total, Daily, 2h, 4h) werden gleichzeitig um +1 erhöht
- Offsets werden nur für Total-Sensoren angewendet
- Die Funktion sollte nur bei echten Flanken (State Changes) aufgerufen werden

### 5. LambdaCyclingSensor Klasse

Die `LambdaCyclingSensor` Klasse ist in `sensor.py` implementiert:

```python
class LambdaCyclingSensor(RestoreEntity, SensorEntity):
    """Cycling total sensor (echte Entity, Wert wird von increment_cycling_counter gesetzt)."""
    
    def __init__(self, ...):
        self._cycling_value = 0
        self._yesterday_value = 0  # Nur für Total-Sensoren
        self._last_2h_value = 0    # Nur für Total-Sensoren
        self._last_4h_value = 0    # Nur für Total-Sensoren
        self._applied_offset = 0   # Nur für Total-Sensoren
    
    def set_cycling_value(self, value):
        """Set the cycling value and update state."""
        self._cycling_value = int(value)
        self.async_write_ha_state()
    
    @property
    def native_value(self):
        """Return the current cycling value."""
        value = getattr(self, "_cycling_value", 0)
        return int(value) if value is not None else 0
```

### 6. Reset-Logik

Die Reset-Logik verwendet Home Assistant Dispatcher-Signale:

```python
# In LambdaCyclingSensor.async_added_to_hass()
from .automations import (
    SIGNAL_RESET_DAILY, 
    SIGNAL_RESET_2H, 
    SIGNAL_RESET_4H, 
    SIGNAL_RESET_MONTHLY, 
    SIGNAL_RESET_YEARLY
)

# Wrapper-Funktion für asynchrone Handler (einheitlich für alle Perioden)
@callback
def _wrap_reset(entry_id: str):
    self.hass.async_create_task(self._handle_reset(entry_id))

# Registriere für alle Perioden
self._unsub_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_DAILY, _wrap_reset
)
self._unsub_2h_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_2H, _wrap_reset
)
self._unsub_4h_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_4H, _wrap_reset
)
self._unsub_monthly_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_MONTHLY, _wrap_reset
)
self._unsub_yearly_dispatcher = async_dispatcher_connect(
    self.hass, SIGNAL_RESET_YEARLY, _wrap_reset
)

async def _handle_reset(self, entry_id: str):
    """Handle reset signal for all periods (einheitlich, wie Energy)."""
    if entry_id != self._entry.entry_id:
        return
    
    # Prüfe Periode basierend auf sensor_id und reset_interval
    if self._sensor_id.endswith("_daily") and self._reset_interval == "daily":
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"Daily sensor {self.entity_id} reset to 0")
    elif self._sensor_id.endswith("_2h") and self._reset_interval == "2h":
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"2H sensor {self.entity_id} reset to 0")
    elif self._sensor_id.endswith("_4h") and self._reset_interval == "4h":
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"4H sensor {self.entity_id} reset to 0")
    elif self._sensor_id.endswith("_monthly") and self._reset_interval == "monthly":
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"Monthly sensor {self.entity_id} reset to 0")
    elif self._sensor_id.endswith("_yearly") and self._reset_interval == "yearly":
        self._cycling_value = 0
        self.async_write_ha_state()
        _LOGGER.info(f"Yearly sensor {self.entity_id} reset to 0")
```

**Reset-Intervall**:
- **Daily**: Um Mitternacht (`SIGNAL_RESET_DAILY`)
- **2h**: Alle 2 Stunden (`SIGNAL_RESET_2H`)
- **4h**: Alle 4 Stunden (`SIGNAL_RESET_4H`)
- **Monthly**: Am 1. des Monats (`SIGNAL_RESET_MONTHLY`)
- **Yearly**: Am 1. Januar (`SIGNAL_RESET_YEARLY`)

**Wichtig**: 
- Reset wird direkt auf 0 gesetzt (nicht wie bei Energy-Sensoren Differenzberechnung)
- Jeder Perioden-Sensor hat seinen eigenen Wert
- Total-Sensoren werden nie zurückgesetzt

### 7. Yesterday-Sensoren

Yesterday-Sensoren speichern die Werte von gestern, bevor der Daily-Sensor zurückgesetzt wird:

```python
# In automations.py
async def _update_yesterday_sensors_async(hass: HomeAssistant, entry_id: str) -> None:
    """Update yesterday sensors with current daily values before reset."""
    cycling_entities = hass.data["lambda_heat_pumps"][entry_id]["cycling_entities"]
    
    # Für jeden Daily-Sensor den entsprechenden Yesterday-Sensor aktualisieren
    for entity_id, entity in cycling_entities.items():
        if entity_id.endswith("_daily"):
            # Erstelle Yesterday-Entity-ID
            yesterday_entity_id = entity_id.replace("_daily", "_yesterday")
            
            # Hole den aktuellen Daily-Wert
            daily_state = hass.states.get(entity_id)
            daily_value = int(float(daily_state.state))
            
            # Setze Yesterday-Sensor auf Daily-Wert
            yesterday_entity = cycling_entities.get(yesterday_entity_id)
            if yesterday_entity:
                yesterday_entity.set_cycling_value(daily_value)
```

**Ablauf**:
1. Vor dem Daily-Reset (um Mitternacht) wird `_update_yesterday_sensors_async()` aufgerufen
2. Für jeden Daily-Sensor wird der aktuelle Wert gelesen
3. Der entsprechende Yesterday-Sensor wird auf diesen Wert gesetzt
4. Anschließend wird der Daily-Sensor auf 0 zurückgesetzt

**Unterschied zu Energy-Sensoren**:
- Energy-Sensoren verwenden Differenzberechnung (`daily = total - yesterday`)
- Cycling-Sensoren speichern Yesterday-Wert in separatem Sensor

### 8. Cycling-Offsets

Cycling-Offsets werden in `lambda_wp_config.yaml` konfiguriert:

```yaml
cycling_offsets:
  hp1:
    heating_cycling_total: 100
    hot_water_cycling_total: 50
```

Offsets werden nur für Total-Sensoren angewendet:

```python
# In LambdaCyclingSensor._apply_cycling_offset()
async def _apply_cycling_offset(self):
    """Apply cycling offset from configuration."""
    config = await load_lambda_config(self.hass)
    cycling_offsets = config.get("cycling_offsets", {})
    
    device_key = f"hp{self._hp_index}"
    current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
    applied_offset = getattr(self, "_applied_offset", 0)
    
    # Berechne Differenz
    offset_difference = current_offset - applied_offset
    
    if offset_difference != 0:
        old_value = self._cycling_value
        self._cycling_value = int(self._cycling_value + offset_difference)
        self._applied_offset = current_offset
        self.async_write_ha_state()
```

**Wichtig**:
- Offsets werden nur beim Start angewendet (in `restore_state()`)
- Nur Total-Sensoren unterstützen Offsets
- Der angewendete Offset wird in `_applied_offset` gespeichert
- Bei Änderung des Offsets wird die Differenz zum aktuellen Wert addiert

### 9. Persistenz

Cycling-Sensoren verwenden Home Assistant's `RestoreEntity`:

```python
class LambdaCyclingSensor(RestoreEntity, SensorEntity):
    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()
        
        # RestoreEntity provides async_get_last_state() method
        last_state = await self.async_get_last_state()
        await self.restore_state(last_state)
    
    async def restore_state(self, last_state):
        """Restore state from database to prevent reset on reload."""
        if last_state is not None:
            last_value = last_state.state
            if last_value not in (None, "unknown", "unavailable"):
                self._cycling_value = int(float(last_value))
            
            # Restore applied offset
            if hasattr(last_state, 'attributes') and last_state.attributes:
                self._applied_offset = last_state.attributes.get("applied_offset", 0)
        
        # Apply cycling offset for total sensors
        if self._sensor_id.endswith("_total"):
            await self._apply_cycling_offset()
```

**Persistierte Daten**:
- `_cycling_value`: Der aktuelle Zählerwert
- `_applied_offset`: Der bereits angewendete Offset (nur Total-Sensoren)

**Wichtig**: 
- Werte werden automatisch von Home Assistant persistiert
- Bei Neustart werden die Werte wiederhergestellt
- Offsets werden nach der Wiederherstellung angewendet

### 10. Entity-Registrierung

Cycling-Entities werden in `hass.data` registriert:

```python
# In sensor.py async_setup_entry()
if entry.entry_id not in hass.data["lambda_heat_pumps"]:
    hass.data["lambda_heat_pumps"][entry.entry_id] = {}

if "cycling_entities" not in hass.data["lambda_heat_pumps"][entry.entry_id]:
    hass.data["lambda_heat_pumps"][entry.entry_id]["cycling_entities"] = {}

# Registriere Entity
hass.data["lambda_heat_pumps"][entry.entry_id]["cycling_entities"][entity_id] = sensor
```

Die Registrierung ermöglicht:
- Zugriff auf Entity-Instanzen von `increment_cycling_counter()`
- Zugriff auf Entity-Instanzen von Automations (Yesterday-Update)
- Fehlerbehandlung bei nicht registrierten Entities

### 11. Unterschiede zu Energy-Sensoren

| Aspekt | Cycling-Sensoren | Energy-Sensoren |
|--------|------------------|-----------------|
| **Berechnung** | Zählt State-Wechsel | Misst kumulative Energie |
| **Reset-Logik** | Direkt auf 0 setzen | Differenzberechnung (`daily = total - yesterday`) |
| **Yesterday** | Separater Sensor | Attribut `_yesterday_value` |
| **Increment** | +1 bei Flanke | Delta-Addition (kWh) |
| **Offsets** | Nur Total-Sensoren | Nur Total-Sensoren |
| **Perioden-Synchronisation** | Alle Perioden unabhängig | Alle Perioden gleichzeitig (gleiches Delta) |
| **Quellsensor** | Operating State Register | Compressor Power/Thermal Energy Register |

## Fehlerbehandlung

### 1. Entity nicht registriert

Wenn `increment_cycling_counter()` eine Entity nicht findet:

```python
cycling_entity = find_cycling_entity(hass, entity_id)
if cycling_entity is None:
    # Fallback: State setzen
    hass.states.async_set(entity_id, final_value, ...)
    _LOGGER.warning(f"Cycling entity {entity_id} not found, using fallback state update")
```

**Dynamische Meldungsunterdrückung**: Die ersten 3 Fehler werden als Debug, weitere als Warning geloggt.

### 2. State nicht verfügbar

Wenn der State nicht verfügbar ist:

```python
state_obj = hass.states.get(entity_id)
if state_obj is None:
    # Dynamische Meldungsunterdrückung
    warning_count = coordinator._cycling_warnings.get(entity_id, 0)
    if warning_count < coordinator._max_cycling_warnings:
        _LOGGER.debug(f"Entity {entity_id} state not available yet")
    else:
        _LOGGER.warning(f"Entity {entity_id} state not available after {max} attempts")
    continue
```

### 3. Initialisierung während Flankenerkennung

Flankenerkennung wird während der Initialisierung unterdrückt:

```python
if not self._initialization_complete:
    _LOGGER.debug("Flankenerkennung während Initialisierung unterdrückt")
    return
```

## Erweiterbarkeit

### Neue Betriebsmodi hinzufügen

1. Sensor-Template in `const.py` hinzufügen:
```python
"new_mode_cycling_total": {
    "name": "New Mode Cycling Total",
    "unit": "cycles",
    "precision": 0,
    "data_type": "calculated",
    "state_class": "total_increasing",
    "device_class": None,
    "mode_value": X,  # Modbus-Wert
    "operating_state": "new_mode",
    "period": "total",
}
```

2. Mode-Wert in Coordinator prüfen:
```python
if op_state_val == NEW_MODE_VALUE:
    await increment_cycling_counter(..., mode="new_mode", ...)
```

### Neue Perioden hinzufügen

1. Sensor-Template in `const.py` hinzufügen
2. Reset-Signal in `automations.py` hinzufügen (falls nicht vorhanden)
3. Reset-Handler in `LambdaCyclingSensor._handle_reset()` erweitern (einheitliche Methode)
4. Sensor-Erstellung in `sensor.py` erweitern
5. Reset-Automatisierung in `reset_manager.py` hinzufügen
6. Increment-Logik in `utils.py` erweitern (falls nötig)

## Debugging

### Logging

Cycling-Sensoren verwenden strukturiertes Logging:

```python
_LOGGER.info(f"Cycling counter incremented: {entity_id} = {final_value} (was {current}, offset {offset})")
_LOGGER.debug(f"Cycling sensor {entity_id} value set to {value}")
_LOGGER.warning(f"Cycling entity {entity_id} not found, using fallback state update")
```

### Entity-Attribute

Total-Sensoren haben folgende Attribute:
- `yesterday_value`: Wert von gestern (nur Total)
- `hp_index`: Index der Wärmepumpe
- `sensor_type`: "cycling_total"
- `applied_offset`: Angewendeter Offset (nur Total)

### State-Überprüfung

In Home Assistant:
- Developer Tools > States: `sensor.eu08l_hp1_heating_cycling_total`
- Developer Tools > Services: `homeassistant.reload_config_entry`
- Logs: Suche nach "Cycling counter incremented"

## Zusammenfassung

Cycling-Sensoren sind einfacher als Energy-Sensoren, da sie:
- Direkt auf 0 zurückgesetzt werden (keine Differenzberechnung)
- State-Wechsel zählen (keine kontinuierliche Messung)
- Unabhängige Perioden haben (keine Synchronisation nötig)

Die Architektur ermöglicht:
- Robuste Flankenerkennung
- Persistenz über Neustarts
- Konfigurierbare Offsets
- Yesterday-Werte für Daily-Sensoren
- Automatische Reset-Logik

