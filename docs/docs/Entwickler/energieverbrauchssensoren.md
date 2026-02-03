---
title: "Energieverbrauchssensoren - Technische Dokumentation"
---

# Energieverbrauchssensoren - Technische Dokumentation

Diese Dokumentation beschreibt die technische Implementierung der Energieverbrauchssensoren (elektrisch und thermisch) in der Lambda Heat Pumps Integration.

## Übersicht

Die Integration bietet zwei Arten von Energieverbrauchssensoren:

1. **Elektrische Energieverbrauchssensoren**: Messen den Stromverbrauch (kWh)
2. **Thermische Energieverbrauchssensoren**: Messen die Wärmeabgabe (kWh)

Beide Typen werden nach Betriebsart (heating, hot_water, cooling, defrost) und Zeitraum (total, daily, monthly, yearly) aufgeteilt.

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _track_hp_energy_consumption()                       │  │
│  │    ├─ _track_hp_energy_type_consumption(electrical) │  │
│  │    └─ _track_hp_energy_type_consumption(thermal)     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _increment_energy_consumption()                      │  │
│  │  _increment_thermal_energy_consumption()              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    utils.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  increment_energy_consumption_counter()               │  │
│  │    - sensor_type: "electrical" | "thermal"            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    sensor.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaEnergyConsumptionSensor                        │  │
│  │    - set_energy_value()                               │  │
│  │    - native_value (berechnet aus period)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss

1. **Quellsensoren** liefern kumulative Werte:
   - Elektrisch: `compressor_power_consumption_accumulated` (Register 1021)
   - Thermisch: `compressor_thermal_energy_output_accumulated` (Register 1022)

2. **Coordinator** berechnet Deltas:
   - Liest Quellsensor-Werte
   - Berechnet Delta zwischen Updates
   - Erkennt Betriebsmodus-Wechsel (Flankenerkennung)

3. **Utils** aktualisieren Sensoren:
   - `increment_energy_consumption_counter()` aktualisiert alle Perioden
   - Unterstützt sowohl elektrische als auch thermische Sensoren

4. **Entities** speichern Werte:
   - `LambdaEnergyConsumptionSensor` speichert Total-Wert in `_energy_value`
   - Berechnet daily/monthly/yearly aus Total-Wert: `native_value = _energy_value - _yesterday_value` (bzw. previous_monthly/yearly)
   - **Persistierung:** Gespeichert wird der **State** (= Anzeige-Wert). Bei Daily/Monthly/Yearly muss beim Restore der kumulative Total aus diesem Wert rekonstruiert oder aus dem Attribut `energy_value` gelesen werden (siehe Abschnitt „Negative Daily/Monthly/Yearly-Werte“).

**Einheitliches Delta-Verfahren:** Elektrische und thermische Sensoren nutzen dasselbe Berechnungsmodell (Delta zum Vortag bzw. Vormonat/Vorjahr): Daily = Total - Yesterday, Monthly = Total - Previous Monthly, Yearly = Total - Previous Yearly. Dieselbe Logik in `LambdaEnergyConsumptionSensor` und `increment_energy_consumption_counter` gilt für beide.

## Implementierung

### 1. Sensor-Erstellung

Sensoren werden in `sensor.py` erstellt:

```python
# Elektrische Sensoren
for hp_idx in range(1, num_hps + 1):
    for mode in ENERGY_CONSUMPTION_MODES:
        for period in ENERGY_CONSUMPTION_PERIODS:
            sensor_id = f"{mode}_energy_{period}"
            sensor = LambdaEnergyConsumptionSensor(...)

# Thermische Sensoren
for hp_idx in range(1, num_hps + 1):
    for mode in ENERGY_CONSUMPTION_MODES:
        for period in ENERGY_CONSUMPTION_PERIODS:
            sensor_id = f"{mode}_thermal_energy_{period}"
            if sensor_template.get("data_type") == "thermal_calculated":
                sensor = LambdaEnergyConsumptionSensor(...)
```

### 2. Sensor-Templates

Templates sind in `const.py` definiert:

```python
ENERGY_CONSUMPTION_SENSOR_TEMPLATES = {
    # Elektrische Sensoren
    "heating_energy_total": {
        "name": "Heating Energy Total",
        "unit": "kWh",
        "data_type": "energy_calculated",
        "state_class": "total_increasing",
        "device_class": "energy",
        "operating_state": "heating",
        "period": "total",
    },
    # Thermische Sensoren
    "heating_thermal_energy_total": {
        "name": "Heating Thermal Energy Total",
        "unit": "kWh",
        "data_type": "thermal_calculated",
        "state_class": "total_increasing",
        "device_class": "energy",
        "operating_state": "heating",
        "period": "total",
    },
    # ...
}
```

### 3. Coordinator-Tracking

Der Coordinator trackt beide Energiearten parallel:

```python
async def _track_hp_energy_consumption(self, hp_idx, current_state, data):
    # Elektrische Energie
    await self._track_hp_energy_type_consumption(
        hp_idx, current_state, data,
        sensor_type="electrical",
        default_sensor_id_template="sensor.{name_prefix}_hp{hp_idx}_compressor_power_consumption_accumulated",
        increment_fn=self._increment_energy_consumption
    )
    
    # Thermische Energie
    await self._track_hp_energy_type_consumption(
        hp_idx, current_state, data,
        sensor_type="thermal",
        default_sensor_id_template="sensor.{name_prefix}_hp{hp_idx}_compressor_thermal_energy_output_accumulated",
        increment_fn=self._increment_thermal_energy_consumption
    )
```

### 4. Delta-Berechnung

Die generische Tracking-Funktion:

```python
async def _track_hp_energy_type_consumption(
    self, hp_idx, current_state, data, sensor_type, 
    default_sensor_id_template, unit_check_fn, convert_to_kwh_fn,
    last_reading_dict, first_value_seen_dict, increment_fn
):
    # 1. Lese Quellsensor
    current_energy_state = self.hass.states.get(sensor_entity_id)
    current_energy = float(current_energy_state.state)
    
    # 2. Konvertiere zu kWh
    current_energy_kwh = convert_to_kwh_fn(current_energy, unit)
    
    # 3. Berechne Delta
    last_energy = last_reading_dict.get(f"hp{hp_idx}", None)
    energy_delta = calculate_energy_delta(current_energy_kwh, last_energy, max_delta=100.0)
    
    # 4. Bestimme Betriebsmodus
    mode = mode_mapping[current_state]  # heating, hot_water, cooling, defrost
    
    # 5. Aktualisiere Sensoren bei Moduswechsel oder kontinuierlich
    if current_state != last_state or (mode == "stby" or energy_delta > 0):
        await increment_fn(hp_idx, mode, energy_delta)
```

### 5. Sensor-Update

Die Update-Funktion aktualisiert alle Perioden:

```python
async def increment_energy_consumption_counter(
    hass, mode, hp_index, energy_delta, name_prefix,
    use_legacy_modbus_names=True, energy_offsets=None,
    sensor_type="electrical"  # oder "thermal"
):
    for period in ["total", "daily", "monthly", "yearly", "2h", "4h"]:
        # Bestimme sensor_id basierend auf sensor_type
        if sensor_type == "thermal":
            sensor_id = f"{mode}_thermal_energy_{period}"
        else:
            sensor_id = f"{mode}_energy_{period}"
        
        # Finde Entity
        energy_entity = find_energy_entity(hass, entity_id)
        
        # Berechne neuen Wert
        current_value = float(state_obj.state)
        new_value = current_value + energy_delta
        
        # Wende Offset an (nur für total)
        if period == "total" and energy_offsets:
            new_value += offset
        
        # Aktualisiere Entity
        energy_entity.set_energy_value(new_value)
```

### 6. Entity-Implementierung

Die `LambdaEnergyConsumptionSensor` Klasse:

```python
class LambdaEnergyConsumptionSensor(RestoreEntity, SensorEntity):
    def __init__(self, hass, entry, sensor_id, name, entity_id, 
                 unique_id, unit, state_class, device_class, 
                 device_type, hp_index, mode, period):
        self._energy_value = 0.0  # Total-Wert
        self._period = period
        # ...
    
    @property
    def native_value(self):
        """Berechnet Wert basierend auf period."""
        if self._period == "total":
            return self._energy_value
        elif self._period == "daily":
            return self._energy_value - self._yesterday_value
        elif self._period == "monthly":
            return self._energy_value - self._previous_monthly_value
        # ...
    
    def set_energy_value(self, value):
        """Wird von increment_energy_consumption_counter aufgerufen."""
        self._energy_value = value
        self.async_write_ha_state()
```

## Quellsensoren

### Elektrische Energie

- **Sensor**: `compressor_power_consumption_accumulated`
- **Register**: 1021 (HP1), 2021 (HP2), etc.
- **Einheit**: Wh (wird zu kWh konvertiert)
- **Typ**: int32, total_increasing

### Thermische Energie

- **Sensor**: `compressor_thermal_energy_output_accumulated`
- **Register**: 1022 (HP1), 2022 (HP2), etc.
- **Einheit**: Wh (wird zu kWh konvertiert)
- **Typ**: int32, total_increasing

## Betriebsmodus-Mapping

```python
mode_mapping = {
    0: "stby",      # Standby
    1: "heating",   # CH - Heizen
    2: "hot_water", # DHW - Warmwasser
    3: "cooling",   # CC - Kühlen
    4: "stby",      # Standby (alternativ)
    5: "defrost",   # DEFROST - Abtauen
}
```

## Flankenerkennung

Die Integration nutzt Flankenerkennung, um Energie-Deltas exakt dem aktiven Betriebsmodus zuzuordnen:

1. **Moduswechsel erkannt**: Delta wird dem neuen Modus zugeordnet
2. **Kontinuierlicher Betrieb**: Delta wird dem aktuellen Modus zugeordnet
3. **Standby**: Delta wird auch Standby zugeordnet (falls vorhanden)

## Einheitenkonvertierung

Unterstützte Einheiten werden automatisch zu kWh konvertiert:

```python
def _convert_energy_to_kwh_cached(self, value, unit):
    if unit == "Wh":
        return value / 1000.0
    elif unit == "kWh":
        return value
    elif unit == "MWh":
        return value * 1000.0
    else:
        return value  # Fallback
```

## Persistierung

- **Total-Werte**: Werden in `LambdaEnergyConsumptionSensor` gespeichert (RestoreEntity)
- **Last Readings**: Werden im Coordinator gespeichert (`_last_energy_reading`, `_last_thermal_energy_reading`)
- **JSON-Persistierung**: Coordinator speichert Werte in `cycle_energy_persist.json`
- **Energy-Sensor-States**: Zusätzlich zu HA-Restore werden die Energy-Sensor-States (Total, Daily, Monthly, Yearly für elektrisch und thermisch) in `cycle_energy_persist.json` unter dem Schlüssel `energy_sensor_states` gespeichert; beim Neustart hat diese Quelle Vorrang, damit Anzeigewerte nicht fallen (z. B. 0,44 → 0,4).

### Neustart-Werterhalt

1. **`set_energy_value()` verringert nie**: Der gespeicherte Wert wird nicht verringert (vermeidet Überschreiben durch veraltete Coordinator-/Total-Werte nach Neustart).
2. **Kein Fallback-`async_set`**: Kann der Coordinator die Entity-Referenz nicht auflösen, wird kein `async_set` mit möglicherweise veraltetem State ausgeführt.
3. **`native_value` auf 2 Dezimalstellen gerundet**: Vermeidet Float-Artefakte im persistierten State (z. B. 0,39999… statt 0,44).
4. **State aus `cycle_energy_persist` bevorzugt**: Nach `restore_state(last_state)` wird, falls der Coordinator einen State aus `cycle_energy_persist` für diese Entity hat, dieser angewendet (`_apply_persisted_energy_state`).

## Konfiguration

### Externe Sensoren

Elektrische Sensoren können extern konfiguriert werden:

```yaml
energy_consumption_sensors:
  hp1:
    electrical_sensor_entity_id: "sensor.shelly_lambda_gesamt_leistung"
```

**Hinweis**: Thermische Sensoren verwenden immer die internen Modbus-Sensoren.

### Offsets

Offsets können für Total-Sensoren konfiguriert werden:

```yaml
energy_consumption_offsets:
  hp1:
    heating_energy_total: 1000.0
    heating_thermal_energy_total: 5000.0
    # ...
```

## Fehlerbehandlung

### Sensor-Wechsel-Erkennung

- Automatische Erkennung von Sensorwechseln
- Nullwert-Schutz beim ersten Start
- Rückwärtssprung-Schutz (Sensor-Reset)

### Zero-Value Protection

```python
if current_energy_kwh == 0.0:
    first_value_seen_dict[f"hp{hp_idx}"] = False
    return  # Warte auf ersten gültigen Wert
```

### Overflow Protection

```python
if current_energy_kwh < last_energy:
    # Sensor wurde zurückgesetzt oder gewechselt
    first_value_seen_dict[f"hp{hp_idx}"] = False
    last_reading_dict[f"hp{hp_idx}"] = None
    return
```

### Negative Daily/Monthly/Yearly-Werte (Restore-Bug)

**Symptom:** `current_daily_value` (bzw. monthly/yearly) wird nach Neustart negativ angezeigt (z. B. -1305.88 kWh).

**Ursache:** Beim Persistieren speichert Home Assistant den **State** der Entity. Bei Daily-Sensoren ist der State der **Anzeige-Wert** (`native_value` = `_energy_value - _yesterday_value`), nicht der kumulative Total `_energy_value`. Beim Restore wurde früher `_energy_value = float(last_state.state)` gesetzt – also der Tageswert statt des Totals. Zusammen mit dem korrekt aus Attributen wiederhergestellten `_yesterday_value` ergibt sich dann: `current_daily_value = _energy_value - _yesterday_value` = (kleiner Tageswert) - (großer Vortag) = negativ.

**Lösung in der Implementierung:**

- Beim **Restore** von Daily/Monthly/Yearly-Sensoren wird `_energy_value` nicht mehr aus `last_state.state` übernommen, sondern rekonstruiert:
  - **Daily:** `_energy_value = _yesterday_value + angezeigter State` (bzw. aus Attribut `energy_value`, falls persistiert).
  - **Monthly/Yearly:** analog mit `_previous_monthly_value` / `_previous_yearly_value`.
- Der kumulative Total wird in den Attributen als `energy_value` mitpersistiert; beim nächsten Restore wird er direkt aus diesem Attribut gelesen, falls vorhanden.

Die Anzeige bleibt durch `native_value = max(0.0, _energy_value - _yesterday_value)` nach unten auf 0 begrenzt; durch die korrigierte Restore-Logik stimmen die internen Werte wieder und negative Werte treten nicht mehr auf.

### Konsistenz Daily/Monthly/Yearly (yesterday/previous_* ≤ energy_value)

**Problem:** Nach Neustart können persistierte Daten (Recorder oder `cycle_energy_persist`) inkonsistent sein: `yesterday_value` bzw. `previous_monthly_value` / `previous_yearly_value` sind größer als `energy_value`. Dann wäre der Periodenwert (daily = energy_value − yesterday_value usw.) negativ.

**Lösung in der Implementierung:**

1. **Restore** (`restore_state`): Nach dem Setzen von `_energy_value` und `_yesterday_value` (bzw. `_previous_monthly_value` / `_previous_yearly_value`) wird geprüft: Ist der Basis-Wert größer als `_energy_value`, wird er auf `_energy_value` gesetzt (Korrektur + Log-Warnung). Die Rekonstruktion „displayed = yesterday + displayed“ wird nur ausgeführt, wenn `_yesterday_value <= _energy_value` (konsistent), damit kein Überschreiben mit falschem Wert erfolgt.

2. **Persist-Anwendung** (`_apply_persisted_energy_state`): Nach dem Übernehmen der Werte aus `cycle_energy_persist` wird für Daily/Monthly/Yearly dieselbe Prüfung durchgeführt; bei Bedarf Korrektur und Warnung.

3. **Persist-Schreiben** (Coordinator `_collect_energy_sensor_states`): Beim Speichern in `cycle_energy_persist` wird nie ein Paar mit `yesterday_value` bzw. `previous_monthly_value` / `previous_yearly_value` größer als `energy_value` geschrieben; der Basis-Wert wird vor dem Schreiben auf `energy_value` begrenzt.

4. **Daily-Init** (`_initialize_daily_yesterday_value`): Erkennt die Integration weiterhin negativen Tageswert (z. B. weil Total-Sensor beim Start noch nicht verfügbar war), setzt sie `yesterday_value = energy_value` und markiert Persist als „dirty“, damit die Korrektur beim nächsten Zyklus mitgespeichert wird.

Damit können nach Neustart keine negativen Daily-/Monthly-/Yearly-Werte mehr aus inkonsistenten persistierten Daten entstehen; die Korrektur ist an Restore, Persist-Anwendung und Persist-Schreiben verankert.

### Migration Electrical (erstes Release)

Beim ersten Start nach einem Update werden bestehende **elektrische** Daily-/Monthly-/Yearly-Sensoren beim Umstieg auf das Delta-Verfahren einmalig migriert: Fehlt in den persistierten Daten das Attribut **`energy_value`**, werden die Werte aus dem zugehörigen Total-Sensor abgeleitet (`restore_state()` nutzt `last_state.state` als Anzeigewert und setzt, falls der Total-Sensor verfügbar ist, `_energy_value` und `_yesterday_value` bzw. `_previous_monthly_value` / `_previous_yearly_value` entsprechend). Der angezeigte Tages-/Monats-/Jahreswert bleibt erhalten, keine negativen Werte. Danach greift die normale Restore-Logik (mit persistiertem `energy_value`). Thermische Sensoren benötigen diese Migration nicht (sie wurden mit dem Delta-Verfahren eingeführt).

## Erweiterungen

### Neue Betriebsmodi hinzufügen

1. Modus zu `ENERGY_CONSUMPTION_MODES` in `const.py` hinzufügen
2. Sensor-Templates in `ENERGY_CONSUMPTION_SENSOR_TEMPLATES` hinzufügen
3. Modus-Mapping in `_track_hp_energy_type_consumption` erweitern

### Neue Zeiträume hinzufügen

1. Zeitraum zu `ENERGY_CONSUMPTION_PERIODS` in `const.py` hinzufügen
2. Sensor-Templates für alle Modi hinzufügen
3. Reset-Logik in `LambdaEnergyConsumptionSensor` erweitern

## Debugging

### Logging

Aktiviere Debug-Logging für detaillierte Informationen:

```yaml
logger:
  default: info
  logs:
    custom_components.lambda_heat_pumps.coordinator: debug
    custom_components.lambda_heat_pumps.utils: debug
```

### Wichtige Log-Meldungen

- `DEBUG-010`: Tracking startet für HP
- `DEBUG-014`: Energie-Offsets werden geladen
- `Energy counters updated`: Sensoren wurden aktualisiert
- `INTERNAL-SENSOR`: Interner Modbus-Sensor wird verwendet

## Tests

Tests befinden sich in `tests/test_energy_consumption_sensors.py`:

- Sensor-Erstellung
- Delta-Berechnung
- Period-Berechnung (daily, monthly, yearly)
- Offset-Anwendung
- Einheitenkonvertierung

## Siehe auch

- [Anwenderdokumentation: Energieverbrauchsberechnung](../Anwender/Energieverbrauchsberechnung.md)
- [Modbus-Register-Dokumentation](modbus-wp-config.md)
- [Ablaufdiagramm](Ablaufdiagramm.md)


