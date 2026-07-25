---
title: "Release 2.8.0"
---

# Release 2.8.0

*Zuletzt geändert am 25.07.2026*

> **Aktueller Release** · Branch `V2.8.0`

---

## Zusammenfassung

Release 2.8.0 behebt vier Befunde aus [Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100) (Datenschaden durch implausible Energie-Sprünge, ungefilterte Lambda-Sentinel-Rohwerte, ein W-only-Register mit ungültigem Lesewert sowie eine seit jeher wirkungslose Firmware-Filterung bei General Sensors) und führt dafür zwei neue, generische Mechanismen ein: Range-Notation für `firmware_versions` und opt-in Sentinel-Werte pro Sensor. Keine Breaking Changes; alle bestehenden `firmware_version: X`-Sensoren bleiben unverändert.

---

## Neue Funktionen

### Range-Notation für Firmware-Versionen (`firmware_versions`)

**Betroffen:** `custom_components/lambda_heat_pumps/utils.py`

Bisher konnte ein Sensor-Template nur ein **Minimum** an Firmware-Version verlangen (`"firmware_version": X` → aktiv ab Version X, ohne Obergrenze). Für Register, die auf neueren Steuerungsgenerationen wieder verschwinden (siehe Befund unten), reicht das nicht aus. Neue Funktion `_parse_firmware_versions()`:

```python
def _parse_firmware_versions(spec: list) -> set:
    """
    "X-Y"  -> Bereich X bis Y inklusive
    "-X"   -> Version X ausschließen
    X      -> Version X einschließen (int)
    """
```

`get_compatible_sensors()` prüft jetzt in dieser Reihenfolge:

1. `firmware_versions` (Range-Notation) — falls vorhanden
2. `firmware_version` (Minimum, bestehendes Verhalten) — falls kein `firmware_versions`
3. Kein Feld → immer aktiv

Beispiel: `"firmware_versions": ["1-7"]` — Sensor nur für Firmware-Ganzzahl 1 bis 7 aktiv, verschwindet ab Version 8.

### Opt-in Sentinel-Werte pro Sensor (`sentinel_values`)

**Betroffen:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

`is_sentinel_value()` (siehe Befund 2 unten) filtert global nur `0x8000` und die Temperatur-Fühler-Sentinel `-3000`. Der Wert `-1` (`0xFFFF`) ist **bewusst kein** globaler Sentinel, da er bei manchen Sensoren (z. B. Temperatur-Offsets) ein gültiger Messwert ist. Für Register, bei denen `-1` tatsächlich "nicht verfügbar" bedeutet, kann das jetzt pro Sensor-Template opt-in aktiviert werden:

```python
"sentinel_values": [65535],
```

`is_sentinel_value(raw_value, data_type, extra_sentinels)` prüft diese Liste zusätzlich zu den globalen Sentinels.

Bereits angewendet auf die definierten Anforderungsregister, bei denen `-1` "keine Anforderung" bedeutet: Buffer 3005–3009 (`request_type`, `request_flow_line_temp_setpoint`, `request_return_line_temp_setpoint`, `request_heat_sink_temp_diff_setpoint`, `modbus_request_heating_capacity`) und HC 5006 (`operating_mode`) — jeweils `"sentinel_values": [65535]`. Alle anderen Buffer-/HC-Sensoren sind davon unberührt.

---

## Fehlerbehebungen ([#100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/100))

### Befund 1 — `calculate_energy_delta` kappte implausible Sprünge statt sie zu verwerfen

**Betroffen:** Energie-Verbrauchssensoren aller Wärmepumpen.

**Symptom:** Nach einem implausiblen Register-Sprung (z. B. durch eine geänderte `int32_register_order`, siehe Release 2.7.0) wurde die Differenz auf `max_delta` gekappt und als echter Verbrauch gebucht — Datenschaden im Zähler.

**Fix:** `calculate_energy_delta()` gibt bei einem Delta über `max_delta` jetzt `None` zurück, statt zu kappen. Der Caller in `coordinator.py` erkennt `None`, setzt die Referenz auf den aktuellen Wert zurück und bucht **nichts**.

**Schwellenwert ausgelagert und verschärft:** `max_delta` war zunächst als Literal `100.0` (kWh) an zwei Stellen hartkodiert (Funktions-Default in `utils.py` **und** expliziter Aufruf in `coordinator.py`). Jetzt einzige Quelle: `MAX_ENERGY_DELTA_WH = 5000` in `const_base.py` (5 kWh statt vorher 100 kWh). Der `coordinator.py`-Aufruf übergibt `max_delta` nicht mehr explizit, sondern nutzt den Default. Der Wert stammt aus einer Analyse in `docs_md/ToDos/auto_32bit_register_handling.md`: Ein echter Register-Order-Flip springt um Vielfache von 65.536 (typischerweise mehrere MWh), realistische Verbrauchssprünge pro Update-Zyklus liegen im Bereich weniger hundert Wh — `5000 Wh` liegt damit weit über normalem Verbrauch, aber weit unter jedem Flip. Nur dieser Schwellenwert wurde übernommen; das dort skizzierte vollständige Konzept einer automatischen Flip-Erkennung ist **nicht** Teil dieses Releases.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/const_base.py`, `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Befund 2 — Lambda-Sentinel-Rohwerte wurden nie gefiltert

**Betroffen:** Alle int16-Register, insbesondere Temperatur-Sensoren.

**Symptom:** Das Lambda-Modbus-Protokoll 1.0 definiert Sentinel-Rohwerte für "Register nicht vorhanden" (`32768` / `0x8000`) und "Fühler nicht angeschlossen" (`62536`, `-3000` als `int16`). Diese wurden bislang ungefiltert skaliert und als reale Messwerte gespeichert (z. B. eine "Temperatur" von −300 °C).

**Fix:** Neue Funktion `is_sentinel_value()` prüft den unskalierten Rohwert, bevor `scale` angewendet wird. Betroffene Sensoren werden auf `None` (→ Entity `unavailable`) gesetzt, mit einem `INFO`-Log-Eintrag (Rohwert, Register-Adresse, Sensor-ID). Angewendet an allen fünf Stellen, an denen Register gelesen und skaliert werden: Batch-Read, Einzel-Read-Fallback, Boiler, Puffer, Solar.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/utils.py`, `custom_components/lambda_heat_pumps/coordinator.py`

### Befund 4a — `ambient_temperature` (Register 0002) liefert auf mancher Firmware einen ungültigen Wert

**Betroffen:** Register 0002 (`ambient_temperature`), alle Firmware-Versionen.

**Symptom:** Register 0002 ist ab einer bestimmten Firmware-Generation als W-only dokumentiert (Einspeisen einer externen Außentemperatur) und liefert beim Lesen `0xFFFF` = −300 °C zurück. Auf älterer Firmware kann das Register hingegen echte Temperaturwerte liefern — ein pauschales Entfernen des Sensors wäre daher zu grob gewesen.

**Fix:** `ambient_temperature` bleibt erhalten, ist aber jetzt nur noch bis `V0.0.9-3K` (Firmware-Ganzzahl 7) verfügbar (`"firmware_versions": ["1-7"]`) und nutzt zusätzlich `"sentinel_values": [65535]`, um `0xFFFF` speziell für diesen Sensor als "nicht verfügbar" zu filtern — andere Sensoren mit gültigem `-1`-Wert (z. B. Temperatur-Offsets) sind davon nicht betroffen.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/const_sensor.py`

### Nebenbefund — General Sensors wurden nie nach Firmware-Version gefiltert

**Betroffen:** Alle General Sensors (`SENSOR_TYPES`), u. a. `ambient_temperature`.

**Symptom:** Beim Umsetzen von Befund 4a fiel auf, dass die General-Sensor-Gruppe (`SENSOR_TYPES`) — anders als HP-/Boiler-/Puffer-/Solar-/Heizkreis-Sensoren — nie durch `get_compatible_sensors()` gefiltert wurde: weder bei der Entity-Erzeugung (`sensor.py`) noch beim Register-Read (`coordinator.py::_read_general_sensors_batch`). Ein `firmware_version`/`firmware_versions`-Feld bei einem General Sensor hatte dadurch **nie** eine Wirkung — auch nicht vor diesem Release. Ohne diesen Fix hätte die Firmware-Range-Gatung bei `ambient_temperature` keine Wirkung gezeigt.

**Fix:** `sensor.py` erzeugt General-Sensor-Entities jetzt über `get_compatible_sensors(SENSOR_TYPES, fw_version)`; `coordinator.py::_read_general_sensors_batch()` erhält die kompatible Sensor-Liste als Parameter statt `SENSOR_TYPES` direkt zu iterieren.

**Betroffene Dateien:** `custom_components/lambda_heat_pumps/sensor.py`, `custom_components/lambda_heat_pumps/coordinator.py`

---

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `custom_components/lambda_heat_pumps/const_base.py` | `MAX_ENERGY_DELTA_WH = 5000` neu — einzige Quelle für den `calculate_energy_delta`-Schwellenwert |
| `custom_components/lambda_heat_pumps/utils.py` | `_parse_firmware_versions()` neu; `get_compatible_sensors()` um Range-Notation erweitert; `calculate_energy_delta()` gibt `None` statt `max_delta` zurück, Default aus `MAX_ENERGY_DELTA_WH`; `is_sentinel_value()` neu, inkl. opt-in `extra_sentinels`-Parameter |
| `custom_components/lambda_heat_pumps/coordinator.py` | Caller von `calculate_energy_delta` behandelt `None` und übergibt `max_delta` nicht mehr explizit; Sentinel-Check (inkl. `sentinel_values` aus Template) vor Skalierung an 5 Stellen, mit `INFO`-Log; `_read_general_sensors_batch()` erhält gefilterte Sensor-Liste als Parameter |
| `custom_components/lambda_heat_pumps/sensor.py` | Entity-Erzeugung für General Sensors (`SENSOR_TYPES`) nutzt jetzt `get_compatible_sensors()` |
| `custom_components/lambda_heat_pumps/const_sensor.py` | `ambient_temperature`: `"firmware_versions": ["1-7"]` + `"sentinel_values": [65535]`; Buffer-Anforderungsregister 3005–3009 (5 Sensoren) + HC 5006 (`operating_mode`): `"sentinel_values": [65535]` |

---

## Offen (nicht Teil dieses Releases)

- **Befund 3 (undokumentierte Register 1024–1060):** Nur 4 der Register in diesem Bereich (`config_parameter_24/33/50/60`) sind tatsächlich undokumentierte Platzhalter. Die FW-Grenze zur neuen Steuerungsgeneration ist noch mit dem Issue-Autor zu klären; bis dahin schützt die Sentinel-Filterung (Befund 2) bereits vor Fehlwerten.
- **Befund 4b (`volume_flow_heat_sink` unit/scale):** Noch nicht umgesetzt.

Details: [ToDo-Dokument Issue #100](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/V2.8.0/docs_md/ToDos/issue100_firmware_range_v280.md).
