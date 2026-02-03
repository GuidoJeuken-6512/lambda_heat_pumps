---
title: "COP-Sensoren - Technische Dokumentation"
---

# COP-Sensoren - Technische Dokumentation

Diese Dokumentation beschreibt die technische Implementierung der COP-Sensoren (Coefficient of Performance) in der Lambda Heat Pumps Integration.

## Übersicht

Die COP-Sensoren berechnen automatisch die Leistungszahl (COP) einer Wärmepumpe basierend auf dem Verhältnis von thermischer Energie zu elektrischer Energie:

**Formel:** `COP = Thermal Energy (kWh) / Electrical Energy (kWh)`

Die Sensoren werden als echte Python-Entities (`LambdaCOPSensor`) implementiert, nicht als Template-Sensoren, um bessere Performance und direkte Kontrolle zu ermöglichen.

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    sensor.py                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaCOPSensor (RestoreEntity, SensorEntity)        │  │
│  │    - _calculate_cop()                                  │  │
│  │    - _update_cop()                                     │  │
│  │    - State-Tracking (async_track_state_change_event)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            │ Liest States                   │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LambdaEnergyConsumptionSensor (Quellsensoren)       │  │
│  │    - thermal_energy_{period}                         │  │
│  │    - energy_{period}                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss

1. **Sensor-Erstellung** (in `async_setup_entry`):
   - Für jede Wärmepumpe (hp1, hp2, ...)
   - Für jeden Mode (heating, hot_water, cooling)
   - Für jeden Period (daily, monthly, total)
   - Generiere Entity-IDs für Quellsensoren
   - Erstelle `LambdaCOPSensor`-Instanz

2. **Initialisierung** (`async_added_to_hass`):
   - RestoreState von vorherigem Wert (falls vorhanden)
   - Registriere State-Change-Tracker für Quellsensoren
   - Berechne initialen COP-Wert

3. **State-Tracking**:
   - `async_track_state_change_event` überwacht beide Quellsensoren
   - Bei State-Änderung wird `_update_cop()` aufgerufen
   - COP wird neu berechnet und State aktualisiert

4. **COP-Berechnung** (`_calculate_cop`):
   - Liest States von thermal_energy und energy Sensoren
   - Prüft Verfügbarkeit beider Sensoren
   - Berechnet COP = thermal / electrical
   - Division durch Null Schutz (COP = 0.0 wenn electrical <= 0)
   - Rundet auf 2 Dezimalstellen

**Hinweis:** Periodische COP-Sensoren (daily, monthly, yearly) bauen sich erst im Lauf der Zeit auf; bis keine Berechnung stattgefunden hat, können sie `unknown` oder `0` anzeigen. Total-COP nutzt eine Baseline (Deltas seit Stichtag). Siehe [FAQ – COP-Sensoren](../FAQ/cop-sensoren.md).

## Implementierung

### 1. Sensor-Klasse

Die `LambdaCOPSensor` Klasse ist in `sensor.py` implementiert:

```python
class LambdaCOPSensor(RestoreEntity, SensorEntity):
    """COP (Coefficient of Performance) sensor."""
    
    def __init__(
        self,
        hass,
        entry,
        sensor_id,
        name,
        entity_id,
        unique_id,
        unit,
        state_class,
        device_class,
        device_type,
        hp_index,
        mode,
        period,
        thermal_energy_entity_id,
        electrical_energy_entity_id,
    ):
        # ... Initialisierung ...
        self._thermal_energy_entity_id = thermal_energy_entity_id
        self._electrical_energy_entity_id = electrical_energy_entity_id
        self._precision = 2
        self._cop_value = None
```

### 2. Sensor-Registrierung

COP-Sensoren werden in `async_setup_entry` erstellt (nach thermal energy Sensoren):

```python
# COP sensors (per HP, per mode, per period)
cop_modes = ["heating", "hot_water", "cooling"]
cop_periods = ["daily", "monthly", "total"]

for hp_idx in range(1, num_hps + 1):
    for mode in cop_modes:
        for period in cop_periods:
            # Generiere Entity-IDs für Quell-Sensoren
            thermal_entity_id = ...  # z.B. sensor.eu08l_hp1_heating_thermal_energy_daily
            electrical_entity_id = ...  # z.B. sensor.eu08l_hp1_heating_energy_daily
            
            # Erstelle COP-Sensor
            cop_sensor = LambdaCOPSensor(
                hass, entry, sensor_id, name, entity_id, unique_id,
                None,  # Keine Einheit (COP ist dimensionslos)
                "measurement",  # State class
                None,  # Keine device_class
                "hp", hp_idx, mode, period,
                thermal_entity_id, electrical_entity_id,
            )
            sensors.append(cop_sensor)
```

### 3. COP-Berechnung

Die `_calculate_cop()` Methode implementiert die Berechnung:

```python
def _calculate_cop(self) -> float | None:
    """Berechne COP aus thermal_energy und electrical_energy."""
    thermal_state = self.hass.states.get(self._thermal_energy_entity_id)
    electrical_state = self.hass.states.get(self._electrical_energy_entity_id)
    
    # Prüfe Verfügbarkeit
    if not thermal_state or thermal_state.state in (None, "unknown", "unavailable"):
        return None
    if not electrical_state or electrical_state.state in (None, "unknown", "unavailable"):
        return None
    
    # Konvertiere zu float
    thermal_value = float(thermal_state.state)
    electrical_value = float(electrical_state.state)
    
    # Division durch Null Schutz
    if electrical_value <= 0:
        return 0.0
    
    # Berechne COP
    cop = thermal_value / electrical_value
    return round(cop, self._precision)  # 2 Dezimalstellen
```

### 4. State-Tracking

State-Tracking wird in `async_added_to_hass` registriert:

```python
async def async_added_to_hass(self):
    await super().async_added_to_hass()
    
    # RestoreState
    last_state = await self.async_get_last_state()
    await self.restore_state(last_state)
    
    # Registriere State-Change-Tracker
    track_entities = [
        self._thermal_energy_entity_id,
        self._electrical_energy_entity_id,
    ]
    
    @callback
    def _state_change_callback(event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        entity_id = event.data.get("entity_id")
        
        if new_state is None:
            return
        
        if old_state is None or old_state.state != new_state.state:
            self._update_cop()
    
    self._unsub_state_changes = async_track_state_change_event(
        self.hass, track_entities, _state_change_callback
    )
    
    # Initialisiere State
    if self._cop_value is None:
        self._update_cop()
    else:
        self.async_write_ha_state()
```

### 5. State-Update

Die `_update_cop()` Methode wird bei Quellsensor-Änderungen aufgerufen:

```python
@callback
def _update_cop(self):
    """Update COP value when source sensors change."""
    old_cop = self._cop_value
    new_cop = self._calculate_cop()
    
    if new_cop != old_cop:
        self._cop_value = new_cop
        self.async_write_ha_state()
```

## Quellsensoren

Die COP-Sensoren verwenden folgende Quellsensoren:

### Thermische Energie-Sensoren

- **Entity-ID Pattern**: `sensor.{prefix}_hp{idx}_{mode}_thermal_energy_{period}`
- **Beispiel**: `sensor.eu08l_hp1_heating_thermal_energy_daily`
- **Typ**: `LambdaEnergyConsumptionSensor` mit `sensor_type="thermal"`
- **Quelle**: `compressor_thermal_energy_output_accumulated` (Modbus Register 1022)

### Elektrische Energie-Sensoren

- **Entity-ID Pattern**: `sensor.{prefix}_hp{idx}_{mode}_energy_{period}`
- **Beispiel**: `sensor.eu08l_hp1_heating_energy_daily`
- **Typ**: `LambdaEnergyConsumptionSensor` mit `sensor_type="electrical"`
- **Quelle**: `compressor_power_consumption_accumulated` (Modbus Register 1021) oder externer Sensor

## Sensoren pro Wärmepumpe

Für jede Wärmepumpe werden folgende COP-Sensoren erstellt:

| Mode | Period | Sensor-ID | Entity-ID (Beispiel) |
|------|--------|-----------|---------------------|
| heating | daily | `heating_cop_daily` | `sensor.eu08l_hp1_heating_cop_daily` |
| heating | monthly | `heating_cop_monthly` | `sensor.eu08l_hp1_heating_cop_monthly` |
| heating | total | `heating_cop_total` | `sensor.eu08l_hp1_heating_cop_total` |
| hot_water | daily | `hot_water_cop_daily` | `sensor.eu08l_hp1_hot_water_cop_daily` |
| hot_water | monthly | `hot_water_cop_monthly` | `sensor.eu08l_hp1_hot_water_cop_monthly` |
| hot_water | total | `hot_water_cop_total` | `sensor.eu08l_hp1_hot_water_cop_total` |
| cooling | daily | `cooling_cop_daily` | `sensor.eu08l_hp1_cooling_cop_daily` |
| cooling | monthly | `cooling_cop_monthly` | `sensor.eu08l_hp1_cooling_cop_monthly` |
| cooling | total | `cooling_cop_total` | `sensor.eu08l_hp1_cooling_cop_total` |

**Total: 9 COP-Sensoren pro Wärmepumpe**

## State-Management

### RestoreEntity

Die `LambdaCOPSensor` Klasse erbt von `RestoreEntity`, um State-Persistenz zu ermöglichen:

- Werte werden beim HA-Neustart automatisch wiederhergestellt
- `restore_state()` wird in `async_added_to_hass()` aufgerufen
- Falls kein vorheriger State vorhanden ist, wird COP initial berechnet

### State-Class

- **Type**: `SensorStateClass.MEASUREMENT`
- **Zweck**: Für momentane Werte (nicht kumulativ)
- **Recorder**: Werte werden automatisch im Home Assistant Recorder gespeichert
- **Grafana/InfluxDB**: Kompatibel für Visualisierung

## Fehlerbehandlung

### Division durch Null

Wenn `electrical_energy <= 0`, wird COP = 0.0 zurückgegeben:

```python
if electrical_value <= 0:
    return 0.0
```

### Unavailable Quellsensoren

Wenn ein Quellsensor nicht verfügbar ist, wird COP = `None` (unavailable) zurückgegeben:

```python
if not thermal_state or thermal_state.state in (None, "unknown", "unavailable"):
    return None
```

### Fehlerhafte Werte

Bei Konvertierungsfehlern (ValueError, TypeError) wird ein Warning geloggt und `None` zurückgegeben.

### Konsistenz Total-COP (Baseline nach Neustart)

**Problem:** Nach Neustart oder Reset der Quellsensoren können persistierte Baselines (`thermal_baseline`, `electrical_baseline`) höher sein als die aktuellen Werte der thermischen bzw. elektrischen Total-Sensoren. Dann wären die effektiven Deltas negativ (effective_thermal = current − baseline &lt; 0), was zu falschem oder „unavailable“ COP führt.

**Lösung:** Beim Restore der Total-COP-Baselines aus den Attributen wird geprüft:

- Ist `thermal_baseline` größer als der aktuelle State des thermischen Quellsensors → Baseline wird auf den aktuellen Wert gesetzt.
- Ist `electrical_baseline` größer als der aktuelle State des elektrischen Quellsensors → Baseline wird auf den aktuellen Wert gesetzt.

Damit gilt nach dem Restore stets: Baseline ≤ aktueller Quellwert; negative Deltas und daraus resultierende Fehlanzeigen werden vermieden. Die Prüfung erfolgt in `LambdaCOPSensor.restore_state()` (sensor.py).

**Hinweis:** COP daily/monthly/yearly haben keine eigene Baseline; sie lesen nur die Quotienten aus den Energy-Sensoren. Ein Reset-Problem wie bei den Energy-Sensoren (yesterday &gt; energy_value) betrifft sie nicht direkt – sie profitieren von der dortigen Konsistenz-Korrektur.

## Performance

### Vorteile gegenüber Template-Sensoren

1. **Kein Template-Rendering**: Direkte Berechnung ohne Jinja2-Overhead
2. **Direkter State-Zugriff**: Kein Template-Parsing nötig
3. **Optimiertes State-Tracking**: Nur bei tatsächlichen Änderungen
4. **Eigene Entity-Klasse**: Bessere Kontrolle über Update-Verhalten

### State-Tracking-Optimierung

- Nur bei State-Änderungen wird COP neu berechnet
- `old_state.state != new_state.state` Prüfung verhindert unnötige Updates
- Callback-Funktion ist mit `@callback` dekoriert (nicht-blockierend)

## Erweiterbarkeit

### Weitere Zeiträume hinzufügen

Um weitere Zeiträume (z.B. yearly, 2h, 4h) hinzuzufügen:

1. Erweitere `cop_periods` in `async_setup_entry`:
```python
cop_periods = ["daily", "monthly", "total", "yearly", "2h", "4h"]
```

2. Stelle sicher, dass Quellsensoren für diese Perioden existieren
3. Keine weiteren Code-Änderungen nötig

### Weitere Modi hinzufügen

Um weitere Modi (z.B. defrost) hinzuzufügen:

1. Erweitere `cop_modes` in `async_setup_entry`:
```python
cop_modes = ["heating", "hot_water", "cooling", "defrost"]
```

2. Stelle sicher, dass Quellsensoren für diese Modi existieren

## Testing

Die COP-Sensoren können getestet werden durch:

1. **Unit-Tests**: Teste `_calculate_cop()` mit verschiedenen Inputs
2. **Integration-Tests**: Teste Sensor-Erstellung und State-Updates
3. **Manuelle Tests**: Überwache COP-Werte in Home Assistant UI

### Beispiel-Test

```python
def test_cop_calculation():
    sensor = LambdaCOPSensor(...)
    
    # Mock Quellsensoren
    sensor.hass.states.get = Mock(return_value=Mock(state="10.0"))  # thermal
    sensor.hass.states.get = Mock(return_value=Mock(state="2.0"))   # electrical
    
    cop = sensor._calculate_cop()
    assert cop == 5.0
    
    # Division durch Null
    sensor.hass.states.get = Mock(return_value=Mock(state="0.0"))   # electrical
    cop = sensor._calculate_cop()
    assert cop == 0.0
```

## Abhängigkeiten

Die COP-Sensoren sind abhängig von:

- **LambdaEnergyConsumptionSensor**: Quellsensoren müssen existieren
- **State-Tracking**: `async_track_state_change_event` aus Home Assistant
- **RestoreEntity**: Für State-Persistenz

## Code-Stellen

- **Klasse**: `custom_components/lambda_heat_pumps/sensor.py` (Zeile 1413-1641)
- **Registrierung**: `custom_components/lambda_heat_pumps/sensor.py` (Zeile 688-743)
- **Translations**: `custom_components/lambda_heat_pumps/translations/de.json` und `en.json`

## Verwandte Dokumentation

- [Energieverbrauchssensoren](energieverbrauchssensoren.md) - Technische Details zu Quellsensoren
- [Sensor-Implementierung](../Anwender/cop-sensoren.md) - Anwenderdokumentation

