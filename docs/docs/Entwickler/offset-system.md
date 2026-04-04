---
title: "Offset-System"
---

# Offset-System – Technische Dokumentation

*Zuletzt geändert am 28.03.2026*

Das Offset-System ermöglicht es, historische Zählerstände beim Austausch einer Wärmepumpe oder nach einem Zählerreset nahtlos fortzuführen. Es gibt zwei unabhängige Offset-Typen: **Cycling-Offsets** (Betriebszyklen) und **Energie-Offsets** (Verbrauchsmengen in kWh).

---

## Übersicht

| Merkmal | Cycling-Offsets | Energie-Offsets |
|---------|----------------|-----------------|
| Sensor-Klasse | `LambdaCyclingSensor` | `LambdaEnergyConsumptionSensor` |
| Einheit | Zyklen (Integer) | kWh (Float) |
| Betroffene Perioden | nur `*_total` | nur `*_total` |
| YAML-Schlüssel | `cycling_offsets` | `energy_consumption_offsets` |
| Konfiguration | `lambda_wp_config.yaml` | `lambda_wp_config.yaml` |
| Anwendungszeitpunkt | einmal beim HA-Start (async_added_to_hass) | einmal beim HA-Start (async_added_to_hass) |
| Persistierung | Attribut `applied_offset` im HA-State | Attribut `applied_offset` im HA-State |
| Datenspeicherung in utils.py | nein | nein |

---

## 1. Cycling-Offsets

### Welche Sensoren erhalten Cycling-Offsets?

Ausschließlich Sensoren, deren `sensor_id` auf `_total` endet:

| Sensor-ID | Beschreibung |
|-----------|-------------|
| `heating_cycling_total` | Gesamtzahl Heizzyklen |
| `hot_water_cycling_total` | Gesamtzahl Warmwasserzyklen |
| `cooling_cycling_total` | Gesamtzahl Kühlzyklen |
| `defrost_cycling_total` | Gesamtzahl Abtauzyklen |
| `compressor_start_cycling_total` | Gesamtzahl Kompressorstarts |

Daily-, Monthly-, Yearly-Sensoren (`*_daily`, `*_monthly`, `*_yearly`) erhalten **keine** Offsets.

### Wie wird der Offset angewendet? – Differenzmethode

Der Offset wird **nicht blind addiert**, sondern es wird immer nur die **Differenz** zwischen dem aktuell konfigurierten Offset und dem bereits angewendeten Offset (`_applied_offset`) berechnet und addiert. Das verhindert Doppelzählung bei mehrfachem HA-Neustart.

```python
# _apply_cycling_offset() in sensor.py
current_offset = cycling_offsets[device_key].get(self._sensor_id, 0)
applied_offset = getattr(self, "_applied_offset", 0)

offset_difference = current_offset - applied_offset   # Nur die Änderung

if offset_difference != 0:
    self._cycling_value = int(self._cycling_value + offset_difference)
    self._applied_offset = current_offset
    self.async_write_ha_state()
```

**Beispiel:**

| Ereignis | `_cycling_value` | `_applied_offset` | `current_offset` | Differenz |
|----------|----------------:|------------------:|-----------------:|----------:|
| Erststart, Offset = 1500 | 0 → **1500** | 0 → 1500 | 1500 | +1500 |
| HA-Neustart, Offset unverändert | 1500 (restored) | 1500 (restored) | 1500 | 0 – kein Effekt |
| Offset auf 1600 geändert | 1500 → **1600** | 1500 → 1600 | 1600 | +100 |

### Ablauf beim HA-Start

```
async_added_to_hass()
  ├── async_restore_last_state()
  │     ├── _cycling_value  ← aus State
  │     └── _applied_offset ← aus State-Attribut "applied_offset"
  └── _apply_cycling_offset()          ← nur für *_total-Sensoren
        └── Differenz berechnen & ggf. addieren
```

### Persistierung des `applied_offset`

Der bereits angewendete Offset wird als State-Attribut gespeichert, damit er nach einem HA-Neustart wiederhergestellt werden kann:

```python
# extra_state_attributes (LambdaCyclingSensor, sensor.py)
if self._sensor_id.endswith("_total"):
    attrs["applied_offset"] = getattr(self, "_applied_offset", 0)
```

Bei `async_restore_last_state()` wird er zurückgelesen:
```python
self._applied_offset = last_state.attributes.get("applied_offset", 0)
```

### Beziehung zu `increment_cycling_counter()` (utils.py)

`increment_cycling_counter()` erhöht den Zähler bei jedem erkannten Zustandswechsel um **genau 1** – **ohne** Offset-Logik. Der Offset wird ausschließlich durch `_apply_cycling_offset()` beim Start angewendet. Dies war vor V2.4.0 eine Fehlerquelle (Bug B-1): Die Funktion addierte fälschlicherweise den vollen YAML-Offset bei jedem Zyklus-Ereignis.

```python
# increment_cycling_counter() – korrekte Version (seit V2.4.0)
new_value = int(current + 1)   # immer +1, kein Offset
cycling_entity.set_cycling_value(new_value)
```

---

## 2. Energie-Offsets

### Welche Sensoren erhalten Energie-Offsets?

Ausschließlich `*_total`-Sensoren der Klasse `LambdaEnergyConsumptionSensor`. Es gibt zwei Untertypen:

**Elektrische Energie-Offsets** (`{mode}_energy_total`):

| Sensor-ID | Beschreibung |
|-----------|-------------|
| `heating_energy_total` | Elektrischer Gesamtverbrauch Heizen |
| `hot_water_energy_total` | Elektrischer Gesamtverbrauch Warmwasser |
| `cooling_energy_total` | Elektrischer Gesamtverbrauch Kühlen |
| `defrost_energy_total` | Elektrischer Gesamtverbrauch Abtauen |

**Thermische Energie-Offsets** (`{mode}_thermal_energy_total`, optional):

| Sensor-ID | Beschreibung |
|-----------|-------------|
| `heating_thermal_energy_total` | Thermischer Gesamtoutput Heizen |
| `hot_water_thermal_energy_total` | Thermischer Gesamtoutput Warmwasser |
| `cooling_thermal_energy_total` | Thermischer Gesamtoutput Kühlen |
| `defrost_thermal_energy_total` | Thermischer Gesamtoutput Abtauen |

### Wie wird der Offset angewendet? – Differenzmethode

Gleiche Logik wie bei Cycling-Offsets. Der Sensor-Schlüssel wird aus `mode` und Sensor-Typ (`electrical` / `thermal`) zusammengesetzt:

```python
# _apply_energy_offset() in sensor.py
sensor_id = f"{self._mode}_energy_total"          # elektrisch
# oder:
sensor_id = f"{self._mode}_thermal_energy_total"  # thermisch

current_offset = energy_offsets[device_key].get(sensor_id, 0.0)
applied_offset = getattr(self, "_applied_offset", 0.0)
offset_difference = current_offset - applied_offset

if offset_difference != 0:
    self._energy_value += float(offset_difference)
    self._applied_offset = current_offset
    self.async_write_ha_state()
```

### Ablauf beim HA-Start

```
async_added_to_hass()
  ├── async_restore_last_state()
  │     ├── _energy_value   ← aus State
  │     └── _applied_offset ← aus State-Attribut "applied_offset"
  └── _apply_energy_offset()            ← nur für period == "total"
        └── Differenz berechnen & ggf. addieren
```

### Persistierung des `applied_offset`

```python
# extra_state_attributes (LambdaEnergyConsumptionSensor, sensor.py)
attrs["applied_offset"] = self._applied_offset
```

Wiederherstellung:
```python
self._applied_offset = float(attrs.get("applied_offset", 0.0))
```

### Beziehung zu `increment_energy_consumption_counter()` (utils.py)

Diese Funktion liest den Quellsensor (externer Verbrauchssensor), berechnet das Delta zum letzten Wert und schreibt es auf alle 7 Perioden (`ENERGY_INCREMENT_PERIODS`):

```python
ENERGY_INCREMENT_PERIODS = ["total", "daily", "monthly", "yearly", "2h", "4h", "hourly"]
```

Der Energie-Offset wird dabei **nicht** in `increment_energy_consumption_counter()` angewendet, sondern ausschließlich durch `_apply_energy_offset()` beim HA-Start.

---

## 3. Struktur der `lambda_wp_config.yaml`

Die Konfigurationsdatei liegt unter `config/lambda_wp_config.yaml` und enthält fünf Abschnitte. Offsets befinden sich in `cycling_offsets` und `energy_consumption_offsets`.

### Vollständige annotierte Struktur

```yaml
# ─────────────────────────────────────────────────────────────
# 1. Deaktivierte Modbus-Register (Pflichtfeld, kann leer sein)
# ─────────────────────────────────────────────────────────────
disabled_registers:
  - 2004   # Beispiel: boil1_actual_circulation_temp deaktivieren

# ─────────────────────────────────────────────────────────────
# 2. Sensor-Namen überschreiben (nur bei use_legacy_modbus_names: true)
# ─────────────────────────────────────────────────────────────
#sensors_names_override:
#- id: name_of_the_sensor_to_override_example
#  override_name: new_name_of_the_sensor_example

# ─────────────────────────────────────────────────────────────
# 3. Cycling-Offsets  (Integer, positiv oder negativ)
# ─────────────────────────────────────────────────────────────
cycling_offsets:
  hp1:
    heating_cycling_total: 1200            # HP1 hatte bereits 1200 Heizzyklen
    hot_water_cycling_total: 450
    cooling_cycling_total: 0
    defrost_cycling_total: 30
    compressor_start_cycling_total: 8500   # Gesamtzahl Kompressorstarts
  hp2:
    heating_cycling_total: 0
    hot_water_cycling_total: 0
    cooling_cycling_total: 0
    defrost_cycling_total: 0
    compressor_start_cycling_total: 0

# ─────────────────────────────────────────────────────────────
# 4. Quellsensoren für die Energieverbrauchsberechnung
# ─────────────────────────────────────────────────────────────
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.lambda_wp_verbrauch"           # elektrisch (Wh oder kWh)
    # thermal_sensor_entity_id: "sensor.lambda_wp_waerme"   # thermisch, optional (Wh oder kWh)
  # hp2:
  #   sensor_entity_id: "sensor.lambda_wp_verbrauch2"

# ─────────────────────────────────────────────────────────────
# 5. Energie-Offsets  (Float in kWh, positiv oder negativ)
#    Wirken ausschließlich auf *_total-Sensoren
# ─────────────────────────────────────────────────────────────
energy_consumption_offsets:
  hp1:
    # Elektrische Offsets:
    heating_energy_total: 1500.75          # kWh, HP1 hatte schon 1500,75 kWh Heizen
    hot_water_energy_total: 320.0
    cooling_energy_total: 0.0
    defrost_energy_total: 12.5
    # Thermische Offsets (optional):
    heating_thermal_energy_total: 6500.0   # kWh thermischer Output Heizen
    hot_water_thermal_energy_total: 1400.0

# ─────────────────────────────────────────────────────────────
# 6. Modbus-Konfiguration
# ─────────────────────────────────────────────────────────────
#modbus:
#  int32_register_order: "high_first"   # oder "low_first"
```

### Schlüssel-Referenz

#### `cycling_offsets`

```
cycling_offsets:
  hp{N}:                               # N = 1..num_hps
    {mode}_cycling_total: <int>
```

| Platzhalter | Erlaubte Werte |
|-------------|----------------|
| `{N}` | 1, 2, … (Anzahl der Wärmepumpen) |
| `{mode}` | `heating`, `hot_water`, `cooling`, `defrost`, `compressor_start` |
| Wert | Integer, positiv oder negativ |

#### `energy_consumption_offsets`

```
energy_consumption_offsets:
  hp{N}:
    {mode}_energy_total: <float>              # elektrisch
    {mode}_thermal_energy_total: <float>      # thermisch, optional
```

| Platzhalter | Erlaubte Werte |
|-------------|----------------|
| `{N}` | 1, 2, … |
| `{mode}` | `heating`, `hot_water`, `cooling`, `defrost` |
| Wert | Float in **kWh**, positiv oder negativ |

**Wichtig:** Werte immer in **kWh** angeben. Der Quellsensor darf Wh oder kWh liefern – die Konvertierung erfolgt automatisch in `increment_energy_consumption_counter()`.

---

## 4. Validierung der Offset-Werte

Ungültige Offset-Einträge werden beim Laden der Konfiguration abgefangen (`load_lambda_config()` / `utils.py`). Die Validierung prüft ausschließlich, ob der Wert numerisch ist:

```python
if not isinstance(value, (int, float)):
    _LOGGER.warning("Ungültiger Offset-Wert %s für %s – wird ignoriert (Wert = 0)", value, key)
    value = 0
```

Negative Werte sind **ausdrücklich erlaubt** – sie subtrahieren vom Gesamtwert (z. B. nach einem Zählerreset auf einen bekannten Zwischenstand).

---

## 5. Gesamtablauf – Sequenzdiagramm

```
HA-Start
  │
  ├─ load_lambda_config()           → liest lambda_wp_config.yaml, cacht in hass.data
  │
  ├─ LambdaCyclingSensor.async_added_to_hass()   [für jeden *_total-Sensor]
  │     ├─ Restore: _cycling_value, _applied_offset
  │     └─ _apply_cycling_offset()
  │           ├─ current_offset  ← aus cycling_offsets[hp{N}][sensor_id]
  │           ├─ offset_diff     = current_offset - _applied_offset
  │           ├─ _cycling_value += offset_diff   (nur wenn ≠ 0)
  │           └─ _applied_offset = current_offset
  │
  └─ LambdaEnergyConsumptionSensor.async_added_to_hass()  [für jeden *_total-Sensor]
        ├─ Restore: _energy_value, _applied_offset
        └─ _apply_energy_offset()
              ├─ current_offset  ← aus energy_consumption_offsets[hp{N}][{mode}_energy_total]
              │                     oder [hp{N}][{mode}_thermal_energy_total]
              ├─ offset_diff     = current_offset - _applied_offset
              ├─ _energy_value  += offset_diff    (nur wenn ≠ 0)
              └─ _applied_offset = current_offset

Laufender Betrieb
  ├─ increment_cycling_counter()     → +1, kein Offset
  └─ increment_energy_consumption_counter() → Delta aus Quellsensor, kein Offset
```

---

## 6. Betroffene Dateien

| Datei | Rolle |
|-------|-------|
| `custom_components/lambda_heat_pumps/sensor.py` | `_apply_cycling_offset()`, `_apply_energy_offset()`, `extra_state_attributes` |
| `custom_components/lambda_heat_pumps/utils.py` | `increment_cycling_counter()`, `increment_energy_consumption_counter()`, `load_lambda_config()` |
| `custom_components/lambda_heat_pumps/const_base.py` | `LAMBDA_WP_CONFIG_TEMPLATE`, `ENERGY_INCREMENT_PERIODS` |
| `config/lambda_wp_config.yaml` | Konfigurationsdatei (Laufzeit) |
| `tests/test_offset_features.py` | Unit-Tests für alle Offset-Szenarien |
