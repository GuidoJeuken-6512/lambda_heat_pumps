# Offset-Fehleranalyse: `cycling_offsets` und `energy_consumption_offsets`

**Version:** 2.3
**Analysedatum:** 21. Februar 2026
**Branch:** Release2.3 (Commit fcd9a83)

---

## Inhaltsverzeichnis

1. [Zusammenfassung](#1-zusammenfassung)
2. [Konfiguration und Soll-Verhalten](#2-konfiguration-und-soll-verhalten)
3. [Bug 1 – Kritisch: Cycling-Offset bei jedem Zyklus-Event erneut addiert](#3-bug-1--kritisch-cycling-offset-bei-jedem-zyklus-event-erneut-addiert)
4. [Bug 2 – Mittel: Daily/Energy-Offset alle 30 Sekunden addiert](#4-bug-2--mittel-dailyenergy-offset-alle-30-sekunden-addiert)
5. [Bug 3 – Mittel: Zwei konkurrierende Offset-Mechanismen](#5-bug-3--mittel-zwei-konkurrierende-offset-mechanismen)
6. [Referenzimplementierung: Energie-Sensor (korrekt)](#6-referenzimplementierung-energie-sensor-korrekt)
7. [Empfohlene Korrekturen](#7-empfohlene-korrekturen)
8. [Betroffene Dateien](#8-betroffene-dateien)

---

## 1. Zusammenfassung

Benutzer berichten, dass konfigurierte Offsets aus der `lambda_wp_config.yaml` nicht einmalig angewendet werden, sondern sich bei jedem Sensor-Update aufaddieren. Die Codeanalyse bestätigt dies und identifiziert **drei unabhängige Bugs**:

| # | Schweregrad | Ort | Beschreibung |
|---|---|---|---|
| B-1 | **Kritisch** | utils.py:901 | Voller YAML-Offset wird bei **jedem Zyklus-Ereignis** auf den Total-Sensor addiert → exponentieller Wertzuwachs |
| B-2 | Mittel | coordinator.py:1974/1982 | `_daily`-Offset wird alle 30 s in den Coordinator-Data-Dict geschrieben |
| B-3 | Mittel | utils.py vs sensor.py | Zwei parallele Offset-Mechanismen für Total-Sensoren – einer ist korrekt, einer nicht |

---

## 2. Konfiguration und Soll-Verhalten

### YAML-Konfiguration

```yaml
# lambda_wp_config.yaml

cycling_offsets:
  hp1:
    heating_cycling_total: 1500    # HP1 hatte bereits 1500 Heizungszyklen
    hot_water_cycling_total: 800
    cooling_cycling_total: 200
    defrost_cycling_total: 50

energy_consumption_offsets:
  hp1:
    heating_energy_total: 12500.0  # kWh-Offset für HP1 Heizungs-Total
    hot_water_energy_total: 3200.0
```

**Anwendungsfall:** Die Wärmepumpe wurde ausgetauscht oder der Zähler zurückgesetzt. Der Offset entspricht dem Vorwert und soll **genau einmal** eingerechnet werden, damit die Gesamtzähler historisch korrekt bleiben.

### Soll-Verhalten (erwartet)

```
Ausgangslage: actual_count = 100, offset = 1500

Nach Konfiguration:  Sensor = 100 + 1500 = 1600  ✓
Nach Zyklus 1:       Sensor = 1601               ✓  (+1)
Nach Zyklus 2:       Sensor = 1602               ✓  (+1)
Nach N Zyklen:       Sensor = 1600 + N           ✓
```

### Ist-Verhalten (Bug B-1)

```
Nach Konfiguration:  Sensor = 1600               ✓
Nach Zyklus 1:       Sensor = 3101               ✗  (+1 + 1500 erneut!)
Nach Zyklus 2:       Sensor = 4602               ✗  (+1 + 1500 erneut!)
Nach N Zyklen:       Sensor = 100 + N + (N+1)×1500
Bei N=10:            Sensor = 16610 statt 1610   ✗  (Abweichung: +15000!)
```

---

## 3. Bug 1 – Kritisch: Cycling-Offset bei jedem Zyklus-Event erneut addiert

### Ort

[utils.py](../../custom_components/lambda_heat_pumps/utils.py) · Funktion `increment_cycling_counter()` · Zeile ~880–914

### Fehlerhafter Code

```python
# Zeile 880-887: Offset wird aus YAML geladen – VOLL, ohne Differenzbildung
offset = 0
if cycling_offsets is not None and sensor_id.endswith("_total"):
    device_key = device_prefix
    if device_key in cycling_offsets:
        offset = int(cycling_offsets[device_key].get(sensor_id, 0))

new_value = int(current + 1)   # korrekt: +1 Inkrement

# ...

final_value = int(new_value + offset)   # ← ZEILE 901: BUG!
# offset = volles YAML-Offset (z.B. 1500), KEIN _applied_offset-Tracking
```

### Ursache

`increment_cycling_counter()` wird **bei jedem erkannten Zyklus-Flankenwechsel** aufgerufen (Betriebszustand wechselt z.B. von Standby auf Heizen). Die Funktion liest den vollen YAML-Offset-Wert und addiert ihn ohne Rücksicht darauf, ob er bereits auf dem Sensorwert enthalten ist.

Da `_apply_cycling_offset()` (sensor.py) beim HA-Start den Offset **bereits einmalig** in `_cycling_value` einrechnet, kommt es zur Doppel- und Mehrfach-Anwendung:

```
HA-Start:
  Gespeicherter Wert:       100
  _apply_cycling_offset():  100 + 1500 = 1600   ← korrekt
  _applied_offset = 1500

Zyklus-Ereignis 1:
  increment_cycling_counter() aufgerufen
  current = 1600   (enthält Offset bereits!)
  offset  = 1500   (aus YAML – kein Tracking, ob bereits angewendet)
  new_value   = 1600 + 1 = 1601
  final_value = 1601 + 1500 = 3101   ← +1500 zu viel!

Zyklus-Ereignis 2:
  current = 3101
  final_value = 3101 + 1 + 1500 = 4602   ← +1500 wieder zu viel!

Formel nach N Zyklen:
  Sensor = initial_count + N + (N+1) × offset
```

### Vergleich zum korrekt implementierten Energie-Sensor

`increment_energy_consumption_counter()` (utils.py:1447) löst genau dasselbe Problem korrekt:

```python
# utils.py:1447-1452 – KORREKT: nur die Differenz addieren
if hasattr(energy_entity, "_applied_offset"):
    if energy_entity._applied_offset != offset:
        new_value += offset - energy_entity._applied_offset  # nur Differenz!
        energy_entity._applied_offset = offset               # merken
```

Das Cycling-Pendant fehlt vollständig.

---

## 4. Bug 2 – Mittel: Daily/Energy-Offset alle 30 Sekunden addiert

### Ort

[coordinator.py](../../custom_components/lambda_heat_pumps/coordinator.py) · Methode `_async_update_data()` · Zeile ~1959–1982

### Fehlerhafter Code

```python
# Zeile 1960-1982 – innerhalb des 30s-Update-Zyklus

# Sucht nach {mode}_cycling_daily in der YAML (undokumentiert!)
hp_cycling_offsets = self._cycling_offsets.get(f"hp{hp_idx}", {})
cycling_offset = hp_cycling_offsets.get(f"{mode}_cycling_daily", 0)

# Sucht nach {mode}_energy_daily in der YAML (undokumentiert!)
energy_offset = self._energy_offsets.get(f"hp{hp_idx}", {})
energy_sensor_offset = energy_offset.get(f"{mode}_energy_daily", 0.0)

# Beide Werte werden JEDE RUNDE in den Coordinator-Data-Dict geschrieben:
data[cycling_entity_id] = cycles.get(hp_idx, 0) + cycling_offset       # alle 30s
data[energy_entity_id]  = energy_value + energy_sensor_offset           # alle 30s
```

### Wirkung

Der Code sucht nach YAML-Schlüsseln wie `heating_cycling_daily` oder `heating_energy_daily`. Diese Schlüssel sind in der **Dokumentation nicht erwähnt** – es sind nur `_total`-Offsets dokumentiert.

Wenn ein Benutzer versehentlich einen `_daily`-Offset einträgt (z.B. Tippfehler `heating_cycling_daily: 5` statt `heating_cycling_total: 5`):

```
Tagesreset um 00:00 Uhr: cycles = 0
00:00:30  → data[daily] = 0 + 5 = 5   (kein echter Zyklus stattgefunden)
00:01:00  → data[daily] = 0 + 5 = 5   (konstant falsch)
Nach 1 echtem Zyklus: data[daily] = 1 + 5 = 6   (statt 1)
```

Der Sensor hat täglich einen festen, falschen Aufschlag. Der Fehler setzt sich nach jedem Tagesreset erneut fort.

### Zusätzliches Risiko

Wenn `cycles.get(hp_idx, 0)` aus irgendeinem Grund keinen absoluten, sondern einen akkumulierten Wert liefert, könnte die Addition sogar über Updatezyklen wachsen – dann wäre das Verhalten ähnlich wie Bug 1.

---

## 5. Bug 3 – Mittel: Zwei konkurrierende Offset-Mechanismen

### Beschreibung

Für Total-Cycling-Sensoren existieren **zwei parallele Mechanismen**, die beide den Offset anwenden wollen:

| Mechanismus | Datei / Zeile | Zeitpunkt | `_applied_offset`-Tracking |
|---|---|---|---|
| `_apply_cycling_offset()` | sensor.py:1032 | Einmalig beim HA-Start (`async_added_to_hass`) | **Ja** – korrekt implementiert |
| `increment_cycling_counter()` | utils.py:901 | Bei jedem Zyklus-Ereignis | **Nein** – volles Offset jedes Mal |

Da beide denselben Sensor beeinflussen, ist das Ergebnis unvorhersehbar. Mechanismus 1 ist korrekt; Mechanismus 2 überschreibt den korrekten Wert mit einem falschen.

### Ablauf

```
HA-Start
│
├─► async_added_to_hass()
│   ├─► _cycling_value = 100   (aus Restore)
│   ├─► _applied_offset = 0
│   └─► _apply_cycling_offset()         ← Mechanismus 1 (KORREKT)
│       ├─► offset     = 1500  (aus YAML)
│       ├─► applied    = 0
│       ├─► diff       = 1500
│       ├─► _cycling_value = 1600       ← korrekt!
│       └─► _applied_offset = 1500
│
[30 Minuten: Heizzyklus startet]
│
└─► increment_cycling_counter()         ← Mechanismus 2 (FALSCH)
    ├─► current     = 1600  (aus state)
    ├─► offset      = 1500  (aus YAML – kein Tracking!)
    ├─► new_value   = 1601
    ├─► final_value = 3101              ← falsch!
    └─► set_cycling_value(3101)
        → _cycling_value = 3101  (überschreibt korrekten Wert)
        → _applied_offset = 1500 (nutzlos geworden)
```

---

## 6. Referenzimplementierung: Energie-Sensor (korrekt)

Das Offset-Handling in `increment_energy_consumption_counter()` ist korrekt und kann als Vorlage für die Korrektur von Bug 1 dienen:

```python
# utils.py:1437-1452 – KORREKT implementiert

# Offset nur für Total-Sensor berücksichtigen
if period == "total" and energy_offsets is not None:
    device_key = device_prefix
    if device_key in energy_offsets:
        device_offsets = energy_offsets[device_key]
        if isinstance(device_offsets, dict):
            sensor_id = f"{mode}_energy_total"
            offset = float(device_offsets.get(sensor_id, 0.0))

            # Prüfe ob Offset bereits angewendet wurde
            if hasattr(energy_entity, "_applied_offset"):
                if energy_entity._applied_offset != offset:
                    new_value += offset - energy_entity._applied_offset  # nur Differenz
                    energy_entity._applied_offset = offset
                    _LOGGER.info(f"Applied offset {offset:.2f} kWh to {entity_id}")
```

**Drei Prinzipien dieser korrekten Implementierung:**

1. `_applied_offset` auf der Entity speichern (was wurde bisher angewendet)
2. Nur die **Differenz** `offset - _applied_offset` zum Wert addieren
3. `_applied_offset` danach auf `offset` setzen, damit der nächste Aufruf nichts tut

Zusätzlich wird `_applied_offset` in den State-Attributen persistiert (sensor.py:1710), damit der Wert einen HA-Neustart übersteht:

```python
# sensor.py:1710 – Persistierung in State-Attributen
attrs["applied_offset"] = self._applied_offset

# sensor.py:1502 – Wiederherstellung nach Neustart
self._applied_offset = float(attrs.get("applied_offset", 0.0))
```

---

## 7. Empfohlene Korrekturen

### Fix für Bug 1 (Kritisch)

**Ort:** [utils.py](../../custom_components/lambda_heat_pumps/utils.py), `increment_cycling_counter()`, Zeile ~880–914

**Option A (empfohlen): Offset-Block aus `increment_cycling_counter()` entfernen**

Da `_apply_cycling_offset()` in sensor.py den Offset bereits korrekt einmalig anwendet, muss `increment_cycling_counter()` den Offset gar nicht kennen. Der Block kann ersatzlos entfernt werden:

```python
# VORHER (fehlerhaft):
offset = 0
if cycling_offsets is not None and sensor_id.endswith("_total"):
    device_key = device_prefix
    if device_key in cycling_offsets:
        offset = int(cycling_offsets[device_key].get(sensor_id, 0))

new_value = int(current + 1)
# ...
final_value = int(new_value + offset)   # ← entfernen

# NACHHER (korrekt – Option A):
new_value = int(current + 1)
# ...
final_value = new_value   # kein Offset mehr hier
```

**Option B: Differenzbasiertes Tracking (analog Energie-Sensor)**

Falls der Offset in `increment_cycling_counter()` absichtlich erhalten bleiben soll (z.B. für Fälle ohne funktionierende `_apply_cycling_offset()`):

```python
# NACHHER (korrekt – Option B):
new_value = int(current + 1)

# Offset nur als Differenz anwenden – analog increment_energy_consumption_counter
if cycling_offsets is not None and sensor_id.endswith("_total"):
    device_key = device_prefix
    if device_key in cycling_offsets and cycling_entity is not None:
        offset = int(cycling_offsets[device_key].get(sensor_id, 0))
        if hasattr(cycling_entity, "_applied_offset"):
            if int(cycling_entity._applied_offset) != offset:
                new_value += offset - int(cycling_entity._applied_offset)
                cycling_entity._applied_offset = offset

final_value = new_value
```

### Fix für Bug 2 (Mittel)

**Ort:** [coordinator.py](../../custom_components/lambda_heat_pumps/coordinator.py), `_async_update_data()`, Zeile ~1959–1982

Daily- und Energy-Daily-Offsets aus dem Coordinator-Update entfernen. Offsets sind ausschließlich für `_total`-Sensoren vorgesehen und werden durch die Sensor-Klassen selbst verwaltet:

```python
# VORHER (fehlerhaft):
cycling_offset = hp_cycling_offsets.get(f"{mode}_cycling_daily", 0)
energy_sensor_offset = energy_offset.get(f"{mode}_energy_daily", 0.0)

data[cycling_entity_id] = cycles.get(hp_idx, 0) + cycling_offset
data[energy_entity_id]  = energy_value + energy_sensor_offset

# NACHHER (korrekt):
data[cycling_entity_id] = cycles.get(hp_idx, 0)   # kein Offset
data[energy_entity_id]  = energy_value             # kein Offset
```

Die zugehörigen Offset-Lookup-Blöcke (Zeile 1959–1972) können ebenfalls vollständig entfernt werden.

### Fix für Bug 3 (Mittel)

Nach Anwenden von Fix B-1 Option A existiert nur noch ein Offset-Mechanismus (`_apply_cycling_offset()` in sensor.py). Kein weiterer Eingriff nötig.

Falls Option B gewählt wird: `_apply_cycling_offset()` in sensor.py muss dann **nicht mehr** vom Start aus aufgerufen werden, da `increment_cycling_counter()` den Offset beim ersten Zyklus-Event korrekt einsetzt. In diesem Fall die Zeile in `async_added_to_hass()` entfernen:

```python
# sensor.py:1029 – nur bei Option B entfernen:
if self._sensor_id.endswith("_total"):
    await self._apply_cycling_offset()   # ← entfernen wenn Option B gewählt
```

---

## 8. Betroffene Dateien

| Datei | Zeile (ca.) | Bug | Aktion |
|---|---|---|---|
| [utils.py](../../custom_components/lambda_heat_pumps/utils.py) | 880–914 | B-1, B-3 | `increment_cycling_counter()`: Offset-Block entfernen (Option A) oder durch Differenz-Tracking ersetzen (Option B) |
| [coordinator.py](../../custom_components/lambda_heat_pumps/coordinator.py) | 1959–1982 | B-2 | Daily-Offset-Lookup und Addition aus `_async_update_data()` entfernen |
| [sensor.py](../../custom_components/lambda_heat_pumps/sensor.py) | 1032–1085 | B-3 | `_apply_cycling_offset()` – keine Änderung (korrekt); ggf. Aufruf entfernen wenn Option B gewählt |

### Keine Änderungen nötig

| Datei | Grund |
|---|---|
| sensor.py `_apply_energy_offset()` (Zeile 1594) | Korrekt implementiert |
| utils.py `increment_energy_consumption_counter()` Offset-Block (Zeile 1437) | Korrekt implementiert |
| YAML-Dokumentation für `_total`-Offsets | Korrekt dokumentiert |

---

*Dokument erstellt durch Codeanalyse von Release2.3 (Commit fcd9a83).*
